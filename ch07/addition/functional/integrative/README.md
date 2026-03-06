
## 12. Functional Style as Concurrency Discipline

The patterns in this series are not academic exercises. Each one removes
a category of defect from concurrent programs -- by construction, not by
careful locking.

This section traces the concurrency implications of each pattern and shows
how they combine into a single principle: *a program composed entirely of
pure functions operating on immutable data needs no synchronisation*.



### The Problem: Shared Mutable State

A data race occurs when two threads access the same memory location, at
least one access is a write, and the accesses are not ordered by a
synchronisation operation. The consequence is undefined behaviour -- the
program may produce wrong results, crash, or appear to work while silently
corrupting data.

The fundamental equation is:

```
shared location + at least one write + concurrent access = data race
```

Eliminate any of the three terms and the race cannot occur.

- Eliminate *shared*: thread-local state. Every thread owns its data.
- Eliminate *at least one write*: immutability. Data is read-only after
  construction.
- Eliminate *concurrent access*: serialise. Use a mutex. But serialisation
  destroys the performance benefit of concurrency.

Functional programming targets the second term -- immutability -- and as a
consequence eliminates the need for the third.



### Pattern by Pattern: The Concurrency Contribution

#### 1. First-Class Functions

A function passed as a value carries no shared state by itself. Passing
behaviour instead of data means that the two sides of the call are
decoupled -- the caller does not need to know what the function does to its
own resources; the callee does not need to know what the caller will do next.

Concurrency implication: functions as values enable work-stealing and
task-parallel execution without any shared mutable queue interface.

#### 2. Closures

A closure captures its surrounding environment at the time of creation.

- *Closure over immutable value*: the captured variable cannot change.
  Multiple threads may call the closure simultaneously -- each reads the
  same fixed value. No synchronisation needed.

- *Closure over mutable shared state*: the captured variable may change
  while another thread is reading or writing it. This is a data race.

The rule is simple: closures are thread-safe if and only if their captured
state is immutable.

#### 3. Immutability

An immutable value is written exactly once -- at construction -- and then
read by any number of readers, in any order, with no synchronisation.

This is the most direct contribution of functional style to concurrency.
The C11 memory model guarantees that a value published through a proper
release store is visible to any subsequent acquire load on another thread.
Once that publication is done, the value is immutable; there are no more
stores; no further memory ordering is required.

In Python, frozen objects and `__slots__`-immutable nodes provide the same
guarantee: after `__init__` completes, the object's fields never change.

#### 4. Higher-Order Functions

`map(f, data)` applies `f` to each element of `data` and collects results.
If `f` is pure (no shared mutable state), then each application of `f` is
independent. The work is *embarrassingly parallel*: it can be distributed
across any number of threads or processes with no coordination.

A parallel `map` over a pure function requires one synchronisation point:
the final assembly of results. One barrier; zero internal locks.

#### 5. Function Composition

A composed pipeline `h = f ∘ g ∘ k` chains pure functions. Each function
reads its input and produces its output, touching nothing else. The pipeline
is a series of transformations with no shared state between stages.

Concurrency implication: multiple composed pipelines can run in parallel
because they share no state. The composition itself is the unit of work.

#### 6. Lazy Evaluation

A generator produces values on demand. It does not build intermediate
collections. Each yielded value flows to the consumer and is discarded.

In a pipeline of generators, values are never stored in shared buffers
between stages; each stage holds only the current element. This eliminates
the class of race conditions that arise from multiple readers and writers
on a shared ring buffer.

#### 7. Functors

`fmap(f, container)` transforms the *contents* of a container without
replacing or modifying the container structure. The original container is
unchanged; the result is a new container.

Concurrency implication: readers of the original container are unaffected
by the transformation. Old and new versions can be accessed simultaneously.

#### 8. Monads

A monad sequences effects in a defined order. A monadic bind chain says:
"do this, then do that." The sequencing is explicit in the code.

In concurrent systems, explicit sequencing is more reliable than implicit
sequencing through lock ordering. When effects are explicit and chained --
rather than hidden in global state -- it is easier to reason about which
operations happen before which, and to parallelise independent chains.

#### 9. Referential Transparency

A referentially transparent function is one whose output depends only on
its input. It reads no global state; it writes no global state.

This is the precise property that makes concurrent execution safe. Two
calls to a referentially transparent function with the same input produce
the same output, regardless of which thread calls them or in what order.
There are no write-write conflicts (no writes to shared state) and no
read-write conflicts (no reads of shared state that might be modified
concurrently).

The compiler can also exploit this property: `ATTR_CONST` and `ATTR_PURE`
tell the optimiser that the function is referentially transparent, enabling
CSE, loop hoisting, and call elimination -- all safe because pure functions
have no side effects that must be preserved.

#### 10. Persistent Data Structures

A persistent data structure exposes every version for reading. Old versions
are never modified; new versions share the unchanged parts of the old.

Concurrency implication: any number of threads may read any version
simultaneously without any synchronisation. The only synchronisation needed
is for publishing a new version -- a single atomic store. No mutex, no
reader-writer lock.

This is the basis of MVCC (multi-version concurrency control) in databases,
and of RCU (read-copy-update) in the Linux kernel. The underlying structure
is always the same: immutable old versions; structural sharing; one atomic
pointer swap to publish the new version.



### The Full Pipeline

A program built from these patterns has the following shape:

```
[pure source] ---> [lazy transform] ---> [pure map] ---> [pure fold]
                         |
                 (each element independent)
                         |
              [thread 1] [thread 2] [thread 3]
                    \       |       /
                     [aggregate once]
```

- The source is pure: it produces values from its arguments only.
- Each transform is lazy: no intermediate allocation.
- Each map is a pure function: thread-safe by construction.
- Aggregation touches shared state once, at the end.

The only synchronisation in this pipeline is the final aggregation. The
ratio of synchronised work to total work approaches zero as the data grows.



### Memory Ordering and Functional Style

When a program is composed of pure functions operating on immutable data,
the memory ordering concerns that occupy much of a systems programming
textbook largely vanish.

Memory barriers exist to enforce ordering between a write on one thread
and a read on another. If a value is written once (immutability) and then
only read, the only ordering required is between the one write and all
subsequent reads -- a single publish operation. After that, no barriers
are needed because there are no more writes.

In C11 terms:

```c
/* Writer: construct the data, publish it atomically. */
node_t *data = build_data(args);          /* pure: no shared state touched */
atomic_store(&shared_ptr, data,           /* one release store */
             memory_order_release);

/* Reader: load once, then read freely. */
node_t *local = atomic_load(&shared_ptr, /* one acquire load */
                             memory_order_acquire);
process(local);                           /* pure: reads local only */
```

Two atomic operations for the lifetime of the shared data. The rest of the
program is barrier-free, because the rest of the program is pure.



### The Underlying Principle

Functional purity is not a programming style. It is a memory access pattern.
It says: this function reads its inputs and produces its output, touching
nothing else. That is what makes it safe to call concurrently.

Every pattern in this series is a tool for extending that property to larger
and more expressive programs:

- Closures: encapsulate state explicitly so it can be made immutable.
- Higher-order functions: factor out pure transformations from impure control.
- Composition: chain pure functions without shared intermediate state.
- Lazy evaluation: defer computation without shared buffers.
- Persistent structures: accumulate results without mutation.
- Monads: sequence effects without hiding them in global state.

The sum of these tools is a programming discipline in which concurrent
correctness follows from the structure of the code, not from the discipline
of the programmer. The program is not thread-safe because its author was
careful with locks. It is thread-safe because it has no shared mutable
state to lock.



*This concludes the series: from first-class functions as values, through
closures capturing environments, higher-order functions separating iteration
from transformation, composition chaining without shared state, lazy
evaluation deferring without buffering, functors and monads making structure
and effects explicit, referential transparency enabling equational reasoning
and compiler optimisation, persistent data structures sharing without
copying, cost models grounding abstraction in hardware reality -- and finally
here, the synthesis: functional style as the discipline that makes concurrent
programs correct by construction.*
