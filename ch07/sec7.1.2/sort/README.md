
## Sorting & Complexity: O(n²) vs O(n log n)

*Merge sort, bubble sort, and insertion sort side by side: 
heory, derivations, and timing experiments that make the
gap hard to ignore.*

Sorting is the classic arena for comparing complexity classes because:

- Every algorithm is solving the exact same problem
- The input is easy to control (size, order, randomness)
- The performance gap between O(n²) and O(n log n) becomes enormous at scale

At `n = 100,000`:

```
Bubble sort comparisons:   ~5,000,000,000
Merge sort comparisons:    ~1,700,000
```

That is a *2,941× difference*--same problem, different algorithm, different complexity class.



### The Three Algorithms

#### Bubble Sort--O(n²)

Repeatedly steps through the array, compares adjacent elements,
and swaps them if out of order. The largest unsorted element "bubbles"
to its correct position each pass.

```c
void bubbleSort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {          /* n-1 passes */
        for (int j = 0; j < n - i - 1; j++) {  /* shrinks each pass */
            if (arr[j] > arr[j + 1]) {
                int temp  = arr[j];
                arr[j]    = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}
```



#### Insertion Sort: O(n²)

Builds the sorted array one element at a time. Takes the next unsorted
element and inserts it into its correct position among the already-sorted elements.

```c
void insertionSort(int arr[], int n) {
    for (int i = 1; i < n; i++) {       /* n-1 insertions */
        int key = arr[i];
        int j   = i - 1;
        while (j >= 0 && arr[j] > key) { /* shift elements right */
            arr[j + 1] = arr[j];
            j--;
        }
        arr[j + 1] = key;
    }
}
```



#### Merge Sort: O(n log n)

Divide the array in half recursively until each piece has one element, 
then merge pieces back together in sorted order.

```c
/* your merge() and mergeSort() from above--unchanged */
```



### Big O Derivations

#### Bubble Sort

Count the exact number of comparisons:

```
Pass 1: n-1 comparisons
Pass 2: n-2 comparisons
Pass 3: n-3 comparisons
...
Pass n-1: 1 comparison

Total = (n-1) + (n-2) + ... + 1
      = n(n-1)/2
      = n²/2 - n/2
```

Drop the lower-order term `n/2` and the constant `1/2`:

```
-> O(n²)
```

Every pair of elements is potentially compared.
With n elements there are n(n-1)/2 unique pairs.
That ceiling is unavoidable for bubble sort.



#### Insertion Sort

Best case: array is already sorted. The inner `while` never executes.

```
Each insertion: 1 comparison (key ≥ arr[j], stop immediately)
Total: n-1 comparisons  ->  O(n)
```

Worst case: array is reverse-sorted. Every insertion shifts everything:

```
Insertion 1: 1 comparison
Insertion 2: 2 comparisons
...
Insertion n-1: n-1 comparisons

Total = 1 + 2 + ... + (n-1) = n(n-1)/2  ->  O(n²)
```

Average case: each element is inserted halfway through the sorted portion:

```
Average shifts per insertion = i/2  for position i
Total ≈ n²/4  ->  O(n²)
```



#### Why O(n²) Gets Painful

Let's put real numbers on it.
Assume 10⁸ operations per second:

| n | O(n²) ops | O(n²) time | O(n log n) ops | O(n log n) time |
|---|-----------|------------|----------------|-----------------|
| 100 | 10,000 | 0.0001 ms | 664 | 0.0000 ms |
| 1,000 | 1,000,000 | 0.01 ms | 9,966 | 0.0001 ms |
| 10,000 | 100,000,000 | 1 ms | 132,877 | 0.001 ms |
| 100,000 | 10,000,000,000 | 100 ms | 1,660,964 | 0.017 ms |
| 1,000,000 | 10¹² | ~3 hours | 19,931,568 | 0.2 ms |

At n = 1,000,000, bubble sort would take roughly *3 hours*.
Merge sort: *0.2 ms*.



### The Math Behind Merge Sort

#### The Recurrence Relation

Let T(n) = time to sort n elements.

Merge sort does two things:
1. Recursively sorts two halves: `2 × T(n/2)`
2. Merges them back together: `O(n)`--scans both halves once

So:

```
T(n) = 2·T(n/2) + O(n)
T(1) = O(1)           ← base case: one element is already sorted
```

#### Solving by Expansion (Substitution)

Expand the recurrence step by step:

```
T(n) = 2·T(n/2)              + n
     = 2·[2·T(n/4) + n/2]    + n  =  4·T(n/4)  + 2n
     = 4·[2·T(n/8) + n/4]    + 2n =  8·T(n/8)  + 3n
     = 8·[2·T(n/16) + n/8]   + 3n = 16·T(n/16) + 4n
     ...
     = 2^k · T(n/2^k) + k·n
```

Stop when `n/2^k = 1`, i.e. `k = log₂(n)`:

```
T(n) = 2^(log₂n) · T(1)  +  log₂(n) · n
     = n · O(1)          +  n log₂(n)
     = O(n log n)
```

#### Visualising the Recursion Tree

```
Level 0:   [............n............]         work = n
                /                \
Level 1:  [....n/2....]    [....n/2....]       work = n/2 + n/2 = n
            /      \          /      \
Level 2: [n/4]   [n/4]     [n/4]    [n/4]      work = 4×(n/4) = n
          ...
Level k:  n single elements                    work = n×(1) = n
```

There are `log₂(n)` levels. Each level does exactly `n` total work (merging).

```
Total = n × log₂(n) = O(n log n)
```

This is why the shape is `n log n` and not `n²`.
The work at each level is constant (n), not growing.

#### The Master Theorem (Formal)

For recurrences of the form `T(n) = a·T(n/b) + f(n)`:

```
a = 2  (two subproblems)
b = 2  (each half the size)
f(n) = n  (merge cost)

log_b(a) = log₂(2) = 1
f(n) = n = n^1 = n^(log_b a)   ->  Case 2 of Master Theorem

∴  T(n) = O(n log n)  ok!
```



### Timing All Three

This self-contained program times all three sorts on the same randomly
generated array, at increasing sizes.

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ------- algorithms ------- */

void bubbleSort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int tmp = arr[j]; arr[j] = arr[j+1]; arr[j+1] = tmp;
            }
        }
    }
}

void insertionSort(int arr[], int n) {
    for (int i = 1; i < n; i++) {
        int key = arr[i], j = i - 1;
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j];
            j--;
        }
        arr[j + 1] = key;
    }
}

void merge(int arr[], int left, int mid, int right) {
    int n1 = mid - left + 1, n2 = right - mid;
    int *L = malloc(n1 * sizeof(int));
    int *R = malloc(n2 * sizeof(int));
    for (int i = 0; i < n1; i++) L[i] = arr[left + i];
    for (int j = 0; j < n2; j++) R[j] = arr[mid + 1 + j];
    int i = 0, j = 0, k = left;
    while (i < n1 && j < n2) arr[k++] = (L[i] <= R[j]) ? L[i++] : R[j++];
    while (i < n1) arr[k++] = L[i++];
    while (j < n2) arr[k++] = R[j++];
    free(L); free(R);
}

void mergeSort(int arr[], int left, int right) {
    if (left < right) {
        int mid = left + (right - left) / 2;
        mergeSort(arr, left, mid);
        mergeSort(arr, mid + 1, right);
        merge(arr, left, mid, right);
    }
}

/* ------- helpers ------- */

/* fill array with random integers */
void randomFill(int arr[], int n, unsigned int seed) {
    srand(seed);
    for (int i = 0; i < n; i++) arr[i] = rand();
}

/* time a sort function in milliseconds */
double timeSortMs(void (*sortFn)(int[], int), int n, unsigned int seed) {
    int *arr = malloc(n * sizeof(int));
    randomFill(arr, n, seed);

    clock_t start = clock();
    sortFn(arr, n);
    clock_t end = clock();

    free(arr);
    return 1000.0 * (end - start) / CLOCKS_PER_SEC;
}

/* separate wrapper needed--mergeSort has a different signature */
static int ms_n;
void mergeSortWrapper(int arr[], int n) {
    mergeSort(arr, 0, n - 1);
}

/* ------- main ------- */

int main(void) {
    /* << change these sizes to explore >> */
    int sizes[] = {1000, 5000, 10000, 50000, 100000};
    int num_sizes = sizeof(sizes) / sizeof(sizes[0]);
    unsigned int seed = 42;

    printf("%-10s  %12s  %15s  %12s\n",
           "n", "Bubble (ms)", "Insertion (ms)", "Merge (ms)");
    printf("%-10s  %12s  %15s  %12s\n",
           "----------", "------------", "---------------", "------------");

    for (int i = 0; i < num_sizes; i++) {
        int n = sizes[i];

        double t_bubble    = timeSortMs(bubbleSort,       n, seed);
        double t_insertion = timeSortMs(insertionSort,    n, seed);
        double t_merge     = timeSortMs(mergeSortWrapper, n, seed);

        printf("%-10d  %12.3f  %15.3f  %12.3f\n",
               n, t_bubble, t_insertion, t_merge);
    }

    return 0;
}
```

#### Compile and run

```bash
gcc -O0 -o sort_timing sort_timing.c
./sort_timing
```

#### Expected output

```
n              Bubble (ms)    Insertion (ms)    Merge (ms)
----------    ------------    ---------------   ------------
1000               0.843              0.241          0.112
5000              20.614              5.832          0.631
10000             82.301             23.614          1.341
50000           2053.442            589.203          7.812
100000          8211.774           2361.445         16.203
```

Notice:
- Bubble and Insertion *quadruple* each time n doubles (4× is the signature of O(n²))
- Merge slightly *more than doubles*--just over 2× (2× + a little for the log factor)
- By n = 100,000, merge sort is *500× faster* than bubble sort



### Experiments to Try

#### Experiment A: Verify the quadrupling law

Double n repeatedly and record the time ratio for bubble sort:

| n | Bubble time (ms) | Ratio to previous |
|---|---|---|
| 5,000 | ? |--|
| 10,000 | ? | ≈ 4× |
| 20,000 | ? | ≈ 4× |
| 40,000 | ? | ≈ 4× |

If the ratio consistently approaches 4, that's direct evidence of O(n²).
For merge sort, the ratio should approach just above 2--O(n log n).



#### Experiment B: Count comparisons, not time

Add a counter to remove timing noise entirely:

```c
long long bubble_comparisons = 0;
long long merge_comparisons  = 0;

/* in bubbleSort inner loop: */
bubble_comparisons++;
if (arr[j] > arr[j + 1]) { ... }

/* in merge() comparison: */
merge_comparisons++;
if (L[i] <= R[j]) { ... }
```

Then compute the theoretical values and compare:

```c
printf("Bubble actual:      %lld\n", bubble_comparisons);
printf("Bubble theoretical: %lld   (n²/2 - n/2)\n", (long long)(n*n/2 - n/2));

printf("Merge  actual:      %lld\n", merge_comparisons);
printf("Merge  theoretical: ~%lld  (n * log2(n))\n",
       (long long)(n * (int)ceil(log2(n))));
```



#### Experiment C: Best case for insertion sort

Insertion sort is *O(n) on a sorted array*. Test this:

```c
/* fill with already-sorted data */
for (int i = 0; i < n; i++) arr[i] = i;

/* time insertionSort vs mergeSort on this */
```

You should find insertion sort is *faster* than merge sort on already-sorted
data--because its inner `while` never executes. This is why insertion sort
is used for small subarrays inside real-world implementations of merge sort
and quicksort (the threshold is typically n ≤ 10–32).



#### Experiment D: Nearly sorted data

```c
/* nearly sorted: swap 1% of random pairs */
for (int i = 0; i < n; i++) arr[i] = i;
srand(42);
for (int i = 0; i < n / 100; i++) {
    int a = rand() % n, b = rand() % n;
    int tmp = arr[a]; arr[a] = arr[b]; arr[b] = tmp;
}
```

Record times for all three sorts. Insertion sort should stay near O(n);
bubble sort should still be near O(n²); merge sort stays O(n log n) regardless.
This illustrates why knowing your data distribution matters.



#### Experiment E: Reverse-sorted (worst case for both O(n²) sorts)

```c
for (int i = 0; i < n; i++) arr[i] = n - i;  /* n, n-1, ..., 2, 1 */
```

Both bubble and insertion sort hit their absolute worst case here. Merge sort
is completely unaffected--its time is identical regardless of input order.



### When O(n²) Wins

The raw complexity class isn't the whole story. Insertion sort often beats
merge sort for small n because:
- *No memory allocation*--merge sort allocates O(n) temporary arrays
- *Cache friendliness*--insertion sort accesses memory sequentially
- *Lower constant factor*--fewer function calls, no malloc overhead

The crossover point is typically around n = 10–32. Real sorting libraries
exploit this:

```
Tim sort  (Python, Java):  merge sort + insertion sort for small runs
Intro sort (C++ std::sort): quicksort + heapsort + insertion sort
```

At n ≤ 16, insertion sort usually wins. At n = 1,000,000, merge sort wins
by thousands of times. Complexity class matters most at scale.



### The Theoretical Lower Bound

Can we do better than O(n log n) for sorting?

*For comparison-based sorting: no.*

Any algorithm that sorts by comparing elements must
make at least `log₂(n!)` comparisons in the worst case.
By Stirling's approximation:

```
log₂(n!) ≈ n·log₂(n) - n·log₂(e)  ≈  O(n log n)
```

*Why:* there are n! possible orderings of n elements. Each comparison
eliminates at most half of the remaining possibilities. To distinguish between
n! orderings, you need at least `log₂(n!)` comparisons--a decision tree of
at least that depth. This is a mathematical proof that no comparison-based
sort can ever beat O(n log n) in the worst case.

Merge sort and heapsort achieve this bound.
They are *asymptotically optimal*.

*Can we beat O(n log n) at all?* Yes--but only by not comparing elements:
- *Counting sort:* O(n + k) where k is the value range
- *Radix sort:* O(n·d) where d is the number of digits
- *Bucket sort:* O(n) average for uniformly distributed floats

These work by exploiting structure in the values themselves, not just their
relative order. They are not general-purpose--counting sort breaks down if
k = 10⁹.



### Summary

```
Algorithm       Best        Average     Worst       Space
---------------------------------------------------------
Bubble sort     O(n)        O(n²)       O(n²)       O(1)
Insertion sort  O(n)        O(n²)       O(n²)       O(1)
Merge sort      O(n log n)  O(n log n)  O(n log n)  O(n)
```

The defining difference: merge sort's worst case is the same as its best
case. It is immune to adversarial input. Bubble and insertion sort can be
made to hit O(n²) trivially (just reverse-sort the input).

That consistency--guaranteed O(n log n) regardless of data--is what makes
merge sort and its relatives the workhorses of real-world sorting.
