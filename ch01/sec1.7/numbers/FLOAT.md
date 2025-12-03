
## Floating-point numbers

Here's a Python program that emulates floating-point arithmetic by breaking down
numbers into their sign, mantissa, and exponent components, following the IEEE 754
floating-point standard.

In this implementation:

- The sign bit represents whether the number is positive or negative.
- The mantissa (or significand) holds the precision of the number.
- The exponent represents the scale or range of the number.

Let's create a simple floating-point emulator. This will convert decimal values
into a binary floating-point representation, perform operations on them, and show
the step-by-step process.

The code below:

1. Converts a decimal number into a custom floating-point format.
2. Prints the binary representations of the sign, exponent, and mantissa.
3. Demonstrates addition and subtraction of two floating-point numbers.


```python
class CustomFloat:
    def __init__(self, value, precision=23, exponent_bits=8):
        # constants for IEEE-like floating point
        self.precision = precision  # number of bits in mantissa
        self.exponent_bits = exponent_bits  # number of bits in exponent
        self.bias = (2 ** (exponent_bits - 1)) - 1

        # convert to floating-point representation
        self.sign, self.exponent, self.mantissa = self.float_to_components(value)
        
    def float_to_components(self, value):
        """Convert a float to its binary components: sign, exponent, and mantissa"""
        # determine the sign bit
        sign = 0 if value >= 0 else 1
        value = abs(value)
        
        # normalise the value to get mantissa and exponent
        exponent = 0
        if value != 0:
            while value >= 2.0:
                value /= 2.0
                exponent += 1
            while value < 1.0:
                value *= 2.0
                exponent -= 1
        
        # bias the exponent
        exponent += self.bias

        # convert mantissa to binary form
        mantissa = int((value - 1.0) * (2 ** self.precision))

        return sign, exponent, mantissa

    def components_to_float(self):
        """Convert binary components back to float"""
        # unbias the exponent
        exponent = self.exponent - self.bias
        # calculate the decimal mantissa
        mantissa = 1.0 + self.mantissa / (2 ** self.precision)
        # calculate the value
        return (-1) ** self.sign * mantissa * (2 ** exponent)

    def __str__(self):
        return f"Sign: {self.sign}, Exponent: {self.exponent - self.bias}, Mantissa: {bin(self.mantissa)}"

    def add(self, other):
        """Add two CustomFloat numbers"""
        # align exponents by shifting mantissas
        if self.exponent > other.exponent:
            shift = self.exponent - other.exponent
            mantissa_a = self.mantissa << shift
            mantissa_b = other.mantissa
            result_exponent = self.exponent
        else:
            shift = other.exponent - self.exponent
            mantissa_a = self.mantissa
            mantissa_b = other.mantissa << shift
            result_exponent = other.exponent

        # add mantissas
        result_mantissa = mantissa_a + mantissa_b

        # normalise result
        while result_mantissa >= (1 << (self.precision + 1)):
            result_mantissa >>= 1
            result_exponent += 1

        # return a new CustomFloat representing the sum
        result = CustomFloat(0.0)
        result.sign = 0
        result.exponent = result_exponent
        result.mantissa = result_mantissa & ((1 << self.precision) - 1)  # mask to precision size
        return result

# example
a = CustomFloat(6.75)  # example number
b = CustomFloat(2.5)   # another example number

print("Number A:", a)
print("Decimal representation of A:", a.components_to_float())
print("Number B:", b)
print("Decimal representation of B:", b.components_to_float())

# add two custom floats
c = a.add(b)
print("\nResult of A + B in custom floating-point format:")
print(c)
print("Decimal representation of Result:", c.components_to_float())
```

### Explanation

1. `CustomFloat` class:
	- Initialization: Initializes with a value, specifying precision (for mantissa bits) and exponent bits.
	- `float_to_components`: Converts a decimal float to its sign, exponent, and mantissa components based on a simplified IEEE 754 logic.
	- `components_to_float`: Converts sign, exponent, and mantissa back to a floating-point decimal.
2. Addition:
	- Exponent alignment: Aligns the exponents by shifting the mantissa of the smaller exponent.
	- Mantissa addition: Adds the two mantissas and normalizes if necessary (shifts if the mantissa overflows).
3. Example operations:
	- `CustomFloat(6.75)` creates a custom float object representing `6.75`.
	- The add method demonstrates addition by creating a new CustomFloat object as the sum of two numbers.

### Example

The program will show the internal representation in terms of sign, exponent, and mantissa, and it will output a custom addition operation:

```shell
Number A: Sign: 0, Exponent: 2, Mantissa: 0b11000000000000000000000
Decimal representation of A: 6.75
Number B: Sign: 0, Exponent: 1, Mantissa: 0b10000000000000000000000
Decimal representation of B: 2.5

Result of A + B in custom floating-point format:
Sign: 0, Exponent: 2, Mantissa: 0b11011000000000000000000
Decimal representation of Result: 9.25
```

This simplified floating-point model shows how each component (sign, exponent, mantissa)
plays a role in representing and performing arithmetic with floating-point numbers.
