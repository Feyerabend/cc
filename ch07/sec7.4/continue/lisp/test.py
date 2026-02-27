#!/usr/bin/env python3
"""
Comprehensive test suite for trampoline (TCO) and call/cc (continuations)
in the Lisp interpreter.
"""

import sys
from lisp import Lisp, RuntimeError as LispRuntimeError

def test_trampoline_basic():
    """Test basic tail call optimization with factorial"""
    print("Testing basic TCO with factorial...")
    lisp = Lisp()
    
    # Tail-recursive factorial
    lisp.run("""
    (define (factorial n acc)
      (if (<= n 1)
          acc
          (factorial (- n 1) (* n acc))))
    """)
    
    # Test small value
    result = lisp.run("(factorial 5 1)")
    assert result == 120, f"Expected 120, got {result}"
    
    # Test large value that would blow stack without TCO
    result = lisp.run("(factorial 1000 1)")
    assert result > 0, "Should compute large factorial without stack overflow"
    print("✓ Basic TCO works")

def test_trampoline_mutual_recursion():
    """Test TCO with mutually recursive functions"""
    print("Testing TCO with mutual recursion...")
    lisp = Lisp()
    
    lisp.run("""
    (define (is-even n)
      (if (= n 0)
          true
          (is-odd (- n 1))))
    
    (define (is-odd n)
      (if (= n 0)
          false
          (is-even (- n 1))))
    """)
    
    result = lisp.run("(is-even 100)")
    assert result == True, f"Expected True, got {result}"
    
    result = lisp.run("(is-odd 99)")
    assert result == True, f"Expected True, got {result}"
    
    # Large value to test TCO
    result = lisp.run("(is-even 10000)")
    assert result == True, "Should handle large mutual recursion"
    print("✓ Mutual recursion with TCO works")

def test_trampoline_sum():
    """Test TCO with sum of list"""
    print("Testing TCO with list sum...")
    lisp = Lisp()
    
    lisp.run("""
    (define (sum-list lst acc)
      (if (null? lst)
          acc
          (sum-list (cdr lst) (+ acc (car lst)))))
    """)
    
    # Create a long list
    lisp.run("(define long-list (list 1 2 3 4 5 6 7 8 9 10))")
    result = lisp.run("(sum-list long-list 0)")
    assert result == 55, f"Expected 55, got {result}"
    print("✓ TCO with list processing works")

def test_callcc_basic():
    """Test basic call/cc functionality"""
    print("Testing basic call/cc...")
    lisp = Lisp()
    
    # Simple escape from computation
    result = lisp.run("""
    (call/cc (lambda (k)
      (+ 1 (k 42) 3)))
    """)
    assert result == 42, f"Expected 42, got {result}"
    print("✓ Basic call/cc escape works")

def test_callcc_conditional_escape():
    """Test call/cc with conditional escape"""
    print("Testing call/cc with conditional escape...")
    lisp = Lisp()
    
    # Escape early if condition is met
    lisp.run("""
    (define (product-with-zero lst)
      (call/cc (lambda (return)
        (define (helper lst acc)
          (if (null? lst)
              acc
              (if (= (car lst) 0)
                  (return 0)
                  (helper (cdr lst) (* acc (car lst))))))
        (helper lst 1))))
    """)
    
    result = lisp.run("(product-with-zero (list 2 3 4))")
    assert result == 24, f"Expected 24, got {result}"
    
    result = lisp.run("(product-with-zero (list 2 0 4))")
    assert result == 0, f"Expected 0, got {result}"
    print("✓ Conditional escape with call/cc works")

def test_callcc_nested():
    """Test nested call/cc"""
    print("Testing nested call/cc...")
    lisp = Lisp()
    
    result = lisp.run("""
    (call/cc (lambda (outer)
      (+ 10
         (call/cc (lambda (inner)
           (outer 5))))))
    """)
    assert result == 5, f"Expected 5, got {result}"
    print("✓ Nested call/cc works")

def test_callcc_with_state():
    """Test call/cc with state modification"""
    print("Testing call/cc with state...")
    lisp = Lisp()
    
    lisp.run("""
    (define saved-cont nil)
    
    (define (save-and-return)
      (call/cc (lambda (k)
        (set! saved-cont k)
        42)))
    """)
    
    result = lisp.run("(save-and-return)")
    assert result == 42, f"Expected 42, got {result}"
    
    # Verify the continuation was saved
    from lisp import Continuation
    cont = lisp.global_env.get("saved-cont")
    assert isinstance(cont, Continuation), f"Expected Continuation, got {type(cont)}"
    print("✓ call/cc with state works (continuation saved)")

def test_callcc_loop_break():
    """Test call/cc to break from a loop"""
    print("Testing call/cc for loop breaking...")
    lisp = Lisp()
    
    lisp.run("""
    (define (find-first predicate lst)
      (call/cc (lambda (return)
        (define (search lst)
          (if (null? lst)
              false
              (if (predicate (car lst))
                  (return (car lst))
                  (search (cdr lst)))))
        (search lst))))
    """)
    
    result = lisp.run("(find-first (lambda (x) (> x 5)) (list 1 2 6 3 8))")
    assert result == 6, f"Expected 6, got {result}"
    
    result = lisp.run("(find-first (lambda (x) (> x 100)) (list 1 2 3))")
    assert result == False, f"Expected False, got {result}"
    print("✓ call/cc for loop breaking works")

def test_trampoline_fibonacci():
    """Test TCO with Fibonacci sequence"""
    print("Testing TCO with Fibonacci...")
    lisp = Lisp()
    
    lisp.run("""
    (define (fib n a b)
      (if (<= n 0)
          a
          (fib (- n 1) b (+ a b))))
    """)
    
    result = lisp.run("(fib 10 0 1)")
    assert result == 55, f"Expected 55, got {result}"
    
    # Large Fibonacci number to test TCO
    result = lisp.run("(fib 100 0 1)")
    assert result > 0, "Should compute large Fibonacci without stack overflow"
    print("✓ TCO with Fibonacci works")

def test_callcc_exception_like():
    """Test call/cc for exception-like behavior"""
    print("Testing call/cc for exception handling...")
    lisp = Lisp()
    
    lisp.run("""
    (define (safe-div a b)
      (call/cc (lambda (error)
        (if (= b 0)
            (error "Division by zero!")
            (/ a b)))))
    """)
    
    result = lisp.run("(safe-div 10 2)")
    assert result == 5.0, f"Expected 5.0, got {result}"
    
    result = lisp.run("(safe-div 10 0)")
    assert result == "Division by zero!", f"Expected error message, got {result}"
    print("✓ call/cc for exception handling works")

def test_combined_tco_callcc():
    """Test combining TCO with call/cc"""
    print("Testing combined TCO and call/cc...")
    lisp = Lisp()
    
    lisp.run("""
    (define (search-tree tree target)
      (call/cc (lambda (found)
        (define (search-node node)
          (if (null? node)
              false
              (if (= node target)
                  (found true)
                  (if (list? node)
                      (begin
                        (search-node (car node))
                        (search-node (cdr node)))
                      false))))
        (search-node tree)
        false)))
    """)
    
    result = lisp.run("(search-tree (list 1 (list 2 3) (list 4 5)) 4)")
    assert result == True, f"Expected True, got {result}"
    
    result = lisp.run("(search-tree (list 1 (list 2 3) (list 4 5)) 10)")
    assert result == False, f"Expected False, got {result}"
    print("✓ Combined TCO and call/cc works")

def test_trampoline_count_down():
    """Test TCO doesn't break with large countdown"""
    print("Testing TCO with countdown...")
    lisp = Lisp()
    
    lisp.run("""
    (define (countdown n)
      (if (<= n 0)
          0
          (countdown (- n 1))))
    """)
    
    result = lisp.run("(countdown 5000)")
    assert result == 0, f"Expected 0, got {result}"
    print("✓ TCO with countdown works")

def test_callcc_generator_like():
    """Test call/cc for generator-like behavior"""
    print("Testing call/cc for generator pattern...")
    lisp = Lisp()
    
    # A simpler test that uses call/cc within a single context
    result = lisp.run("""
    (define (yield-example)
      (call/cc (lambda (return)
        (return (list 1 2 3))
        "unreachable")))
    """)
    
    # The continuation returns early with the list
    lisp.run("(define result (yield-example))")
    result = lisp.run("result")
    assert result == [1, 2, 3], f"Expected [1, 2, 3], got {result}"
    print("✓ Basic generator pattern with call/cc works")

def test_stress_trampoline():
    """Stress test the trampoline with very deep recursion"""
    print("Testing trampoline stress test...")
    lisp = Lisp()
    
    lisp.run("""
    (define (deep-recursion n result)
      (if (<= n 0)
          result
          (deep-recursion (- n 1) (+ result 1))))
    """)
    
    # This would definitely blow the stack without TCO
    result = lisp.run("(deep-recursion 50000 0)")
    assert result == 50000, f"Expected 50000, got {result}"
    print("✓ Trampoline handles very deep recursion")

def test_callcc_multiple_escapes():
    """Test multiple continuations don't interfere"""
    print("Testing multiple independent continuations...")
    lisp = Lisp()
    
    result = lisp.run("""
    (+ (call/cc (lambda (k1) (k1 10)))
       (call/cc (lambda (k2) (k2 20))))
    """)
    assert result == 30, f"Expected 30, got {result}"
    print("✓ Multiple independent continuations work")

def test_callcc_in_map():
    """Test call/cc works inside higher-order functions"""
    print("Testing call/cc inside map...")
    lisp = Lisp()
    
    result = lisp.run("""
    (map (lambda (x)
           (call/cc (lambda (k)
             (if (< x 0)
                 (k 0)
                 x))))
         (list 1 -2 3 -4 5))
    """)
    assert result == [1, 0, 3, 0, 5], f"Expected [1, 0, 3, 0, 5], got {result}"
    print("✓ call/cc inside higher-order functions works")

def test_trampoline_ackermann():
    """Test TCO with Ackermann-like function (limited for practicality)"""
    print("Testing TCO with complex recursion pattern...")
    lisp = Lisp()
    
    lisp.run("""
    (define (ack-iter m n)
      (if (= m 0)
          (+ n 1)
          (if (= n 0)
              (ack-iter (- m 1) 1)
              (ack-iter (- m 1) (ack-iter m (- n 1))))))
    """)
    
    result = lisp.run("(ack-iter 2 2)")
    assert result == 7, f"Expected 7, got {result}"
    print("✓ Complex recursion patterns work")

def run_all_tests():
    """Run all tests and report results"""
    tests = [
        test_trampoline_basic,
        test_trampoline_mutual_recursion,
        test_trampoline_sum,
        test_trampoline_fibonacci,
        test_trampoline_count_down,
        test_trampoline_ackermann,
        test_stress_trampoline,
        test_callcc_basic,
        test_callcc_conditional_escape,
        test_callcc_nested,
        test_callcc_with_state,
        test_callcc_loop_break,
        test_callcc_exception_like,
        test_callcc_generator_like,
        test_callcc_multiple_escapes,
        test_callcc_in_map,
        test_combined_tco_callcc,
    ]
    
    passed = 0
    failed = 0
    

    print("TRAMPOLINE AND CALL/CC TEST SUITE")
    print("\n\n")
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("\n\n")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("\n\n")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
