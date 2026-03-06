/*
 * functors.c
 * Functional Patterns -- 7. Functors in C
 *
 * This file exists to show WHY functors are awkward in C, not to
 * recommend the patterns here for production use.
 *
 * Three attempts, in order of increasing generality:
 *
 *   1. Concrete Maybe for one type (maybe_int).
 *      Clear and correct. Problem: must be fully duplicated per type.
 *
 *   2. Generic void* Maybe.
 *      One struct for all types, but no type safety.
 *      A wrong function pointer silently corrupts memory.
 *
 *   3. Macro-generated Maybe.
 *      DECLARE_MAYBE(T) generates maybe_T and map_maybe_T.
 *      Reduces source duplication; compiler errors become unreadable.
 *
 *   4. Result type -- same story as Maybe.
 *
 *   Conclusion: in C, write the specific struct for the specific type.
 *   Do not build a generic functor hierarchy.
 *
 * Build:  cc -Wall -o functors functors.c
 * Run:    ./functors
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

typedef int    (*int_fn)(int);
typedef double (*dbl_fn)(double);


/* 
 * Attempt 1: Concrete Maybe for int
 *
 * Everything below must be copy-pasted and edited for every new type.
 * maybe_double, maybe_long, maybe_point_t ... all look identical.
 */

typedef struct { int value; int present; } maybe_int;

static maybe_int just_int(int v) { return (maybe_int){ v, 1 }; }
static maybe_int nothing_int(void) { return (maybe_int){ 0, 0 }; }

static maybe_int map_maybe_int(maybe_int m, int_fn f) {
    if (!m.present) return nothing_int();
    return just_int(f(m.value));
}

static void print_maybe_int(const char *label, maybe_int m) {
    if (m.present) printf("  %-34s Just(%d)\n", label, m.value);
    else           printf("  %-34s Nothing\n",  label);
}

/* Identical struct and functions, different type: */
typedef struct { double value; int present; } maybe_double;

static maybe_double just_dbl(double v) { return (maybe_double){ v, 1 }; }
static maybe_double nothing_dbl(void) { return (maybe_double){ 0.0, 0 }; }

static maybe_double map_maybe_double(maybe_double m, dbl_fn f) {
    if (!m.present) return nothing_dbl();
    return just_dbl(f(m.value));
}

/* Every line above is a copy of the int version with "int" replaced by
 * "double". This is the boilerplate cost of concrete Maybe in C. */


/* 
 * Attempt 2: Generic void* Maybe
 *
 * One struct covers all types -- but the compiler can no longer verify
 * that the function pointer matches the stored type.
 */

typedef struct { void *value; } maybe_t;   /* NULL = Nothing */

static maybe_t maybe_just(const void *val, size_t size) {
    void *copy = malloc(size);
    memcpy(copy, val, size);
    return (maybe_t){ copy };
}

static maybe_t maybe_nothing(void) { return (maybe_t){ NULL }; }
static int maybe_is_nothing(maybe_t m) { return m.value == NULL; }
static void maybe_free(maybe_t m) { free(m.value); }

/* f must match the actual stored type -- checked only by the programmer */
typedef void (*generic_fn)(const void *in, void *out);

static maybe_t map_maybe(maybe_t m, generic_fn f, size_t out_size) {
    if (maybe_is_nothing(m)) return maybe_nothing();
    void *result = malloc(out_size);
    f(m.value, result);
    return (maybe_t){ result };
}

/* One adapter function still needed per transformation: */
static void double_int_fn(const void *in, void *out)
    { *(int *)out = *(const int *)in * 2; }

static void square_int_fn(const void *in, void *out)
    { *(int *)out = *(const int *)in * *(const int *)in; }

/* Passing the wrong adapter (e.g. double_int_fn to a maybe_double) would
 * compile without complaint and produce garbage. No safety net. */


/* 
 * Attempt 3: Macro-generated Maybe
 *
 * DECLARE_MAYBE(T) emits a complete maybe_T type and its map function.
 * Avoids copy-paste; error messages become incomprehensible.
 */

#define DECLARE_MAYBE(T)                                           \
    typedef struct { T value; int present; } maybe_##T;            \
    static maybe_##T just_##T(T v)                                 \
        { return (maybe_##T){ v, 1 }; }                            \
    static maybe_##T nothing_##T(void)                             \
        { return (maybe_##T){ (T){0}, 0 }; }                       \
    static maybe_##T map_maybe_##T(maybe_##T m, T (*f)(T))         \
    {                                                              \
        if (!m.present) return nothing_##T();                      \
        return just_##T(f(m.value));                               \
    }

DECLARE_MAYBE(float)
DECLARE_MAYBE(long)

static float  square_float(float x)  { return x * x; }
static long   negate_long(long x)    { return -x; }

/*
 * The macro correctly generates separate types: maybe_float and maybe_long
 * are distinct. Passing a maybe_long to map_maybe_float IS a compile error.
 * But errors INSIDE a macro expansion report the expanded line, not the
 * source line -- making debugging painful.
 *
 * Try: map_maybe_float(just_float(2.0f), negate_long) -- type mismatch,
 * but the error message says nothing useful about where the problem is.
 */


/* 
 * Result type -- same story
 */

typedef struct {
    int  value;
    int  ok;
    char error[64];
} result_int;

static result_int result_ok(int v)
    { return (result_int){ v, 1, "" }; }

static result_int result_err(const char *e) {
    result_int r = { 0, 0, "" };
    strncpy(r.error, e, sizeof(r.error) - 1);
    return r;
}

static result_int map_result_int(result_int r, int_fn f) {
    if (!r.ok) return r;
    return result_ok(f(r.value));
}

static void print_result_int(const char *label, result_int r) {
    if (r.ok) printf("  %-34s Ok(%d)\n",  label, r.value);
    else      printf("  %-34s Err(%s)\n", label, r.error);
}

static int double_it(int x) { return x * 2; }
static int square_it(int x) { return x * x; }



int main(void) {
    /* --- 1. Concrete maybe_int */
    printf("-- 1. Concrete maybe_int --\n");
    {
        maybe_int j = just_int(10);
        maybe_int n = nothing_int();

        print_maybe_int("just(10).map(*2):", map_maybe_int(j, double_it));
        print_maybe_int("nothing.map(*2):", map_maybe_int(n, double_it));
        print_maybe_int("just(10).map(*2).map(sq):", map_maybe_int(map_maybe_int(j, double_it), square_it));
    }

    printf("\n  -- maybe_double: identical code, different type --\n");
    {
        maybe_double jd = just_dbl(3.5);
        maybe_double nd = nothing_dbl();
        (void)nd;
        (void)map_maybe_double;   /* suppress unused-function warning */
        printf("  just_dbl(3.5) maps fine (present=%d) -- all code duplicated.\n",
               jd.present);
        printf("  To add maybe_long, maybe_float, maybe_point_t: repeat again.\n");
    }

    /* --- 2. Generic void* */
    printf("\n-- 2. Generic void* Maybe --\n");
    {
        int val = 21;
        maybe_t m = maybe_just(&val, sizeof(int));
        maybe_t emp = maybe_nothing();

        maybe_t doubled = map_maybe(m, double_int_fn, sizeof(int));
        maybe_t squared = map_maybe(m, square_int_fn, sizeof(int));
        maybe_t nothing = map_maybe(emp, double_int_fn, sizeof(int));

        printf("  just(21).map(*2)   = %d\n", *(int *)doubled.value);
        printf("  just(21).map(sq)   = %d\n", *(int *)squared.value);
        printf("  nothing.map(*2)    = %s\n",
               maybe_is_nothing(nothing) ? "Nothing" : "has value");

        printf("  Danger: passing square_int_fn to a maybe_double compiles fine.\n");
        printf("  Result: reads int bits as double -- silent garbage, no error.\n");

        maybe_free(m);
        maybe_free(doubled);
        maybe_free(squared);
        /* emp, nothing: NULL -- free(NULL) is a no-op */
    }

    /* --- 3. Macro-generated */
    printf("\n-- 3. Macro-generated DECLARE_MAYBE(T) --\n");
    {
        maybe_float mf  = just_float(4.0f);
        maybe_float mf2 = map_maybe_float(mf, square_float);
        printf("  just_float(4.0).map(sq) = Just(%.1f)\n", mf2.value);

        maybe_long ml  = just_long(-7L);
        maybe_long ml2 = map_maybe_long(ml, negate_long);
        printf("  just_long(-7).map(neg)  = Just(%ld)\n", ml2.value);

        maybe_float nothing_f = nothing_float();
        maybe_float nf2       = map_maybe_float(nothing_f, square_float);
        printf("  nothing_float.map(sq)   = %s\n",
               nf2.present ? "Just(...)" : "Nothing");

        printf("  Macro works. But a typo in the macro body reports an error\n");
        printf("  at the expansion site with the mangled generated name.\n");
        printf("  Debuggers show the generated struct, not the macro source.\n");
    }

    /* --- 4. result_int */
    printf("\n-- 4. Concrete result_int --\n");
    {
        result_int ok  = result_ok(10);
        result_int err = result_err("network timeout");

        print_result_int("ok(10).map(*2):", map_result_int(ok,  double_it));
        print_result_int("err(...).map(*2):", map_result_int(err, double_it));
        print_result_int("ok(10).map(*2).map(sq):", map_result_int(map_result_int(ok, double_it), square_it));
        print_result_int("err.map(*2).map(sq):", map_result_int(map_result_int(err, double_it), square_it));
    }

    /* --- Conclusion */
    printf("\n-- Conclusion --\n");
    printf("  Attempt 1 (concrete): type-safe and readable.\n");
    printf("    Cost: O(types) duplication. Every new type = rewrite everything.\n\n");
    printf("  Attempt 2 (void*): one struct, zero type safety.\n");
    printf("    Cost: wrong fn pointer -> silent memory corruption, no compile check.\n\n");
    printf("  Attempt 3 (macros): reduces source repetition.\n");
    printf("    Cost: cryptic error messages, poor debugger support.\n\n");
    printf("  Right answer in C: write maybe_int for int, stop there.\n");
    printf("  The functor abstraction requires parametric polymorphism\n");
    printf("  (C++ templates, Rust generics/traits) to be genuinely useful.\n");
    printf("  In C, the boilerplate cost exceeds the abstraction benefit.\n");

    return 0;
}
