# Explicit-state CTL model checker: Kripke structures, fixpoint evaluation, caching.
# Two examples: (1) traffic light — simple warm-up; (2) 3-floor elevator.

from collections import defaultdict, deque
from typing import Set, Dict, List, Optional, Union
import time
from dataclasses import dataclass
from abc import ABC, abstractmethod

#  Kripke structure with validation
class KripkeStructure:    
    def __init__(self, name: str = "unnamed"):
        self.name = name
        self.states: Set[str] = set()
        self.transitions: Dict[str, Set[str]] = defaultdict(set)
        self.labels: Dict[str, Set[str]] = defaultdict(set)
        self.atomic_propositions: Set[str] = set()
        self._validated = False
        
    def add_state(self, state: str, props: Optional[List[str]] = None) -> 'KripkeStructure':
        if not isinstance(state, str) or not state.strip():
            raise ValueError(f"State must be non-empty string, got: {state}")
        
        self.states.add(state)
        if props:
            for prop in props:
                if not isinstance(prop, str) or not prop.strip():
                    raise ValueError(f"Proposition must be non-empty string, got: {prop}")
                self.labels[state].add(prop)
                self.atomic_propositions.add(prop)
        return self
    
    def add_transition(self, from_state: str, to_state: str) -> 'KripkeStructure':
        if from_state not in self.states:
            raise ValueError(f"Source state '{from_state}' not found")
        if to_state not in self.states:
            raise ValueError(f"Target state '{to_state}' not found")
        
        self.transitions[from_state].add(to_state)
        return self
    
    def ensure_total_relation(self) -> 'KripkeStructure':
        for state in list(self.states):
            if not self.transitions[state]:
                self.transitions[state].add(state)
                print(f"Warning: Added self-loop to state '{state}' to ensure totality")
        return self
    
    def validate(self) -> bool:
        if not self.states:
            raise ValueError("Kripke structure must have at least one state")
        
        # Check totality
        for state in self.states:
            if not self.transitions[state]:
                raise ValueError(f"State '{state}' has no outgoing transitions. Use ensure_total_relation() first.")
        
        # Check all transitions reference valid states
        for from_state, to_states in self.transitions.items():
            if from_state not in self.states:
                raise ValueError(f"Transition source '{from_state}' not in states")
            for to_state in to_states:
                if to_state not in self.states:
                    raise ValueError(f"Transition target '{to_state}' not in states")
        
        self._validated = True
        return True
    
    def get_successors(self, state: str) -> Set[str]:
        return self.transitions.get(state, set())
    
    def get_predecessors(self, states: Set[str]) -> Set[str]:
        predecessors = set()
        for state in self.states:
            if any(succ in states for succ in self.transitions[state]):
                predecessors.add(state)
        return predecessors
    
    def get_universal_predecessors(self, states: Set[str]) -> Set[str]:
        predecessors = set()
        for state in self.states:
            successors = self.transitions[state]
            if successors and all(succ in states for succ in successors):
                predecessors.add(state)
        return predecessors
    
    def get_strongly_connected_components(self) -> List[Set[str]]:
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = {}
        sccs = []
        
        def strongconnect(state):
            index[state] = index_counter[0]
            lowlinks[state] = index_counter[0]
            index_counter[0] += 1
            stack.append(state)
            on_stack[state] = True
            
            for successor in self.transitions[state]:
                if successor not in index:
                    strongconnect(successor)
                    lowlinks[state] = min(lowlinks[state], lowlinks[successor])
                elif on_stack.get(successor, False):
                    lowlinks[state] = min(lowlinks[state], index[successor])
            
            if lowlinks[state] == index[state]:
                scc = set()
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    scc.add(w)
                    if w == state:
                        break
                sccs.append(scc)
        
        for state in self.states:
            if state not in index:
                strongconnect(state)
        
        return sccs
    
    def __str__(self) -> str:
        lines = [f"Kripke Structure: {self.name}"]
        lines.append(f"States ({len(self.states)}): {sorted(self.states)}")
        lines.append(f"Atomic Propositions: {sorted(self.atomic_propositions)}")
        lines.append("Transitions:")
        for state in sorted(self.states):
            successors = sorted(self.transitions[state])
            props = sorted(self.labels[state])
            lines.append(f"  {state} -> {successors} (labels: {props})")
        return '\n'.join(lines)


#  CTL Formula AST with validation
class CTLFormula(ABC):    
    @abstractmethod
    def validate(self, atomic_props: Set[str]) -> bool:
        pass
    
    @abstractmethod
    def __str__(self) -> str:
        pass
    
    @abstractmethod
    def get_atomic_props(self) -> Set[str]:
        pass

class Atom(CTLFormula):
    def __init__(self, name: str):
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Atomic proposition must be non-empty string, got: {name}")
        self.name = name.strip()
    
    def validate(self, atomic_props: Set[str]) -> bool:
        if self.name not in atomic_props:
            raise ValueError(f"Atomic proposition '{self.name}' not found in model")
        return True
    
    def get_atomic_props(self) -> Set[str]:
        return {self.name}
    
    def __str__(self) -> str:
        return self.name

class UnaryFormula(CTLFormula):
    def __init__(self, operand: CTLFormula):
        if not isinstance(operand, CTLFormula):
            raise TypeError("Operand must be a CTL formula")
        self.operand = operand
    
    def validate(self, atomic_props: Set[str]) -> bool:
        return self.operand.validate(atomic_props)
    
    def get_atomic_props(self) -> Set[str]:
        return self.operand.get_atomic_props()

class BinaryFormula(CTLFormula):
    def __init__(self, left: CTLFormula, right: CTLFormula):
        if not isinstance(left, CTLFormula) or not isinstance(right, CTLFormula):
            raise TypeError("Operands must be CTL formulas")
        self.left = left
        self.right = right
    
    def validate(self, atomic_props: Set[str]) -> bool:
        return self.left.validate(atomic_props) and self.right.validate(atomic_props)
    
    def get_atomic_props(self) -> Set[str]:
        return self.left.get_atomic_props() | self.right.get_atomic_props()

# Boolean operators
class Not(UnaryFormula):
    def __str__(self) -> str:
        return f"¬({self.operand})"

class And(BinaryFormula):
    def __str__(self) -> str:
        return f"({self.left} ∧ {self.right})"

class Or(BinaryFormula):
    def __str__(self) -> str:
        return f"({self.left} ∨ {self.right})"

class Implies(BinaryFormula):
    def __str__(self) -> str:
        return f"({self.left} → {self.right})"

# Temporal operators
class EX(UnaryFormula):
    def __str__(self) -> str:
        return f"EX({self.operand})"

class AX(UnaryFormula):
    def __str__(self) -> str:
        return f"AX({self.operand})"

class EU(BinaryFormula):
    def __str__(self) -> str:
        return f"E[{self.left} U {self.right}]"

class AU(BinaryFormula):
    def __str__(self) -> str:
        return f"A[{self.left} U {self.right}]"

class EG(UnaryFormula):
    def __str__(self) -> str:
        return f"EG({self.operand})"

class AG(UnaryFormula):
    def __str__(self) -> str:
        return f"AG({self.operand})"

class EF(UnaryFormula):
    def __str__(self) -> str:
        return f"EF({self.operand})"

class AF(UnaryFormula):
    def __str__(self) -> str:
        return f"AF({self.operand})"


#  Model Checker with performance tracking
@dataclass
class ModelCheckingResult:
    formula: str
    satisfying_states: Set[str]
    computation_time: float
    iterations: int
    formula_size: int

class CTLModelChecker:    
    def __init__(self, kripke: KripkeStructure):
        if not kripke._validated:
            kripke.validate()
        self.kripke = kripke
        self.cache: Dict[str, Set[str]] = {}
        
    def check_formula(self, formula: CTLFormula, use_cache: bool = True) -> ModelCheckingResult:
        formula.validate(self.kripke.atomic_propositions)
        
        start_time = time.time()
        satisfying_states, iterations = self._evaluate_formula(formula, use_cache)
        end_time = time.time()
        
        return ModelCheckingResult(
            formula=str(formula),
            satisfying_states=satisfying_states,
            computation_time=end_time - start_time,
            iterations=iterations,
            formula_size=self._formula_size(formula)
        )
    
    def _formula_size(self, formula: CTLFormula) -> int:
        if isinstance(formula, Atom):
            return 1
        elif isinstance(formula, UnaryFormula):
            return 1 + self._formula_size(formula.operand)
        elif isinstance(formula, BinaryFormula):
            return 1 + self._formula_size(formula.left) + self._formula_size(formula.right)
        return 1
    
    def _evaluate_formula(self, formula: CTLFormula, use_cache: bool) -> tuple[Set[str], int]:
        formula_key = str(formula) if use_cache else None
        
        if use_cache and formula_key in self.cache:
            return self.cache[formula_key], 0
        
        result, iterations = self._eval_formula_impl(formula)
        
        if use_cache and formula_key:
            self.cache[formula_key] = result
        
        return result, iterations
    
    def _eval_formula_impl(self, formula: CTLFormula) -> tuple[Set[str], int]:        

        if isinstance(formula, Atom):
            result = {s for s in self.kripke.states if formula.name in self.kripke.labels[s]}
            return result, 0
        
        if isinstance(formula, Not):
            inner, iters = self._eval_formula_impl(formula.operand)
            return self.kripke.states - inner, iters
        
        if isinstance(formula, And):
            left, iters1 = self._eval_formula_impl(formula.left)
            right, iters2 = self._eval_formula_impl(formula.right)
            return left & right, iters1 + iters2
        
        if isinstance(formula, Or):
            left, iters1 = self._eval_formula_impl(formula.left)
            right, iters2 = self._eval_formula_impl(formula.right)
            return left | right, iters1 + iters2
        
        if isinstance(formula, Implies):
            left, iters1 = self._eval_formula_impl(formula.left)
            right, iters2 = self._eval_formula_impl(formula.right)
            return (self.kripke.states - left) | right, iters1 + iters2
        
        if isinstance(formula, EX):
            operand_states, iters = self._eval_formula_impl(formula.operand)
            result = self.kripke.get_predecessors(operand_states)
            return result, iters
        
        if isinstance(formula, AX):
            operand_states, iters = self._eval_formula_impl(formula.operand)
            # AX φ ≡ ¬EX(¬φ)
            complement = self.kripke.states - operand_states
            ex_complement = self.kripke.get_predecessors(complement)
            result = self.kripke.states - ex_complement
            return result, iters
        
        if isinstance(formula, EU):
            return self._eval_eu(formula)
        
        if isinstance(formula, AU):
            return self._eval_au(formula)
        
        if isinstance(formula, EG):
            return self._eval_eg(formula)
        
        if isinstance(formula, AG):
            # AG φ ≡ ¬EF(¬φ) ≡ ¬E[true U ¬φ]
            neg_operand = Not(formula.operand)
            ef_neg, iters = self._eval_ef_impl(neg_operand)
            return self.kripke.states - ef_neg, iters
        
        if isinstance(formula, EF):
            return self._eval_ef_impl(formula)
        
        if isinstance(formula, AF):
            # AF φ ≡ A[true U φ] - we'll implement directly
            return self._eval_af_impl(formula)
        
        raise ValueError(f"Unknown formula type: {type(formula)}")

    # E[φ U ψ] - least fixpoint algorithm
    def _eval_eu(self, formula: EU) -> tuple[Set[str], int]:
        phi_states, iters1 = self._eval_formula_impl(formula.left)
        psi_states, iters2 = self._eval_formula_impl(formula.right)
        
        # Z₀ = [ψ]
        Z = set(psi_states)
        iterations = 0
        
        while True:
            iterations += 1
            # Z_{i+1} = [ψ] ∪ ([φ] ∩ Pre∃(Z_i))
            pre_exists = self.kripke.get_predecessors(Z)
            new_Z = psi_states | (phi_states & pre_exists)
            
            if new_Z == Z:
                break
            Z = new_Z
            
            # Safety check to prevent infinite loops
            if iterations > len(self.kripke.states):
                raise RuntimeError("EU fixpoint iteration exceeded maximum iterations")
        
        return Z, iters1 + iters2 + iterations

    # A[φ U ψ] - least fixpoint with universal predecessors
    def _eval_au(self, formula: AU) -> tuple[Set[str], int]:
        phi_states, iters1 = self._eval_formula_impl(formula.left)
        psi_states, iters2 = self._eval_formula_impl(formula.right)
        
        Z = set(psi_states)
        iterations = 0
        
        while True:
            iterations += 1
            # Universal predecessors: states where all successors are in Z
            pre_forall = self.kripke.get_universal_predecessors(Z)
            new_Z = psi_states | (phi_states & pre_forall)
            
            if new_Z == Z:
                break
            Z = new_Z
            
            if iterations > len(self.kripke.states):
                raise RuntimeError("AU fixpoint iteration exceeded maximum iterations")
        
        return Z, iters1 + iters2 + iterations

    # EG φ — greatest fixpoint: Z₀ = [[φ]], Z_{i+1} = [[φ]] ∩ Pre∃(Z_i)
    def _eval_eg(self, formula: EG) -> tuple[Set[str], int]:
        phi_states, iters1 = self._eval_formula_impl(formula.operand)

        Z = set(phi_states)
        iterations = 0

        while True:
            iterations += 1
            new_Z = phi_states & self.kripke.get_predecessors(Z)
            if new_Z == Z:
                break
            Z = new_Z
            if iterations > len(self.kripke.states):
                break

        return Z, iters1 + iterations

    # EF φ ≡ E[true U φ]
    def _eval_ef_impl(self, formula) -> tuple[Set[str], int]:
        if isinstance(formula, EF):
            operand_states, iters = self._eval_formula_impl(formula.operand)
        else:  # Called from AG with Not formula
            operand_states, iters = self._eval_formula_impl(formula)
        
        # E[true U φ] where true is satisfied by all states
        Z = set(operand_states)
        iterations = 0
        
        while True:
            iterations += 1
            pre_exists = self.kripke.get_predecessors(Z)
            new_Z = operand_states | pre_exists  # true is satisfied everywhere
            
            if new_Z == Z:
                break
            Z = new_Z
            
            if iterations > len(self.kripke.states):
                break
        
        return Z, iters + iterations

    # AF φ ≡ A[true U φ]    
    def _eval_af_impl(self, formula: AF) -> tuple[Set[str], int]:
        operand_states, iters = self._eval_formula_impl(formula.operand)
        
        Z = set(operand_states)
        iterations = 0
        
        while True:
            iterations += 1
            pre_forall = self.kripke.get_universal_predecessors(Z)
            new_Z = operand_states | pre_forall
            
            if new_Z == Z:
                break
            Z = new_Z
            
            if iterations > len(self.kripke.states):
                break
        
        return Z, iters + iterations


#  Example: Elevator Control System
def build_elevator_model() -> KripkeStructure:
    """Build a more sophisticated example: 3-floor elevator control system."""
    elevator = KripkeStructure("3-Floor Elevator System")
    
    # States encode: floor_direction_doors_request
    # floor: 1,2,3
    # direction: up(u), down(d), idle(i)  
    # doors: open(o), closed(c)
    # request: request_pending(r), no_request(n)
    
    # Floor 1 states
    elevator.add_state('1_i_c_n', ['floor1', 'idle', 'doors_closed', 'no_request'])
    elevator.add_state('1_i_c_r', ['floor1', 'idle', 'doors_closed', 'request_pending'])
    elevator.add_state('1_i_o_n', ['floor1', 'idle', 'doors_open', 'no_request'])
    elevator.add_state('1_u_c_n', ['floor1', 'moving_up', 'doors_closed', 'no_request'])
    elevator.add_state('1_u_c_r', ['floor1', 'moving_up', 'doors_closed', 'request_pending'])
    
    # Floor 2 states  
    elevator.add_state('2_i_c_n', ['floor2', 'idle', 'doors_closed', 'no_request'])
    elevator.add_state('2_i_c_r', ['floor2', 'idle', 'doors_closed', 'request_pending'])
    elevator.add_state('2_i_o_n', ['floor2', 'idle', 'doors_open', 'no_request'])
    elevator.add_state('2_u_c_n', ['floor2', 'moving_up', 'doors_closed', 'no_request'])
    elevator.add_state('2_u_c_r', ['floor2', 'moving_up', 'doors_closed', 'request_pending'])
    elevator.add_state('2_d_c_n', ['floor2', 'moving_down', 'doors_closed', 'no_request'])
    elevator.add_state('2_d_c_r', ['floor2', 'moving_down', 'doors_closed', 'request_pending'])
    
    # Floor 3 states
    elevator.add_state('3_i_c_n', ['floor3', 'idle', 'doors_closed', 'no_request'])
    elevator.add_state('3_i_c_r', ['floor3', 'idle', 'doors_closed', 'request_pending'])
    elevator.add_state('3_i_o_n', ['floor3', 'idle', 'doors_open', 'no_request'])
    elevator.add_state('3_d_c_n', ['floor3', 'moving_down', 'doors_closed', 'no_request'])
    elevator.add_state('3_d_c_r', ['floor3', 'moving_down', 'doors_closed', 'request_pending'])
    
    # Transitions modeling elevator behavior
    
    # From floor 1
    elevator.add_transition('1_i_c_n', '1_i_c_r')     # request arrives
    elevator.add_transition('1_i_c_r', '1_i_o_n')     # open doors (serve request)
    elevator.add_transition('1_i_o_n', '1_i_c_n')     # close doors
    elevator.add_transition('1_i_c_n', '1_u_c_n')     # start moving up
    elevator.add_transition('1_u_c_n', '2_i_c_n')     # arrive at floor 2
    elevator.add_transition('1_i_c_r', '1_u_c_r')     # move up with request pending
    elevator.add_transition('1_u_c_r', '2_i_c_r')     # arrive with request
    
    # From floor 2  
    elevator.add_transition('2_i_c_n', '2_i_c_r')     # request arrives
    elevator.add_transition('2_i_c_r', '2_i_o_n')     # serve request
    elevator.add_transition('2_i_o_n', '2_i_c_n')     # close doors
    elevator.add_transition('2_i_c_n', '2_u_c_n')     # go up
    elevator.add_transition('2_i_c_n', '2_d_c_n')     # go down
    elevator.add_transition('2_u_c_n', '3_i_c_n')     # arrive at 3
    elevator.add_transition('2_d_c_n', '1_i_c_n')     # arrive at 1
    elevator.add_transition('2_i_c_r', '2_u_c_r')     # up with request
    elevator.add_transition('2_i_c_r', '2_d_c_r')     # down with request  
    elevator.add_transition('2_u_c_r', '3_i_c_r')     # arrive at 3 with request
    elevator.add_transition('2_d_c_r', '1_i_c_r')     # arrive at 1 with request
    
    # From floor 3
    elevator.add_transition('3_i_c_n', '3_i_c_r')     # request arrives
    elevator.add_transition('3_i_c_r', '3_i_o_n')     # serve request
    elevator.add_transition('3_i_o_n', '3_i_c_n')     # close doors  
    elevator.add_transition('3_i_c_n', '3_d_c_n')     # start going down
    elevator.add_transition('3_d_c_n', '2_i_c_n')     # arrive at floor 2
    elevator.add_transition('3_i_c_r', '3_d_c_r')     # down with request
    elevator.add_transition('3_d_c_r', '2_i_c_r')     # arrive at 2 with request
    
    return elevator.ensure_total_relation()


# Test Suite and Demonstration
def run_elevator_analysis():
    print("   CTL Model Checker - Elevator Control System Analysis")
    print("=" * 70)
    
    # Build and validate model
    elevator = build_elevator_model()
    print(f"\n  Model Statistics:")
    print(f"   States: {len(elevator.states)}")
    print(f"   Transitions: {sum(len(succs) for succs in elevator.transitions.values())}")
    print(f"   Atomic Propositions: {len(elevator.atomic_propositions)}")
    
    # Initialize model checker
    checker = CTLModelChecker(elevator)
    
    # Define properties to check
    properties = [
        # Safety Properties
        ("Safety: Never doors open while moving", 
         AG(Implies(Or(Atom('moving_up'), Atom('moving_down')), Atom('doors_closed')))),
        
        ("Safety: Can't be on multiple floors", 
         AG(Not(And(Atom('floor1'), Or(Atom('floor2'), Atom('floor3')))))),
        
        # Liveness Properties (see liveness gap note below)
        ("Liveness gap: every request eventually served (expected FAILS — model gap)",
         AG(Implies(Atom('request_pending'), AF(Atom('doors_open'))))),
        
        ("Liveness: From any floor, can reach any other floor",
         And(AG(EF(Atom('floor2'))), And(AG(EF(Atom('floor1'))), AG(EF(Atom('floor3')))))),
        
        # Reachability: from any floor1 state, floor3 is eventually reachable
        # (The earlier EF(floor3 ∧ EX(floor1)) was wrong: it asked whether
        #  floor3 has a direct one-step transition back to floor1, which no
        #  3-floor elevator has.  The correct reading is AG(floor1 → EF(floor3)).)
        ("Reachability: floor 3 is reachable from every floor 1 state",
         AG(Implies(Atom('floor1'), EF(Atom('floor3'))))),

        # Liveness gap: properties below expose that the model allows a
        # moving elevator with a pending request to cycle indefinitely.
        # These fail — correctly — because the non-deterministic model does
        # not enforce fair scheduling.  To make them hold the model would
        # need to remove transitions that leave a pending request unserved
        # when the elevator is idle at the right floor, or add fairness
        # constraints beyond plain CTL.
        ("Liveness gap: no infinite moving without serving (expected FAILS)",
         AG(Implies(And(Or(Atom('moving_up'), Atom('moving_down')), Atom('request_pending')),
                    AF(Atom('doors_open'))))),
    ]
    
    print(f"\n  Property Verification Results:")
    print("-" * 70)
    
    total_time = 0
    for i, (description, formula) in enumerate(properties, 1):
        try:
            result = checker.check_formula(formula)
            total_time += result.computation_time
            
            # Check if property holds in all states (universal validity)
            holds_everywhere = result.satisfying_states == elevator.states
            status = " HOLDS" if holds_everywhere else " FAILS"
            
            print(f"\n{i}. {description}")
            print(f"   Formula: {result.formula}")
            print(f"   Status: {status}")
            print(f"   Satisfying states: {len(result.satisfying_states)}/{len(elevator.states)}")
            print(f"   Computation time: {result.computation_time:.4f}s")
            print(f"   Iterations: {result.iterations}")
            
            if not holds_everywhere and len(result.satisfying_states) < len(elevator.states):
                violating_states = elevator.states - result.satisfying_states
                print(f"   Counterexample states: {sorted(list(violating_states)[:3])}{'...' if len(violating_states) > 3 else ''}")
        
        except Exception as e:
            print(f"\n{i}. {description}")
            print(f"   Status: ERROR - {e}")
    
    print(f"\n  Total verification time: {total_time:.4f}s")
    print(f" Cache entries: {len(checker.cache)}")
    
    # Analyze model structure
    print(f"\n Structural Analysis:")
    sccs = elevator.get_strongly_connected_components()
    print(f"   Strongly Connected Components: {len(sccs)}")
    for i, scc in enumerate(sccs[:5]):  # Show first 5 SCCs
        print(f"   SCC {i+1}: {sorted(list(scc))}")
    
    return checker

# Add this if you want to make the script more robust when run directly
def main():
    try:
        checker = run_elevator_analysis()
        print(f"\n Analysis complete! Model checker ready for interactive use.")
        return checker
    except KeyboardInterrupt:
        print(f"\n  Analysis interrupted by user.")
        return None
    except Exception as e:
        print(f" Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        raise

# ---------------------------------------------------------------------------
# Example 2: Traffic Light
#
# A minimal Kripke structure to introduce CTL before the elevator example.
# Four states follow the standard European sequence:
#
#   red  ->  red_amber  ->  green  ->  amber  ->  red  (cycle)
#
# Atomic propositions: red, amber, green, safe_to_go
#   safe_to_go holds only in the green state.
#
# This lets us check simple but instructive CTL properties:
#   - AG(EF(green))         every state can eventually reach green
#   - AG(green -> AX(amber)) green is always followed by amber
#   - AG(red -> A[red U green]) while red, stays red until green
#   - AG(safe_to_go -> green) safe_to_go implies green (sanity check)
# ---------------------------------------------------------------------------

def build_traffic_light_model() -> KripkeStructure:
    tl = KripkeStructure("Traffic Light")

    tl.add_state('red',       ['red'])
    tl.add_state('red_amber', ['red', 'amber'])
    tl.add_state('green',     ['green', 'safe_to_go'])
    tl.add_state('amber',     ['amber'])

    tl.add_transition('red',       'red_amber')
    tl.add_transition('red_amber', 'green')
    tl.add_transition('green',     'amber')
    tl.add_transition('amber',     'red')

    return tl.ensure_total_relation()


def run_traffic_light_analysis():
    print("\n" + "=" * 70)
    print("  CTL Model Checker — Traffic Light")
    print("=" * 70)

    tl = build_traffic_light_model()
    print(f"\n  Model Statistics:")
    print(f"   States              : {len(tl.states)}")
    print(f"   Transitions         : {sum(len(s) for s in tl.transitions.values())}")
    print(f"   Atomic Propositions : {len(tl.atomic_propositions)}")
    print(f"   Propositions        : {sorted(tl.atomic_propositions)}")

    checker = CTLModelChecker(tl)

    properties = [
        ("Every state can eventually reach green",
         AG(EF(Atom('green')))),

        ("Green is always immediately followed by amber",
         AG(Implies(Atom('green'), AX(Atom('amber'))))),

        ("From red, stays red until green (no skipping red_amber)",
         AG(Implies(Atom('red'), AU(Atom('red'), Atom('green'))))),

        ("safe_to_go implies green (label consistency)",
         AG(Implies(Atom('safe_to_go'), Atom('green')))),

        ("Red is always eventually left (liveness)",
         AG(Implies(Atom('red'), AF(Atom('green'))))),

        ("There exists a path that stays non-green indefinitely (EG)",
         EG(Not(Atom('green')))),
    ]

    print(f"\n  Property Verification:")
    print("-" * 70)
    for i, (desc, formula) in enumerate(properties, 1):
        result = checker.check_formula(formula)
        holds = result.satisfying_states == tl.states
        status = "HOLDS" if holds else "FAILS"
        n_sat = len(result.satisfying_states)
        print(f"\n{i}. {desc}")
        print(f"   Formula : {result.formula}")
        print(f"   Status  : {status}  ({n_sat}/{len(tl.states)} states satisfy)")
        if not holds:
            counterex = sorted(tl.states - result.satisfying_states)
            print(f"   Not satisfied in: {counterex}")

    return checker


def main():
    try:
        run_traffic_light_analysis()
        print()
        checker = run_elevator_analysis()
        print(f"\n  Analysis complete.")
        return checker
    except KeyboardInterrupt:
        print("\n  Interrupted.")
        return None
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()
