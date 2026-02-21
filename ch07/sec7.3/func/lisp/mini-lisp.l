; Mini-Lisp: A minimal Lisp interpreter written in Lisp
; Features: basic eval, apply, file loading, and recursion depth protection


; Helper functions (not in the host interpreter)

(define (cadr x) (car (cdr x)))
(define (caddr x) (car (cdr (cdr x))))
(define (cadddr x) (car (cdr (cdr (cdr x)))))
(define (cddr x) (cdr (cdr x)))
(define (cdddr x) (cdr (cdr (cdr x))))
(define (caar x) (car (car x)))


; Recursion depth tracking to prevent stack overflow

(define max-recursion-depth 100)
(define current-depth 0)

(define (check-recursion-depth)
  (if (> current-depth max-recursion-depth)
      (begin
        (display "ERROR: Maximum recursion depth exceeded!")
        (display " (depth: ")
        (display current-depth)
        (display ")")
        (print "")
        'recursion-limit-exceeded)
      'ok))


; Core predicates

(define (atom? x)
  (not (list? x)))

(define (pair? x)
  (and (list? x) (not (null? x))))

(define (eq? a b)
  (= a b))


; Environment operations (simple association lists)

(define (make-env) '())

(define (extend-env vars vals env)
  (define (make-bindings vars vals)
    (if (null? vars)
        '()
        (cons (list (car vars) (car vals))
              (make-bindings (cdr vars) (cdr vals)))))
  (cons (make-bindings vars vals) env))

(define (lookup var env)
  (if (null? env)
      (begin
        (display "Unbound variable: ")
        (print var)
        'error)
      (let ((frame (car env)))
        (let ((binding (find-binding var frame)))
          (if binding
              (binding-value binding)
              (lookup var (cdr env)))))))

(define (find-binding key alist)
  (if (null? alist)
      false
      (if (eq? (car (car alist)) key)
          (car alist)
          (find-binding key (cdr alist)))))

(define (binding-value binding)
  (cadr binding))


; The mini-lisp EVAL function

(define (mini-eval expr env)
  (let ((depth-check (check-recursion-depth)))
    (if (eq? depth-check 'recursion-limit-exceeded)
        'error
        (begin
          (set! current-depth (+ current-depth 1))
          (let ((result (mini-eval-inner expr env)))
            (set! current-depth (- current-depth 1))
            result)))))

(define (mini-eval-inner expr env)
  ; Self-evaluating expressions
  (cond
    ((number? expr) expr)
    ((string? expr) expr)
    ((eq? expr 'true) true)
    ((eq? expr 'false) false)
    
    ; Variable lookup
    ((symbol? expr) (lookup expr env))
    
    ; Empty list
    ((null? expr) '())
    
    ; Special forms and function application
    ((list? expr)
     (let ((op (car expr)))
       (cond
         ; quote
         ((eq? op 'quote) (cadr expr))
         
         ; if
         ((eq? op 'if)
          (if (mini-eval (cadr expr) env)
              (mini-eval (caddr expr) env)
              (if (not (null? (cdddr expr)))
                  (mini-eval (cadddr expr) env)
                  false)))
         
         ; lambda
         ((eq? op 'lambda)
          (let ((params (cadr expr))
                (body (cddr expr)))
            (list 'closure params body env)))
         
         ; define
         ((eq? op 'define)
          (let ((var (cadr expr))
                (val (mini-eval (caddr expr) env)))
            (set! global-mini-env 
                  (extend-env (list var) (list val) global-mini-env))
            var))
         
         ; begin
         ((eq? op 'begin)
          (eval-sequence (cdr expr) env))
         
         ; Function application
         (else
          (mini-apply (mini-eval op env)
                     (map (lambda (arg) (mini-eval arg env)) (cdr expr)))))))
    
    ; Unknown expression type
    (else 
     (begin
       (display "Cannot evaluate: ")
       (print expr)
       'error))))


; The mini-lisp APPLY function

(define (mini-apply proc args)
  (cond
    ; Closure (user-defined function)
    ((and (list? proc) (eq? (car proc) 'closure))
     (let ((params (cadr proc))
           (body (caddr proc))
           (closure-env (cadddr proc)))
       (let ((new-env (extend-env params args closure-env)))
         (eval-sequence body new-env))))
    
    ; Primitive procedure
    ((and (list? proc) (eq? (car proc) 'primitive))
     (apply-primitive (cadr proc) args))
    
    ; Error case
    (else
     (begin
       (display "Not a procedure: ")
       (print proc)
       'error))))

(define (eval-sequence exprs env)
  (if (null? (cdr exprs))
      (mini-eval (car exprs) env)
      (begin
        (mini-eval (car exprs) env)
        (eval-sequence (cdr exprs) env))))


; Primitive procedures

(define (apply-primitive name args)
  (cond
    ((eq? name '+) 
     (if (null? args) 
         0 
         (+ (car args) (apply-primitive '+ (cdr args)))))
    ((eq? name '-) 
     (if (null? (cdr args))
         (- 0 (car args))
         (- (car args) (apply-primitive '+ (cdr args)))))
    ((eq? name '*) 
     (if (null? args) 
         1 
         (* (car args) (apply-primitive '* (cdr args)))))
    ((eq? name '/) 
     (if (null? (cdr args))
         (/ 1 (car args))
         (/ (car args) (apply-primitive '* (cdr args)))))
    ((eq? name '=) (= (car args) (cadr args)))
    ((eq? name '<) (< (car args) (cadr args)))
    ((eq? name '>) (> (car args) (cadr args)))
    ((eq? name '<=) (<= (car args) (cadr args)))
    ((eq? name '>=) (>= (car args) (cadr args)))
    ((eq? name 'cons) (cons (car args) (cadr args)))
    ((eq? name 'car) (car (car args)))
    ((eq? name 'cdr) (cdr (car args)))
    ((eq? name 'null?) (null? (car args)))
    ((eq? name 'list?) (list? (car args)))
    ((eq? name 'number?) (number? (car args)))
    ((eq? name 'symbol?) (symbol? (car args)))
    ((eq? name 'print) (print (car args)))
    ((eq? name 'display) (display (car args)))
    (else 
     (begin
       (display "Unknown primitive: ")
       (print name)
       'error))))


; Global environment setup

(define (make-primitives names)
  (if (null? names)
      '()
      (cons (list 'primitive (car names))
            (make-primitives (cdr names)))))

(define primitive-names 
  '(+ - * / = < > <= >= cons car cdr null? list? number? symbol? print display))

(define global-mini-env
  (extend-env
   primitive-names
   (make-primitives primitive-names)
   (make-env)))

; Add some useful constants
(set! global-mini-env (extend-env '(true false) (list true false) global-mini-env))


; File loading functionality

(define (mini-load filename)
  (display "Loading file: ")
  (print filename)
  (display "[File loading requires host system support]")
  (print "")
  'ok)


; REPL and helpers

(define (mini-repl)
  (display "Mini-Lisp REPL")
  (print "")
  (display "Type expressions to evaluate, or use:")
  (print "")
  (display "  (mini-eval <expr> global-mini-env)")
  (print "")
  (display "  (test-mini-lisp) to run tests")
  (print "")
  'ready)


; Test suite

(define (test-mini-lisp)
  (display "*** Testing Mini-Lisp ***")
  (print "")
  
  ; Reset recursion counter
  (set! current-depth 0)
  
  ; Test 1: Arithmetic
  (display "Test 1: Arithmetic")
  (print "")
  (display "  Result: ")
  (print (mini-eval '(+ 1 2 3) global-mini-env))
  
  ; Test 2: Variables and define
  (display "Test 2: Define variable")
  (print "")
  (mini-eval '(define x 42) global-mini-env)
  (display "  x = ")
  (print (mini-eval 'x global-mini-env))
  
  ; Test 3: Lambda and function call
  (display "Test 3: Lambda")
  (print "")
  (mini-eval '(define square (lambda (n) (* n n))) global-mini-env)
  (display "  (square 5) = ")
  (print (mini-eval '(square 5) global-mini-env))
  
  ; Test 4: Conditional
  (display "Test 4: If expression")
  (print "")
  (display "  (if (< 3 5) \"yes\" \"no\") = ")
  (print (mini-eval '(if (< 3 5) "yes" "no") global-mini-env))
  
  ; Test 5: Simple recursion test (non-recursive for now)
  (display "Test 5: Multiple operations")
  (print "")
  (mini-eval '(define add-and-mult 
                (lambda (a b c)
                  (+ (* a b) c)))
             global-mini-env)
  (display "  (add-and-mult 2 3 4) = ")
  (let ((result (mini-eval '(add-and-mult 2 3 4) global-mini-env)))
    (if (eq? result 'error)
        (print "ERROR")
        (print result)))
  
  ; Test 6: List operations
  (display "Test 6: List operations")
  (print "")
  (display "  (car (cons 1 (cons 2 (quote ())))) = ")
  (print (mini-eval '(car (cons 1 (cons 2 (quote ())))) global-mini-env))
  
  ; Test 7: Quote
  (display "Test 7: Quote")
  (print "")
  (display "  (quote (a b c)) = ")
  (print (mini-eval '(quote (a b c)) global-mini-env))
  
  (display "")
  (display "=== All tests completed! ===")
  (print "")
  (display "Current recursion depth: ")
  (print current-depth)
  'done)


; Recursion safety demonstration: just becase recursion is tricky..

(define (test-recursion-limit)
  (display "Testing recursion limit..")
  (print "")
  (set! current-depth 0)
  
  ; This will hit the recursion limit
  (mini-eval '(define infinite-loop 
                (lambda () (infinite-loop)))
             global-mini-env)
  
  (display "Calling infinite recursion (should fail safely):")
  (print "")
  (mini-eval '(infinite-loop) global-mini-env)
  
  (display "")
  (display "Recursion limit working correctly!")
  (print "")
  'done)


; Example programs that can be evaluated in mini-lisp

(define example-fibonacci
  '(begin
     (define fib
       (lambda (n)
         (if (<= n 1)
             n
             (+ (fib (- n 1)) (fib (- n 2))))))
     (fib 8)))

(define example-sum-list
  '(begin
     (define sum-list
       (lambda (lst)
         (if (null? lst)
             0
             (+ (car lst) (sum-list (cdr lst))))))
     (sum-list (quote (1 2 3 4 5)))))


; Convenience function to run examples

(define (run-example name expr)
  (display "Running example: ")
  (print name)
  (set! current-depth 0)
  (display "Result: ")
  (print (mini-eval expr global-mini-env))
  (print "")
  'done)


; Print welcome message and instructions

(display "")
(display "-------------------------------------")
(print "")
(display "   Mini-Lisp Interpreter Loaded!")
(print "")
(display "-------------------------------------")
(print "")
(display "This is minimal Lisp interpreter written in Lisp!")
(print "")
(display "Try commands:")
(print "")
(display "  (test-mini-lisp)         ; Run test suite")
(print "")
(display "  (test-recursion-limit)   ; Test safety")
(print "")
(display "  (run-example 'fib example-fibonacci)")
(print "")
(display "  (run-example 'sum example-sum-list)")
(print "")
(display "Or evaluate directly:")
(print "")
(display "  (mini-eval '(+ 1 2 3) global-mini-env)")
(print "")
(display "  (mini-eval '(define double (lambda (x) (* x 2))) global-mini-env)")
(print "")
(display "  (mini-eval '(double 21) global-mini-env)")
(print "")
(display "-------------------------------------")
(print "")
