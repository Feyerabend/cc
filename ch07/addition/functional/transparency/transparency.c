/*
 * transparency.c
 * Functional Patterns -- 9. Referential Transparency
 *
 * Shows which C functions are referentially transparent and which are not,
 * the GCC/Clang annotations that communicate RT to the compiler,
 * and the connection between RT violations and data races.
 *
 * Sections:
 *   1. Pure functions -- the compiler can reason about these freely.
 *   2. RT violations: static locals, global state, errno, rand().
 *   3. __attribute__((pure)) and __attribute__((const)).
 *   4. What the optimiser does with RT: CSE, loop hoisting, dead elim.
 *   5. Data races as RT violations (pthreads demo).
 *   6. The fix: eliminate shared mutable state.
 *
 * Build:            cc -Wall -O2 -o transparency transparency.c
 * With pthreads:    cc -Wall -O2 -pthread -o transparency transparency.c
 * Run:              ./transparency
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <errno.h>
#include <time.h>

/* 
 * 1. Referentially transparent functions
 *
 * Output determined entirely by arguments.
 * No global reads, no global writes, no I/O.
 */
static int square(int x)      { return x * x; }
static int add(int a, int b)  { return a + b; }
static int factorial(int n)   { return n <= 1 ? 1 : n * factorial(n-1); }

static long sum_of_squares(long n) {
    long s = 0;
    for (long i = 0; i < n; i++) s += i * i;
    return s;
}

/* 
 * 2. RT violations
 */

/* 2a. Static local -- hidden state between calls */
static int next_id(void) {
    static int counter = 0;   /* survives across calls -- hidden global */
    return ++counter;
}

/* 2b. Global mutation */
static int g_state = 0;

static int impure_add(int x) {
    g_state += x;             /* modifies global -- side effect */
    return g_state;
}

/* 2c. errno: standard library side channel */
static double safe_log(double x) {
    errno = 0;
    double r = log(x);
    if (errno) return -1.0;
    return r;
}
/* log() sets errno on error -- a global side channel.
 * Two threads calling log() simultaneously can corrupt each other's errno
 * (unless errno is thread-local, which POSIX requires but C89 does not). */

/* 2d. rand() -- global seed state */
static int random_roll(void) { return rand() % 6 + 1; }

/* 
 * 3. GCC/Clang RT annotations
 *
 * __attribute__((const))  -- result depends only on arguments; reads no memory.
 * __attribute__((pure))   -- result depends on arguments + readable memory;
 *                            no writes.
 *
 * These tell the optimiser it may:
 *   - Eliminate redundant calls (CSE).
 *   - Hoist calls out of loops.
 *   - Remove calls whose results are unused.
 */

#if defined(__GNUC__) || defined(__clang__)
#  define ATTR_CONST __attribute__((const))
#  define ATTR_PURE  __attribute__((pure))
#else
#  define ATTR_CONST
#  define ATTR_PURE
#endif

ATTR_CONST static int square_const(int x)      { return x * x; }
ATTR_CONST static int add_const(int a, int b)  { return a + b; }

ATTR_PURE  static int strlen_pure(const char *s) {
    int n = 0;
    while (s[n]) n++;
    return n;
}

/* 
 * 4. What the optimiser does with ATTR_CONST
 *
 * Without annotation, the compiler must assume square() might touch memory.
 * With ATTR_CONST it may fold, hoist, and eliminate calls.
 *
 * We cannot easily observe this in output, but we can write code that
 * would be wasteful without the annotation and verify correctness.
 */
static long loop_with_invariant(int scale, long n) {
    /* Without ATTR_CONST: square_const(scale) might be called n times.
     * With ATTR_CONST:    compiler hoists it -- called once. */
    long total = 0;
    for (long i = 0; i < n; i++)
        total += i * square_const(scale);
    return total;
}

/* 
 * 5. Data race demo (pthreads)
 *
 * A non-RT function modifying shared state causes a data race.
 * The race means the output is not determined by the arguments alone.
 */
#ifdef HAVE_PTHREADS
#include <pthread.h>

static long shared_counter = 0;

static void *racy_increment(void *arg) {
    long n = *(long *)arg;
    for (long i = 0; i < n; i++)
        shared_counter++;   /* read-modify-write: not atomic, not RT */
    return NULL;
}

static void *safe_local(void *arg) {
    /* Pure: accumulates into a local, returns through arg pointer.
     * No shared state: no race possible. */
    long  n      = ((long*)arg)[0];
    long *result = &((long*)arg)[1];
    long  local  = 0;
    for (long i = 0; i < n; i++) local++;
    *result = local;
    return NULL;
}
#endif  /* HAVE_PTHREADS */

/* 
 * 6. The fix: eliminate shared mutable state
 *
 * The RT-compatible version of a "global counter" passes its state
 * explicitly and returns the new state -- no mutation.
 */
static int pure_next_id(int current) { return current + 1; }



int main(void) {
    /* --- 1. Pure functions */
    printf("-- 1. Referentially transparent --\n");
    printf("  square(5)       = %d\n", square(5));
    printf("  square(5)       = %d  (always the same)\n", square(5));
    printf("  add(3,4)        = %d\n", add(3, 4));
    printf("  factorial(6)    = %d\n", factorial(6));
    printf("  sum_squares(5)  = %ld\n", sum_of_squares(5));  /* 0+1+4+9+16=30 */

    /* --- 2. RT violations */
    printf("\n-- 2. RT violations --\n");

    printf("  next_id()       = %d\n", next_id());
    printf("  next_id()       = %d  (same call, different result)\n", next_id());

    printf("  impure_add(5)   = %d\n", impure_add(5));
    printf("  impure_add(5)   = %d  (hidden global changes result)\n", impure_add(5));

    errno = 0;
    double lr = safe_log(2.718);
    printf("  safe_log(e)     = %.4f  (uses errno side channel)\n", lr);

    srand(42);
    printf("  random_roll()   = %d\n", random_roll());
    srand(42);   /* reset seed */
    printf("  random_roll()   = %d  (same seed -> same result, but seed is global)\n",
           random_roll());

    /* --- 3. Annotated functions */
    printf("\n-- 3. ATTR_CONST / ATTR_PURE annotations --\n");
    printf("  square_const(7) = %d  (compiler may CSE/hoist/eliminate)\n",
           square_const(7));
    printf("  add_const(3,4)  = %d\n", add_const(3, 4));
    printf("  strlen_pure(\"hello\") = %d\n", strlen_pure("hello"));

    /* --- 4. Loop with invariant */
    printf("\n-- 4. Loop with invariant call --\n");
    {
        long result = loop_with_invariant(3, 1000000L);
        printf("  sum(i * square_const(3), i=0..1M-1) = %ld\n", result);
        printf("  With ATTR_CONST, compiler hoists square_const(3)=9 out of loop.\n");
        printf("  Without annotation, compiler must call it 1,000,000 times.\n");
    }

    /* --- 5. Data race demo */
    printf("\n-- 5. Data race = RT violation under concurrency --\n");
#ifdef HAVE_PTHREADS
    {
        pthread_t t1, t2;
        long      n = 100000L;

        /* Racy: two threads increment a shared counter */
        shared_counter = 0;
        pthread_create(&t1, NULL, racy_increment, &n);
        pthread_create(&t2, NULL, racy_increment, &n);
        pthread_join(t1, NULL);
        pthread_join(t2, NULL);
        printf("  racy: expected %ld, got %ld  (may differ due to race)\n",
               2 * n, shared_counter);

        /* Safe: each thread accumulates locally */
        long args1[2] = { n, 0 };
        long args2[2] = { n, 0 };
        pthread_create(&t1, NULL, safe_local, args1);
        pthread_create(&t2, NULL, safe_local, args2);
        pthread_join(t1, NULL);
        pthread_join(t2, NULL);
        printf("  safe:  t1=%ld, t2=%ld, total=%ld  (always correct)\n",
               args1[1], args2[1], args1[1] + args2[1]);
    }
#else
    printf("  (pthreads not available -- skipping race demo)\n");
    printf("  Principle: racy_increment reads-modifies-writes shared_counter;\n");
    printf("  two threads interleave those three steps -> lost updates.\n");
    printf("  RT violation (output depends on scheduler) causes the race.\n");
#endif

    /* --- 6. The fix */
    printf("\n-- 6. Fix: explicit state, no mutation --\n");
    {
        int id = 0;
        id = pure_next_id(id);  printf("  id=%d\n", id);
        id = pure_next_id(id);  printf("  id=%d\n", id);
        id = pure_next_id(id);  printf("  id=%d\n", id);
        printf("  pure_next_id(n) = n+1: RT, thread-safe, no hidden state.\n");
        printf("  Caller owns the state; function transforms it functionally.\n");
    }

    /* --- The bridge */
    printf("\n-- The bridge --\n");
    printf("  Pure function  ->  no shared mutable state\n");
    printf("  No shared mutable state  ->  no data race\n");
    printf("  No data race  ->  no locks needed\n");
    printf("  No locks needed  ->  composable across threads\n");
    printf("  RT is the property that makes all previous claims hold.\n");

    return 0;
}
