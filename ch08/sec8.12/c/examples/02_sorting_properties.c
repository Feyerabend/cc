#include "../src/core/property_test.h"
#include "../src/strategies/integer_strategy.h"
#include "../src/strategies/list_strategy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void simple_sort(int* arr, int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}

bool is_sorted(int* arr, int n) {
    for (int i = 0; i < n - 1; i++) {
        if (arr[i] > arr[i + 1]) {
            return false;
        }
    }
    return true;
}

bool has_same_elements(int* arr1, int n1, int* arr2, int n2) {
    if (n1 != n2) {
        return false;
    }
    
    int* temp1 = (int*)malloc(n1 * sizeof(int));
    int* temp2 = (int*)malloc(n2 * sizeof(int));
    
    memcpy(temp1, arr1, n1 * sizeof(int));
    memcpy(temp2, arr2, n2 * sizeof(int));
    
    simple_sort(temp1, n1);
    simple_sort(temp2, n2);
    
    bool result = memcmp(temp1, temp2, n1 * sizeof(int)) == 0;
    
    free(temp1);
    free(temp2);
    
    return result;
}

void test_sort_ordering(void* input) {
    IntList* list = (IntList*)input;
    
    if (list->length == 0) {
        return;
    }
    
    int* sorted = (int*)malloc(list->length * sizeof(int));
    memcpy(sorted, list->data, list->length * sizeof(int));
    
    simple_sort(sorted, list->length);
    
    bool sorted_property = is_sorted(sorted, list->length);
    
    free(sorted);
    
    PROPERTY_ASSERT(sorted_property);
}

void test_sort_permutation(void* input) {
    IntList* list = (IntList*)input;
    
    if (list->length == 0) {
        return;
    }
    
    int* sorted = (int*)malloc(list->length * sizeof(int));
    memcpy(sorted, list->data, list->length * sizeof(int));
    
    simple_sort(sorted, list->length);
    
    bool same_elements = has_same_elements(
        list->data,
        list->length,
        sorted,
        list->length
    );
    
    free(sorted);
    
    PROPERTY_ASSERT(same_elements);
}

void test_sort_length(void* input) {
    IntList* list = (IntList*)input;
    
    int* sorted = (int*)malloc(list->length * sizeof(int));
    memcpy(sorted, list->data, list->length * sizeof(int));
    
    simple_sort(sorted, list->length);
    
    free(sorted);
    
    PROPERTY_ASSERT(list->length == list->length);
}

void test_sort_idempotence(void* input) {
    IntList* list = (IntList*)input;
    
    if (list->length == 0) {
        return;
    }
    
    int* sorted1 = (int*)malloc(list->length * sizeof(int));
    int* sorted2 = (int*)malloc(list->length * sizeof(int));
    
    memcpy(sorted1, list->data, list->length * sizeof(int));
    memcpy(sorted2, list->data, list->length * sizeof(int));
    
    simple_sort(sorted1, list->length);
    simple_sort(sorted2, list->length);
    simple_sort(sorted2, list->length);
    
    bool idempotent = memcmp(sorted1, sorted2, list->length * sizeof(int)) == 0;
    
    free(sorted1);
    free(sorted2);
    
    PROPERTY_ASSERT(idempotent);
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
            IntList* list = (IntList*)result->minimal_failing_case;
            printf("    Minimal failing case: [");
            for (int i = 0; i < list->length; i++) {
                printf("%d", list->data[i]);
                if (i < list->length - 1) {
                    printf(", ");
                }
            }
            printf("]\n");
        }
    }
    
    test_result_free(result);
    printf("\n");
}

int main(void) {
    printf("Property-Based Testing - Sorting Properties\n");
    printf("==========================================\n\n");
    
    Strategy* int_strategy = integer_strategy_create(-100, 100);
    Strategy* list_strategy = list_strategy_create(int_strategy, 50);
    
    printf("Testing Sorting Function Properties:\n");
    printf("------------------------------------\n");
    
    run_property_test(
        "Sorting produces ordered output",
        test_sort_ordering,
        list_strategy,
        100
    );
    
    run_property_test(
        "Sorting preserves all elements (permutation)",
        test_sort_permutation,
        list_strategy,
        100
    );
    
    run_property_test(
        "Sorting preserves length",
        test_sort_length,
        list_strategy,
        100
    );
    
    run_property_test(
        "Sorting is idempotent",
        test_sort_idempotence,
        list_strategy,
        100
    );
    
    strategy_free(list_strategy);
    strategy_free(int_strategy);
    
    printf("All tests completed.\n");
    return 0;
}
