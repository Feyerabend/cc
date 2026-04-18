
## Project: From Abstraction, Interface, and Complexity to Modularity

You already understand three systemic forces:
- *Abstraction*: hiding implementation details behind a simpler representation.
- *Interface*: the defined boundary through which components interact.
- *Complexity*: the degree to which a system's behaviour is difficult to predict, understand, or manage.

In this project, you will discover that as complexity grows, abstraction and
interface stop being conveniences and become necessities--and their combination
forces a specific structural response:
- *Modularity*.

The equation you will derive is:
```
Abstraction + Interface + Complexity  ->  Modularity
```
Your task is not to start from "modularity" as a given solution, but to
*reconstruct why partitioning a system into independent units becomes
inevitable* as complexity crosses a threshold.

This is a design discovery exercise, not a memorisation one.


### Part 1 - A Thought Experiment: Small System, No Problem

Imagine you are writing a program with 50 lines of code.
Every function can see every other function.
Every variable is accessible everywhere.
You hold the entire system in your head.

When something breaks, you find it immediately.
When you want to add a feature, you see exactly where it belongs.
There is no need for structure. Structure would only add overhead.

Now imagine the program grows to 50,000 lines.
Then 500,000. Written by a team of twenty people over three years.

At what point does "everyone can touch everything" become a catastrophe?


### Part 2 - Discovering Complexity as a Force

Complexity in a system is not just size. It is the number of *dependencies*--
the ways in which one part of the system depends on, and can be broken by,
changes to another part.

Model it:

```python
def dependency_count(n_components, coupling):
    return n_components * (n_components - 1) * coupling / 2

print("Dependencies by system size (high coupling):")
for n in [5, 10, 20, 50, 100]:
    d = dependency_count(n, coupling=0.8)
    print(f"  {n:>4} components: ~{d:.0f} dependencies")
```

Observe: dependencies grow roughly as n^2. A system of 100 tightly coupled
components has roughly 4,000 potential dependency paths. No single person
can track them all.

This is the complexity trap: as systems grow, coupling creates a web of
dependencies that makes the system *unknowable* to any individual.


### Part 3 - Why Abstraction Alone Is Not Enough

Abstraction helps. If you hide the internals of a component, callers
do not need to understand them.

But abstraction without discipline leaks. Implementors add "just one"
extra parameter. Callers reach past the abstraction into internals
because it is convenient. Over time, the abstraction becomes nominal--
everyone knows it exists but nobody respects it.

```python
class LeakyAbstraction:
    def __init__(self):
        self._internal_buffer = []   # meant to be private
        self.public_value     = 0

    def process(self, x):
        self._internal_buffer.append(x)
        self.public_value = sum(self._internal_buffer)

obj = LeakyAbstraction()
obj.process(5)

obj._internal_buffer.append(999)   # bypass the abstraction entirely
print(obj.public_value)            # stale; internal state corrupted

obj.process(1)
print(obj.public_value)            # includes the injected value
```

Without an enforced boundary, abstraction is just a convention.
Conventions erode under deadline pressure. You need something stronger.


### Part 4 - Why Interface Becomes the Enforcer

An interface is not just documentation. It is a *contract*:
"You may only interact with me through these operations, with these types,
producing these results. Everything else is hidden and may change."

When an interface is enforced--by a language, a compiler, an API boundary,
or a process boundary--the abstraction becomes real.

```python
from abc import ABC, abstractmethod

class DataStore(ABC):
    @abstractmethod
    def read(self, key: str) -> str: ...

    @abstractmethod
    def write(self, key: str, value: str) -> None: ...

class InMemoryStore(DataStore):
    def __init__(self):
        self._data = {}

    def read(self, key):
        return self._data.get(key, "")

    def write(self, key, value):
        self._data[key] = value

store = InMemoryStore()
store.write("x", "hello")
print(store.read("x"))
```

Now the caller cannot access `_data`. The boundary is enforced.
But this is one component. The question is: how do you apply this
at the scale of an entire system?


### Part 5 - Your Task: Measure the Benefit of Boundaries

Before building a modular system, measure what boundaries cost and what they buy.

Write two versions of the same small system--one with free-form coupling,
one with enforced interfaces--and count:
- How many places must change when an internal detail changes?
- How many files must you read to understand one component?

```python
class TightlyCoupled:
    def __init__(self):
        self.raw_data    = []
        self.total       = 0
        self.item_count  = 0

    def add(self, x):
        self.raw_data.append(x)
        self.total      += x
        self.item_count += 1

class LooselyCoupleda:
    def __init__(self, store):
        self._store = store

    def add(self, x):
        prev = self._store.read("total") or 0
        n    = self._store.read("count") or 0
        self._store.write("total", prev + x)
        self._store.write("count", n + 1)

    def average(self):
        total = self._store.read("total") or 0
        count = self._store.read("count") or 1
        return total / count
```

Now ask: if you need to switch from in-memory to file-backed storage,
how many changes does each version require?

In the tightly coupled version: the whole class must change.
In the loosely coupled version: swap the `store` argument. Nothing else changes.


### Part 6 - Introduce Partitioning Without Naming It

Now apply this across a full system.
Divide the system into *pieces*, each with:
- A clear responsibility (one thing it does).
- A defined interface (the only way to reach it).
- Hidden internals (not accessible from outside).

You still do not call this "modularity". You call it *putting walls between things*.

```python
class AuthService:
    def __init__(self):
        self._tokens = {}

    def login(self, user, password) -> str:
        token = f"tok-{user}-{hash(password)}"
        self._tokens[token] = user
        return token

    def verify(self, token) -> str | None:
        return self._tokens.get(token)

class DataService:
    def __init__(self):
        self._store = {}

    def get(self, key) -> str | None:
        return self._store.get(key)

    def put(self, key, value) -> None:
        self._store[key] = value

class App:
    def __init__(self):
        self._auth = AuthService()
        self._data = DataService()

    def handle_request(self, user, password, key, value=None):
        token = self._auth.login(user, password)
        if not self._auth.verify(token):
            return "Unauthorised"
        if value is not None:
            self._data.put(key, value)
            return "Stored"
        return self._data.get(key)

app = App()
print(app.handle_request("alice", "secret", "greeting", "hello"))
print(app.handle_request("alice", "secret", "greeting"))
```

Now ask: can you replace `AuthService` without touching `DataService`?
Can you test `DataService` without running `AuthService`?

The answer is yes. The walls make that possible.


### Part 7 - Observe the Emergence

Now measure complexity in both systems:

| Property            | No boundaries               | With walls                                 |
|---------------------|-----------------------------|--------------------------------------------|
| Dependencies        | n^2                         | n (each piece touches only its neighbours) |
| Change blast radius | Entire system               | One piece                                  |
| Testability         | Requires full system        | Each piece in isolation                    |
| Understandability   | Must know everything        | Must know one piece at a time              |
| Replaceability      | Impossible without rewrites | Swap one piece behind its interface        |

This is the moment the equation becomes real:
```
Abstraction + Interface + Complexity  ->  Modularity
```

Not as a style preference. As an *inevitability*.

When complexity makes a system unknowable, and abstraction alone leaks,
and interfaces alone are local--the only structural response is to divide
the system into pieces with enforced boundaries and hidden internals.
That structure is modularity.


### Part 8 - The Costs of Modularity

Modularity is not free. Observe what you give up:

- *Indirection*: every call now crosses a boundary. Finding where something
  actually happens requires tracing through interfaces, not reading straight
  through code.

- *Premature partitioning*: if you modularise before you understand the
  problem, you draw the walls in the wrong places. Moving walls later is
  expensive. Wrong modularity is worse than no modularity.

- *Interface rigidity*: once an interface is published and others depend on it,
  changing it breaks all callers. Good interfaces are hard to design in advance.

- *Overhead*: crossing a process or network boundary (as in microservices)
  adds latency and failure modes that a single-process system does not have.

The right level of modularity depends on the size and volatility of the system.
A 200-line script does not need modules. A 200,000-line system cannot survive without them.


### Part 9 - Reflection Questions

Answer in writing:

1. Why does dependency count grow faster than component count in a tightly coupled system?
2. Why is abstraction without an enforced interface insufficient?
3. What is the relationship between interface and testability?
4. Why can premature modularisation be worse than no modularisation?
5. How do you decide where to draw the boundary between two modules?
6. What is the difference between modularity at the function level, the class level,
   the library level, and the service level?

If you can answer these, you understand modularity at a systemic level.
Not as a coding style. As a necessity created by deeper forces.

Now. Rename your "walls between things" to *modules*--or *packages*,
or *services*, or *components*, depending on the scale.
At that point, you are not learning what modularity is.
You are recognising what you already built.
