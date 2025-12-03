
## What is Gray Code?

Gray code, also known as *reflected binary code*, is a binary numeral system where two
consecutive values differ by only *one bit*. Unlike standard binary encoding, where
multiple bits may change when incrementing a number (e.g., from 3 (0011) to 4 (0100),
three bits change), Gray code ensures that transitioning from one value to the next
involves flipping just *a single bit*. This property makes Gray code particularly useful
in applications where errors due to bit changes need to be minimised, such as in digital
systems, rotary encoders, or analog-to-digital converters.


#### Key Properties of Gray Code

1. *Single-Bit Transitions*: Between any two consecutive numbers, only one bit changes
   (Hamming distance of 1). This reduces errors during transitions in hardware or sensors,
   as it minimises the chance of misreading due to transient states.

2. *Non-Weighted Code*: Unlike binary, Gray code is not a weighted system (i.e., bit
   positions don't represent powers of 2). This means you can't directly perform arithmetic
   on Gray code values without converting them back to binary.

3. *Cyclic Nature*: Gray code can be arranged in a cycle (e.g., for 4 bits, from 0 to 15
   and back to 0) where the first and last values also differ by one bit, making it ideal
   for applications like rotary encoders.


#### Example of Gray Code vs. Binary

For 3-bit numbers (0 to 7), here's a comparison:

| Decimal | Binary | Gray Code |
|---------|--------|-----------|
|       0 |    000 |       000 |
|       1 |    001 |       001 |
|       2 |    010 |       011 |
|       3 |    011 |       010 |
|       4 |    100 |       110 |
|       5 |    101 |       111 |
|       6 |    110 |       101 |
|       7 |    111 |       100 |

Notice:
- From binary 3 (011) to 4 (100), *three bits* change.
- From Gray code 3 (010) to 4 (110), *only one bit* changes (the second bit).

This single-bit change property is what makes Gray code robust against errors
in applications where values are read sequentially, such as in mechanical or
optical encoders.


#### How Gray Code is Generated

Gray code can be generated from binary using a simple formula:

- *Binary to Gray*: For a binary number $n$, the Gray code is $n \ XOR \ (n >> 1)$.
  This means you take the binary number and XOR it with itself shifted right by one bit.

- *Gray to Binary*: To convert back, iteratively XOR the Gray code with itself shifted
  right, accumulating the result. For example, for a Gray code $g$, initialize $n = g$,
  then repeatedly compute $n = n \ XOR \ (g >> 1)$ until $g$ becomes 0.


#### Why Use Gray Code?

Gray code is widely used in:
- *Rotary Encoders*: In devices like rotary dials or motor position sensors, where
  mechanical transitions might cause bits to be read incorrectly during a change
  (e.g., due to electrical noise or timing issues).

- *Error Correction*: In digital communications, where minimizing bit errors during
  state changes is critical.

- *Karnaugh Maps*: In digital circuit design, Gray code simplifies the representation
  of adjacent states in truth tables.

- *Analog-to-Digital Conversion*: To reduce errors when sampling analog signals.


### Explanation of the Example Code

The provided C code simulates a scenario where bit glitches (random bit flips) occur
during the reading of a sequence of numbers, comparing the robustness of *standard
binary encoding* versus *Gray code*. The simulation mimics a real-world system,
such as a rotary encoder, where electrical noise or mechanical imperfections might
cause a bit to be misread (a glitch). The goal is to demonstrate that Gray code's
single-bit transition property reduces errors compared to binary encoding, where
multiple bits may change simultaneously.


#### Code Overview

The program:
1. Converts numbers to Gray code and back using helper functions.
2. Simulates a sequence of values (e.g., from 1 to 15 for 4 bits).
3. Introduces random single-bit glitches to mimic real-world errors.
4. Compares the decoded values (after a glitch) for both binary and
   Gray code encodings to check for errors.
5. Prints a table showing the true value, binary representation,
   glitched binary, Gray code, glitched Gray code, and whether each
   encoding results in an error.


#### Key Components of the Code

1. *Binary to Gray Conversion (`binary_to_gray`)*
   ```c
   unsigned int binary_to_gray(unsigned int n) {
       return n ^ (n >> 1);
   }
   ```
   - Takes a binary number $n$.
   - Shifts it right by 1 bit ($n >> 1$) and XORs it with the original number.
   - Example: For $n = 3$ (binary 0011), $n >> 1 = 0001$, so $0011 \ XOR \ 0001 = 0010$,
     which is the Gray code for 3.

2. *Gray to Binary Conversion (`gray_to_binary`)*
   ```c
   unsigned int gray_to_binary(unsigned int g) {
       unsigned int n = g;
       while (g >>= 1)
           n ^= g;
       return n;
   }
   ```
   - Converts a Gray code back to binary by iteratively XORing with
     right-shifted versions of itself.
   - Example: For Gray code 0010 ($g$), initialize $n = 0010$. Shift
     $g \to 0001$, XOR $n = 0010 \ XOR \ 0001 = 0011$. Shift
     $g \to 0000$, XOR $n = 0011 \ XOR \ 0000 = 0011$. Result is binary 3 (0011).

3. *Simulate Bit Glitch (`simulate_bit_glitch`)*
   ```c
   unsigned int simulate_bit_glitch(unsigned int value, double glitch_chance, int bits) {
       if ((rand() / (double)RAND_MAX) < glitch_chance) {
           int bit_to_flip = rand() % bits;
           return value ^ (1 << bit_to_flip);
       }
       return value;
   }
   ```
   - Simulates a glitch by randomly flipping one bit in the input value
     with a given probability (e.g., 20%).
   - Example: For value 0011 and a glitch flipping the second bit,
     $0011 \ XOR \ 0010 = 0001$.
   - This mimics real-world scenarios where electrical noise or timing
     issues cause a single bit to be misread.

4. *Main Simulation Loop*
   - Iterates through values from 1 to $2^4 - 1 = 15$ (for 4 bits).
   - For each value:
     - Computes its binary and Gray code representations.
     - Applies a random glitch to both representations.
     - Converts the glitched Gray code back to binary for comparison.
     - Checks if the glitched value matches the true value (i.e., no error).
     - Prints a table showing:
       - Step number
       - True decimal value
       - True binary and glitched binary, with error status
       - True Gray code and glitched Gray code, with error status


#### Example Output Explained

Here's a sample output row from the code:
```
Step | True Dec | Binary    | Read Bin | Error | Gray     | Read Gray | Error
-------------------------------------------------------------------------------
 3   |    3     | 0011      | 0001     | FAIL  | 0010     | 0010      |  OK
```

- *Step 3, True Decimal 3*:
  - *Binary*: 0011 (decimal 3).
  - *Read Binary*: 0001 (a glitch flipped the third bit from 1 to 0).
  - *Binary Error*: FAIL (0001 is decimal 1, not 3).
  - *Gray Code*: 0010 (Gray code for 3).
  - *Read Gray*: 0010 (no glitch occurred, or the glitch didn't affect the value).
  - *Gray Error*: OK (when converted back, 0010 is still 3).

This row shows a case where a binary glitch caused an error (reading 1 instead of 3),
but the Gray code read was correct because only one bit changes between consecutive
Gray code values, making it more likely to tolerate glitches.


#### Why Gray Code Performs Better

- In binary, transitioning between numbers often involves multiple bit changes (e.g.,
  from 3 (0011) to 4 (0100), three bits change). If a glitch occurs during this transition,
  the read value might be completely wrong (e.g., 0001 instead of 0100).

- In Gray code, only one bit changes (e.g., from 3 (010) to 4 (110)). A glitch in a single
  bit is either:
  - In the bit that didn't change (no effect), or
  - In the bit that did change, which might result in reading the previous or next value
    (a smaller error).

- This property makes Gray code more robust in systems where transitions are frequent,
  and glitches are possible.


#### Observations from the Simulation

- *Binary Failures*: Binary encoding often fails when multiple bits change between steps,
  as a single-bit glitch can result in a completely different number (e.g., 3 (0011)
  misread as 1 (0001)).

- *Gray Code Robustness*: Gray code tends to produce fewer errors because a glitch typically
  results in a value that's either correct or off by one (e.g., reading 2 or 4 instead of 3),
  which is less severe than binary's potential for large errors.


### Real-World Context

The simulation mimics systems like *rotary encoders*, which are used in devices like computer
mice, motor controllers, or industrial machinery. In a rotary encoder, a disk with patterns
is read by sensors to determine position. During fast rotation, sensors might misread bits due
to timing or noise. Gray code ensures that even if a bit is misread, the error is minimal
(e.g., off by one position) rather than catastrophic (e.g., jumping to a distant value).

For example, in a binary-encoded encoder, transitioning from 7 (0111) to 8 (1000) changes
all four bits. If the sensors catch an intermediate state (e.g., 0110 due to timing), it
might read 6 instead of 8--a significant error. In Gray code, 7 (0100) to 8 (1100) changes
only one bit, so a glitch is less likely to cause a large deviation.


### Summary

- *Gray Code*: A binary system where consecutive values differ by one bit, reducing errors
  in systems with frequent transitions or noise.

- *Simulation Purpose*: The code demonstrates Gray code's robustness by simulating bit
  glitches in a sequence of values, showing that Gray code tolerates errors better than binary.

- *Key Insight*: Gray code's single-bit transitions make it ideal for applications like encoders,
  where minimising misreads is critical.


