from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_properties(lst):
    sorted_lst = sort(lst)
    
    # Property 1: Ordering invariant
    # Every element should be <= its successor
    for i in range(len(sorted_lst) - 1):
        assert sorted_lst[i] <= sorted_lst[i + 1], \
            f"Ordering violated at index {i}"
    
    # Property 2: Permutation property
    # Result should contain exactly the same elements
    assert sorted(sorted_lst) == sorted(lst), \
        "Result is not a permutation of input"
    
    # Property 3: Length preservation
    # Output should have same length as input
    assert len(sorted_lst) == len(lst), \
        "Length not preserved"
    
    # Property 4: Idempotence
    # Sorting an already sorted list should not change it
    assert sort(sorted_lst) == sorted_lst, \
        "Sort function is not idempotent"

def sort(lst):
    """Simple sorting function for demonstration"""
    return sorted(lst)
