# persistent.py
# Functional Patterns -- 10. Persistent Data Structures
#
# Structural sharing: new versions share unchanged parts with old ones.
# No mutation; all versions coexist.
#
# Run:  python persistent.py

import sys



# 1. Persistent linked list
#    Prepend = one new node + shared tail. O(1), zero copying.

class Node:
    """A singly-linked list node. Immutable after construction."""
    __slots__ = ('value', 'next')

    def __init__(self, value, next_node=None):
        self.value = value
        self.next  = next_node

    def __repr__(self):
        items = []
        n = self
        while n is not None:
            items.append(repr(n.value))
            n = n.next
        return '[' + ' -> '.join(items) + ']'


EMPTY = None

def cons(value, lst):    return Node(value, lst)
def head(lst):           return lst.value
def tail(lst):           return lst.next
def is_empty(lst):       return lst is None

def to_list(lst):
    result = []
    while lst is not None:
        result.append(lst.value)
        lst = lst.next
    return result


print("-- 1. Persistent linked list --")

# Build list_a = [1, 2, 3]
list_a = cons(1, cons(2, cons(3, EMPTY)))

# Prepend to create new versions -- both share list_a's nodes
list_b = cons(0, list_a)    # [0, 1, 2, 3]
list_c = cons(9, list_a)    # [9, 1, 2, 3]

print(f"  list_a = {to_list(list_a)}")
print(f"  list_b = {to_list(list_b)}  (prepended 0 to list_a)")
print(f"  list_c = {to_list(list_c)}  (prepended 9 to list_a)")

# Sharing: the tail of list_b and list_c IS list_a -- same object
print(f"  tail(list_b) is list_a: {tail(list_b) is list_a}")   # True
print(f"  tail(list_c) is list_a: {tail(list_c) is list_a}")   # True
print(f"  (three heads, one shared tail -- no copying)")



# 2. Persistent stack -- history for free

def push(stack, value): return cons(value, stack)
def pop(stack):         return tail(stack)
def peek(stack):        return head(stack)

print("\n-- 2. Persistent stack (undo for free) --")

s0 = EMPTY
s1 = push(s0, 'a')
s2 = push(s1, 'b')
s3 = push(s2, 'c')

print(f"  s0: {to_list(s0)}")
print(f"  s1: {to_list(s1)}")
print(f"  s2: {to_list(s2)}  shares s1")
print(f"  s3: {to_list(s3)}  shares s2 (which shares s1)")
print(f"  'Undo' s3 -> s2: {to_list(pop(s3))}")
print(f"  All versions still accessible: s1={to_list(s1)}, s2={to_list(s2)}")



# 3. Path-copying binary search tree
#    Insert copies O(depth) nodes; all others are shared.

class BSTNode:
    __slots__ = ('key', 'value', 'left', 'right')

    def __init__(self, key, value, left=None, right=None):
        self.key   = key
        self.value = value
        self.left  = left
        self.right = right


def bst_insert(node, key, value):
    """Return a new tree with (key, value) inserted. Shares unchanged nodes."""
    if node is None:
        return BSTNode(key, value)
    if key == node.key:
        # Only this node changes; both children are shared
        return BSTNode(key, value, node.left, node.right)
    if key < node.key:
        # This node + left path are copied; right child is shared
        return BSTNode(node.key, node.value,
                       bst_insert(node.left, key, value),
                       node.right)
    else:
        # This node + right path are copied; left child is shared
        return BSTNode(node.key, node.value,
                       node.left,
                       bst_insert(node.right, key, value))


def bst_get(node, key):
    if node is None:          return None
    if key == node.key:       return node.value
    if key < node.key:        return bst_get(node.left, key)
    return bst_get(node.right, key)


def bst_inorder(node):
    if node is None: return []
    return bst_inorder(node.left) + [(node.key, node.value)] + bst_inorder(node.right)


def count_nodes(node):
    if node is None: return 0
    return 1 + count_nodes(node.left) + count_nodes(node.right)


print("\n-- 3. Path-copying BST --")

t0 = None
for k, v in [(5,'e'), (3,'c'), (7,'g'), (1,'a'), (4,'d')]:
    t0 = bst_insert(t0, k, v)

print(f"  t0 inorder: {bst_inorder(t0)}")
print(f"  t0 nodes: {count_nodes(t0)}")

# Insert a new key -> new version t1
t1 = bst_insert(t0, 6, 'f')

print(f"  t1 inorder: {bst_inorder(t1)}")
print(f"  t1 nodes: {count_nodes(t1)}")

# Verify structural sharing: unchanged subtrees are the same objects
# (node with key=1 is on neither the left nor right path from root for key=6)
print(f"  t0 and t1 share node key=1: {bst_get(t0, 1) == bst_get(t1, 1)}")
print(f"  t0.left is t1.left: {t0.left is t1.left}")
# t0.left (key=3) is NOT shared because 6 > 5, so we went right from root.
# t0.right is NOT shared; new node 6 was inserted under 7.
# But t0.right.left (key=None, not present) -- let's check t0.left
print(f"  (left subtree rooted at key=3 is shared: {t0.left is t1.left})")

# Update an existing key -> old value accessible in t0
t2 = bst_insert(t1, 3, 'C_UPDATED')
print(f"  t0 key=3: {bst_get(t0, 3)!r}  (original)")
print(f"  t2 key=3: {bst_get(t2, 3)!r}  (updated in t2 only)")



# 4. Memory comparison: naive copy vs. persistent

print("\n-- 4. Memory: naive copy vs. persistent --")

N = 500

# Naive: each "version" is a full copy of the list up to that point
naive_versions = []
base = list(range(N))
for i in range(20):
    naive_versions.append(base[:])   # full copy each time

naive_mem = sum(sys.getsizeof(v) for v in naive_versions)
print(f"  Naive: 20 full copies of list({N}): ~{naive_mem:,} bytes")

# Persistent: prepend to a shared base, 20 new heads
shared_base = EMPTY
for v in range(N - 1, -1, -1):
    shared_base = cons(v, shared_base)

persistent_versions = [cons(i * 100, shared_base) for i in range(20)]
# Each version = one Node; shared_base = N nodes (counted once)
node_size   = sys.getsizeof(persistent_versions[0])
shared_size = node_size * N
heads_size  = node_size * 20
total_pers  = shared_size + heads_size
print(f"  Persistent: {N} shared + 20 heads: ~{total_pers:,} bytes")
print(f"  Ratio: {naive_mem // total_pers}x less memory for the persistent version")



# 5. Immutable dict update (functional style, shared structure)

print("\n-- 5. Functional dict update (structural sharing in dicts) --")

def with_key(d, key, value):
    """Return a new dict with key updated. Old dict is untouched."""
    return {**d, key: value}

def without_key(d, key):
    """Return a new dict without key. Old dict is untouched."""
    return {k: v for k, v in d.items() if k != key}

config_v1 = {'host': 'localhost', 'port': 8080, 'debug': False}
config_v2 = with_key(config_v1, 'port', 9090)
config_v3 = with_key(config_v2, 'debug', True)
config_v4 = without_key(config_v3, 'host')

print(f"  v1: {config_v1}")
print(f"  v2: {config_v2}")
print(f"  v3: {config_v3}")
print(f"  v4: {config_v4}")
print(f"  v1 unchanged: {config_v1}")
print("  (Python dicts do not structurally share, but the pattern is correct)")
print("  (pyrsistent.pmap() provides O(log32 n) structural sharing)")



# 6. Persistent structure as a concurrency primitive

print("\n-- 6. Concurrent reads of shared persistent list --")

import threading

results = []
lock    = threading.Lock()

def reader(lst, thread_id):
    """Read the shared list. No lock needed -- it is never mutated."""
    total = sum(to_list(lst))
    with lock:
        results.append((thread_id, total))

# Build a shared list once
shared = EMPTY
for v in range(1, 101):
    shared = cons(v, shared)   # [100, 99, ..., 1]

# Many threads read it simultaneously -- no synchronisation needed
threads = [threading.Thread(target=reader, args=(shared, i)) for i in range(6)]
for t in threads: t.start()
for t in threads: t.join()

expected = sum(range(1, 101))   # 5050
all_ok   = all(r == expected for _, r in results)
print(f"  Expected sum: {expected}")
print(f"  All 6 threads got correct result: {all_ok}")
print(f"  No lock used during reads -- immutability makes it safe.")
