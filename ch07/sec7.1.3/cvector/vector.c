#include <stdlib.h>
#include <string.h>
#include "vector.h"

struct Vector {
    int* data;
    int  size;
    int  capacity;
};

Vector* vector_create(void) {
    Vector* v = malloc(sizeof(Vector));
    if (!v) return NULL;
    v->capacity = 4;  // start small
    v->size = 0;
    v->data = malloc(sizeof(int) * v->capacity);
    if (!v->data) { free(v); return NULL; }
    return v;
}

void vector_destroy(Vector* v) {
    if (!v) return;
    free(v->data);
    free(v);
}

static void vector_grow(Vector* v) {
    int new_cap = v->capacity * 2;
    int* new_data = realloc(v->data, sizeof(int) * new_cap);
    if (!new_data) return; // allocation failed, keep old data
    v->data = new_data;
    v->capacity = new_cap;
}

void vector_push_back(Vector* v, int value) {
    if (v->size >= v->capacity) {
        vector_grow(v);
    }
    v->data[v->size++] = value;
}

int vector_pop_back(Vector* v, int* out) {
    if (v->size == 0) return 0;
    *out = v->data[--v->size];
    return 1;
}

int vector_get(Vector* v, int index, int* out) {
    if (index < 0 || index >= v->size) return 0;
    *out = v->data[index];
    return 1;
}

int vector_set(Vector* v, int index, int value) {
    if (index < 0 || index >= v->size) return 0;
    v->data[index] = value;
    return 1;
}

int vector_size(Vector* v)     { return v->size; }
int vector_capacity(Vector* v) { return v->capacity; }

void vector_clear(Vector* v) { v->size = 0; }
