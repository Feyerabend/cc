
## Project: From Latency and Cost to Cache via Locality

You already understand two systemic forces:
- *Latency*: some operations take much longer than others.
- *Cost*: time, energy, memory, hardware, and complexity are limited resources.

In this project, you will discover a third force that naturally
emerges when systems try to balance latency and cost:
- *Locality*.
This has so far been missing from the list of systemic concepts.

From the three together, you will derive:
```
Latency + Cost + Locality -> Cache
```
Your task is not to start from "cache" as a given solution, but to
*reconstruct why cache must exist* if you try to design a fast
and economical system.

This is a design discovery exercise, not a memorisation one.



### Part 1 - A Thought Experiment: One Memory vs Two Memories

Imagine a machine with only one kind of memory:
- Every access takes 100 time units.
- It is cheap.
- It is large.

You run a program that performs 1 million memory accesses.
Total time: 1,000,000 x 100 = 100,000,000 time units.

Now imagine a second kind of memory:
- Access time: 1 time unit
- Cost: 100x more expensive
- Size: very limited

You cannot replace the large memory entirely.
It really would be too expensive.
So you are forced into a design with:
- One large, slow, cheap memory
- One small, fast, expensive memory

At this point, you have latency and cost. But nothing yet tells
you *what to place* in the fast memory.

That missing concept is *locality*.

At this point, you are expected to pause and explore it. Let your thinking wander,
form hypotheses, test ideas, and, if helpful, use tools such as LLMs to deepen your
understanding. Your goal is to uncover what locality really means in practice,
how it appears in program behaviour, and why it matters so strongly when latency
and cost are already present.


### Part 2 - Discovering Locality

Run this mental experiment:
Suppose your program accesses memory addresses in this pattern:
```
5, 5, 5, 5, 5, 5, 5, 5, 5, 5
```
Would it make sense to keep address `5` in fast memory?
Yes. Almost all accesses benefit.

Now suppose the pattern is:
```
1, 873492, 55, 9123, 400001, 7, 88, 91231, 3, 700002
```
Would fast memory help? Almost not at all.

So something about *how programs access data* matters.

This observation leads you to locality:
> Programs tend to reuse the same data and access nearby data in clusters.

There are two main forms:
- *Temporal locality:*
  If something was used recently, it is likely to be used again soon.
- *Spatial locality:*
  If something is used, nearby data is likely to be used soon.

Locality is not a hardware property.  
It is a property of *program behaviour*.


### Part 3 - Why Cache Is Inevitable

Now combine the three forces:
1. *Latency:*
   Fast memory is dramatically faster than slow memory.
2. *Cost:*
   Fast memory is dramatically more expensive than slow memory.
3. *Locality:*
   Programs repeatedly touch small working sets of data.

Conclusion: You should keep *only the working set* in fast memory.
That structure is called a *cache*. You have not defined cache as
a concept yet. You have *derived* it as a necessity.

In that way cache is the only rational architecture that satisfies all
three constraints.


### Part 4 - Your Task: Build Locality Before You Build Cache

Before you write any cache, you must first *observe locality*.
Write a small program that generates access patterns.
Example patterns:
- High temporal locality
- High spatial locality
- No locality (random)

```python
import random

def temporal_locality(n):
    return [5 for _ in range(n)]

def spatial_locality(n):
    base = random.randint(0, 1000)
    return [base + i for i in range(n)]

def no_locality(n):
    return [random.randint(0, 1_000_000) for _ in range(n)]
```
Print (or plot) small sequences.
Convince yourself that these patterns are structurally different.
In this step you are observing locality before any caching exists.


### Part 5 - Simulate Latency and Cost

Now define a memory model:
```python
SLOW_LATENCY = 100
FAST_LATENCY = 1
```
You start with no cache:
```python
def access_no_cache(address):
    return SLOW_LATENCY
```
Total execution time:
```python
def run(pattern):
    time = 0
    for addr in pattern:
        time += access_no_cache(addr)
    return time
```
Run all three patterns. They all cost the same time.
Locality currently has no effect. That is your baseline.



### Part 6 - Introduce a Cache Without Naming It

Now you introduce a small, expensive structure:
- Limited size
- Much faster access
- Stores recently used addresses

You still do not call it a "cache". You call it fast memory.
```python
FAST_MEMORY_SIZE = 8
fast_memory = []
```
Access rule:
1. If address is in fast memory -> cost FAST_LATENCY
2. Otherwise -> cost SLOW_LATENCY and insert it into fast memory
3. If fast memory is full -> evict something

You must decide:
- What replacement policy to use?
- FIFO (First In, First Out)?
- LRU (Least Recently Used)?
- Random?

You are now designing a cache without being told to.


### Part 7 - Observe the Emergence

Run your simulation again:
- With temporal locality
- With spatial locality
- With no locality

You should see:

| Pattern           | Without Fast Memory | With Fast Memory |
|-------------------|---------------------|------------------|
| Temporal locality | Slow	              | Extremely fast   |
| Spatial locality  | Slow                | Very fast        |
| No locality       | Slow                | Almost unchanged |

This is the moment where the equation becomes real:
```
Latency + Cost + Locality  ->  Cache
```
Not as theory. More of an unavoidable design consequence.


### Part 8 - Reflection Questions

Answer in writing:
1. Why does cache fail when locality is absent?
2. Why can't we make all memory fast?
3. Why does cache introduce unpredictability in timing?
4. Why does cache increase system complexity?
5. Why does cache leak through abstraction into application performance?

If you can answer these, you understand caching at a systemic level.
Not as a feature. As a necessity created by deeper forces.

Now. Rename your "fast memory" to "cache".
At that point, you are not learning what a cache is.
You are recognising what you already built.


