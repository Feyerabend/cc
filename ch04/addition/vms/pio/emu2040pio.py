#!/usr/bin/env python3
# Raspberry Pi Pico PIO (Programmable I/O) Emulator

import time
import re
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Protocol, Any, Union
from enum import Enum
from abc import ABC, abstractmethod


class PIOError(Exception):
    pass


class InstructionType(Enum):
    JMP = "jmp"
    WAIT = "wait"
    IN = "in"
    OUT = "out"
    PUSH = "push"
    PULL = "pull"
    MOV = "mov"
    IRQ = "irq"
    SET = "set"
    NOP = "nop"
    RAW = "raw"


class JmpCondition(Enum):
    ALWAYS = None
    NOT_X = "!x"
    X_DECREMENT = "x--"
    NOT_Y = "!y"
    Y_DECREMENT = "y--"
    X_NOT_EQUAL_Y = "x!=y"
    PIN = "pin"
    NOT_OSRE = "!osre"


class WaitCondition(Enum):
    GPIO = "gpio"
    PIN = "pin"
    IRQ = "irq"


class Instruction(ABC):    
    def __init__(self, delay: int = 0, side_set: Optional[int] = None):
        self.delay = delay
        self.side_set = side_set
    
    @abstractmethod
    def execute(self, sm: 'PIOStateMachine') -> bool:
        pass
    
    @abstractmethod
    def __str__(self) -> str:
        pass


@dataclass
class JmpInstruction(Instruction):
    condition: Optional[JmpCondition]
    target: Union[int, str]
    
    def execute(self, sm: 'PIOStateMachine') -> bool:
        should_jump = True
        
        if self.condition == JmpCondition.NOT_X:
            should_jump = sm.x == 0
        elif self.condition == JmpCondition.X_DECREMENT:
            sm.x = (sm.x - 1) & 0xFFFFFFFF
            should_jump = sm.x != 0
        elif self.condition == JmpCondition.NOT_Y:
            should_jump = sm.y == 0
        elif self.condition == JmpCondition.Y_DECREMENT:
            sm.y = (sm.y - 1) & 0xFFFFFFFF
            should_jump = sm.y != 0
        elif self.condition == JmpCondition.X_NOT_EQUAL_Y:
            should_jump = sm.x != sm.y
        elif self.condition == JmpCondition.PIN:
            pin_val = sm.pio.get_gpio(sm.jmp_pin)
            should_jump = bool(pin_val)
        elif self.condition == JmpCondition.NOT_OSRE:
            should_jump = sm.osr_shift_count == 0
        
        if should_jump:
            if isinstance(self.target, str):
                sm.pc = sm.labels[self.target]
            else:
                sm.pc = self.target
            return True
        
        return True
    
    def __str__(self) -> str:
        cond_str = f" {self.condition.value}" if self.condition else ""
        return f"jmp{cond_str} {self.target}"


@dataclass
class WaitInstruction(Instruction):
    polarity: int
    condition: WaitCondition
    index: int
    
    def execute(self, sm: 'PIOStateMachine') -> bool:
        if self.condition == WaitCondition.GPIO:
            gpio_val = sm.pio.get_gpio(self.index)
            if bool(gpio_val) == bool(self.polarity):
                return True
            sm.stalled = True
            return False
        elif self.condition == WaitCondition.PIN:
            pin_val = sm.pio.get_gpio(sm.in_base + self.index)
            if bool(pin_val) == bool(self.polarity):
                return True
            sm.stalled = True
            return False
        elif self.condition == WaitCondition.IRQ:
            irq_state = sm.pio.get_irq(self.index)
            if bool(irq_state) == bool(self.polarity):
                if self.polarity:  # Clear IRQ if waiting for high
                    sm.pio.clear_irq(self.index)
                return True
            sm.stalled = True
            return False
        
        return True
    
    def __str__(self) -> str:
        return f"wait {self.polarity} {self.condition.value} {self.index}"


@dataclass
class InInstruction(Instruction):
    source: str
    bit_count: int
    
    def execute(self, sm: 'PIOStateMachine') -> bool:
        data = 0
        
        if self.source == "pins":
            for i in range(self.bit_count):
                pin_val = sm.pio.get_gpio(sm.in_base + i)
                data |= (pin_val << i)
        elif self.source == "x":
            data = sm.x >> (32 - self.bit_count)
        elif self.source == "y":
            data = sm.y >> (32 - self.bit_count)
        elif self.source == "null":
            data = 0
        elif self.source == "isr":
            data = sm.isr >> (32 - self.bit_count)
        elif self.source == "osr":
            data = sm.osr >> (32 - self.bit_count)
        
        # Shift data into ISR
        sm.isr = (sm.isr >> self.bit_count) | (data << (32 - self.bit_count))
        sm.isr_shift_count += self.bit_count
        
        # Auto-push if ISR is full
        if sm.isr_shift_count >= sm.push_threshold:
            if len(sm.rx_fifo) < 8:  # FIFO depth is 8
                sm.rx_fifo.append(sm.isr)
            sm.isr = 0
            sm.isr_shift_count = 0
        
        return True
    
    def __str__(self) -> str:
        return f"in {self.source}, {self.bit_count}"


@dataclass
class OutInstruction(Instruction):
    destination: str
    bit_count: int
    
    def execute(self, sm: 'PIOStateMachine') -> bool:
        if sm.osr_shift_count == 0:
            # Need to pull from FIFO
            if not sm.tx_fifo:
                if sm.autopull:
                    sm.osr = 0
                    sm.osr_shift_count = sm.pull_threshold
                else:
                    sm.stalled = True
                    return False
            else:
                sm.osr = sm.tx_fifo.pop(0)
                sm.osr_shift_count = 32
        
        # Extract bits from OSR
        mask = (1 << self.bit_count) - 1
        data = sm.osr & mask
        sm.osr >>= self.bit_count
        sm.osr_shift_count -= self.bit_count
        
        # Output to destination
        if self.destination == "pins":
            for i in range(self.bit_count):
                pin_val = (data >> i) & 1
                sm.pio.set_gpio(sm.out_base + i, pin_val)
        elif self.destination == "x":
            sm.x = data
        elif self.destination == "y":
            sm.y = data
        elif self.destination == "pindirs":
            for i in range(self.bit_count):
                dir_val = (data >> i) & 1
                sm.pio.set_gpio_dir(sm.out_base + i, dir_val)
        elif self.destination == "pc":
            sm.pc = data
        elif self.destination == "isr":
            sm.isr = data
        elif self.destination == "exec":
            # instruction inline
            pass # ..
        
        return True
    
    def __str__(self) -> str:
        return f"out {self.destination}, {self.bit_count}"


@dataclass
class PushInstruction(Instruction):
    if_full: bool
    block: bool
    
    def execute(self, sm: 'PIOStateMachine') -> bool:
        if self.if_full and sm.isr_shift_count < sm.push_threshold:
            return True
        
        if len(sm.rx_fifo) >= 8:  # FIFO full
            if not self.block:
                return True
            sm.stalled = True
            return False
        
        sm.rx_fifo.append(sm.isr)
        sm.isr = 0
        sm.isr_shift_count = 0
        return True
    
    def __str__(self) -> str:
        flags = []
        if self.if_full:
            flags.append("iffull")
        if not self.block:
            flags.append("noblock")
        flag_str = " " + " ".join(flags) if flags else ""
        return f"push{flag_str}"


@dataclass
class PullInstruction(Instruction):
    if_empty: bool
    block: bool
    
    def execute(self, sm: 'PIOStateMachine') -> bool:
        if self.if_empty and sm.osr_shift_count > 0:
            return True
        
        if not sm.tx_fifo:
            if not self.block:
                sm.osr = sm.x  # pull from X if FIFO empty and non-blocking
                sm.osr_shift_count = 32
                return True
            sm.stalled = True
            return False
        
        sm.osr = sm.tx_fifo.pop(0)
        sm.osr_shift_count = 32
        return True
    
    def __str__(self) -> str:
        flags = []
        if self.if_empty:
            flags.append("ifempty")
        if not self.block:
            flags.append("noblock")
        flag_str = " " + " ".join(flags) if flags else ""
        return f"pull{flag_str}"


@dataclass
class MovInstruction(Instruction):
    destination: str
    source: str
    operation: Optional[str] = None
    
    def execute(self, sm: 'PIOStateMachine') -> bool:
        # source value
        if self.source == "pins":
            value = 0
            for i in range(32):
                if sm.pio.get_gpio(sm.in_base + i):
                    value |= (1 << i)
        elif self.source == "x":
            value = sm.x
        elif self.source == "y":
            value = sm.y
        elif self.source == "null":
            value = 0
        elif self.source == "status":
            value = (len(sm.tx_fifo) << 4) | len(sm.rx_fifo)
        elif self.source == "isr":
            value = sm.isr
        elif self.source == "osr":
            value = sm.osr
        else:
            value = 0
        
        if self.operation == "~":
            value = ~value & 0xFFFFFFFF
        elif self.operation == "::":
            # reverse  bits
            value = int(f"{value:032b}"[::-1], 2)
        
        if self.destination == "pins":
            for i in range(32):
                pin_val = (value >> i) & 1
                sm.pio.set_gpio(sm.out_base + i, pin_val)
        elif self.destination == "x":
            sm.x = value & 0xFFFFFFFF
        elif self.destination == "y":
            sm.y = value & 0xFFFFFFFF
        elif self.destination == "isr":
            sm.isr = value & 0xFFFFFFFF
        elif self.destination == "osr":
            sm.osr = value & 0xFFFFFFFF
        elif self.destination == "pc":
            sm.pc = value & 0x1F  # PC is 5 bits
        
        return True
    
    def __str__(self) -> str:
        op_str = f" {self.operation}" if self.operation else ""
        return f"mov {self.destination}, {self.operation or ''}{self.source}"

# simplify, simplify
@dataclass
class IrqInstruction(Instruction):
    clear: bool
    wait: bool
    index: int
    
    def execute(self, sm: 'PIOStateMachine') -> bool:
        if self.clear:
            sm.pio.clear_irq(self.index)
        else:
            sm.pio.set_irq(self.index)
        
        if self.wait:
            # wait for IRQ to be cleared
            if sm.pio.get_irq(self.index):
                sm.stalled = True
                return False
        
        return True
    
    def __str__(self) -> str:
        flags = []
        if self.clear:
            flags.append("clear")
        if self.wait:
            flags.append("wait")
        flag_str = " " + " ".join(flags) if flags else ""
        return f"irq{flag_str} {self.index}"


@dataclass
class SetInstruction(Instruction):
    destination: str
    value: int
    
    def execute(self, sm: 'PIOStateMachine') -> bool:
        if self.destination == "pins":
            for i in range(sm.set_count):
                pin_val = (self.value >> i) & 1
                sm.pio.set_gpio(sm.set_base + i, pin_val)
        elif self.destination == "x":
            sm.x = self.value & 0xFFFFFFFF
        elif self.destination == "y":
            sm.y = self.value & 0xFFFFFFFF
        elif self.destination == "pindirs":
            for i in range(sm.set_count):
                dir_val = (self.value >> i) & 1
                sm.pio.set_gpio_dir(sm.set_base + i, dir_val)
        
        return True
    
    def __str__(self) -> str:
        return f"set {self.destination}, {self.value}"


@dataclass
class NopInstruction(Instruction):    
    def execute(self, sm: 'PIOStateMachine') -> bool:
        return True
    
    def __str__(self) -> str:
        return "nop"


@dataclass
class RawInstruction(Instruction):
    text: str
    
    def execute(self, sm: 'PIOStateMachine') -> bool:
        return True
    
    def __str__(self) -> str:
        return self.text


class PIOBlock:    
    def __init__(self):
        self.state_machines: List['PIOStateMachine'] = []
        self.gpio_state = [0] * 32  # 32 GPIO pins
        self.gpio_dirs = [0] * 32   # GPIO directions (0=in, 1=out)
        self.irq_flags = [False] * 8  # 8 IRQ flags
        self.instruction_memory: List[Instruction] = []
        self.running = False
        
    def add_state_machine(self, sm: 'PIOStateMachine'):
        if len(self.state_machines) >= 4:
            raise PIOError("PIO block can only contain 4 state machines")
        sm.pio = self
        sm.sm_id = len(self.state_machines)
        self.state_machines.append(sm)
    
    def get_gpio(self, pin: int) -> int:
        if 0 <= pin < 32:
            return self.gpio_state[pin]
        return 0
    
    def set_gpio(self, pin: int, value: int):
        if 0 <= pin < 32:
            self.gpio_state[pin] = value & 1
    
    def set_gpio_dir(self, pin: int, direction: int):
        if 0 <= pin < 32:
            self.gpio_dirs[pin] = direction & 1
    
    def get_irq(self, index: int) -> bool:
        if 0 <= index < 8:
            return self.irq_flags[index]
        return False
    
    def set_irq(self, index: int):
        if 0 <= index < 8:
            self.irq_flags[index] = True
    
    def clear_irq(self, index: int):
        if 0 <= index < 8:
            self.irq_flags[index] = False
    
    def start_all(self):
        self.running = True
        for sm in self.state_machines:
            sm.enabled = True
    
    def stop_all(self):
        self.running = False
        for sm in self.state_machines:
            sm.enabled = False
    
    def step_all(self):
        if not self.running:
            return False
        
        any_active = False
        for sm in self.state_machines:
            if sm.enabled and sm.step():
                any_active = True
        
        return any_active


class PIOStateMachine:
    def __init__(self):
        # Registers
        self.pc = 0
        self.x = 0
        self.y = 0
        self.isr = 0  # Input Shift Register
        self.osr = 0  # Output Shift Register
        
        # FIFO
        self.tx_fifo: List[int] = []
        self.rx_fifo: List[int] = []
        
        # Configuration
        self.enabled = False
        self.stalled = False
        self.autopull = False
        self.autopush = False
        self.pull_threshold = 32
        self.push_threshold = 32
        
        # Pin configuration
        self.out_base = 0
        self.out_count = 1
        self.set_base = 0
        self.set_count = 1
        self.in_base = 0
        self.sideset_base = 0
        self.sideset_count = 0
        self.jmp_pin = 0
        
        # Program control
        self.wrap_target = 0
        self.wrap = 31
        self.instructions: List[Instruction] = []
        self.labels: Dict[str, int] = {}
        
        # Shift registers
        self.isr_shift_count = 0
        self.osr_shift_count = 0
        
        # Clock
        self.cycle_count = 0
        
        # Reference to PIO block
        self.pio: Optional[PIOBlock] = None
        self.sm_id = 0
    
    def load_program(self, program: List[str]):
        self.instructions = []
        self.labels = {}
        
        # First pass: find labels and directives
        for i, line in enumerate(program):
            line = line.strip()
            if line.endswith(':') and not line.startswith(';'):
                # Label
                label = line[:-1].strip()
                self.labels[label] = i
            elif line.startswith('.wrap_target'):
                self.wrap_target = i
            elif line.startswith('.wrap'):
                self.wrap = i
        
        # Second pass: parse instructions
        for line in program:
            instruction = self._parse_instruction(line.strip())
            self.instructions.append(instruction)
    
    def _parse_instruction(self, line: str) -> Instruction:
            if not line or line.startswith(';') or line.startswith('.') or line.endswith(':'):
                return RawInstruction(line)
            
            # Parse delay and side-set
            delay = 0
            side_set = None
            
            delay_match = re.search(r'\[(\d+)\]', line)
            if delay_match:
                delay = int(delay_match.group(1))
                line = re.sub(r'\[\d+\]', '', line)
            
            side_match = re.search(r'side\s+(\d+)', line, re.IGNORECASE)
            if side_match:
                side_set = int(side_match.group(1))
                line = re.sub(r'side\s+\d+', '', line, flags=re.IGNORECASE)
            
            # split
            parts = [p.strip() for p in re.split(r'[,\s]+', line) if p.strip()]
            if not parts:
                return RawInstruction(line)
            
            op = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            # Parse based on operation - create instruction with base class args first
            if op == 'jmp':
                if len(args) == 1:
                    target = args[0]
                    if target.isdigit():
                        target = int(target)
                    instr = JmpInstruction(None, target)
                else:
                    condition_str = args[0].lower()
                    condition = None
                    for cond in JmpCondition:
                        if cond.value == condition_str:
                            condition = cond
                            break
                    target = args[1]
                    if target.isdigit():
                        target = int(target)
                    instr = JmpInstruction(condition, target)
            
            elif op == 'wait':
                polarity = int(args[0])
                condition_str = args[1].lower()
                condition = WaitCondition.GPIO  # default
                for cond in WaitCondition:
                    if cond.value == condition_str:
                        condition = cond
                        break
                index = int(args[2])
                instr = WaitInstruction(polarity, condition, index)
            
            elif op == 'in':
                source = args[0].lower()
                bit_count = int(args[1])
                instr = InInstruction(source, bit_count)
            
            elif op == 'out':
                dest = args[0].lower()
                bit_count = int(args[1])
                instr = OutInstruction(dest, bit_count)
            
            elif op == 'push':
                if_full = 'iffull' in [a.lower() for a in args]
                block = 'noblock' not in [a.lower() for a in args]
                instr = PushInstruction(if_full, block)
            
            elif op == 'pull':
                if_empty = 'ifempty' in [a.lower() for a in args]
                block = 'noblock' not in [a.lower() for a in args]
                instr = PullInstruction(if_empty, block)
            
            elif op == 'mov':
                dest = args[0].lower()
                source_arg = args[1].lower()
                operation = None
                source = source_arg
                if source_arg.startswith('~'):
                    operation = '~'
                    source = source_arg[1:]
                elif '::' in source_arg:
                    operation = '::'
                    source = source_arg.replace('::', '')
                instr = MovInstruction(dest, source, operation)
            
            elif op == 'irq':
                clear = 'clear' in [a.lower() for a in args]
                wait = 'wait' in [a.lower() for a in args]
                # Find the index (should be a number)
                index = 0
                for arg in args:
                    if arg.isdigit():
                        index = int(arg)
                        break
                instr = IrqInstruction(clear, wait, index)
            
            elif op == 'set':
                dest = args[0].lower()
                value = int(args[1])
                instr = SetInstruction(dest, value)
            
            elif op == 'nop':
                instr = NopInstruction()
            
            else:
                return RawInstruction(line)
            
            # Set delay and side_set after creating the instruction
            instr.delay = delay
            instr.side_set = side_set
            return instr
    
    def step(self) -> bool:
        if not self.enabled or self.stalled:
            return self.enabled
        
        if self.pc >= len(self.instructions):
            if self.wrap >= 0:
                self.pc = self.wrap_target
            else:
                self.enabled = False
                return False
        
        instruction = self.instructions[self.pc]
        
        # Execute instruction (skip RawInstructions)
        if not isinstance(instruction, RawInstruction):
            continue_execution = instruction.execute(self)
            if not continue_execution:
                return True  # Stalled, but still enabled
            
            # Handle side-set (only for non-raw instructions)
            if hasattr(instruction, 'side_set') and instruction.side_set is not None and self.sideset_count > 0:
                for i in range(self.sideset_count):
                    pin_val = (instruction.side_set >> i) & 1
                    if self.pio:
                        self.pio.set_gpio(self.sideset_base + i, pin_val)
            
            # Handle delay (only for non-raw instructions)
            if hasattr(instruction, 'delay'):
                for _ in range(instruction.delay):
                    self.cycle_count += 1
        
        # Advance PC if not modified by instruction
        if isinstance(instruction, JmpInstruction):
            # JMP instruction handles PC itself
            pass
        else:
            self.pc += 1
        
        # Handle wrap
        if self.pc > self.wrap:
            self.pc = self.wrap_target
        
        self.cycle_count += 1
        return True

    def run_cycles(self, max_cycles: int = 1000):
        for _ in range(max_cycles):
            if not self.step():
                break
    
    def put_tx(self, value: int):
        if len(self.tx_fifo) < 8:
            self.tx_fifo.append(value & 0xFFFFFFFF)
    
    def get_rx(self) -> Optional[int]:
        if self.rx_fifo:
            return self.rx_fifo.pop(0)
        return None
    
    def restart(self):
        self.pc = 0
        self.stalled = False
        self.cycle_count = 0
        self.isr = 0
        self.osr = 0
        self.isr_shift_count = 0
        self.osr_shift_count = 0
    
    def print_state(self):
        current_instr = ""
        if self.pc < len(self.instructions):
            current_instr = str(self.instructions[self.pc])
        
        print(f"SM{self.sm_id}: PC={self.pc:2d} X={self.x:08x} Y={self.y:08x} "
              f"ISR={self.isr:08x}({self.isr_shift_count:2d}) "
              f"OSR={self.osr:08x}({self.osr_shift_count:2d}) "
              f"TX={len(self.tx_fifo)} RX={len(self.rx_fifo)} "
              f"{'STALL' if self.stalled else 'RUN  '} | {current_instr}")


# example programs
def blink_program():
    """Simple LED blink program"""
    return [
        ".wrap_target",
        "    set pins, 1   [31]",
        "    set pins, 0   [31]",
        ".wrap"
    ]

def ws2812_program():
    """WS2812 RGB LED driver program"""
    return [
        ".side_set 1",
        "",
        ".wrap_target",
        "bitloop:",
        "    out x, 1       side 0 [2]",
        "    jmp !x, do_zero side 1 [1]",
        "do_one:",
        "    jmp bitloop    side 1 [4]",
        "do_zero:",
        "    nop            side 0 [4]",
        ".wrap"
    ]

def uart_tx_program():
    """UART transmit program"""
    return [
        ".side_set 1 opt",
        "",
        "    pull       side 1 [7]",
        "    set x, 7   side 0 [7]",
        "bitloop:",
        "    out pins, 1",
        "    jmp x--, bitloop [6]",
        "    nop        side 1 [7]"
    ]

def counter_program():
    """Simple counter with conditional jump"""
    return [
        "    set x, 31",
        "loop:",
        "    out pins, 1 [3]",
        "    jmp x--, loop",
        "    irq 0",
        "    jmp 0"
    ]



# example usage
def demo_blink():
    """Demonstrate LED blinking"""
    print("=== LED Blink Demo ===")
    pio = PIOBlock()
    sm = PIOStateMachine()
    
    # Configure state machine
    sm.set_base = 0
    sm.set_count = 1
    
    # Load program
    sm.load_program(blink_program())
    pio.add_state_machine(sm)
    
    print("Program loaded:")
    for i, instruction in enumerate(sm.instructions):
        print(f"  {i:2d}: {instruction}")
    
    print("\nRunning simulation:")
    pio.start_all()
    
    # Run simulation for several cycles
    print("Cycle | Pin State")
    print("------|----------")
    
    for cycle in range(20):  # Run for 20 cycles to see the pattern
        pio.step_all()
        pin_state = pio.get_gpio(0)  # Check pin 0 state
        print(f"  {cycle:2d}  |    {pin_state}")
        
        # Add a small delay to make it more realistic
        time.sleep(0.1)
    
    print("\nFinal state machine status:")
    sm.print_state()


def demo_ws2812():
    """Demonstrate WS2812 RGB LED driver"""
    print("\n=== WS2812 RGB LED Demo ===")
    pio = PIOBlock()
    sm = PIOStateMachine()
    
    # Configure for WS2812 (side-set pin for data)
    sm.sideset_base = 0
    sm.sideset_count = 1
    sm.out_base = 0
    sm.out_count = 1
    
    # Load program
    sm.load_program(ws2812_program())
    pio.add_state_machine(sm)
    
    # Put some test data (RGB values)
    sm.put_tx(0x00FF0000)  # Red
    sm.put_tx(0x0000FF00)  # Green
    
    pio.start_all()
    
    print("Sending RGB data...")
    for cycle in range(30):
        pio.step_all()
        data_pin = pio.get_gpio(0)
        print(f"Cycle {cycle:2d}: Data pin = {data_pin}")
        if cycle > 0 and cycle % 10 == 0:
            print("---")


def demo_uart_tx():
    """Demonstrate UART transmit"""
    print("\n=== UART TX Demo ===")
    pio = PIOBlock()
    sm = PIOStateMachine()
    
    # Configure UART
    sm.out_base = 0
    sm.out_count = 1
    sm.sideset_base = 0
    sm.sideset_count = 1
    
    sm.load_program(uart_tx_program())
    pio.add_state_machine(sm)
    
    # Send character 'A' (0x41)
    sm.put_tx(0x41)
    
    pio.start_all()
    
    print("Transmitting 'A' (0x41)...")
    for cycle in range(20):
        pio.step_all()
        tx_pin = pio.get_gpio(0)
        print(f"Cycle {cycle:2d}: TX = {tx_pin}")


def demo_counter():
    """Demonstrate counter with conditional jump"""
    print("\n=== Counter Demo ===")
    pio = PIOBlock()
    sm = PIOStateMachine()
    
    # Configure counter
    sm.out_base = 0
    sm.out_count = 8  # 8-bit output
    
    sm.load_program(counter_program())
    pio.add_state_machine(sm)
    
    # Put counter values
    for i in range(5):
        sm.put_tx(i)
    
    pio.start_all()
    
    print("Running counter...")
    for cycle in range(50):
        pio.step_all()
        if cycle % 5 == 0:  # Print every 5th cycle
            sm.print_state()
        
        # Check for IRQ
        if pio.get_irq(0):
            print(f"IRQ triggered at cycle {cycle}")
            pio.clear_irq(0)


def demo_all():
    """Run all demos"""
    demo_blink()
    demo_ws2812()
    demo_uart_tx()
    demo_counter()


# Update the main execution
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        demo_name = sys.argv[1].lower()
        if demo_name == "blink":
            demo_blink()
        elif demo_name == "ws2812":
            demo_ws2812()
        elif demo_name == "uart":
            demo_uart_tx()
        elif demo_name == "counter":
            demo_counter()
        elif demo_name == "all":
            demo_all()
        else:
            print("Available demos: blink, ws2812, uart, counter, all")
    else:
        demo_blink()  # Default demo


