#include <stdio.h>
#include <stdint.h>

// define the number of fractional bits for Q2.3
#define FRACTIONAL_BITS 3
#define SCALE (1 << FRACTIONAL_BITS)  // 2^3 = 8 for scaling

// fixed-point type: using 8-bit signed integer
typedef int8_t fixed_point;

// convert from float to fixed-point
fixed_point float_to_fixed(float value) {
    return (fixed_point)(value * SCALE);
}

// convert from fixed-point to float
float fixed_to_float(fixed_point value) {
    return (float)value / SCALE;
}

// addition of fixed-point numbers
fixed_point fixed_add(fixed_point a, fixed_point b) {
    return a + b;  // simple addition
}

// subtraction of fixed-point numbers
fixed_point fixed_sub(fixed_point a, fixed_point b) {
    return a - b;  // simple subtraction
}

// multiplication of fixed-point numbers
fixed_point fixed_mul(fixed_point a, fixed_point b) {
    return (fixed_point)(((int16_t)a * (int16_t)b) >> FRACTIONAL_BITS); // right shift to scale down!
}

// division of fixed-point numbers
fixed_point fixed_div(fixed_point a, fixed_point b) {
    return (fixed_point)((((int16_t)a << FRACTIONAL_BITS) + (b / 2)) / b); // scale numerator for precision
}

// function to convert fixed-point to binary representation
void print_binary(fixed_point value) {
    for (int i = 7; i >= 0; i--) {
        printf("%d", (value >> i) & 1);
    }
}

// print fixed-point value and binary representation
void print_fixed(fixed_point value) {
    printf("Fixed-point: %d (Float equivalent: %f) | Binary: ", value, fixed_to_float(value));
    print_binary(value);
    printf("\n");
}

int main() {
    // example: represent 2.3 in fixed-point
    float num1 = 2.3;
    fixed_point fixed_num1 = float_to_fixed(num1);
    
    // represent another number, say 1.5
    float num2 = 1.5;
    fixed_point fixed_num2 = float_to_fixed(num2);
    
    printf("Original float: %f -> Fixed-point: ", num1);
    print_fixed(fixed_num1);
    
    printf("Original float: %f -> Fixed-point: ", num2);
    print_fixed(fixed_num2);
    
    // addition
    fixed_point sum = fixed_add(fixed_num1, fixed_num2);
    printf("\nAddition:\n");
    print_fixed(sum);

    // subtraction
    fixed_point diff = fixed_sub(fixed_num1, fixed_num2);
    printf("\nSubtraction:\n");
    print_fixed(diff);

    // multiplication
    fixed_point product = fixed_mul(fixed_num1, fixed_num2);
    printf("\nMultiplication:\n");
    print_fixed(product);

    // division
    fixed_point quotient = fixed_div(fixed_num1, fixed_num2);
    printf("\nDivision:\n");
    print_fixed(quotient);

    return 0;
}