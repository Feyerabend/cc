# composition.py
# Functional Patterns -- 5. Function Composition
#
# Demonstrates binary compose, variadic compose, pipe order,
# associativity, partial application, and decorators as composition.
#
# Run:  python composition.py

from functools import reduce, partial
import time



# Primitive functions used throughout

def square(x):      return x * x
def increment(x):   return x + 1
def negate(x):      return -x
def double(x):      return x * 2
def halve(x):       return x // 2



# 1. Binary compose  -- f ∘ g, right to left

def compose(f, g):
    """Return the function x -> f(g(x)).  g is applied first."""
    return lambda x: f(g(x))

print("-- 1. Binary compose --")

inc_then_square = compose(square, increment)    # square(increment(x))
square_then_neg = compose(negate, square)       # negate(square(x))
double_then_inc = compose(increment, double)    # increment(double(x))

print(f"  inc_then_square(4)  = {inc_then_square(4)}")    # square(5)  = 25
print(f"  square_then_neg(3)  = {square_then_neg(3)}")    # negate(9)  = -9
print(f"  double_then_inc(7)  = {double_then_inc(7)}")    # increment(14) = 15



# 2. Variadic compose  -- right to left, arbitrary length

def compose_all(*funcs):
    """
    Compose an arbitrary number of functions, right to left.
    compose_all(f, g, h)(x)  =  f(g(h(x)))
    """
    return reduce(compose, funcs)

print("\n-- 2. Variadic compose --")

process = compose_all(negate, square, increment)
# negate(square(increment(x)))
print(f"  negate∘square∘increment (4) = {process(4)}")    # negate(25) = -25
print(f"  negate∘square∘increment (0) = {process(0)}")    # negate(1)  = -1



# 3. Pipe order  -- left to right (easier to read as a pipeline)

def pipe(*funcs):
    """
    Apply funcs left to right: pipe(f, g, h)(x) = h(g(f(x))).
    Same result as compose_all with reversed argument order.
    """
    return reduce(lambda f, g: lambda x: g(f(x)), funcs)

print("\n-- 3. Pipe order (left to right) --")

pipeline = pipe(increment, square, negate)
# step 1: increment(x), step 2: square(that), step 3: negate(that)
print(f"  increment -> square -> negate (4) = {pipeline(4)}")   # -25
print(f"  increment -> square -> negate (0) = {pipeline(0)}")   # -1

# Reading left to right mirrors the data flow, which many find clearer.
clean = pipe(double, increment, square)
print(f"  double -> increment -> square (3) = {clean(3)}")   # (6+1)^2 = 49



# 4. Associativity

print("\n-- 4. Associativity --")

f, g, h = negate, square, increment

left  = compose(compose(f, g), h)   # (f ∘ g) ∘ h
right = compose(f, compose(g, h))   # f ∘ (g ∘ h)

for x in [0, 1, 4, -3]:
    assert left(x) == right(x), f"associativity failed at x={x}"
    print(f"  left({x}) = right({x}) = {left(x)}")

print("  associativity holds for all tested inputs")



# 5. Partial application as a composition building block

print("\n-- 5. Partial application --")

def add(a, b):    return a + b
def power(b, e):  return b ** e
def clamp(lo, hi, x): return max(lo, min(hi, x))

add5       = partial(add, 5)
cube       = partial(power, e=3)
clamp_0_10 = partial(clamp, 0, 10)

print(f"  add5(3)        = {add5(3)}")          # 8
print(f"  cube(4)        = {cube(4)}")          # 64
print(f"  clamp_0_10(15) = {clamp_0_10(15)}")   # 10
print(f"  clamp_0_10(-3) = {clamp_0_10(-3)}")   # 0

pipeline2 = pipe(add5, cube, clamp_0_10)
print(f"  add5 -> cube -> clamp_0_10 (0) = {pipeline2(0)}")   # clamp(125) = 10
print(f"  add5 -> cube -> clamp_0_10 (1) = {pipeline2(1)}")   # clamp(216) = 10
print(f"  add5 -> cube -> clamp_0_10 (-4) = {pipeline2(-4)}") # clamp(1)   = 1



# 6. Decorators as composition

print("\n-- 6. Decorators as composition --")

def logged(f):
    """Wrap f to print its input and output."""
    def wrapper(x):
        result = f(x)
        print(f"  {f.__name__}({x}) -> {result}")
        return result
    wrapper.__name__ = f"logged({f.__name__})"
    return wrapper

def memoised(f):
    """Wrap f to cache results for repeated inputs."""
    cache = {}
    def wrapper(x):
        if x not in cache:
            cache[x] = f(x)
        return cache[x]
    wrapper.__name__ = f"memoised({f.__name__})"
    return wrapper

# Using decorator syntax (which is just composition):
@logged
def triple(x):
    return x * 3

triple(5)    # logged(triple)(5)
triple(5)    # called again -- logged every time

# Compose manually for more control:
fast_square = memoised(logged(square))
fast_square(7)   # logs and caches
fast_square(7)   # cache hit, no log (result returned directly from cache)
fast_square(8)   # new input, logs again



# 7. Composing over a collection -- point-free style

print("\n-- 7. Point-free pipeline over a list --")

# "Point-free": we define what to do, not what to do it to.
transform = pipe(increment, square, negate)

nums    = [1, 2, 3, 4, 5]
results = list(map(transform, nums))

print(f"  input:  {nums}")
print(f"  output: {results}")
# increment -> square -> negate applied to each element



# 8. Extracting a sub-pipeline (associativity in practice)


print("\n-- 8. Refactoring by splitting the pipeline --")

# Full pipeline
full = pipe(increment, double, square, negate, halve)

# Refactored: split into two stages
pre  = pipe(increment, double, square)
post = pipe(negate, halve)
split = pipe(pre, post)

# Both must agree on all inputs
test_inputs = range(-5, 6)
for x in test_inputs:
    assert full(x) == split(x), f"mismatch at {x}"

print("  full(x) == split(x) for all x in -5..5 -- refactoring is safe")
print(f"  example: full(3) = {full(3)}, split(3) = {split(3)}")
