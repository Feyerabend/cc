
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



### The Problem: Memory Safety

When programs run, they need to manage memory. The fundamental challenge is:
- *How do we know when it's safe to free/deallocate memory?*
- *How do we prevent using memory after it's been freed?*

Traditional solutions have tradeoffs:
- *Garbage collection*: Safe but slow, unpredictable pauses
- *Manual management* (C/C++): Fast but error-prone, causes bugs like use-after-free, double-free


### Ownership: Who's Responsible?

*Core idea*: Every piece of data has exactly one "owner"--the
variable responsible for cleaning it up.

Think of it like *library books*:
- When you check out a book, YOU own it
- You're responsible for returning it
- Only one person can own that specific book at a time
- When you return it (owner goes out of scope), the library gets it back

*Why this matters*:
```
function example() {
    let book = checkout_book()  // You own this book
    
    // book goes out of scope here - automatically returned
}
```

The compiler knows exactly when to free memory
because it knows when the owner disappears.


### Moving Ownership: Transferring Responsibility

Sometimes you want to give your data to someone else:

```
let original_owner = create_data()
let new_owner = original_owner  // Ownership transferred!

// Can't use original_owner anymore - you gave it away
```

Like selling your bike--once you transfer the title,
you no longer have the right to ride it.

*Why prevent using moved values?*
- Prevents double-free: two variables trying to clean up the same memory
- Prevents use-after-free: using memory that's already been cleaned up


### Borrowing: Temporary Access Without Taking Ownership

*Core idea*: Sometimes you just need to look at or use data temporarily,
without taking full responsibility for it.

Like *borrowing a friend's laptop*:
- You can use it, but you don't own it
- Your friend still owns it
- You must give it back
- Your friend can't throw it away while you're using it

*Two types of borrowing*:


#### Immutable Borrow (Read-Only)
Multiple people can look at the same data simultaneously:
```
let data = create_data()
let reader1 = borrow(data)    // Just looking
let reader2 = borrow(data)    // Also just looking
// Many readers are fine, nobody is modifying
```

Like multiple people reading the same book at a library
(maybe a reference book that can't be checked out).


#### Mutable Borrow (Exclusive Write Access)
Only one person can modify data at a time:
```
let data = create_data()
let writer = mut_borrow(data)  // Exclusive access
// Can't create any other borrows while writer exists
```

*Why this rule?* Prevents *data races*:
- If one person is modifying data while another is reading it,
  the reader sees inconsistent state
- Like editing a document while someone else is reading
  it--they might see half-written sentences


### Lifetimes: How Long Is The Borrow Valid?

*Core idea*: A borrowed reference can't outlive the data it points to.

The problem lifetimes solve:
```
let reference = null

{
    let temporary_data = create_data()
    reference = borrow(temporary_data)
}  // temporary_data is destroyed here

// ERROR: reference points to destroyed data (dangling pointer!)
```

*Think of it like*:
- You can't keep a library book after the library burns down
- A restaurant menu reference isn't valid after the restaurant closes
- A hotel room key doesn't work after checkout

*Lifetime relationships*:
When a function returns a borrowed reference, we need to know which input it came from:

```
function pick_larger(a, b):
    // Returns a reference to either a or b
    // But which one? The returned reference must not outlive BOTH inputs
    if value_of(a) > value_of(b):
        return borrow(a)
    else:
        return borrow(b)
```

The compiler needs to track: "this returned reference is valid
as long as BOTH a and b are valid"


### Why This All Matters

These three concepts work together to provide *compile-time guarantees*:

1. *No use-after-free*: Can't use data after its owner is gone
2. *No double-free*: Only the owner cleans up, and ownership is exclusive
3. *No data races*: Can't modify while others are reading
4. *No dangling pointers*: Borrows can't outlive their data

And it's all checked *at compile time* - zero runtime overhead!


### Real-World Analogy: A Shared Kitchen

- *Ownership*: You bought ingredients, you're responsible for them
- *Moving*: You give ingredients to your roommate--now they're responsible
- *Immutable borrow*: Multiple people can look at a recipe simultaneously
- *Mutable borrow*: Only one person can use the stove at a time (exclusive access)
- *Lifetimes*: Can't use a recipe reference after the cookbook is thrown away

The compiler acts like a strict but helpful kitchen manager,
preventing chaos by enforcing these rules before anyone even starts cooking!




### How Ownership Actually Works

*The mechanism*: Static scope analysis at compile time.

The compiler tracks every value's lifetime by analyzing the code's structure:

```
{                           // Scope begins
    let x = allocate(100)   // Compiler notes: x owns memory M1
    
    // Compiler knows: M1 is valid here
    use(x)
    
}                           // Scope ends: Compiler inserts: free(M1)
```

*The solution*: 
- Compiler builds a graph of which variable owns what
- At scope exit, compiler automatically inserts cleanup code
- No runtime tracking needed--it's all determined during compilation

*Example - preventing double-free*:
```
let x = allocate(100)   // x owns M1
let y = x               // Compiler marks: ownership moved to y
                        // x is now "dead" - can't be used
use(y)                  // OK
use(x)                  // COMPILE ERROR: "x was moved"
```

The compiler literally forbids accessing `x` after the move,
not at runtime, but by refusing to compile the code.


### How Borrowing Actually Works

*The mechanism*: Reference counting at compile time + access restrictions.

The compiler maintains, for each value, a count of active borrows:

```
let data = allocate(100)     // Compiler: data owns M1, borrow_count=0

let ref1 = borrow(data)      // Compiler: borrow_count=1, type=immutable
let ref2 = borrow(data)      // Compiler: borrow_count=2, type=immutable

// Compiler checks: can we move/mutate data?
// Answer: NO - borrow_count > 0

drop(ref1)                   // borrow_count=1
drop(ref2)                   // borrow_count=0

// Now data can be moved/freed
```

*The enforcement rules*:

1. *While immutable borrows exist (count > 0, all immutable)*:
   - Can create more immutable borrows
   - Cannot create mutable borrows
   - Cannot move ownership
   - Cannot mutate the original

2. *While a mutable borrow exists (count = 1, mutable)*:
   - Cannot create any other borrows
   - Cannot access the original data at all

The compiler enforces these by analyzing all possible code paths.

*Example - preventing concurrent modification*:
```
let data = allocate(100)
let reader = borrow(data)         // immutable borrow

let writer = mut_borrow(data)     // COMPILE ERROR!
// Compiler: "cannot borrow mutably while immutably borrowed"
```

The compiler sees both borrows are active in overlapping scopes and rejects it.


### How Lifetimes Actually Work

*The mechanism*: Constraint solving with scope annotations.

The compiler assigns every reference a "lifetime". Essentially is is a label
representing how long it's valid. Then it solves constraints to ensure
no reference outlives its data.

*Step 1: Assign lifetime variables*:
```
{                                    // lifetime 'a begins
    let data = allocate(100)         // data has lifetime 'a
    {                                // lifetime 'b begins (nested in 'a)
        let ref = borrow(data)       // ref has lifetime 'b, points to lifetime 'a
    }                                // lifetime 'b ends
}                                    // lifetime 'a ends
```

*Step 2: Check constraints*:
The compiler verifies: `'b ⊆ 'a` (lifetime 'b is contained within 'a)

If this relationship is violated, compilation fails:

```
let ref = null                       // lifetime 'outer
{                                    // lifetime 'inner begins
    let data = allocate(100)         // data: 'inner
    ref = borrow(data)               // PROBLEM: ref is 'outer, data is 'inner
}                                    // 'inner ends, data destroyed

// Compiler error: "data does not live long enough"
// Constraint violated: 'outer ⊄ 'inner
```

*The solution mechanism*: 
The compiler builds a directed graph of lifetime relationships and checks for violations:
- Nodes: lifetimes
- Edges: "outlives" relationships
- Check: no reference's lifetime extends beyond what it points to

*For functions*, the compiler infers relationships:
```
function longest(a, b):              
    // Compiler inference:
    // - a has some lifetime 'x
    // - b has some lifetime 'y  
    // - result must have lifetime 'min('x, 'y)
    //   (whichever ends first)
    
    if len(a) > len(b):
        return borrow(a)
    else:
        return borrow(b)
```

When you call this function:
```
{                                    // lifetime 'a
    let str1 = "hello"              
    let result
    {                                // lifetime 'b (nested)
        let str2 = "world"
        result = longest(str1, str2) // result has lifetime 'b
    }                                // 'b ends
    
    use(result)                      // COMPILE ERROR
    // Compiler: result's lifetime is 'b, which ended
}
```

The compiler calculated that `result` can only live as long as the
shorter-lived input (`str2` with lifetime 'b), so using it after 'b ends is forbidden.


### The Complete Picture: A Three-Phase Process

*Phase 1: Build the ownership graph*
- Track which variables own what
- Mark moves when ownership transfers
- Detect use-after-move

*Phase 2: Track borrow sets*
- For each variable, maintain set of active borrows
- Check borrow rules on every access
- Ensure exclusive mutable access

*Phase 3: Solve lifetime constraints*
- Assign lifetime variables to all references
- Build constraint system (X must outlive Y)
- Use constraint solver to find violations

All of this happens at *compile time* through static analysis.
The generated machine code contains:
- No ownership tracking (just normal pointers)
- No borrow counters (all checks done)
- No lifetime information (all proven safe)

*The key insight*: These aren't runtime checks: they're compile-time *proofs*.
The compiler mathematically proves your program is memory-safe,
then compiles to code as fast as manual C.


