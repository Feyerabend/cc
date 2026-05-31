#!/usr/bin/env python3
# Presburger Arithmetic System

import re
from typing import List, Optional, Dict, Any


# core

class Term:
    def __str__(self):
        raise NotImplementedError
    
    def __eq__(self, other):
        return str(self) == str(other)
    
    def __hash__(self):
        return hash(str(self))

class Zero(Term):
    def __str__(self):
        return "0"

class Var(Term):
    def __init__(self, name: str):
        self.name = name
    
    def __str__(self):
        return self.name

class Succ(Term):
    def __init__(self, term: Term):
        self.term = term
    
    def __str__(self):
        return f"S({self.term})"

class Add(Term):
    def __init__(self, left: Term, right: Term):
        self.left = left
        self.right = right
    
    def __str__(self):
        return f"({self.left} + {self.right})"


# Multiplication by constants (for extended Presburger)
class Mult(Term):
    def __init__(self, constant: int, term: Term):
        self.constant = constant
        self.term = term
    
    def __str__(self):
        if self.constant == 1:
            return str(self.term)
        return f"{self.constant}*{self.term}"



class Formula:
    def __str__(self):
        raise NotImplementedError
    
    def __eq__(self, other):
        return str(self) == str(other)
    
    def __hash__(self):
        return hash(str(self))

class Eq(Formula):
    def __init__(self, left: Term, right: Term):
        self.left = left
        self.right = right
    
    def __str__(self):
        return f"({self.left} = {self.right})"

class Lt(Formula):
    def __init__(self, left: Term, right: Term):
        self.left = left
        self.right = right
    
    def __str__(self):
        return f"({self.left} < {self.right})"

class Le(Formula):
    def __init__(self, left: Term, right: Term):
        self.left = left
        self.right = right

    def __str__(self):
        return f"({self.left} ≤ {self.right})"

class Divisibility(Formula):
    """Divisibility predicate: divisor | term  (term ≡ 0 mod divisor).
    Arises naturally in Cooper's quantifier elimination — every existential
    over a variable with coefficient >1 generates a divisibility constraint."""
    def __init__(self, divisor: int, term: Term):
        self.divisor = divisor
        self.term = term

    def __str__(self):
        return f"({self.divisor} | {self.term})"

class Not(Formula):
    def __init__(self, formula: Formula):
        self.formula = formula
    
    def __str__(self):
        return f"¬{self.formula}"

class And(Formula):
    def __init__(self, left: Formula, right: Formula):
        self.left = left
        self.right = right
    
    def __str__(self):
        return f"({self.left} ∧ {self.right})"

class Or(Formula):
    def __init__(self, left: Formula, right: Formula):
        self.left = left
        self.right = right
    
    def __str__(self):
        return f"({self.left} ∨ {self.right})"

class Implies(Formula):
    def __init__(self, left: Formula, right: Formula):
        self.left = left
        self.right = right
    
    def __str__(self):
        return f"({self.left} → {self.right})"

class Iff(Formula):
    def __init__(self, left: Formula, right: Formula):
        self.left = left
        self.right = right
    
    def __str__(self):
        return f"({self.left} ↔ {self.right})"

class ForAll(Formula):
    def __init__(self, varname: str, formula: Formula):
        self.varname = varname
        self.formula = formula
    
    def __str__(self):
        return f"(∀{self.varname}. {self.formula})"

class Exists(Formula):
    def __init__(self, varname: str, formula: Formula):
        self.varname = varname
        self.formula = formula
    
    def __str__(self):
        return f"(∃{self.varname}. {self.formula})"



def get_free_vars(obj) -> set:
    if isinstance(obj, Var):
        return {obj.name}
    elif isinstance(obj, (Zero, int)):
        return set()
    elif isinstance(obj, Succ):
        return get_free_vars(obj.term)
    elif isinstance(obj, Not):
        return get_free_vars(obj.formula)
    elif isinstance(obj, (Mult, Divisibility)):
        return get_free_vars(obj.term)
    elif isinstance(obj, (Add, Eq, Lt, Le, And, Or, Implies, Iff)):
        return get_free_vars(obj.left) | get_free_vars(obj.right)
    elif isinstance(obj, (ForAll, Exists)):
        inner_vars = get_free_vars(obj.formula)
        inner_vars.discard(obj.varname)
        return inner_vars
    return set()


def substitute_var(term: Term, varname: str, replacement: Term) -> Term:
    if isinstance(term, Var):
        return replacement if term.name == varname else term
    elif isinstance(term, Zero):
        return term
    elif isinstance(term, Succ):
        return Succ(substitute_var(term.term, varname, replacement))
    elif isinstance(term, Add):
        return Add(substitute_var(term.left, varname, replacement),
                   substitute_var(term.right, varname, replacement))
    elif isinstance(term, Mult):
        return Mult(term.constant, substitute_var(term.term, varname, replacement))
    else:
        return term

def substitute_formula(formula: Formula, varname: str, replacement: Term) -> Formula:
    if isinstance(formula, (Eq, Lt, Le)):
        return formula.__class__(substitute_var(formula.left, varname, replacement),
                               substitute_var(formula.right, varname, replacement))
    elif isinstance(formula, Divisibility):
        return Divisibility(formula.divisor,
                            substitute_var(formula.term, varname, replacement))
    elif isinstance(formula, Not):
        return Not(substitute_formula(formula.formula, varname, replacement))
    elif isinstance(formula, (And, Or, Implies, Iff)):
        return formula.__class__(substitute_formula(formula.left, varname, replacement),
                               substitute_formula(formula.right, varname, replacement))
    elif isinstance(formula, (ForAll, Exists)):
        if formula.varname == varname:
            return formula  # variable bound, don't substitute
        else:
            return formula.__class__(formula.varname, 
                                   substitute_formula(formula.formula, varname, replacement))
    else:
        return formula



def evaluate_term(term: Term, env: Dict[str, int] = None) -> int:
    """Evaluate a ground or partially-ground term under variable assignment env."""
    if env is None:
        env = {}
    if isinstance(term, Zero):
        return 0
    elif isinstance(term, Var):
        if term.name not in env:
            raise ValueError(f"Unbound variable: {term.name}")
        return env[term.name]
    elif isinstance(term, Succ):
        return evaluate_term(term.term, env) + 1
    elif isinstance(term, Add):
        return evaluate_term(term.left, env) + evaluate_term(term.right, env)
    elif isinstance(term, Mult):
        return term.constant * evaluate_term(term.term, env)
    raise ValueError(f"Unknown term type: {type(term).__name__}")

def evaluate_formula(formula: Formula, env: Dict[str, int] = None) -> bool:
    """Evaluate a quantifier-free formula under variable assignment env."""
    if env is None:
        env = {}
    if isinstance(formula, Eq):
        return evaluate_term(formula.left, env) == evaluate_term(formula.right, env)
    elif isinstance(formula, Lt):
        return evaluate_term(formula.left, env) < evaluate_term(formula.right, env)
    elif isinstance(formula, Le):
        return evaluate_term(formula.left, env) <= evaluate_term(formula.right, env)
    elif isinstance(formula, Divisibility):
        val = evaluate_term(formula.term, env)
        return val % formula.divisor == 0
    elif isinstance(formula, Not):
        return not evaluate_formula(formula.formula, env)
    elif isinstance(formula, And):
        return evaluate_formula(formula.left, env) and evaluate_formula(formula.right, env)
    elif isinstance(formula, Or):
        return evaluate_formula(formula.left, env) or evaluate_formula(formula.right, env)
    elif isinstance(formula, Implies):
        return (not evaluate_formula(formula.left, env)) or evaluate_formula(formula.right, env)
    elif isinstance(formula, Iff):
        return evaluate_formula(formula.left, env) == evaluate_formula(formula.right, env)
    raise ValueError(
        f"Cannot evaluate {type(formula).__name__}: quantified formulas require a decision procedure")


def num(n: int) -> Term:
    if n == 0:
        return Zero()
    elif n > 0:
        result = Zero()
        for _ in range(n):
            result = Succ(result)
        return result
    else:
        raise ValueError("Negative numbers not directly representable")

def var(name: str) -> Var:
    return Var(name)



class PresburgerAxioms:
    def __init__(self):
        self.axioms = []
        self._generate_axioms()
    
    def _generate_axioms(self):
        x, y, z = var("x"), var("y"), var("z")
        
        # Basic successor axioms
        # A1: ∀x. S(x) ≠ 0
        self.axioms.append(ForAll("x", Not(Eq(Succ(x), Zero()))))
        
        # A2: ∀x∀y. S(x) = S(y) → x = y (injectivity of successor)
        self.axioms.append(ForAll("x", ForAll("y", 
            Implies(Eq(Succ(x), Succ(y)), Eq(x, y)))))
        
        # A3: ∀x. x = 0 ∨ ∃y. S(y) = x (every number is 0 or a successor)
        self.axioms.append(ForAll("x", 
            Or(Eq(x, Zero()), Exists("y", Eq(Succ(var("y")), x)))))
        
        # Addition axioms
        # A4: ∀x. x + 0 = x
        self.axioms.append(ForAll("x", Eq(Add(x, Zero()), x)))
        
        # A5: ∀x∀y. x + S(y) = S(x + y)
        self.axioms.append(ForAll("x", ForAll("y", 
            Eq(Add(x, Succ(y)), Succ(Add(x, y))))))
        
        # Additional useful axioms
        # A6: ∀x. 0 + x = x (commutativity base case)
        self.axioms.append(ForAll("x", Eq(Add(Zero(), x), x)))
        
        # A7: ∀x∀y. x + y = y + x (commutativity)
        self.axioms.append(ForAll("x", ForAll("y", Eq(Add(x, y), Add(y, x)))))
        
        # A8: ∀x∀y∀z. (x + y) + z = x + (y + z) (associativity)
        self.axioms.append(ForAll("x", ForAll("y", ForAll("z",
            Eq(Add(Add(x, y), z), Add(x, Add(y, z)))))))



class ProofStep:
    def __init__(self, formula: Formula, rule: str, justification: str = ""):
        self.formula = formula
        self.rule = rule
        self.justification = justification
    
    def __str__(self):
        return f"{self.formula} [{self.rule}] {self.justification}"

class ProofSystem:
    def __init__(self):
        self.axioms = PresburgerAxioms()
        self.proven_formulas = list(self.axioms.axioms)
        self.proof_history = []
    
    def is_axiom(self, formula: Formula) -> bool:
        return any(str(formula) == str(ax) for ax in self.axioms.axioms)
    
    def is_proven(self, formula: Formula) -> bool:
        return any(str(formula) == str(pf) for pf in self.proven_formulas)
    
    def modus_ponens(self, implication: Formula, premise: Formula) -> Optional[Formula]:
        if isinstance(implication, Implies) and str(implication.left) == str(premise):
            return implication.right
        return None
    
    def universal_instantiation(self, formula: Formula, replacement: Term) -> Optional[Formula]:
        if isinstance(formula, ForAll):
            return substitute_formula(formula.formula, formula.varname, replacement)
        return None
    
    def existential_generalization(self, formula: Formula, varname: str, term: Term) -> Optional[Formula]:
        if varname not in get_free_vars(formula):
            return Exists(varname, substitute_formula(formula, term.name if isinstance(term, Var) else str(term), var(varname)))
        return None
    
    def prove_step(self, formula: Formula, rule: str = "assumption") -> bool:
        
        # Check if already proven or is axiom
        if self.is_proven(formula) or self.is_axiom(formula):
            step = ProofStep(formula, "axiom" if self.is_axiom(formula) else "already proven")
            self.proof_history.append(step)
            return True
        
        # Try modus ponens with all proven implications
        for proven in self.proven_formulas:
            if isinstance(proven, Implies):
                conclusion = self.modus_ponens(proven, formula)
                if conclusion and not self.is_proven(conclusion):
                    self.proven_formulas.append(conclusion)
                    step = ProofStep(conclusion, "modus ponens", f"from {proven} and {formula}")
                    self.proof_history.append(step)
                    return True
        
        # Try universal instantiation
        if rule == "universal_inst":
            # This would need more sophisticated term matching
            pass
        
        # Add as assumption for now
        self.proven_formulas.append(formula)
        step = ProofStep(formula, rule)
        self.proof_history.append(step)
        return True
    
    def get_proof_history(self) -> List[str]:
        return [str(step) for step in self.proof_history]



class Examples:
    @staticmethod
    def basic_arithmetic():
        x, y = var("x"), var("y")
        
        examples = [
            ("Zero identity", Eq(Add(x, Zero()), x)),
            ("Successor addition", Eq(Add(x, Succ(Zero())), Succ(x))),
            ("2 + 3 = 5", Eq(Add(num(2), num(3)), num(5))),
            ("Commutativity", Eq(Add(x, y), Add(y, x))),
            ("x + 0 = 0 + x", Eq(Add(x, Zero()), Add(Zero(), x))),
        ]
        
        return examples
    
    @staticmethod
    def logical_formulas():
        x, y, z = var("x"), var("y"), var("z")

        examples = [
            ("Existence of successor", Exists("x", Eq(x, Succ(Zero())))),
            ("Universal property", ForAll("x", Not(Eq(Succ(x), Zero())))),
            ("Conditional", Implies(Eq(x, Zero()), Eq(Add(x, y), y))),
            ("Biconditional", Iff(Eq(x, y), Eq(Add(x, z), Add(y, z)))),
            ("Complex formula", ForAll("x", Implies(
                Exists("y", Eq(Add(x, y), num(5))),
                Not(Eq(x, num(6)))
            ))),
        ]

        return examples

    @staticmethod
    def divisibility_examples():
        """Divisibility predicates — key primitives in Presburger arithmetic.
        Cooper's algorithm introduces these automatically during quantifier
        elimination whenever a variable has a coefficient greater than 1."""
        x = var("x")
        six = num(6)

        return [
            ("2 divides x+x", Divisibility(2, Add(x, x))),
            ("3 divides 6",    Divisibility(3, six)),
            ("Even number <= 6 exists",
             Exists("x", And(Le(x, six), Divisibility(2, x)))),
            ("Periodicity mod 3: every x is 0, 1, or 2 mod 3",
             ForAll("x", Or(
                 Divisibility(3, x),
                 Or(Divisibility(3, Add(x, num(1))),
                    Divisibility(3, Add(x, num(2))))))),
        ]


class InteractivePresburger:
    def __init__(self):
        self.proof_system = ProofSystem()
        self.examples = Examples()
    
    def show_menu(self):
        print("\n" + "="*60)
        print("INTERACTIVE PRESBURGER ARITHMETIC SYSTEM")
        print("="*60)
        print("1. View axioms")
        print("2. View examples")
        print("3. Build and test formulas")
        print("4. Attempt proofs")
        print("5. View proof history")
        print("6. Formula parser (simple)")
        print("7. Help")
        print("0. Exit")
        print("="*60)
    
    def show_axioms(self):
        print("\nPRESBURGER ARITHMETIC AXIOMS:")
        print("- " * 40)
        for i, axiom in enumerate(self.proof_system.axioms.axioms, 1):
            print(f"A{i}: {axiom}")
    
    def show_examples(self):
        print("\nBASIC ARITHMETIC EXAMPLES:")
        print("- " * 40)
        for name, formula in self.examples.basic_arithmetic():
            print(f"{name}: {formula}")

        print("\nLOGICAL FORMULA EXAMPLES:")
        print("- " * 40)
        for name, formula in self.examples.logical_formulas():
            print(f"{name}: {formula}")

        print("\nDIVISIBILITY EXAMPLES:")
        print("- " * 40)
        for name, formula in self.examples.divisibility_examples():
            print(f"{name}: {formula}")
    
    def formula_builder(self):
        print("\nFORMULA BUILDER")
        print("- " * 20)
        print("Build terms and formulas step by step:")
        
        # Simple term builder
        print("\n1. Create terms:")
        print("   - Numbers: Use num(n) for integers")
        print("   - Variables: Use var('name')")
        print("   - Successor: Use Succ(term)")
        print("   - Addition: Use Add(term1, term2)")
        
        print("\n2. Create formulas:")
        print("   - Equality: Use Eq(term1, term2)")
        print("   - Negation: Use Not(formula)")
        print("   - Conjunction: Use And(formula1, formula2)")
        print("   - Universal: Use ForAll('var', formula)")
        
        # Interactive building
        while True:
            try:
                user_input = input("\nEnter Python expression (or 'back'): ").strip()
                if user_input.lower() == 'back':
                    break
                
                # Simple evaluation (dangerous in real apps, but OK for demo)
                result = eval(user_input, {
                    'num': num, 'var': var, 'Zero': Zero, 'Succ': Succ, 'Add': Add,
                    'Eq': Eq, 'Not': Not, 'And': And, 'Or': Or, 'Implies': Implies,
                    'ForAll': ForAll, 'Exists': Exists, 'Iff': Iff, 'Lt': Lt, 'Le': Le,
                    'Divisibility': Divisibility, 'Mult': Mult,
                })
                
                print(f"Result: {result}")
                print(f"Type: {type(result).__name__}")
                
                if isinstance(result, Formula):
                    print(f"Free variables: {get_free_vars(result)}")
                
            except Exception as e:
                print(f"Error: {e}")
    
    def attempt_proof(self):
        print("\nPROOF SYSTEM")
        print("- " * 20)
        print("Try to prove formulas using the proof system.")
        print("Note: This is a simplified proof checker.")
        
        while True:
            try:
                user_input = input("\nEnter formula to prove (or 'back'): ").strip()
                if user_input.lower() == 'back':
                    break
                
                # Parse and attempt proof
                formula = eval(user_input, {
                    'num': num, 'var': var, 'Zero': Zero, 'Succ': Succ, 'Add': Add,
                    'Eq': Eq, 'Not': Not, 'And': And, 'Or': Or, 'Implies': Implies,
                    'ForAll': ForAll, 'Exists': Exists, 'Iff': Iff,
                    'Divisibility': Divisibility, 'Mult': Mult,
                })
                
                print(f"\nAttempting to prove: {formula}")
                
                if self.proof_system.prove_step(formula):
                    print("Proof successful (or added as assumption)")
                else:
                    print("Could not prove automatically")
                
            except Exception as e:
                print(f"Error: {e}")
    
    def show_proof_history(self):
        print("\nPROOF HISTORY:")
        print("-" * 20)
        history = self.proof_system.get_proof_history()
        if not history:
            print("No proofs attempted yet.")
        else:
            for i, step in enumerate(history, 1):
                print(f"{i}. {step}")
    
    def show_help(self):
        print("\nHELP - HOW TO USE THIS SYSTEM")
        print("="*40)
        print("""
This system implements Presburger arithmetic - the first-order theory
of natural numbers with addition.

BASIC SYNTAX:
- Numbers: num(5) creates the term for 5
- Variables: var('x') creates variable x
- Zero: Zero() is the constant 0  
- Successor: Succ(term) is the successor function
- Addition: Add(term1, term2) is addition

FORMULAS:
- Equality: Eq(term1, term2)
- Logical connectives: Not, And, Or, Implies, Iff
- Quantifiers: ForAll('var', formula), Exists('var', formula)

EXAMPLES:
- Simple equation: Eq(Add(num(2), num(3)), num(5))
- Universal statement: ForAll('x', Eq(Add(x, Zero()), x))
- Existence: Exists('y', Eq(Succ(y), num(3)))

The system includes axioms for successor, addition, and basic properties.
You can build formulas, attempt proofs, and explore the theory interactively.
        """)
    
    def run(self):
        print("Welcome to the Interactive Presburger Arithmetic System!")
        
        while True:
            self.show_menu()
            try:
                choice = input("\nEnter your choice (0-7): ").strip()
                
                if choice == '0':
                    print("Goodbye!")
                    break
                elif choice == '1':
                    self.show_axioms()
                elif choice == '2':
                    self.show_examples()
                elif choice == '3':
                    self.formula_builder()
                elif choice == '4':
                    self.attempt_proof()
                elif choice == '5':
                    self.show_proof_history()
                elif choice == '6':
                    print("Formula parser not implemented. Use formula builder.")
                elif choice == '7':
                    self.show_help()
                else:
                    print("Invalid choice. Please try again.")
                    
                input("\nPress Enter to continue ..")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


def run_demos():
    print("PRESBURGER ARITHMETIC DEMONSTRATIONS")
    print("="*50)
    
    # Create proof system
    ps = ProofSystem()
    
    # Demo 1: Basic arithmetic
    print("\n1. Basic Arithmetic Examples:")
    examples = Examples.basic_arithmetic()
    for name, formula in examples[:3]:
        print(f"   {name}: {formula}")
    
    # Demo 2: Logical formulas
    print("\n2. Logical Formula Examples:")
    examples = Examples.logical_formulas()
    for name, formula in examples[:3]:
        print(f"   {name}: {formula}")
    
    # Demo 3: Simple proofs
    print("\n3. Axiom Verification:")
    print(f"   Number of axioms loaded: {len(ps.axioms.axioms)}")
    print(f"   First axiom: {ps.axioms.axioms[0]}")
    
    # Demo 4: Term building
    print("\n4. Term Construction Examples:")
    print(f"   Number 3: {num(3)}")
    print(f"   Variable x: {var('x')}")
    print(f"   x + 3: {Add(var('x'), num(3))}")
    print(f"   S(x + 3): {Succ(Add(var('x'), num(3)))}")

    # Demo 5: Evaluation and divisibility
    print("\n5. Evaluation and Divisibility:")
    x = var("x")
    env = {"x": 5}
    f1 = Lt(Add(x, num(3)), num(10))
    print(f"   x+3 < 10  with x=5:  {f1}  =  {evaluate_formula(f1, env)}")
    f2 = Divisibility(2, num(6))
    f3 = Divisibility(2, num(7))
    print(f"   2 | 6:  {f2}  =  {evaluate_formula(f2)}")
    print(f"   2 | 7:  {f3}  =  {evaluate_formula(f3)}")
    f4 = And(Divisibility(2, x), Le(x, num(6)))
    print(f"   2|x /\\ x<=6  with x=4:  {f4}  =  {evaluate_formula(f4, {'x': 4})}")


def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        run_demos()
    else:
        # Start interactive system
        system = InteractivePresburger()
        system.run()

if __name__ == "__main__":
    main()
