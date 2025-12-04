#include <stdio.h>

int AND(int a, int b) { return a & b; }
int OR(int a, int b) { return a | b; }
int XOR(int a, int b) { return a ^ b; }
int NOT(int a) { return ~a & 1; }  // simulate 1-bit NOT operation

void fullAdder(int a, int b, int carryIn, int *sum, int *carryOut) {
    *sum = XOR(XOR(a, b), carryIn);
    *carryOut = OR(AND(a, b), AND(XOR(a, b), carryIn));
}

// multi-bit addition
int add(int a, int b, int *carryFlag) {
    int result = 0, carryIn = 0, carryOut = 0;

    // 4 bit
    for (int i = 0; i < 4; i++) {
        int bitA = (a >> i) & 1;
        int bitB = (b >> i) & 1;
        int sum = 0;

        fullAdder(bitA, bitB, carryIn, &sum, &carryOut);
        result |= (sum << i);
        carryIn = carryOut;
    }

    *carryFlag = carryOut; // overflow
    return result & 0xF; // result within 4 bits
}

// two's complement subtraction
int subtract(int a, int b, int *carryFlag) {
    int negB = add(~b, 1, carryFlag);
    return add(a, negB, carryFlag);
}

// op codes
enum { ADD = 0, SUB, AND_OP, OR_OP, XOR_OP };


int ALU(int op, int a, int b, int *flags) {
    switch (op) {
        case ADD:
            return add(a, b, flags);
        case SUB:
            return subtract(a, b, flags);
        case AND_OP:
            return AND(a, b);
        case OR_OP:
            return OR(a, b);
        case XOR_OP:
            return XOR(a, b);
        default:
            *flags = 1; // error flag
            return 0; // invalid op
    }
}

int main() {
    int flags = 0;
    int a = 5;  // binary: 0101
    int b = 3;  // binary: 0011

    printf("Addition (5 + 3): %d\n", ALU(ADD, a, b, &flags));     //  8
    printf("Subtraction (5 - 3): %d\n", ALU(SUB, a, b, &flags));  //  2
    printf("AND (5 & 3): %d\n", ALU(AND_OP, a, b, &flags));       //  1
    printf("OR (5 | 3): %d\n", ALU(OR_OP, a, b, &flags));         //  7
    printf("XOR (5 ^ 3): %d\n", ALU(XOR_OP, a, b, &flags));       //  6

    return 0;
}
