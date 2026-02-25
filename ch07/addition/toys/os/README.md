
## ToyOS - Operating System Simulator

A modular operating system built on top of the cooperative kernel from `toyvm.c`.

### Architecture

```
  Applications Layer
  ? (Future: shell, user programs, utilities)

<- System Calls ->

  Operating System (toyos.c)
  - Process Management (fork, wait, exit) 
  - File System (VFS with file descriptors)
  - System Call Interface
  - Time-based Scheduling

<- Uses ->

   Cooperative Kernel (toyvm.c)
   - Thread Scheduling (run queue)
   - Synchronization (locks, semaphores)
   - Inter-thread Communication (queues)
   - Deadlock Detection
```


#### Process Management
- *fork()* - Clone current process, child gets PID 0 as return value
- *wait()* - Parent blocks until child exits, reaps zombie children
- *exit()* - Terminate process, become zombie until reaped
- *getpid()* - Return current process ID

#### File System
- In-memory virtual file system
- File descriptor abstraction (per-process fd table)
- Reference counting for open files
- System calls: open(), read(), write(), close()

#### Time & Scheduling
- Tick-based system clock
- *sleep()* - Block process for N ticks
- *gettime()* - Get current system time

#### System Call Interface
- New `OP_SYSCALL` opcode with syscall numbers
- Clean separation between user code and kernel


### Demo

1. *Fork and Wait* - Parent creates child, child computes 10+20, parent waits and reaps
2. *File I/O* - Write ASCII values 65,66 to file, read them back
3. *Sleep and Timing* - Two processes print timestamps, one sleeps between iterations

- *Process*: Extended thread with parent/child relationships, file descriptors
- *File System*: Simple in-memory files with path-based lookup
- *System Calls*: Interface between user-mode process and OS kernel
- *Scheduler*: Cooperative scheduling with sleep/wake mechanism



### Next Steps

### Phase 1: Enhanced Process Control DONE
- [x] Fork/exec model
- [x] Process hierarchy
- [x] Zombie processes and reaping

### Phase 2: Richer File System
- [ ] Directories and path traversal
- [ ] File permissions (read/write/execute)
- [ ] Pipes for IPC (`pipe()` syscall)
- [ ] Standard input/output/error (stdin=0, stdout=1, stderr=2)

### Phase 3: Memory Management
- [ ] Virtual memory abstraction
- [ ] Heap allocation syscalls (malloc/free primitives)
- [ ] Memory protection boundaries
- [ ] Simple page table simulation

### Phase 4: Simple Shell
- [ ] Command parser (splits input into argv)
- [ ] Built-in commands (cd, pwd, echo, exit)
- [ ] Execute programs via exec()
- [ ] Pipes between processes (cmd1 | cmd2)
- [ ] I/O redirection (>, <, >>)

### Phase 5: Loadable Programs
- [ ] Program format specification (bytecode file format)
- [ ] Program loader (read bytecode from file)
- [ ] Dynamic linking (shared library simulation)
- [ ] ELF-like structure with headers

### Phase 6: "Real" Applications ("toys")
- [ ] Calculator program (bytecode)
- [ ] Text editor (line-based)
- [ ] File utilities (ls, cat, cp, rm)
- [ ] Process manager (ps, kill)


### Design Philosophy

This project demonstrates *layered abstraction*:

1. *Kernel* (`toyvm.c`): Manages threads, locks, queues
2. *OS* (`toyos.c`): Adds processes, files, syscalls on top
3. *Applications* (future): Use syscalls to do useful work

Each layer only uses the interface below it,
creating clean separation of concerns.


### Example: Writing a "Hello World" Program

In the current system, you'd write it as instruction arrays:

```c
Instr hello_program[] = {
    instr_push(72),   // 'H'
    instr_print(),
    instr_push(101),  // 'e'
    instr_print(),
    // ... etc
    instr_exit(),
};
```

*Future (Phase 5)*: Load from bytecode file:

```
$ cat hello.tbc
PUSH 72
PRINT
PUSH 101
PRINT
...
EXIT

$ ./toyos
> run hello.tbc
Hello
>
```


### Plausible Extensions

#### 1. Network Stack (Advanced)
- Socket abstraction
- TCP/IP state machine simulation
- Packet queue as message queues

#### 2. Multi-Core Simulation
- Multiple run queues
- CPU affinity
- Load balancing between cores

#### 3. Interrupt Simulation
- Timer interrupts for preemption
- I/O completion interrupts
- Interrupt handlers in kernel

#### 4. Debugging Tools
- Process inspector (stack trace, variables)
- System call tracer (like strace)
- Performance profiler


### Why This Approach?

Traditional OS courses teach concepts but students rarely see them *integrated*.
This project shows:

- How processes are built on threads
- How file descriptors are just indexes into tables
- How syscalls cross the user/kernel boundary
- How scheduling interacts with I/O

All in ~1500 lines of readable C code.


### Educational Value

Perfect for:
- OS course projects
- Interview preparation (system design questions)
- Understanding Unix/Linux internals
- Learning about abstraction layers


### Implementation Notes

#### Fork Implementation
Fork creates a complete copy of the parent's state:
- Program counter (child continues from same instruction)
- Stack (child inherits parent's execution state)
- Variables (copy-on-write would be future enhancement)
- File descriptors (currently inherited, could add close-on-exec flags)

#### File System Design
Currently in-memory only, but structure supports:
- Adding persistence (write to actual files)
- Mounting different filesystem types
- Network filesystems

#### Syscall Mechanism
Uses a simple opcode (`OP_SYSCALL`) with syscall numbers.
Could be extended to:
- Verify user/kernel mode boundaries
- Copy data safely between user/kernel space
- Handle errors more robustly

### Performance Characteristics

- *Process creation*: O(1) copy of parent state
- *Context switch*: O(1) save/restore
- *File operations*: O(n) linear search for file paths
- *Scheduling*: O(1) round-robin queue

### Comparison to Real OSes

| Feature       | ToyOS          | Linux                   |
|---------------|----------------|-------------------------|
| Process Model | Fork/exec      | Fork/exec               |
| File System   | In-memory      | ext4, xfs, etc.         |
| Scheduling    | Cooperative    | Preemptive CFS          |
| Memory        | None           | Virtual memory          |
| IPC           | Message queues | pipes, sockets, signals |
| Syscalls      | 10             | 300+                    |

