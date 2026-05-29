#!/usr/bin/env python3
import sys
import traceback
from presburger import *


def run_test(test_name, test_func):
    try:
        test_func()
        print(f"ok {test_name}")
        return True
    except Exception as e:
        print(f"not ok {test_name}: {str(e)}")
        traceback.print_exc()
        return False

def test_zero_creation():
    z = Zero()
    assert str(z) == "0"
    assert z == Zero()
    assert hash(z) == hash(Zero())

def test_var_creation():
    x = Var("x")
    y = Var("y")
    assert str(x) == "x"
    assert str(y) == "y"
    assert x == Var("x")
    assert x != y
    assert hash(x) == hash(Var("x"))

def test_succ_creation():
    z = Zero()
    s_z = Succ(z)
    assert str(s_z) == "S(0)"
    
    x = Var("x")
    s_x = Succ(x)
    assert str(s_x) == "S(x)"
    assert s_x == Succ(Var("x"))

def test_add_creation():
    x = Var("x")
    y = Var("y")
    add_xy = Add(x, y)
    assert str(add_xy) == "(x + y)"
    
    z = Zero()
    add_xz = Add(x, z)
    assert str(add_xz) == "(x + 0)"

def test_mult_creation():
    x = Var("x")
    mult_2x = Mult(2, x)
    assert str(mult_2x) == "2*x"
    
    mult_1x = Mult(1, x)
    assert str(mult_1x) == "x"
    
    mult_0x = Mult(0, x)
    assert str(mult_0x) == "0*x"

def test_eq_creation():
    x = Var("x")
    y = Var("y")
    eq = Eq(x, y)
    assert str(eq) == "(x = y)"
    assert eq == Eq(Var("x"), Var("y"))

def test_lt_creation():
    x = Var("x")
    y = Var("y")
    lt = Lt(x, y)
    assert str(lt) == "(x < y)"

def test_le_creation():
    x = Var("x")
    y = Var("y")
    le = Le(x, y)
    assert str(le) == "(x ≤ y)"

def test_divisibility_creation():
    x = Var("x")
    div = Divisibility(2, x)
    assert str(div) == "(2 | x)"
    assert isinstance(div, Formula)

    div3 = Divisibility(3, Add(x, Zero()))
    assert str(div3) == "(3 | (x + 0))"

def test_divisibility_free_vars():
    x = Var("x")
    y = Var("y")
    div = Divisibility(2, Add(x, y))
    assert get_free_vars(div) == {"x", "y"}

    div_ground = Divisibility(3, Zero())
    assert get_free_vars(div_ground) == set()

def test_divisibility_substitution():
    x = Var("x")
    y = Var("y")
    div = Divisibility(2, Add(x, y))
    result = substitute_formula(div, "x", Zero())
    assert str(result) == "(2 | (0 + y))"
    # Substituting a non-present variable leaves formula unchanged
    result2 = substitute_formula(div, "z", Zero())
    assert str(result2) == str(div)

def test_evaluate_term():
    assert evaluate_term(Zero()) == 0
    assert evaluate_term(num(3)) == 3
    assert evaluate_term(Var("x"), {"x": 7}) == 7
    assert evaluate_term(Add(num(2), num(3))) == 5
    assert evaluate_term(Succ(num(4))) == 5
    assert evaluate_term(Mult(3, Var("x")), {"x": 4}) == 12
    assert evaluate_term(Add(Var("x"), Var("y")), {"x": 3, "y": 4}) == 7

    try:
        evaluate_term(Var("x"))  # unbound variable
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

def test_evaluate_formula_ground():
    assert evaluate_formula(Eq(num(3), num(3)))
    assert not evaluate_formula(Eq(num(3), num(4)))
    assert evaluate_formula(Lt(num(2), num(5)))
    assert not evaluate_formula(Lt(num(5), num(2)))
    assert evaluate_formula(Le(num(3), num(3)))
    assert not evaluate_formula(Le(num(4), num(3)))

def test_evaluate_formula_divisibility():
    assert evaluate_formula(Divisibility(2, num(6)))
    assert not evaluate_formula(Divisibility(2, num(7)))
    assert evaluate_formula(Divisibility(3, num(9)))
    assert not evaluate_formula(Divisibility(3, num(8)))
    # 2 | (x + x) for any x
    x = Var("x")
    for v in range(5):
        assert evaluate_formula(Divisibility(2, Add(x, x)), {"x": v})

def test_evaluate_formula_logical():
    t = Eq(num(1), num(1))
    f = Eq(num(1), num(2))
    assert evaluate_formula(Not(f))
    assert not evaluate_formula(Not(t))
    assert evaluate_formula(And(t, t))
    assert not evaluate_formula(And(t, f))
    assert evaluate_formula(Or(t, f))
    assert not evaluate_formula(Or(f, f))
    assert evaluate_formula(Implies(f, t))   # false => anything
    assert evaluate_formula(Implies(f, f))
    assert not evaluate_formula(Implies(t, f))
    assert evaluate_formula(Iff(t, t))
    assert evaluate_formula(Iff(f, f))
    assert not evaluate_formula(Iff(t, f))

def test_evaluate_formula_with_env():
    x = Var("x")
    y = Var("y")
    # x + 3 = 5 with x=2
    assert evaluate_formula(Eq(Add(x, num(3)), num(5)), {"x": 2})
    assert not evaluate_formula(Eq(Add(x, num(3)), num(5)), {"x": 3})
    # x <= y with x=3, y=5
    assert evaluate_formula(Le(x, y), {"x": 3, "y": 5})
    assert not evaluate_formula(Le(x, y), {"x": 5, "y": 3})

def test_evaluate_formula_quantifier_raises():
    x = Var("x")
    try:
        evaluate_formula(ForAll("x", Eq(x, x)))
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

def test_not_creation():
    x = Var("x")
    y = Var("y")
    eq = Eq(x, y)
    not_eq = Not(eq)
    assert str(not_eq) == "¬(x = y)"

def test_and_creation():
    x = Var("x")
    y = Var("y")
    z = Var("z")
    eq1 = Eq(x, y)
    eq2 = Eq(y, z)
    and_formula = And(eq1, eq2)
    assert str(and_formula) == "((x = y) ∧ (y = z))"

def test_or_creation():
    x = Var("x")
    y = Var("y")
    z = Var("z")
    eq1 = Eq(x, y)
    eq2 = Eq(y, z)
    or_formula = Or(eq1, eq2)
    assert str(or_formula) == "((x = y) ∨ (y = z))"

def test_implies_creation():
    x = Var("x")
    y = Var("y")
    premise = Eq(x, Zero())
    conclusion = Eq(Add(x, y), y)
    implies_formula = Implies(premise, conclusion)
    assert str(implies_formula) == "((x = 0) → ((x + y) = y))"

def test_iff_creation():
    x = Var("x")
    y = Var("y")
    left = Eq(x, y)
    right = Eq(y, x)
    iff_formula = Iff(left, right)
    assert str(iff_formula) == "((x = y) ↔ (y = x))"

def test_forall_creation():
    x = Var("x")
    body = Eq(Add(x, Zero()), x)
    forall_formula = ForAll("x", body)
    assert str(forall_formula) == "(∀x. ((x + 0) = x))"

def test_exists_creation():
    x = Var("x")
    body = Eq(x, Succ(Zero()))
    exists_formula = Exists("x", body)
    assert str(exists_formula) == "(∃x. (x = S(0)))"

def test_get_free_vars_terms():
    assert get_free_vars(Zero()) == set()
    assert get_free_vars(Var("x")) == {"x"}
    assert get_free_vars(Succ(Var("x"))) == {"x"}
    assert get_free_vars(Add(Var("x"), Var("y"))) == {"x", "y"}
    assert get_free_vars(Mult(3, Var("x"))) == {"x"}

def test_get_free_vars_formulas():
    x = Var("x")
    y = Var("y")
    
    assert get_free_vars(Eq(x, y)) == {"x", "y"}
    assert get_free_vars(Not(Eq(x, y))) == {"x", "y"}
    assert get_free_vars(And(Eq(x, y), Eq(y, Zero()))) == {"x", "y"}

def test_get_free_vars_quantifiers():
    x = Var("x")
    y = Var("y")
    
    forall_formula = ForAll("x", Eq(x, y))
    assert get_free_vars(forall_formula) == {"y"}
    
    exists_formula = Exists("x", Eq(x, y))
    assert get_free_vars(exists_formula) == {"y"}
    
    nested = ForAll("x", Exists("y", Eq(x, y)))
    assert get_free_vars(nested) == set()

def test_substitute_var_terms():
    x = Var("x")
    y = Var("y")
    replacement = Succ(Zero())
    
    assert substitute_var(x, "x", replacement) == replacement
    assert substitute_var(y, "x", replacement) == y
    assert substitute_var(Zero(), "x", replacement) == Zero()
    
    succ_x = Succ(x)
    succ_replaced = substitute_var(succ_x, "x", replacement)
    assert str(succ_replaced) == "S(S(0))"
    
    add_xy = Add(x, y)
    add_replaced = substitute_var(add_xy, "x", replacement)
    assert str(add_replaced) == "(S(0) + y)"

def test_substitute_formula():
    x = Var("x")
    y = Var("y")
    replacement = Zero()
    
    eq_xy = Eq(x, y)
    eq_replaced = substitute_formula(eq_xy, "x", replacement)
    assert str(eq_replaced) == "(0 = y)"
    
    not_eq = Not(eq_xy)
    not_replaced = substitute_formula(not_eq, "x", replacement)
    assert str(not_replaced) == "¬(0 = y)"
    
    forall_formula = ForAll("x", Eq(x, y))
    forall_replaced = substitute_formula(forall_formula, "x", replacement)
    assert str(forall_replaced) == str(forall_formula)  # x is bound, no substitution
    
    forall_replaced_y = substitute_formula(forall_formula, "y", replacement)
    assert str(forall_replaced_y) == "(∀x. (x = 0))"

def test_num_function():
    assert str(num(0)) == "0"
    assert str(num(1)) == "S(0)"
    assert str(num(2)) == "S(S(0))"
    assert str(num(3)) == "S(S(S(0)))"
    
    try:
        num(-1)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

def test_var_function():
    x = var("x")
    assert isinstance(x, Var)
    assert x.name == "x"
    assert str(x) == "x"

def test_presburger_axioms():
    axioms = PresburgerAxioms()
    assert len(axioms.axioms) == 8
    
    # Check that all axioms are formulas
    for axiom in axioms.axioms:
        assert isinstance(axiom, Formula)
    
    # Check specific axioms exist (by string representation)
    axiom_strings = [str(ax) for ax in axioms.axioms]
    assert "(∀x. ¬(S(x) = 0))" in axiom_strings
    assert "(∀x. ((x + 0) = x))" in axiom_strings

def test_proof_system_creation():
    ps = ProofSystem()
    assert isinstance(ps.axioms, PresburgerAxioms)
    assert len(ps.proven_formulas) == len(ps.axioms.axioms)
    assert ps.proof_history == []

def test_is_axiom():
    ps = ProofSystem()
    x = var("x")
    axiom = ForAll("x", Eq(Add(x, Zero()), x))
    assert ps.is_axiom(axiom)
    
    non_axiom = Eq(var("a"), var("b"))
    assert not ps.is_axiom(non_axiom)

def test_is_proven():
    ps = ProofSystem()
    x = var("x")
    axiom = ForAll("x", Eq(Add(x, Zero()), x))
    assert ps.is_proven(axiom)  # axioms are initially in proven_formulas
    
    new_formula = Eq(var("a"), var("b"))
    assert not ps.is_proven(new_formula)

def test_modus_ponens():
    ps = ProofSystem()
    
    premise = Eq(var("x"), Zero())
    conclusion = Eq(Add(var("x"), var("y")), var("y"))
    implication = Implies(premise, conclusion)
    
    result = ps.modus_ponens(implication, premise)
    assert result == conclusion
    
    wrong_premise = Eq(var("x"), Succ(Zero()))
    result = ps.modus_ponens(implication, wrong_premise)
    assert result is None

def test_universal_instantiation():
    ps = ProofSystem()
    
    x = var("x")
    universal = ForAll("x", Eq(Add(x, Zero()), x))
    replacement = Succ(Zero())
    
    result = ps.universal_instantiation(universal, replacement)
    assert str(result) == "((S(0) + 0) = S(0))"
    
    non_universal = Eq(x, Zero())
    result = ps.universal_instantiation(non_universal, replacement)
    assert result is None

def test_prove_step():
    ps = ProofSystem()
    
    # Test axiom recognition
    x = var("x")
    axiom = ForAll("x", Eq(Add(x, Zero()), x))
    initial_length = len(ps.proof_history)
    result = ps.prove_step(axiom)
    assert result is True
    assert len(ps.proof_history) == initial_length + 1
    
    # Test new formula
    new_formula = Eq(var("a"), var("b"))
    initial_length = len(ps.proof_history)
    result = ps.prove_step(new_formula, "assumption")
    assert result is True
    assert len(ps.proof_history) == initial_length + 1
    assert ps.is_proven(new_formula)

def test_examples_basic():
    examples = Examples.basic_arithmetic()
    assert len(examples) == 5
    
    for name, formula in examples:
        assert isinstance(name, str)
        assert isinstance(formula, Formula)

def test_examples_logical():
    examples = Examples.logical_formulas()
    assert len(examples) == 5
    
    for name, formula in examples:
        assert isinstance(name, str)
        assert isinstance(formula, Formula)

def test_complex_term_construction():
    # Build (S(S(0)) + (x + y))
    two = num(2)
    x = var("x")
    y = var("y")
    x_plus_y = Add(x, y)
    complex_term = Add(two, x_plus_y)
    
    assert str(complex_term) == "(S(S(0)) + (x + y))"
    assert get_free_vars(complex_term) == {"x", "y"}

def test_complex_formula_construction():
    # Build ∀x∃y. (x + y = S(S(0))) → (x < S(S(0)))
    x = var("x")
    y = var("y")
    two = num(2)
    
    premise = Eq(Add(x, y), two)
    conclusion = Lt(x, two)
    implication = Implies(premise, conclusion)
    exists_formula = Exists("y", implication)
    forall_formula = ForAll("x", exists_formula)
    
    expected = "(∀x. (∃y. (((x + y) = S(S(0))) → (x < S(S(0))))))"
    assert str(forall_formula) == expected

def test_nested_substitutions():
    x = var("x")
    y = var("y")
    z = var("z")
    
    # Original: ∀x. (x + y = z)
    inner = Eq(Add(x, y), z)
    formula = ForAll("x", inner)
    
    # Substitute y with S(0)
    replacement = Succ(Zero())
    result = substitute_formula(formula, "y", replacement)
    
    expected = "(∀x. ((x + S(0)) = z))"
    assert str(result) == expected
    assert get_free_vars(result) == {"z"}

def test_proof_multiple_steps():
    ps = ProofSystem()
    
    # Try to prove some basic facts
    x = var("x")
    
    # Prove x + 0 = x (this should be an axiom)
    formula1 = ForAll("x", Eq(Add(x, Zero()), x))
    assert ps.prove_step(formula1)
    
    # Add another formula
    formula2 = Eq(Add(var("a"), Zero()), var("a"))
    assert ps.prove_step(formula2, "universal_instantiation")
    
    # Check proof history
    history = ps.get_proof_history()
    assert len(history) >= 2

def test_empty_variable():
    empty_var = Var("")
    assert str(empty_var) == ""
    assert empty_var.name == ""

def test_large_numbers():
    large_num = num(10)
    str_repr = str(large_num)
    # Should be S(S(S(...))) with 10 S's
    assert str_repr.count("S(") == 10
    assert str_repr.endswith("0" + ")" * 10)

def test_deeply_nested_terms():
    x = var("x")
    nested = x
    for i in range(5):
        nested = Succ(nested)
    
    expected = "S(S(S(S(S(x)))))"
    assert str(nested) == expected

def test_formula_equality_and_hashing():
    x1 = var("x")
    x2 = var("x")
    y = var("y")
    
    eq1 = Eq(x1, y)
    eq2 = Eq(x2, y)
    eq3 = Eq(y, x1)
    
    assert eq1 == eq2
    assert eq1 != eq3
    assert hash(eq1) == hash(eq2)
    
    # Test with sets (requires consistent hashing)
    formula_set = {eq1, eq2, eq3}
    assert len(formula_set) == 2  # eq1 and eq2 should be the same

def test_full_workflow():
    # Test a complete workflow from term creation to proof attempts
    
    # 1. Create terms
    x = var("x")
    y = var("y")
    zero = Zero()
    one = num(1)
    
    # 2. Build formulas
    simple_eq = Eq(Add(x, zero), x)
    complex_formula = ForAll("x", Implies(
        Eq(x, zero),
        Eq(Add(x, y), y)
    ))
    
    # 3. Initialize proof system
    ps = ProofSystem()
    
    # 4. Attempt proofs
    assert ps.prove_step(simple_eq, "assumption")
    assert ps.prove_step(complex_formula, "assumption")
    
    # 5. Verify state
    assert ps.is_proven(simple_eq)
    assert ps.is_proven(complex_formula)
    assert len(ps.get_proof_history()) >= 2

def test_substitution_preservation():
    # Test that substitutions preserve formula structure
    x = var("x")
    y = var("y")
    
    original = ForAll("z", Implies(
        Eq(Add(x, var("z")), y),
        Lt(x, y)
    ))
    
    # Substitute x with S(0)
    substituted = substitute_formula(original, "x", num(1))
    
    # Check that structure is preserved
    assert isinstance(substituted, ForAll)
    assert substituted.varname == "z"
    assert isinstance(substituted.formula, Implies)
    
    # Check that free variables changed correctly
    original_free = get_free_vars(original)
    substituted_free = get_free_vars(substituted)
    
    assert "x" in original_free
    assert "x" not in substituted_free
    assert "y" in original_free and "y" in substituted_free

def run_all_tests():
    tests = [
        ("Zero Creation", test_zero_creation),
        ("Variable Creation", test_var_creation),
        ("Successor Creation", test_succ_creation),
        ("Addition Creation", test_add_creation),
        ("Multiplication Creation", test_mult_creation),
        ("Equality Creation", test_eq_creation),
        ("Less Than Creation", test_lt_creation),
        ("Less Equal Creation", test_le_creation),
        ("Divisibility Creation", test_divisibility_creation),
        ("Divisibility Free Vars", test_divisibility_free_vars),
        ("Divisibility Substitution", test_divisibility_substitution),
        ("Evaluate Term", test_evaluate_term),
        ("Evaluate Ground Formula", test_evaluate_formula_ground),
        ("Evaluate Divisibility", test_evaluate_formula_divisibility),
        ("Evaluate Logical Connectives", test_evaluate_formula_logical),
        ("Evaluate With Environment", test_evaluate_formula_with_env),
        ("Evaluate Quantifier Raises", test_evaluate_formula_quantifier_raises),
        ("Negation Creation", test_not_creation),
        ("Conjunction Creation", test_and_creation),
        ("Disjunction Creation", test_or_creation),
        ("Implication Creation", test_implies_creation),
        ("Biconditional Creation", test_iff_creation),
        ("Universal Quantification", test_forall_creation),
        ("Existential Quantification", test_exists_creation),
        ("Free Variables in Terms", test_get_free_vars_terms),
        ("Free Variables in Formulas", test_get_free_vars_formulas),
        ("Free Variables with Quantifiers", test_get_free_vars_quantifiers),
        ("Variable Substitution in Terms", test_substitute_var_terms),
        ("Variable Substitution in Formulas", test_substitute_formula),
        ("Number Construction", test_num_function),
        ("Variable Function", test_var_function),
        ("Presburger Axioms", test_presburger_axioms),
        ("Proof System Creation", test_proof_system_creation),
        ("Axiom Recognition", test_is_axiom),
        ("Proven Formula Check", test_is_proven),
        ("Modus Ponens", test_modus_ponens),
        ("Universal Instantiation", test_universal_instantiation),
        ("Proof Steps", test_prove_step),
        ("Basic Examples", test_examples_basic),
        ("Logical Examples", test_examples_logical),
        ("Complex Term Construction", test_complex_term_construction),
        ("Complex Formula Construction", test_complex_formula_construction),
        ("Nested Substitutions", test_nested_substitutions),
        ("Multiple Proof Steps", test_proof_multiple_steps),
        ("Empty Variable Names", test_empty_variable),
        ("Large Numbers", test_large_numbers),
        ("Deeply Nested Terms", test_deeply_nested_terms),
        ("Formula Equality and Hashing", test_formula_equality_and_hashing),
        ("Full Workflow Integration", test_full_workflow),
        ("Substitution Preservation", test_substitution_preservation),
    ]
    
    passed = 0
    failed = 0
    
    print("Running Presburger Arithmetic System Tests")
    print("- " * 30)
    
    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
        else:
            failed += 1
    
    print("- " * 30)
    print(f"Tests completed: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("All tests passed!")
    else:
        print(f"{failed} test(s) failed")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
