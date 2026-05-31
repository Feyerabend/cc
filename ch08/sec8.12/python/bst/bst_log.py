import json
from hypothesis import given, strategies as st, settings

LOG_FILE = "bst_test_log.jsonl"

class BinarySearchTree:
    def __init__(self):
        self._values = set()
    def insert(self, value):
        self._values.add(value)
    def inorder_traversal(self):
        return sorted(self._values)
    def contains(self, value):
        return value in self._values
    def size(self):
        return len(self._values)

def is_sorted_ascending(lst):
    return all(lst[i] <= lst[i + 1] for i in range(len(lst) - 1))

@given(st.lists(st.integers(), min_size=0, max_size=20))
@settings(max_examples=10)  # how many test cases Hypothesis will generate
def test_bst_invariants(values):
    bst = BinarySearchTree()
    log_entry = {
        "generated_values": values,
        "states": []
    }
    for v in values:
        bst.insert(v)
        log_entry["states"].append({
            "inserted": v,
            "current_traversal": bst.inorder_traversal()
        })

    traversal = bst.inorder_traversal()
    assert is_sorted_ascending(traversal)
    unique_values = set(values)
    assert bst.size() == len(unique_values)
    for v in unique_values:
        assert bst.contains(v)
    for v in traversal:
        assert v in unique_values

    # Write run data to file
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

if __name__ == "__main__":
    test_bst_invariants()  # run Hypothesis property test
    print(f"Log written to {LOG_FILE}")
