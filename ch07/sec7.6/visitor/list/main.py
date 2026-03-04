
from abc import ABC, abstractmethod

class Node(ABC):
    @abstractmethod
    def accept(self, visitor):
        pass

class EmptyNode(Node):
    def accept(self, visitor):
        return visitor.for_empty_node(self)

class NextNode(Node):
    def __init__(self, t, n):
        self.t = t
        self.n = n
    
    def accept(self, visitor):
        return visitor.for_next_node(self)

class NodeVisitor(ABC):
    @abstractmethod
    def for_empty_node(self, node):
        pass
    
    @abstractmethod
    def for_next_node(self, node):
        pass

class Remove(NodeVisitor):
    def __init__(self, o):
        self.o = o
    
    def for_empty_node(self, node):
        return EmptyNode()
    
    def for_next_node(self, node):
        if self.o == node.t:
            return node.n.accept(self)
        else:
            return NextNode(node.t, node.n.accept(self))

class Insert(NodeVisitor):
    def __init__(self, o):
        self.o = o
    
    def for_empty_node(self, node):
        return NextNode(self.o, EmptyNode())
    
    def for_next_node(self, node):
        return NextNode(node.t, node.n.accept(self))

class Replace(NodeVisitor):
    def __init__(self, r, o):
        self.r = r
        self.o = o
    
    def for_empty_node(self, node):
        return EmptyNode()
    
    def for_next_node(self, node):
        if self.o == node.t:
            return NextNode(self.r, node.n.accept(self))
        else:
            return NextNode(node.t, node.n.accept(self))

class PrintElements(NodeVisitor):
    def for_empty_node(self, node):
        print()
        return None
    
    def for_next_node(self, node):
        print(node.t)
        node.n.accept(self)
        return node.t

class TreeDuties(ABC):
    @abstractmethod
    def add(self, o):
        pass
    
    @abstractmethod
    def insert(self, o):
        pass
    
    @abstractmethod
    def remove(self, o):
        pass
    
    @abstractmethod
    def replace(self, o, p):
        pass

class Gardener(TreeDuties):
    def __init__(self):
        self.t = EmptyNode()
    
    def add(self, o):
        self.t = NextNode(o, self.t)
    
    def insert(self, o):
        self.t = self.t.accept(Insert(o))
    
    def remove(self, o):
        self.t = self.t.accept(Remove(o))
    
    def replace(self, o, p):
        self.t = self.t.accept(Replace(o, p))
    
    def print_all_elements(self):
        return self.t.accept(PrintElements())

def main():
    g = Gardener()
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
