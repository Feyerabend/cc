# immutability.py
# Functional Patterns -- 3. Immutability
#
# Demonstrates the contrast between mutable and immutable styles,
# shallow vs. deep immutability, and frozen dataclasses.
#
# Run:  python immutability.py

from dataclasses import dataclass



# 1. Built-in immutable types

print("-- 1. Built-in immutable types --")

t = (1, 2, 3)
s = "hello"

try:
    t[0] = 9
except TypeError as e:
    print(f"  tuple assignment blocked: {e}")

try:
    s[0] = "H"
except TypeError as e:
    print(f"  str assignment blocked:   {e}")

# int "mutation" always produces a new object
a = 42
b = a
a += 1
print(f"  a={a}, b={b}  -- integers are immutable, a+=1 rebinds a")



# 2. The mutable shared list problem

print("\n-- 2. Mutable shared list --")

def add_item_mutating(collection, item):
    """Mutates the caller's list -- a side effect."""
    collection.append(item)
    return collection

original = [1, 2, 3]
result   = add_item_mutating(original, 4)

print(f"  original after call: {original}")       # [1, 2, 3, 4] -- changed!
print(f"  result is original:  {result is original}")  # True



# 3. Immutable style: return a new value

print("\n-- 3. Immutable style (new list) --")

def add_item(collection, item):
    """Returns a new list; the original is untouched."""
    return collection + [item]

original = [1, 2, 3]
result   = add_item(original, 4)

print(f"  original after call: {original}")       # [1, 2, 3]
print(f"  result:              {result}")          # [1, 2, 3, 4]
print(f"  result is original:  {result is original}")  # False



# 4. Tuple as immutable record

print("\n-- 4. Tuple as immutable record --")

def translate_tuple(point, dx, dy):
    return (point[0] + dx, point[1] + dy)

origin = (0, 0)
moved  = translate_tuple(origin, 3, 4)

print(f"  origin: {origin}")   # (0, 0)
print(f"  moved:  {moved}")    # (3, 4)



# 5. Frozen dataclass -- enforced immutability

print("\n-- 5. Frozen dataclass --")

@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def translate(self, dx, dy):
        return Point(self.x + dx, self.y + dy)

    def scale(self, factor):
        return Point(self.x * factor, self.y * factor)

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

p = Point(0.0, 0.0)
q = p.translate(3.0, 4.0)
r = q.scale(2.0)

print(f"  p: {p}")   # Point(0.0, 0.0)
print(f"  q: {q}")   # Point(3.0, 4.0)
print(f"  r: {r}")   # Point(6.0, 8.0)

try:
    p.x = 99.0
except Exception as e:
    print(f"  assignment to frozen field blocked: {e}")



# 6. Shallow vs. deep immutability

print("\n-- 6. Shallow immutability (tuple holding a list) --")

t = ([1, 2], [3, 4])
print(f"  before: {t}")
t[0].append(99)            # the list inside the tuple is still mutable
print(f"  after t[0].append(99): {t}")

# True deep immutability: use nested tuples
deep = ((1, 2), (3, 4))
try:
    deep[0] += (99,)       # rebinds deep[0] -- but deep itself is immutable
except TypeError as e:
    print(f"  nested tuple protected: {e}")



# 7. Immutability in practice: updating nested structures

print("\n-- 7. Updating nested immutable structures --")

# Functional update: produce a new dict with one field changed.
# (dict itself is mutable, but this pattern treats it as immutable.)
def update_field(record, key, value):
    """Return a new dict with key set to value; original untouched."""
    return {**record, key: value}

person = {'name': 'Alice', 'age': 30, 'city': 'Berlin'}
older  = update_field(person, 'age', 31)

print(f"  original: {person}")
print(f"  updated:  {older}")
print(f"  same object: {person is older}")  # False



# 8. Safe sharing across "threads" (simulated)

print("\n-- 8. Safe sharing (immutable config) --")

import threading

# A frozen config object can be read by many threads without a lock.
@dataclass(frozen=True)
class Config:
    host: str
    port: int
    max_connections: int

config = Config(host="localhost", port=8080, max_connections=100)
results = []

def worker(cfg, worker_id):
    # Reading immutable fields -- no lock needed
    results.append(f"worker {worker_id} connecting to {cfg.host}:{cfg.port}")

threads = [threading.Thread(target=worker, args=(config, i)) for i in range(4)]
for th in threads: th.start()
for th in threads: th.join()

for line in sorted(results):
    print(f"  {line}")
