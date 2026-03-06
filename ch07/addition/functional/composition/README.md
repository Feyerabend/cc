
## 5. Function Composition


Function composition is the act of combining two or more functions so that the
output of one becomes the input of the next. If `f` and `g` are functions,
their composition `f ∘ g` is the function that applies `g` first, then passes
the result to `f`:

```
(f ∘ g)(x)  =  f(g(x))
```

In code:

```python
def compose(f, g):
    return lambda x: f(g(x))
```

The result is a new function. It is not a loop, not a class, not a protocol.
It is just a function built from two smaller functions.



### Why It Exists

A large function is hard to reason about in isolation. Its correctness depends
on the interaction of every line it contains. A composed function is different:
if `g` is correct for all inputs, and `f` is correct for all outputs of `g`,
then `f ∘ g` is correct. *Local correctness implies global correctness.* This
is the core argument for composition.

The consequence is a different way of building programs:
- Write small functions that each do one thing and are easy to verify.
- Compose them into larger functions.
- The composed functions are correct if the components are correct.

This eliminates entire categories of bugs that arise from tangled logic.
It also eliminates the need for inheritance hierarchies built to share and
combine behavior: composition does that without coupling types to each other.



### Python: The Exposition Language

#### Binary compose

```python
def compose(f, g):
    """Return the function x -> f(g(x))."""
    return lambda x: f(g(x))
```

```python
def square(x):    return x * x
def increment(x): return x + 1
def negate(x):    return -x

inc_then_square = compose(square, increment)   # square(increment(x))
print(inc_then_square(4))   # square(5) = 25

square_then_negate = compose(negate, square)
print(square_then_negate(3))   # negate(9) = -9
```

Order matters: `compose(f, g)` applies `g` first. This matches mathematical
convention where `f ∘ g` means "first `g`, then `f`". Some prefer the
reversed reading -- "pipe" order, left to right. Both are valid; be explicit.

#### Variadic compose

Composing many functions at once:

```python
from functools import reduce

def compose_all(*funcs):
    """
    Return the composition of all funcs, applied right to left.
    compose_all(f, g, h)(x)  =  f(g(h(x)))
    """
    return reduce(compose, funcs)
```

```python
process = compose_all(negate, square, increment)
print(process(4))   # negate(square(increment(4))) = negate(25) = -25
```

#### Pipe order (left to right)

When reading a pipeline left to right is more natural, reverse the composition:

```python
def pipe(*funcs):
    """Apply funcs left to right: pipe(f, g, h)(x) = h(g(f(x)))."""
    return reduce(lambda f, g: lambda x: g(f(x)), funcs)

process = pipe(increment, square, negate)
print(process(4))   # negate(square(increment(4))) = -25
```

`pipe` and `compose_all` produce the same result when the function list is
reversed. Which to use is a matter of readability at the call site.

#### Composition is associative

```python
f = negate
g = square
h = increment

left  = compose(compose(f, g), h)   # (f ∘ g) ∘ h
right = compose(f, compose(g, h))   # f ∘ (g ∘ h)

print(left(4))    # -25
print(right(4))   # -25
```

Associativity means the grouping of compositions does not matter--only the
order of application. This is not just a curiosity: it means you can
restructure composed pipelines freely without changing semantics, which is
what makes refactoring safe.

#### Partial application as composition building block

Partial application fixes some arguments of a function, producing a new
function of the remaining arguments. It is a key tool for building composable
pieces:

```python
from functools import partial

def add(a, b):   return a + b
def power(b, e): return b ** e

add5    = partial(add, 5)       # add5(x) = x + 5
square2 = partial(power, e=2)   # square2(b) = b ** 2

pipeline = pipe(add5, square2, negate)
print(pipeline(3))   # negate((3+5)^2) = negate(64) = -64
```

`partial` lets you adapt multi-argument functions into single-argument
functions suitable for composition.

#### Decorators as composition

Python decorators are syntactic sugar for function composition:

```python
def logged(f):
    def wrapper(x):
        result = f(x)
        print(f"  {f.__name__}({x}) = {result}")
        return result
    return wrapper

def timed(f):
    import time
    def wrapper(x):
        t0 = time.perf_counter()
        result = f(x)
        print(f"  {f.__name__} took {(time.perf_counter()-t0)*1e6:.1f} µs")
        return result
    return wrapper

@logged
@timed
def square(x):
    return x * x

square(7)
# timed wrapper runs first (innermost), then logged wrapper
```

`@logged @timed def square` is exactly `square = logged(timed(square))` --
composition written with syntax.



### Key Discussion Points

#### Small units of reasoning

A function of five lines with one responsibility is easy to test and verify.
A function of fifty lines with five responsibilities is not. Composition keeps
the units small. The complexity of a composed system grows with the number of
components, not with the product of their interactions--as long as each
component is truly independent.

#### No inheritance needed

In object-oriented design, behavior is often shared by putting it in a base
class and inheriting it. This creates coupling: the derived class depends on
the base class's implementation, and changes to the base affect all derived
classes. Composition avoids this entirely. `compose(logged, timed)` combines
behaviors without making either function know about the other.

#### Associativity and refactoring

Because composition is associative, you can split a long pipeline at any point:

```python
# Original
process = pipe(a, b, c, d, e)

# Refactored: extract a sub-pipeline
pre  = pipe(a, b, c)
post = pipe(d, e)
process = pipe(pre, post)   # same result
```

This is the compositional analogue of algebraic simplification. It works
without touching the implementations of `a` through `e`.



### Under the Hood: C

In C, function composition requires stacking closure pairs: each composed
function carries a pointer to the next function and its context.

#### Composing two function pointers

For pure functions (no context), composition is straightforward:

```c
typedef int (*unary_int)(int);

typedef struct {
    unary_int f;
    unary_int g;
} compose_ctx;

int compose_fn(void *ctx, int x) {
    compose_ctx *c = (compose_ctx *)ctx;
    return c->f(c->g(x));   /* apply g first, then f */
}
```

A composed function is itself a closure: a `(compose_fn, compose_ctx*)` pair.
To compose three functions you nest two such pairs.

#### Context stacking

Each level of composition adds one struct and two pointers to the call:

```
compose(f, compose(g, h)):

  call compose_outer.fn(ctx_outer, x)
    -> calls ctx_outer.g = compose_inner.fn(ctx_inner, x)
      -> calls ctx_inner.g = h(x)          // one indirection
      -> calls ctx_inner.f = g(result)     // one indirection
    -> calls ctx_outer.f = f(result)       // one indirection
```

Three functions composed: three indirect calls, three context loads. Each
level of composition adds one indirect call. This is the cost model of
composition in C.

#### Cost model

| Depth | Direct calls | Indirect calls | Context loads |
|-------|--------------|----------------|---------------|
| 1 function | 1 | 0 | 0 |
| 2 composed | 0 | 2 | 2 |
| 3 composed | 0 | 3 | 3 |
| n composed | 0 | n | n |

A Python composition pays the same indirection cost plus Python's per-call
overhead (frame allocation, reference counting, dictionary dispatch). The
indirection cost of a function pointer call is small in absolute terms--one
extra memory load--but it blocks the compiler from inlining and the CPU from
predicting the branch.

If the composed functions are known at compile time (i.e., inlinable), a
sufficiently smart C compiler can collapse the chain into a direct sequence of
operations with no indirection at all. This is the best case: zero overhead,
same semantics. It requires the function addresses to be visible to the
optimiser at the point of the composed call.



### Concurrency Link

Composition and immutability together enable *deterministic pipelines*. Each
stage of a composed pipeline:
- receives its input (immutable, from the previous stage),
- produces its output (a new value, passed to the next stage),
- has no side effects, no shared state, no synchronisation requirements.

A pipeline composed of pure functions is deterministic: the same input always
produces the same output, regardless of scheduling, thread interleaving, or
execution order of unrelated work. This is not a claim about speed--it is a
claim about *correctness under concurrency*.

Two independent composed pipelines can run on separate threads without any
coordination:

```
thread 0: pipe(f, g, h)(input_0)  -->  result_0
thread 1: pipe(f, g, h)(input_1)  -->  result_1
```

They share the function objects (read-only) but not the data. No lock is
needed because there is nothing to protect. Determinism is free.

The converse is also instructive: a pipeline with *any* mutable shared state
loses this property entirely. One stateful stage makes the whole pipeline's
output depend on execution order.



*Next: [6. Lazy Evaluation](../lazy/README.md)--deferred computation,
generators, and why producing values on demand changes the cost model.*
