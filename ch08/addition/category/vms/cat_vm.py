"""
Categorical Stack-Oriented Virtual Machine
A stack VM where operations are morphisms in a category

In reality a more decorative implementation of category theory concepts
as compared to earlier vm examples. Not a good idea for actual use to build upon
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum


# TYPE SYSTEM (Objects in Category)

class Type(ABC):
    """Base type (object in category)"""
    pass

@dataclass
class IntType(Type):
    def __repr__(self): return "Int"

@dataclass
class BoolType(Type):
    def __repr__(self): return "Bool"

@dataclass
class StrType(Type):
    def __repr__(self): return "Str"

@dataclass
class UnitType(Type):
    def __repr__(self): return "Unit"

@dataclass
class ProductType(Type):
    left: Type
    right: Type
    def __repr__(self): return f"({self.left} x {self.right})"

@dataclass
class SumType(Type):
    left: Type
    right: Type
    def __repr__(self): return f"({self.left} + {self.right})"

@dataclass
class StackType(Type):
    """Type of the entire stack"""
    types: list[Type]
    def __repr__(self): return f"[{', '.join(map(str, self.types))}]"



# TYPED VALUES

@dataclass
class TypedValue:
    """A value with its type"""
    typ: Type
    value: Any
    
    def __repr__(self):
        return f"{self.value}:{self.typ}"



# INSTRUCTIONS (Morphisms)

class Instruction(ABC):
    """Base instruction - represents a morphism between stack types"""
    
    @abstractmethod
    def execute(self, stack: list[TypedValue]) -> list[TypedValue]:
        """Execute instruction (apply morphism)"""
        pass
    
    @abstractmethod
    def type_transform(self, stack_type: StackType) -> StackType:
        """Type-level transformation"""
        pass


# Stack Manipulation (Structural morphisms)

class Push(Instruction):
    """Push a value onto stack: S -> (a : S)"""
    def __init__(self, value: TypedValue):
        self.value = value
    
    def execute(self, stack):
        return [self.value] + stack
    
    def type_transform(self, st):
        return StackType([self.value.typ] + st.types)
    
    def __repr__(self):
        return f"PUSH {self.value}"

class Dup(Instruction):
    """Duplicate top: (a : S) -> (a : a : S)"""
    def execute(self, stack):
        if not stack:
            raise RuntimeError("Cannot DUP empty stack")
        return [stack[0], stack[0]] + stack[1:]
    
    def type_transform(self, st):
        if not st.types:
            raise TypeError("Cannot DUP empty stack type")
        return StackType([st.types[0], st.types[0]] + st.types[1:])
    
    def __repr__(self):
        return "DUP"

class Drop(Instruction):
    """Drop top: (a : S) -> S"""
    def execute(self, stack):
        if not stack:
            raise RuntimeError("Cannot DROP empty stack")
        return stack[1:]
    
    def type_transform(self, st):
        if not st.types:
            raise TypeError("Cannot DROP empty stack type")
        return StackType(st.types[1:])
    
    def __repr__(self):
        return "DROP"

class Swap(Instruction):
    """Swap top two: (a : b : S) -> (b : a : S)"""
    def execute(self, stack):
        if len(stack) < 2:
            raise RuntimeError("Cannot SWAP with fewer than 2 elements")
        return [stack[1], stack[0]] + stack[2:]
    
    def type_transform(self, st):
        if len(st.types) < 2:
            raise TypeError("Cannot SWAP with fewer than 2 types")
        return StackType([st.types[1], st.types[0]] + st.types[2:])
    
    def __repr__(self):
        return "SWAP"

class Rot(Instruction):
    """Rotate top three: (a : b : c : S) -> (b : c : a : S)"""
    def execute(self, stack):
        if len(stack) < 3:
            raise RuntimeError("Cannot ROT with fewer than 3 elements")
        return [stack[1], stack[2], stack[0]] + stack[3:]
    
    def type_transform(self, st):
        if len(st.types) < 3:
            raise TypeError("Cannot ROT with fewer than 3 types")
        return StackType([st.types[1], st.types[2], st.types[0]] + st.types[3:])
    
    def __repr__(self):
        return "ROT"


# Arithmetic Operations (Endomorphisms on Int)

class Add(Instruction):
    """Addition: (Int : Int : S) -> (Int : S)"""
    def execute(self, stack):
        if len(stack) < 2:
            raise RuntimeError("ADD requires 2 values")
        a, b = stack[0], stack[1]
        if not (isinstance(a.typ, IntType) and isinstance(b.typ, IntType)):
            raise TypeError("ADD requires Int types")
        return [TypedValue(IntType(), a.value + b.value)] + stack[2:]
    
    def type_transform(self, st):
        if len(st.types) < 2:
            raise TypeError("ADD requires 2 types")
        return StackType([IntType()] + st.types[2:])
    
    def __repr__(self):
        return "ADD"

class Sub(Instruction):
    """Subtraction: (Int : Int : S) -> (Int : S)"""
    def execute(self, stack):
        if len(stack) < 2:
            raise RuntimeError("SUB requires 2 values")
        a, b = stack[0], stack[1]
        if not (isinstance(a.typ, IntType) and isinstance(b.typ, IntType)):
            raise TypeError("SUB requires Int types")
        return [TypedValue(IntType(), b.value - a.value)] + stack[2:]
    
    def type_transform(self, st):
        if len(st.types) < 2:
            raise TypeError("SUB requires 2 types")
        return StackType([IntType()] + st.types[2:])
    
    def __repr__(self):
        return "SUB"

class Mul(Instruction):
    """Multiplication: (Int : Int : S) -> (Int : S)"""
    def execute(self, stack):
        if len(stack) < 2:
            raise RuntimeError("MUL requires 2 values")
        a, b = stack[0], stack[1]
        if not (isinstance(a.typ, IntType) and isinstance(b.typ, IntType)):
            raise TypeError("MUL requires Int types")
        return [TypedValue(IntType(), a.value * b.value)] + stack[2:]
    
    def type_transform(self, st):
        if len(st.types) < 2:
            raise TypeError("MUL requires 2 types")
        return StackType([IntType()] + st.types[2:])
    
    def __repr__(self):
        return "MUL"

class Div(Instruction):
    """Division: (Int : Int : S) -> (Int : S)"""
    def execute(self, stack):
        if len(stack) < 2:
            raise RuntimeError("DIV requires 2 values")
        a, b = stack[0], stack[1]
        if not (isinstance(a.typ, IntType) and isinstance(b.typ, IntType)):
            raise TypeError("DIV requires Int types")
        if a.value == 0:
            raise RuntimeError("Division by zero")
        return [TypedValue(IntType(), b.value // a.value)] + stack[2:]
    
    def type_transform(self, st):
        if len(st.types) < 2:
            raise TypeError("DIV requires 2 types")
        return StackType([IntType()] + st.types[2:])
    
    def __repr__(self):
        return "DIV"


# Comparison Operations (Int × Int -> Bool)

class Eq(Instruction):
    """Equality: (Int : Int : S) -> (Bool : S)"""
    def execute(self, stack):
        if len(stack) < 2:
            raise RuntimeError("EQ requires 2 values")
        a, b = stack[0], stack[1]
        return [TypedValue(BoolType(), a.value == b.value)] + stack[2:]
    
    def type_transform(self, st):
        if len(st.types) < 2:
            raise TypeError("EQ requires 2 types")
        return StackType([BoolType()] + st.types[2:])
    
    def __repr__(self):
        return "EQ"

class Lt(Instruction):
    """Less than: (Int : Int : S) -> (Bool : S)"""
    def execute(self, stack):
        if len(stack) < 2:
            raise RuntimeError("LT requires 2 values")
        a, b = stack[0], stack[1]
        if not (isinstance(a.typ, IntType) and isinstance(b.typ, IntType)):
            raise TypeError("LT requires Int types")
        return [TypedValue(BoolType(), b.value < a.value)] + stack[2:]
    
    def type_transform(self, st):
        if len(st.types) < 2:
            raise TypeError("LT requires 2 types")
        return StackType([BoolType()] + st.types[2:])
    
    def __repr__(self):
        return "LT"


# Product Operations (Categorical Products)

class Pair(Instruction):
    """Create pair: (a : b : S) -> ((a x b) : S)"""
    def execute(self, stack):
        if len(stack) < 2:
            raise RuntimeError("PAIR requires 2 values")
        a, b = stack[0], stack[1]
        prod_type = ProductType(b.typ, a.typ)
        return [TypedValue(prod_type, (b.value, a.value))] + stack[2:]
    
    def type_transform(self, st):
        if len(st.types) < 2:
            raise TypeError("PAIR requires 2 types")
        return StackType([ProductType(st.types[1], st.types[0])] + st.types[2:])
    
    def __repr__(self):
        return "PAIR"

class Fst(Instruction):
    """First projection: ((a x b) : S) -> (a : S)"""
    def execute(self, stack):
        if not stack:
            raise RuntimeError("FST requires 1 value")
        val = stack[0]
        if not isinstance(val.typ, ProductType):
            raise TypeError("FST requires Product type")
        return [TypedValue(val.typ.left, val.value[0])] + stack[1:]
    
    def type_transform(self, st):
        if not st.types or not isinstance(st.types[0], ProductType):
            raise TypeError("FST requires Product type")
        return StackType([st.types[0].left] + st.types[1:])
    
    def __repr__(self):
        return "FST"

class Snd(Instruction):
    """Second projection: ((a x b) : S) -> (b : S)"""
    def execute(self, stack):
        if not stack:
            raise RuntimeError("SND requires 1 value")
        val = stack[0]
        if not isinstance(val.typ, ProductType):
            raise TypeError("SND requires Product type")
        return [TypedValue(val.typ.right, val.value[1])] + stack[1:]
    
    def type_transform(self, st):
        if not st.types or not isinstance(st.types[0], ProductType):
            raise TypeError("SND requires Product type")
        return StackType([st.types[0].right] + st.types[1:])
    
    def __repr__(self):
        return "SND"


# Sum Operations (Categorical Coproducts)

class InL(Instruction):
    """Left injection: (a : S) -> ((a + b) : S)"""
    def __init__(self, right_type: Type):
        self.right_type = right_type
    
    def execute(self, stack):
        if not stack:
            raise RuntimeError("INL requires 1 value")
        val = stack[0]
        sum_type = SumType(val.typ, self.right_type)
        return [TypedValue(sum_type, ('left', val.value))] + stack[1:]
    
    def type_transform(self, st):
        if not st.types:
            raise TypeError("INL requires 1 type")
        return StackType([SumType(st.types[0], self.right_type)] + st.types[1:])
    
    def __repr__(self):
        return f"INL[{self.right_type}]"

class InR(Instruction):
    """Right injection: (b : S) -> ((a + b) : S)"""
    def __init__(self, left_type: Type):
        self.left_type = left_type
    
    def execute(self, stack):
        if not stack:
            raise RuntimeError("INR requires 1 value")
        val = stack[0]
        sum_type = SumType(self.left_type, val.typ)
        return [TypedValue(sum_type, ('right', val.value))] + stack[1:]
    
    def type_transform(self, st):
        if not st.types:
            raise TypeError("INR requires 1 type")
        return StackType([SumType(self.left_type, st.types[0])] + st.types[1:])
    
    def __repr__(self):
        return f"INR[{self.left_type}]"

class Case(Instruction):
    """Case analysis: ((a + b) : S) -> ? (branches handle continuation)"""
    def __init__(self, left_prog: list[Instruction], right_prog: list[Instruction]):
        self.left_prog = left_prog
        self.right_prog = right_prog
    
    def execute(self, stack):
        if not stack:
            raise RuntimeError("CASE requires 1 value")
        val = stack[0]
        if not isinstance(val.typ, SumType):
            raise TypeError("CASE requires Sum type")
        
        tag, data = val.value
        rest = stack[1:]
        
        if tag == 'left':
            new_stack = [TypedValue(val.typ.left, data)] + rest
            return VM.execute_program(self.left_prog, new_stack)
        else:
            new_stack = [TypedValue(val.typ.right, data)] + rest
            return VM.execute_program(self.right_prog, new_stack)
    
    def type_transform(self, st):
        # Simplified - would need full type inference
        return st
    
    def __repr__(self):
        return f"CASE"


# Control Flow

class Quote(Instruction):
    """Quote a program (creates a function value)"""
    def __init__(self, program: list[Instruction]):
        self.program = program
    
    def execute(self, stack):
        # Push the quoted program as data
        return [TypedValue(StrType(), f"<quoted: {len(self.program)} instrs>")] + stack
    
    def type_transform(self, st):
        return st  # Simplified
    
    def __repr__(self):
        return f"QUOTE[{len(self.program)}]"

class Call(Instruction):
    """Call a quoted program"""
    def __init__(self, program: list[Instruction]):
        self.program = program
    
    def execute(self, stack):
        return VM.execute_program(self.program, stack)
    
    def type_transform(self, st):
        return st  # Would need proper inference
    
    def __repr__(self):
        return f"CALL"



# CAT VIRTUAL MACHINE

class VM:
    """Categorical Stack VM"""
    
    def __init__(self):
        self.stack: list[TypedValue] = []
        self.trace: bool = False
    
    def push(self, typ: Type, value: Any):
        """Push a typed value"""
        self.stack = [TypedValue(typ, value)] + self.stack
    
    def execute(self, instr: Instruction):
        """Execute single instruction"""
        if self.trace:
            instr_str = str(instr).ljust(20)
            print(f"  {instr_str} | Stack: {self.format_stack()}")
        self.stack = instr.execute(self.stack)
    
    def run(self, program: list[Instruction]):
        """Run a program"""
        for instr in program:
            self.execute(instr)
    
    @staticmethod
    def execute_program(program: list[Instruction], stack: list[TypedValue]) -> list[TypedValue]:
        """Execute program on given stack (static method for CASE)"""
        for instr in program:
            stack = instr.execute(stack)
        return stack
    
    def format_stack(self) -> str:
        """Format stack for display"""
        if not self.stack:
            return "[]"
        return f"[{', '.join(str(v) for v in self.stack)}]"
    
    def __repr__(self):
        return f"VM(stack={self.format_stack()})"




# EXAMPLES & TESTS

def example_basic_arithmetic():
    """Basic arithmetic operations"""
    print("\n" + "-"*70)
    print("EXAMPLE: Basic Arithmetic")
    print("-"*70)
    
    vm = VM()
    vm.trace = True
    
    # Compute: (3 + 4) * 2
    program = [
        Push(TypedValue(IntType(), 3)),
        Push(TypedValue(IntType(), 4)),
        Add(),
        Push(TypedValue(IntType(), 2)),
        Mul(),
    ]
    
    print("\nProgram: (3 + 4) * 2")
    print("-" * 70)
    vm.run(program)
    print("-" * 70)
    print(f"Result: {vm.stack[0] if vm.stack else 'empty'}")
    assert vm.stack[0].value == 14

def example_stack_manipulation():
    """Stack manipulation operations"""
    print("\n" + "-"*70)
    print("EXAMPLE: Stack Manipulation")
    print("-"*70)
    
    vm = VM()
    vm.trace = True
    
    # DUP, SWAP, ROT demo
    program = [
        Push(TypedValue(IntType(), 1)),
        Push(TypedValue(IntType(), 2)),
        Push(TypedValue(IntType(), 3)),
        Dup(),     # [3, 3, 2, 1]
        Rot(),     # [2, 1, 3, 3]
        Swap(),    # [1, 2, 3, 3]
    ]
    
    print("\nProgram: Push 1,2,3 then DUP, ROT, SWAP")
    print("-" * 70)
    vm.run(program)
    print("-" * 70)
    print(f"Final stack: {vm.format_stack()}")

def example_products():
    """Categorical products"""
    print("\n" + "-"*70)
    print("EXAMPLE: Categorical Products (Pairs)")
    print("-"*70)
    
    vm = VM()
    vm.trace = True
    
    # Create a pair and project
    program = [
        Push(TypedValue(IntType(), 42)),
        Push(TypedValue(IntType(), 17)),
        Pair(),    # Create (42, 17)
        Dup(),     # Duplicate the pair
        Fst(),     # Project first: 42
        Swap(),    # Swap to get pair back on top
        Snd(),     # Project second: 17
    ]
    
    print("\nProgram: Create pair (42, 17) and project both components")
    print("-" * 70)
    vm.run(program)
    print("-" * 70)
    print(f"Final stack: {vm.format_stack()}")

def example_sums():
    """Categorical sums (coproducts)"""
    print("\n" + "-"*70)
    print("EXAMPLE: Categorical Sums (Either)")
    print("-"*70)
    
    # Test left injection
    vm1 = VM()
    vm1.trace = True
    
    program1 = [
        Push(TypedValue(IntType(), 42)),
        InL(BoolType()),  # Left injection into (Int + Bool)
        Case(
            # Left branch: double it
            [Push(TypedValue(IntType(), 2)), Mul()],
            # Right branch: convert true->1, false->0
            [Drop(), Push(TypedValue(IntType(), 0))]
        )
    ]
    
    print("\nProgram 1: Left injection (Int + Bool) with Int=42")
    print("-" * 70)
    vm1.run(program1)
    print("-" * 70)
    print(f"Result: {vm1.stack[0]}")
    
    # Test right injection
    vm2 = VM()
    vm2.trace = True
    
    program2 = [
        Push(TypedValue(BoolType(), True)),
        InR(IntType()),  # Right injection into (Int + Bool)
        Case(
            # Left branch: double it
            [Push(TypedValue(IntType(), 2)), Mul()],
            # Right branch: convert bool to int
            [Drop(), Push(TypedValue(IntType(), 1))]
        )
    ]
    
    print("\nProgram 2: Right injection (Int + Bool) with Bool=True")
    print("-" * 70)
    vm2.run(program2)
    print("-" * 70)
    print(f"Result: {vm2.stack[0]}")

def example_factorial():
    """Factorial using categorical primitives"""
    print("\n" + "-"*70)
    print("EXAMPLE: Factorial (Iterative)")
    print("-"*70)
    
    def factorial_program(n: int) -> list[Instruction]:
        """Generate factorial program for n"""
        # Simple approach: compute n * (n-1) * (n-2) * ... * 1
        if n == 0 or n == 1:
            return [Push(TypedValue(IntType(), 1))]
        
        # Start by pushing all numbers from n down to 1
        program = []
        for i in range(n, 0, -1):
            program.append(Push(TypedValue(IntType(), i)))
        
        # Now multiply them all together (n-1 multiplications)
        for _ in range(n - 1):
            program.append(Mul())
        
        return program
    
    vm = VM()
    vm.trace = False  # Too verbose for factorial
    
    for n in [5, 6, 7]:
        vm.stack = []
        program = factorial_program(n)
        print(f"\nComputing {n}!")
        vm.run(program)
        result = vm.stack[0].value
        expected = 1
        for i in range(1, n + 1):
            expected *= i
        print(f"  Result: {result}")
        print(f"  Expected: {expected}")
        print(f"  Correct: {result == expected}")
        assert result == expected

def example_comparison_and_logic():
    """Comparison operations"""
    print("\n" + "-"*70)
    print("EXAMPLE: Comparison Operations")
    print("-"*70)
    
    vm = VM()
    vm.trace = True
    
    # Test: is 5 < 10?
    program = [
        Push(TypedValue(IntType(), 5)),
        Push(TypedValue(IntType(), 10)),
        Lt(),
    ]
    
    print("\nProgram: 5 < 10")
    print("-" * 70)
    vm.run(program)
    print("-" * 70)
    print(f"Result: {vm.stack[0]}")
    assert vm.stack[0].value == True

def run_all_tests():
    """Run all examples"""
    print("\n" + "-"*70)
    print("CATEGORICAL STACK VM - DEMONSTRATION\n")
    print("A stack-based VM where operations are morphisms in a category")
    print("- Types are objects")
    print("- Instructions are arrows (morphisms)")
    print("- Composition is instruction sequencing")
    print("- Products and Sums are categorical constructs")
    
    example_basic_arithmetic()
    example_stack_manipulation()
    example_products()
    example_sums()
    example_comparison_and_logic()
    example_factorial()
    

    print("\n\nALL TESTS PASSED!\n")

if __name__ == "__main__":
    run_all_tests()
