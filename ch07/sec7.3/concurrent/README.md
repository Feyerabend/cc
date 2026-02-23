
## Concurrency

> [!NOTE]
> Also compare with low level constructs on [concurrency](.).

*Concurrency*, as a concept in computing, has evolved through a rich
interplay between hardware capabilities, theoretical breakthroughs,
and the development of programming languages. Its roots stretch back
to the earliest days of computing, yet its meaning and implementation
have changed profoundly over time. To understand concurrency in a
historical sense is to trace the gradual realisation that computers
can--and often must--do more than one thing at a time,
or at least appear to.

In the earliest digital computers of the 1940s and 1950s, programs
were executed sequentially, in a single stream of instructions.
These machines ran one task at a time, and control remained firmly
in the hands of the program's step-by-step execution. As computing
systems became more powerful and more users needed to share them, the idea
of *multiprogramming* began to emerge. This involved the system switching
between multiple programs, keeping them resident in memory and giving
each a slice of time on the CPU. This was not true concurrency in the
modern sense, but it was a foundational shift: the machine could now
maintain the illusion that multiple tasks were progressing
simultaneously.

By the 1960s, with the advent of *time-sharing systems*, this illusion
became more refined. Operating systems like Multics allowed multiple
users to interact with a central computer as if they had it to themselves.
This required the operating system to interleave computations carefully
and manage concurrent access to resources like memory and disk.
These early efforts brought forth the first serious efforts to formalise
concepts like processes, critical sections, and mutual exclusion.
Dijkstra, Hoare, and others developed theoretical models that became
central to understanding concurrency, such as semaphores and monitors.

The challenge at this stage was not just how to run concurrent processes,
but how to reason about them. Theoretical computer science developed a
rich body of work on process calculi (like CSP and π-calculus), synchronisation,
and deadlock avoidance. These abstractions had a major influence on both
operating system design and the emerging field of concurrent programming languages.

High-level language support for concurrency began to appear in the 1970s.
Languages like Concurrent Pascal and Modula-2 (by Niklaus Wirth) introduced
structured ways of managing concurrent processes, but they remained niche.
The Ada programming language, developed by the U.S. Department of Defense,
took a more ambitious step in the early 1980s by incorporating built-in
support for tasking, rendezvous (a form of synchronous message passing),
and protected types. These features brought concurrency to the forefront
as a language-level construct.

In the 1980s and 1990s, as personal computing expanded and multi-processor
systems became more common, concurrency began to shift from large mainframes
to the desktop and eventually the server room. Threads became the dominant
model, supported by libraries (like POSIX threads) and gradually incorporated
into languages such as Java and C#. Java, in particular, made multithreading
a first-class citizen with its Thread class and synchronisation primitives,
although it inherited many of the complexities and pitfalls of low-level
thread programming.

By the 2000s, the rise of multi-core processors made concurrent programming
not just an option but a necessity. Languages like Erlang, which had long
championed lightweight, message-passing processes for telecom systems,
gained new attention. Erlang's actor model, where processes communicate only
through message passing and do not share state, offered a radical
and safer alternative to shared-memory concurrency.

The actor model also inspired newer languages and frameworks. Scala, with
its Akka library, became popular in distributed system development. Functional
languages such as Haskell began to offer advanced concurrency models like software
transactional memory, which allowed for composable, declarative management
of state changes in a concurrent context.

In the past two decades, the programming world has seen a shift toward more
abstract and safer concurrency models. Go, released by Google in 2009, made
concurrency a language design feature through goroutines and channels,
reflecting a philosophy of "don't communicate by sharing memory; share memory
by communicating." Rust, with its strict ownership model, approaches
concurrency from a safety-first perspective, catching many concurrency errors
at compile time that would otherwise lead to runtime crashes or data races.

Today, concurrency is deeply embedded in every layer of computing, from web
servers handling millions of connections simultaneously, to GPUs executing
thousands of threads, to reactive user interfaces responding to human actions in
real time. High-level language development continues to evolve to meet the
challenge: asynchronous programming with promises and async/await syntax has
become standard in JavaScript, Python, and C#, making event-driven concurrency
easier to write and understand.

Yet despite these developments, concurrency remains one of the hardest areas
of programming. Its difficulty lies not just in syntax, but in reasoning:
understanding how independent flows of execution interact, how to prevent subtle
timing bugs, and how to maintain consistency without sacrificing performance.
As such, the history of concurrency is not only a story of languages and hardware,
but of an evolving attempt to make the invisible world of simultaneous
computation intelligible and manageable to human beings.



### How do we let independent things cooperate without chaos?

So, when multiple processes run at the same time, they face a problem that doesn't
exist in sequential programming: they must share resources without interfering
with each other. A bank account updated by two transactions simultaneously,
a printer accessed by multiple programs, memory read and written by different
threads—these situations create fundamental challenges.

The difficulty is that parallelism breaks our comfortable assumption that one thing
happens, then another. Instead, many things happen at once, and their interactions
create possibilities we must carefully control. Without coordination, we get chaos:
corrupted data, lost updates, deadlocks where everyone waits forever.

The concepts below represent our toolkit for managing this chaos. Some describe the
problems we face, others the mechanisms we use to solve them, and still others provide
formal models to reason about parallel systems altogether.


#### Atomicity

*Making complex operations appear instantaneous*

Some operations need to happen "all at once" from the perspective of other processes.
Reading and updating a bank balance must be atomic—no one should see a half-updated value.
Atomicity is the property that an operation either completes entirely or not at all,
with no visible intermediate states.


#### Race Conditions

*When timing determines correctness*

A race condition occurs when the outcome depends on the unpredictable timing of events.
Two threads reading a counter, incrementing it, and writing it back might both read "5",
both compute "6", and both write "6"—losing an increment. The result "races" on which
thread happens to go first.


#### Mutual Exclusion (Mutex)

*One at a time, please*

A mutex ensures only one process can access a resource at a time. It's like a bathroom
lock: whoever holds it has exclusive access, everyone else must wait. This prevents race
conditions but introduces the risk of deadlock if locks are acquired in conflicting orders.


#### Semaphores

*Counting permissions*

A semaphore is a generalisation of a mutex that allows N processes to access a resource
simultaneously. It maintains a count: taking the semaphore decrements the count, releasing
increments it. When the count reaches zero, processes must wait. Useful for limiting
concurrent access to limited resources.


#### Producer-Consumer

*Coordinating different roles*

A classic pattern where some processes produce data and others consume it, typically through
a shared buffer. Producers must wait when the buffer is full; consumers must wait when it's
empty. This pattern appears everywhere: web servers producing requests for worker threads
to consume, data pipelines, event processing.


#### Reader-Writer Locks

*Different access, different rules*

Multiple readers can safely access data simultaneously, but writers need exclusive access.
Reader-writer locks optimize for this: any number of readers allowed together, but writers
get exclusive access. This improves concurrency when reads vastly outnumber writes.


#### Dining Philosophers

*Deadlock made concrete*

Five philosophers sit at a round table with five forks. Each needs two forks to eat.
If all grab their left fork simultaneously, all will wait forever for their right
fork—deadlock. This problem elegantly illustrates how resource contention and circular
waiting create deadlock, and how difficult it can be to avoid.


#### Communicating Sequential Processes (CSP)

*Coordination through channels*

Instead of sharing memory, processes communicate by sending messages through channels.
A process that wants to send must wait for a receiver, and vice versa. This
synchronization-through-communication often makes parallel programs easier to reason
about than shared-memory approaches.


#### π-calculus

*A language for parallel processes*

The π-calculus provides a mathematical foundation for describing concurrent systems.
It treats communication channels as first-class values that can be passed around,
created, and destroyed. This allows formal reasoning about parallelism, protocol
verification, and proving properties of concurrent systems.

