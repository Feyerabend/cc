from hypothesis import given, strategies as st
from typing import List, Tuple, Union, Optional, Dict, Any
import unittest
import math
from enum import Enum
from dataclasses import dataclass

# Define opcodes as an enum for better type safety
class OpCode(Enum):
    PUSH = 'PUSH'   # Push a value onto the stack
    ADD = 'ADD'     # Add top two stack values
    SUB = 'SUB'     # Subtract top two stack values
    MUL = 'MUL'     # Multiply top two stack values
    DIV = 'DIV'     # Divide top two stack values
    MOD = 'MOD'     # Modulo top two stack values 
    POW = 'POW'     # Power of top two stack values
    SQRT = 'SQRT'   # Square root of top stack value
    DUP = 'DUP'     # Duplicate top of stack
    SWAP = 'SWAP'   # Swap top two elements
    ROT = 'ROT'     # Rotate top 3: a b c -> b c a
    DROP = 'DROP'   # Remove top element
    EQ = 'EQ'       # Equal comparison
    LT = 'LT'       # Less than
    GT = 'GT'       # Greater than
    AND = 'AND'     # Logical AND
    OR = 'OR'       # Logical OR
    NOT = 'NOT'     # Logical NOT
    JMP = 'JMP'     # Unconditional jump
    JZ = 'JZ'       # Jump if zero
    JNZ = 'JNZ'     # Jump if not zero
    CALL = 'CALL'   # Call subroutine
    RET = 'RET'     # Return from subroutine
    HALT = 'HALT'   # Halt execution
    NOP = 'NOP'     # No operation

# Instruction types
Instruction = Union[
    OpCode,                    # Simple opcodes
    Tuple[OpCode, float],      # PUSH with value
    Tuple[OpCode, int],        # Jump instructions with address
    Tuple[OpCode, str]         # CALL with label
]

@dataclass
class VMState:
    stack: List[float]
    pc: int
    call_stack: List[int]
    halted: bool
    instruction_count: int

class VMError(Exception):
    pass

class StackUnderflowError(VMError):
    pass

class DivisionByZeroError(VMError):
    pass

class InvalidJumpError(VMError):
    pass

class InvalidInstructionError(VMError):
    pass

class EnhancedVM:
    def __init__(self, max_instructions: int = 10000, debug: bool = False):
        self.stack: List[float] = []
        self.pc: int = 0
        self.call_stack: List[int] = []
        self.halted: bool = False
        self.instruction_count: int = 0
        self.max_instructions = max_instructions
        self.debug = debug
        self.labels: Dict[str, int] = {}  # For named jumps/calls
        
    def reset(self):
        self.stack = []
        self.pc = 0
        self.call_stack = []
        self.halted = False
        self.instruction_count = 0
        self.labels = {}
        
    def get_state(self) -> VMState:
        return VMState(
            stack=self.stack.copy(),
            pc=self.pc,
            call_stack=self.call_stack.copy(),
            halted=self.halted,
            instruction_count=self.instruction_count
        )
        
    def push(self, value: float):
        self.stack.append(value)
        
    def pop(self) -> float:
        if not self.stack:
            raise StackUnderflowError(f"Stack underflow at PC {self.pc}")
        return self.stack.pop()
        
    def peek(self, depth: int = 0) -> float:
        if len(self.stack) <= depth:
            raise StackUnderflowError(f"Stack underflow (peek depth {depth}) at PC {self.pc}")
        return self.stack[-(depth + 1)]
        
    def stack_size(self) -> int:
        return len(self.stack)
        
    def preprocess_program(self, program: List[Instruction]):
        self.labels = {}
        cleaned_program = []
        
        for i, instr in enumerate(program):
            # Handle label definitions (strings that end with ':')
            if isinstance(instr, str) and instr.endswith(':'):
                label_name = instr[:-1]
                self.labels[label_name] = len(cleaned_program)
            else:
                cleaned_program.append(instr)
                
        return cleaned_program
        
    def execute_instruction(self, instr: Instruction, program: List[Instruction]) -> bool:
        self.instruction_count += 1
        
        if self.instruction_count > self.max_instructions:
            raise VMError(f"Execution limit exceeded ({self.max_instructions} instructions)")
            
        if self.debug:
            print(f"PC: {self.pc:3d}, Stack: {self.stack}, Instr: {instr}")
            
        # Handle tuple instructions
        if isinstance(instr, tuple):
            opcode, operand = instr
        else:
            opcode = instr
            operand = None
            
        # Arithmetic operations
        if opcode == OpCode.PUSH:
            self.push(operand)
        elif opcode == OpCode.ADD:
            b, a = self.pop(), self.pop()
            self.push(a + b)
        elif opcode == OpCode.SUB:
            b, a = self.pop(), self.pop()
            self.push(a - b)
        elif opcode == OpCode.MUL:
            b, a = self.pop(), self.pop()
            self.push(a * b)
        elif opcode == OpCode.DIV:
            b, a = self.pop(), self.pop()
            if b == 0:
                raise DivisionByZeroError(f"Division by zero at PC {self.pc}")
            self.push(a / b)
        elif opcode == OpCode.MOD:
            b, a = self.pop(), self.pop()
            if b == 0:
                raise DivisionByZeroError(f"Modulo by zero at PC {self.pc}")
            self.push(a % b)
        elif opcode == OpCode.POW:
            b, a = self.pop(), self.pop()
            self.push(a ** b)
        elif opcode == OpCode.SQRT:
            a = self.pop()
            if a < 0:
                raise VMError(f"Square root of negative number at PC {self.pc}")
            self.push(math.sqrt(a))
            
        # Stack manipulation
        elif opcode == OpCode.DUP:
            self.push(self.peek())
        elif opcode == OpCode.SWAP:
            b, a = self.pop(), self.pop()
            self.push(b)
            self.push(a)
        elif opcode == OpCode.ROT:
            c, b, a = self.pop(), self.pop(), self.pop()
            self.push(b)
            self.push(c)
            self.push(a)
        elif opcode == OpCode.DROP:
            self.pop()
            
        # Comparison operations
        elif opcode == OpCode.EQ:
            b, a = self.pop(), self.pop()
            self.push(1.0 if a == b else 0.0)
        elif opcode == OpCode.LT:
            b, a = self.pop(), self.pop()
            self.push(1.0 if a < b else 0.0)
        elif opcode == OpCode.GT:
            b, a = self.pop(), self.pop()
            self.push(1.0 if a > b else 0.0)
            
        # Logical operations
        elif opcode == OpCode.AND:
            b, a = self.pop(), self.pop()
            self.push(1.0 if (a != 0 and b != 0) else 0.0)
        elif opcode == OpCode.OR:
            b, a = self.pop(), self.pop()
            self.push(1.0 if (a != 0 or b != 0) else 0.0)
        elif opcode == OpCode.NOT:
            a = self.pop()
            self.push(1.0 if a == 0 else 0.0)
            
        # Control flow
        elif opcode == OpCode.JMP:
            target = operand if isinstance(operand, int) else self.labels.get(operand, -1)
            if target < 0 or target >= len(program):
                raise InvalidJumpError(f"Invalid jump target {target} at PC {self.pc}")
            self.pc = target - 1  # -1 because pc will be incremented
        elif opcode == OpCode.JZ:
            condition = self.pop()
            if condition == 0:
                target = operand if isinstance(operand, int) else self.labels.get(operand, -1)
                if target < 0 or target >= len(program):
                    raise InvalidJumpError(f"Invalid jump target {target} at PC {self.pc}")
                self.pc = target - 1
        elif opcode == OpCode.JNZ:
            condition = self.pop()
            if condition != 0:
                target = operand if isinstance(operand, int) else self.labels.get(operand, -1)
                if target < 0 or target >= len(program):
                    raise InvalidJumpError(f"Invalid jump target {target} at PC {self.pc}")
                self.pc = target - 1
        elif opcode == OpCode.CALL:
            # FIXED: Save the address of the NEXT instruction (pc + 1)
            self.call_stack.append(self.pc + 1)
            target = operand if isinstance(operand, int) else self.labels.get(operand, -1)
            if target < 0 or target >= len(program):
                raise InvalidJumpError(f"Invalid call target {target} at PC {self.pc}")
            self.pc = target - 1  # -1 because pc will be incremented
        elif opcode == OpCode.RET:
            if not self.call_stack:
                raise VMError(f"Return without call at PC {self.pc}")
            # FIXED: Set pc to the saved return address - 1 (since pc will be incremented)
            self.pc = self.call_stack.pop() - 1
            
        # Control
        elif opcode == OpCode.HALT:
            self.halted = True
            return True
        elif opcode == OpCode.NOP:
            pass  # Do nothing
        else:
            raise InvalidInstructionError(f"Unknown instruction: {instr} at PC {self.pc}")
            
        return False
        
    def run(self, program: List[Instruction]) -> Optional[float]:
        self.reset()
        cleaned_program = self.preprocess_program(program)
        
        while self.pc < len(cleaned_program) and not self.halted:
            should_halt = self.execute_instruction(cleaned_program[self.pc], cleaned_program)
            if should_halt:
                break
            self.pc += 1
            
        return self.stack[-1] if self.stack else None


number_strategy = st.integers(min_value=-50, max_value=50).map(float)
small_positive_strategy = st.integers(min_value=1, max_value=10).map(float)

@st.composite
def simple_rpn_strategy(draw):
    ops = [OpCode.ADD, OpCode.SUB, OpCode.MUL]
    
    def generate_expr() -> List[Instruction]:
        if draw(st.booleans()):
            return [(OpCode.PUSH, draw(number_strategy))]
        else:
            expr1 = generate_expr()
            expr2 = generate_expr()
            op = draw(st.sampled_from(ops))
            return expr1 + expr2 + [op]
    
    return generate_expr() + [OpCode.HALT]

@st.composite
def stack_manipulation_strategy(draw):
    program = [(OpCode.PUSH, draw(number_strategy))]
    
    for _ in range(draw(st.integers(min_value=0, max_value=3))):
        program.append((OpCode.PUSH, draw(number_strategy)))
        
    # Add some stack operations
    ops = [OpCode.DUP, OpCode.SWAP, OpCode.ADD, OpCode.SUB]
    for _ in range(draw(st.integers(min_value=1, max_value=2))):
        if len([i for i in program if isinstance(i, tuple) and i[0] == OpCode.PUSH]) >= 2:
            program.append(draw(st.sampled_from(ops)))
            
    program.append(OpCode.HALT)
    return program

# Unit tests using unittest
class TestEnhancedVM(unittest.TestCase):
    
    def setUp(self):
        self.vm = EnhancedVM()
    
    def test_basic_push_pop(self):
        self.vm.push(42.0)
        self.assertEqual(self.vm.pop(), 42.0)
        
    def test_arithmetic_operations(self):
        program = [
            (OpCode.PUSH, 10.0),
            (OpCode.PUSH, 5.0),
            OpCode.ADD,
            OpCode.HALT
        ]
        result = self.vm.run(program)
        self.assertEqual(result, 15.0)
        
    def test_stack_underflow(self):
        with self.assertRaises(StackUnderflowError):
            self.vm.run([OpCode.ADD, OpCode.HALT])
            
    def test_division_by_zero(self):
        with self.assertRaises(DivisionByZeroError):
            self.vm.run([
                (OpCode.PUSH, 5.0),
                (OpCode.PUSH, 0.0),
                OpCode.DIV,
                OpCode.HALT
            ])
    
    def test_control_flow(self):
        program = [
            (OpCode.PUSH, 10.0),
            (OpCode.JMP, 4),
            (OpCode.PUSH, 20.0),  # Should be skipped
            OpCode.HALT,
            (OpCode.PUSH, 30.0),  # Jump target
            OpCode.HALT
        ]
        
        result = self.vm.run(program)
        self.assertEqual(len(self.vm.stack), 2)
        self.assertEqual(self.vm.stack, [10.0, 30.0])
    
    def test_subroutines(self):
        # Program that calls a subroutine to square a number
        program = [
            (OpCode.PUSH, 5.0),    # 0: Push 5
            (OpCode.CALL, 5),      # 1: Call square subroutine at index 5
            OpCode.HALT,           # 2: Halt
            # Skip instructions (indices 3-4)
            OpCode.NOP,            # 3: No operation
            OpCode.NOP,            # 4: No operation
            # Subroutine starts here (index 5)
            OpCode.DUP,            # 5: Duplicate top of stack  
            OpCode.MUL,            # 6: Multiply (square)
            OpCode.RET             # 7: Return
        ]
        
        result = self.vm.run(program)
        self.assertEqual(result, 25.0)
    
    def test_comparison_operations(self):
        # Test equality
        program = [
            (OpCode.PUSH, 5.0),
            (OpCode.PUSH, 5.0),
            OpCode.EQ,
            OpCode.HALT
        ]
        
        result = self.vm.run(program)
        self.assertEqual(result, 1.0)  # True
        
        # Test less than
        self.vm.reset()
        program = [
            (OpCode.PUSH, 3.0),
            (OpCode.PUSH, 7.0),
            OpCode.LT,
            OpCode.HALT
        ]
        
        result = self.vm.run(program)
        self.assertEqual(result, 1.0)  # True

# usage
if __name__ == "__main__":
    # Example 1: Basic arithmetic
    vm = EnhancedVM(debug=True)
    program = [
        (OpCode.PUSH, 10.0),
        (OpCode.PUSH, 5.0),
        OpCode.ADD,
        (OpCode.PUSH, 2.0),
        OpCode.MUL,
        OpCode.HALT
    ]
    
    print("Example 1: (10 + 5) * 2")
    result = vm.run(program)
    print(f"Result: {result}")
    print()
    
    # Example 2: Simple counting loop (count down from 5 to 1)
    vm = EnhancedVM(debug=True)
    program = [
        (OpCode.PUSH, 5.0),    # 0: counter = 5
        # Loop: while counter > 0, print and decrement
        OpCode.DUP,            # 1: Stack: [counter, counter]
        (OpCode.PUSH, 0.0),    # 2: Stack: [counter, counter, 0]
        OpCode.GT,             # 3: Stack: [counter, (counter > 0)]
        (OpCode.JZ, 8),        # 4: If counter <= 0, jump to HALT (index 8)
        # Decrement counter
        (OpCode.PUSH, 1.0),    # 5: Stack: [counter, 1]
        OpCode.SUB,            # 6: Stack: [counter - 1]
        (OpCode.JMP, 1),       # 7: Jump back to loop start
        # End
        OpCode.HALT            # 8: counter should be 0
    ]
    
    print("Example 2: Count down from 5 to 0")
    result = vm.run(program)
    print(f"Final counter value: {result}")
    print()
    
    # Example 3: Manual factorial calculation (no loops)
    vm = EnhancedVM(debug=False)
    program = [
        (OpCode.PUSH, 1.0),    # Start with 1
        (OpCode.PUSH, 2.0),    # Multiply by 2
        OpCode.MUL,            # 1 * 2 = 2
        (OpCode.PUSH, 3.0),    # Multiply by 3  
        OpCode.MUL,            # 2 * 3 = 6
        (OpCode.PUSH, 4.0),    # Multiply by 4
        OpCode.MUL,            # 6 * 4 = 24
        OpCode.HALT            # 4! = 24
    ]
    
    print("Example 3: Manual calculation of 4! = 4 x 3 x 2 x 1")
    result = vm.run(program)
    print(f"4! = {result}")
    print()
    
    # Run unittest suite
    print("\nRunning unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)

# Property-based tests (keeping these as standalone functions for Hypothesis)
@given(simple_rpn_strategy())
def test_hypothesis_basic_arithmetic(program):
    """Property-based test for basic arithmetic operations."""
    vm = EnhancedVM()
    try:
        result = vm.run(program)
        assert result is not None
        assert isinstance(result, float)
    except (StackUnderflowError, DivisionByZeroError):
        # These are expected for some generated programs
        pass

@given(stack_manipulation_strategy())
def test_hypothesis_stack_operations(program):
    """Property-based test for stack manipulation operations."""
    vm = EnhancedVM()
    try:
        result = vm.run(program)
        # Should not crash
        assert vm.get_state().halted
    except StackUnderflowError:
        # Expected for some operations
        pass

