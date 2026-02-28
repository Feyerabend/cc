
### Computation Models

| Mechanism | Description | Use Cases | Related Pattern(s) |
|-----------|-------------|-----------|--------------------|
| Coroutine | Generalised subroutine with suspend/resume semantics | Generators, cooperative multitasking, simulations | Actor model, State Machine |

Coroutines are cooperative multitasking constructs where control is explicitly yielded
between different execution contexts, unlike threads (which are preemptively scheduled
by the OS).

Key characteristics:
- Suspendable & Resumable Execution: A coroutine can pause (yield) and later resume where it left off.
- Multiple Entry Points: Unlike functions (which have a single entry and exit), coroutines can yield
  control and later resume from the same point.
- State Retention: Coroutines maintain their execution state (stack, locals, instruction pointer)
  between suspensions.
- Cooperative Scheduling: They require explicit yielding, rather than being interrupted by an external
  scheduler.


Comparison with Related Concepts
|Feature	| Functions (Subroutines)	| Threads	| Coroutines|
|---------|-------------------------|---------|-----------|
|Execution	| Runs to completion	| Preemptive scheduling	| Cooperative yielding|
|Concurrency	| No	|Parallel (if multi-core)	|Single-threaded concurrency|
|State	| Lost after return	|OS-managed stack	|Preserved across yields|
|Overhead	| Low	|High (context switch)	|Low (no OS involvement)|


### Implementions

Coroutines can be implemented in different ways depending on the language and runtime support, with
two major categories: stackful and stackless coroutines. Stackful coroutines, like Goroutines in Go
and Kotlin coroutines, allocate a separate stack for each coroutine. This allows them to yield execution
from anywhere within nested calls, offering flexibility at the cost of higher memory overhead. Stackless
coroutines, such as Python generators and C++20 coroutines, do not use separate stacks. Instead, they
suspend and resume only at explicit points, which makes them more lightweight but limits where yielding
can occur.

Several languages offer their own coroutine implementations. Python provides generators using yield for
basic coroutine behavior and extends this with async/await (PEP 492) for asynchronous coroutines.
C++20 introduces low-level coroutines that are compiler-transformed into state machines, though they
require manual management of coroutine frames. Kotlin coroutines are built on suspendable functions
marked with the suspend keyword, and they are lightweight and integrated into structured concurrency
models. Go offers Goroutines, which use an M:N threading model where many coroutines are multiplexed
over a smaller number of OS threads, managed by the Go runtime scheduler. Lua provides coroutines
through its coroutine library, with explicit yield and resume semantics, commonly used for cooperative 
multitasking in game scripting.


### Uses

Coroutines are commonly used in situations that require concurrency without true parallelism. In
asynchronous I/O and networking, coroutines handle non-blocking network requests efficiently, such
as managing thousands of simultaneous connections in a web server; examples include Python’s asyncio
and JavaScript’s Promise with async/await. In game development, coroutines manage behaviors of game
entities like animations and AI state machines; Unity’s coroutines using C#’s IEnumerator and yield
return are a typical example. In data processing pipelines, coroutines enable lazy evaluation of
sequences, such as processing large files line by line; Python’s generators using yield are often
used for streaming data in this context. For cooperative multitasking in embedded systems, coroutines
provide lightweight task switching without needing a real-time operating system (RTOS), similar
to Arduino-style event loops. Finally, coroutines are useful for implementing concurrency patterns
such as producer-consumer problems and state machines, where each state can be modeled as a coroutine.

