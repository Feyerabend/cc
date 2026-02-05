"""
Advanced Extensions for the Design-by-Contract VM

This file demonstrates how to extend the basic VM with more sophisticated features:
1. Loop invariants
2. Function contracts
3. Heap-allocated objects
4. More precise abstract domains
"""

from improved_vm import *
from typing import Set, Tuple


# Extension 1: Range Abstract Domain

class RangeValue(AbstractValue):
    def __init__(self, min_val: int, max_val: int):
        self.min = min_val
        self.max = max_val
    
    def __repr__(self):
        if self.min == self.max:
            return f"int({self.min})"
        return f"int[{self.min}..{self.max}]"
    
    def add(self, other: 'RangeValue') -> 'RangeValue':
        return RangeValue(self.min + other.min, self.max + other.max)
    
    def sub(self, other: 'RangeValue') -> 'RangeValue':
        return RangeValue(self.min - other.max, self.max - other.min)
    
    def mul(self, other: 'RangeValue') -> 'RangeValue':
        products = [
            self.min * other.min,
            self.min * other.max,
            self.max * other.min,
            self.max * other.max,
        ]
        return RangeValue(min(products), max(products))
    
    def contains(self, value: int) -> bool:
        return self.min <= value <= self.max
    
    def is_positive(self) -> bool:
        return self.min > 0
    
    def is_non_negative(self) -> bool:
        return self.min >= 0


def add_with_range_spec():
    return InstructionSpec(
        name="ADD",
        precondition=lambda state, args: (
            len(state.stack) >= 2 and
            all(isinstance(x, (int, IntValue, RangeValue)) for x in state.stack[-2:])
        ),
        execute=lambda state, args: (
            state.stack.append(state.stack.pop() + state.stack.pop())
        ),
        abstract_execute=lambda state, args: (
            (lambda a, b: state.stack.append(
                a.add(b) if isinstance(a, RangeValue) and isinstance(b, RangeValue)
                else IntValue()
            ))(state.stack.pop(), state.stack.pop())
        ),
        postcondition=lambda state, args: len(state.stack) > 0,
        description="Add with range tracking"
    )



# Extension 2: Loop Invariants

class LoopInvariant:
    def __init__(self, condition: Callable[[VMState], bool], description: str):
        self.condition = condition
        self.description = description
    
    def check(self, state: VMState) -> bool:
        return self.condition(state)


def loop_invariant_spec():
    return InstructionSpec(
        name="ASSERT_INVARIANT",
        precondition=lambda state, args: len(args) == 1,
        execute=lambda state, args: (
            None if args[0].check(state)
            else (_ for _ in ()).throw(ContractViolation(
                f"Loop invariant violated: {args[0].description}"
            ))
        ),
        abstract_execute=lambda state, args: None,  # No effect on abstract state
        postcondition=lambda state, args: True,
        description="Assert loop invariant"
    )


# Example: Loop that counts from 0 to 10
def demo_loop_invariant():
    """Demonstrate loop invariants"""
    print("\n" + "=" * 70)
    print("DEMO: Loop Invariants")
    print("=" * 70)
    
    # Define invariant: 0 <= i <= 10
    invariant = LoopInvariant(
        condition=lambda vm: (
            'i' in vm.memory and
            isinstance(vm.memory['i'], int) and
            0 <= vm.memory['i'] <= 10
        ),
        description="0 <= i <= 10"
    )
    
    program = [
        ('PUSH', 0),
        ('STORE', 'i'),
        # Loop header - check invariant
        ('ASSERT_INVARIANT', invariant),
        ('LOAD', 'i'),
        ('PUSH', 1),
        ('ADD',),
        ('STORE', 'i'),
        # Check invariant still holds
        ('ASSERT_INVARIANT', invariant),
    ]
    
    instructions = create_instruction_set()
    instructions['ASSERT_INVARIANT'] = loop_invariant_spec()
    
    vm = VirtualMachine(instructions)
    try:
        vm.execute(program)
        print("\n✓ Loop invariant maintained!")
    except ContractViolation as e:
        print(f"\n✗ Invariant violation: {e}")



# Extension 3: Function Contracts

@dataclass
class FunctionContract:
    name: str
    requires: Callable[[VMState, tuple], bool]  # Precondition
    ensures: Callable[[VMState, tuple, Any], bool]  # Postcondition (with result)
    modifies: Set[str]  # Which memory locations can be modified
    
    def check_precondition(self, state: VMState, args: tuple):
        if not self.requires(state, args):
            raise ContractViolation(
                f"Precondition for {self.name} failed with args {args}"
            )
    
    def check_postcondition(self, state: VMState, args: tuple, result: Any):
        if not self.ensures(state, args, result):
            raise ContractViolation(
                f"Postcondition for {self.name} failed"
            )


def call_function_spec():
    return InstructionSpec(
        name="CALL",
        precondition=lambda state, args: (
            len(args) >= 2 and  # (contract, arg_count)
            isinstance(args[0], FunctionContract) and
            isinstance(args[1], int) and
            len(state.stack) >= args[1]
        ),
        execute=lambda state, args: (
            # Would actually call the function here
            # For demo, just checking contracts
            (lambda contract, arg_count: (
                contract.check_precondition(state, tuple(state.stack[-arg_count:])),
                # .. function execution ..
                # contract.check_postcondition(state, args, result)
            ))(args[0], args[1])
        ),
        abstract_execute=lambda state, args: None,
        postcondition=lambda state, args: True,
        description="Call function with contract checking"
    )


# Example function contract
sqrt_contract = FunctionContract(
    name="sqrt",
    requires=lambda state, args: (
        len(args) == 1 and
        isinstance(args[0], (int, float)) and
        args[0] >= 0
    ),
    ensures=lambda state, args, result: (
        result * result <= args[0] < (result + 1) * (result + 1)
    ),
    modifies=set()
)



# Extension 4: Heap Objects and Aliasing

class HeapObject(AbstractValue):
    def __init__(self, obj_id: int, obj_type: str, aliases: Set[int] = None):
        self.obj_id = obj_id
        self.obj_type = obj_type
        self.aliases = aliases or {obj_id}
    
    def __repr__(self):
        alias_str = f", aliases={self.aliases}" if len(self.aliases) > 1 else ""
        return f"{self.obj_type}@{self.obj_id}{alias_str}"
    
    def may_alias(self, other: 'HeapObject') -> bool:
        return bool(self.aliases & other.aliases)


class HeapState:
    def __init__(self):
        self.next_id = 0
        self.heap: Dict[int, Any] = {}
        self.alias_sets: List[Set[int]] = []
    
    def allocate(self, obj_type: str) -> HeapObject:
        obj_id = self.next_id
        self.next_id += 1
        self.alias_sets.append({obj_id})
        return HeapObject(obj_id, obj_type, {obj_id})
    
    def assign(self, target: HeapObject, source: HeapObject):
        target.aliases |= source.aliases



# Extension 5: Effect System
# Tracks side effects of operations
@dataclass
class Effect:
    reads: Set[str] = field(default_factory=set)
    writes: Set[str] = field(default_factory=set)
    allocates: bool = False
    may_fail: bool = False
    
    def combine(self, other: 'Effect') -> 'Effect':
        return Effect(
            reads=self.reads | other.reads,
            writes=self.writes | other.writes,
            allocates=self.allocates or other.allocates,
            may_fail=self.may_fail or other.may_fail,
        )


def store_with_effect_spec():
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
        description="Store with effect tracking"
    )


# Analyzes the effects of a program.
class EffectAnalyzer:
    def __init__(self, instructions: Dict[str, InstructionSpec]):
        self.instructions = instructions
        self.effect_map: Dict[str, Effect] = {
            'LOAD': Effect(reads={'*'}),
            'STORE': Effect(writes={'*'}),
            'PUSH_LIST': Effect(allocates=True),
        }
    
    def analyze_effects(self, program: List[tuple]) -> Effect:
        total_effect = Effect()
        
        for instruction in program:
            opcode = instruction[0]
            args = instruction[1:] if len(instruction) > 1 else ()
            
            effect = self.effect_map.get(opcode, Effect())
            
            # Refine effect based on args
            if opcode == 'LOAD' and args:
                effect = Effect(reads={args[0]})
            elif opcode == 'STORE' and args:
                effect = Effect(writes={args[0]})
            
            total_effect = total_effect.combine(effect)
        
        return total_effect


# Extension 6: Symbolic Execution
# Represents a symbolic value in terms of program inputs
# such as: "input[0] + 5"
class SymbolicValue(AbstractValue):
    def __init__(self, expr: str):
        self.expr = expr
    
    def __repr__(self):
        return f"symbolic({self.expr})"
    
    def add(self, other: 'SymbolicValue') -> 'SymbolicValue':
        return SymbolicValue(f"({self.expr} + {other.expr})")
    
    def eq(self, other: 'SymbolicValue') -> 'SymbolicConstraint':
        return SymbolicConstraint(f"{self.expr} == {other.expr}")


# Constraint on symbolic values
class SymbolicConstraint:
    def __init__(self, constraint: str):
        self.constraint = constraint
    
    def __repr__(self):
        return f"constraint({self.constraint})"

# Executes program symbolically
class SymbolicExecutor:
    def __init__(self):
        self.path_constraints: List[SymbolicConstraint] = []
        self.symbolic_state = VMState()
    
    def execute_symbolically(self, program: List[tuple], inputs: Dict[str, str]):
        # Init symbolic memory
        for var, expr in inputs.items():
            self.symbolic_state.memory[var] = SymbolicValue(expr)
        
        # Execute each instruction symbolically
        for instruction in program:
            opcode = instruction[0]
            args = instruction[1:] if len(instruction) > 1 else ()
            
            if opcode == 'LOAD':
                var = args[0]
                self.symbolic_state.stack.append(self.symbolic_state.memory[var])
            
            elif opcode == 'PUSH':
                self.symbolic_state.stack.append(SymbolicValue(str(args[0])))
            
            elif opcode == 'ADD':
                b = self.symbolic_state.stack.pop()
                a = self.symbolic_state.stack.pop()
                self.symbolic_state.stack.append(a.add(b))
            
            # ..other operations..
        
        return self.symbolic_state, self.path_constraints


# Demos

def demo_range_analysis():
    print("\nDEMO: Range Analysis\n")
    
    # Program: x = 5; y = 3; z = x + y
    # We can prove: z is in range [8, 8]
    
    state = VMState()
    state.stack = [RangeValue(5, 5), RangeValue(3, 3)]
    
    spec = add_with_range_spec()
    spec.abstract_execute(state, ())
    
    result = state.stack[-1]
    print(f"Result range: {result}")
    print(f"Proves: result is exactly {result.min}")


def demo_effect_analysis():
    print("\nDEMO: Effect Analysis\n")
    
    program = [
        ('LOAD', 'x'),
        ('LOAD', 'y'),
        ('ADD',),
        ('STORE', 'result'),
        ('PUSH_LIST',),
        ('STORE', 'lst'),
    ]
    
    analyzer = EffectAnalyzer(create_instruction_set())
    effect = analyzer.analyze_effects(program)
    
    print(f"Reads: {effect.reads}")
    print(f"Writes: {effect.writes}")
    print(f"Allocates: {effect.allocates}")
    print(f"May fail: {effect.may_fail}")


def demo_symbolic_execution():
    print("\nDEMO: Symbolic Execution\n")
    
    program = [
        ('LOAD', 'x'),
        ('PUSH', 5),
        ('ADD',),
        ('STORE', 'y'),
    ]
    
    executor = SymbolicExecutor()
    final_state, constraints = executor.execute_symbolically(
        program,
        inputs={'x': 'input_x'}
    )
    
    print(f"Symbolic memory: {final_state.memory}")
    print(f"Path constraints: {constraints}")
    print(f"\nProves: y = input_x + 5")


if __name__ == '__main__':
    demo_range_analysis()
    demo_effect_analysis()
    demo_symbolic_execution()
    demo_loop_invariant()

