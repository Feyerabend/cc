
## One Complement

One's complement is a way of representing signed integers in binary. In this system, positive
numbers are represented as usual in binary, while negative numbers are obtained by inverting
(flipping) all bits of the corresponding positive number. This means that for an n-bit system,
a number x is represented as:
- x (if positive) -> standard binary representation.
- -x (if negative) -> bitwise NOT (~x) of the positive counterpart.

A key characteristic of one's complement is that it has two representations of zero: all 0s
(positive zero) and all 1s (negative zero). This can lead to some extra handling in arithmetic
operations.

### Simulation: Basic Arithmetic in One's Complement

Addition in one's complement follows standard binary addition, but with an extra step called
end-around carry:
*if there is a carry from the most significant bit, it is added back to the least significant bit.*

Here's a Python implementation that simulates an n-bit one's complement system, including negation, addition, and subtraction.

```python
def ones_complement(value, bits):
    if value >= 0:
        return value & ((1 << bits) - 1)  # mask to fit within bit-width
    else:
        return (~(-value)) & ((1 << bits) - 1)  # invert bits of the magnitude

def add_ones_complement(a, b, bits):
    result = (a + b) & ((1 << bits) - 1)  # add and mask within bit-width
    if result >= (1 << bits):  # if there is an overflow, apply end-around carry
        result = (result + 1) & ((1 << bits) - 1)
    return result

def subtract_ones_complement(a, b, bits):
    return add_ones_complement(a, ones_complement(-b, bits), bits)

def display(value, bits):
    return f"{value:0{bits}b}"

# example
bits = 4  # 4-bit one's complement system
a = ones_complement(5, bits)   # 5 in one's complement
b = ones_complement(-3, bits)  # -3 in one's complement

print(f"5 in one's complement:  {display(a, bits)}")
print(f"-3 in one's complement: {display(b, bits)}")

sum_result = add_ones_complement(a, b, bits)
print(f"5 + (-3) in one's complement: {display(sum_result, bits)}")

sub_result = subtract_ones_complement(a, b, bits)
print(f"5 - (-3) in one's complement: {display(sub_result, bits)}")
```


#### Explanation of Output for a 4-bit System

1. 5 is represented as 0101 in 4-bit one's complement.

2. -3 is obtained by flipping 0011 (3 in binary), resulting in 1100.

3. Addition 5 + (-3):
- 0101 + 1100 = 0001 (with carry)
- End-around carry: Add 1 -> 0010 (which is +2 in one's complement).

4. Subtraction 5 - (-3):
- Equivalent to 5 + 3, which results in 1000 (-8, demonstrating an overflow in 4-bit representation).
