#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef int (*CompareFn)(const void*, const void*);
typedef void (*PrintFn)(const void*);
typedef void (*DestroyFn)(void*);

typedef struct Node {
    void* data;
    struct Node* next;
} Node;

typedef struct {
    Node* head;
    size_t data_size;
    CompareFn cmp;
    PrintFn print;
    DestroyFn destroy;
} Gardener;

Node* create_node(const void* data, size_t size, Node* next) {
    Node* node = malloc(sizeof(Node));
    node->data = malloc(size);
    memcpy(node->data, data, size);
    node->next = next;
    return node;
}

Gardener* gardener_create(size_t size, CompareFn cmp, PrintFn print, DestroyFn destroy) {
    Gardener* g = malloc(sizeof(Gardener));
    g->head = NULL;
    g->data_size = size;
    g->cmp = cmp;
    g->print = print;
    g->destroy = destroy;
    return g;
}

void gardener_push_front(Gardener* g, const void* data) {
    g->head = create_node(data, g->data_size, g->head);
}

void gardener_push_back(Gardener* g, const void* data) {
    Node** current = &g->head;
    while (*current)
        current = &((*current)->next);

    *current = create_node(data, g->data_size, NULL);
}

void gardener_remove(Gardener* g, const void* value) {
    Node** current = &g->head;
    while (*current) {
        if (g->cmp((*current)->data, value) == 0) {
            Node* temp = *current;
            *current = temp->next;

            if (g->destroy)
                g->destroy(temp->data);

            free(temp->data);
            free(temp);
            return;
        }
        current = &((*current)->next);
    }
}

void gardener_replace(Gardener* g, const void* old_value, const void* new_value) {
    Node* current = g->head;
    while (current) {
        if (g->cmp(current->data, old_value) == 0) {
            memcpy(current->data, new_value, g->data_size);
            return;
        }
        current = current->next;
    }
}

void gardener_print(Gardener* g) {
    Node* current = g->head;
    while (current) {
        g->print(current->data);
        current = current->next;
    }
}

void gardener_free(Gardener* g) {
    Node* current = g->head;
    while (current) {
        Node* temp = current;
        current = current->next;

        if (g->destroy)
            g->destroy(temp->data);

        free(temp->data);
        free(temp);
    }
    free(g);
}

int int_cmp(const void* a, const void* b) {
    int x = *(int*)a;
    int y = *(int*)b;
    return x - y;
}

void int_print(const void* a) {
    printf("%d\n", *(int*)a);
}

int main() {
    Gardener* g = gardener_create(sizeof(int), int_cmp, int_print, NULL);

    int x = 5;
    gardener_push_front(g, &x);

    int y = 10;
    gardener_push_back(g, &y);

    gardener_print(g);

    gardener_free(g);
}
