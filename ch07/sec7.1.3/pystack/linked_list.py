from typing import Optional
from abstack import StackADT, T
from dataclasses import dataclass

@dataclass
class _Node:
    value: object
    next: Optional['_Node'] = None

class LinkedStack(StackADT[T]):
    """Concrete implementation using a singly linked list."""

    def __init__(self) -> None:
        self._head: Optional[_Node] = None
        self._size: int = 0

    def push(self, value: T) -> None:
        self._head = _Node(value=value, next=self._head)
        self._size += 1

    def pop(self) -> T:
        if self.is_empty():
            raise IndexError("pop from empty stack")
        value = self._head.value
        self._head = self._head.next
        self._size -= 1
        return value

    def peek(self) -> T:
        if self.is_empty():
            raise IndexError("peek at empty stack")
        return self._head.value

    def is_empty(self) -> bool:
        return self._head is None

    def size(self) -> int:
        return self._size

    def __repr__(self) -> str:
        items, curr = [], self._head
        while curr:
            items.append(curr.value)
            curr = curr.next
        return f"LinkedStack({items})"
