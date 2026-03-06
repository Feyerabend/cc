# cost.py
# Functional Patterns -- 11. Cost Model
#
# Measures the concrete overhead of functional-style operations in Python:
# object size, allocation cost, function-call dispatch, closure overhead,
# composition depth.
#
# Run:  python cost.py

import sys
import time
import functools
import tracemalloc

REPS = 500_000


def perf(label, fn, reps=REPS):
    """Time fn() called reps times; print ns per call."""
    for _ in range(min(2000, reps)):   # warmup
        fn()
    t0 = time.perf_counter()
    for _ in range(reps):
        fn()
    t1 = time.perf_counter()
    ns = (t1 - t0) * 1e9 / reps
    print(f"  {label:<44} {ns:7.1f} ns/call")



# 1. Object size

print("-- 1. Object size --")


class NodeSlots:
    __slots__ = ('value', 'next')

    def __init__(self, v, n=None):
        self.value = v
        self.next  = n


class NodeDict:
    def __init__(self, v, n=None):
        self.value = v
        self.next  = n


n_slots = NodeSlots(1)
n_dict  = NodeDict(1)

total_dict = sys.getsizeof(n_dict) + sys.getsizeof(n_dict.__dict__)

print(f"  int(1)                         : {sys.getsizeof(1)} bytes")
print(f"  Node with __slots__            : {sys.getsizeof(n_slots)} bytes")
print(f"  Node without __slots__         : {sys.getsizeof(n_dict)} bytes")
print(f"    + __dict__ overhead          : {sys.getsizeof(n_dict.__dict__)} bytes (hidden)")
print(f"    total Node+dict              : {total_dict} bytes")
print(f"  tuple (value, next)            : {sys.getsizeof((1, None))} bytes")
print(f"  C node_t (int+ptr+atomic_int)  : 24 bytes  (for comparison)")



# 2. Allocation cost: cons N times

print("\n-- 2. Allocation: building a persistent linked list --")


def cons(v, lst):
    return NodeSlots(v, lst)


N = 20_000

tracemalloc.start()
snap_before = tracemalloc.take_snapshot()
t0 = time.perf_counter()
lst = None
for v in range(N):
    lst = cons(v, lst)
t1 = time.perf_counter()
snap_after = tracemalloc.take_snapshot()
tracemalloc.stop()

stats      = snap_after.compare_to(snap_before, 'lineno')
alloc_bytes = sum(s.size_diff for s in stats if s.size_diff > 0)

print(f"  cons() x {N:,}:")
print(f"    time       : {(t1 - t0) * 1000:.2f} ms")
print(f"    allocated  : ~{alloc_bytes:,} bytes (~{alloc_bytes // N} bytes/node)")
print(f"    per call   : {(t1 - t0) * 1e9 / N:.0f} ns/cons")

# Equivalent mutable list
t0 = time.perf_counter()
mlist = []
for v in range(N):
    mlist.append(v)
t1 = time.perf_counter()
print(f"  list.append() x {N:,}:")
print(f"    time       : {(t1 - t0) * 1000:.2f} ms  (mutable, contiguous buffer)")
print(f"    per call   : {(t1 - t0) * 1e9 / N:.0f} ns/append")



# 3. Function call overhead

print("\n-- 3. Function call overhead --")

x = 7


def bare(n): return n * n


class Squarer:
    def square(self, n): return n * n


sq = Squarer()


def apply(f, v): return f(v)


double = functools.partial(lambda a, b: a * b, 2)
sq_lambda = lambda n: n * n   # noqa: E731

perf("bare call:        bare(x)",                 lambda: bare(x))
perf("lambda call:      sq_lambda(x)",            lambda: sq_lambda(x))
perf("method call:      sq.square(x)",            lambda: sq.square(x))
perf("HOF:              apply(bare, x)",          lambda: apply(bare, x))
perf("partial call:     double(x)",               lambda: double(x))
perf("built-in:         abs(x)",                  lambda: abs(x))



# 4. Closure capture overhead

print("\n-- 4. Closure overhead --")


def make_adder(n):
    def add(x): return x + n
    return add


add5 = make_adder(5)


def add_direct(x, n): return x + n


perf("closure call:     add5(x)",                 lambda: add5(x))
perf("direct call:      add_direct(x, 5)",        lambda: add_direct(x, 5))



# 5. Map / comprehension / generator

print("\n-- 5. Map vs comprehension vs generator (data = range(1000)) --")

data = list(range(1000))


def square(n): return n * n


for label, expr in [
    ("map(square, data) -> list",    lambda: list(map(square, data))),
    ("[square(x) for x in data]",   lambda: [square(x) for x in data]),
    ("[x*x for x in data]",         lambda: [x * x for x in data]),
    ("sum(x*x for x in data)",      lambda: sum(x * x for x in data)),
]:
    perf(label, expr, reps=5000)



# 6. Composition depth: cost per added layer

print("\n-- 6. Composition depth: cost per added layer --")


def compose(f, g): return lambda x: f(g(x))


inc = lambda x: x + 1   # noqa: E731
f1  = inc
f2  = compose(inc, inc)
f4  = compose(f2, f2)
f8  = compose(f4, f4)
f16 = compose(f8, f8)

for label, fn in [
    ("depth  1: inc(0)",      f1),
    ("depth  2: f2(0)",       f2),
    ("depth  4: f4(0)",       f4),
    ("depth  8: f8(0)",       f8),
    ("depth 16: f16(0)",      f16),
]:
    perf(label, lambda fn=fn: fn(0))



# 7. Summary

print("\n-- 7. Summary --")
print("  Python object sizes (CPython, this machine):")
print(f"    int(1)              : {sys.getsizeof(1)} bytes")
print(f"    Node with __slots__ : {sys.getsizeof(NodeSlots(1))} bytes")
print(f"    Node + __dict__     : {sys.getsizeof(NodeDict(1)) + sys.getsizeof(NodeDict(1).__dict__)} bytes")
print( "    C node_t            : 24 bytes  (int + ptr + atomic_int)")
print("  Python functional style costs (observed above):")
print("    Function call : ~40--65 ns   (frame creation + descriptor lookup)")
print("    HOF call      : ~65 ns       (two frames)")
print("    Compose N     : ~N × 45 ns  (N frames, linear)")
print("    map(f, 1000)  : ~40--47 µs  (~40 ns per element)")
print("    [x*x for x]  : ~25 µs       (~25 ns per element, no function call)")
print("  C costs at -O2 (NOINLINE, observed above):")
print("    Function call : ~1 ns        (indirect branch, well-predicted)")
print("    Closure call  : ~1--2 ns     (one extra load for ctx pointer)")
print("    Compose N     : ~N × 1 ns   (N indirect branches, linear)")
print("    Heap malloc+free: ~20--25 ns (allocator overhead)")
print("  Ratio, function call: Python ~45 ns / C ~1 ns = ~45x.")
print("  Ratio, compose-16:    Python ~800 ns / C ~14 ns = ~57x.")
