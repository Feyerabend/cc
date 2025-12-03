from functools import reduce

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

class SymbolicFraction(Fraction):
    def __init__(self, numerator, denominator):
        super().__init__(numerator, denominator)
        self.symbolic_expr = f"{self.numerator}/{self.denominator}"

    def __add__(self, other):
        expr = f"({self.symbolic_expr} + {other.symbolic_expr})"
        num = self.numerator * other.denominator + self.denominator * other.numerator
        denom = self.denominator * other.denominator
        result = SymbolicFraction(num, denom)
        result.symbolic_expr = expr
        return result

    def __sub__(self, other):
        expr = f"({self.symbolic_expr} - {other.symbolic_expr})"
        num = self.numerator * other.denominator - self.denominator * other.numerator
        denom = self.denominator * other.denominator
        result = SymbolicFraction(num, denom)
        result.symbolic_expr = expr
        return result

    def __mul__(self, other):
        expr = f"({self.symbolic_expr} * {other.symbolic_expr})"
        num = self.numerator * other.numerator
        denom = self.denominator * other.denominator
        result = SymbolicFraction(num, denom)
        result.symbolic_expr = expr
        return result

    def __truediv__(self, other):
        expr = f"({self.symbolic_expr} / {other.symbolic_expr})"
        num = self.numerator * other.denominator
        denom = self.denominator * other.numerator
        result = SymbolicFraction(num, denom)
        result.symbolic_expr = expr
        return result

    def __str__(self):
        return f"{self.symbolic_expr} = {self.numerator}/{self.denominator}"

    # comparison operations (returns boolean)
    def is_equal_to(self, other):
        return self.numerator * other.denominator == self.denominator * other.numerator

    def is_greater_than(self, other):
        return self.numerator * other.denominator > self.denominator * other.numerator

    def is_less_than(self, other):
        return self.numerator * other.denominator < self.denominator * other.numerator

    # conditional expression
    def if_greater_than(self, other, result_if_true, result_if_false):
        if self.is_greater_than(other):
            return result_if_true
        else:
            return result_if_false

# example
f1 = SymbolicFraction(1, 2)
f2 = SymbolicFraction(3, 4)

# symbolic representation without evaluation
symbolic_sum = f1 + f2
print(symbolic_sum)  # output: "(1/2 + 3/4) = 5/4"

# conditional check
result = f1.if_greater_than(f2, "f1 is greater", "f2 is greater")
print(result)  # output: "f2 is greater"
