from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional

T = TypeVar('T')

class StackADT(ABC, Generic[T]):
    """
    Abstract Base Class defining the Stack ADT contract.
    Any class that inherits this MUST implement all abstract methods.
    """

    @abstractmethod
    def push(self, value: T) -> None:
        """Add an element to the top of the stack."""
        ...

    @abstractmethod
    def pop(self) -> T:
        """Remove and return the top element. Raises IndexError if empty."""
        ...

    @abstractmethod
    def peek(self) -> T:
        """Return (but don't remove) the top element. Raises IndexError if empty."""
        ...

    @abstractmethod
    def is_empty(self) -> bool:
        """Return True if the stack has no elements."""
        ...

    @abstractmethod
    def size(self) -> int:
        """Return the number of elements in the stack."""
        ...
