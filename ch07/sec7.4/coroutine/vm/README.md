
## Coroutine Virtual Machine in C

A demonstration of cooperative multitasking using coroutines
implemented in a simple stack-based virtual machine.

Coroutines are generalised subroutines that can:
- *Suspend* their execution at any point (yield)
- *Resume* from where they left off
- Maintain their own execution state (stack, program counter, local variables)
- Enable *cooperative multitasking* without threads or preemption

#### VM Architecture
- *Stack-based execution model* with push/pop operations
- *Bytecode interpreter* with custom instruction set
- *Multiple independent coroutines* running cooperatively
- *State preservation* across yield/resume cycles

#### Instruction Set
- `OP_PUSH/POP` - Stack manipulation
- `OP_ADD/SUB` - Arithmetic operations
- `OP_LOAD/STORE` - Local variable access
- `OP_PRINT` - Output values
- `OP_YIELD` - *Suspend coroutine and return control*
- `OP_RETURN` - Mark coroutine as completed
- `OP_JMP/JZ` - Control flow

#### Coroutine States
1. *READY* - Created but not yet started
2. *RUNNING* - Currently executing
3. *SUSPENDED* - Yielded, waiting to resume
4. *DEAD* - Finished execution


#### Execution Flow
```
1. Create coroutines with bytecode
2. Start first coroutine (READY -> RUNNING)
3. Execute instructions until YIELD
4. Coroutine suspends (RUNNING -> SUSPENDED)
5. Switch to next coroutine
6. Resume previous coroutine (SUSPENDED -> RUNNING)
7. Continue from saved program counter
8. Repeat until all coroutines are DEAD
```

#### Details

*State Preservation:*
Each coroutine maintains:
- Program counter (PC) - where to resume
- Stack pointer (SP) - current stack position
- Stack contents - intermediate values
- Local variables - persistent data

*Cooperative Scheduling:*
The main loop round-robins through coroutines:
```c
while (active_coroutines > 0) {
    vm_resume(&vm, co1);  // Run until yield
    vm_resume(&vm, co2);  // Run until yield
    vm_resume(&vm, co3);  // Run until yield
}
```

### Example Output

```
[Coroutine 0] Starting...
[Coroutine 0] Value: 0
[Coroutine 0] Yielding...
[Coroutine 1] Starting...
[Coroutine 1] Value: 100
[Coroutine 1] Yielding...
[Coroutine 2] Starting...
[Coroutine 2] Value: 30
[Coroutine 2] Yielding...

[Coroutine 0] Resuming...
[Coroutine 0] Value: 1
[Coroutine 0] Yielding...
...
```

Notice how each coroutine:
- Maintains its own counter
- Yields after printing
- Resumes with its state intact
- Executes in round-robin fashion


### Uses

#### 1. Generators
Produce sequences of values on demand:
```
Coroutine 0: yields 0, 1, 2, 3, 4
Coroutine 1: yields 100, 101, 102
```

#### 2. Cooperative Multitasking
Multiple tasks sharing CPU without preemption:
- Each task yields voluntarily
- No race conditions (single-threaded)
- Predictable context switches

#### 3. State Machines
Actor model implementation:
- Each actor is a coroutine
- Processes messages and yields
- Maintains internal state

#### 4. Event-Driven Systems
- Coroutines waiting for events
- Yield until event occurs
- Resume when triggered

### Comparison to Threads

| Feature | Coroutines | Threads |
|---------|-----------|----------|
| Context Switch | Cooperative (yield) | Preemptive (OS) |
| Overhead | Very low | Higher |
| Synchronization | Not needed | Mutexes, locks |
| Stack Size | Can be smaller | OS-determined |
| Control | Programmer | OS scheduler |


### Building and Running

```bash
gcc -o coroutine_vm coroutine_vm.c -Wall
./coroutine_vm
```

### Real-World Applications

1. *Language Implementations*: Python generators, JavaScript async/await, Lua coroutines
2. *Game Engines*: Entity behaviours, animation systems, AI scripts
3. *Network Servers*: Handle multiple connections without threads
4. *Simulations*: Discrete event simulation, process modeling
5. *Parsers*: Recursive descent with backtracking


### Extensions

Possible enhancements:
- *Call/return between coroutines* (coroutine communication)
- *Message passing* (actor model)
- *Scheduler policies* (priority-based, deadline-driven)
- *Debugging support* (breakpoints, single-step)
- *Garbage collection* (for dynamic memory)

### Technical Notes

- Each coroutine has its own 256-element stack
- Maximum 8 concurrent coroutines
- 16 local variables per coroutine
- Bytecode is dynamically allocated
- No preemption--relies on cooperative yields

This implementation demonstrates the core concepts of coroutines in a minimal
VM suitable for understanding cooperative multitasking fundamentals.

