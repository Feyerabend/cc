
## Algorithm Criteria for Systems Work

*Choosing the right algorithm is frequently the difference
between a system that scales to millions of requests per
second and one that collapses under moderate load.*



### 1. Correctness

*Description:*
An algorithm must produce the correct output for *every* valid input--not
just the typical case. This includes edge cases: empty inputs, single-element
collections, maximum-size inputs, duplicate values, already-sorted data,
and boundary conditions. In systems work, a sorting routine that fails 0.001%
of the time is unacceptable when running billions of operations a day.
Correctness is the baseline; no other metric matters if the result is wrong.
Formal verification, exhaustive unit testing, and property-based testing
are all tools used to establish confidence in correctness.



#### C: Binary Search (Correct Handling of Edge Cases)

```c
#include <stdio.h>

// Returns index of target in sorted array, or -1 if not found.
// Correctly handles: empty arrays, single elements, duplicates.
int binary_search(const int *arr, int n, int target) {
    if (n <= 0) return -1; // edge: empty array
    int lo = 0, hi = n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2; // avoids integer overflow vs. (lo+hi)/2
        if (arr[mid] == target) return mid;
        else if (arr[mid] < target)  lo = mid + 1;
        else                         hi = mid - 1;
    }
    return -1;
}

int main(void) {
    int arr[] = {1, 3, 5, 7, 9, 11};
    int n = sizeof(arr) / sizeof(arr[0]);

    printf("Find 7:  index %d\n",  binary_search(arr, n, 7));   //  3
    printf("Find 1:  index %d\n",  binary_search(arr, n, 1));   //  0
    printf("Find 11: index %d\n",  binary_search(arr, n, 11));  //  5
    printf("Find 4:  index %d\n",  binary_search(arr, n, 4));   // -1
    printf("Empty:   index %d\n",  binary_search(arr, 0, 7));   // -1
    return 0;
}
```



#### Python: Binary Search (Correct Handling of Edge Cases)

```python
def binary_search(arr: list[int], target: int) -> int:
    """Return index of target in sorted arr, or -1 if absent.
    Handles empty lists and single-element lists correctly."""
    if not arr:
        return -1
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

if __name__ == "__main__":
    arr = [1, 3, 5, 7, 9, 11]
    print(binary_search(arr, 7))    # 3
    print(binary_search(arr, 1))    # 0
    print(binary_search(arr, 11))   # 5
    print(binary_search(arr, 4))    # -1
    print(binary_search([], 7))     # -1
```



### 2. Time Complexity

*Description:*
Time complexity describes how the execution time of an algorithm
grows as the size of the input *n* increases. It is most commonly
expressed using *Big-O notation*, which captures the dominant term
and ignores constants. Common classes include O(1) (constant),
O(log n) (logarithmic), O(n) (linear), O(n log n) (linearithmic),
O(n²) (quadratic), and O(2ⁿ) (exponential). In systems work, the
difference between O(n²) and O(n log n) is the difference between
a routine that works fine at n=1,000 and one that brings a server
to its knees at n=100,000. Time complexity analysis guides us
toward scalable designs.



#### C: Merge Sort O(n log n) vs Bubble Sort O(n²)

```c
#include <stdio.h>
#include <string.h>

// --- Merge Sort: O(n log n) ---
void merge(int *arr, int l, int m, int r) {
    int n1 = m - l + 1, n2 = r - m;
    int left[n1], right[n2];
    for (int i = 0; i < n1; i++) left[i]  = arr[l + i];
    for (int j = 0; j < n2; j++) right[j] = arr[m + 1 + j];
    int i = 0, j = 0, k = l;
    while (i < n1 && j < n2)
        arr[k++] = (left[i] <= right[j]) ? left[i++] : right[j++];
    while (i < n1) arr[k++] = left[i++];
    while (j < n2) arr[k++] = right[j++];
}

void merge_sort(int *arr, int l, int r) {
    if (l < r) {
        int m = l + (r - l) / 2;
        merge_sort(arr, l, m);
        merge_sort(arr, m + 1, r);
        merge(arr, l, m, r);
    }
}


// --- Bubble Sort: O(n²) ---
void bubble_sort(int *arr, int n) {
    for (int i = 0; i < n - 1; i++)
        for (int j = 0; j < n - i - 1; j++)
            if (arr[j] > arr[j + 1]) {
                int tmp = arr[j]; arr[j] = arr[j+1]; arr[j+1] = tmp;
            }
}

int main(void) {
    int a[] = {64, 34, 25, 12, 22, 11, 90};
    int b[] = {64, 34, 25, 12, 22, 11, 90};
    int n = 7;
    merge_sort(a, 0, n - 1);
    bubble_sort(b, n);
    printf("Merge sort:  "); for (int i=0;i<n;i++) printf("%d ",a[i]); printf("\n");
    printf("Bubble sort: "); for (int i=0;i<n;i++) printf("%d ",b[i]); printf("\n");
}
```



#### Python: Merge Sort O(n log n) vs Bubble Sort O(n²)

```python
def merge_sort(arr: list[int]) -> list[int]:
    """O(n log n)--divide and conquer."""
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left  = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    result, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def bubble_sort(arr: list[int]) -> list[int]:
    """O(n²)--fine for tiny n, painful at scale."""
    arr = arr[:]
    n = len(arr)
    for i in range(n - 1):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

data = [64, 34, 25, 12, 22, 11, 90]
print("Merge sort: ", merge_sort(data))
print("Bubble sort:", bubble_sort(data))
```



### 3. Space Complexity

*Description:*
Space complexity measures the memory an algorithm consumes relative to its
input size, covering both the *runtime stack* (including recursive call frames)
and any *auxiliary data structures* allocated during execution. In resource-constrained
environments--embedded systems, high-throughput servers, containers with
memory limits--an algorithm that uses O(1) auxiliary space may be preferable
to one using O(n), even if both have the same time complexity. For example,
in-place QuickSort uses O(log n) stack space, while Merge Sort requires O(n)
auxiliary space for the temporary arrays.



#### C: In-Place QuickSort (O(log n) auxiliary) vs Merge Sort (O(n) auxiliary)

```c
#include <stdio.h>

// -- In-place QuickSort: O(log n) stack, O(1) auxiliary --
void swap(int *a, int *b) { int t = *a; *a = *b; *b = t; }

int partition(int *arr, int lo, int hi) {
    int pivot = arr[hi], i = lo - 1;
    for (int j = lo; j < hi; j++)
        if (arr[j] <= pivot) swap(&arr[++i], &arr[j]);
    swap(&arr[i + 1], &arr[hi]);
    return i + 1;
}

void quicksort(int *arr, int lo, int hi) {
    if (lo < hi) {
        int p = partition(arr, lo, hi);
        quicksort(arr, lo, p - 1);
        quicksort(arr, p + 1, hi);
    }
}

int main(void) {
    int arr[] = {10, 80, 30, 90, 40, 50, 70};
    int n = 7;
    quicksort(arr, 0, n - 1);
    printf("QuickSort (in-place, O(log n) stack): ");
    for (int i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\n");
}
```



#### Python--In-Place QuickSort vs Space-Heavy Naive Merge

```python
def quicksort_inplace(arr: list[int], lo: int, hi: int) -> None:
    """O(log n) average stack depth; O(1) auxiliary heap."""
    if lo < hi:
        pivot = arr[hi]
        i = lo - 1
        for j in range(lo, hi):
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        arr[i + 1], arr[hi] = arr[hi], arr[i + 1]
        p = i + 1
        quicksort_inplace(arr, lo, p - 1)
        quicksort_inplace(arr, p + 1, hi)

def merge_sort_extra(arr: list[int]) -> list[int]:
    """O(n) auxiliary: creates new lists at every level."""
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    l, r = merge_sort_extra(arr[:mid]), merge_sort_extra(arr[mid:])
    return [x for pair in __import__('itertools').zip_longest(l, r)
            for x in pair if x is not None]  ## simplified illustrative merge

data = [10, 80, 30, 90, 40, 50, 70]
quicksort_inplace(data, 0, len(data) - 1)
print("QuickSort in-place:", data)
```



### 4. Work-Depth / Parallelisability

*Description:*
In multi-core and distributed systems, it is not enough for an algorithm to
be efficient sequentially--it must also expose *parallelism*. *Work* is the
total number of operations performed (equivalent to sequential time). *Depth*
(or span) is the length of the longest chain of sequential dependencies--i.e.,
the minimum time achievable even with unlimited processors. A low depth means
more opportunities to run tasks simultaneously. Algorithms like parallel prefix
sum (scan), parallel merge sort, and map-reduce patterns are designed with
this in mind. In systems work, parallelisability determines how well a solution
leverages modern hardware.



#### C: Parallel Sum Using POSIX Threads

```c
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

#define N (1 << 20)   // 1M elements
#define THREADS 4

long long arr[N];
long long partial[THREADS];

typedef struct { int tid, lo, hi; } Args;

void *partial_sum(void *arg) {
    Args *a = arg;
    long long s = 0;
    for (int i = a->lo; i < a->hi; i++) s += arr[i];
    partial[a->tid] = s;
    return NULL;
}

int main(void) {
    for (int i = 0; i < N; i++) arr[i] = 1;  // fill with 1s
    pthread_t tids[THREADS];
    Args args[THREADS];
    int chunk = N / THREADS;
    for (int t = 0; t < THREADS; t++) {
        args[t] = (Args){t, t * chunk, (t + 1) * chunk};
        pthread_create(&tids[t], NULL, partial_sum, &args[t]);
    }
    for (int t = 0; t < THREADS; t++) pthread_join(tids[t], NULL);
    long long total = 0;
    for (int t = 0; t < THREADS; t++) total += partial[t];
    printf("Parallel sum: %lld (expected %d)\n", total, N);
}
// Compile: gcc -O2 -pthread parallel_sum.c -o parallel_sum
```



#### Python: Parallel Sum Using multiprocessing

```python
from multiprocessing import Pool
import os

def partial_sum(chunk: list[int]) -> int:
    """Each worker sums its own chunk independently--O(n/p) work per core."""
    return sum(chunk)

def parallel_sum(data: list[int], workers: int = os.cpu_count()) -> int:
    """
    Work  = O(n)           -total operations across all cores.
    Depth = O(n/p + log p) -limited by largest chunk + reduction tree.
    """
    chunk_size = len(data) // workers
    chunks = [data[i * chunk_size:(i + 1) * chunk_size] for i in range(workers)]
    chunks[-1].extend(data[workers * chunk_size:])   # remainder to last chunk
    with Pool(workers) as pool:
        partials = pool.map(partial_sum, chunks)
    return sum(partials)

if __name__ == "__main__":
    data = list(range(1, 1_000_001))
    result = parallel_sum(data)
    print(f"Parallel sum: {result}")   # 500000500000
```



### 5. Cache Behaviour and Constant Factors

*Description:*
Asymptotic analysis tells us how an algorithm scales, but in real
hardware the *constant factors* and *memory access patterns* often
dominate. Modern CPUs are orders of magnitude faster than main memory;
cache misses can cost hundreds of cycles. Algorithms that access memory
*sequentially* (cache-friendly, exploiting spatial locality) dramatically
outperform those that jump around (cache-hostile). This is why matrix
multiplication done naively (row × column) is slower than the cache-blocked
version at large sizes, even though both are O(n³). In systems work,
tuning for cache is frequently the last-mile optimisation that determines
real-world throughput.



#### C: Row-Major (Cache-Friendly) vs Column-Major (Cache-Hostile) Matrix Sum

```c
#include <stdio.h>
#include <time.h>

#define N 1024
static int mat[N][N];

// Cache-FRIENDLY: sequential access along rows (stride-1 in memory)
long long row_major_sum(void) {
    long long s = 0;
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            s += mat[i][j];
    return s;
}

// Cache-HOSTILE: jumps N ints per step (stride-N in memory = cache misses)
long long col_major_sum(void) {
    long long s = 0;
    for (int j = 0; j < N; j++)
        for (int i = 0; i < N; i++)
            s += mat[i][j];
    return s;
}

int main(void) {
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++) mat[i][j] = i + j;

    clock_t t0 = clock(); long long r = row_major_sum(); clock_t t1 = clock();
    clock_t t2 = clock(); long long c = col_major_sum(); clock_t t3 = clock();

    printf("Row-major: %lld  in %.3f s\n", r, (double)(t1-t0)/CLOCKS_PER_SEC);
    printf("Col-major: %lld  in %.3f s\n", c, (double)(t3-t2)/CLOCKS_PER_SEC);
    // Row-major will be noticeably faster on most hardware
}
```



#### Python: Cache-Friendly Layout with NumPy (C-order vs Fortran-order)

```python
import numpy as np
import time

N = 2048

# C-order (row-major): default NumPy layout, cache-friendly row iteration
a_c = np.ones((N, N), dtype=np.int32, order='C')

# Fortran-order (column-major): cache-hostile for row iteration
a_f = np.ones((N, N), dtype=np.int32, order='F')

def time_row_sum(mat: np.ndarray, label: str) -> None:
    start = time.perf_counter()
    total = sum(mat[i].sum() for i in range(N))   # row-by-row
    elapsed = time.perf_counter() - start
    print(f"{label}: sum={total}, time={elapsed:.4f}s")

time_row_sum(a_c, "C-order (row-major, cache-friendly)")
time_row_sum(a_f, "F-order (col-major, cache-hostile )")
# C-order will typically run faster for row iteration
```



### 6. Stability, Simplicity, and Maintainability

*Description:*
A *stable* sort preserves the relative order of elements that compare
as equal--critical when sorting records by a secondary key, or in
multi-pass sorting pipelines. *Simplicity* means code that is easy
to understand, audit, and debug; a clever O(n log log n) algorithm
with 400 lines of tricky pointer arithmetic is often worse in practice
than a clean O(n log n) one. *Maintainability*--especially in production
codebases with rotating engineering teams--is the long-term cost of an
algorithmic choice. Overly complex algorithms introduce subtle bugs,
resist refactoring, and are expensive to extend. The best production
systems favour correctness and clarity first, then optimise only where
profiling reveals a bottleneck.



#### C: Stable Insertion Sort (simple, maintains relative order)

```c
#include <stdio.h>
#include <string.h>

typedef struct { char name[32]; int priority; } Task;

// Insertion sort is stable: equal-priority tasks keep their original order.
// Simple enough to audit in under a minute; suitable for small n in prod.
void insertion_sort_tasks(Task *tasks, int n) {
    for (int i = 1; i < n; i++) {
        Task key = tasks[i];
        int j = i - 1;
        // strictly less-than (not <=) preserves stability
        while (j >= 0 && tasks[j].priority > key.priority) {
            tasks[j + 1] = tasks[j];
            j--;
        }
        tasks[j + 1] = key;
    }
}

int main(void) {
    Task tasks[] = {
        {"render",   3},
        {"network",  1},
        {"log",      2},
        {"compress", 1},   // same priority as "network"--must stay after
        {"cleanup",  2},
    };
    int n = 5;
    insertion_sort_tasks(tasks, n);
    printf("Sorted tasks (stable):\n");
    for (int i = 0; i < n; i++)
        printf("  priority %d: %s\n", tasks[i].priority, tasks[i].name);
    // "network" appears before "compress"--stability preserved
}
```



#### Python: Stable sort with `sorted()` / `list.sort()` (Timsort)

```python
from dataclasses import dataclass

@dataclass
class Task:
    name: str
    priority: int

# Python's built-in sort (Timsort) is:
#   - Stable       : equal elements keep their original order
#   - O(n log n)   : optimal for comparison-based sorting
#   - Adaptive     : O(n) for nearly-sorted data (common in practice)
#   - Readable     : one line, well-tested, zero maintenance burden

tasks = [
    Task("render",   3),
    Task("network",  1),
    Task("log",      2),
    Task("compress", 1),   # same priority as "network"; must follow it
    Task("cleanup",  2),
]

sorted_tasks = sorted(tasks, key=lambda t: t.priority)

print("Sorted tasks (stable via Timsort):")
for t in sorted_tasks:
    print(f"  priority {t.priority}: {t.name}")
# "network" precedes "compress"--stability guaranteed by the language spec
```



### Summary Table

| Criterion | Key Question | Target |
|-----------|--------------|--------|
| *Correctness* | Right answer for *all* valid inputs? | Verified, edge-cases tested |
| *Time Complexity* | How does runtime scale with *n*? | Lowest feasible Big-O class |
| *Space Complexity* | How much memory is consumed? | Minimise auxiliary space |
| *Parallelisability* | Can work be split across cores/nodes? | Low depth, high parallelism |
| *Cache Behaviour* | Are memory accesses sequential? | Stride-1 / cache-friendly |
| *Stability & Simplicity* | Is it correct, readable, maintainable? | Simple, stable, auditable |

