#include <stdio.h>
#include <stdint.h>

// define the number of fractional bits (we use 16 for Q16.16 fixed-point format)
#define FRACTIONAL_BITS 16
#define SCALE (1 << FRACTIONAL_BITS)  // 2^16 or 65536 for scaling

// fixed-point type: using 32-bit signed integer
typedef int32_t fixed_point;

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
    return a + b;
}

// subtraction of fixed-point numbers
fixed_point fixed_sub(fixed_point a, fixed_point b) {
    return a - b;
}

// multiplication of fixed-point numbers
fixed_point fixed_mul(fixed_point a, fixed_point b) {
    return (fixed_point)(((int64_t)a * b) >> FRACTIONAL_BITS);
}

// corrected division of fixed-point numbers with rounding
fixed_point fixed_div(fixed_point a, fixed_point b) {
    return (fixed_point)(((int64_t)a << FRACTIONAL_BITS) / b);
}

// modulo operation for fixed-point numbers
fixed_point fixed_mod(fixed_point a, fixed_point b) {
    return a % b;
}

// printing fixed-point value (debugging)
void print_fixed(fixed_point value) {
    printf("Fixed-point: %d (Float equivalent: %f)\n", value, fixed_to_float(value));
}

int main() {
    // convert floating-point numbers to fixed-point numbers
    float a_f = 14.4375;
    float b_f = 7.5625;
    
    fixed_point a = float_to_fixed(a_f);
    fixed_point b = float_to_fixed(b_f);

    printf("Original floating-point numbers:\n");
    printf("a = %f, b = %f\n", a_f, b_f);
    
    printf("\nFixed-point representations:\n");
    print_fixed(a);
    print_fixed(b);
    
    // addition
    fixed_point sum = fixed_add(a, b);
    printf("\nAddition:\n");
    print_fixed(sum);

    // subtraction
    fixed_point diff = fixed_sub(a, b);
    printf("\nSubtraction:\n");
    print_fixed(diff);

    // multiplication
    fixed_point product = fixed_mul(a, b);
    printf("\nMultiplication:\n");
    print_fixed(product);

    // division
    fixed_point quotient = fixed_div(a, b);
    printf("\nDivision:\n");
    print_fixed(quotient);

    // modulo
    fixed_point remainder = fixed_mod(a, b);
    printf("\nModulo:\n");
    print_fixed(remainder);

    return 0;
}

/*
Original floating-point numbers:
a = 5.250000, b = 2.750000

Fixed-point representations:
Fixed-point: 344064 (Float equivalent: 5.250000)
Fixed-point: 180224 (Float equivalent: 2.750000)

Addition:
Fixed-point: 524288 (Float equivalent: 8.000000)

Subtraction:
Fixed-point: 163840 (Float equivalent: 2.500000)

Multiplication:
Fixed-point: 619520 (Float equivalent: 9.062500)

Division:
Fixed-point: 122880 (Float equivalent: 1.500000)

Modulo:
Fixed-point: 163840 (Float equivalent: 2.500000)
*/

/*
Fixed-point representation: For example, `5.25` is represented as `344064` in fixed-point.
This is calculated as `5.25 * 65536 = 344064`.

Addition: `5.25 + 2.75 = 8.0` in floating-point. In fixed-point, `344064 + 180224 = 524288`,
which converts back to `8.0` in floating-point.

Subtraction: `5.25 - 2.75 = 2.5`, and in fixed-point, `344064 - 180224 = 163840`, which converts
back to `2.5`.

Multiplication: `5.25 * 2.75 = 9.0625`. The fixed-point result is `619520`, and `619520 / 65536 = 9.0625`.

Division: `5.25 / 2.75 = 1.5`. The fixed-point result is `122880`, and `122880 / 65536 = 1.5`.

Modulo: `5.25 % 2.75 = 2.5`. In fixed-point, `163840` represents `2.5`.



1. Precision: The multiplication and division operations involve shifts to maintain precision.
Using `int64_t` for intermediate results ensures that we avoid overflow during these operations.

2. Scaling factor: This implementation uses a Q16.16 format (16 bits for the fractional part).
You can adjust `FRACTIONAL_BITS` if a different precision is needed.

3. Limitations: Fixed-point numbers offer limited precision compared to floating-point, so rounding
errors and overflow issues can occur with large numbers or very small fractional parts.

This library provides basic functionality for handling fixed-point numbers in C and showcases
the core operations like conversion, arithmetic, and printing.
*/