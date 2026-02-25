
## Mutex

A mutex, short for mutual exclusion, is a fundamental synchronisation primitive used in concurrent
programming to prevent multiple threads from accessing a shared resource simultaneously in a way
that leads to race conditions or data inconsistency. The core idea is simple but powerful: at any
given time, only one thread can "own" a mutex and thus gain access to the protected section of code
or resource. All other threads attempting to acquire the mutex must wait until it becomes available.

The historical origin of the concept can be traced back to the earliest days of multitasking operating
systems in the 1960s and 1970s, as developers realised that concurrent execution--particularly in
multiprocessor systems--could easily result in corrupted state when two processes attempted to modify
the same memory region or perform non-atomic operations. The term "mutual exclusion" and early
theoretical formulations such as Dekker's and Peterson's algorithms arose during this time to formalise
how competing processes could cooperate without interference. These early approaches were purely
software-based and worked only in restricted environments. Later, hardware-level atomic instructions
such as test-and-set, compare-and-swap, and fetch-and-add enabled more robust and portable implementations
of mutexes in operating systems and runtime libraries.

In practice, mutexes are ubiquitous in systems programming (e.g. C, C++, Rust) and application-level
concurrency frameworks (e.g. Java’s synchronised, Python’s threading.Lock, or Go’s sync.Mutex). They
are used whenever one needs to protect critical sections--regions of code that must be executed atomically
with respect to some shared resource, such as writing to a file, modifying a shared counter, or managing
a queue.

Using a mutex involves two key operations: `lock()` (or `acquire()`) and `unlock()` (or `release()`).
When a thread locks a mutex, it either gains access to the resource if the mutex was free, or is blocked
(or delayed) if another thread currently holds the lock. Once the thread finishes working with the
resource, it must unlock the mutex so that other waiting threads can proceed. Failing to release the
mutex leads to deadlock or starvation.

To demonstrate this in general, consider a simple Python example using threading.Lock:

```python
from threading import Lock, Thread

counter = 0
lock = Lock()

def increment():
    global counter
    for _ in range(100000):
        with lock:
            counter += 1

threads = [Thread(target=increment) for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()

print(counter)  # should be 400000 if all increments were synchronised correctly
```

Without the lock, race conditions may cause unpredictable results--some increments could be lost due
to thread interleaving. The with lock: ensures only one thread modifies counter at a time.

## Mutex in the ToyVM

To illustrate these principles more concretely and observe the mechanics of mutex synchronisation at
a lower level, we provide a demonstration using a minimal virtual machine implementation (ToyVM). The
ToyVM is a simple stack-based interpreter that supports thread creation, scheduling, and synchronisation
primitives including locks (mutexes), semaphores, and message queues. It allows us to see exactly how
threads compete for a shared resource and how a mutex enforces mutual exclusion step-by-step.

The `mutex.py` script showcases four key scenarios using the ToyVM:

*Demonstration 1: Race Condition Without Mutex*

Four threads each increment a shared counter one hundred times without any locking mechanism. The
expected final value is 400, but due to race conditions--where threads read, modify, and write the
counter without coordination--the actual result is typically much lower. This occurs because increments
can be lost when two threads read the same value simultaneously, increment it independently, and write
back overlapping results. Running this demonstration vividly shows how fragile unsynchronised concurrent
access can be.

*Demonstration 2: Proper Synchronisation With Mutex*

The same workload as Demonstration 1, but now each thread acquires a mutex before entering the critical
section (loading the counter, incrementing it, and storing it back) and releases the mutex afterward.
With the mutex in place, only one thread at a time can modify the counter, ensuring that all four hundred
increments are accounted for. The final value is reliably 400, demonstrating that mutual exclusion
prevents lost updates and guarantees correctness.

*Demonstration 3: Deadlock Scenario*

This demonstration introduces two mutexes (lock1 and lock2) and two threads that each need to acquire
both locks. However, Thread A acquires lock1 first and then lock2, while Thread B does the reverse:
lock2 first and then lock1. If both threads acquire their first lock at nearly the same time, each will
then wait indefinitely for the other's lock, resulting in deadlock--a situation where neither thread can
proceed. The script detects this condition by using a timeout; if the threads do not complete within a
few seconds, the demonstration reports a deadlock. This illustrates one of the classic pitfalls of using
multiple mutexes: acquiring locks in inconsistent orders can cause the entire system to freeze.

*Demonstration 4: Deadlock Prevention Through Consistent Lock Ordering*

To resolve the deadlock issue, both threads are instructed to acquire the locks in the same order: lock1
first, then lock2. Even though the threads are running concurrently and may interleave in various ways,
they can never form a circular wait because there is a global ordering to lock acquisition. One thread
will successfully acquire both locks, perform its work, and release them; the other thread will then do
the same. This demonstration completes successfully every time, showing that disciplined lock ordering is
a simple yet effective strategy for preventing deadlock when multiple mutexes are required.

These four demonstrations, when run in sequence, provide a hands-on understanding of why mutexes are
necessary, how they work, and the care one must take when using them--particularly in the presence of
multiple locks. The ToyVM's explicit step-by-step execution makes the abstract concept of mutual exclusion
tangible, revealing the interplay between thread scheduling and synchronisation primitives that underpins
all concurrent programming.

