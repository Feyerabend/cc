
## Algebraic Effect Systems in C

A practical demonstration of algebraic effect systems implemented from scratch in C.
The core idea: *effects are values, handlers are interpreters*.



### What Are Algebraic Effects?

Most languages conflate _doing_ a side effect with _describing_ one.
An algebraic effect system separates the two:
- A *computation* yields an _effect description_ (a value) instead of performing the effect directly
- A *handler* intercepts that description and decides what to actually do

This gives you unprecedented control over side effects--you can swap handlers to mock IO,
reify nondeterminism into a list, run state transactionally, or backtrack on failure.

In a typed language it might look like:

```
fn read_line() -> String with IO         // describes IO, does nothing yet
fn parse(s: String) -> Int with Error    // can fail, but that's just a value
fn pick(xs: List<Int>) -> Int with Amb   // nondeterministic choice
```

The handler decides what `IO`, `Error`, and `Amb` mean. Swap the handler, change the semantics.



### Implementation Architecture

C has no built-in effect tracking, but we can encode the core machinery with three ingredients.

#### 1. Effect as a tagged union

```c
typedef struct Effect {
    EffectTag tag;              // what kind of effect
    union { ... } data;         // payload
    Continuation* continuation; // "what to do next"
} Effect;
```

A computation returns an `Effect` instead of performing the side effect.
`EFF_RETURN` signals normal completion; all other tags are suspended requests.

#### 2. Continuation

```c
typedef struct Continuation {
    ResumeFn resume;            // function pointer: (k, value) -> Effect
    void*    context;           // the computation's local state
    struct Continuation* parent;
} Continuation;
```

A continuation captures "the rest of the computation".
Resuming it with a value is equivalent to answering the effect request and continuing execution.

#### 3. Handler loop

```c
while (current.tag != EFF_RETURN) {
    switch (current.tag) {
        case EFF_STATE_GET:
            current = current.continuation->resume(k, &state);
            break;
        case EFF_STATE_PUT:
            state = current.data.put.value;
            current = current.continuation->resume(k, NULL);
            break;
        case EFF_ERROR:
            /* abort or recover */
    }
}
```

The handler is just a loop.
It interprets each effect request and resumes the continuation with whatever answer it chooses.
Different handlers give the same computation entirely different behaviour.



### Files


#### `effect.h` / `effect.c` — Core effect system

Defines the `Effect`, `Continuation`, and `EffectTag` types, plus constructors:

| Constructor | Effect |
|-------------|--------|
| `eff_return(val)` | Normal completion |
| `eff_get(k)` | Read current state |
| `eff_put(val, k)` | Write new state |
| `eff_error(msg)` | Raise an error |
| `eff_choose(choices, n, k)` | Nondeterministic choice |
| `eff_async(fn, arg, k)` | Yield to scheduler (cooperative multitasking) |

Two variants exist: `effect.h` (simple, keyless state) used by
`counter/`,
`amb/`,
`nondet/`,
`soduku/`,
`coop/`;
and `effects.h` (key-value state) used by
`log/`,
`trans/`,
`plog/`.



#### `counter.c` — State effects

Demonstrates `EFF_STATE_GET` and `EFF_STATE_PUT` with a simple counter.

*Key insight*: the computation never touches mutable memory directly.
It yields a `GET` or `PUT` request; the handler owns the actual state variable.

```
computation: GET -> PUT(state+1) -> GET -> return
handler:     provides state, applies writes, passes result back
```

Two handlers are shown:
- `handle_state` — straightforward stateful interpreter
- `handle_state_and_error` — composes state + error handling in one loop

Because handler and computation are decoupled, you can run the same computation
under a _logging_ handler, a _transactional_ handler, or a _mock_ handler in tests.



#### `trans.c` — Transactional state (STM)

Uses key-value `EFF_STATE_GET`/`EFF_STATE_PUT` effects (from `effects.h`)
to implement software transactional memory.

The `handle_stm` handler buffers all writes in a log. Nothing is committed until the
computation returns successfully. On `EFF_ERROR`, the entire log is discarded--atomicity
for free, just by changing the handler.

```
write "x"=10  ->  write "y"=20  ->  read "x"  ->  return 10
          [buffered]        [buffered]    [from log]    [commit all]
```



#### `amb.c` — Nondeterminism as backtracking

`EFF_NONDETERMINISM` lets a computation request a choice from a set of values.
The `handle_amb` handler explores all branches via an explicit stack (depth-first search).

*Demo*: finding Pythagorean triples by nondeterministically picking `a`, `b`, `c` from `{1..5}`
and failing on constraint violations. Backtracking is implicit--failed branches just don't push further frames.

```
pick a ∈ {1,2,3,4,5}
pick b ∈ {1,2,3,4,5}
pick c ∈ {1,2,3,4,5}
require a²+b²=c²   ->  EFF_ERROR  ->  handler silently backtracks
require a<b<c       ->  EFF_ERROR  ->  handler silently backtracks
return (a,b,c)      ->  print triple
```

The computation expresses _what_ to search; the handler decides _how_ (DFS, BFS, random, parallel).



#### `log.c` — Nondeterminism + transactional state combined

Combines `EFF_NONDETERMINISM` and `EFF_STATE_PUT`/`EFF_STATE_GET` in one handler.

Each branch of the nondeterministic search gets its own isolated transaction log.
On `EFF_ERROR` (constraint violation) the branch's writes are discarded--no explicit rollback needed.
On `EFF_RETURN` the branch's writes are printed as committed.

This is algebraic effects as a composition mechanism: two orthogonal
effect kinds handled by the same loop, no framework required.



#### `soduku.c` — Constraint solving via nondeterminism

Solves 4×4 Sudoku by placing one digit at a time. At each cell it yields an `EFF_NONDETERMINISM`
choice over `{1,2,3,4}`; the handler clones the continuation for each branch.
Invalid placements return `EFF_ERROR`, pruning the search tree automatically.

The solver contains zero backtracking code. All search logic lives in the handler.



#### `nondet/` — Context isolation

Shows that each branch of a nondeterministic search must receive its *own copy*
of the computation's context. The handler clones both the `Continuation` struct
and the application-specific context struct before resuming each branch,
so mutations in one branch don't bleed into siblings.

The computation makes two sequential choices (from `{1,2,3}` then `{10,20}`),
producing 6 paths total. Each path accumulates its own chain of choices independently.



#### `coop/` — Cooperative multitasking via `EFF_ASYNC`

`EFF_ASYNC` is a yield point: the computation suspends itself and hands control
back to the scheduler (handler). The handler advances the computation past the yield
and re-queues it behind any other tasks already waiting.

```
Task 0: Starting
Task 1: Starting          <-- tasks interleave at yield points
Task 2: Starting
Task 0: Resumed after yield
Task 1: Resumed after yield
Task 2: Resumed after yield
```

The key distinction from state or nondeterminism: `EFF_ASYNC` doesn't need an
answer from the handler — it's a pure yield. The continuation resumes with `NULL`.
Swapping `run_async` for a thread-pool or event-loop handler requires zero changes
to the task code.



#### `plog/` — Logic programming engine

A minuscle Prolog-style interpreter where the search procedure is itself an effect.
- The computation yields `EFF_NONDETERMINISM` to choose which knowledge-base clause to try
- Unification is performed inside the continuation
- Backtracking on unification failure is handled entirely by the `handle_logic` loop

The knowledge base, search strategy, and unification are cleanly separated--each
a different layer in the effect stack.



### Conclusion

The same computation:

```c
Effect eff = k.resume(&k, NULL);
```

behaves completely differently depending on which handler processes it:

| Handler        | Behaviour                                          |
|----------------|----------------------------------------------------|
| `handle_state` | Runs with mutable state                            |
| `handle_stm`   | Runs transactionally, commits or aborts atomically |
| `handle_amb`   | Explores all nondeterministic branches             |
| `handle_logic` | Performs logic search with backtracking            |
| `run_async`    | Cooperative scheduler - yields between tasks       |

No modification to the computation required. This is the power of effect handlers:
*the semantics of a computation are not fixed at definition time--they are supplied by the handler at call time*.



### Readings

- *Algebraic Effects for the Rest of Us* - Oleg Kiselyov
- *Handlers of Algebraic Effects* - Gordon Plotkin & Matija Pretnar (2009)
- Languages with native effect systems: *Koka*, *Effekt*, *OCaml 5* (effects), *Eff*



### Aspects

This repository also includes a small example of aspect-oriented programming in
[`./aspects/`](./aspects/).

Aspect-oriented programming addresses *cross-cutting concerns* such as logging,
security checks, or instrumentation by allowing behavior to be injected at specific
points in program execution. In a historical sense, it can be viewed as an early
attempt to modularise computational effects.

A rough historical trajectory of related ideas in programming language design is:
- 1990s: aspect-oriented programming  
- 2000s: monadic approaches to effect tracking  
- 2010s: algebraic effects and effect handlers  
- 2020s: structured and typed effect systems

In modern programming language research, *effect handlers* are often seen as a
more principled and compositional alternative to aspects. They provide a similar
mechanism for separating concerns, but with explicit semantics and stronger
support from the type system.
