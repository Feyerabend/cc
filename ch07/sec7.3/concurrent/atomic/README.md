
## Atomic Counter

Atomic counters are shared variables that guarantee thread-safe read-modify-write operations in *parallel*
(not just concurrent) systems. They are enforced by hardware/OS primitives, not just logical scheduling,
and are critical for performance-sensitive systems like databases, OS kernels, and game engines.

The code in the folder defines a modular virtual machine (ToyVM) that simulates *cooperative multithreading*
with synchronisation primitives, message passing, and stack-based instruction execution. It models OS-like concepts
(locks, semaphores, atomic counters, message queues) and supports configurable scheduling policies (round-robin,
priority-based). Threads execute in discrete *atomic steps*, managed by a non-preemptive scheduler, ensuring
operations like `acquire()` or `send()` are treated as indivisible within the VM's concurrency model.

`atomic_demo.py` demonstrates this directly by running two back-to-back experiments — one unsafe, one safe —
over the same ToyVM, making the consequence of missing atomicity observable and measurable.


### The Demo: `atomic_demo.py`

The script requires `toyvm.py` to be in the same directory and is run with:

```
python atomic_demo.py
```

Two experiments execute sequentially. Both spawn two worker threads, each looping 50 times to increment a
shared counter. The expected final value is always 100 (2 threads × 50 increments). What actually arrives
depends on whether the increment is atomic.

*Experiment 1 — UNSAFE (race condition)*

Each worker increments the global `counter_value` using three separate VM instructions:

```
LOAD  counter_value    ← read current value     (step A)
PUSH  1 / ADD          ← compute new value      (step B)
GLOBAL_STORE           ← write back to global   (step C)
```

Because these are three distinct instructions, the scheduler may switch threads between any two of them.
When a context switch occurs between step A and step C, both threads hold the same stale value, both
compute `stale + 1`, and both write it back — one increment is silently lost. In the worst case (maximum
interleaving) the final counter is 50 rather than 100.

*Experiment 2 — SAFE (atomic counter)*

Each worker increments using a single `ATOMIC_INCREMENT` instruction:

```
LOAD  atomic_ctr       ← push counter handle
ATOMIC_INCREMENT       ← indivisible read-add-write
POP                    ← discard returned new value
```

`ATOMIC_INCREMENT` is one VM instruction and therefore one scheduler step. No context switch can occur
inside it. Every increment lands, and the final value is exactly 100 on every run.


### Instruction-Level Race Window

The gap between step A (read) and step C (write) in the unsafe path is the *race window*. Any thread
scheduled during that window operates on a stale snapshot. The table below shows how the two approaches
compare at the instruction level:

| Step | UNSAFE (3 instructions)       | SAFE (1 instruction)        |
|------|-------------------------------|-----------------------------|
| 1    | `LOAD counter_value`  ← read  | `LOAD atomic_ctr`           |
| 2    | `PUSH 1` / `ADD`  ← compute   | `ATOMIC_INCREMENT` ← all-in-one |
| 3    | `GLOBAL_STORE`  ← write       | `POP`                       |
| Race | Possible between steps 1–3    | Impossible: single step     |


### Comparison to Real-World Counters

| Feature             | ToyVM AtomicCounter                   | Real-World Atomic (e.g., C++/Java)              |
|---------------------|---------------------------------------|-------------------------------------------------|
| Atomicity Guarantee | Cooperative scheduler steps           | Hardware instructions (e.g., x86 `LOCK` prefix) |
| Concurrency Model   | Simulated (single-threaded)           | Parallel (true multithreading)                  |
| Use Case            | Education/deterministic sim           | High-performance, thread-safe code              |
| Overhead            | None (logical abstraction)            | Low-level CPU/OS overhead                       |
| Operations          | `increment()`, `decrement()`, `get()` | `fetch_add()`, `compare_exchange_strong()`, etc.|
| Thread Safety       | VM-enforced via cooperative steps     | Hardware/OS-enforced                            |


### Atomicity in the ToyVM Context

"Atomic" here refers to *logical indivisibility*, not hardware-level guarantees. Operations are atomic
*within the VM's cooperative scheduling model*: the scheduler ensures no thread is interrupted mid-operation,
enabling deterministic concurrency simulation.

1. *Thread (Execution Context)*  
   - Manages per-thread state: program counter (`pc`), stack, local variables, and status (`running`, `waiting`).  
   - *Atomic operation*: `step()` executes *one instruction* as an indivisible unit before yielding control.  

2. *Lock*  
   - Mutual exclusion primitive.  
   - *Atomic operations*:  
     - `acquire()`: Checks/updates `locked` and `owner` without interruption.  
     - `release()`: Clears ownership and unblocks a waiting thread (if any).  

3. *Semaphore*  
   - Counting-based synchronisation.  
   - *Atomic operations*:  
     - `acquire()`: Decrements `count` or blocks the thread.  
     - `release()`: Increments `count` and wakes one blocked thread.  

4. *MessageQueue*  
   - Thread communication channel.  
   - *Atomic operations*:  
     - `send()`: Transfers a message directly to a waiting receiver or enqueues it.  
     - `receive()`: Retrieves a message or blocks until one is available.  

5. *AtomicCounter*  
   - Shared integer with thread-safe semantics *within the VM*.  
   - *Atomic operations*: `increment()`, `decrement()`, and `get()` appear indivisible.  
   - *Demonstrated by*: `atomic_demo.py`, which shows that `ATOMIC_INCREMENT` always yields 100
     while a plain read-modify-write sequence yields less whenever the scheduler interleaves threads.


*Core Behaviour*  
1. *Instruction Execution*  
   - Threads execute instructions sequentially via `step()`, with each step treated as atomic.  
   - Example instructions: `PUSH`, `ADD`, `LOAD`, `GLOBAL_STORE`, `ATOMIC_INCREMENT`.  

2. *Scheduling*  
   - Cooperative: Threads run until they block, complete, or explicitly yield.  
   - Policies:  
     - *Round-robin*: Cycles through ready threads.  
     - *Priority*: Selects threads based on priority.  
   - Deadlock detection halts execution if all threads are blocked.  

3. *Synchronisation & Communication*  
   - Threads block on locks/semaphores/message queues, managed by the VM.  
   - `join()`: Blocks until a target thread terminates.  

4. *Debugging*  
   - Verbose logging tracks thread states, instruction flow, and synchronisation events.  
   - Pass `debug=True` to `vm.run()` to enable per-step output.  


*Atomic Concept Summary*  
| Concept        | Atomic Operations            | Guarantee                               |  
|----------------|------------------------------|-----------------------------------------|  
| Thread         | `step()`                     | Single instruction execution            |  
| Lock           | `acquire()`, `release()`     | Uninterrupted ownership transition      |  
| Semaphore      | `acquire()`, `release()`     | Atomic count adjustment + thread wakeup |  
| MessageQueue   | `send()`, `receive()`        | Uninterrupted message transfer          |  
| AtomicCounter  | `increment()`, `decrement()` | Indivisible value update                |  
| VM Scheduler   | `select_thread()`            | Thread state transitions without race   |  


*Class Diagram Highlights*  
- *ToyVM*: Central coordinator managing threads, primitives, and scheduling.  
- *Primitives (Lock/Semaphore/MessageQueue)*: Decouple synchronisation logic from threads.  
- *Cooperative Design*: Threads rely on the scheduler to advance, enabling deterministic atomicity.  


*Key Clarifications*  
- *Simulated Concurrency*: No parallelism; atomicity is enforced via scheduling, not hardware.  
- *Non-Preemptive*: Threads yield control explicitly (e.g., via blocking instructions or thread completion).  
- *Determinism*: Atomic steps and cooperative scheduling enable reproducible behaviour.  
- *Observable Race*: `atomic_demo.py` makes the race condition concrete — without `ATOMIC_INCREMENT`,
  lost increments are not an edge case but the expected outcome under interleaved scheduling.  

This version emphasises the VM's *simulated* concurrency model, distinguishes logical vs. 
hardware atomicity, and aligns terminology with cooperative multithreading paradigms.
