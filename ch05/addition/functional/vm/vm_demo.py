"""
Demonstration Programs for the Functional VM

This file contains example programs showing various features of the VM:
- Lambda calculus
- Maybe/Result types
- Pattern matching
- List operations
- Monadic composition
- Higher-order functions
"""

from functional_vm import *

def demo_basic_arithmetic():
    """Demo: Basic arithmetic operations."""
    print("=" * 60)
    print("DEMO: Basic Arithmetic")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # (2 + 3) * 4
    program = mul(
        add(lit_int(2), lit_int(3)),
        lit_int(4)
    )
    
    result = vm.run(program)
    print(f"(2 + 3) * 4 = {result}")
    print()


def demo_lambda_calculus():
    """Demo: Lambda calculus and function application."""
    print("=" * 60)
    print("DEMO: Lambda Calculus")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Identity function: λx. x
    identity = lam("x", var("x"))
    program1 = app(identity, lit_int(42))
    result1 = vm.run(program1)
    print(f"(λx. x) 42 = {result1}")
    
    # Constant function: λx. λy. x
    const_fn = lam("x", lam("y", var("x")))
    program2 = app(app(const_fn, lit_int(5)), lit_int(10))
    result2 = vm.run(program2)
    print(f"(λx. λy. x) 5 10 = {result2}")
    
    # Double function: λx. x + x
    double = lam("x", add(var("x"), var("x")))
    program3 = app(double, lit_int(21))
    result3 = vm.run(program3)
    print(f"(λx. x + x) 21 = {result3}")
    print()


def demo_let_bindings():
    """Demo: Let bindings."""
    print("=" * 60)
    print("DEMO: Let Bindings")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # let x = 10 in x + 5
    program1 = let("x", lit_int(10),
                   add(var("x"), lit_int(5)))
    result1 = vm.run(program1)
    print(f"let x = 10 in x + 5 = {result1}")
    
    # let square = λx. x * x in square 7
    program2 = let("square", 
                   lam("x", mul(var("x"), var("x"))),
                   app(var("square"), lit_int(7)))
    result2 = vm.run(program2)
    print(f"let square = λx. x * x in square 7 = {result2}")
    
    # Nested let bindings
    program3 = let("x", lit_int(5),
                   let("y", lit_int(3),
                       mul(var("x"), var("y"))))
    result3 = vm.run(program3)
    print(f"let x = 5 in let y = 3 in x * y = {result3}")
    print()


def demo_maybe_type():
    """Demo: Maybe type operations."""
    print("=" * 60)
    print("DEMO: Maybe Type")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Create Some(42)
    program1 = some(lit_int(42))
    result1 = vm.run(program1)
    print(f"Some(42) = {result1}")
    
    # Create Nothing
    program2 = nothing_node()
    result2 = vm.run(program2)
    print(f"Nothing = {result2}")
    
    # Map over Maybe: Some(10).map(λx. x * 2)
    program3 = map_node(
        lam("x", mul(var("x"), lit_int(2))),
        some(lit_int(10))
    )
    result3 = vm.run(program3)
    print(f"Some(10).map(λx. x * 2) = {result3}")
    
    # FlatMap over Maybe: Some(5).flatMap(λx. Some(x + 3))
    program4 = flatmap_node(
        lam("x", some(add(var("x"), lit_int(3)))),
        some(lit_int(5))
    )
    result4 = vm.run(program4)
    print(f"Some(5).flatMap(λx. Some(x + 3)) = {result4}")
    
    # Filter Maybe: Some(10).filter(λx. x > 5)
    program5 = filter_node(
        lam("x", lt(lit_int(5), var("x"))),
        some(lit_int(10))
    )
    result5 = vm.run(program5)
    print(f"Some(10).filter(λx. x > 5) = {result5}")
    
    # Filter that fails: Some(3).filter(λx. x > 5)
    program6 = filter_node(
        lam("x", lt(lit_int(5), var("x"))),
        some(lit_int(3))
    )
    result6 = vm.run(program6)
    print(f"Some(3).filter(λx. x > 5) = {result6}")
    print()


def demo_result_type():
    """Demo: Result type operations."""
    print("=" * 60)
    print("DEMO: Result Type")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Create Ok(42)
    program1 = ok(lit_int(42))
    result1 = vm.run(program1)
    print(f"Ok(42) = {result1}")
    
    # Create Err("error")
    program2 = err(lit_str("error"))
    result2 = vm.run(program2)
    print(f'Err("error") = {result2}')
    
    # Map over Result: Ok(10).map(λx. x * 2)
    program3 = map_node(
        lam("x", mul(var("x"), lit_int(2))),
        ok(lit_int(10))
    )
    result3 = vm.run(program3)
    print(f"Ok(10).map(λx. x * 2) = {result3}")
    
    # FlatMap chain: Ok(10).flatMap(λx. Ok(x * 2))
    program4 = flatmap_node(
        lam("x", ok(mul(var("x"), lit_int(2)))),
        ok(lit_int(10))
    )
    result4 = vm.run(program4)
    print(f"Ok(10).flatMap(λx. Ok(x * 2)) = {result4}")
    print()


def demo_pattern_matching():
    """Demo: Pattern matching."""
    print("=" * 60)
    print("DEMO: Pattern Matching")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Match on Maybe
    # match Some(42) with
    #   | Some(x) -> x * 2
    #   | Nothing -> 0
    program1 = match(
        some(lit_int(42)),
        case({'type': 'Some', 'inner': {'type': 'var', 'name': 'x'}},
             mul(var("x"), lit_int(2))),
        case({'type': 'Nothing'},
             lit_int(0))
    )
    result1 = vm.run(program1)
    print(f"match Some(42) -> {result1}")
    
    # Match on Nothing
    program2 = match(
        nothing_node(),
        case({'type': 'Some', 'inner': {'type': 'var', 'name': 'x'}},
             mul(var("x"), lit_int(2))),
        case({'type': 'Nothing'},
             lit_int(0))
    )
    result2 = vm.run(program2)
    print(f"match Nothing -> {result2}")
    
    # Match on Result
    program3 = match(
        ok(lit_int(10)),
        case({'type': 'Ok', 'inner': {'type': 'var', 'name': 'x'}},
             add(var("x"), lit_int(5))),
        case({'type': 'Err', 'inner': {'type': 'var', 'name': 'e'}},
             lit_int(0))
    )
    result3 = vm.run(program3)
    print(f"match Ok(10) -> {result3}")
    print()


def demo_lists():
    """Demo: List operations."""
    print("=" * 60)
    print("DEMO: Lists")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Create a list
    program1 = list_node(lit_int(1), lit_int(2), lit_int(3))
    result1 = vm.run(program1)
    print(f"[1, 2, 3] = {result1}")
    
    # Map over list: [1,2,3].map(λx. x * 2)
    program2 = map_node(
        lam("x", mul(var("x"), lit_int(2))),
        list_node(lit_int(1), lit_int(2), lit_int(3))
    )
    result2 = vm.run(program2)
    print(f"[1,2,3].map(λx. x * 2) = {result2}")
    
    # Filter list: [1,2,3,4,5].filter(λx. x > 2)
    program3 = filter_node(
        lam("x", lt(lit_int(2), var("x"))),
        list_node(lit_int(1), lit_int(2), lit_int(3), 
                 lit_int(4), lit_int(5))
    )
    result3 = vm.run(program3)
    print(f"[1,2,3,4,5].filter(λx. x > 2) = {result3}")
    print()


def demo_higher_order():
    """Demo: Higher-order functions."""
    print("=" * 60)
    print("DEMO: Higher-Order Functions")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # compose: λf. λg. λx. f(g(x))
    # Let's do: double ∘ increment
    # where double = λx. x * 2 and increment = λx. x + 1
    
    program = let("double", lam("x", mul(var("x"), lit_int(2))),
                  let("increment", lam("x", add(var("x"), lit_int(1))),
                      let("compose", lam("f", lam("g", lam("x", 
                          app(var("f"), app(var("g"), var("x")))))),
                          let("composed", app(app(var("compose"), var("double")), 
                                            var("increment")),
                              app(var("composed"), lit_int(5))))))
    
    result = vm.run(program)
    print(f"(double ∘ increment) 5 = {result}")
    print(f"Expected: double(increment(5)) = double(6) = 12")
    print()


def demo_factorial():
    """Demo: Recursive factorial using Y combinator concept."""
    print("=" * 60)
    print("DEMO: Factorial (iterative style)")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Since we don't have built-in recursion, let's compute factorial iteratively
    # factorial 5 = 5 * 4 * 3 * 2 * 1
    # We'll just compute a few multiplications manually
    
    program = let("n", lit_int(5),
                  mul(var("n"), 
                      mul(lit_int(4),
                          mul(lit_int(3),
                              mul(lit_int(2), lit_int(1))))))
    
    result = vm.run(program)
    print(f"5! = {result}")
    print()


def demo_monadic_chain():
    """Demo: Monadic composition (chaining operations)."""
    print("=" * 60)
    print("DEMO: Monadic Chains")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # Chain: Some(10).flatMap(x -> Some(x * 2)).flatMap(y -> Some(y + 5))
    program = flatmap_node(
        lam("y", some(add(var("y"), lit_int(5)))),
        flatmap_node(
            lam("x", some(mul(var("x"), lit_int(2)))),
            some(lit_int(10))
        )
    )
    
    result = vm.run(program)
    print(f"Some(10) >>= (x -> Some(x*2)) >>= (y -> Some(y+5)) = {result}")
    print(f"Expected: Some(10) -> Some(20) -> Some(25)")
    print()


def demo_conditional():
    """Demo: Conditional expressions."""
    print("=" * 60)
    print("DEMO: Conditionals")
    print("=" * 60)
    
    vm = FunctionalVM()
    
    # if 5 > 3 then 100 else 200
    program1 = if_expr(
        lt(lit_int(3), lit_int(5)),
        lit_int(100),
        lit_int(200)
    )
    result1 = vm.run(program1)
    print(f"if 5 > 3 then 100 else 200 = {result1}")
    
    # if 2 > 5 then 100 else 200
    program2 = if_expr(
        lt(lit_int(5), lit_int(2)),
        lit_int(100),
        lit_int(200)
    )
    result2 = vm.run(program2)
    print(f"if 2 > 5 then 100 else 200 = {result2}")
    
    # Nested conditional
    program3 = if_expr(
        lit_bool(True),
        if_expr(lit_bool(True), lit_int(1), lit_int(2)),
        lit_int(3)
    )
    result3 = vm.run(program3)
    print(f"if true then (if true then 1 else 2) else 3 = {result3}")
    print()


def demo_all():
    """Run all demos."""
    demo_basic_arithmetic()
    demo_lambda_calculus()
    demo_let_bindings()
    demo_maybe_type()
    demo_result_type()
    demo_pattern_matching()
    demo_lists()
    demo_higher_order()
    demo_factorial()
    demo_monadic_chain()
    demo_conditional()
    
    print("=" * 60)
    print("All demos completed!")
    print("=" * 60)


if __name__ == "__main__":
    demo_all()
