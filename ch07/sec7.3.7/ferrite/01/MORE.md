
## More Projects
Here are some progressively more ambitious project ideas that can be built on top of.
They are ordered roughly from "easier / quicker" to "very ambitious / long-term".

| # | Project Name | Difficulty | Main Learning/Challenge Areas | Estimated Effort | "Cool Factor" |
|---|--------------|------------|-------------------------------|------------------|---------------|
| 1 | Ferrite Standard Library | *-- | basic types, functions, borrowing | 1-3 weeks | **- |
| 2 | Tiny Game - "Ferrite Snake" | **- | foreign function interface (SDL/raylib), loops via recursion| 2-5 weeks | *** |
| 3 | Ferrite -> LLVM backend | *** | IR generation, calling convention, memory layout | 2-8 months | **** |
| 4 | Algebraic Data Types + real `match` | **- | enum support, better pattern matching, tag + payload | 3-8 weeks | *** |
| 5 | Mini borrow checker improvements | *** | NLL-like analysis, reborrowing, split borrows | 2-6 months | **** |
| 6 | Ferrite Package Manager / Build Tool | **- | module system, dependency resolution, simple build graph | 1-4 months | *** |
| 7 | Self-hosted Ferrite compiler | **** | bootstrap, rewriting parser+type-checker+codegen in Ferrite| 1-3 years | ***** |
| 8 | Safe systems programming playground | *** | kernel-like abstractions, no_std mode, memory mapped I/O | 6-18 months | **** |
| 9 | Ferrite -> WASM backend | *** | wasm text/binary format, linear memory, function table | 3-10 months | **** |
| 10 | Ferrite + effect system experiment | **** | tagged unions + effects, row polymorphism, `try`/`?` syntax | 6-24 months | ***** |


### Starter projects (1-6 months)

1. *Ferrite Prelude / tiny standard library*

   Add `Option`, `Result`, basic `String` (or `&str`), `Vec`,
   `HashMap` (very simple hash table), `assert!`, etc.

2. *Ferrite Snake / Tetris / simple roguelike*

   Bindings to raylib or very simple terminal + ncurses ->
   very satisfying first "real" program (or use the RPI Pico)

3. *Better pattern matching + sum types*

 ```lisp
(defenum Maybe (Nothing) (Just i32))

(defn unwrap-or ((opt (Maybe i32)) (default i32)) i32
  (match opt
    ((Nothing) default)
    ((Just v)  v)))
 ```

 This is one of the most requested features after ownership.


4. *Simple module system + file imports*

 ```lisp
 ;; file: math.fe
 (defn add ((a i32) (b i32)) i32 (+ a b))

 ;; file: main.fe
 (import math)
 (print (math/add 7 11))
 ```


### Medium-term projects (6-18 months)

5. *LLVM backend* (most popular realistic next big step) 

Many stop at C backend -> going to LLVM gives you:
 - real optimisations
 - much better debugging experience
 - easier platform support
 - path to serious language status

6. *More sophisticated borrow checker*

Current implementation is quite naïve. Adding:
 - non-lexical lifetimes
 - reborrowing
 - mutable split borrows
 - partial moves

would make the language feel much more modern/Rust-like

7. *Ferrite -> WebAssembly*

Very attractive target. You could run Ferrite code directly
in the browser (especially nice for tiny games or demos)


### Long-term projects

8. *Self-hosting Ferrite*

The classic rite of passage. (A programming language's own compiler
(or interpreter) is written in that same language).

9. *Ferrite as a safe-systems language*

Try to write tiny kernels, drivers, firmware, or unikernels in Ferrite
(requires no_std mode + very good FFI + strong control over memory layout)

10. *Effects / Capabilities / Algebraic effects experiment*

One interesting current research direction.
Ferrite is small enough that you can realistically
try to add something like `try`/`?` + effects

Given:
```lisp
(defn process-file ((path String)) (Result String Error)
  (let ((file  (try-open path))           ;; manual error handling
        (data (try-read-all file)))
    (try-close file)
    (if (error? data)
        (Err data)
        (Ok (process data)))))
```

Replace by:
```
(effectful [io]                           ;; declares: this function does I/O
  (defn process-file ((path String)) String
    (let ((data (? (read-file path))))    ;; ? = "propagate any io error"
      (process data))))
```

Or even:
```lisp
(defn process-file ((path String)) String / io
  (let ((data (? (read-file path))))
    (process data)))
```


### Recommended starting order

1. Better match + sum types (enums)
2. Tiny standard library (Option, Result, Vec, String view)
3. Real game with raylib / SDL2 bindings
4. LLVM backend
5. Much better borrow checker
6. Modules + package manager
7. Self-hosting dream

