
## Design Patterns in Linked List

The visitor pattern is being used to separate operations from the data structure.
This allows new operations to be added without modifying the node classes, following
the open-closed principle (*open for extension, closed for modification*).

The pattern works through "double dispatch" - when you call `node.accept(visitor)`,
the node determines which visitor method to call based on its concrete type (either
`forEmptyNode` or `forNextNode`), and then the visitor determines what operation to
perform.

This approach is particularly interesting because operations like 'insertion' (adding)
and 'removal', which typically require special handling for edge cases, are cleanly
encapsulated in visitor classes. Each visitor recursively traverses the list, building
a new list with the desired modifications.

The `Gardener` class provides a simplified interface to these operations, hiding the
complexity of the visitor pattern from client code.

There is also a sample file named 'main2.c' that follows a more conventional implementation
approach, which is likely to be more efficient in practice. As always, there is a
trade-off between speed and code reusability, which can be reflected in different
programming styles. If you write your own libraries, use whatever approach that is
most applicable to the situation.


#### Node Hierarchy

- `Abstract Node` class that defines an interface
- `EmptyNode` represents the end of the list (null terminator)
- `NextNode` contains data and a reference to the next node


#### Visitor Pattern

- The `NodeVisitor` interface allows operations to be performed on nodes
- Each node type has an accept method that delegates to the appropriate visitor method
- Visitors provide different implementations for each node type


#### Operations as Visitors

- `Remove`: Removes specified elements from the list
- `Insert`: Adds elements to the end of the list
- `Replace`: Substitutes specified elements with others
- `PrintElements`: Displays all elements in the list


#### Gardener Class

- Manages the linked list and provides a high-level interface
- Implements TreeDuties interface for standard operations
- Maintains a reference to the head node
- Delegates operations to appropriate visitors
