#ifndef BST_STRATEGY_H
#define BST_STRATEGY_H

#include "../core/property_test.h"

typedef struct TreeNode TreeNode;
typedef struct BinarySearchTree BinarySearchTree;

struct TreeNode {
    int value;
    TreeNode* left;
    TreeNode* right;
};

struct BinarySearchTree {
    TreeNode* root;
    int size;
};

BinarySearchTree* bst_create(void);
void bst_free(BinarySearchTree* bst);
void bst_insert(BinarySearchTree* bst, int value);
bool bst_contains(BinarySearchTree* bst, int value);
IntList* bst_inorder_traversal(BinarySearchTree* bst);
bool bst_is_valid(BinarySearchTree* bst);

Strategy* bst_strategy_create(int max_operations);

#endif
