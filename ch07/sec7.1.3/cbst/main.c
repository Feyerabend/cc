#include <stdio.h>
#include "bst.h"

void maintain_user_ids() {
    printf("-- User ID Registry (BST ADT for sorted unique values) --\n\n");
    
    BST* user_ids = bst_create();
    
    // Register users
    int new_ids[] = {1050, 1020, 1080, 1010, 1060, 1030, 1070};
    printf("Registering user IDs:\n");
    for (int i = 0; i < 7; i++) {
        bst_insert(user_ids, new_ids[i]);
        printf("  Registered: %d\n", new_ids[i]);
    }
    
    printf("\nAll IDs (sorted by BST in-order traversal):\n  ");
    bst_print_inorder(user_ids);
    
    // Check if IDs exist
    int check_ids[] = {1050, 9999, 1010};
    printf("\nID lookup:\n");
    for (int i = 0; i < 3; i++) {
        printf("  ID %d: %s\n", check_ids[i], 
               bst_search(user_ids, check_ids[i]) ? "EXISTS" : "NOT FOUND");
    }
    
    // Delete a user
    printf("\nDeleting user ID 1050...\n");
    bst_delete(user_ids, 1050);
    printf("Remaining IDs: ");
    bst_print_inorder(user_ids);
    
    int min_id, max_id;
    bst_min(user_ids, &min_id);
    bst_max(user_ids, &max_id);
    printf("\nID range: %d to %d\n", min_id, max_id);
    
    bst_destroy(user_ids);
}

int main(void) {
    maintain_user_ids();
    return 0;
}
