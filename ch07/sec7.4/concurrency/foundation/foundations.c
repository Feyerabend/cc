/*
 * foundations.c
 *
 * Four pillars that underpin actor systems (like Akka)
 *
 *   1. THREADS          — structural basis for parallelism
 *   2. RE-ENTRANT FNs   — modular safety (no hidden shared state)
 *   3. CONTEXT SWITCHES — cooperative multitasking via a tiny scheduler
 *   4. MEMORY BARRIERS  — consistency when threads share memory
 *
 * Portable: C11 + POSIX threads. No platform-specific headers.
 * Build:  gcc -std=c11 -Wall -pthread -o foundations foundations.c
 * Run:    ./foundations
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <stdatomic.h>   /* C11 atomics — memory barriers live here */

/* 
   PILLAR 1 — THREADS
   Threads give each actor its own execution path.
   Without threads, actors would have to take turns on a single CPU.
   Here: two threads race to increment a counter. */

#define THREAD_ITERS 100000

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
long shared_counter   = 0;   /* guarded by mutex */
long unsafe_counter   = 0;   /* NOT guarded — to show the race */

void *thread_worker(void *arg) {
    int id = *(int *)arg;
    for (int i = 0; i < THREAD_ITERS; i++) {
        /* Safe path: lock before touching shared state */
        pthread_mutex_lock(&mutex);
        shared_counter++;
        pthread_mutex_unlock(&mutex);

        /* Unsafe path: no lock — data race! */
        unsafe_counter++;   /* read-modify-write is NOT atomic */
    }
    printf("  Thread %d done.\n", id);
    return NULL;
}

void demo_threads(void) {
    puts("\n  PILLAR 1. THREADS");
    puts("  Two threads each increment counters 100 000 times.");
    puts("  One counter is mutex-guarded, the other is naked.\n");

    pthread_t t1, t2;
    int id1 = 1, id2 = 2;
    pthread_create(&t1, NULL, thread_worker, &id1);
    pthread_create(&t2, NULL, thread_worker, &id2);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);

    long expected = 2L * THREAD_ITERS;
    printf("  Expected            : %ld\n", expected);
    printf("  Mutex-guarded value : %ld  %s\n",
           shared_counter, shared_counter == expected ? "(+) correct" : "(-) wrong");
    printf("  Unguarded value     : %ld  %s\n",
           unsafe_counter,
           unsafe_counter == expected ? "(got lucky)" : "(-) RACE — lost updates!");
    puts("\n  > Actor systems give each actor its own thread (or a thread-pool");
    puts("    slot) so work truly runs in parallel, like these two threads.");
}

/* PILLAR 2 — RE-ENTRANT FUNCTIONS
   A re-entrant function is safe to call from multiple threads
   simultaneously because it relies ONLY on its arguments and local
   (stack) variables — no static/global state.

   Contrast:
     strtok()       — NOT re-entrant (hides a static pointer inside)
     strtok_r()     — re-entrant (caller supplies the state)

   In actor systems, behavior functions must be re-entrant so many
   actors can invoke the same logic concurrently without corrupting
   each other. */

/* ── BAD: uses a static local — the saved position leaks between calls ── */
char *tokenize_unsafe(char *s, const char *delim) {
    static char *saved;          /* ← shared between ALL callers */
    return strtok_r(s, delim, &saved);
    /* (using strtok_r internally to avoid UB, but 'saved' is still static) */
}

/* ── GOOD: caller owns the state, stored on THEIR stack ── */
char *tokenize_safe(char *s, const char *delim, char **saved) {
    return strtok_r(s, delim, saved);  /* no hidden state */
}

typedef struct { int id; char sentence[64]; } TokenArg;

void *tokenize_thread(void *arg) {
    TokenArg *ta = (TokenArg *)arg;
    char buf[64];
    strncpy(buf, ta->sentence, sizeof(buf) - 1);

    char *saved = NULL;                         /* lives on THIS thread's stack */
    char *tok   = tokenize_safe(buf, " ", &saved);
    printf("  Thread %d tokens:", ta->id);
    while (tok) {
        printf(" [%s]", tok);
        tok = tokenize_safe(NULL, " ", &saved);
    }
    putchar('\n');
    return NULL;
}

void demo_reentrant(void) {
    puts("\n  PILLAR 2. RE-ENTRANT FUNCTIONS");
    puts("  Two threads tokenize different sentences simultaneously.");
    puts("  Each carries its own 'saved' pointer on its stack.\n");

    pthread_t t1, t2;
    TokenArg a1 = {1, "the quick brown fox"};
    TokenArg a2 = {2, "jumps over lazy dog"};
    pthread_create(&t1, NULL, tokenize_thread, &a1);
    pthread_create(&t2, NULL, tokenize_thread, &a2);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);

    puts("\n  > Actor behavior functions must be re-entrant: no global");
    puts("    mutable state, only arguments + local variables.");
    puts("    That's why Akka actors hold state *inside* the actor object,");
    puts("    not in static variables.");
}

/* PILLAR 3 — CONTEXT SWITCHES
   A context switch saves one task's CPU registers and resumes
   another — the OS does this between threads.  Actor frameworks
   multiplex many actors onto few OS threads: when an actor yields
   (waiting for a message), the thread picks up the next ready actor.

   We illustrate the mechanics using POSIX semaphores: each "actor"
   thread blocks on its own semaphore (= parked / context saved).
   A round-robin scheduler posts them one at a time (= context
   restored), exactly mirroring how a green-thread dispatcher works.

   This is fully portable C11 + POSIX, no platform-specific headers. */

/* A minimal "gate": one thread waits, another signals it.
   Built from pthread_cond_t + mutex — available everywhere. */
typedef struct {
    pthread_mutex_t mtx;
    pthread_cond_t  cond;
    int             flag;   /* 0 = closed, 1 = open */
} Gate;

static void gate_init(Gate *g) {
    pthread_mutex_init(&g->mtx,  NULL);
    pthread_cond_init (&g->cond, NULL);
    g->flag = 0;
}
static void gate_wait(Gate *g) {        /* block until signalled */
    pthread_mutex_lock(&g->mtx);
    while (!g->flag) pthread_cond_wait(&g->cond, &g->mtx);
    g->flag = 0;
    pthread_mutex_unlock(&g->mtx);
}
static void gate_signal(Gate *g) {     /* wake the waiting thread */
    pthread_mutex_lock(&g->mtx);
    g->flag = 1;
    pthread_cond_signal(&g->cond);
    pthread_mutex_unlock(&g->mtx);
}
static void gate_destroy(Gate *g) {
    pthread_cond_destroy (&g->cond);
    pthread_mutex_destroy(&g->mtx);
}

#define CS_TASKS  3
#define CS_STEPS  3

typedef struct {
    int  id;
    Gate run;        /* scheduler signals this to resume the actor */
    Gate done_step;  /* actor signals this after each step */
} CSTask;

static CSTask cs_tasks[CS_TASKS];

void *cs_actor(void *arg) {
    CSTask *t = (CSTask *)arg;
    for (int s = 1; s <= CS_STEPS; s++) {
        gate_wait  (&t->run);                       /* park — wait to be scheduled */
        printf("  Actor %d  — step %d/%d\n", t->id, s, CS_STEPS);
        gate_signal(&t->done_step);                 /* yield back to scheduler */
    }
    return NULL;
}

void demo_context_switch(void) {
    puts("\n  PILLAR 3. CONTEXT SWITCHES");
    puts("  3 actor threads, each parked on a cond-var (= context saved).");
    puts("  Scheduler signals one at a time — round-robin interleaving.");
    puts("  gate_wait / gate_signal mirror 'save context / restore context'.\n");

    pthread_t threads[CS_TASKS];
    for (int i = 0; i < CS_TASKS; i++) {
        cs_tasks[i].id = i;
        gate_init(&cs_tasks[i].run);
        gate_init(&cs_tasks[i].done_step);
        pthread_create(&threads[i], NULL, cs_actor, &cs_tasks[i]);
    }

    /* Round-robin: signal each actor in turn, wait for it to yield */
    for (int step = 0; step < CS_STEPS; step++) {
        for (int i = 0; i < CS_TASKS; i++) {
            gate_signal(&cs_tasks[i].run);       /* <-- resume actor i */
            gate_wait  (&cs_tasks[i].done_step); /* <-- wait for yield */
        }
    }

    for (int i = 0; i < CS_TASKS; i++) {
        pthread_join(threads[i], NULL);
        gate_destroy(&cs_tasks[i].run);
        gate_destroy(&cs_tasks[i].done_step);
    }

    puts("\n  > Akka's thread-pool executor does exactly this at scale:");
    puts("    thousands of actors share tens of OS threads via fast");
    puts("    context switches — no actor blocks the thread while waiting.");
}

/* 
   PILLAR 4 — MEMORY BARRIERS
   CPUs and compilers reorder instructions for speed.  Without a
   barrier, Thread A's write may not be visible to Thread B in time.

   C11 atomics give us explicit control:
     memory_order_relaxed  — no ordering guarantee, just atomicity
     memory_order_release  — "publish": all prior writes visible BEFORE this store
     memory_order_acquire  — "subscribe": all subsequent reads see prior release

   Classic pattern: a flag that signals "data is ready". */

typedef struct {
    int            payload;          /* the data being transferred */
    atomic_int     ready;            /* the barrier flag */
} SharedSlot;

void *barrier_producer(void *arg) {
    SharedSlot *slot = (SharedSlot *)arg;
    slot->payload = 42;              /* write data first */
    /* release barrier: payload write is visible BEFORE ready=1 */
    atomic_store_explicit(&slot->ready, 1, memory_order_release);
    printf("  Producer: wrote payload=42, set ready=1 (release barrier)\n");
    return NULL;
}

void *barrier_consumer(void *arg) {
    SharedSlot *slot = (SharedSlot *)arg;
    /* acquire barrier: spin until flag seen, then payload is safe to read */
    while (atomic_load_explicit(&slot->ready, memory_order_acquire) == 0)
        ; /* busy-wait (fine for illustration) */
    printf("  Consumer: saw ready=1 (acquire barrier), payload=%d  ok\n", slot->payload);
    return NULL;
}

void demo_memory_barrier(void) {
    puts("\n  PILLAR 4. MEMORY BARRIERS");
    puts("  Producer writes data then sets a release flag.");
    puts("  Consumer spins on an acquire load — guaranteed to see");
    puts("  the payload once the flag is observed.\n");

    SharedSlot slot = { .payload = 0, .ready = 0 };
    pthread_t prod, cons;
    pthread_create(&cons, NULL, barrier_consumer, &slot);
    pthread_create(&prod, NULL, barrier_producer, &slot);
    pthread_join(prod, NULL);
    pthread_join(cons, NULL);

    puts("\n  > When an Akka actor sends a message, the framework inserts");
    puts("    a happens-before edge (a memory barrier) so the receiving");
    puts("    actor sees the sender's state consistently — same idea.");
}


int main(void) {
    puts("FOUNDATIONS UNDERLYING ACTOR SYSTEMS");

    demo_threads();
    demo_reentrant();
    demo_context_switch();
    demo_memory_barrier();

    puts("\n");
    puts("  Together these four primitives let actor frameworks like");
    puts("  Akka give you: true parallelism, safe concurrent logic,");
    puts("  efficient scheduling, and consistent shared-nothing memory.");
    puts("\n");
    return 0;
}

// gcc -std=c11 -Wall -Wextra -pthread -o foundations foundations.c
