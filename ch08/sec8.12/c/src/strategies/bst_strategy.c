#include "bst_strategy.h"
#include <stdlib.h>
#include <limits.h>

static TreeNode* tree_node_create(int value) {
    TreeNode* node = (TreeNode*)malloc(sizeof(TreeNode));
    node->value = value;
    node->left = NULL;
    node->right = NULL;
    return node;
}

static void tree_node_free(TreeNode* node) {
    if (node) {
        tree_node_free(node->left);
        tree_node_free(node->right);
        free(node);
    }
}

BinarySearchTree* bst_create(void) {
    BinarySearchTree* bst = (BinarySearchTree*)malloc(sizeof(BinarySearchTree));
    bst->root = NULL;
    bst->size = 0;
    return bst;
}

void bst_free(BinarySearchTree* bst) {
    if (bst) {
        tree_node_free(bst->root);
        free(bst);
    }
}

static TreeNode* bst_insert_recursive(TreeNode* node, int value) {
    if (node == NULL) {
        return tree_node_create(value);
    }
    
    if (value <= node->value) {
        node->left = bst_insert_recursive(node->left, value);
    } else {
        node->right = bst_insert_recursive(node->right, value);
    }
    
    return node;
}

void bst_insert(BinarySearchTree* bst, int value) {
    bst->root = bst_insert_recursive(bst->root, value);
    bst->size++;
}

static bool bst_search(TreeNode* node, int value) {
    if (node == NULL) {
        return false;
    }
    if (value == node->value) {
        return true;
    } else if (value < node->value) {
        return bst_search(node->left, value);
    } else {
        return bst_search(node->right, value);
    }
}

bool bst_contains(BinarySearchTree* bst, int value) {
    return bst_search(bst->root, value);
}

static void bst_inorder_recursive(TreeNode* node, IntList* result) {
    if (node) {
        bst_inorder_recursive(node->left, result);
        int_list_append(result, node->value);
        bst_inorder_recursive(node->right, result);
    }
}

IntList* bst_inorder_traversal(BinarySearchTree* bst) {
    IntList* result = int_list_create(bst->size + 1);
    bst_inorder_recursive(bst->root, result);
    return result;
}

static bool bst_is_valid_recursive(
    TreeNode* node,
    int min_val,
    int max_val
) {
    if (node == NULL) {
        return true;
    }
    
    if (node->value < min_val || node->value > max_val) {
        return false;
    }
    
    return bst_is_valid_recursive(node->left, min_val, node->value) &&
           bst_is_valid_recursive(node->right, node->value, max_val);
}

bool bst_is_valid(BinarySearchTree* bst) {
    return bst_is_valid_recursive(bst->root, INT_MIN, INT_MAX);
}

typedef struct {
    int max_operations;
} BSTContext;

static void* bst_generate(Strategy* strategy, unsigned int* seed, int size) {
    BSTContext* ctx = (BSTContext*)strategy->context;
    
    BinarySearchTree* bst = bst_create();
    int num_ops = rand_range(seed, 1, size < ctx->max_operations ? size : ctx->max_operations);
    
    for (int i = 0; i < num_ops; i++) {
        int value = rand_range(seed, -100, 100);
        bst_insert(bst, value);
    }
    
    return bst;
}

static bool bst_shrink_has_next(ShrinkIterator* iter) {
    (void)iter;
    return false;
}

static void* bst_shrink_next(ShrinkIterator* iter) {
    (void)iter;
    return NULL;
}

static void bst_shrink_free(ShrinkIterator* iter) {
    free(iter);
}

static ShrinkIterator* bst_shrink(Strategy* strategy, void* value) {
    (void)strategy;
    (void)value;
    
    ShrinkIterator* iter = (ShrinkIterator*)malloc(sizeof(ShrinkIterator));
    iter->state = NULL;
    iter->current = NULL;
    iter->has_next = bst_shrink_has_next;
    iter->next = bst_shrink_next;
    iter->free_iter = bst_shrink_free;
    
    return iter;
}

static void bst_free_value(void* value) {
    bst_free((BinarySearchTree*)value);
}

Strategy* bst_strategy_create(int max_operations) {
    Strategy* strategy = (Strategy*)malloc(sizeof(Strategy));
    BSTContext* ctx = (BSTContext*)malloc(sizeof(BSTContext));
    
    ctx->max_operations = max_operations;
    
    strategy->context = ctx;
    strategy->generate = bst_generate;
    strategy->shrink = bst_shrink;
    strategy->free_value = bst_free_value;
    
    return strategy;
}
