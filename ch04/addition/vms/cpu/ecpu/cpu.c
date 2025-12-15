#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "cpu.h"


// fundamental logic gates used in higher-level circuits

bool and_gate(bool a, bool b) {
    return a && b;
}

bool or_gate(bool a, bool b) {
    return a || b;
}

bool xor_gate(bool a, bool b) {
    return a != b;
}

bool not_gate(bool a) {
    return !a;
}

bool nand_gate(bool a, bool b) {
    return not_gate(and_gate(a, b));
}

bool nor_gate(bool a, bool b) {
    return not_gate(or_gate(a, b));
}


// adders for binary arithmetic

HalfAdderResult half_adder(bool a, bool b) {
    HalfAdderResult result = {
        .sum = xor_gate(a, b),
        .carry = and_gate(a, b)
    };
    return result;
}

FullAdderResult full_adder(bool a, bool b, bool carry_in) {
    FullAdderResult result;
    HalfAdderResult ha1 = half_adder(a, b);
    HalfAdderResult ha2 = half_adder(ha1.sum, carry_in);
    result.sum = ha2.sum;
    result.carry_out = or_gate(ha1.carry, ha2.carry);
    return result;
}

AdderResult ripple_carry_adder_8bit(uint8_t a, uint8_t b, bool carry_in) {
    AdderResult result = {0};
    bool carry = carry_in;
    uint8_t sum = 0;

    for (int i = 0; i < 8; i++) {
        bool bit_a = (a >> i) & 1;
        bool bit_b = (b >> i) & 1;
        FullAdderResult fa = full_adder(bit_a, bit_b, carry);
        sum |= (fa.sum << i);
        carry = fa.carry_out;
    }

    result.sum = sum;
    result.carry_out = carry;

    // overflow! detection for signed arithmetic
    bool msb_a = (a >> 7) & 1;
    bool msb_b = (b >> 7) & 1;
    bool msb_sum = (sum >> 7) & 1;
    result.overflow = (msb_a && msb_b && !msb_sum) || (!msb_a && !msb_b && msb_sum);

    return result;
}


// 8-bit bitwise operations using logic gates

uint8_t bitwise_and_8bit(uint8_t a, uint8_t b) {
    uint8_t result = 0;
    for (int i = 0; i < 8; i++) {
        bool bit_a = (a >> i) & 1;
        bool bit_b = (b >> i) & 1;
        if (and_gate(bit_a, bit_b)) {
            result |= (1 << i);
        }
    }
    return result;
}

uint8_t bitwise_or_8bit(uint8_t a, uint8_t b) {
    uint8_t result = 0;
    for (int i = 0; i < 8; i++) {
        bool bit_a = (a >> i) & 1;
        bool bit_b = (b >> i) & 1;
        if (or_gate(bit_a, bit_b)) {
            result |= (1 << i);
        }
    }
    return result;
}

uint8_t bitwise_xor_8bit(uint8_t a, uint8_t b) {
    uint8_t result = 0;
    for (int i = 0; i < 8; i++) {
        bool bit_a = (a >> i) & 1;
        bool bit_b = (b >> i) & 1;
        if (xor_gate(bit_a, bit_b)) {
            result |= (1 << i);
        }
    }
    return result;
}

uint8_t bitwise_not_8bit(uint8_t a) {
    uint8_t result = 0;
    for (int i = 0; i < 8; i++) {
        bool bit_a = (a >> i) & 1;
        if (not_gate(bit_a)) {
            result |= (1 << i);
        }
    }
    return result;
}


// ALU, Arithmetic Logic Unit with flag support

ALUResult enhanced_alu(uint8_t a, uint8_t b, uint8_t opcode) {
    ALUResult alu_result = {0};

    switch (opcode) {
        case 0: { // ADD
            AdderResult add_result = ripple_carry_adder_8bit(a, b, false);
            alu_result.result = add_result.sum;
            alu_result.flags.carry = add_result.carry_out;
            alu_result.flags.overflow = add_result.overflow;
            break;
        }
        case 1: { // SUB (A - B = A + (~B + 1))
            uint8_t b_complement = bitwise_not_8bit(b);
            AdderResult sub_result = ripple_carry_adder_8bit(a, b_complement, true);
            alu_result.result = sub_result.sum;
            alu_result.flags.carry = sub_result.carry_out;
            alu_result.flags.overflow = sub_result.overflow;
            break;
        }
        case 2: // AND
            alu_result.result = bitwise_and_8bit(a, b);
            break;
        case 3: // OR
            alu_result.result = bitwise_or_8bit(a, b);
            break;
        case 4: // XOR
            alu_result.result = bitwise_xor_8bit(a, b);
            break;
        case 5: // NOT A
            alu_result.result = bitwise_not_8bit(a);
            break;
        case 6: // SHL A
            alu_result.result = a << 1;
            alu_result.flags.carry = (a & 0x80) != 0;
            break;
        case 7: // SHR A
            alu_result.result = a >> 1;
            alu_result.flags.carry = (a & 0x01) != 0;
            break;
        default:
            alu_result.result = 0;
            break;
    }

    alu_result.flags.zero = (alu_result.result == 0);
    alu_result.flags.negative = (alu_result.result & 0x80) != 0;

    return alu_result;
}


// Memory interface functions
uint8_t mem_read(VM *vm, uint8_t addr) {
    return vm->memory[addr];
}

void mem_write(VM *vm, uint8_t addr, uint8_t value) {
    vm->memory[addr] = value;
}


// Instruction decoding
DecodedInstruction decode_instruction(uint16_t instruction) {
    DecodedInstruction decoded = {0};
    
    // Extract opcode from upper 8 bits
    decoded.opcode = (instruction >> 8) & 0xFF;
    
    // Extract operands based on instruction format
    decoded.reg_a = (instruction >> 6) & 0x3;  // Bits 7-6
    decoded.reg_b = (instruction >> 4) & 0x3;  // Bits 5-4
    decoded.immediate = instruction & 0xFF;    // Lower 8 bits for immediate values
    decoded.address = instruction & 0xFF;      // Lower 8 bits for addresses
    
    return decoded;
}

// Fetch
uint16_t cpu_fetch(VM *vm) {

    // Read 16-bit instruction from memory (little-endian)
    uint16_t instruction = mem_read(vm, vm->pc) | (mem_read(vm, vm->pc + 1) << 8);
    vm->ir = instruction;  // Store in instruction register
    
    // PC update is automatic unless overridden by control flow instructions
    vm->pc += 2;  // 16-bit instructions! are 2 bytes
    
    return instruction;
}

// Control unit
void cpu_decode_and_execute(VM *vm) {
    DecodedInstruction decoded = decode_instruction(vm->ir);
    
    printf("Cycle: PC=%d, IR=0x%04X, Opcode=0x%02X\n", 
           vm->pc - 2, vm->ir, decoded.opcode);
    
    switch (decoded.opcode) {
        case OP_ADD: {
            ALUResult result = enhanced_alu(vm->registers[decoded.reg_a], 
                                          vm->registers[decoded.reg_b], 0);
            vm->registers[decoded.reg_a] = result.result;
            vm->flags = result.flags;
            printf("  ADD R%d, R%d -> R%d = %d\n", 
                   decoded.reg_a, decoded.reg_b, decoded.reg_a, result.result);
            break;
        }
        
        case OP_SUB: {
            ALUResult result = enhanced_alu(vm->registers[decoded.reg_a], 
                                          vm->registers[decoded.reg_b], 1);
            vm->registers[decoded.reg_a] = result.result;
            vm->flags = result.flags;
            printf("  SUB R%d, R%d -> R%d = %d\n", 
                   decoded.reg_a, decoded.reg_b, decoded.reg_a, result.result);
            break;
        }
        
        case OP_AND: {
            ALUResult result = enhanced_alu(vm->registers[decoded.reg_a], 
                                          vm->registers[decoded.reg_b], 2);
            vm->registers[decoded.reg_a] = result.result;
            vm->flags = result.flags;
            break;
        }
        
        case OP_OR: {
            ALUResult result = enhanced_alu(vm->registers[decoded.reg_a], 
                                          vm->registers[decoded.reg_b], 3);
            vm->registers[decoded.reg_a] = result.result;
            vm->flags = result.flags;
            break;
        }
        
        case OP_XOR: {
            ALUResult result = enhanced_alu(vm->registers[decoded.reg_a], 
                                          vm->registers[decoded.reg_b], 4);
            vm->registers[decoded.reg_a] = result.result;
            vm->flags = result.flags;
            break;
        }
        
        case OP_NOT: {
            ALUResult result = enhanced_alu(vm->registers[decoded.reg_a], 0, 5);
            vm->registers[decoded.reg_a] = result.result;
            vm->flags = result.flags;
            break;
        }
        
        case OP_SHL: {
            ALUResult result = enhanced_alu(vm->registers[decoded.reg_a], 0, 6);
            vm->registers[decoded.reg_a] = result.result;
            vm->flags = result.flags;
            break;
        }
        
        case OP_SHR: {
            ALUResult result = enhanced_alu(vm->registers[decoded.reg_a], 0, 7);
            vm->registers[decoded.reg_a] = result.result;
            vm->flags = result.flags;
            break;
        }
        
        case OP_LOAD: {
            uint8_t value = mem_read(vm, decoded.address);
            vm->registers[decoded.reg_a] = value;
            printf("  LOAD R%d, [%d] -> R%d = %d\n", 
                   decoded.reg_a, decoded.address, decoded.reg_a, value);
            break;
        }
        
        case OP_STORE: {
            mem_write(vm, decoded.address, vm->registers[decoded.reg_a]);
            printf("  STORE R%d, [%d] -> memory[%d] = %d\n", 
                   decoded.reg_a, decoded.address, decoded.address, vm->registers[decoded.reg_a]);
            break;
        }
        
        case OP_JMP: {
            // PC update is overridden for jumps, patching the instruction pointer directly
            // This is a direct jump, so we set the PC to the address
            vm->pc = decoded.address;
            printf("  JMP %d -> PC = %d\n", decoded.address, vm->pc);
            break;
        }
        
        case OP_JZ: {
            if (vm->flags.zero) {
                vm->pc = decoded.address;
                printf("  JZ %d -> PC = %d (taken)\n", decoded.address, vm->pc);
            } else {
                printf("  JZ %d -> not taken\n", decoded.address);
            }
            break;
        }
        
        case OP_JC: {
            if (vm->flags.carry) {
                vm->pc = decoded.address;
                printf("  JC %d -> PC = %d (taken)\n", decoded.address, vm->pc);
            } else {
                printf("  JC %d -> not taken\n", decoded.address);
            }
            break;
        }
        
        case OP_HALT: {
            vm->running = false;
            printf("  HALT -> CPU stopped\n");
            break;
        }
        
        default: {
            printf("  Unknown opcode: 0x%02X\n", decoded.opcode);
            break;
        }
    }
}

// Simplified VM init / reset ..
void init_vm(VM *vm) {
    memset(vm->registers, 0, sizeof(vm->registers));
    memset(vm->memory, 0, sizeof(vm->memory));
    vm->pc = 0;
    vm->ir = 0;  // Init instruction register
    vm->flags = (ALUFlags){0};
    vm->running = true;
}

// Main CPU  - classic fetch-decode-execute cycle
void run_vm(VM *vm) {
    int cycle = 0;
    printf("Starting CPU execution ..\n");
    
    while (vm->running && cycle < 1000) {
        printf("\n--- Cycle %d ---\n", cycle);
        printf("Before: PC=%d, R0=%d, R1=%d, R2=%d, R3=%d\n",
               vm->pc, vm->registers[0], vm->registers[1], vm->registers[2], vm->registers[3]);
        
        // FETCH: Get next instruction from memory
        cpu_fetch(vm);
        
        // DECODE & EXECUTE: Interpret and carry out the instruction
        cpu_decode_and_execute(vm);
        
        printf("After:  PC=%d, R0=%d, R1=%d, R2=%d, R3=%d, Flags(Z=%d,C=%d,O=%d,N=%d)\n",
               vm->pc, vm->registers[0], vm->registers[1], vm->registers[2], vm->registers[3],
               vm->flags.zero, vm->flags.carry, vm->flags.overflow, vm->flags.negative);
        
        cycle++;
    }
    
    if (cycle >= 1000) {
        printf("\nExecution stopped: Cycle limit reached\n");
    } else {
        printf("\nExecution completed: CPU halted\n");
    }
}

// Legacy compatibility functions for existing microcode system
uint8_t fetch(VM *vm) {
    return mem_read(vm, vm->pc++);
}

// Keep the existing microcode system for backward compatibility
#define MAX_MICRO_STEPS 8
#define NUM_OPCODES 16

MicroInstruction microcode_rom[NUM_OPCODES][MAX_MICRO_STEPS];
static bool microcode_initialized = false;

void init_microcode(void) {
    if (microcode_initialized) return;
    // .. (keep existing microcode init) ..
    microcode_initialized = true;
}

void execute_microinstruction(VM *vm, const MicroInstruction *micro) {
    // .. (keep existing microcode execution) ..
}
