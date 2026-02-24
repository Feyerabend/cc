
## Concurrency in Operating Systems

It is often helpful to illustrate key concepts by relating them to the familiar
behaviour of real operating systems. The ToyVM used in our exploration of
concurrency concepts ([sec7.3](./../../sec7.3/)) serves also as a simplified model
of mechanisms that exist within an operating system kernel. By examining this
simulation alongside the behavior of a real OS—specifically xv6--we can better
understand how abstract ideas such as process scheduling, context switching,
and resource management are implemented in practice. This comparison highlights
similarities and the deliberate simplifications made in the ToyVM in C,
offering clearer insight into how kernels coordinate concurrent execution.


### Comparison Between our Simulator and xv6 Kernel

The `toyvm.c` program is a lightweight, user-space simulator designed to illustrate
core operating system (OS) concurrency concepts like thread management, scheduling,
and synchronisation primitives. It runs cooperatively within a single real OS thread,
mimicking kernel behaviours without interacting with hardware. In contrast, xv6[^xv6]
is a simple, Unix-like teaching kernel developed at MIT, modeled after Unix Version 6.
It's a real, monolithic kernel that runs on hardware (originally x86, now primarily
RISC-V), providing a full OS environment with preemptive multitasking, hardware
interrupts, and system calls.

[^xv6]: xv6 is used in educational settings (e.g., MIT's 6.1810 course) to teach OS principles through a minimal but functional implementation.

Below, we'll compare the two across key aspects, highlighting similarities (both are
educational tools emphasising simplicity) and differences (toyvm's simulation vs.
xv6's hardware-backed execution). This draws from xv6's design as described in
its documentation and source code.

* https://github.com/mit-pdos/xv6-riscv
* https://pdos.csail.mit.edu/6.828/2025/xv6/book-riscv-rev5.pdf


#### 1. *Overall Architecture*

   - *toyvm*: A cooperative simulator running entirely in user space as a
     single-threaded C program. It emulates a "kernel" with data structures
     like Thread Control Blocks (TCBs), run queues, and resource managers
     (locks, semaphores, message queues). There's no privilege separation,
     no hardware access, and no real kernel mode—everything is simulated
     in one process. It's designed for readability, with a main loop acting
     as the scheduler. No file system, devices, or virtual memory hardware;
     globals and thread-local vars simulate shared/private state.

   - *xv6*: A monolithic kernel running in supervisor (privileged) mode on
     real hardware. It provides a complete OS with user/kernel space separation,
     handling traps (system calls, interrupts, exceptions) to switch modes.
     The kernel manages physical memory, devices (e.g., UART console, disk),
     and a file system. User programs run in unprivileged mode, invoking
     services via system calls (e.g., `fork`, `exec`, `read`). xv6 supports
     multiprocessing on multi-core systems with per-CPU structures.

   - *Similarities*: Both follow a traditional kernel structure with a central
     scheduler and data structures for managing execution units (threads in
     toyvm, processes in xv6). They emphasise teaching concepts like context
     switching and resource management.

   - *Differences*: toyvm is a non-preemptive simulation (no interrupts;
     threads yield cooperatively), while xv6 is a real, preemptive kernel
     with hardware support. toyvm lacks xv6's trap handling, page tables,
     and device drivers, making it far simpler (a few hundred lines vs.
     xv6's thousands).


#### 2. *Process/Thread Management*

   - *toyvm*: Uses "threads" as the basic unit, represented by a `Thread` struct
     (similar to a TCB or Linux's `task_struct`). Each thread has an ID, program
     counter (PC), stack, local variables, state (runnable, waiting, terminated),
     and a wait resource ID. Threads are created with a program (array of instructions)
     and run in a shared "kernel" environment. No real address spaces—memory is
     simulated via stacks and globals. Termination sets state to `TS_TERMINATED`.

   - *xv6*: Uses "processes" as the unit of isolation (no user-level threads;
     each process has one kernel thread). Each is a `struct proc` with PID, state
     (e.g., `RUNNABLE`, `SLEEPING`, `ZOMBIE`), page table, kernel stack, and trap
     frame. Processes are created via `fork` (copies parent) and loaded via `exec`
     (ELF files from disk). Each has its own virtual address space for isolation,
     with lazy allocation for heap growth (`sbrk`). Termination via `exit` releases
     resources, with parents reaping via `wait`.

   - *Similarities*: Both use structs to track execution state (e.g., PC/registers,
     run state) and support creation/termination. toyvm's threads mimic xv6's
     processes in managing saved contexts for suspension/resumption.

   - *Differences*: toyvm threads share a single address space (no isolation),
     while xv6 processes have hardware-enforced separate virtual memory. xv6 handles
     real system calls and forking; toyvm uses a simple `create_thread` with opcodes,
     more like a bytecode VM than a full process model.


#### 3. *Scheduling and Run Queue*

   - *toyvm*: Employs a round-robin scheduler in a main loop: dequeues a
     runnable thread from a FIFO run queue, executes one instruction
     (cooperative time-slice), and re-enqueues if still runnable. Context
     switching is simulated by saving/restoring PC and stack in the `Thread`
     struct. No preemption—threads block voluntarily (e.g., on locks).
     Deadlock detection checks if the run queue empties with waiting threads.

   - *xv6*: Uses a simple round-robin scheduler per CPU, scanning the process
     table for `RUNNABLE` processes. Preemptive via timer interrupts (forces
     `yield` to switch). Context switching via `swtch` (assembly) saves/restores
     registers on the kernel stack. Each CPU has a scheduler thread that picks
     the next process.

   - *Similarities*: Both use round-robin with a run queue (toyvm's explicit
     FIFO queue vs. xv6's process table scan). Context switching concepts
     align—saving state and resuming another entity. toyvm's main loop mirrors
     xv6's `scheduler` function.

   - *Differences*: toyvm is cooperative (one instruction per turn, no interrupts),
     while xv6 is preemptive (hardware timers enforce time slices). xv6 handles
     multi-core with per-CPU queues; toyvm simulates everything single-threaded.


#### 4. *Synchronisation Primitives*

   - *toyvm*: Supports mutex locks (with wait queues for blocking), semaphores
     (count-based, with waiters), and message queues (bounded buffers with receivers
     queue). Blocking moves threads to `TS_WAITING` and off the run queue; wakeup
     enqueues them back. Fast paths for acquisition; slow paths decrement PC to
     retry on wake. No spinlocks--everything is cooperative.

   - *xv6*: Provides spinlocks (atomic, busy-wait for short sections) and sleep
     locks (block/yield for longer waits). Synchronisation via `sleep`/`wakeup`
     on channels (e.g., for I/O or events), with locks preventing races/lost
     wakeups. No native semaphores (though exercises add them). Interrupts are
     disabled during critical sections.

   - *Similarities*: Both use wait queues for blocked entities (toyvm's `WaitQueue`
     vs. xv6's process table with channels). Wakeup mechanisms are analogous
     (enqueue runnable after signal). Locks ensure mutual exclusion, with hand-off to waiters.

   - *Differences*: toyvm's primitives are higher-level and simulated (e.g.,
     semaphores built-in, no hardware atomics), while xv6 relies on low-level
     spinlocks tied to interrupts and hardware (e.g., RISC-V atomic instructions).
     xv6 has no message queues (uses pipes for IPC); toyvm emphasises them
     for producer-consumer demos.


#### 5. *Message Passing and IPC*

   - *toyvm*: Explicit message queues (`MsgQueue`) for sending/receiving values,
     with direct handoff if receivers wait (rendezvous). Supports blocking on empty queues.

   - *xv6*: No explicit message passing. IPC via pipes (byte streams with buffering,
     synchronised by sleep/wakeup) or shared files. Processes communicate through
     system calls like `pipe`, `read`, `write`.

   - *Similarities*: Both handle producer-consumer patterns (toyvm demos it explicitly;
     xv6 via pipes).

   - *Differences*: toyvm's queues are a core primitive; xv6 treats IPC as file-like
     operations, integrated with its file system.


#### 6. *Other Features*

   - *Memory Management*: toyvm simulates stacks and variables (no paging);
     xv6 uses hardware page tables for virtual memory, lazy allocation, and protection.

   - *Instructions/Execution*: toyvm executes custom opcodes (e.g., `OP_LOCK_ACQUIRE`);
     xv6 runs native machine code with system calls trapping to kernel.

   - *Debugging/Demos*: toyvm includes built-in demos (mutex, producer-consumer,
     deadlock); xv6 focuses on Unix compatibility (shell, utilities).

   - *Scope and Complexity*: toyvm is ~1000 lines for concurrency simulation;
     xv6 is a full OS (~10k lines) with file system, networking stubs, and crash recovery.



### Conclusion

toyvm and xv6 are both teaching tools, but they serve different purposes:
toyvm simplifies concurrency concepts into a runnable simulator (ideal for
quick experiments without booting a VM), while xv6 provides a realistic,
bootable kernel for understanding hardware-software interactions. toyvm
illustrate abstract ideas like wait queues and cooperative scheduling but
lacks xv6's preemption, isolation, and hardware realism. If you're studying
OS basics, toyvm is a gentle intro; xv6 dives deeper into real-world
implementation. For hands-on, you can compile/run toyvm easily, while
xv6 requires QEMU emulation. You see the possible projects now?
