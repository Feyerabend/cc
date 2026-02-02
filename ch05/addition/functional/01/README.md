
## Functional Programming Core

A clean implementation of core functional programming primitives that form
the substrate of modern functional languages. This library brings *Maybe/Option types*,
*Result/Either types*, *function composition*, and other FP fundamentals to Python.

This library provides:
- *Maybe/Option types* (`Some`, `Nothing`) - for handling optional values without null checks
- *Result/Either types* (`Ok`, `Err`) - for error handling without exceptions
- *Function composition* - compose, pipe, curry
- *Safe operations* - division, parsing, dictionary access that return Maybe/Result
- *List operations* - fold, traverse, sequence
- *Immutability* - all types are frozen dataclasses

Functional programming provides:
1. *Explicit error handling* - no silent nulls or hidden exceptions
2. *Composability* - small functions that chain together elegantly
3. *Type safety* - the type system tracks success/failure
4. *Immutability* - no surprising mutations
5. *Railway-oriented programming* - errors propagate automatically

Run the examples:
```bash
python3 examples.py
```


### Maybe Type - Handling Optional Values

```python
from functional_core import Some, nothing, safe_head

# Create Maybe values
x = Some(42)          # Has a value
y = nothing()         # No value

# Chain operations - they short-circuit on Nothing
result = (
    Some(5)
    .map(lambda x: x * 2)      # Some(10)
    .filter(lambda x: x > 8)   # Some(10)
    .map(lambda x: x + 1)      # Some(11)
)

# Safe operations that return Maybe
numbers = [1, 2, 3]
first = safe_head(numbers)  # Some(1)
first_empty = safe_head([]) # Nothing

# Get value with default
value = first.get_or_else(0)  # 1
```


### Result Type - Error Handling

```python
from functional_core import Ok, Err, safe_divide, safe_parse_int

# Operations that can fail return Result
result = safe_divide(10, 2)   # Ok(5.0)
result = safe_divide(10, 0)   # Err("Division by zero")

# Chain operations - errors propagate automatically
result = (
    safe_parse_int("42")                     # Ok(42)
    .flat_map(lambda x: safe_divide(100, x)) # Ok(2.38...)
    .map(lambda x: x * 2)                    # Ok(4.76...)
)

# Handle the result
if result.is_ok():
    print(f"Success: {result.get_or_else(0)}")
else:
    print(f"Error: {result}")
```


### Function Composition

```python
from functional_core import compose, pipe, curry

# Compose functions (right to left)
add_one = lambda x: x + 1
double = lambda x: x * 2

composed = compose(add_one, double)
result = composed(5)  # (5 * 2) + 1 = 11

# Pipe (left to right - more intuitive)
piped = pipe(double, add_one)
result = piped(5)  # (5 * 2) + 1 = 11

# Currying for partial application
def add(a, b, c):
    return a + b + c

curried_add = curry(add)
add_5 = curried_add(5)
add_5_and_10 = add_5(10)
result = add_5_and_10(3)  # 18
```


### Core Types

#### Maybe[A]

Represents an optional value - either `Some(value)` or `Nothing`.

*Methods:*
- `map(f)` - Transform the value if present
- `flat_map(f)` - Chain Maybe-returning operations
- `filter(predicate)` - Keep value only if predicate is true
- `get_or_else(default)` - Extract value or return default
- `or_else(alternative)` - Use alternative if Nothing
- `is_some()`, `is_none()` - Check state

*Example:*
```python
# Avoid null checks
def get_user_email(user_id):
    return (
        fetch_user(user_id)           # Maybe[User]
        .map(lambda u: u.email)       # Maybe[str]
        .filter(lambda e: "@" in e)   # Maybe[str]
        .get_or_else("no-email@example.com")
    )
```


#### Result[A, E]

Represents a computation that can succeed (`Ok(value)`) or fail (`Err(error)`).

*Methods:*
- `map(f)` - Transform the success value
- `map_err(f)` - Transform the error value
- `flat_map(f)` - Chain Result-returning operations
- `get_or_else(default)` - Extract value or return default
- `or_else(alternative)` - Use alternative if Err
- `is_ok()`, `is_err()` - Check state

*Example:*
```python
# Railway-oriented programming
def process_payment(amount_str, account_str):
    return (
        safe_parse_int(amount_str)           # Result[int, str]
        .flat_map(validate_amount)           # Result[int, str]
        .flat_map(lambda amt: 
            safe_parse_int(account_str)
            .flat_map(lambda acc: charge_account(acc, amt))
        )
    )
```


### Real-World Example

```python
from functional_core import Ok, Err, safe_parse_int

def validate_age(age_str):
    """Validate and parse age"""
    return (
        safe_parse_int(age_str)
        .flat_map(lambda age: 
            Ok(age) if 0 <= age <= 150 
            else Err("Age out of range")
        )
    )

def validate_email(email):
    """Simple email validation"""
    if "@" in email and "." in email:
        return Ok(email)
    return Err("Invalid email format")

def create_user(name, age_str, email):
    """Create user with validation"""
    age_result = validate_age(age_str)
    email_result = validate_email(email)
    
    if age_result.is_err():
        return age_result
    if email_result.is_err():
        return email_result
    
    return Ok({
        "name": name,
        "age": age_result.get_or_else(0),
        "email": email_result.get_or_else("")
    })

# Usage
user = create_user("Alice", "30", "alice@example.com")
# Ok({'name': 'Alice', 'age': 30, 'email': 'alice@example.com'})

bad_user = create_user("Bob", "200", "bob@example.com")
# Err('Age out of range')
```


### Data Pipeline Example

```python
from functional_core import safe_get

def fetch_user_id(username):
    users = {"alice": 1, "bob": 2}
    return safe_get(users, username)

def fetch_user_score(user_id):
    scores = {1: 95, 2: 87}
    return safe_get(scores, user_id)

def grade_score(score):
    if score >= 90:
        return Some("A")
    elif score >= 80:
        return Some("B")
    else:
        return Some("C")

def get_user_grade(username):
    return (
        fetch_user_id(username)      # Maybe[int]
        .flat_map(fetch_user_score)  # Maybe[int]
        .flat_map(grade_score)       # Maybe[str]
    )

grade = get_user_grade("alice")  # Some('A')
missing = get_user_grade("xyz")   # Nothing
```


### Utility Functions

#### Safe Operations

All safe operations return Maybe or Result instead of raising exceptions:

```python
safe_divide(10, 2)           # Ok(5.0)
safe_divide(10, 0)           # Err("Division by zero")
safe_parse_int("42")         # Ok(42)
safe_parse_int("xyz")        # Err("Failed to parse...")
safe_get({"a": 1}, "a")      # Some(1)
safe_get({"a": 1}, "b")      # Nothing
safe_head([1, 2, 3])         # Some(1)
safe_head([])                # Nothing
```


#### List Operations

```python
# Fold (reduce)
foldl(lambda acc, x: acc + x, 0, [1, 2, 3, 4])  # 10

# Traverse - apply function to all elements
traverse_maybe(
    lambda x: Some(x * 2) if x > 0 else nothing(),
    [1, 2, 3]
)  # Some([2, 4, 6])

# Sequence - convert list of Maybes to Maybe of list
sequence_maybe([Some(1), Some(2), Some(3)])  # Some([1, 2, 3])
sequence_maybe([Some(1), nothing(), Some(3)])  # Nothing
```


### Design Principles

1. *Familiar Python syntax* - uses lambda, dataclasses, type hints
2. *Immutability* - all types are frozen
3. *Composability* - everything chains naturally
4. *Type safety* - generic types throughout
5. *Zero dependencies* - pure Python standard library
6. *Lazy evaluation* - operations only execute when needed


### Comparison to Other Languages

This library brings concepts from:
- *Haskell* - Maybe, Either, function composition
- *Scala* - Option, Either, for-comprehensions (via flat_map)
- *Rust* - Option, Result, Railway-oriented programming
- *F#* - Railway-oriented programming pattern
- *OCaml* - option type, result type


### When to Use ..

Use *Maybe* when:
- Dealing with values that might be missing
- Want to avoid null checks
- Need to chain operations on optional data

Use *Result* when:
- Operations can fail with meaningful error messages
- Want type-safe error handling
- Building validation pipelines
- Replacing try/except with explicit error handling

Use *composition* when:
- Building complex transformations from simple functions
- Creating reusable function pipelines
- Want clear, declarative data processing


### Advanced Patterns

#### Applicative Style

```python
# Combine multiple Maybe values
name = Some("Alice")
age = Some(30)

# If both are Some, create a user
user = (
    name.flat_map(lambda n:
        age.map(lambda a: {"name": n, "age": a})
    )
)
```

#### Error Recovery

```python
# Try primary, fall back to alternative
result = (
    primary_operation()
    .or_else(backup_operation())
    .get_or_else(default_value)
)
```


#### Validation Chaining

```python
def validate_all(data):
    return (
        validate_field1(data)
        .flat_map(lambda _: validate_field2(data))
        .flat_map(lambda _: validate_field3(data))
        .map(lambda _: data)  # Return original data if all valid
    )
```


## Next Steps

Potential extensions:
- Non-empty lists
- Validated types
- IO monads
- State monads
- Reader/Writer monads
- Async/Future types
- Property-based testing integration
