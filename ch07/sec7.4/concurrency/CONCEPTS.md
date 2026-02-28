
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
