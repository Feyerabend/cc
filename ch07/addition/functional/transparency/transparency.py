# transparency.py
# Functional Patterns -- 9. Referential Transparency
#
# Demonstrates pure vs. impure functions, equational reasoning,
# memoisation, and how hidden state breaks transparency.
#
# Run:  python transparency.py

import random
import time
import threading
from functools import lru_cache



# 1. Pure functions -- RT holds

def square(x):      return x * x
def add(a, b):      return a + b
def to_upper(s):    return s.upper()

def factorial(n):
    return 1 if n <= 1 else n * factorial(n - 1)

print("-- 1. Pure (referentially transparent) functions --")
print(f"  square(5)    = {square(5)}")
print(f"  square(5)    = {square(5)}   (always the same)")
print(f"  add(3, 4)    = {add(3, 4)}")
print(f"  factorial(6) = {factorial(6)}")



# 2. Impure functions -- RT broken

_counter = 0

def next_id():
    global _counter
    _counter += 1
    return _counter

def current_time():
    return time.time()

def random_roll():
    return random.randint(1, 6)

print("\n-- 2. Impure functions (RT broken) --")
print(f"  next_id()  = {next_id()}")
print(f"  next_id()  = {next_id()}   (same call, different result)")
t1, t2 = current_time(), current_time()
print(f"  current_time() two calls: t2 > t1 = {t2 > t1}")
print(f"  random_roll() = {random_roll()}, {random_roll()}  (unpredictable)")



# 3. Equational reasoning

def double(x):  return x * 2
def inc(x):     return x + 1

print("\n-- 3. Equational reasoning --")
print("  double(inc(3))")
print(f"    = double({inc(3)})       [substitute inc(3)={inc(3)}]")
print(f"    = {double(inc(3))}              [substitute double({inc(3)})={double(inc(3))}]")
print("  This substitution is valid because both functions are pure.")
print()

# With an impure function, substitution fails:
count = [0]
def inc_impure():
    count[0] += 1
    return count[0]

r1 = inc_impure()
r2 = inc_impure()
print(f"  inc_impure() + inc_impure() = {r1} + {r2} = {r1 + r2}")
count[0] = 0
r3 = inc_impure()
print(f"  2 * inc_impure()            = 2 * {r3} = {2 * r3}")
print(f"  Not equal: {r1+r2} ≠ {2*r3}  (substitution fails with mutable state)")



# 4. Memoisation -- only correct when RT holds

print("\n-- 4. Memoisation --")

@lru_cache(maxsize=None)
def fib(n):
    if n < 2: return n
    return fib(n - 1) + fib(n - 2)

import time
t0 = time.perf_counter()
result = fib(38)
t1 = time.perf_counter()
result2 = fib(38)
t2 = time.perf_counter()

print(f"  fib(38) = {result}")
print(f"  first call:  {(t1-t0)*1000:.2f} ms")
print(f"  cached call: {(t2-t1)*1000:.4f} ms  (effectively zero)")
print(f"  Cache is correct because fib is referentially transparent.")

# Incorrect memoisation of an impure function:
_call_count = [0]
_bad_cache = {}

def impure_fn(x):
    _call_count[0] += 1
    return x + _call_count[0]   # result changes with each call

def bad_memo(x):
    if x not in _bad_cache:
        _bad_cache[x] = impure_fn(x)
    return _bad_cache[x]

print()
print(f"  bad_memo(5) = {bad_memo(5)}  (caches first result)")
print(f"  bad_memo(5) = {bad_memo(5)}  (returns stale cache)")
print(f"  impure_fn(5) would now return {impure_fn(5)}  (differs from cache)")
print(f"  Cached value is now WRONG -- RT violation made memoisation unsound.")



# 5. Hidden state: closure over mutable value

print("\n-- 5. Hidden state in a closure --")

def make_accumulator():
    total = [0]
    def add(x):
        total[0] += x
        return total[0]
    return add

acc = make_accumulator()
print(f"  acc(5) = {acc(5)}")
print(f"  acc(5) = {acc(5)}   (same arg, different result -- hidden mutable cell)")

# Compare with a pure version:
def pure_acc(total, x):
    return total + x     # caller passes state explicitly

t = 0
t = pure_acc(t, 5)
t = pure_acc(t, 5)
print(f"  pure_acc: explicit state threading, always RT: pure_acc(0,5)={pure_acc(0,5)}")



# 6. Detecting RT violations mechanically

print("\n-- 6. Detecting violations --")

def check_rt(f, *args, trials=5):
    """Call f with args multiple times; return True if all results equal."""
    results = [f(*args) for _ in range(trials)]
    return len(set(results)) == 1, results

for fn, args, label in [
    (square,      (7,),     "square(7)"),
    (add,         (3, 4),   "add(3,4)"),
    (next_id,     (),       "next_id()"),
    (random_roll, (),       "random_roll()"),
]:
    ok, vals = check_rt(fn, *args)
    status = "RT" if ok else "NOT RT"
    print(f"  {label:<18} [{status}]  sample results: {vals}")



# 7. RT and thread safety

print("\n-- 7. RT and thread safety --")

# Pure function: safe to call from many threads simultaneously
def cpu_heavy_pure(n):
    """Compute sum of squares up to n -- no shared state."""
    return sum(i * i for i in range(n))

results_pure = []
lock = threading.Lock()

def worker_pure(n):
    r = cpu_heavy_pure(n)
    with lock: results_pure.append((n, r))

threads = [threading.Thread(target=worker_pure, args=(i * 100,))
           for i in range(1, 5)]
for t in threads: t.start()
for t in threads: t.join()

for n, r in sorted(results_pure):
    print(f"  cpu_heavy_pure({n:4}) = {r:10}  (safe: no shared mutable state)")

# Impure function: would race -- we simulate the problem without actually racing
shared_total = [0]

def worker_impure(n):
    # In real concurrent code this would race:
    # shared_total[0] += n  <-- read-modify-write is not atomic
    pass

print("  impure version omitted: read-modify-write on shared_total would race.")
print("  The race is a direct consequence of breaking referential transparency.")



# 8. RT enables compiler optimisations (Python analogy)

print("\n-- 8. Optimisation enabled by RT --")

# CSE: compute once, reuse
x = 7
r = square(x) + square(x) + square(x)
print(f"  square({x}) + square({x}) + square({x}) = {r}")
print(f"  A compiler knows square({x}) = {square(x)} for all calls;")
print(f"  it may call square once and reuse the result.")

# Loop invariant hoist:
data  = list(range(100))
scale = 3
# The compiler knows square(scale) is constant -- it can hoist it:
result = [x * square(scale) for x in data]
print(f"  [x * square({scale}) for x in data]: square({scale})={square(scale)} hoisted out of loop.")
print(f"  Only possible because square has no side effects.")
