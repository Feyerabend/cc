;; Move a box with the four buttons

(define x 152)
(define y 112)

(on-button-a (lambda () (set! y (- y 8))))  ; up
(on-button-b (lambda () (set! y (+ y 8))))  ; down
(on-button-x (lambda () (set! x (- x 8))))  ; left
(on-button-y (lambda () (set! x (+ x 8))))  ; right

(on-update (lambda ()
  (clear 0x0000)
  (fill-rect x y 16 16 0x07E0)
  (draw-text 10 10 "Move the box!" 0xFFFF 0x0000)))

(start)
