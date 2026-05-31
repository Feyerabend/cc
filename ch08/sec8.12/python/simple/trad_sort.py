def sort(lst):
    """Simple sorting function for demonstration"""
    return sorted(lst)


def test_sort():
    # Test basic functionality
    assert sort([3, 1, 2]) == [1, 2, 3]

    # Test edge cases
    assert sort([]) == []
    assert sort([5]) == [5]

    # Test duplicates
    assert sort([1, 1, 1]) == [1, 1, 1]

    # Test negative numbers
    assert sort([-1, 0, 1]) == [-1, 0, 1]


if __name__ == "__main__":
    test_sort()
    print("All tests passed!")
