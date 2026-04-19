
## Concurrency

Concurrency is the property of a system in which multiple computations are in progress at the same
time--overlapping in their execution, even if not literally simultaneous. It is one of the most
pervasive and consequential systemic properties in computing, appearing from the deepest layers of
hardware to the highest levels of distributed software. A CPU pipeline executes several instructions
in overlapping stages; an operating system interleaves the execution of dozens of processes; a web
server handles thousands of simultaneous requests; a distributed database coordinates updates across
nodes on different continents. In every case, the underlying challenge is the same: how do we reason
about and control systems where the order of events is not fully determined in advance?

Concurrency is often confused with *parallelism*, but the two are distinct. Parallelism is a
*hardware property*--multiple operations executing at the exact same instant on separate processors.
Concurrency is a *structural property* of a program or system--the possibility of interleaving.
A single-core machine can run concurrent programs, switching rapidly between tasks; a multi-core
machine can run parallel programs. Concurrency is about *dealing with* many things at once;
parallelism is about *doing* many things at once. The distinction matters because concurrency
introduces coordination problems that parallelism alone does not solve.


### Why Concurrency Matters

The need for concurrency is driven by several forces that are now inescapable in practice.

* *Hiding latency:* Waiting for I/O--disk reads, network responses, user input--is vastly more
  common than computation in most real-world systems. Concurrency allows a system to perform
  useful work while blocked on a slow resource, rather than sitting idle. This is the primary
  reason event loops, async/await, and non-blocking I/O have become dominant patterns in
  server-side programming.

* *Hardware reality:* Clock speeds stopped scaling around 2004. Since then, the industry has
  responded with more cores, more pipelines, more memory channels. To extract performance from
  modern hardware, software must expose and exploit concurrency.

* *Responsiveness:* User-facing applications must remain responsive even while performing
  long-running operations in the background. A UI that freezes during a file download is a
  concurrency failure.

* *Distribution:* Any system that spans more than one machine is inherently concurrent. Nodes
  act independently, messages arrive in unpredictable orders, and partitions can occur. Designing
  for distributed systems means designing for concurrency at a fundamental level.


### Models of Concurrency

Several different models have been developed to express and reason about concurrent computation.
Each makes different trade-offs between expressiveness, safety, and performance.


#### Threads and Shared Memory

The most widely used model. Multiple threads of execution share a common address space, and
coordinate through *locks*, *mutexes*, *semaphores*, and *condition variables*. This model maps
closely to hardware and gives fine-grained control, but places the full burden of correctness on
the programmer. Race conditions, deadlocks, and livelocks are the characteristic failure modes.

* *Race condition:* Two threads read and write a shared variable without synchronisation; the
  result depends on which runs first, producing non-deterministic, often incorrect outcomes.

* *Deadlock:* Two or more threads each hold a lock the other needs, waiting forever.

* *Livelock:* Threads keep responding to each other's actions without making progress, analogous
  to two people stepping aside for each other in a corridor and both stepping in the same direction.


#### Event Loops and Asynchronous I/O

A single-threaded model where a central loop dispatches callbacks or resumes coroutines as
events (I/O completions, timers, messages) arrive. Node.js, Python's asyncio, and many GUI
frameworks use this model. It avoids the complexity of thread synchronisation at the cost of
an execution model that can be difficult to reason about when control flow is fragmented
across many callbacks.

* *async/await:* A syntactic layer over coroutines that makes asynchronous code read more like
  sequential code. The `await` keyword marks suspension points where the event loop may switch
  to another task.


#### Message Passing

Processes (or actors) share no state; they communicate exclusively by sending messages to each
other. Erlang, Elixir, and Go (via goroutines and channels) use this model. Because there is
no shared mutable state, entire classes of synchronisation errors are eliminated. The Erlang
runtime, for example, spawns millions of lightweight processes, each isolated, and has used
this model to achieve extraordinary fault tolerance in telecommunications systems.

* *Actor model:* Each actor has a private state and a mailbox. It processes messages one at a
  time, potentially updating its state and sending further messages. Popularised by Erlang;
  also implemented in Akka (JVM) and Pony.

* *Communicating Sequential Processes (CSP):* A formal model where processes communicate
  through synchronous channels. Go's channels are inspired by CSP.


#### Software Transactional Memory (STM)

Shared state is accessed inside *transactions*: atomic, isolated blocks that either commit
fully or are retried on conflict--analogous to database transactions. Haskell's STM is the
most mature implementation. STM avoids lock-based programming but introduces its own
trade-offs around performance and the constraint that transactions must be free of side effects.


### Synchronisation Primitives

When shared state cannot be avoided, several primitives are used to protect it.

* *Mutex (mutual exclusion lock):* Ensures only one thread accesses a critical section at a time.
  Coarse locking is simple but can serialise work that could proceed in parallel; fine-grained
  locking improves parallelism but increases deadlock risk.

* *Semaphore:* A generalisation of a mutex, allowing up to $n$ concurrent accesses. Useful for
  rate limiting or resource pooling.

* *Read-write lock:* Allows many concurrent readers or one exclusive writer, improving throughput
  when reads are far more common than writes.

* *Atomic operations:* Hardware-supported compare-and-swap (CAS) and fetch-and-add instructions
  allow lock-free algorithms that operate correctly without holding a lock. Used in high-performance
  queues, counters, and memory allocators.

* *Barriers and fences:* Control the ordering of memory operations as seen by different CPU cores,
  preventing reordering by the compiler or hardware that could violate correctness assumptions.


### Concurrency and Correctness

Concurrency is one of the primary enemies of correctness. The *sequential consistency* model--
where the result of any execution appears as if all operations were executed in some sequential
order--is the intuitive programmer's model, but hardware and compilers do not guarantee it by
default for performance reasons. Weaker *memory models* (as specified by C++11, Java, or the
x86 TSO model) allow reordering that can produce results impossible under sequential execution.

Formal approaches to concurrent correctness include:

* *Linearisability:* Each operation appears to take effect atomically at some point between
  its invocation and response. The standard correctness criterion for concurrent data structures.

* *Serializability:* In databases, the result of executing transactions concurrently is equivalent
  to some serial execution. Combined with durability, this forms the ACID properties.

* *Model checking:* Tools like TLA+ and SPIN exhaustively explore the state space of concurrent
  protocols to find violations, used to verify algorithms in distributed systems (e.g., Amazon
  uses TLA+ to verify internal protocols).

* *Type systems for concurrency:* Rust's ownership model statically prevents data races by
  ensuring mutable access to data is exclusive. Languages like Pony use *reference capabilities*
  to enforce safe concurrency at compile time.


### Concurrency in the Layers of a System

Concurrency is not confined to a single level; it is woven through every layer of a computer system.


#### Hardware

* *Instruction-level parallelism (ILP):* Modern CPUs execute multiple instructions simultaneously
  through pipelining, superscalar execution, and out-of-order execution. The hardware manages this
  concurrency invisibly, subject to data dependencies.

* *Cache coherence:* Multiple cores each have private caches. The coherence protocol (e.g., MESI)
  ensures that a write by one core is eventually visible to all others, making shared memory
  consistent despite physical replication.

* *DMA and I/O:* Direct Memory Access controllers transfer data between peripherals and memory
  concurrently with CPU execution.


#### Operating System

* *Processes and threads:* The OS time-slices the CPU among multiple processes, creating the
  illusion of simultaneous execution. Context switching saves and restores the complete CPU state.

* *Scheduling:* Policies (round-robin, priority, CFS) determine which thread runs next, affecting
  both performance and fairness. Real-time systems require schedulers with deterministic guarantees.

* *Interrupts:* Hardware events (keyboard input, network packets) interrupt the running program
  asynchronously. The OS must handle these with care to avoid corrupting state.


#### Application and Distributed Systems

* *Thread pools and work queues:* A fixed set of threads draws tasks from a shared queue, amortising
  thread creation cost and bounding resource usage.

* *Reactive and actor frameworks:* Akka, Vert.x, and similar frameworks structure entire applications
  around asynchronous message passing, scaling to millions of concurrent operations.

* *Consensus protocols:* Paxos, Raft, and Viewstamped Replication coordinate state across distributed
  nodes, providing a consistent view despite concurrent updates and node failures. These protocols
  are the foundation of distributed databases, coordination services (ZooKeeper, etcd), and replication.


### Concurrency and Related Systemic Concepts

Concurrency does not exist in isolation; it interacts deeply with several other systemic properties.

* *Latency:* Concurrency is the primary technique for hiding latency. By overlapping computation and
  waiting, systems remain responsive. The tension is that adding concurrency to hide latency also
  adds synchronisation overhead, which can itself become a source of latency.

* *Determinism:* Concurrency is the principal source of non-determinism in software. The same program
  with the same inputs may behave differently on different runs due to scheduling variation.
  Non-determinism makes testing and debugging fundamentally harder--bugs that occur only under
  specific interleavings may be almost impossible to reproduce.

* *State:* Shared mutable state is the root cause of most concurrency bugs. Functional and actor-based
  approaches respond to this by eliminating or isolating shared state. Managing state consistently
  and safely in the presence of concurrency is one of the deepest design challenges in systems programming.

* *Correctness:* Achieving correctness in a concurrent system requires reasoning about all possible
  interleavings, which grows combinatorially with the number of concurrent actors. Formal methods,
  type systems, and careful abstraction are the primary defences.

* *Fault tolerance:* In distributed systems, concurrency and fault tolerance are inseparable.
  Concurrent nodes fail independently; the system must continue despite partial failure, and
  protocols must tolerate messages being lost, reordered, or duplicated.

* *Security:* Race conditions in security-sensitive code (time-of-check to time-of-use, or TOCTOU,
  bugs) have been exploited to bypass access controls, escalate privileges, or corrupt state in
  ways that open vulnerabilities.


### The Hardest Problems

Some problems in concurrent systems have no clean general solution and remain active areas of
research and engineering.

* *The dining philosophers:* Dijkstra's classic illustration of deadlock and resource allocation.
  Five philosophers sit at a table; each needs two forks to eat but there are only five forks.
  Naive strategies lead to deadlock or starvation.

* *The ABA problem:* In lock-free programming, a thread reads value A, another changes it to B
  and back to A, and the first thread incorrectly concludes nothing has changed.

* *Priority inversion:* A high-priority thread is blocked waiting for a lock held by a low-priority
  thread, which is itself preempted by a medium-priority thread. The high-priority task is
  effectively run at the lowest priority. This bug caused the Mars Pathfinder spacecraft to reset
  repeatedly in 1997.

* *CAP theorem:* In a distributed system subject to network partitions, it is impossible to
  simultaneously guarantee both consistency and availability. This is one of the most important
  results in distributed systems, forcing explicit trade-off decisions in database and service design.

* *Thundering herd:* When many concurrent threads or processes are all waiting for the same event
  (a lock release, a connection becoming available), and they all wake up simultaneously, the
  resulting contention can saturate the system.


### Concurrency in AI and Machine Learning

AI and ML systems are increasingly defined by concurrency, both as a target to optimise and as
a source of complexity to manage.

* *Data parallelism:* Training is distributed across many GPU cores or machines, each processing
  a different batch of data. Gradient updates must be synchronised--either by a central parameter
  server or through all-reduce protocols (used by frameworks like Horovod and PyTorch DDP).

* *Pipeline parallelism:* Large models are split across multiple devices, with different layers
  executing concurrently on different stages of the same batch.

* *Inference servers:* Serving models at scale requires handling thousands of concurrent requests
  efficiently, typically with asynchronous batching and dynamic memory management for attention caches.

* *Non-determinism in training:* GPU operations are often non-deterministic for performance reasons
  (floating-point reductions in arbitrary order; atomic updates to shared memory). This makes
  reproducing a training run exactly very difficult, with implications for debugging and scientific
  rigour.

* *Data pipelines:* Preprocessing and augmentation run concurrently with training, typically in
  separate processes or threads, requiring careful coordination to avoid bottlenecks and stale data.

* *Reinforcement learning:* Asynchronous algorithms such as A3C run many agents simultaneously,
  each exploring the environment independently and sending gradients back to a shared model.
  The asynchrony improves throughput but introduces gradient staleness.

The growth of large-scale ML has made concurrent programming skills as important for AI engineers
as for systems programmers--and has made the correctness and reproducibility challenges of
concurrency newly visible in a field that once worked largely sequentially.


### Trade-offs and Design Principles

Concurrency is a powerful tool but not a free one. Every concurrency decision involves trade-offs.

* *Correctness vs. performance:* The most correct approach--a single global lock--is also the least
  parallel. Fine-grained locking and lock-free algorithms improve parallelism but are significantly
  harder to implement correctly and reason about.

* *Simplicity vs. scalability:* Sequential code is far easier to write, test, and debug. Concurrency
  should be introduced when a clear bottleneck demands it, not speculatively.

* *Consistency vs. availability:* In distributed systems, stronger consistency guarantees require
  coordination that reduces availability during failures. Weaker models (eventual consistency) trade
  predictability for resilience.

Some principles that guide concurrency design:

* *Minimise shared mutable state.* The less shared state there is, the fewer opportunities for
  races. Immutability and message passing are structural responses to this principle.

* *Prefer higher-level abstractions.* Thread pools, channels, futures, and actors encapsulate
  concurrency patterns that have been designed and tested by experts. Rolling bespoke lock-based
  code is the most error-prone approach.

* *Test with concurrency in mind.* Race conditions are not reliably triggered by standard test suites.
  Stress testing, fuzzing with thread scheduling perturbation, and model checking are needed.

* *Document concurrency assumptions.* Which invariants must hold across threads? Which data structures
  are thread-safe? Leaving these implicit is a reliable path to subtle, production-only bugs.

Concurrency is unavoidable in modern computing. From the hardware that executes instructions in
overlapping pipelines to the distributed services that coordinate work across continents, the
ability to make progress on multiple things at once is fundamental to building systems that are
fast, responsive, and useful. Its costs--non-determinism, synchronisation complexity, and
the possibility of subtle, hard-to-reproduce bugs--demand that it be approached with care,
with clear design intent, and with a willingness to reach for higher-level abstractions when
the lower-level ones become unmanageable.
