#include <stdio.h>

typedef struct {
    void (*operation)(int, int);  // pointer to function that takes two int parameters
    char* description;            // description of operation
} Operation;

// wrapper functions for the arithmetic operations
void add_wrapper(int a, int b) {
    printf("Result: %d\n", a + b);
}

void subtract_wrapper(int a, int b) {
    printf("Result: %d\n", a - b);
}

void multiply_wrapper(int a, int b) {
    printf("Result: %d\n", a * b);
}

void divide_wrapper(int a, int b) {
    if (b != 0) {
        printf("Result: %d\n", a / b);
    } else {
        printf("Error: Division by zero!\n");
    }
}

// dispatch based on operation structure
void dispatch(Operation operations[], int operation_code, int a, int b) {
    int num_operations = 4; // number of operations explicitly
    
    if (operation_code >= 0 && operation_code < num_operations) {
        printf("Operation: %s\n", operations[operation_code].description);
        operations[operation_code].operation(a, b);  // call corresponding function with parameters
    } else {
        printf("Unknown operation.\n");
    }
}

int main() {
    // define an array of operation structs
    // with function pointers and descriptions
    // it can be defined at compile time,
    // or with some changes, it can be
    // initialised at runtime
    Operation operations[] = {
        { add_wrapper,      "Addition" },
        { subtract_wrapper, "Subtraction" },
        { multiply_wrapper, "Multiplication" },
        { divide_wrapper,   "Division" }
    };

    // Test with actual values
    int a = 10, b = 5;
    
    dispatch(operations, 0, a, b); // Perform addition
    dispatch(operations, 1, a, b); // Perform subtraction
    dispatch(operations, 2, a, b); // Perform multiplication
    dispatch(operations, 3, a, b); // Perform division
    dispatch(operations, 5, a, b); // Unknown operation

    return 0;
}

// This code defines a simple dispatch mechanism for arithmetic operations
// using function pointers in a struct. The dispatch function
// takes an array of operations, an operation code, and two integers,
// and calls the corresponding operation function with the integers.
// The operations are addition, subtraction, multiplication, and division.
// The code also includes error handling for division by zero.
// The dispatch function checks if the operation code is valid
// and prints an error message if it is not.

