/*
 * firstclass.c
 * Functional Patterns — 1. First-Class Functions
 *
 * C does not have first-class functions in the Python sense, but it does have
 * function pointers: variables that hold the address of a function.
 * This file demonstrates:
 *   1. A simple function-pointer typedef and an apply() helper.
 *   2. A dispatch table (array of function pointers).
 *   3. A factory pattern using a struct to carry extra state (the boundary
 *      between first-class functions and closures — see firstclass_closure.c).
 *   4. A pipeline of function pointers applied in sequence.
 *
 * Build:  cc -Wall -o firstclass firstclass.c
 * Run:    ./firstclass
 */

#include <stdio.h>

/* 
 * 1. Function-pointer type
 * 
 * typedef int (*unary_int)(int);
 * declares "unary_int" as a type alias for a pointer to a function that takes
 * one int and returns one int.  Without the typedef the declarations below
 * become unreadable quickly.
 */
typedef int (*unary_int)(int);

/* Concrete functions that match the unary_int signature. */
static int square(int x)    { return x * x; }
static int negate(int x)    { return -x; }
static int increment(int x) { return x + 1; }
static int double_it(int x) { return x * 2; }

/*
 * apply — the simplest higher-order function in C.
 * f is a function pointer received as an ordinary parameter value.
 * The call f(x) is an indirect call: the CPU loads the address stored
 * in f and jumps to it.  The callee is not known at compile time.
 */
static int apply(unary_int f, int x) {
    return f(x);
}


/* 
 * 2. Dispatch table
 * 
 * An array of function pointers is a lookup table for behaviour.
 * This is structurally identical to a regular C++ vtable.
 */
static const char *op_names[] = { "square", "negate", "increment", "double" };
static unary_int   ops[]      = {  square,   negate,   increment,  double_it };
#define NUM_OPS (int)(sizeof(ops) / sizeof(ops[0]))

static int dispatch(int op_index, int x) {
    if (op_index < 0 || op_index >= NUM_OPS) {
        fprintf(stderr, "dispatch: index %d out of range\n", op_index);
        return 0;
    }
    return ops[op_index](x);  /* indirect call through the table */
}


/* 
 * 3. Pipeline: applying a sequence of function pointers
 * 
 * Without closures we pass the array and its length explicitly.
 */
static int pipeline(unary_int *funcs, int num_funcs, int value) {
    for (int i = 0; i < num_funcs; i++) {
        value = funcs[i](value);   /* each step feeds the next */
    }
    return value;
}


/* 
 * 4. The closure boundary
 * 
 * A plain function pointer carries no environment.  To pass "a multiplier
 * of 3" we must bundle the code pointer and the captured value together.
 * This struct is the minimal simulation of a closure in C.
 *
 * The full pattern (heap allocation, lifetime management) is in section 2
 * (Closures).  Here we only show the shape of the problem.
 */
typedef struct {
    unary_int fn;   /* what to call  */
    int       arg;  /* captured data */
} bound_fn;

/*
 * scaled_apply — the factor is carried in bf.arg rather than in a new
 * function created at runtime (which C cannot do).
 * In a full closure simulation bf.fn would point to a generic helper that
 * reads a void* context; the full pattern is in section 2.
 */
static int scaled_apply(bound_fn bf, int x) {
    /* bf.fn is ignored here; bf.arg holds the scale factor. */
    return x * bf.arg;
}



int main(void) {
    int i;

    /* --- 1. apply */
    printf("-- 1. apply --\n");
    printf("  apply(square,    5) = %d\n", apply(square,    5));   /* 25 */
    printf("  apply(negate,    5) = %d\n", apply(negate,    5));   /* -5 */
    printf("  apply(increment, 5) = %d\n", apply(increment, 5));   /*  6 */

    /* --- 2. dispatch table */
    printf("\n-- 2. Dispatch table --\n");
    for (i = 0; i < NUM_OPS; i++) {
        printf("  %s(5) = %d\n", op_names[i], dispatch(i, 5));
    }

    /* --- 3. Pipeline */
    printf("\n-- 3. Pipeline --\n");
    {
        /* increment -> double -> negate applied to 5:
         *   increment(5) = 6
         *   double(6)    = 12
         *   negate(12)   = -12
         */
        unary_int pipe[] = { increment, double_it, negate };
        int n_pipe = (int)(sizeof(pipe) / sizeof(pipe[0]));
        int result = pipeline(pipe, n_pipe, 5);
        printf("  increment -> double -> negate applied to 5: %d\n", result);
    }

    /* --- 4. Closure boundary */
    printf("\n-- 4. Closure boundary --\n");
    {
        bound_fn triple = { NULL, 3 };   /* "remembers" the factor 3 */
        bound_fn double2 = { NULL, 2 };
        printf("  triple(7)  = %d\n", scaled_apply(triple,  7));  /* 21 */
        printf("  double2(7) = %d\n", scaled_apply(double2, 7));  /* 14 */
        printf("  (Note: fn field is unused here; see section 2 for the\n");
        printf("   full closure simulation with void* context.)\n");
    }

    /* --- Key observation */
    printf("\n-- Key observation --\n");
    printf("  A function pointer is an address stored in a variable.\n");
    printf("  Calling through it (f(x)) is an indirect call:\n");
    printf("  the CPU reads the address, then jumps.\n");
    printf("  The compiler cannot inline it; the branch predictor\n");
    printf("  cannot reliably predict it.\n");
    printf("  This is the cost of behavioral abstraction in C.\n");

    return 0;
}
