#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct Node {
    char* data;
    struct Node* next;
} Node;

typedef struct {
    Node* head;
} Gardener;

Node* create_node(const char* data, Node* next) {
    Node* node = malloc(sizeof(Node));
    node->data = strdup(data);  // duplicate string to avoid modifying original
    node->next = next;
    return node;
}

Gardener* create_gardener() {
    Gardener* g = malloc(sizeof(Gardener));
    g->head = NULL;
    return g;
}

// add at the front (push)
void gardener_add(Gardener* g, const char* data) {
    g->head = create_node(data, g->head);
}

// insert at the end
void gardener_insert(Gardener* g, const char* data) {
    Node** current = &g->head;
    while (*current) {
        current = &((*current)->next);
    }
    *current = create_node(data, NULL);
}

// remove a node by value
void gardener_remove(Gardener* g, const char* data) {
    Node** current = &g->head;
    while (*current) {
        if (strcmp((*current)->data, data) == 0) {
            Node* temp = *current;
            *current = temp->next;
            free(temp->data);
            free(temp);
            return;
        }
        current = &((*current)->next);
    }
}

// replace a node's value
void gardener_replace(Gardener* g, const char* old_data, const char* new_data) {
    Node* current = g->head;
    while (current) {
        if (strcmp(current->data, old_data) == 0) {
            free(current->data);
            current->data = strdup(new_data);
            return;
        }
        current = current->next;
    }
}

void gardener_print_all_elements(Gardener* g) {
    Node* current = g->head;
    while (current) {
        printf("%s\n", current->data);
        current = current->next;
    }
}

void gardener_free(Gardener* g) {
    Node* current = g->head;
    while (current) {
        Node* temp = current;
        current = current->next;
        free(temp->data);
        free(temp);
    }
    free(g);
}


int main() {
    Gardener* g = create_gardener();
    gardener_add(g, "1");
    gardener_add(g, "2");
    gardener_add(g, "3");
    gardener_add(g, "4");
    gardener_add(g, "5");
    gardener_add(g, "6");
    gardener_insert(g, "7");
    gardener_insert(g, "8");
    gardener_add(g, "9");
    
    printf("List after adding and inserting:\n");
    gardener_print_all_elements(g);

    gardener_replace(g, "1", "0");
    printf("\nList after replacing '1' with '0':\n");
    gardener_print_all_elements(g);

    gardener_replace(g, "1", "0");
    gardener_free(g); // free memory
    return 0;
}
