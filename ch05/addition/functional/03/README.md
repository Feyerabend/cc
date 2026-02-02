
## Algebraic Data Types & Type Classes

This module extends the functional core with advanced type system
features from languages like Haskell, Scala, and ML.

1. *Algebraic Data Types (ADTs)* - Sum types with pattern matching
2. *Type Classes* - Functor, Applicative, Monad, Foldable, etc.
3. *Immutable List* - Full type class implementation
4. *Monoids* - Sum, Product, All, Any, First, Last
5. *Do Notation* - Haskell-style monadic composition
6. *Lenses* - Functional references for nested updates



### Algebraic Data Types (Sum Types) (+)

ADTs let you define types that can be one of several variants.
Think of them as type-safe enums "on steroids."

#### Basic Example - Shapes

```python
from functional_types import adt
from dataclasses import dataclass

@adt('Shape')
@dataclass(frozen=True)
class Circle:
    radius: float

@adt('Shape')
@dataclass(frozen=True)
class Rectangle:
    width: float
    height: float

# Create instances
circle = Circle(5.0)
rect = Rectangle(10.0, 20.0)

# Pattern match
def area(shape):
    return shape.match(
        Circle=lambda radius: 3.14159 * radius * 2,
        Rectangle=lambda width, height: width * height,
    )

area(circle)  # 78.54
area(rect)    # 200.0
```

#### Expression Trees

```python
@adt('Expr')
@dataclass(frozen=True)
class Lit:
    value: int

@adt('Expr')
@dataclass(frozen=True)
class Add:
    left: 'Expr'
    right: 'Expr'

@adt('Expr')
@dataclass(frozen=True)
class Mul:
    left: 'Expr'
    right: 'Expr'

# Build: (2 + 3) * 4
expr = Mul(Add(Lit(2), Lit(3)), Lit(4))

# Evaluate
def eval_expr(e):
    return e.match(
        Lit=lambda value: value,
        Add=lambda left, right: eval_expr(left) + eval_expr(right),
        Mul=lambda left, right: eval_expr(left) * eval_expr(right),
    )

eval_expr(expr)  # 20
```

#### Custom Option Type

```python
@adt('Option')
@dataclass(frozen=True)
class Nope:
    pass

@adt('Option')
@dataclass(frozen=True)
class Yep:
    value: any

def safe_divide(a, b):
    if b == 0:
        return Nope()
    return Yep(a / b)

result = safe_divide(10, 2).match(
    Nope=lambda: "Error!",
    Yep=lambda value: f"Result: {value}"
)
```



### Type Classes

Type classes define interfaces that types can implement.
They're like protocols/interfaces but more powerful.

#### Functor

Types that can be mapped over.

```python
from functional_types import List

# List is a Functor
numbers = List.of(1, 2, 3)
doubled = numbers.fmap(lambda x: x * 2)
# List([2, 4, 6])

# Maybe is also a Functor
from functional_core import Some
value = Some(5).map(lambda x: x * 2)
# Some(10)
```

*Laws:*
1. Identity: `fmap(id, x) == x`
2. Composition: `fmap(f ∘ g, x) == fmap(f, fmap(g, x))`

#### Applicative

Functors that can apply functions in a context.

```python
# Lift a value
single = List.pure(42)  # List([42])

# Apply functions to values
values = List.of(1, 2, 3)
functions = List.of(lambda x: x * 2, lambda x: x + 10)

result = values.ap(functions)
# List([2, 4, 6, 11, 12, 13])
```

*Laws:*
1. Identity: `pure(id) <*> v == v`
2. Composition: `pure(∘) <*> u <*> v <*> w == u <*> (v <*> w)`
3. Homomorphism: `pure(f) <*> pure(x) == pure(f(x))`

#### Monad

Applicatives that support bind (flatMap).

```python
# List monad
numbers = List.of(1, 2, 3)

# Each number generates a list, then flatten
result = numbers.bind(lambda x: List.of(x, x * 10))
# List([1, 10, 2, 20, 3, 30])

# Cartesian product
letters = List.of('a', 'b')
nums = List.of(1, 2)

pairs = letters.bind(lambda letter:
    nums.fmap(lambda num: (letter, num))
)
# List([('a', 1), ('a', 2), ('b', 1), ('b', 2)])
```

*Laws:*
1. Left identity: `pure(a).bind(f) == f(a)`
2. Right identity: `m.bind(pure) == m`
3. Associativity: `m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))`

#### Foldable

Types that can be folded (reduced).

```python
numbers = List.of(1, 2, 3, 4, 5)

# Fold left (sum)
total = numbers.foldl(lambda acc, x: acc + x, 0)
# 15

# Fold right
result = numbers.foldr(lambda x, acc: [x] + acc, [])
# [1, 2, 3, 4, 5]

# Product
product = numbers.foldl(lambda acc, x: acc * x, 1)
# 120
```



### Monoids

A monoid is a type with an associative binary operation and an identity element.

#### Sum Monoid (Addition)

```python
from functional_types import Sum, mconcat

values = [Sum(1), Sum(2), Sum(3), Sum(4)]
total = mconcat(values)
# Sum(value=10)

# Identity
Sum(5).append(Sum.empty())  # Sum(5)
```

#### Product Monoid (Multiplication)

```python
from functional_types import Product

values = [Product(2), Product(3), Product(4)]
total = mconcat(values)
# Product(value=24)
```

#### All Monoid (AND)

```python
from functional_types import All

conditions = [All(True), All(True), All(False)]
result = mconcat(conditions)
# All(value=False)
```

#### Any Monoid (OR)

```python
from functional_types import Any

flags = [Any(False), Any(False), Any(True)]
result = mconcat(flags)
# Any(value=True)
```

#### First Monoid

Keeps the first `Some` value.

```python
from functional_types import First
from functional_core import Some, nothing

values = [First(nothing()), First(Some(10)), First(Some(20))]
result = mconcat(values)
# First(value=Some(10))
```

#### Last Monoid

Keeps the last `Some` value.

```python
from functional_types import Last

values = [Last(Some(10)), Last(nothing()), Last(Some(20))]
result = mconcat(values)
# Last(value=Some(20))
```

#### List Monoid (Concatenation)

```python
list1 = List.of(1, 2, 3)
list2 = List.of(4, 5, 6)

combined = list1.append(list2)
# List([1, 2, 3, 4, 5, 6])

# Identity
list1.append(List.empty())  # List([1, 2, 3])
```



### Immutable List

A fully-featured immutable list with all type class implementations.

#### Creating Lists

```python
from functional_types import List

# From items
nums = List.of(1, 2, 3, 4, 5)

# Empty
empty = List.empty()

# Check
nums.is_empty()  # False
```

#### List Operations

```python
# Head (first element)
nums.head()  # Some(1)

# Tail (all but first)
nums.tail()  # List([2, 3, 4, 5])

# Cons (prepend)
nums.cons(0)  # List([0, 1, 2, 3, 4, 5])

# Map
nums.fmap(lambda x: x * 2)  # List([2, 4, 6, 8, 10])

# FlatMap
nums.bind(lambda x: List.of(x, -x))
# List([1, -1, 2, -2, 3, -3, 4, -4, 5, -5])

# Fold
nums.foldl(lambda acc, x: acc + x, 0)  # 15

# Append
List.of(1, 2).append(List.of(3, 4))  # List([1, 2, 3, 4])
```



### Do Notation

Simulates Haskell's do-notation for cleaner monadic composition.

#### With Maybe

```python
from functional_types import Do
from functional_core import Some

result = (
    Do(Some(5))
    .bind(lambda x: Some(x * 2))
    .bind(lambda x: Some(x + 3))
    .bind(lambda x: Some(x * 2))
    .result()
)
# Some(169)
```

#### With List

```python
result = (
    Do(List.of(1, 2))
    .bind(lambda x: List.of(x, x * 10))
    .bind(lambda x: List.of(x, x + 100))
    .result()
)
# List([1, 101, 10, 110, 2, 102, 20, 120])
```



### Lenses

Functional references for getting and setting values in nested immutable structures.

#### Basic Lens

```python
from functional_types import lens
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class Person:
    name: str
    age: int

# Create lens
age_lens = lens(
    getter=lambda p: p.age,
    setter=lambda p, a: replace(p, age=a)
)

alice = Person("Alice", 30)

# Get
age_lens.get(alice)  # 30

# Set
older = age_lens.set(alice, 31)
# Person(name='Alice', age=31)

# Modify
birthday = age_lens.modify(alice, lambda age: age + 1)
# Person(name='Alice', age=31)
```

#### Composing Lenses

```python
@dataclass(frozen=True)
class Address:
    city: str
    zip: str

@dataclass(frozen=True)
class Person:
    name: str
    address: Address

# Individual lenses
address_lens = lens(
    lambda p: p.address,
    lambda p, a: replace(p, address=a)
)

city_lens = lens(
    lambda a: a.city,
    lambda a, c: replace(a, city=c)
)

# Compose to focus deep
person_city = address_lens.compose(city_lens)

alice = Person("Alice", Address("NYC", "10001"))

# Get nested value
person_city.get(alice)  # "NYC"

# Set nested value
moved = person_city.set(alice, "LA")
# Person with address.city = "LA"
```



### Real-World Example: Validation

Accumulate validation errors using monoids.

```python
@dataclass(frozen=True)
class Validation:
    errors: List[str]
    value: Maybe[any]
    
    def is_valid(self):
        return self.errors.is_empty()
    
    @classmethod
    def success(cls, value):
        return cls(List.empty(), Some(value))
    
    @classmethod
    def failure(cls, error):
        return cls(List.of(error), nothing())

def validate_age(age):
    if age < 0:
        return Validation.failure("Age cannot be negative")
    if age > 150:
        return Validation.failure("Age too high")
    return Validation.success(age)

def validate_name(name):
    if not name:
        return Validation.failure("Name cannot be empty")
    if len(name) < 2:
        return Validation.failure("Name too short")
    return Validation.success(name)

# Validate and accumulate errors
age_val = validate_age(-5)
name_val = validate_name("")

# Combine errors
all_errors = age_val.errors.append(name_val.errors)
# List(['Age cannot be negative', 'Name cannot be empty'])
```



### Type Class Polymorphism

Write functions that work with ANY type implementing a type class.

```python
# Works with any Functor
def double_all(functor):
    return functor.fmap(lambda x: x * 2)

# Works with List
double_all(List.of(1, 2, 3))
# List([2, 4, 6])

# Works with Maybe (using map)
Some(5).map(lambda x: x * 2)
# Some(10)
```



### Summary of Type Classes

| Type Class | What It Does | Key Method |
|------------|--------------|------------|
| Functor | Map over structure | `fmap` |
| Applicative | Apply functions in context | `pure`, `ap` |
| Monad | Sequential composition | `bind` |
| Foldable | Reduce structure | `foldr`, `foldl` |
| Semigroup | Combine values | `append` |
| Monoid | Semigroup + identity | `empty`, `append` |



### Benefits

1. *Type Safety* - Pattern matching ensures all cases handled
2. *Composition* - Type classes enable powerful abstraction
3. *Immutability* - All structures are immutable by default
4. *Reusability* - Polymorphic functions work across types
5. *Mathematical Properties* - Type class laws guarantee behavior



### Next Level Extensions

Want to go even further?
- *Free Monads* - Build interpreters and DSLs
- *Monad Transformers* - Stack monads (ReaderT, StateT)
- *Arrows* - Generalize functions
- *Comonads* - Dual of monads
- *Profunctors* - Abstract over input/output
- *Recursion Schemes* - Catamorphisms, anamorphisms

