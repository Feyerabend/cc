
## Memory Barriers and Thread-Safe Implementation

This directory contains a thread-safe implementation of the compiler's
core data structures using memory barriers and atomic operations.

The implementation provides:

1. *Memory Barriers* (`atomic.h`)
   - Full memory barriers (sequential consistency)
   - Acquire/release barriers
   - Compiler barriers
   - Platform-specific optimizations

2. *Atomic Operations* (`atomic.h`)
   - Atomic load/store
   - Compare-and-swap (CAS)
   - Fetch-and-add
   - Atomic increment/decrement

3. *Thread-Safe Arena Allocator* (`arena_threadsafe.h`)
   - Lock-free allocation in common case
   - Spinlock for block creation
   - Memory barriers ensure visibility across threads

4. *Synchronisation Primitives* (`atomic.h`)
   - Spinlocks
   - Lock-free stack


### Memory Barrier Types

#### Full Memory Barrier
```c
memory_barrier_full();
```
Ensures all memory operations before the barrier are visible
before operations after it. Uses sequential consistency.

#### Acquire Barrier
```c
memory_barrier_acquire();
```
Prevents reordering of loads after the barrier with operations
before it. Used after reading shared flags.

#### Release Barrier
```c
memory_barrier_release();
```
Prevents reordering of stores before the barrier with operations
after it. Used before writing shared flags.

#### Compiler Barrier
```c
compiler_barrier();
```
Prevents compiler reordering only (not CPU reordering).
Useful for volatile-like semantics.


### Thread-Safe Arena Implementation

1. *Lock-Free Fast Path*
   - Uses CAS to atomically reserve space in current block
   - No locks needed for successful allocation from existing block

2. *Spinlock for Block Creation*
   - Only acquired when new block is needed
   - Reduces contention compared to always locking

3. *Memory Ordering*
   - New blocks use release semantics when published
   - Readers use acquire semantics when accessing blocks
   - Ensures block initialization is visible before block pointer

```c
// Create thread-safe arena
ThreadSafeArena *arena = ts_arena_create(8192);

// Allocate from multiple threads safely
void *ptr = ts_arena_alloc(arena, 256);

// Duplicate strings safely
char *str = ts_arena_strdup(arena, "hello");

// Get statistics
size_t allocated = ts_arena_total_allocated(arena);
size_t blocks = ts_arena_total_blocks(arena);

// Cleanup
ts_arena_destroy(arena);
```


### Building and Testing

#### Build Tests
```bash
make -f Makefile.tests
```

#### Run Tests
```bash
make -f Makefile.tests test
```

#### Run with ThreadSanitizer
```bash
make -f Makefile.tests test-tsan
```

#### Run Benchmark
```bash
make -f Makefile.tests benchmark
```

#### Run with Valgrind
```bash
make -f Makefile.tests valgrind
```



### Test Suite

The test suite includes 10 comprehensive tests:

1. *Memory Barriers* - Tests store/load ordering with barriers
2. *Atomic Operations* - Concurrent increments
3. *Compare-and-Swap* - Lock-free counter using CAS
4. *Spinlock* - Mutual exclusion
5. *Lock-Free Stack* - Concurrent push/pop operations
6. *Thread-Safe Arena (Small)* - Many small allocations
7. *Thread-Safe Arena (Mixed)* - Mixed size allocations
8. *Thread-Safe Arena (Strdup)* - String duplication
9. *Sequential Consistency* - Memory ordering verification
10. *Stress Test* - High contention scenario

#### Test Configuration

Default configuration (can be modified in test source):
- `NUM_THREADS`: 8 threads
- `ALLOCATIONS_PER_THREAD`: 10,000 allocations per thread
- Various allocation sizes: 32, 256, 4096 bytes


### Memory Ordering Semantics

#### Sequential Consistency (seq_cst)
Strongest ordering: all operations appear in a single total order.

```c
atomic_store_explicit(&x, 1, memory_order_seq_cst);
int val = atomic_load_explicit(&y, memory_order_seq_cst);
```

#### Acquire-Release
Synchronizes data between threads.

```c
// Thread 1 (producer)
data = compute_value();
atomic_store_explicit(&flag, true, memory_order_release);

// Thread 2 (consumer)
while (!atomic_load_explicit(&flag, memory_order_acquire)) {
    // wait
}
use(data); // Guaranteed to see updated data
```

#### Relaxed
No ordering guarantees, fastest for independent operations.

```c
atomic_fetch_add_explicit(&counter, 1, memory_order_relaxed);
```

### Platform Support

The implementation uses C11 atomics and should work on:

- x86/x86_64 (Linux, macOS, Windows)
- ARM/AArch64
- Other architectures supporting C11 stdatomic.h

Platform-specific optimizations:
- x86: Uses `pause` instruction in spinlock
- ARM: Uses `yield` instruction in spinlock


### Performance Characteristics

*Best Case* (allocation from existing block):
- 1 atomic load (acquire)
- 1 atomic CAS (release)
- No locks, minimal contention

*Worst Case* (new block needed):
- Spinlock acquisition
- Block allocation
- 1 atomic store (release)
- Spinlock release


### Thread Safety Guarantees

1. *Memory Safety*
   - No data races (verified with ThreadSanitizer)
   - No use-after-free
   - No double-free

2. *Correctness*
   - Atomic counters always accurate
   - All allocations succeed or fail consistently
   - No memory corruption

3. *Progress*
   - Lock-free allocation in common case
   - No deadlocks (spinlocks have no dependencies)


### Common Patterns

#### Producer-Consumer
```c
// Producer
data_t *data = produce_data();
atomic_store_explicit(&ready, true, memory_order_release);

// Consumer
while (!atomic_load_explicit(&ready, memory_order_acquire));
consume(data); // Safe to access
```

#### Reference Counting
```c
void retain(Object *obj) {
    atomic_fetch_add_explicit(&obj->refcount, 1, memory_order_relaxed);
}

void release(Object *obj) {
    if (atomic_fetch_sub_explicit(&obj->refcount, 1, memory_order_release) == 1) {
        memory_barrier_acquire(); // Synchronise before destruction
        destroy(obj);
    }
}
```

#### Double-Checked Locking
```c
if (atomic_load_explicit(&initialized, memory_order_acquire) == 0) {
    spinlock_lock(&init_lock);
    if (atomic_load_explicit(&initialized, memory_order_relaxed) == 0) {
        initialize();
        atomic_store_explicit(&initialized, 1, memory_order_release);
    }
    spinlock_unlock(&init_lock);
}
```


### Debugging

#### ThreadSanitizer
Detects data races:
```bash
make -f Makefile.tests test-tsan
```

#### Valgrind/Helgrind
Detects threading issues:
```bash
make -f Makefile.tests valgrind
```



### References

- C11 Standard (ISO/IEC 9899:2011) - Section 7.17 (Atomics)
- "C++ Concurrency in Action" by Anthony Williams
- "The Art of Multiprocessor Programming" by Herlihy & Shavit
- Linux kernel memory barriers documentation

