#ifndef SAP_VM_H
#define SAP_VM_H

#include <stdint.h>
#include <stdbool.h>

#define OPCODE_SHIFT 12
#define ADDR_MODE_SHIFT 10
#define OPERAND_MASK 0x03FF
#define OPCODE_MASK 0xF000
#define ADDR_MODE_MASK 0x0C00

typedef enum {
    OP_NOP = 0, OP_LDA, OP_STA, OP_ADD, OP_SUB, OP_MUL, OP_DIV, OP_AND,
    OP_OR, OP_XOR, OP_CMP, OP_JMP, OP_JZ, OP_JNZ, OP_JSR, OP_RTS
} opcode_t;

typedef enum {
    ADDR_IMMEDIATE, ADDR_DIRECT, ADDR_INDIRECT, ADDR_INDEXED
} addressing_mode_t;

typedef enum {
    VM_STOPPED, VM_RUNNING, VM_HALTED, VM_ERROR, VM_BREAKPOINT
} vm_state_t;

typedef enum {
    RESULT_OK, RESULT_ERROR, RESULT_HALT, RESULT_BREAKPOINT
} result_t;

typedef struct {
    bool zero;
    bool negative;
    bool carry;
    bool overflow;
} cpu_flags_t;

typedef struct {
    uint16_t pc;
    uint16_t sp;
    int16_t accumulator;
    uint16_t x_reg;
    uint16_t ir;
    cpu_flags_t flags;
} cpu_t;

typedef struct {
    uint16_t address;
    bool enabled;
    uint32_t hit_count;
    char condition[64];
} breakpoint_t;

typedef struct {
    cpu_t cpu;
    int16_t memory[1024];
    vm_state_t state;
    uint64_t cycle_count;
    bool debug_enabled;
    bool trace_enabled;
    uint16_t last_pc;
    char last_error[256];
    uint16_t error_address;
    breakpoint_t breakpoints[32];
    int breakpoint_count;
} sap_vm_t;

// Core VM functions
void vm_init(sap_vm_t *vm);
void vm_reset(sap_vm_t *vm);
void vm_destroy(sap_vm_t *vm);
bool vm_is_valid_address(uint16_t address);
int16_t vm_read_memory(sap_vm_t *vm, uint16_t address);
result_t vm_write_memory(sap_vm_t *vm, uint16_t address, int16_t value);
result_t vm_set_error(sap_vm_t *vm, const char *format, ...);
result_t vm_step(sap_vm_t *vm);
result_t vm_run(sap_vm_t *vm, uint64_t max_cycles);
result_t vm_run_until_halt(sap_vm_t *vm);
uint16_t vm_encode_instruction(opcode_t opcode, addressing_mode_t mode, uint16_t operand);
void vm_decode_instruction(uint16_t instruction, opcode_t *opcode, 
                         addressing_mode_t *mode, uint16_t *operand);
const char *opcode_to_string(opcode_t opcode);
const char *addressing_mode_to_string(addressing_mode_t mode);
const char *vm_state_to_string(vm_state_t state);
void vm_print_state(sap_vm_t *vm);
void vm_print_memory(sap_vm_t *vm, uint16_t start, uint16_t end);
void vm_print_disassembly(sap_vm_t *vm, uint16_t start, uint16_t count);

// Debug support functions
result_t vm_add_breakpoint(sap_vm_t *vm, uint16_t address);
result_t vm_remove_breakpoint(sap_vm_t *vm, uint16_t address);
void vm_list_breakpoints(sap_vm_t *vm);
bool vm_check_breakpoint(sap_vm_t *vm, uint16_t address);
result_t vm_load_program(sap_vm_t *vm, const char *filename);
result_t vm_save_program(sap_vm_t *vm, const char *filename, 
                       uint16_t start_addr, uint16_t end_addr);
void vm_dump_state(sap_vm_t *vm, const char *filename);

#endif // SAP_VM_H

