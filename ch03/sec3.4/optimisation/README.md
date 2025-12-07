
## Performance Optimisation Examples

A comprehensive collection of *real-world performance optimisation techniques* demonstrated
through small, self-contained, and benchmarked examples in *C* and *Python*.

Each file focuses on a specific area of optimisation and shows both *naïve* and *optimised*
approaches with actual timing comparisons.


### Overview

| File              | Language | Topic                                      | Key Techniques Demonstrated                                  |
|-------------------|----------|--------------------------------------------|--------------------------------------------------------------|
| `compiler.c`      | C        | Compiler & low-level optimisations         | Loop unrolling, inlining, constant folding, dead code elimination, SIMD hints, restrict, alignment |
| `memory.c`        | C        | Memory access patterns & cache efficiency  | Row-major vs column-major, cache blocking/tiling, struct padding |
| `io.py`           | Python   | Disk I/O optimisation                      | Buffering, batch writing, streaming vs loading all at once   |
| `data_struct.py`  | Python   | Choosing the right data structure          | list vs set vs deque vs defaultdict vs Counter, bisect, comprehensions |
| `strings.py`      | Python   | String operation performance               | `+` vs `join`, f-strings, built-in methods vs manual loops   |
| `parallel.py`     | Python   | Parallelism & concurrency                  | `multiprocessing` vs `threading`, ProcessPool vs ThreadPool, shared state pitfalls |
| `network.py`      | Python   | Network & API optimisation                 | Batching, connection pooling, compression, ETag caching, parallel requests, payload minimisation, GraphQL vs REST |

### Example Results (typical on a modern laptop)

| Area                              | Naïve -> Optimised Speed-up |
|-----------------------------------|-----------------------------|
| String concatenation (10k items)  | 50-200×                     |
| List membership testing           | up to 300× (list → set)     |
| Inserting at list beginning       | 100×+ (list → deque)        |
| CPU-bound work (8 cores)          | ~7-8× (sequential → multiprocessing) |
| Matrix multiplication (200×200)   | 4-6× (parallel rows)        |
| Row vs column-major traversal     | 5-20× difference            |
| I/O reading large file            | 3-10× (line-by-line → readlines/all-at-once) |

(Actual numbers vary by hardware, Python version, compiler, etc.)


### Key Takeaways

1. *Let the compiler do the work* - modern compilers (GCC/Clang) are incredibly smart at -O2/-O3.
2. *Memory access pattern > raw CPU speed* - cache-friendly code beats "faster" algorithms.
3. *Choose data structures by access pattern*, not habit (`set` for lookup, `deque` for queues, `Counter` for counting).
4. *Prefer built-in functions and comprehensions* over manual Python loops.
5. *Use `str.join()`* - never `+=` strings in a loop.
6. *f-strings are the fastest formatting method* (Python 3.6+).
7. *Multiprocessing for CPU-bound, threading for I/O-bound*.
8. *Batch network requests*, reuse connections, compress payloads, cache aggressively.

