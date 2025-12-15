
## TinyMOS

TinyMOS is a lightweight operating system designed for resource-constrained devices
like the Pico. Below is a general overview of its key characteristics, focusing on
scheduling, multitasking, and priority mechanisms.


### 1. *Preemptive Scheduling*

   - *TinyMOS is preemptive*: It enforces a time slice (default 200ms in the demos)
     for each process, ensuring that no single process monopolises the CPU. After the
     time slice expires, the scheduler performs a context switch to another process,
     even if the current process hasn't yielded voluntarily.

   - The `run` method enforces this by tracking elapsed time (`time_slice_ms`) and
     switching processes if the time slice is exceeded, making it preemptive.


### 2. *Multitasking*

   - *Cooperative Multitasking*: TinyMOS supports cooperative multitasking through
     system calls like `Yield`, `Sleep`, and `WaitForMessage`. Processes can voluntarily
     yield control back to the scheduler, allowing other processes to run. This is
     evident in the `yield OS.yield_cpu()` calls in the example processes (e.g.,
     `counter_process`, `blinker_process`).

   - *Preemptive Multitasking*: In addition to cooperative multitasking, TinyMOS uses
     preemptive multitasking by enforcing time slices. If a process doesn't yield
     within its allocated time slice, the scheduler forcibly switches to the next
     process, ensuring fair CPU allocation.


### 3. *Priority-Based Scheduling*

   - *Priority Support*: TinyMOS supports priority-based scheduling, which can be
     enabled via `enable_priority_scheduling()`. Processes are assigned priorities
     (`LOW`, `NORMAL`, `HIGH`, `CRITICAL`), and the scheduler prioritises higher-priority
     processes when this mode is active.

   - *Priority Queues*: When priority scheduling is enabled, processes are organised
     into separate queues for each priority level (stored in `priority_queues`).
     The scheduler selects processes from the highest-priority queue first (e.g.,
     `CRITICAL` processes run before `HIGH`, `NORMAL`, or `LOW`).

   - *Default Scheduling*: Without priority scheduling, TinyMOS uses round-robin
     scheduling, where processes are executed in a first-in, first-out (FIFO) order
     from a single ready queue (`ready_queue`), ensuring equal CPU time for all processes.


### 4. *Process Management*

   - *Process States*: Processes can be in one of four states: `READY`, `RUNNING`,
     `BLOCKED`, or `TERMINATED`. This allows the OS to manage processes efficiently,
     moving them between queues based on their state.

   - *Process Control Block (PCB)*: Each process has a PCB that tracks its state,
     priority, CPU time, context switches, and messages. The PCB also stores the
     process's context (using Python generators), enabling context switching.

   - *Inter-Process Communication (IPC)*: TinyMOS supports basic IPC through message
     passing. Processes can send messages to each other (`SendMessage`) and wait
     for messages (`WaitForMessage`), facilitating communication (e.g., producer-consumer demo).


### 5. *System Calls*

   - TinyMOS provides system calls for process management and synchronisation, including:
     - `Yield`: Voluntarily relinquish CPU control.
     - `Sleep`: Block the process for a specified duration.
     - `WaitForMessage`: Block until a message is received.
     - `SendMessage`: Send a message to another process.
     - `Exit`: Terminate the process.
     - `IOOperation`: Simulate I/O operations by blocking for a specified duration.
   - These system calls allow processes to interact with the OS and other processes,
     supporting both cooperative and preemptive behaviour.


### 6. *Resource Management*

   - *Memory Management*: TinyMOS includes periodic garbage collection (`gc.collect()`)
     to manage memory, which is critical for resource-constrained devices like the Pico.
   - *Blocking and Unblocking*: Processes blocked due to I/O operations or waiting for
     messages are moved to a `blocked_processes` list and periodically checked to be
     unblocked when their blocking condition (e.g., timeout) is met.


### 7. *Scheduling Modes*

   - *Round-Robin (Default)*: Processes are scheduled in a FIFO manner with equal time
     slices, ensuring fairness but not prioritising critical tasks.
   - *Priority-Based*: When enabled, processes with higher priorities (e.g., `CRITICAL`)
     are executed before lower-priority ones, which is useful for real-time or time-sensitive
     tasks (demonstrated in the `demo_priority_scheduling`).


### 8. *Example Use Cases*

   - The provided demos showcase TinyMOS's capabilities:
     - *Basic Multitasking Demo*: Runs multiple processes (`Counter`, `Blinker`,
       `TemperatureReader`) concurrently, demonstrating cooperative and preemptive multitasking.
     - *Producer-Consumer Demo*: Shows IPC using message passing between a producer
       and consumer process.
     - *Priority Scheduling Demo*: Demonstrates how high-priority processes (e.g.,
       `HighPrio`) are executed before lower-priority ones when priority scheduling is enabled.


### Summary

TinyMOS is a *preemptive and cooperative multitasking* operating system with support for
*priority-based scheduling* (when enabled) or *round-robin scheduling* (by default).
It manages processes using a *Process Control Block*, supports *inter-process communication*
via message passing, and enforces *time slicing* for fair CPU allocation. It is suited
for embedded systems like the Pico, balancing simplicity and functionality for resource-constrained
environments.


