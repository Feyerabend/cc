
## Project: From Determinism, Time, and Latency to Real-Time Systems

You already understand three systemic forces:
- *Determinism*: the same inputs always produce the same outputs.
- *Time*: operations happen at moments, take durations, and must be ordered.
- *Latency*: the delay between cause and effect--between input and response.

In this project, you will discover that when these three forces must all hold
*simultaneously*, they force a particular kind of system into existence:
- *Real-Time Systems*.

The equation you will derive is:
```
Determinism + Time + Latency  ->  Real-Time Systems
```
Your task is not to start from "real-time" as a given solution, but to
*reconstruct why timing guarantees must be designed in explicitly* when
latency and determinism are both required.

This is a design discovery exercise, not a memorisation one.


### Part 1 - A Thought Experiment: When Late Is Wrong

Most programs treat time as invisible.
A sorting algorithm is correct if it sorts. It does not matter whether it
takes one millisecond or one second. The output is the same either way.

Now consider a different kind of system.

A car's braking system receives a signal from the brake pedal.
It must activate the brakes.
If it activates them in 1 millisecond: safe.
If it activates them in 500 milliseconds: the car has already travelled
several metres further than expected. The response is *wrong*--not because
the computation was incorrect, but because it was *late*.

In this system, a correct answer delivered too late is not a correct answer.
It is a failure.

Time is now part of correctness.


### Part 2 - Discovering the Deadline

The key concept is a *deadline*: a point in time by which a response must
have occurred. Missing a deadline is not a performance issue. It is a
correctness issue--sometimes a safety issue.

Real-time systems are not about being *fast*. They are about being
*predictably on time*.

Consider these three systems:

| System         | Response required    | Late response consequence |
|----------------|----------------------|---------------------------|
| Web search     | "Soon"               | Mildly annoying           |
| Video playback | Every 33 ms (30 fps) | Visible stutter           |
| ABS braking    | Within 10 ms         | Physical danger           |

The distinction is not speed. It is *consequence of lateness*.

Now model a deadline explicitly:

```python
import time

DEADLINE_MS = 10   # milliseconds

def respond(computation_ms):
    start = time.perf_counter()
    time.sleep(computation_ms / 1000)
    elapsed_ms = (time.perf_counter() - start) * 1000
    if elapsed_ms <= DEADLINE_MS:
        print(f"OK:   {elapsed_ms:.2f} ms  (deadline: {DEADLINE_MS} ms)")
    else:
        print(f"MISS: {elapsed_ms:.2f} ms  (deadline: {DEADLINE_MS} ms) -- FAILURE")

for ms in [2, 5, 9, 11, 20]:
    respond(ms)
```

Observe: the system does not degrade gracefully past the deadline.
It fails. The line between "correct" and "incorrect" is a moment in time.


### Part 3 - Why Determinism Becomes Critical

In an ordinary system, non-determinism in timing is an inconvenience.
In a real-time system, it is catastrophic.

Consider a scheduler that sometimes takes 2 ms to dispatch a task,
and sometimes takes 15 ms, depending on what else is running.
On a normal server, this is acceptable variance.
On a braking system with a 10 ms deadline, this means the system
randomly fails.

Non-deterministic latency + hard deadline = unpredictable correctness.

Simulate this:

```python
import random

DEADLINE_MS = 10

def scheduler_delay():
    return random.choice([2, 3, 2, 15, 3, 2, 20, 3])  # ms; occasional spikes

def run_task(n):
    failures = 0
    for _ in range(n):
        delay = scheduler_delay()
        if delay > DEADLINE_MS:
            failures += 1
    return failures

n = 1000
f = run_task(n)
print(f"Failures: {f}/{n} ({100*f/n:.1f}%)")
```

Run it several times. The failure rate varies. You cannot predict it.

This is the core problem: latency without determinism means you cannot
*guarantee* deadline compliance. You can only *hope* for it.


### Part 4 - Your Task: Measure Your Own System's Variance

Before designing anything, measure the latency variance of your own environment.

```python
import time, statistics

def measure_variance(n):
    samples = []
    for _ in range(n):
        start = time.perf_counter()
        x = sum(range(1000))   # a small, fixed computation
        elapsed_us = (time.perf_counter() - start) * 1_000_000
        samples.append(elapsed_us)
    return samples

samples = measure_variance(10_000)
print(f"Mean:   {statistics.mean(samples):.2f} us")
print(f"Stdev:  {statistics.stdev(samples):.2f} us")
print(f"Min:    {min(samples):.2f} us")
print(f"Max:    {max(samples):.2f} us")
```

Observe that even a trivial computation on a general-purpose OS has variance.
The OS scheduler, garbage collector, cache state, and other processes all
introduce jitter you do not control.

This is why general-purpose systems cannot provide real-time guarantees.
Not because they are slow. Because they are *unpredictably* slow.


### Part 5 - The Worst Case Is What Matters

In most systems, you optimise for the *average* case.
In real-time systems, you design for the *worst* case.

A deadline is not "usually met". It is either *guaranteed* or it is not.

Define worst-case execution time (WCET) as the maximum time a task can
ever take, across all possible inputs and system states:

```python
def wcet(task_fn, inputs):
    worst = 0
    for inp in inputs:
        start   = time.perf_counter()
        task_fn(inp)
        elapsed = (time.perf_counter() - start) * 1000
        if elapsed > worst:
            worst = elapsed
    return worst

def example_task(n):
    return sum(range(n))

test_inputs = list(range(0, 10_000, 100))
print(f"WCET: {wcet(example_task, test_inputs):.3f} ms")
```

The system is schedulable only if, for every task, WCET <= deadline.

If WCET is unknown or unbounded--as it is in most general-purpose code--
you cannot make a guarantee. You have no real-time system. You have a
system that *usually* responds in time.


### Part 6 - Introduce Guarantees Without Naming Them

Now build the simplest structure that provides a timing guarantee.

You have a set of tasks. Each has a deadline. You must decide in what
order to run them so that as many deadlines as possible are met--
ideally, all of them.

A simple rule: always run the task whose deadline is soonest.
You still do not call this anything. You call it *urgent-first*.

```python
import heapq, time

def run_urgent_first(tasks):
    heap = []
    for name, deadline_ms, duration_ms in tasks:
        heapq.heappush(heap, (deadline_ms, name, duration_ms))

    clock = 0
    while heap:
        deadline, name, duration = heapq.heappop(heap)
        clock += duration
        status = "OK  " if clock <= deadline else "MISS"
        print(f"{status} | task={name:10} | finish={clock:5} ms | deadline={deadline:5} ms")

tasks = [
    ("brake",   10,  3),
    ("display", 33, 10),
    ("log",    100, 20),
    ("sensor",  10,  2),
]

run_urgent_first(tasks)
```

Run it. Do all deadlines get met? What happens if you add a task that
takes longer than its deadline? What happens if two urgent tasks compete?

You are now scheduling for time, not for throughput.


### Part 7 - Observe the Emergence

Now compare two scheduling strategies on the same task set:

```python
def run_fifo(tasks):
    clock = 0
    for name, deadline_ms, duration_ms in tasks:
        clock += duration_ms
        status = "OK  " if clock <= deadline_ms else "MISS"
        print(f"{status} | task={name:10} | finish={clock:5} ms | deadline={deadline_ms:5} ms")

print("=== FIFO ===")
run_fifo(tasks)
print()
print("=== Urgent-First ===")
run_urgent_first(tasks)
```

| Strategy     | Deadline misses  | Predictability |
|--------------|------------------|----------------|
| FIFO         | Depends on order | Low            |
| Urgent-first | Minimised        | Higher         |

This is the moment the equation becomes real:
```
Determinism + Time + Latency  ->  Real-Time Systems
```

Not as a category of systems. As an *inevitability*.

When latency has a hard bound that must not be exceeded, and that bound
must hold deterministically--not on average, not usually, but always--
you are forced to design a system that treats time as a first-class
correctness criterion. That structure is a real-time system.


### Part 8 - The Cost of the Guarantee

Real-time guarantees are not free. Observe what you gave up:

- *Throughput*: urgent-first scheduling may leave lower-priority tasks
  starved, reducing overall work completed.
- *Flexibility*: you cannot use features that have unbounded latency--
  garbage collection, dynamic memory allocation, general OS scheduling.
- *Complexity*: you must analyse every task's worst-case execution time,
  which is difficult and sometimes impossible for general-purpose code.
- *Generality*: a real-time system is designed for a specific workload.
  Changing the tasks may invalidate all guarantees.

The tighter the deadline, the more of the system must be sacrificed
to meet it. Hard real-time systems (aircraft, pacemakers) give up almost
all general-purpose flexibility. Soft real-time systems (video, audio)
accept occasional misses in exchange for usability.


### Part 9 - Reflection Questions

Answer in writing:

1. Why is "fast on average" not good enough for a real-time system?
2. Why does non-determinism in latency make deadline guarantees impossible?
3. What is the relationship between worst-case execution time and scheduling?
4. Why do real-time systems typically avoid garbage collection and dynamic memory?
5. What is the difference between a *hard* and a *soft* real-time system?
   Give one example of each.
6. Can a general-purpose operating system ever provide real-time guarantees?
   Under what conditions?

If you can answer these, you understand real-time systems at a systemic level.
Not as a category of hardware. As a necessity created by deeper forces.

Now. Rename your "urgent-first scheduler" to *Earliest Deadline First (EDF)*--
one of the classical real-time scheduling algorithms.
At that point, you are not learning what real-time systems are.
You are recognising what you already built.
