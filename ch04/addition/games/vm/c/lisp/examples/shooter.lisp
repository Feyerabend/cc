;; Space shooter
;; Hold X and Y to move left and right, press A to fire, B to restart.

(define black  0x0000)
(define white  0xFFFF)
(define green  0x07E0)
(define red    0xF800)
(define yellow 0xFFE0)

;; Player ship, 8x8
(define player-sprite (make-sprite 8 8))
(sprite-fill player-sprite 3 0 2 2 green)
(sprite-fill player-sprite 2 2 4 3 green)
(sprite-fill player-sprite 0 5 8 2 green)
(sprite-set-pixel player-sprite 1 7 yellow)
(sprite-set-pixel player-sprite 6 7 yellow)

;; Enemy, 8x8
(define enemy-sprite (make-sprite 8 8))
(sprite-fill enemy-sprite 1 1 6 4 red)
(sprite-set-pixel enemy-sprite 0 0 red)
(sprite-set-pixel enemy-sprite 7 0 red)
(sprite-set-pixel enemy-sprite 2 2 black)
(sprite-set-pixel enemy-sprite 5 2 black)
(sprite-fill enemy-sprite 1 5 2 2 red)
(sprite-fill enemy-sprite 5 5 2 2 red)

(define player-x 0)
(define player-y 220)
(define enemy-x 0)
(define enemy-y 0)
(define enemy-dx 0)
(define bullet-x 0)
(define bullet-y -1)       ; -1 means no bullet on screen
(define score 0)
(define game-over 0)

(define (reset)
  (set! player-x 156)
  (set! enemy-x 100)
  (set! enemy-y 30)
  (set! enemy-dx 2)
  (set! bullet-y -1)
  (set! score 0)
  (set! game-over 0))

(define (new-enemy)
  (set! enemy-x (random (- screen-width 8)))
  (set! enemy-y 30)
  (set! enemy-dx (+ 2 (/ score 5))))

(on-button-a (lambda ()
  (when (< bullet-y 0)
    (set! bullet-x (+ player-x 3))
    (set! bullet-y (- player-y 4)))))

(on-button-b reset)

(define (move-player)
  (when (button? button-x) (set! player-x (max 0 (- player-x 3))))
  (when (button? button-y) (set! player-x (min (- screen-width 8) (+ player-x 3)))))

(define (move-enemy)
  (set! enemy-x (+ enemy-x enemy-dx))
  ;; Bounce at the edges and come one step closer
  (when (or (< enemy-x 0) (> enemy-x (- screen-width 8)))
    (set! enemy-dx (- enemy-dx))
    (set! enemy-x (+ enemy-x enemy-dx))
    (set! enemy-y (+ enemy-y 12)))
  (when (> (+ enemy-y 8) player-y)
    (set! game-over 1)))

(define (move-bullet)
  (when (>= bullet-y 0)
    (set! bullet-y (- bullet-y 6))
    (when (collide? bullet-x bullet-y 2 4 enemy-x enemy-y 8 8)
      (set! score (+ score 1))
      (set! bullet-y -1)
      (new-enemy))))

(define (draw)
  (clear black)
  (draw-sprite player-sprite player-x player-y)
  (draw-sprite enemy-sprite enemy-x enemy-y)
  (when (>= bullet-y 0)
    (fill-rect bullet-x bullet-y 2 4 yellow))
  (draw-text 10 10 "Score:" white black)
  (draw-text 50 10 score yellow black))

(on-update (lambda ()
  (if game-over
      (begin
        (draw)
        (draw-text 130 110 "GAME OVER" red black)
        (draw-text 106 126 "Press B to restart" white black))
      (begin
        (move-player)
        (move-enemy)
        (move-bullet)
        (draw)))))

(reset)
(start)
