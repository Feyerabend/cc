
## 9. Referential Transparency


A function is *referentially transparent* if you can replace any call to it
with its return value without changing the meaning of the program. Same
arguments always produce the same result, and the function has no observable
side effects.

```python
# Referentially transparent: f(3) is always 9
def square(x): return x * x

# Not transparent: result changes between calls
import random
def random_add(x): return x + random.random()
```

You can substitute `square(3)` with `9` anywhere in a program and the program
behaves identically. You cannot do the same with `random_add(3)`.

This sounds like a narrow technical property. In practice it is the foundation
on which safe caching, equational reasoning, and parallel execution all rest.



### Why It Exists

*Equational reasoning.* In mathematics, you substitute equals for equals
freely. If `f(x) = x * x`, then wherever `f(3)` appears, `9` can appear
instead. Referential transparency brings that same substitution property to
code. You can reason about a program by rewriting it with known values, without
reading the full execution history.

*Safe caching.* If `f(x)` always returns the same value for a given `x`, you
can cache the result and never compute it again for that input. The cached
value is guaranteed to be correct--not just probably correct. This is
memoisation, and it is only sound when the function is referentially
transparent.

*Parallel execution.* Two calls `f(a)` and `f(b)` with a referentially
transparent `f` can run on separate threads without any coordination. They
share no state, produce no side effects, depend on nothing but their arguments.
You can schedule them in any order, simultaneously, on any number of cores,
and the result is always the same. This is the deepest link between functional
style and concurrency.



### What Breaks Referential Transparency

A function is *not* referentially transparent if it:

- reads or writes a global variable,
- reads from a mutable object that may have changed since the last call,
- reads from external state (time, random numbers, environment variables),
- writes output (I/O is a side effect),
- throws an exception that depends on something beyond the arguments,
- calls another non-transparent function.

The violation is always the same: the output is not fully determined by the
inputs. Something else contributes.



### Python: The Exposition Language

#### Pure vs. Impure

```python
# Pure: output determined entirely by input
def add(a, b):      return a + b
def factorial(n):   return 1 if n <= 1 else n * factorial(n - 1)
def to_upper(s):    return s.upper()
```

```python
# Impure: output depends on something beyond arguments
import random, time

counter = 0
def next_id():      global counter; counter += 1; return counter   # global state
def now():          return time.time()                              # clock
def roll():         return random.randint(1, 6)                    # random
def read_file(p):   return open(p).read()                          # I/O
```

None of the impure functions can be memoised safely. Calling `next_id()` twice
with no arguments returns different values; replacing the second call with the
result of the first would change program behaviour.

#### Equational Reasoning in Practice

When a function is referentially transparent, you can trace its behaviour by
substituting:

```python
def double(x):  return x * 2
def inc(x):     return x + 1

# We can reason:
# double(inc(3))
# = double(4)      [substitute inc(3) = 4]
# = 8              [substitute double(4) = 8]
```

This substitution chain is a proof that `double(inc(3)) == 8` -- not just for
this run, but for every run, in any context, with any other code around it.

With impure functions, this reasoning breaks down immediately:

```python
count = 0
def inc_global():
    global count
    count += 1
    return count

# inc_global() + inc_global()  ≠  2 * inc_global()
# First call: 1+2=3.  Second form: 2*3=6.  Not equal.
```

#### Memoisation as a Consequence

Memoisation is only correct when the function is referentially transparent:

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)

print(fib(40))   # computed once per n; subsequent calls return cached result
```

`@lru_cache` is a mechanical proof that `fib` is referentially transparent:
Python trusts that `fib(n)` will always return the same value for the same `n`.
If `fib` read a global, the cache would silently return stale results.

#### Hidden State Violations

A particularly subtle violation: a function that closes over mutable state.

```python
def make_accumulator():
    total = [0]
    def add(x):
        total[0] += x
        return total[0]
    return add

acc = make_accumulator()
print(acc(5))   # 5
print(acc(5))   # 10  -- same argument, different result
```

`acc(5)` is not referentially transparent: the result changes between calls
with the same argument. The mutable `total` cell is the hidden state.

#### Detecting Transparency Violations

The simplest test: call the function twice with identical arguments and check
that the results are identical *and* that nothing external changed.

```python
def is_transparent(f, *args):
    r1 = f(*args)
    r2 = f(*args)
    return r1 == r2

print(is_transparent(add, 3, 4))        # True
print(is_transparent(lambda: roll(), )) # probably False
```

This test is necessary but not sufficient: a function that mutates a global
but returns the same value (e.g., a logger) passes this test but is still
impure.



### Under the Hood: C

C makes it easy to write functions that violate referential transparency, and
easy to do so invisibly.

#### The errno Side Channel

```c
#include <math.h>
#include <errno.h>

double safe_log(double x) {
    errno = 0;
    double result = log(x);
    if (errno) return -1.0;   /* error case */
    return result;
}
```

`log` is not referentially transparent: it communicates errors through `errno`,
a global (or thread-local in POSIX) variable. Two calls to `log` with the same
argument may behave differently if `errno` was set between calls. The function's
observable effect extends beyond its return value.

#### Static Local Variables

```c
int next_id(void) {
    static int counter = 0;
    return ++counter;
}
```

`next_id()` is called with no arguments and returns a different value each
time. A static local variable is global state with a narrower scope--the
referential transparency violation is the same.

#### Global Mutation

```c
static int cache_valid = 0;
static double cached   = 0.0;

double expensive(double x) {
    if (cache_valid) return cached;     /* broken: ignores x */
    cached      = x * x;
    cache_valid = 1;
    return cached;
}
```

This attempted manual cache is incorrect: it caches the result of the first
call and returns it for all subsequent calls regardless of `x`. A referentially
transparent function cannot behave this way.

#### Compiler Optimisations Enabled by RT

The GCC and Clang compilers annotate functions that are referentially
transparent with two attributes:

```c
/* pure: result depends only on arguments and readable memory (no writes) */
int strlen_pure(const char *s) __attribute__((pure));

/* const: result depends only on arguments; reads no memory at all */
int square_const(int x) __attribute__((const));
```

With `__attribute__((const))`, the compiler is allowed to:

- Call the function once and reuse the result (common subexpression elimination).
- Hoist the call out of a loop if the argument does not change (loop-invariant
  code motion).
- Eliminate the call entirely if the result is unused.

Without this annotation, the compiler must assume the function might read or
write memory and cannot move or eliminate it. Referential transparency is the
property the compiler needs to perform these transformations safely.

#### Data Races as Referential Transparency Violations

A data race is a situation where two threads access the same memory location
and at least one access is a write, without synchronisation. A function that
participates in a data race is, by definition, not referentially transparent:
its result depends on which thread writes what and when--invisible to the
function signature.

```c
static int shared = 0;

int increment_shared(void) {
    return ++shared;    /* NOT thread-safe; NOT referentially transparent */
}
```

Two threads calling `increment_shared()` concurrently will produce results
that depend on the interleaving. The output is not determined by the arguments
(there are none)--it is determined by the scheduler.

This is the direct link between referential transparency and concurrency: a
function that is referentially transparent cannot participate in a data race,
because a data race requires that the function's output depend on external
mutable state, which is exactly what referential transparency forbids.

#### Undefined Behaviour

C's undefined behaviour (UB) is closely related. A function that invokes UB
(signed integer overflow, out-of-bounds access, use-after-free) produces a
result that is not determined by its arguments--it is determined by the
compiler's optimisation choices and the memory layout at runtime. UB is a
referential transparency violation enforced by the hardware and the compiler
rather than by program logic.

The compiler is permitted to assume UB never occurs. If it occurs, all bets
are off: the function no longer has a well-defined return value at all.



### The Bridge

This section sits at the boundary between functional patterns and low-level
concurrency. The connection is:
1. *Functional style* encourages referentially transparent functions.
2. *Referentially transparent functions* share no mutable state.
3. *No shared mutable state* means no data races.
4. *No data races* means no need for locks for those functions.
5. *No locks* means those functions compose freely across threads.

The previous eight sections describe how to write code in a referentially
transparent style. This section explains why that style matters for programs
that run on real hardware with real concurrency.

The next sections follow this bridge into cost models, persistent data
structures, and the integrative chapter that connects functional discipline
to concurrency correctness.



*Next: [10. Persistent Data Structures](../persistent/README.md)--structural
sharing as the efficient implementation of immutability at scale.*
