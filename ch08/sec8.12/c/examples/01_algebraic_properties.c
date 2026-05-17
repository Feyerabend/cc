#include "../src/core/property_test.h"
#include "../src/strategies/integer_strategy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void test_associativity(void* input) {
    int a = *(int*)input;
    int b = a + 1;
    int c = a + 2;
    
    int left = (a + b) + c;
    int right = a + (b + c);
    
    PROPERTY_ASSERT(left == right);
}

void test_commutativity(void* input) {
    int a = *(int*)input;
    int b = a + 1;
    
    PROPERTY_ASSERT(a + b == b + a);
}

void test_identity(void* input) {
    int a = *(int*)input;
    
    PROPERTY_ASSERT(a + 0 == a);
    PROPERTY_ASSERT(0 + a == a);
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
        if (result->minimal_failing_case) {
            int* value = (int*)result->minimal_failing_case;
            printf("    Minimal failing case: %d\n", *value);
        }
    }
    
    test_result_free(result);
    printf("\n");
}

int main(void) {
    printf("Property-Based Testing Framework - C Implementation\n");
    printf("====================================================\n\n");
    
    Strategy* int_strategy = integer_strategy_create(-1000, 1000);
    
    printf("Testing Algebraic Properties:\n");
    printf("-----------------------------\n");
    
    run_property_test(
        "Integer Addition Associativity",
        test_associativity,
        int_strategy,
        100
    );
    
    run_property_test(
        "Integer Addition Commutativity",
        test_commutativity,
        int_strategy,
        100
    );
    
    run_property_test(
        "Integer Addition Identity",
        test_identity,
        int_strategy,
        100
    );
    
    strategy_free(int_strategy);
    
    printf("All tests completed.\n");
    return 0;
}
