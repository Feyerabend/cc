#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/*
 * Knapsack Problem
 * 
 * This implementation demonstrates multiple algorithmic paradigms
 * for solving the 0/1 Knapsack.
 */

/* Fwd decl */
int max(int a, int b);
int knapsack_recursive(int W, int wt[], int val[], int n);
int knapsack_dp(int W, int wt[], int val[], int n, int **selected, int *selected_count);
void print_solution(int result, int *selected, int selected_count, int wt[], int val[], int W);
int validate_solution(int W, int wt[], int val[], int n, int result, int *selected, int selected_count);

/* Utility function to return maximum of two integers */
int max(int a, int b) {
    return (a > b) ? a : b;
}


/*
 * PARADIGM 1: DIVIDE AND CONQUER (Naive Recursion)
 * 
 * Algorithmic Paradigm: Divide and Conquer
 * - Recursively try including/excluding each item
 * - Exponential time due to overlapping subproblems
 * 
 * Time Complexity: O(2^n) - exponential
 * Space Complexity: O(n)  - recursion stack depth
 * 
 * Use: Education only - impractical for n > 25
 */
int knapsack_recursive(int W, int wt[], int val[], int n) {
    /* Base case: no items or no capacity */
    if (n == 0 || W == 0) {
        return 0;
    }
    
    /* If current item's weight exceeds capacity, skip it */
    if (wt[n-1] > W) {
        return knapsack_recursive(W, wt, val, n-1);
    }
    
    /* Return maximum of two cases:
     * 1. Include item n-1: add its value and solve for remaining
     * 2. Exclude item n-1: solve for remaining with same capacity */
    else {
        int include = val[n-1] + knapsack_recursive(W - wt[n-1], wt, val, n-1);
        int exclude = knapsack_recursive(W, wt, val, n-1);
        return max(include, exclude);
    }
}


/* 
 * PARADIGM 2: DYNAMIC PROGRAMMING (Tabulation - Bottom-Up)
 * 
 * Algorithmic Paradigm: Dynamic Programming (Bottom-Up)
 * - Builds solution table iteratively from base cases
 * - No recursion stack overhead
 * - Easy to backtrack for solution reconstruction
 * 
 * Time Complexity: O(n × W)  - polynomial
 * Space Complexity: O(n × W) - DP table
 * 
 * Use: Production code (standard approach)
 */
int knapsack_dp(int W, int wt[], int val[], int n, int **selected, int *selected_count) {
    int i, w;
    int **K;
    int max_value;
    
    /* Allocate memory for the DP table with error checking */
    K = (int **)malloc((n + 1) * sizeof(int *));
    if (K == NULL) {
        fprintf(stderr, "Error: Memory allocation failed for DP table\n");
        return -1;
    }
    
    for (i = 0; i <= n; i++) {
        K[i] = (int *)malloc((W + 1) * sizeof(int));
        if (K[i] == NULL) {
            fprintf(stderr, "Error: Memory allocation failed for DP table row %d\n", i);
            /* Free already allocated memory */
            for (int j = 0; j < i; j++) {
                free(K[j]);
            }
            free(K);
            return -1;
        }
    }
    
    /* Build table K[][] in bottom-up manner */
    for (i = 0; i <= n; i++) {
        for (w = 0; w <= W; w++) {
            if (i == 0 || w == 0) {
                /* Base case: no items or no capacity */
                K[i][w] = 0;
            }
            else if (wt[i-1] <= w) {
                /* Item fits: choose max of including or excluding */
                int include = val[i-1] + K[i-1][w-wt[i-1]];
                int exclude = K[i-1][w];
                K[i][w] = max(include, exclude);
            }
            else {
                /* Item doesn't fit: carry forward previous best */
                K[i][w] = K[i-1][w];
            }
        }
    }
    
    max_value = K[n][W];
    
    /* Backtrack to find the selected items */
    *selected = (int *)malloc(n * sizeof(int));
    if (*selected == NULL) {
        fprintf(stderr, "Error: Memory allocation failed for selected items\n");
        /* Free DP table */
        for (i = 0; i <= n; i++) {
            free(K[i]);
        }
        free(K);
        return -1;
    }
    
    *selected_count = 0;
    i = n;
    w = W;
    
    while (i > 0 && w > 0) {
        /* If value came from including item i */
        if (K[i][w] != K[i-1][w]) {
            (*selected)[*selected_count] = i - 1;  /* 0-indexed */
            (*selected_count)++;
            w -= wt[i-1];
        }
        i--;
    }
    
    /* Reverse the selected items array to get correct order */
    for (i = 0; i < *selected_count / 2; i++) {
        int temp = (*selected)[i];
        (*selected)[i] = (*selected)[*selected_count - 1 - i];
        (*selected)[*selected_count - 1 - i] = temp;
    }
    
    /* Free the DP table */
    for (i = 0; i <= n; i++) {
        free(K[i]);
    }
    free(K);
    
    return max_value;
}


/* 
 * UTILITY FUNCTIONS
 */

void print_solution(int result, int *selected, int selected_count, int wt[], int val[], int W) {
    int i;
    int total_weight = 0;
    int total_value = 0;
    
    printf("\nSOLUTION DETAILS:\n");
    printf("----------------------\n");
    printf("Maximum value: %d\n", result);
    printf("Number of items selected: %d\n", selected_count);
    printf("\nSelected items:\n");
    
    for (i = 0; i < selected_count; i++) {
        int idx = selected[i];
        printf("  Item %d: value=%d, weight=%d\n", idx, val[idx], wt[idx]);
        total_weight += wt[idx];
        total_value += val[idx];
    }
    
    printf("\nTotal weight: %d/%d\n", total_weight, W);
    printf("Total value: %d\n", total_value);
    printf("Capacity utilisation: %.1f%%\n", (100.0 * total_weight) / W);
}


int validate_solution(int W, int wt[], int val[], int n, int result, int *selected, int selected_count) {
    int i;
    int total_weight = 0;
    int total_value = 0;
    
    printf("\nVALIDATION:\n");
    printf("---------------\n");
    
    /* Check all items exist */
    for (i = 0; i < selected_count; i++) {
        if (selected[i] < 0 || selected[i] >= n) {
            printf("(-) Invalid item index: %d\n", selected[i]);
            return 0;
        }
    }
    
    /* Check weight and value */
    for (i = 0; i < selected_count; i++) {
        total_weight += wt[selected[i]];
        total_value += val[selected[i]];
    }
    
    if (total_weight > W) {
        printf("(-) Weight %d exceeds capacity %d\n", total_weight, W);
        return 0;
    }
    
    if (total_value != result) {
        printf("(-) Value mismatch: %d != %d\n", total_value, result);
        return 0;
    }
    
    printf("(+) Solution validated successfully\n");
    return 1;
}


/* 
 * MAIN FUNCTION
 */

int main() {
    /* Example problem */
    int val[] = {60, 100, 120};
    int wt[] = {10, 20, 30};
    int W = 50;
    int n = sizeof(val) / sizeof(val[0]);
    int *selected;
    int selected_count;
    int result;
    clock_t start, end;
    double cpu_time_used;
    
    printf("KNAPSACK PROBLEM - ENHANCED C VERSION\n\n");
    printf("Items: %d\n", n);
    printf("Capacity: %d\n", W);
    printf("Values: ");
    for (int i = 0; i < n; i++) {
        printf("%d%s", val[i], (i < n-1) ? ", " : "\n");
    }
    printf("Weights: ");
    for (int i = 0; i < n; i++) {
        printf("%d%s", wt[i], (i < n-1) ? ", " : "\n");
    }
    
    /*
     * 1. RECURSIVE APPROACH
     */
    printf("\n1. RECURSIVE APPROACH (Divide & Conquer)\n");
    printf("----------------------------------------\n");
    start = clock();
    result = knapsack_recursive(W, wt, val, n);
    end = clock();
    cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC * 1000;
    printf("Maximum value: %d\n", result);
    printf("Time: %.4f ms\n", cpu_time_used);
    printf("Note: O(2^n) - exponential time\n");
    
    /* 
     * 2. DYNAMIC PROGRAMMING APPROACH
     */
    printf("\n2. DYNAMIC PROGRAMMING (Tabulation)\n");
    printf("----------------------------------------\n");
    start = clock();
    result = knapsack_dp(W, wt, val, n, &selected, &selected_count);
    end = clock();
    cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC * 1000;
    
    if (result == -1) {
        fprintf(stderr, "Error: DP algorithm failed\n");
        return 1;
    }
    
    printf("Maximum value: %d\n", result);
    printf("Selected items (0-indexed): ");
    for (int i = 0; i < selected_count; i++) {
        printf("%d%s", selected[i], (i < selected_count-1) ? ", " : "\n");
    }
    printf("Time: %.4f ms\n", cpu_time_used);
    printf("Note: O(n x W) - polynomial time\n");
    
    /* Print detailed solution */
    print_solution(result, selected, selected_count, wt, val, W);
    
    /* Validate solution */
    validate_solution(W, wt, val, n, result, selected, selected_count);
    
    /* Free memory */
    free(selected);
    
    printf("\n\nDone.\n\n");
    
    return 0;
}
