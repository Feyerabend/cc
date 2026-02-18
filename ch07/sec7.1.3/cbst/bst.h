#ifndef BST_H
#define BST_H

typedef struct BST BST;

BST* bst_create(void);
void bst_destroy(BST* tree);

void bst_insert(BST* tree, int value);
int  bst_search(BST* tree, int value);  // returns 1 if found
int  bst_delete(BST* tree, int value);  // returns 1 if deleted
int  bst_min(BST* tree, int* out);      // returns 1 if tree non-empty
int  bst_max(BST* tree, int* out);
int  bst_size(BST* tree);
void bst_print_inorder(BST* tree);

#endif // BST_H
