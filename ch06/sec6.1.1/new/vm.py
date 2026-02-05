"""
Virtual Machine with Design-by-Contract Verification
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, List, Dict
from abc import ABC, abstractmethod


# Abstract Value System for Static Analysis

class AbstractValue(ABC):    
    @abstractmethod
    def __repr__(self):
        pass
    
    def is_compatible(self, other: 'AbstractValue') -> bool:
        return type(self) == type(other)


class AnyValue(AbstractValue):
    def __repr__(self):
        return "?"


class IntValue(AbstractValue):
    def __init__(self, value: Optional[int] = None):
        self.value = value
    
    def __repr__(self):
        return f"int({self.value})" if self.value is not None else "int"


class ListValue(AbstractValue):
    def __init__(self, element_type: Optional[AbstractValue] = None):
        self.element_type = element_type or AnyValue()
    
    def __repr__(self):
        return f"list[{self.element_type}]"


class BoolValue(AbstractValue):
    def __init__(self, value: Optional[bool] = None):
        self.value = value
    
    def __repr__(self):
        return f"bool({self.value})" if self.value is not None else "bool"


# VM State (for both concrete execution and abstract analysis)

@dataclass
class VMState:
    stack: List[Any] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    
    def clone(self) -> 'VMState':
        return VMState(
            stack=self.stack.copy(),
            memory=self.memory.copy()
        )
    
    def __repr__(self):
        return f"VMState(stack={self.stack}, memory={self.memory})"


# Instruction Specification

@dataclass
class InstructionSpec:
    name: str
    
    # Precondition: checks before execution
    precondition: Callable[[VMState, tuple], bool]
    
    # Concrete execution: how to execute on concrete values
    execute: Callable[[VMState, tuple], None]
    
    # Abstract execution: how to transform abstract state
    abstract_execute: Callable[[VMState, tuple], None]
    
    # Postcondition: checks after execution
    postcondition: Callable[[VMState, tuple], bool]
    
    # Human-readable description
    description: str = ""
    
    def verify_and_execute(self, state: VMState, args: tuple) -> None:
        if not self.precondition(state, args):
            raise ContractViolation(
                f"Precondition failed for {self.name}{args}\n"
                f"State: {state}"
            )
        
        self.execute(state, args)
        
        if not self.postcondition(state, args):
            raise ContractViolation(
                f"Postcondition failed for {self.name}{args}\n"
                f"State: {state}"
            )


class ContractViolation(Exception):
    pass



# Instruction Definitions

def create_instruction_set() -> Dict[str, InstructionSpec]:
    def push_spec():
        return InstructionSpec(
            name="PUSH",
            precondition=lambda state, args: len(args) == 1,
            execute=lambda state, args: state.stack.append(args[0]),
            abstract_execute=lambda state, args: (
                state.stack.append(IntValue(args[0])) if isinstance(args[0], int)
                else state.stack.append(AnyValue())
            ),
            postcondition=lambda state, args: len(state.stack) > 0,
            description="Push a value onto the stack"
        )
    
    def add_spec():
        return InstructionSpec(
            name="ADD",
            precondition=lambda state, args: (
                len(state.stack) >= 2 and
                all(isinstance(x, (int, IntValue)) for x in state.stack[-2:])
            ),
            execute=lambda state, args: (
                state.stack.append(state.stack.pop() + state.stack.pop())
            ),
            abstract_execute=lambda state, args: (
                state.stack.pop(),
                state.stack.pop(),
                state.stack.append(IntValue())
            )[-1],  # Use tuple trick to execute multiple statements
            postcondition=lambda state, args: (
                len(state.stack) > 0 and
                isinstance(state.stack[-1], (int, IntValue))
            ),
            description="Add top two stack values"
        )
    
    def push_list_spec():
        return InstructionSpec(
            name="PUSH_LIST",
            precondition=lambda state, args: True,
            execute=lambda state, args: state.stack.append([]),
            abstract_execute=lambda state, args: state.stack.append(ListValue()),
            postcondition=lambda state, args: isinstance(state.stack[-1], (list, ListValue)),
            description="Push an empty list onto the stack"
        )
    
    def append_spec():
        return InstructionSpec(
            name="APPEND",
            precondition=lambda state, args: (
                len(state.stack) >= 2 and
                isinstance(state.stack[-1], (list, ListValue))
            ),
            execute=lambda state, args: (
                (lambda lst, val: (lst.append(val), state.stack.append(lst)))
                (state.stack.pop(), state.stack.pop())
            ),
            abstract_execute=lambda state, args: (
                state.stack.pop(),  # pop list
                state.stack.pop(),  # pop value
                state.stack.append(ListValue())
            )[-1],
            postcondition=lambda state, args: isinstance(state.stack[-1], (list, ListValue)),
            description="Append value to list (list on top, value below)"
        )
    
    def store_spec():
        return InstructionSpec(
            name="STORE",
            precondition=lambda state, args: len(args) == 1 and len(state.stack) > 0,
            execute=lambda state, args: (
                state.memory.__setitem__(args[0], state.stack.pop())
            ),
            abstract_execute=lambda state, args: (
                state.memory.__setitem__(args[0], state.stack.pop())
            ),
            postcondition=lambda state, args: args[0] in state.memory,
            description="Store top of stack in memory"
        )
    
    def load_spec():
        return InstructionSpec(
            name="LOAD",
            precondition=lambda state, args: len(args) == 1 and args[0] in state.memory,
            execute=lambda state, args: state.stack.append(state.memory[args[0]]),
            abstract_execute=lambda state, args: state.stack.append(state.memory[args[0]]),
            postcondition=lambda state, args: len(state.stack) > 0,
            description="Load value from memory onto stack"
        )
    
    return {
        'PUSH': push_spec(),
        'ADD': add_spec(),
        'PUSH_LIST': push_list_spec(),
        'APPEND': append_spec(),
        'STORE': store_spec(),
        'LOAD': load_spec(),
    }



# Static Analyser

class StaticAnalyzer:
    def __init__(self, instructions: Dict[str, InstructionSpec]):
        self.instructions = instructions
    
    def analyze(self, program: List[tuple], initial_state: VMState) -> bool:
        print("\nSTATIC ANALYSIS (Abstract Interpretation)\n")
        
        # Create abstract version of initial state
        abstract_state = self._abstractify_state(initial_state)
        
        for i, instruction in enumerate(program):
            opcode = instruction[0]
            args = instruction[1:] if len(instruction) > 1 else ()
            
            print(f"\n[{i}] {opcode}{args}")
            print(f"  Stack: {abstract_state.stack}")
            print(f"  Memory: {abstract_state.memory}")
            
            spec = self.instructions.get(opcode)
            if spec is None:
                raise Exception(f"Unknown instruction: {opcode}")
            
            # Check precondition on abstract state
            try:
                if not spec.precondition(abstract_state, args):
                    raise ContractViolation(
                        f"Static precondition failed at instruction {i}: {opcode}{args}"
                    )
            except (IndexError, KeyError) as e:
                raise ContractViolation(
                    f"Static precondition error at instruction {i}: {opcode}{args}\n"
                    f"Error: {e}"
                )
            
            # Execute abstractly
            spec.abstract_execute(abstract_state, args)
            
            # Check postcondition
            try:
                if not spec.postcondition(abstract_state, args):
                    raise ContractViolation(
                        f"Static postcondition failed at instruction {i}: {opcode}{args}"
                    )
            except (IndexError, KeyError) as e:
                raise ContractViolation(
                    f"Static postcondition error at instruction {i}: {opcode}{args}\n"
                    f"Error: {e}"
                )
        
        print("\nStatic analysis OK\n")
        return True
    
    def _abstractify_state(self, concrete_state: VMState) -> VMState:
        abstract_state = VMState()
        
        # Abstract the stack
        for value in concrete_state.stack:
            abstract_state.stack.append(self._abstractify_value(value))
        
        # Abstract the memory
        for key, value in concrete_state.memory.items():
            abstract_state.memory[key] = self._abstractify_value(value)
        
        return abstract_state
    
    def _abstractify_value(self, value: Any) -> AbstractValue:
        if isinstance(value, int):
            return IntValue(value)
        elif isinstance(value, list):
            return ListValue()
        elif isinstance(value, bool):
            return BoolValue(value)
        else:
            return AnyValue()



# Virtual Machine

class VirtualMachine:
    def __init__(self, instructions: Dict[str, InstructionSpec], 
                 check_contracts: bool = True):
        self.instructions = instructions
        self.check_contracts = check_contracts
        self.state = VMState()
    
    def execute(self, program: List[tuple]) -> VMState:
        print("\nRUNTIME EXECUTION\n")
        
        for i, instruction in enumerate(program):
            opcode = instruction[0]
            args = instruction[1:] if len(instruction) > 1 else ()
            
            print(f"\n[{i}] {opcode}{args}")
            print(f"  Stack before: {self.state.stack}")
            print(f"  Memory before: {self.state.memory}")
            
            spec = self.instructions.get(opcode)
            if spec is None:
                raise Exception(f"Unknown instruction: {opcode}")
            
            if self.check_contracts:
                spec.verify_and_execute(self.state, args)
            else:
                spec.execute(self.state, args)
            
            print(f"  Stack after: {self.state.stack}")
            print(f"  Memory after: {self.state.memory}")
        
        print("\nExecution COMPLETED")
        print(f"Final stack: {self.state.stack}")
        print(f"Final memory: {self.state.memory}\n")
        
        return self.state



# Demos

def demo_correct_program():
    print("\nDEMO 1: Correct Program\n")
    
    program = [
        ('PUSH', 5),          # Stack: [5]
        ('PUSH', 10),         # Stack: [5, 10]
        ('ADD',),             # Stack: [15]
        ('PUSH', 20),         # Stack: [15, 20]
        ('PUSH_LIST',),       # Stack: [15, 20, []]
        ('APPEND',),          # Stack: [15, [20]]  (FIXED!)
        ('STORE', 'result'),  # Stack: [15], Memory: {result: [20]}
    ]
    
    instructions = create_instruction_set()
    
    # Static analysis
    analyzer = StaticAnalyzer(instructions)
    initial_state = VMState()
    analyzer.analyze(program, initial_state)
    
    # Runtime execution
    vm = VirtualMachine(instructions)
    vm.execute(program)

def demo_buggy_program():
    print("\nDEMO 2: Buggy Program (will be caught by static analysis)\n")
    
    program = [
        ('PUSH', 5),
        ('PUSH', 10),
        ('APPEND',),  # BUG: Can't append to an integer!
    ]
    
    instructions = create_instruction_set()
    analyzer = StaticAnalyzer(instructions)
    initial_state = VMState()
    
    try:
        analyzer.analyze(program, initial_state)
    except ContractViolation as e:
        print(f"\nBug caught during static analysis!")
        print(f"Error: {e}")


def demo_with_initial_state():
    print("\n\nDEMO 3: Program with Initial State\n")
    
    program = [
        ('LOAD', 'x'),        # Load x from memory
        ('PUSH', 10),         # Push 10
        ('ADD',),             # Add them
        ('STORE', 'result'),  # Store result
    ]
    
    instructions = create_instruction_set()
    
    # Create initial state with 'x' defined
    initial_state = VMState(memory={'x': 5})
    
    # Static analysis
    analyzer = StaticAnalyzer(instructions)
    analyzer.analyze(program, initial_state)
    
    # Runtime execution
    vm = VirtualMachine(instructions)
    vm.state.memory['x'] = 5
    vm.execute(program)


if __name__ == '__main__':
    demo_correct_program()
    demo_buggy_program()
    demo_with_initial_state()
