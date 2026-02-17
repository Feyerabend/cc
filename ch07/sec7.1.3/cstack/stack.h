#ifndef STACK_H
#define STACK_H

// Opaque pointer: the user sees Stack*, but NOT what's inside it.
// This enforces true encapsulation in C.
typedef struct Stack Stack;

// Constructor / Destructor
Stack* stack_create(int capacity);
void stack_destroy(Stack* s);

// Operations--this IS the ADT definition
int stack_push(Stack* s, int value);   // returns 1 on success, 0 on overflow
int stack_pop(Stack* s, int* out);     // returns 1 on success, 0 on underflow
int stack_peek(Stack* s, int* out);    // returns 1 on success, 0 if empty
int stack_is_empty(Stack* s);
int stack_size(Stack* s);

#endif // STACK_H
