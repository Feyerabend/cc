
# Negabinary (Base -2)

Negabinary is a positional numeral system that uses **base -2** instead of the
usual base +2. Bits are still 0 or 1. But the place values alternate between
positive and negative, so negative numbers arise naturally without any sign bit
or two's complement convention.

## Place values

Each bit position n contributes `bit × (-2)^n`:

| Position | 7      | 6    | 5     | 4    | 3    | 2   | 1    | 0  |
|----------|--------|------|-------|------|------|-----|------|----|
| Value    | -128   | +64  | -32   | +16  | -8   | +4  | -2   | +1 |

Values alternate sign: even positions are positive, odd positions are negative.

### Example: the number -6

We need to find bits b_n such that Σ b_n × (-2)^n = -6.

```
-6 = -8 + 4 - 2 = 1×(-8) + 1×(+4) + 1×(-2) + 0×(+1)
   = 1×(-2)³ + 1×(-2)² + 1×(-2)¹ + 0×(-2)⁰
   -> negabinary: 1110
```

Check: -8 + 4 - 2 + 0 = -6  CORRECT


## Key properties

- Every integer has a **unique** negabinary representation.
- No sign bit is needed.
- The range of an n-bit number is roughly **-2(2^n)/3** to **+(2^n)/3**,
  alternating tighter on the negative or positive side depending on n.
- Positive integers tend to have bits set at even positions; negative integers
  tend to have bits set at odd positions - though both can mix freely.
- There is only **one zero** (unlike IEEE floats which have +0 and -0).
- No standard hardware support; it is a theoretical and educational curiosity.


## Conversion: integer -> negabinary

The algorithm mirrors ordinary base-2 conversion, but we divide by -2
and keep the remainder in {0, 1} at each step:

1. Compute `remainder = n % (-2)`.  
   Python's `%` always returns a non-negative result, so remainder ∈ {0, 1}.
2. Record the remainder as the next bit (LSB first).
3. Set `n = (n - remainder) // (-2)`.
4. Repeat until n = 0.

```python
def to_negabinary(n):
    if n == 0:
        return "0"
    bits = []
    while n != 0:
        remainder = n % (-2)
        n = (n - remainder) // (-2)
        bits.append(str(remainder))
    return "".join(reversed(bits))
```


## Conversion: negabinary -> integer

```python
def from_negabinary(s):
    result = 0
    base = 1
    for bit in reversed(s):
        result += int(bit) * base
        base *= -2
    return result
```


## Arithmetic

### Addition

In standard binary, adding two 1 bits gives sum 0 carry 1 (since 1+1 = 2 = 1×2¹).
In negabinary the carry propagates into base -2, so the rules differ:

| a | b | carry_in | total | bit | carry_out |
|---|---|----------|-------|-----|-----------|
| 0 | 0 |  0       |  0    |  0  |  0        |
| 0 | 0 |  1       |  1    |  1  |  0        |
| 0 | 1 |  0       |  1    |  1  |  0        |
| 0 | 1 |  1       |  2    |  0  | -1        |
| 1 | 1 |  0       |  2    |  0  | -1        |
| 1 | 1 |  1       |  3    |  1  | -1        |
| 0 | 0 | -1       | -1    |  1  |  1        |
| 0 | 1 | -1       |  0    |  0  |  0        |
| 1 | 1 | -1       |  1    |  1  |  0        |

The carry can be 0, +1, or -1. When `total = s`:

```
bit   = s & 1          (bottom bit, always 0 or 1)
carry = -(s >> 1)      (negate the upper part)
```

This single formula handles all cases correctly.

```python
def nb_add(a, b):
    """Add two negabinary strings, return result string."""
    da = [int(c) for c in reversed(a)]
    db = [int(c) for c in reversed(b)]
    length = max(len(da), len(db)) + 2
    da += [0] * (length - len(da))
    db += [0] * (length - len(db))

    result = []
    carry = 0
    for i in range(length):
        s = da[i] + db[i] + carry
        bit = s & 1
        carry = -(s >> 1)
        result.append(bit)

    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return "".join(str(b) for b in reversed(result))
```


### Subtraction

There is no trivial negation trick (unlike balanced ternary). The simplest
approach is to convert, negate in regular integers, then convert back - or
just add via the standard formula after computing the negabinary of -b:

```python
def nb_negate(s):
    """Negate a negabinary number by converting through int."""
    return to_negabinary(-from_negabinary(s))

def nb_subtract(a, b):
    """Subtract b from a."""
    return nb_add(a, nb_negate(b))
```

Note: unlike balanced ternary, negation has no simple bit-flip rule.
That is one of negabinary's less elegant properties.


### Multiplication

Long multiplication: shift a left by i positions (appending i zero bits)
for each set bit of b at position i, then add the partial products.
Because negabinary bits are only 0 or 1, no scaling is needed - just
include or skip each partial product:

```python
def nb_multiply(a, b):
    """Multiply two negabinary strings."""
    result = "0"
    for i, ch in enumerate(reversed(b)):
        if ch == "1":
            shifted = a + "0" * i
            result = nb_add(result, shifted)
    return result
```

Note: shifting left by 1 in negabinary multiplies by -2, not +2, so the
partial products are automatically signed correctly by the place values.


## Comparison table: binary vs negabinary

| Integer | Unsigned binary | Two's complement (8-bit) | Negabinary |
|---------|-----------------|--------------------------|------------|
| -7      | -               | 11111001                 | 1010101    |
| -6      | -               | 11111010                 | 1110       |
| -5      | -               | 11111011                 | 1011       |
| -4      | -               | 11111100                 | 1100       |
| -3      | -               | 11111101                 | 1101       |
| -2      | -               | 11111110                 | 10         |
| -1      | -               | 11111111                 | 11         |
|  0      | 0               | 00000000                 | 0          |
|  1      | 1               | 00000001                 | 1          |
|  2      | 10              | 00000010                 | 110        |
|  3      | 11              | 00000011                 | 111        |
|  4      | 100             | 00000100                 | 100        |
|  5      | 101             | 00000101                 | 101        |
|  6      | 110             | 00000110                 | 11010      |
|  7      | 111             | 00000111                 | 11011      |

Observe that small negative numbers like -1 and -2 are very compact (just
`11` and `10`), while some positive numbers like 6 and 7 need more bits than
their binary equivalents.


## Floating point in negabinary

Extending negabinary to fractions follows the same place-value logic.

### Fractional place values

Positions -1, -2, -3, ... represent (-2)^-1, (-2)^-2, (-2)^-3, ...:

| Position | -1     | -2    | -3      | -4      |
|----------|--------|-------|---------|---------|
| Value    | -1/2   | +1/4  | -1/8    | +1/16   |

Values alternate sign, just like the integer side.

### Structure of a negabinary float

With base -2, there is no sign bit needed. A practical layout:

```
[ exponent (standard positive base, biased) | mantissa (negabinary bits) ]
```

The exponent uses a conventional positive base (base 2 or base -2 are both
possible, but base 2 avoids sign-flip issues on odd exponents). The mantissa
encodes the fractional value in negabinary.

Because fractional negabinary can represent negative fractions naturally
(via odd-position bits), no sign bit is required anywhere.

### Key differences from IEEE 754

| Property             | IEEE 754           | Negabinary float        |
|----------------------|--------------------|-------------------------|
| Sign bit             | Required           | Not needed              |
| Fractional values    | All positive bits  | Alternating ±           |
| Negative fractions   | Need sign bit      | Fall out naturally      |
| Positive zero only   | +0 and -0 exist    | Only one zero           |
| Exponent sign flip   | Never              | Odd exponents flip sign |
| Rounding bias        | Round-half-even    | More complex            |

### Python demo

```python
def nb_frac_value(bits, precision=12):
    """Compute decimal value of fractional negabinary bits (list of 0/1)."""
    return sum(b * ((-2) ** -(i + 1)) for i, b in enumerate(bits))

def to_nb_float(x, precision=12):  # see negabinary.py for full version
    """
    Convert float x to negabinary.
    Returns (integer_part_string, fractional_bit_list).
    Uses floor so the fractional remainder is always >= 0.
    """
    import math
    int_part = math.floor(x)
    frac = x - int_part
    frac_bits = []
    for _ in range(precision):
        frac *= -2
        bit = int(frac)
        if frac < 0:
            bit = 0
        frac -= bit
        frac_bits.append(bit)
    return to_negabinary(int_part), frac_bits
```


## Summary: negabinary vs two's complement vs balanced ternary

| Property              | Two's complement | Negabinary      | Balanced ternary |
|-----------------------|------------------|-----------------|------------------|
| Base                  | +2               | -2              | -1, 0, +1 (±3)   |
| Sign bit              | Required         | Not needed      | Not needed       |
| Negation              | Flip + add 1     | No simple rule  | Just flip        |
| Carry values          | 0 or 1           | 0, +1, or -1    | -1, 0, or +1     |
| Unique zero           | No (+0/-0)       | Yes             | Yes              |
| Arithmetic carry rule | Simple           | Slightly tricky | Symmetric        |
| Hardware support      | Universal        | None            | None             |
