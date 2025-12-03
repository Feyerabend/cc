
## Fixed Q16.16

A fixed-point number system represents real numbers as integers while implicitly treating
the number as being scaled by some factor (usually a power of two or ten). In C, we can
implement a fixed-point library to handle basic arithmetic (addition, subtraction, multiplication,
division, and modulo) and convert between fixed-point and floating-point numbers.

We'll represent fixed-point numbers with an integer and a fixed scaling factor
(e.g., 16 fractional bits for a 32-bit fixed-point type).


### Fixed-point in C


```c
#include <stdio.h>
#include <stdint.h>

#define FRACTIONAL_BITS 16
#define SCALE (1 << FRACTIONAL_BITS)  // 2^16 for scaling

typedef int32_t fixed_point;

fixed_point float_to_fixed(float value) {
    return (fixed_point)(value * SCALE);
}

float fixed_to_float(fixed_point value) {
    return (float)value / SCALE;
}

fixed_point fixed_add(fixed_point a, fixed_point b) {
    return a + b;
}

fixed_point fixed_sub(fixed_point a, fixed_point b) {
    return a - b;
}

fixed_point fixed_mul(fixed_point a, fixed_point b) {
    return (fixed_point)(((int64_t)a * b) >> FRACTIONAL_BITS);
}

fixed_point fixed_div(fixed_point a, fixed_point b) {
    return (fixed_point)(((int64_t)a << FRACTIONAL_BITS) / b);
}

fixed_point fixed_mod(fixed_point a, fixed_point b) {
    return a % b;
}

void print_fixed(fixed_point value) {
    printf("Fixed-point: %d (Float equivalent: %f)\n", value, fixed_to_float(value));
}
```

### Explanation

- *Conversion between float and fixed-point*:
  - `float_to_fixed(float value)`: Converts a floating-point number to a fixed-point number
    by multiplying the float by the scale factor (2^16).
  - `fixed_to_float(fixed_point value)`: Converts a fixed-point number back to a floating-point
    number by dividing it by the scale factor.
  
- *Arithmetic operations*:
  - `fixed_add`, `fixed_sub`: Simple integer addition and subtraction.
  - `fixed_mul`: Multiplies two fixed-point numbers and shifts the result back by `FRACTIONAL_BITS`
    to account for the fixed-point scaling.
  - `fixed_div`: Shifts the dividend up by `FRACTIONAL_BITS` before performing integer division,
    to maintain precision.
  - `fixed_mod`: Uses the modulo operation, which operates at the integer level and provides
    the remainder in fixed-point form.

- *Printing*: `print_fixed` outputs both the fixed-point representation (raw integer value) and
  the floating-point equivalent.


### Example

Here's a sample program demonstrating the usage of the fixed-point library
with addition, subtraction, multiplication, division, and modulo operations:

```c
int main() {
    float a_f = 5.25;
    float b_f = 2.75;
    
    fixed_point a = float_to_fixed(a_f);
    fixed_point b = float_to_fixed(b_f);

    printf("Original floating-point numbers:\n");
    printf("a = %f, b = %f\n", a_f, b_f);
    
    printf("\nFixed-point representations:\n");
    print_fixed(a);
    print_fixed(b);
    
    // Addition
    fixed_point sum = fixed_add(a, b);
    printf("\nAddition:\n");
    print_fixed(sum);

    // Subtraction
    fixed_point diff = fixed_sub(a, b);
    printf("\nSubtraction:\n");
    print_fixed(diff);

    // Multiplication
    fixed_point product = fixed_mul(a, b);
    printf("\nMultiplication:\n");
    print_fixed(product);

    // Division
    fixed_point quotient = fixed_div(a, b);
    printf("\nDivision:\n");
    print_fixed(quotient);

    // Modulo
    fixed_point remainder = fixed_mod(a, b);
    printf("\nModulo:\n");
    print_fixed(remainder);

    return 0;
}
```

### Output

```bash
Original floating-point numbers:
a = 14.437500, b = 7.562500

Fixed-point representations:
Fixed-point: 946176 (Float equivalent: 14.437500)
Fixed-point: 495616 (Float equivalent: 7.562500)

Addition:
Fixed-point: 1441792 (Float equivalent: 22.000000)

Subtraction:
Fixed-point: 450560 (Float equivalent: 6.875000)

Multiplication:
Fixed-point: 7155456 (Float equivalent: 109.183594)

Division:
Fixed-point: 125114 (Float equivalent: 1.909088)

Modulo:
Fixed-point: 450560 (Float equivalent: 6.875000)
```

### Notes

1. *Precision*: The multiplication and division operations involve shifts
   to maintain precision. Using `int64_t` for intermediate results ensures
   that we avoid overflow during these operations.

2. *Scaling factor*: This implementation uses a Q16.16 format (16 bits for
   the fractional part). You can adjust `FRACTIONAL_BITS` if a different
   precision is needed.

3. *Limitations*: Fixed-point numbers offer limited precision compared to
   floating-point, so rounding errors and overflow issues can occur with
   large numbers or very small fractional parts.
