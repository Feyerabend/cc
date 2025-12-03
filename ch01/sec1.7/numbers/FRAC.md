
## Fractional numbers

In Python and C, fractional numbers can be represented and manipulated using
both floats and rational numbers, though rational numbers offer higher precision
in mathematical calculations.


### Representing fractions

Fractions are parts of a whole and can be represented as two integers: a
numerator (top part) and a denominator (bottom part). Working directly with
numerators and denominators instead of converting fractions to decimal
approximations (floats) avoids precision loss, which is common in floating-point
arithmetic.

In both Python and C, a fraction can be represented as a structure with two
integers: the numerator and the denominator. The key to calculating with fractions
lies in applying the appropriate rules of arithmetic and simplifying the fraction
by finding the *greatest common divisor* (GCD) of the numerator and denominator.


#### Simple fractional arithmetic rules

1. Addition:
$\frac{a}{b} + \frac{c}{d} = \frac{a \cdot d + b \cdot c}{b \cdot d}$


2. Subtraction:
$\frac{a}{b} - \frac{c}{d} = \frac{a \cdot d - b \cdot c}{b \cdot d}$


3. Multiplication:
$\frac{a}{b} \times \frac{c}{d} = \frac{a \cdot c}{b \cdot d}$


4. Division:
$\frac{a}{b} \div \frac{c}{d} = \frac{a \cdot d}{b \cdot c}$


To ensure the results are as simplified as possible, we divide both the
numerator and the denominator by their GCD after each operation.


#### Python

Here's how to implement a `Fraction` class in Python, along with a helper
function for the GCD:

```python
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
```


### C

In C, we can define a similar structure and functions for the four
basic arithmetic operations.

```c
#include <stdio.h>

typedef struct {
    int numerator;
    int denominator;
} Fraction;

int gcd(int a, int b) {
    while (b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

Fraction simplify(Fraction frac) {
    int common = gcd(frac.numerator, frac.denominator);
    frac.numerator /= common;
    frac.denominator /= common;
    return frac;
}

Fraction add(Fraction f1, Fraction f2) {
    Fraction result;
    result.numerator = f1.numerator * f2.denominator + f1.denominator * f2.numerator;
    result.denominator = f1.denominator * f2.denominator;
    return simplify(result);
}

Fraction subtract(Fraction f1, Fraction f2) {
    Fraction result;
    result.numerator = f1.numerator * f2.denominator - f1.denominator * f2.numerator;
    result.denominator = f1.denominator * f2.denominator;
    return simplify(result);
}

Fraction multiply(Fraction f1, Fraction f2) {
    Fraction result;
    result.numerator = f1.numerator * f2.numerator;
    result.denominator = f1.denominator * f2.denominator;
    return simplify(result);
}

Fraction divide(Fraction f1, Fraction f2) {
    Fraction result;
    result.numerator = f1.numerator * f2.denominator;
    result.denominator = f1.denominator * f2.numerator;
    return simplify(result);
}

void print_fraction(Fraction f) {
    printf("%d/%d\n", f.numerator, f.denominator);
}

int main() {
    Fraction f1 = {1, 2};
    Fraction f2 = {3, 4};

    printf("Addition: ");
    print_fraction(add(f1, f2));      // output: 5/4

    printf("Subtraction: ");
    print_fraction(subtract(f1, f2)); // output: -1/4

    printf("Multiplication: ");
    print_fraction(multiply(f1, f2)); // output: 3/8

    printf("Division: ");
    print_fraction(divide(f1, f2));   // output: 2/3

    return 0;
}
```

### Explanation

1. GCD Calculation: Both Python and C examples use the Euclidean algorithm to compute the GCD,
   ensuring each fraction is in its simplest form.
2. Arithmetic: Each operation follows the fraction arithmetic rules above, and the results are
   simplified before returning.
3. Division by zero: Both examples avoid cases where the denominator is zero, which would lead
   to an undefined fraction.

This setup in both Python and C will allow you to perform arithmetic operations with
fractions (without relying on floating-point approximations).



### Using symbolic logic

Incorporating symbolic logic into number calculations, particularly with fractions, allows
for a more flexible and expressive representation of operations. This could include representing
operations and expressions symbolically (e.g., without immediately evaluating them) or enabling
conditional logic based on specific conditions or properties of the fractions (like divisibility,
equality, or relational comparisons).

We can start by creating a symbolic structure in Python that allows us to represent arithmetic
expressions with fractions. The symbolic logic would let us:

1.	Represent operations symbolically without immediately computing the result.
2.	Define conditional expressions based on certain properties (like checking if one fraction is greater than another).
3.	Evaluate expressions only when required, allowing for lazy evaluation, which is common in symbolic mathematics.

Let's extend our Fraction class to include symbolic representation with *lazy evaluation*. Here's an example of how this could look:


#### Python

We'll start by creating a SymbolicFraction class that extends the Fraction class. This class
will store operations symbolically and evaluate them only when necessary. We'll add methods
to support symbolic comparisons and boolean checks.

```python
from functools import reduce

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
```


#### Explanation

1. Representation: Each operation (+, -, *, /) is overridden to store the operation symbolically as a
   string in symbolic_expr, allowing us to print expressions without immediate evaluation.

2. Lazy evaluation: Only the result of an operation is printed or evaluated when required. For instance,
   symbolic_sum will hold the expression "(1/2 + 3/4) = 5/4" symbolically until printed.

3. Comparisons with conditional logic: The methods is_equal_to, is_greater_than, and is_less_than
   allow us to perform symbolic comparisons, while if_greater_than lets us apply conditional logic
   based on the comparison of fractions.

#### C: Fraction arithmetic with conditionals

In C, symbolic handling is less straightforward but still possible by using strings to store operations
symbolically. This example provides a simpler approach, where conditions and comparisons are added for
symbolic evaluations.

Here's the continuation of the C example where we complete the SymbolicFraction structure, add symbolic
arithmetic, and enable conditional logic with string-based symbolic expressions.

Continuing from where we left off, we'll implement the add, subtract, multiply, and divide functions,
each of which will generate a symbolic expression. Additionally, we'll add a couple of functions for
comparison and conditional expressions.

```c
#include <stdio.h>
#include <string.h>

typedef struct {
    int numerator;
    int denominator;
    char symbolic_expr[50];
} SymbolicFraction;

int gcd(int a, int b) {
    while (b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

SymbolicFraction simplify(SymbolicFraction frac) {
    int common = gcd(frac.numerator, frac.denominator);
    frac.numerator /= common;
    frac.denominator /= common;
    return frac;
}

SymbolicFraction add(SymbolicFraction f1, SymbolicFraction f2) {
    SymbolicFraction result;
    result.numerator = f1.numerator * f2.denominator + f1.denominator * f2.numerator;
    result.denominator = f1.denominator * f2.denominator;
    result = simplify(result);
    snprintf(result.symbolic_expr, sizeof(result.symbolic_expr), "(%s + %s)", f1.symbolic_expr, f2.symbolic_expr);
    return result;
}

SymbolicFraction subtract(SymbolicFraction f1, SymbolicFraction f2) {
    SymbolicFraction result;
    result.numerator = f1.numerator * f2.denominator - f1.denominator * f2.numerator;
    result.denominator = f1.denominator * f2.denominator;
    result = simplify(result);
    snprintf(result.symbolic_expr, sizeof(result.symbolic_expr), "(%s - %s)", f1.symbolic_expr, f2.symbolic_expr);
    return result;
}

SymbolicFraction multiply(SymbolicFraction f1, SymbolicFraction f2) {
    SymbolicFraction result;
    result.numerator = f1.numerator * f2.numerator;
    result.denominator = f1.denominator * f2.denominator;
    result = simplify(result);
    snprintf(result.symbolic_expr, sizeof(result.symbolic_expr), "(%s * %s)", f1.symbolic_expr, f2.symbolic_expr);
    return result;
}

SymbolicFraction divide(SymbolicFraction f1, SymbolicFraction f2) {
    SymbolicFraction result;
    result.numerator = f1.numerator * f2.denominator;
    result.denominator = f1.denominator * f2.numerator;
    result = simplify(result);
    snprintf(result.symbolic_expr, sizeof(result.symbolic_expr), "(%s / %s)", f1.symbolic_expr, f2.symbolic_expr);
    return result;
}

void print_fraction(SymbolicFraction f) {
    printf("%s = %d/%d\n", f.symbolic_expr, f.numerator, f.denominator);
}

// comparison
int is_equal(SymbolicFraction f1, SymbolicFraction f2) {
    return f1.numerator * f2.denominator == f1.denominator * f2.numerator;
}

int is_greater(SymbolicFraction f1, SymbolicFraction f2) {
    return f1.numerator * f2.denominator > f1.denominator * f2.numerator;
}

int is_less(SymbolicFraction f1, SymbolicFraction f2) {
    return f1.numerator * f2.denominator < f1.denominator * f2.numerator;
}

// conditionals
void if_greater(SymbolicFraction f1, SymbolicFraction f2, char* result_if_true, char* result_if_false) {
    if (is_greater(f1, f2)) {
        printf("%s\n", result_if_true);
    } else {
        printf("%s\n", result_if_false);
    }
}

int main() {
    SymbolicFraction f1 = {1, 2, "1/2"};
    SymbolicFraction f2 = {3, 4, "3/4"};

    // addition
    SymbolicFraction result = add(f1, f2);
    print_fraction(result); // output: "(1/2 + 3/4) = 5/4"

    // conditional check
    if_greater(f1, f2, "f1 is greater", "f2 is greater"); // output: "f2 is greater"

    return 0;
}
```

#### Explanation

1. Symbolic expressions: Each operation (add, subtract, multiply, divide) constructs a symbolic
   expression and assigns it to symbolic_expr. We use snprintf to ensure string safety, formatting the
   symbolic expression as a readable string.

2. Comparisons: Functions like is_equal, is_greater, and is_less perform comparisons on the
   fractions, allowing conditional logic based on their relationships.

3. Conditional `if_greater`: This function takes two SymbolicFraction instances and two string
   messages (`result_if_true` and `result_if_false`). It uses `is_greater` to check if one
   fraction is greater than the other and prints the appropriate message.

With this approach, the program maintains a symbolic representation of arithmetic operations on fractions
and supports conditional checks and expressions based on symbolic logic. The final output reflects both
the symbolic expression and the computed result, combining the symbolic and computational aspects.
