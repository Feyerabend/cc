from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class Node(ABC, Generic[T]):
    @abstractmethod
    def accept(self, visitor: "NodeVisitor[T, R]") -> R:
        pass


class EmptyNode(Node[T]):
    def accept(self, visitor: "NodeVisitor[T, R]") -> R:
        return visitor.for_empty_node(self)


class NextNode(Node[T]):
    def __init__(self, value: T, next_node: Node[T]):
        self.value = value
        self.next = next_node

    def accept(self, visitor: "NodeVisitor[T, R]") -> R:
        return visitor.for_next_node(self)


class NodeVisitor(ABC, Generic[T, R]):
    @abstractmethod
    def for_empty_node(self, node: EmptyNode[T]) -> R:
        pass

    @abstractmethod
    def for_next_node(self, node: NextNode[T]) -> R:
        pass


class Remove(NodeVisitor[T, Node[T]]):
    def __init__(self, target: T):
        self.target = target

    def for_empty_node(self, node: EmptyNode[T]) -> Node[T]:
        return EmptyNode()

    def for_next_node(self, node: NextNode[T]) -> Node[T]:
        if self.target == node.value:
            return node.next.accept(self)
        return NextNode(node.value, node.next.accept(self))


class Insert(NodeVisitor[T, Node[T]]):
    def __init__(self, value: T):
        self.value = value

    def for_empty_node(self, node: EmptyNode[T]) -> Node[T]:
        return NextNode(self.value, EmptyNode())

    def for_next_node(self, node: NextNode[T]) -> Node[T]:
        return NextNode(node.value, node.next.accept(self))


class Replace(NodeVisitor[T, Node[T]]):
    def __init__(self, old: T, new: T):
        self.old = old
        self.new = new

    def for_empty_node(self, node: EmptyNode[T]) -> Node[T]:
        return EmptyNode()

    def for_next_node(self, node: NextNode[T]) -> Node[T]:
        value = self.new if node.value == self.old else node.value
        return NextNode(value, node.next.accept(self))


class PrintElements(NodeVisitor[T, None]):
    def for_empty_node(self, node: EmptyNode[T]) -> None:
        print()
        return None

    def for_next_node(self, node: NextNode[T]) -> None:
        print(node.value)
        node.next.accept(self)
        return None


class TreeDuties(ABC, Generic[T]):
    @abstractmethod
    def add(self, value: T) -> None:
        pass

    @abstractmethod
    def insert(self, value: T) -> None:
        pass

    @abstractmethod
    def remove(self, value: T) -> None:
        pass

    @abstractmethod
    def replace(self, old: T, new: T) -> None:
        pass


class Gardener(TreeDuties[T]):
    def __init__(self):
        self.root: Node[T] = EmptyNode()

    def add(self, value: T) -> None:
        self.root = NextNode(value, self.root)

    def insert(self, value: T) -> None:
        self.root = self.root.accept(Insert(value))

    def remove(self, value: T) -> None:
        self.root = self.root.accept(Remove(value))

    def replace(self, old: T, new: T) -> None:
        self.root = self.root.accept(Replace(old, new))

    def print_all_elements(self) -> None:
        self.root.accept(PrintElements())


def main():
    g = Gardener[int]()
    g.add(1)
    g.add(2)
    g.add(3)
    g.insert(10)
    g.print_all_elements()


if __name__ == "__main__":
    main()
