#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <assert.h>
#include <string.h>

// Refinement type checking macros
#define REFINE_CHECK(condition, message) \
    do { \
        if (!(condition)) { \
            fprintf(stderr, "Refinement error: %s\n", message); \
            fprintf(stderr, "  at %s:%d in %s\n", __FILE__, __LINE__, __func__); \
            abort(); \
        } \
    } while(0)

// Common refinement predicates
#define IS_POSITIVE(x) ((x) > 0)
#define IS_NON_ZERO(x) ((x) != 0)
#define IS_IN_RANGE(x, min, max) ((x) >= (min) && (x) <= (max))
#define IS_NON_NULL(x) ((x) != NULL)
#define IS_NON_EMPTY(s) (IS_NON_NULL(s) && strlen(s) > 0)

// Type definitions with refinements encoded in names
typedef int positive_int;    // {x: int | x > 0}
typedef int non_zero_int;    // {x: int | x != 0}
typedef char* non_empty_str; // {s: string | len(s) > 0}

// Constructor functions that enforce refinements
positive_int make_positive(int value) {
    REFINE_CHECK(IS_POSITIVE(value), "Expected positive integer");
    return value;
}

non_zero_int make_non_zero(int value) {
    REFINE_CHECK(IS_NON_ZERO(value), "Expected non-zero integer");
    return value;
}

non_empty_str make_non_empty_str(char* str) {
    REFINE_CHECK(IS_NON_EMPTY(str), "Expected non-empty string");
    return str;
}

// Functions using refinement types
positive_int safe_divide(positive_int numerator, non_zero_int denominator) {
    // Refinements checked by caller through constructors
    // But we can add runtime assertions for extra safety
    REFINE_CHECK(IS_POSITIVE(numerator), "Numerator must be positive");
    REFINE_CHECK(IS_NON_ZERO(denominator), "Denominator must be non-zero");
    
    int result = numerator / denominator;
    
    // Post-condition: result should be non-negative for positive inputs
    REFINE_CHECK(result >= 0, "Result should be non-negative");
    
    return result;
}

size_t string_length(non_empty_str str) {
    REFINE_CHECK(IS_NON_EMPTY(str), "String must be non-empty");
    size_t len = strlen(str);
    REFINE_CHECK(len > 0, "Length must be positive");
    return len;
}

// Array bounds checking with refinement types
typedef struct {
    int* data;
    size_t length;
} array;

int array_get(array* arr, size_t index) {
    REFINE_CHECK(IS_NON_NULL(arr), "Array must not be null");
    REFINE_CHECK(IS_NON_NULL(arr->data), "Array data must not be null");
    REFINE_CHECK(index < arr->length, "Index out of bounds");
    return arr->data[index];
}

void array_set(array* arr, size_t index, int value) {
    REFINE_CHECK(IS_NON_NULL(arr), "Array must not be null");
    REFINE_CHECK(IS_NON_NULL(arr->data), "Array data must not be null");
    REFINE_CHECK(index < arr->length, "Index out of bounds");
    arr->data[index] = value;
}

// Example with percentage type
typedef float percentage; // {x: float | 0 <= x <= 100}

percentage make_percentage(float value) {
    REFINE_CHECK(IS_IN_RANGE(value, 0.0f, 100.0f), 
                 "Percentage must be between 0 and 100");
    return value;
}

void print_progress(percentage pct) {
    REFINE_CHECK(IS_IN_RANGE(pct, 0.0f, 100.0f), 
                 "Percentage must be between 0 and 100");
    printf("Progress: %.1f%%\n", pct);
}

int main() {
    printf("Testing refinement types in C...\n\n");
    
    // Valid operations
    positive_int a = make_positive(10);
    non_zero_int b = make_non_zero(2);
    printf("safe_divide(%d, %d) = %d\n", a, b, safe_divide(a, b));
    
    non_empty_str str = make_non_empty_str("hello");
    printf("string_length(\"%s\") = %zu\n", str, string_length(str));
    
    percentage pct = make_percentage(75.5);
    print_progress(pct);
    
    // Array example
    int data[] = {1, 2, 3, 4, 5};
    array arr = {data, 5};
    printf("array_get(arr, 2) = %d\n", array_get(&arr, 2));
    
    printf("\nTesting invalid operations...\n");
    
    // Uncomment to test error cases:
    // make_positive(-5);           // Will abort: not positive
    // make_non_zero(0);            // Will abort: is zero
    // make_non_empty_str("");      // Will abort: empty string
    // make_percentage(150.0);      // Will abort: out of range
    // array_get(&arr, 10);         // Will abort: out of bounds
    
    printf("All valid operations completed successfully!\n");
    
    return 0;
}
