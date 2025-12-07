/*
 * Compiler Optimisation Examples
 * 
 * Compile with different optimisation levels:
 * gcc -O0 compiler_opt.c -o prog_O0  (No optimisation)
 * gcc -O1 compiler_opt.c -o prog_O1  (Basic optimisation)
 * gcc -O2 compiler_opt.c -o prog_O2  (Recommended level)
 * gcc -O3 compiler_opt.c -o prog_O3  (Aggressive optimisation)
 * gcc -Os compiler_opt.c -o prog_Os  (Optimise for size)
 * gcc -Ofast compiler_opt.c -o prog_Ofast (Fastest, may break standards)
 * 
 * Additional useful flags:
 * -march=native    : Optimise for current CPU architecture
 * -funroll-loops   : Unroll loops for better performance
 * -finline-functions : Inline functions aggressively
 * -ffast-math      : Fast floating point (may reduce precision)
 * -flto            : Link-time optimisation
 */

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

// Example 1: Loop optimisation
void loop_example(int *arr, int size) {
    // Compiler can vectorise, unroll, and optimise this loop
    for (int i = 0; i < size; i++) {
        arr[i] = arr[i] * 2 + 1;
    }
}

// Example 2: Function inlining
inline int add(int a, int b) {
    return a + b;
}

// Example 3: Constant propagation
int constant_folding_example() {
    int a = 5;
    int b = 10;
    int c = a + b;      // Compiler can compute at compile time
    int d = c * 2;      // Also compile-time computable
    return d;
}

// Example 4: Dead code elimination
int dead_code_example(int x) {
    int y = 100;        // Dead code: never used
    int z = x * 2;
    int w = 50;         // Dead code: never used
    return z;
}

// Example 5: Common subexpression elimination
int cse_example(int a, int b) {
    int x = a * b + a * b;  // Compiler optimises to: temp = a*b; x = temp + temp
    return x;
}

// Example 6: Loop unrolling demonstration
void loop_unroll_example(int *arr, int size) {
    // At -O2/-O3, compiler may unroll this automatically
    for (int i = 0; i < size; i++) {
        arr[i] += 1;
    }
}

// Manual loop unrolling for comparison
void loop_unroll_manual(int *arr, int size) {
    int i;
    // Process 4 elements at a time
    for (i = 0; i < size - 3; i += 4) {
        arr[i] += 1;
        arr[i+1] += 1;
        arr[i+2] += 1;
        arr[i+3] += 1;
    }
    // Handle remaining elements
    for (; i < size; i++) {
        arr[i] += 1;
    }
}

// Example 7: Strength reduction
int strength_reduction_example(int x) {
    // Compiler converts multiplication by power of 2 to shift
    return x * 8;  // Becomes: x << 3
}

// Example 8: Branch prediction hints (GCC specific)
int branch_prediction_example(int x) {
    // Help branch predictor
    if (__builtin_expect(x > 0, 1)) {  // Expect this branch to be taken
        return x * 2;
    } else {
        return x;
    }
}

// Example 9: Restrict keyword for pointer aliasing
void pointer_aliasing(int * restrict a, int * restrict b, int size) {
    // 'restrict' tells compiler pointers don't alias
    // Enables more aggressive optimisation
    for (int i = 0; i < size; i++) {
        a[i] = b[i] * 2;
    }
}

// Example 10: Memory alignment for SIMD
typedef struct {
    float data[1000];
} __attribute__((aligned(32))) AlignedArray;

void simd_friendly_operation(AlignedArray *arr) {
    // Aligned data allows compiler to use SIMD instructions
    for (int i = 0; i < 1000; i++) {
        arr->data[i] *= 2.0f;
    }
}

// Benchmark function
double benchmark(void (*func)(int*, int), int *arr, int size, const char *name) {
    clock_t start = clock();
    
    for (int iter = 0; iter < 1000; iter++) {
        func(arr, size);
    }
    
    clock_t end = clock();
    double time_taken = (double)(end - start) / CLOCKS_PER_SEC;
    printf("%s: %.6f seconds\n", name, time_taken);
    return time_taken;
}

int main() {
    printf("-- Compiler Optimisation Examples --\n\n");
    
    printf("Compile this program with different optimisation levels:\n");
    printf("  gcc -O0 : No optimisation\n");
    printf("  gcc -O2 : Recommended (default for most projects)\n");
    printf("  gcc -O3 : Aggressive optimisation\n");
    printf("  gcc -march=native : CPU-specific optimisations\n\n");
    
    const int size = 1000000;
    int *arr = (int*)malloc(size * sizeof(int));
    
    // Init array
    for (int i = 0; i < size; i++) {
        arr[i] = i;
    }
    
    printf("Running benchmarks (1000 iterations each)..\n\n");
    
    double time1 = benchmark(loop_unroll_example, arr, size, "Auto loop");
    double time2 = benchmark(loop_unroll_manual, arr, size, "Manual unroll");
    
    printf("\nAt -O0: Manual unrolling is faster\n");
    printf("At -O2/-O3: Compiler does it automatically\n\n");
    
    printf("-- Compiler Optimisations --\n");
    printf("1. Loop unrolling - Reduces loop overhead\n");
    printf("2. Function inlining - Eliminates call overhead\n");
    printf("3. Constant folding - Computes constants at compile time\n");
    printf("4. Dead code elimination - Removes unused code\n");
    printf("5. Common subexpression elimination - Reuses calculations\n");
    printf("6. Strength reduction - Replaces expensive ops with cheaper ones\n");
    printf("7. Vectorisation (SIMD) - Process multiple data in parallel\n");
    printf("8. Register allocation - Keeps hot data in registers\n");
    printf("9. Instruction scheduling - Reorders for CPU pipeline\n");
    printf("10. Link-time optimisation (LTO) - Optimises across files\n\n");
    
    printf("-- Optimisation Flags Summary --\n");
    printf("-O0: Debug builds, no optimisation\n");
    printf("-O1: Basic optimisations, fast compile\n");
    printf("-O2: Recommended for production (good balance)\n");
    printf("-O3: Aggressive, may increase binary size\n");
    printf("-Os: Optimise for smaller binary size\n");
    printf("-Ofast: Maximum speed (may break IEEE compliance)\n");
    printf("-march=native: Use CPU-specific instructions\n");
    printf("-flto: Link-time optimisation across all files\n");
    printf("-fprofile-generate/-fprofile-use: Profile-guided optimisation\n");
    
    free(arr);
    return 0;
}
