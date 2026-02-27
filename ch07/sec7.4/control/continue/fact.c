#include <stdio.h>
#include <stdlib.h>

// Step struct to manage state and continuation
typedef struct Step {
    int n;  // current value of n
    long long accumulator;  // accumulator holding the intermediate factorial result
    struct Step* (*next)(struct Step*);  // pointer to the next step function
} Step;

// define the "step" function, which is responsible for the recursive logic
Step* step(Step* current) {
    if (current == NULL) {
        fprintf(stderr, "Error: current step is NULL\n");
        exit(1);  // exit if current is NULL
    }

    printf("Step: n = %d, accumulator = %lld\n", current->n, current->accumulator);

    // next step and continue the computation
    Step* next_step = malloc(sizeof(Step));
    if (next_step == NULL) {
        fprintf(stderr, "Memory allocation failed!\n");
        exit(1);  // exit program, if memory allocation fails
    }

    if (current->n == 0) {
        // base case: when n reaches 0, just copy the current values
        next_step->n = current->n;
        next_step->accumulator = current->accumulator;
        next_step->next = NULL;  // indicate this is the final step
        return next_step;
    } else {
        next_step->n = current->n - 1;  // decrement n
        next_step->accumulator = current->accumulator * current->n;  // update the accumulator
        next_step->next = step;  // set the next function to be this same step function
        return next_step;
    }
}

// factorial function using the trampoline pattern
long long factorial_trampoline(int n) {
    // input validation
    if (n < 0) {
        fprintf(stderr, "Error: factorial not defined for negative numbers\n");
        exit(1);
    }
    
    // special case for n = 0
    if (n == 0) {
        return 1;
    }

    // allocate the first step
    Step* current = malloc(sizeof(Step));
    if (current == NULL) {
        fprintf(stderr, "Memory allocation failed!\n");
        exit(1);  // exit the program, if memory allocation fails
    }

    current->n = n;
    current->accumulator = 1;
    current->next = step;  // first step

    printf("Starting factorial with n = %d\n", n);

    // iterate through the trampoline steps
    Step* next_step = NULL;  // pointer for next step
    long long result = 0;    // store result
    
    while (current != NULL && current->next != NULL) {
        printf("Current: n = %d, accumulator = %lld\n", current->n, current->accumulator);
        
        // get next step before freeing current step
        next_step = current->next(current);
        
        // free current step before moving to the next one
        free(current);
        current = next_step;
    }

    // store the final result and free last step
    if (current != NULL) {
        result = current->accumulator;
        free(current);
    }

    return result;
}

int main() {

    // different values
    int test_values[] = {0, 1, 5, 10};
    int num_tests = sizeof(test_values) / sizeof(test_values[0]);
    
    for (int i = 0; i < num_tests; i++) {
        int n = test_values[i];
        printf("\nCalculating factorial of %d:\n", n);
        long long result = factorial_trampoline(n);
        printf("Factorial of %d = %lld\n", n, result);
    }
    
    return 0;
}
