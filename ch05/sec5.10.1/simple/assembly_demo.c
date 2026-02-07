/*
 * Simple example to demonstrate assembly-level optimisations
 * This shows how the same C code produces very different assembly
 * at different optimisation levels
 */

#include <stdio.h>

// Example 1: Simple arithmetic that shows constant folding
int constant_computation(void) {
    int a = 10;
    int b = 20;
    int c = 30;
    int result = (a + b) * c - 15;
    return result;
}

// Example 2: Loop that shows loop unrolling and strength reduction
int array_sum(int n) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += i;
    }
    return sum;
}

// Example 3: Shows common subexpression elimination
int geometric_calculation(int x, int y) {
    int area1 = x * y;
    int area2 = x * y + 10;
    int area3 = x * y - 5;
    return area1 + area2 + area3;
}

int main() {
    printf("Result 1: %d\n", constant_computation());
    printf("Result 2: %d\n", array_sum(100));
    printf("Result 3: %d\n", geometric_calculation(5, 7));
    return 0;
}
