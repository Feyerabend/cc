#include <stdio.h>
#include <string.h>
#include "trit.h"
#include "setun.h"
#include "setun70.h"

static void print_separator(const char *label)
{
    printf("\n=== %s ===\n", label);
}

/* Test balanced ternary arithmetic. */
static void test_trit_arithmetic(void)
{
    print_separator("Balanced ternary arithmetic");

    long values[] = { 13, 7, 6, -6, -7, -13, 0, 100, -100 };
    int n = (int) (sizeof(values) / sizeof(values[0]));

    for (int i = 0; i < n; i++) {
        word18_t w = long_to_word18(values[i]);
        long back = word18_to_long(&w);
        printf("  %6ld -> ", values[i]);
        word18_print(&w);
        printf(" -> %ld  %s\n", back, back == values[i] ? "OK" : "FAIL");
    }

    printf("\nAddition: 7 + 6 = ");
    word18_t a = long_to_word18(7);
    word18_t b = long_to_word18(6);
    trit_t ov;
    word18_t c = word18_add(&a, &b, &ov);
    word18_print(&c);
    printf(" = %ld\n", word18_to_long(&c));

    printf("Negation: -(+7) = ");
    word18_t neg = word18_neg(&a);
    word18_print(&neg);
    printf(" = %ld\n", word18_to_long(&neg));

    printf("Multiply: 7 * 6 = ");
    word18_t prod = word18_mul(&a, &b);
    word18_print(&prod);
    printf(" = %ld\n", word18_to_long(&prod));
}

/*
 * Setun demo: compute sum of integers 1..5 using a simple loop.
 *
 * Memory layout (each "slot" is two 9-trit cells for 18-trit data):
 *   addr 0,1  : variable N  (loop counter, starts at 5)
 *   addr 2,3  : variable SUM (accumulator, starts at 0)
 *   addr 4,5  : constant ONE (value 1)
 *   addr 6    : instruction: LOAD N (S := N)
 *   addr 7    : instruction: JZERO done (if N==0 jump to done)
 *   addr 8    : instruction: LOAD SUM (S := SUM)
 *   addr 9    : instruction: ADD N (S := SUM + N)
 *   addr 10   : instruction: STORE SUM
 *   addr 11   : instruction: LOAD N
 *   addr 12   : instruction: SUB ONE (S := N - 1)
 *   addr 13   : instruction: STORE N
 *   addr 14   : instruction: JUMP loop_start (back to addr 6)
 *   addr 15   : instruction: HALT  (done)
 */
static void demo_setun_sum(void)
{
    print_separator("Setun: sum of 1..5");

    setun_t cpu;
    setun_init(&cpu);

    /* Data: N=5, SUM=0, ONE=1 */
    word18_t n_val   = long_to_word18(5);
    word18_t sum_val = long_to_word18(0);
    word18_t one_val = long_to_word18(1);

    setun_mem_write18(&cpu, 0, &n_val);
    setun_mem_write18(&cpu, 2, &sum_val);
    setun_mem_write18(&cpu, 4, &one_val);

    /* map_op converts an opcode enum to the 3-trit integer the assembler expects. */
    #define map_op(op) ((int)(op) - 13)

    word9_t wi;
    wi = setun_assemble(map_op(OP_LOAD),  0);  setun_mem_write(&cpu, 6,  &wi);
    wi = setun_assemble(map_op(OP_JZERO), 15); setun_mem_write(&cpu, 7,  &wi);
    wi = setun_assemble(map_op(OP_LOAD),  2);  setun_mem_write(&cpu, 8,  &wi);
    wi = setun_assemble(map_op(OP_ADD),   0);  setun_mem_write(&cpu, 9,  &wi);
    wi = setun_assemble(map_op(OP_STORE), 2);  setun_mem_write(&cpu, 10, &wi);
    wi = setun_assemble(map_op(OP_LOAD),  0);  setun_mem_write(&cpu, 11, &wi);
    wi = setun_assemble(map_op(OP_SUB),   4);  setun_mem_write(&cpu, 12, &wi);
    wi = setun_assemble(map_op(OP_STORE), 0);  setun_mem_write(&cpu, 13, &wi);
    wi = setun_assemble(map_op(OP_JUMP),  6);  setun_mem_write(&cpu, 14, &wi);
    wi = setun_assemble(map_op(OP_HALT),  0);  setun_mem_write(&cpu, 15, &wi);

    #undef map_op

    /* Start PC at instruction address 6. */
    cpu.P = int_to_word9(6);

    setun_run(&cpu);

    word18_t result = setun_mem_read18(&cpu, 2);
    printf("  sum(1..5) = %ld  (expected 15)\n", word18_to_long(&result));
    printf("  Final state:\n  ");
    setun_dump(&cpu);
}

/* Setun demo: compute 4! = 4*3*2*1. MUL stores the product in R; LOADR copies R to S. */
static void demo_setun_factorial(void)
{
    print_separator("Setun: factorial of 4 via multiply");

    setun_t cpu;
    setun_init(&cpu);

    /* Data slots */
    word18_t val4  = long_to_word18(4);
    word18_t val3  = long_to_word18(3);
    word18_t val2  = long_to_word18(2);
    word18_t val1  = long_to_word18(1);
    word18_t acc   = long_to_word18(1);

    setun_mem_write18(&cpu, 0, &val4);
    setun_mem_write18(&cpu, 2, &val3);
    setun_mem_write18(&cpu, 4, &val2);
    setun_mem_write18(&cpu, 6, &val1);
    setun_mem_write18(&cpu, 8, &acc);  /* accumulator starts at 1 */

    #define map_op(op) ((int)(op) - 13)

    /* Program starts at cell 22: load 1, then multiply by 2, 3, 4 in sequence. */
    word9_t wf;
    wf = setun_assemble(map_op(OP_LOAD),  6); setun_mem_write(&cpu, 22, &wf);  /* S = 1 */
    wf = setun_assemble(map_op(OP_MUL),   4); setun_mem_write(&cpu, 23, &wf);  /* S = 1*2 */
    wf = setun_assemble(map_op(OP_LOADR), 0); setun_mem_write(&cpu, 24, &wf);  /* S = R */
    wf = setun_assemble(map_op(OP_MUL),   2); setun_mem_write(&cpu, 25, &wf);  /* S = 2*3 */
    wf = setun_assemble(map_op(OP_LOADR), 0); setun_mem_write(&cpu, 26, &wf);  /* S = R */
    wf = setun_assemble(map_op(OP_MUL),   0); setun_mem_write(&cpu, 27, &wf);  /* S = 6*4 */
    wf = setun_assemble(map_op(OP_LOADR), 0); setun_mem_write(&cpu, 28, &wf);  /* S = R = 24 */
    wf = setun_assemble(map_op(OP_STORE), 8); setun_mem_write(&cpu, 29, &wf);  /* mem[8] = 24 */
    wf = setun_assemble(map_op(OP_HALT),  0); setun_mem_write(&cpu, 30, &wf);

    #undef map_op

    cpu.P = int_to_word9(22);
    setun_run(&cpu);

    word18_t result = setun_mem_read18(&cpu, 8);
    printf("  4! = %ld  (expected 24)\n", word18_to_long(&result));
}

/* Setun-70 demo: GCD(12, 8) using Euclid's algorithm on the data stack. */
static void demo_setun70_gcd(void)
{
    print_separator("Setun-70: GCD(12, 8) via Euclid");

    setun70_t cpu;
    setun70_init(&cpu);

    /* GCD via Euclid: while b != 0, replace (a, b) with (b, a mod b).
       a mod b is computed as a - (a/b)*b using RPUSH/RPOP to hold b across the SUB. */

    int gcd_prog[] = {
        /* 0: loop */
        S70_DUP,                /* [ a b b ] */
        S70_JZERO, 18, 0,        /* if b==0 goto done(17); DS=[ a b ] */
        S70_OVER,               /* [ a b a ] */
        S70_OVER,               /* [ a b a b ] */
        S70_SWAP,               /* [ a b b a ] */
        S70_OVER,               /* [ a b b a b ] */
        S70_DIV,                /* [ a b b a/b ] */
        S70_MUL,                /* [ a b b*(a/b) ] */
        S70_SWAP,               /* [ a b*(a/b) b ] */
        S70_RPUSH,              /* RS=[b]; DS=[ a b*(a/b) ] */
        S70_SUB,                /* [ a - b*(a/b) ] = [ a%b ] */
        S70_RPOP,               /* RS=[]; DS=[ a%b b ] */
        S70_SWAP,               /* [ b a%b ] */
        S70_JUMP, 0, 0,          /* goto loop(0) */
        /* 17: done */
        S70_POP,                /* discard 0 (the b that was zero) */
        /* result a remains on stack */
        S70_HALT
    };

    int prog_len = (int) (sizeof(gcd_prog) / sizeof(gcd_prog[0]));
    setun70_load_program(&cpu, 0, gcd_prog, prog_len);

    /* Push initial values: a=12, b=8 */
    tryte_t a = int_to_tryte(12);
    tryte_t b_val = int_to_tryte(8);
    setun70_ds_push(&cpu, &a);
    setun70_ds_push(&cpu, &b_val);

    cpu.pc = 0;
    setun70_run(&cpu);

    if (!cpu.error && cpu.ds_top > 0) {
        tryte_t result = setun70_ds_pop(&cpu);
        printf("  GCD(12, 8) = %d  (expected 4)\n", tryte_to_int(&result));
    }
    printf("  Final state:\n  ");
    setun70_dump(&cpu);
}

/* Setun-70 demo: factorial via CALL/RET to show the return stack. */
static void demo_setun70_factorial(void)
{
    print_separator("Setun-70: factorial via CALL/RET (4!)");

    setun70_t cpu;
    setun70_init(&cpu);

    /* Iterative factorial: DS holds [ acc n ].  Each iteration: acc *= n, n--.
       CALL at addr 4 pushes return addr 7 (HALT); RET jumps back there. */

    int main_prog[] = {
        /* addr 0: main */
        S70_PUSH, 1,            /* push acc=1 */
        S70_PUSH, 4,            /* push n=4 */
        S70_CALL, 8, 0,         /* CALL fact_loop (addr 8); return addr 7 pushed */
        /* addr 7: */
        S70_HALT,

        /* addr 8: fact_loop  DS: [ acc n ] */
        S70_DUP,                /* [ acc n n ] */
        S70_JZERO, 22, 0,       /* if n==0 jump to done (addr 22) */
        S70_SWAP,               /* [ n acc ] */
        S70_OVER,               /* [ n acc n ] */
        S70_MUL,                /* [ n acc*n ] */
        S70_SWAP,               /* [ acc*n n ] */
        S70_PUSH, 1,            /* [ acc*n n 1 ] */
        S70_SUB,                /* [ acc*n n-1 ] */
        S70_JUMP, 8, 0,         /* loop back to addr 8 */

        /* addr 22: done  DS: [ acc 0 ] */
        S70_POP,                /* [ acc ] discard the 0 */
        S70_RET                 /* return to addr 7 (HALT) */
    };

    int prog_len = (int) (sizeof(main_prog) / sizeof(main_prog[0]));
    setun70_load_program(&cpu, 0, main_prog, prog_len);

    cpu.pc = 0;
    setun70_run(&cpu);

    if (!cpu.error && cpu.ds_top > 0) {
        tryte_t result = setun70_ds_pop(&cpu);
        printf("  4! = %d  (expected 24)\n", tryte_to_int(&result));
    }
    printf("  Final state:\n  ");
    setun70_dump(&cpu);
}

int main(void)
{
    printf("Setun / Setun-70 emulator\n");
    printf("Balanced ternary (trits: -1, 0, +1)\n");

    test_trit_arithmetic();
    demo_setun_sum();
    demo_setun_factorial();
    demo_setun70_gcd();
    demo_setun70_factorial();

    printf("\nDone.\n");
    return 0;
}
