/*
 * fuzzmut.c
 *   gcc -std=c11 -O2 fuzzmut.c -o vm_test
 *   -fsanitize=address,undefined
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

/* Opcodes */
enum {
    OP_PUSH = 0x01,
    OP_ADD  = 0x02,
    OP_SUB  = 0x03,
    OP_MUL  = 0x04,
    OP_DIV  = 0x05,
    OP_DUP  = 0x06,
    OP_POP  = 0x07,
    OP_HALT = 0x08,
    OP_PRINT= 0x09,
    OP_JZ   = 0x0A,
    OP_JNZ  = 0x0B,
    OP_INVALID = 0xFF
};

/* VM result codes */
enum {
    VM_OK = 0,
    VM_ERR_STACK_UNDERFLOW = 1,
    VM_ERR_STACK_OVERFLOW  = 2,
    VM_ERR_DIV_ZERO        = 3,
    VM_ERR_INVALID_OPCODE  = 4,
    VM_ERR_PC_OOB          = 5,
    VM_ERR_TIMEOUT         = 6
};

#define STACK_MAX 256
#define PROGRAM_MAX 1024
#define PRINT_BUF_MAX 64
#define STEP_LIMIT 10000

typedef struct {
    int32_t stack[STACK_MAX];
    int sp;
    uint8_t program[PROGRAM_MAX];
    size_t prog_len;
    int outputs[PRINT_BUF_MAX];
    int out_count;
} VM;

void vm_init(VM *vm) {
    vm->sp = 0;
    vm->prog_len = 0;
    vm->out_count = 0;
    memset(vm->program, 0, PROGRAM_MAX);
}

int vm_push(VM *vm, int32_t v) {
    if (vm->sp >= STACK_MAX) return VM_ERR_STACK_OVERFLOW;
    vm->stack[vm->sp++] = v;
    return VM_OK;
}

int vm_pop(VM *vm, int32_t *out) {
    if (vm->sp <= 0) return VM_ERR_STACK_UNDERFLOW;
    *out = vm->stack[--vm->sp];
    return VM_OK;
}

/* read 32-bit little-endian immediate from program starting at pc; require pc+3 < len */
static int32_t read_i32(const uint8_t *prog, size_t len, size_t pc) {
    if (pc + 3 >= len) return 0;
    int32_t v = (int32_t)(
        (uint32_t)prog[pc] |
        (uint32_t)prog[pc+1] << 8 |
        (uint32_t)prog[pc+2] << 16 |
        (uint32_t)prog[pc+3] << 24);
    return v;
}

int vm_run(VM *vm) {
    size_t pc = 0;
    int steps = 0;
    while (pc < vm->prog_len) {
        if (++steps > STEP_LIMIT) return VM_ERR_TIMEOUT;
        uint8_t op = vm->program[pc++];
        int32_t a, b;
        int rc;
        switch (op) {
        case OP_PUSH:
            if (pc + 3 >= vm->prog_len) return VM_ERR_PC_OOB;
            {
                int32_t imm = read_i32(vm->program, vm->prog_len, pc);
                pc += 4;
                rc = vm_push(vm, imm);
                if (rc != VM_OK) return rc;
            }
            break;
        case OP_ADD:
            rc = vm_pop(vm, &b); if (rc) return rc;
            rc = vm_pop(vm, &a); if (rc) return rc;
            if (vm_push(vm, a + b) != VM_OK) return VM_ERR_STACK_OVERFLOW;
            break;
        case OP_SUB:
            rc = vm_pop(vm, &b); if (rc) return rc;
            rc = vm_pop(vm, &a); if (rc) return rc;
            if (vm_push(vm, a - b) != VM_OK) return VM_ERR_STACK_OVERFLOW;
            break;
        case OP_MUL:
            rc = vm_pop(vm, &b); if (rc) return rc;
            rc = vm_pop(vm, &a); if (rc) return rc;
            if (vm_push(vm, a * b) != VM_OK) return VM_ERR_STACK_OVERFLOW;
            break;
        case OP_DIV:
            rc = vm_pop(vm, &b); if (rc) return rc;
            rc = vm_pop(vm, &a); if (rc) return rc;
            if (b == 0) return VM_ERR_DIV_ZERO;
            if (vm_push(vm, a / b) != VM_OK) return VM_ERR_STACK_OVERFLOW;
            break;
        case OP_DUP:
            if (vm->sp <= 0) return VM_ERR_STACK_UNDERFLOW;
            if (vm->sp >= STACK_MAX) return VM_ERR_STACK_OVERFLOW;
            vm->stack[vm->sp] = vm->stack[vm->sp - 1];
            vm->sp++;
            break;
        case OP_POP:
            if (vm->sp <= 0) return VM_ERR_STACK_UNDERFLOW;
            vm->sp--;
            break;
        case OP_PRINT:
            rc = vm_pop(vm, &a); if (rc) return rc;
            if (vm->out_count < PRINT_BUF_MAX) vm->outputs[vm->out_count++] = a;
            break;
        case OP_JZ:
            if (pc >= vm->prog_len) return VM_ERR_PC_OOB;
            {
                uint8_t offset = vm->program[pc++];
                rc = vm_pop(vm, &a); if (rc) return rc;
                if (a == 0) {
                    size_t newpc = pc + offset;
                    if (newpc >= vm->prog_len) return VM_ERR_PC_OOB;
                    pc = newpc;
                }
            }
            break;
        case OP_JNZ:
            if (pc >= vm->prog_len) return VM_ERR_PC_OOB;
            {
                uint8_t offset = vm->program[pc++];
                rc = vm_pop(vm, &a); if (rc) return rc;
                if (a != 0) {
                    size_t newpc = pc + offset;
                    if (newpc >= vm->prog_len) return VM_ERR_PC_OOB;
                    pc = newpc;
                }
            }
            break;
        case OP_HALT:
            return VM_OK;
        default:
            return VM_ERR_INVALID_OPCODE;
        }
    }
    return VM_ERR_PC_OOB;
}

/* helpers for random generation */
static int rnd_int(int a, int b) { return a + rand() % (b - a + 1); }

void vm_emit_push(VM *vm, int32_t val) {
    if (vm->prog_len + 5 > PROGRAM_MAX) return;
    vm->program[vm->prog_len++] = OP_PUSH;
    vm->program[vm->prog_len++] = (uint8_t)(val & 0xFF);
    vm->program[vm->prog_len++] = (uint8_t)((val >> 8) & 0xFF);
    vm->program[vm->prog_len++] = (uint8_t)((val >> 16) & 0xFF);
    vm->program[vm->prog_len++] = (uint8_t)((val >> 24) & 0xFF);
}

void vm_random_program(VM *vm, size_t max_len) {
    vm->prog_len = 0;
    size_t len = rnd_int(1, (int)max_len);
    while (vm->prog_len < len) {
        int choice = rnd_int(0, 9);
        if (choice == 0 && vm->prog_len + 5 <= len) {
            vm_emit_push(vm, rnd_int(-100,100));
        } else {
            uint8_t ops[] = {OP_ADD,OP_SUB,OP_MUL,OP_DIV,OP_DUP,OP_POP,OP_PRINT,OP_HALT,0xAA,0xBB};
            vm->program[vm->prog_len++] = ops[rand() % (sizeof(ops)/1)];
        }
    }
    /* ensure HALT exists somewhere */
    if (vm->prog_len < PROGRAM_MAX) vm->program[vm->prog_len++] = OP_HALT;
}

/* mutate a program in-place (simple mutations) */
void mutate_program(const VM *src, VM *dst) {
    memcpy(dst->program, src->program, src->prog_len);
    dst->prog_len = src->prog_len;
    int op = rand() % 4;
    if (op == 0 && dst->prog_len > 0) {
        /* flip a random byte */
        size_t i = rand() % dst->prog_len;
        dst->program[i] ^= (uint8_t)(1 << (rand() % 8));
    } else if (op == 1) {
        /* replace a byte with a random opcode */
        size_t i = rand() % dst->prog_len;
        uint8_t random_ops[] = {OP_PUSH, OP_ADD, OP_SUB, OP_MUL, OP_DIV, OP_DUP, OP_POP, OP_PRINT, OP_JZ, OP_JNZ, OP_HALT, 0xAB, 0xCD};
        dst->program[i] = random_ops[rand() % (sizeof(random_ops)/1)];
    } else if (op == 2 && dst->prog_len + 1 < PROGRAM_MAX) {
        /* insert a random byte */
        size_t i = rand() % (dst->prog_len + 1);
        memmove(dst->program + i + 1, dst->program + i, dst->prog_len - i);
        dst->program[i] = (uint8_t)(rand() & 0xFF);
        dst->prog_len++;
    } else if (op == 3 && dst->prog_len > 1) {
        /* delete a byte */
        size_t i = rand() % dst->prog_len;
        memmove(dst->program + i, dst->program + i + 1, dst->prog_len - i - 1);
        dst->prog_len--;
    }
    /* ensure HALT at end */
    if (dst->prog_len < PROGRAM_MAX) dst->program[dst->prog_len-1] = OP_HALT;
}

/* Run a program and produce a textual summary (return code + outputs) */
void run_and_report(const VM *prog, int *out_rc, int *out_count, int *outputs) {
    VM vm;
    vm_init(&vm);
    memcpy(vm.program, prog->program, prog->prog_len);
    vm.prog_len = prog->prog_len;
    int rc = vm_run(&vm);
    *out_rc = rc;
    *out_count = vm.out_count;
    for (int i=0;i<vm.out_count && i<PRINT_BUF_MAX;i++) outputs[i] = vm.outputs[i];
}

/* simple pretty print of program bytes */
void print_program_hex(const VM *p) {
    for (size_t i=0;i<p->prog_len;i++) {
        printf("%02X ", p->program[i]);
    }
    printf("\n");
}

int main(void) {
    srand((unsigned)time(NULL));

    printf("Tiny VM fuzz + mutation test (C)\n");

    /* --- Example seed program: compute (3 + 4) * 5 and print result --- */
    VM seed;
    vm_init(&seed);
    vm_emit_push(&seed, 3);
    vm_emit_push(&seed, 4);
    seed.program[seed.prog_len++] = OP_ADD;
    vm_emit_push(&seed, 5);
    seed.program[seed.prog_len++] = OP_MUL;
    seed.program[seed.prog_len++] = OP_PRINT;
    seed.program[seed.prog_len++] = OP_HALT;

    printf("Seed program (hex): ");
    print_program_hex(&seed);

    int seed_rc; int seed_outc; int seed_out[PRINT_BUF_MAX];
    run_and_report(&seed, &seed_rc, &seed_outc, seed_out);
    printf("Seed run -> rc=%d outc=%d", seed_rc, seed_outc);
    if (seed_outc>0) printf(" output=%d", seed_out[0]);
    printf("\n\n");

    /* --- Mutation testing: create N mutated variants and check differences --- */
    const int MUTATIONS = 200;
    int detected = 0;
    for (int i=0;i<MUTATIONS;i++) {
        VM m;
        vm_init(&m);
        mutate_program(&seed, &m);
        int rc; int oc; int out[PRINT_BUF_MAX];
        run_and_report(&m, &rc, &oc, out);
        /* We consider the mutation 'interesting' if rc != seed_rc or outputs differ */
        int outputs_differ = (oc != seed_outc) || (oc>0 && seed_outc>0 && out[0] != seed_out[0]);
        if (rc != seed_rc || outputs_differ) {
            detected++;
            printf("Mutation %3d detected: rc=%d oc=%d (seed rc=%d oc=%d)\n", i, rc, oc, seed_rc, seed_outc);
            printf(" mutated hex: ");
            print_program_hex(&m);
            if (oc>0) printf(" mutated output[0]=%d\n", out[0]);
        }
    }
    printf("Mutation testing: %d/%d mutations detected differences\n\n", detected, MUTATIONS);

    /* --- Fuzzing: run random programs and count crashes/timeouts --- */
    const int RUNS = 1000;
    int crashes = 0, timeouts = 0, invalid = 0, ok = 0;
    for (int i=0;i<RUNS;i++) {
        VM p;
        vm_init(&p);
        vm_random_program(&p, 64);
        int rc; int oc; int out[PRINT_BUF_MAX];
        run_and_report(&p, &rc, &oc, out);
        if (rc == VM_OK) ok++;
        else if (rc == VM_ERR_TIMEOUT) timeouts++;
        else if (rc == VM_ERR_INVALID_OPCODE || rc == VM_ERR_PC_OOB) invalid++;
        else crashes++;
    }
    printf("Fuzzing summary (runs=%d): OK=%d INVALID=%d TIMEOUT=%d OTHER_CRASHES=%d\n", RUNS, ok, invalid, timeouts, crashes);
    printf("Done.\n");
    return 0;
}

