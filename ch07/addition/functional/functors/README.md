
## 7. Functors (Mapped Contexts)


A functor is any container--any context--that supports a `map` operation.
`map` applies a function to the value *inside* the container and returns a new
container of the same shape, with the transformed value inside.

The simplest statement: a functor is something you can map over.

You already know one: a list. `map(f, [1, 2, 3])` applies `f` to each element
and returns a new list of the same length. The container shape (a list of three
elements) is preserved; only the values inside change.

The insight is that this pattern generalises far beyond lists.



### Why It Exists

Different containers carry different semantics:
- A list carries *zero or more* values.
- A `Maybe` carries *zero or one* value (a value that might be absent).
- A `Result` carries either a *success value* or an *error*.
- A tree carries values *at every node*.

In each case, you frequently want to transform the value inside without
changing the container structure or manually unpacking and repacking it. The
functor interface gives every container a uniform `map` operation that handles
the unpacking/repacking internally.

The result is that transformation logic (the function you pass) is decoupled
from the container logic (how the container maps over itself). You write `f`
once; it works with any functor, not just lists.

Note: this section deliberately avoids category theory. The word "functor"
comes from mathematics, but the programming concept needs no mathematical
background to understand or use. Think of it as: *a box that knows how to
apply a function to whatever is inside it*.



### Python: The Exposition Language

#### The Simplest Functor: Box

```python
class Box:
    def __init__(self, value):
        self._value = value

    def map(self, f):
        return Box(f(self._value))

    def __repr__(self):
        return f"Box({self._value!r})"
```

```python
b = Box(5)
print(b.map(lambda x: x * x))   # Box(25)
print(b.map(str).map(len))      # Box(1) -- chained maps
```

`map` always returns a new `Box`. The original is untouched. Chaining maps
is natural because each result is also a `Box`.

#### The Maybe Functor

`Maybe` represents a value that might be absent. It has two states: `Just(value)`
and `Nothing`. The crucial property: `map` on `Nothing` stays `Nothing`--the
absent value propagates silently, without any `if` check in the caller.

```python
class Maybe:
    def __init__(self, value):
        self._value = value            # None means Nothing

    @classmethod
    def just(cls, value):  return cls(value)
    @classmethod
    def nothing(cls):      return cls(None)

    def is_nothing(self):  return self._value is None

    def map(self, f):
        if self.is_nothing():
            return Maybe.nothing()     # propagate absence
        return Maybe.just(f(self._value))

    def __repr__(self):
        if self.is_nothing(): return "Nothing"
        return f"Just({self._value!r})"
```

```python
just5   = Maybe.just(5)
nothing = Maybe.nothing()

print(just5.map(lambda x: x * 2))     # Just(10)
print(nothing.map(lambda x: x * 2))   # Nothing

# Chained maps: if any step produces Nothing, all subsequent maps are no-ops
print(just5
      .map(lambda x: x - 3)           # Just(2)
      .map(lambda x: x * 10)          # Just(20)
      .map(str))                       # Just('20')

print(Maybe.just(0)
      .map(lambda x: None if x == 0 else 100 // x)   # None -> Nothing path
      .map(lambda x: x + 1))          # skipped
```

Without `Maybe`, every caller of a function that might return "no value" must
write an `if result is None` check before using the result. With `Maybe`, the
absence propagates through map chains automatically. The check is inside `map`,
written once.

#### The Result Functor

`Result` carries either a success value (`Ok`) or an error (`Err`). `map`
transforms the success value and passes errors through untouched:

```python
class Result:
    def __init__(self, value, error):
        self._value = value
        self._error = error

    @classmethod
    def ok(cls, value):   return cls(value, None)
    @classmethod
    def err(cls, error):  return cls(None, error)

    def is_ok(self):      return self._error is None

    def map(self, f):
        if not self.is_ok():
            return Result.err(self._error)    # pass error through
        return Result.ok(f(self._value))

    def __repr__(self):
        if self.is_ok(): return f"Ok({self._value!r})"
        return f"Err({self._error!r})"
```

```python
ok10  = Result.ok(10)
fail  = Result.err("network timeout")

print(ok10.map(lambda x: x * 3))       # Ok(30)
print(fail.map(lambda x: x * 3))       # Err('network timeout')

# Processing pipeline: error short-circuits cleanly
def parse_int(s):
    try:    return Result.ok(int(s))
    except: return Result.err(f"cannot parse {s!r}")

print(parse_int("42").map(lambda x: x * 2))    # Ok(84)
print(parse_int("??").map(lambda x: x * 2))    # Err("cannot parse '??'")
```

The error propagation is free: once `Err` is produced, all subsequent `map`
calls are no-ops. No exception handling, no `if` cascades.

#### The List Functor

A list is a functor. Python's `map` is its `fmap`:

```python
nums = [1, 2, 3, 4, 5]
print(list(map(lambda x: x * x, nums)))   # [1, 4, 9, 16, 25]
```

We can give list a `map` method to make the functor interface uniform:

```python
class FList(list):
    def map(self, f):
        return FList(f(x) for x in self)

fl = FList([1, 2, 3, 4])
print(fl.map(lambda x: x * 2).map(str))   # FList(['2', '4', '6', '8'])
```

#### The Tree Functor

A binary tree where `map` applies a function to every leaf value:

```python
class Tree:
    def __init__(self, value=None, left=None, right=None):
        self.value = value
        self.left  = left
        self.right = right
        self.is_leaf = (left is None and right is None)

    def map(self, f):
        if self.is_leaf:
            return Tree(f(self.value))
        return Tree(
            left  = self.left.map(f)  if self.left  else None,
            right = self.right.map(f) if self.right else None,
        )

    def leaves(self):
        if self.is_leaf: return [self.value]
        result = []
        if self.left:  result += self.left.leaves()
        if self.right: result += self.right.leaves()
        return result
```

```python
#       *
#      / \
#     *   5
#    / \
#   2   3
tree = Tree(left=Tree(left=Tree(2), right=Tree(3)), right=Tree(5))
doubled = tree.map(lambda x: x * 2)
print(doubled.leaves())   # [4, 6, 10]
```

The tree's structure is preserved. Only the leaf values change. The branching
logic lives in `Tree.map`, not in the caller.



### The Functor Laws

Two laws define whether something truly is a functor. They are not enforced by
Python, but you can verify them:

*Identity law:* mapping the identity function does nothing.

```python
identity = lambda x: x
assert Box(42).map(identity)._value == Box(42)._value
```

*Composition law:* mapping `f` then `g` is the same as mapping `f ∘ g`.

```python
f = lambda x: x * 2
g = lambda x: x + 1

b = Box(5)
assert b.map(f).map(g)._value == b.map(lambda x: g(f(x)))._value
```

If your `map` satisfies both laws, it is a genuine functor. If it does not--for
example if `map` has side effects or reorders elements--the abstraction
breaks and callers cannot reason about its behaviour generically.



### Why Not in C

C can represent the functor idea--but at a painful cost.

To write a single `map` function that works over a `Maybe` *and* a `Result`
*and* a `Tree`, you need either:

- A separate `map` function for each type (maximum verbosity, zero reuse).
- A `void*` interface with explicit type tags and casts (error-prone, no
  type safety).
- A macro that generates a `map` function for each type (preprocessor abuse,
  hard to debug).

C has none of the mechanisms that make functors practical:

- No generics / templates (no parametric polymorphism).
- No type classes or interfaces (no way to say "this type has a `map`").
- No garbage collection (manual lifetime for every boxed value).

The absence of these features is not a deficiency for C's intended domain
(systems programming close to hardware). But it is the reason functional
abstractions like functors, and the next section's monads, are rare in C and
natural in languages that have generics or type classes.

In C++ (with templates) or Rust (with traits), the functor pattern is
expressible cleanly. In C, the honest answer is: write the specific function
you need for the specific type you have, and do not try to build a generic
container hierarchy.



### Concurrency Link

A functor's `map` operation is pure: it takes an immutable container, applies
a function, and returns a new container. The original is untouched.

This means all the properties of pure functions apply: two threads can map
over the same functor simultaneously, safely, with no locking. A `Maybe` that
holds a configuration value can be mapped in parallel by many workers without
coordination, because `map` never mutates the original.

The composition law also ensures determinism: the result of a mapped functor
depends only on the input value and the function, never on when or in what
order the map runs. For concurrent systems, this is precisely the guarantee
you want: local reasoning implies global correctness.



*Next: [8. Monads](../monads/README.md)--structured composition of
computations that carry a context, and why that makes error handling and
effect management explicit.*
