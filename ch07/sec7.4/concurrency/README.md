
### Concurrency & Threading

> [!NOTE]
> Also compare with [concurrent](./../../sec7.3/concurrent/)
> programming lanuages constructs.

| Mechanism | Description | Use Cases | Related Pattern(s) |
|-----------|-------------|-----------|--------------------|
| [Re-entrant](./reentrant/) | Function safe to be re-entered concurrently | Multithreading, interrupt-safe routines | Thread-safe design, Stateless design |
| [Context Switch](./context/) | Save/restore execution context between tasks | Thread scheduling, green threads, RTOS | Scheduler design |
| [Memory Barrier](./barrier/) | Prevent CPU from reordering memory operations | Lock-free concurrency, shared memory | Happens-before relations |

[Threads](./THREADS.md) are independent execution units within a process, sharing heap/global memory while maintaining
their own program counter, stack, and registers. They enable fine-grained multitasking, serving as the foundation for
concurrency mechanisms like re-entrant functions, context switching, and memory barriers. Managed by the OS (kernel threads)
or runtime (green threads), kernel threads offer true parallelism with higher overhead, while green threads (e.g., Go’s Goroutines)
prioritize lightweight, user-space scheduling for scalable I/O workloads. Threads facilitate parallel computation (e.g., matrix
operations) and real-time systems but introduce challenges: race conditions require synchronization (mutexes, atomics), deadlocks
arise from improper locking, and excessive context switching degrades performance. Optimizations include thread pooling to limit
overhead, work-stealing schedulers for load balancing, and non-blocking algorithms for lock-free coordination. Their balance of
shared-memory efficiency and execution independence underpins modern concurrent systems.

A *re-entrant function* guarantees safety when interrupted and re-entered, such as by a signal handler or another thread, without
corrupting its state. This is achieved by avoiding static or global variables, relying instead on parameters or thread-local storage
for state preservation. For example, a recursive factorial function that uses stack-allocated variables is inherently re-entrant,
whereas a function modifying a global counter is not. Re-entrancy is critical in interrupt-driven systems (e.g., embedded firmware
handling hardware signals) and multithreaded libraries (e.g., OpenMP functions). These functions align with stateless design
principles, where each invocation is isolated, and thread-safe patterns, such as immutability or copy-on-write strategies.
Non-reentrant functions often require synchronisation wrappers (e.g., mutex guards) to safely operate in concurrent contexts.  

*Context switching* involves saving the CPU state (registers, program counter, stack pointer) of the current thread and restoring
another thread’s state to resume execution. This mechanism enables time-sharing of CPU resources across threads or tasks. In
preemptive multitasking, the OS scheduler forcibly interrupts threads after a time slice, ensuring fair resource allocation,
while cooperative multitasking (e.g., early Windows or coroutines) relies on threads yielding control voluntarily. Context
switches are expensive due to CPU cache invalidation and OS kernel involvement, making them a bottleneck in high-throughput
systems. Techniques to minimize switching include event-driven architectures (e.g., Node.js’s event loop) or user-space schedulers
(e.g., Go’s M:N threading model). Real-time operating systems (RTOS) prioritize deterministic context switching to meet strict
timing constraints, such as in automotive control systems.  

*Memory barriers* enforce ordering constraints on memory operations, preventing compilers or CPUs from reordering instructions in
ways that violate program correctness. Modern CPUs employ out-of-order execution and speculative optimizations, which can lead to
inconsistencies in concurrent code (e.g., a thread reading a stale value after another thread updates it). A write barrier ensures
all prior writes are visible to other threads, while a read barrier ensures subsequent reads occur after the barrier. These are
vital in lock-free algorithms (e.g., atomic queues), spinlock implementations, and when using low-level primitives like `volatile`
in C/C++. Memory barriers map to *happens-before* relationships in formal memory models (e.g., Java’s or C++’s), which define legal
instruction reorderings. Misuse can result in subtle bugs like torn reads or visibility issues, often detectable only through tools
like TSAN (ThreadSanitizer).  

These low-level mechanisms collectively enable higher-level concurrency abstractions. Threads provide the structural basis for
parallelism, re-entrant functions ensure modular safety, context switches enable multitasking, and memory barriers maintain
consistency in shared memory. Together, they underpin frameworks like actor systems (e.g., Akka), parallel pipelines (e.g., GPU
compute shaders), and asynchronous runtimes (e.g., Python’s asyncio). Mastery of these concepts is essential for building systems
that balance performance, correctness, and scalability in multi-core and distributed environments.

