
## A Lisp Game Engine

A minimalist Lisp interpreter for game development on Raspberry Pi Pico 2
with Pimoroni Display Pack 2.0 (320x240 IPS screen).

- *Cross-Platform*: Same Lisp code runs on Pico 2 hardware and in browser emulator
- *Sprite System*: Create and manipulate pixel art sprites up to 32x32
- *Collision Detection*: Built-in AABB collision detection
- *Framebuffer Rendering*: Smooth 60 FPS gameplay with DMA acceleration
- *Memory Efficient*: Fixed-size heap with mark-sweep garbage collection
- *Simple API*: Lisp syntax designed for game development


- Raspberry Pi Pico 2 (or Pico 2W)
- Pimoroni Display Pack 2.0 (320x240 IPS, ST7789 controller)
- 4 x tactile buttons (A, B, X, Y)


## PicoLisp Language Reference

### Basic Syntax

```lisp
;; Comments start with semicolon

;; Variables
(define x 100)
(set! x 150)  ;; Update existing variable

;; Math
(+ 1 2 3)      ;; => 6
(- 10 3)       ;; => 7
(* 2 3 4)      ;; => 24
(/ 10 2)       ;; => 5

;; Comparisons (return 1 for true, 0 for false)
(< 5 10)       ;; => 1
(> 5 10)       ;; => 0
(= 5 5)        ;; => 1

;; Conditionals
(if (< x 100)
  (draw-text 10 10 "Small" 0xFFFF 0x0000)
  (draw-text 10 10 "Large" 0xFFFF 0x0000))

;; Functions
(define move-player (lambda (dx dy)
  (set! player-x (+ player-x dx))
  (set! player-y (+ player-y dy))))

;; Call function
(move-player 4 0)
```

### Graphics Functions

```lisp
;; Clear screen to color (RGB565 format)
(clear 0x0000)  ;; Black

;; Draw filled rectangle
(fill-rect x y width height color)
(fill-rect 10 10 50 50 0xF800)  ;; Red square

;; Draw text (5×8 font)
(draw-text x y "Hello!" fg-color bg-color)
(draw-text 10 10 "Score: 100" 0xFFFF 0x0000)

;; Common colors (RGB565)
;; 0x0000 = Black
;; 0xFFFF = White
;; 0xF800 = Red
;; 0x07E0 = Green
;; 0x001F = Blue
;; 0xFFE0 = Yellow
;; 0x07FF = Cyan
;; 0xF81F = Magenta (used for transparency)
```

### Sprite Functions

```lisp
;; Create sprite
(define my-sprite (make-sprite 16 16))

;; Set individual pixels
(sprite-set-pixel my-sprite 0 0 0xF800)  ;; Red pixel at (0,0)

;; Fill region (browser only)
(sprite-fill my-sprite 0 0 16 16 0x07E0)  ;; Fill with green

;; Draw sprite to screen
(draw-sprite my-sprite x y)

;; Transparent color: 0xF81F (magenta) pixels won't be drawn
```

### Collision Detection

```lisp
;; Check if two rectangles overlap
(collide? x1 y1 w1 h1 x2 y2 w2 h2)

;; Example: Check player-enemy collision
(if (collide? player-x player-y 16 16 enemy-x enemy-y 16 16)
  (begin
    ;; Collision happened!
    (set! score (+ score 1))
    (set! enemy-x 0)))
```

### Game Loop

```lisp
;; Set update callback (called every frame ~60 FPS)
(on-update (lambda ()
  (clear 0x0000)
  (draw-sprite player-sprite player-x player-y)
  (draw-text 10 10 "Hello!" 0xFFFF 0x0000)))

;; Button callbacks (called when button pressed)
(on-button-a (lambda () (set! y (- y 4))))  ;; Up
(on-button-b (lambda () (set! y (+ y 4))))  ;; Down
(on-button-x (lambda () (set! x (- x 4))))  ;; Left
(on-button-y (lambda () (set! x (+ x 4))))  ;; Right

;; Start game loop
(start)

;; Stop game loop
(stop)
```

## Example Games

### Minimal Game

```lisp
(define x 160)
(define y 120)

(on-button-a (lambda () (set! y (- y 4))))
(on-button-b (lambda () (set! y (+ y 4))))
(on-button-x (lambda () (set! x (- x 4))))
(on-button-y (lambda () (set! x (+ x 4))))

(on-update (lambda ()
  (clear 0x0000)
  (fill-rect x y 16 16 0x07E0)
  (draw-text 10 10 "Move the box!" 0xFFFF 0x0000)))

(start)
```

### Snake Game

See browser emulator for full implementation with:
- Wrapping movement
- Food collection
- Score tracking

### Sprite-based Shooter

See `main.c` for full implementation with:
- Player and enemy sprites
- Movement and collision
- Score system

## Memory Configuration

Edit `lisp_vm.h` to adjust memory limits:

```c
#define LISP_HEAP_SIZE 8192        // Cons cells (32 bytes each)
#define LISP_SYMBOL_TABLE_SIZE 256 // Unique symbols
#define LISP_STACK_SIZE 256        // Evaluation depth
#define LISP_MAX_SPRITES 32        // Max sprites
#define LISP_SPRITE_MAX_SIZE 32    // Max sprite dimension
```

*Memory usage* (approximate):
- Heap: 8192 × 32 bytes = 256 KB
- Sprites: 32 × 32×32×2 = 64 KB
- *Total*: ~320 KB (fits in Pico 2's 264 KB SRAM with optimization)

For larger games, reduce `LISP_HEAP_SIZE` or `LISP_MAX_SPRITES`.

## File Structure

```
picolisp_game/
├── display.h           # Display driver interface
├── display.c           # ST7789 display + button driver
├── lisp_vm.h          # VM interface
├── lisp_vm.c          # Parser, evaluator, GC
├── lisp_builtins.c    # Built-in functions
├── main.c             # Example game
├── CMakeLists.txt     # Build configuration
├── README.md          # This file
└── lisp_game_vm.html  # Browser emulator
```

## Development Workflow

1. *Prototype in browser*: Fast iteration, instant feedback
2. *Test on hardware*: Verify performance and memory usage
3. *Optimize*: Adjust memory limits, use framebuffer efficiently

## Performance Tips

- Use framebuffer for smooth rendering (allocated once at startup)
- Minimize sprite count (max 32 by default)
- Keep game logic simple (complex math is slow in interpreted Lisp)
- Use integer arithmetic (floats are slower)
- Reuse variables instead of creating many temporaries

## Extending the System

### Add New Built-in Function

1. *Define in `lisp_vm.h`*:
```c
lisp_value_t* lisp_builtin_random(lisp_vm_t *vm, lisp_value_t *args);
```

2. *Implement in `lisp_builtins.c`*:
```c
lisp_value_t* lisp_builtin_random(lisp_vm_t *vm, lisp_value_t *args) {
    int32_t max = get_num(lisp_car(args));
    return lisp_number(vm, rand() % max);
}
```

3. *Register in `lisp_init()`*:
```c
REGISTER("random", lisp_builtin_random);
```

### Load Game from File

Embed game script in header file:
```c
// game_script.h
const char GAME_SCRIPT[] = 
"(define x 100)\n"
"(on-update (lambda () ...))\n"
"(start)\n";
```

## Troubleshooting

*"Out of memory"*: Reduce `LISP_HEAP_SIZE` or simplify game logic

*Slow performance*: 
- Use framebuffer (`disp_framebuffer_alloc()`)
- Reduce sprite count
- Simplify update logic

## Future Enhancements

- Sound/music support (PWM audio)
- Save/load game state (flash storage)
- Network play (Pico W wifi)
- Advanced graphics (line drawing, circles)
- Bytecode compiler for better performance
- REPL over USB for live coding
