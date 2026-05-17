#include "../src/core/property_test.h"
#include "../src/strategies/bst_strategy.h"
#include <stdio.h>
#include <stdlib.h>

void test_bst_order_invariant(void* input) {
    BinarySearchTree* bst = (BinarySearchTree*)input;
    
    IntList* traversal = bst_inorder_traversal(bst);
    
    for (int i = 0; i < traversal->length - 1; i++) {
        PROPERTY_ASSERT(traversal->data[i] <= traversal->data[i + 1]);
    }
    
    int_list_free(traversal);
}

void test_bst_completeness_invariant(void* input) {
    BinarySearchTree* bst = (BinarySearchTree*)input;
    
    IntList* traversal = bst_inorder_traversal(bst);
    
    for (int i = 0; i < traversal->length; i++) {
        PROPERTY_ASSERT(bst_contains(bst, traversal->data[i]));
    }
    
    int_list_free(traversal);
}

void test_bst_ordering_property(void* input) {
    BinarySearchTree* bst = (BinarySearchTree*)input;
    
    PROPERTY_ASSERT(bst_is_valid(bst));
}

void test_bst_size_property(void* input) {
    BinarySearchTree* bst = (BinarySearchTree*)input;
    
    IntList* traversal = bst_inorder_traversal(bst);
    
    PROPERTY_ASSERT(traversal->length == bst->size);
    
    int_list_free(traversal);
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
    printf("Property-Based Testing - Binary Search Tree\n");
    printf("==========================================\n\n");
    
    Strategy* bst_strategy = bst_strategy_create(50);
    
    printf("Testing BST Structural Invariants:\n");
    printf("---------------------------------\n");
    
    run_property_test(
        "BST order invariant (in-order traversal is sorted)",
        test_bst_order_invariant,
        bst_strategy,
        100
    );
    
    run_property_test(
        "BST completeness invariant (all inserted values present)",
        test_bst_completeness_invariant,
        bst_strategy,
        100
    );
    
    run_property_test(
        "BST ordering property (maintains BST structure)",
        test_bst_ordering_property,
        bst_strategy,
        100
    );
    
    run_property_test(
        "BST size property (traversal length equals size)",
        test_bst_size_property,
        bst_strategy,
        100
    );
    
    strategy_free(bst_strategy);
    
    printf("All tests completed.\n");
    printf("\nNote: BST properties tested:\n");
    printf("  - Order: In-order traversal produces sorted sequence\n");
    printf("  - Completeness: All inserted values are present\n");
    printf("  - Structure: Binary search tree property maintained\n");
    printf("  - Size: Tree size matches number of elements\n");
    printf("\nThis demonstrates testing of structural invariants,\n");
    printf("parallel to the 'Structural Properties' section in the book.\n");
    
    return 0;
}
