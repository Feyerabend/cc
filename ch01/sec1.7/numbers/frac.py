def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return abs(a)

class Fraction:
    def __init__(self, numerator, denominator):
        if denominator == 0:
            raise ValueError("Denominator cannot be zero.")
        common = gcd(numerator, denominator)
        self.numerator = numerator // common
        self.denominator = denominator // common

    def __str__(self):
        return f"{self.numerator}/{self.denominator}"

    def __add__(self, other):
        num = self.numerator * other.denominator + self.denominator * other.numerator
        denom = self.denominator * other.denominator
        return Fraction(num, denom)

    def __sub__(self, other):
        num = self.numerator * other.denominator - self.denominator * other.numerator
        denom = self.denominator * other.denominator
        return Fraction(num, denom)

    def __mul__(self, other):
        num = self.numerator * other.numerator
        denom = self.denominator * other.denominator
        return Fraction(num, denom)

    def __truediv__(self, other):
        num = self.numerator * other.denominator
        denom = self.denominator * other.numerator
        return Fraction(num, denom)

# example
f1 = Fraction(1, 2)
f2 = Fraction(3, 4)
print(f"Addition: {f1 + f2}")       # output: 5/4
print(f"Subtraction: {f1 - f2}")    # output: -1/4
print(f"Multiplication: {f1 * f2}") # output: 3/8
print(f"Division: {f1 / f2}")       # output: 2/3
