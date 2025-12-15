
## TinyMOS Project


### 1. Introduction

This project guides you through building and extending TinyMOS, a lightweight
operating system aimed at resource-constrained environments such as the
Raspberry Pi Pico. The goal is for you to understand how an operating system
can manage multiple processes, schedule them fairly, and provide basic
inter-process communication while running on tight hardware constraints.

By the end of the project, you will have extended the provided TinyMOS
framework into a working multitasking operating system with preemptive scheduling,
process control, message passing, and optional priority-based task handling.
You will run multiple concurrent processes and observe how the system manages
them over time.

TinyMOS uses Python to simulate OS behaviour. This allows you to focus on
operating system design rather than low-level hardware details, while still
producing correct OS behaviour.



### 2. Starting Point

The project begins from the provided files, which include a basic TinyMOS
framework. You will build on this foundation rather than starting from scratch.

The provided code gives you:

- A basic OS structure
- A scheduler loop
- A process abstraction (based on generators)
- Time slicing support
- Demonstration processes and example scheduling behaviour

To run the project, you need Python 3. Your development loop is:
```
> python3 main.py
```
You will see multiple processes running in parallel as you complete
more of the project.



### 3. Project Goal

The goal is to implement a minimal but functional operating system that supports:

- Multiple processes
- Cooperative multitasking
- Preemptive multitasking with time slicing
- Message passing between processes
- Process blocking and waking
- Process states and lifecycle management
- Priority-based scheduling (optional but encouraged)

You will complete these features in a linear sequence.


### 4. Core Tasks

#### 4.1 Process creation and scheduler loop
Implement or verify:

- A process control block structure
- A scheduler loop that selects the next runnable process
- The ability to create and register multiple processes

Expected behaviour: multiple processes should get CPU time, one after the other.

#### 4.2 Cooperative multitasking (yield, sleep)
Add support for:

- Yielding voluntarily
- Sleeping for a period of time
- Blocking a process until a timeout expires

Expected behaviour: processes that sleep or yield should allow others to run.

#### 4.3 Preemptive multitasking (time slicing)
Extend the scheduler so that:

- Each process receives a fixed time slice
- If it does not yield, the OS performs a forced context switch

Expected behaviour: even a greedy process should not starve others.

#### 4.4 IPC with message passing
Implement:

- SendMessage
- WaitForMessage
- A process moves to a blocked list if it waits with no message available

Expected behaviour: a producer process should wake a consumer when delivering a message.

#### 4.5 Process states and lifecycle
Support state transitions:

- READY
- RUNNING
- BLOCKED
- TERMINATED

Expected behaviour: terminated processes must be cleaned up and removed from the schedule.

#### 4.6 Priority scheduling
Add optional support for:

- Priority queues
- Choice of round-robin (default) or priority-based scheduling

Expected behaviour: a high-priority process runs before a low-priority process when enabled.



### 5. Verification

At the end of each core task, run `main.py` and confirm:

- Output from multiple active processes
- Forced scheduling after time slicing
- Consumer waking when a producer posts a message
- No permanent starvation
- Blocked tasks moving back to READY when appropriate
- Terminated tasks never scheduled again

If each step behaves as expected, move on to the next task.



### 6. Final Result

When all core tasks are completed, you will have a functioning operating system
that manages multiple concurrent processes, performs both cooperative and preemptive
scheduling, and supports message-based inter-process communication. You will
understand how an OS transitions between process states, how a scheduler enforces
time fairness, and how blocking, priorities, and IPC interact in a live system.

Even though TinyMOS runs in Python, the operating principles carry directly to
embedded operating systems and microkernels. The result is a compact but
realistic OS design suitable for constrained hardware.


### 7. Optional Extensions

You may extend TinyMOS with:

- A file system abstraction
- A shell process that accepts commands
- Round-robin vs priority mode switching via system call
- System call logging
- Deadlock detection
- Named message channels



## 8. Closing Notes

This project teaches the core mechanisms of operating system behaviour through hands-on
implementation. You have worked through the concepts that make embedded operating systems
function, including process lifecycle management, scheduling, time slicing, and IPC.
From here, you can continue toward drivers, memory management, or hardware integration
as a natural next step ..

