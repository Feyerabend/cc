/*
 * monads.c
 * Functional Patterns -- 8. Monads in C
 *
 * C has no monads. What it has is the manual equivalent: error codes
 * propagated through explicit if-checks. This file shows that pattern
 * in three forms, then compares each form to the monadic bind chain.
 *
 * Sections:
 *   1. Naive approach -- early return on error.
 *   2. goto cleanup   -- the C approximation of bind with resource cleanup.
 *   3. Result struct  -- a concrete maybe_int / result_int bind simulation.
 *   4. Macro bind     -- mechanically reducing the if (err) return err boilerplate.
 *   5. Side-by-side comparison of all styles on the same problem.
 *
 * Build:  cc -Wall -o monads monads.c
 * Run:    ./monads
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <ctype.h>

/* 
 * Error codes
 */
#define OK           0
#define ERR_PARSE   -1
#define ERR_RANGE   -2
#define ERR_LOGIC   -3

static const char *err_str(int err)
{
    switch (err) {
    case OK:         return "ok";
    case ERR_PARSE:  return "parse error";
    case ERR_RANGE:  return "out of range";
    case ERR_LOGIC:  return "logic error";
    default:         return "unknown error";
    }
}


/* 
 * 1. Naive approach: early return on error
 *
 * Each step checks the previous result before proceeding.
 * The if-checks ARE the bind operation, written by hand each time.
 */

static int step_parse(const char *s, int *out) {
    char *end;
    long  val = strtol(s, &end, 10);
    if (*end != '\0' || end == s) return ERR_PARSE;
    *out = (int)val;
    return OK;
}

static int step_positive(int n, int *out) {
    if (n <= 0) return ERR_RANGE;
    *out = n;
    return OK;
}

static int step_small(int n, int *out) {
    if (n > 100) return ERR_RANGE;
    *out = n;
    return OK;
}

static int step_double(int n, int *out) {
    *out = n * 2;
    return OK;
}

/* The pipeline -- early return style */
static int process_naive(const char *s, int *result) {
    int n, tmp, err;

    err = step_parse(s, &n);
    if (err) return err;          /* bind */

    err = step_positive(n, &tmp);
    if (err) return err;          /* bind */

    err = step_small(tmp, &tmp);
    if (err) return err;          /* bind */

    err = step_double(tmp, result);
    if (err) return err;          /* bind */

    return OK;
}


/* 
 * 2. goto cleanup
 *
 * When resources must be released on failure, goto is the C idiom.
 * The label collects all cleanup paths -- the monad's "context" made explicit.
 */
typedef struct { int value; int acquired; } Resource;

static Resource *acquire(int seed) {
    Resource *r = malloc(sizeof(Resource));
    if (!r) return NULL;
    r->value    = seed * 10;
    r->acquired = 1;
    return r;
}

static int use_resource(const Resource *r, int *out) {
    if (!r || r->value <= 0) return ERR_LOGIC;
    *out = r->value + 1;
    return OK;
}

static void release(Resource *r) { free(r); }

static int process_with_resources(int seed, int *result) {
    Resource *r1 = NULL, *r2 = NULL;
    int       err = OK, tmp = 0;

    r1 = acquire(seed);
    if (!r1) { err = ERR_LOGIC; goto done; }    /* bind */

    err = use_resource(r1, &tmp);
    if (err) goto done;                         /* bind */

    r2 = acquire(tmp);
    if (!r2) { err = ERR_LOGIC; goto done; }    /* bind */

    err = use_resource(r2, result);
    if (err) goto done;                         /* bind */

done:
    release(r2);   /* safe: free(NULL) is a no-op */
    release(r1);
    return err;
}


/* 
 * 3. Result struct -- explicit bind function
 *
 * We can make the bind pattern a little cleaner by encoding the result
 * and error together in a struct and writing a bind() function.
 * This is the most explicit C simulation of a monad.
 */
typedef struct {
    int  value;
    int  ok;
    char error[64];
} result_t;

static result_t result_ok(int v) {
    result_t r; r.value = v; r.ok = 1; r.error[0] = '\0'; return r;
}

static result_t result_err(int code, const char *msg) {
    result_t r; r.value = 0; r.ok = 0;
    snprintf(r.error, sizeof(r.error), "%s (code %d)", msg, code);
    return r;
}

/* bind: if r is ok, apply f; otherwise pass error through */
typedef result_t (*result_fn)(int);

static result_t bind(result_t r, result_fn f) {
    if (!r.ok) return r;
    return f(r.value);
}

/* Pipeline steps as result_fn */
static result_t r_positive(int n) {
    return n > 0 ? result_ok(n) : result_err(ERR_RANGE, "not positive");
}

static result_t r_small(int n) {
    return n <= 100 ? result_ok(n) : result_err(ERR_RANGE, "exceeds 100");
}

static result_t r_double(int n) { return result_ok(n * 2); }

static result_t r_parse(const char *s) {
    char *end;
    long  val = strtol(s, &end, 10);
    if (*end != '\0' || end == s)
        return result_err(ERR_PARSE, "not an integer");
    return result_ok((int)val);
}

static void print_result(const char *label, result_t r) {
    if (r.ok) printf("  %-24s Ok(%d)\n",  label, r.value);
    else      printf("  %-24s Err(%s)\n", label, r.error);
}


/* 
 * 4. Macro bind -- reduce the if (err) return err boilerplate
 *
 * TRY(expr) evaluates expr; if it returns non-zero, propagates the error.
 * This is the C preprocessor approximation of the do-notation used in
 * languages with native monad syntax (Haskell's do, Rust's ? operator).
 */
#define TRY(expr)           \
    do {                    \
        int _e = (expr);    \
        if (_e) return _e;  \
    } while (0)

static int process_macro(const char *s, int *result) {
    int n, tmp;
    TRY(step_parse(s, &n));
    TRY(step_positive(n, &tmp));
    TRY(step_small(tmp, &tmp));
    TRY(step_double(tmp, result));
    return OK;
}

/*
 * TRY is Rust's ? operator, spelled differently.
 * Rust's ? operator is exactly monadic bind for the Result type,
 * built into the language syntax.
 */


/* 
 * 5. Side-by-side comparison
 */

static void compare(const char *s) {
    int r1 = -999, r2 = -999, r3 = -999;

    int err1 = process_naive(s, &r1);
    int err2 = process_macro(s, &r3);

    result_t chain = bind(bind(bind(r_parse(s), r_positive), r_small), r_double);

    printf("  input=%-6s  naive=%-16s  macro=%-16s  bind_chain=%s\n",
           s,
           err1 == OK ? "ok" : err_str(err1),
           err2 == OK ? "ok" : err_str(err2),
           chain.ok   ? "ok" : chain.error);
    (void)r2;
}


/* 
 * main
 */
int main(void)
{
    /* --- 1. Naive early-return */
    printf("-- 1. Naive: early return on error --\n");
    {
        const char *inputs[] = { "42", "-5", "999", "??" };
        for (int i = 0; i < 4; i++) {
            int result = 0;
            int err    = process_naive(inputs[i], &result);
            if (err) printf("  %-6s -> error: %s\n", inputs[i], err_str(err));
            else     printf("  %-6s -> %d\n",        inputs[i], result);
        }
        printf("  Note: each 'if (err) return err' is a manual bind.\n");
    }

    /* --- 2. goto cleanup */
    printf("\n-- 2. goto cleanup --\n");
    {
        int result = 0;
        int err    = process_with_resources(3, &result);
        if (err) printf("  seed=3 -> error: %s\n",  err_str(err));
        else     printf("  seed=3 -> %d\n",          result);

        err = process_with_resources(0, &result);
        if (err) printf("  seed=0 -> error: %s\n",  err_str(err));
        else     printf("  seed=0 -> %d\n",          result);

        printf("  'goto done' is bind's short-circuit; 'done:' is the cleanup context.\n");
    }

    /* --- 3. Result struct + bind function */
    printf("\n-- 3. Result struct with bind() --\n");
    {
        const char *inputs[] = { "42", "-5", "999", "??" };
        for (int i = 0; i < 4; i++) {
            result_t r = bind(
                             bind(
                                 bind(r_parse(inputs[i]),
                                      r_positive),
                                 r_small),
                             r_double);
            print_result(inputs[i], r);
        }
        printf("  bind() = if (!r.ok) return r; else return f(r.value);\n");
    }

    /* --- 4. Macro TRY */
    printf("\n-- 4. Macro TRY (= Rust's ? operator) --\n");
    {
        const char *inputs[] = { "42", "-5", "999", "??" };
        for (int i = 0; i < 4; i++) {
            int result = 0;
            int err    = process_macro(inputs[i], &result);
            if (err) printf("  %-6s -> error: %s\n", inputs[i], err_str(err));
            else     printf("  %-6s -> %d\n",        inputs[i], result);
        }
        printf("  TRY(expr) expands to: int _e=expr; if(_e) return _e;\n");
        printf("  This is exactly Rust's ?, spelled with a macro.\n");
    }

    /* --- 5. Comparison */
    printf("\n-- 5. Side-by-side --\n");
    compare("42");
    compare("-5");
    compare("999");
    compare("??");

    /* --- Key observations */
    printf("\n-- Key observations --\n");
    printf("  if (err) return err  =  bind for the error monad, inlined.\n");
    printf("  goto done            =  bind's short-circuit + cleanup context.\n");
    printf("  bind(r, f)           =  if (!r.ok) return r; else f(r.value).\n");
    printf("  TRY macro            =  Rust's ? operator, preprocessor edition.\n");
    printf("  All four approaches express the same structure:\n");
    printf("  chain steps, stop at first failure, propagate the error.\n");
    printf("  The monad centralises that logic; C spreads it across call sites.\n");

    return 0;
}
