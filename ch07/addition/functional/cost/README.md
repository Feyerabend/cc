
## 11. Cost Model

*The cost of abstraction is the question. The answer depends entirely on the language's object model.*

Functional style in Python and functional style in C are written with the same
vocabulary--functions, closures, higher-order functions, immutable values--but
the two runtimes charge very different prices for them. Understanding the
cost model is what separates principled use of functional patterns from
cargo-cult adoption.

This section measures the concrete overheads of each pattern introduced in the
series, compares Python and C on identical operations, and traces each cost
back to a specific aspect of how the language is implemented.

*The code has been tested on a MacBook with Pro Apple M5 in 2026.*


### The Python Object Model

Every value in Python is a heap-allocated object. Every object carries:
- A reference count (8 bytes)
- A pointer to the type object (`ob_type`, 8 bytes)
- For objects tracked by the cyclic GC: a GC header (16 bytes)
- For objects with a `__dict__`: a further dictionary pointer (8 bytes)

A Python integer `1` takes 28 bytes. A custom `Node` class with `__slots__`
takes roughly 56 bytes. The equivalent C struct--`int value`, `node_t *next`,
`atomic_int refcount`--takes 24 bytes on a 64-bit platform.

#### Allocation Cost

Python allocation goes through:
1. The type's `__new__` method
2. CPython's small-object allocator (256-byte arenas, but still synchronised)
3. Reference count initialisation
4. Optional GC registration for trackable objects

Each `cons(v, lst)` in the Python persistent list section allocates one `Node`
object. Building a list of N elements = N object allocations, each with
Python-object overhead.

C allocation goes through `malloc`. A pool allocator reduces this to a
pointer bump per allocation, with no per-object overhead.

#### Dynamic Dispatch

Python attribute access goes through `__getattribute__`, the descriptor
protocol, method wrapper objects, and type checks. Reading `n.value` on a
`Node` with `__slots__` requires a slot descriptor lookup. Calling a method
requires more steps: find the attribute, wrap it in a bound-method object,
build the argument tuple, create a new frame.

In C, `n->value` is a single memory read at a compile-time-known offset. No
runtime lookup, no wrapper, no frame.

#### GC Pressure

CPython uses reference counting for immediate reclamation, plus a cyclic
garbage collector for objects involved in reference cycles. The cyclic GC
periodically pauses all threads to collect cycles; this adds unpredictable
latency. In C with explicit `free`, there is no GC--deallocation happens
exactly when the last reference is dropped.



### C: The Zero-Overhead Principle

C's design principle: abstractions you do not use cost nothing; abstractions
you do use cost no more than the equivalent hand-written code.

#### Stack Allocation

A small struct passed by value lives entirely in registers or on the call
stack. No `malloc`, no `free`, no pointer indirection. A closure pair
(`fn_ptr`, `void *ctx`) is two machine words--two register loads.

Returning a struct by value is compiled to writing into caller-provided
memory (return-value optimisation, RVO). In practice, small structs live in
registers from the caller's perspective.

#### Inline Expansion

The compiler replaces a call to a small, pure function with its body at the
call site. Call overhead (frame setup, argument marshalling, return address
save) disappears. With `ATTR_CONST`, the compiler may additionally hoist the
call out of loops or fold it at compile time.

A chain of composed functions--`f(g(h(x)))`--where each is small and
pure becomes a straight sequence of arithmetic operations after inlining.
No function calls remain in the final binary.

#### Function Pointer Cost

A call through a function pointer is one indirect branch: the processor loads
the target address from memory and jumps. On modern out-of-order processors
this costs 1--3 cycles if the branch predictor has seen this address before.
In a tight inner loop calling the same function pointer repeatedly, the
predictor hits and the overhead approaches zero.

In Python, a call through a bound method involves attribute lookup, type
checks, argument-tuple allocation, and frame creation--roughly 100--500 ns.



### Pattern-by-Pattern Summary

| Pattern | Python cost | C cost |
|---------|-------------|--------|
| Value | Object on heap (28--56 bytes) | Value in register or stack |
| Closure | Object + captured variables in cell objects | Two-word struct, stack |
| HOF call | ~200 ns (frame + descriptor protocol) | ~1--3 ns (indirect branch) |
| Compose N layers | N × Python call overhead | N × 0 ns if inlined |
| Lazy generator | Generator object (frame kept alive on heap) | Struct with explicit fields, stack |
| Functor map | N object allocations for result | Zero if computed in-place |
| Persistent cons | One `Node` object (~56 bytes) | One `malloc` (24 bytes) |
| Structural share | Pointer copy + refcount increment | Pointer copy + `atomic_fetch_add` |



### The Speed Ratio in Practice

For tight numeric loops, C at `-O2` is typically 50--200x faster than
equivalent Python. For allocation-heavy workloads the ratio can be larger,
because Python's per-object overhead dominates over the actual work.

For I/O-bound or logic-heavy code where Python spends most of its time in
compiled C extensions--NumPy, database drivers, parsers--the ratio
narrows toward zero. The Python "glue" is rarely the bottleneck.

The functional patterns in this series were written in Python for clarity.
In performance-critical C code, the same patterns can be applied with zero
additional overhead over hand-written code, because the compiler eliminates
the abstraction.



### Practical Rules

1. *Measure first.* Profile before optimising. Python is fast enough for most
   programs; C is needed for hot paths.

2. *Python for structure, C for speed.* Write the algorithm in Python; rewrite
   the bottleneck in C or use a C extension.

3. *Use `__slots__`.* Eliminates `__dict__` overhead; reduces object size
   by roughly half.

4. *Use generators over lists.* Defers allocation; avoids building
   intermediate lists that are immediately consumed.

5. *In C, prefer stack allocation.* Pass small structs by value; return them
   by value. The compiler assigns them to registers.

6. *In C, trust the inliner.* Write small, pure functions. Annotate with
   `ATTR_CONST`. The optimiser collapses the abstraction overhead to zero.

7. *In C, function pointers are not free but are cheap.* One indirect branch
   per call. If the same pointer is called in a loop, the branch predictor
   learns it quickly and the overhead vanishes.



*Next: [12. Functional Style as Concurrency Discipline](../integrative/README.md)--the
closing section showing how every pattern in this series contributes to safe concurrent programs.*
