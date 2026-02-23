
### Threads

Python's threading module allows running multiple threads concurrently.

```python
import threading

def worker():
    print("Thread is running")

t = threading.Thread(target=worker)
t.start()
t.join()
```


### Locks & Mutexes

A Lock ensures only one thread accesses a shared resource at a time.

```python
lock = threading.Lock()

def safe_increment():
    global counter
    with lock:
        counter += 1  # Critical section

counter = 0
threads = [threading.Thread(target=safe_increment) for _ in range(10)]

for t in threads:
    t.start()
for t in threads:
    t.join()
```



### Semaphores

A Semaphore limits the number of concurrent accesses.

```python
semaphore = threading.Semaphore(3)

def worker():
    with semaphore:
        print("Semaphore acquired")
        time.sleep(1)

threads = [threading.Thread(target=worker) for _ in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```



### Atomic Operations

Using threading for atomic increments is unreliable due to the Global Interpreter Lock (GIL), but multiprocessing.Value allows atomic operations in parallel processes.

```python
from multiprocessing import Value, Process

counter = Value('i', 0)

def increment():
    with counter.get_lock():  # Ensures atomic update
        counter.value += 1

processes = [Process(target=increment) for _ in range(10)]
for p in processes:
    p.start()
for p in processes:
    p.join()

print(counter.value)
```




### Message Passing

The queue.Queue module allows safe communication between threads.

```python
from queue import Queue

queue = Queue()

def producer():
    for i in range(5):
        queue.put(i)

def consumer():
    while not queue.empty():
        item = queue.get()
        print(f"Consumed {item}")

t1 = threading.Thread(target=producer)
t2 = threading.Thread(target=consumer)

t1.start()
t1.join()
t2.start()
t2.join()
```




### Parallelism

Python's multiprocessing module bypasses the GIL for true parallelism.

```python
from multiprocessing import Pool

def square(n):
    return n * n

with Pool(4) as p:
    results = p.map(square, range(10))
print(results)
```




### Condition Variables

A Condition allows threads to wait for a condition before proceeding.

```python
condition = threading.Condition()
ready = False

def worker():
    global ready
    with condition:
        condition.wait_for(lambda: ready)
        print("Worker started")

def starter():
    global ready
    with condition:
        ready = True
        condition.notify_all()

t1 = threading.Thread(target=worker)
t1.start()
threading.Thread(target=starter).start()
t1.join()
```
