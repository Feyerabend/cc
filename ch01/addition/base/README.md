
## Number Representations

This text explains how computers represent numbers using different *number systems*, each defined
by its *base* or *radix*. Understanding these systems is crucial for low-level computing, binary
protocols, memory layouts, and data formats.

### Common Number Systems

Number systems vary by base and digit range. The most common are:

- *Binary (Base 2):* Digits 0–1, the foundation of digital computing.
- *Octal (Base 8):* Digits 0–7, used in legacy systems.
- *Decimal (Base 10):* Digits 0–9, standard for human use.
- *Hexadecimal (Base 16):* Digits 0–9 and A–F, for compact binary representation.


### Positional Notation

In a positional number system, a number’s value is the *sum of each digit multiplied by a power of the base*:

```math
(d_n d_{n-1} \dots d_1 d_0)_{\text{base } b} = d_n \cdot b^n + d_{n-1} \cdot b^{n-1} + \dots + d_1 \cdot b^1 + d_0 \cdot b^0
```

#### Floating-Point Extension

For fractional numbers, a radix point (like a decimal point in base 10) introduces negative powers:

```math
(d_n \dots d_1 d_0 . d_{-1} d_{-2} \dots)_{\text{base } b} = d_n \cdot b^n + \dots + d_0 \cdot b^0 + d_{-1} \cdot b^{-1} + d_{-2} \cdot b^{-2} + \dots
```

*Example:* In base 10, $123.45$ is:

$$1 \cdot 10^2 + 2 \cdot 10^1 + 3 \cdot 10^0 + 4 \cdot 10^{-1} + 5 \cdot 10^{-2} = 100 + 20 + 3 + 0.4 + 0.05 = 123.45$$


#### Examples

- *Decimal (Base 10):* The number 345 is:

$$3 \cdot 10^2 + 4 \cdot 10^1 + 5 \cdot 10^0 = 300 + 40 + 5 = 345$$

- *Binary (Base 2):* The number $1011_2$ is:

$$1 \cdot 2^3 + 0 \cdot 2^2 + 1 \cdot 2^1 + 1 \cdot 2^0 = 8 + 0 + 2 + 1 = 11_{10}$$


### Number Base Prefixes in Programming

Programming languages use prefixes to indicate number bases:

| Prefix   | Base         | Example   | Language Support       |
|----------|--------------|-----------|------------------------|
| `0b`     | Binary       | `0b1011`  | C, C++, Python, Java   |
| `0`      | Octal        | `077`     | C, C++, Python         |
| `0x`     | Hexadecimal  | `0xFF`    | C, C++, Python, Java   |

These prefixes ensure clarity when working with different bases.


### Converting

__From Any Base to Decimal__

Multiply each digit by its corresponding power of the base and sum the results.

*Example:* Convert $1A3_{16}$ to decimal:

$$1 \cdot 16^2 + 10 \cdot 16^1 + 3 \cdot 16^0 = 256 + 160 + 3 = 419_{10}$$


__From Decimal to Any Base__

Repeatedly divide by the target base, recording remainders in reverse order.

*Example:* Convert 42 to binary:

$$
\begin{aligned}
42 \div 2 &= 21, \text{ remainder } 0 \\
21 \div 2 &= 10, \text{ remainder } 1 \\
10 \div 2 &= 5, \text{ remainder } 0 \\
5 \div 2 &= 2, \text{ remainder } 1 \\
2 \div 2 &= 1, \text{ remainder } 0 \\
1 \div 2 &= 0, \text{ remainder } 1 \\
\end{aligned}
$$

Read remainders bottom-up: $101010_2$.


### Representing Negative Numbers

Negative numbers in computers are typically represented using *two’s complement* or *signed magnitude*, each with distinct characteristics.


#### Signed Magnitude

In *signed magnitude* representation, one bit (usually the most significant bit) indicates the sign (0 for positive, 1 for negative), while the remaining bits represent the magnitude (absolute value) of the number. This approach is intuitive for humans but less efficient for computer arithmetic.

For an $n$-bit number:
- The first bit is the *sign bit*: $0$ (positive or zero) or $1$ (negative).
- The remaining $n-1$ bits encode the magnitude in standard binary.

*Example (8-bit signed magnitude):*
- Positive 5: $5_{10} = 00000101_2$ (sign bit 0, magnitude $00101_2$).
- Negative 5: $-5_{10} = 10000101_2$ (sign bit 1, magnitude $00101_2$).
- Zero: $00000000_2$ (positive zero) or $10000000_2$ (negative zero).

#### Pros
- Simple to understand, as it mimics human notation (e.g., "-5" vs. "+5").
- Easy to convert between positive and negative by flipping the sign bit.

#### Cons
- *Two zeros:* Both $00000000_2$ and $10000000_2$ represent zero, complicating arithmetic and comparisons.
- *Arithmetic complexity:* Addition and subtraction require special handling of the sign bit, making hardware implementation less efficient.
- *Range asymmetry:* For an 8-bit signed magnitude, the range is $-127$ to $+127$ (since $11111111_2$ represents $-127$), but the negative zero reduces the effective range.


#### Example: Adding in Signed Magnitude

To add $+5$ ($00000101_2$) and $-3$ ($10000011_2$):
1. Compare signs: Different signs, so subtract magnitudes.
2. Magnitudes: $5_{10} = 00101_2$, $3_{10} = 00011_2$.
3. Subtract: $5 - 3 = 2$ ($00010_2$).
4. Use the sign of the larger magnitude (positive): Result is $00000010_2$ ($+2$).

This process is more complex than in two’s complement, where addition is uniform regardless of signs.


#### Comparison to Two’s Complement

Unlike signed magnitude, *two’s complement* uses a single representation for zero and simplifies arithmetic by allowing standard binary addition for both positive and negative numbers. For example, in 8-bit two’s complement:
- $-5$ is $11111011_2$ (formed by inverting $00000101_2$ and adding 1).
- Adding $+5$ and $-3$ is a single operation without sign checks.

Signed magnitude is rarely used in modern computers due to these inefficiencies but may appear in specific contexts, like early computer designs or certain data formats.


#### Two’s Complement

Two’s complement is the standard for representing negative numbers in modern computers. To form the two’s complement of a number:
1. Invert all bits (one’s complement).
2. Add 1 to the result.

*Example:* Represent $-5$ in 8-bit two’s complement:
- $5_{10} = 00000101_2$
- Invert: $11111010_2$
- Add 1: $11111011_2$

This representation ensures a single zero and seamless arithmetic operations.


### Summary of Number Systems

| Base | Name        | Digits       | Primary Use Case                     |
|------|-------------|--------------|--------------------------------------|
| 2    | Binary      | 0–1          | Machine-level operations             |
| 8    | Octal       | 0–7          | Legacy systems, Unix permissions     |
| 10   | Decimal     | 0–9          | Human-readable numbers               |
| 16   | Hexadecimal | 0–9, A–F     | Memory addresses, color encoding     |


