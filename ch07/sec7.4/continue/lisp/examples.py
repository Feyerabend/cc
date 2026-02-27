#!/usr/bin/env python3
"""
Working Examples: Lisp Built-ins + Trampoline + call/cc

Run this file to see practical uses with inline commentary.
"""

from lisp import Lisp

def header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)

def run_example(title, code, description=""):
    """Run a single example"""
    print(f"\n{title}")
    if description:
        print(f"  {description}")
    print(f"\nCode:\n{code}")
    try:
        lisp = Lisp()
        result = lisp.run(code)
        print(f"→ Result: {result}")
        return result
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


# --------------
header("ARITHMETIC OPERATIONS")
print("""
Practicality: Core math operations.
TCO note: Use accumulators for tail recursion.
""")

run_example(
    "Basic Arithmetic",
    "(+ 1 2 3 4 5)",
    "Sum multiple numbers"
)

run_example(
    "Factorial with TCO",
    """(define (factorial n acc)
  (if (<= n 1) acc (factorial (- n 1) (* n acc))))
(factorial 20 1)""",
    "Tail-recursive - handles huge numbers without stack overflow"
)

run_example(
    "Sum of Squares (map + reduce)",
    """(reduce (lambda (a b) (+ a b))
        (map (lambda (x) (* x x)) (list 1 2 3 4 5)))""",
    "Functional pipeline: map then reduce (lambda wraps +)"
)

# --------------
header("COMPARISON & LOGIC")

run_example(
    "Comparisons",
    "(and (> 5 3) (< 2 4) (!= 1 2))",
    "Short-circuit evaluation"
)

run_example(
    "Guard Clauses with cond",
    """(define (grade score)
  (cond
    ((>= score 90) "A")
    ((>= score 80) "B")
    ((>= score 70) "C")
    (true "F")))
(grade 85)""",
    "Multi-way branching"
)

# --------------
header("LIST OPERATIONS")

run_example(
    "List Construction",
    "(cons 1 (cons 2 (cons 3 (list))))",
    "Classic cons cells - building from empty list"
)

run_example(
    "List Processing",
    """(define lst (list 1 2 3 4 5))
(append (reverse (filter (lambda (x) (> x 2)) lst)) (list 99))""",
    "Combining filter, reverse, append"
)

run_example(
    "Deep List Flatten with TCO",
    """(define (flatten lst acc)
  (if (null? lst) acc
      (if (list? (car lst))
          (flatten (cdr lst) (flatten (car lst) acc))
          (flatten (cdr lst) (append acc (list (car lst)))))))
(flatten (list 1 (list 2 3) (list 4 (list 5))) (list))""",
    "Recursively flatten nested lists - no stack overflow"
)

# --------------
header("HIGHER-ORDER FUNCTIONS")

run_example(
    "Map",
    "(map (lambda (x) (* x x)) (list 1 2 3 4 5))",
    "Transform each element"
)

run_example(
    "Filter",
    "(filter (lambda (x) (> x 3)) (list 1 5 2 6 3 7))",
    "Select elements matching predicate"
)

run_example(
    "Reduce",
    "(reduce (lambda (a b) (* a b)) (list 2 3 4 5))",
    "Combine elements - here: product"
)

run_example(
    "Apply",
    "(apply (lambda args (reduce (lambda (a b) (if (> a b) a b)) args)) (list 3 9 2 7 5))",
    "Apply function to list - here finding max"
)

run_example(
    "Pipeline: Filter → Map → Reduce",
    """(reduce (lambda (a b) (+ a b))
  (map (lambda (x) (* x x))
    (filter (lambda (x) (> x 0)) 
      (list -2 3 -1 4 5))))""",
    "Sum of squares of positive numbers"
)

# --------------
header("CLOSURES & LAMBDA")

run_example(
    "Closure Captures Environment",
    """(define (make-adder n)
  (lambda (x) (+ x n)))
(define add-10 (make-adder 10))
(add-10 5)""",
    "Inner function remembers 'n'"
)

run_example(
    "Currying",
    """(define (curry-multiply x)
  (lambda (y) (* x y)))
(map (curry-multiply 3) (list 1 2 3 4))""",
    "Partial application pattern"
)

# --------------
header("CONTROL FLOW")

run_example(
    "If Expression",
    "(if (> 5 3) 'yes 'no)",
    "Simple binary choice"
)

run_example(
    "Short-circuit AND",
    "(and (> 5 3) (< 2 4) false (print 'never-reached))",
    "Stops at first false - never prints"
)

run_example(
    "Short-circuit OR",
    "(or false false (> 5 3) (print 'never-reached))",
    "Stops at first true - never prints"
)

# --------------
header("TYPE CHECKING")

run_example(
    "Type Predicates",
    """(list 
  (number? 42)
  (string? "hello")
  (list? (list 1 2))
  (procedure? (lambda (x) x)))""",
    "Check types before operations"
)

run_example(
    "Polymorphic Function",
    """(define (safe-add x y)
  (if (and (number? x) (number? y))
      (+ x y)
      "Error: not numbers"))
(list (safe-add 3 4) (safe-add 3 "oops"))""",
    "Type guards prevent errors"
)

# --------------
header("VARIABLES & SCOPE")

run_example(
    "Let for Local Variables",
    """(let ((x 10) (y 20))
  (+ (* x x) (* y y)))""",
    "Local bindings don't pollute outer scope"
)

run_example(
    "Define",
    """(define pi 3.14159)
(define radius 5)
(* pi radius radius)""",
    "Create global bindings"
)

# --------------
header("TRAMPOLINE (TCO) EXAMPLES")

run_example(
    "Countdown (10,000 levels!)",
    """(define (countdown n)
  (if (<= n 0) "Done!" (countdown (- n 1))))
(countdown 10000)""",
    "Would stack overflow without TCO"
)

run_example(
    "Mutual Recursion",
    """(define (is-even n)
  (if (= n 0) true (is-odd (- n 1))))
(define (is-odd n)
  (if (= n 0) false (is-even (- n 1))))
(list (is-even 100) (is-odd 99))""",
    "Two functions calling each other - optimized!"
)

run_example(
    "Fibonacci with TCO",
    """(define (fib n a b)
  (if (<= n 0) a (fib (- n 1) b (+ a b))))
(fib 30 0 1)""",
    "Efficient - constant stack space"
)

# --------------
header("CALL/CC (CONTINUATIONS) EXAMPLES")

run_example(
    "Basic Escape",
    "(call/cc (lambda (k) (+ 1 (k 42) 3)))",
    "Returns 42, skipping the + 1 and + 3"
)

run_example(
    "Early Exit from Search",
    """(define (find-first pred lst)
  (call/cc (lambda (return)
    (define (search items)
      (if (null? items) false
          (if (pred (car items)) 
              (return (car items))
              (search (cdr items)))))
    (search lst))))
(find-first (lambda (x) (> x 5)) (list 1 2 6 3 8))""",
    "Exits immediately when found - doesn't check 3 or 8"
)

run_example(
    "Product with Zero Optimization",
    """(define (product-zero lst)
  (call/cc (lambda (return)
    (define (mult items acc)
      (if (null? items) acc
          (if (= (car items) 0) 
              (return 0)
              (mult (cdr items) (* acc (car items))))))
    (mult lst 1))))
(list (product-zero (list 2 3 4)) 
      (product-zero (list 2 0 4)))""",
    "Second list returns 0 immediately without computing"
)

run_example(
    "Exception-like Behavior",
    """(define (safe-div a b)
  (call/cc (lambda (error)
    (if (= b 0) 
        (error "Division by zero!")
        (/ a b)))))
(list (safe-div 10 2) (safe-div 10 0))""",
    "Using continuations for error handling"
)

run_example(
    "Nested Continuations",
    """(call/cc (lambda (outer)
  (+ 100 (call/cc (lambda (inner)
    (outer 42))))))""",
    "Inner escapes to outer - result is 42, not 142"
)

# --------------
header("COMBINED: TCO + CALL/CC")

run_example(
    "Tree Search with Early Exit",
    """(define (search-tree tree target)
  (call/cc (lambda (found)
    (define (search node)
      (if (null? node) false
          (if (= node target) (found true)
              (if (list? node)
                  (begin (search (car node)) (search (cdr node)))
                  false))))
    (search tree) false)))
(search-tree (list 1 (list 2 3) (list 4 (list 5))) 4)""",
    "Deep recursion (TCO) + early exit (call/cc)"
)

# --------------
header("ADVANCED PATTERNS")

run_example(
    "QuickSort with TCO",
    """(define (qsort lst)
  (if (null? lst) (list)
      (let ((pivot (car lst)) (rest (cdr lst)))
        (append
          (qsort (filter (lambda (x) (< x pivot)) rest))
          (list pivot)
          (qsort (filter (lambda (x) (>= x pivot)) rest))))))
(qsort (list 3 1 4 1 5 9 2 6))""",
    "Combining recursion, filter, higher-order functions"
)

run_example(
    "Fold Left (Custom Reduce)",
    """(define (fold-left fn acc lst)
  (if (null? lst) acc
      (fold-left fn (fn acc (car lst)) (cdr lst))))
(fold-left + 0 (list 1 2 3 4 5))""",
    "Tail-recursive accumulator pattern"
)

# --------------
header("MACROS & QUOTING")

print("""
Macros transform code before evaluation - advanced feature.
Quote prevents evaluation, quasiquote allows selective evaluation.
Example syntax: (defmacro name (params) body)
Note: Macro system is available but complex - see docs for details.
""")

# --------------
header("PERFORMANCE TIPS")

print("""
1. TAIL RECURSION: Always use accumulators
   ✗ Bad:  (define (sum lst) (if (null? lst) 0 (+ (car lst) (sum (cdr lst)))))
     Good: (define (sum lst acc) (if (null? lst) acc (sum (cdr lst) (+ acc (car lst)))))

2. CALL/CC FOR EARLY EXIT: Don't compute what you don't need
     Use call/cc to exit loops/searches immediately when done

3. HIGHER-ORDER FUNCTIONS: Clear but may allocate intermediate lists
   - map/filter/reduce create new lists
   - Direct recursion can be more memory-efficient
   - Use what's clearer unless profiling shows it matters

4. LET vs DEFINE: Use 'let' for temporary values
     Better scoping, clearer intent

5. AVOID MUTATION: Functional style is easier to reason about
   - Use 'set!' only for: counters, caches, state machines
   - Prefer closures over mutable state
""")

# --------------
header("COMMON PATTERNS")

print("""
ACCUMULATOR PATTERN (TCO):
  (define (fn lst acc) 
    (if (null? lst) acc 
        (fn (cdr lst) (op acc (car lst)))))

CONTINUATION PASSING (call/cc):
  (call/cc (lambda (k) 
    ... (k value) ...))

FILTER-MAP-REDUCE PIPELINE:
  (reduce op 
    (map transform 
      (filter pred data)))

GUARD CLAUSES (cond):
  (cond 
    (error-case (handle-error))
    (normal-case (process)))

CLOSURE FACTORY:
  (define (make-X param) 
    (lambda (arg) (use param arg)))
""")

# --------------
print("\n  ALL EXAMPLES COMPLETED.\n")

# Examples on:
#    Arithmetic, comparison, logic
#    List operations (cons, car, cdr, map, filter, reduce)
#    Higher-order functions & pipelines
#    Closures & lambda
#    Type checking
#    Control flow (if, cond, and, or)
#    Variables & scope (define, let, set!)
#    Trampoline (TCO) - unlimited recursion
#    call/cc - early exit & control flow
#    Advanced patterns (QuickSort, fold, macros)
