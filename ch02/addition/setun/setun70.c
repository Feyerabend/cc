#include "setun70.h"
#include <stdio.h>
#include <stdlib.h>

void setun70_init(setun70_t *cpu)
{
    tryte_t zero = int_to_tryte(0);

    for (int i = 0; i < S70_MEM_TRYTES; i++)
        cpu->mem[i] = zero;

    for (int i = 0; i < S70_OPEN_PAGES; i++)
        cpu->page_reg[i] = i;   /* pages 0, 1, 2 open by default */

    for (int i = 0; i < S70_STACK_DEPTH; i++) {
        cpu->ds[i] = zero;
        cpu->rs[i] = zero;
    }

    cpu->ds_top = 0;
    cpu->rs_top = 0;
    cpu->pc     = 0;
    cpu->halted = 0;
    cpu->error  = 0;

    for (int i = 0; i < 27; i++)
        cpu->user_op_target[i] = 0;
}

void setun70_mem_write(setun70_t *cpu, int addr, const tryte_t *tr)
{
    if (addr < 0 || addr >= S70_MEM_TRYTES) {
        fprintf(stderr, "setun70: memory write out of range: %d\n", addr);
        cpu->error = 1;
        return;
    }
    cpu->mem[addr] = *tr;
}

tryte_t setun70_mem_read(const setun70_t *cpu, int addr)
{
    tryte_t zero = int_to_tryte(0);
    if (addr < 0 || addr >= S70_MEM_TRYTES) {
        fprintf(stderr, "setun70: memory read out of range: %d\n", addr);
        return zero;
    }
    return cpu->mem[addr];
}

void setun70_ds_push(setun70_t *cpu, const tryte_t *val)
{
    if (cpu->ds_top >= S70_STACK_DEPTH) {
        fprintf(stderr, "setun70: data stack overflow\n");
        cpu->error = 1;
        return;
    }
    cpu->ds[cpu->ds_top++] = *val;
}

tryte_t setun70_ds_pop(setun70_t *cpu)
{
    tryte_t zero = int_to_tryte(0);
    if (cpu->ds_top <= 0) {
        fprintf(stderr, "setun70: data stack underflow\n");
        cpu->error = 1;
        return zero;
    }
    return cpu->ds[--cpu->ds_top];
}

tryte_t setun70_ds_peek(const setun70_t *cpu)
{
    tryte_t zero = int_to_tryte(0);
    if (cpu->ds_top <= 0) {
        fprintf(stderr, "setun70: data stack peek on empty stack\n");
        return zero;
    }
    return cpu->ds[cpu->ds_top - 1];
}

void setun70_rs_push(setun70_t *cpu, const tryte_t *val)
{
    if (cpu->rs_top >= S70_STACK_DEPTH) {
        fprintf(stderr, "setun70: return stack overflow\n");
        cpu->error = 1;
        return;
    }
    cpu->rs[cpu->rs_top++] = *val;
}

tryte_t setun70_rs_pop(setun70_t *cpu)
{
    tryte_t zero = int_to_tryte(0);
    if (cpu->rs_top <= 0) {
        fprintf(stderr, "setun70: return stack underflow\n");
        cpu->error = 1;
        return zero;
    }
    return cpu->rs[--cpu->rs_top];
}

static int tryte_val(const tryte_t *tr)
{
    return tryte_to_int(tr);
}

int setun70_step(setun70_t *cpu)
{
    if (cpu->halted || cpu->error)
        return -1;

    tryte_t op_tryte = setun70_mem_read(cpu, cpu->pc);
    int op_val = tryte_val(&op_tryte);
    cpu->pc++;

    /*
     * Map tryte value to opcode index.
     * Basic ops:   op_val 0..26  (stored as balanced ternary of their index)
     * Aux ops:     op_val 27..53
     * User ops:    op_val 54..80
     * We convert from the stored balanced-ternary integer directly.
     */
    int op_idx = op_val;

    if (op_idx < 0 || op_idx > 80) {
        fprintf(stderr, "setun70: invalid opcode index %d\n", op_idx);
        cpu->error = 1;
        return -1;
    }

    tryte_t a, b, result;
    int va, vb, vr;

    if (op_idx >= S70_USER_BASE) {
        /* User-programmable: call the stored target address. */
        int user_idx = op_idx - S70_USER_BASE;
        tryte_t ret_tryte = int_to_tryte(cpu->pc);
        setun70_rs_push(cpu, &ret_tryte);
        cpu->pc = cpu->user_op_target[user_idx];
        return 0;
    }

    s70_opcode_t op = (s70_opcode_t) op_idx;

    switch (op) {

    case S70_NOP:
        break;

    case S70_PUSH: {
        tryte_t lit = setun70_mem_read(cpu, cpu->pc++);
        setun70_ds_push(cpu, &lit);
        break;
    }

    case S70_POP: {
        setun70_ds_pop(cpu);
        break;
    }

    case S70_DUP: {
        a = setun70_ds_peek(cpu);
        setun70_ds_push(cpu, &a);
        break;
    }

    case S70_SWAP: {
        a = setun70_ds_pop(cpu);
        b = setun70_ds_pop(cpu);
        setun70_ds_push(cpu, &a);
        setun70_ds_push(cpu, &b);
        break;
    }

    case S70_OVER: {
        if (cpu->ds_top < 2) {
            fprintf(stderr, "setun70: OVER requires 2 stack items\n");
            cpu->error = 1;
            return -1;
        }
        tryte_t second = cpu->ds[cpu->ds_top - 2];
        setun70_ds_push(cpu, &second);
        break;
    }

    case S70_ADD: {
        b = setun70_ds_pop(cpu);
        a = setun70_ds_pop(cpu);
        result = int_to_tryte(tryte_val(&a) + tryte_val(&b));
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_SUB: {
        b = setun70_ds_pop(cpu);
        a = setun70_ds_pop(cpu);
        result = int_to_tryte(tryte_val(&a) - tryte_val(&b));
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_MUL: {
        b = setun70_ds_pop(cpu);
        a = setun70_ds_pop(cpu);
        result = int_to_tryte(tryte_val(&a) * tryte_val(&b));
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_DIV: {
        b = setun70_ds_pop(cpu);
        a = setun70_ds_pop(cpu);
        vb = tryte_val(&b);
        if (vb == 0) {
            fprintf(stderr, "setun70: division by zero\n");
            cpu->error = 1;
            return -1;
        }
        result = int_to_tryte(tryte_val(&a) / vb);
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_NEG: {
        a = setun70_ds_pop(cpu);
        result = int_to_tryte(-tryte_val(&a));
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_ABS: {
        a = setun70_ds_pop(cpu);
        va = tryte_val(&a);
        result = int_to_tryte(va < 0 ? -va : va);
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_SGN: {
        a = setun70_ds_pop(cpu);
        va = tryte_val(&a);
        vr = (va > 0) ? 1 : (va < 0) ? -1 : 0;
        result = int_to_tryte(vr);
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_EQ: {
        b = setun70_ds_pop(cpu);
        a = setun70_ds_pop(cpu);
        result = int_to_tryte(tryte_val(&a) == tryte_val(&b) ? 1 : 0);
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_LT: {
        b = setun70_ds_pop(cpu);
        a = setun70_ds_pop(cpu);
        result = int_to_tryte(tryte_val(&a) < tryte_val(&b) ? 1 : 0);
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_AND: {
        b = setun70_ds_pop(cpu);
        a = setun70_ds_pop(cpu);
        va = tryte_val(&a);
        vb = tryte_val(&b);
        result = int_to_tryte(va < vb ? va : vb);
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_OR: {
        b = setun70_ds_pop(cpu);
        a = setun70_ds_pop(cpu);
        va = tryte_val(&a);
        vb = tryte_val(&b);
        result = int_to_tryte(va > vb ? va : vb);
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_NOT: {
        a = setun70_ds_pop(cpu);
        result = int_to_tryte(-tryte_val(&a));
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_LOAD: {
        a = setun70_ds_pop(cpu);
        int load_addr = tryte_val(&a);
        tryte_t val = setun70_mem_read(cpu, load_addr);
        setun70_ds_push(cpu, &val);
        break;
    }

    case S70_STORE: {
        a = setun70_ds_pop(cpu);  /* address */
        b = setun70_ds_pop(cpu);  /* value */
        int store_addr = tryte_val(&a);
        setun70_mem_write(cpu, store_addr, &b);
        break;
    }

    case S70_CALL: {
        int lo  = tryte_to_int(&cpu->mem[cpu->pc++]);
        int hi  = tryte_to_int(&cpu->mem[cpu->pc++]);
        int tgt = lo + hi * 243;
        /* Push 2-tryte return address onto RS (lo first, then hi). */
        tryte_t ret_lo = int_to_tryte(cpu->pc % 243);
        tryte_t ret_hi = int_to_tryte(cpu->pc / 243);
        setun70_rs_push(cpu, &ret_hi);
        setun70_rs_push(cpu, &ret_lo);
        cpu->pc = tgt;
        break;
    }

    case S70_RET: {
        tryte_t ret_lo = setun70_rs_pop(cpu);
        tryte_t ret_hi = setun70_rs_pop(cpu);
        cpu->pc = tryte_to_int(&ret_lo) + tryte_to_int(&ret_hi) * 243;
        break;
    }

    case S70_JUMP: {
        int lo  = tryte_to_int(&cpu->mem[cpu->pc++]);
        int hi  = tryte_to_int(&cpu->mem[cpu->pc]);
        cpu->pc = lo + hi * 243;
        break;
    }

    case S70_JPOS: {
        int lo  = tryte_to_int(&cpu->mem[cpu->pc++]);
        int hi  = tryte_to_int(&cpu->mem[cpu->pc++]);
        int tgt = lo + hi * 243;
        a = setun70_ds_pop(cpu);
        if (tryte_val(&a) > 0)
            cpu->pc = tgt;
        break;
    }

    case S70_JZERO: {
        int lo  = tryte_to_int(&cpu->mem[cpu->pc++]);
        int hi  = tryte_to_int(&cpu->mem[cpu->pc++]);
        int tgt = lo + hi * 243;
        a = setun70_ds_pop(cpu);
        if (tryte_val(&a) == 0)
            cpu->pc = tgt;
        break;
    }

    case S70_JNEG: {
        int lo  = tryte_to_int(&cpu->mem[cpu->pc++]);
        int hi  = tryte_to_int(&cpu->mem[cpu->pc++]);
        int tgt = lo + hi * 243;
        a = setun70_ds_pop(cpu);
        if (tryte_val(&a) < 0)
            cpu->pc = tgt;
        break;
    }

    case S70_HALT: {
        cpu->halted = 1;
        return -1;
    }

    case S70_EMIT: {
        a = setun70_ds_pop(cpu);
        putchar(tryte_val(&a));
        break;
    }

    case S70_KEY: {
        int ch = getchar();
        result = int_to_tryte(ch);
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_PAGESEL: {
        b = setun70_ds_pop(cpu);   /* page number */
        a = setun70_ds_pop(cpu);   /* slot (0..2) */
        int slot = tryte_val(&a);
        int page = tryte_val(&b);
        if (slot >= 0 && slot < S70_OPEN_PAGES &&
            page >= 0 && page < S70_NUM_PAGES) {
            cpu->page_reg[slot] = page;
        } else {
            fprintf(stderr, "setun70: invalid PAGESEL slot=%d page=%d\n",
                    slot, page);
            cpu->error = 1;
            return -1;
        }
        break;
    }

    case S70_DEPTH: {
        result = int_to_tryte(cpu->ds_top);
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_RDEPTH: {
        result = int_to_tryte(cpu->rs_top);
        setun70_ds_push(cpu, &result);
        break;
    }

    case S70_RPUSH: {
        a = setun70_ds_pop(cpu);
        setun70_rs_push(cpu, &a);
        break;
    }

    case S70_RPOP: {
        a = setun70_rs_pop(cpu);
        setun70_ds_push(cpu, &a);
        break;
    }

    case S70_RPEEK: {
        if (cpu->rs_top <= 0) {
            fprintf(stderr, "setun70: RPEEK on empty return stack\n");
            cpu->error = 1;
            return -1;
        }
        tryte_t top = cpu->rs[cpu->rs_top - 1];
        setun70_ds_push(cpu, &top);
        break;
    }

    default: {
        /* Reserved auxiliary slots are no-ops for now. */
        break;
    }
    }

    return 0;
}

void setun70_run(setun70_t *cpu)
{
    while (!cpu->halted && !cpu->error)
        setun70_step(cpu);
}

void setun70_dump(const setun70_t *cpu)
{
    printf("PC      = %d\n", cpu->pc);
    printf("Pages   = [%d, %d, %d]\n",
           cpu->page_reg[0], cpu->page_reg[1], cpu->page_reg[2]);

    printf("DS (%d): ", cpu->ds_top);
    for (int i = 0; i < cpu->ds_top; i++) {
        printf("%d ", tryte_to_int(&cpu->ds[i]));
    }
    putchar('\n');

    printf("RS (%d): ", cpu->rs_top);
    for (int i = 0; i < cpu->rs_top; i++) {
        printf("%d ", tryte_to_int(&cpu->rs[i]));
    }
    putchar('\n');

    printf("halted=%d  error=%d\n", cpu->halted, cpu->error);
}

void setun70_load_program(setun70_t *cpu, int start_addr,
                          const int *values, int count)
{
    for (int i = 0; i < count; i++) {
        tryte_t tr = int_to_tryte(values[i]);
        setun70_mem_write(cpu, start_addr + i, &tr);
    }
}
