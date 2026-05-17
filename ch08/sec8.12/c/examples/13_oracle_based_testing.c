#include "../src/core/property_test.h"
#include "../src/strategies/integer_strategy.h"
#include "../src/strategies/tuple_strategy.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define EPSILON 0.001

typedef struct {
    double x;
    double y;
} Point2D;

double fast_sqrt_approximation(double x) {
    if (x <= 0.0) return 0.0;
    
    double guess = x / 2.0;
    for (int i = 0; i < 10; i++) {
        guess = (guess + x / guess) / 2.0;
    }
    return guess;
}

double fast_sin_approximation(double x) {
    while (x > M_PI) x -= 2 * M_PI;
    while (x < -M_PI) x += 2 * M_PI;
    
    double x2 = x * x;
    double x3 = x2 * x;
    double x5 = x3 * x2;
    double x7 = x5 * x2;
    double x9 = x7 * x2;
    double x11 = x9 * x2;
    
    return x - (x3 / 6.0) + (x5 / 120.0) - (x7 / 5040.0) + (x9 / 362880.0) - (x11 / 39916800.0);
}

double fast_cos_approximation(double x) {
    while (x > M_PI) x -= 2 * M_PI;
    while (x < -M_PI) x += 2 * M_PI;
    
    double x2 = x * x;
    double x4 = x2 * x2;
    double x6 = x4 * x2;
    double x8 = x6 * x2;
    double x10 = x8 * x2;
    
    return 1.0 - (x2 / 2.0) + (x4 / 24.0) - (x6 / 720.0) + (x8 / 40320.0) - (x10 / 3628800.0);
}

double fast_exp_approximation(double x) {
    if (x > 10.0) return exp(10.0);
    if (x < -10.0) return exp(-10.0);
    
    double result = 1.0;
    double term = 1.0;
    
    for (int i = 1; i <= 20; i++) {
        term *= x / i;
        result += term;
    }
    
    return result;
}

void test_pythagorean_identity(void* input) {
    int* angle_int = (int*)input;
    double angle = (*angle_int % 360) * M_PI / 180.0;
    
    double sin_val = fast_sin_approximation(angle);
    double cos_val = fast_cos_approximation(angle);
    
    double sum_of_squares = sin_val * sin_val + cos_val * cos_val;
    
    PROPERTY_ASSERT(fabs(sum_of_squares - 1.0) < EPSILON);
}

void test_sqrt_multiplication_identity(void* input) {
    Tuple2* pair = (Tuple2*)input;
    int a_int = abs(*(int*)pair->first) % 100 + 1;
    int b_int = abs(*(int*)pair->second) % 100 + 1;
    
    double a = (double)a_int;
    double b = (double)b_int;
    
    double sqrt_ab = fast_sqrt_approximation(a * b);
    double sqrt_a_times_sqrt_b = fast_sqrt_approximation(a) * fast_sqrt_approximation(b);
    
    PROPERTY_ASSERT(fabs(sqrt_ab - sqrt_a_times_sqrt_b) < EPSILON);
}

void test_exp_addition_identity(void* input) {
    Tuple2* pair = (Tuple2*)input;
    int a_int = (*(int*)pair->first) % 10;
    int b_int = (*(int*)pair->second) % 10;
    
    double a = (double)a_int / 2.0;
    double b = (double)b_int / 2.0;
    
    double exp_a_plus_b = fast_exp_approximation(a + b);
    double exp_a_times_exp_b = fast_exp_approximation(a) * fast_exp_approximation(b);
    
    PROPERTY_ASSERT(fabs(exp_a_plus_b - exp_a_times_exp_b) < EPSILON);
}

void test_double_angle_formula(void* input) {
    int* angle_int = (int*)input;
    double angle = (*angle_int % 180) * M_PI / 180.0;
    
    double sin_2a = fast_sin_approximation(2.0 * angle);
    double two_sin_a_cos_a = 2.0 * fast_sin_approximation(angle) * fast_cos_approximation(angle);
    
    PROPERTY_ASSERT(fabs(sin_2a - two_sin_a_cos_a) < EPSILON);
}

void test_sqrt_square_identity(void* input) {
    int* val_int = (int*)input;
    int positive_val = abs(*val_int) % 1000;
    double x = (double)positive_val;
    
    double sqrt_x_squared = fast_sqrt_approximation(x * x);
    
    PROPERTY_ASSERT(fabs(sqrt_x_squared - x) < EPSILON);
}

void run_property_test(
    const char* name,
    PropertyFn property,
    Strategy* strategy,
    int max_examples
) {
    printf("Running: %s\n", name);
    
    TestResult* result = test_property(
        property,
        strategy,
        max_examples,
        (unsigned int)time(NULL)
    );
    
    if (result->passed) {
        printf("  ✓ PASSED (%d examples in %.3fs)\n",
               result->examples_tried,
               result->execution_time);
    } else {
        printf("  ✗ FAILED after %d examples\n", result->examples_tried);
        printf("    Shrink iterations: %d\n", result->shrink_iterations);
    }
    
    test_result_free(result);
    printf("\n");
}

int main(void) {
    printf("Property-Based Testing - Oracle-Based Testing\n");
    printf("=============================================\n\n");
    
    printf("Testing Mathematical Approximations Against Identities:\n");
    printf("-------------------------------------------------------\n");
    
    Strategy* angle_strategy = integer_strategy_create(-360, 360);
    
    run_property_test(
        "Pythagorean identity: sin²(x) + cos²(x) = 1",
        test_pythagorean_identity,
        angle_strategy,
        100
    );
    
    run_property_test(
        "Double angle formula: sin(2x) = 2·sin(x)·cos(x)",
        test_double_angle_formula,
        angle_strategy,
        100
    );
    
    strategy_free(angle_strategy);
    
    Strategy* int_strategy = integer_strategy_create(-100, 100);
    Strategy* pair_strategy = tuple2_strategy_create(int_strategy, int_strategy);
    
    run_property_test(
        "Square root multiplication: √(a·b) = √a · √b",
        test_sqrt_multiplication_identity,
        pair_strategy,
        100
    );
    
    run_property_test(
        "Exponential addition: e^(a+b) = e^a · e^b",
        test_exp_addition_identity,
        pair_strategy,
        100
    );
    
    strategy_free(pair_strategy);
    
    Strategy* val_strategy = integer_strategy_create(0, 1000);
    
    run_property_test(
        "Square root of square: √(x²) = x",
        test_sqrt_square_identity,
        val_strategy,
        100
    );
    
    strategy_free(val_strategy);
    strategy_free(int_strategy);
    
    printf("All tests completed.\n");
    printf("\nOracle-Based Testing Pattern:\n");
    printf("  Use mathematical identities as test oracles:\n");
    printf("  - We don't know if sin(0.5) = 0.479425...\n");
    printf("  - But we KNOW sin²(x) + cos²(x) must equal 1\n");
    printf("  - Test implementation against known relationships\n");
    printf("\nExamples of Oracles:\n");
    printf("  - Mathematical identities (Pythagorean theorem)\n");
    printf("  - Physical laws (conservation of energy)\n");
    printf("  - Business rules (debits = credits)\n");
    printf("  - Algebraic properties (commutativity, etc.)\n");
    printf("\nThis tests correctness without knowing exact answers!\n");
    
    return 0;
}
