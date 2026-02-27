#include <stdio.h>

// function types
typedef int (*operation_fn)(int, int);

// ordinary arithmetic operations
int add(int a, int b) {
    return a + b;
}

int subtract(int a, int b) {
    return a - b;
}

int multiply(int a, int b) {
    return a * b;
}

int divide(int a, int b) {
    if (b != 0) {
        return a / b;
    } else {
        printf("Error: Division by zero!\n");
        return 0;
    }
}

// perform the operation based on the operation code
int perform_operation(int operation_code, int a, int b) {

    // jump table (array of function pointers)
    operation_fn jump_table[] = {
        add,
        subtract,
        multiply,
        divide
    };
    
    // if the operation code within valid range
    if (operation_code >= 0 && operation_code < sizeof(jump_table) / sizeof(jump_table[0])) {
        return jump_table[operation_code](a, b);  // call corresponding function
    } else {
        printf("Error: Invalid operation code!\n");
        return 0;
    }
}

int main() {
    int a = 10, b = 5;
    
    // test jump table with different operation codes
    printf("Addition: %d + %d = %d\n", a, b, perform_operation(0, a, b));        // Operation 0: add
    printf("Subtraction: %d - %d = %d\n", a, b, perform_operation(1, a, b));     // Operation 1: subtract
    printf("Multiplication: %d * %d = %d\n", a, b, perform_operation(2, a, b));  // Operation 2: multiply
    printf("Division: %d / %d = %d\n", a, b, perform_operation(3, a, b));        // Operation 3: divide
    
    return 0;
}
