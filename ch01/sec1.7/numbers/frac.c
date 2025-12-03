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
