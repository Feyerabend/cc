
## ToyVM & Concur

The *ToyVM* (Threaded Operations Yard Virtual Machine) is a Python-based virtual
machine designed to simulate a multithreaded environment. It provides a stack-based
instruction set with support for threads, locks, semaphores, message queues, and
atomic counters--intended for educational purposes, prototyping concurrent algorithms,
or experimenting with thread-based programming in a controlled environment.

*Concur* is a high-level language built on top of the ToyVM. Short for "Concurrent,"
it abstracts away the low-level stack-based instruction set into intuitive constructs
for writing multithreaded programs--making the ToyVM accessible for learners and
rapid prototyping alike.



### Part I: The ToyVM

#### 1. Architecture Overview

The ToyVM consists of several key components:

- *Thread*: A single thread of execution with its own program counter (PC), stack, and variables.
- *Lock*: A mutual exclusion mechanism ensuring only one thread accesses a critical section at a time.
- *Semaphore*: A synchronisation primitive for controlling access to resources with a specified count.
- *MessageQueue*: A queue for asynchronous communication between threads.
- *AtomicCounter*: A thread-safe counter for atomic increment/decrement operations.
- *ToyVM*: The main virtual machine managing threads, resources, and scheduling.

Key features include stack-based execution (similar to the JVM), round-robin/priority/random
thread scheduling, deadlock detection, and a debug mode with detailed trace output.


#### 2. Instruction Set

Instructions use a tuple-based format: `(opcode, *args)`.

__Stack Operations__
- *PUSH value*: Pushes a value onto the thread's stack.
- *POP*: Removes the top value from the stack.
- *DUP*: Duplicates the top value on the stack.

__Arithmetic__
- *ADD*: Pops two values, pushes `a + b`.
- *SUB*: Pops two values, pushes `a - b`.
- *MUL [mod]*: Pops two values, pushes `a * b` (or `a % b` if `mod` is specified).
- *DIV*: Pops two values, pushes `a // b`. Assumes `b != 0`.

__Variables__
- *LOAD var_name*: Pushes the value of `var_name` (thread-local or global) onto the stack.
- *STORE var_name*: Pops the top value into thread-local `var_name`.
- *GLOBAL_STORE var_name*: Pops the top value into a global variable.

__Control Flow__
- *JUMP address*: Sets the program counter to `address` (0-based).
- *JUMP_IF address*: Pops a value; jumps if it's non-negative (`>= 0`).

__Output__
- *PRINT [message]*: Prints a message or the top stack value. If `message`
  contains `{}`, formats with the top stack value.

__Thread Management__
- *THREAD_CREATE instruction_list*: Pops an index, selects instructions from
  `instruction_list`, creates a new thread, pushes the thread name.
- *THREAD_JOIN*: Pops a thread name and waits for it to terminate.

__Synchronization__
- *LOCK_CREATE*: Creates a new lock and pushes its name.
- *LOCK_ACQUIRE*: Acquires the lock at the top of the stack. Blocks if already held.
- *LOCK_RELEASE*: Releases the lock at the top of the stack, waking the next waiting thread.
- *SEMAPHORE_CREATE*: Pops a count, creates a semaphore, pushes its name.
- *SEMAPHORE_ACQUIRE*: Acquires the semaphore at the top of the stack. Blocks if count is zero.
- *SEMAPHORE_RELEASE*: Releases the semaphore, waking a waiting thread or incrementing the count.
- *ATOMIC_CREATE*: Pops an initial value, creates an atomic counter, pushes its name.
- *ATOMIC_INCREMENT*: Increments the named counter and pushes the new value.
- *ATOMIC_DECREMENT*: Decrements the named counter and pushes the new value.
- *ATOMIC_GET*: Pushes the current value of the named counter.

__Message Passing__
- *QUEUE_CREATE*: Creates a message queue and pushes its name.
- *QUEUE_SEND*: Pops a message and queue name, sends the message. Delivers directly if a receiver is waiting.
- *QUEUE_RECEIVE*: Receives from the named queue. Blocks if no message is available.

__Miscellaneous__
- *SLEEP duration*: Pauses the thread for `duration` milliseconds.
- *NOP*: No operation.


#### 3. How to Use

```python
## Step 1: Initialise the VM
vm = ToyVM()

## Step 2: Define instructions
instructions = [
    ("PUSH", 42),
    ("PRINT", "Value: {}"),
    ("POP",),
]

## Step 3: Create a thread and run
vm.create_thread(instructions, name="main")
vm.run(max_steps=1000, debug=True)
```


#### 4. Example Programs

__Simple Arithmetic__

```python
instructions = [
    ("PUSH", 10),
    ("PUSH", 20),
    ("ADD",),
    ("PRINT", "Sum: {}"),
]

vm = ToyVM()
vm.create_thread(instructions, name="main")
vm.run(debug=True)
```

*Output*:
```
[main] Sum: 30
All threads completed after 4 steps
```

__Producer-Consumer with Message Queue__

```python
producer_instructions = [
    ("QUEUE_CREATE",),
    ("DUP",),
    ("GLOBAL_STORE", "queue"),
    ("PUSH", "Hello"),
    ("PUSH", "queue"),
    ("QUEUE_SEND",),
    ("PUSH", "World"),
    ("PUSH", "queue"),
    ("QUEUE_SEND",),
]

consumer_instructions = [
    ("LOAD", "queue"),
    ("QUEUE_RECEIVE",),
    ("PRINT", "Received: {}"),
    ("LOAD", "queue"),
    ("QUEUE_RECEIVE",),
    ("PRINT", "Received: {}"),
]

vm = ToyVM()
vm.create_thread(producer_instructions, name="producer")
vm.create_thread(consumer_instructions, name="consumer")
vm.run(debug=True)
```

*Output* (abridged):
```
[consumer] Received: Hello
[consumer] Received: World
All threads completed after X steps
```

__Critical Section with Lock__

```python
worker_instructions = [
    ("LOAD", "lock"),
    ("LOCK_ACQUIRE",),
    ("LOAD", "counter"),
    ("ATOMIC_INCREMENT",),
    ("GLOBAL_STORE", "counter"),
    ("LOAD", "lock"),
    ("LOCK_RELEASE",),
]

counter_instructions = [
    ("LOCK_CREATE",),
    ("GLOBAL_STORE", "lock"),
    ("ATOMIC_CREATE", 0),
    ("GLOBAL_STORE", "counter"),
    ("PUSH", 0),
    ("THREAD_CREATE", [worker_instructions]),
    ("PUSH", 0),
    ("THREAD_CREATE", [worker_instructions]),
    ("THREAD_JOIN",),
    ("THREAD_JOIN",),
    ("LOAD", "counter"),
    ("PRINT", "Final counter: {}"),
]

vm = ToyVM()
vm.create_thread(counter_instructions, name="main")
vm.run(debug=True)
```

*Output* (abridged):
```
[main] Final counter: 2
All threads completed after X steps
```


#### 5. Scheduling and Thread States

Set the scheduler via `vm.scheduler_type`:
- *round_robin* (default): Cycles through active threads in order.
- *priority*: Selects the highest-priority thread (ties broken by least recent execution).
- *random*: Chooses a thread randomly.

Thread states: *runnable*, *waiting* (blocked on lock/semaphore/queue/join), or *terminated*.


#### 6. Deadlock Detection

The VM detects deadlocks when all threads are waiting and no progress is possible — for example, two threads each holding a lock and waiting for the other's. In debug mode, the deadlock is reported and execution halts.


#### 7. Limitations

- No floating-point arithmetic (integer only).
- No true parallelism — threads run one instruction at a time.
- No advanced data types (integers and strings only).
- Long-running programs may be cut off by `max_steps`.
- Division by zero or invalid opcodes produce warnings but may not halt cleanly.



### Part II: Concur

#### 1. Overview

*Concur* is a high-level, concurrency-first language that compiles to ToyVM instructions. It is designed to:
- Simplify writing multithreaded programs with intuitive syntax.
- Provide first-class constructs for threads, locks, semaphores, queues, and atomic counters.
- Serve as an educational tool for learning concurrency concepts.
- Abstract away stack manipulation and low-level jumps entirely.


#### 2. Syntax Reference

__Variables and Arithmetic__

Variables are declared implicitly via assignment. Standard operators: `+`, `-`, `*`, `%`, `/`.

```concur
x = 10
y = 20
z = x + y
print("Sum: ", z)
```

__Threads__

`thread <name> { <body> }` spawns a thread; `join <name>` waits for it.

```concur
thread worker {
    print("Worker running")
}
join worker
print("Main done")
```

__Locks__

`lock <name> { <body> }` acquires the lock, runs the body, then releases automatically.

```concur
global counter = 0
lock mylock {
    counter = counter + 1
}
print("Counter: ", counter)
```

__Semaphores__

`semaphore <name> = <count>` creates a semaphore; `acquire` and `release` manage it.

```concur
semaphore sem = 2
acquire sem
print("In critical section")
release sem
```

__Message Queues__

`queue <name>` creates a queue; `send <name>, <value>` and `receive <name>` handle messages.

```concur
queue q
thread producer {
    send q, "Hello"
}
thread consumer {
    msg = receive q
    print("Got: ", msg)
}
join producer
join consumer
```

__Atomic Counters__

`atomic <name> = <initial>` creates a counter; `increment`, `decrement`, and `get` manipulate it.

```concur
atomic counter = 0
increment counter
print("Counter: ", get counter)
```

__Control Flow__

```concur
x = 0
while x < 3 {
    print("x = ", x)
    x = x + 1
}
```

__Sleep__

```concur
print("Start")
sleep 1000
print("End")
```


#### 3. Example Program: Producer-Consumer

```concur
queue q
global counter = 0
lock counter_lock

thread producer {
    send q, "Message 1"
    send q, "Message 2"
    lock counter_lock {
        counter = counter + 1
    }
}

thread consumer {
    msg1 = receive q
    print("Consumer got: ", msg1)
    msg2 = receive q
    print("Consumer got: ", msg2)
    lock counter_lock {
        counter = counter + 1
    }
}

join producer
join consumer
print("Final counter: ", counter)
```

*Behaviour*: The producer sends two messages and increments a shared counter;
the consumer receives and prints them, then also increments.
The lock ensures thread-safe updates. Final counter should be 2.

*Output*:
```
[consumer] Consumer got: Message 1
[consumer] Consumer got: Message 2
[main] Final counter: 2
All threads completed after X steps
```


#### 4. Compilation to ToyVM

A Concur compiler would:
1. *Parse* the source into an AST (e.g., using PLY or Lark).
2. *Generate instructions* by traversing the AST — variables map
   to `PUSH`/`STORE`/`LOAD`/`GLOBAL_STORE`, arithmetic to `ADD`/`SUB`/`MUL`/`DIV`,
   threads to `THREAD_CREATE`/`THREAD_JOIN`, synchronization to
   `LOCK_*`/`SEMAPHORE_*`/`ATOMIC_*`/`QUEUE_*`, and control flow to `JUMP`/`JUMP_IF`.
3. *Optimise* by eliminating redundant stack operations where possible.
4. *Output* a list of ToyVM instruction tuples.

`lock` blocks compile to a `LOCK_ACQUIRE` → body → `LOCK_RELEASE` sequence,
ensuring the lock is always released via a try-finally-like mechanism.


#### 5. Potential Extensions

- *Condition Variables*: `wait` and `signal` for more flexible synchronisation.
- *Arrays / Lists*: Basic data structures via new ToyVM instructions.
- *Error Handling*: `try-catch` blocks for robust programs.
- *Type System*: Optional types for early error detection.
- *Standard Library*: Built-in functions for common tasks (e.g., random numbers).



### Conclusion

The ToyVM provides a transparent, educational platform for exploring concurrent
programming--covering threads, synchronisation, and inter-thread communication
through a minimal stack-based instruction set. Concur sits on top of it as an
expressive, concurrency-first language that hides the low-level details while
preserving full access to the VM's capabilities. Together, they form a complete
environment for learning, prototyping, and experimenting with concurrent algorithms.
I Concur.
