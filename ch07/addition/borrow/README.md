
## Static Borrow and Resource Checker

This is a complete static ownership and resource checker in C,
suitable as the safety layer of a compiled language. If the checker
accepts a program, that program is memory-safe, leak-free, and free
of data races on owned values--with zero runtime overhead required.

This checker implements the core of a *borrow checker*--the static analysis
pass that enforces ownership and aliasing invariants in languages like Rust,
Vale, or Cyclone. It is written as a pure C library with no I/O or global
state: everything lives in a `BC` handle that a compiler front-end allocates,
feeds with operations, and then inspects for diagnostics.

The checker tracks:
- who owns each value at each program point
- which borrows are live and what kind they are
- whether borrows have read-only or read-write access
- whether borrows outlive their referents
- which external resources (files, sockets, locks, heap allocations) are open
- whether cleanup is provably complete on every exit path

A program that passes the checker with zero errors can be compiled without
any reference-counting, garbage collection, or runtime safety checks for the
properties the checker covers.


#### What it is __not__

This is not a type checker, not a parser, and not a code generator. It sits
*between* type inference and code generation in a compiler pipeline. It
assumes type-correct input: the compiler front-end knows what kind of thing
each name refers to and calls the appropriate `bc_*` function. The checker
then proves that the sequence of operations is safe.



### Files

```
checker.h   Public API: all structs, enums, and function declarations.
            A compiler front-end only needs to include this file.

checker.c   Implementation: pure checking logic. Zero I/O.
            Never calls printf or any output function.

diagram.h   Renderer API: turns BC events into human-readable diagrams.

diagram.c   Renderer implementation. Reads bc->events[] and bc->diags[].
            Never calls any bc_* function.

main.c      28 test scenarios covering every feature.
            Serves as both a test suite and a usage reference.
```

The separation between `checker.c` and `diagram.c` is a hard boundary: the
checker knows nothing about how it will be displayed, and the renderer knows
nothing about how checking decisions are made. A production compiler would
replace `diagram.c` entirely with its own error-formatting layer, keeping
`checker.c` unchanged.



### Building and Running

```sh
gcc -Wall -Wextra -std=c11 -o bc checker.c diagram.c main.c
./bc
```

No dependencies beyond a C11 compiler and standard library. The `BC` struct
is large (its event log holds full state snapshots); always allocate it on
the heap:

```c
BC *bc = calloc(1, sizeof *bc);
bc_init(bc);
/* .. use the checker .. */
free(bc);
```

But then its intended use is in a compiler situation. 


### Using It in a Compiler

The checker is designed to be driven by a compiler's MIR (mid-level
intermediate representation) or similar lowered form, after type-checking
and before code generation.

#### Typical compiler integration

```
Source code
    |
    v
Lexer / Parser
    |
    v
Type checker              <-- assigns types, resolves names
    |
    v
Lowering pass             <-- produces a linear sequence of named operations
    |
    v
Borrow checker (this!)    <-- bc_* calls, inspect bc->error_count
    |
    v
Code generation           <-- if error_count == 0, emit code with no safety checks
```

#### Walk-through: compiling a function

Given a source function like:

```rust
fn process(fd: FileHandle, buf: &mut [u8]) -> Result<(), Error> {
    let n = fd.read(buf)?;
    drop(fd);
    use_bytes(&buf[..n]);
    Ok(())
}
```

The compiler's lowering pass would emit something like:

```c
bc_scope_enter(bc);

bc_resource_acquire(bc, "fd",  RK_FILE);
bc_defer          (bc, "fd");              /* safety net for early return */
bc_declare        (bc, "buf", 1);
bc_borrow_mut_slice(bc, "buf_ref", "buf", 0, BUF_SIZE);

bc_use_write      (bc, "fd");              /* fd.read(...) mutates fd state */
bc_use_write      (bc, "buf_ref");         /* writes into buf               */
bc_release        (bc, "buf_ref");

bc_resource_release(bc, "fd");            /* explicit close — satisfies defer */

bc_borrow_slice   (bc, "result_slice", "buf", 0, N);
bc_use            (bc, "result_slice");
bc_release        (bc, "result_slice");

bc_scope_exit(bc);
```

If `bc->error_count == 0` after this sequence, the compiler can emit code
that calls `read()` and `close()` exactly once, with no runtime checks. The
checker has *proved* it.

#### The checker never needs to know about types

The `bc_*` functions only care about names and operations. The compiler
front-end is responsible for deciding, during type-checking, whether a given
expression is a move, a copy, or a borrow — and then calling the
corresponding `bc_*` function. The checker enforces the *consequences* of
those decisions but not the decisions themselves.

#### Handling early returns and panics

Any scope that can exit early (via `return`, `break`, `?`, or exception)
should have its resources registered with `bc_defer`. Then every possible
exit path must satisfy the defer before the scope exits. The checker verifies
this at `bc_scope_exit`. A compiler that models all exit paths as scope exits
gets early-return safety for free.



### Concepts and Theory

#### Ownership and Linear Types

The theoretical foundation is *linear type theory*, which originates in
Girard's linear logic (1987). In a linear type system, every value must be
used *exactly once*: neither ignored (which would leak it) nor used twice
(which would alias or double-free it).

The checker relaxes this to an *affine* system: a value may be used at most
once (it can be dropped without being used, but it cannot be used after being
dropped or moved). Resources tighten this back to fully linear: a resource
must be explicitly released.

In practice, this means:
- every value has exactly one owner at any point in time
- ownership can be transferred (moved), ending the previous owner's access
- when the owner goes out of scope, the value is destroyed exactly once
- two names can never simultaneously claim ownership of the same value

This gives you memory safety and the absence of double-frees entirely at
compile time, with no overhead.

#### Move Semantics

A *move* transfers ownership from one variable to another. After a move, the
source variable is in state `VS_MOVED` and any attempt to use it is an error.

```
let a = String::new();     // bc_declare(bc, "a", 0)
let b = a;                 // bc_move(bc, "b", "a")
use(a);                    // ERROR: use after move
use(b);                    // OK
```

The key invariant: the underlying memory slot has exactly one owner at all
times. A move does not copy memory — it transfers the *obligation* to clean
up that memory from `a` to `b`. The slot's `id` stays the same through a
move; only the name changes. Borrows follow the slot id, so any borrows of
`a` automatically become borrows of `b` after the move.

#### Copy Types

Types that are cheap and safe to duplicate bitwise (integers, booleans,
floats, and structs composed entirely of such) are marked as *Copy* types
with `bc_declare_copy`. For these, a "move" is silently treated as a copy:
the source remains valid, and the destination gets a fresh independent slot.

The checker emits a `DIAG_NOTE` when `bc_move` is called on a Copy type,
informing the compiler that a copy occurred. No error is raised.

This mirrors Rust's `Copy` trait exactly.

#### Partial Moves

A struct can have some of its fields moved out without the whole struct being
consumed. `bc_field_move(bc, "dst", "src", "field_name")` moves one named
field out of `src`. After this:
- `src` transitions to `VS_PARTIALLY_MOVED`
- the moved field is tracked by name in `src->moved_fields[]`
- attempting to move the same field again is an error
- attempting to use `src` as a whole (e.g. passing it to a function expecting
  the full struct) is an error
- the individual extracted field `dst` is a normal owned value

This models the behaviour of pattern matching in Rust (`let Pair { a, b } = p`)
and explicit field access moves. A compiler generating code for such patterns
would call `bc_field_move` once per extracted field.

#### Borrows: the Reference Model

The borrow system is the heart of the checker. It enforces the *aliasing XOR
mutation* invariant: at any point in time, a value has either:
- any number of active *shared borrows* (`&T`) — read-only references, or
- exactly one active *mutable borrow* (`&mut T`) — an exclusive read/write
  reference

but never both simultaneously. This is the fundamental rule that makes data
races on owned values impossible.

The invariant is maintained by the checker's conflict table:

| Existing \ New  | `&T` (shared) | `&mut T` (mutable) |
|-----------------|---------------|--------------------|
| nothing         | OK            | OK                 |
| `&T` borrows    | OK            | *ERROR*            |
| `&mut T` borrow | *ERROR*       | *ERROR*            |

Borrows are scoped: they are automatically released when the scope that
created them exits. They can also be released early with `bc_release`.

A borrow must not outlive its referent. The checker enforces this in two
ways: by detecting dangling borrows when a variable is dropped or moved while
borrowed, and by checking that borrows are fully released before their target
is dropped at scope exit (reverse drop order ensures this when scopes nest
naturally).

#### Use-Kind Checking

Not all uses of a name are equivalent. The checker distinguishes:
- `bc_use` — a read-only access; valid through any live borrow or owned variable
- `bc_use_write` — a mutation; requires either:
  - an owned mutable variable (`is_mut == 1`), or
  - an active `&mut T` borrow of the target

Attempting to write through a `&T` shared borrow is a type error:

```
let r = &x;          // shared borrow
write_through(r);    // ERROR: &T is read-only
```

This is the static enforcement of Rust's rule that `&T` is immutable. The
distinction matters for a compiler because it determines whether to emit a
store instruction or to reject the program at compile time.

#### Lifetime Regions

Lifetime regions are named scopes that constrain how long a borrow may live.
They are independent of lexical scopes: a region can span multiple lexical
scopes or be a subset of one. They correspond to Rust's named lifetime
parameters (`'a`, `'b`) in function signatures.

```c
bc_region_begin(bc, "'a");
bc_borrow_in_region(bc, "r", "data", "'a");
bc_use(bc, "r");
bc_region_end(bc, "'a");   // r's region ends — r becomes dangling
bc_use(bc, "r");           // ERROR
```

The checker maintains a table of open regions. When a region ends, all
borrows tagged to it are invalidated (set to `BS_DANGLING`). Any subsequent
use of those borrows is an error.

Regions are particularly useful for modelling function call boundaries: a
compiler can open a region at the call site, model the borrow that the
callee takes, and close the region when the call returns. This gives precise
lifetime tracking across function calls without requiring whole-program
analysis.

Outlives constraints (`bc_region_outlives`) record that one region is
guaranteed to live at least as long as another. These constraints are used
by region coercion to verify that a borrow in a longer-lived region can
safely be treated as a borrow in a shorter-lived one.

#### Non-Lexical Lifetimes

In a purely lexical borrow system, a borrow lives until the end of the
enclosing scope even if it is never used again after some early point. This
is overly conservative and rejects safe programs like:

```rust
let mut v = vec![1, 2, 3];
let first = &v[0];     // shared borrow
println!("{}", first); // last use of `first`
v.push(4);             // this should be OK — first is done
```

Non-lexical lifetimes (NLL), introduced in Rust 2018, end a borrow at its
*last use point* rather than at the end of its lexical scope. The checker
models this with `bc_last_use`:

```c
bc_borrow    (bc, "first", "v");
bc_use       (bc, "first");         // last use
bc_last_use  (bc, "first");         // NLL: borrow ends here
bc_borrow_mut(bc, "m", "v");        // now OK — first is gone
```

`bc_last_use` immediately calls `dec_borrow_counts` on the target, freeing
the target for re-borrowing even though the borrow name is still lexically
in scope. Any use of the borrow after `bc_last_use` is an error.

A compiler implementing NLL would compute the last-use point during a liveness
analysis pass before calling the borrow checker, then emit `bc_last_use` at
the appropriate point in the operation sequence.

#### Two-Phase Borrows

Some common patterns require a `&mut` borrow to be "intended" before it is
fully activated. The canonical example is `vec.push(vec.len())`:

```rust
vec.push(vec.len());
// Desugars to:
// tmp = vec.len();    // shared borrow of vec
// vec.push(tmp);      // mutable borrow of vec
```

A naive checker would reject this because the shared borrow of `vec` (for
`len`) appears to conflict with the mutable borrow (for `push`). Two-phase
borrows resolve this by splitting the mutable borrow into two phases:

1. *Reserve* (`bc_two_phase_reserve`): the `&mut` borrow is created in
   state `BS_RESERVED`. While reserved it does not count against the
   target's exclusivity — shared borrows can still be taken.

2. *Activate* (`bc_two_phase_activate`): the reserved borrow is promoted
   to `BS_ACTIVE`. From this point the normal exclusive rules apply.

```c
bc_two_phase_reserve (bc, "push_ref", "vec");   // reserve &mut vec
bc_borrow            (bc, "len_ref",  "vec");   // shared: still OK
bc_use               (bc, "len_ref");
bc_release           (bc, "len_ref");
bc_two_phase_activate(bc, "push_ref");           // now exclusive
bc_use_write         (bc, "push_ref");
bc_release           (bc, "push_ref");
```

The theoretical justification is that the reservation expresses *intent to
mutate* without yet establishing exclusivity. Shared borrows taken after the
reservation but before activation are valid as long as they are released
before activation.

#### Slice and Index Borrows

When a value is a collection (array, vector, string), it is often safe to
have multiple borrows of *different parts* of it simultaneously. The checker
supports this with slice borrows:

```c
bc_borrow_slice    (bc, "s1", "arr", 0, 4);   // arr[0..4)
bc_borrow_slice    (bc, "s2", "arr", 4, 8);   // arr[4..8): OK, non-overlapping
bc_borrow_mut_slice(bc, "m1", "arr", 0, 5);   // &mut arr[0..5)
bc_borrow_mut_slice(bc, "m2", "arr", 3, 7);   // ERROR: overlaps with m1
```

The conflict rule for slices:

- Two *shared* slice borrows are compatible if and only if their ranges do
  not overlap. (Non-overlapping shared slices are always fine.)
- A *mutable* slice borrow conflicts with any other borrow of the same owner
  whose range overlaps, whether shared or mutable.
- A whole-object borrow (no range) conflicts with any slice borrow of the
  same owner.

This models Rust's `split_at_mut` and similar patterns that the standard
borrow checker cannot handle without unsafe code. The range check is purely
static when indices are compile-time constants, and can be combined with a
runtime bounds check when they are not.

#### Interior Mutability

Some types provide a safe abstraction over mutation through a shared
reference. Rust's `RefCell<T>`, `Cell<T>`, and `Mutex<T>` are examples:
they accept `&self` (a shared borrow) but allow mutation of the inner value,
enforcing the aliasing XOR mutation rule at runtime instead of compile time.

The checker models this with `bc_declare_interior_mut`. Variables declared
this way are exempt from the write-through-shared-borrow error:

```c
bc_declare_interior_mut(bc, "cell");   // like RefCell<T>
bc_borrow              (bc, "r", "cell");
bc_use_write           (bc, "r");      // NOTE: runtime check applies, not an error
```

Instead of an error, the checker emits a `DIAG_NOTE` explaining that the
static check has been bypassed and that a runtime check (the `RefCell`
borrow counter, the mutex lock) is responsible for safety. A compiler would
use this note to know that it must emit the runtime check code at this site.

#### Resources

Resources are external capabilities (file handles, network sockets, heap
allocations, mutex locks) that require explicit paired acquire/release
operations and must not be leaked, double-released, or used after release.

The checker tracks resources as a layer on top of variables:
`bc_resource_acquire` creates both a `Var` and a `Resource` record.
`bc_resource_release` closes the resource and drops the owning variable.

At scope exit, any resource in that scope that has not been released
generates a `DIAG_ERROR` naming the resource kind:

```
FileHandle 'fd' leaked: acquired at event #2, never released
```

Resources use `ResourceKind` to produce human-readable diagnostics:
`RK_HEAP`, `RK_FILE`, `RK_SOCKET`, `RK_LOCK`, `RK_CUSTOM`. A language
can introduce new resource kinds by using `RK_CUSTOM` and post-processing
the diagnostic messages with its own kind names.

Resources compose cleanly with borrows: borrowing a resource handle is
valid; releasing the resource while it is borrowed produces a dangling
borrow error, exactly as for ordinary owned values.

#### Defer and Exit-Path Verification

`bc_defer(bc, "name")` registers a constraint: *before the current scope
exits, `name` must be released*. The checker verifies this at `bc_scope_exit`
by checking that every deferred entry for the current scope has its
`satisfied` flag set.

This is the static equivalent of:

- C++: RAII destructors
- Go: `defer` statement
- Java/Python: `try/finally` or `with` blocks
- Rust: `Drop` trait

For a compiler, the workflow is:

1. When a resource is acquired on an error-prone code path, call `bc_defer`
   immediately after `bc_resource_acquire`.
2. On the happy path, call `bc_resource_release` normally. This sets
   `satisfied = 1` on the matching defer.
3. On any error path, the scope will exit without calling
   `bc_resource_release`. The checker detects the unsatisfied defer and
   emits an error.

This means the compiler does not need to reason about which paths lead to
scope exit — it just registers the obligation once and the checker verifies
it.

When `bc_move` is called on a deferred variable, the defer is automatically
re-pointed to the new owner name, so cleanup obligations survive ownership
transfer.

#### Drop Order

When multiple variables are in scope simultaneously, the order in which they
are dropped matters: a variable that borrows another must be dropped before
the variable it borrows. The checker enforces drop order automatically at
scope exit using the `decl_order` field on each `Var`, which records the
position of the declaration within the scope.

Variables are dropped in *reverse declaration order* (LIFO), matching the
semantics of Rust, C++, and most languages with deterministic destruction.
This means:

```c
bc_declare(bc, "a", 0);   // decl_order = 0
bc_declare(bc, "b", 0);   // decl_order = 1
bc_borrow (bc, "r", "a"); // r borrows a
// At scope exit: b dropped first, then r, then a
// r is released before a — safe
```

If the source language uses a different drop order, the compiler would need
to emit explicit `bc_drop` calls in the desired order rather than relying on
`bc_scope_exit`.

#### Region Variance and Coercion

Lifetime regions support *covariant subtyping*: a borrow in a longer-lived
region can be used where a borrow in a shorter-lived region is expected. This
is because a longer-lived borrow provides strictly more guarantees than a
shorter-lived one.

`bc_coerce_region(bc, "ref", "'shorter")` re-tags a borrow from its current
region to a shorter-lived one. The checker verifies that the source region
outlives the target region using the `bc_region_outlives` constraint table.
If no such constraint exists, the coercion is rejected.

In Rust, this corresponds to lifetime subtyping: `'long: 'short` means
`'long` outlives `'short`, and a `&'long T` can be coerced to `&'short T`.

The reverse — widening a borrow to a longer-lived region — is never valid
because it would allow the borrow to outlive guarantees it was created with.

#### Diagnostics with Provenance

Every diagnostic (`Diag`) carries two event indices:

- `cause_event`: the event that *introduced* the bad state (e.g. where the
  borrow was created, where the variable was declared)
- `detect_event`: the event where the checker *detected* the violation

When these differ, the compiler front-end can emit a two-location error
message, which is far more useful to the programmer than a single-location
error:

```
error: cannot move `src` — it is borrowed
  --> file.lang:8:5
   |
6  |     let r = &src;        // borrow introduced here  [cause_event]
   |             -
7  |     ...
8  |     consume(src);        // move attempted here     [detect_event]
   |     ^^^^^^^^^^^^
```

This is exactly how Rust's compiler formats borrow errors. The provenance
information in the checker makes this straightforward to implement.

#### String Diagrams

The renderer (`diagram.c`) uses an ASCII notation inspired by *string
diagrams* from category theory and process calculus. In string diagrams,
wires represent values flowing through time (top to bottom), and nodes
(boxes) represent operations that transform wires.

The notation used here:

```
[name           ] ───owns──►  [name]         alive ownership wire
[name           ] ╌╌╌╌ moved ╌╌╌╌╌╌          dead wire (moved out)
[name           ] ✗  dropped                 dead wire (dropped)
[name           ] [partial: N moved]         partial-move wire

[ref            ] ·····&T·····►  [tgt]       shared borrow wire
[ref            ] ═════&mut══►  [tgt]        mutable borrow wire
[ref            ] - - -&mut(reserved)-► [tgt]  two-phase reserved
[ref            ] ~~✗~~~~~~~~~~►  [tgt]      DANGLING  broken wire

▣File  ▣Heap  ▣Sock  ▣Lock       resource badges on ownership wires
'region_name                     lifetime region tag on borrow wire
[N..M)                           slice range tag on borrow wire
NLL-end:#N                       NLL last-use annotation
```

A "broken wire" (`~~✗~~`) is the visual signature of a safety violation: a
wire that was supposed to carry a value has been severed.

The string diagram metaphor makes the checker's output pedagogically useful:
you can literally see the flow of ownership and the points where it breaks,
rather than reading abstract error descriptions.



### API Reference

#### Lifecycle

```c
void bc_init(BC *bc);
```
Initialise a zeroed BC handle. Always call this before any other function.
The BC must be heap-allocated (it is large).

#### Scopes

```c
void bc_scope_enter(BC *bc);
void bc_scope_exit (BC *bc);
```
Enter and exit a lexical scope. `bc_scope_exit` automatically:
- verifies all defers for this scope are satisfied
- releases all borrows created in this scope
- drops all variables in this scope (reverse declaration order)
- detects leaked resources

#### Lifetime Regions

```c
int  bc_region_begin        (BC *bc, const char *name);
void bc_region_end          (BC *bc, const char *name);
void bc_region_outlives     (BC *bc, const char *longer, const char *shorter);
void bc_borrow_in_region    (BC *bc, const char *ref, const char *target,
                             const char *region);
void bc_borrow_mut_in_region(BC *bc, const char *ref, const char *target,
                             const char *region);
void bc_coerce_region       (BC *bc, const char *ref, const char *new_region);
```

#### Variables

```c
void bc_declare          (BC *bc, const char *name, int is_mut);
void bc_declare_copy     (BC *bc, const char *name);
void bc_declare_interior_mut(BC *bc, const char *name);
void bc_assign           (BC *bc, const char *name);
void bc_move             (BC *bc, const char *dst, const char *src);
void bc_copy             (BC *bc, const char *dst, const char *src);
void bc_field_move       (BC *bc, const char *dst, const char *src,
                          const char *field);
void bc_drop             (BC *bc, const char *name);
void bc_use              (BC *bc, const char *name);        /* read */
void bc_use_write        (BC *bc, const char *name);        /* write */
```

`is_mut` in `bc_declare`: pass `1` if the variable is declared mutable
(`let mut x`), `0` otherwise. Immutable variables cannot be assigned to or
borrowed mutably.

#### Borrows

```c
void bc_borrow           (BC *bc, const char *ref, const char *target);
void bc_borrow_mut       (BC *bc, const char *ref, const char *target);
void bc_borrow_slice     (BC *bc, const char *ref, const char *target,
                          int lo, int hi);
void bc_borrow_mut_slice (BC *bc, const char *ref, const char *target,
                          int lo, int hi);
void bc_two_phase_reserve(BC *bc, const char *ref, const char *target);
void bc_two_phase_activate(BC *bc, const char *ref);
void bc_reborrow         (BC *bc, const char *new_ref, const char *src_ref);
void bc_release          (BC *bc, const char *ref);
void bc_last_use         (BC *bc, const char *ref);         /* NLL end */
```

#### Resources

```c
void bc_resource_acquire (BC *bc, const char *name, ResourceKind kind);
void bc_resource_release (BC *bc, const char *name);
```

`ResourceKind`: `RK_PLAIN`, `RK_HEAP`, `RK_FILE`, `RK_SOCKET`, `RK_LOCK`,
`RK_CUSTOM`.

#### Defer and Linear Types

```c
void bc_defer           (BC *bc, const char *name);
void bc_assert_consumed (BC *bc, const char *name);
```

`bc_assert_consumed` verifies that `name` is in state `VS_MOVED` or
`VS_DROPPED` — useful for enforcing that a value was consumed (submitted,
acknowledged, logged) rather than silently dropped.

#### Rendering

```c
DiagOpts diag_default_opts(void);
void diag_render_all    (const BC *bc, const DiagOpts *opts);
void diag_render_event  (const BC *bc, int event_idx, const DiagOpts *opts);
void diag_render_summary(const BC *bc, const DiagOpts *opts);
```

`DiagOpts` fields: `colour`, `show_resources`, `show_regions`,
`show_generations`, `show_scope_depth`, `show_provenance`, `compact`.



### Error Catalogue

| Error | Triggered by | Meaning |
|-------|--------------|---------|
| use after move | `bc_use`, `bc_use_write`, `bc_move` | Variable was moved out; source name is dead |
| use after free | `bc_use`, `bc_use_write` | Variable was explicitly dropped |
| double free | `bc_drop`, `bc_resource_release` | Drop or release called twice on same name |
| dangling borrow | `bc_drop`, `bc_scope_exit`, `bc_region_end` | Target dropped while borrow still live |
| use of dangling borrow | `bc_use`, `bc_use_write` | Borrow is in `BS_DANGLING` state |
| use of released borrow | `bc_use`, `bc_use_write` | Borrow was already released (includes NLL end) |
| borrow conflict | `bc_borrow`, `bc_borrow_mut` | Aliasing XOR mutation rule violated |
| write through &T | `bc_use_write` | Mutation attempted through a shared borrow |
| cannot move (borrowed) | `bc_move` | Target has active borrows; move would dangle them |
| cannot assign (immutable) | `bc_assign` | Variable declared without `is_mut` |
| cannot assign (borrowed) | `bc_assign` | Target has active borrows |
| resource leaked | `bc_scope_exit` | Resource acquired but not released before scope exits |
| double-release | `bc_resource_release` | Release called twice |
| defer unsatisfied | `bc_scope_exit` | `bc_defer` registered but release not called |
| field already moved | `bc_field_move` | Same field moved out twice |
| use of partially-moved | `bc_use`, `bc_move` | Whole-struct use after field move |
| slice conflict | `bc_borrow_slice`, `bc_borrow_mut_slice` | Overlapping slice borrows |
| region coercion failed | `bc_coerce_region` | Source region does not outlive target region |
| borrow outlives region | `bc_region_end`, `bc_scope_exit` | Active borrow in a region that is closing |
| assert_consumed failed | `bc_assert_consumed` | Value still alive where language requires consumption |
| reborrow of non-active | `bc_reborrow` | Reborrow source is released or dangling |
| two-phase activate (conflict) | `bc_two_phase_activate` | Active borrows exist when activating reserved &mut |



### Limitations and What Sits Above This Layer

This checker is a complete implementation of ownership and borrowing semantics
but it deliberately leaves several concerns to layers above it.

*Type checking.* The checker works on names and operations. It knows that
`x` is being moved but not what type `x` has. Whether a given type implements
`Copy`, `Drop`, or has interior mutability is determined by the type checker,
which then calls the appropriate `bc_*` function. A compiler must run type
inference and checking *before* driving the borrow checker.

*Variance in type parameters.* Rust's type system tracks covariance and
contravariance in generic parameters (e.g. function arguments are
contravariant in their lifetime parameters). This requires a full type-level
analysis that is above this checker's scope. The checker's region coercion
handles the borrow-level consequence of variance but not the type-parameter
level.

*Trait object lifetimes.* `dyn Trait + 'a` lifetime bounds require
unification across all possible implementations, which belongs in a trait
solver above this layer.

*Cross-function lifetime inference.* The checker models one function body
at a time. Lifetime relationships between caller and callee (Rust's lifetime
elision rules, or explicit `'a` annotations in function signatures) must be
resolved by the compiler before the checker is called. Concretely: when a
function call is modelled, the compiler opens a region at the call site,
models the borrows the callee takes, and closes the region when the call
returns.

*Alias analysis for raw pointers.* If the language allows raw (unsafe)
pointers, those escape the borrow checker entirely. The checker can model
the point where a raw pointer is created (as a move-out of an owned value)
but cannot track what happens to it thereafter. Safety for raw pointer
operations is the programmer's (or unsafe block reviewer's) responsibility.

*Numeric range inference for slice borrows.* The slice conflict check is
exact when bounds are compile-time constants. For runtime bounds the checker
can only be called with conservative (possibly overlapping) approximations,
which may reject safe programs. A more precise analysis would require an
integer interval domain, which belongs in a separate static analysis pass
that feeds its conclusions to the checker.

*Concurrency.* The checker proves aliasing XOR mutation for values owned
by a single thread. Cross-thread aliasing (as mediated by `Arc<Mutex<T>>`
in Rust, or channel passing) requires a separate analysis. The `RK_LOCK`
resource kind makes lock acquisition and release visible to the checker, but
proving absence of deadlock or proving correct critical section structure
requires reasoning that this checker does not perform.

In short: this checker sits at the *ownership and borrowing* layer of a
language's safety stack. A complete safe language would also need a type
checker, a trait solver, and (for concurrency) a thread-safety analysis.
Those layers can feed this one: they determine *what operation* is happening;
this checker proves that the *sequence of operations* is safe.
