#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

#define FIXED_POINT_SCALE 256   // scaling factor (2^8 for 8-bit precision)

// floating-point --> fixed-point
int float_to_fixed(float value) {
    return (int)(value * FIXED_POINT_SCALE);
}

// fixed-point --> floating-point
float fixed_to_float(int value) {
    return (float)value / FIXED_POINT_SCALE;
}

typedef enum { ADD, SUB, MUL, DIV, HALT } OpCode;

typedef struct {
    OpCode op;
    int operand;  // fixed-point operand
} Instruction;

typedef struct {
    Instruction* instructions;
    int ip;  // instruction pointer
    int result;  // fixed-point result
} Interpreter;

typedef struct {
    void (*next)(Interpreter*);
} Trampoline;

void add(Interpreter* interpreter) {
    interpreter->result += interpreter->instructions[interpreter->ip].operand;
    interpreter->ip++;
    printf("ADD: result = %d\n", interpreter->result);
}

void sub(Interpreter* interpreter) {
    interpreter->result -= interpreter->instructions[interpreter->ip].operand;
    interpreter->ip++;
    printf("SUB: result = %d\n", interpreter->result);
}

void mul(Interpreter* interpreter) {
    interpreter->result = (interpreter->result * interpreter->instructions[interpreter->ip].operand) / FIXED_POINT_SCALE;
    interpreter->ip++;
    printf("MUL: result = %d\n", interpreter->result);
}

void fixed_point_div(Interpreter* interpreter) {
    int divisor = interpreter->instructions[interpreter->ip].operand;
    if (divisor == 0) {
        printf("Error: Division by zero.\n");
        exit(1);  // Handle division by zero
    }

    // 64-bit precision
    int64_t extended_result = (int64_t)interpreter->result * FIXED_POINT_SCALE;

    // scale back to the fixed-point format (32-bit precision result)
    interpreter->result = (int)(extended_result / divisor);
    interpreter->ip++;
    printf("DIV: result = %d\n", interpreter->result);
}

void halt(Interpreter* interpreter) {
    printf("Final result: %d / %d = %f\n", interpreter->result, FIXED_POINT_SCALE, (float)interpreter->result / FIXED_POINT_SCALE);
}


void execute(Interpreter* interpreter) {
    Trampoline trampoline;
    trampoline.next = NULL;

    while (1) {
        Instruction* inst = &interpreter->instructions[interpreter->ip];

        printf("Executing instruction %d: ", interpreter->ip);
        switch (inst->op) {
            case ADD:
                trampoline.next = add;
                printf("ADD\n");
                break;
            case SUB:
                trampoline.next = sub;
                printf("SUB\n");
                break;
            case MUL:
                trampoline.next = mul;
                printf("MUL\n");
                break;
            case DIV:
                trampoline.next = fixed_point_div;
                printf("DIV\n");
                break;
            case HALT:
                trampoline.next = halt;
                printf("HALT\n");
                break;
        }

        if (trampoline.next != NULL) {
            trampoline.next(interpreter);
        }

        if (inst->op == HALT) {
            break;
        }
    }
}

int main() {

    // test conversions
    assert(float_to_fixed(10.5) == 2688);  // 10.5 * 256 = 2688
    assert(float_to_fixed(5.5) == 1408);   // 5.5 * 256 = 1408
    assert(float_to_fixed(3.0) == 768);    // 3.0 * 256 = 768
    assert(float_to_fixed(-2.75) == -704); // -2.75 * 256 = -704

    assert(fixed_to_float(2688) == 10.5);  // 2688 / 256 = 10.5
    assert(fixed_to_float(1408) == 5.5);   // 1408 / 256 = 5.5
    assert(fixed_to_float(768) == 3.0);    // 768 / 256 = 3.0
    assert(fixed_to_float(-704) == -2.75); // -704 / 256 = -2.75

    // Example program: (10.5 + 5.5) * 3.0 - 4.0 / 2.0
    // Representing 10.5 as 10*256 + 128 (10.5 * 256 = 2688)
    Instruction program[] = {
        {ADD, 2688},  // 10.5 * 256
        {ADD, 1408},  // 5.5 * 256
        {MUL, 768},   // 3.0 * 256
        {SUB, 1024},  // 4.0 * 256
        {DIV, 512},   // 2.0 * 256
        {HALT, 0}
    };

    // init and start at 0
    Interpreter interpreter = {program, 0, 0};  

    execute(&interpreter);

    printf("Executing edge test cases ..\n");
    assert(float_to_fixed(0.0) == 0);          // case: zero
    assert(fixed_to_float(0) == 0.0);          // case: zero
    assert(float_to_fixed(-100.25) == -25664); // case: negative
    assert(fixed_to_float(-25664) == -100.25); // case: negative

    printf("All tests passed!\n");

    return 0;
}

// This code implements a simple interpreter for a fixed-point arithmetic language
// using a trampoline to manage control flow. The trampoline allows us to execute
// instructions without deep recursion.

// How would the recursive version look like?
// In a recursive version of the interpreter, we would directly call the function
// corresponding to each opcode without using a trampoline. This would lead to
// deep recursion, if the program has many instructions, which can cause a stack overflow.
