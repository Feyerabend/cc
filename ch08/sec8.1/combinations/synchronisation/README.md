
## Project: From Concurrency, State, and Determinism to Synchronisation

You already understand three systemic forces:
- *Concurrency*: multiple computations proceed at the same time, sharing resources.
- *State*: a system's configuration at a given moment--the data it holds and transforms.
- *Determinism*: the same inputs always produce the same outputs.

In this project, you will discover that when these three forces meet, a fourth
force is created by their collision:
- *Synchronisation*.

The equation you will derive is:
```
Concurrency + State + Determinism  ->  Synchronisation
```
Your task is not to start from "synchronisation" as a given solution, but to
*reconstruct why synchronisation must exist* if you want a concurrent system
with shared state to behave predictably.

This is a design discovery exercise, not a memorisation one.


### Part 1 - A Thought Experiment: One Thread, No Problem

Imagine a program with a single counter, starting at zero.
A single thread runs this operation one thousand times:

```
read counter
add 1
write counter
```

After one thousand iterations, the counter holds 1000.
It is always 1000.
The result is completely determined by the inputs and the operations.
This is determinism at work.

Now introduce a second thread, doing the same thing simultaneously.
You expect the counter to reach 2000.

Run it. What do you get?


### Part 2 - Discovering the Problem

The two threads are each performing three steps:

```
read counter  (see: 500)
add 1         (compute: 501)
write counter (store: 501)
```

But the threads interleave. While thread A is between its read and its write,
thread B also reads the same value, adds 1, and writes 501.
Thread A then writes 501 as well.

Two increments happened. The counter advanced by one.

This is called a *race condition*. The result depends not only on the inputs
and the logic, but on the *exact timing* of the threads--something you do not
control.

Concurrency + shared State = lost Determinism.

Run a small experiment:

```python
import threading

counter = 0

def increment(n):
    global counter
    for _ in range(n):
        counter += 1

t1 = threading.Thread(target=increment, args=(100_000,))
t2 = threading.Thread(target=increment, args=(100_000,))
t1.start(); t2.start()
t1.join(); t2.join()

print(counter)
```

Run it several times. Record the results. Are they the same each time?


### Part 3 - Why Determinism Demands Ordering

You want determinism back.
That means: for any given schedule of thread operations, the outcome must
be the same as if the threads ran one at a time.

The problem is *interleaving*: thread A's read-add-write is not atomic.
Another thread can step in between any two of those steps.

To restore determinism, you must ensure that the full read-add-write
sequence of one thread completes before another thread touches the counter.

You need to impose *ordering* on access to shared state.

That structure--whatever it is--must:
1. Allow only one thread at a time to perform the sensitive sequence.
2. Make all other threads wait their turn.
3. Release them afterwards.

You have not yet named this structure.


### Part 4 - Your Task: Observe the Race Before You Fix It

Before writing any fix, you must first *observe the race clearly*.

Modify the experiment to print intermediate values, or run it many times
and collect results:

```python
results = []
for _ in range(20):
    counter = 0  # reset

    def increment(n):
        global counter
        for _ in range(n):
            counter += 1

    t1 = threading.Thread(target=increment, args=(10_000,))
    t2 = threading.Thread(target=increment, args=(10_000,))
    t1.start(); t2.start()
    t1.join(); t2.join()
    results.append(counter)

print(results)
print("Expected:", 20_000)
print("Min:", min(results), "Max:", max(results))
```

Observe that:
- The result varies across runs.
- It is always less than or equal to the expected value.
- The deficit is the exact measure of lost determinism.


### Part 5 - Simulate the Cost of Lost Determinism

Now make the cost explicit. Suppose the counter tracks money transferred
between accounts. A race condition does not just produce a wrong number--
it silently destroys value.

Write a model where:
- Two accounts start with a combined balance of 1000.
- Threads transfer amounts between them concurrently.
- After all transfers, you check whether the total is still 1000.

```python
balance = [500, 500]

def transfer(from_acc, to_acc, amount, n):
    for _ in range(n):
        if balance[from_acc] >= amount:
            balance[from_acc] -= amount
            balance[to_acc]   += amount

t1 = threading.Thread(target=transfer, args=(0, 1, 1, 50_000))
t2 = threading.Thread(target=transfer, args=(1, 0, 1, 50_000))
t1.start(); t2.start()
t1.join(); t2.join()

print("Total:", sum(balance), "(should be 1000)")
```

Run it. Is the total preserved?

The systemic point: when concurrency meets state, determinism breaks--
and the consequences are not just wrong answers but *invisible corruption*.


### Part 6 - Introduce Order Without Naming It

Now introduce a small structure:
- It can be held by at most one thread at a time.
- Any thread that wants to proceed must first acquire it.
- A thread that cannot acquire it waits.
- When done, the holder releases it, allowing one waiting thread to proceed.

You still do not call it anything. You call it a *gate*.

```python
import threading

gate = threading.Lock()
counter = 0

def increment(n):
    global counter
    for _ in range(n):
        gate.acquire()
        counter += 1
        gate.release()

t1 = threading.Thread(target=increment, args=(100_000,))
t2 = threading.Thread(target=increment, args=(100_000,))
t1.start(); t2.start()
t1.join(); t2.join()

print(counter)
```

Run it. Is the result now always 200,000?

You have restored determinism. But you used something new to do it.


### Part 7 - Observe the Emergence

Now run both versions and compare:

| Scenario               | Result                  | Deterministic? |
|------------------------|-------------------------|----------------|
| Two threads, no gate   | Varies, often < 200,000 | No             |
| Two threads, with gate | Always 200,000          | Yes            |
| One thread, no gate    | Always 200,000          | Yes            |

The gate restores the property that was lost when concurrency met state.

This is the moment the equation becomes real:
```
Concurrency + State + Determinism  ->  Synchronisation
```

Not as a mechanism to memorise. As an *inevitability*.

If you want concurrency (you do--it is how you use hardware efficiently),
and you have shared mutable state (you often do), and you require determinism
(you always do, for correctness), then you are forced to invent synchronisation.
There is no other option.


### Part 8 - The Cost of the Solution

Synchronisation restores determinism, but it is not free.
Observe what you gave up:

- *Performance*: threads now wait. Parallelism is reduced.
- *Scalability*: more threads competing for the gate means more waiting.
- *Complexity*: you must decide what is protected, and by which gate.
- *New failure modes*: two threads each holding a gate the other needs--
  neither can proceed. This is called *deadlock*.

Run a timing comparison:

```python
import time

def timed(fn, label):
    start = time.perf_counter()
    fn()
    elapsed = time.perf_counter() - start
    print(f"{label}: {elapsed:.3f}s")
```

Measure the gated version against a single-threaded version.
Is the gated version faster? Why or why not?

Synchronisation is the cost you pay to preserve determinism under concurrency.
The design question is never "should we synchronise?"--it is
"what is the minimum synchronisation required?"


### Part 9 - Reflection Questions

Answer in writing:

1. Why does concurrency alone not break determinism?
2. Why does state alone not break determinism?
3. Why does their combination break it?
4. Why does synchronisation restore determinism rather than merely reduce the problem?
5. Why does synchronisation reduce concurrency, and what does that tell you about the
   relationship between concurrency and determinism?
6. Can you think of a system design that avoids synchronisation entirely?
   What would it require?

If you can answer these, you understand synchronisation at a systemic level.
Not as a feature. As an inevitability created by deeper forces.

Now. Rename your "gate" to "lock"--or "mutex", or "semaphore", or "monitor".
At that point, you are not learning what synchronisation is.
You are recognising what you already built.
