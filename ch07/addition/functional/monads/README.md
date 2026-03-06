
## 8. Monads (Effect Management)


Section 7 showed that a functor is a container with a `map` operation. `map`
takes a plain function (`A -> B`) and lifts it into the container
(`M[A] -> M[B]`).

A monad is a functor with one additional operation: `bind` (also called
`flat_map`, `and_then`, or `>>=`). `bind` handles a different case: what if
the function you want to apply *itself* returns a container?

```
map:   f : A -> B        lifts to  M[A] -> M[B]
bind:  f : A -> M[B]     gives     M[A] -> M[B]
```

Without `bind`, applying an `A -> M[B]` function through `map` would produce
`M[M[B]]`--a doubly-wrapped value. `bind` unwraps the outer layer and
returns a flat `M[B]`. This "unwrapping" is the operation that makes monads
useful for chaining computations that each produce effects.



### Why It Exists

Many real computations are not pure functions from A to B. They:
- might fail (return an error instead of a value),
- might produce no result (return absence),
- carry state that must be threaded through,
- perform I/O whose ordering must be controlled,
- involve async steps that must complete before the next begins.

Each of these is an *effect*: something beyond the plain computation of a
return value. Monads are a way to structure the composition of effectful
computations so that the effect-handling code is written once (inside `bind`)
and reused everywhere, rather than scattered across every call site.

Without monads, composing fallible functions looks like this:

```python
result = step_one(input)
if result is None: return None
result = step_two(result)
if result is None: return None
result = step_three(result)
if result is None: return None
```

With a monad, the same logic is:

```python
result = (Maybe.just(input)
          .bind(step_one)
          .bind(step_two)
          .bind(step_three))
```

The `None`-check is inside `bind`, written once. The call sites are clean.



### The Two Monad Operations

Every monad provides exactly two operations:

*`return` (or `unit`, or `just`):* wrap a plain value in the context.
```python
Maybe.just(5)    # wrap 5 in Maybe context
Result.ok(5)     # wrap 5 in Result context
```

*`bind` (or `and_then`):* apply a function that returns a wrapped value, and
flatten the result.
```python
Maybe.just(5).bind(f)    # f: int -> Maybe[int]
Result.ok(5).bind(g)     # g: int -> Result[int, err]
```

The container is responsible for the effect. `Maybe.bind` handles the
Nothing case. `Result.bind` handles the Err case. The caller only writes the
happy-path function and the monad handles the rest.



### Python: The Exposition Language

#### The Problem: map on a function that returns Maybe

```python
def safe_reciprocal(x):
    if x == 0: return Maybe.nothing()
    return Maybe.just(1.0 / x)
```

What happens if we use `map`?

```python
result = Maybe.just(4).map(safe_reciprocal)
# result is Just(Just(0.25)) -- doubly wrapped!
```

`map` wraps the result of `safe_reciprocal` (which is already a `Maybe`)
inside another `Maybe`. We get `Just(Just(0.25))`--a `Maybe[Maybe[float]]`.
That is not what we want.

`bind` flattens it:

```python
result = Maybe.just(4).bind(safe_reciprocal)
# result is Just(0.25) -- correctly flat
```

#### Maybe Monad

```python
class Maybe:
    def __init__(self, value, present):
        self._value   = value
        self._present = present

    @classmethod
    def just(cls, value): return cls(value, True)
    @classmethod
    def nothing(cls):     return cls(None, False)

    def map(self, f):
        if not self._present: return Maybe.nothing()
        return Maybe.just(f(self._value))

    def bind(self, f):
        """f: A -> Maybe[B].  Unwraps and applies; propagates Nothing."""
        if not self._present: return Maybe.nothing()
        return f(self._value)           # f already returns a Maybe

    def get_or(self, default):
        return self._value if self._present else default
```

Chaining fallible lookups:

```python
users = {1: {'name': 'Alice', 'address_id': 10}}
addrs = {10: {'city': 'Berlin', 'zip_id': 20}}
zips  = {20: '10115'}

def get_user(uid):  return Maybe.just(users[uid]) if uid in users else Maybe.nothing()
def get_address(u): return Maybe.just(addrs[u['address_id']]) if u['address_id'] in addrs else Maybe.nothing()
def get_zip(a):     return Maybe.just(zips[a['zip_id']]) if a['zip_id'] in zips else Maybe.nothing()

# Bind chain: each step only runs if the previous succeeded
result = (Maybe.just(1)
          .bind(get_user)
          .bind(get_address)
          .bind(get_zip))
print(result.get_or('unknown'))   # '10115'

# Missing user -- Nothing propagates through all remaining binds
result = (Maybe.just(99)
          .bind(get_user)
          .bind(get_address)
          .bind(get_zip))
print(result.get_or('unknown'))   # 'unknown'
```

Every bind in the chain is a no-op if the value is `Nothing`. The chain
terminates cleanly without any conditional logic at the call site.

#### Result Monad

`Result` carries either a value (`Ok`) or an error (`Err`). `bind` passes
errors through, transforming only successes:

```python
class Result:
    def __init__(self, value, error):
        self._value = value
        self._error = error

    @classmethod
    def ok(cls, v):   return cls(v, None)
    @classmethod
    def err(cls, e):  return cls(None, e)

    def is_ok(self):  return self._error is None

    def map(self, f):
        if not self.is_ok(): return self
        return Result.ok(f(self._value))

    def bind(self, f):
        """f: A -> Result[B, E].  Chains fallible computations."""
        if not self.is_ok(): return self
        return f(self._value)
```

A processing pipeline:

```python
def parse_int(s):
    try:    return Result.ok(int(s))
    except: return Result.err(f"not an integer: {s!r}")

def check_positive(n):
    if n <= 0: return Result.err(f"{n} is not positive")
    return Result.ok(n)

def check_small(n):
    if n > 100: return Result.err(f"{n} exceeds limit of 100")
    return Result.ok(n)

def process(s):
    return (Result.ok(s)
            .bind(parse_int)
            .bind(check_positive)
            .bind(check_small))

print(process("42"))    # Ok(42)
print(process("-5"))    # Err('-5 is not positive')
print(process("999"))   # Err('999 exceeds limit of 100')
print(process("??"))    # Err("not an integer: '??'")
```

Each bind step is tried only if the previous succeeded. The first failure
short-circuits the remainder. One error path; zero conditional logic at the
call site.

#### The C-Style Equivalent

```python
def process_imperative(s):
    try:    n = int(s)
    except: return None, f"not an integer: {s!r}"

    if n <= 0:   return None, f"{n} is not positive"
    if n > 100:  return None, f"{n} exceeds limit of 100"
    return n, None

value, error = process_imperative("42")
if error: print(f"error: {error}")
else:     print(f"value: {value}")
```

This is the manual version. Every step must explicitly check the previous
result before continuing. The error-handling logic is woven through the
business logic. As the chain grows, the ratio of error-handling to
business-logic lines increases.

#### State Monad (Brief)

A `State` monad threads an implicit state value through a chain of
computations, without passing it explicitly at every call:

```python
class State:
    """Wraps a function: state -> (value, new_state)."""
    def __init__(self, run):
        self._run = run

    @classmethod
    def unit(cls, value):
        return cls(lambda state: (value, state))

    def bind(self, f):
        def run(state):
            value, new_state = self._run(state)
            return f(value)._run(new_state)
        return State(run)

    def run(self, initial_state):
        return self._run(initial_state)

def get_state():
    return State(lambda s: (s, s))

def put_state(new_s):
    return State(lambda _: (None, new_s))

def modify(f):
    return State(lambda s: (None, f(s)))
```

```python
program = (
    State.unit(0)
    .bind(lambda _: modify(lambda s: s + 10))
    .bind(lambda _: modify(lambda s: s * 2))
    .bind(lambda _: get_state())
)
value, final_state = program.run(0)
print(final_state)   # 20: (0+10)*2
```

State is threaded automatically. No explicit state parameter at each step.

#### async/await as IO Monad

Python's `async`/`await` is monadic bind for the IO monad. `await expr` is
`bind(expr)`: suspend this computation, execute `expr`, and resume with its
result. The event loop is the monad's runtime.

```python
import asyncio

async def fetch(url):          return f"data from {url}"
async def parse(data):         return data.upper()
async def process_url(url):
    data   = await fetch(url)   # bind
    parsed = await parse(data)  # bind
    return parsed

asyncio.run(process_url("http://example.com"))
```

Each `await` is a bind on the IO monad. The ordering of effects (fetch before
parse) is made explicit by the bind chain. The event loop handles scheduling
without the programmer managing threads or callbacks.



### The Monad Laws

Three laws define a correct monad. They ensure bind chains behave predictably:

*Left identity:* `unit(a).bind(f) == f(a)`
Wrapping then immediately binding is the same as just calling f.

*Right identity:* `m.bind(unit) == m`
Binding with the wrap operation does nothing.

*Associativity:* `m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))`
The grouping of binds does not matter; only the order does.

These are the same guarantees composition gives for pure functions, lifted
into the effectful context.



### Under the Hood: C

C has no monads. What it has is the manual equivalent: error codes and
explicit checks at every call site.

#### The Standard C Pattern

```c
int step_one(int input, int *out);
int step_two(int input, int *out);
int step_three(int input, int *out);

int process(int input, int *result) {
    int tmp1, tmp2;
    int err;

    err = step_one(input, &tmp1);
    if (err) return err;

    err = step_two(tmp1, &tmp2);
    if (err) return err;

    err = step_three(tmp2, result);
    if (err) return err;

    return 0;
}
```

This *is* monadic composition, written by hand. The `if (err) return err`
check is the bind operation for the error monad, inlined at every step. The
pattern is correct but verbose. As the chain grows, the error-handling lines
begin to dwarf the business logic.

#### The goto cleanup Pattern

For computations that require cleanup on failure, C uses `goto`:

```c
int process_with_cleanup(int input, int *result) {
    Resource *r1 = NULL, *r2 = NULL;
    int err = 0;

    r1 = acquire_resource();
    if (!r1) { err = ERR_ACQUIRE; goto done; }

    err = use_resource(r1, input, result);
    if (err) goto done;

    r2 = acquire_second();
    if (!r2) { err = ERR_ACQUIRE2; goto done; }

    err = use_both(r1, r2, result);

done:
    if (r2) release(r2);
    if (r1) release(r1);
    return err;
}
```

`goto done` is `bind`'s short-circuit. The `done:` block is the monad's
cleanup context. This pattern appears throughout the Linux kernel and any C
code that manages multiple resources. It is idiomatic precisely because it
approximates monadic sequencing as closely as C allows.

#### The Comparison

| C (manual) | Monad (Python) |
|------------|----------------|
| `int err; err = f(); if (err) return err;` | `.bind(f)` |
| `if (!ptr) { err = ERR; goto done; }` | `.bind(check_ptr)` |
| `done: cleanup(); return err;` | error propagated by bind |
| error-handling woven into business logic | separated by bind |
| correctness enforced by discipline | correctness enforced by type |

The monad does not add power--C can express the same computations. It
adds *structure*: the effect-handling protocol is centralised in `bind` rather
than duplicated at every call site.



### Concurrency Link

Monads serialise effect flow. Each bind step happens after the previous one
completes and delivers its result. This makes effect ordering explicit in the
structure of the code, not in the timing of threads.

This is the central property of `async`/`await`: the event loop can run other
coroutines while one is suspended at `await`, but the ordering of effects
*within* a single coroutine chain is guaranteed. No locks are needed for the
ordering of effects within one bind chain, because bind is sequential by
construction.

The contrast with threads is significant: two threads interacting through
shared mutable state have an ordering that depends on the scheduler. Two
bind steps in a monadic chain have an ordering that is fixed by the program
text. One is hard to reason about; the other is determined by reading the
code.

Side effects made explicit by monads are also easier to test: you can
substitute a pure test implementation for the effect-carrying monad and verify
the logic without touching I/O, the network, or the clock.



*Next: [9. Referential Transparency](../transparency/README.md)--same input,
same output, always; and why that property enables caching, parallelism,
and equational reasoning.*
