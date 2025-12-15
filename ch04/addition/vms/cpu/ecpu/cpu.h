#ifndef CPU_H
#define CPU_H

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

// instruction set constants -  bit encoding
#define OP_ADD   0x00  //     ADD R1, R2 -> R1 = R1 + R2
#define OP_SUB   0x01  //     SUB R1, R2 -> R1 = R1 - R2
#define OP_AND   0x02  //     AND R1, R2 -> R1 = R1 & R2
#define OP_OR    0x03  //     OR  R1, R2 -> R1 = R1 | R2
#define OP_XOR   0x04  //     XOR R1, R2 -> R1 = R1 ^ R2
#define OP_NOT   0x05  //     NOT R1     -> R1 = ~R1
#define OP_SHL   0x06  //     SHL R1     -> R1 = R1 << 1
#define OP_SHR   0x07  //     SHR R1     -> R1 = R1 >> 1
#define OP_LOAD  0x08  //  LOAD R1, addr -> R1 = memory[addr]
#define OP_STORE 0x09  // STORE R1, addr -> memory[addr] = R1
#define OP_JMP   0x0A  //     JMP addr   -> PC = addr
#define OP_JZ    0x0B  //     JZ addr    -> if zero flag set, PC = addr
#define OP_JC    0x0C  //     JC addr    -> if carry flag set, PC = addr
#define OP_HALT  0xFF  //     HALT       -> Stop execution

// helpers
#define ENCODE_INSTRUCTION(opcode, reg_a, reg_b) \
    (((opcode) << 8) | ((reg_a) << 6) | ((reg_b) << 4))

#define ENCODE_INSTRUCTION_IMM(opcode, reg_a, immediate) \
    (((opcode) << 8) | ((reg_a) << 6) | (immediate))

// struct and typedef decl
typedef struct {
    bool sum;
    bool carry;
} HalfAdderResult;

typedef struct {
    bool sum;
    bool carry_out;
} FullAdderResult;

typedef struct {
    uint8_t sum;
    bool carry_out;
    bool overflow;
} AdderResult;

typedef struct {
    bool zero;
    bool carry;
    bool overflow;
    bool negative;
} ALUFlags;

typedef struct {
    uint8_t result;
    ALUFlags flags;
} ALUResult;

// decoded instruction structure
typedef struct {
    uint8_t opcode;
    uint8_t reg_a;
    uint8_t reg_b;
    uint8_t immediate;
    uint8_t address;
} DecodedInstruction;

// VM struct
typedef struct {
    uint8_t registers[4];      // Register file
    uint8_t memory[256];       // Memory
    uint8_t pc;                // Program Counter
    uint16_t ir;               // Instruction Register (IR)
    ALUFlags flags;            // Status flags
    bool running;              // CPU state
    
    // Legacy microcode support
    uint8_t current_instruction;
    uint8_t micro_step;
    uint8_t fetched_byte;
    ALUResult alu_result;
    uint8_t memory_data;
} VM;

// microcode struct (legacy compatibility)
typedef struct {
    bool reg_write_enable;
    uint8_t reg_write_select;
    uint8_t reg_read_a_select;
    uint8_t reg_read_b_select;
    bool alu_enable;
    uint8_t alu_operation;
    bool alu_use_immediate;
    uint8_t immediate_value;
    bool mem_read;
    bool mem_write;
    bool mem_use_immediate_addr;
    uint8_t mem_addr_immediate;
    bool pc_increment;
    bool pc_jump;
    bool pc_jump_conditional;
    uint8_t jump_condition;
    uint8_t jump_address;
    bool fetch_next_byte;
    bool end_instruction;
    bool halt_cpu;
    bool use_alu_result;
} ControlSignals;

typedef struct {
    ControlSignals signals;
    const char* description;
} MicroInstruction;

// logic gate functions
bool and_gate(bool a, bool b);
bool or_gate(bool a, bool b);
bool xor_gate(bool a, bool b);
bool not_gate(bool a);
bool nand_gate(bool a, bool b);
bool nor_gate(bool a, bool b);

// adder functions
HalfAdderResult half_adder(bool a, bool b);
FullAdderResult full_adder(bool a, bool b, bool carry_in);
AdderResult ripple_carry_adder_8bit(uint8_t a, uint8_t b, bool carry_in);

// bitwise operation functions
uint8_t bitwise_and_8bit(uint8_t a, uint8_t b);
uint8_t bitwise_or_8bit(uint8_t a, uint8_t b);
uint8_t bitwise_xor_8bit(uint8_t a, uint8_t b);
uint8_t bitwise_not_8bit(uint8_t a);

// ALU function
ALUResult enhanced_alu(uint8_t a, uint8_t b, uint8_t opcode);

// CPU functions
uint8_t mem_read(VM *vm, uint8_t addr);
void mem_write(VM *vm, uint8_t addr, uint8_t value);
DecodedInstruction decode_instruction(uint16_t instruction);
uint16_t cpu_fetch(VM *vm);
void cpu_decode_and_execute(VM *vm);

// VM functions
void init_vm(VM *vm);
void run_vm(VM *vm);

// Legacy compatibility functions
uint8_t fetch(VM *vm);
void execute_microinstruction(VM *vm, const MicroInstruction *micro);
void init_microcode(void);

// Util macros for instruction building
#define BUILD_TWO_REG_INSTR(opcode, ra, rb) \
    do { \
        vm->memory[pc++] = (opcode << 8) & 0xFF; \
        vm->memory[pc++] = ((opcode << 8) >> 8) | (ra << 6) | (rb << 4); \
    } while(0)

#define BUILD_LOAD_STORE_INSTR(opcode, reg, addr) \
    do { \
        vm->memory[pc++] = (opcode << 8) & 0xFF; \
        vm->memory[pc++] = ((opcode << 8) >> 8) | (reg << 6) | (addr); \
    } while(0)

#endif // CPU_H