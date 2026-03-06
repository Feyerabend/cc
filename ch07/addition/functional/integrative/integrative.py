# integrative.py
# Functional Patterns -- 12. Functional Style as Concurrency Discipline
#
# Demonstrates how each functional pattern contributes to concurrent safety:
# 1. Racy imperative pipeline  -- shared mutable state causes errors
# 2. Functional pipeline       -- pure functions + immutable data, lock-free
# 3. Concurrent functional map -- embarrassingly parallel, no locks
# 4. Persistent accumulation   -- collect results without shared mutation
#
# Run:  python integrative.py

import threading
import time
import random
from functools import reduce
from concurrent.futures import ThreadPoolExecutor



# 1. The racy alternative: shared mutable state

print("-- 1. Racy imperative counter (shared mutable state) --")

shared_total = 0    # mutable shared state -- source of races


def racy_sum(numbers):
    """Add numbers to a shared global -- race if called concurrently."""
    global shared_total
    for n in numbers:
        # read-modify-write: not atomic in Python (GIL softens but does not
        # eliminate the problem; on true parallel runtimes this races)
        shared_total += n


data = list(range(1, 101))    # [1..100], expected sum = 5050
half = len(data) // 2

# Sequential call: correct
shared_total = 0
racy_sum(data[:half])
racy_sum(data[half:])
print(f"  Sequential racy_sum:  {shared_total}  (correct by accident -- no race)")

# Two threads sharing the same mutable global
shared_total = 0
t1 = threading.Thread(target=racy_sum, args=(data[:half],))
t2 = threading.Thread(target=racy_sum, args=(data[half:],))
t1.start(); t2.start()
t1.join();  t2.join()
print(f"  Concurrent racy_sum:  {shared_total}  (may be wrong due to race)")
print(f"  Expected:             5050")
print(f"  Correct: {shared_total == 5050}  (CPython GIL often saves us, but not in general)")



# 2. Pure functional pipeline: no shared state

print("\n-- 2. Pure functional pipeline --")


# --- Pattern 9: Referentially transparent functions ---
def square(x):      return x * x          # pure
def is_odd(x):      return x % 2 != 0     # pure
def add(acc, x):    return acc + x        # pure


# --- Pattern 5: Function composition ---
def compose(f, g):
    return lambda x: f(g(x))

square_odd = compose(square, is_odd)   # True when x is odd and x^2 is truthy


# --- Pattern 6: Lazy evaluation (generators) ---
def naturals(n):
    """Infinite-ish generator of naturals up to n."""
    i = 1
    while i <= n:
        yield i
        i += 1


# --- Pattern 4: Higher-order functions (map, filter, reduce) ---
source = naturals(10)                    # lazy
odds   = filter(is_odd, source)          # lazy filter
sq     = map(square, odds)               # lazy map
total  = reduce(add, sq, 0)             # eager terminal: sum of squares of odds <= 10

# Odd numbers <= 10: 1,3,5,7,9 -- squares: 1,9,25,49,81 -- sum = 165
print(f"  sum(square(x) for odd x in 1..10) = {total}  (expected 165)")
print(f"  Pipeline: naturals -> filter(is_odd) -> map(square) -> reduce(add)")
print(f"  No shared state; each step is a pure lazy transform.")



# 3. Embarrassingly parallel map over pure function
#    Pattern 4 + Pattern 1 (first-class functions) + Pattern 9 (purity)

print("\n-- 3. Concurrent map over pure function (ThreadPoolExecutor) --")


def cpu_work(x):
    """Pure: result depends only on x. Safe to call from any thread."""
    return sum(i * i for i in range(x))


inputs = list(range(100, 200))   # 100 values

# Sequential
t0 = time.perf_counter()
seq_results = list(map(cpu_work, inputs))
t_seq = time.perf_counter() - t0

# Concurrent: same pure function, no locks needed
t0 = time.perf_counter()
with ThreadPoolExecutor(max_workers=4) as pool:
    par_results = list(pool.map(cpu_work, inputs))
t_par = time.perf_counter() - t0

assert seq_results == par_results, "results differ -- function is not pure!"
print(f"  Sequential:  {t_seq * 1000:.1f} ms")
print(f"  4 threads:   {t_par * 1000:.1f} ms")
print(f"  Results match: {seq_results == par_results}  (pure function: always correct)")
print(f"  No locks used. Purity is the only synchronisation primitive needed.")



# 4. Persistent accumulation: each thread builds its own result
#    Pattern 10 (persistence) + Pattern 2 (immutable closure capture)

print("\n-- 4. Persistent accumulation: thread-local results, no sharing --")


class Node:
    """Immutable linked list node. After __init__, fields never change."""
    __slots__ = ('value', 'next')

    def __init__(self, value, next_node=None):
        self.value = value
        self.next  = next_node


EMPTY = None


def cons(v, lst):  return Node(v, lst)
def to_list(lst):
    r = []
    while lst:
        r.append(lst.value)
        lst = lst.next
    return r


def local_pipeline(chunk):
    """
    Pure pipeline: build a persistent list of squared-odds from chunk.
    No shared state; safe to run on any thread.
    """
    result = EMPTY
    for x in chunk:
        if is_odd(x):
            result = cons(square(x), result)
    return result   # a persistent list; caller owns it


# Split data across threads
n_threads = 4
chunk_size = len(data) // n_threads
chunks = [data[i * chunk_size:(i + 1) * chunk_size] for i in range(n_threads)]

thread_results = [None] * n_threads
lock = threading.Lock()   # only needed to write into the results list


def worker(idx, chunk):
    local_result = local_pipeline(chunk)    # pure; no shared state touched
    with lock:
        thread_results[idx] = local_result  # one write per thread, to own slot


threads = [threading.Thread(target=worker, args=(i, chunks[i]))
           for i in range(n_threads)]
for t in threads: t.start()
for t in threads: t.join()

# Merge: combine all thread-local persistent lists
all_values = []
for r in thread_results:
    all_values.extend(to_list(r))

all_values.sort()
expected = sorted(square(x) for x in range(1, len(data) + 1) if is_odd(x))

print(f"  {n_threads} threads, each building a thread-local persistent list.")
print(f"  One lock used only to write the result pointer -- not for the work.")
print(f"  Results match sequential: {all_values == expected}")



# 5. The closure safety contrast
#    Pattern 2: closure over immutable vs mutable

print("\n-- 5. Closure safety: immutable vs mutable capture --")


def make_safe_adder(n):
    """Closure over immutable n. Safe to call from any thread."""
    def add(x):
        return x + n     # n is never modified
    return add


_counter = [0]   # mutable shared cell


def make_unsafe_counter():
    """Closure over mutable shared cell. NOT thread-safe."""
    def inc():
        _counter[0] += 1   # read-modify-write on shared state
        return _counter[0]
    return inc


add10 = make_safe_adder(10)

# Many threads calling the safe closure simultaneously
safe_results = []
safe_lock    = threading.Lock()


def safe_worker(v):
    r = add10(v)     # pure; no shared state
    with safe_lock:
        safe_results.append(r)


workers = [threading.Thread(target=safe_worker, args=(i,)) for i in range(8)]
for w in workers: w.start()
for w in workers: w.join()

safe_results.sort()
expected_safe = sorted(i + 10 for i in range(8))
print(f"  Safe closure (immutable capture): all {len(safe_results)} results correct: "
      f"{safe_results == expected_safe}")

# Note: the unsafe counter is NOT demonstrated concurrently because the
# race condition is non-deterministic; we just describe the problem.
print(f"  Unsafe closure (mutable capture): _counter[0] += 1 is a data race.")
print(f"  Two threads interleave read-modify-write -> lost updates.")



# 6. Summary: each pattern's concurrency contribution

print("\n-- 6. Summary: concurrency contributions --")
contributions = [
    ("First-class functions",    "Pass behaviour without shared state"),
    ("Closures (immutable)",     "Encapsulate state safely; safe from any thread"),
    ("Immutability",             "Write once, read many; no synchronisation needed"),
    ("Higher-order functions",   "Pure transforms are embarrassingly parallel"),
    ("Function composition",     "Chained pure stages; no shared intermediate state"),
    ("Lazy evaluation",          "No shared buffers between pipeline stages"),
    ("Functors",                 "Transform contents; original unchanged and shareable"),
    ("Monads",                   "Explicit effect sequencing; no hidden global state"),
    ("Referential transparency", "Same input -> same output; safe to call concurrently"),
    ("Persistent structures",    "N readers, 0 locks; one atomic swap to publish"),
]
for pattern, contribution in contributions:
    print(f"  {pattern:<28} {contribution}")

print("\n  The principle: functional purity is a memory access pattern.")
print("  Pure functions read inputs, produce outputs, touch nothing else.")
print("  That property makes concurrent correctness follow from code structure.")
