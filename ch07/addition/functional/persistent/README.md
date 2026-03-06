
## 10. Persistent Data Structures


A *persistent* data structure is one where every update produces a new version
while the old version remains intact and accessible. Neither version is
mutated. This is immutability in action--but implemented efficiently.

The key mechanism is *structural sharing*: when a new version is created,
it does not copy the parts that did not change. It points to them. The old
and new versions share the unchanged structure, so the cost of an update is
proportional to what changed, not to the size of the whole structure.

```
Version 1:  [A] -> [B] -> [C]

Prepend D:
Version 2:  [D] -> [A] -> [B] -> [C]
                    ^
                    shared tail
```

`Version 1` and `Version 2` coexist. Neither is destroyed. `[A] -> [B] -> [C]`
is shared between them, occupying memory only once.



### Why It Exists

Naive immutability--copy the entire structure on every update--costs O(n)
time and space per operation. That is unacceptable for large structures used
frequently.

Persistent data structures recover efficiency through sharing:

| Operation | Naive copy | Persistent |
|-----------|------------|------------|
| List prepend | O(n) | O(1) |
| List update at index i | O(n) | O(log n) with a tree |
| Tree insert | O(n) | O(log n) path-copy |
| Dict update | O(n) | O(log n) hash-array mapped trie |

The underlying trade-off is between *time* (persistent structures may have
higher constant factors than mutable ones) and *correctness under sharing*
(persistent structures are always safe to share). When safety is the
constraint, persistence is the tool.



### The Persistent Linked List

A singly-linked list is naturally persistent. Prepending an element creates
one new node; the new list shares the entire original list as its tail.

```
list_a = [1, 2, 3]           # three nodes
list_b = cons(0, list_a)     # one new node + shared tail
list_c = cons(9, list_a)     # one new node + same shared tail

list_a  ->  [1] -> [2] -> [3]
list_b  ->  [0]  \
list_c  ->  [9]   -> [1] -> [2] -> [3]   (shared)
```

`list_a`, `list_b`, and `list_c` coexist. Three heads; one tail. No copying.
The tail nodes are not owned by any single list--they are shared by all three.

This is why functional languages (Haskell, Erlang, Clojure) use linked lists
as their default list type: prepend and pattern-match are O(1), and sharing
is free.

### Path Copying in Trees

For random-access data, a tree structure allows O(log n) updates through
*path copying*: on update, copy only the nodes on the path from the root to
the changed node. All other nodes are shared.

```
Original tree:           After updating node B:

        root                    root'
       /    \                  /    \
      A      B               A      B'
     / \    / \             / \    / \
    C   D  E   F           C   D  E   F
                                 (shared)
```

`root'`, and `B'` are new nodes. `A`, `C`, `D`, `E`, `F` are shared between
the old and new version. The update cost is O(depth)--O(log n) for a
balanced tree--regardless of the total number of nodes.

This is the basis of Clojure's persistent vectors and hash maps, which use
wide-branching tries (32-way branching) to keep depths small in practice.



### Python: The Exposition Language

Python's built-in data structures are not persistent, but the concept is
straightforward to implement and to see at work.

#### Persistent List (Linked Nodes)

```python
class Node:
    __slots__ = ('value', 'next')
    def __init__(self, value, next=None):
        self.value = value
        self.next  = next

def cons(value, lst):       return Node(value, lst)
def head(lst):              return lst.value
def tail(lst):              return lst.next
def is_empty(lst):          return lst is None
```

```python
a = cons(1, cons(2, cons(3, None)))    # [1, 2, 3]
b = cons(0, a)                         # [0, 1, 2, 3] -- shares a
c = cons(9, a)                         # [9, 1, 2, 3] -- shares a

# All three lists share the same 1->2->3 nodes
assert tail(b) is a    # True: same object, not a copy
assert tail(c) is a    # True: same object, not a copy
```

#### Persistent Stack

A stack is just a list with push/pop:

```python
EMPTY = None

def push(stack, value): return cons(value, stack)
def pop(stack):         return tail(stack)
def peek(stack):        return head(stack)

s0 = EMPTY
s1 = push(s0, 'a')
s2 = push(s1, 'b')
s3 = push(s2, 'c')

# Every old version still accessible:
# s0 = []
# s1 = ['a']
# s2 = ['b', 'a']  -- shares s1
# s3 = ['c', 'b', 'a']  -- shares s2 (which shares s1)
```

Undo is trivial: keep a reference to the previous version. No copy made,
no history stored separately -- the history *is* the shared structure.

#### Path-Copying Binary Search Tree

```python
class BSTNode:
    __slots__ = ('key', 'value', 'left', 'right')
    def __init__(self, key, value, left=None, right=None):
        self.key   = key
        self.value = value
        self.left  = left
        self.right = right

def bst_insert(node, key, value):
    if node is None:
        return BSTNode(key, value)
    if key == node.key:
        # Copy this node with new value; children are shared
        return BSTNode(key, value, node.left, node.right)
    if key < node.key:
        # Copy this node; new left child; right is shared
        return BSTNode(node.key, node.value,
                       bst_insert(node.left, key, value),
                       node.right)
    else:
        # Copy this node; left is shared; new right child
        return BSTNode(node.key, node.value,
                       node.left,
                       bst_insert(node.right, key, value))
```

Each insert copies O(depth) nodes. Every node not on the insertion path is
shared unchanged. The old tree remains intact.

#### Sharing vs. Copying: A Memory Comparison

```python
import sys

# Naive: copy entire list on prepend
naive  = list(range(1000))
copies = [naive[:i+1] for i in range(100)]  # 100 copies of growing list
# Total: ~100 * 500 * element_size on average

# Persistent: share tail
head_node = None
for v in range(999, -1, -1):
    head_node = cons(v, head_node)   # build [0..999]

# 100 versions sharing the tail: only 100 new nodes
versions = [cons(i, head_node) for i in range(100)]
# Total: 1000 + 100 nodes  (not 100 * 1000)
```



### Under the Hood: C

Persistent data structures in C require two mechanisms that are automatic in
GC languages: tracking how many references point to each shared node, and
freeing nodes when no version needs them any more.

#### Reference Counting

Each shared node carries a count of how many structures point to it. When a
new version is created, the count on shared nodes is incremented. When a
version is dropped, counts are decremented. When a count reaches zero, the
node is freed.

```c
typedef struct node {
    int value;
    struct node *next;
    int refcount;   /* how many live pointers to this node */
} node_t;

node_t *node_retain(node_t *n) {
    if (n) n->refcount++;
    return n;
}

void node_release(node_t *n) {
    if (!n) return;
    n->refcount--;
    if (n->refcount == 0) {
        node_release(n->next);   /* release the tail first */
        free(n);
    }
}
```

`cons` increments the refcount on the tail (because the new node points to
it). Dropping a version decrements. When the last version that uses a node
is dropped, the node is freed automatically.

#### Copy-on-Write

Copy-on-write (COW) is a lazy form of persistence: nodes are shared until one
version needs to modify a node that is shared. At that point, the modifying
version makes a private copy, decrements the refcount on the original, and
modifies its private copy.

This is how Linux's `fork()` works: parent and child share all memory pages
with refcount > 1; a write by either side triggers a page copy for that page
only.

#### Thread Safety of Refcounts

A simple integer refcount is not thread-safe: two threads calling
`node_release` simultaneously on a node with refcount 2 may both read `2`,
both decrement to `1`, and neither frees the node--a memory leak. Or one
reads `1` and the other reads the decremented `0` and frees the node while
the first thread still holds a pointer--use-after-free.

Thread-safe reference counting requires atomic increment and decrement
operations:

```c
#include <stdatomic.h>

typedef struct node {
    int value;
    struct node *next;
    atomic_int refcount;
} node_t;

void node_release(node_t *n) {
    if (!n) return;
    if (atomic_fetch_sub(&n->refcount, 1) == 1) {
        /* We just decremented to 0: we are the last owner */
        node_release(n->next);
        free(n);
    }
}
```

`atomic_fetch_sub` returns the *old* value before subtraction. If it returns
`1`, the new value is `0`--this thread is the last owner and should free.
This is the correct idiom for lock-free reference counting in C11.

#### Memory Allocator Concerns

High-frequency allocation and deallocation of small nodes (as persistent
linked lists produce) stresses the general-purpose allocator. Each `malloc`
call acquires a global lock internally; each `free` does the same. Under
contention from many threads, this becomes a bottleneck.

Production implementations use:

- *Pool allocators*: allocate a large slab, hand out fixed-size chunks from
  it without locking (lock is taken only when a new slab is needed).
- *Thread-local allocation*: each thread has its own pool; no cross-thread
  locking for the common case.
- *Epoch-based reclamation*: instead of refcounting, defer freeing until
  all threads have passed through a safe point. Used in lock-free data
  structures where even atomic refcounts are too slow.

These are significant engineering investments. They are the reason persistent
data structures are straightforward to use in GC languages and substantial to
implement correctly in C.



### Concurrency Link: Lock-Free Read Sharing

The deepest value of persistent data structures for concurrent programs is
that multiple readers can safely access any version--old or new--without
any synchronisation, because no version is ever mutated.

```
Thread A: reading version 1    (safely -- version 1 is immutable)
Thread B: reading version 1    (simultaneously -- no conflict)
Thread C: creating version 2   (does not invalidate version 1)
```

The only synchronisation needed is for the pointer swap that makes version 2
visible to threads that want the latest version--a single atomic store. No
mutex, no reader-writer lock, no copy-on-access.

This is the lock-free read-sharing pattern used in databases (MVCC --
multi-version concurrency control), in the Linux kernel's RCU (read-copy-
update) mechanism, and in functional language runtimes. The structure
underpinning all of them is the same: old versions are never mutated;
structural sharing keeps the cost of new versions proportional to the change.



*Next: [11. Cost Model](../cost/README.md)--comparing the abstraction overhead
of functional style in Python and C across all patterns in this series.*
