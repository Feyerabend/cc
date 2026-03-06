/*
 * lazy.c
 * Functional Patterns -- 6. Lazy Evaluation and Generators
 *
 * Implements the generator pattern in C as explicit state machines.
 * Each "generator" is a struct (the frame) plus a next() function.
 *
 * PROTOCOL (consistent throughout):
 *   _init(&g, ...)   -- set up the frame; done=0.
 *   _next(&g)        -- compute the next value into g.value,
 *                       or set g.done=1 if exhausted.
 *   Loop:
 *       _init(&g);
 *       _next(&g);          // prime: get first value
 *       while (!g.done) {
 *           use(g.value);
 *           _next(&g);
 *       }
 *
 * Sections:
 *   1. Counter generator      -- single state, infinite.
 *   2. Range generator        -- finite, with termination.
 *   3. Fibonacci generator    -- two-variable frame.
 *   4. Filter wrapper         -- wraps fib_gen, skips non-matching values.
 *   5. Map wrapper            -- transforms values from filter.
 *   6. take()                 -- consume N steps from any generator
 *                               via a function-pointer interface.
 *   7. Multi-yield state machine -- explicit pc field.
 *   8. Eager vs. lazy cost comparison.
 *
 * Build:  cc -Wall -o lazy lazy.c
 * Run:    ./lazy
 */

#include <stdio.h>
#include <stdlib.h>

/* 
 * 1. Counter generator -- infinite
 *
 * Python equivalent:
 *   def count_up():
 *       i = 0
 *       while True:
 *           yield i
 *           i += 1
 */
typedef struct {
    long value;
    int  done;
    long i;        /* frame: the loop variable */
} counter_gen;

static void counter_init(counter_gen *g) {
    g->i = 0; g->done = 0;
}

static void counter_next(counter_gen *g) {
    /* Infinite: never sets done. */
    g->value = g->i++;
}


/* 
 * 2. Range generator -- finite
 *
 * Python equivalent:
 *   def range_gen(start, stop, step):
 *       i = start
 *       while i < stop:
 *           yield i
 *           i += step
 */
typedef struct {
    long value;
    int  done;
    long i, stop, step;
} range_gen;

static void range_init(range_gen *g, long start, long stop, long step) {
    g->i = start; g->stop = stop; g->step = step; g->done = 0;
}

static void range_next(range_gen *g) {
    if (g->i >= g->stop) { g->done = 1; return; }
    g->value  = g->i;
    g->i     += g->step;
}


/* 
 * 3. Fibonacci generator -- infinite
 *
 * Python equivalent:
 *   def fibonacci():
 *       a, b = 0, 1
 *       while True:
 *           yield a
 *           a, b = b, a + b
 */
typedef struct {
    long value;
    int  done;
    long a, b;
} fib_gen;

static void fib_init(fib_gen *g)  { g->a = 0; g->b = 1; g->done = 0; }

static void fib_next(fib_gen *g) {
    long tmp;
    g->value = g->a;
    tmp      = g->a + g->b;
    g->a     = g->b;
    g->b     = tmp;
}


/* 
 * 4. Filter wrapper over fib_gen
 *
 * Python equivalent:
 *   def even_fibs(source):
 *       for x in source:
 *           if x % 2 == 0:
 *               yield x
 *
 * Holds a pointer to the source; pulls and tests until a match is found.
 */
typedef struct {
    long     value;
    int      done;
    fib_gen *src;
} even_fib_gen;

static void even_fib_init(even_fib_gen *g, fib_gen *src) {
    g->src  = src;
    g->done = 0;
}

static void even_fib_next(even_fib_gen *g) {
    /* Pull from fib source until we find an even value.
     * (fib is infinite so src->done is never set.) */
    while (1) {
        fib_next(g->src);
        if (g->src->value % 2 == 0) {
            g->value = g->src->value;
            return;
        }
    }
}


/* 
 * 5. Map wrapper over even_fib_gen
 *
 * Python equivalent:
 *   def squares(source):
 *       for x in source:
 *           yield x * x
 */
typedef struct {
    long          value;
    int           done;
    even_fib_gen *src;
} sq_even_fib_gen;

static void sq_even_fib_init(sq_even_fib_gen *g, even_fib_gen *src) {
    g->src = src; g->done = 0;
}

static void sq_even_fib_next(sq_even_fib_gen *g) {
    even_fib_next(g->src);
    g->value = g->src->value * g->src->value;
}


/* 
 * 6. take() via a function-pointer interface
 *
 * To call take() with different generator types we pass:
 *   state   -- pointer to the concrete generator struct
 *   advance -- its _next function cast to a generic signature
 *   value   -- pointer to the struct's value field
 *   done    -- pointer to the struct's done field
 */
typedef void (*advance_fn)(void *state);

static void take(void *state, advance_fn advance, long *value_ptr, int *done_ptr, int n, long *out) {
    for (int i = 0; i < n && !(*done_ptr); i++) {
        advance(state);
        if (*done_ptr) break;
        out[i] = *value_ptr;
    }
}


/* 
 * 7. Multi-yield state machine -- explicit program counter
 *
 * Python equivalent:
 *   def multi():
 *       yield 10     # pc=0
 *       yield 20     # pc=1
 *       yield 30     # pc=2
 *                    # pc=3 -> done
 *
 * Each case in the switch corresponds to one yield point.
 */
typedef struct {
    int value;
    int done;
    int pc;     /* stored program counter: which yield to resume at */
} multi_gen;

static void multi_init(multi_gen *g) { g->pc = 0; g->done = 0; }

static void multi_next(multi_gen *g) {
    switch (g->pc) {
    case 0: g->value = 10; g->pc = 1; return;
    case 1: g->value = 20; g->pc = 2; return;
    case 2: g->value = 30; g->pc = 3; return;
    default: g->done = 1; return;
    }
}


/* 
 * 8. Eager vs. lazy cost comparison
 */
static long eager_sum_squares_to(long n) {
    long *evens = malloc(n * sizeof(long));
    long  count = 0, sum = 0;

    for (long i = 0; i < n; i++)
        if (i % 2 == 0) evens[count++] = i;
    for (long i = 0; i < count; i++)
        sum += evens[i] * evens[i];

    free(evens);
    return sum;
}

static long lazy_sum_squares_to(long n) {
    /* No allocation: the "generator" is the loop variable itself. */
    long sum = 0;
    for (long i = 0; i < n; i++)
        if (i % 2 == 0) sum += i * i;
    return sum;
}



int main(void) {
    /* --- 1. Counter */
    printf("-- 1. Counter generator --\n  ");
    {
        counter_gen g;
        counter_init(&g);
        for (int i = 0; i < 8; i++) {
            counter_next(&g);
            printf("%ld ", g.value);
        }
        printf("\n");
    }

    /* --- 2. Range */
    printf("\n-- 2. Range generator --\n");
    {
        range_gen g;
        range_init(&g, 0, 10, 2);
        printf("  range(0,10,2): ");
        range_next(&g);          /* prime */
        while (!g.done) {
            printf("%ld ", g.value);
            range_next(&g);
        }
        printf("\n");
    }

    /* --- 3. Fibonacci */
    printf("\n-- 3. Fibonacci generator --\n  ");
    {
        fib_gen g;
        fib_init(&g);
        fib_next(&g);            /* prime */
        for (int i = 0; i < 10; i++) {
            printf("%ld ", g.value);
            fib_next(&g);
        }
        printf("\n");
    }

    /* --- 4+5. Chained pipeline: fib -> even filter -> square map */
    printf("\n-- 4+5. Pipeline: fib -> even filter -> square map --\n");
    {
        fib_gen      fib;  fib_init(&fib);
        even_fib_gen ef;   even_fib_init(&ef, &fib);
        sq_even_fib_gen sq; sq_even_fib_init(&sq, &ef);

        printf("  first 6 squares of even Fibonacci numbers:\n  ");
        for (int i = 0; i < 6; i++) {
            sq_even_fib_next(&sq);
            printf("%ld ", sq.value);
        }
        /* even fibs: 0, 2, 8, 34, 144, 610 ...
           squares:   0, 4, 64, 1156, 20736, 372100 */
        printf("\n");
    }

    /* --- 6. take() via function pointer */
    printf("\n-- 6. take() with counter via function pointer --\n");
    {
        counter_gen g;
        counter_init(&g);
        long buf[5] = {0};

        take(&g, (advance_fn)counter_next,
             &g.value, &g.done, 5, buf);

        printf("  first 5: ");
        for (int i = 0; i < 5; i++) printf("%ld ", buf[i]);
        printf("\n");
    }

    /* --- 7. Multi-yield state machine */
    printf("\n-- 7. Multi-yield state machine (pc field) --\n");
    {
        multi_gen g;
        multi_init(&g);
        printf("  pc=0->10, pc=1->20, pc=2->30, pc=3->done\n  values: ");
        multi_next(&g);          /* prime */
        while (!g.done) {
            printf("%d ", g.value);
            multi_next(&g);
        }
        printf("\n");
    }

    /* --- 8. Eager vs. lazy */
    printf("\n-- 8. Eager vs. lazy: sum of squares of even numbers < N --\n");
    {
        long N = 1000;
        long e = eager_sum_squares_to(N);
        long l = lazy_sum_squares_to(N);
        printf("  N=%ld\n", N);
        printf("  eager: %ld  (allocated array of %ld longs)\n", e, N);
        printf("  lazy:  %ld  (no allocation; loop variable is the generator)\n", l);
        printf("  results match: %s\n", e == l ? "yes" : "no");
    }

    /* --- Key observations */
    printf("\n-- Key observations --\n");
    printf("  A C generator = struct (frame) + next() function.\n");
    printf("  The struct holds local variables; pc handles multiple yield points.\n");
    printf("  Chaining: each generator holds a pointer to its upstream source.\n");
    printf("  Protocol: init -> prime with next() -> loop while !done.\n");
    printf("  Python automates frame allocation and state machine compilation;\n");
    printf("  in C you write both by hand, per generator type.\n");

    return 0;
}
