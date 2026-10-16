## A Lisp Game Engine

A small Lisp interpreter for writing games on a Raspberry Pi Pico 2 with
a Pimoroni Display Pack 2.0 (320x240 IPS screen, four buttons).

- *Same code on PC and Pico*: games can be tried, tested and turned into
  screenshots on a PC before they go onto the hardware
- *Sprites*: pixel art sprites up to 32x32, with a transparent colour
- *Collision detection*: overlapping rectangles
- *Framebuffer rendering*: each frame is drawn off screen and sent with DMA
- *Fixed memory*: a heap of cells with a mark-sweep garbage collector
- *Proper tail calls*: a game can loop by recursion without running out of stack

Hardware:
- Raspberry Pi Pico 2 (or Pico 2 W), with RP2350
- Pimoroni Display Pack 2.0 (320x240 IPS, ST7789 controller, buttons A, B, X, Y)


### Quick start on a PC

```sh
make                                  # builds ./lisp_host
./lisp_host                           # interactive prompt
./lisp_host examples/snake.lisp -f 300 -p a@60 -p x@100 -o snake.ppm
make test                             # runs the tests
```

`lisp_host` runs a game for a number of frames (`-f`, default 300) with
simulated button presses (`-p`) and can save the last frame as an image
(`-o`, PPM format). `-p x@100` presses X at frame 100; `-p x@100-140` holds
it from frame 100 to 140. Errors are reported with the frame they happened in.


### Building for the Pico 2

```sh
mkdir build
cd build
cmake -DGAME=shooter ..               # or minimal, snake, ...
make
```

Then copy `picolisp_game.uf2` to the Pico in BOOTSEL mode. `GAME` names a
file in `examples/`; the file is built into the program. Messages (errors,
frame rate, memory use) are printed on the USB serial port, and errors are
also shown on the screen.


## Language Reference

### Values

- Numbers are 32-bit integers, written `42`, `-7` or `0xF800`.
  Arithmetic wraps around on overflow.
- Strings are written `"Score:"`, with `\n`, `\t`, `\"` and `\\` as escapes.
- Symbols are names such as `player-x` or `set!`.
- Lists are written `(1 2 3)`; the empty list is `()` or `nil`.
- `nil`, `()` and `0` are false. Everything else is true.
  Comparisons return `1` or `0`.

### Special forms

```lisp
(define x 100)                  ; global variable
(define (add a b) (+ a b))      ; global function
(set! x 150)                    ; change a variable
(lambda (a b) expr ...)         ; function; the last expression is the result
(if test then else)             ; else is optional
(cond (test expr ...) ... (else expr ...))
(when test expr ...)
(and a b ...)                   ; stops at the first false value
(or a b ...)                    ; stops at the first true value
(begin expr ...)
(let ((name value) ...) expr ...)
(while test expr ...)
(quote x)   or   'x
```

`define` always makes a global definition, also when it is used inside
a function. Use `let` for local variables.

### Built-in functions

| Function | Meaning |
| --- | --- |
| `+ - * /` | Arithmetic. `/` divides with truncation; `(- x)` negates |
| `mod abs min max` | `(mod -1 10)` is 9 |
| `random` | `(random n)` gives 0 to n-1 |
| `= < > <= >=` | `(< a b c)` means a < b < c |
| `not eq?` | `eq?` compares numbers by value, other values by identity |
| `cons car cdr list` | `(car ())` and `(cdr ())` are `()` |
| `length nth reverse` | `(nth 0 lst)` is the first element |
| `null? pair? number?` | Type tests |
| `number->string` | `(number->string 42)` is `"42"` |
| `print` | Writes its arguments to the console (USB serial on the Pico) |


## Game API

### Drawing

Colours are RGB565 numbers. Drawing outside the screen is clipped.

```lisp
(clear 0x0000)                          ; fill the screen
(fill-rect x y width height color)
(draw-text x y "Hello!" fg-color bg-color)
(draw-text x y score fg-color bg-color) ; numbers are drawn too
```

Characters are 6 pixels wide and 8 pixels high.

Common colours: `0x0000` black, `0xFFFF` white, `0xF800` red, `0x07E0` green,
`0x001F` blue, `0xFFE0` yellow, `0x07FF` cyan, `0xF81F` magenta.

### Sprites

```lisp
(define ship (make-sprite 8 8))          ; starts fully transparent
(sprite-set-pixel ship 3 0 0x07E0)
(sprite-fill ship 0 5 8 2 0x07E0)        ; x y width height color
(draw-sprite ship x y)
```

Magenta (`0xF81F`) is the transparent colour: those pixels are not drawn.
At most 32 sprites can exist at the same time; sprites that are no longer
used are freed by the garbage collector.

### Collision

```lisp
(collide? x1 y1 w1 h1 x2 y2 w2 h2)      ; do the two rectangles overlap?
```

### Buttons and the game loop

```lisp
(on-update (lambda () ...))             ; called every frame, about 60 per second
(on-button-a (lambda () ...))           ; called once when A is pressed
(on-button-b ...) (on-button-x ...) (on-button-y ...)
(button? button-x)                      ; true while X is held down
(start)                                 ; start the game loop
(stop)                                  ; stop it
```

The constants `button-a`, `button-b`, `button-x`, `button-y`,
`screen-width` (320) and `screen-height` (240) are predefined.

A game file first sets things up, then calls `(start)`. After that the
loop calls the button callbacks and the update callback every frame and
sends the framebuffer to the display.


## Example Games

- `examples/minimal.lisp`: move a box with the buttons
- `examples/shooter.lisp`: hold X and Y to move, A fires, B restarts
- `examples/snake.lisp`: A, B, X and Y steer; uses lists for the snake

The smallest game:

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


## How It Works

*Values.* Every value is a 16-byte cell in a fixed array: a type tag and
a union holding a number, a pair of pointers (car and cdr), a function,
and so on. Symbols are interned, so two symbols with the same name are
the same cell, and a symbol cell also holds the symbol's global value.

*Evaluation.* `lisp_eval` walks the list structure directly. Expressions
in tail position (the branches of `if`, the last expression in a function
body, and so on) are evaluated by looping inside `lisp_eval` instead of
calling it again, so a function that calls itself as its last step runs
in constant stack space. Other nesting is limited by `LISP_MAX_DEPTH`.

*Errors.* An error anywhere (an undefined name, a wrong type, running out
of memory) calls `lisp_fail`, which jumps back with `longjmp` to the
top-level call (`lisp_run` or `lisp_call`). That call returns `NULL`, and
`lisp_error` gives the message. The game shows it on the screen.

*Garbage collection.* Free cells are kept in a linked list. When it is
empty, the collector marks everything that can be reached from the roots
and puts all unmarked cells back on the list. Cells never move. The roots
are the symbols (and through them all global values), the callbacks, and
the C stack: values that C code holds in local variables while it is
evaluating are found by scanning the stack for words that point into the
heap. This is called conservative stack scanning. Before the scan,
`__builtin_unwind_init` forces the processor's registers onto the stack,
so values held only in registers are found too.

To test the collector, build with `-DLISP_GC_STRESS` (`make test` does
this): it then collects before every allocation and overwrites freed
cells, so a value it fails to find shows up at once as a wrong result.

*The two cores.* On the RP2350 the stack of core 0 is only 4 KB, which is
too little for a recursive interpreter. `main` therefore starts the game
on core 1 with a 32 KB stack of its own. Each level of Lisp nesting uses
about 60 to 80 bytes of stack on the Cortex-M33 (measured with
`-fstack-usage`), so a depth limit of 200 leaves plenty of room.

*The framebuffer.* The ST7789 display expects each pixel's high byte
first, while the processor stores the low byte first. The framebuffer
functions therefore store colours with their bytes swapped, so the whole
buffer can be sent to the display with one DMA transfer.


## Memory

Settings are in `lisp_vm.h`:

```c
#define LISP_HEAP_SIZE          8192  // Number of value cells
#define LISP_MAX_SYMBOLS        256   // Max unique symbols
#define LISP_STRING_SLOTS       32    // Strings created at run time
#define LISP_MAX_SPRITES        32
#define LISP_SPRITE_MAX_SIZE    32    // Max sprite dimension (32x32)
```

Memory use on the Pico 2 (520 KB of RAM):

| Part | Size |
| --- | --- |
| Heap, 8192 cells of 16 bytes | 128 KB |
| Sprites, 32 of 32x32 pixels | 64 KB |
| Symbol names, string literals and other VM state | 10 KB |
| Framebuffer, 320x240 pixels | 150 KB |
| Stack for core 1 | 32 KB |
| Total | about 385 KB |


## File Structure

```
lisp/
├── lisp_vm.h, lisp_vm.c   # Values, parser, evaluator, garbage collector
├── lisp_builtins.c        # Arithmetic, lists, printing
├── lisp_game.h, lisp_game.c  # Drawing, sprites, buttons, frame loop
├── display.h, display.c   # ST7789 display and button driver
├── font5x8.h              # Font used by the display
├── main.c                 # Pico program: runs the game on core 1
├── CMakeLists.txt         # Pico build
├── Makefile               # PC build and tests
├── host/                  # PC stand-in for the display, and lisp_host
├── examples/              # Games
└── tests/                 # Tests run by make test
```


## Extending the System

A built-in function gets its arguments evaluated, as a list:

```c
static lisp_value_t *bi_square(lisp_vm_t *vm, lisp_value_t *args) {
    int32_t n = lisp_to_int(vm, lisp_car(vm, args));
    return lisp_number(vm, n * n);
}
```

Register it in `lisp_register_builtins` (lisp_builtins.c) or
`lisp_game_init` (lisp_game.c):

```c
lisp_define_builtin(vm, "square", bi_square);
```

`lisp_to_int` and the other helpers call `lisp_fail` on a wrong type, so
the built-in does not need to check for errors itself.


## Troubleshooting

*"Out of memory"*: the game keeps too much data alive at once, or builds
an endless list. Raise `LISP_HEAP_SIZE` if there is RAM to spare.

*"Nested too deeply"*: a function calls itself in a way that is not a
tail call, for example `(+ 1 (f (- n 1)))`, too many times. Rewrite it
with an accumulator so the call is the last thing the function does.

*Nothing on the screen*: check the USB serial console for messages.


## Future Enhancements

- Sound (PWM audio)
- Saving high scores in flash
- Line and circle drawing
- A REPL over USB for live coding
- A bytecode compiler for speed
