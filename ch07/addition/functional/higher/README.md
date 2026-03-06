
## 4. Higher-Order Functions


A higher-order function is a function that takes one or more functions as
arguments, returns a function as its result, or both. The three canonical
examples are `map`, `filter`, and `reduce`.

Higher-order functions are a direct consequence of functions being first-class.
Once a function is a value, you can do with it what you do with any value:
pass it somewhere and let something else decide when and how to call it.



### Why It Exists

An ordinary loop mixes two concerns: *how to iterate* and *what to do with
each element*. A higher-order function separates them. `map` owns the
iteration; the function you pass to it owns the transformation. Neither knows
anything about the other beyond the agreed-upon signature.

This separation has concrete effects:

- *Declarative style.* You say what you want, not how the loop should run.
- *Reduced mutation surface.* A map produces a new collection; the original
  is untouched. There is no loop variable to accidentally overwrite.
- *Pipeline reasoning.* A sequence of maps, filters, and reductions can be
  read left to right as a series of transformations. Each step is independent;
  you can verify each one in isolation.
- *Reuse.* The iteration logic is written once, in `map`. Every caller reuses
  it without re-implementing it.



### Python: The Exposition Language

#### map

`map(f, iterable)` applies `f` to every element and returns a lazy iterator
over the results:

```python
nums    = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x * x, nums))
# [1, 4, 9, 16, 25]
```

The transformation logic (`lambda x: x * x`) is completely separate from the
iteration logic (inside `map`). Swap in a different function, get a different
result -- no loop rewriting needed.

Named functions work equally well:

```python
def square(x): return x * x
def negate(x): return -x

print(list(map(square, nums)))   # [1, 4, 9, 16, 25]
print(list(map(negate, nums)))   # [-1, -2, -3, -4, -5]
```

#### filter

`filter(pred, iterable)` keeps only the elements for which `pred` returns
true:

```python
evens = list(filter(lambda x: x % 2 == 0, nums))
# [2, 4]
```

The predicate is a function of one argument returning a boolean. `filter`
does not know or care what the predicate tests; it only knows whether to keep
or discard each element.

#### reduce

`reduce(f, iterable, initial)` from `functools` collapses a sequence to a
single value by repeatedly applying `f` to an accumulator and the next
element:

```python
from functools import reduce

total  = reduce(lambda acc, x: acc + x, nums, 0)   # 15
product = reduce(lambda acc, x: acc * x, nums, 1)  # 120
```

`reduce` is the most general of the three. `map` and `filter` can both be
implemented in terms of `reduce`, though less readably.

#### Chaining into a Pipeline

Higher-order functions compose naturally. A pipeline reads as a left-to-right
sequence of transformations:

```python
from functools import reduce

nums = [1, 2, 3, 4, 5, 6, 7, 8]

result = reduce(
    lambda acc, x: acc + x,          # sum
    map(lambda x: x * x,             # square
        filter(lambda x: x % 2 == 0, # keep evens
               nums)),
    0
)
# evens: [2, 4, 6, 8]  -> squares: [4, 16, 36, 64]  -> sum: 120
print(result)   # 120
```

Or written with intermediate names for clarity:

```python
evens   = filter(lambda x: x % 2 == 0, nums)
squares = map(lambda x: x * x, evens)
total   = reduce(lambda acc, x: acc + x, squares, 0)
print(total)   # 120
```

#### Custom Higher-Order Functions

You are not limited to the three built-ins. Any function that receives a
function and applies it is higher-order:

```python
def apply_twice(f, x):
    return f(f(x))

print(apply_twice(square, 3))   # square(square(3)) = 81
print(apply_twice(negate, 5))   # negate(negate(5)) = 5

def take_while(pred, iterable):
    """Yield elements as long as pred holds; stop at the first failure."""
    for item in iterable:
        if not pred(item):
            break
        yield item

print(list(take_while(lambda x: x < 4, [1, 2, 3, 5, 2])))  # [1, 2, 3]
```

#### Sorting with a Key Function

`sorted` and `list.sort` both accept a `key` function -- a higher-order
interface built into the language:

```python
words = ["banana", "fig", "apple", "kiwi", "date"]
by_length = sorted(words, key=len)
# ['fig', 'kiwi', 'date', 'apple', 'banana']

by_last = sorted(words, key=lambda w: w[-1])
# sort by last character
```

The sort algorithm owns the comparison mechanics; the `key` function owns the
ordering criterion. Classic separation of concerns.



### Key Discussion Points

#### Declarative vs. Imperative

An imperative loop says *how*:

```python
result = []
for x in nums:
    if x % 2 == 0:
        result.append(x * x)
```

A higher-order pipeline says *what*:

```python
result = list(map(lambda x: x * x, filter(lambda x: x % 2 == 0, nums)))
```

Both produce the same result. The declarative version exposes less internal
machinery and provides fewer places for mutation bugs to hide.

#### Stateless Transformations

A function passed to `map` should ideally be stateless: given the same input,
it returns the same output, and it has no side effects. Stateless
transformations have a property that is critical for concurrency: each
element can be processed independently, in any order, including in parallel.

A stateful transformation -- one that reads or writes a shared variable --
breaks this property. The elements must then be processed in a specific order,
or with locks, or not at all in parallel.

#### No Lazy Evaluation by Default

Python's `map` and `filter` return iterators, not lists. They are lazy: they
produce elements on demand. This is a significant efficiency benefit for large
or infinite sequences -- the transformation runs only when a value is actually
consumed. Converting to a list with `list(...)` forces evaluation of the
entire sequence.

This laziness is a design choice, not a fundamental requirement of higher-order
functions. C's equivalent is eager by necessity: you must know the output size
to allocate memory.



### Under the Hood: C

C has no built-in `map`, `filter`, or `reduce`. Each must be written as a
function that accepts an array, its length, an output buffer, and a function
pointer.

#### map in C

```c
typedef int (*transform_fn)(int);

void map_int(const int *in, int *out, int n, transform_fn f) {
    for (int i = 0; i < n; i++)
        out[i] = f(in[i]);
}
```

The caller provides pre-allocated input and output arrays. `map_int` owns the
loop; `f` owns the per-element logic. The signature matches the Python idea
exactly -- the difference is that allocation, length, and lifetime are all
explicit.

#### filter in C

```c
typedef int (*predicate_fn)(int);

int filter_int(const int *in, int *out, int n, predicate_fn pred) {
    int count = 0;
    for (int i = 0; i < n; i++)
        if (pred(in[i]))
            out[i - (n - ++count)] = in[i];  /* compact into out */
    return count;   /* number of elements kept */
}
```

`filter` cannot know how many elements will pass the predicate before running.
Either the caller allocates `n` slots (pessimistic, safe) and uses the returned
count, or a dynamic structure is used. Python avoids this: the iterator just
produces elements on demand without pre-allocating.

#### reduce in C

```c
typedef int (*combine_fn)(int acc, int x);

int reduce_int(const int *in, int n, int initial, combine_fn f) {
    int acc = initial;
    for (int i = 0; i < n; i++)
        acc = f(acc, in[i]);
    return acc;
}
```

No allocation needed: `reduce` folds everything into one scalar.

#### No Implicit Closure

The C function pointer carries no environment. A predicate like "keep elements
greater than `threshold`" cannot be expressed as a plain `predicate_fn` if
`threshold` is not a compile-time constant. The standard workaround is a
context pointer:

```c
typedef int (*pred_with_ctx)(void *ctx, int x);

int filter_with_ctx(const int *in, int *out, int n,
                    pred_with_ctx pred, void *ctx) {
    int count = 0;
    for (int i = 0; i < n; i++)
        if (pred(ctx, in[i]))
            out[count++] = in[i];
    return count;
}
```

This is the closure pair from section 2 applied to higher-order functions. The
`(pred, ctx)` pair is a manual closure.



### Cost Model

| | Python | C |
|---|---|---|
| Iteration | inside `map` iterator | explicit loop |
| Per-element call | dynamic dispatch + frame | indirect call (function ptr) |
| Output allocation | lazy iterator (none until consumed) | caller-provided buffer |
| Closure support | built-in | (fn, ctx) pair manually |
| Parallelism | GIL limits real parallelism | pthreads or SIMD possible |

The Python pipeline is elegant but carries real overhead per element: object
allocation, reference counting, and dynamic dispatch at every step. For small
collections this is irrelevant. For large numerical data it matters, which is
why libraries like NumPy bypass Python's loop and dispatch entirely, operating
directly on contiguous memory with vectorised CPU instructions.

C's version is verbose but direct. The inner loop of `map_int` with a simple
`transform_fn` may be inlined by the compiler if the function pointer target
is visible at the call site -- though this is unusual for a runtime-passed
pointer.



### Concurrency Link

Stateless transformations are *embarrassingly parallel*: each element can be
processed independently with no communication between workers. A parallel
`map` over a large array needs no locks, no shared mutable state, no
coordination -- just a partition of the input.

```
thread 0: map f over arr[0   .. n/4-1]
thread 1: map f over arr[n/4 .. n/2-1]
thread 2: map f over arr[n/2 .. 3n/4-1]
thread 3: map f over arr[3n/4 .. n-1]
```

Each thread writes to its own slice of the output. As long as `f` is
stateless -- no shared mutable data, no side effects -- this is correct by
construction. No synchronisation needed during the map phase; a barrier at
the end suffices.

This is the data-parallel execution model used in GPU computing and SIMD
vectorisation. The language primitive is `map`; the hardware primitive is
applying the same operation to multiple data lanes simultaneously.

`filter` and `reduce` are harder to parallelise. Filter changes the output
length unpredictably; parallel filter typically uses a prefix-sum step to
determine output positions. Reduce is associative for addition and
multiplication, which allows a tree-structured parallel reduction -- but only
if the combining function is truly associative and the order of operations is
acceptable.



*Next: [5. Function Composition](../composition/README.md)--combining small
functions into larger ones without shared state or inheritance.*
