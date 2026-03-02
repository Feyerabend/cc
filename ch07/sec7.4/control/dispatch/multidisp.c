#include <stdio.h>

typedef enum { INT, FLOAT } Type;

typedef struct {
    Type type1, type2;
    int (*func)(void*, void*);
} DispatchEntry;

int multiply_int_int(int *a, int *b) { return (*a) * (*b); }
int multiply_float_float(float *a, float *b) { return (int)((*a) * (*b)); }

DispatchEntry dispatch_table[] = {
    {INT, INT, (int (*)(void*, void*))multiply_int_int},
    {FLOAT, FLOAT, (int (*)(void*, void*))multiply_float_float},
    {-1, -1, NULL} // sentinel
};

int dispatch(Type t1, Type t2, void *a, void *b) {
    for (int i = 0; dispatch_table[i].func != NULL; i++) {
        if (dispatch_table[i].type1 == t1 && dispatch_table[i].type2 == t2) {
            return dispatch_table[i].func(a, b);
        }
    }
    return 0;
}

int main() {
    int a = 2, b = 3;
    float x = 2.0, y = 3.0;
    printf("%d\n", dispatch(INT, INT, &a, &b)); // Output: 6
    printf("%d\n", dispatch(FLOAT, FLOAT, &x, &y)); // Output: 6
    return 0;
}

// This code implements a simple multi-dispatch mechanism in C.
// It defines a dispatch table that maps pairs of types to functions.
// The dispatch function looks up the appropriate function based on the types
// of the arguments and calls it. The example demonstrates how to use this
// mechanism to multiply integers and floats, returning the result as an integer.
// The dispatch function returns 0 if no matching function is found.
