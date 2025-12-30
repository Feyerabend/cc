
## Binary-Coded Decimal (BCD)

*Binary-Coded Decimal (BCD)* is a number representation system where each decimal digit
(0–9) is encoded using a fixed number of bits, typically 4 bits per digit. Unlike standard
binary, which represents numbers as powers of 2, BCD directly maps each decimal digit to
its binary equivalent, making it ideal for applications requiring precise decimal arithmetic,
such as financial calculations or digital displays, where rounding errors from floating-point
representations are unacceptable.

In BCD, each decimal digit is represented by its 4-bit binary equivalent:

| Decimal Digit | BCD (4-bit) |
|---------------|-------------|
| 0             | 0000        |
| 1             | 0001        |
| 2             | 0010        |
| 3             | 0011        |
| 4             | 0100        |
| 5             | 0101        |
| 6             | 0110        |
| 7             | 0111        |
| 8             | 1000        |
| 9             | 1001        |

- *Example:* The decimal number 123 is represented in BCD as `0001 0010 0011` (12 bits,
  with each 4-bit group encoding one digit).
- *Key Feature:* BCD preserves decimal precision, avoiding conversion errors inherent
  in binary floating-point representations.
- *Trade-off:* BCD is less space-efficient than pure binary, as it uses more bits to
  represent the same numerical value (e.g., 123 in binary is `1111011`, only 7 bits).


### Uses

- *Financial Systems:* Ensures exact decimal calculations for currency.
- *Digital Displays:* Simplifies mapping digits to display segments.
- *Embedded Systems:* Used in devices like calculators or counters where decimal
  output is critical.


### BCD in Programming

BCD is not natively supported in most high-level languages, but it can be implemented
by manipulating bits or bytes to represent decimal digits. Below are examples in C and
Python to convert a decimal number to BCD and display it.


### Example in C: Convert Decimal to BCD

This C program converts a decimal number (e.g., 123) to BCD and prints the binary representation.

```c
#include <stdio.h>

// Convert a decimal number to BCD
void decimalToBCD(int decimal) {
    int digit;
    printf("BCD representation of %d: ", decimal);
    // Each digit from left to right
    while (decimal > 0) {
        digit = decimal % 10; // Get rightmost digit
        // Print 4-bit BCD for the digit (padded to 4 bits)
        printf("%04d ", digit); // %04d ensures 4-bit output (e.g., 0001 for 1)
        decimal /= 10; // Remove processed digit
    }
    printf("\n");
}

int main() {
    int number = 123;
    decimalToBCD(number);
    return 0;
}
```

*Output:*
```shell
BCD representation of 123: 0011 0010 0001
```

*Explanation:*
- The program extracts each digit of the input (123) using modulo (`%`) and division (`/`).
- Each digit is printed as a 4-bit binary value (e.g., 3 = `0011`, 2 = `0010`, 1 = `0001`).
- The digits are processed from right to left, but the output appears in the correct order.


#### Example in Python: Convert Decimal to BCD

This Python script converts a decimal number to BCD and prints the binary representation,
with each digit padded to 4 bits.

```python
def decimal_to_bcd(decimal):
    # Convert number to string to process digits
    digits = str(decimal)
    bcd_result = []
    
    # Convert each digit to 4-bit binary
    for digit in digits:
        # Convert digit to int and then to binary, remove '0b' prefix, pad to 4 bits
        bcd = format(int(digit), '04b')
        bcd_result.append(bcd)
    
    # Join with spaces for readability
    print(f"BCD representation of {decimal}: {' '.join(bcd_result)}")

# Test function
decimal_to_bcd(123)
```

*Output:*
```shell
BCD representation of 123: 0001 0010 0011
```

*Explanation:*
- The number is converted to a string to iterate over its digits.
- Each digit is converted to a 4-bit binary string using `format(int(digit), '04b')`, which ensures zero-padding.
- The BCD digits are joined with spaces for clarity.


### Advantages
- *Decimal Precision:* No rounding errors, ideal for financial or exact decimal applications.
- *Human-Readable:* Easy to map to decimal displays or interfaces.
- *Simple Conversion:* Direct mapping of decimal digits to binary.

### Disadvantages
- *Inefficient Storage:* Requires more bits than pure binary (e.g., 12 bits for 123 in BCD vs. 7 bits in binary).
- *Complex Arithmetic:* Addition and subtraction require special handling to correct invalid BCD codes (e.g., 1010–1111 are unused).
- *Limited Native Support:* Most modern processors lack direct BCD arithmetic instructions, requiring software implementation.


### BCD in Practice

BCD is less common in modern computing due to the efficiency of binary and floating-point
representations but remains relevant in specialised applications. For example, in financial
software, BCD ensures that $123.45 is stored exactly, avoiding errors like $123.449999...$
in floating-point. In embedded systems, BCD simplifies driving 7-segment displays by directly
mapping digits to output patterns.

