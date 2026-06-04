
## Balanced Ternary

Balanced ternary is a base-3 numeral system, but instead of the usual digits 0, 1, 2
it uses the digits *-1, 0, +1*, commonly written as *T, 0, 1* (where T stands for
"negative one"). Because the digits include negative values directly, no separate sign
bit or two's complement trick is needed. Negative numbers arise naturally, just like
in negabinary.

### Place values

Each position represents a power of 3:

| Position | 3       | 2      | 1      | 0      |
|----------|---------|--------|--------|--------|
| Value    | 3³ = 27 | 3² = 9 | 3¹ = 3 | 3⁰ = 1 |

A digit at position n contributes `digit × 3^n`, where digit ∈ {-1, 0, +1}.

#### Example: the number 5

We need 9·0 + 3·2 + 1·? — but 2 is not a valid digit. Instead:

```
5 = 9·0 + 3·1 + 1·(-1) = 0·9 + 1·3 + T·1
  → balanced ternary: 1 T  (read: one-tee)
```

Check: 1×3 + (-1)×1 = 3 - 1 = 2... let's redo carefully:

```
5 = 6 - 1 = 2×3 - 1×1
  but digit 2 is invalid, so replace 2×3 with 1×9 - 1×3:
5 = 1×9 + (-1)×3 + (-1)×1 = 9 - 3 - 1 = 5  ✓
  → balanced ternary: 1 T T
```

### Properties

- Every integer has a *unique* balanced ternary representation.
- The range of an n-trit number is *-(3ⁿ-1)/2* to *+(3ⁿ-1)/2*.
  For 4 trits: -40 to +40.
- Negation is trivial: *flip every digit* (T<->1, 0 stays 0). No two's complement needed.
- Rounding is natural: the "round half" problem disappears because the middle digit is 0.
- Historically used in the Soviet *Setun* computer (1958), the only balanced ternary
  computer ever built for production use.


### Conversion: integer → balanced ternary

The algorithm is like normal base-3 conversion but we adjust remainders to stay in {-1, 0, 1}:

1. Divide n by 3.
2. If remainder is 0 or 1, keep it.
3. If remainder is 2, record -1 (T) and add 1 to the quotient (carry).
4. Repeat until quotient is 0.

```python
def to_balanced_ternary(n):
    if n == 0:
        return "0"
    digits = []
    while n != 0:
        remainder = n % 3
        if remainder == 2:
            remainder = -1
        n = (n - remainder) // 3
        digits.append(remainder)
    return "".join("T10"[d] for d in reversed(digits))
```

The string uses `T` for -1, `0` for 0, `1` for +1.


### Conversion: balanced ternary → integer

```python
def from_balanced_ternary(s):
    value_of = {"T": -1, "0": 0, "1": 1}
    result = 0
    for ch in s:
        result = result * 3 + value_of[ch]
    return result
```


### Arithmetic

#### Negation

Flip every trit: T becomes 1, 1 becomes T, 0 stays 0.

```python
def bt_negate(s):
    return s.translate(str.maketrans("T01", "10T"))
```

This is far simpler than two's complement negation.


#### Addition

The trit addition table (ignoring carry for now):

| a  | b  | sum | carry |
|----|----|-----|-------|
|  0 |  0 |  0  |  0    |
|  0 |  1 |  1  |  0    |
|  0 | -1 | -1  |  0    |
|  1 |  1 | -1  |  1    |  <- 1+1 = 3-1, so trit=-1, carry=1
|  1 | -1 |  0  |  0    |
| -1 | -1 |  1  | -1    |  <- -1-1 = -3+1, so trit=1, carry=-1

The carry can be -1, 0, or +1 — itself a balanced ternary digit!

```python
def bt_add(a, b):
    """Add two balanced ternary strings, return result string."""
    map_digit = {"T": -1, "0": 0, "1": 1}
    da = [map_digit[c] for c in reversed(a)]
    db = [map_digit[c] for c in reversed(b)]
    length = max(len(da), len(db)) + 1
    da += [0] * (length - len(da))
    db += [0] * (length - len(db))

    result = []
    carry = 0
    for i in range(length):
        s = da[i] + db[i] + carry
        trit = s % 3
        if trit == 2:
            trit = -1
        carry = (s - trit) // 3
        result.append(trit)

    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return "".join("T10"[d] for d in reversed(result))
```


#### Subtraction

Subtraction is addition of the negation:

```python
def bt_subtract(a, b):
    return bt_add(a, bt_negate(b))
```


#### Multiplication

Long multiplication: for each trit of b (scaled by its position), add the
shifted version of a (or its negation if the trit is -1):

```python
def bt_multiply(a, b):
    map_digit = {"T": -1, "0": 0, "1": 1}
    result = "0"
    for i, ch in enumerate(reversed(b)):
        d = map_digit[ch]
        if d == 0:
            continue
        shifted = a + "0" * i
        if d == -1:
            shifted = bt_negate(shifted)
        result = bt_add(result, shifted)
    return result
```


### Comparison table: binary vs balanced ternary

| Integer | Binary (2's complement) | Balanced ternary |
|---------|------------------------|-----------------|
| -5      | ...11111011            | T11             |
| -4      | ...11111100            | TT1             |
| -3      | ...11111101            | T0              |
| -2      | ...11111110            | T1              |
| -1      | ...11111111            | T               |
|  0      | 0                      | 0               |
|  1      | 1                      | 1               |
|  2      | 10                     | 1T              |
|  3      | 11                     | 10              |
|  4      | 100                    | 11              |
|  5      | 101                    | 1TT             |

Notice: negating just flips every T<->1. Clean and symmetric.


### Floating point in balanced ternary

The same ideas from negabinary floats apply, but even more naturally here:

- **No sign bit**: handled by the digits themselves.
- **Mantissa**: fractional trits represent 3⁻¹ = 1/3, 3⁻² = 1/9, etc., with values
  in {-1/3, 0, +1/3}, {-1/9, 0, +1/9}, and so on.
- **Exponent**: a conventional positive base-3 exponent works cleanly. Unlike negabinary,
  there is no sign-flipping problem — 3^n is always positive.
- **Rounding**: because the digit set is symmetric around 0 and the middle digit is 0,
  balanced ternary has **perfect round-to-nearest** with no "round half up" bias.

```python
def bt_frac_value(trits, precision=12):
    """trits: list of {-1,0,1} for positions 3^-1, 3^-2, ..."""
    return sum(t * (3 ** -(i + 1)) for i, t in enumerate(trits))

def to_bt_float(x, precision=12):
    int_part = int(x)
    frac = x - int_part
    trits = []
    for _ in range(precision):
        frac *= 3
        t = round(frac)
        if t > 1:
            t = 1
        if t < -1:
            t = -1
        frac -= t
        trits.append(t)
    int_str = to_balanced_ternary(int_part)
    frac_str = "".join("T10"[d] for d in trits)
    return int_str, frac_str

for x in [0.5, -0.5, 1.333333, -3.75, 0.1]:
    ib, fb = to_bt_float(x)
    reconstructed = from_balanced_ternary(ib) + bt_frac_value(
        [{"T": -1, "0": 0, "1": 1}[c] for c in fb]
    )
    print(f"{x:7.4f}  int={ib:>6s}  frac={fb}  -> {reconstructed:.6f}")
```


### Summary

| Property            | Two's complement binary | Balanced ternary    |
|---------------------|-------------------------|---------------------|
| Digits              | 0, 1                    | -1, 0, +1           |
| Sign bit            | Required                | Not needed          |
| Negation            | Flip + 1                | Just flip           |
| Carry values        | 0 or 1                  | -1, 0, or +1        |
| Rounding bias       | Round-half-up bias      | Perfectly symmetric |
| Floating point sign | Needed                  | Not needed          |
| Real-world use      | Universal               | Setun (1958)        |

Balanced ternary is arguably the most mathematically elegant integer representation.
It is symmetric around zero, no sign bit, trivial negation, and perfect rounding.
Its main drawback is that modern hardware is built entirely around base-2,
so it stays a beautiful theoretical alternative.
