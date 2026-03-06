
## 3. Immutability


Immutability means that a value cannot be changed after it is created. Once
constructed, it is fixed. Code that receives an immutable value can rely on it
remaining what it was when received--no matter what other code runs
concurrently, and no matter how many other references to the same value exist.

This is a much stronger guarantee than "I happen not to change it". Immutability
is enforced by the language or by design, not by convention.



### Why It Exists

Mutation is the primary source of coupling between otherwise unrelated parts of
a program. When a function modifies a value, every other piece of code that
holds a reference to that value is affected. The mutation is a hidden
communication channel--invisible in the type, invisible in the call signature,
visible only if you happen to read the right function body at the right time.

Immutability severs that channel. If data cannot be changed, sharing it is safe.
Multiple threads can read the same value simultaneously without locking. A
function can pass a value to another function without worrying that the other
function will change it under it. Caching is safe: the cached result will always
match a future call with the same input.

Three concrete benefits:

- *Simplifies reasoning.* You can substitute a value for any expression that
  produced it. The value at line 10 is still the same value at line 200.
- *Eliminates data races.* A race requires at least one write. No writes, no
  race.
- *Enables safe sharing.* Multiple owners, zero locks, no copies needed.



### Python: The Exposition Language

#### What Python Makes Immutable

Python has a handful of built-in immutable types: `int`, `float`, `bool`,
`str`, `bytes`, `tuple`, `frozenset`. Once created, their contents cannot be
changed.

```python
t = (1, 2, 3)
# t[0] = 9 --TypeError: 'tuple' object does not support item assignment

s = "hello"
# s[0] = "H" --TypeError: 'str' object does not support item assignment
```

What Python does *not* make immutable: `list`, `dict`, `set`, and any
user-defined class by default. These are mutable, and that mutability is
often the source of subtle bugs.

#### The Mutable Shared List Problem

```python
def add_item(collection, item):
    collection.append(item)   # mutates the caller's list
    return collection

original = [1, 2, 3]
result = add_item(original, 4)

print(original)   # [1, 2, 3, 4] --original was changed
print(result is original)   # True --same object
```

The caller passed a list and got it back modified. If `original` is shared
between threads, this is a data race. If it is used elsewhere in the program
after the call, the caller's reasoning about its value is now wrong.

#### The Immutable Style: Return a New Value

```python
def add_item(collection, item):
    return collection + [item]   # creates a new list

original = [1, 2, 3]
result = add_item(original, 4)

print(original)   # [1, 2, 3] --unchanged
print(result)     # [1, 2, 3, 4]
print(result is original)   # False --distinct objects
```

The function now has no side effects. `original` is safe to share. The result
is a new value, not a modification of an existing one.

#### Tuples as Immutable Records

```python
Point = tuple   # just for naming clarity

def translate(p, dx, dy):
    return (p[0] + dx, p[1] + dy)

origin = (0, 0)
moved  = translate(origin, 3, 4)

print(origin)   # (0, 0) --untouched
print(moved)    # (3, 4)
```

A tuple is a natural immutable record. Operations on it always produce new
tuples; the original is unaffected.

For more expressive records, use `collections.namedtuple` or
`dataclasses.dataclass(frozen=True)`:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def translate(self, dx, dy):
        return Point(self.x + dx, self.y + dy)

p = Point(0, 0)
q = p.translate(3, 4)

print(p)   # Point(x=0, y=0) --unchanged
print(q)   # Point(x=3, y=4)
# p.x = 9 --FrozenInstanceError
```

`frozen=True` makes the dataclass reject attribute assignment after
construction. The object is immutable by enforcement, not by convention.

#### Shallow vs. Deep Immutability

Python's immutability is *shallow*. A tuple is immutable, but if it contains
a list, that list is still mutable:

```python
t = ([1, 2], [3, 4])
t[0].append(99)   # this works
print(t)          # ([1, 2, 99], [3, 4])
```

The tuple itself cannot be rebound, but its contents can be changed through
the mutable list references it holds. True deep immutability requires that
every value reachable from the root also be immutable. In Python this must be
designed in, it is not automatic.



### Key Discussion Points

#### Immutability vs. Const

"Immutable" and "`const`" are related but not the same. `const` in C (and
`const` references in C++) is a promise about *one path of access*--it does
not prevent the value from being changed through another path. Immutability
is a property of the *value itself*.

#### Copy vs. Structural Sharing

The obvious cost of immutability is copying. Instead of mutating a list of
one million elements, you create a new list of one million elements. That is
expensive.

Persistent data structures solve this with *structural sharing*: the new
version of the structure reuses as much of the old one as possible, copying
only the parts that changed. A persistent list that appends one element might
share all of the original million elements and add only a small new node.
This is the subject of section 10.

For now, the simple rule is: immutability is cheap when values are small or
when sharing is managed, and expensive when it requires naive full copies.

#### Immutability and Equational Reasoning

When values are immutable, you can replace any expression with the value it
evaluates to without changing the meaning of the program. This is *equational
reasoning*, and it is what makes functional code easier to test, optimize,
and refactor. The compiler can also exploit it: a pure function called twice
with the same immutable input can have its second call eliminated entirely.



### Under the Hood: C

C does not enforce immutability at the language level in the way a functional
language does. It offers two partial tools: `const` and copying.

#### const Correctness

```c
void print_point(const int *p) {
    printf("(%d, %d)\n", p[0], p[1]);
    /* p[0] = 9; --compile error through this pointer */
}
```

`const int *p` says: through *this pointer*, the pointed-to data is read-only.
It does not say the data is immutable. Another pointer to the same memory
without `const` can still write to it:

```c
int coords[2] = { 3, 4 };
int *mutable_alias = coords;
const int *immutable_view = coords;

mutable_alias[0] = 99;   /* legal */
/* immutable_view[0] = 99; --illegal through this pointer */
printf("%d\n", immutable_view[0]);   /* 99--the value changed anyway */
```

`const` is a contract about access paths, not about values.

#### Immutable by Copy

The only way to guarantee a value will not change in C is to copy it so that
no other code can reach the original through your copy:

```c
typedef struct { int x; int y; } point_t;

point_t translate(point_t p, int dx, int dy) {
    /* p is a copy; the caller's original is untouched */
    return (point_t){ p.x + dx, p.y + dy };
}
```

Passing a struct by value copies it. Returning a struct by value copies the
result. No heap allocation, no shared pointer, no aliasing. This is the C
equivalent of immutable-style programming for small values.

For large structures, copying is expensive. The C programmer then chooses
between:

- Accepting the cost and making a full copy.
- Using `const` pointers and trusting the contract.
- Implementing structural sharing manually (copy-on-write, reference
  counting)--which is what persistent data structures require.

#### The Connection to Data Races

A data race in C requires two threads to access the same memory location with
at least one write. If data is never written after construction, races on that
data are impossible by definition. No mutex, no atomic, no memory barrier
needed for read-only data.

```c
/* Safe to read from multiple threads simultaneously,
   because it is never written after initialisation. */
static const int lookup_table[256] = { /* ... */ };
```

`static const` at file scope is the strongest immutability C offers: the
linker places the data in a read-only segment, and the OS may enforce that
with page protection. A write attempt causes a segmentation fault rather than
silent corruption.

#### Structural Sharing in C

Structural sharing--the technique that makes persistent data structures
efficient--requires careful memory management in C:

- Reference counting to track when nodes are no longer needed.
- Copy-on-write to delay copying until a modification is actually needed.
- A custom allocator to make node allocation fast.

None of these are provided by the language. Each must be implemented by hand,
and each introduces new failure modes (use-after-free, double-free, counting
errors). This is why persistent data structures are rare in C and common in
garbage-collected languages.



### Cost Model

| Operation | Python (mutable) | Python (immutable) | C (copy) | C (const ptr) |
|-----------|------------------|--------------------|----------|---------------|
| Read      | one deref        | one deref          | direct   | one deref     |
| Write     | one deref        | not allowed        | copy     | not allowed*  |
| Share     | pointer          | pointer            | copy     | pointer       |
| Thread safety | needs lock   | safe               | safe     | needs lock*   |

*`const` does not prevent writes through other pointers.

The immutable read path is identical in cost to the mutable read path. The
cost appears only when you would have mutated: instead, you produce a new
value. How expensive that is depends entirely on the size of the value and
whether structural sharing is available.



### Concurrency Link

Immutability is the simplest solution to the problem of shared mutable state.
If state is not mutable, it can be shared without coordination.

In the memory model of modern CPUs, writes require cache coherence traffic:
the writing core must acquire ownership of the cache line, invalidating
copies in other cores. A value that is never written generates no coherence
traffic after its initial placement. Multiple cores reading the same immutable
value in their local caches is the cheapest possible form of sharing.

Memory barriers--the fences that enforce ordering of reads and writes across
cores--are needed only when writes occur. A program composed entirely of
reads of immutable data after an initial write phase needs barriers only at
the boundary between the write phase and the read phase, not throughout the
concurrent section.

This is not a theoretical benefit. High-performance systems deliberately
separate a configuration or initialisation phase (writes, single-threaded)
from a serving phase (reads, multi-threaded) precisely to exploit this
property.



*Next: [4. Higher-Order Functions](../higher/README.md)--functions that take
or return other functions, and why that separates iteration from transformation.*
