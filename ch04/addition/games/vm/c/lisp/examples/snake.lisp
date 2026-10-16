;; Snake
;; A = up, B = down, X = left, Y = right. Eat the red food to grow.
;; The snake wraps around the edges of the screen.

(define cell 10)
(define cols (/ screen-width cell))
(define rows (/ screen-height cell))

;; The snake is a list of (x . y) cells, head first
(define snake ())
(define dx 1)
(define dy 0)
(define food (cons 0 0))
(define score 0)
(define alive 1)
(define tick 0)

(define (same? a b)
  (and (= (car a) (car b)) (= (cdr a) (cdr b))))

(define (member? c lst)
  (cond ((null? lst) 0)
        ((same? c (car lst)) 1)
        (else (member? c (cdr lst)))))

(define (place-food)
  (set! food (cons (random cols) (random rows)))
  (when (member? food snake) (place-food)))

;; All but the last element of a list
(define (drop-last lst)
  (reverse (cdr (reverse lst))))

(define (reset)
  (set! snake (list (cons 10 12) (cons 9 12) (cons 8 12)))
  (set! dx 1)
  (set! dy 0)
  (set! score 0)
  (set! alive 1)
  (place-food))

;; Turning back into the snake's own body is not allowed
(define (turn x y)
  (when (not (and (= x (- dx)) (= y (- dy))))
    (set! dx x)
    (set! dy y)))

(on-button-a (lambda () (if alive (turn 0 -1) (reset))))
(on-button-b (lambda () (if alive (turn 0 1) (reset))))
(on-button-x (lambda () (if alive (turn -1 0) (reset))))
(on-button-y (lambda () (if alive (turn 1 0) (reset))))

(define (step)
  (let ((head (car snake)))
    (let ((next (cons (mod (+ (car head) dx) cols)
                      (mod (+ (cdr head) dy) rows))))
      (cond ((member? next snake) (set! alive 0))
            ((same? next food)
             (set! snake (cons next snake))
             (set! score (+ score 1))
             (place-food))
            (else
             (set! snake (cons next (drop-last snake))))))))

(define (draw-cell c color)
  (fill-rect (* (car c) cell) (* (cdr c) cell) (- cell 1) (- cell 1) color))

(define (draw-snake lst)
  (when (pair? lst)
    (draw-cell (car lst) 0x07E0)
    (draw-snake (cdr lst))))

(on-update (lambda ()
  (set! tick (+ tick 1))
  (when (and alive (= (mod tick 6) 0))
    (step))
  (clear 0x0000)
  (draw-cell food 0xF800)
  (draw-snake snake)
  (draw-text 4 4 "Score:" 0xFFFF 0x0000)
  (draw-text 44 4 score 0xFFE0 0x0000)
  (when (not alive)
    (draw-text 130 110 "GAME OVER" 0xF800 0x0000)
    (draw-text 88 126 "Press any button" 0xFFFF 0x0000))))

(reset)
(start)
