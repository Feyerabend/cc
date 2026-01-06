
## Ferrite Tutorial

Ferrite is a simple, statically-typed programming language with Lisp-like syntax,
inspired by functional languages and Rust's ownership model. It compiles to C code
for efficiency and portability. Ferrite emphasises safe memory management through
borrowing and lifetimes, preventing common errors like use-after-free or data races
at compile time. This tutorial covers the basics, assuming familiarity with programming
concepts but no prior knowledge of Ferrite.

We'll use short, original code snippets to illustrate concepts. To follow along,
save code in a `.fe` file and compile it using the provided Ferrite compiler
(e.g., `python3 ferrite.py input.fe` to generate `input.c`, then compile the
C file with `gcc input.c -o output` and run `./output`).


### 1. Introduction

Ferrite programs consist of top-level forms like structure definitions and functions.
All code uses S-expressions (parenthesised lists). Comments start with `;;`.

A minimal program might look like this:

```lisp
(defn main ()
  (print 42))
```

This defines a `main` function that prints 42. Ferrite's type system includes primitives
like integers, and it supports recursion, pattern matching, and references with ownership tracking.


### 2. Basic Syntax

- *Atoms*: Numbers (e.g., `5`, `-3`), symbols (e.g., `x`, `+`), or strings
  (though limited support in this version).
- *Lists*: Enclosed in parentheses, e.g., `(add 1 2)`.
- *Expressions*: Everything is an expression; even control flow returns values.
- *Operators*: Arithmetic like `+`, `-`, `*`, `/`, `%`; comparisons like `==`, `<`, `>`, `<=`, `>=`.
- *Whitespace and Comments*: Ignored except in atoms; `;` starts a line comment.

Expressions are evaluated from innermost to outermost. Function calls and special forms use prefix notation.


### 3. Data Types

Ferrite has a simple type system:

- *Primitives*:
  - `i32`: 32-bit signed integer.
  - `unit`: Void type (like `void` in C), for functions with no return value.
  - `bool`: Boolean (though not explicitly used in ops; comparisons return `i32` where 0 is false).

- *Structures*: User-defined via `defstruct`.
- *References*: `(& Type)` for immutable borrows; mutable references with `(&mut Type)`.
- *Lifetimes*: Annotated as `'a` for tracking reference validity (inferred or explicit).
- *Other*: `List` is a built-in for linked lists, but treat it as opaque.

Types are declared in function parameters and returns. Inference is limited, so specify types where needed.

Ferrite uses double parentheses like `((path String))` in parameter lists because each parameter
is represented as a tiny two-element list: one for the name and one for the type.
This nested structure keeps the syntax clean and consistent in a Lisp-like S-expression world,
clearly pairing each name with its required type without introducing new punctuation or keywords.
It mirrors Rust's `fn foo(p: &Point)` visually: `(p (& Point))` reflects "name: type".


### 4. Defining Structures

Use `defstruct` to define composite types. It takes a name and field-type pairs.

Syntax:
```lisp
(defstruct Name (field1 Type1) (field2 Type2) ...)
```

Fields are accessed with `.` (dot notation), e.g., `(. var field)`.

Example:
```lisp
(defstruct Box (value i32))
```

This creates a `Box` struct with an `i32` field. Instantiate with `(Box 100)`.

Structures are not Copy by default; ownership rules apply.


### 5. Functions

Define functions with `defn`. They can have parameters,
an optional return type (defaults to `i32`), and a body.

Syntax:
```lisp
(defn name ((param1 Type1) (param2 Type2) ...) ReturnType
  body-expr1
  body-expr2
  ...)
```

- If no return type, assume `i32`.
- Body is a sequence of expressions; the last one's value is returned.
- `main` is the entry point, returns `unit` implicitly.
- Recursion is supported (no loops in this version).

Example:
```lisp
(defn add ((a i32) (b i32)) i32
  (+ a b))
```

Call it as `(add 3 4)`. Functions can take references for borrowing.


### 6. Variables and Bindings

Use `let` to bind values. It's an expression that introduces a new scope.

Syntax:
```lisp
(let ((var1 value1) (var2 value2) ...)
  body)
```

- Bindings are immutable by default.
- Values can be expressions, including struct creations or function calls.
- Scope is lexical; inner `let` shadows outer ones.

Example:
```lisp
(let ((num 5))
  (print num))
```

Ownership: Bound values are owned unless borrowed. Moving a value
(e.g., passing to a function that takes ownership) invalidates it.


### 7. Control Structures

#### If Expressions

`if` is an expression for conditional branching.

Syntax:
```lisp
(if condition
    then-branch
    else-branch)
```

- Condition is an expression evaluating to `i32` (non-zero is true).
- Both branches must return the same type.

Example:
```lisp
(if (> x 0)
    (print x)
    (print (- x)))
```

No `else if`; nest `if`s.


#### Pattern Matching

Use `match` for destructuring and branching, especially on structs.

Syntax:
```lisp
(match expr
  ((Pattern1) body1)
  ((Pattern2) body2)
  ...)
```

- Patterns: Struct names with bindings, e.g., `(StructName bind1 bind2)`.
- `_` ignores a field.
- Must be exhaustive or compiler errors.

Example (assuming a `Maybe` struct variants):
```lisp
(defstruct Nothing ())
(defstruct Just (value i32))

(match maybe-val
  ((Nothing) 0)
  ((Just v) v))
```


### 8. Ownership and Borrowing

Ferrite borrows Rust's model to ensure memory safety:

- *Ownership*: Each value has one owner. When owner goes out of scope, value is dropped.
- *Moving*: Passing owned values to functions transfers ownership (unless type is Copy, like primitives).
- *Borrowing*: Use `borrow` or `borrow-mut` to create references without moving.
  - Immutable borrow: `(& Type)`, multiple allowed.
  - Mutable borrow: `(&mut Type)`, exclusive (no other borrows).
- *Lifetimes*: Ensure references don't outlive owners. Use `'a` annotations if needed.

Syntax for references:
- Parameter: `((p (& Struct)))`
- Borrow: `(borrow var)` or `(borrow-mut var)`
- Cannot use a value after moving it.
- Multiple immutable borrows OK; mixing mutable/immutable not allowed while borrow active.

Example:
```lisp
(defstruct Item (count i32))

(defn inspect ((i (& Item))) i32
  (. i count))

(let ((item (Item 100)))
  (inspect (borrow item))
  ;; item still usable here
  (print (. item count)))
```

Compiler tracks borrows and prevents invalid uses (e.g., use after move).


### 9. Built-ins and I/O

- `print`: Outputs an `i32` (maps to `printf` in C).
- Arithmetic and comparison ops are built-in.
- No strings or advanced I/O in this basic version.
- Lists: Use `Nil` and `Cons` structs for linked lists.


### 10. Compiling and Error Handling

- Compile: Run the Ferrite compiler on your `.fe` file to get `.c`.
- Common Errors: Type mismatches, non-exhaustive matches, ownership violations
  (e.g., use after move).
- Debug: Compiler reports errors like "Moved value used" or "Mutable borrow conflict".


### Advanced Tips

- Use recursion for iteration (no loops).
- Structs can nest; references enable tree-like structures.
- For performance, prefer borrows over copies.
- Extend with more types or traits in future versions (project!).

Practice by writing small programs, like a simple calculator or tree traversal.
Experiment with borrowing to see compiler safeguards in action! If you encounter
issues, check the generated C code for insights. And use the test framework,
to start trace bugs and other issues.

