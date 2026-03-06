# functors.py
# Functional Patterns -- 7. Functors (Mapped Contexts)
#
# A functor is any container that supports a map() operation:
# apply a function to the value inside without changing the container shape.
#
# Run:  python functors.py



# 1. Box -- the simplest possible functor

class Box:
    """A single-value container that supports map."""

    def __init__(self, value):
        self._value = value

    def map(self, f):
        return Box(f(self._value))

    def get(self):
        return self._value

    def __repr__(self):
        return f"Box({self._value!r})"

    def __eq__(self, other):
        return isinstance(other, Box) and self._value == other._value


print("-- 1. Box functor --")
b = Box(5)
print(f"  Box(5).map(square)   = {b.map(lambda x: x * x)}") # Box(25)
print(f"  Box(5).map(str)      = {b.map(str)}") # Box('5')
print(f"  chained maps:        {b.map(lambda x: x+1).map(lambda x: x*2)}") # Box(12)



# 2. Maybe -- a value that might be absent

class Maybe:
    """
    Represents a value that may or may not be present.
    Just(v) -- a present value.
    Nothing -- absence.
    map() propagates Nothing silently; no if-checks needed in the caller.
    """

    def __init__(self, value, _present):
        self._value   = value
        self._present = _present

    @classmethod
    def just(cls, value):
        return cls(value, True)

    @classmethod
    def nothing(cls):
        return cls(None, False)

    def is_nothing(self):
        return not self._present

    def map(self, f):
        if self.is_nothing():
            return Maybe.nothing()
        return Maybe.just(f(self._value))

    def get_or(self, default):
        return self._value if self._present else default

    def __repr__(self):
        if self.is_nothing(): return "Nothing"
        return f"Just({self._value!r})"

    def __eq__(self, other):
        if not isinstance(other, Maybe): return False
        if self._present != other._present: return False
        return self._value == other._value


print("\n-- 2. Maybe functor --")

j = Maybe.just(10)
n = Maybe.nothing()

print(f"  Just(10).map(*2)         = {j.map(lambda x: x * 2)}") # Just(20)
print(f"  Nothing.map(*2)          = {n.map(lambda x: x * 2)}") # Nothing

# Chained: Nothing short-circuits all subsequent maps
print(f"  Just(5).map(-3).map(*10) = {j.map(lambda x:x-3).map(lambda x:x*10)}") # Just(70)
print(f"  Nothing chain            = {n.map(lambda x:x-3).map(lambda x:x*10)}") # Nothing

# Safe division: return Nothing for division by zero
def safe_div(a, b):
    return Maybe.nothing() if b == 0 else Maybe.just(a // b)

print(f"  safe_div(10,2).map(+1)   = {safe_div(10,2).map(lambda x:x+1)}") # Just(6)
print(f"  safe_div(10,0).map(+1)   = {safe_div(10,0).map(lambda x:x+1)}") # Nothing

# Safe dict lookup
def safe_get(d, key):
    return Maybe.just(d[key]) if key in d else Maybe.nothing()

config = {'host': 'localhost', 'port': '8080'}
print(f"  safe_get port, map int   = {safe_get(config,'port').map(int)}") # Just(8080)
print(f"  safe_get missing         = {safe_get(config,'timeout').map(int)}") # Nothing



# 3. Result -- success or error


class Result:
    """
    Represents a computation that either succeeded (Ok) or failed (Err).
    map() transforms Ok values; Err values pass through untouched.
    """

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
            return Result.err(self._error)
        return Result.ok(f(self._value))

    def get_or(self, default):
        return self._value if self.is_ok() else default

    def __repr__(self):
        if self.is_ok(): return f"Ok({self._value!r})"
        return f"Err({self._error!r})"

    def __eq__(self, other):
        if not isinstance(other, Result): return False
        return self._value == other._value and self._error == other._error


print("\n-- 3. Result functor --")

ok   = Result.ok(10)
fail = Result.err("network timeout")

print(f"  Ok(10).map(*3)    = {ok.map(lambda x: x * 3)}")     # Ok(30)
print(f"  Err(...).map(*3)  = {fail.map(lambda x: x * 3)}")   # Err(...)

def parse_int(s):
    try:    return Result.ok(int(s))
    except: return Result.err(f"cannot parse {s!r} as int")

def check_positive(n):
    if n <= 0: return Result.err(f"{n} is not positive")
    return Result.ok(n)

# Happy path
r = parse_int("42").map(lambda x: x * 2)
print(f"  parse('42')*2     = {r}")   # Ok(84)

# Error path -- all maps after the error are no-ops
r = parse_int("??").map(lambda x: x * 2).map(str)
print(f"  parse('??')*2     = {r}")   # Err(...)



# 4. FList -- list as an explicit functor

class FList(list):
    """List subclass with an explicit .map() method."""

    def map(self, f):
        return FList(f(x) for x in self)

    def __repr__(self):
        return f"FList({list.__repr__(self)})"


print("\n-- 4. FList functor --")
fl = FList([1, 2, 3, 4, 5])
print(f"  FList squares:  {fl.map(lambda x: x*x)}")
print(f"  FList as str:   {fl.map(str)}")
print(f"  chained:        {fl.map(lambda x:x+10).map(lambda x:x*2)}")



# 5. Tree functor -- map applies to all leaf values

class Tree:
    """
    Binary tree where map() transforms every leaf value.
    Internal nodes (branches) hold no value; only leaves do.
    """

    def __init__(self, value=None, left=None, right=None):
        self.value = value
        self.left  = left
        self.right = right

    @property
    def is_leaf(self):
        return self.left is None and self.right is None

    def map(self, f):
        if self.is_leaf:
            return Tree(value=f(self.value))
        return Tree(
            left  = self.left.map(f)  if self.left  else None,
            right = self.right.map(f) if self.right else None,
        )

    def leaves(self):
        if self.is_leaf:
            return [self.value]
        result = []
        if self.left:  result += self.left.leaves()
        if self.right: result += self.right.leaves()
        return result

    def __repr__(self):
        if self.is_leaf: return f"Leaf({self.value})"
        return f"Branch({self.left}, {self.right})"


print("\n-- 5. Tree functor --")
#        branch
#       /      \
#   branch      5
#   /    \
#  2      3
tree = Tree(
    left  = Tree(left=Tree(value=2), right=Tree(value=3)),
    right = Tree(value=5)
)

print(f"  leaves:         {tree.leaves()}")                     # [2, 3, 5]
print(f"  map(*2) leaves: {tree.map(lambda x: x*2).leaves()}")  # [4, 6, 10]
print(f"  map(str) leaves:{tree.map(str).leaves()}")            # ['2','3','5']
print("  original unchanged:", tree.leaves())                   # [2, 3, 5]



# 6. Functor laws

print("\n-- 6. Functor laws --")

f = lambda x: x * 2
g = lambda x: x + 1
identity = lambda x: x

# Identity law: map(id) == id
for functor in [Box(42), Maybe.just(7), Result.ok(3)]:
    mapped = functor.map(identity)
    assert mapped == functor, f"identity law failed for {functor}"
print("  identity law holds for Box, Maybe, Result")

# Composition law: map(f).map(g) == map(g∘f)
for val in [Box(5), Maybe.just(5), Result.ok(5)]:
    left  = val.map(f).map(g)
    right = val.map(lambda x: g(f(x)))
    assert left == right, f"composition law failed for {val}"
print("  composition law holds for Box, Maybe, Result")

# Show the tree law holds too
t   = Tree(left=Tree(value=4), right=Tree(value=8))
lhs = t.map(f).map(g).leaves()
rhs = t.map(lambda x: g(f(x))).leaves()
assert lhs == rhs
print(f"  composition law holds for Tree: {lhs} == {rhs}")



# 7. Uniform interface: the same f works across different functors

print("\n-- 7. Same function, different contexts --")

def apply_to_functor(functor, f):
    return functor.map(f)

double = lambda x: x * 2

contexts = [
    Box(21),
    Maybe.just(21),
    Maybe.nothing(),
    Result.ok(21),
    Result.err("oops"),
]

for ctx in contexts:
    print(f"  {str(ctx):<20} -> {apply_to_functor(ctx, double)}")
