
## Project: From State, Time, and Concurrency to Consistency

You already understand three systemic forces:
- *State*: a system's configuration at a given moment--the data it holds.
- *Time*: operations happen at moments; state changes over time.
- *Concurrency*: multiple actors read and write simultaneously.

In this project, you will discover that when multiple actors interact with
shared state across time, a new and unavoidable question arises:
*which version of the state is correct?*

The answer to that question requires a model. That model is:
- *Consistency*.

The equation you will derive is:
```
State + Time + Concurrency  ->  Consistency
```
Your task is not to start from "consistency" as a given solution, but to
*reconstruct why you are forced to choose a consistency model* the moment
state is shared across time by concurrent actors.

This is a design discovery exercise, not a memorisation one.


### Part 1 - A Thought Experiment: One Actor, No Problem

Imagine a bank account with a balance of 1000.
One person makes deposits and withdrawals, one at a time.
The account is always in a known state. Every operation is ordered.
The balance at any moment is unambiguous.

Now introduce a second person--a partner--who also has access to the account.
They use a different branch, a different device, a different interface.

Both partners check the balance at the same moment.
Both see 1000.
Both decide to withdraw 800.

What is the balance after both withdrawals complete?


### Part 2 - Discovering the Problem

If both withdrawals succeed, the balance is -600.
If only one succeeds, the balance is 200.
The outcome depends on *timing and ordering*--not on the intentions of either actor.

This is not a bug in either actor's logic. Each followed the rules correctly.
The problem is that the system has no *shared truth* about what the state is
at any given moment, across all actors, across time.

Model it:

```python
import threading, time

balance = 1000

def withdraw(amount, actor, delay):
    global balance
    current = balance
    print(f"{actor}: sees balance = {current}")
    time.sleep(delay)
    if current >= amount:
        balance = current - amount
        print(f"{actor}: withdraws {amount}, new balance = {balance}")
    else:
        print(f"{actor}: insufficient funds")

t1 = threading.Thread(target=withdraw, args=(800, "Alice", 0.01))
t2 = threading.Thread(target=withdraw, args=(800, "Bob",   0.00))
t1.start(); t2.start()
t1.join(); t2.join()
print(f"Final balance: {balance}")
```

Run it. What happens? Does the balance go negative?

Both actors read *consistent* state at the moment they read it.
The inconsistency emerges from the *gap between reading and writing*,
combined with concurrent access.


### Part 3 - Why Time Makes It Worse

The problem is not merely concurrency. It is concurrency *across time*.

A read and a write are not instantaneous. Between the moment Alice reads
the balance and the moment she writes the new value, time passes.
Bob can act in that interval.

In a distributed system--where actors are on different machines, connected
by a network--that interval can be substantial. Clocks on different machines
do not agree perfectly. Messages take unpredictable time to arrive.

The question "what is the current state?" has no single answer when
state is spread across machines and time has elapsed since the last update.

```python
import random

def simulate_distributed_read(actor, propagation_delay_ms):
    time.sleep(propagation_delay_ms / 1000)
    return balance

print("What different actors see at roughly the same moment:")
for actor, delay in [("Alice", 0), ("Bob", 5), ("Carol", 12)]:
    seen = simulate_distributed_read(actor, delay)
    print(f"  {actor} (delay {delay:>2} ms): balance = {seen}")
```

Each actor sees a version of the state. None of them is necessarily wrong.
All of them may be out of date. The question is: how out of date is acceptable?


### Part 4 - Your Task: Define What "Correct" Means

Before designing any solution, you must decide what correctness means.

There are at least three different answers, each valid in different contexts:

*Strong consistency*: every read sees the most recent write. No actor ever
sees stale data. Feels like one single machine. Expensive to achieve across
multiple machines.

*Eventual consistency*: if no new writes occur, all actors will eventually
see the same value. Reads may be stale for a period. Cheaper and faster
to achieve.

*No consistency guarantee*: actors may see different values indefinitely.
Essentially no model at all. Valid for some caches and analytics systems.

```python
def check_consistency(reads, writes, model):
    if model == "strong":
        latest_write = writes[-1] if writes else None
        return all(r == latest_write for r in reads)
    elif model == "eventual":
        return reads[-1] == writes[-1] if reads and writes else True
    elif model == "none":
        return True

writes = [1000, 200]   # initial, then withdrawal
reads  = [1000, 1000, 200]   # Alice, Bob (stale), Carol (fresh)

for model in ["strong", "eventual", "none"]:
    ok = check_consistency(reads, writes, model)
    print(f"  {model:<10}: consistent = {ok}")
```

Observe: what is consistent under one model is inconsistent under another.
The model does not describe what the system *does*. It describes what the
system *promises*.


### Part 5 - Introduce Order Without Naming It

To achieve strong consistency, you must ensure that all actors see the
same ordering of writes. That requires serialising access--ensuring that
operations happen one at a time, even if actors are concurrent.

You still do not call this "consistency". You call it *agreeing on order*.

```python
import threading

balance_lock = threading.Lock()
balance      = 1000

def safe_withdraw(amount, actor):
    global balance
    with balance_lock:
        if balance >= amount:
            balance -= amount
            print(f"{actor}: withdrew {amount}, balance now {balance}")
        else:
            print(f"{actor}: refused -- insufficient funds (balance={balance})")

t1 = threading.Thread(target=safe_withdraw, args=(800, "Alice"))
t2 = threading.Thread(target=safe_withdraw, args=(800, "Bob"))
t1.start(); t2.start()
t1.join(); t2.join()
print(f"Final balance: {balance}")
```

Now run it. Only one withdrawal succeeds. The other is correctly refused.

Strong consistency achieved. But you serialised all access. What did you give up?


### Part 6 - The Trade-Off Becomes Visible

Strong consistency has a cost. Model it:

```python
import time

def throughput(n_operations, with_lock, work_ms=1):
    lock = threading.Lock() if with_lock else None
    results = []

    def op():
        if lock:
            with lock:
                time.sleep(work_ms / 1000)
        else:
            time.sleep(work_ms / 1000)
        results.append(1)

    threads = [threading.Thread(target=op) for _ in range(n_operations)]
    start = time.perf_counter()
    for t in threads: t.start()
    for t in threads: t.join()
    elapsed = time.perf_counter() - start
    return len(results) / elapsed

for locked in [False, True]:
    tp = throughput(50, with_lock=locked)
    label = "Consistent (locked)" if locked else "Inconsistent (no lock)"
    print(f"  {label}: {tp:.1f} ops/sec")
```

Observe: locking reduces throughput. The more actors compete, the worse it gets.

This is the fundamental tension: strong consistency costs throughput.
Eventual consistency recovers throughput but allows temporary divergence.
You cannot have both simultaneously. This is not a bug. It is physics.


### Part 7 - Observe the Emergence

The full picture:

| Model    | Guarantee                    | Throughput       | Use case           |
|----------|------------------------------|------------------|--------------------|
| Strong   | Every read sees latest write | Low (serialised) | Banking, inventory |
| Eventual | All reads converge over time | High (parallel)  | Social feeds, DNS  |
| None     | No guarantee                 | Maximum          | Caches, analytics  |

This is the moment the equation becomes real:
```
State + Time + Concurrency  ->  Consistency
```

Not as a database property. As an *inevitability*.

The moment state is shared, time passes between reads and writes, and
multiple actors act concurrently--you have already made a consistency choice.
The only question is whether you made it deliberately.

A system with no explicit consistency model is a system that chose the
*none* model by default, often without realising it.


### Part 8 - Reflection Questions

Answer in writing:

1. Why does the problem disappear with a single actor?
2. Why does the problem disappear with a single point in time?
3. Why does the problem disappear without shared state?
4. What is the cost of strong consistency at scale?
5. Why is eventual consistency acceptable for some systems but catastrophic for others?
6. The CAP theorem states that a distributed system cannot simultaneously guarantee
   Consistency, Availability, and Partition Tolerance. Which two does a bank choose?
   Which two does a social media feed choose? Why?

If you can answer these, you understand consistency at a systemic level.
Not as a database configuration option. As a necessity created by deeper forces.

Now. Rename your "agreeing on order" to a *consistency model*--
and your lock-based solution to *serialisable isolation*.
At that point, you are not learning what consistency is.
You are recognising what you already built.
