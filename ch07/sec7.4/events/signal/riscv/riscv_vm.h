/*
 * RISC-V RV32IM Virtual Machine - Header
 * ANSI C implementation
 */

#ifndef RISCV_VM_H
#define RISCV_VM_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/* Configuration */
#define DEFAULT_MEM_SIZE 65536
#define NUM_REGISTERS 32
#define MAX_OUTPUT_LEN 4096

/* Instruction types */
typedef enum {
    /* R-type */
    OP_ADD, OP_SUB, OP_XOR, OP_OR, OP_AND,
    OP_SLL, OP_SRL, OP_SRA, OP_SLT, OP_SLTU,
    /* M extension */
    OP_MUL, OP_MULH, OP_MULHSU, OP_MULHU,
    OP_DIV, OP_DIVU, OP_REM, OP_REMU,
    /* I-type arithmetic */
    OP_ADDI, OP_XORI, OP_ORI, OP_ANDI,
    OP_SLTI, OP_SLTIU,
    OP_SLLI, OP_SRLI, OP_SRAI,
    /* Load */
    OP_LB, OP_LH, OP_LW, OP_LBU, OP_LHU,
    /* Store */
    OP_SB, OP_SH, OP_SW,
    /* Branch */
    OP_BEQ, OP_BNE, OP_BLT, OP_BGE, OP_BLTU, OP_BGEU,
    /* Jump */
    OP_JAL, OP_JALR,
    /* Upper immediate */
    OP_LUI, OP_AUIPC,
    /* System */
    OP_ECALL, OP_EBREAK,
    OP_UNKNOWN
} opcode_t;

/* Decoded instruction */
typedef struct {
    opcode_t opcode;
    uint8_t rd;
    uint8_t rs1;
    uint8_t rs2;
    int32_t imm;
    uint8_t funct3;
    uint8_t funct7;
} instruction_t;

/* VM state */
typedef struct {
    uint32_t regs[NUM_REGISTERS];
    uint32_t pc;
    uint8_t *memory;
    size_t mem_size;
    int running;
    int debug;
    int trace;
    unsigned long instruction_count;
    char output[MAX_OUTPUT_LEN];
    size_t output_len;
    
    /* Interrupt handling hooks (set to NULL if not used) */
    int (*interrupt_check)(void *user_data);
    void (*interrupt_handler)(void *user_data, int interrupt_num);
    void *interrupt_user_data;
} riscv_vm_t;

/* ABI register names */
extern const char *reg_names[NUM_REGISTERS];

/* Function prototypes */
riscv_vm_t *vm_create(size_t mem_size, int debug, int trace);
void vm_destroy(riscv_vm_t *vm);
void vm_reset(riscv_vm_t *vm);
int vm_load_program(riscv_vm_t *vm, const char *filename);
void vm_execute(riscv_vm_t *vm);
void vm_step(riscv_vm_t *vm);

/* Helper functions */
int32_t sign_extend(int32_t val, int bits);
uint32_t read_mem(riscv_vm_t *vm, uint32_t addr, int size, int is_signed);
void write_mem(riscv_vm_t *vm, uint32_t addr, uint32_t val, int size);

/* Decode and execute */
instruction_t decode(uint32_t word);
void execute(riscv_vm_t *vm, instruction_t *instr);
void handle_syscall(riscv_vm_t *vm);

/* Debug functions */
void print_regs(riscv_vm_t *vm);
void dump_memory(riscv_vm_t *vm, uint32_t start, uint32_t length);
const char *opcode_to_string(opcode_t op);

/* Interrupt support */
void vm_set_interrupt_handler(riscv_vm_t *vm,
                               int (*check_fn)(void *),
                               void (*handler_fn)(void *, int),
                               void *user_data);

#endif /* RISCV_VM_H */
