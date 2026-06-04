"""
Balanced ternary: a base-3 system with digits {-1, 0, +1}.
Digits are written as T (for -1), 0, and 1.
"""


TRIT_CHAR = {-1: "T", 0: "0", 1: "1"}
CHAR_TRIT = {"T": -1, "0": 0, "1": 1}


def to_balanced_ternary(n):
    """Convert integer n to a balanced ternary string."""
    if n == 0:
        return "0"
    digits = []
    while n != 0:
        remainder = n % 3
        if remainder == 2:
            remainder = -1
        n = (n - remainder) // 3
        digits.append(remainder)
    return "".join(TRIT_CHAR[d] for d in reversed(digits))


def from_balanced_ternary(s):
    """Convert balanced ternary string to integer."""
    result = 0
    for ch in s:
        result = result * 3 + CHAR_TRIT[ch]
    return result


def bt_negate(s):
    """Negate by flipping every trit: T<->1, 0 stays 0."""
    return s.translate(str.maketrans("T01", "10T"))


def _str_to_trits(s):
    return [CHAR_TRIT[c] for c in s]


def _trits_to_str(trits):
    trimmed = trits[:]
    while len(trimmed) > 1 and trimmed[0] == 0:
        trimmed.pop(0)
    return "".join(TRIT_CHAR[d] for d in trimmed)


def bt_add(a, b):
    """Add two balanced ternary strings."""
    da = [CHAR_TRIT[c] for c in reversed(a)]
    db = [CHAR_TRIT[c] for c in reversed(b)]
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
    return "".join(TRIT_CHAR[d] for d in reversed(result))


def bt_subtract(a, b):
    """Subtract b from a: just add the negation of b."""
    return bt_add(a, bt_negate(b))


def bt_multiply(a, b):
    """Multiply two balanced ternary strings."""
    result = "0"
    for i, ch in enumerate(reversed(b)):
        d = CHAR_TRIT[ch]
        if d == 0:
            continue
        shifted = a + "0" * i
        if d == -1:
            shifted = bt_negate(shifted)
        result = bt_add(result, shifted)
    return result


def bt_frac_value(trits):
    """
    Compute the decimal value of a fractional balanced ternary sequence.
    trits: list of {-1, 0, 1} representing positions 3^-1, 3^-2, ...
    """
    return sum(t * (3 ** -(i + 1)) for i, t in enumerate(trits))


def to_bt_float(x, precision=12):
    """
    Convert a float to balanced ternary.
    Returns (integer_part_string, fractional_trit_list).
    Uses floor for the integer part so the fractional remainder is always >= 0.
    """
    import math
    int_part = math.floor(x)
    frac = x - int_part

    frac_trits = []
    for _ in range(precision):
        frac *= 3
        t = round(frac)
        t = max(-1, min(1, t))
        frac -= t
        frac_trits.append(t)

    return to_balanced_ternary(int_part), frac_trits


def bt_float_value(int_str, frac_trits):
    return from_balanced_ternary(int_str) + bt_frac_value(frac_trits)


def demo_conversion():
    print("=== Conversion: integer <-> balanced ternary ===\n")
    print(f"  {'n':>5}   {'bt':>8}   {'back':>5}")
    print(f"  {'':->5}   {'':->8}   {'':->5}")
    for n in range(-13, 14):
        bt = to_balanced_ternary(n)
        back = from_balanced_ternary(bt)
        print(f"  {n:>5}   {bt:>8}   {back:>5}")


def demo_negation():
    print("\n=== Negation (just flip T<->1) ===\n")
    for n in [5, -5, 13, -13, 0]:
        bt = to_balanced_ternary(n)
        neg = bt_negate(bt)
        print(f"  {n:>4}  {bt:>6}   ->  {neg:>6}  = {from_balanced_ternary(neg)}")


def demo_addition():
    print("\n=== Addition ===\n")
    pairs = [(5, 3), (5, -3), (-5, -3), (13, -7), (0, -9)]
    for x, y in pairs:
        ax = to_balanced_ternary(x)
        ay = to_balanced_ternary(y)
        result_bt = bt_add(ax, ay)
        result_int = from_balanced_ternary(result_bt)
        print(f"  {x:>4} ({ax:>6}) + {y:>4} ({ay:>6})"
              f" = {result_bt:>8}  = {result_int}  (expected {x + y})")


def demo_subtraction():
    print("\n=== Subtraction (add negation) ===\n")
    pairs = [(5, 3), (3, 5), (-5, -3), (10, 4)]
    for x, y in pairs:
        ax = to_balanced_ternary(x)
        ay = to_balanced_ternary(y)
        result_bt = bt_subtract(ax, ay)
        result_int = from_balanced_ternary(result_bt)
        print(f"  {x:>4} ({ax:>6}) - {y:>4} ({ay:>6})"
              f" = {result_bt:>8}  = {result_int}  (expected {x - y})")


def demo_multiplication():
    print("\n=== Multiplication ===\n")
    pairs = [(3, 4), (-3, 4), (-3, -4), (5, 5), (9, -3)]
    for x, y in pairs:
        ax = to_balanced_ternary(x)
        ay = to_balanced_ternary(y)
        result_bt = bt_multiply(ax, ay)
        result_int = from_balanced_ternary(result_bt)
        print(f"  {x:>4} ({ax:>5}) * {y:>4} ({ay:>5})"
              f" = {result_bt:>9}  = {result_int}  (expected {x * y})")


def demo_float():
    print("\n=== Floating point in balanced ternary ===\n")
    print(f"  {'x':>8}   {'int part':>8}   {'frac trits':>14}   {'reconstructed':>14}")
    print(f"  {'':->8}   {'':->8}   {'':->14}   {'':->14}")
    for x in [0.5, -0.5, 1.0 / 3.0, -1.0 / 3.0, 1.25, -3.75, 0.1]:
        ib, fb = to_bt_float(x)
        frac_str = "".join(TRIT_CHAR[t] for t in fb)
        reconstructed = bt_float_value(ib, fb)
        print(f"  {x:>8.4f}   {ib:>8}   {frac_str:>14}   {reconstructed:>14.8f}")


def demo_trit_addition_table():
    print("\n=== Trit addition table (a + b = carry·3 + trit) ===\n")
    print(f"  {'a':>3}  {'b':>3}  {'sum':>4}  {'trit':>5}  {'carry':>6}")
    print(f"  {'':->3}  {'':->3}  {'':->4}  {'':->5}  {'':->6}")
    for a in [-1, 0, 1]:
        for b in [-1, 0, 1]:
            s = a + b
            trit = s % 3
            if trit == 2:
                trit = -1
            carry = (s - trit) // 3
            print(f"  {a:>3}  {b:>3}  {s:>4}  {trit:>5}  {carry:>6}")


if __name__ == "__main__":
    demo_conversion()
    demo_negation()
    demo_trit_addition_table()
    demo_addition()
    demo_subtraction()
    demo_multiplication()
    demo_float()
