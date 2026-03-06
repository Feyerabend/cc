# monads.py
# Functional Patterns -- 8. Monads (Effect Management)
#
# A monad extends a functor with bind (flat_map / and_then):
#   map:  f : A -> B      gives  M[A] -> M[B]
#   bind: f : A -> M[B]   gives  M[A] -> M[B]   (avoids double-wrapping)
#
# Run:  python monads.py

import asyncio



# Shared helpers

def divider(line=60):
    print("-" * line)



# 1. The map-vs-bind problem

class Maybe:
    def __init__(self, value, present):
        self._value   = value
        self._present = present

    @classmethod
    def just(cls, v): return cls(v, True)
    @classmethod
    def nothing(cls): return cls(None, False)

    def is_nothing(self): return not self._present

    def map(self, f):
        if self.is_nothing(): return Maybe.nothing()
        return Maybe.just(f(self._value))

    def bind(self, f):
        """f: A -> Maybe[B]. Apply and flatten -- no double wrapping."""
        if self.is_nothing(): return Maybe.nothing()
        return f(self._value)

    def get_or(self, default):
        return self._value if self._present else default

    def __repr__(self):
        if self.is_nothing(): return "Nothing"
        return f"Just({self._value!r})"

    def __eq__(self, other):
        if not isinstance(other, Maybe): return False
        return self._present == other._present and self._value == other._value


def safe_reciprocal(x):
    if x == 0: return Maybe.nothing()
    return Maybe.just(round(1.0 / x, 4))

print("-- 1. map vs. bind --")
print(f"  just(4).map(safe_reciprocal)  = {Maybe.just(4).map(safe_reciprocal)}")
# Just(Just(0.25)) -- doubly wrapped!  map is wrong here.
print(f"  just(4).bind(safe_reciprocal) = {Maybe.just(4).bind(safe_reciprocal)}")
# Just(0.25)       -- correctly flat.
print(f"  just(0).bind(safe_reciprocal) = {Maybe.just(0).bind(safe_reciprocal)}")
# Nothing          -- absence propagated.



# 2. Maybe monad -- chained lookups

print("\n-- 2. Maybe monad: chained lookups --")

users = {1: {'name': 'Alice', 'address_id': 10},
         2: {'name': 'Bob',   'address_id': 99}}   # 99 not in addrs
addrs = {10: {'street': 'Unter den Linden', 'zip_id': 20}}
zips  = {20: '10117'}

def find_user(uid):
    return Maybe.just(users[uid]) if uid in users else Maybe.nothing()

def find_address(user):
    aid = user['address_id']
    return Maybe.just(addrs[aid]) if aid in addrs else Maybe.nothing()

def find_zip(addr):
    zid = addr['zip_id']
    return Maybe.just(zips[zid]) if zid in zips else Maybe.nothing()

for uid in [1, 2, 99]:
    result = Maybe.just(uid).bind(find_user).bind(find_address).bind(find_zip)
    print(f"  user {uid} zip: {result.get_or('(not found)')}")



# 3. Result monad -- chained fallible operations

class Result:
    def __init__(self, value, error):
        self._value = value
        self._error = error

    @classmethod
    def ok(cls, v):  return cls(v, None)
    @classmethod
    def err(cls, e): return cls(None, e)

    def is_ok(self): return self._error is None

    def map(self, f):
        if not self.is_ok(): return self
        return Result.ok(f(self._value))

    def bind(self, f):
        if not self.is_ok(): return self
        return f(self._value)

    def get_or(self, default):
        return self._value if self.is_ok() else default

    def __repr__(self):
        if self.is_ok(): return f"Ok({self._value!r})"
        return f"Err({self._error!r})"

    def __eq__(self, other):
        if not isinstance(other, Result): return False
        return self._value == other._value and self._error == other._error


def parse_int(s):
    try:    return Result.ok(int(s))
    except: return Result.err(f"not an integer: {s!r}")

def check_positive(n):
    return Result.ok(n) if n > 0 else Result.err(f"{n} is not positive")

def check_small(n):
    return Result.ok(n) if n <= 100 else Result.err(f"{n} exceeds limit 100")

def process(s):
    return (Result.ok(s)
            .bind(parse_int)
            .bind(check_positive)
            .bind(check_small))

print("\n-- 3. Result monad: validation pipeline --")
for s in ["42", "-5", "999", "??"]:
    print(f"  process({s!r:6}) = {process(s)}")



# 4. The C-style equivalent (manual monad)

print("\n-- 4. C-style equivalent (manual error checking) --")

def process_imperative(s):
    # Step 1: parse
    try:    n = int(s)
    except: return None, f"not an integer: {s!r}"
    # Step 2: check positive
    if n <= 0: return None, f"{n} is not positive"
    # Step 3: check small
    if n > 100: return None, f"{n} exceeds limit 100"
    return n, None

for s in ["42", "-5", "999", "??"]:
    val, err = process_imperative(s)
    if err:  print(f"  process({s!r:6}) -> error: {err}")
    else:    print(f"  process({s!r:6}) -> value: {val}")

print("  (Same logic; error-handling woven into business logic)")



# 5. Monadic laws

print("\n-- 5. Monad laws (Result) --")

f = lambda x: Result.ok(x * 2)    if x > 0 else Result.err("non-positive")
g = lambda x: Result.ok(x + 1)    if x < 100 else Result.err("too large")

for val in [5, -1, 60]:
    r = Result.ok(val)

    # Left identity: unit(a).bind(f) == f(a)
    li = Result.ok(val).bind(f) == f(val)

    # Right identity: m.bind(unit) == m
    ri = r.bind(Result.ok) == r

    # Associativity: m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
    lhs = r.bind(f).bind(g)
    rhs = r.bind(lambda x: f(x).bind(g))
    assoc = lhs == rhs

    print(f"  val={val:3}  left_id={li}  right_id={ri}  assoc={assoc}")



# 6. State monad -- threading state without explicit parameters

print("\n-- 6. State monad --")

class State:
    """Wraps: state -> (value, new_state)"""
    def __init__(self, run_fn):
        self._run = run_fn

    @classmethod
    def unit(cls, value):
        return cls(lambda s: (value, s))

    def bind(self, f):
        def run(state):
            value, new_state = self._run(state)
            return f(value)._run(new_state)
        return State(run)

    def run(self, initial):
        return self._run(initial)

def get():
    """Read the current state as the value."""
    return State(lambda s: (s, s))

def put(new_state):
    """Replace the state; value is None."""
    return State(lambda _: (None, new_state))

def modify(f):
    """Apply f to the current state."""
    return State(lambda s: (None, f(s)))

# A computation that logs steps by accumulating into a list-state
def log(msg):
    return State(lambda s: (None, s + [msg]))

program = (
    State.unit(0)
    .bind(lambda _: log("start"))
    .bind(lambda _: modify(lambda s: s))   # no-op on list state -- see below
)

# Simpler example: numeric state
counter_prog = (
    State.unit(0)
    .bind(lambda _: put(10))
    .bind(lambda _: modify(lambda s: s + 5))
    .bind(lambda _: modify(lambda s: s * 2))
    .bind(lambda _: get())
)
value, final = counter_prog.run(0)
print(f"  put(10), +5, *2 -> value={value}, state={final}")   # (30, 30)

# State as a counter with history
def increment_and_log():
    return (get()
            .bind(lambda n: put(n + 1)
            .bind(lambda _: get())))

steps = (
    State.unit(None)
    .bind(lambda _: put(0))
    .bind(lambda _: increment_and_log())
    .bind(lambda _: increment_and_log())
    .bind(lambda _: increment_and_log())
    .bind(lambda _: get())
)
val, state = steps.run(0)
print(f"  three increments -> state={state}")   # 3



# 7. Writer monad -- accumulating a log alongside a value

print("\n-- 7. Writer monad (logging) --")

class Writer:
    """Pairs a value with an accumulated log (list of strings)."""
    def __init__(self, value, log):
        self.value = value
        self.log   = log

    @classmethod
    def unit(cls, value):
        return cls(value, [])

    def bind(self, f):
        result = f(self.value)
        return Writer(result.value, self.log + result.log)

    def tell(self, msg):
        return Writer(self.value, self.log + [msg])

    def __repr__(self):
        return f"Writer(value={self.value!r}, log={self.log})"


def logged_double(x):
    return Writer(x * 2, [f"doubled {x} -> {x*2}"])

def logged_increment(x):
    return Writer(x + 1, [f"incremented {x} -> {x+1}"])

def logged_negate(x):
    return Writer(-x, [f"negated {x} -> {-x}"])

result = (Writer.unit(5)
          .bind(logged_double)
          .bind(logged_increment)
          .bind(logged_negate))

print(f"  value: {result.value}")
print("  log:")
for entry in result.log:
    print(f"    {entry}")



# 8. async/await as IO monad

print("\n-- 8. async/await as IO monad --")

async def fetch(url):
    # Simulate I/O
    return f"<html from {url}>"

async def extract_title(html):
    return html.replace("<html from ", "Page at ").replace(">", "")

async def upper(s):
    return s.upper()

async def pipeline(url):
    # Each await is a monadic bind on the IO monad.
    # Ordering is guaranteed by the bind chain, not by thread scheduling.
    html  = await fetch(url)
    title = await extract_title(html)
    upper_title = await upper(title)
    return upper_title

result = asyncio.run(pipeline("example.com"))
print(f"  pipeline result: {result}")
print("  (each await = bind; effect ordering explicit in program text)")
