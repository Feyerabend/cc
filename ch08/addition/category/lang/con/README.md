
## Category Theory Concepts Applied to Concurrency in Python

This repository contains a series of Python examples that progressively explore
category theory concepts (functors, natural transformations, applicatives, monads,
and free monads) and their practical applications to concurrency and asynchronous
programming. Each file builds on the previous ones, demonstrating how these abstract
ideas can structure concurrent code in a composable, predictable way. The examples
use threading for simplicity, but the principles extend to real-world async
frameworks like asyncio or concurrent.futures.


### 01. Functors for Independent Transformations

*`cat_con.py`*

In this initial example, we introduce the concept of a *Functor* in the context of
asynchronous computations. The `Async` class represents a computation that produces
a value of type `A` eventually, acting as a container for concurrency. We implement
`fmap` (functor map), which lifts pure functions to operate on these async values
while preserving composition: `fmap(g ∘ f) = fmap(g) ∘ fmap(f)`. This allows transforming
results of concurrent tasks without blocking or altering their execution model.

The demo shows creating concurrent tasks, applying chained transformations (like squaring
and adding), and verifying functor laws. It also demonstrates running multiple independent
functor applications in parallel using threads, highlighting how functors enable independent
value transformations in concurrent settings. This sets the foundation for handling
concurrency without deep entanglement, making code more modular and testable.


### 02. Natural Transformations for Execution Strategy Switching

*`cat_natural_con.py`*

Building on functors, this file explores *Natural Transformations*—morphisms
between functors that preserve structure. We define multiple functor types:
`Sync` (immediate execution), `Async` (threaded), `Lazy` (deferred), and `Parallel`
(concurrent batch). Natural transformations like `sync_to_async` or `sync_to_lazy`
convert between these while satisfying the naturality law: transforming then
mapping equals mapping then transforming.

The demonstrations verify this law, showcase switching execution strategies
(e.g., from sync to async for I/O-bound tasks), and transform sequential lists
to parallel execution for performance gains. A real-world pipeline example
processes user data with different strategies, showing how natural transformations
enable flexible optimization—such as parallelizing independent fetches—without
rewriting core logic. This bridges the gap between different concurrency models
in a type-safe, composable manner.


### 3. Applicative Functors for Parallel Composition

*`applicative_functors.py`*

Extending functors, *Applicative Functors* add the ability to compose independent
computations in parallel. We implement `pure` (to lift values) and `ap` (to apply
wrapped functions), enabling operations like `map2` and `map3` for combining results
with binary/ternary functions. The key insight is parallelism: in `ParAsync`, `ap`
runs computations concurrently via threads, unlike the sequential `SeqAsync` variant
for comparison.

Demos illustrate parallel vs. sequential execution (e.g., fetching user data and posts
independently), verify applicative laws (identity, homomorphism), and show real-world
uses like parallel form validation or traffic light sensor readings. We contrast applicatives
with monads: use applicatives for independent operations (parallelizable) and monads
for dependent ones (sequential). This highlights applicatives' role in the hierarchy--between
functors (simple transforms) and monads (sequencing)--for efficient concurrent composition.


### 4. Monads for Dependent Sequencing

*`cat_monads_con.py`*

Advancing to *Monads*, this example adds `unit` (to lift values) and `bind` (for sequencing)
to the `Async` functor, enabling dependent concurrent operations where each step relies on
the previous result. Monad laws (left/right identity, associativity) are verified to ensure
predictable composition.

The file demonstrates sequential pipelines (e.g., fetch user → fetch posts → count words),
comparing parallel independent tasks with monadic dependent ones. It also shows error handling
in chains, like clamping negative values. Overall, monads shine for structuring async workflows
with dependencies, complementing functors (independent transforms) and applicatives (parallel
independents) by providing a way to sequence effects in concurrency.


### 5. Free Monads for Decoupled Description and Execution

*`free_monads_concurrency.py`*

Culminating the series, *Free Monads* separate program *description* (as an AST of operations)
from *execution* (via interpreters). We define a DSL for file ops (`ReadFile`, `WriteFile`, etc.)
as a functor, build `Free` as the free monad over it, and use `bind` for composition. Programs
like backups or ETL pipelines are pure data structures, executable by different interpreters:
synchronous, asynchronous (threaded), mock (for testing), or optimising (parallelising independents).

Demos show running the same program with various interpreters, composing complex workflows, and
performance comparisons. A real-world ETL example underscores decoupling: test with mocks, deploy
with async. Free monads enable ultimate flexibility--analyse/optimise ASTs, swap strategies--tying
together prior concepts for production-grade concurrent systems.

