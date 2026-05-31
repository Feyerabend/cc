#include "../src/core/property_test.h"
#include "../src/strategies/list_strategy.h"
#include "../src/strategies/integer_strategy.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

typedef struct AVLNode {
    int value;
    int height;
    struct AVLNode* left;
    struct AVLNode* right;
} AVLNode;

typedef struct {
    AVLNode* root;
    int size;
} AVLTree;

int max(int a, int b) {
    return (a > b) ? a : b;
}

int avl_height(AVLNode* node) {
    return node ? node->height : 0;
}

int avl_balance_factor(AVLNode* node) {
    return node ? avl_height(node->left) - avl_height(node->right) : 0;
}

void avl_update_height(AVLNode* node) {
    if (node) {
        node->height = 1 + max(avl_height(node->left), avl_height(node->right));
    }
}

AVLNode* avl_rotate_right(AVLNode* y) {
    AVLNode* x = y->left;
    AVLNode* T2 = x->right;
    
    x->right = y;
    y->left = T2;
    
    avl_update_height(y);
    avl_update_height(x);
    
    return x;
}

AVLNode* avl_rotate_left(AVLNode* x) {
    AVLNode* y = x->right;
    AVLNode* T2 = y->left;
    
    y->left = x;
    x->right = T2;
    
    avl_update_height(x);
    avl_update_height(y);
    
    return y;
}

AVLNode* avl_node_create(int value) {
    AVLNode* node = (AVLNode*)malloc(sizeof(AVLNode));
    node->value = value;
    node->height = 1;
    node->left = NULL;
    node->right = NULL;
    return node;
}

AVLNode* avl_insert_recursive(AVLNode* node, int value) {
    if (node == NULL) {
        return avl_node_create(value);
    }
    
    if (value < node->value) {
        node->left = avl_insert_recursive(node->left, value);
    } else if (value > node->value) {
        node->right = avl_insert_recursive(node->right, value);
    } else {
        return node;
    }
    
    avl_update_height(node);
    
    int balance = avl_balance_factor(node);
    
    if (balance > 1 && value < node->left->value) {
        return avl_rotate_right(node);
    }
    
    if (balance < -1 && value > node->right->value) {
        return avl_rotate_left(node);
    }
    
    if (balance > 1 && value > node->left->value) {
        node->left = avl_rotate_left(node->left);
        return avl_rotate_right(node);
    }
    
    if (balance < -1 && value < node->right->value) {
        node->right = avl_rotate_right(node->right);
        return avl_rotate_left(node);
    }
    
    return node;
}

void avl_free_node(AVLNode* node) {
    if (node) {
        avl_free_node(node->left);
        avl_free_node(node->right);
        free(node);
    }
}

AVLTree* avl_create(void) {
    AVLTree* tree = (AVLTree*)malloc(sizeof(AVLTree));
    tree->root = NULL;
    tree->size = 0;
    return tree;
}

void avl_free(AVLTree* tree) {
    if (tree) {
        avl_free_node(tree->root);
        free(tree);
    }
}

void avl_insert(AVLTree* tree, int value) {
    tree->root = avl_insert_recursive(tree->root, value);
    tree->size++;
}

bool avl_check_balance_recursive(AVLNode* node) {
    if (node == NULL) {
        return true;
    }
    
    int balance = avl_balance_factor(node);
    if (balance < -1 || balance > 1) {
        return false;
    }
    
    return avl_check_balance_recursive(node->left) && 
           avl_check_balance_recursive(node->right);
}

bool avl_is_balanced(AVLTree* tree) {
    return avl_check_balance_recursive(tree->root);
}

bool avl_check_bst_recursive(AVLNode* node, int min_val, int max_val) {
    if (node == NULL) {
        return true;
    }
    
    if (node->value <= min_val || node->value >= max_val) {
        return false;
    }
    
    return avl_check_bst_recursive(node->left, min_val, node->value) &&
           avl_check_bst_recursive(node->right, node->value, max_val);
}

bool avl_is_bst(AVLTree* tree) {
    return avl_check_bst_recursive(tree->root, -2147483648, 2147483647);
}

int avl_count_nodes(AVLNode* node) {
    if (node == NULL) {
        return 0;
    }
    return 1 + avl_count_nodes(node->left) + avl_count_nodes(node->right);
}

void test_avl_balance_invariant(void* input) {
    IntList* values = (IntList*)input;
    
    AVLTree* tree = avl_create();
    
    for (int i = 0; i < values->length; i++) {
        avl_insert(tree, values->data[i]);
        PROPERTY_ASSERT(avl_is_balanced(tree));
    }
    
    avl_free(tree);
}

void test_avl_bst_property(void* input) {
    IntList* values = (IntList*)input;
    
    AVLTree* tree = avl_create();
    
    for (int i = 0; i < values->length; i++) {
        avl_insert(tree, values->data[i]);
        PROPERTY_ASSERT(avl_is_bst(tree));
    }
    
    avl_free(tree);
}

void test_avl_height_bound(void* input) {
    IntList* values = (IntList*)input;
    
    AVLTree* tree = avl_create();
    
    for (int i = 0; i < values->length; i++) {
        avl_insert(tree, values->data[i]);
    }
    
    int n = avl_count_nodes(tree->root);
    int h = avl_height(tree->root);
    
    if (n > 0) {
        PROPERTY_ASSERT(h <= 1.44 * (int)(log(n + 2) / log(2)));
    }
    
    avl_free(tree);
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
    printf("Property-Based Testing - AVL Tree\n");
    printf("==================================\n\n");
    
    printf("Testing AVL Tree Balance Invariants:\n");
    printf("------------------------------------\n");
    
    Strategy* int_strategy = integer_strategy_create(-1000, 1000);
    Strategy* list_strategy = list_strategy_create(int_strategy, 100);
    
    run_property_test(
        "AVL balance invariant maintained after every insert",
        test_avl_balance_invariant,
        list_strategy,
        100
    );
    
    run_property_test(
        "AVL tree maintains BST property",
        test_avl_bst_property,
        list_strategy,
        100
    );
    
    strategy_free(list_strategy);
    strategy_free(int_strategy);
    
    printf("All tests completed.\n");
    printf("\nNote: AVL tree properties tested:\n");
    printf("  - Balance: |height(left) - height(right)| <= 1\n");
    printf("  - BST ordering maintained throughout\n");
    printf("  - Invariants preserved after every insert\n");
    printf("\nThis demonstrates advanced data structure testing.\n");
    
    return 0;
}
