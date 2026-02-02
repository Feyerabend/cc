
## Functional Core - Added Monads & Async

This extends the [functional core](./../02/) with advanced monads and async support.

1. *IO Monad* - Lazy Side Effects
2. *State Monad* - Stateful Computations  
3. *Reader Monad* - Dependency Injection
4. *AsyncMaybe* - Async Optional Values
5. *AsyncResult* - Async Error Handling
6. *AsyncIO* - Async Side Effects


### IO Monad - Pure Side Effects

The IO monad represents side effects as *lazy, composable values*.
Operations don't execute until you call `.run()`.

### Why IO?

Without IO:
```python
# Side effects happen immediately, can't compose
print("Hello")
x = input("Name: ")
print(f"Hi, {x}")
```

With IO:
```python
# Side effects are values - compose first, execute later
program = (
    io_print("Hello")
    .flat_map(lambda _: io_input("Name: "))
    .flat_map(lambda name: io_print(f"Hi, {name}!"))
)

# Program is just a value - but hasn't run yet
# Execute when ready:
program.run()
```

#### Basic Usage

```python
from functional import io_pure, io_lazy, io_print, io_read_file

# Wrap pure values
greeting = io_pure("Hello")
result = greeting.run()  # "Hello"

# Wrap side effects
program = io_print("Starting...")
program.run()  # Prints now

# Chain operations
pipeline = (
    io_read_file("input.txt")
    .map(lambda content: content.upper())
    .map(lambda text: f"CONTENT: {text}")
    .flat_map(lambda text: io_print(text))
)

pipeline.run()  # Reads file, transforms, prints
```

#### File Operations

```python
from functional import io_write_file, io_read_file

# Compose file operations
program = (
    io_write_file("data.txt", "Hello World")
    .flat_map(lambda _: io_read_file("data.txt"))
    .flat_map(lambda content: io_print(f"Read: {content}"))
)

program.run()
```

#### Multiple Actions

```python
from functional import io_sequence

actions = [
    io_print("First"),
    io_print("Second"),
    io_print("Third"),
]

# Run all and collect results
io_sequence(actions).run()  # [None, None, None]
```



### State Monad - Threading State

The State monad threads state through computations without global variables.

#### Why State?

Without State:
```python
counter = 0

def increment():
    global counter
    counter += 1
    return counter

# Global state, hard to compose
```

With State:
```python
from functional import state_get, state_modify

def increment():
    return (
        state_modify(lambda x: x + 1)
        .flat_map(lambda _: state_get())
    )

# Pure function, easy to compose
result, final_state = increment().run(0)  # (1, 1)
```

#### Basic Operations

```python
from functional import (
    state_pure, state_get, state_put, 
    state_modify, state_gets
)

# Get current state
state_get().run(10)  # (10, 10)

# Put new state
state_put(20).run(10)  # (None, 20)

# Modify state
state_modify(lambda x: x * 2).run(5)  # (None, 10)

# Get derived value
state_gets(lambda x: x + 1).run(10)  # (11, 10)
```

#### Counter Example

```python
def increment():
    return state_modify(lambda x: x + 1).flat_map(lambda _: state_get())

def add(n):
    return state_modify(lambda x: x + n)

program = (
    increment()
    .flat_map(lambda _: increment())
    .flat_map(lambda _: add(5))
    .flat_map(lambda _: state_get())
)

result, final = program.run(0)  # (7, 7)
```

#### Stack Example

```python
from functional import _StateImpl

def push(value):
    return state_modify(lambda stack: [value] + stack)

def pop():
    def pop_fn(stack):
        if stack:
            return (stack[0], stack[1:])
        return (None, stack)
    return _StateImpl(pop_fn)

program = (
    push(1)
    .flat_map(lambda _: push(2))
    .flat_map(lambda _: push(3))
    .flat_map(lambda _: pop())
)

top, stack = program.run([])  # (3, [2, 1])
```



### Reader Monad - Dependency Injection

The Reader monad passes environment/config through computations without explicit parameters.

#### Why Reader?

Without Reader:
```python
def get_user(config, user_id):
    url = config["db_url"]
    # ... use url
    
def send_email(config, user):
    smtp = config["smtp_server"]
    # ... use smtp

# Config passed everywhere!
result = send_email(config, get_user(config, 123))
```

With Reader:
```python
from functional import reader_asks

def get_user(user_id):
    return reader_asks(lambda config: f"User from {config['db_url']}")

def send_email(user):
    return reader_asks(lambda config: f"Email via {config['smtp_server']}")

# Compose without mentioning config
program = get_user(123).flat_map(send_email)

# Provide config once at the end
result = program.run(config)
```

#### Basic Operations

```python
from functional import reader_pure, reader_ask, reader_asks

# Pure value (ignores env)
reader_pure(42).run(anything)  # 42

# Get environment
reader_ask().run({"name": "Alice"})  # {"name": "Alice"}

# Extract from environment  
reader_asks(lambda env: env["name"]).run({"name": "Bob"})  # "Bob"
```

#### Configuration Example

```python
def get_db_url():
    return reader_asks(lambda config: config["db_url"])

def get_timeout():
    return reader_asks(lambda config: config.get("timeout", 30))

def build_connection():
    return (
        get_db_url()
        .flat_map(lambda url:
            get_timeout().map(lambda timeout:
                f"{url}?timeout={timeout}"))
    )

config = {"db_url": "postgres://localhost/db", "timeout": 60}
result = build_connection().run(config)
# "postgres://localhost/db?timeout=60"
```

#### Dependency Injection

```python
def get_user_service():
    return reader_asks(lambda deps: deps["user_service"])

def get_email_service():
    return reader_asks(lambda deps: deps["email_service"])

def send_welcome(user_id):
    return (
        get_user_service()
        .flat_map(lambda user_svc:
            get_email_service().map(lambda email_svc:
                email_svc.send(user_svc.get(user_id))
            ))
    )

# Inject dependencies at runtime
dependencies = {
    "user_service": MyUserService(),
    "email_service": MyEmailService()
}

send_welcome(123).run(dependencies)
```



### Async Monads

All the power of Maybe, Result, and IO, but for async operations!

#### AsyncMaybe - Async Optional Values

```python
from functional import AsyncSome, async_nothing

async def fetch_user(user_id):
    await asyncio.sleep(0.1)
    if user_id == 1:
        return AsyncSome({"id": 1, "name": "Alice"})
    return async_nothing()

# Chain async operations
user = await fetch_user(1)
name = await user.map(lambda u: u["name"])
default = await name.get_or_else("Unknown")
```

#### AsyncResult - Async Error Handling

```python
from functional import AsyncOk, AsyncErr

async def async_divide(a, b):
    await asyncio.sleep(0.1)
    if b == 0:
        return AsyncErr("Division by zero")
    return AsyncOk(a / b)

async def async_parse(s):
    try:
        return AsyncOk(int(s))
    except ValueError as e:
        return AsyncErr(str(e))

# Chain async operations - errors propagate
result = await (
    await async_parse("42")
).flat_map_async(lambda x: async_divide(100, x))

# AsyncOk(2.38...)
```

#### AsyncIO - Async Side Effects

```python
from functional import async_io_pure, async_io_sleep

# Lazy async computation
program = (
    async_io_pure("Starting")
    .flat_map(lambda msg: async_io_sleep(1.0).map(lambda _: msg))
    .map(lambda msg: f"{msg} - Done!")
)

# Nothing happens until run()
result = await program.run()
```

#### Safe Async Operations

```python
from functional import safe_async_operation

async def risky_operation():
    return 10 / 0  # Will raise

# Wrap in AsyncResult
result = await safe_async_operation(risky_operation)
# AsyncErr(ZeroDivisionError(...))

value = await result.get_or_else(0)  # 0
```



### Combining Monads

#### IO + State Pattern

```python
# Simulate stateful IO
def stateful_program():
    state = {"counter": 0}
    
    def increment_and_log():
        state["counter"] += 1
        return io_print(f"Counter: {state['counter']}")
    
    return io_sequence([
        increment_and_log(),
        increment_and_log(),
        increment_and_log(),
    ])

stateful_program().run()
# Prints: Counter: 1, Counter: 2, Counter: 3
```

#### Reader + IO Pattern

```python
def log_with_config():
    return (
        reader_asks(lambda config: config["log_level"])
        .map(lambda level: io_print(f"Log level: {level}"))
    )

# Get IO action based on config
io_action = log_with_config().run({"log_level": "DEBUG"})
io_action.run()  # Prints: Log level: DEBUG
```



### Advanced Patterns

#### Lazy Evaluation

```python
# IO doesn't execute until run()
expensive = io_lazy(lambda: complex_computation())
cheap = io_pure(42)

# Can pass around, compose, without executing
program = expensive.map(process).flat_map(transform)

# Execute only when needed
result = program.run()
```

#### Stateful Generators

```python
def fibonacci():
    def fib_step():
        return (
            state_gets(lambda s: s[0])  # Get current
            .flat_map(lambda current:
                state_modify(lambda s: (s[1], s[0] + s[1]))
                .map(lambda _: current)
            )
        )
    return fib_step

# Generate Fibonacci numbers
gen = fibonacci()
n1, s1 = gen().run((0, 1))  # 0
n2, s2 = gen().run(s1)       # 1
n3, s3 = gen().run(s2)       # 1
n4, s4 = gen().run(s3)       # 2
```

#### Configuration-Based Execution

```python
def create_processor():
    return (
        reader_asks(lambda config: config["mode"])
        .map(lambda mode:
            fast_processor() if mode == "fast" else slow_processor()
        )
    )

# Different configs = different behavior
fast_config = {"mode": "fast"}
slow_config = {"mode": "slow"}

processor1 = create_processor().run(fast_config)
processor2 = create_processor().run(slow_config)
```



### Benefits Summary

| Monad | Solves | Replaces |
|-------|--------|----------|
| IO | Side effects | Immediate execution |
| State | Threading state | Global variables |
| Reader | Config passing | Parameter drilling |
| AsyncMaybe | Async optionals | Async None checks |
| AsyncResult | Async errors | Async try/except |
| AsyncIO | Async side effects | Async immediate execution |



### Principles

1. *Lazy* - IO and AsyncIO don't execute until `.run()`
2. *Pure* - State and Reader are pure functions
3. *Composable* - All monads chain with `map` and `flat_map`
4. *Type-safe* - Generic types throughout
5. *Backwards compatible* - Works alongside original functional_core



### When to Use Each

*IO*: When you have side effects (file I/O, printing, network) and want to keep functions pure

*State*: When you need to thread state through computations without global variables

*Reader*: When you have configuration/environment that many functions need

*AsyncMaybe/AsyncResult*: When you have async operations that might fail or return nothing

*AsyncIO*: When you have async side effects and want lazy execution



### Complete Example

```python
from functional import *
from functional_core import *

# Combine multiple monads
def process_user_async(user_id):
    # Reader for config
    def get_config_value(key):
        return reader_asks(lambda config: config[key])
    
    # IO for logging
    def log(message):
        return io_print(f"[LOG] {message}")
    
    # State for tracking
    def track_operation():
        return state_modify(lambda count: count + 1)
    
    # AsyncResult for async operations
    async def fetch_and_process():
        result = await fetch_user_async(user_id)
        return await result.map_async(process_user_data)
    
    return fetch_and_process

# Each monad handles its concern
# - Reader: config
# - IO: logging  
# - State: counting
# - AsyncResult: async + errors
```



## Next Steps / Projects

The library now has the core monads from functional languages.
Potential future extensions:

- *Writer Monad* - Accumulating logs/output
- *Validation Monad* - Accumulating errors (not fail-fast)
- *Monad Transformers* - Combine monads (ReaderT, StateT, etc.)
- *Free Monads* - Build DSLs
- *Lens/Optics* - Deep immutable updates

