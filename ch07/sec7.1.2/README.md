
## Beatiful Big O Notation

Big O notation is a *mathematical language* for describing how an algorithm's
resource usage (time or memory) *grows* as the input size `n` grows toward infinity.

It does *not* measure wall-clock time in seconds. It measures the *shape* of
growth--the relationship between input size and work performed.


#### The Core Intuition

Imagine you have a list of `n` names and you want to find "Alice":
- *Approach A:* You know Alice is always first -> check once -> *O(1)*
- *Approach B:* The list is sorted, so you split it in half repeatedly -> *O(log n)*
- *Approach C:* You scan every name from top to bottom -> *O(n)*
- *Approach D:* For every name, you compare it to every other name -> *O(n²)*

The *scale* at which these diverge is dramatic. At `n = 1,000,000`:

| Complexity | Operations        |
|------------|-------------------|
| O(1)       | 1                 |
| O(log n)   | ~20               |
| O(n)       | 1,000,000         |
| O(n²)      | 1,000,000,000,000 |

This is why choosing the right algorithm matters far more than hardware speed.



### 2. The Formal Definition

#### The Mathematical Definition of Big O

We say *f(n) = O(g(n))* if and only if there exist positive
constants *c* and *n₀* such that:

```
f(n) ≤ c · g(n)    for all n ≥ n₀
```

In plain English: beyond some threshold `n₀`, the function `f(n)` never exceeds `g(n)`
multiplied by some constant `c`. The constant `c` absorbs hardware differences,
language overhead, and implementation details.

#### Example: Proving f(n) = 3n + 5 is O(n)

We need to find constants `c` and `n₀` such that:

```
3n + 5 ≤ c · n    for all n ≥ n₀
```

Choose `c = 4`. Then we need:

```
3n + 5 ≤ 4n
5 ≤ n
```

So for all `n ≥ 5`, with `c = 4`, the inequality holds. Therefore `3n + 5 = O(n)`. ✓

#### Example: Proving f(n) = 2n² + 3n + 1 is O(n²)

We need: `2n² + 3n + 1 ≤ c · n²` for all `n ≥ n₀`.

Divide both sides by `n²` (valid since `n > 0`):

```
2 + 3/n + 1/n² ≤ c
```

As `n -> ∞`, the terms `3/n` and `1/n²` vanish. Choose `c = 6` and `n₀ = 1`. Then:

```
2 + 3 + 1 = 6 ≤ 6    ✓  (at n = 1, the maximum)
```

Therefore `2n² + 3n + 1 = O(n²)`. ✓

#### Related Notations

Big O is one of several asymptotic notations.
Understanding themclarifies what Big O *doesn't* say:

| Notation | Meaning | Formal condition |
|----------|---------|------------------|
| *O(g(n))* | Upper bound (at most) | f(n) ≤ c·g(n) for large n |
| *Ω(g(n))* | Lower bound (at least) | f(n) ≥ c·g(n) for large n |
| *Θ(g(n))* | Tight bound (exactly) | c₁·g(n) ≤ f(n) ≤ c₂·g(n) |
| *o(g(n))* | Strict upper bound | lim f(n)/g(n) = 0 as n -> ∞ |

When engineers say "Big O" in practice, they almost always mean *Θ* (tight bound).
A linear search is O(n²) by the formal definition--but that's useless.
We aim for the *tightest* correct bound.



### 3. The Complexity Classes

Listed from best to worst:

```
O(1) < O(log n) < O(n) < O(n log n) < O(n²) < O(n³) < O(2ⁿ) < O(n!)
```

#### O(1)--Constant

Runtime is *independent of input size*.
The same work is done whether `n = 1` or `n = 1,000,000`.

*Examples:* array index access, hash table lookup,
stack push/pop, returning the first element.

*Growth:* flat line. Always the goal.



#### O(log n)--Logarithmic

The algorithm *halves* (or thirds, or divides by k)
the problem with each step.

*Mathematical basis:* If you halve n repeatedly until you reach 1:

```
n -> n/2 -> n/4 -> ... -> 1
```

After `k` steps: `n / 2^k = 1` -> `2^k = n` -> `k = log₂(n)`.

That's why binary search takes at most `log₂(n)` steps.

*Examples:* binary search, balanced BST operations,
finding a number in a phone book.

*Growth:* extremely slow. At `n = 1,000,000,000`,
only ~30 steps are needed.



#### O(n)--Linear

Work grows *proportionally* to input.
Every element is visited a constant number of times.

*Examples:* linear search, summing an array, finding min/max,
reading a file.

*Growth:* straight line through the origin. 2× input = 2× time.



#### O(n log n)--Linearithmic

Appears in *divide-and-conquer* algorithms: split the data
(log n levels), do O(n) work at each level.

*Mathematical basis:* `T(n) = 2T(n/2) + O(n)` (recurrence for merge sort).
By the Master Theorem (Case 2):

```
a = 2, b = 2, f(n) = n
log_b(a) = log₂(2) = 1
f(n) = n = n^(log_b a)  ->  Case 2  ->  T(n) = O(n log n)
```

*Examples:* merge sort, heapsort, many divide-and-conquer algorithms.

*Growth:* slightly worse than linear, but far better than quadratic.
The best possible for comparison-based sorting.



#### O(n²)--Quadratic

Typically arises from *two nested loops* each iterating over the input.

*Examples:* bubble sort, insertion sort, selection sort, comparing all pairs.

*Growth:* 2× input = 4× time. Becomes painful around n = 10,000–100,000.



#### O(2ⁿ)--Exponential

Each new element *doubles* the total work. Arises in brute-force
combinatorial search.

*Examples:* naive recursive Fibonacci, generating all subsets,
the travelling salesman (brute force).

*Growth:* explosive. At `n = 64`, `2⁶⁴ ≈ 1.8 × 10¹⁹`--more operations
than a modern computer can run in thousands of years.



#### O(n!)--Factorial

Even worse than exponential. Arises in *permutation* problems.

*Examples:* brute-force travelling salesman, generating all permutations.

*Growth:* `20! ≈ 2.4 × 10¹⁸`. Practically impossible for n > ~12.



### 4. The Four Rules of Simplification

These rules let you reduce any expression to its Big O class.

#### Rule 1: Drop Constants

Constant multipliers don't affect the growth class.

```
O(2n)      ->  O(n)
O(500)     ->  O(1)
O(3n²)     ->  O(n²)
O(n/2)     ->  O(n)
```

*Why:* The formal definition already absorbs constants into `c`.
Hardware can change a constant by 10×; the growth class cannot be changed by any constant.



#### Rule 2: Drop Lower-Order Terms

As n -> ∞, the dominant term overwhelms all others.

```
O(n² + n)          ->  O(n²)
O(n³ + n² + n + 1) ->  O(n³)
O(2ⁿ + n¹⁰⁰)       ->  O(2ⁿ)
O(n log n + n)      ->  O(n log n)
```

*Why:* At `n = 1000`, `n² = 1,000,000` vs `n = 1,000`.
The smaller term is less than 0.1% of the total.



#### Rule 3: Sequential Steps Add

If you do step A, then step B, add their complexities:

```
O(A) + O(B)
```

Then apply Rule 2 to simplify.

```
O(n) + O(n²)     =  O(n + n²)  ->  O(n²)
O(log n) + O(n)  =  O(n)
O(n) + O(n)      =  O(2n)      ->  O(n)
```



#### Rule 4: Nested Steps Multiply

If step A contains step B (a loop inside a loop), multiply:

```
O(A) × O(B)
```

```
O(n) × O(n)      =  O(n²)
O(n) × O(log n)  =  O(n log n)
O(n) × O(1)      =  O(n)
O(n²) × O(n)     =  O(n³)
```



### 5. Calculating Big O Step by Step

#### Method

1. Identify every loop and recursive call.
2. Determine how many times each executes in terms of `n`.
3. Apply Rules 3 and 4 (add sequential, multiply nested).
4. Apply Rules 1 and 2 (drop constants and lower-order terms).



#### Worked Example A--Two separate loops

```python
for i in range(n):       ## Loop 1: n iterations
    print(i)

for j in range(n):       ## Loop 2: n iterations
    print(j * 2)
```

Step-by-step:
- Loop 1 -> `O(n)`
- Loop 2 -> `O(n)`
- Sequential (Rule 3): `O(n) + O(n) = O(2n)`
- Drop constant (Rule 1): `O(2n) -> O(n)`

*Result: O(n)*



#### Worked Example B--Nested loops

```python
for i in range(n):        ## Outer: n iterations
    for j in range(n):    ## Inner: n iterations each time
        print(i, j)
```

Step-by-step:
- Inner loop -> `O(n)`
- Outer loop wraps it -> `O(n) × O(n)` (Rule 4)
- Result: `O(n²)`

*Result: O(n²)*



#### Worked Example C--Constant inner loop (a common trap)

```python
for i in range(n):           ## Outer: n iterations
    for j in range(1000):    ## Inner: 1000--a fixed constant
        print(i, j)
```

Step-by-step:
- Inner loop -> `O(1000)` = `O(1)` (constant, independent of n)
- Outer loop -> `O(n) × O(1)` = `O(n)`

*Result: O(n)*--not O(n²). The inner loop is constant.



#### Worked Example D--Shrinking inner loop

```python
for i in range(n):
    for j in range(i, n):    ## Inner runs n-i times
        print(i, j)
```

Step-by-step--count total iterations precisely:

```
When i=0: n   iterations
When i=1: n-1 iterations
...
When i=n-1: 1 iteration

Total = n + (n-1) + (n-2) + ... + 1 = n(n+1)/2
```

Expand: `n(n+1)/2 = n²/2 + n/2`

Drop lower term and constant (Rules 1, 2): `-> O(n²)`

*Result: O(n²)*--even though the inner loop shrinks,
the total is still quadratic.



#### Worked Example E--Logarithmic recursion

```python
def halving(n):
    if n <= 1:
        return
    halving(n // 2)    ## Problem is halved each call
```

Step-by-step:
- Each call halves `n`
- Calls continue until `n = 1`
- Number of calls: how many times can you halve n? -> `log₂(n)` times

*Result: O(log n)*



#### Worked Example F--Mixed complexity

```python
for i in range(n):                  ## O(n)
    print(i)

for i in range(n):                  ## O(n log n)
    j = n
    while j > 1:
        j = j // 2                  ## halves: O(log n) iterations
        print(i, j)

for i in range(n):                  ## O(n²)
    for j in range(n):
        print(i * j)
```

Step-by-step:
- Block 1: `O(n)`
- Block 2: outer `O(n)` × inner `O(log n)` = `O(n log n)`
- Block 3: `O(n) × O(n)` = `O(n²)`
- Sequential (Rule 3): `O(n) + O(n log n) + O(n²)`
- Drop lower terms (Rule 2): `O(n²)`

*Result: O(n²)*



### 6. Real Algorithm Analysis

#### Linear Search--O(n)

```python
def linear_search(arr, target):
    for i in range(len(arr)):    ## worst case: all n elements
        if arr[i] == target:
            return i
    return -1
```

*Analysis:* One loop over n elements, doing O(1) work per iteration.
Total: `n × O(1) = O(n)`.

Worst case: target is last or not present -> n comparisons.



#### Binary Search--O(log n)

```python
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```

*Analysis:* Each iteration halves the search space:

```
Start: n elements
After 1 step: n/2
After 2 steps: n/4
After k steps: n/2^k

Stop when n/2^k = 1  ->  k = log₂(n)
```

Total iterations: `log₂(n)`. Each does O(1) work.

*Result: O(log n)*

*Requires a sorted array. The O(log n) benefit over O(n) is only
worth it if you search many times (otherwise the sort cost dominates).*



#### Bubble Sort--O(n²)

```python
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):              ## outer: n
        for j in range(n - i - 1): ## inner: n-1, n-2, ..., 1
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
```

*Analysis:* Total comparisons:

```
(n-1) + (n-2) + ... + 1 = n(n-1)/2 = n²/2 - n/2
```

Drop lower term and constant -> `O(n²)`.



#### Merge Sort--O(n log n)

```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left  = merge_sort(arr[:mid])   ## recurse left half
    right = merge_sort(arr[mid:])   ## recurse right half
    return merge(left, right)       ## O(n) merge step
```

*Analysis via recurrence relation:*

Let `T(n)` = time to sort n elements.

```
T(n) = 2·T(n/2) + O(n)
     ↑              ↑
  two halves    merging them
```

Solve by expanding:

```
T(n) = 2·T(n/2)   + n
     = 2·[2·T(n/4) + n/2] + n  =  4·T(n/4) + 2n
     = 4·[2·T(n/8) + n/4] + 2n =  8·T(n/8) + 3n
     ...
     = 2^k · T(n/2^k) + k·n
```

Stop when `n/2^k = 1`, i.e. `k = log₂(n)`:

```
T(n) = n·T(1) + n·log₂(n)  =  O(n log n)
```

*Alternatively, via the Master Theorem:*

For recurrences of the form `T(n) = a·T(n/b) + f(n)`:

```
a = 2, b = 2, f(n) = n
log_b(a) = log₂(2) = 1
f(n) = n^1 = n^(log_b a)  ->  Case 2 of Master Theorem
->  T(n) = O(n log n)
```

*Result: O(n log n)*

This is also the *theoretical lower bound* for comparison-based sorting--no
comparison sort can do better than O(n log n) in the worst case.



#### Naive Fibonacci--O(2ⁿ)

```python
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
```

*Analysis:* The call tree branches into 2 calls per node,
to a depth of n:

```
              fib(5)
            /        \
        fib(4)       fib(3)
       /     \       /    \
   fib(3) fib(2) fib(2) fib(1)
   ...
```

Total nodes in the tree ≈ `2⁰ + 2¹ + 2² + ... + 2ⁿ = 2^(n+1) - 1 = O(2ⁿ)`.

Many subproblems are recalculated repeatedly. Fix:
*memoization* stores computed values, reducing it to `O(n)`.



#### Hash Table Lookup--O(1) average

```python
table = {"alice": 42, "bob": 7}
value = table["alice"]
```

*Analysis:* A hash function maps the key to a bucket in O(1).
No iteration needed. On average, O(1) per lookup.

*Worst case* (all keys collide to one bucket): O(n).
A good hash function makes this astronomically rare in practice.



#### QuickSort--O(n log n) average, O(n²) worst

```python
def quicksort(arr, lo, hi):
    if lo < hi:
        pivot = partition(arr, lo, hi)   ## O(n)
        quicksort(arr, lo, pivot - 1)
        quicksort(arr, pivot + 1, hi)
```

*Average case:* pivot splits array roughly in half each time -> same
recurrence as merge sort -> `O(n log n)`.

*Worst case:* pivot is always the smallest or largest element
(e.g., sorted input with naive pivot) -> one side has n-1 elements each time:

```
T(n) = T(n-1) + O(n)  ->  O(n²)
```

Fix: random pivot or median-of-three selection keeps expected time at `O(n log n)`.



### 7. Best, Average, and Worst Case

Big O typically describes *worst-case* behaviour, but algorithms have three cases:

| Case | Meaning | Notation |
|------|---------|----------|
| *Best* | Input is already ideal (e.g., sorted) | Often Ω(·) |
| *Average* | Expected over all typical inputs | Often Θ(·) |
| *Worst* | Most adversarial input possible | Often O(·) |

#### Example: Linear Search

| Case | When | Complexity |
|------|------|------------|
| Best | Target is the first element | O(1) |
| Average | Target is somewhere in the middle | O(n/2) -> O(n) |
| Worst | Target is last or not present | O(n) |

#### Example: QuickSort

| Case | When | Complexity |
|------|------|------------|
| Best | Pivot always splits perfectly in half | O(n log n) |
| Average | Random or typical data | O(n log n) |
| Worst | Already sorted, naive pivot | O(n²) |



### 8. Space Complexity

Big O applies to *memory* too. Every variable, recursive call frame,
and data structure costs space.

#### Examples

*O(1) space*--iterative algorithms with a fixed number of variables:

```python
def sum_array(arr):
    total = 0           ## one variable
    for x in arr:
        total += x
    return total
```

*O(n) space*--storing n elements:

```python
def copy_array(arr):
    result = []
    for x in arr:
        result.append(x)  ## grows with n
    return result
```

*O(n) space (call stack)*--recursive calls each use a stack frame:

```python
def factorial(n):
    if n == 0: return 1
    return n * factorial(n - 1)  ## n frames on the stack
```

*O(log n) space*--binary search recursively (depth = log n):

```python
def binary_search_rec(arr, target, lo, hi):
    if lo > hi: return -1
    mid = (lo + hi) // 2
    if arr[mid] == target: return mid
    if arr[mid] < target:
        return binary_search_rec(arr, target, mid + 1, hi)
    return binary_search_rec(arr, target, lo, mid - 1)
```

#### Time vs Space Trade-offs

Many algorithms trade one for the other. Memoisation sacrifices O(n)
space to reduce O(2ⁿ) time to O(n). Hash maps use O(n) space to give
O(1) lookups instead of O(n) searches.



### 9. Data Structure Reference

#### Time Complexity

| Structure | Access | Search | Insert | Delete |
|-----------|--------|--------|--------|--------|
| Array | O(1) | O(n) | O(n) | O(n) |
| Linked List | O(n) | O(n) | O(1) | O(1) |
| Stack | O(n) | O(n) | O(1) | O(1) |
| Queue | O(n) | O(n) | O(1) | O(1) |
| Hash Table |--| O(1) avg | O(1) avg | O(1) avg |
| BST (balanced) | O(log n) | O(log n) | O(log n) | O(log n) |
| Heap | O(1) peak | O(n) | O(log n) | O(log n) |

#### Sorting Algorithm Reference

| Algorithm | Best | Average | Worst | Space |
|-----------|------|---------|-------|-------|
| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) |
| Selection Sort | O(n²) | O(n²) | O(n²) | O(1) |
| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) |
| QuickSort | O(n log n) | O(n log n) | O(n²) | O(log n) |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | O(1) |
| Counting Sort | O(n+k) | O(n+k) | O(n+k) | O(k) |



### 10. Common Mistakes

#### Mistake 1: Confusing O with Θ

Saying "bubble sort is O(n)" is technically true by the formal definition,
but useless. Always aim for the *tightest* correct bound.
Bubble sort is Θ(n²) in the worst and average case.



#### Mistake 2: Forgetting that constant-bound inner loops are O(1)

```python
for i in range(n):
    for j in range(10):   ## This is O(1), not O(n)
        print(j)
```

This is `O(n)`, not `O(n²)`. The inner loop iterates a fixed 10 times.



#### Mistake 3: Assuming two inputs are the same

If a function takes two lists of sizes `m` and `n`:

```python
def combine(a, b):
    for x in a:      ## O(m)
        for y in b:  ## O(n)
            print(x, y)
```

This is `O(m × n)`, not `O(n²)`. If m and n are independent,
they must stay separate.



#### Mistake 4: Ignoring amortised complexity

A dynamic array (like Python's `list`) occasionally doubles its capacity, costing O(n).
But averaged across many appends, each append costs O(1) amortised:

```
n appends: n×O(1) + occasional O(n) resize  ->  total O(n)  ->  O(1) per append
```



#### Mistake 5: Thinking O(n log n) is "almost" O(n)

It isn't. At `n = 10⁶`, `n log n ≈ 2 × 10⁷`--twenty times more than `n`. At `n = 10⁹`,
it's thirty times more. In latency-critical systems, that gap matters.



### Summary

```
O(1)  <  O(log n)  <   O(n)  <  O(n log n)  <  O(n²)  <  O(2ⁿ)  <  O(n!)
 │          │           │            │           │         │         │
hash      binary      scan      merge sort    nested    subsets   permutations
lookup    search      list                     loops
```

The fundamental skill is this:
*look at your loops,
count how they scale with n,
multiply for nesting,
add for sequence, then simplify*.
Everything else follows from those rules.



### Reference

* Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2022). *Introduction to algorithms* (4th ed.). The MIT Press.

* Knuth, D. E. (1998). *The art of computer programming: Vol. 3. Sorting and searching* (2nd ed.). Addison-Wesley.

![CLRS](.)
