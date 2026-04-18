
## Project: From Scalability, Cost, and Latency to Distributed Systems

You already understand three systemic forces:
- *Scalability*: a system must handle growing amounts of work or data.
- *Cost*: memory, compute, bandwidth, and hardware are limited resources.
- *Latency*: the delay between cause and effect matters--to users, to correctness, to throughput.

In this project, you will discover that when these three forces push hard enough,
they leave only one possible architectural response:
- *Distribution*.

The equation you will derive is:
```
Scalability + Cost + Latency  ->  Distributed Systems
```
Your task is not to start from "distributed systems" as a given solution, but to
*reconstruct why distribution must happen* when a single machine is no longer enough.

This is a design discovery exercise, not a memorisation one.


### Part 1 - A Thought Experiment: One Machine, No Problem

Imagine a web service running on a single machine.
It receives requests, processes them, and returns responses.
At low load, everything works. Latency is low. Cost is fixed. Life is simple.

Now traffic doubles. Then doubles again.

You have three levers on a single machine:
- Add more CPU cores.
- Add more RAM.
- Add faster storage.

Each lever helps. Each lever has a ceiling.
At some point, no single machine exists that can satisfy your requirements--
or if it does, it costs more than any reasonable budget allows.

You have hit the wall where Scalability and Cost collide.


### Part 2 - Discovering the Wall

Run a mental experiment. Your service processes 1,000 requests per second
on a machine costing X per month. Traffic grows:

| Requests/sec | Single machine cost | Feasible? |
|--------------|---------------------|-----------|
| 1,000        | X                   | Yes.      |
| 10,000       | ~10X                | Probably  |
| 100,000      | ~100X               | Unlikely  |
| 1,000,000    | Does not exist      | No        |

The wall is not just cost. It is physical.
Memory bandwidth, bus speed, and power dissipation all have hard limits.
The fastest single machine you can buy today cannot serve a billion users.

Now model it simply:

```python
MACHINE_CAPACITY = 10_000   # requests per second
MACHINE_COST     = 1_000    # arbitrary units per month

def single_machine_cost(load):
    if load <= MACHINE_CAPACITY:
        return MACHINE_COST
    else:
        return float('inf')   # cannot be done

for load in [1_000, 5_000, 10_000, 50_000]:
    print(f"Load {load:>6}: cost = {single_machine_cost(load)}")
```

The `inf` is the wall. Something must change.


### Part 3 - The Naive Fix: Buy a Bigger Machine

Before distributing, consider the obvious alternative: scale *up*.
Replace the machine with one twice as powerful.

This is called *vertical scaling*. It works--up to a point.

```python
def vertical_scale_cost(load, scale_factor):
    capacity = MACHINE_CAPACITY * scale_factor
    cost     = MACHINE_COST * (scale_factor ** 1.5)   # bigger machines cost superlinearly
    if load <= capacity:
        return cost
    else:
        return float('inf')

for sf in [1, 2, 4, 8, 16]:
    cost = vertical_scale_cost(50_000, sf)
    print(f"Scale x{sf:>2}: cost = {cost:.0f}")
```

Observe: cost grows faster than capacity. At some point vertical scaling
becomes economically irrational--and eventually physically impossible.

So you are forced to consider the alternative: use many smaller machines.
This is *horizontal scaling*. But now you have a new problem.


### Part 4 - The Latency Problem of Many Machines

If your data lives on one machine and your compute lives on another,
every operation now crosses a network.

A memory access on a single machine: ~100 nanoseconds.
A network round-trip between two machines: ~500,000 nanoseconds.

That is a five-thousand-fold increase in latency--for the same logical operation.

```python
MEMORY_LATENCY  = 100          # nanoseconds, same machine
NETWORK_LATENCY = 500_000      # nanoseconds, different machine

print(f"Memory:  {MEMORY_LATENCY} ns")
print(f"Network: {NETWORK_LATENCY} ns")
print(f"Ratio:   {NETWORK_LATENCY // MEMORY_LATENCY}x slower")
```

Distribution solves the scalability and cost problem.
It immediately creates a latency problem.

You cannot escape all three forces simultaneously. You must manage their tension.


### Part 5 - Your Task: Model the Trade-Off

Before designing any distributed system, model the trade-off explicitly.

```python
def total_cost(load, strategy):
    if strategy == "single":
        if load <= MACHINE_CAPACITY:
            return MACHINE_COST, MEMORY_LATENCY
        else:
            return float('inf'), MEMORY_LATENCY

    elif strategy == "distributed":
        n_machines = -(-load // MACHINE_CAPACITY)   # ceiling division
        cost       = n_machines * MACHINE_COST * 0.8  # some economies of scale
        latency    = NETWORK_LATENCY
        return cost, latency

for load in [1_000, 10_000, 100_000, 1_000_000]:
    sc, sl = total_cost(load, "single")
    dc, dl = total_cost(load, "distributed")
    print(f"Load {load:>8}: single cost={sc}, distributed cost={dc:.0f}, latency penalty={dl // sl}x")
```

Observe: at low load, single machine wins on latency. At high load, distribution
wins on cost and feasibility. There is a crossover point.

Find it. That crossover is where distribution becomes *necessary*, not optional.


### Part 6 - Introduce Distribution Without Naming It

Now build the simplest possible multi-machine model.
You have one *coordinator* that receives requests and routes them
to one of several *workers*, each holding part of the data.

You still do not call this "distributed". You call it *spreading the load*.

```python
import random

class Worker:
    def __init__(self, worker_id, data):
        self.worker_id = worker_id
        self.data      = data

    def handle(self, key):
        if key in self.data:
            return self.data[key]
        return None

class Coordinator:
    def __init__(self, workers):
        self.workers = workers

    def route(self, key):
        worker = self.workers[hash(key) % len(self.workers)]
        return worker.handle(key)

workers = [
    Worker(0, {"a": 1, "b": 2}),
    Worker(1, {"c": 3, "d": 4}),
    Worker(2, {"e": 5, "f": 6}),
]
coord = Coordinator(workers)

for key in ["a", "c", "e", "b", "f"]:
    print(f"Key '{key}' -> {coord.route(key)}")
```

You now have:
- Multiple machines (workers), each handling part of the load.
- A coordinator routing requests based on a rule (hash of key).
- No single machine that needs to hold everything.

You have spread the load. You have not yet named what you built.


### Part 7 - Observe What You Gained and Lost

Now stress-test your design. Ask:

1. What happens if one worker goes down?
   - Some keys become unreachable. The system partially fails.

2. What happens if you add a fourth worker?
   - You must re-route some keys. Data must move. This is expensive.

3. What if two requests for the same key arrive at the same time?
   - On different workers, no problem. On the same worker--you are back to the
     synchronisation problem from the previous combination.

4. What is the latency of a request that needs data from two workers?
   - You must make two network calls. Latency compounds.

Record these observations:

| Property            | Single machine       | Spread load             |
|---------------------|----------------------|-------------------------|
| Max load            | Bounded              | Unbounded (add workers) |
| Cost at scale       | Prohibitive          | Linear                  |
| Latency per request | Low                  | Higher                  |
| Failure modes       | One point of failure | Partial failures        |
| Complexity          | Low                  | High                    |

This is the moment the equation becomes real:
```
Scalability + Cost + Latency  ->  Distributed Systems
```

Not as a technology choice. As an *unavoidable consequence* of the three forces.

When you need to scale beyond what one machine can offer, and cost prevents
you from buying a machine large enough, and latency forces you to place
computation near data--you have no architectural choice left but to distribute.


### Part 8 - The New Problems Distribution Creates

Distribution solves the original three forces. It creates three new ones:

- *Partial failure*: a single machine either works or does not.
  In a distributed system, some parts fail while others continue.
  Your system must decide: stop entirely, or proceed with incomplete information?

- *Consistency*: on a single machine, state is in one place.
  Across machines, copies of state can diverge. Which copy is correct?
  This is the consistency problem--and it has no perfect solution.

- *Coordination cost*: the machines must agree on things--which worker owns
  which data, whether a transaction succeeded, what the current time is.
  That agreement itself requires communication, which costs latency.

Each of these is a new systemic concept that distribution *creates*.
You did not have them before. You have them now, as the price of scale.


### Part 9 - Reflection Questions

Answer in writing:

1. Why does scalability alone not force distribution?
2. Why does cost alone not force distribution?
3. What is the precise moment when distribution becomes *necessary* rather than optional?
4. Why does distributing computation increase latency, even though the goal was to improve performance?
5. Why is "just buy a bigger machine" not a long-term strategy?
6. What would a system look like that achieves scalability and low cost without distribution?
   Is such a system possible?

If you can answer these, you understand distributed systems at a systemic level.
Not as a technology. As a necessity created by deeper forces.

Now. Rename your "coordinator and workers" to a *distributed system*.
At that point, you are not learning what distribution is.
You are recognising what you already built.
