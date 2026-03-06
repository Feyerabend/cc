/*
 * persistent.c
 * Functional Patterns -- 10. Persistent Data Structures
 *
 * Implements a persistent singly-linked list in C using reference counting
 * to manage the lifetime of shared nodes.
 *
 * Sections:
 *   1. Node type with refcount; retain / release.
 *   2. cons / head / tail -- the list API.
 *   3. Structural sharing demo: three lists, one shared tail.
 *   4. Persistent stack: push / pop / peek.
 *   5. Refcount trace: watching counts change as versions are created/dropped.
 *   6. Thread-safe refcounts with C11 _Atomic.
 *   7. Copy-on-write string (simpler COW pattern).
 *   8. Lock-free read sharing: multiple readers, one shared list.
 *
 * Build (single-threaded):
 *   cc -Wall -O2 -o persistent persistent.c
 *
 * Build (with pthreads + atomics):
 *   cc -Wall -O2 -pthread -DHAVE_PTHREADS -o persistent persistent.c
 *
 * Run:  ./persistent
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdatomic.h>

/* 
 * 1. Node type
 *
 * refcount tracks how many list handles point (directly or indirectly)
 * to this node.  When refcount reaches 0, the node is freed.
 */
typedef struct node {
    int              value;
    struct node     *next;
    atomic_int       refcount;   /* C11 atomic for thread safety */
} node_t;

static node_t *node_retain(node_t *n) {
    if (n) atomic_fetch_add(&n->refcount, 1);
    return n;
}

static void node_release(node_t *n) {
    if (!n) return;
    /* atomic_fetch_sub returns the OLD value */
    if (atomic_fetch_sub(&n->refcount, 1) == 1) {
        /* We just decremented to 0 -- we are the sole remaining owner */
        node_release(n->next);   /* release tail first (may chain) */
        free(n);
    }
}

static node_t *node_new(int value, node_t *next) {
    node_t *n     = malloc(sizeof(node_t));
    n->value      = value;
    n->next       = next;               /* steal: caller must have retained if needed */
    atomic_init(&n->refcount, 1);       /* starts with one owner (the caller) */
    return n;
}


/* 
 * 2. Persistent list API
 *
 * A list is just a pointer to a node (or NULL for the empty list).
 * Each "list variable" contributes one refcount unit to the node it points to.
 */
typedef node_t *list_t;

#define LIST_EMPTY NULL

/* cons: prepend value to lst.  lst's refcount is incremented by node_new. */
static list_t cons(int value, list_t lst) {
    return node_new(value, lst);
}

static int  head(list_t lst)  { return lst->value; }
static list_t tail(list_t lst) { return lst->next; }

/* drop: decrement refcount on lst (and transitively when count hits 0) */
static void list_drop(list_t lst) {
    node_release(lst);
}

/* retain: another handle to the same list */
static list_t list_retain(list_t lst) {
    return node_retain(lst);
}

/* print */
static void list_print(const char *label, list_t lst) {
    printf("  %-20s [", label);
    for (node_t *n = lst; n; n = n->next)
        printf("%d%s", n->value, n->next ? " -> " : "");
    printf("]\n");
}

/* sum */
static long list_sum(list_t lst) {
    long s = 0;
    for (node_t *p = lst; p; p = p->next) s += p->value;
    return s;
}


/* 
 * 3. Structural sharing demo
 */
// hm

/* 
 * 4. Persistent stack
 */
/* stack_push borrows s -- retains it so s remains valid after the call */
static list_t stack_push(list_t s, int v) { return cons(v, list_retain(s)); }
static list_t stack_pop(list_t s) {
    list_t new_top = list_retain(tail(s));   /* new handle to the tail */
    list_drop(s);                            /* release the old top */
    return new_top;
}
static int stack_peek(list_t s) { return head(s); }


/* 
 * 5. Refcount trace
 *
 * Print the refcount of the first node of a list.
 */
static int refcount_of(list_t lst) {
    return lst ? (int)atomic_load(&lst->refcount) : 0;
}


/* 
 * 6. Thread-safe section -- already handled: we use atomic_int throughout.
 * The lock-free read sharing demo uses pthreads.
 */
#ifdef HAVE_PTHREADS
#include <pthread.h>

typedef struct {
    list_t shared_list;
    long   expected_sum;
    long   computed_sum;
    int    id;
} reader_arg;

static void *read_list(void *arg) {
    reader_arg *r = (reader_arg *)arg;
    /* No lock: shared_list is never mutated after creation */
    r->computed_sum = list_sum(r->shared_list);
    return NULL;
}
#endif


/* 
 * 7. Copy-on-write string
 *
 * A simpler demonstration of the COW pattern:
 * a string struct starts with refcount > 1 (shared).
 * A "write" triggers a private copy first.
 */
typedef struct {
    char      *data;
    size_t     len;
    atomic_int refcount;
} cow_str;

static cow_str *cow_new(const char *s) {
    cow_str *cs = malloc(sizeof(cow_str));
    cs->len     = strlen(s);
    cs->data    = malloc(cs->len + 1);
    memcpy(cs->data, s, cs->len + 1);
    atomic_init(&cs->refcount, 1);
    return cs;
}

static cow_str *cow_retain(cow_str *cs) {
    atomic_fetch_add(&cs->refcount, 1);
    return cs;
}

static void cow_release(cow_str *cs) {
    if (atomic_fetch_sub(&cs->refcount, 1) == 1) {
        free(cs->data);
        free(cs);
    }
}

/* If shared (refcount > 1), make a private copy before modifying */
static cow_str *cow_make_unique(cow_str *cs) {
    if (atomic_load(&cs->refcount) == 1) return cs;  /* already unique */
    cow_str *copy = cow_new(cs->data);
    cow_release(cs);
    return copy;
}

static cow_str *cow_append(cow_str *cs, char ch) {
    cs = cow_make_unique(cs);       /* copy-on-write */
    cs->data = realloc(cs->data, cs->len + 2);
    cs->data[cs->len]     = ch;
    cs->data[cs->len + 1] = '\0';
    cs->len++;
    return cs;
}



int main(void) {
    /* --- 1. Build and share a base list */
    printf("-- 1+2. Structural sharing --\n");
    {
        /* list_a = [1, 2, 3] */
        list_t list_a = cons(1, cons(2, cons(3, LIST_EMPTY)));

        /* list_b and list_c share list_a as their tail */
        list_t list_b = cons(0, list_retain(list_a));
        list_t list_c = cons(9, list_retain(list_a));

        list_print("list_a:", list_a);
        list_print("list_b:", list_b);
        list_print("list_c:", list_c);

        /* The first node of list_a has refcount 3:
           list_a itself + tail(list_b) + tail(list_c) */
        printf("  refcount of list_a head: %d  (pointed to by a, b, c)\n",
               refcount_of(list_a));

        /* Drop list_b -- refcount of list_a head drops to 2 */
        list_drop(list_b);
        printf("  after drop(list_b): refcount of list_a head: %d\n",
               refcount_of(list_a));

        list_drop(list_c);
        printf("  after drop(list_c): refcount of list_a head: %d\n",
               refcount_of(list_a));

        list_drop(list_a);
        printf("  after drop(list_a): all nodes freed\n");
    }

    /* --- 3. Refcount trace during push/pop */
    printf("\n-- 3. Persistent stack (push / pop) --\n");
    {
        list_t s0 = LIST_EMPTY;
        list_t s1 = stack_push(s0, 'a');
        list_t s2 = stack_push(s1, 'b');
        list_t s3 = stack_push(s2, 'c');

        printf("  peek(s3) = '%c'\n", (char)stack_peek(s3));
        printf("  refcount of 'b' node (shared by s2 and tail(s3)): %d\n",
               refcount_of(tail(s3)));

        list_t s2_via_pop = stack_pop(s3);   /* s3 released, tail retained */
        printf("  after pop(s3), peek(s2_via_pop) = '%c'\n",
               (char)stack_peek(s2_via_pop));
        printf("  s2 still valid: peek(s2) = '%c'\n", (char)stack_peek(s2));

        list_drop(s2_via_pop);
        list_drop(s2);
        list_drop(s1);
        printf("  all stack versions dropped; nodes freed\n");
    }

    /* --- 4. Copy-on-write string */
    printf("\n-- 4. Copy-on-write string --\n");
    {
        cow_str *s1 = cow_new("hello");
        cow_str *s2 = cow_retain(s1);   /* s2 shares s1's buffer */

        printf("  s1 = \"%s\", s2 = \"%s\"  (shared, refcount=%d)\n",
               s1->data, s2->data, (int)atomic_load(&s1->refcount));

        /* Append to s2: triggers private copy */
        s2 = cow_append(s2, '!');

        printf("  after s2 append '!':\n");
        printf("    s1 = \"%s\"  (unchanged)\n", s1->data);
        printf("    s2 = \"%s\"  (private copy)\n", s2->data);
        printf("    s1 refcount = %d  (no longer shared)\n",
               (int)atomic_load(&s1->refcount));

        cow_release(s1);
        cow_release(s2);
    }

    /* --- 5. Lock-free read sharing (pthreads) */
    printf("\n-- 5. Lock-free read sharing --\n");
#ifdef HAVE_PTHREADS
    {
        /* Build a shared list [1..100] */
        list_t shared = LIST_EMPTY;
        for (int v = 100; v >= 1; v--)
            shared = cons(v, shared);

        long expected = 5050L;   /* 1+2+...+100 */

        /* Retain once per reader thread (6 threads + the main reference) */
        int num_readers = 6;
        reader_arg args[6];
        pthread_t  threads[6];

        for (int i = 0; i < num_readers; i++) {
            args[i].shared_list  = list_retain(shared);
            args[i].expected_sum = expected;
            args[i].id           = i;
            pthread_create(&threads[i], NULL, read_list, &args[i]);
        }
        for (int i = 0; i < num_readers; i++) {
            pthread_join(threads[i], NULL);
            list_drop(args[i].shared_list);   /* release reader's reference */
        }

        int all_ok = 1;
        for (int i = 0; i < num_readers; i++)
            if (args[i].computed_sum != expected) all_ok = 0;

        printf("  %d threads read shared list simultaneously\n", num_readers);
        printf("  Expected sum: %ld\n", expected);
        printf("  All correct:  %s\n", all_ok ? "yes" : "no");
        printf("  No mutex used during reads -- immutability is the lock.\n");

        list_drop(shared);   /* release main reference; all nodes freed */
    }
#else
    printf("  (build with -DHAVE_PTHREADS -pthread to enable this section)\n");
    printf("  Principle: shared persistent list is read-only after creation.\n");
    printf("  N readers, 0 locks: safe because no writer exists.\n");
#endif

    /* --- Key observations */
    printf("\n-- Key observations --\n");
    printf("  cons(v, lst) = one malloc; steals lst (caller retains if needed).\n");
    printf("  drop(lst)    = one decrement; free only when count reaches 0.\n");
    printf("  Shared nodes freed automatically when last reference is dropped.\n");
    printf("  atomic_int refcount: thread-safe without a mutex.\n");
    printf("  COW: copy only when a write is needed on a shared buffer.\n");
    printf("  Immutable shared list: N readers, 0 synchronisation points.\n");

    return 0;
}
