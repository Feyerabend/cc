"""
Examples for Extended Functional Core - Monads and Async
Demonstrates IO, State, Reader monads and async variants.
"""

import asyncio
from functional import (
    # IO Monad
    io_pure, io_lazy, io_print, io_input, io_sequence,
    io_read_file, io_write_file,
    # State Monad
    state_pure, state_get, state_put, state_modify, state_gets,
    # Reader Monad
    reader_pure, reader_ask, reader_asks, reader_local,
    # Async
    AsyncSome, async_nothing, AsyncOk, AsyncErr,
    async_io_pure, async_io_lazy, async_io_sleep,
    safe_async_operation
)


# IO MONAD EXAMPLES

def example_io_basics():
    """Basic IO monad usage - lazy side effects"""
    print("IO Monad Basics")
    
    # IO actions are lazy - they don't execute until run()
    greeting = io_pure("Hello")
    print(f"Created IO: {greeting}")  # Just shows IO, doesn't run
    
    # Now execute it
    result = greeting.run()
    print(f"After run(): {result}")
    
    # Chain IO operations
    program = (
        io_pure(5)
        .map(lambda x: x * 2)
        .map(lambda x: x + 1)
    )
    
    print(f"IO computation: {program}")
    print(f"Result: {program.run()}")
    print()


def example_io_side_effects():
    """Composing side effects with IO"""
    print("IO Side Effects")
    
    # Build a program with multiple side effects
    program = (
        io_print("What's your name?")
        .flat_map(lambda _: io_input("Name: "))
        .flat_map(lambda name: io_print(f"Hello, {name}!")
                  .map(lambda _: name))
    )
    
    print("Program built (not executed yet)")
    print("To run interactively, uncomment the line below:")
    # result = program.run()  # Uncomment to run interactively
    print()


def example_io_file_operations():
    """IO for file operations"""
    print("IO File Operations")
    
    # Create test file
    test_file = "/tmp/test_io.txt"
    
    # Build a program that writes and reads a file
    program = (
        io_write_file(test_file, "Hello from IO monad!")
        .flat_map(lambda _: io_print("File written"))
        .flat_map(lambda _: io_read_file(test_file))
        .flat_map(lambda content: io_print(f"File content: {content}")
                  .map(lambda _: content))
    )
    
    print("Executing file I/O program...")
    result = program.run()
    print(f"Final result: {result!r}")
    print()


def example_io_sequence():
    """Running multiple IO actions"""
    print("IO Sequence")
    
    # Create multiple print actions
    actions = [
        io_print("First"),
        io_print("Second"),
        io_print("Third"),
    ]
    
    # Run them all and collect results
    program = io_sequence(actions)
    
    print("Executing sequence of IO actions:")
    results = program.run()
    print(f"Results: {results}")
    print()



# STATE MONAD EXAMPLES

def example_state_basics():
    """Basic State monad usage"""
    print("State Monad Basics")
    
    # Simple stateful computation
    computation = (
        state_get()  # Get current state
        .map(lambda x: x + 1)  # Increment it
    )
    
    result, final_state = computation.run(10)
    print(f"Initial state: 10")
    print(f"Result: {result}, Final state: {final_state}")
    
    # Modify state
    computation2 = (
        state_modify(lambda x: x * 2)  # Double the state
        .flat_map(lambda _: state_get())  # Get new state
    )
    
    result2, final_state2 = computation2.run(5)
    print(f"\nInitial state: 5")
    print(f"After doubling - Result: {result2}, Final state: {final_state2}")
    print()


def example_state_counter():
    """State monad for counter"""
    print("State Counter")
    
    def increment():
        """Increment counter and return new value"""
        return (
            state_modify(lambda x: x + 1)
            .flat_map(lambda _: state_get())
        )
    
    def add(n):
        """Add n to counter"""
        return state_modify(lambda x: x + n)
    
    # Build a computation
    program = (
        increment()
        .flat_map(lambda _: increment())
        .flat_map(lambda _: add(5))
        .flat_map(lambda _: state_get())
    )
    
    result, final_state = program.run(0)
    print(f"Starting from 0:")
    print(f"After increment, increment, add(5)")
    print(f"Result: {result}, Final state: {final_state}")
    print()


def example_state_stack():
    """State monad for stack operations"""
    print("State Stack")
    
    def push(value):
        """Push value onto stack"""
        return state_modify(lambda stack: [value] + stack)
    
    def pop():
        """Pop value from stack"""
        def pop_fn(stack):
            if stack:
                return (stack[0], stack[1:])
            return (None, stack)
        return _StateImpl(pop_fn)
    
    # Import for access to _StateImpl
    from functional import _StateImpl
    
    # Build stack operations
    program = (
        push(1)
        .flat_map(lambda _: push(2))
        .flat_map(lambda _: push(3))
        .flat_map(lambda _: pop())
        .flat_map(lambda top: state_get().map(lambda s: (top, s)))
    )
    
    result, final_state = program.run([])
    top, stack = result
    print(f"Pushed 1, 2, 3, then popped")
    print(f"Popped value: {top}")
    print(f"Remaining stack: {final_state}")
    print()


# READER MONAD EXAMPLES

def example_reader_basics():
    """Basic Reader monad usage - dependency injection"""
    print("Reader Monad Basics")
    
    # Reader that accesses the environment
    computation = (
        reader_ask()  # Get environment
        .map(lambda env: env["name"])
    )
    
    result = computation.run({"name": "Alice", "age": 30})
    print(f"Environment: {{'name': 'Alice', 'age': 30}}")
    print(f"Extracted name: {result}")
    print()


def example_reader_config():
    """Reader for configuration"""
    print("Reader Configuration")
    
    # Configuration-dependent computations
    def get_db_url():
        return reader_asks(lambda config: config.get("db_url"))
    
    def get_timeout():
        return reader_asks(lambda config: config.get("timeout", 30))
    
    def build_connection_string():
        return (
            get_db_url()
            .flat_map(lambda url:
                get_timeout().map(lambda timeout:
                    f"{url}?timeout={timeout}"))
        )
    
    # Run with different configs
    config1 = {"db_url": "postgres://localhost/mydb", "timeout": 60}
    config2 = {"db_url": "mysql://localhost/otherdb"}
    
    result1 = build_connection_string().run(config1)
    result2 = build_connection_string().run(config2)
    
    print(f"Config 1: {result1}")
    print(f"Config 2: {result2}")
    print()


def example_reader_dependency_injection():
    """Reader for dependency injection"""
    print("Reader Dependency Injection")
    
    # Services that depend on injected dependencies
    def get_user_service():
        return reader_asks(lambda deps: deps["user_service"])
    
    def get_email_service():
        return reader_asks(lambda deps: deps["email_service"])
    
    def send_welcome_email(user_id):
        return (
            get_user_service()
            .flat_map(lambda user_svc:
                get_email_service().map(lambda email_svc:
                    f"{email_svc.send(user_svc.get(user_id))}"
                ))
        )
    
    # Mock services
    class MockUserService:
        def get(self, user_id):
            return f"User({user_id})"
    
    class MockEmailService:
        def send(self, user):
            return f"Email sent to {user}"
    
    dependencies = {
        "user_service": MockUserService(),
        "email_service": MockEmailService()
    }
    
    result = send_welcome_email(123).run(dependencies)
    print(f"Result: {result}")
    print()



# ASYNC MAYBE EXAMPLES

async def example_async_maybe():
    """AsyncMaybe for async optional values"""
    print("Async Maybe")
    
    async def fetch_user(user_id):
        """Simulate async user fetch"""
        await asyncio.sleep(0.01)
        if user_id == 1:
            return AsyncSome({"id": 1, "name": "Alice"})
        return async_nothing()
    
    async def get_user_email(user):
        """Extract email from user"""
        await asyncio.sleep(0.01)
        email = user.get("email")
        if email:
            return AsyncSome(email)
        return async_nothing()
    
    # Chain async operations
    result1 = await (
        await fetch_user(1)
    ).map_async(lambda user: asyncio.sleep(0.01) or user)
    
    print(f"Fetch user 1: {result1}")
    
    result2 = await fetch_user(999)
    print(f"Fetch user 999: {result2}")
    
    value = await result1.get_or_else({"id": 0, "name": "Unknown"})
    print(f"User or default: {value}")
    print()



# ASYNC RESULT EXAMPLES

async def example_async_result():
    """AsyncResult for async error handling"""
    print("Async Result")
    
    async def async_divide(a, b):
        """Async division"""
        await asyncio.sleep(0.01)
        if b == 0:
            return AsyncErr("Division by zero")
        return AsyncOk(a / b)
    
    async def async_parse_int(s):
        """Async int parsing"""
        await asyncio.sleep(0.01)
        try:
            return AsyncOk(int(s))
        except ValueError as e:
            return AsyncErr(str(e))
    
    # Chain async operations
    result = await (
        await async_parse_int("42")
    ).flat_map_async(lambda x: async_divide(100, x))
    
    print(f"Parse '42' and divide 100 by it: {result}")
    
    # Error case
    result2 = await (
        await async_parse_int("0")
    ).flat_map_async(lambda x: async_divide(100, x))
    
    print(f"Parse '0' and divide: {result2}")
    
    # Get value or default
    value = await result.get_or_else(0.0)
    print(f"Value: {value}")
    print()



# ASYNC IO EXAMPLES

async def example_async_io():
    """AsyncIO for async side effects"""
    print("Async IO")
    
    # Build async program
    program = (
        async_io_pure("Starting...")
        .map_async(lambda msg: asyncio.sleep(0.1) or msg)
        .map(lambda msg: f"{msg} Done!")
    )
    
    print("Created AsyncIO program")
    result = await program.run()
    print(f"Result: {result}")
    
    # Chain async operations with sleep
    program2 = (
        async_io_pure(1)
        .flat_map(lambda x: async_io_sleep(0.1).map(lambda _: x * 2))
        .flat_map(lambda x: async_io_sleep(0.1).map(lambda _: x + 3))
    )
    
    result2 = await program2.run()
    print(f"After async operations: {result2}")
    print()



# COMBINING MONADS

def example_combining_io_and_state():
    """Combining IO and State"""
    print("Combining IO and State")
    
    # This demonstrates the concept - in practice you'd use monad transformers
    # For now, we show the pattern
    
    def stateful_io_simulation():
        """Simulate stateful IO"""
        state = {"counter": 0}
        
        def increment_and_log():
            state["counter"] += 1
            return io_print(f"Counter: {state['counter']}")
        
        return io_sequence([
            increment_and_log(),
            increment_and_log(),
            increment_and_log(),
        ]).map(lambda _: state["counter"])
    
    print("Executing stateful IO simulation:")
    result = stateful_io_simulation().run()
    print(f"Final counter: {result}")
    print()


async def example_safe_async_operation():
    """Safe async operations with error handling"""
    print("Safe Async Operations")
    
    async def risky_operation():
        """Operation that might fail"""
        await asyncio.sleep(0.01)
        return 10 / 2
    
    async def failing_operation():
        """Operation that will fail"""
        await asyncio.sleep(0.01)
        return 10 / 0
    
    # Safe execution
    result1 = await safe_async_operation(risky_operation)
    print(f"Risky operation: {result1}")
    
    result2 = await safe_async_operation(failing_operation)
    print(f"Failing operation: {result2}")
    
    # Get value safely
    value = await result1.get_or_else(0)
    print(f"Value: {value}")
    print()


# ALL

async def run_async_examples():
    """Run all async examples"""
    await example_async_maybe()
    await example_async_result()
    await example_async_io()
    await example_safe_async_operation()


if __name__ == "__main__":
    # Sync examples
    example_io_basics()
    example_io_file_operations()
    example_io_sequence()
    example_state_basics()
    example_state_counter()
    example_state_stack()
    example_reader_basics()
    example_reader_config()
    example_reader_dependency_injection()
    example_combining_io_and_state()
    
    # Async examples
    print("\n" + "="*60)
    print("ASYNC EXAMPLES")
    print("="*60 + "\n")
    asyncio.run(run_async_examples())
    
    print("\nAll extended examples completed!")

