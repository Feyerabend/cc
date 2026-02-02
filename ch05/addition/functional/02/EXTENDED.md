
### Maybe / Option

```python
from functional_core import Some, nothing, maybe

# Create
Some(42)                    # Has value
nothing()                   # No value
maybe(None)                 # Nothing
maybe(42)                   # Some(42)

# Operations
Some(5).map(lambda x: x * 2)              # Some(10)
Some(5).flat_map(lambda x: Some(x + 1))   # Some(6)
Some(5).filter(lambda x: x > 3)           # Some(5)
Some(5).get_or_else(0)                    # 5
nothing().get_or_else(0)                  # 0
nothing().or_else(Some(10))               # Some(10)
```

### Result / Either

```python
from functional_core import Ok, Err

# Create
Ok(42)                      # Success
Err("error")                # Failure

# Operations
Ok(5).map(lambda x: x * 2)                # Ok(10)
Ok(5).flat_map(lambda x: Ok(x + 1))       # Ok(6)
Err("oops").map(lambda x: x * 2)          # Err("oops")
Ok(5).get_or_else(0)                      # 5
Err("x").get_or_else(0)                   # 0
```

### IO Monad

```python
from functional import io_pure, io_lazy, io_print

# Create
io_pure(42)                         # Wrap value
io_lazy(lambda: print("hi"))        # Wrap effect

# Operations (lazy until .run())
io_pure(5).map(lambda x: x * 2)               # IO
io_pure(5).flat_map(lambda x: io_pure(x + 1)) # IO

# Execute
io_pure(42).run()                   # 42
io_print("hello").run()             # prints, returns None

# Common actions
io_print("message")                 # Print
io_input("prompt: ")                # Input
io_read_file("path.txt")            # Read file
io_write_file("path.txt", data)     # Write file
io_sequence([io1, io2, io3])        # Run multiple
```

### State Monad

```python
from functional import (
    state_pure, state_get, state_put, state_modify, state_gets
)

# Create
state_pure(42)                    # Return value, keep state
state_get()                       # Get state
state_put(10)                     # Set state
state_modify(lambda x: x + 1)     # Modify state
state_gets(lambda x: x * 2)       # Get derived value

# Operations
state_get().map(lambda x: x + 1)              # State
state_get().flat_map(lambda x: state_put(x))  # State

# Execute
state_get().run(10)                           # (10, 10)
state_modify(lambda x: x * 2).run(5)          # (None, 10)
state_pure(42).run(anything)                  # (42, anything)

# Only value
state_get().eval(10)              # 10

# Only state
state_put(20).exec(10)            # 20
```

### Reader Monad

```python
from functional import reader_pure, reader_ask, reader_asks

# Create
reader_pure(42)                              # Ignore env
reader_ask()                                 # Get env
reader_asks(lambda env: env["key"])          # Extract from env

# Operations
reader_ask().map(lambda x: x["name"])        # Reader
reader_asks(lambda c: c["db"]).flat_map(...) # Reader

# Execute
reader_ask().run({"key": "value"})           # {"key": "value"}
reader_asks(lambda e: e["x"]).run({"x": 5})  # 5
```

### AsyncMaybe

```python
from functional import AsyncSome, async_nothing

# Create
AsyncSome(42)                   # Has value
async_nothing()                 # No value

# Operations (all async)
await AsyncSome(5).map(lambda x: x * 2)              # AsyncSome(10)
await AsyncSome(5).map_async(async_func)             # AsyncSome(...)
await AsyncSome(5).flat_map(lambda x: AsyncSome(x))  # AsyncSome(5)
await AsyncSome(5).get_or_else(0)                    # 5

# Check
await AsyncSome(5).is_some()    # True
await async_nothing().is_none() # True
```

### AsyncResult

```python
from functional import AsyncOk, AsyncErr

# Create
AsyncOk(42)                     # Success
AsyncErr("error")               # Failure

# Operations (all async)
await AsyncOk(5).map(lambda x: x * 2)               # AsyncOk(10)
await AsyncOk(5).map_async(async_func)              # AsyncOk(...)
await AsyncOk(5).flat_map(lambda x: AsyncOk(x))     # AsyncOk(5)
await AsyncErr("x").map(lambda x: x * 2)            # AsyncErr("x")
await AsyncOk(5).get_or_else(0)                     # 5

# Check
await AsyncOk(5).is_ok()        # True
await AsyncErr("x").is_err()    # True
```

### AsyncIO

```python
from functional import async_io_pure, async_io_lazy, async_io_sleep

# Create
async_io_pure(42)                        # Wrap value
async_io_lazy(async_func)                # Wrap async effect

# Operations (setup only, lazy)
async_io_pure(5).map(lambda x: x * 2)                 # AsyncIO
async_io_pure(5).map_async(async_func)                # AsyncIO
async_io_pure(5).flat_map(lambda x: async_io_pure(x)) # AsyncIO

# Execute (runs the async computation)
await async_io_pure(42).run()            # 42
await async_io_sleep(1.0).run()          # sleeps, returns None
```

### Function Composition

```python
from functional_core import compose, pipe, curry

# Compose (right to left)
f = compose(add1, mul2, square)
f(5)  # add1(mul2(square(5))) = add1(mul2(25)) = add1(50) = 51

# Pipe (left to right)
f = pipe(square, mul2, add1)  
f(5)  # add1(mul2(square(5))) = 51

# Curry
add3 = curry(lambda a, b, c: a + b + c)
add3(1)(2)(3)   # 6
add3(1, 2)(3)   # 6
add3(1)(2, 3)   # 6
```

### Safe Operations

```python
from functional_core import (
    safe_divide, safe_parse_int, safe_get, safe_head
)

safe_divide(10, 2)              # Ok(5.0)
safe_divide(10, 0)              # Err("Division by zero")
safe_parse_int("42")            # Ok(42)
safe_parse_int("xyz")           # Err("...")
safe_get({"a": 1}, "a")         # Some(1)
safe_get({"a": 1}, "b")         # Nothing
safe_head([1, 2, 3])            # Some(1)
safe_head([])                   # Nothing
```

### List Operations

```python
from functional_core import foldl, foldr, traverse_maybe, sequence_maybe

# Fold
foldl(lambda acc, x: acc + x, 0, [1,2,3])  # 6

# Traverse - apply function to all
traverse_maybe(lambda x: Some(x * 2), [1,2,3])
# Some([2, 4, 6])

# Sequence - convert list of Maybe to Maybe of list
sequence_maybe([Some(1), Some(2), Some(3)])
# Some([1, 2, 3])

sequence_maybe([Some(1), nothing(), Some(3)])
# Nothing
```

### Common Patterns

#### Railway-Oriented Programming
```python
result = (
    safe_parse_int("42")
    .flat_map(validate)
    .flat_map(process)
    .flat_map(save)
)
```

#### Chaining with Maybe
```python
user_email = (
    fetch_user(user_id)
    .flat_map(lambda u: maybe(u.email))
    .filter(lambda e: "@" in e)
    .get_or_else("default@example.com")
)
```

#### Lazy IO Pipeline
```python
program = (
    io_read_file("input.txt")
    .map(str.upper)
    .flat_map(lambda data: io_write_file("output.txt", data))
    .flat_map(lambda _: io_print("Done!"))
)
# Nothing happens until:
program.run()
```

#### Stateful Computation
```python
def counter():
    return (
        state_modify(lambda x: x + 1)
        .flat_map(lambda _: state_get())
    )

# Thread state through multiple operations
result, final = (
    counter()
    .flat_map(lambda _: counter())
    .flat_map(lambda _: counter())
).run(0)
# result = 3, final = 3
```

#### Dependency Injection
```python
def get_service():
    return reader_asks(lambda deps: deps["service"])

def use_service():
    return (
        get_service()
        .map(lambda svc: svc.do_something())
    )

# Inject dependencies at the end
result = use_service().run({"service": MyService()})
```

#### Async Error Handling
```python
async def process():
    result = await (
        await async_fetch_data()
    ).flat_map_async(validate_async)
    
    return await result.get_or_else(default_value)
```

### Type Signatures

```python
Maybe[A]                        # Some(value: A) | Nothing
Result[A, E]                    # Ok(value: A) | Err(error: E)
IO[A]                           # Lazy(() -> A)
State[S, A]                     # S -> (A, S)
Reader[R, A]                    # R -> A
AsyncMaybe[A]                   # async Maybe[A]
AsyncResult[A, E]               # async Result[A, E]
AsyncIO[A]                      # async IO[A]
```

### Imports Cheat Sheet

```python
# Core (01)
from functional_core import (
    Some, nothing, maybe,        # Maybe
    Ok, Err,                     # Result
    compose, pipe, curry,        # Functions
    safe_divide, safe_parse_int, # Safe ops
    foldl, traverse_maybe,       # Lists
)

# Extended (02)
from functional import (
    io_pure, io_lazy, io_print,   # IO
    state_get, state_put,         # State
    reader_ask, reader_asks,      # Reader
    AsyncSome, async_nothing,     # AsyncMaybe
    AsyncOk, AsyncErr,            # AsyncResult
    async_io_pure, async_io_lazy, # AsyncIO
)
```
