from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Protocol, runtime_checkable
from collections import defaultdict
import time


class VMError(Exception):
    """Base exception for all VM-related errors."""
    pass


class StackUnderflowError(VMError):
    pass


class InvalidInstructionError(VMError):
    pass


class MemoryAccessError(VMError):
    pass


class DivisionByZeroError(VMError):
    pass


class CallStackUnderflowError(VMError):
    pass


class OpCode(Enum):
    PUSH = 0x01
    POP = 0x02
    DUP = 0x03
    SWAP = 0x04
    ROT = 0x05

    ADD = 0x10
    SUB = 0x11
    MUL = 0x12
    DIV = 0x13
    MOD = 0x14
    NEG = 0x15

    EQ = 0x30
    NE = 0x31
    LT = 0x32
    LE = 0x33
    GT = 0x34
    GE = 0x35

    JUMP = 0x40
    JUMP_IF_ZERO = 0x41
    JUMP_IF_NOT_ZERO = 0x42
    CALL = 0x43
    RET = 0x44

    LOAD = 0x50
    STORE = 0x51
    LOAD_LOCAL = 0x52
    STORE_LOCAL = 0x53

    PRINT = 0x60
    PRINT_CHAR = 0x61
    INPUT = 0x62

    HALT = 0x70
    NOP = 0x71


@dataclass(frozen=True)
class Instruction:
    opcode: OpCode
    operands: tuple[Any, ...] = field(default_factory=tuple)
    address: int = 0

    def __str__(self) -> str:
        if not self.operands:
            return self.opcode.name
        return f"{self.opcode.name} {' '.join(map(str, self.operands))}"

    def __post_init__(self) -> None:
        self._validate_operands_count()

    def _validate_operands_count(self) -> None:
        expected = {
            OpCode.PUSH: 1,
            OpCode.JUMP: 1,
            OpCode.JUMP_IF_ZERO: 1,
            OpCode.JUMP_IF_NOT_ZERO: 1,
            OpCode.CALL: 1,
            OpCode.LOAD: 1,
            OpCode.STORE: 1,
            OpCode.LOAD_LOCAL: 1,
            OpCode.STORE_LOCAL: 1,
        }.get(self.opcode, 0)

        if len(self.operands) != expected:
            raise InvalidInstructionError(
                f"{self.opcode.name} expects {expected} operand(s), got {len(self.operands)}"
            )


@runtime_checkable
class InstructionExecutor(Protocol):
    def execute(self, vm: 'ExecutionEngine', instr: Instruction) -> Optional[int]:
        """Return new PC or None to continue with pc += 1"""


@runtime_checkable
class InstructionCompiler(Protocol):
    def compile_to_python(self, vm: 'ExecutionEngine', instr: Instruction) -> list[str]:
        """Return list of python code lines (indented)"""


class InstructionHandler(ABC, InstructionExecutor, InstructionCompiler):
    """Base class for handlers that implement both execution and JIT compilation"""
    pass


class StackHandler(InstructionHandler):
    def execute(self, vm: 'ExecutionEngine', instr: Instruction) -> Optional[int]:
        stack = vm.stack
        match instr.opcode:
            case OpCode.PUSH:
                stack.append(instr.operands[0])
            case OpCode.POP:
                if not stack: raise StackUnderflowError("POP")
                stack.pop()
            case OpCode.DUP:
                if not stack: raise StackUnderflowError("DUP")
                stack.append(stack[-1])
            case OpCode.SWAP:
                if len(stack) < 2: raise StackUnderflowError("SWAP")
                stack[-1], stack[-2] = stack[-2], stack[-1]
            case OpCode.ROT:
                if len(stack) < 3: raise StackUnderflowError("ROT")
                c, b, a = stack.pop(), stack.pop(), stack.pop()
                stack.extend([b, c, a])
        return None

    def compile_to_python(self, vm: 'ExecutionEngine', instr: Instruction) -> list[str]:
        match instr.opcode:
            case OpCode.PUSH:
                return [f"    stack.append({repr(instr.operands[0])})"]
            case OpCode.POP:
                return ["    if not stack: raise StackUnderflowError('POP')", "    stack.pop()"]
            case OpCode.DUP:
                return ["    if not stack: raise StackUnderflowError('DUP')", "    stack.append(stack[-1])"]
            case OpCode.SWAP:
                return ["    if len(stack) < 2: raise StackUnderflowError('SWAP')",
                        "    stack[-1], stack[-2] = stack[-2], stack[-1]"]
            case OpCode.ROT:
                return ["    if len(stack) < 3: raise StackUnderflowError('ROT')",
                        "    c, b, a = stack.pop(), stack.pop(), stack.pop()",
                        "    stack.extend([b, c, a])"]
        return []


class ArithmeticHandler(InstructionHandler):
    def execute(self, vm: 'ExecutionEngine', instr: Instruction) -> Optional[int]:
        stack = vm.stack
        if instr.opcode == OpCode.NEG:
            if not stack: raise StackUnderflowError("NEG")
            stack[-1] = -stack[-1]
            return None

        if len(stack) < 2: raise StackUnderflowError(instr.opcode.name)
        b = stack.pop()
        a = stack.pop()

        match instr.opcode:
            case OpCode.ADD: result = a + b
            case OpCode.SUB: result = a - b
            case OpCode.MUL: result = a * b
            case OpCode.DIV:
                if b == 0: raise DivisionByZeroError()
                result = a / b
            case OpCode.MOD:
                if b == 0: raise DivisionByZeroError()
                result = a % b
            case _:
                raise InvalidInstructionError(f"Unexpected arithmetic opcode: {instr.opcode}")
        stack.append(result)
        return None

    def compile_to_python(self, vm: 'ExecutionEngine', instr: Instruction) -> list[str]:
        if instr.opcode == OpCode.NEG:
            return ["    if not stack: raise StackUnderflowError('NEG')", "    stack[-1] = -stack[-1]"]

        op_map = {OpCode.ADD: "+", OpCode.SUB: "-", OpCode.MUL: "*", OpCode.DIV: "/", OpCode.MOD: "%"}
        op = op_map[instr.opcode]

        lines = [
            f"    if len(stack) < 2: raise StackUnderflowError('{instr.opcode.name}')",
            "    b = stack.pop()",
            "    a = stack.pop()"
        ]
        if instr.opcode in (OpCode.DIV, OpCode.MOD):
            lines.append("    if b == 0: raise DivisionByZeroError()")
        lines.append(f"    stack.append(a {op} b)")
        return lines


class ComparisonHandler(InstructionHandler):
    def execute(self, vm: 'ExecutionEngine', instr: Instruction) -> Optional[int]:
        stack = vm.stack
        if len(stack) < 2: raise StackUnderflowError(instr.opcode.name)
        b = stack.pop()
        a = stack.pop()

        result = {
            OpCode.EQ: a == b,
            OpCode.NE: a != b,
            OpCode.LT: a < b,
            OpCode.LE: a <= b,
            OpCode.GT: a > b,
            OpCode.GE: a >= b,
        }[instr.opcode]

        stack.append(1 if result else 0)
        return None

    def compile_to_python(self, vm: 'ExecutionEngine', instr: Instruction) -> list[str]:
        op_map = {
            OpCode.EQ: "==", OpCode.NE: "!=", OpCode.LT: "<",
            OpCode.LE: "<=", OpCode.GT: ">", OpCode.GE: ">="
        }
        op = op_map[instr.opcode]

        return [
            f"    if len(stack) < 2: raise StackUnderflowError('{instr.opcode.name}')",
            "    b = stack.pop()",
            "    a = stack.pop()",
            f"    stack.append(1 if a {op} b else 0)"
        ]


class ControlFlowHandler(InstructionHandler):
    def execute(self, vm: 'ExecutionEngine', instr: Instruction) -> Optional[int]:
        match instr.opcode:
            case OpCode.JUMP:
                target = instr.operands[0]
                if not (0 <= target < len(vm.instructions)):
                    raise VMError(f"Jump target out of bounds: {target}")
                return target

            case OpCode.JUMP_IF_ZERO:
                if not vm.stack: raise StackUnderflowError("JUMP_IF_ZERO")
                val = vm.stack.pop()
                if val == 0:
                    target = instr.operands[0]
                    if not (0 <= target < len(vm.instructions)):
                        raise VMError(f"Jump target out of bounds: {target}")
                    return target

            case OpCode.JUMP_IF_NOT_ZERO:
                if not vm.stack: raise StackUnderflowError("JUMP_IF_NOT_ZERO")
                val = vm.stack.pop()
                if val != 0:
                    target = instr.operands[0]
                    if not (0 <= target < len(vm.instructions)):
                        raise VMError(f"Jump target out of bounds: {target}")
                    return target

            case OpCode.CALL:
                target = instr.operands[0]
                if not (0 <= target < len(vm.instructions)):
                    raise VMError(f"Call target out of bounds: {target}")
                vm.call_stack.append(vm.pc + 1)
                return target

            case OpCode.RET:
                if not vm.call_stack:
                    raise CallStackUnderflowError("RET with empty call stack")
                return vm.call_stack.pop()

        return None

    def compile_to_python(self, vm: 'ExecutionEngine', instr: Instruction) -> list[str]:
        # For loop compilation - compile conditional branches differently
        match instr.opcode:
            case OpCode.JUMP_IF_ZERO:
                target = instr.operands[0]
                # In a loop, this exits to code after the loop
                return [
                    "    if not stack: raise StackUnderflowError('JUMP_IF_ZERO')",
                    "    val = stack.pop()",
                    f"    if val == 0:",
                    f"        return {target}  # exit loop"
                ]
            case OpCode.JUMP_IF_NOT_ZERO:
                target = instr.operands[0]
                return [
                    "    if not stack: raise StackUnderflowError('JUMP_IF_NOT_ZERO')",
                    "    val = stack.pop()",
                    f"    if val != 0:",
                    f"        return {target}  # conditional jump"
                ]
            case OpCode.JUMP:
                # Backward jump - handled by while loop, don't compile
                return ["    # backward jump - handled by loop structure"]
            case _:
                return [f"    return {vm.pc}  # exit JIT region"]


class MemoryHandler(InstructionHandler):
    def execute(self, vm: 'ExecutionEngine', instr: Instruction) -> Optional[int]:
        match instr.opcode:
            case OpCode.LOAD:
                addr = instr.operands[0]
                if addr < 0:
                    raise MemoryAccessError(f"Negative memory address: {addr}")
                vm.stack.append(vm.memory.get(addr, 0))

            case OpCode.STORE:
                addr = instr.operands[0]
                if addr < 0:
                    raise MemoryAccessError(f"Negative memory address: {addr}")
                if not vm.stack:
                    raise StackUnderflowError("STORE")
                vm.memory[addr] = vm.stack.pop()

            case OpCode.LOAD_LOCAL:
                idx = instr.operands[0]
                if idx < 0:
                    raise MemoryAccessError(f"Negative local index: {idx}")
                while idx >= len(vm.locals):
                    vm.locals.append(0)
                vm.stack.append(vm.locals[idx])

            case OpCode.STORE_LOCAL:
                idx = instr.operands[0]
                if idx < 0:
                    raise MemoryAccessError(f"Negative local index: {idx}")
                if not vm.stack:
                    raise StackUnderflowError("STORE_LOCAL")
                while idx >= len(vm.locals):
                    vm.locals.append(0)
                vm.locals[idx] = vm.stack.pop()

        return None

    def compile_to_python(self, vm: 'ExecutionEngine', instr: Instruction) -> list[str]:
        match instr.opcode:
            case OpCode.LOAD:
                addr = instr.operands[0]
                return [
                    f"    if {addr} < 0: raise MemoryAccessError('Negative address')",
                    f"    stack.append(memory.get({addr}, 0))"
                ]
            case OpCode.STORE:
                addr = instr.operands[0]
                return [
                    f"    if {addr} < 0: raise MemoryAccessError('Negative address')",
                    "    if not stack: raise StackUnderflowError('STORE')",
                    f"    memory[{addr}] = stack.pop()"
                ]
            case OpCode.LOAD_LOCAL:
                idx = instr.operands[0]
                return [
                    f"    if {idx} < 0: raise MemoryAccessError('Negative local index')",
                    f"    while {idx} >= len(locals): locals.append(0)",
                    f"    stack.append(locals[{idx}])"
                ]
            case OpCode.STORE_LOCAL:
                idx = instr.operands[0]
                return [
                    f"    if {idx} < 0: raise MemoryAccessError('Negative local index')",
                    "    if not stack: raise StackUnderflowError('STORE_LOCAL')",
                    f"    while {idx} >= len(locals): locals.append(0)",
                    f"    locals[{idx}] = stack.pop()"
                ]
        return []


class IOHandler(InstructionHandler):
    def execute(self, vm: 'ExecutionEngine', instr: Instruction) -> Optional[int]:
        match instr.opcode:
            case OpCode.PRINT:
                if not vm.stack: raise StackUnderflowError("PRINT")
                print(f"Output: {vm.stack.pop()}")

            case OpCode.PRINT_CHAR:
                if not vm.stack: raise StackUnderflowError("PRINT_CHAR")
                code = vm.stack.pop()
                if not isinstance(code, int) or not (0 <= code <= 127):
                    raise VMError(f"Invalid char code: {code}")
                print(chr(code), end="")

            case OpCode.INPUT:
                try:
                    value = input("Input: ")
                    if value.strip() == "":
                        vm.stack.append("")
                    else:
                        try:
                            vm.stack.append(int(value))
                        except ValueError:
                            try:
                                vm.stack.append(float(value))
                            except ValueError:
                                vm.stack.append(value)
                except EOFError:
                    vm.stack.append("")

        return None

    def compile_to_python(self, vm: 'ExecutionEngine', instr: Instruction) -> list[str]:
        match instr.opcode:
            case OpCode.PRINT:
                return [
                    "    if not stack: raise StackUnderflowError('PRINT')",
                    "    print(f'Output: {{stack.pop()}}')"
                ]
            case OpCode.PRINT_CHAR:
                return [
                    "    if not stack: raise StackUnderflowError('PRINT_CHAR')",
                    "    code = stack.pop()",
                    "    if not isinstance(code, int) or not (0 <= code <= 127):",
                    "        raise VMError(f'Invalid char code: {{code}}')",
                    "    print(chr(code), end='')"
                ]
            case _:
                return ["    # I/O operation - not supported in JIT"]
        return []


@dataclass
class JITStats:
    """Statistics about JIT compilation"""
    compilations: int = 0
    jit_executions: int = 0
    interpreter_executions: int = 0
    total_jit_time: float = 0.0
    total_interp_time: float = 0.0
    
    def show(self) -> None:
        print(f"\n{'='*60}")
        print(f"JIT COMPILATION STATISTICS")
        print(f"{'='*60}")
        print(f"Total compilations:       {self.compilations}")
        print(f"JIT executions:           {self.jit_executions:,}")
        print(f"Interpreter executions:   {self.interpreter_executions:,}")
        print(f"Total JIT time:           {self.total_jit_time:.6f}s")
        print(f"Total interpreter time:   {self.total_interp_time:.6f}s")
        if self.jit_executions > 0 and self.interpreter_executions > 0:
            avg_jit = self.total_jit_time / self.jit_executions
            avg_interp = self.total_interp_time / self.interpreter_executions
            speedup = avg_interp / avg_jit if avg_jit > 0 else 0
            print(f"Avg JIT exec time:        {avg_jit*1e6:.2f}μs")
            print(f"Avg interp exec time:     {avg_interp*1e6:.2f}μs")
            print(f"Speedup factor:           {speedup:.2f}x")
        print(f"{'='*60}\n")


class ExecutionEngine:
    def __init__(self, hotspot_threshold: int = 10, verbose: bool = False):
        self.stack: list[Any] = []
        self.call_stack: list[int] = []
        self.memory: dict[int, Any] = {}
        self.locals: list[Any] = []
        self.pc: int = 0
        self.instructions: list[Instruction] = []
        self.hotspot_threshold = hotspot_threshold
        self.verbose = verbose
        
        # JIT tracking
        self.exec_count: dict[int, int] = defaultdict(int)
        self.jit_cache: dict[int, callable] = {}
        self.handlers: dict[OpCode, InstructionHandler] = {}
        self.stats = JITStats()
        
        # Loop detection
        self.edge_count: dict[tuple[int, int], int] = defaultdict(int)
        
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.handlers.update({op: StackHandler() for op in [
            OpCode.PUSH, OpCode.POP, OpCode.DUP, OpCode.SWAP, OpCode.ROT]})
        self.handlers.update({op: ArithmeticHandler() for op in [
            OpCode.ADD, OpCode.SUB, OpCode.MUL, OpCode.DIV, OpCode.MOD, OpCode.NEG]})
        self.handlers.update({op: ComparisonHandler() for op in [
            OpCode.EQ, OpCode.NE, OpCode.LT, OpCode.LE, OpCode.GT, OpCode.GE]})
        self.handlers.update({op: ControlFlowHandler() for op in [
            OpCode.JUMP, OpCode.JUMP_IF_ZERO, OpCode.JUMP_IF_NOT_ZERO, OpCode.CALL, OpCode.RET]})
        self.handlers.update({op: MemoryHandler() for op in [
            OpCode.LOAD, OpCode.STORE, OpCode.LOAD_LOCAL, OpCode.STORE_LOCAL]})
        self.handlers.update({op: IOHandler() for op in [
            OpCode.PRINT, OpCode.PRINT_CHAR, OpCode.INPUT]})

    def load(self, instructions: list[Instruction]) -> None:
        if not instructions:
            raise ValueError("Cannot load empty program")
        self.instructions = instructions
        self.pc = 0
        for i, instr in enumerate(self.instructions):
            object.__setattr__(instr, 'address', i)

    def run(self) -> None:
        last_pc = -1
        
        while self.pc < len(self.instructions):
            instr = self.instructions[self.pc]

            if instr.opcode == OpCode.HALT:
                break

            # Track control flow edges for loop detection
            if last_pc != -1:
                edge = (last_pc, self.pc)
                self.edge_count[edge] += 1

            # JIT fast path - execute compiled code
            if self.pc in self.jit_cache:
                start_time = time.perf_counter()
                next_pc = self.jit_cache[self.pc]()
                self.stats.total_jit_time += time.perf_counter() - start_time
                self.stats.jit_executions += 1
                last_pc = self.pc
                self.pc = next_pc
                continue

            # Hotspot detection
            self.exec_count[self.pc] += 1
            if self.exec_count[self.pc] >= self.hotspot_threshold and self.pc not in self.jit_cache:
                # Try to detect a loop first (most important for JIT)
                loop = self._detect_loop(self.pc)
                if loop:
                    self._jit_compile_loop(loop)
                    # After compilation, continue from current PC (will hit cache next iteration)
                    # Don't immediately execute, let it go through normal path once more
                else:
                    # Fallback to straight-line region
                    region = self._try_detect_hot_region()
                    if region:
                        self._jit_compile_region(region)

            # Normal interpreter path
            start_time = time.perf_counter()
            handler = self.handlers.get(instr.opcode)
            if handler is None:
                raise InvalidInstructionError(f"No handler for opcode: {instr.opcode}")

            new_pc = handler.execute(self, instr)
            self.stats.total_interp_time += time.perf_counter() - start_time
            self.stats.interpreter_executions += 1
            
            last_pc = self.pc
            self.pc = new_pc if new_pc is not None else self.pc + 1

    def _detect_loop(self, pc: int) -> Optional[tuple[int, int]]:
        """Detect backward jumps (loops) starting at pc"""
        # Look for backward jump instruction within next few instructions
        for i in range(pc, min(pc + 50, len(self.instructions))):
            instr = self.instructions[i]
            if instr.opcode == OpCode.JUMP:
                target = instr.operands[0]
                # Backward jump indicates a loop
                if target <= pc:
                    # Check if this edge is hot
                    edge = (i, target)
                    if self.edge_count.get(edge, 0) >= self.hotspot_threshold // 2:
                        return (target, i)  # loop body from target to jump (excluding jump itself)
        return None

    def _try_detect_hot_region(self) -> Optional[tuple[int, int]]:
        """Detect straight-line code region"""
        start = self.pc
        end = start
        max_scan = min(start + 30, len(self.instructions))

        forbidden = {
            OpCode.JUMP, OpCode.JUMP_IF_ZERO, OpCode.JUMP_IF_NOT_ZERO,
            OpCode.CALL, OpCode.RET, OpCode.HALT, OpCode.INPUT
        }

        for i in range(start, max_scan):
            if self.instructions[i].opcode in forbidden:
                break
            end = i + 1

        if end - start >= 5:
            return start, end
        return None

    def _jit_compile_loop(self, loop: tuple[int, int]) -> None:
        """Compile a loop - this is where JIT really shines!"""
        start, end = loop
        
        # The backward JUMP is at position 'end', loop body is start to end-1
        if self.verbose:
            print(f"\n[JIT] Compiling LOOP at PC {start}-{end}")
            for i in range(start, end + 1):
                print(f"  {i:3d}: {self.instructions[i]}")
        
        lines = [
            "def jit_loop():",
            "    # JIT-compiled loop - runs much faster than interpreter!",
            "    stack = self.stack",
            "    memory = self.memory",
            "    locals = self.locals",
            "    while True:  # loop structure"
        ]

        # Compile loop body (start to end-1, excluding the backward JUMP at 'end')
        for i in range(start, end):
            instr = self.instructions[i]
            handler = self.handlers.get(instr.opcode)
            if handler:
                compiled = handler.compile_to_python(self, instr)
                # Indent one more level for while loop
                lines.extend("    " + line for line in compiled)
        
        # After the while loop completes via return, we're done
        # No need to compile the backward JUMP - the while handles it

        code = "\n".join(lines)
        
        if self.verbose:
            print("\n[JIT] Generated code:")
            print(code)
        
        local_env = {}
        try:
            exec(code, {
                "self": self,
                "StackUnderflowError": StackUnderflowError,
                "MemoryAccessError": MemoryAccessError,
                "DivisionByZeroError": DivisionByZeroError,
                "VMError": VMError
            }, local_env)
            self.jit_cache[start] = local_env["jit_loop"]
            self.stats.compilations += 1
            if self.verbose:
                print(f"[JIT] + Loop compiled successfully!\n")
        except Exception as e:
            if self.verbose:
                print(f"[JIT] - Loop compilation failed: {e}\n")

    def _jit_compile_region(self, region: tuple[int, int]) -> None:
        """Compile a straight-line region"""
        start, end = region
        
        if self.verbose:
            print(f"\n[JIT] Compiling REGION at PC {start}-{end-1}")
            for i in range(start, end):
                print(f"  {i:3d}: {self.instructions[i]}")
        
        lines = [
            "def jit_block():",
            "    stack = self.stack",
            "    memory = self.memory",
            "    locals = self.locals"
        ]

        for i in range(start, end):
            instr = self.instructions[i]
            handler = self.handlers.get(instr.opcode)
            if handler:
                lines.extend(handler.compile_to_python(self, instr))

        lines.append(f"    return {end}")

        code = "\n".join(lines)
        
        if self.verbose:
            print("\n[JIT] Generated code:")
            print(code)
        
        local_env = {}
        try:
            exec(code, {
                "self": self,
                "StackUnderflowError": StackUnderflowError,
                "MemoryAccessError": MemoryAccessError,
                "DivisionByZeroError": DivisionByZeroError
            }, local_env)
            self.jit_cache[start] = local_env["jit_block"]
            self.stats.compilations += 1
            if self.verbose:
                print(f"[JIT] + Region compiled successfully!\n")
        except Exception as e:
            if self.verbose:
                print(f"[JIT] - Compilation failed: {e}\n")


def create_countdown_program(n: int) -> list[Instruction]:
    """Create a countdown loop - perfect for demonstrating JIT!"""
    return [
        # loop start (PC 0)
        Instruction(OpCode.LOAD_LOCAL, (0,)),      # load counter
        Instruction(OpCode.DUP, ()),                # duplicate for test
        Instruction(OpCode.JUMP_IF_ZERO, (7,)),     # exit if zero (was 8, should be 7)
        # loop body
        Instruction(OpCode.PUSH, (1,)),             # push 1
        Instruction(OpCode.SUB, ()),                # counter - 1
        Instruction(OpCode.STORE_LOCAL, (0,)),      # store back (was duplicated, now direct)
        Instruction(OpCode.JUMP, (0,)),             # jump to start
        # after loop (PC 7)
        Instruction(OpCode.HALT, ())
    ]


def create_sum_program(n: int) -> list[Instruction]:
    """Sum from 1 to n - another great JIT example"""
    return [
        # Initialise: counter=n (local 0), sum=0 (local 1)
        Instruction(OpCode.PUSH, (0,)),
        Instruction(OpCode.STORE_LOCAL, (1,)),      # sum = 0
        
        # loop start (PC 2)
        Instruction(OpCode.LOAD_LOCAL, (0,)),       # load counter
        Instruction(OpCode.DUP, ()),                # duplicate for test
        Instruction(OpCode.JUMP_IF_ZERO, (14,)),    # exit if zero (skip the JUMP)
        
        # loop body: sum += counter; counter--
        Instruction(OpCode.LOAD_LOCAL, (1,)),       # load sum
        Instruction(OpCode.LOAD_LOCAL, (0,)),       # load counter
        Instruction(OpCode.ADD, ()),                # sum + counter
        Instruction(OpCode.STORE_LOCAL, (1,)),      # store sum
        
        Instruction(OpCode.LOAD_LOCAL, (0,)),       # load counter
        Instruction(OpCode.PUSH, (1,)),             # push 1
        Instruction(OpCode.SUB, ()),                # counter - 1
        Instruction(OpCode.STORE_LOCAL, (0,)),      # store counter
        Instruction(OpCode.JUMP, (2,)),             # jump to loop start (PC 13)
        
        # after loop (PC 14)
        Instruction(OpCode.POP, ()),                # clean up stack
        Instruction(OpCode.LOAD_LOCAL, (1,)),       # load result
        Instruction(OpCode.PRINT, ()),              # print sum
        Instruction(OpCode.HALT, ())
    ]


if __name__ == "__main__":
    print("="*60)
    print("HotspotVM - JIT Compilation Demonstration")
    print("="*60)
    
    # Example 1: Countdown loop (shows JIT compilation)
    print("\n--- Example 1: Countdown Loop (10,000 iterations) ---")
    vm1 = ExecutionEngine(hotspot_threshold=10, verbose=True)
    program1 = create_countdown_program(10_000)
    vm1.locals = [10_000]  # Initialise counter
    vm1.load(program1)
    
    start = time.perf_counter()
    vm1.run()
    elapsed = time.perf_counter() - start
    
    print(f"\nCompleted in {elapsed:.4f}s")
    vm1.stats.show()
    
    # Example 2: Sum calculation (more complex)
    print("\n--- Example 2: Sum 1 to 1000 ---")
    vm2 = ExecutionEngine(hotspot_threshold=10, verbose=True)
    program2 = create_sum_program(1000)
    vm2.locals = [1000, 0]  # counter, sum
    vm2.load(program2)
    
    start = time.perf_counter()
    vm2.run()
    elapsed = time.perf_counter() - start
    
    print(f"\nCompleted in {elapsed:.4f}s")
    vm2.stats.show()
    
    # Example 3: Comparison - with vs without JIT
    print("\n--- Example 3: JIT vs Interpreter Comparison ---")
    iterations = 5000
    
    print(f"\nRunning with JIT (threshold=5)...")
    vm_jit = ExecutionEngine(hotspot_threshold=5, verbose=False)
    program = create_countdown_program(iterations)
    vm_jit.locals = [iterations]
    vm_jit.load(program)
    start = time.perf_counter()
    vm_jit.run()
    jit_time = time.perf_counter() - start
    
    print(f"Running WITHOUT JIT (threshold=999999)...")
    vm_no_jit = ExecutionEngine(hotspot_threshold=999999, verbose=False)
    program = create_countdown_program(iterations)
    vm_no_jit.locals = [iterations]
    vm_no_jit.load(program)
    start = time.perf_counter()
    vm_no_jit.run()
    no_jit_time = time.perf_counter() - start
    
    print(f"\n{'='*60}")
    print("COMPARISON RESULTS")
    print(f"{'='*60}")
    print(f"With JIT:     {jit_time:.4f}s")
    print(f"Without JIT:  {no_jit_time:.4f}s")
    print(f"Speedup:      {no_jit_time/jit_time:.2f}x faster with JIT!")
    print(f"{'='*60}")
