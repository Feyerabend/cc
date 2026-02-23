
## Semaphores

A semaphore is a synchronisation primitive used to control access to a shared resource by multiple
threads in a concurrent system. Conceptually, a semaphore maintains an internal counter. Threads
perform two main operations on a semaphore:

- `acquire()` (sometimes called wait or P): Decrements the counter. If the counter is zero, the
  thread blocks until another thread releases.

- `release()` (also called signal or V): Increments the counter and potentially unblocks waiting threads.

There are two common types of semaphores:
1. *Counting Semaphore.* Allows a fixed number of threads to access a resource concurrently (e.g., a
   thread pool of size 5).
2. *Binary Semaphore (Mutex).* Can be either 0 or 1, effectively acting as a lock (mutual exclusion).

Semaphores are useful for:
- Limiting concurrent access to a finite number of resources.
- Managing producer-consumer scenarios.
- Coordinating threads in specific sequences.

Unlike locks or mutexes, semaphores do not necessarily enforce *ownership*, meaning a thread that didn’t
acquire it may still release it--this flexibility comes with both power and risk.

```mermaid
flowchart TD
    A[Start Thread] --> B[Try to acquire semaphore]
    B --> C{Semaphore count > 0}
    C -- Yes --> D[Decrement count]
    D --> E[Enter critical section]
    E --> F[Do work]
    F --> G[Release semaphore - increment count]
    G --> H[Thread exits]

    C -- No --> W[Wait until count > 0]
    W --> B
```



Simple Example in Python with threading.Semaphore

```python
import threading
import time
import random

# A shared resource: a pool with 3 available "slots"
semaphore = threading.Semaphore(3)

def worker(thread_id: int):
    print(f"Thread-{thread_id} is waiting to enter critical section.")
    with semaphore:  # Acquire semaphore
        print(f"Thread-{thread_id} has entered critical section.")
        time.sleep(random.uniform(0.5, 2.0))  # Simulate work
        print(f"Thread-{thread_id} is leaving critical section.")

threads = []
for i in range(7):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("All threads completed.")
```


### Explanation

In this simulation, we create 7 threads, but the semaphore allows only 3 threads to execute in the "critical section"
at a time. This models situations like limiting the number of database connections, concurrent downloads, or slots in
a connection pool.

Python's `threading.Semaphore(value)` starts with a given value (3 in this case). Each thread calls `semaphore.acquire()`
when entering the critical section and semaphore.release() when exiting (implicitly done by with block). This ensures at
most 3 threads can work concurrently in the guarded block.


```mermaid
flowchart TD
    S[Semaphore count = 3]

    T1[Thread 1 wants access] --> A1[Acquire S]
    T2[Thread 2 wants access] --> A2[Acquire S]
    T3[Thread 3 wants access] --> A3[Acquire S]
    T4[Thread 4 wants access] --> A4[Acquire S]

    A1 --> C1[Critical Section 1]
    A2 --> C2[Critical Section 2]
    A3 --> C3[Critical Section 3]
    A4 --> W4[Blocked - Waiting for Slot]

    C1 --> R1[Release S]
    R1 --> A4
    A4 --> C4[Critical Section 4]
```