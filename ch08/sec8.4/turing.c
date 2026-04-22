#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BLANK     '_'
#define HALT      (-1)
#define TAPE_SIZE 4096
#define ORIGIN    (TAPE_SIZE / 2)

typedef struct {
    int  from;   /* current state   */
    char read;   /* symbol read     */
    char write;  /* symbol to write */
    int  move;   /* -1=L, 0=stay, 1=R */
    int  to;     /* next state      */
} Rule;

typedef struct {
    char cells[TAPE_SIZE];
    int  head;              /* absolute index into cells[] */
} Tape;

static void tape_init(Tape *t, const char *input) {
    memset(t->cells, BLANK, TAPE_SIZE);
    t->head = ORIGIN;
    for (int i = 0; input[i]; i++)
        t->cells[ORIGIN + i] = input[i];
}

static char tape_read(const Tape *t) {
    return (t->head >= 0 && t->head < TAPE_SIZE) ? t->cells[t->head] : BLANK;
}

static void tape_write(Tape *t, char sym) {
    if (t->head >= 0 && t->head < TAPE_SIZE)
        t->cells[t->head] = sym;
}

/* Runs the machine; returns number of steps taken. */
static int tm_run(Tape *t, int init_state,
                  const Rule *rules, int nrules, int max_steps) {
    int state = init_state, steps = 0;
    while (state != HALT && steps < max_steps) {
        char sym = tape_read(t);
        int matched = 0;
        for (int i = 0; i < nrules; i++) {
            if (rules[i].from == state && rules[i].read == sym) {
                tape_write(t, rules[i].write);
                t->head += rules[i].move;
                state = rules[i].to;
                matched = 1;
                break;
            }
        }
        if (!matched) break;
        steps++;
    }
    return steps;
}

/* Copy the non-blank content into buf (must be large enough). */
static void result_to_str(const Tape *t, char *buf) {
    int lo = TAPE_SIZE, hi = -1;
    for (int i = 0; i < TAPE_SIZE; i++) {
        if (t->cells[i] != BLANK) {
            if (i < lo) lo = i;
            hi = i;
        }
    }
    if (lo > hi) { buf[0] = BLANK; buf[1] = '\0'; return; }
    int k = 0;
    for (int i = lo; i <= hi; i++) buf[k++] = t->cells[i];
    buf[k] = '\0';
}

/* Read the non-blank content as a binary integer. */
static long result_to_long(const Tape *t) {
    int lo = TAPE_SIZE, hi = -1;
    for (int i = 0; i < TAPE_SIZE; i++) {
        if (t->cells[i] != BLANK) {
            if (i < lo) lo = i;
            hi = i;
        }
    }
    long val = 0;
    for (int i = lo; i <= hi; i++)
        val = val * 2 + (t->cells[i] - '0');
    return val;
}

int main(void) {
    /*
     * Binary increment TM
     * State 0: scan right to find the blank at the end of input
     * State 1: scan left, propagating carry
     */
    static const Rule rules[] = {
        /* from  read    write   move  to   */
        {  0,   '0',    '0',     1,   0  }, /* keep scanning right */
        {  0,   '1',    '1',     1,   0  },
        {  0,   BLANK,  BLANK,  -1,   1  }, /* hit end; begin carry */
        {  1,   '1',    '0',    -1,   1  }, /* 1+carry=10; write 0, carry on */
        {  1,   '0',    '1',     0,  HALT}, /* 0+carry=1; done */
        {  1,   BLANK,  '1',     0,  HALT}, /* overflow: prepend 1 */
    };
    int nrules = (int)(sizeof rules / sizeof rules[0]);

    const char *examples[] = {"0", "1", "101", "1011", "111", "1111", NULL};

    printf("%-8s  %4s   %-8s  %4s   %s\n",
           "Input", "Dec", "Output", "Dec", "Steps");
    printf("%-8s  %4s   %-8s  %4s   %s\n",
           "-----", "---", "------", "---", "-----");

    for (int e = 0; examples[e]; e++) {
        const char *inp = examples[e];
        Tape t;
        tape_init(&t, inp);

        long dec_in = strtol(inp, NULL, 2);
        int steps = tm_run(&t, 0, rules, nrules, 100000);
        long dec_out = result_to_long(&t);
        char out[64];
        result_to_str(&t, out);

        printf("%-8s  %4ld   %-8s  %4ld   %d\n",
               inp, dec_in, out, dec_out, steps);
    }
    return 0;
}
