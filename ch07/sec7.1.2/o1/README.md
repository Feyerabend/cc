
## Hash Tables

Using two real implementations to understand why hash tables
are O(1) average, when they degrade to O(n), and how resising
keeps them fast.


### 1. What Makes a Hash Table Fast?

A hash table answers the question: *"given a key, find its value instantly."*

The trick is turning the key into an *array index* using a hash function.
Instead of scanning all n entries, you jump directly to the right bucket:

```
key "apple"  ->  hash()  ->  index 7  ->  arr[7]  ->  value 5
```

No loop. No comparison of every element. One calculation, one memory access.
That's why lookups are *O(1) on average*.

The word *average* is doing a lot of work there.
Understanding when and why it fails is the real lesson.



### 2. The Two Implementations

We have two files that build on each other:

#### `hash.c` Fixed-size chaining table

```
TABLE_SIZE = 10  (never changes)
Structure:  HashTable { Node* table[10] }  (static array on the stack)
Collision resolution: chaining (linked list per bucket)
```

Simple. The table never grows--which means performance
degrades as you insert more keys than buckets.

#### `hashs.c` Dynamic resising table

```
TABLE_SIZE = 16  (initial, doubles when needed)
LOAD_FACTOR = 0.75
Structure:  HashTable { Node* table; int size; int count; }  (heap-allocated)
Collision resolution: chaining + resize when count/size >= 0.75
```

Closer to how real hash maps work (Java's `HashMap`, Python's `dict`).
When the table gets 75% full, it doubles in size and rehashes everything.



### 3. Big O Analysis: Operation by Operation

#### Insert

```c
/* hash.c */
void insert(HashTable* ht, const char* key, int value) {
    unsigned int index = hash(key);          // O(k) -> k = key length
    Node* current = ht->table[index];        // O(1) -> array access

    while (current) {                        // O(L) -> L = chain length at index
        if (strcmp(current->key, key) == 0) {
            current->value = value;
            return;
        }
        current = current->next;
    }
    Node* newNode = createNode(key, value);  // O(1)
    ...
}
```

| Scenario | Complexity | Why |
|----------|------------|-----|
| Best case | O(1) | Empty bucket--no chain to scan |
| Average case | O(1) | Chain length ≈ load factor (constant) |
| Worst case | O(n) | All keys collide into one bucket (chain length = n) |

The average case is O(1) *assuming a good hash function*
distributes keys uniformly. With a uniform distribution
and load factor α, the expected chain length is α.
If α is bounded by a constant (e.g., 0.75), lookup is O(1).

#### Search / Get

Same analysis as insert--hash to the bucket in O(1), then walk the chain.

```c
int get(HashTable* ht, const char* key) {
    unsigned int index = hash(key);   // O(k)
    Node* current = ht->table[index]; // O(1)
    while (current) {                 // O(L) average O(1), worst O(n)
        if (strcmp(current->key, key) == 0) return current->value;
        current = current->next;
    }
    return -1;
}
```

#### Delete

```c
void delete(HashTable* ht, const char* key) {
    unsigned int index = hash(key);   // O(k)
    /* walk chain, unlink node */     // O(L)
}
```

Same as insert and search: *O(1) average, O(n) worst*.

#### Resize (hashs.c only)

```c
void resize(HashTable* ht) {
    int newSize = ht->size * 2;
    Node* newTable = calloc(newSize, sizeof(Node*));  // O(newSize)

    for (int i = 0; i < ht->size; i++) {              // O(n) -> visit every node
        Node* current = ht->table[i];
        while (current) {
            unsigned int newIndex = hash(current->key) % newSize;
            ...
        }
    }
}
```

Resize is *O(n)*--it must rehash every existing key. But it only triggers
when the table is 75% full, and then doubles capacity. So if you insert n
keys total, resize is triggered at sizes 12, 24, 48, ...--the total resize
work sums to roughly `12 + 24 + 48 + ... ≈ 2n`. Spread across n inserts,
that's *O(1) amortised per insert*.

#### Summary Table

| Operation | `hash.c` (fixed) | `hashs.c` (dynamic) |
|-----------|------------------|---------------------|
| Insert | O(1) avg / O(n) worst | O(1) amortised |
| Search | O(1) avg / O(n) worst | O(1) avg / O(n) worst |
| Delete | O(1) avg / O(n) worst | O(1) avg / O(n) worst |
| Resize | N/A | O(n)--amortises to O(1) per insert |
| Space | O(n + TABLE_SIZE) | O(n + size) |



### 4. The Hash Function

Both files use the same polynomial rolling hash:

```c
unsigned int hash(const char* key) {
    unsigned int hash = 0;
    while (*key) {
        hash = (hash * 31) + *key++;
    }
    return hash % TABLE_SIZE;
}
```

*What it does:* treats the string as a base-31 number.

```
"abc"  ->  'a'*31² + 'b'*31¹ + 'c'*31⁰
       =    97*961 + 98*31   + 99
       =    93217 + 3038 + 99
       =    96354
       ->   96354 % 10  =  4   (index into the table)
```

*Time complexity:* O(k) where k is the key length. For short keys (as in
most practical usage), this is treated as O(1).

*The multiplier 31:* a small prime. Prime multipliers spread bits more
uniformly and reduce collisions. Java's `String.hashCode()` uses the same
value. Other common choices: 37, 53, 97.

*The modulo `% TABLE_SIZE`:* maps the hash to a valid array index. This
is where collisions can be introduced if TABLE_SIZE is poorly chosen (e.g.,
a power of 2 with a bad hash can cluster keys).



### 5. The Collision Problem

A collision is when two different keys hash to the same index. Both files
resolve this with *separate chaining*--each bucket is a linked list.

```
After inserting "a", "b", "c" into hash.c (TABLE_SIZE = 10):

Index 0: NULL
Index 1: (b: 2) -> NULL
Index 2: NULL
Index 3: NULL
Index 4: NULL
Index 5: NULL
Index 6: (a: 10) -> NULL       <- "a" updated from 1 to 10
Index 7: (c: 3) -> NULL
Index 8: NULL
Index 9: NULL
```

No collisions here because the table is nearly empty. Now imagine inserting
100 keys into a table of size 10. Each bucket's chain grows to ~10 nodes.
Every lookup must now scan 10 nodes on average--*O(10) = O(1)* technically
(constant), but 10× slower than an empty table.

With 1000 keys and TABLE_SIZE = 10, chains grow to ~100 nodes.
Lookups become *O(100)*--the hash table has degraded to near-linear search.

This is exactly the problem that `hashs.c` solves with resizing.



### 6. Load Factor and Resizing

The *load factor* α = count / size. It measures how full the table is.

```c
/* hashs.c triggers resize when: */
if ((float)ht->count / ht->size >= LOAD_FACTOR) {  /* 0.75 */
    resize(ht);
}
```

| Load factor | Average chain length | Behaviour |
|-------------|----------------------|-----------|
| 0.25 | 0.25 nodes | Very fast, wastes memory |
| 0.75 | 0.75 nodes | Good balance (Java, Python use this) |
| 1.0 | 1.0 nodes | Acceptable |
| 5.0 | 5.0 nodes | Noticeably slower |
| 100.0 | 100 nodes | Hash table has become a linked list |

`hash.c` has no load factor control. Insert 100 keys and it silently degrades.
`hashs.c` keeps α ≤ 0.75 by resizing--guaranteeing O(1) average behaviour.

*The resize sequence for `hashs.c`:*

```
Start:       size=16,  resize at count=12
After 1st:   size=32,  resize at count=24
After 2nd:   size=64,  resize at count=48
After 3rd:   size=128, resize at count=96
...
```

Each resize doubles capacity, so it happens at most log₂(n) times for n inserts.



### 7. Timing the Difference

The following program measures insert and lookup performance for both approaches
as n grows. It deliberately overloads `hash.c`'s fixed table to show degradation.

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ── paste the full hash.c and hashs.c code here,
      renaming their functions to avoid conflicts:
      hash.c   -> insert_fixed, get_fixed, etc.
      hashs.c  -> insert_dynamic, search_dynamic, etc.   ── */

#define REPEATS 5

double time_ms(clock_t start, clock_t end, int reps) {
    return 1000.0 * (end - start) / CLOCKS_PER_SEC / reps;
}

/* generate a key string like "key_000042" */
void make_key(char* buf, int i) {
    sprintf(buf, "key_%06d", i);
}

void benchmark(int n) {
    char key[32];
    clock_t start, end;

    /* ── fixed table (hash.c style) ── */
    /* For demonstration: manually track degradation by
       printing chain lengths after bulk insert */

    printf("\n--- n = %d ---\n", n);

    /* You can adapt this to call your actual fixed/dynamic
       insert and get functions and time them with clock() */

    /* Example timing skeleton: */

    /*
    start = clock();
    for (int r = 0; r < REPEATS; r++) {
        for (int i = 0; i < n; i++) {
            make_key(key, i);
            insert_fixed(&ht_fixed, key, i);
        }
    }
    end = clock();
    printf("Fixed   insert %d keys: %.3f ms avg\n", n, time_ms(start, end, REPEATS));

    start = clock();
    for (int r = 0; r < REPEATS; r++) {
        for (int i = 0; i < n; i++) {
            make_key(key, i);
            get_fixed(&ht_fixed, key);
        }
    }
    end = clock();
    printf("Fixed   lookup %d keys: %.3f ms avg\n", n, time_ms(start, end, REPEATS));

    // ... same for dynamic table
    */
}

int main(void) {
    int sizes[] = {10, 100, 1000, 10000, 100000};
    for (int i = 0; i < 5; i++) {
        benchmark(sizes[i]);
    }
    return 0;
}
```

#### Self-contained timing experiment (no merging needed)

A simpler approach: just add `clock()` calls directly inside your two files.

*Add to `hash.c` main():*

```c
#include <time.h>

int main() {
    HashTable ht = {0};
    int n = 5000;    /* << change this */
    char key[32];
    clock_t start, end;

    /* --- time inserts --- */
    start = clock();
    for (int i = 0; i < n; i++) {
        sprintf(key, "key_%d", i);
        insert(&ht, key, i);
    }
    end = clock();
    printf("hash.c  insert %d keys: %.4f ms\n", n,
           1000.0 * (end - start) / CLOCKS_PER_SEC);

    /* --- time lookups (worst case: last key inserted) --- */
    sprintf(key, "key_%d", n - 1);
    start = clock();
    for (int r = 0; r < 100000; r++) {
        get(&ht, key);
    }
    end = clock();
    printf("hash.c  lookup x100000: %.4f ms\n",
           1000.0 * (end - start) / CLOCKS_PER_SEC);

    freeTable(&ht);
    return 0;
}
```

*Add the equivalent to `hashs.c` main()*--replacing `insert`/`search`
with the `hashs.c` versions.

#### Expected results

With TABLE_SIZE = 10 and n = 5000 (500 keys per bucket on average):

```
hash.c  insert 5000 keys:  2.1430 ms    <- slows down as chains grow
hash.c  lookup x100000:    8.7210 ms    <- scanning long chains

hashs.c insert 5000 keys:  0.9820 ms    <- stays fast, resizes as needed
hashs.c lookup x100000:    0.3140 ms    <- nearly constant time
```

The lookup gap widens as n grows. That's O(n) vs O(1) made visible.



### 8. Experiments to Try

#### Experiment A: Overload the fixed table

In `hash.c`, change `TABLE_SIZE` to `5`, insert 500 keys, and time lookups.
Then change it to `1000` and repeat. Record:

| TABLE_SIZE | Keys inserted | Avg chain length | Lookup time |
|------------|---------------|------------------|-------------|
| 5 | 500 | 100 | ? |
| 10 | 500 | 50 | ? |
| 50 | 500 | 10 | ? |
| 500 | 500 | 1 | ? |
| 1000 | 500 | 0.5 | ? |

*What to observe:* lookup time scales with average chain length, which is
`n / TABLE_SIZE`. This is O(n) behaviour hiding inside a "hash table."



#### Experiment B: Measure resize triggers in hashs.c

Add a print statement inside `resize()`:

```c
void resize(HashTable* ht) {
    printf("  [resize] size %d -> %d  (count=%d)\n",
           ht->size, ht->size * 2, ht->count);
    ...
}
```

Insert 200 keys and watch when resizes happen. You'll see:

```
[resize] size 16  -> 32   (count=12)
[resize] size 32  -> 64   (count=24)
[resize] size 64  -> 128  (count=48)
[resize] size 128 -> 256  (count=96)
[resize] size 256 -> 512  (count=192)
```

Resizes double each time--that's why the amortised cost per insert is O(1).



#### Experiment C: Visualise the distribution

Add this function to either file to print how evenly keys are distributed:

```c
void printDistribution(HashTable* ht) {
    int max_chain = 0;
    int empty = 0;
    for (int i = 0; i < ht->size; i++) {  /* or TABLE_SIZE for hash.c */
        int len = 0;
        Node* cur = ht->table[i];
        while (cur) { len++; cur = cur->next; }
        if (len == 0) empty++;
        if (len > max_chain) max_chain = len;
        /* print a bar */
        printf("  [%3d] ", i);
        for (int j = 0; j < len; j++) printf("*");
        printf(" (%d)\n", len);
    }
    printf("  Empty buckets: %d  Max chain: %d\n", empty, max_chain);
}
```

Run it after inserting 5, 10, and 50 keys. A good hash function produces
roughly equal bar lengths. If one bar is much longer than others, you have
a clustering problem--a sign of a poor hash function or an adversarial input.



#### Experiment D: Hash function comparison

Replace the hash function in `hash.c` with a terrible one:

```c
/* bad hash: maps everything to index 0 */
unsigned int hash(const char* key) {
    return 0;
}
```

Now insert 100 keys. Every single key lands in bucket 0. Every lookup
must scan all 100 nodes. The hash table has become a linked list: *O(n)*.

This is the worst case made explicit. Restore the original hash and observe
the difference in lookup time.



### 9. Comparison: Array vs Linked List vs Hash Table

After working through these experiments, you can see where hash tables fit:

| Operation | Unsorted Array | Sorted Array | Linked List | Hash Table (good) | Hash Table (degraded) |
|-----------|----------------|--------------|-------------|-------------------|-----------------------|
| Access by index | O(1) | O(1) | O(n) | N/A | N/A |
| Search by value | O(n) | O(log n) | O(n) | *O(1)* | O(n) |
| Insert | O(1) tail | O(n) shift | O(1) head | *O(1)* | O(n) |
| Delete | O(n) | O(n) | O(1)* | *O(1)* | O(n) |

*Linked list delete is O(1) only if you already have a pointer to the node.

The hash table wins on search, insert, and delete simultaneously--but only
if the load factor is controlled. That's the whole point of `hashs.c`.



### Takeaways

*O(1) is conditional.* Hash table operations are O(1) *on average*, assuming
a uniform hash function and a bounded load factor. Neither is guaranteed
automatically--both must be designed for.

*The load factor is the controlling variable.* Keep it low (≤ 0.75) and
performance stays O(1). Let it grow unbounded and you get O(n).
The difference between `hash.c` and `hashs.c` is entirely about
controlling this one number.

*Resize is expensive but amortised.* A single resize costs O(n), but
because it doubles capacity, it happens log₂(n) times over n inserts.
Total resize cost across all inserts is O(n), making each insert
O(1) amortised--the same accounting trick that makes dynamic arrays fast.

*The hash function matters.* A poor hash function clusters keys into
a few buckets, turning O(1) lookup into O(n) lookup. The polynomial
hash in these files is a solid general-purpose choice for string keys.

