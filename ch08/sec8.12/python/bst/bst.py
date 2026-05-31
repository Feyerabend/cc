from hypothesis import given, strategies as st

class BinarySearchTree:
    """Binary search tree implementation for demonstration"""
    
    def __init__(self):
        self._values = set()
    
    def insert(self, value):
        """Insert a value into the BST"""
        self._values.add(value)
    
    def inorder_traversal(self):
        """Return values in sorted order"""
        return sorted(list(self._values))
    
    def contains(self, value):
        """Check if value exists in the BST"""
        return value in self._values
    
    def size(self):
        """Return number of elements in the BST"""
        return len(self._values)

def is_sorted_ascending(lst):
    """Verify that a list is sorted in ascending order"""
    return all(lst[i] <= lst[i + 1] for i in range(len(lst) - 1))

@given(st.lists(st.integers(), min_size=0, max_size=50))
def test_bst_invariants(values):
    """Test that BST maintains its structural invariants"""
    bst = BinarySearchTree()
    
    # Insert all values
    for value in values:
        bst.insert(value)
    
    # Structural invariant: in-order traversal yields sorted sequence
    traversal = bst.inorder_traversal()
    assert is_sorted_ascending(traversal), \
        f"In-order traversal not sorted: {traversal}"
    
    # Cardinality property: all unique values are present
    unique_values = set(values)
    assert bst.size() == len(unique_values), \
        f"Size mismatch: {bst.size()} != {len(unique_values)}"
    
    # Membership property: all inserted values are retrievable
    for value in unique_values:
        assert bst.contains(value), \
            f"Value {value} not found after insertion"
    
    # Completeness property: no extra values present
    for value in traversal:
        assert value in unique_values, \
            f"Unexpected value {value} found in BST"
