#include "setun.h"
#include <stdio.h>
#include <stdlib.h>

void setun_init(setun_t *cpu)
{
    word9_t  zero9  = { .t = {0,0,0,0,0,0,0,0,0} };
    word18_t zero18 = { .t = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0} };

    for (int i = 0; i < SETUN_MEM_CELLS; i++)
        cpu->mem[i] = zero9;

    cpu->S      = zero18;
    cpu->R      = zero18;
    cpu->F      = zero9;
    cpu->P      = zero9;
    cpu->omega  = TRIT_ZERO;
    cpu->halted = 0;
    cpu->error  = 0;
}

void setun_mem_write(setun_t *cpu, int addr, const word9_t *w)
{
    if (addr < 0 || addr >= SETUN_MEM_CELLS) {
        fprintf(stderr, "setun: memory write out of range: %d\n", addr);
        cpu->error = 1;
        return;
    }
    cpu->mem[addr] = *w;
}

word9_t setun_mem_read(const setun_t *cpu, int addr)
{
    word9_t zero = { .t = {0,0,0,0,0,0,0,0,0} };
    if (addr < 0 || addr >= SETUN_MEM_CELLS) {
        fprintf(stderr, "setun: memory read out of range: %d\n", addr);
        return zero;
    }
    return cpu->mem[addr];
}

void setun_mem_write18(setun_t *cpu, int addr, const word18_t *w)
{
    word9_t upper = word18_upper9(w);
    word9_t lower = word18_lower9(w);
    setun_mem_write(cpu, addr,     &upper);
    setun_mem_write(cpu, addr + 1, &lower);
}

word18_t setun_mem_read18(const setun_t *cpu, int addr)
{
    word9_t upper = setun_mem_read(cpu, addr);
    word9_t lower = setun_mem_read(cpu, addr + 1);
    return word9_combine(&upper, &lower);
}

/*
 * Instruction layout (9 trits, LST = trit 0):
 *   trits 0..5  address field  (6 trits)
 *   trits 6..8  opcode field   (3 trits)
 */
word9_t setun_assemble(int opcode_val, int addr_val)
{
    word9_t instr;
    word9_t addr_w  = int_to_word9(addr_val);
    word9_t op_w    = int_to_word9(opcode_val);

    for (int i = 0; i < 6; i++)
        instr.t[i] = addr_w.t[i];
    for (int i = 0; i < 3; i++)
        instr.t[6 + i] = op_w.t[i];

    return instr;
}

void setun_decode(const word9_t *instr, int *opcode_val, int *addr_val)
{
    word9_t op_w   = { .t = {0,0,0,0,0,0,0,0,0} };
    word9_t addr_w = { .t = {0,0,0,0,0,0,0,0,0} };

    for (int i = 0; i < 6; i++)
        addr_w.t[i] = instr->t[i];
    for (int i = 0; i < 3; i++)
        op_w.t[i] = instr->t[6 + i];

    *opcode_val = word9_to_int(&op_w);
    *addr_val   = word9_to_int(&addr_w);
}

/*
 * Map the balanced-ternary opcode integer (from the 3-trit field) to the
 * setun_opcode_t enum.  We assign:
 *   -13 .. +13 range, 24 values used, linearly mapped to OP_LOAD..OP_HALT.
 */
static setun_opcode_t map_opcode(int v)
{
    /* Shift from [-13,+10] to [0,23]. */
    int idx = v + 13;
    if (idx < 0 || idx > 23)
        return OP_NOP;
    return (setun_opcode_t) idx;
}

/*
 * Resolve the effective address: flat memory index after applying index
 * register F.  The paper says F modifies address by addition or subtraction;
 * we support both via the sign of F (positive => add, negative => subtract).
 */
static int effective_addr(const setun_t *cpu, int raw_addr)
{
    int f_val = word9_to_int(&cpu->F);
    int ea    = raw_addr + f_val;

    if (ea < 0 || ea >= SETUN_MEM_CELLS) {
        fprintf(stderr, "setun: effective address out of range: %d\n", ea);
        return 0;
    }
    return ea;
}

int setun_step(setun_t *cpu)
{
    if (cpu->halted || cpu->error)
        return -1;

    int pc = word9_to_int(&cpu->P);
    if (pc < 0 || pc >= SETUN_MEM_CELLS) {
        fprintf(stderr, "setun: PC out of range: %d\n", pc);
        cpu->error = 1;
        return -1;
    }

    word9_t instr = setun_mem_read(cpu, pc);

    int opcode_val, raw_addr;
    setun_decode(&instr, &opcode_val, &raw_addr);

    setun_opcode_t op = map_opcode(opcode_val);

    /* Advance PC before execution (may be overridden by jumps). */
    word9_t next_pc = int_to_word9(pc + 1);
    cpu->P = next_pc;

    int ea = effective_addr(cpu, raw_addr);
    trit_t overflow;

    switch (op) {

    case OP_LOAD: {
        cpu->S = setun_mem_read18(cpu, ea);
        cpu->omega = word18_sign(&cpu->S);
        break;
    }

    case OP_STORE: {
        setun_mem_write18(cpu, ea, &cpu->S);
        break;
    }

    case OP_ADD: {
        word18_t operand = setun_mem_read18(cpu, ea);
        cpu->S = word18_add(&cpu->S, &operand, &overflow);
        cpu->omega = word18_sign(&cpu->S);
        break;
    }

    case OP_SUB: {
        word18_t operand = setun_mem_read18(cpu, ea);
        word18_t neg_op  = word18_neg(&operand);
        cpu->S = word18_add(&cpu->S, &neg_op, &overflow);
        cpu->omega = word18_sign(&cpu->S);
        break;
    }

    case OP_MUL: {
        word18_t operand = setun_mem_read18(cpu, ea);
        word18_t product = word18_mul(&cpu->S, &operand);
        cpu->R = product;
        /* Upper half of full product into S (approximate; full 36-trit
           product would need bigger intermediate; use upper 18 trits). */
        long full = word18_to_long(&cpu->S) * word18_to_long(&operand);
        /* Divide by 3^9 to shift right 9 trits for the "upper" portion. */
        long divisor = 1;
        for (int i = 0; i < 9; i++) divisor *= 3;
        cpu->S = long_to_word18(full / divisor);
        cpu->omega = word18_sign(&cpu->S);
        break;
    }

    case OP_DIV: {
        word18_t operand = setun_mem_read18(cpu, ea);
        long va = word18_to_long(&cpu->S);
        long vb = word18_to_long(&operand);
        if (vb == 0) {
            fprintf(stderr, "setun: division by zero\n");
            cpu->error = 1;
            return -1;
        }
        cpu->S = long_to_word18(va / vb);
        cpu->R = long_to_word18(va % vb);
        cpu->omega = word18_sign(&cpu->S);
        break;
    }

    case OP_NEG: {
        cpu->S = word18_neg(&cpu->S);
        cpu->omega = word18_sign(&cpu->S);
        break;
    }

    case OP_ABS: {
        trit_t sign = word18_sign(&cpu->S);
        if (sign == TRIT_NEG)
            cpu->S = word18_neg(&cpu->S);
        cpu->omega = word18_sign(&cpu->S);
        break;
    }

    case OP_LOADR: {
        cpu->S = cpu->R;
        cpu->omega = word18_sign(&cpu->S);
        break;
    }

    case OP_STORER: {
        cpu->R = cpu->S;
        break;
    }

    case OP_LOADF: {
        word9_t cell = setun_mem_read(cpu, ea);
        cpu->F = cell;
        break;
    }

    case OP_STOREF: {
        setun_mem_write(cpu, ea, &cpu->F);
        break;
    }

    case OP_ADDF: {
        word9_t cell = setun_mem_read(cpu, ea);
        cpu->F = word9_add(&cpu->F, &cell, &overflow);
        break;
    }

    case OP_ADDPROD: {
        /* S := S + (R * mem[ea])  — polynomial evaluation helper */
        word18_t operand = setun_mem_read18(cpu, ea);
        word18_t product = word18_mul(&cpu->R, &operand);
        cpu->S = word18_add(&cpu->S, &product, &overflow);
        cpu->omega = word18_sign(&cpu->S);
        break;
    }

    case OP_JUMP: {
        cpu->P = int_to_word9(ea);
        break;
    }

    case OP_JPOS:   if (cpu->omega == TRIT_POS)  cpu->P = int_to_word9(ea); break;
    case OP_JZERO:  if (cpu->omega == TRIT_ZERO) cpu->P = int_to_word9(ea); break;
    case OP_JNEG:   if (cpu->omega == TRIT_NEG)  cpu->P = int_to_word9(ea); break;
    case OP_JNPOS:  if (cpu->omega != TRIT_POS)  cpu->P = int_to_word9(ea); break;
    case OP_JNZERO: if (cpu->omega != TRIT_ZERO) cpu->P = int_to_word9(ea); break;
    case OP_JNNEG:  if (cpu->omega != TRIT_NEG)  cpu->P = int_to_word9(ea); break;

    case OP_SETOMEGA: {
        cpu->omega = word18_sign(&cpu->S);
        break;
    }

    case OP_NOP: {
        break;
    }

    case OP_HALT: {
        cpu->halted = 1;
        return -1;
    }

    default: {
        fprintf(stderr, "setun: unknown opcode value %d\n", opcode_val);
        cpu->error = 1;
        return -1;
    }
    }

    return 0;
}

void setun_run(setun_t *cpu)
{
    while (!cpu->halted && !cpu->error)
        setun_step(cpu);
}

void setun_dump(const setun_t *cpu)
{
    printf("S     = "); word18_print(&cpu->S);
    printf("  (%ld)\n", word18_to_long(&cpu->S));

    printf("R     = "); word18_print(&cpu->R);
    printf("  (%ld)\n", word18_to_long(&cpu->R));

    printf("F     = "); word9_print(&cpu->F);
    printf("  (%d)\n", word9_to_int(&cpu->F));

    printf("P     = "); word9_print(&cpu->P);
    printf("  (%d)\n", word9_to_int(&cpu->P));

    printf("omega = %+d\n", (int) cpu->omega);
    printf("halted=%d  error=%d\n", cpu->halted, cpu->error);
}
