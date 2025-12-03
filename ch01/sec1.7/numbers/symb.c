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
