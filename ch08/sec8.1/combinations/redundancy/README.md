
## Project: From Fault Tolerance, Scalability, and Resilience to Redundancy

You already understand three systemic forces:
- *Fault Tolerance*: a system must continue operating correctly despite failures.
- *Scalability*: a system grows--more components, more users, more data.
- *Resilience*: a system must degrade gracefully and recover, not just survive.

In this project, you will discover that when these three forces act together,
they converge on a single structural response:
- *Redundancy*.

The equation you will derive is:
```
Fault Tolerance + Scalability + Resilience  ->  Redundancy
```
Your task is not to start from "redundancy" as a given solution, but to
*reconstruct why keeping extra copies is not waste but necessity* when
systems must be both large and reliable.

This is a design discovery exercise, not a memorisation one.


### Part 1 - A Thought Experiment: One Component, One Failure Mode

Imagine a single disk storing your data.
It works reliably--until it does not.
Disks fail. Mechanical parts wear out. Firmware has bugs.
A typical hard disk has a mean time between failures of roughly 3 to 5 years.

If your system has one disk, the probability it fails within a year is
roughly 20-30%. That is not an edge case. It is an expectation.

Model it:

```python
import math

def survival_probability(mtbf_years, years):
    rate = 1 / mtbf_years
    return math.exp(-rate * years)

mtbf = 4   # years

print("Single component survival over time:")
for y in [0.5, 1, 2, 3, 5]:
    p = survival_probability(mtbf, y)
    print(f"  {y:.1f} years: {p:.1%} chance of survival")
```

A single component is a liability. Now ask: what does scalability do to this?


### Part 2 - Discovering the Scalability Trap

A system with one disk has one failure mode.
A system with one thousand disks has one thousand failure modes--any one of
which can bring the system down.

As systems scale, the probability of *some* failure approaches certainty.

```python
def system_survival(n_components, mtbf_years, years):
    p_single = survival_probability(mtbf_years, years)
    return p_single ** n_components

print("\nSystem survival at 1 year (MTBF = 4 years):")
for n in [1, 10, 100, 1_000, 10_000]:
    p = system_survival(n, mtbf=4, years=1)
    print(f"  {n:>6} components: {p:.6%} survival")
```

Observe: at 10,000 components, the system almost never survives a full year
without at least one failure.

This is the scalability trap: the system must grow to serve users, but
every component added increases the probability of failure. Fault tolerance
cannot be achieved by building more reliable parts--you run out of
improvement headroom. Something structural must change.


### Part 3 - Why Resilience Demands More Than Tolerance

Fault tolerance says: survive the failure.
Resilience says: survive it gracefully--and recover.

These are different. A system that freezes when one disk fails and requires
manual intervention to restart has fault tolerance of a kind. A system that
automatically detects the failure, routes around it, and begins recovery
without human involvement is resilient.

Resilience demands that the system *knows about* the failure, *has an
alternative*, and can *restore itself*. All three require something extra
to be present--something that was not there before the failure occurred.

That something is what you are about to derive.


### Part 4 - Your Task: Measure the Cost of a Single Point of Failure

A single point of failure (SPOF) is any component whose failure brings the
whole system down. Before designing anything, locate yours.

```python
class Component:
    def __init__(self, name, mtbf_years):
        self.name       = name
        self.mtbf_years = mtbf_years
        self.failed     = False

    def fail_probability(self, years):
        return 1 - survival_probability(self.mtbf_years, years)

components = [
    Component("power supply",   5),
    Component("network switch", 7),
    Component("primary disk",   4),
    Component("CPU",           10),
]

print("Single points of failure (1 year horizon):")
for c in components:
    p = c.fail_probability(1)
    print(f"  {c.name:<20}: {p:.1%} probability of failure")
```

Any component with a non-trivial failure probability is a SPOF if there
is no alternative. Resilience requires an alternative for every SPOF.


### Part 5 - Introduce Extra Copies Without Naming Them

Now add a second disk alongside the first.
Both hold the same data. If one fails, the other continues serving reads.

You still do not call this "redundancy". You call it *having a spare*.

```python
import random

class Disk:
    def __init__(self, disk_id, failure_rate):
        self.disk_id      = disk_id
        self.failure_rate = failure_rate
        self.alive        = True

    def tick(self):
        if self.alive and random.random() < self.failure_rate:
            self.alive = False

    def read(self, key):
        if self.alive:
            return f"data:{key}"
        return None

def simulate(n_disks, failure_rate, ticks):
    disks    = [Disk(i, failure_rate) for i in range(n_disks)]
    failures = 0
    for t in range(ticks):
        for d in disks:
            d.tick()
        if not any(d.read("x") for d in disks):
            failures += 1
    return failures

ticks        = 1_000
failure_rate = 0.005   # 0.5% chance of failure per tick

for n in [1, 2, 3]:
    f = simulate(n, failure_rate, ticks)
    print(f"{n} disk(s): {f} total outage ticks out of {ticks} ({f/ticks:.1%})")
```

Run it. How does the outage rate change as you add disks?

Each additional spare reduces the chance that *all* copies fail simultaneously--
which requires independent failures to coincide.


### Part 6 - Observe the Emergence

Now generalise. Two copies fail together only if both fail in the same window.
That probability is the product of their individual failure probabilities--
a dramatic reduction.

```python
def system_failure_probability(n_copies, p_single_failure):
    return p_single_failure ** n_copies

p = 0.20   # 20% annual failure rate per disk

print("Annual system failure probability:")
for n in [1, 2, 3, 5]:
    pf = system_failure_probability(n, p)
    print(f"  {n} cop{'y' if n==1 else 'ies'}: {pf:.4%}")
```

This is the moment the equation becomes real:
```
Fault Tolerance + Scalability + Resilience  ->  Redundancy
```

Not as a design choice. As an *inevitability*.

When you need fault tolerance (survive failures), and the system must scale
(more components means more failures), and you require resilience (graceful
degradation and automatic recovery), you are forced to keep extra copies.
There is no other structural response.


### Part 7 - The Costs of Redundancy

Redundancy is not free. Observe what you pay:

- *Cost*: two disks cost twice as much. Three cost three times as much.
  At scale, this is significant. The decision is always: how much reliability
  is worth how much cost?

- *Consistency*: if two copies hold the same data and one is written to,
  both must be updated. What if the update reaches one but not the other?
  Now the copies disagree. This is the *consistency problem* you will
  encounter in the consistency combination.

- *Complexity*: the system must detect failures, decide which copy is
  authoritative, manage the spare, and coordinate recovery. All of this
  is new code that did not exist when there was only one copy.

- *False confidence*: redundancy only helps if the failure modes are
  independent. Two disks in the same rack, on the same power circuit,
  with the same firmware version, can fail together. Redundancy must
  be *diverse* to be effective.

```python
def correlated_failure(p_single, correlation):
    p_independent = p_single ** 2
    return p_independent + correlation * p_single * (1 - p_single)

p = 0.20
print("Two-copy failure probability by correlation:")
for corr in [0.0, 0.1, 0.5, 1.0]:
    pf = correlated_failure(p, corr)
    print(f"  Correlation {corr:.1f}: {pf:.4%}")
```

Perfect correlation: two copies are no better than one.


### Part 8 - Reflection Questions

Answer in writing:

1. Why does the failure probability of a system *increase* as you add components?
2. Why does redundancy reduce system failure probability even though it adds more components?
3. What is the difference between fault tolerance and resilience in the context of redundancy?
4. Why must redundant copies be *independent* to be effective?
5. What is the relationship between redundancy and consistency? Why does one create the other?
6. Give three real-world examples of redundancy at different layers of a computing system.

If you can answer these, you understand redundancy at a systemic level.
Not as a storage strategy. As a necessity created by deeper forces.

Now. Rename your "having a spare" to *replication*--or *RAID*, or *clustering*,
depending on what layer you are working at.
At that point, you are not learning what redundancy is.
You are recognising what you already built.
