#!/usr/bin/env python3
"""
Quick demo of trampoline and call/cc features (non-interactive)
"""

from lisp import Lisp

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def main():
    print("""
       TRAMPOLINE & CALL/CC QUICK DEMO
""")

    lisp = Lisp()

    # TRAMPOLINE DEMOS
    print_header("TRAMPOLINE (TCO) DEMONSTRATIONS")
    
    print("\n1. Factorial with large values:")
    lisp.run('''
(define (factorial n acc)
  (if (<= n 1) acc (factorial (- n 1) (* n acc))))
''')
    print(f"   factorial(10) = {lisp.run('(factorial 10 1)')}")
    print(f"   factorial(100) = {lisp.run('(factorial 100 1)')}")
    
    print("\n2. Deep recursion (10,000 levels - no stack overflow!):")
    lisp.run('''
(define (countdown n)
  (if (<= n 0) "Done!" (countdown (- n 1))))
''')
    print(f"   countdown(10000) = {lisp.run('(countdown 10000)')}")
    
    print("\n3. Mutual recursion:")
    lisp.run('''
(define (is-even n)
  (if (= n 0) true (is-odd (- n 1))))

(define (is-odd n)
  (if (= n 0) false (is-even (- n 1))))
''')
    print(f"   is-even(9999) = {lisp.run('(is-even 9999)')}")
    print(f"   is-odd(9999) = {lisp.run('(is-odd 9999)')}")
    
    print("\n4. Fibonacci sequence:")
    lisp.run('''
(define (fib n a b)
  (if (<= n 0) a (fib (- n 1) b (+ a b))))
''')
    print(f"   fib(20) = {lisp.run('(fib 20 0 1)')}")
    print(f"   fib(50) = {lisp.run('(fib 50 0 1)')}")

    # CALL/CC DEMOS
    print_header("CALL/CC (CONTINUATIONS) DEMONSTRATIONS")
    
    print("\n1. Basic escape from computation:")
    result = lisp.run('(call/cc (lambda (k) (+ 1 (k 42) 3)))')
    print(f"   (call/cc (lambda (k) (+ 1 (k 42) 3)))")
    print(f"   Result: {result} (escapes before adding 1 and 3)")
    
    print("\n2. Early exit from search:")
    lisp.run('''
(define (find-first pred lst)
  (call/cc (lambda (return)
    (define (search lst)
      (if (null? lst) false
          (if (pred (car lst)) (return (car lst))
              (search (cdr lst)))))
    (search lst))))
''')
    result = lisp.run('(find-first (lambda (x) (> x 5)) (list 1 2 6 3 8 4 9))')
    print(f"   find-first (>5) in [1,2,6,3,8,4,9] = {result}")
    print(f"   (stops at 6, doesn't check 8 or 9)")
    
    print("\n3. Product with zero optimization:")
    lisp.run('''
(define (product-with-zero lst)
  (call/cc (lambda (return)
    (define (multiply lst acc)
      (if (null? lst) acc
          (if (= (car lst) 0) (return 0)
              (multiply (cdr lst) (* acc (car lst))))))
    (multiply lst 1))))
''')
    print(f"   product([2,3,4]) = {lisp.run('(product-with-zero (list 2 3 4))')}")
    print(f"   product([2,3,0,4,5]) = {lisp.run('(product-with-zero (list 2 3 0 4 5))')}")
    print(f"   (returns 0 immediately when found)")
    
    print("\n4. Exception-like error handling:")
    lisp.run('''
(define (safe-div a b)
  (call/cc (lambda (error)
    (if (= b 0) (error "Division by zero!")
        (/ a b)))))
''')
    print(f"   safe-div(10, 2) = {lisp.run('(safe-div 10 2)')}")
    print(f"   safe-div(10, 0) = {lisp.run('(safe-div 10 0)')}")

    # COMBINED DEMO
    print_header("COMBINED: TCO + CALL/CC")
    
    print("\nTree search with early exit:")
    lisp.run('''
(define (search-tree tree target)
  (call/cc (lambda (found)
    (define (search-node node)
      (if (null? node) false
          (if (= node target) (found true)
              (if (list? node)
                  (begin
                    (search-node (car node))
                    (search-node (cdr node)))
                  false))))
    (search-node tree)
    false)))

(define my-tree (list 1 (list 2 3) (list 4 (list 5 6))))
''')
    print(f"   search-tree(my-tree, 5) = {lisp.run('(search-tree my-tree 5)')}")
    print(f"   search-tree(my-tree, 99) = {lisp.run('(search-tree my-tree 99)')}")

    print_header("SUMMARY")
    print("""
    All demonstrations completed.

          For comprehensive testing, run:
          python test_trampoline_callcc.py
""")

if __name__ == "__main__":
    main()


#   Trampoline enables unlimited recursion depth
#   call/cc provides powerful non-local control flow
#   Both features work together seamlessly
#   No stack overflows, even with 10,000+ recursive calls
