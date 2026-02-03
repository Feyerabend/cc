"""
Advanced Demonstrations for the Functional VM

More complex examples showing:
- Fixed-point recursion
- Complex pattern matching
- Church encodings
- Continuation-passing style
- Monadic do-notation style
"""

from functional_vm import *


def demo_church_numerals():
    """Demo: Church encoding of natural numbers."""
    print("=" * 60)
    print("DEMO: Church Numerals")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Church numeral 0 = λf. λx. x
    zero = lam("f", lam("x", var("x")))
    
    # Church numeral 1 = λf. λx. f x
    one = lam("f", lam("x", app(var("f"), var("x"))))
    
    # Church numeral 2 = λf. λx. f (f x)
    two = lam("f", lam("x", 
              app(var("f"), app(var("f"), var("x")))))
    
    # Church numeral 3 = λf. λx. f (f (f x))
    three = lam("f", lam("x",
                app(var("f"), 
                    app(var("f"), 
                        app(var("f"), var("x"))))))
    
    # To "run" a church numeral, we apply it to (λx. x + 1) and 0
    increment = lam("x", add(var("x"), lit_int(1)))
    
    # Apply: three increment 0
    program = app(app(three, increment), lit_int(0))
    result = vm.run(program)
    
    print(f"Church numeral 3 applied to increment and 0 = {result}")
    print()


def demo_church_booleans():
    """Demo: Church encoding of booleans."""
    print("=" * 60)
    print("DEMO: Church Booleans")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Church true = λt. λf. t
    true_church = lam("t", lam("f", var("t")))
    
    # Church false = λt. λf. f
    false_church = lam("t", lam("f", var("f")))
    
    # Church if: if_then_else b t f = b t f
    # Test: true "yes" "no" = "yes"
    program1 = app(app(true_church, lit_str("yes")), lit_str("no"))
    result1 = vm.run(program1)
    print(f'Church true "yes" "no" = {result1}')
    
    # Test: false "yes" "no" = "no"
    program2 = app(app(false_church, lit_str("yes")), lit_str("no"))
    result2 = vm.run(program2)
    print(f'Church false "yes" "no" = {result2}')
    
    # Church AND: λp. λq. p q p
    and_church = lam("p", lam("q", 
                     app(app(var("p"), var("q")), var("p"))))
    
    # true AND true = true
    result3 = vm.run(app(app(app(app(and_church, true_church), true_church),
                             lit_str("T")), lit_str("F")))
    print(f'true AND true = {result3}')
    print()


def demo_option_chaining():
    """Demo: Railway-oriented programming with Result."""
    print("=" * 60)
    print("DEMO: Railway-Oriented Programming")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Simulate: parse_int -> validate_positive -> divide_by_2
    # All returning Result types
    
    # Step 1: "Parse" a number (wrap in Ok)
    parse = lam("x", ok(var("x")))
    
    # Step 2: Validate it's positive
    validate = lam("x", 
                  if_expr(
                      lt(lit_int(0), var("x")),
                      ok(var("x")),
                      err(lit_str("Not positive"))
                  ))
    
    # Step 3: Divide by 2
    divide_by_2 = lam("x", ok(div(var("x"), lit_int(2))))
    
    # Chain them all: parse(10) >>= validate >>= divide_by_2
    program_success = flatmap_node(
        divide_by_2,
        flatmap_node(
            validate,
            app(parse, lit_int(10))
        )
    )
    
    result_success = vm.run(program_success)
    print(f"Pipeline with 10: {result_success}")
    
    # Now with a negative number (should fail at validate)
    program_fail = flatmap_node(
        divide_by_2,
        flatmap_node(
            validate,
            app(parse, lit_int(-5))
        )
    )
    
    result_fail = vm.run(program_fail)
    print(f"Pipeline with -5: {result_fail}")
    print()


def demo_list_combinators():
    """Demo: List combinators (sum, product, etc.)."""
    print("=" * 60)
    print("DEMO: List Combinators")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Simple map example
    program1 = map_node(
        lam("x", mul(var("x"), var("x"))),  # Square
        list_node(lit_int(1), lit_int(2), lit_int(3), lit_int(4))
    )
    result1 = vm.run(program1)
    print(f"map square [1,2,3,4] = {result1}")
    
    # FlatMap example: duplicate each element
    # [1,2,3] >>= (x -> [x, x]) = [1,1,2,2,3,3]
    program2 = flatmap_node(
        lam("x", list_node(var("x"), var("x"))),
        list_node(lit_int(1), lit_int(2), lit_int(3))
    )
    result2 = vm.run(program2)
    print(f"flatMap (x -> [x,x]) [1,2,3] = {result2}")
    print()


def demo_nested_patterns():
    """Demo: Nested pattern matching."""
    print("=" * 60)
    print("DEMO: Nested Pattern Matching")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Match on Some(Ok(42))
    # | Some(Ok(x)) -> x * 2
    # | Some(Err(e)) -> 0
    # | Nothing -> -1
    
    nested_value = some(ok(lit_int(42)))
    
    program = match(
        nested_value,
        case({'type': 'Some', 'inner': {
                'type': 'Ok', 'inner': {'type': 'var', 'name': 'x'}
              }},
             mul(var("x"), lit_int(2))),
        case({'type': 'Some', 'inner': {
                'type': 'Err', 'inner': {'type': 'var', 'name': 'e'}
              }},
             lit_int(0)),
        case({'type': 'Nothing'},
             lit_int(-1))
    )
    
    result = vm.run(program)
    print(f"match Some(Ok(42)) -> {result}")
    print()


def demo_currying():
    """Demo: Manual currying of multi-argument functions."""
    print("=" * 60)
    print("DEMO: Currying")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Curried add: λa. λb. a + b
    curried_add = lam("a", lam("b", add(var("a"), var("b"))))
    
    # Partial application: add_five = add 5
    add_five = app(curried_add, lit_int(5))
    
    # Full application: add_five 10 = 15
    program = let("add_five", add_five,
                  app(var("add_five"), lit_int(10)))
    
    result = vm.run(program)
    print(f"(add 5) 10 = {result}")
    
    # Three-argument curried function: λa. λb. λc. a + b + c
    add3 = lam("a", lam("b", lam("c",
           add(add(var("a"), var("b")), var("c")))))
    
    # Partial: add3 1 2 = λc. 1 + 2 + c
    partial = app(app(add3, lit_int(1)), lit_int(2))
    
    # Full: (add3 1 2) 3 = 6
    program2 = app(partial, lit_int(3))
    result2 = vm.run(program2)
    print(f"(add3 1 2) 3 = {result2}")
    print()


def demo_combinators():
    """Demo: SKI combinator calculus."""
    print("=" * 60)
    print("DEMO: SKI Combinators")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # S combinator: λx. λy. λz. (x z)(y z)
    s_comb = lam("x", lam("y", lam("z",
             app(app(var("x"), var("z")),
                 app(var("y"), var("z"))))))
    
    # K combinator: λx. λy. x
    k_comb = lam("x", lam("y", var("x")))
    
    # I combinator: λx. x (can be derived as SKK)
    i_comb = lam("x", var("x"))
    
    # Test K: K 42 100 = 42
    program1 = app(app(k_comb, lit_int(42)), lit_int(100))
    result1 = vm.run(program1)
    print(f"K 42 100 = {result1}")
    
    # Test I: I 42 = 42
    program2 = app(i_comb, lit_int(42))
    result2 = vm.run(program2)
    print(f"I 42 = {result2}")
    
    # Test S with simple functions
    # S K K x = K x (K x) = x (so S K K is identity)
    skk = app(app(s_comb, k_comb), k_comb)
    program3 = app(skk, lit_int(42))
    result3 = vm.run(program3)
    print(f"S K K 42 = {result3} (should be 42)")
    print()


def demo_option_traversal():
    """Demo: Traversing a list of Maybe values."""
    print("=" * 60)
    print("DEMO: Option Traversal")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Map over a list, producing Maybe values
    # [1,2,3].map(x -> if x > 2 then Some(x) else Nothing)
    to_maybe = lam("x",
                  if_expr(
                      lt(lit_int(2), var("x")),
                      some(var("x")),
                      nothing_node()
                  ))
    
    program = map_node(
        to_maybe,
        list_node(lit_int(1), lit_int(2), lit_int(3), lit_int(4))
    )
    
    result = vm.run(program)
    print(f"[1,2,3,4].map(x -> if x > 2 then Some(x) else Nothing)")
    print(f"  = {result}")
    print()


def demo_complex_let():
    """Demo: Complex nested let bindings."""
    print("=" * 60)
    print("DEMO: Complex Let Bindings")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Pythagorean theorem: sqrt(a² + b²)
    # (without sqrt, just compute a² + b²)
    program = let("a", lit_int(3),
              let("b", lit_int(4),
              let("square", lam("x", mul(var("x"), var("x"))),
              let("a_sq", app(var("square"), var("a")),
              let("b_sq", app(var("square"), var("b")),
                  add(var("a_sq"), var("b_sq")))))))
    
    result = vm.run(program)
    print(f"3² + 4² = {result}")
    print()


def demo_eta_expansion():
    """Demo: Eta expansion/reduction."""
    print("=" * 60)
    print("DEMO: Eta Expansion")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Original function: λx. x + 1
    original = lam("x", add(var("x"), lit_int(1)))
    
    # Eta-expanded: λy. (λx. x + 1) y
    expanded = lam("y", app(original, var("y")))
    
    # Both should behave identically
    program1 = app(original, lit_int(5))
    result1 = vm.run(program1)
    print(f"original(5) = {result1}")
    
    program2 = app(expanded, lit_int(5))
    result2 = vm.run(program2)
    print(f"expanded(5) = {result2}")
    
    print("Both produce the same result (eta-equivalence)")
    print()


def demo_point_free():
    """Demo: Point-free style programming."""
    print("=" * 60)
    print("DEMO: Point-Free Style")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Pointful: λx. (x + 1) * 2
    pointful = lam("x", mul(add(var("x"), lit_int(1)), lit_int(2)))
    
    # Point-free (via composition): ((*2) . (+1))
    # compose = λf. λg. λx. f(g(x))
    compose = lam("f", lam("g", lam("x",
              app(var("f"), app(var("g"), var("x"))))))
    
    add_one = lam("x", add(var("x"), lit_int(1)))
    mul_two = lam("x", mul(var("x"), lit_int(2)))
    
    # Point-free version: compose mul_two add_one
    point_free = app(app(compose, mul_two), add_one)
    
    # Test both
    program1 = app(pointful, lit_int(5))
    result1 = vm.run(program1)
    print(f"pointful(5) = {result1}")
    
    program2 = app(point_free, lit_int(5))
    result2 = vm.run(program2)
    print(f"point-free(5) = {result2}")
    print()


def demo_all():
    """Run all advanced demos."""
    demo_church_numerals()
    demo_church_booleans()
    demo_option_chaining()
    demo_list_combinators()
    demo_nested_patterns()
    demo_currying()
    demo_combinators()
    demo_option_traversal()
    demo_complex_let()
    demo_eta_expansion()
    demo_point_free()
    
    print("=" * 60)
    print("All advanced demos completed!")
    print("=" * 60)


if __name__ == "__main__":
    demo_all()
