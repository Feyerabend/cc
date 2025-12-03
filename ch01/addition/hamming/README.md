
## Hamming Code

Hamming Code, introduced by Richard Hamming in 1950, is a family of linear error-correcting codes
designed to detect and correct single-bit errors in data transmission or storage. By adding redundant
*parity bits* to data, Hamming Codes can identify and fix a single erroneous bit, ensuring reliable
communication in digital systems.


*Applications*
- Digital communication (e.g., satellites, modems)
- Memory systems (e.g., ECC RAM)
- Embedded systems and IoT devices

```plaintext
Original Data: 1011
With Error:    10*0*1  (bit flipped)
Corrected:     1011    (Hamming Code fixes it)
```

### General Structure

A Hamming Code is defined by two parameters:
- *k*: Number of data bits
- *r*: Number of parity bits

The total codeword length is *n = k + r*. The number of parity bits must satisfy:

*2ʳ ≥ k + r + 1*

This ensures enough unique parity combinations to identify any single-bit error (or confirm no error).
Each parity bit is placed at a position that is a power of 2 (1, 2, 4, 8, ...), and data bits fill the
remaining positions.

```plaintext
Codeword Structure:
Positions:  1   2   3   4   5   6   7   8   ...
Content:   P1  P2  D1  P4  D2  D3  D4  P8   ...
           ^   ^       ^           ^   (powers of 2)
```


### Code Variants

Hamming Codes are flexible and can be designed for any number of data bits *k*,
with the appropriate number of parity bits *r*. Some common variants include:

- *(7,4)*: 4 data bits, 3 parity bits, total length 7
  - Ideal for small data blocks, often used in educational examples

- *(15,11)*: 11 data bits, 4 parity bits, total length 15
  - Suitable for slightly larger data, used in some embedded systems

- *(31,26)*: 26 data bits, 5 parity bits, total length 31
  - Used in applications requiring moderate data sizes, like ECC memory

- *(n,k)*: General form, where *r* is the smallest integer satisfying *2ʳ ≥ k + r + 1*

For example:
- For *k=8* data bits, solve *2ʳ ≥ 8 + r + 1*:
  - Try *r=4*: *2⁴ = 16 ≥ 8 + 4 + 1 = 13* (works)
  - Code: (12,8) with 8 data bits, 4 parity bits, total length 12

```plaintext
(7,4)  Codeword: P1 P2 D1 P4 D2 D3 D4
(15,11) Example: P1 P2 D1 P4 D2 D3 D4 P8 D5 D6 D7 D8 D9 D10 D11
```

## Parity Bit Calculations

Each parity bit checks a unique subset of positions, determined by their binary representation.
For position *i*:
- *P1* (position 1): Checks positions where the 1st bit is 1 (1, 3, 5, 7, ...)
- *P2* (position 2): Checks positions where the 2nd bit is 1 (2, 3, 6, 7, ...)
- *P4* (position 4): Checks positions where the 3rd bit is 1 (4, 5, 6, 7, ...)
- And so on for higher powers of 2

Parity is calculated using XOR (⊕) to ensure even parity across the checked bits.

```plaintext
P1 checks: [1]     [3]     [5]     [7]     ...
           P1 ---- D1 ---- D2 ---- D3 --- ...
P2 checks:    [2]  [3]     [6]     [7]     ...
              P2 - D1 ---- D2 ---- D3 --- ...
```

## Error Detection and Correction

1. *Syndrome Calculation*: The receiver recomputes parity checks.
   Failed checks form a binary *syndrome* indicating the erroneous bit's position.
2. *Error Handling*:
   - Syndrome = 0: No error
   - Syndrome ≠ 0: Flip the bit at the position indicated by the syndrome

*Example (7,4)*:
- Data: *1011*
- Codeword: *0110011*
- Error in bit 3: *01*0*0011*
- Syndrome: *011* (binary) = 3 (decimal)
- Action: Flip bit 3 to restore *0110011*

```plaintext
Transmitted: 0110011
Received:    01*0*0011
Syndrome:    011 = 3
Corrected:   0110011
```

### Advantages
- Corrects single-bit errors reliably
- Detects double-bit errors (with an optional overall parity bit)
- Simple implementation using XOR operations
- Flexible for various data sizes

### Limitations
- Corrects only one error per block
- Inefficient for large data (requires more parity bits)
- Struggles with burst errors without additional techniques (e.g., interleaving)


### Modern Relevance

Hamming Codes are foundational in error correction, used in ECC memory, low-power IoT devices,
and educational settings. While advanced codes (e.g., Reed-Solomon, LDPC) handle complex errors,
Hamming Codes remain relevant for their simplicity and efficiency in small-scale applications.

```plaintext
(15,11) Example:
Data:       10110011011
Codeword:   P1 P2 D1 P4 D2 D3 D4 P8 D5 D6 D7 D8 D9 D10 D11
Error:      Bit 6 flips
Corrected:  Syndrome identifies and fixes bit 6
```

### Summary

Hamming Codes form a versatile family of error-correcting codes, with variants like
(7,4), (15,11) and beyond, tailored to different data sizes. Their ability to correct
single-bit errors with minimal overhead makes them a timeless tool in digital systems,
balancing simplicity and reliability.

