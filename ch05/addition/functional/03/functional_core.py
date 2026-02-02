"""
Functional Programming Core - A substrate for functional programming in Python

This module provides fundamental functional programming primitives:
- Maybe/Option types (Some, None)
- Result types (Ok, Err)
- Immutable data structures
- Function composition utilities
- Common FP operations (map, flatMap, fold, etc.)
"""

from typing import TypeVar, Generic, Callable, Optional, Union, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import reduce


# Type variables for generic programming
A = TypeVar('A')
B = TypeVar('B')
E = TypeVar('E')


# ============================================================================
# MAYBE / OPTION TYPE
# ============================================================================

class Maybe(Generic[A], ABC):
    """
    Represents an optional value: every Maybe is either Some and contains a value,
    or None, and does not.
    """
    
    @abstractmethod
    def is_some(self) -> bool:
        """Returns True if the Maybe is a Some value."""
        pass
    
    @abstractmethod
    def is_none(self) -> bool:
        """Returns True if the Maybe is None."""
        pass
    
    @abstractmethod
    def map(self, f: Callable[[A], B]) -> 'Maybe[B]':
        """Applies a function to the contained value (if any)."""
        pass
    
    @abstractmethod
    def flat_map(self, f: Callable[[A], 'Maybe[B]']) -> 'Maybe[B]':
        """Applies a function that returns a Maybe to the contained value."""
        pass
    
    @abstractmethod
    def filter(self, predicate: Callable[[A], bool]) -> 'Maybe[A]':
        """Returns None if the value doesn't satisfy the predicate."""
        pass
    
    @abstractmethod
    def get_or_else(self, default: A) -> A:
        """Returns the value if present, otherwise returns default."""
        pass
    
    @abstractmethod
    def or_else(self, alternative: 'Maybe[A]') -> 'Maybe[A]':
        """Returns this Maybe if it contains a value, otherwise returns alternative."""
        pass
    
    def __bool__(self) -> bool:
        """Allows using Maybe in boolean contexts."""
        return self.is_some()


@dataclass(frozen=True)
class Some(Maybe[A]):
    """Represents a Maybe that contains a value."""
    value: A
    
    def is_some(self) -> bool:
        return True
    
    def is_none(self) -> bool:
        return False
    
    def map(self, f: Callable[[A], B]) -> Maybe[B]:
        return Some(f(self.value))
    
    def flat_map(self, f: Callable[[A], Maybe[B]]) -> Maybe[B]:
        return f(self.value)
    
    def filter(self, predicate: Callable[[A], bool]) -> Maybe[A]:
        return self if predicate(self.value) else nothing()
    
    def get_or_else(self, default: A) -> A:
        return self.value
    
    def or_else(self, alternative: Maybe[A]) -> Maybe[A]:
        return self
    
    def __repr__(self) -> str:
        return f"Some({self.value!r})"


class _Nothing(Maybe[A]):
    """Represents a Maybe that contains no value."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def is_some(self) -> bool:
        return False
    
    def is_none(self) -> bool:
        return True
    
    def map(self, f: Callable[[A], B]) -> Maybe[B]:
        return nothing()
    
    def flat_map(self, f: Callable[[A], Maybe[B]]) -> Maybe[B]:
        return nothing()
    
    def filter(self, predicate: Callable[[A], bool]) -> Maybe[A]:
        return self
    
    def get_or_else(self, default: A) -> A:
        return default
    
    def or_else(self, alternative: Maybe[A]) -> Maybe[A]:
        return alternative
    
    def __repr__(self) -> str:
        return "Nothing"


def nothing() -> Maybe[A]:
    """Returns the singleton Nothing instance."""
    return _Nothing()


def maybe(value: Optional[A]) -> Maybe[A]:
    """Converts a Python Optional value to a Maybe."""
    return Some(value) if value is not None else nothing()


# ============================================================================
# RESULT / EITHER TYPE
# ============================================================================

class Result(Generic[A, E], ABC):
    """
    Represents a computation that can either succeed with a value (Ok)
    or fail with an error (Err).
    """
    
    @abstractmethod
    def is_ok(self) -> bool:
        """Returns True if the result is Ok."""
        pass
    
    @abstractmethod
    def is_err(self) -> bool:
        """Returns True if the result is Err."""
        pass
    
    @abstractmethod
    def map(self, f: Callable[[A], B]) -> 'Result[B, E]':
        """Applies a function to the Ok value (if any)."""
        pass
    
    @abstractmethod
    def map_err(self, f: Callable[[E], B]) -> 'Result[A, B]':
        """Applies a function to the Err value (if any)."""
        pass
    
    @abstractmethod
    def flat_map(self, f: Callable[[A], 'Result[B, E]']) -> 'Result[B, E]':
        """Applies a function that returns a Result to the Ok value."""
        pass
    
    @abstractmethod
    def get_or_else(self, default: A) -> A:
        """Returns the Ok value if present, otherwise returns default."""
        pass
    
    @abstractmethod
    def or_else(self, alternative: 'Result[A, E]') -> 'Result[A, E]':
        """Returns this Result if Ok, otherwise returns alternative."""
        pass


@dataclass(frozen=True)
class Ok(Result[A, E]):
    """Represents a successful computation."""
    value: A
    
    def is_ok(self) -> bool:
        return True
    
    def is_err(self) -> bool:
        return False
    
    def map(self, f: Callable[[A], B]) -> Result[B, E]:
        return Ok(f(self.value))
    
    def map_err(self, f: Callable[[E], B]) -> Result[A, B]:
        return Ok(self.value)
    
    def flat_map(self, f: Callable[[A], Result[B, E]]) -> Result[B, E]:
        return f(self.value)
    
    def get_or_else(self, default: A) -> A:
        return self.value
    
    def or_else(self, alternative: Result[A, E]) -> Result[A, E]:
        return self
    
    def __repr__(self) -> str:
        return f"Ok({self.value!r})"


@dataclass(frozen=True)
class Err(Result[A, E]):
    """Represents a failed computation."""
    error: E
    
    def is_ok(self) -> bool:
        return False
    
    def is_err(self) -> bool:
        return True
    
    def map(self, f: Callable[[A], B]) -> Result[B, E]:
        return Err(self.error)
    
    def map_err(self, f: Callable[[E], B]) -> Result[A, B]:
        return Err(f(self.error))
    
    def flat_map(self, f: Callable[[A], Result[B, E]]) -> Result[B, E]:
        return Err(self.error)
    
    def get_or_else(self, default: A) -> A:
        return default
    
    def or_else(self, alternative: Result[A, E]) -> Result[A, E]:
        return alternative
    
    def __repr__(self) -> str:
        return f"Err({self.error!r})"


# ============================================================================
# FUNCTION COMPOSITION
# ============================================================================

def compose(*functions: Callable) -> Callable:
    """
    Composes functions from right to left.
    compose(f, g, h)(x) == f(g(h(x)))
    """
    def _compose(f: Callable, g: Callable) -> Callable:
        return lambda x: f(g(x))
    
    return reduce(_compose, functions, lambda x: x)


def pipe(*functions: Callable) -> Callable:
    """
    Pipes functions from left to right.
    pipe(f, g, h)(x) == h(g(f(x)))
    """
    return compose(*reversed(functions))


def curry(f: Callable) -> Callable:
    """
    Transforms a function f(a, b, c) into a curried form f(a)(b)(c).
    """
    from inspect import signature
    sig = signature(f)
    arity = len(sig.parameters)
    
    def curried(*args):
        if len(args) >= arity:
            return f(*args[:arity])
        return lambda *more_args: curried(*(args + more_args))
    
    return curried


# ============================================================================
# COMMON FP OPERATIONS
# ============================================================================

def identity(x: A) -> A:
    """The identity function: returns its argument unchanged."""
    return x


def const(x: A) -> Callable[[Any], A]:
    """Returns a function that always returns x."""
    return lambda _: x


def flip(f: Callable[[A, B], Any]) -> Callable[[B, A], Any]:
    """Flips the order of a function's first two arguments."""
    return lambda b, a: f(a, b)


def fmap(f: Callable[[A], B], container: Maybe[A]) -> Maybe[B]:
    """Generic map function for functors."""
    return container.map(f)


# ============================================================================
# LIST OPERATIONS
# ============================================================================

def foldl(f: Callable[[B, A], B], initial: B, items: list[A]) -> B:
    """Left fold over a list."""
    return reduce(f, items, initial)


def foldr(f: Callable[[A, B], B], initial: B, items: list[A]) -> B:
    """Right fold over a list."""
    return reduce(lambda b, a: f(a, b), reversed(items), initial)


def traverse_maybe(f: Callable[[A], Maybe[B]], items: list[A]) -> Maybe[list[B]]:
    """
    Applies a function returning Maybe to each element and collects results.
    Returns Some(list) if all succeed, Nothing if any fail.
    """
    result = []
    for item in items:
        maybe_b = f(item)
        if maybe_b.is_none():
            return nothing()
        result.append(maybe_b.get_or_else(None))
    return Some(result)


def sequence_maybe(maybes: list[Maybe[A]]) -> Maybe[list[A]]:
    """
    Converts a list of Maybes into a Maybe of list.
    Returns Some(list) if all are Some, Nothing if any are Nothing.
    """
    return traverse_maybe(identity, maybes)


# ============================================================================
# HELPER FUNCTIONS FOR SAFE OPERATIONS
# ============================================================================

def safe_divide(a: float, b: float) -> Result[float, str]:
    """Division that returns Result instead of raising exception."""
    if b == 0:
        return Err("Division by zero")
    return Ok(a / b)


def safe_get(dictionary: dict, key: Any) -> Maybe[Any]:
    """Dictionary lookup that returns Maybe."""
    value = dictionary.get(key)
    return maybe(value)


def safe_parse_int(s: str) -> Result[int, str]:
    """Parse integer that returns Result instead of raising exception."""
    try:
        return Ok(int(s))
    except ValueError as e:
        return Err(f"Failed to parse '{s}': {e}")


def safe_head(items: list[A]) -> Maybe[A]:
    """Returns the first element of a list, or Nothing if empty."""
    return Some(items[0]) if items else nothing()


def safe_tail(items: list[A]) -> Maybe[list[A]]:
    """Returns all but the first element, or Nothing if empty."""
    return Some(items[1:]) if items else nothing()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def try_maybe(f: Callable[[], A]) -> Maybe[A]:
    """Wraps a function call in Maybe, catching exceptions."""
    try:
        return Some(f())
    except Exception:
        return nothing()


def try_result(f: Callable[[], A]) -> Result[A, Exception]:
    """Wraps a function call in Result, catching exceptions."""
    try:
        return Ok(f())
    except Exception as e:
        return Err(e)
