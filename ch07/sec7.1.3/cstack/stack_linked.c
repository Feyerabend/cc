#include <stdlib.h>
#include "stack.h"

// Completely different internal structure--but same interface!
typedef struct Node {
    int value;
    struct Node* next;
} Node;

struct Stack {
    Node* head;
    int   size;
    int   capacity; // unused here, but kept for interface compatibility
};

Stack* stack_create(int capacity) {
    Stack* s = malloc(sizeof(Stack));
    if (!s) return NULL;
    s->head = NULL;
    s->size = 0;
    s->capacity = capacity;
    return s;
}

void stack_destroy(Stack* s) {
    Node* curr = s->head;
    while (curr) {
        Node* next = curr->next;
        free(curr);
        curr = next;
    }
    free(s);
}

int stack_push(Stack* s, int value) {
    Node* n = malloc(sizeof(Node));
    if (!n) return 0;
    n->value = value;
    n->next  = s->head;
    s->head  = n;
    s->size++;
    return 1;
}

int stack_pop(Stack* s, int* out) {
    if (!s->head) return 0;
    Node* old = s->head;
    *out = old->value;
    s->head = old->next;
    free(old);
    s->size--;
    return 1;
}

int stack_peek(Stack* s, int* out) {
    if (!s->head) return 0;
    *out = s->head->value;
    return 1;
}

int stack_is_empty(Stack* s) { return s->head == NULL; }
int stack_size(Stack* s)     { return s->size; }

