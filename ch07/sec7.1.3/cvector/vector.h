#ifndef VECTOR_H
#define VECTOR_H

typedef struct Vector Vector;

Vector* vector_create(void);
void    vector_destroy(Vector* v);

void vector_push_back(Vector* v, int value);
int  vector_pop_back(Vector* v, int* out);  // returns 1 on success
int  vector_get(Vector* v, int index, int* out);
int  vector_set(Vector* v, int index, int value);
int  vector_size(Vector* v);
int  vector_capacity(Vector* v);
void vector_clear(Vector* v);

#endif // VECTOR_H
