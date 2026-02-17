
## Linear Search vs Binary Search

The best way to understand O(n) vs O(log n) is to measure it.

Both algorithms find a target in an array. But as the array grows,
their runtimes diverge dramatically:

| Array size (n) | Linear steps (worst) | Binary steps (worst) |
|----------------|----------------------|----------------------|
| 100 | 100 | 7 |
| 10,000 | 10,000 | 14 |
| 1,000,000 | 1,000,000 | 20 |
| 1,000,000,000 | 1,000,000,000 | 30 |

That's the power of O(log n). Let's prove it by measuring real time.



### Step 1: The Two Algorithms (Unmodified)

Here is the binary search you already have,
plus the equivalent linear search for comparison:

```c
/* linear_search: scan every element from left to right */
int linearSearch(int arr[], int n, int target) {
    for (int i = 0; i < n; i++) {
        if (arr[i] == target) {
            return i;
        }
    }
    return -1;
}

/* binarySearch: halve the search space each step (array must be sorted) */
int binarySearch(int arr[], int left, int right, int target) {
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) {
            return mid;
        }
        if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    return -1;
}
```



### Step 2: Adding a Timer

C gives us `clock()` from `<time.h>`. It returns a count of CPU "ticks".
Divide the difference by `CLOCKS_PER_SEC` to get seconds.

```c
#include <time.h>

clock_t start = clock();
/* ... code to time ... */
clock_t end = clock();

double elapsed_ms = 1000.0 * (end - start) / CLOCKS_PER_SEC;
printf("Time: %.4f ms\n", elapsed_ms);
```

For very fast operations, one run may read as 0 ms--the clock resolution isn't fine enough.
The fix is to *run the search many times in a loop* and divide the total time by the number of runs.



### Step 3: The Full Timing Program

Compile and run this. Try changing `N` to different values and see what happens.

```c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N        1000000   /* <-- try: 1000, 10000, 100000, 1000000, 10000000 */
#define REPEATS  1000      /* run each search this many times for stable timing */

/* ---------- algorithms ---------- */

int linearSearch(int arr[], int n, int target) {
    for (int i = 0; i < n; i++) {
        if (arr[i] == target) {
            return i;
        }
    }
    return -1;
}

int binarySearch(int arr[], int left, int right, int target) {
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) {
            return mid;
        }
        if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    return -1;
}

/* ---------- main ---------- */

int main(void) {
    /* build a sorted array: arr[i] = i*2 (0, 2, 4, 6, ...) */
    int *arr = malloc(N * sizeof(int));
    if (!arr) {
        fprintf(stderr, "malloc failed\n");
        return 1;
    }
    for (int i = 0; i < N; i++) {
        arr[i] = i * 2;
    }

    /* target the last element--worst case for linear, still O(log n) for binary */
    int target = (N - 1) * 2;

    clock_t start, end;
    double linear_ms, binary_ms;
    volatile int result; /* volatile: stops compiler optimising the loop away */

    /* ---- time linear search ---- */
    start = clock();
    for (int r = 0; r < REPEATS; r++) {
        result = linearSearch(arr, N, target);
    }
    end = clock();
    linear_ms = 1000.0 * (end - start) / CLOCKS_PER_SEC / REPEATS;

    /* ---- time binary search ---- */
    start = clock();
    for (int r = 0; r < REPEATS; r++) {
        result = binarySearch(arr, 0, N - 1, target);
    }
    end = clock();
    binary_ms = 1000.0 * (end - start) / CLOCKS_PER_SEC / REPEATS;

    /* ---- report ---- */
    printf("\n-- Search Timing Comparison --\n");
    printf("Array size (n)    : %d\n", N);
    printf("Target value      : %d (last element--worst case)\n", target);
    printf("Result index      : %d\n", result);
    printf("Repeats per timer : %d\n\n", REPEATS);

    printf("Linear search     : %.4f ms   O(n)\n",    linear_ms);
    printf("Binary search     : %.4f ms   O(log n)\n", binary_ms);

    if (binary_ms > 0) {
        printf("\nSpeedup           : %.1fx faster\n", linear_ms / binary_ms);
    }

    free(arr);
    return 0;
}
```



### Step 4: Compile and Run

```bash
gcc -O0 -o search_timing search_timing.c
./search_timing
```

> Use `-O0` to disable compiler optimisations! Otherwise the compiler
may eliminate loops it considers redundant, making the results misleading.

*Expected output (n = 1,000,000):*

```
-- Search Timing Comparison --
Array size (n)    : 1000000
Target value      : 1999998 (last element--worst case)
Result index      : 999999
Repeats per timer : 1000

Linear search     : 1.2483 ms   O(n)
Binary search     : 0.0003 ms   O(log n)

Speedup           : 4161.0x faster
```

The exact numbers depend on your machine, but the ratio is what matters.



### Step 5: The Experiment

Change `N` at the top of the file and re-run. Record your results in a table like this:

| n | Linear (ms) | Binary (ms) | Speedup |
|---|-------------|-------------|---------|
| 1,000 | ? | ? | ? |
| 10,000 | ? | ? | ? |
| 100,000 | ? | ? | ? |
| 1,000,000 | ? | ? | ? |
| 10,000,000 | ? | ? | ? |

*What to observe:*

- Each time you multiply n by 10, linear search time multiplies by roughly *10*--that's O(n).
- Each time you multiply n by 10, binary search time increases by roughly *3.3* *steps*
  (log₂(10) ≈ 3.32)--but in milliseconds it stays nearly flat because the overhead is so tiny.



### Step 6: Also Count the Steps

Timing is noisy. Step counts are exact.
Add a counter to each algorithm to see the difference directly:

```c
#include <stdio.h>
#include <stdlib.h>

#define N 1000000

int linearSearchCounted(int arr[], int n, int target, int *steps) {
    *steps = 0;
    for (int i = 0; i < n; i++) {
        (*steps)++;
        if (arr[i] == target) {
            return i;
        }
    }
    return -1;
}

int binarySearchCounted(int arr[], int left, int right, int target, int *steps) {
    *steps = 0;
    while (left <= right) {
        (*steps)++;
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) {
            return mid;
        }
        if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    return -1;
}

int main(void) {
    int *arr = malloc(N * sizeof(int));
    for (int i = 0; i < N; i++) arr[i] = i * 2;

    int target = (N - 1) * 2;   /* worst case: last element */
    int steps;

    linearSearchCounted(arr, N, target, &steps);
    printf("Linear search steps : %d\n", steps);

    binarySearchCounted(arr, 0, N - 1, target, &steps);
    printf("Binary search steps : %d\n", steps);
    printf("log2(%d) = %.1f\n", N, __builtin_log2(N));

    free(arr);
    return 0;
}
```

*Expected output:*

```
Linear search steps : 1000000
Binary search steps : 20
log2(1000000) = 19.9
```

Binary search used exactly *20 steps* to search through *1,000,000* elements.



### What the Numbers Tell You

The step counts make the theory tangible:

```
n = 1,000,000

Linear:  1,000,000 steps   <- visits every element
Binary:         20 steps   <- log₂(1,000,000) ≈ 19.9
```

Each time binary search runs, it asks:
*"Is the target in the left half or the right half?"*
It discards half the remaining elements with each answer.
After 20 such questions, only one element remains.

This is exactly why O(log n) is so powerful--and
why binary search is used everywhere from database
indexes to DNS lookups (to Git's `bisect` command).



### Rule to Remember

Binary search only works on a *sorted* array.
If the data is unsorted, you must sort
it first (O(n log n)), which only pays off i
you search many times.
The break-even is roughly:

```
sort cost + k × O(log n)  <  k × O(n)
```

For large n and many searches (large k),
binary search wins decisively.
