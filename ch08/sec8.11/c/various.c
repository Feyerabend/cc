/*
 * Hoare Logic Examples in C
 * 
 * This file contains annotated C code demonstrating various
 * theoretical aspects of Hoare Logic with runtime verification.
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <stdbool.h>

/*
 * Example 1: Weakest Precondition Demonstration
 * Shows how wp is computed backwards through a sequence
 */

void wp_example(void) {
    printf("\n-- Weakest Precondition Example --\n");
    
    /*
     * Goal: {?} x := 5; y := x + 1; z := y * 2 {z = 12}
     * 
     * Working backwards with wp:
     * wp(z := y * 2, z = 12) = (y * 2 = 12) = (y = 6)
     * wp(y := x + 1, y = 6) = (x + 1 = 6) = (x = 5)
     * wp(x := 5, x = 5) = (5 = 5) = true
     * 
     * Therefore: {true} S {z = 12}
     */
    
    int x, y, z;
    
    printf("Computing weakest precondition backwards:\n");
    printf("Target postcondition: z = 12\n");
    
    x = 5;
    printf("After x := 5, need wp(y := x + 1; z := y * 2, z = 12)\n");
    
    y = x + 1;
    printf("After y := x + 1 (y = %d), need wp(z := y * 2, z = 12)\n", y);
    printf("This requires y = 6, and we have y = %d\n", y);
    
    z = y * 2;
    printf("After z := y * 2, z = %d\n", z);
    
    assert(z == 12);
    printf("Postcondition verified: z = 12\n");
}

/*
 * Example 2: Strongest Postcondition Demonstration
 * Shows how sp is computed forwards through a sequence
 */

void sp_example(void) {
    printf("\n-- Strongest Postcondition Example --\n");
    
    /*
     * Goal: {x = 3} x := x + 1; y := x * 2 {?}
     * 
     * Working forwards with sp:
     * sp(x = 3, x := x + 1) = ∃x₀. (x₀ = 3 ∧ x = x₀ + 1) = (x = 4)
     * sp(x = 4, y := x * 2) = ∃x₀. (x₀ = 4 ∧ y = x₀ * 2) = (y = 8)
     * 
     * Therefore: {x = 3} S {y = 8}
     */
    
    int x = 3;
    printf("Starting with precondition: x = %d\n", x);
    
    printf("Computing strongest postcondition forwards:\n");
    printf("After x := x + 1:\n");
    x = x + 1;
    printf("  sp = (x = 4), actual x = %d\n", x);
    assert(x == 4);
    
    int y = x * 2;
    printf("After y := x * 2:\n");
    printf("  sp = (y = 8), actual y = %d\n", y);
    assert(y == 8);
    
    printf("Strongest postcondition: y = 8\n");
}

/*
 * Example 3: Loop Invariant with Array Sum
 * Demonstrates invariant preservation
 */

int array_sum_verified(int arr[], int n) {
    printf("\n-- Loop Invariant Example: Array Sum --\n");
    
    /*
     * Precondition: n = len(arr) ∧ n ≥ 0
     * Postcondition: result = Σ(arr[0..n-1])
     * 
     * Loop Invariant: I = (sum = Σ(arr[0..i-1]) ∧ 0 ≤ i ≤ n)
     */
    
    assert(n >= 0);
    
    int i = 0;
    int sum = 0;
    int expected_sum = 0;
    
    for (int k = 0; k < n; k++) {
        expected_sum += arr[k];
    }
    
    printf("Array: [");
    for (int k = 0; k < n; k++) {
        printf("%d%s", arr[k], k < n - 1 ? ", " : "");
    }
    printf("], expected sum = %d\n", expected_sum);
    
    printf("\nLoop execution with invariant checking:\n");
    
    while (i < n) {
        int partial_sum = 0;
        for (int k = 0; k < i; k++) {
            partial_sum += arr[k];
        }
        
        printf("Iteration %d: sum = %d, invariant check: sum = Σ(arr[0..%d]) = %d? %s\n", i, sum, i - 1, partial_sum, sum == partial_sum ? "✓" : "✗");
        assert(sum == partial_sum);
        assert(0 <= i && i <= n);
        
        sum = sum + arr[i];
        i = i + 1;
    }
    
    printf("\nLoop terminated: i = %d, sum = %d\n", i, sum);
    assert(i == n);
    assert(sum == expected_sum);
    
    printf("Postcondition verified: sum = %d\n", sum);
    return sum;
}

/*
 * Example 4: Termination with Variant Function
 * Demonstrates that a variant decreases
 */

void termination_example(void) {
    printf("\n-- Termination with Variant Function --\n");
    
    /*
     * Variant: V = x
     * Well-founded order: Natural numbers with <
     * 
     * Must prove: V decreases on each iteration
     */
    
    int x = 10;
    printf("Starting with x = %d (variant V = %d)\n", x, x);
    
    printf("\nLoop execution:\n");
    int iteration = 0;
    
    while (x > 0) {
        int old_variant = x;
        
        printf("Iteration %d: V = %d, condition (x > 0) = true\n", iteration, old_variant);
        
        x = x - 1;
        iteration++;
        
        int new_variant = x;
        printf("  After x := x - 1: V_new = %d < V_old = %d? %s\n", new_variant, old_variant, new_variant < old_variant ? "✓" : "✗");
        
        assert(new_variant < old_variant);
        assert(new_variant >= 0);
    }
    
    printf("\nLoop terminated after %d iterations\n", iteration);
    printf("Final: x = %d, variant V = %d (well-founded minimum reached)\n", x, x);
    printf("Termination proven via decreasing variant\n");
}

/*
 * Example 5: Assignment Axiom
 * Demonstrates Q[E/x] substitution
 */

void assignment_axiom_example(void) {
    printf("\n-- Assignment Axiom Example --\n");
    
    /*
     * Rule: {Q[E/x]} x := E {Q}
     * 
     * Example: {?} x := x + 1 {x > 5}
     * Q = (x > 5)
     * E = x + 1
     * Q[E/x] = (x + 1 > 5) = (x > 4)
     * 
     * Therefore: {x > 4} x := x + 1 {x > 5}
     */
    
    int x = 5;
    printf("Starting with x = %d\n", x);
    
    printf("Goal: {?} x := x + 1 {x > 5}\n");
    printf("Computing precondition via substitution:\n");
    printf("  Q = (x > 5)\n");
    printf("  E = x + 1\n");
    printf("  Q[E/x] = (x + 1 > 5) = (x > 4)\n");
    
    bool precondition = (x > 4);
    printf("Checking precondition: x > 4 = %d > 4? %s\n", 
           x, precondition ? "✓" : "✗");
    assert(precondition);
    
    x = x + 1;
    
    bool postcondition = (x > 5);
    printf("After assignment: x = %d\n", x);
    printf("Checking postcondition: x > 5 = %d > 5? %s\n",
           x, postcondition ? "✓" : "✗");
    assert(postcondition);
    
    printf("Assignment axiom verified\n");
}

/*
 * Example 6: Conditional Rule
 * Demonstrates both branches establishing same postcondition
 */

int conditional_example(int x) {
    printf("\n-- Conditional Rule Example --\n");
    
    /*
     * Rule: {P ∧ B} S1 {Q}    {P ∧ ¬B} S2 {Q}
     *       -----------------------------------
     *          {P} if B then S1 else S2 {Q}
     * 
     * Example: {x ∈ ℤ} if (x >= 0) then y := x else y := -x {y >= 0}
     */
    
    printf("Input: x = %d\n", x);
    
    int y;
    
    if (x >= 0) {
        printf("Branch: x >= 0 (true branch)\n");
        printf("  Precondition: x ∈ ℤ ∧ x >= 0\n");
        
        y = x;
        
        printf("  After y := x: y = %d\n", y);
        printf("  Postcondition: y >= 0? %s\n", y >= 0 ? "✓" : "✗");
        assert(y >= 0);

    } else {
        printf("Branch: x < 0 (false branch)\n");
        printf("  Precondition: x ∈ ℤ ∧ x < 0\n");
        
        y = -x;
        
        printf("  After y := -x: y = %d\n", y);
        printf("  Postcondition: y >= 0? %s\n", y >= 0 ? "✓" : "✗");
        assert(y >= 0);
    }
    
    printf("Both branches establish: y >= 0\n");
    printf("Conditional rule verified\n");
    
    return y;
}

/*
 * Example 7: Consequence Rule
 * Demonstrates strengthening precondition and weakening postcondition
 */

void consequence_rule_example(void) {
    printf("\n-- Consequence Rule Example --\n");
    
    /*
     * Rule: P' ⇒ P    {P} S {Q}    Q ⇒ Q'
     *       -------------------------------
     *               {P'} S {Q'}
     * 
     * Example: {x = 5} x := x + 1 {x > 0}
     * We have: {x = 5} x := x + 1 {x = 6}
     * And: (x = 5) ⇒ (x = 5)  [trivial]
     * And: (x = 6) ⇒ (x > 0)  [weakening]
     */
    
    int x = 5;
    printf("Stronger precondition: x = 5\n");
    assert(x == 5);
    
    x = x + 1;
    
    printf("After x := x + 1: x = %d\n", x);
    printf("Intermediate: x = 6? %s\n", x == 6 ? "✓" : "✗");
    assert(x == 6);
    
    printf("Weaker postcondition: x > 0? %s\n", x > 0 ? "✓" : "✗");
    assert(x > 0);
    
    printf("Implication: (x = 6) ⇒ (x > 0)? ✓\n");
    printf("Consequence rule verified\n");
}

/*
 * Example 8: Separation Logic - Pointer Disjointness
 * Demonstrates separating conjunction
 */

typedef struct {
    int value;
} Cell;

void separation_logic_example(void) {
    printf("\n-- Separation Logic Example --\n");
    
    /*
     * Assertion: x ↦ 3 * y ↦ 5
     * Means: Heap has exactly two cells, x and y are disjoint
     */
    
    Cell* x = (Cell*)malloc(sizeof(Cell));
    Cell* y = (Cell*)malloc(sizeof(Cell));
    
    printf("Allocated two cells:\n");
    printf("  x at address %p\n", (void*)x);
    printf("  y at address %p\n", (void*)y);
    
    bool disjoint = (x != y);
    printf("Disjointness check: x ≠ y? %s\n", disjoint ? "✓" : "✗");
    assert(disjoint);
    
    x->value = 3;
    y->value = 5;
    
    printf("After initialization:\n");
    printf("  x ↦ %d\n", x->value);
    printf("  y ↦ %d\n", y->value);
    
    printf("\nModifying *x should not affect *y (frame property):\n");
    x->value = 10;
    printf("After x->value := 10:\n");
    printf("  x ↦ %d (changed)\n", x->value);
    printf("  y ↦ %d (unchanged)? %s\n", y->value, y->value == 5 ? "✓" : "✗");
    assert(y->value == 5);
    
    printf("Separation property verified\n");
    
    free(x);
    free(y);
}

/*
 * Example 9: Frame Rule
 * Demonstrates local reasoning with disjoint resources
 */

void increment_cell(Cell* c) {
    c->value = c->value + 1;
}

void frame_rule_example(void) {
    printf("\n-- Frame Rule Example --\n");
    
    /*
     * Rule:     {P} S {Q}
     *       -----------------  [mod(S) ∩ fv(R) = ∅]
     *       {P * R} S {Q * R}
     * 
     * Example: {x ↦ v} increment(x) {x ↦ v+1}
     * Frame: R = y ↦ w
     * Therefore: {x ↦ v * y ↦ w} increment(x) {x ↦ v+1 * y ↦ w}
     */
    
    Cell* x = (Cell*)malloc(sizeof(Cell));
    Cell* y = (Cell*)malloc(sizeof(Cell));
    
    x->value = 5;
    y->value = 10;
    
    printf("Before: x ↦ %d, y ↦ %d\n", x->value, y->value);
    printf("Calling increment_cell(x)...\n");
    
    int y_before = y->value;
    
    increment_cell(x);
    
    printf("After: x ↦ %d, y ↦ %d\n", x->value, y->value);
    
    printf("Frame preserved: y unchanged? %s\n", y->value == y_before ? "✓" : "✗");
    assert(y->value == y_before);
    assert(x->value == 6);
    
    printf("Frame rule verified\n");
    
    free(x);
    free(y);
}

/*
 * Example 10: Binary Search with Loop Invariant
 * Demonstrates complex invariant in realistic code
 */

int binary_search_verified(int arr[], int n, int target) {
    printf("\n-- Binary Search with Invariant --\n");
    
    /*
     * Precondition: arr is sorted ∧ n = len(arr)
     * Postcondition: (result ≥ 0 ⇒ arr[result] = target) ∧
     *                (result < 0 ⇒ target ∉ arr)
     * 
     * Invariant: I = (target ∈ arr ⇒ target ∈ arr[left..right])
     */
    
    printf("Array: [");
    for (int i = 0; i < n; i++) {
        printf("%d%s", arr[i], i < n - 1 ? ", " : "");
    }
    printf("], searching for %d\n", target);
    
    for (int i = 1; i < n; i++) {
        assert(arr[i - 1] <= arr[i]);
    }
    printf("Precondition verified: array is sorted\n");
    
    int left = 0;
    int right = n - 1;
    
    printf("\nLoop execution:\n");
    int iteration = 0;
    
    while (left <= right) {
        printf("Iteration %d: searching in [%d..%d]\n", iteration, left, right);
        
        bool found_in_range = false;
        for (int i = left; i <= right; i++) {
            if (arr[i] == target) {
                found_in_range = true;
                break;
            }
        }
        
        bool target_exists = false;
        for (int i = 0; i < n; i++) {
            if (arr[i] == target) {
                target_exists = true;
                break;
            }
        }
        
        if (target_exists) {
            printf("  Invariant check: if target exists, it's in range? %s\n",
                   found_in_range ? "✓" : "✗");
            assert(found_in_range);
        }
        
        int mid = (left + right) / 2;
        printf("  mid = %d, arr[mid] = %d\n", mid, arr[mid]);
        
        if (arr[mid] == target) {
            printf("Found target at index %d\n", mid);
            assert(arr[mid] == target);
            printf("Postcondition verified\n");
            return mid;
        } else if (arr[mid] < target) {
            printf("  arr[mid] < target, searching right half\n");
            left = mid + 1;
        } else {
            printf("  arr[mid] > target, searching left half\n");
            right = mid - 1;
        }
        
        iteration++;
    }
    
    printf("Loop terminated without finding target\n");
    printf("Invariant at exit: left > right, range is empty\n");
    
    bool target_exists = false;
    for (int i = 0; i < n; i++) {
        if (arr[i] == target) {
            target_exists = true;
            break;
        }
    }
    
    printf("Target in array? %s\n", target_exists ? "yes" : "no");
    assert(!target_exists);
    printf("Postcondition verified: target not in array\n");
    
    return -1;
}

/*
 * Main: Run all examples
 */

int main(void) {
    printf("\nAdvanced Hoare Logic Examples in C\n");
    printf("Runtime Verification of Theoretical Concepts\n");
    printf("--------------------------------------------\n");
    
    wp_example();
    sp_example();
    
    int arr1[] = {1, 2, 3, 4, 5};
    array_sum_verified(arr1, 5);
    
    termination_example();
    assignment_axiom_example();
    conditional_example(10);
    conditional_example(-5);
    consequence_rule_example();
    separation_logic_example();
    frame_rule_example();
    
    int arr2[] = {1, 3, 5, 7, 9, 11, 13, 15};
    binary_search_verified(arr2, 8, 7);
    binary_search_verified(arr2, 8, 6);
    
    printf("\n\nDone.\n");
    
    return 0;
}
