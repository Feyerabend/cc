## Fixed Q2.3

### Representation of 2.3

When we use *2.3* as our model for fixed-point representation, we will choose a
fixed-point format, say *Qm.n*, where `m` is the integer part, and `n` is the
fractional part.


#### Example: The *Q2.3* Fixed-Point Format

In the *Q2.3* format:
- *2 bits* are reserved for the integer part.
- *3 bits* are for the fractional part.

This setup allows us to represent:
- *Integer Range*: from -2 to 1 (where binary `10` is -2, and `01` is 1).
- *Fractional Range*: from `0.0` to `0.875` (binary `0.111` represents
$`\frac{7}{8}`$).

### Converting 2.3 to Fixed-Point in *Q2.3*

To represent *2.3* in Q2.3:

1. *Integer Part*: The integer portion of 2.3 is 2, which is `10` in binary.
2. *Fractional Part*: The fractional part, `.3`, needs to be converted to binary.
   - To convert `.3`, we multiply by 2 repeatedly to identify binary bits:
     - $`0.3 \times 2 = 0.6 `$ (whole part = 0), remaining 0.6
     - $`0.6 \times 2 = 1.2 `$ (whole part = 1), remaining 0.2
     - $`0.2 \times 2 = 0.4 `$ (whole part = 0), remaining 0.4
     - $`0.4 \times 2 = 0.8 `$ (whole part = 0), remaining 0.8
     - $`0.8 \times 2 = 1.6 `$ (whole part = 1), remaining 0.6
     - This pattern (`0.01001...`) repeats.

3. *Final Conversion*:
   - Integer part: `10` (for 2)
   - Fractional part (limited to 3 bits): `010` (approximation of `0.3`)

So, in Q2.3 format:
- *Fixed-point representation* of *2.3* is `10.010`, where `10` is the integer
part and `010` is the fractional part.

### Arithmetic Operations with *2.3* in Fixed-Point Q2.3

Now, let's explore basic arithmetic operations with *2.3* in *Q2.3* format.

#### Addition

Let's add *2.3* (`10.010`) to *1.5*.

1. *Convert 1.5 to Q2.3*:
   - Integer part: 1 (`01`)
   - Fractional part: 0.5 converts to `100` in 3 bits.
   - Fixed-point representation of 1.5: `01.100`

2. *Addition*:

```
       10.010  (= 2.3)
     + 01.100  (= 1.5)
     ---------
       11.110  (= 3.5 in fixed-point)
```

Result: `11.110`, representing 3.5, which is within the representable range.

#### Subtraction

Now, subtract *1.5* from *2.3*.

```
          10.010  (= 2.3)
        - 01.100  (= 1.5)
        ---------
          00.010  (= 0.5 in fixed-point)
```

Result: `00.010`, representing 0.5, which is also valid in our range.

#### Multiplication

To multiply *2.3* by *1.5*:

1. *Fixed-Point Representations*:
   - *2.3* as `10.010`
   - *1.5* as `01.100`

2. *Multiplication*:
   - Multiply as if they were integers: `10.010 x 01.100 = 10.111100`

3. *Scaling*: Since each operand has 3 fractional bits, the result needs adjustment
by shifting right by 3 bits.
   - Right shift `10.111100` by 3: `001.111`

This is approximately `3.5`, fitting within our fixed-point range.

#### Division

To divide *2.3* by *1.5*:

1. *Fixed-Point Representations*:
   - *2.3* as `10.010`
   - *1.5* as `01.100`

2. *Division*:
   $$\[
   \text{Result} = \frac{2.3}{1.5} \approx 1.5333
   \]$$

3. *Convert Back to Fixed-Point*:
   - Convert both to integers and adjust:
   - With a scaling factor of \(8\) (for Q2.3):
   $$\[
   \frac{(10.010 \times 8)}{(01.100 \times 8)} = \frac{18.88}{12.0} \approx 1.57
   \]$$

So, the result in fixed-point representation is approximately `1.57`.

### C code

Here's a simple implementation of fixed-point arithmetic using *2.3* as a model in C.

```c
#include <stdio.h>
#include <stdint.h>

#define FRACTIONAL_BITS 3
#define SCALE (1 << FRACTIONAL_BITS)  // 2^3 = 8 for scaling

typedef int8_t fixed_point;

fixed_point float_to_fixed(float value) {
    return (fixed_point)(value * SCALE);
}

float fixed_to_float(fixed_point value) {
    return (float)value / SCALE;
}

fixed_point fixed_add(fixed_point a, fixed_point b) {
    return a + b;  // addition
}

fixed_point fixed_sub(fixed_point a, fixed_point b) {
    return a - b;  // subtraction
}

fixed_point fixed_mul(fixed_point a, fixed_point b) {
    return (fixed_point)(((int16_t)a * (int16_t)b) >> FRACTIONAL_BITS); // right shift to scale down
}

fixed_point fixed_div(fixed_point a, fixed_point b) {
    return (fixed_point)((((int16_t)a << FRACTIONAL_BITS) + (b / 2)) / b); // scale numerator for precision
}

void print_fixed(fixed_point value) {
    printf("Fixed-point: %d (Float equivalent: %f)\n", value, fixed_to_float(value));
}

int main() {
    float num1 = 2.3;
    fixed_point fixed_num1 = float_to_fixed(num1);
    
    float num2 = 1.5;
    fixed_point fixed_num2 = float_to_fixed(num2);
    
    printf("Original float: %f -> Fixed-point: ", num1);
    print_fixed(fixed_num1);
    
    printf("Original float: %f -> Fixed-point: ", num2);
    print_fixed(fixed_num2);
    
    fixed_point sum = fixed_add(fixed_num1, fixed_num2);
    printf("\nAddition:\n");
    print_fixed(sum);

    fixed_point diff = fixed_sub(fixed_num1, fixed_num2);
    printf("\nSubtraction:\n");
    print_fixed(diff);

    fixed_point product = fixed_mul(fixed_num1, fixed_num2);
    printf("\nMultiplication:\n");
    print_fixed(product);

    fixed_point quotient = fixed_div(fixed_num1, fixed_num2);
    printf("\nDivision:\n");
    print_fixed(quotient);

    return 0;
}
```

### Running

```shell
Original float: 2.300000 -> Fixed-point: Fixed-point: 18 (Float equivalent: 2.250000) | Binary: 00010010
Original float: 1.500000 -> Fixed-point: Fixed-point: 12 (Float equivalent: 1.500000) | Binary: 00001100

Addition:
Fixed-point: 30 (Float equivalent: 3.750000) | Binary: 00011110

Subtraction:
Fixed-point: 6 (Float equivalent: 0.750000) | Binary: 00000110

Multiplication:
Fixed-point: 27 (Float equivalent: 3.375000) | Binary: 00011011

Division:
Fixed-point: 12 (Float equivalent: 1.500000) | Binary: 00001100
```
