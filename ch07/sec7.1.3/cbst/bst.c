#include <stdio.h>
#include <stdlib.h>
#include "bst.h"

typedef struct Node {
    int value;
    struct Node* left;
    struct Node* right;
} Node;

struct BST {
    Node* root;
    int   size;
};

BST* bst_create(void) {
    BST* tree = malloc(sizeof(BST));
    if (!tree) return NULL;
    tree->root = NULL;
    tree->size = 0;
    return tree;
}

static void destroy_recursive(Node* n) {
    if (!n) return;
    destroy_recursive(n->left);
    destroy_recursive(n->right);
    free(n);
}

void bst_destroy(BST* tree) {
    destroy_recursive(tree->root);
    free(tree);
}

static Node* insert_recursive(Node* n, int value) {
    if (!n) {
        Node* new_node = malloc(sizeof(Node));
        new_node->value = value;
        new_node->left = new_node->right = NULL;
        return new_node;
    }
    if (value < n->value)      n->left  = insert_recursive(n->left, value);
    else if (value > n->value) n->right = insert_recursive(n->right, value);
    return n;
}

void bst_insert(BST* tree, int value) {
    int old_size = tree->size;
    tree->root = insert_recursive(tree->root, value);
    if (old_size == tree->size) tree->size++; // new node added
}

static int search_recursive(Node* n, int value) {
    if (!n) return 0;
    if (value == n->value) return 1;
    if (value < n->value) return search_recursive(n->left, value);
    return search_recursive(n->right, value);
}

int bst_search(BST* tree, int value) {
    return search_recursive(tree->root, value);
}

static Node* find_min(Node* n) {
    while (n && n->left) n = n->left;
    return n;
}

static Node* delete_recursive(Node* n, int value, int* deleted) {
    if (!n) return NULL;
    
    if (value < n->value) {
        n->left = delete_recursive(n->left, value, deleted);
    } else if (value > n->value) {
        n->right = delete_recursive(n->right, value, deleted);
    } else {
        *deleted = 1;
        // Node found — handle 3 cases
        if (!n->left) {
            Node* temp = n->right;
            free(n);
            return temp;
        }
        if (!n->right) {
            Node* temp = n->left;
            free(n);
            return temp;
        }
        // Two children: replace with inorder successor
        Node* successor = find_min(n->right);
        n->value = successor->value;
        n->right = delete_recursive(n->right, successor->value, deleted);
    }
    return n;
}

int bst_delete(BST* tree, int value) {
    int deleted = 0;
    tree->root = delete_recursive(tree->root, value, &deleted);
    if (deleted) tree->size--;
    return deleted;
}

static void inorder_recursive(Node* n) {
    if (!n) return;
    inorder_recursive(n->left);
    printf("%d ", n->value);
    inorder_recursive(n->right);
}

void bst_print_inorder(BST* tree) {
    inorder_recursive(tree->root);
    printf("\n");
}

int bst_min(BST* tree, int* out) {
    Node* n = find_min(tree->root);
    if (!n) return 0;
    *out = n->value;
    return 1;
}

int bst_max(BST* tree, int* out) {
    Node* n = tree->root;
    if (!n) return 0;
    while (n->right) n = n->right;
    *out = n->value;
    return 1;
}

int bst_size(BST* tree) { return tree->size; }
