
## ToyVM & ToyOS - Educational Operating System Simulator

### [The Kernel](./kernel/) (toyvm.c)

*What it does*: Manages concurrency at the lowest level.

The kernel provides the machinery for running multiple threads
of execution cooperatively. It implements the *fundamental primitives*
every conventional OS needs:
- *Thread Control Blocks (TCB)*: Each thread has saved registers
  (PC, stack), scheduling metadata, and local variables
- *Run Queue*: Fair scheduling - threads take turns executing one
  instruction at a time
- *Synchronization*: Locks (mutual exclusion), semaphores
  (resource counting), message queues (communication)
- *Wait Queues*: When a thread blocks on a lock or semaphore,
  it goes into a wait queue until the resource is available
- *Deadlock Detection*: Detects when all threads are blocked
  waiting for each other

Think of it as the *traffic controller*--it decides which thread runs
next and handles the mechanics of switching between them.


### [The Operating System](./os/) (toyos.c)

*What it does*: Adds the abstractions that programs actually use.

The OS builds on the kernel's thread machinery to provide *higher-level concepts*:
- *Processes*: Threads with parent/child relationships, PIDs,
  and lifecycle (fork/wait/exit)
- *Virtual File System*: Files with paths, file descriptors
  (per-process tables), read/write operations
- *System Call Interface*: Clean boundary between user programs
  and OS services
- *Time Management*: System clock, sleep/wake scheduling

Think of it as the *librarian*--it organises resources (files, memory, time)
and provides a clean API for programs to use them.

*Key Insight*: The kernel says "how do I run many things at once?"
The OS says "what useful services should I offer to those things?"


### The Relationship

```
Programs (future)
    v syscalls
Operating System (toyos.c) < processes, files, time
    v uses
Kernel (toyvm.c) < threads, locks, scheduling
```

The OS *doesn't reimplement* scheduling--it reuses the kernel's run queue
and context switching. It just wraps threads in the "process" concept
and adds file/memory management.



### Toys: Future Extensions

Ideas for students to push this further, ordered by difficulty:

#### Toy 1: Simple Shell
Build an interactive command interpreter:
- Parse user input into commands and arguments
- Implement built-ins: `cd`, `pwd`, `echo`, `exit`
- Execute programs from bytecode files
- Add I/O redirection: `program > output.txt`
- Support pipes: `cmd1 | cmd2`

*Learning*: How shells work, process creation, I/O streams

#### Toy 2: Program Loader
Create a bytecode file format and loader:
- Design `.tbc` bytecode format (header + instructions + data)
- Write assembler: text → bytecode
- Implement `exec()` syscall to load programs
- Add dynamic linking (shared function library)

*Learning*: How executables work, ELF format, linking

#### Toy 3: Memory Manager
Add virtual memory abstraction:
- Heap allocator: `malloc()` / `free()` syscalls
- Memory protection (bounds checking)
- Shared memory between processes
- Page table simulation (virtual → physical mapping)

*Learning*: Virtual memory, memory allocation algorithms, segmentation faults

#### Toy 4: Standard Utilities
Build a library of tiny programs:
- `cat` - read and print file
- `ls` - list files in directory
- `cp` - copy file
- `wc` - count lines/words
- `grep` - search for pattern
- `ps` - list running processes

*Learning*: Unix philosophy, system programming, file I/O

#### Toy 5: Network Stack
Simulate a simple network:
- Socket API: `socket()`, `bind()`, `connect()`, `send()`, `recv()`
- TCP state machine (SYN, ACK, FIN handshakes)
- Packet queue using message queues
- Simple HTTP server demo

*Learning*: Network protocols, state machines, async I/O

__This is now implemented as [toynet](./net/).__


#### Toy 6: Debugging Tools
Build developer tools:
- `strace` - trace system calls
- `gdb`-like debugger (breakpoints, step, inspect variables)
- Process inspector (show TCB, stack, file descriptors)
- Performance profiler (instruction counts, syscall frequency)

*Learning*: Debugging techniques, instrumentation, profiling

#### Toy 7: Multi-Core Simulation
Extend to simulate multiple CPUs:
- Per-CPU run queues
- CPU affinity and load balancing
- Spinlocks vs mutex behavior differences
- Cache coherency simulation

*Learning*: Parallel computing, race conditions, multi-core architectures

#### Toy 8: Preemptive Scheduling
Replace cooperative scheduling with preemption:
- Timer interrupt simulation
- Context switches at arbitrary points (not just after each instruction)
- Priority scheduling algorithms (Round-Robin, CFS, Real-time)
- Scheduler benchmarks and analysis

*Learning*: Preemption, interrupts, scheduling algorithms

#### Toy 9: Graphical Display
Add visual output:
- Framebuffer abstraction (2D pixel array)
- Terminal emulator (character grid with cursor)
- Simple window system
- Draw process execution timelines

*Learning*: Graphics programming, UI basics, visualization

#### Toy 10: Formal Verification
Prove correctness properties:
- Model checker for deadlock-free programs
- Prove mutual exclusion properties
- Race condition detector
- Annotate code with invariants

*Learning*: Formal methods, model checking, program verification



### Why Toys Matter?

Each toy teaches a *concrete OS concept* that you
read about in textbooks but rarely implement:

- *Shells* → process control and I/O redirection
- *Loaders* → how programs get into memory
- *Memory managers* → allocation, fragmentation, protection
- *Network stacks* → layered protocols and async I/O
- *Debuggers* → introspection and control flow
- *Multi-core* → parallelism and synchronization at scale

Because the codebase is small (~1500 lines total),
you can *actually understand the entire system*--something
impossible with real OSes like Linux, in a short time at least.


### Pedagogical Approach

Students start with:
1. *Read* toyvm.c to understand kernel basics
2. *Read* toyos.c to see how OS builds on kernel  
3. *Pick a toy* based on interest
4. *Implement* using existing syscall interface
5. *Reflect* on what they learned about real OSes

Each toy is *self-contained*--you can build the shell without
touching memory management, or add networking without changing the loader.

Perfect for:
- OS course term projects
- Self-directed learning
- Interview prep (system design)
- Research into new scheduling/allocation algorithms

Your choice!
