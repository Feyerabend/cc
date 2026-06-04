"""
Negabinary (base -2): a positional system using bits {0, 1} but base -2.
Place values alternate sign: ..., +16, -8, +4, -2, +1.
No sign bit needed -- negative numbers arise from the alternating place values.
"""

import math
import fractions


def to_negabinary(n):
    """
    Convert integer n to a negabinary string (MSB first).

    At each step we need remainder in {0, 1} such that:
        n = quotient * (-2) + remainder

    Using n % 2 always gives remainder in {0, 1} (Python's % is non-negative
    for positive divisor 2), and the next n is -(n // 2).
    """
    if n == 0:
        return "0"
    bits = []
    while n != 0:
        remainder = n % 2
        n = -(n // 2)
        bits.append(remainder)
    return "".join(str(b) for b in reversed(bits))


def from_negabinary(s):
    """Convert negabinary string to integer."""
    result = 0
    base = 1
    for bit in reversed(s):
        result += int(bit) * base
        base *= -2
    return result


def nb_negate(s):
    """Negate a negabinary number (no simple bit-flip rule; goes via int)."""
    return to_negabinary(-from_negabinary(s))


def nb_add(a, b):
    """
    Add two negabinary strings.

    Core rule at each bit position:
        s     = bit_a + bit_b + carry
        bit   = s & 1          (always 0 or 1)
        carry = -(s >> 1)      (can be 0, +1, or -1)
    """
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


def nb_subtract(a, b):
    """Subtract b from a."""
    return nb_add(a, nb_negate(b))


def nb_multiply(a, b):
    """
    Multiply two negabinary strings using long multiplication.

    For each set bit of b at position i, add a shifted left by i positions.
    Shifting left by i in negabinary multiplies by (-2)^i, which is exactly
    the place value at that position -- so the partial products are correct.
    """
    result = "0"
    for i, ch in enumerate(reversed(b)):
        if ch == "1":
            shifted = a + "0" * i
            result = nb_add(result, shifted)
    return result


def _to_negabinary_bits_lsb(n):
    """Return negabinary bits of integer n, LSB first."""
    if n == 0:
        return [0]
    bits = []
    while n != 0:
        remainder = n % 2
        n = -(n // 2)
        bits.append(remainder)
    return bits


def to_nb_float(x, precision=12):
    """
    Convert float x to negabinary fixed-point representation.
    Returns (integer_part_string, fractional_bit_list).

    Uses even precision p so that (-2)^p = 2^p (positive), allowing us to
    scale x by 2^p, convert the resulting integer to negabinary, and split
    the low p bits as the fractional part and the remaining high bits as the
    integer part. The fractional bits at index i represent position -(p - i)
    in negabinary, i.e., (-2)^-(p-i).
    """
    p = precision if precision % 2 == 0 else precision + 1
    scale = 2 ** p

    x_frac = fractions.Fraction(x).limit_denominator(10 ** 9)
    x_int = round(float(x_frac * scale))

    all_bits = _to_negabinary_bits_lsb(x_int)
    while len(all_bits) < p:
        all_bits.append(0)

    frac_bits = all_bits[:p]
    int_bits  = all_bits[p:]

    int_str = "0" if not int_bits else "".join(str(b) for b in reversed(int_bits))
    return int_str, frac_bits, p


def nb_frac_value(frac_bits, p):
    """
    Compute the decimal value of fractional negabinary bits.
    frac_bits[0] is at negabinary position -p, frac_bits[i] at -(p - i).
    """
    return sum(b * ((-2) ** -(p - i)) for i, b in enumerate(frac_bits))


def nb_float_value(int_str, frac_bits, p):
    return from_negabinary(int_str) + nb_frac_value(frac_bits, p)


def demo_place_values():
    print("=== Place values: (-2)^n for n = 7 down to -4 ===\n")
    print(f"  {'position':>9}   {'value':>8}")
    print(f"  {'':->9}   {'':->8}")
    for n in range(7, -5, -1):
        val = (-2) ** n
        label = f"(-2)^{n}"
        print(f"  {label:>9}   {val:>8}")


def demo_conversion():
    print("\n=== Conversion: integer <-> negabinary ===\n")
    print(f"  {'n':>5}   {'negabinary':>12}   {'back':>5}")
    print(f"  {'':->5}   {'':->12}   {'':->5}")
    for n in range(-13, 14):
        nb = to_negabinary(n)
        back = from_negabinary(nb)
        print(f"  {n:>5}   {nb:>12}   {back:>5}")


def demo_negation():
    print("\n=== Negation (converts through int; no simple bit-flip rule) ===\n")
    for n in [5, -5, 6, -6, 13, -13, 0]:
        nb     = to_negabinary(n)
        neg_nb = nb_negate(nb)
        print(f"  {n:>4}  {nb:>10}   ->  {neg_nb:>10}  = {from_negabinary(neg_nb)}")


def demo_carry_table():
    print("\n=== Carry table for negabinary addition ===\n")
    print(f"  {'a':>3}  {'b':>3}  {'carry_in':>9}  {'total':>6}  {'bit':>4}  {'carry_out':>10}")
    print(f"  {'':->3}  {'':->3}  {'':->9}  {'':->6}  {'':->4}  {'':->10}")
    for carry_in in [0, 1, -1]:
        for a in [0, 1]:
            for b in [0, 1]:
                s         = a + b + carry_in
                bit       = s & 1
                carry_out = -(s >> 1)
                if 0 <= bit <= 1:
                    print(f"  {a:>3}  {b:>3}  {carry_in:>9}  {s:>6}  {bit:>4}  {carry_out:>10}")


def demo_addition():
    print("\n=== Addition ===\n")
    pairs = [(5, 3), (5, -3), (-5, -3), (6, 6), (13, -7), (0, -9)]
    for x, y in pairs:
        ax        = to_negabinary(x)
        ay        = to_negabinary(y)
        result_nb  = nb_add(ax, ay)
        result_int = from_negabinary(result_nb)
        print(f"  {x:>4} ({ax:>8}) + {y:>4} ({ay:>8})"
              f"  =  {result_nb:>10}  = {result_int}  (expected {x + y})")


def demo_subtraction():
    print("\n=== Subtraction ===\n")
    pairs = [(5, 3), (3, 5), (-5, -3), (10, 4), (6, -2)]
    for x, y in pairs:
        ax        = to_negabinary(x)
        ay        = to_negabinary(y)
        result_nb  = nb_subtract(ax, ay)
        result_int = from_negabinary(result_nb)
        print(f"  {x:>4} ({ax:>8}) - {y:>4} ({ay:>8})"
              f"  =  {result_nb:>10}  = {result_int}  (expected {x - y})")


def demo_multiplication():
    print("\n=== Multiplication ===\n")
    pairs = [(3, 4), (-3, 4), (-3, -4), (5, 5), (6, -3), (2, -2)]
    for x, y in pairs:
        ax        = to_negabinary(x)
        ay        = to_negabinary(y)
        result_nb  = nb_multiply(ax, ay)
        result_int = from_negabinary(result_nb)
        print(f"  {x:>4} ({ax:>7}) * {y:>4} ({ay:>7})"
              f"  =  {result_nb:>12}  = {result_int}  (expected {x * y})")


def demo_float():
    print("\n=== Floating point in negabinary ===\n")
    print(f"  {'x':>8}   {'int part':>8}   {'frac bits':>14}   {'reconstructed':>14}")
    print(f"  {'':->8}   {'':->8}   {'':->14}   {'':->14}")
    for x in [0.5, -0.5, 0.25, -0.25, 1.25, -3.75, 0.1, -0.1]:
        ib, fb, p  = to_nb_float(x, 12)
        frac_str   = "".join(str(b) for b in fb)
        reconstructed = nb_float_value(ib, fb, p)
        print(f"  {x:>8.4f}   {ib:>8}   {frac_str:>14}   {reconstructed:>14.8f}")


if __name__ == "__main__":
    demo_place_values()
    demo_conversion()
    demo_negation()
    demo_carry_table()
    demo_addition()
    demo_subtraction()
    demo_multiplication()
    demo_float()
