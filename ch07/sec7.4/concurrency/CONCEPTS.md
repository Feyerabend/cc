
## Some Concepts ..

| Concept | Description | Scheduling Type | Context Switching | Memory Management | Overhead | Parallelism | Use Cases |
|---------|-------------|-----------------|-------------------|-------------------|----------|-------------|-----------|
| *Processes* | Independent execution units with their own address space, resources, and lifecycle. Managed by the OS. | Typically preemptive (OS decides when to switch). | Handled by the OS kernel (involuntary). | Isolated memory spaces (private to each process). | High (full context switch including memory mappings). | True parallelism on multicore systems. | Running multiple applications, isolation for security/stability (e.g., web browsers with tabs as processes). |
| *Threads* | Lightweight subunits within a process, sharing the same memory space. Also called kernel threads when OS-managed. | Preemptive (OS scheduler interrupts and switches). | Kernel-level (involuntary for preemptive threads). | Shared memory within the process. | Medium (switches registers, stack, but not full memory). | True parallelism on multicore (multiple threads can run simultaneously). | Concurrent tasks within an app, like UI and background work in software. |
| *Coroutines* (Cooperative Multitasking) | Programmer-controlled, lightweight functions that can pause and resume, yielding control voluntarily. | Cooperative (tasks yield explicitly). | User-level (voluntary, no kernel involvement). | Shared memory, but managed by the runtime. | Low (minimal state saving, no kernel calls). | Pseudo-concurrency (single thread, interleaved execution). | Async programming (e.g., in Python asyncio), event-driven systems where tasks are non-blocking. |
| *Tasks in Preemptive RTOS* | Similar to threads but in real-time operating systems for embedded devices; prioritised units of execution. | Preemptive (RTOS kernel interrupts based on priority). | Kernel-level (involuntary, priority-based). | Shared or protected memory depending on RTOS (often shared in embedded). | Medium (context switches optimised for real-time). | True parallelism if multicore support, but often single-core with strict timing. | Embedded systems requiring deterministic response (e.g., automotive, robotics, IoT devices). |

Additional related concepts:

- *Green Threads/User-Level Threads*: Like coroutines but thread-like;
  cooperative scheduling in user space (e.g., in some languages like Go's
  goroutines, which can be preemptive in newer versions).

- *Fibers*: Very lightweight, user-managed threads similar to coroutines,
  often used in Windows for cooperative multitasking.


These concepts overlap in concurrency models:
processes for isolation,
threads for shared-memory concurrency,
coroutines for efficient async,
and RTOS tasks for real-time guarantees.





### Historical Context

The evolution of these concurrency concepts reflects decades of computing history,
driven by changing hardware capabilities and programming needs.

*Early Computing (1950s-1960s)*: The first computers ran single programs sequentially.
The concept of *processes* emerged with early time-sharing systems like CTSS 
Compatible Time-Sharing System, 1961, and later Multics, which pioneered the idea of
multiple isolated programs sharing a single machine. Process isolation was critical
for security and stability in multi-user mainframe environments.

*The Thread Revolution (1970s-1980s)*: As applications grew more complex, developers
needed lighter-weight concurrency within programs. *Threads* emerged as a solution,
notably popularized by Unix System V in the 1980s and standardised with POSIX threads
(pthreads) in 1995. Threads allowed programmers to write concurrent code without the
heavy overhead of full process context switches, making responsive user interfaces
and server applications practical.

*Cooperative Multitasking's Long History*: *Coroutines* actually predate threads
conceptually--Melvin Conway described them in 1958, and they appeared in early
languages like Simula (1967). However, preemptive multitasking dominated for
decades because cooperative approaches required careful programming to avoid one
task monopolising the CPU. Coroutines experienced a renaissance in the 2000s-2010s
with the rise of asynchronous I/O programming (Node.js in 2009, Python's asyncio
in 2012), where their efficiency for handling thousands of concurrent I/O operations
became invaluable.

*Real-Time and Embedded Systems (1980s-present)*: *RTOS tasks* evolved from the
needs of embedded systems and industrial control, where deterministic timing is
critical. Early examples include VxWorks (1987) and later FreeRTOS (2003).
These systems prioritised predictability over throughput, using priority-based
preemptive scheduling to guarantee that critical tasks meet deadlines--essential
for applications from aircraft controls to medical devices.

*Modern Convergence (2000s-present)*: Today's landscape blends these approaches.
Languages like Go introduced *goroutines* (2009), user-level threads that combine
the efficiency of coroutines with preemptive scheduling. Rust's async/await
(stabilised 2019) brings zero-cost coroutines to systems programming. Meanwhile,
multicore processors have made true parallelism common, and even embedded systems
now often feature multiple cores, blurring the traditional distinctions between
these models.

The evolution reflects a tension between
control (cooperative),
fairness (preemptive),
efficiency (lightweight constructs), and
isolation (processes)--each era's dominant model addressing
the most pressing constraints of its time.

