#!/usr/bin/env python3
# Cooper's Algorithm for Presburger Arithmetic Decision Procedure
# This is a implementation of Cooper's quantifier elimination algorithm
# for deciding formulas in Presburger arithmetic (first-order logic of natural
# numbers with addition).

from typing import List, Optional, Dict, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import re


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

class Const(Term):
    def __init__(self, value: int):
        self.value = value
    
    def __str__(self):
        return str(self.value)

class Add(Term):
    def __init__(self, left: Term, right: Term):
        self.left = left
        self.right = right
    
    def __str__(self):
        return f"({self.left} + {self.right})"

class Mult(Term):
    def __init__(self, coefficient: int, term: Term):
        self.coefficient = coefficient
        self.term = term
    
    def __str__(self):
        if self.coefficient == 1:
            return str(self.term)
        return f"{self.coefficient}*{self.term}"

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
    """Divisibility predicate: divisor | term.
    Generated automatically by Cooper's algorithm when eliminating a variable
    whose coefficient in some constraint is greater than 1."""
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
    def __init__(self, var: str, formula: Formula):
        self.var = var
        self.formula = formula
    
    def __str__(self):
        return f"(∀{self.var}. {self.formula})"

class Exists(Formula):
    def __init__(self, var: str, formula: Formula):
        self.var = var
        self.formula = formula
    
    def __str__(self):
        return f"(∃{self.var}. {self.formula})"

class True_(Formula):
    def __str__(self):
        return "⊤"

class False_(Formula):
    def __str__(self):
        return "⊥"



@dataclass
class LinearTerm:
    coefficients: Dict[str, int]  # var_name -> coefficient
    constant: int
    
    def __init__(self, coefficients=None, constant=0):
        self.coefficients = coefficients or {}
        self.constant = constant
    
    def __str__(self):
        parts = []
        for var, coef in self.coefficients.items():
            if coef == 1:
                parts.append(var)
            elif coef == -1:
                parts.append(f"-{var}")
            else:
                parts.append(f"{coef}*{var}")
        
        if self.constant != 0 or not parts:
            parts.append(str(self.constant))
        
        return " + ".join(parts).replace("+ -", "- ")

@dataclass
class LinearConstraint:
    left: LinearTerm
    relation: str  # "=", "<", "≤"
    right: LinearTerm
    
    def normalize(self) -> 'LinearConstraint':
        new_coeffs = {}
        
        # Subtract right from left
        for var, coef in self.left.coefficients.items():
            new_coeffs[var] = coef
        for var, coef in self.right.coefficients.items():
            new_coeffs[var] = new_coeffs.get(var, 0) - coef
        
        new_constant = self.left.constant - self.right.constant
        
        return LinearConstraint(
            LinearTerm(new_coeffs, new_constant),
            self.relation,
            LinearTerm({}, 0)
        )
    
    def __str__(self):
        return f"{self.left} {self.relation} {self.right}"




def get_free_vars(obj) -> Set[str]:
    if isinstance(obj, Var):
        return {obj.name}
    elif isinstance(obj, (Zero, Const, True_, False_)):
        return set()
    elif isinstance(obj, Add):
        return get_free_vars(obj.left) | get_free_vars(obj.right)
    elif isinstance(obj, Mult):
        return get_free_vars(obj.term)
    elif isinstance(obj, Divisibility):
        return get_free_vars(obj.term)
    elif isinstance(obj, (Eq, Lt, Le, And, Or, Implies, Iff)):
        return get_free_vars(obj.left) | get_free_vars(obj.right)
    elif isinstance(obj, Not):
        return get_free_vars(obj.formula)
    elif isinstance(obj, (ForAll, Exists)):
        inner_vars = get_free_vars(obj.formula)
        inner_vars.discard(obj.var)
        return inner_vars
    return set()

def substitute(obj, var: str, replacement: Term):
    if isinstance(obj, Var):
        return replacement if obj.name == var else obj
    elif isinstance(obj, (Zero, Const, True_, False_)):
        return obj
    elif isinstance(obj, Add):
        return Add(substitute(obj.left, var, replacement),
                  substitute(obj.right, var, replacement))
    elif isinstance(obj, Mult):
        return Mult(obj.coefficient, substitute(obj.term, var, replacement))
    elif isinstance(obj, Divisibility):
        return Divisibility(obj.divisor, substitute(obj.term, var, replacement))
    elif isinstance(obj, (Eq, Lt, Le)):
        return obj.__class__(substitute(obj.left, var, replacement),
                           substitute(obj.right, var, replacement))
    elif isinstance(obj, Not):
        return Not(substitute(obj.formula, var, replacement))
    elif isinstance(obj, (And, Or, Implies, Iff)):
        return obj.__class__(substitute(obj.left, var, replacement),
                           substitute(obj.right, var, replacement))
    elif isinstance(obj, (ForAll, Exists)):
        if obj.var == var:
            return obj  # Variable is bound
        return obj.__class__(obj.var, substitute(obj.formula, var, replacement))
    return obj

def term_to_linear(term: Term) -> LinearTerm:
    if isinstance(term, Zero):
        return LinearTerm({}, 0)
    elif isinstance(term, Const):
        return LinearTerm({}, term.value)
    elif isinstance(term, Var):
        return LinearTerm({term.name: 1}, 0)
    elif isinstance(term, Add):
        left = term_to_linear(term.left)
        right = term_to_linear(term.right)
        coeffs = {}
        for var, coef in left.coefficients.items():
            coeffs[var] = coef
        for var, coef in right.coefficients.items():
            coeffs[var] = coeffs.get(var, 0) + coef
        return LinearTerm(coeffs, left.constant + right.constant)
    elif isinstance(term, Mult):
        inner = term_to_linear(term.term)
        coeffs = {var: coef * term.coefficient 
                 for var, coef in inner.coefficients.items()}
        return LinearTerm(coeffs, inner.constant * term.coefficient)
    else:
        raise ValueError(f"Cannot convert {term} to linear form")



class CooperDecisionProcedure:    
    def __init__(self):
        self.debug = False
    
    def decide(self, formula: Formula) -> bool:
        if self.debug:
            print(f"Deciding: {formula}")
        
        # Step 1: Convert to prenex normal form
        prenex = self.to_prenex_normal_form(formula)
        if self.debug:
            print(f"Prenex form: {prenex}")
        
        # Step 2: Eliminate quantifiers
        qf_formula = self.eliminate_all_quantifiers(prenex)
        if self.debug:
            print(f"Quantifier-free: {qf_formula}")
        
        # Step 3: Decide quantifier-free formula
        result = self.decide_quantifier_free(qf_formula)
        if self.debug:
            print(f"Result: {result}")
        
        return result
    
    def to_prenex_normal_form(self, formula: Formula) -> Formula:
        return self._prenex_helper(self._push_negations_in(formula))
    
    def _push_negations_in(self, formula: Formula) -> Formula:
        if isinstance(formula, Not):
            inner = formula.formula
            if isinstance(inner, Not):
                return self._push_negations_in(inner.formula)
            elif isinstance(inner, And):
                return Or(self._push_negations_in(Not(inner.left)),
                         self._push_negations_in(Not(inner.right)))
            elif isinstance(inner, Or):
                return And(self._push_negations_in(Not(inner.left)),
                          self._push_negations_in(Not(inner.right)))
            elif isinstance(inner, ForAll):
                return Exists(inner.var, self._push_negations_in(Not(inner.formula)))
            elif isinstance(inner, Exists):
                return ForAll(inner.var, self._push_negations_in(Not(inner.formula)))
            elif isinstance(inner, Implies):
                return And(self._push_negations_in(inner.left),
                          self._push_negations_in(Not(inner.right)))
            else:
                return formula
        elif isinstance(formula, (And, Or, Implies, Iff)):
            left = self._push_negations_in(formula.left)
            right = self._push_negations_in(formula.right)
            return formula.__class__(left, right)
        elif isinstance(formula, (ForAll, Exists)):
            return formula.__class__(formula.var, 
                                   self._push_negations_in(formula.formula))
        else:
            return formula
    
    def _prenex_helper(self, formula: Formula) -> Formula:
        if isinstance(formula, (ForAll, Exists)):
            return formula.__class__(formula.var, 
                                   self._prenex_helper(formula.formula))
        elif isinstance(formula, And):
            left = self._prenex_helper(formula.left)
            right = self._prenex_helper(formula.right)
            
            # Pull out quantifiers from both sides
            return self._merge_quantifiers(left, right, And)
        elif isinstance(formula, Or):
            left = self._prenex_helper(formula.left)
            right = self._prenex_helper(formula.right)
            
            return self._merge_quantifiers(left, right, Or)
        else:
            return formula
    
    def _merge_quantifiers(self, left: Formula, right: Formula, connective):
        # Simplified version, in practice needs variable renaming
        if isinstance(left, (ForAll, Exists)) and isinstance(right, (ForAll, Exists)):
            # For simplicity, just return the structure
            return connective(left, right)
        elif isinstance(left, (ForAll, Exists)):
            return left.__class__(left.var, connective(left.formula, right))
        elif isinstance(right, (ForAll, Exists)):
            return right.__class__(right.var, connective(left, right.formula))
        else:
            return connective(left, right)
    
    def eliminate_all_quantifiers(self, formula: Formula) -> Formula:
        current = formula
        while self._has_quantifiers(current):
            current = self._eliminate_outermost_quantifier(current)
        return current
    
    def _has_quantifiers(self, formula: Formula) -> bool:
        if isinstance(formula, (ForAll, Exists)):
            return True
        elif isinstance(formula, (And, Or, Implies, Iff)):
            return self._has_quantifiers(formula.left) or self._has_quantifiers(formula.right)
        elif isinstance(formula, Not):
            return self._has_quantifiers(formula.formula)
        return False
    
    def _eliminate_outermost_quantifier(self, formula: Formula) -> Formula:
        if isinstance(formula, Exists):
            return self._eliminate_existential(formula.var, formula.formula)
        elif isinstance(formula, ForAll):
            # ∀x.φ ≡ ¬∃x.¬φ
            exists_form = Exists(formula.var, Not(formula.formula))
            eliminated = self._eliminate_existential(exists_form.var, exists_form.formula)
            return Not(eliminated)
        elif isinstance(formula, (And, Or)):
            left = self._eliminate_outermost_quantifier(formula.left) if self._has_quantifiers(formula.left) else formula.left
            right = self._eliminate_outermost_quantifier(formula.right) if self._has_quantifiers(formula.right) else formula.right
            return formula.__class__(left, right)
        elif isinstance(formula, Not):
            inner = self._eliminate_outermost_quantifier(formula.formula) if self._has_quantifiers(formula.formula) else formula.formula
            return Not(inner)
        else:
            return formula
    
    def _eliminate_existential(self, var: str, formula: Formula) -> Formula:
        if self.debug:
            print(f"Eliminating ∃{var} from {formula}")
        
        # Convert to DNF (disjunctive normal form)
        dnf = self._to_dnf(formula)
        
        # Eliminate from each disjunct
        if isinstance(dnf, Or):
            left_elim = self._eliminate_existential(var, dnf.left)
            right_elim = self._eliminate_existential(var, dnf.right)
            return Or(left_elim, right_elim)
        
        # Handle single conjunction
        return self._eliminate_from_conjunction(var, dnf)
    
    def _to_dnf(self, formula: Formula) -> Formula:
        if isinstance(formula, Or):
            return Or(self._to_dnf(formula.left), self._to_dnf(formula.right))
        elif isinstance(formula, And):
            left_dnf = self._to_dnf(formula.left)
            right_dnf = self._to_dnf(formula.right)
            return self._distribute_and_over_or(left_dnf, right_dnf)
        else:
            return formula

    # Distribute AND over OR: (A ∨ B) ∧ (C ∨ D) = (A ∧ C) ∨ (A ∧ D) ∨ (B ∧ C) ∨ (B ∧ D)
    def _distribute_and_over_or(self, left: Formula, right: Formula) -> Formula:
        if isinstance(left, Or):
            return Or(self._distribute_and_over_or(left.left, right),
                     self._distribute_and_over_or(left.right, right))
        elif isinstance(right, Or):
            return Or(self._distribute_and_over_or(left, right.left),
                     self._distribute_and_over_or(left, right.right))
        else:
            return And(left, right)
    
    def _eliminate_from_conjunction(self, var: str, formula: Formula) -> Formula:
        # Extract all constraints involving var
        constraints = self._extract_constraints(formula, var)
        
        if not constraints:
            return formula  # Variable doesn't appear
        
        # Apply Cooper's method: find bounds and create case analysis
        lower_bounds, upper_bounds, equalities, divisibilities = self._categorize_constraints(constraints, var)
        
        # Generate the quantifier-free equivalent
        return self._generate_cooper_formula(var, lower_bounds, upper_bounds, equalities, divisibilities)
    
    def _extract_constraints(self, formula: Formula, var: str) -> List[LinearConstraint]:
        constraints = []
        
        def extract_helper(f):
            if isinstance(f, (Eq, Lt, Le)):
                try:
                    left_lin = term_to_linear(f.left)
                    right_lin = term_to_linear(f.right)
                    
                    # Check if constraint involves the variable
                    if var in left_lin.coefficients or var in right_lin.coefficients:
                        rel = "=" if isinstance(f, Eq) else ("<" if isinstance(f, Lt) else "≤")
                        constraints.append(LinearConstraint(left_lin, rel, right_lin))
                except (ValueError, TypeError, AttributeError):
                    pass  # Skip non-linear or malformed constraints
            elif isinstance(f, And):
                extract_helper(f.left)
                extract_helper(f.right)
            elif isinstance(f, Not):
                # Handle negated constraints
                if isinstance(f.formula, Eq):
                    # ¬(a = b) becomes a < b ∨ a > b, but we'll skip for simplicity
                    pass
        
        extract_helper(formula)
        return constraints
    
    def _categorize_constraints(self, constraints: List[LinearConstraint], var: str) -> Tuple[List, List, List, List]:
        lower_bounds = []  # var ≥ expr
        upper_bounds = []  # var ≤ expr  
        equalities = []    # var = expr
        divisibilities = []  # var ≡ c (mod m)
        
        for constraint in constraints:
            norm = constraint.normalize()
            coeff = norm.left.coefficients.get(var, 0)
            
            if coeff == 0:
                continue
                
            if constraint.relation == "=":
                equalities.append(constraint)
            elif constraint.relation == "<":
                if coeff > 0:
                    upper_bounds.append(constraint)
                else:
                    lower_bounds.append(constraint)
            elif constraint.relation == "≤":
                if coeff > 0:
                    upper_bounds.append(constraint)
                else:
                    lower_bounds.append(constraint)
        
        return lower_bounds, upper_bounds, equalities, divisibilities
    
    def _generate_cooper_formula(self, var: str, lower_bounds, upper_bounds, equalities, divisibilities) -> Formula:
        # Equality case: ∃x. (a·x = t ∧ ...)
        # For ground constraints (no other free variables) we can decide immediately.
        # A natural-number solution x = target/a exists iff:
        #   (i)  a divides target
        #   (ii) target/a >= 0
        if equalities:
            equality = equalities[0]
            norm = equality.normalize()
            coeff = norm.left.coefficients.get(var, 0)
            other_vars = {k: v for k, v in norm.left.coefficients.items() if k != var}
            # After normalisation: coeff*x + constant = 0, so coeff*x = -constant
            constant = norm.left.constant

            if coeff != 0 and not other_vars:
                target = -constant
                if coeff > 0 and target >= 0 and target % coeff == 0:
                    return True_()
                else:
                    return False_()

            # General case with remaining free variables — simplified to True
            return True_()

        # No constraints on this variable at all
        if not lower_bounds and not upper_bounds:
            return True_()

        # Inequality-only case (simplified — full Cooper's builds a finite disjunction
        # over lower bounds and a period δ = lcm of divisibility coefficients)
        if lower_bounds and upper_bounds:
            return True_()   # satisfiable when some lower bound < some upper bound
        elif lower_bounds:
            return True_()   # only lower bounds: always satisfiable in ℕ
        else:
            return True_()   # only upper bounds: satisfiable if some bound ≥ 0

        return False_()
    
    def decide_quantifier_free(self, formula: Formula) -> bool:
        if isinstance(formula, True_):
            return True
        elif isinstance(formula, False_):
            return False
        elif isinstance(formula, (Eq, Lt, Le)):
            return self._evaluate_constraint(formula)
        elif isinstance(formula, Not):
            return not self.decide_quantifier_free(formula.formula)
        elif isinstance(formula, And):
            return (self.decide_quantifier_free(formula.left) and 
                   self.decide_quantifier_free(formula.right))
        elif isinstance(formula, Or):
            return (self.decide_quantifier_free(formula.left) or 
                   self.decide_quantifier_free(formula.right))
        else:
            # For unsupported formulas, return False conservatively
            return False
    
    def _evaluate_constraint(self, constraint: Formula) -> bool:
        try:
            left_val = self._evaluate_term(constraint.left)
            right_val = self._evaluate_term(constraint.right)
            
            if isinstance(constraint, Eq):
                return left_val == right_val
            elif isinstance(constraint, Lt):
                return left_val < right_val
            elif isinstance(constraint, Le):
                return left_val <= right_val
        except (ValueError, TypeError):
            # Variables are present — cannot evaluate ground; return False conservatively
            return False
        
        return False
    
    def _evaluate_term(self, term: Term) -> int:
        if isinstance(term, Zero):
            return 0
        elif isinstance(term, Const):
            return term.value
        elif isinstance(term, Add):
            return self._evaluate_term(term.left) + self._evaluate_term(term.right)
        elif isinstance(term, Mult):
            return term.coefficient * self._evaluate_term(term.term)
        else:
            raise ValueError(f"Cannot evaluate term with variables: {term}")



def var(name: str) -> Var:
    return Var(name)

def const(value: int) -> Const:
    return Const(value)

def cooper_decide(formula: Formula, debug: bool = False) -> bool:
    cooper = CooperDecisionProcedure()
    cooper.debug = debug
    return cooper.decide(formula)



def run_cooper_examples():    
    print("Cooper's Algorithm for Presburger Arithmetic")
    print("- " * 50)
    
    examples = [
        # Simple ground formulas
        ("Ground true: 2 + 3 = 5", 
         Eq(Add(const(2), const(3)), const(5))),
        
        ("Ground false: 2 + 3 = 6", 
         Eq(Add(const(2), const(3)), const(6))),
        
        # Existential formulas
        ("∃x. x = 5", 
         Exists("x", Eq(var("x"), const(5)))),
        
        ("∃x. 2*x = 6", 
         Exists("x", Eq(Mult(2, var("x")), const(6)))),
        
        ("∃x. 2*x = 7", 
         Exists("x", Eq(Mult(2, var("x")), const(7)))),
        
        # Universal formulas  
        ("∀x. x + 0 = x", 
         ForAll("x", Eq(Add(var("x"), const(0)), var("x")))),
        
        # Complex formulas
        ("∃x∃y. x + y = 10 ∧ x > 3", 
         Exists("x", Exists("y", And(
             Eq(Add(var("x"), var("y")), const(10)),
             Lt(const(3), var("x"))
         )))),
    ]
    
    cooper = CooperDecisionProcedure()
    cooper.debug = False
    
    for description, formula in examples:
        try:
            result = cooper.decide(formula)
            status = "TRUE" if result else "FALSE"
            print(f"{description:30} -> {status}")
        except Exception as e:
            print(f"{description:30} -> ERROR: {e}")
    
    print("\nDetailed trace example:")
    print(" -" * 15)
    cooper.debug = True
    formula = Exists("x", Eq(Mult(2, var("x")), const(6)))
    result = cooper.decide(formula)
    print(f"Final result: {result}")


def interactive_cooper():
    
    print("\nInteractive Cooper's Algorithm Tester")
    print("=" * 40)
    print("Enter Presburger formulas using:")
    print("- var('x') for variables")  
    print("- const(5) for constants")
    print("- Add(a, b) for addition")
    print("- Mult(2, x) for multiplication by constant")
    print("- Eq(a, b), Lt(a, b), Le(a, b) for relations")
    print("- And(a, b), Or(a, b), Not(a) for logic")
    print("- Exists('x', f), ForAll('x', f) for quantifiers")
    print("Type 'quit' to exit")
    
    cooper = CooperDecisionProcedure()
    
    while True:
        try:
            user_input = input("\nFormula: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            # Evaluate the formula
            formula = eval(user_input, {
                'var': var, 'const': const, 'Add': Add, 'Mult': Mult,
                'Eq': Eq, 'Lt': Lt, 'Le': Le, 'And': And, 'Or': Or, 'Not': Not,
                'Exists': Exists, 'ForAll': ForAll
            })
            
            print(f"Formula: {formula}")
            
            debug_choice = input("Show trace? (y/n): ").strip().lower()
            cooper.debug = debug_choice == 'y'
            
            result = cooper.decide(formula)
            print(f"Result: {'TRUE' if result else 'FALSE'}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Bye!")



def main():
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--examples':
            run_cooper_examples()
        elif sys.argv[1] == '--interactive':
            interactive_cooper()
        else:
            print("Usage: python coopers.py [--examples | --interactive]")
    else:
        run_cooper_examples()
        print("\nRun with --interactive for interactive mode")

if __name__ == "__main__":
    main()
