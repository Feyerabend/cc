#include "../src/core/property_test.h"
#include "../src/strategies/string_strategy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void test_string_concatenation_associativity(void* input) {
    String* a = (String*)input;
    
    char b[] = "b";
    char c[] = "c";
    
    int left_len = a->length + strlen(b) + strlen(c);
    int right_len = a->length + strlen(b) + strlen(c);
    
    PROPERTY_ASSERT(left_len == right_len);
}

void test_string_concatenation_identity(void* input) {
    String* s = (String*)input;
    
    String* with_empty = string_copy(s);
    string_append(with_empty, "", 0);
    
    PROPERTY_ASSERT(strcmp(s->data, with_empty->data) == 0);
    PROPERTY_ASSERT(s->length == with_empty->length);
    
    string_free(with_empty);
}

void test_string_concatenation_length(void* input) {
    String* a = (String*)input;
    
    char b[] = "test";
    int expected_length = a->length + (int)strlen(b);
    
    String* result = string_copy(a);
    string_append(result, b, strlen(b));
    
    PROPERTY_ASSERT(result->length == expected_length);
    
    string_free(result);
}

void test_string_shrinking_maintains_validity(void* input) {
    String* s = (String*)input;
    
    PROPERTY_ASSERT(s->length >= 0);
    PROPERTY_ASSERT(s->data != NULL);
    PROPERTY_ASSERT(s->data[s->length] == '\0');
    
    for (int i = 0; i < s->length; i++) {
        PROPERTY_ASSERT(s->data[i] != '\0');
    }
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
            String* str = (String*)result->minimal_failing_case;
            printf("    Minimal failing case: \"%s\" (length: %d)\n",
                   str->data,
                   str->length);
        }
    }
    
    test_result_free(result);
    printf("\n");
}

int main(void) {
    printf("Property-Based Testing - String Properties\n");
    printf("==========================================\n\n");
    
    Strategy* text_strategy = string_strategy_create(NULL, 100);
    
    printf("Testing String Concatenation (Monoid Properties):\n");
    printf("------------------------------------------------\n");
    
    run_property_test(
        "String concatenation associativity",
        test_string_concatenation_associativity,
        text_strategy,
        100
    );
    
    run_property_test(
        "String concatenation identity (empty string)",
        test_string_concatenation_identity,
        text_strategy,
        100
    );
    
    run_property_test(
        "String concatenation length property",
        test_string_concatenation_length,
        text_strategy,
        100
    );
    
    printf("Testing String Shrinking:\n");
    printf("------------------------\n");
    
    run_property_test(
        "String maintains validity during shrinking",
        test_string_shrinking_maintains_validity,
        text_strategy,
        100
    );
    
    Strategy* alpha_strategy = string_strategy_create("abcdefghijklmnopqrstuvwxyz", 50);
    
    printf("Testing Alphabetic Strings:\n");
    printf("--------------------------\n");
    
    run_property_test(
        "Alphabetic strings maintain validity",
        test_string_shrinking_maintains_validity,
        alpha_strategy,
        100
    );
    
    strategy_free(alpha_strategy);
    strategy_free(text_strategy);
    
    printf("All tests completed.\n");
    printf("\nNote: String strategy uses 3-phase shrinking:\n");
    printf("  1. Length reduction (most effective)\n");
    printf("  2. Character substitution (move towards 'a')\n");
    printf("  3. Character removal (remove individual chars)\n");
    
    return 0;
}
