from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Node(ABC, Generic[T]):
    @abstractmethod
    def accept(self, visitor: "NodeVisitor[T]"):
        pass


class EmptyNode(Node[T]):
    def accept(self, visitor: "NodeVisitor[T]"):
        return visitor.for_empty_node(self)


class NextNode(Node[T]):
    def __init__(self, value: T, next_node: Node[T]):
        self.value = value
        self.next = next_node

    def accept(self, visitor: "NodeVisitor[T]"):
        return visitor.for_next_node(self)


class NodeVisitor(ABC, Generic[T]):
    @abstractmethod
    def for_empty_node(self, node: EmptyNode[T]):
        pass

    @abstractmethod
    def for_next_node(self, node: NextNode[T]):
        pass


class Remove(NodeVisitor[T]):
    def __init__(self, target: T):
        self.target = target

    def for_empty_node(self, node: EmptyNode[T]):
        return EmptyNode()

    def for_next_node(self, node: NextNode[T]):
        if self.target == node.value:
            return node.next.accept(self)
        return NextNode(node.value, node.next.accept(self))


class Insert(NodeVisitor[T]):
    def __init__(self, value: T):
        self.value = value

    def for_empty_node(self, node: EmptyNode[T]):
        return NextNode(self.value, EmptyNode())

    def for_next_node(self, node: NextNode[T]):
        return NextNode(node.value, node.next.accept(self))


class Replace(NodeVisitor[T]):
    def __init__(self, old: T, new: T):
        self.old = old
        self.new = new

    def for_empty_node(self, node: EmptyNode[T]):
        return EmptyNode()

    def for_next_node(self, node: NextNode[T]):
        value = self.new if node.value == self.old else node.value
        return NextNode(value, node.next.accept(self))


class PrintElements(NodeVisitor[T]):
    def for_empty_node(self, node: EmptyNode[T]):
        print()
        return None

    def for_next_node(self, node: NextNode[T]):
        print(node.value)
        node.next.accept(self)
        return node.value


class TreeDuties(ABC, Generic[T]):
    @abstractmethod
    def add(self, value: T):
        pass

    @abstractmethod
    def insert(self, value: T):
        pass

    @abstractmethod
    def remove(self, value: T):
        pass

    @abstractmethod
    def replace(self, old: T, new: T):
        pass


class Gardener(TreeDuties[T]):
    def __init__(self):
        self.root: Node[T] = EmptyNode()

    def add(self, value: T):
        self.root = NextNode(value, self.root)

    def insert(self, value: T):
        self.root = self.root.accept(Insert(value))

    def remove(self, value: T):
        self.root = self.root.accept(Remove(value))

    def replace(self, old: T, new: T):
        self.root = self.root.accept(Replace(old, new))

    def print_all_elements(self):
        return self.root.accept(PrintElements())


def main():
    g = Gardener[str]()
    g.add("1")
    g.add("2")
    g.add("3")
    g.add("4")
    g.add("5")
    g.add("6")
    g.insert("7")
    g.insert("8")
    g.add("9")
    g.print_all_elements()
    g.replace("0", "1")
    g.print_all_elements()
    g.replace("0", "1")


if __name__ == "__main__":
    main()
