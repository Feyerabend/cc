
## Throughput

Throughput is the rate at which a system completes useful work: requests per second, bytes per
second, transactions per hour. It is the answer to the question "how much does this system
accomplish?" where latency answers "how long does one operation take?" The two are related but
measure fundamentally different things, and optimising for one often harms the other.

Throughput is ultimately what determines a system's capacity. A system that serves 10,000
requests per second can handle 10,000 concurrent users at a given activity level. A system
that serves 100 requests per second under the same conditions cannot. When a system can no
longer keep up with the incoming rate of work, it queues requests, which increases latency,
which eventually causes failures. Understanding throughput means understanding the ceiling
above which a system begins to degrade.


### Throughput vs. Latency

The distinction between throughput and latency is one of the most important and most frequently
blurred in system design. A concrete analogy: a highway can carry many cars per hour (throughput)
even if the journey from one end to the other takes 45 minutes (latency). Widening the highway
adds lanes and increases throughput. Building a faster road decreases latency. These are different
improvements that require different interventions.

In computing:
- *Latency* is the time from the start of one operation to its completion.
- *Throughput* is the number of operations completed per unit time.

A system can have low latency and low throughput (a fast single-user desktop app), high latency
and high throughput (a batch processing pipeline that takes hours but processes terabytes), or
many other combinations. The goal depends on the use case.

*Little's Law* gives the mathematical relationship between the two. In a stable system:

```
L = λ × W
```

Where L is the average number of requests in the system (queue + in service), λ is the arrival
rate (throughput), and W is the average time a request spends in the system (latency). If latency
doubles without throughput decreasing, the queue depth doubles--and if the queue is bounded, requests
start being dropped. Little's Law makes the tension concrete: you cannot hold all three of L, λ,
and W constant if any one of them changes.


### Goodput: Useful vs. Total Work

Throughput measures everything the system does. *Goodput* measures only the useful part--the
work that results in correct, valuable output. The distinction matters in several contexts:

- *Networks:* A link carrying 1 Gbps of traffic may be retransmitting 30% of packets due to
  errors. Goodput is 700 Mbps. The retransmissions cost bandwidth without delivering value.
- *Databases:* A system executing 1,000 transactions per second where 200 are aborted and
  retried due to conflicts has a goodput of 800 TPS.
- *CPUs:* A processor that stalls 40% of cycles waiting for memory is executing at 60% goodput.
  The clock rate does not reflect useful work done.

Optimising throughput without attending to goodput can be misleading. A system can appear to
be busy--high CPU, high network utilisation--while actually accomplishing very little.


### Bottlenecks and the Constraint

Throughput in any pipeline is bounded by its slowest stage--the bottleneck. This is sometimes
called the *Theory of Constraints* in manufacturing, and it applies directly to computing:
adding resources to non-bottleneck stages does not improve throughput. The only lever that
moves the ceiling is addressing the bottleneck.

*Amdahl's Law* formalises this for parallel systems. If a fraction f of a computation can be
parallelised and the rest is sequential, the maximum speedup from using N parallel processors is:

```
Speedup = 1 / ((1 - f) + f/N)
```

As N → ∞, speedup → 1/(1-f). If 10% of the work is sequential, the maximum possible speedup
is 10x, no matter how many processors you add. The sequential fraction is the throughput ceiling.

Practical implications:
- A single-threaded lock protecting a critical section becomes the throughput ceiling in
  a multi-threaded system. No amount of additional threads helps.
- A single database that all services write to becomes the throughput ceiling of the
  distributed system that depends on it.
- A slow serialisation step becomes the throughput ceiling of a high-speed network connection.

Finding the bottleneck is the first task in any throughput investigation. The tools are:
resource utilisation metrics (which component is at 100%?), queueing depth (where are
requests accumulating?), and profiling (where does time go within the bottleneck?).


### Throughput at Different Layers

Throughput is a meaningful measure at every layer of a computing system.

#### Network Throughput

Network throughput is the rate at which data traverses a link or path, measured in bits per
second. It is bounded by physical bandwidth (the capacity of the link), by protocol overhead
(headers, acknowledgements, retransmissions), and by the receiver's ability to process incoming
data.

TCP throughput is additionally constrained by the *bandwidth-delay product*: the amount of
data that can be "in flight" on the network at once. A long-latency link (cross-continental)
with high bandwidth requires a large TCP window to keep the pipe full. If the window is smaller
than the bandwidth-delay product, the sender must wait for acknowledgements before sending more,
and throughput falls well below the link's capacity.

#### Disk Throughput

Disk throughput measures bytes read or written per second. It differs significantly from disk
*latency* (time to access one location). A spinning disk may have 10 ms seek latency but 150
MB/s sequential throughput: once the head is positioned, it reads quickly. An SSD may have
0.1 ms latency and 500 MB/s sequential throughput, but random small reads are a different
story--the throughput of many small random reads is often far below the sequential rate because
each read incurs controller overhead.

Database performance is often limited by disk throughput in write-heavy workloads. Techniques
like *write coalescing* (grouping small writes into larger ones), *write-ahead logging* (turning
random writes into sequential ones), and *log-structured merge-trees* (LSM trees) exist to
convert random-write patterns into sequential ones, improving throughput.

#### CPU Throughput (Instructions Per Second)

At the hardware level, throughput is measured in instructions per second (IPS) or floating-point
operations per second (FLOPS). Modern CPUs execute multiple instructions per clock cycle through
superscalar execution, out-of-order execution, and pipelining. However, the theoretical peak
throughput is rarely achieved because of:
- Cache misses that stall the pipeline.
- Branch mispredictions that flush and restart the pipeline.
- Data dependencies that prevent independent instruction issue.

High-throughput numerical computing (scientific simulation, machine learning) uses SIMD
(Single Instruction, Multiple Data) instructions to perform the same operation on many data
elements simultaneously, multiplying throughput for vectorisable workloads.

#### Application Throughput

At the application level, throughput is measured in the units of work the application performs:
requests per second for a web service, documents indexed per hour for a search engine, messages
processed per second for a message queue consumer.

Application throughput is limited by the compound effect of all lower-level bottlenecks. A web
service that serialises requests through a single database connection, a mutex protecting a shared
cache, or a slow external API call will never achieve high throughput regardless of how much
hardware it runs on.


### Throughput and Concurrency

The primary tool for increasing application throughput is concurrency: doing multiple things at once.
If each request takes 10 ms and is handled by one thread, a single thread achieves 100 requests per
second. Ten threads can achieve 1,000 requests per second--provided there is no shared bottleneck
between them.

The critical qualifier is *independent work*. Concurrency improves throughput only where operations
do not contend for the same resource. A system where every request must acquire a global lock is
effectively single-threaded at that lock. This is why lock contention is one of the primary
throughput killers in concurrent systems, and why lock-free data structures, connection pools,
and sharding exist.

Asynchronous I/O is a particularly effective throughput technique for I/O-bound workloads.
If a request spends 8 of its 10 ms waiting for a database response, a single thread can
interleave hundreds of such requests: send the query, switch to another request while waiting,
return when the response arrives. The thread achieves high throughput not by doing work faster
but by never sitting idle.


### Saturation, Queues, and Degradation

As arrival rate approaches throughput capacity, queue depth increases and latency rises. This
is queuing theory in practice. At 50% utilisation, queues are short and latency is close to
service time. At 90% utilisation, queues grow significantly. At 100% utilisation, queues grow
without bound--the system is saturated and latency climbs until requests time out or are dropped.

The characteristic shape of this relationship--latency stable at low utilisation, then rising
sharply near saturation--means that operating near 100% throughput capacity is dangerous.
A small burst of extra traffic pushes the system over the saturation point, and recovery can
be slow because the queue must drain before latency returns to normal.

Well-designed systems operate with headroom: 60-70% utilisation is a common target, leaving
capacity for bursts and degraded dependencies. *Backpressure* is the mechanism by which a
saturated component signals upstream components to slow down--preventing queue overflow by
making the producer aware of the consumer's state.

*Throughput is the ceiling. Latency is what you feel when you approach it.*
