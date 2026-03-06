# lazy.py
# Functional Patterns -- 6. Lazy Evaluation and Generators
#
# Demonstrates generators, suspension, lazy pipelines, infinite sequences,
# send(), and a memory comparison between eager and lazy approaches.
#
# Run:  python lazy.py

import sys
import itertools



# 1. Basic generator -- suspension and resumption

def count_up():
    """Infinite counter. Produces one integer at a time."""
    i = 0
    while True:
        yield i       # suspend here; resume when next() is called
        i += 1

print("-- 1. Basic generator --")
gen = count_up()
print(f"  next: {next(gen)}")   # 0
print(f"  next: {next(gen)}")   # 1
print(f"  next: {next(gen)}")   # 2
print(f"  (generator is still alive, paused at yield)")



# 2. Finite generator with natural termination

def range_gen(start, stop, step=1):
    """Finite range as a generator."""
    i = start
    while i < stop:
        yield i
        i += step

print("\n-- 2. Finite generator --")
print(f"  range_gen(0, 6, 2): {list(range_gen(0, 6, 2))}")  # [0, 2, 4]



# 3. Infinite Fibonacci sequence

def fibonacci():
    """Infinite Fibonacci sequence. Holds only two integers at any time."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

print("\n-- 3. Fibonacci (infinite) --")
fibs = fibonacci()
first_ten = [next(fibs) for _ in range(10)]
print(f"  first 10: {first_ten}")



# 4. take() -- consume n elements from any generator

def take(n, source):
    """Yield the first n elements of source."""
    for _, x in zip(range(n), source):
        yield x

print("\n-- 4. take --")
print(f"  take(5, count_up()): {list(take(5, count_up()))}")
print(f"  take(8, fibonacci()): {list(take(8, fibonacci()))}")



# 5. Generator expressions vs. list comprehensions

print("\n-- 5. Generator expression vs. list --")

squares_list = [x * x for x in range(1_000_000)]
squares_gen  = (x * x for x in range(1_000_000))

list_size = sys.getsizeof(squares_list)
gen_size  = sys.getsizeof(squares_gen)

print(f"  list of 1M squares: {list_size:,} bytes")
print(f"  generator (same):   {gen_size} bytes")
print(f"  ratio: {list_size // gen_size}x more memory for the eager version")

# Clean up the large list
del squares_list



# 6. Lazy pipeline -- no intermediate collections

def integers():
    i = 0
    while True:
        yield i
        i += 1

def evens(source):
    for x in source:
        if x % 2 == 0:
            yield x

def squares(source):
    for x in source:
        yield x * x

print("\n-- 6. Lazy pipeline (integers -> evens -> squares -> take 6) --")
pipeline = take(6, squares(evens(integers())))
print(f"  result: {list(pipeline)}")
# At no point does an intermediate list of all integers, evens, or squares exist.



# 7. Chaining with itertools

print("\n-- 7. itertools chaining --")

# islice: lazy slice of any iterable
from itertools import islice, takewhile, dropwhile, chain

fibs = fibonacci()
print(f"  fibs < 100: {list(takewhile(lambda x: x < 100, fibonacci()))}")
print(f"  fibs[10:15]: {list(islice(fibonacci(), 10, 15))}")

# chain: lazily concatenate iterables
combined = chain(range(3), range(10, 13))
print(f"  chain([0,1,2], [10,11,12]): {list(combined)}")



# 8. send() -- bidirectional generator (coroutine style)

def running_total():
    """
    Coroutine-style generator.
    Receives addends via send(), yields the running total.
    """
    total = 0
    while True:
        addend = yield total
        if addend is None:
            return
        total += addend

print("\n-- 8. send() -- bidirectional generator --")
acc = running_total()
next(acc)             # prime: run to first yield
print(f"  send(10): {acc.send(10)}")   # 10
print(f"  send(20): {acc.send(20)}")   # 30
print(f"  send(5):  {acc.send(5)}")    # 35
acc.close()



# 9. The state machine inside a generator (manual reconstruction)

def multi_yield_gen():
    """A generator with three distinct yield points."""
    print("  [gen] starting")
    yield 'first'
    print("  [gen] after first yield")
    yield 'second'
    print("  [gen] after second yield")
    yield 'third'
    print("  [gen] done")

print("\n-- 9. Multiple yield points (state machine) --")
g = multi_yield_gen()
for value in g:
    print(f"  consumer got: {value!r}")



# 10. Generator as backpressure mechanism

def slow_producer():
    """Simulates a producer that tracks when it is called."""
    for i in range(10):
        print(f"  [producer] computing item {i}")
        yield i

def slow_consumer(source, limit):
    """Consumes only as many items as needed."""
    count = 0
    for item in source:
        print(f"  [consumer] processing item {item}")
        count += 1
        if count >= limit:
            print(f"  [consumer] got enough, stopping")
            break

print("\n-- 10. Backpressure: consumer controls producer --")
slow_consumer(slow_producer(), limit=3)
# Producer is called exactly 3 times -- no more work done than necessary.
