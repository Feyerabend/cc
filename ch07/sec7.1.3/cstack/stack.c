#include <stdlib.h>
#include "stack.h"

// The real struct definition--hidden in the .c file
struct Stack {
    int* data;
    int  top;
    int  capacity;
};

Stack* stack_create(int capacity) {
    Stack* s = malloc(sizeof(Stack));
    if (!s) return NULL;
    s->data = malloc(sizeof(int) * capacity);
    if (!s->data) { free(s); return NULL; }
    s->top = -1;
    s->capacity = capacity;
    return s;
}

void stack_destroy(Stack* s) {
    if (!s) return;
    free(s->data);
    free(s);
}

int stack_push(Stack* s, int value) {
    if (s->top >= s->capacity - 1) return 0; // overflow
    s->data[++(s->top)] = value;
    return 1;
}

int stack_pop(Stack* s, int* out) {
    if (s->top < 0) return 0; // underflow
    *out = s->data[(s->top)--];
    return 1;
}

int stack_peek(Stack* s, int* out) {
    if (s->top < 0) return 0;
    *out = s->data[s->top];
    return 1;
}

int stack_is_empty(Stack* s) { return s->top < 0; }
int stack_size(Stack* s)     { return s->top + 1; }

