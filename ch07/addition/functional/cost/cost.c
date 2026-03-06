/*
 * cost.c
 * Functional Patterns -- 11. Cost Model
 *
 * Measures the concrete overhead of functional patterns in C:
 * stack vs heap allocation, inline vs function-pointer call,
 * closure pair call, composition depth.
 *
 * Build:  cc -Wall -O2 -o cost cost.c
 * Run:    ./cost
 *
 * Note: benchmark functions are declared NOINLINE so the optimiser cannot
 * fold them away.  ATTR_CONST functions without NOINLINE show the cost
 * when the compiler can inline and eliminate the call--near zero.
 */

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

/* 
 * Compiler annotations
 */
#if defined(__GNUC__) || defined(__clang__)
#  define ATTR_CONST __attribute__((const))
#  define NOINLINE   __attribute__((noinline))
#else
#  define ATTR_CONST
#  define NOINLINE
#endif

/* 
 * Timer
 */
static double now_ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec * 1e9 + (double)t.tv_nsec;
}

static volatile long sink = 0;   /* volatile: prevents dead-store elim */

#define REPS 10000000L

/* vx: volatile so the optimiser cannot treat it as a compile-time constant */
static volatile int vx = 7;

#define BENCH(label, expr) do {                                        \
    double _t0 = now_ns();                                             \
    for (long _i = 0; _i < REPS; _i++) { sink += (long)(expr); }       \
    double _t1 = now_ns();                                             \
    printf("  %-46s %6.2f ns/call\n",                                  \
           (label), (_t1 - _t0) / REPS);                               \
} while (0)


/* 
 * 1. Struct sizes
 */
typedef struct node {
    int          value;
    struct node *next;
    int          refcount;
} node_t;

typedef int (*ctx_fn)(void *ctx, int x);
typedef struct { ctx_fn fn; void *ctx; } closure_t;


/* 
 * 2. Stack vs heap allocation
 */

/* NOINLINE: prevents escape analysis from eliminating the allocation */
NOINLINE static node_t make_node_stack(int v) {
    return (node_t){ v, NULL, 1 };
}

NOINLINE static node_t *make_node_heap(int v) {
    node_t *n = malloc(sizeof(node_t));
    n->value    = v;
    n->next     = NULL;
    n->refcount = 1;
    return n;
}


/* 
 * 3. Inline vs function-pointer call
 *
 * square_inlinable: ATTR_CONST but NOT NOINLINE.
 *   With a volatile input, the compiler still computes it at runtime, but
 *   can hoist the call out of the loop or CSE it -- the call vanishes.
 *
 * square_noinline: NOINLINE.
 *   Compiler cannot see the body; must make a real call every iteration.
 */
ATTR_CONST          static int square_inlinable(int x) { return x * x; }
NOINLINE ATTR_CONST static int square_noinline(int x)  { return x * x; }

typedef int (*int_fn)(int);


/* 
 * 4. Closure pair call vs direct call
 */
NOINLINE static int add_n_fn(void *ctx, int x)    { return x + *(int *)ctx; }
NOINLINE static int add_direct(int x, int n)       { return x + n; }

NOINLINE static int closure_call(closure_t c, int x) {
    return c.fn(c.ctx, x);
}


/* 
 * 5. Composition depth
 *
 * inc_ni: NOINLINE so that function-pointer calls through it are real.
 */
NOINLINE static int inc_ni(int x) { return x + 1; }

NOINLINE static int compose2(int_fn f, int_fn g, int x) {
    return f(g(x));
}
NOINLINE static int compose4(int_fn f, int_fn g, int x) {
    return compose2(f, g, compose2(f, g, x));
}
NOINLINE static int compose8(int_fn f, int_fn g, int x) {
    return compose4(f, g, compose4(f, g, x));
}
NOINLINE static int compose16(int_fn f, int_fn g, int x) {
    return compose8(f, g, compose8(f, g, x));
}




int main(void) {
    int ctx5 = 5;

    /* --- 1. Struct sizes */
    printf("-- 1. Struct sizes --\n");
    printf("  int                            : %2zu bytes\n", sizeof(int));
    printf("  node_t (int + ptr + int)       : %2zu bytes\n", sizeof(node_t));
    printf("  closure_t (fn_ptr + void*)     : %2zu bytes\n", sizeof(closure_t));
    printf("  (Python int: 28 bytes; Python Node with __slots__: ~56 bytes)\n");


    /* --- 2. Stack vs heap allocation */
    printf("\n-- 2. Stack vs heap allocation (NOINLINE to prevent elision) --\n");

    BENCH("stack: make_node_stack(vx).value",  make_node_stack(vx).value);

    {
        double t0 = now_ns();
        for (long i = 0; i < REPS; i++) {
            node_t *n = make_node_heap((int)vx);
            sink += n->value;
            free(n);
        }
        double t1 = now_ns();
        printf("  %-46s %6.2f ns/call\n",
               "heap:  make_node_heap(vx) + free",
               (t1 - t0) / REPS);
    }


    /* --- 3. Inline vs function-pointer call */
    printf("\n-- 3. Inline vs NOINLINE vs function pointer --\n");
    printf("  Note: with volatile input, inline expands vx*vx to 2 volatile reads;\n");
    printf("  NOINLINE loads vx once then passes a register -- call overhead ~0 ns.\n");

    /* inlinable: expanded inline, but vx*vx = 2 volatile reads (see note above) */
    BENCH("inlinable (2 volatile reads): square_inlinable(vx)", square_inlinable(vx));
    /* noinline: 1 volatile read + function call; call overhead barely visible */
    BENCH("NOINLINE (1 read + call):     square_noinline(vx)",  square_noinline(vx));
    /* function pointer through NOINLINE target -- same as noinline */
    {
        int_fn fp = square_noinline;
        BENCH("function pointer:             fp(vx)",            fp(vx));
    }


    /* --- 4. Closure pair call vs direct call */
    printf("\n-- 4. Closure call vs direct call (both NOINLINE) --\n");

    closure_t add5 = { add_n_fn, &ctx5 };
    BENCH("direct:        add_direct(vx, 5)",          add_direct(vx, 5));
    BENCH("closure call:  closure_call(add5, vx)",     closure_call(add5, vx));


    /* --- 5. Composition depth */
    printf("\n-- 5. Composition depth (NOINLINE function pointers) --\n");

    int_fn fp_inc = inc_ni;
    BENCH("depth  1: inc_ni(vx)",                      inc_ni(vx));
    BENCH("depth  2: compose2(fp_inc, fp_inc, vx)",    compose2(fp_inc, fp_inc, vx));
    BENCH("depth  4: compose4(fp_inc, fp_inc, vx)",    compose4(fp_inc, fp_inc, vx));
    BENCH("depth  8: compose8(fp_inc, fp_inc, vx)",    compose8(fp_inc, fp_inc, vx));
    BENCH("depth 16: compose16(fp_inc, fp_inc, vx)",   compose16(fp_inc, fp_inc, vx));


    /* --- 6. Summary */
    printf("\n-- 6. Summary (-O2, NOINLINE benchmark functions) --\n");
    printf("  Stack struct alloc  :  ~1 ns  (NOINLINE call; value lives in registers)\n");
    printf("  Heap malloc + free  : ~25 ns  (allocator + cache effects)\n");
    printf("  Inline function     :  ~1 ns  (volatile read dominates; call is free)\n");
    printf("  NOINLINE/fn pointer :  ~1 ns  (indirect branch; well-predicted in loop)\n");
    printf("  Closure call pair   : ~1-2 ns (load ctx + indirect branch)\n");
    printf("  Compose N (fn ptrs) : ~N * 1 ns (N indirect branches, linear)\n");
    printf("\n");
    printf("  For comparison -- Python function call: ~100-300 ns.\n");
    printf("  C/Python ratio for compute:             ~50-200x.\n");

    (void)sink;
    return 0;
}
