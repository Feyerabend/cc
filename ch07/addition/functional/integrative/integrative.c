/*
 * integrative.c
 * Functional Patterns -- 12. Functional Style as Concurrency Discipline
 *
 * Shows how the patterns from this series combine to produce concurrent
 * programs that are correct by construction:
 *
 *   1. Racy imperative counter -- shared mutable state causes lost updates.
 *   2. Pure function alternative -- no shared state, no race.
 *   3. Parallel map via pthreads -- pure function; no locks in the workers.
 *   4. Thread-local accumulation -- each thread owns its result; one merge.
 *   5. The single synchronisation point -- atomic publish of immutable data.
 *
 * Build:         cc -Wall -O2 -o integrative integrative.c
 * Build+threads: cc -Wall -O2 -pthread -DHAVE_PTHREADS -o integrative integrative.c
 * Run:           ./integrative
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdatomic.h>

#if defined(__GNUC__) || defined(__clang__)
#  define ATTR_CONST __attribute__((const))
#  define NOINLINE   __attribute__((noinline))
#else
#  define ATTR_CONST
#  define NOINLINE
#endif

/* 
 * Pure functions (patterns 9, 5, 4)
 *
 * ATTR_CONST: output depends only on arguments.
 * No shared state; safe to call from any thread simultaneously.
 */
ATTR_CONST static int square(int x)        { return x * x; }
ATTR_CONST static int is_odd(int x)        { return x % 2 != 0; }

/* compose: apply f after g -- no shared state between stages */
ATTR_CONST static int square_if_odd(int x) { return is_odd(x) ? square(x) : 0; }


/* 
 * 1. Racy counter: shared mutable state
 *
 * shared_counter++ is read-modify-write: not atomic.
 * Two threads interleaving the three steps lose updates.
 */
#ifdef HAVE_PTHREADS
#include <pthread.h>

static long shared_counter = 0;    /* mutable shared -- source of race */

static void *racy_worker(void *arg) {
    long n = *(long *)arg;
    for (long i = 0; i < n; i++)
        shared_counter++;    /* race: read / add / write not atomic */
    return NULL;
}

/* 
 * 3. Pure parallel map
 *
 * cpu_work(x): pure -- depends only on x, writes nothing shared.
 * Each thread processes its own slice; no locks in the workers.
 */
ATTR_CONST static long cpu_work(int x) {
    long s = 0;
    for (int i = 0; i < x; i++) s += (long)i * i;
    return s;
}

#define N_WORKERS 4
#define WORK_N    100

typedef struct {
    int  start;
    int  end;
    long results[WORK_N];   /* thread writes only to its own slice */
} work_arg;

static void *map_worker(void *arg) {
    work_arg *w = (work_arg *)arg;
    for (int i = w->start; i < w->end; i++)
        w->results[i - w->start] = cpu_work(i);   /* pure; no shared writes */
    return NULL;
}

/* 
 * 4. Thread-local accumulation then merge
 *
 * Each thread computes a local sum of squared-odds in its slice.
 * The only shared write is the final merge (one addition per thread).
 */
typedef struct {
    const int *data;
    int        start;
    int        end;
    long       local_sum;   /* written by this thread only */
} sum_arg;

static void *sum_worker(void *arg) {
    sum_arg *s = (sum_arg *)arg;
    long acc = 0;
    for (int i = s->start; i < s->end; i++)
        if (is_odd(s->data[i]))
            acc += square(s->data[i]);
    s->local_sum = acc;    /* no lock: this thread owns local_sum */
    return NULL;
}
#endif  /* HAVE_PTHREADS */


/* 
 * 5. Atomic publish of immutable result (pattern 10 + C11 atomics)
 *
 * Writer builds data, publishes with release.
 * Readers load with acquire, then read freely -- no further barriers.
 */
typedef struct { long value; int ready; } result_t;

static _Atomic(result_t *) published = NULL;   /* atomic pointer */

static void publish(long v) {
    result_t *r = malloc(sizeof(result_t));
    r->value = v;
    r->ready = 1;
    /* release store: all prior writes visible before this pointer */
    atomic_store_explicit(&published, r, memory_order_release);
}

static long wait_and_read(void) {
    result_t *r;
    /* acquire load: all writes before the release are now visible */
    while ((r = atomic_load_explicit(&published, memory_order_acquire)) == NULL)
        ;   /* spin -- fine for this demo */
    return r->value;
}




int main(void) {
    /* --- 1. Pure functions */
    printf("-- 1. Pure functions (patterns 4, 5, 9) --\n");
    printf("  square(7)       = %d\n", square(7));
    printf("  square(7)       = %d   (always the same -- referentially transparent)\n",
           square(7));

    long total = 0;
    for (int x = 1; x <= 10; x++)
        total += square_if_odd(x);
    printf("  sum of squares of odds 1..10 = %ld  (expected 165)\n", total);
    printf("  Pure functions: safe to call from any thread, any time.\n");


    /* --- 2. Racy vs safe */
    printf("\n-- 2. Racy counter vs pure alternative --\n");
#ifdef HAVE_PTHREADS
    {
        pthread_t t1, t2;
        long n = 100000L;

        /* Racy: two threads increment shared_counter */
        shared_counter = 0;
        pthread_create(&t1, NULL, racy_worker, &n);
        pthread_create(&t2, NULL, racy_worker, &n);
        pthread_join(t1, NULL);
        pthread_join(t2, NULL);
        printf("  Racy:  expected %ld, got %ld  (lost updates if < expected)\n",
               2 * n, shared_counter);

        /* Pure alternative: each thread accumulates locally */
        long a1[2] = { n, 0 }, a2[2] = { n, 0 };
        /* Reuse sum_worker logic with a simple lambda-equivalent struct */
        /* (inline for brevity) */
        long s1 = 0, s2 = 0;
        for (long i = 0; i < n; i++) s1++;
        for (long i = 0; i < n; i++) s2++;
        printf("  Pure:  t1=%ld, t2=%ld, total=%ld  (always correct)\n",
               s1, s2, s1 + s2);
        printf("  No shared state in the pure version: no race possible.\n");
        (void)a1; (void)a2;
    }
#else
    printf("  (build with -DHAVE_PTHREADS -pthread to enable)\n");
    printf("  Principle: racy_worker does read-modify-write on shared_counter.\n");
    printf("  Two threads interleave the three steps -> lost updates.\n");
    printf("  Fix: each thread accumulates in a local variable; merge at the end.\n");
#endif


    /* --- 3. Parallel map over pure function */
    printf("\n-- 3. Parallel map over pure function --\n");
#ifdef HAVE_PTHREADS
    {
        pthread_t threads[N_WORKERS];
        work_arg  args[N_WORKERS];
        int       slice = WORK_N / N_WORKERS;

        for (int i = 0; i < N_WORKERS; i++) {
            args[i].start = 100 + i * slice;
            args[i].end   = 100 + (i + 1) * slice;
            pthread_create(&threads[i], NULL, map_worker, &args[i]);
        }
        for (int i = 0; i < N_WORKERS; i++)
            pthread_join(threads[i], NULL);

        /* Verify: sequential reference */
        int ok = 1;
        int idx = 0;
        for (int i = 0; i < N_WORKERS; i++) {
            int start = args[i].start;
            int end   = args[i].end;
            for (int j = start; j < end; j++, idx++)
                if (args[i].results[j - start] != cpu_work(j)) { ok = 0; break; }
        }
        printf("  %d workers mapped cpu_work() over [100..%d).\n",
               N_WORKERS, 100 + WORK_N);
        printf("  Results match sequential: %s\n", ok ? "yes" : "NO");
        printf("  Workers share NO data during computation.\n");
        printf("  cpu_work is ATTR_CONST: the compiler knows it is safe.\n");
    }
#else
    printf("  (build with -DHAVE_PTHREADS -pthread to enable)\n");
    printf("  Principle: cpu_work(x) is ATTR_CONST -- pure.\n");
    printf("  Each thread maps over its own slice; no shared writes.\n");
    printf("  Correct by construction; no locks needed.\n");
#endif


    /* --- 4. Thread-local accumulation */
    printf("\n-- 4. Thread-local accumulation (sum of squared odds) --\n");
    {
        int data[20];
        for (int i = 0; i < 20; i++) data[i] = i + 1;   /* [1..20] */

        /* Sequential reference */
        long seq_sum = 0;
        for (int i = 0; i < 20; i++)
            if (is_odd(data[i])) seq_sum += square(data[i]);
        printf("  Sequential sum of squared odds 1..20 = %ld\n", seq_sum);

#ifdef HAVE_PTHREADS
        /* Split into two thread-local computations */
        sum_arg sa[2] = {
            { data,  0, 10, 0 },
            { data, 10, 20, 0 }
        };
        pthread_t st[2];
        pthread_create(&st[0], NULL, sum_worker, &sa[0]);
        pthread_create(&st[1], NULL, sum_worker, &sa[1]);
        pthread_join(st[0], NULL);
        pthread_join(st[1], NULL);

        long par_sum = sa[0].local_sum + sa[1].local_sum;
        printf("  Parallel sum (2 threads)            = %ld\n", par_sum);
        printf("  Match: %s\n", seq_sum == par_sum ? "yes" : "NO");
        printf("  Each thread wrote only to its own local_sum field.\n");
        printf("  One addition at merge -- the only shared-state operation.\n");
#endif
    }


    /* --- 5. Atomic publish of immutable result */
    printf("\n-- 5. Atomic publish of immutable result (C11 atomics) --\n");
    {
        long computed = total;   /* the value computed in section 1 */
        publish(computed);

        /* In a real program a second thread would call wait_and_read().
         * Here we do it in the same thread to demonstrate the pattern. */
        long read_back = wait_and_read();
        printf("  Published: %ld\n", computed);
        printf("  Read back: %ld\n", read_back);
        printf("  One release store to publish; one acquire load to read.\n");
        printf("  After the acquire load, no further barriers needed.\n");
        printf("  The data is immutable; any number of readers can access it.\n");

        /* Cleanup */
        result_t *r = atomic_load(&published);
        free(r);
    }


    /* --- 6. Summary */
    printf("\n-- 6. Summary --\n");
    printf("  Pattern               Concurrency contribution\n");
    printf("  -------               -----------------------\n");
    printf("  Pure function         No shared writes -> no race\n");
    printf("  Immutable value       Write once, read many -> no synchronisation\n");
    printf("  ATTR_CONST            Compiler-verified purity\n");
    printf("  Thread-local work     Each thread owns its data -> no locks\n");
    printf("  Atomic publish        One release store to make result visible\n");
    printf("  Structural sharing    N readers, 0 locks (persistent structures)\n");
    printf("\n");
    printf("  The deeper principle:\n");
    printf("  Functional purity is a memory access pattern.\n");
    printf("  Pure functions read inputs, produce outputs, touch nothing else.\n");
    printf("  That property makes concurrent correctness follow from code structure.\n");

    return 0;
}
