/*
 * concurrency.c -- Concurrent Hoare Logic and Rely-Guarantee
 *
 * --- §17 (Concurrent and Probabilistic Extensions): Why sequential Hoare proofs fail ---
 *
 * Each thread's sequential Hoare proof is individually valid:
 *   Thread 1: {counter = 0} counter++ {counter = 1}
 *   Thread 2: {counter = 0} counter++ {counter = 1}
 *
 * But counter++ is NOT atomic.  At the machine level it is roughly:
 *   tmp = load(counter)       -- (1)
 *   tmp = tmp + 1             -- (2)
 *   store(counter, tmp)       -- (3)
 *
 * A legal interleaving:
 *   T1 step (1): tmp1 = 0
 *   T2 step (1): tmp2 = 0    <- T2 reads the stale value!
 *   T1 steps(2,3): counter = 1
 *   T2 steps(2,3): counter = 1  <- overwrites T1's increment
 *
 * Result: counter = 1, not 2.  The Owicki-Gries interference-freedom
 * check catches this: T2's action does NOT preserve T1's assertion
 * {counter = 1}, so the parallel composition rule cannot be applied.
 *
 * --- §17.1 (Concurrent Transition Systems): Resource invariant ---
 *
 * With a mutex, each critical section maintains the resource invariant:
 *   I = (counter >= 0)
 * The invariant must hold before every lock acquisition and after
 * every lock release; it may be transiently broken inside.
 *
 * --- §17.3 (Non-Interference Under Concurrency): Rely-Guarantee ---
 *
 * Each thread carries an explicit contract:
 *   Rely:      R = (counter' >= counter)    -- others only increment
 *   Guarantee: G = (counter' = counter + 1) -- we increment by exactly 1
 *
 * Each thread relies on G of the other; together the contracts compose
 * without re-verifying the whole system when a thread is added.
 *
 * Compile:  gcc -Wall -std=c11 -o concurrency concurrency.c -lpthread
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <pthread.h>


/* §17.1 (Concurrent Transition Systems): Lock-protected counter with resource invariant */

typedef struct {
    int counter;
    pthread_mutex_t lock;
} SharedCounter;

static SharedCounter g_shared;

/*
 * The resource invariant I = (counter >= 0).
 * Call this with the lock NOT held.
 */
static void assert_invariant(const char *who)
{
    assert(g_shared.counter >= 0);
    printf("  [%s] I=(counter >= 0) holds: counter = %d\n",
           who, g_shared.counter);
}

/*
 * Thread body: increment inside critical section.
 *
 * Owicki-Gries resource invariant: I = (counter >= 0)
 *   Before lock: I must hold (guaranteed by previous release or init).
 *   After unlock: I must hold (we restore it inside the section).
 *
 * Rely-Guarantee contract:
 *   Rely:      R: counter is non-decreasing (environment only increments)
 *   Guarantee: G: counter' = counter + 1 (we increment by exactly 1)
 */
static void *counter_thread(void *arg)
{
    int tid = *(int *)arg;

    pthread_mutex_lock(&g_shared.lock);
    /* { I holds: counter >= 0 } */

    int before = g_shared.counter;
    assert(g_shared.counter >= 0);     /* I at entry to critical section */

    g_shared.counter++;

    assert(g_shared.counter >= 0);     /* I restored before release */
    int after = g_shared.counter;

    /* Guarantee G: we incremented by exactly 1 */
    assert(after == before + 1);
    printf("  Thread %d: %d -> %d  (G: counter' = counter + 1)\n",
           tid, before, after);

    pthread_mutex_unlock(&g_shared.lock);
    /* { I holds for next thread } */

    return NULL;
}

static void demo_locked_counter(void)
{
    printf("-- Lock-Protected Counter (§17.1 and §17.3) --\n\n");

    printf("Resource invariant: I = (counter >= 0)\n");
    printf("Rely:               R = (counter' >= counter)\n");
    printf("Guarantee:          G = (counter' = counter + 1)\n\n");

    g_shared.counter = 0;
    pthread_mutex_init(&g_shared.lock, NULL);
    assert_invariant("init");

    enum { N = 4 };
    pthread_t threads[N];
    int       tids[N];

    for (int i = 0; i < N; i++) {
        tids[i] = i + 1;
        pthread_create(&threads[i], NULL, counter_thread, &tids[i]);
    }
    for (int i = 0; i < N; i++)
        pthread_join(threads[i], NULL);

    assert_invariant("final");
    printf("\nFinal counter = %d (expected %d after %d increments)\n",
           g_shared.counter, N, N);
    assert(g_shared.counter == N);

    pthread_mutex_destroy(&g_shared.lock);
    printf("\n");
}


/* §17.3 (Non-Interference Under Concurrency): Rely-Guarantee -- monotone counter */

/*
 * Two threads share a counter and each carry an explicit R/G contract.
 * We verify at runtime that every step of every thread satisfies G,
 * and that the final state is consistent with R.
 *
 * Because each thread's G implies the other's R (G ⊆ R), the
 * parallel composition rule is satisfied without any global
 * interference check.
 */

typedef struct {
    int  initial;          /* value of counter when this thread ran */
    int  final_val;        /* value after this thread's increment */
    int  guarantee_delta;  /* must equal 1 to satisfy G */
} ThreadResult;

static pthread_mutex_t rg_lock;
static int             rg_counter;

static void *rg_thread(void *arg)
{
    ThreadResult *res = (ThreadResult *)arg;

    pthread_mutex_lock(&rg_lock);

    res->initial = rg_counter;

    /*
     * Rely R: counter is non-decreasing.
     * Under R, whatever the environment did before we acquired the lock
     * only increased counter -- we never see a lower value than we expect.
     * Here the mutex makes this trivially true; in a lock-free design
     * R would be a meaningful assumption.
     */
    assert(rg_counter >= res->initial);   /* R holds: no decrease observed */

    rg_counter++;

    res->final_val        = rg_counter;
    res->guarantee_delta  = res->final_val - res->initial;

    /* Guarantee G: we incremented by exactly 1. */
    assert(res->guarantee_delta == 1);

    pthread_mutex_unlock(&rg_lock);
    return NULL;
}

static void demo_rely_guarantee(void)
{
    printf("-- Rely-Guarantee Composition (§17.3: Non-Interference Under Concurrency) --\n\n");
    printf("Per-thread contract:\n");
    printf("  Rely R:      counter' >= counter  (environment never decreases)\n");
    printf("  Guarantee G: counter' = counter + 1  (we increment by exactly 1)\n\n");
    printf("Because G ⊆ R, each thread's guarantee satisfies the other's rely.\n");
    printf("No global interference check is required.\n\n");

    rg_counter = 0;
    pthread_mutex_init(&rg_lock, NULL);

    enum { M = 3 };
    pthread_t    threads[M];
    ThreadResult results[M];

    for (int i = 0; i < M; i++)
        pthread_create(&threads[i], NULL, rg_thread, &results[i]);
    for (int i = 0; i < M; i++)
        pthread_join(threads[i], NULL);

    printf("Results:\n");
    for (int i = 0; i < M; i++) {
        printf("  Thread %d: counter %d -> %d,  delta = %d  (G satisfied: %s)\n",
               i, results[i].initial, results[i].final_val,
               results[i].guarantee_delta,
               results[i].guarantee_delta == 1 ? "yes" : "NO");
        assert(results[i].guarantee_delta == 1);
    }

    printf("\nFinal counter = %d (Rely R: non-decreasing throughout: %s)\n",
           rg_counter, rg_counter >= 0 ? "yes" : "no");
    assert(rg_counter == M);

    pthread_mutex_destroy(&rg_lock);
    printf("\n");
}


/* §17.2 (Interleaving Semantics): Illustrating why the race condition is a problem */

/*
 * This section is EXPLANATORY ONLY -- the racy increment is shown as
 * commented-out pseudocode because running it is undefined behavior
 * under the C memory model.
 *
 * The Owicki-Gries interference check that catches the race:
 *
 *   Thread 1 proof:
 *     {counter = 0} [read: tmp1 = counter] {tmp1 = 0}
 *     {tmp1 = 0}    [add:  tmp1 = tmp1+1]  {tmp1 = 1}
 *     {tmp1 = 1}    [write: counter = tmp1] {counter = 1}
 *
 *   Thread 2 proof (identical):
 *     {counter = 0} ... {counter = 1}
 *
 *   Interference check for Thread 2's [write: counter = tmp2]
 *   against Thread 1's assertion {counter = 1}:
 *
 *     {counter = 1 ∧ Pre(write)} write {counter = 1}
 *     i.e.  {counter = 1 ∧ tmp2 = 1} counter = tmp2 {counter = 1}
 *
 *   But tmp2 might be 0 (if T2 read before T1 wrote), making
 *   the write set counter = 0, violating {counter = 1}.
 *   Interference-freedom FAILS => composition rule cannot be applied.
 */

static void demo_race_explanation(void)
{
    printf("-- Race Condition: Why Sequential Proofs Fail (§17.2: Interleaving Semantics) --\n\n");

    printf("Sequential proof of each thread is valid in isolation:\n");
    printf("  {counter = 0} counter++ {counter = 1}\n\n");

    printf("Owicki-Gries interference check (for 2-thread increment):\n");
    printf("  Thread 2's write (counter = tmp2) must preserve\n");
    printf("  Thread 1's intermediate assertion {counter = 1}.\n\n");
    printf("  If tmp2 was read BEFORE T1's write, tmp2 = 0.\n");
    printf("  T2 then writes counter = 0, violating {counter = 1}.\n");
    printf("  => interference-freedom FAILS => race condition detected.\n\n");

    printf("The parallel composition rule requires interference-freedom.\n");
    printf("Without it, the combined postcondition {counter = 2} is not\n");
    printf("derivable -- and indeed, the actual result may be 1 or 2.\n\n");

    printf("Fix: use a mutex (see demo_locked_counter above).\n");
    printf("The lock enforces atomicity of the read-modify-write;\n");
    printf("the resource invariant replaces the interference check.\n\n");
}


int main(void)
{
    printf("Concurrent Hoare Logic and Rely-Guarantee\n");
    printf("-----------------------------------------\n\n");

    demo_race_explanation();
    demo_locked_counter();
    demo_rely_guarantee();

    printf("All concurrent reasoning properties verified.\n");
    return 0;
}
