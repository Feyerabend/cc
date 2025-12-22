
## Ferrite: An Experimental Language Inspired by Rust

The language in these examples is called *Ferrite* (file extension `.fe`,
from "Fe" for iron in the periodic table, tying into the material "ferrite").

It is a small, educational or toy programming language *heavily inspired by Rust*,
designed to illustrate key Rust concepts like ownership, borrowing, and lifetimes
in a simplified, functional-leaning syntax.


### Some Features and Rust Inspirations

- *Borrowing and References*: 
  - Uses `(borrow expr)` to create a reference `(& Type)`.
  - Function parameters like `(& Point)` or `(& List)` take borrowed references.
  - This directly mirrors Rust's borrowing system to prevent mutation aliasing
    and enforce lifetimes (e.g., in `borrow.fe`, borrowing allows access without
    moving ownership).

- *Structs and Pattern Matching*:
  - `defstruct` defines structs with named fields (like Rust's `struct`).
  - Field access via `.` (e.g., `. p x`).
  - Pattern matching with `match` and destructuring (e.g., `(Point x y)`),
    very similar to Rust's `match` and struct patterns.

- *Algebraic Data Types for Lists*:
  - Linked lists via variants: `Nil` and `Cons(head, tail: &List)`, recursive with borrowing.
  - This emulates Rust's enum-based recursive types (like `Option` or `List`),
    but requires explicit borrowing for recursion.

- *Functions and Recursion*:
  - `defn` for functions, with parameters in double parens.
  - Supports recursion (e.g., factorial, Fibonacci, GCD, prime check).
  - Simple `if`, `let` bindings, arithmetic, and `print`.

- *No Mutation or Ownership Moves Visible*:
  - Everything appears immutable; no visible `mut` or move semantics.
  - Ownership is implicit through borrowing (values can be "moved" by not
    borrowing, but examples mostly borrow).

- *Other Elements*:
  - Only `i32` type shown, basic control flow.
  - Entry point is `main ()`.
  - Lisp-like syntax with double parentheses: `(defn name ((args)) body)`,
    `(let ((bindings)) body)`, `(if cond then else)`.

### Comparison to Rust Syntax

| Concept              | Ferrite Example                          | Rust Equivalent                              |
|----------------------|------------------------------------------|----------------------------------------------|
| Struct definition    | `(defstruct Point (x i32) (y i32))`      | `struct Point { x: i32, y: i32 }`            |
| Borrowing            | `(borrow p)` → `(& Point)`               | `&p`                                         |
| Field access         | `(. p x)`                                | `p.x`                                        |
| Function param       | `(p (& Point))`                          | `p: &Point`                                  |
| Pattern match        | `(match p ((Point x y) ...))`            | `match p { Point { x, y } => ... }`          |
| List cons            | `(Cons 1 (borrow tail))`                 | `Cons(1, Box::new(tail))` (with Box for heap)|

This language seems designed as a teaching tool or prototype to demonstrate Rust's core
ownership model in a more minimal, Scheme/Lisp-influenced syntax (double parens, prefix notation).

The examples cover classics like Fibonacci, GCD, primes, recursion, and data structures--perfect
for exploring safe references without full Rust complexity.

