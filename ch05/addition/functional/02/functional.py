"""
Functional Programming Core - MORE: Monads and Async

This module extends the functional core with:
- IO monad for lazy, composable side effects
- State monad for stateful computations
- Reader monad for dependency injection
- Async versions of Maybe and Result
- AsyncIO monad
"""

from typing import TypeVar, Generic, Callable, Tuple, Any, Awaitable
from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncio


# Type variables
A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
S = TypeVar('S')  # State type
R = TypeVar('R')  # Reader environment type
E = TypeVar('E')  # Error type



# IO MONAD - Lazy Side Effects

class IO(Generic[A], ABC):
    """
    IO monad represents a lazy computation that performs side effects.
    The computation is not executed until run() is called.
    
    This allows you to compose side effects while keeping them pure
    until the very edge of your program.
    """
    
    @abstractmethod
    def run(self) -> A:
        """Execute the IO action and return the result."""
        pass
    
    @abstractmethod
    def map(self, f: Callable[[A], B]) -> 'IO[B]':
        """Transform the result of this IO."""
        pass
    
    @abstractmethod
    def flat_map(self, f: Callable[[A], 'IO[B]']) -> 'IO[B]':
        """Chain IO operations."""
        pass
    
    def __rshift__(self, f: Callable[[A], 'IO[B]']) -> 'IO[B]':
        """Operator for chaining: io1 >> io2"""
        return self.flat_map(f)


@dataclass
class _IOImpl(IO[A]):
    """Internal implementation of IO."""
    effect: Callable[[], A]
    
    def run(self) -> A:
        return self.effect()
    
    def map(self, f: Callable[[A], B]) -> IO[B]:
        return _IOImpl(lambda: f(self.effect()))
    
    def flat_map(self, f: Callable[[A], IO[B]]) -> IO[B]:
        return _IOImpl(lambda: f(self.effect()).run())
    
    def __repr__(self) -> str:
        return f"IO(<lazy computation>)"


def io_pure(value: A) -> IO[A]:
    """Wrap a pure value in IO."""
    return _IOImpl(lambda: value)


def io_lazy(effect: Callable[[], A]) -> IO[A]:
    """Create an IO from a side-effecting function."""
    return _IOImpl(effect)


# Common IO operations
def io_print(message: str) -> IO[None]:
    """IO action that prints a message."""
    return io_lazy(lambda: print(message))


def io_input(prompt: str = "") -> IO[str]:
    """IO action that reads input."""
    return io_lazy(lambda: input(prompt))


def io_read_file(path: str) -> IO[str]:
    """IO action that reads a file."""
    def read():
        with open(path, 'r') as f:
            return f.read()
    return io_lazy(read)


def io_write_file(path: str, content: str) -> IO[None]:
    """IO action that writes to a file."""
    def write():
        with open(path, 'w') as f:
            f.write(content)
    return io_lazy(write)


def io_sequence(ios: list[IO[A]]) -> IO[list[A]]:
    """Execute a list of IO actions and collect results."""
    def run_all():
        return [io.run() for io in ios]
    return io_lazy(run_all)



# STATE MONAD - Stateful Computations

class State(Generic[S, A], ABC):
    """
    State monad represents a stateful computation.
    It threads state through a sequence of operations.
    
    State[S, A] takes a state of type S and produces a value of type A
    along with a new state.
    """
    
    @abstractmethod
    def run(self, initial_state: S) -> Tuple[A, S]:
        """Run the stateful computation with an initial state."""
        pass
    
    @abstractmethod
    def map(self, f: Callable[[A], B]) -> 'State[S, B]':
        """Transform the value while threading state."""
        pass
    
    @abstractmethod
    def flat_map(self, f: Callable[[A], 'State[S, B]']) -> 'State[S, B]':
        """Chain stateful computations."""
        pass
    
    def eval(self, initial_state: S) -> A:
        """Run and return only the value, discarding final state."""
        return self.run(initial_state)[0]
    
    def exec(self, initial_state: S) -> S:
        """Run and return only the final state, discarding value."""
        return self.run(initial_state)[1]


@dataclass
class _StateImpl(State[S, A]):
    """Internal implementation of State."""
    state_func: Callable[[S], Tuple[A, S]]
    
    def run(self, initial_state: S) -> Tuple[A, S]:
        return self.state_func(initial_state)
    
    def map(self, f: Callable[[A], B]) -> State[S, B]:
        def new_state_func(s: S) -> Tuple[B, S]:
            a, s_new = self.state_func(s)
            return (f(a), s_new)
        return _StateImpl(new_state_func)
    
    def flat_map(self, f: Callable[[A], State[S, B]]) -> State[S, B]:
        def new_state_func(s: S) -> Tuple[B, S]:
            a, s_new = self.state_func(s)
            return f(a).run(s_new)
        return _StateImpl(new_state_func)
    
    def __repr__(self) -> str:
        return f"State(<stateful computation>)"


def state_pure(value: A) -> State[S, A]:
    """Create a State that returns a value without modifying state."""
    return _StateImpl(lambda s: (value, s))


def state_get() -> State[S, S]:
    """Get the current state."""
    return _StateImpl(lambda s: (s, s))


def state_put(new_state: S) -> State[S, None]:
    """Replace the state."""
    return _StateImpl(lambda s: (None, new_state))


def state_modify(f: Callable[[S], S]) -> State[S, None]:
    """Modify the state with a function."""
    return _StateImpl(lambda s: (None, f(s)))


def state_gets(f: Callable[[S], A]) -> State[S, A]:
    """Get a value derived from the state."""
    return _StateImpl(lambda s: (f(s), s))



# READER MONAD - Dependency Injection

class Reader(Generic[R, A], ABC):
    """
    Reader monad represents a computation that depends on some environment.
    This is useful for dependency injection without global state.
    
    Reader[R, A] takes an environment of type R and produces a value of type A.
    """
    
    @abstractmethod
    def run(self, env: R) -> A:
        """Run the computation with the given environment."""
        pass
    
    @abstractmethod
    def map(self, f: Callable[[A], B]) -> 'Reader[R, B]':
        """Transform the result."""
        pass
    
    @abstractmethod
    def flat_map(self, f: Callable[[A], 'Reader[R, B]']) -> 'Reader[R, B]':
        """Chain Reader computations."""
        pass


@dataclass
class _ReaderImpl(Reader[R, A]):
    """Internal implementation of Reader."""
    reader_func: Callable[[R], A]
    
    def run(self, env: R) -> A:
        return self.reader_func(env)
    
    def map(self, f: Callable[[A], B]) -> Reader[R, B]:
        return _ReaderImpl(lambda env: f(self.reader_func(env)))
    
    def flat_map(self, f: Callable[[A], Reader[R, B]]) -> Reader[R, B]:
        return _ReaderImpl(lambda env: f(self.reader_func(env)).run(env))
    
    def __repr__(self) -> str:
        return f"Reader(<computation>)"


def reader_pure(value: A) -> Reader[R, A]:
    """Create a Reader that ignores the environment and returns a value."""
    return _ReaderImpl(lambda env: value)


def reader_ask() -> Reader[R, R]:
    """Get the environment."""
    return _ReaderImpl(lambda env: env)


def reader_asks(f: Callable[[R], A]) -> Reader[R, A]:
    """Get a value derived from the environment."""
    return _ReaderImpl(f)


def reader_local(f: Callable[[R], R], reader: Reader[R, A]) -> Reader[R, A]:
    """Run a Reader with a modified environment."""
    return _ReaderImpl(lambda env: reader.run(f(env)))



# ASYNC MAYBE - Asynchronous Optional Values

class AsyncMaybe(Generic[A], ABC):
    """
    AsyncMaybe represents an async computation that may or may not produce a value.
    Like Maybe, but for async operations.
    """
    
    @abstractmethod
    async def is_some(self) -> bool:
        """Returns True if the AsyncMaybe contains a value."""
        pass
    
    @abstractmethod
    async def is_none(self) -> bool:
        """Returns True if the AsyncMaybe is empty."""
        pass
    
    @abstractmethod
    async def map(self, f: Callable[[A], B]) -> 'AsyncMaybe[B]':
        """Transform the value if present."""
        pass
    
    @abstractmethod
    async def map_async(self, f: Callable[[A], Awaitable[B]]) -> 'AsyncMaybe[B]':
        """Transform with an async function."""
        pass
    
    @abstractmethod
    async def flat_map(self, f: Callable[[A], 'AsyncMaybe[B]']) -> 'AsyncMaybe[B]':
        """Chain AsyncMaybe operations."""
        pass
    
    @abstractmethod
    async def flat_map_async(self, f: Callable[[A], Awaitable['AsyncMaybe[B]']]) -> 'AsyncMaybe[B]':
        """Chain with async function."""
        pass
    
    @abstractmethod
    async def get_or_else(self, default: A) -> A:
        """Get value or return default."""
        pass


@dataclass
class AsyncSome(AsyncMaybe[A]):
    """AsyncMaybe that contains a value."""
    value: A
    
    async def is_some(self) -> bool:
        return True
    
    async def is_none(self) -> bool:
        return False
    
    async def map(self, f: Callable[[A], B]) -> AsyncMaybe[B]:
        return AsyncSome(f(self.value))
    
    async def map_async(self, f: Callable[[A], Awaitable[B]]) -> AsyncMaybe[B]:
        result = await f(self.value)
        return AsyncSome(result)
    
    async def flat_map(self, f: Callable[[A], AsyncMaybe[B]]) -> AsyncMaybe[B]:
        return f(self.value)
    
    async def flat_map_async(self, f: Callable[[A], Awaitable[AsyncMaybe[B]]]) -> AsyncMaybe[B]:
        return await f(self.value)
    
    async def get_or_else(self, default: A) -> A:
        return self.value
    
    def __repr__(self) -> str:
        return f"AsyncSome({self.value!r})"


class _AsyncNothing(AsyncMaybe[A]):
    """AsyncMaybe that contains no value."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def is_some(self) -> bool:
        return False
    
    async def is_none(self) -> bool:
        return True
    
    async def map(self, f: Callable[[A], B]) -> AsyncMaybe[B]:
        return async_nothing()
    
    async def map_async(self, f: Callable[[A], Awaitable[B]]) -> AsyncMaybe[B]:
        return async_nothing()
    
    async def flat_map(self, f: Callable[[A], AsyncMaybe[B]]) -> AsyncMaybe[B]:
        return async_nothing()
    
    async def flat_map_async(self, f: Callable[[A], Awaitable[AsyncMaybe[B]]]) -> AsyncMaybe[B]:
        return async_nothing()
    
    async def get_or_else(self, default: A) -> A:
        return default
    
    def __repr__(self) -> str:
        return "AsyncNothing"


def async_nothing() -> AsyncMaybe[A]:
    """Returns the singleton AsyncNothing instance."""
    return _AsyncNothing()



# ASYNC RESULT - Asynchronous Error Handling

class AsyncResult(Generic[A, E], ABC):
    """
    AsyncResult represents an async computation that can succeed or fail.
    Like Result, but for async operations.
    """
    
    @abstractmethod
    async def is_ok(self) -> bool:
        """Returns True if the result is Ok."""
        pass
    
    @abstractmethod
    async def is_err(self) -> bool:
        """Returns True if the result is Err."""
        pass
    
    @abstractmethod
    async def map(self, f: Callable[[A], B]) -> 'AsyncResult[B, E]':
        """Transform the Ok value."""
        pass
    
    @abstractmethod
    async def map_async(self, f: Callable[[A], Awaitable[B]]) -> 'AsyncResult[B, E]':
        """Transform with async function."""
        pass
    
    @abstractmethod
    async def flat_map(self, f: Callable[[A], 'AsyncResult[B, E]']) -> 'AsyncResult[B, E]':
        """Chain AsyncResult operations."""
        pass
    
    @abstractmethod
    async def flat_map_async(self, f: Callable[[A], Awaitable['AsyncResult[B, E]']]) -> 'AsyncResult[B, E]':
        """Chain with async function."""
        pass
    
    @abstractmethod
    async def get_or_else(self, default: A) -> A:
        """Get value or return default."""
        pass


@dataclass
class AsyncOk(AsyncResult[A, E]):
    """AsyncResult representing success."""
    value: A
    
    async def is_ok(self) -> bool:
        return True
    
    async def is_err(self) -> bool:
        return False
    
    async def map(self, f: Callable[[A], B]) -> AsyncResult[B, E]:
        return AsyncOk(f(self.value))
    
    async def map_async(self, f: Callable[[A], Awaitable[B]]) -> AsyncResult[B, E]:
        result = await f(self.value)
        return AsyncOk(result)
    
    async def flat_map(self, f: Callable[[A], AsyncResult[B, E]]) -> AsyncResult[B, E]:
        return f(self.value)
    
    async def flat_map_async(self, f: Callable[[A], Awaitable[AsyncResult[B, E]]]) -> AsyncResult[B, E]:
        return await f(self.value)
    
    async def get_or_else(self, default: A) -> A:
        return self.value
    
    def __repr__(self) -> str:
        return f"AsyncOk({self.value!r})"


@dataclass
class AsyncErr(AsyncResult[A, E]):
    """AsyncResult representing failure."""
    error: E
    
    async def is_ok(self) -> bool:
        return False
    
    async def is_err(self) -> bool:
        return True
    
    async def map(self, f: Callable[[A], B]) -> AsyncResult[B, E]:
        return AsyncErr(self.error)
    
    async def map_async(self, f: Callable[[A], Awaitable[B]]) -> AsyncResult[B, E]:
        return AsyncErr(self.error)
    
    async def flat_map(self, f: Callable[[A], AsyncResult[B, E]]) -> AsyncResult[B, E]:
        return AsyncErr(self.error)
    
    async def flat_map_async(self, f: Callable[[A], Awaitable[AsyncResult[B, E]]]) -> AsyncResult[B, E]:
        return AsyncErr(self.error)
    
    async def get_or_else(self, default: A) -> A:
        return default
    
    def __repr__(self) -> str:
        return f"AsyncErr({self.error!r})"



# ASYNC IO - Asynchronous Side Effects

class AsyncIO(Generic[A], ABC):
    """
    AsyncIO represents a lazy async computation with side effects.
    Like IO, but for async operations.
    """
    
    @abstractmethod
    async def run(self) -> A:
        """Execute the async IO action."""
        pass
    
    @abstractmethod
    def map(self, f: Callable[[A], B]) -> 'AsyncIO[B]':
        """Transform the result."""
        pass
    
    @abstractmethod
    def map_async(self, f: Callable[[A], Awaitable[B]]) -> 'AsyncIO[B]':
        """Transform with async function."""
        pass
    
    @abstractmethod
    def flat_map(self, f: Callable[[A], 'AsyncIO[B]']) -> 'AsyncIO[B]':
        """Chain AsyncIO operations."""
        pass
    
    @abstractmethod
    def flat_map_async(self, f: Callable[[A], Awaitable['AsyncIO[B]']]) -> 'AsyncIO[B]':
        """Chain with async function."""
        pass


@dataclass
class _AsyncIOImpl(AsyncIO[A]):
    """Internal implementation of AsyncIO."""
    effect: Callable[[], Awaitable[A]]
    
    async def run(self) -> A:
        return await self.effect()
    
    def map(self, f: Callable[[A], B]) -> AsyncIO[B]:
        async def new_effect():
            result = await self.effect()
            return f(result)
        return _AsyncIOImpl(new_effect)
    
    def map_async(self, f: Callable[[A], Awaitable[B]]) -> AsyncIO[B]:
        async def new_effect():
            result = await self.effect()
            return await f(result)
        return _AsyncIOImpl(new_effect)
    
    def flat_map(self, f: Callable[[A], AsyncIO[B]]) -> AsyncIO[B]:
        async def new_effect():
            result = await self.effect()
            return await f(result).run()
        return _AsyncIOImpl(new_effect)
    
    def flat_map_async(self, f: Callable[[A], Awaitable[AsyncIO[B]]]) -> AsyncIO[B]:
        async def new_effect():
            result = await self.effect()
            io = await f(result)
            return await io.run()
        return _AsyncIOImpl(new_effect)
    
    def __repr__(self) -> str:
        return f"AsyncIO(<lazy async computation>)"


def async_io_pure(value: A) -> AsyncIO[A]:
    """Wrap a pure value in AsyncIO."""
    async def effect():
        return value
    return _AsyncIOImpl(effect)


def async_io_lazy(effect: Callable[[], Awaitable[A]]) -> AsyncIO[A]:
    """Create an AsyncIO from an async function."""
    return _AsyncIOImpl(effect)


# Common async IO operations
def async_io_sleep(seconds: float) -> AsyncIO[None]:
    """AsyncIO action that sleeps."""
    return async_io_lazy(lambda: asyncio.sleep(seconds))


def async_io_read_file(path: str) -> AsyncIO[str]:
    """AsyncIO action that reads a file asynchronously."""
    async def read():
        import aiofiles
        async with aiofiles.open(path, 'r') as f:
            return await f.read()
    return async_io_lazy(read)



# UTILITY FUNCTIONS

def lift_io(f: Callable[[A], B]) -> Callable[[IO[A]], IO[B]]:
    """Lift a pure function into the IO context."""
    return lambda io: io.map(f)


def lift_state(f: Callable[[A], B]) -> Callable[[State[S, A]], State[S, B]]:
    """Lift a pure function into the State context."""
    return lambda state: state.map(f)


def lift_reader(f: Callable[[A], B]) -> Callable[[Reader[R, A]], Reader[R, B]]:
    """Lift a pure function into the Reader context."""
    return lambda reader: reader.map(f)


async def safe_async_operation(f: Callable[[], Awaitable[A]]) -> AsyncResult[A, Exception]:
    """Wrap an async operation in AsyncResult, catching exceptions."""
    try:
        result = await f()
        return AsyncOk(result)
    except Exception as e:
        return AsyncErr(e)
