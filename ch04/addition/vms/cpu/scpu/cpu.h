#ifndef CPU_H
#define CPU_H

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

// instruction set constants
#define OP_ADD   0x00  // ADD R1, R2 -> R1 = R1 + R2
#define OP_SUB   0x01  // SUB R1, R2 -> R1 = R1 - R2
#define OP_AND   0x02  // AND R1, R2 -> R1 = R1 & R2
#define OP_OR    0x03  // OR  R1, R2 -> R1 = R1 | R2
#define OP_XOR   0x04  // XOR R1, R2 -> R1 = R1 ^ R2
#define OP_NOT   0x05  // NOT R1     -> R1 = ~R1
#define OP_SHL   0x06  // SHL R1     -> R1 = R1 << 1
#define OP_SHR   0x07  // SHR R1     -> R1 = R1 >> 1
#define OP_LOAD  0x08  // LOAD R1, addr -> R1 = memory[addr]
#define OP_STORE 0x09  // STORE R1, addr -> memory[addr] = R1
#define OP_JMP   0x0A  // JMP addr   -> PC = addr
#define OP_JZ    0x0B  // JZ addr    -> if zero flag set, PC = addr
#define OP_JC    0x0C  // JC addr    -> if carry flag set, PC = addr
#define OP_HALT  0xFF  // HALT       -> Stop execution

// struct and typedef declarations
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

typedef struct {
    uint8_t registers[4];
    uint8_t memory[256];
    uint8_t pc;
    ALUFlags flags;
    bool running;
    uint8_t current_instruction;
    uint8_t micro_step;
    uint8_t fetched_byte;
    ALUResult alu_result;
    uint8_t memory_data;
} VM;

// Fwd decl
bool and_gate(bool a, bool b);
bool or_gate(bool a, bool b);
bool xor_gate(bool a, bool b);
bool not_gate(bool a);
bool nand_gate(bool a, bool b);
bool nor_gate(bool a, bool b);
HalfAdderResult half_adder(bool a, bool b);
FullAdderResult full_adder(bool a, bool b, bool carry_in);
AdderResult ripple_carry_adder_8bit(uint8_t a, uint8_t b, bool carry_in);
uint8_t bitwise_and_8bit(uint8_t a, uint8_t b);
uint8_t bitwise_or_8bit(uint8_t a, uint8_t b);
uint8_t bitwise_xor_8bit(uint8_t a, uint8_t b);
uint8_t bitwise_not_8bit(uint8_t a);
ALUResult enhanced_alu(uint8_t a, uint8_t b, uint8_t opcode);
void init_vm(VM *vm);
uint8_t fetch(VM *vm);
void execute_microinstruction(VM *vm, const MicroInstruction *micro);
void run_vm(VM *vm);

#endif // CPU_H