/*
 * closure.c
 * Functional Patterns -- 2. Closures
 *
 * C has no built-in closure syntax.  This file shows how to simulate them
 * using the "closure pair" idiom: a function pointer bundled with a pointer
 * to the environment it needs.
 *
 * Sections:
 *   1. The closure_t type (fn ptr + context ptr).
 *   2. make_adder: simple read-only environment.
 *   3. Mutable counter: environment holds state.
 *   4. Shared environment: two closures over one context.
 *   5. Lifetime hazard: stack-allocated context (what NOT to do).
 *   6. Heap-allocated context with explicit free.
 *
 * Build:  cc -Wall -o closure closure.c
 * Run:    ./closure
 */

#include <stdio.h>
#include <stdlib.h>

/* 
 * 1. The closure type
 *
 * Every C "closure" in this file is a (fn, ctx) pair.
 * fn  -- pointer to a function that takes the context and one int argument.
 * ctx -- pointer to the environment struct that fn needs.
 *
 * Calling a closure:   c.fn(c.ctx, x)
 */
typedef int (*closure_fn)(void *ctx, int x);

typedef struct {
    closure_fn fn;
    void      *ctx;
} closure_t;

/* Convenience: call a closure. */
static int closure_call(closure_t c, int x) {
    return c.fn(c.ctx, x);
}


/* 
 * 2. make_adder -- read-only environment
 *
 * Equivalent Python:
 *   def make_adder(n):
 *       def adder(x): return x + n
 *       return adder
 */
typedef struct { int n; } adder_ctx;

static int adder_fn(void *ctx, int x) {
    adder_ctx *c = (adder_ctx *)ctx;
    return x + c->n;
}

/* ctx must outlive the returned closure. */
static closure_t make_adder(adder_ctx *ctx, int n) {
    ctx->n = n;
    return (closure_t){ adder_fn, ctx };
}


/* 
 * 3. Mutable counter -- environment holds state
 *
 * Equivalent Python:
 *   def make_counter(start=0):
 *       count = start
 *       def increment(): nonlocal count; count += 1; return count
 *       return increment
 */
typedef struct { int count; int start; } counter_ctx;

static int increment_fn(void *ctx, int ignored) {
    (void)ignored;
    counter_ctx *c = (counter_ctx *)ctx;
    c->count += 1;
    return c->count;
}

static int reset_fn(void *ctx, int ignored) {
    (void)ignored;
    counter_ctx *c = (counter_ctx *)ctx;
    c->count = c->start;
    return c->count;
}

/* Returns two closures that share the same counter_ctx. */
static void make_counter(counter_ctx *ctx, int start, closure_t *inc_out, closure_t *rst_out) {
    ctx->count = start;
    ctx->start = start;
    *inc_out = (closure_t){ increment_fn, ctx };
    *rst_out = (closure_t){ reset_fn,     ctx };
}


/* 
 * 4. Shared environment -- deposit / withdraw over one balance
 *
 * Equivalent Python:
 *   def make_account(bal):
 *       def deposit(x):  nonlocal bal; bal += x; return bal
 *       def withdraw(x): nonlocal bal; bal -= x; return bal
 *       return deposit, withdraw
 */
typedef struct { int balance; } account_ctx;

static int deposit_fn(void *ctx, int amount) {
    account_ctx *c = (account_ctx *)ctx;
    c->balance += amount;
    return c->balance;
}

static int withdraw_fn(void *ctx, int amount) {
    account_ctx *c = (account_ctx *)ctx;
    c->balance -= amount;
    return c->balance;
}

static void make_account(account_ctx *ctx, int initial, closure_t *dep, closure_t *wit) {
    ctx->balance = initial;
    *dep = (closure_t){ deposit_fn,  ctx };
    *wit = (closure_t){ withdraw_fn, ctx };
}


/* 
 * 5. Lifetime hazard -- context on the stack
 *
 * This function is intentionally wrong!!  It returns a closure whose
 * context is a local struct.  After the function returns, the struct is
 * gone.  Calling the closure is undefined behaviour.
 *
 * In Python the runtime keeps the cell alive automatically.
 * In C, you must ensure the context outlives the closure.
 */
static closure_t bad_adder(int n) {
    adder_ctx local = { n };                /* lives on the stack */
    return (closure_t){ adder_fn, &local }; /* BUG: dangling pointer */
    /* local is destroyed when bad_adder returns */
}


/* 
 * 6. Heap-allocated context -- correct lifetime, manual free
 */
static closure_t heap_adder(int n) {
    adder_ctx *ctx = (adder_ctx *)malloc(sizeof(adder_ctx));
    if (!ctx) { fprintf(stderr, "malloc failed\n"); exit(1); }
    ctx->n = n;
    return (closure_t){ adder_fn, ctx };
    /* Caller must free(c.ctx) when done with the closure. */
}



int main(void) {
    /* --- 2. make_adder */
    printf("-- 2. make_adder --\n");
    {
        adder_ctx ctx5, ctx10;
        closure_t add5  = make_adder(&ctx5,  5);
        closure_t add10 = make_adder(&ctx10, 10);

        printf("  add5(3)  = %d\n", closure_call(add5,  3));   /* 8  */
        printf("  add10(3) = %d\n", closure_call(add10, 3));   /* 13 */

        /* The two closures have different context pointers. */
        printf("  independent contexts: %s\n",
               add5.ctx != add10.ctx ? "yes" : "no");
    }

    /* --- 3. counter */
    printf("\n-- 3. Mutable counter --\n");
    {
        counter_ctx cctx;
        closure_t inc, rst;
        make_counter(&cctx, 0, &inc, &rst);

        printf("  inc() = %d\n", closure_call(inc, 0));  /* 1 */
        printf("  inc() = %d\n", closure_call(inc, 0));  /* 2 */
        printf("  inc() = %d\n", closure_call(inc, 0));  /* 3 */
        closure_call(rst, 0);
        printf("  after reset, inc() = %d\n", closure_call(inc, 0));  /* 1 */
    }

    /* --- 4. shared environment */
    printf("\n-- 4. Shared environment (account) --\n");
    {
        account_ctx actx;
        closure_t dep, wit;
        make_account(&actx, 100, &dep, &wit);

        printf("  initial balance: %d\n", actx.balance);       /* 100 */
        printf("  deposit(50):  %d\n", closure_call(dep, 50)); /* 150 */
        printf("  withdraw(30): %d\n", closure_call(wit, 30)); /* 120 */
        printf("  balance: %d\n", actx.balance);               /* 120 */
    }

    /* --- 5. lifetime hazard (DO NOT call) */
    printf("\n-- 5. Lifetime hazard --\n");
    {
        closure_t bad = bad_adder(7);
        printf("  bad_adder returned a closure with a dangling context ptr.\n");
        printf("  Calling it would be undefined behavior -- skipping.\n");
        (void)bad;  /* suppress unused-variable warning */
    }

    /* --- 6. heap allocation */
    printf("\n-- 6. Heap-allocated context --\n");
    {
        closure_t c = heap_adder(42);
        printf("  heap_adder(42)(8) = %d\n", closure_call(c, 8));  /* 50 */
        free(c.ctx);   /* caller's responsibility */
        printf("  context freed.\n");
    }

    /* --- Key observation */
    printf("\n-- Key observation --\n");
    printf("  A C closure = (function pointer, context pointer).\n");
    printf("  Python hides both: the cell object IS the context,\n");
    printf("  the runtime manages its lifetime automatically.\n");
    printf("  In C, the programmer owns the lifetime contract.\n");

    return 0;
}
