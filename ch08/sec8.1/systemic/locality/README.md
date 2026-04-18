
## Locality

Locality is a property of *programme behaviour*, not of hardware. It describes the tendency of programmes
to access a small, repeatedly used subset of their data and instructions over any given time window. It is
one of the most consequential empirical observations in the history of computing: without it, caches would
be useless, virtual memory would be impractical, and most of the performance gap between fast and slow
storage would be unmanageable.

Locality does not appear in the specification of an algorithm. It emerges from the way real programmes
actually execute--loops, data structures traversed in order, functions called repeatedly. It is, in a
precise sense, the bridge between the theoretical model of a programme and the physical constraints of
the machine that runs it.


### Two Forms of Locality

*Temporal locality* is the observation that if a memory location was accessed recently, it is likely
to be accessed again soon. A loop variable read on every iteration is the canonical example: the same
address is touched thousands of times in rapid succession. A function called repeatedly from a hot
path exhibits temporal locality in the instruction stream as well as in any data it touches.

*Spatial locality* is the observation that if a memory location is accessed, nearby locations are
likely to be accessed soon. Iterating through an array in order is the canonical example: after
accessing element i, element i+1 is almost certainly next. A struct whose fields are accessed
together in a tight loop exhibits spatial locality because its fields are contiguous in memory.

These two forms reinforce each other. A programme that processes an array in a loop exhibits both:
temporal locality over the loop control variable, and spatial locality over the array elements.
Together they define a *working set*--the set of pages or cache lines that a programme actively
uses during a phase of execution.


### The Working Set

The working set concept, introduced by Peter Denning in 1968, formalises the intuition behind locality.
At any moment, a programme has a working set W(t, τ): the set of distinct memory pages it has
referenced during the time window ending at t with length τ.

If the working set fits in fast memory (cache or RAM), most accesses are fast. If the working set
exceeds the available fast memory, the system begins evicting pages it will need again soon--a
condition called *thrashing*. In a thrashing system, the time spent moving data between fast and
slow memory dominates, and the programme barely makes forward progress.

This makes working set size a critical design parameter. A programme whose working set exceeds
the L3 cache will pay many cache misses. A programme whose working set exceeds available RAM
will thrash the disk. Understanding locality means understanding where these thresholds lie
and designing data layouts and access patterns to stay below them.


### Where Locality Appears

#### CPU Caches

The cache hierarchy (L1, L2, L3) exists entirely because of locality. When the CPU fetches a
cache line (typically 64 bytes), it bets that nearby bytes will be needed soon--spatial locality.
When it keeps recently used lines in cache, it bets the same line will be needed again--temporal
locality. A programme with poor locality causes frequent cache misses. Each L3 miss on a modern
CPU costs roughly 100-300 ns of stall time, compared to 1-4 ns for an L1 hit. The difference
between a cache-friendly and cache-hostile programme on the same hardware can easily be 10-50x.

A practical example: matrix multiplication. The naive implementation iterates over rows of one
matrix and columns of the other. Columns in a row-major layout are not contiguous--each column
element is a full row-width apart. A cache line loaded for one element contains mostly unused
data. Transposing one matrix before multiplying restores spatial locality, and the performance
improvement can be dramatic even on small matrices.

#### Virtual Memory and Paging

The operating system uses locality when managing which pages of a process stay in RAM and which
are swapped to disk. The LRU (Least Recently Used) eviction policy is a direct application of
temporal locality: the page used least recently is the one least likely to be needed soon.
When a programme's working set fits in RAM, page faults are rare. When it exceeds RAM, the OS
thrashes--replacing pages that are immediately needed again.

#### Instruction Fetch and Branch Prediction

Programmes spend most of their time in loops. Loops are compact in memory and exhibit extreme
temporal and spatial locality in the instruction stream. The CPU instruction cache is very
effective precisely because of this. Branch predictors learn from history (temporal locality
of branch outcomes) and predict that sequential code (spatial locality of the instruction pointer)
will continue straight ahead. A programme with highly irregular control flow--many function
pointers, unpredictable branches--defeats both and runs substantially slower.

#### Database Buffer Pools

A database engine maintains a buffer pool: a region of RAM holding recently accessed pages from
disk. It relies on the same principle as a CPU cache--temporal and spatial locality in query patterns.
A frequently accessed table fits in the buffer pool and is served from RAM. A large table scanned
once blows out the buffer pool, evicting pages that hot queries need. This is why databases expose
query plan hints and why scan-resistant replacement policies (like the CLOCK-Pro algorithm) exist.

#### Compiler Optimisations

Compilers exploit locality explicitly. Loop unrolling increases the amount of work done per loop
iteration, increasing temporal locality over the loop's data. Loop tiling (also called blocking)
restructures nested loops to process a block of the data matrix that fits in cache before moving
on, trading iteration order for cache friendliness. Auto-vectorisation depends on spatial locality:
adjacent elements must be in memory so the CPU can load a full SIMD register at once.

#### NUMA (Non-Uniform Memory Access)

In multi-socket servers, memory is physically attached to specific CPU sockets. A CPU accessing
memory attached to a remote socket pays a latency penalty (typically 1.5-3x). This is NUMA:
Non-Uniform Memory Access. A NUMA-aware programme places data on the NUMA node local to the
thread that will use it. Operating systems, databases, and high-performance runtimes all have
NUMA-awareness built in precisely because physical locality of data to processor matters.


### Locality and Programme Design

Locality is not just a hardware concern. It is a design principle that should inform data structure
choices, memory layout decisions, and access pattern planning.

*Array of Structs vs. Struct of Arrays.* A common layout question in performance-sensitive code.
An array of structs (AoS) places all fields of one record together--good for operations that
read many fields of one record. A struct of arrays (SoA) places all values of one field together--
good for operations that process one field across many records (e.g., summing a column). The right
choice depends entirely on access pattern, which is a question of locality.

*Cache-oblivious algorithms* are designed to exploit locality at all levels of the memory hierarchy
without being tuned to specific cache sizes. The cache-oblivious matrix multiplication, for example,
recursively divides the problem until the subproblem fits in whatever cache is available, automatically
achieving good cache behaviour across the entire hierarchy.

*Memory allocators* attempt to place objects that are allocated together close to each other in memory,
on the theory that objects allocated at the same time are likely to be used at the same time (temporal
locality). Arena allocators and pool allocators make this explicit: all objects of one type or one
request are allocated from a contiguous region.


### When Locality Breaks Down

Locality is an observation about typical programmes, not a guarantee. Some workloads genuinely lack it:

- *Random access patterns:* Hash table lookups, random reads from a large key-value store, and certain
  graph algorithms access unpredictable locations. Each access is likely a cache miss. These workloads
  are inherently latency-bound, and the solution is often to move computation to the data (locality of
  execution) rather than data to computation.

- *Large streaming scans:* Sequential scans over data too large for cache exhibit spatial but not temporal
  locality. Each cache line is loaded once and never reused. Prefetching helps--the hardware can detect
  the sequential pattern and load ahead--but cache size provides no benefit beyond a single line.

- *Pointer-chasing structures:* Linked lists, trees, and graphs stored as heap-allocated nodes with
  pointers scatter data across memory. Traversing a linked list follows one pointer at a time; each
  node may be in a different cache line. This is one of the core arguments for contiguous data structures
  (arrays, B-trees) over pointer-linked ones in performance-critical code.

Understanding when your workload has locality--and when it does not--is the first step in deciding
whether hardware caches will help you or whether you need a different strategy entirely.


### Locality as a Lens

Locality is worth understanding not just for its direct performance implications, but as a lens for
thinking about the relationship between software and hardware. A programme is not a sequence of
abstract operations on abstract memory. It is a physical process unfolding in a physical hierarchy
of storage at different speeds and sizes. Locality is the property that makes that hierarchy work.

When a programme runs slowly for reasons you cannot explain, ask: what is the working set? Is it
larger than the relevant cache? What is the access pattern--sequential or random? Are frequently
used objects laid out near each other, or scattered? These questions often reveal the problem faster
than profiling CPU cycles alone.

*The fastest code is code that does not need to wait for its data.*
Locality is the discipline of making that true.
