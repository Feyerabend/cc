
## Representing Negative Numbers

*The problem negative numbers pose.*

A physical register in a CPU is just a row of switches--on or off, 1 or 0.
As we have been told many times. Nothing about that hardware inherently means
"negative." The negativity has to be encoded as a convention, and historically
that convention has been chosen more than one way.



### A brief history of signed representations

*Sign-magnitude* is the most intuitive. Reserve one bit for the sign, use the
remaining bits for the magnitude. A 4-bit word gives +3 = `0011` and -3 = `1011`.
Simple to understand, but it creates *two* zeros (`+0` and `-0`), and addition
requires checking the sign before deciding whether to add or subtract. It is
inconvenient for hardware.

*Ones' complement* flips all bits to negate: -3 = `1100` (from `0011`).
Addition mostly works, but a carry out of the MSB has to be fed back in (an
"end-around carry"), and it still has two zeros. Some early machines used it:
notably the CDC 6600 (1964) and the PDP-1 (1960).

*Two's complement* flips all bits and adds one: -3 = `1101`. Addition now
requires no special cases, there is only one zero, and the hardware is simpler.
Every general-purpose CPU since the 1970s uses it. It became so universal that
most programmers never think about the alternatives.

*Excess-N (biased) notation* adds a fixed offset so the most negative value
maps to all zeros. IEEE 754 floating-point uses this for its exponent field.
A stored exponent of `01111111` in a 32-bit float means the actual exponent is
0, because the bias is 127. It makes exponent comparison a simple unsigned
integer comparison.

*BCD (Binary Coded Decimal)* encodes each decimal digit in four bits
separately. Pocket calculators and financial systems use it so that decimal
fractions like 0.1 are exact. Negative BCD numbers are usually handled with a
separate sign digit or the ten's complement of the digit string.



### Calculators and the ten's complement

Mechanical and early electronic calculators worked in base 10, not base 2.
To subtract, many used the *ten's complement*: negate a number by subtracting
each digit from 9 and adding 1. Then subtraction becomes addition and you
discard any final carry. That is, no subtraction circuit needed at all. The Marchant,
Friden, and Monroe mechanical calculators of the 1940s and 1950s all used
variants of this idea. The same principle appears in the nine's complement (like
ones' complement but in decimal) on some machines.

HP's scientific calculators of the 1970s used BCD internally with a special sign
digit. The HP-35 (1972), the first handheld scientific calculator, stored ten
decimal digits and a two-digit exponent, all in BCD, with the sign encoded as an
extra nibble.



### Floating-point representations across hardware

The sign-exponent-mantissa structure of IEEE 754 (1985) is now standard, but
before it every manufacturer did something different:

- *IBM System/360* (1964): base-16 floating point. The exponent counted
  powers of 16, which gave a wider range but fewer significant bits than base-2
  for the same word width.
- *Cray-1* (1976): its own 64-bit format with a 15-bit exponent biased by
  16384, no denormals, no NaN (speed above all).
- *DEC VAX* (1977): four different float formats (F, D, G, H), all
  little-endian in a way that made the bytes look scrambled on other machines.
- *Intel 8087* (1980): 80-bit extended precision, which still survives as the
  x87 `long double` on x86 today.

IEEE 754 unified most of this in 1985 and its 2008 revision added half-precision
(float16, now widely used in machine learning) and decimal floating-point
formats for financial applications.



### The systems in this repository

The files here explore two systems that take a different philosophical approach:
instead of adding a sign convention on top of a positive base, they build
negativity directly into the base or the digit set.

#### Negabinary (base -2)

Use -2 as the base instead of +2. Bit positions still hold only 0 or 1, but
the place values alternate sign: ..., +16, -8, +4, -2, +1. Negative numbers
appear naturally, thers is no sign bit, no two's complement adjustment. The
addition carry can be -1, 0, or +1 instead of just 0 or 1, which is the price
paid for the sign-free representation. Every integer has a unique representation
and there is exactly one zero.

The Soviet mathematician Vitold Krylov and others studied negative-base systems
in the 1950s. They never made it into production hardware, but they are a clean
demonstration that the base itself can carry sign information.

#### Balanced ternary (base 3, digits -1, 0, +1)

Use base 3 with the digit set {-1, 0, +1} (written T, 0, 1). The digits are
symmetric around zero, so negation is just a trit flip: swap every +1 for -1
and vice versa. This makes subtraction essentially free on top of addition.
Rounding is also naturally unbiased because the middle digit is 0, so
round-to-nearest has no "which way does the half go" ambiguity.

The only balanced ternary computer ever built for production was the *Setun*,
designed by Nikolay Brusentsov at Moscow State University in 1958. It ran until
the mid-1960s and was reportedly more reliable and economical than contemporary
binary machines of the same scale. A follow-up, the Setun-70, was built in 1970.
No balanced ternary machine has been built since, largely because the world had
already committed to binary electronics, but the elegance of the system is
frequently revisited in computer science education.



### Files

| File                  | Description                                                        |
|-----------------------|--------------------------------------------------------------------|
| `negabinary.py`       | Negabinary conversion, arithmetic, and fixed-point in Python       |
| `negabinary.c`        | Same in C, with explicit bit manipulation                          |
| `negabinary.md`       | Explanation of the negabinary system                               |
| `balanced_ternary.py` | Balanced ternary conversion, arithmetic, and fixed-point in Python |
| `balanced_ternary.c`  | Same in C, with packed 2-bit trit representation                   |
| `balanced_ternary.md` | Explanation of the balanced ternary system                         |



### Building and running

```sh
gcc -Wall -Wextra -o negabinary negabinary.c -lm
gcc -Wall -Wextra -o balanced_ternary balanced_ternary.c -lm

./negabinary
./balanced_ternary

python negabinary.py
python balanced_ternary.py
```



### Further reading

- Knuth, D. E. *The Art of Computer Programming*, Vol. 2
  (*§4.1: covers non-standard positional systems including negative bases.*)
- Avizienis, A. (1961). Signed-digit number representations for fast parallel arithmetic.
  *IRE Transactions on Electronic Computers*, EC-10(3), 389-400.
- Brusentsov, N. P., & Ramil Alvarez, J. (2011). Ternary Computers: The Setun and the Setun 70.
  In E. Proydakov & J. Impagliazzo (Eds.), *Perspectives on Soviet and Russian Computing*
  (Vol. 357, pp. 74-80). Springer Berlin / Heidelberg. https://doi.org/10.1007/978-3-642-22816-2_10
- IEEE 754-2008 standard. (*The definitive reference for modern floating-point.*)
  See e.g., https://en.wikipedia.org/wiki/IEEE_754-2008_revision.
