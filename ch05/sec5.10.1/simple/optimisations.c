/*
 * Compiler Optimisation Examples in C
 * Demonstrates low-level optimisation techniques
 * Compile with different optimisation levels to see the difference:
 *   gcc -O0 optimizations.c -o opt_O0    # No optimisation
 *   gcc -O2 optimizations.c -o opt_O2    # Medium optimisation
 *   gcc -O3 optimizations.c -o opt_O3    # Aggressive optimisation
 */

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

#define ARRAY_SIZE 10000
#define ITERATIONS 100000

/* 
 * Example 1: REGISTER ALLOCATION
 * Frequent variable access - compiler will try to keep in registers
 */

// Unoptimised: Many memory accesses
int sum_with_memory_access(int *arr, int size) {
    int sum = 0;
    int *temp_ptr = arr;  // Extra pointer variable
    int count = 0;
    
    while (count < size) {
        sum = sum + temp_ptr[count];
        count = count + 1;
    }
    return sum;
}

// Optimised: Minimal variables, easier to keep in registers
int sum_optimized(int *arr, int size) {
    int sum = 0;
    for (int i = 0; i < size; i++) {
        sum += arr[i];
    }
    return sum;
}


/*
 * Example 2: LOOP UNROLLING
 * Reduces branch overhead and enables better pipelining
 */

// Normal loop
void copy_array_normal(int *dest, int *src, int size) {
    for (int i = 0; i < size; i++) {
        dest[i] = src[i];
    }
}

// Manually unrolled loop (compiler often does this with -O3)
void copy_array_unrolled(int *dest, int *src, int size) {
    int i;
    // Process 4 elements at a time
    for (i = 0; i < size - 3; i += 4) {
        dest[i]     = src[i];
        dest[i + 1] = src[i + 1];
        dest[i + 2] = src[i + 2];
        dest[i + 3] = src[i + 3];
    }
    // Handle remaining elements
    for (; i < size; i++) {
        dest[i] = src[i];
    }
}


/* Example 3: BRANCH PREDICTION & ELIMINATION
 * Predictable branches vs unpredictable branches
 */

// Unpredictable branches (bad for CPU pipeline)
int sum_with_conditional_unpredictable(int *arr, int size) {
    int sum = 0;
    for (int i = 0; i < size; i++) {
        if (arr[i] % 2 == 0) {  // Unpredictable branch
            sum += arr[i];
        }
    }
    return sum;
}

// Branch-free version using arithmetic
int sum_with_conditional_branchless(int *arr, int size) {
    int sum = 0;
    for (int i = 0; i < size; i++) {
        // If even: (arr[i] % 2 == 0) evaluates to 1, else 0
        // Multiply by arr[i] to conditionally add
        int is_even = (arr[i] & 1) == 0;  // Bitwise AND faster than modulo
        sum += arr[i] * is_even;
    }
    return sum;
}


/*
 * Example 4: POINTER ALIASING & RESTRICT KEYWORD
 * Helps compiler understand pointers don't overlap
 */

// Without restrict - compiler must assume pointers might alias
void add_arrays_normal(int *a, int *b, int *result, int size) {
    for (int i = 0; i < size; i++) {
        result[i] = a[i] + b[i];
    }
}

// With restrict - compiler knows pointers don't overlap, enables better optimisation
void add_arrays_restrict(int *restrict a, int *restrict b, int *restrict result, int size) {
    for (int i = 0; i < size; i++) {
        result[i] = a[i] + b[i];
    }
}


/* 
 * Example 5: MEMORY ALIGNMENT & PADDING
 * Proper alignment improves memory access speed
 */

// Unaligned struct (likely 13 bytes with padding)
struct UnalignedData {
    char flag;      // 1 byte
    int value;      // 4 bytes (probably padded to align)
    double data;    // 8 bytes
};

// Aligned struct (reordered for better packing)
struct AlignedData {
    double data;    // 8 bytes (largest first)
    int value;      // 4 bytes
    char flag;      // 1 byte
    // Total: 16 bytes with padding, but better cache line usage
};


/* 
 * Example 6: INLINING
 * Small frequently-called functions
 */

// Small function that benefits from inlining
inline int max(int a, int b) {
    return (a > b) ? a : b;
}

// Using the inline function
int find_max_in_array(int *arr, int size) {
    int maximum = arr[0];
    for (int i = 1; i < size; i++) {
        maximum = max(maximum, arr[i]);  // Will be inlined by compiler
    }
    return maximum;
}


/* BENCHMARK UTIL */

double benchmark_function(void (*func)(int*, int*, int), int *input, int *output, int size) {
    clock_t start = clock();
    
    for (int i = 0; i < ITERATIONS; i++) {
        func(output, input, size);
    }
    
    clock_t end = clock();
    return ((double)(end - start)) / CLOCKS_PER_SEC * 1000.0;  // Return milliseconds
}



int main() {
    printf("  COMPILER OPTIMIZATION EXAMPLES IN C\n");
    
    // Setup test data
    int *test_array = (int*)malloc(ARRAY_SIZE * sizeof(int));
    int *dest_array = (int*)malloc(ARRAY_SIZE * sizeof(int));
    
    // Init with random data
    srand(42);
    for (int i = 0; i < ARRAY_SIZE; i++) {
        test_array[i] = rand() % 100;
    }
    
    /* Example 1: Register Allocation */
    printf("Example 1: REGISTER ALLOCATION\n");
    printf("------------------------------\n");
    
    clock_t start = clock();
    for (int i = 0; i < ITERATIONS; i++) {
        sum_with_memory_access(test_array, ARRAY_SIZE);
    }
    double time1 = ((double)(clock() - start)) / CLOCKS_PER_SEC * 1000.0;
    
    start = clock();
    for (int i = 0; i < ITERATIONS; i++) {
        sum_optimized(test_array, ARRAY_SIZE);
    }
    double time2 = ((double)(clock() - start)) / CLOCKS_PER_SEC * 1000.0;
    
    printf("Many variables (memory access):  %.3f ms\n", time1);
    printf("Optimised (register friendly):   %.3f ms\n", time2);
    printf("Speedup:                         %.2fx\n\n", time1/time2);
    
    
    /* Example 2: Loop Unrolling */
    printf("Example 2: LOOP UNROLLING\n");
    printf("-------------------------\n");
    
    double time_normal = benchmark_function(copy_array_normal, test_array, dest_array, ARRAY_SIZE);
    double time_unrolled = benchmark_function(copy_array_unrolled, test_array, dest_array, ARRAY_SIZE);
    
    printf("Normal loop:                     %.3f ms\n", time_normal);
    printf("Unrolled loop (4x):              %.3f ms\n", time_unrolled);
    printf("Speedup:                         %.2fx\n", time_normal/time_unrolled);
    printf("Note: Compiler at -O3 often does this automatically\n\n");
    
    
    /* Example 3: Branch Prediction */
    printf("Example 3: BRANCH PREDICTION\n");
    printf("----------------------------\n");
    
    start = clock();
    int sum1 = 0;
    for (int i = 0; i < ITERATIONS; i++) {
        sum1 += sum_with_conditional_unpredictable(test_array, ARRAY_SIZE);
    }
    double time_branch = ((double)(clock() - start)) / CLOCKS_PER_SEC * 1000.0;
    
    start = clock();
    int sum2 = 0;
    for (int i = 0; i < ITERATIONS; i++) {
        sum2 += sum_with_conditional_branchless(test_array, ARRAY_SIZE);
    }
    double time_branchless = ((double)(clock() - start)) / CLOCKS_PER_SEC * 1000.0;
    
    printf("With branches:                   %.3f ms\n", time_branch);
    printf("Branch-free (arithmetic):        %.3f ms\n", time_branchless);
    printf("Speedup:                         %.2fx\n", time_branch/time_branchless);
    printf("Note: Results match: sum1=%d, sum2=%d\n\n", sum1, sum2);
    
    
    /* Struct size comparison */
    printf("Example 4: MEMORY ALIGNMENT\n");
    printf("---------------------------\n");
    printf("Unaligned struct size:           %zu bytes\n", sizeof(struct UnalignedData));
    printf("Aligned struct size:             %zu bytes\n", sizeof(struct AlignedData));
    printf("Note: Proper alignment reduces padding and improves cache usage\n\n");
    
    
    /* Compilation tips */
    printf("COMPILATION OPTIMISATION LEVELS\n");
    printf("===============================\n");
    printf("-O0: No optimisation (debugging)\n");
    printf("-O1: Basic optimisations (constant folding, dead code elimination)\n");
    printf("-O2: Moderate optimisations (loop optimization, register allocation)\n");
    printf("-O3: Aggressive (auto-vectorisation, loop unrolling, inlining)\n");
    printf("-Os: Optimise for size\n");
    printf("-Ofast: -O3 + fast math (may break IEEE compliance)\n\n");
    
    printf("To see assembly output:\n");
    printf("  gcc -S -O0 optimisations.c -o output_O0.s\n");
    printf("  gcc -S -O3 optimisations.c -o output_O3.s\n");
    printf("  diff output_O0.s output_O3.s  # See the difference!\n\n");
    
    printf("Try this:\n");
    printf("  gcc -O0 optimisations.c -o opt_O0 && time ./opt_O0\n");
    printf("  gcc -O3 optimisations.c -o opt_O3 && time ./opt_O3\n");
    printf("===============================\n");
    
    free(test_array);
    free(dest_array);
    
    return 0;
}


/* 
 * Assembly comparison example
 * 
 * Simple function to see optimisation in assembly:
 * 
 * int compute(int x) {
 *     int result = x * 2 + 5;
 *     return result;
 * }
 * 
 * With -O0 (no optimisation):
 *   - Multiple mov instructions
 *   - Stack usage for local variables
 *   - imul for multiplication
 * 
 * With -O3 (optimised):
 *   - lea instruction (address calculation does add+shift in one go)
 *   - No stack usage
 *   - Entire function might be inlined away
 * 
 * Compile and compare:
 *   gcc -S -O0 -c optimisations.c -o O0.s
 *   gcc -S -O3 -c optimisations.c -o O3.s
 */
