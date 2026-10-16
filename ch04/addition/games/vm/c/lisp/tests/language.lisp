;; Language tests. Each line of output is compared with language.expected.

(print "arithmetic" (+ 1 2 3) (- 10 3) (- 5) (* 2 3 4) (/ 17 5) (/ -17 5))
(print "mod" (mod 17 5) (mod -1 10) (mod 7 -3) (abs -4) (min 3 1 2) (max 3 1 2))
(print "overflow" (* 2147483647 2) (+ 2147483647 1) (/ -2147483648 -1))
(print "numbers" 0x1F -0x10 007)
(print "compare" (< 1 2 3) (< 1 3 2) (= 4 4 4) (>= 3 3 1) (<= 1 2 2) (> 2 1))
(print "logic" (not 0) (not 5) (and 1 2 3) (and 1 0 3) (or 0 () 7) (or) (and))

(define x 5)
(set! x (+ x 1))
(print "define" x)

(define (square n) (* n n))
(print "function" (square 7))

(define (fact n) (if (< n 2) 1 (* n (fact (- n 1)))))
(print "recursion" (fact 10))

;; Tail calls run in constant stack space
(define (count n acc) (if (= n 0) acc (count (- n 1) (+ acc 1))))
(print "tail-call" (count 100000 0))

(print "let" (let ((a 1) (b 2)) (+ a b)))
(print "quote" '(1 2 3) (quote (a b . c)) 'sym)
(print "list" (list 1 (list 2 3) "four") (cons 1 2) (car '(1 2)) (cdr '(1 2)))
(print "list2" (length '(1 2 3)) (nth 1 '(10 20 30)) (reverse '(1 2 3)) (null? ()) (pair? '(1)))
(print "cond" (cond ((= 1 2) 10) ((= 1 1) 20) (else 30)) (cond ((= 1 2) 10) (else 30)) (cond (0 1)))
(print "when" (when (> 2 1) 4 5) (when 0 4))
(print "if" (if 1 'yes 'no) (if 0 'yes 'no) (if 0 'yes))
(print "begin" (begin 1 2 3) (begin))
(print "eq" (eq? 'a 'a) (eq? 'a 'b) (eq? 3 3) (eq? '(1) '(1)))

(define i 0)
(define total 0)
(while (< i 10)
  (set! total (+ total i))
  (set! i (+ i 1)))
(print "while" total)

;; Closures keep their own state
(define (make-counter)
  (let ((n 0))
    (lambda () (set! n (+ n 1)) n)))
(define c1 (make-counter))
(define c2 (make-counter))
(c1)
(c1)
(print "closure" (c1) (c2))

(print "strings" "a \"quoted\" word" (number->string -42))

;; Lots of garbage: the collector must run many times during this loop
(define (range a b) (if (>= a b) () (cons a (range (+ a 1) b))))
(define (sum lst) (if (null? lst) 0 (+ (car lst) (sum (cdr lst)))))
(define kept (list "kept" (number->string 123) (range 0 5)))
(define j 0)
(define s 0)
(while (< j 500)
  (set! s (sum (range 0 40)))
  (number->string j)
  (set! j (+ j 1)))
(print "gc" s kept)
