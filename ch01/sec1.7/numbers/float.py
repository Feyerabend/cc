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
        # determine sign bit
        sign = 0 if value >= 0 else 1
        value = abs(value)
        
        # normalize the value to get mantissa and exponent
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
        # unbias exponent
        exponent = self.exponent - self.bias
        # calculate decimal mantissa
        mantissa = 1.0 + self.mantissa / (2 ** self.precision)
        # calculate value
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

        # normalize result
        while result_mantissa >= (1 << (self.precision + 1)):
            result_mantissa >>= 1
            result_exponent += 1

        # return a new CustomFloat representing sum
        result = CustomFloat(0.0)
        result.sign = 0
        result.exponent = result_exponent
        result.mantissa = result_mantissa & ((1 << self.precision) - 1)  # mask to precision size
        return result

# example
a = CustomFloat(6.75)
b = CustomFloat(2.5)

print("Number A:", a)
print("Decimal representation of A:", a.components_to_float())
print("Number B:", b)
print("Decimal representation of B:", b.components_to_float())

# add two floats
c = a.add(b)
print("\nResult of A + B in custom floating-point format:")
print(c)
print("Decimal representation of Result:", c.components_to_float())
