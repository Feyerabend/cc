/*
 * higher.c
 * Functional Patterns -- 4. Higher-Order Functions
 *
 * Implements map, filter, and reduce for integer arrays using function
 * pointers, then shows the context-pointer pattern for predicates that
 * need captured state (the manual closure from section 2).
 *
 * Sections:
 *   1. map_int    -- apply transform to every element.
 *   2. filter_int -- keep elements matching a predicate.
 *   3. reduce_int -- fold array to a scalar.
 *   4. Chained pipeline: filter -> map -> reduce.
 *   5. Context-pointer pattern: predicate with captured threshold.
 *   6. apply_twice -- a simple custom higher-order function.
 *   7. Parallel map sketch -- how stateless transforms map to threads.
 *
 * Build:  cc -Wall -o higher higher.c
 * Run:    ./higher
 *
 * For the threaded section (section 7):
 *   cc -Wall -pthread -o higher higher.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* 
 * Shared types
 */
typedef int (*transform_fn)(int);
typedef int (*combine_fn)(int acc, int x);
typedef int (*predicate_fn)(int);
typedef int (*pred_ctx_fn)(void *ctx, int x);


/* 
 * 1. map_int
 *
 * Apply f to every element of in[0..n-1], write results to out[0..n-1].
 * Caller allocates out (at least n elements).
 */
static void map_int(const int *in, int *out, int n, transform_fn f) {
    for (int i = 0; i < n; i++)
        out[i] = f(in[i]);
}

/* 
 * 2. filter_int
 *
 * Copy elements of in[] for which pred returns non-zero into out[].
 * out must hold at least n elements (worst case: all pass).
 * Returns the number of elements written.
 */
static int filter_int(const int *in, int *out, int n, predicate_fn pred) {
    int count = 0;
    for (int i = 0; i < n; i++)
        if (pred(in[i]))
            out[count++] = in[i];
    return count;
}

/* 
 * 3. reduce_int
 *
 * Fold in[0..n-1] into a single value using f and an initial accumulator.
 */
static int reduce_int(const int *in, int n, int initial, combine_fn f) {
    int acc = initial;
    for (int i = 0; i < n; i++)
        acc = f(acc, in[i]);
    return acc;
}

/* 
 * Concrete functions used as arguments
 */
static int square(int x)            { return x * x; }
static int negate_fn(int x)         { return -x; }
static int double_it(int x)         { return x * 2; }
static int is_even(int x)           { return x % 2 == 0; }
static int is_odd(int x)            { return x % 2 != 0; }
static int add(int acc, int x)      { return acc + x; }
static int multiply(int acc, int x) { return acc * x; }
static int max2(int acc, int x)     { return acc > x ? acc : x; }

/* 
 * 5. Context-pointer pattern
 *
 * A plain predicate_fn cannot capture a runtime threshold.
 * We add a void* ctx parameter to carry the captured value.
 */
static int filter_ctx(const int *in, int *out, int n, pred_ctx_fn pred, void *ctx) {
    int count = 0;
    for (int i = 0; i < n; i++)
        if (pred(ctx, in[i]))
            out[count++] = in[i];
    return count;
}

/* Predicate: keep values greater than *(int*)ctx */
static int gt_threshold(void *ctx, int x) {
    int threshold = *(int *)ctx;
    return x > threshold;
}

/* Predicate: keep values in [lo, hi] stored in a small struct */
typedef struct { int lo; int hi; } range_t;

static int in_range(void *ctx, int x) {
    range_t *r = (range_t *)ctx;
    return x >= r->lo && x <= r->hi;
}

/* 
 * 6. apply_twice -- a custom higher-order function
 */
static int apply_twice(transform_fn f, int x) {
    return f(f(x));
}

/* 
 * Utility: print an int array
 */
static void print_arr(const char *label, const int *arr, int n) {
    printf("  %-26s [", label);
    for (int i = 0; i < n; i++)
        printf("%s%d", i ? ", " : "", arr[i]);
    printf("]\n");
}

/* 
 * 7. Parallel map sketch using pthreads
 *
 * Each thread maps square() over its own slice of the input.
 * No shared mutable state: no locks needed.
 */
#ifdef __has_include
#  if __has_include(<pthread.h>)
#    define HAVE_PTHREADS 1
#  endif
#endif

#ifdef HAVE_PTHREADS
#include <pthread.h>

typedef struct {
    const int *in;
    int       *out;
    int        start;
    int        end;
    transform_fn f;
} slice_t;

static void *map_slice(void *arg) {
    slice_t *s = (slice_t *)arg;
    for (int i = s->start; i < s->end; i++)
        s->out[i] = s->f(s->in[i]);
    return NULL;
}

#define NUM_THREADS 4

static void parallel_map(const int *in, int *out, int n, transform_fn f) {
    pthread_t threads[NUM_THREADS];
    slice_t   slices[NUM_THREADS];
    int chunk = n / NUM_THREADS;

    for (int t = 0; t < NUM_THREADS; t++) {
        slices[t].in = in;
        slices[t].out = out;
        slices[t].start = t * chunk;
        slices[t].end = (t == NUM_THREADS - 1) ? n : (t + 1) * chunk;
        slices[t].f = f;
        pthread_create(&threads[t], NULL, map_slice, &slices[t]);
    }
    for (int t = 0; t < NUM_THREADS; t++)
        pthread_join(threads[t], NULL);
}
#endif  /* HAVE_PTHREADS */



int main(void) {
    int nums[]  = { 1, 2, 3, 4, 5, 6, 7, 8 };
    int n       = (int)(sizeof(nums) / sizeof(nums[0]));
    int buf[8];   /* reused as output buffer */
    int count;

    /* --- 1. map */
    printf("-- 1. map --\n");

    map_int(nums, buf, n, square);
    print_arr("square:", buf, n);

    map_int(nums, buf, n, negate_fn);
    print_arr("negate:", buf, n);

    map_int(nums, buf, n, double_it);
    print_arr("double:", buf, n);

    /* --- 2. filter */
    printf("\n-- 2. filter --\n");

    count = filter_int(nums, buf, n, is_even);
    print_arr("evens:", buf, count);

    count = filter_int(nums, buf, n, is_odd);
    print_arr("odds:", buf, count);

    /* --- 3. reduce */
    printf("\n-- 3. reduce --\n");
    printf("  sum:     %d\n", reduce_int(nums, n, 0, add));        /* 36    */
    printf("  product: %d\n", reduce_int(nums, n, 1, multiply));   /* 40320 */
    printf("  max:     %d\n", reduce_int(nums, n, nums[0], max2)); /* 8     */

    /* --- 4. Pipeline: filter evens -> square -> sum */
    printf("\n-- 4. Pipeline: evens -> squared -> sum --\n");
    {
        int filtered[8], mapped[8];
        int nf, result;

        nf     = filter_int(nums, filtered, n, is_even);
        map_int(filtered, mapped, nf, square);
        result = reduce_int(mapped, nf, 0, add);

        print_arr("evens:", filtered, nf);
        print_arr("evens squared:", mapped, nf);
        printf("  sum of squared evens: %d\n", result);  /* 120 */
    }

    /* --- 5. Context-pointer pattern */
    printf("\n-- 5. Context-pointer (predicate with captured state) --\n");
    {
        int threshold = 4;
        count = filter_ctx(nums, buf, n, gt_threshold, &threshold);
        printf("  threshold=%d, elements > threshold: ", threshold);
        print_arr("", buf, count);

        range_t r = { 3, 6 };
        count = filter_ctx(nums, buf, n, in_range, &r);
        printf("  range=[%d,%d], elements in range: ", r.lo, r.hi);
        print_arr("", buf, count);
    }

    /* --- 6. apply_twice */
    printf("\n-- 6. apply_twice --\n");
    printf("  apply_twice(square,    3) = %d\n", apply_twice(square,    3)); /* 81 */
    printf("  apply_twice(negate_fn, 5) = %d\n", apply_twice(negate_fn, 5)); /* 5 */
    printf("  apply_twice(double_it, 3) = %d\n", apply_twice(double_it, 3)); /* 12 */

    /* --- 7. Parallel map */
    printf("\n-- 7. Parallel map --\n");
#ifdef HAVE_PTHREADS
    {
        int big[8];
        parallel_map(nums, big, n, square);
        print_arr("parallel squares:", big, n);
        printf("  (each thread processed its own slice -- no locks)\n");
    }
#else
    printf("  (pthreads not available; parallel section skipped)\n");
#endif

    /* --- Key observations */
    printf("\n-- Key observations --\n");
    printf("  map_int owns the loop; transform_fn owns the per-element logic.\n");
    printf("  filter requires the caller to size the output buffer.\n");
    printf("  A plain function pointer cannot capture state: use (fn, ctx).\n");
    printf("  Stateless transforms require no locks when parallelised.\n");

    return 0;
}
