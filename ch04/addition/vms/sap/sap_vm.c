#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <ctype.h>
#include "sap_vm.h"
#include "sap_vm_config.h"

void vm_init(sap_vm_t *vm) {
    memset(vm, 0, sizeof(sap_vm_t));
    vm->cpu.sp = STACK_TOP;
    vm->state = VM_STOPPED;
    vm->debug_enabled = true;
    vm->trace_enabled = false;
}

void vm_reset(sap_vm_t *vm) {
    vm->cpu.accumulator = 0;
    vm->cpu.pc = PROGRAM_START;
    vm->cpu.sp = STACK_TOP;
    vm->cpu.x_reg = 0;
    vm->cpu.ir = 0;
    memset(&vm->cpu.flags, 0, sizeof(cpu_flags_t));
    memset(vm->memory, 0, sizeof(int16_t) * MEMORY_SIZE);
    vm->state = VM_STOPPED;
    vm->cycle_count = 0;
    vm->last_pc = 0;
    vm->last_error[0] = '\0';
    vm->error_address = 0;
    if (vm->debug_enabled) {
        printf("VM reset to initial state, memory cleared\n");
    }
}

void vm_destroy(sap_vm_t *vm) {
    vm_init(vm);
}

bool vm_is_valid_address(uint16_t address) {
    return address < MEMORY_SIZE;
}

int16_t vm_read_memory(sap_vm_t *vm, uint16_t address) {
    if (!vm_is_valid_address(address)) {
        vm_set_error(vm, "Invalid read from address 0x%04X", address);
        return 0;
    }
    return vm->memory[address];
}

result_t vm_write_memory(sap_vm_t *vm, uint16_t address, int16_t value) {
    if (!vm_is_valid_address(address)) {
        return vm_set_error(vm, "Invalid write to address 0x%04X", address);
    }
    vm->memory[address] = value;
    return RESULT_OK;
}

result_t vm_set_error(sap_vm_t *vm, const char *format, ...) {
    va_list args;
    va_start(args, format);
    vsnprintf(vm->last_error, sizeof(vm->last_error), format, args);
    va_end(args);
    vm->error_address = vm->cpu.pc;
    vm->state = VM_ERROR;
    if (vm->debug_enabled) {
        printf("VM Error at PC=0x%04X: %s\n", vm->error_address, vm->last_error);
    }
    return RESULT_ERROR;
}

static void update_flags(sap_vm_t *vm, int32_t result) {
    vm->cpu.flags.zero = (result == 0);
    vm->cpu.flags.negative = (result < 0);
    vm->cpu.flags.carry = (result > 32767 || result < -32768);
    vm->cpu.flags.overflow = vm->cpu.flags.carry;
}

static result_t resolve_operand(sap_vm_t *vm, addressing_mode_t mode, 
                              uint16_t operand, int16_t *value) {
    switch (mode) {
        case ADDR_IMMEDIATE:
            // Sign extend 10-bit immediate value
            *value = (operand & 0x200) ? (operand | 0xFC00) : operand;
            break;
        case ADDR_DIRECT:
            if (!vm_is_valid_address(operand)) {
                return vm_set_error(vm, "Invalid direct address 0x%04X", operand);
            }
            *value = vm_read_memory(vm, operand);
            break;
        case ADDR_INDIRECT:
            if (!vm_is_valid_address(operand)) {
                return vm_set_error(vm, "Invalid indirect address 0x%04X", operand);
            }
            {
                uint16_t addr = vm_read_memory(vm, operand);
                if (!vm_is_valid_address(addr)) {
                    return vm_set_error(vm, "Invalid indirect target address 0x%04X", addr);
                }
                *value = vm_read_memory(vm, addr);
            }
            break;
        case ADDR_INDEXED:
            {
                uint16_t addr = operand + vm->cpu.x_reg;
                if (!vm_is_valid_address(addr)) {
                    return vm_set_error(vm, "Invalid indexed address 0x%04X", addr);
                }
                *value = vm_read_memory(vm, addr);
            }
            break;
        default:
            return vm_set_error(vm, "Invalid addressing mode %d", mode);
    }
    return (vm->state == VM_ERROR) ? RESULT_ERROR : RESULT_OK;
}

static result_t store_operand(sap_vm_t *vm, addressing_mode_t mode, 
                            uint16_t operand, int16_t value) {
    uint16_t addr;
    
    switch (mode) {
        case ADDR_IMMEDIATE:
            return vm_set_error(vm, "Cannot store to immediate value");
            
        case ADDR_DIRECT:
            if (!vm_is_valid_address(operand)) {
                return vm_set_error(vm, "Invalid direct store address 0x%04X", operand);
            }
            return vm_write_memory(vm, operand, value);
            
        case ADDR_INDIRECT:
            if (!vm_is_valid_address(operand)) {
                return vm_set_error(vm, "Invalid indirect store address 0x%04X", operand);
            }
            addr = vm_read_memory(vm, operand);
            if (!vm_is_valid_address(addr)) {
                return vm_set_error(vm, "Invalid indirect target store address 0x%04X", addr);
            }
            return vm_write_memory(vm, addr, value);
            
        case ADDR_INDEXED:
            addr = operand + vm->cpu.x_reg;
            if (!vm_is_valid_address(addr)) {
                return vm_set_error(vm, "Invalid indexed store address 0x%04X", addr);
            }
            return vm_write_memory(vm, addr, value);
            
        default:
            return vm_set_error(vm, "Invalid addressing mode for store %d", mode);
    }
}

result_t vm_step(sap_vm_t *vm) {
    if (vm->state == VM_HALTED || vm->state == VM_ERROR) {
        return vm->state == VM_HALTED ? RESULT_HALT : RESULT_ERROR;
    }
    
    if (vm_check_breakpoint(vm, vm->cpu.pc)) {
        vm->state = VM_BREAKPOINT;
        return RESULT_BREAKPOINT;
    }
    
    vm->last_pc = vm->cpu.pc;
    
    if (!vm_is_valid_address(vm->cpu.pc)) {
        return vm_set_error(vm, "PC out of bounds: 0x%04X", vm->cpu.pc);
    }
    
    vm->cpu.ir = vm->memory[vm->cpu.pc++];
    vm->cycle_count++;
    
    opcode_t opcode;
    addressing_mode_t mode;
    uint16_t operand;
    vm_decode_instruction(vm->cpu.ir, &opcode, &mode, &operand);
    
    if (vm->trace_enabled) {
        printf("PC:%04X IR:%04X %s ", vm->last_pc, vm->cpu.ir, opcode_to_string(opcode));
        if (opcode != OP_NOP && opcode != OP_RTS) {
            printf("%s%d", addressing_mode_to_string(mode), operand);
        }
        printf(" ACC:%d X:%d SP:%04X\n", vm->cpu.accumulator, vm->cpu.x_reg, vm->cpu.sp);
    }
    
    int16_t operand_value;
    int32_t result;
    
    switch (opcode) {
        case OP_NOP:
            break;
            
        case OP_LDA:
            if (resolve_operand(vm, mode, operand, &operand_value) != RESULT_OK) {
                return RESULT_ERROR;
            }
            vm->cpu.accumulator = operand_value;
            update_flags(vm, vm->cpu.accumulator);
            break;
            
        case OP_STA:
            if (store_operand(vm, mode, operand, vm->cpu.accumulator) != RESULT_OK) {
                return RESULT_ERROR;
            }
            break;
            
        case OP_ADD:
            if (resolve_operand(vm, mode, operand, &operand_value) != RESULT_OK) {
                return RESULT_ERROR;
            }
            result = (int32_t)vm->cpu.accumulator + operand_value;
            vm->cpu.accumulator = (int16_t)result;
            update_flags(vm, result);
            break;
            
        case OP_SUB:
            if (resolve_operand(vm, mode, operand, &operand_value) != RESULT_OK) {
                return RESULT_ERROR;
            }
            result = (int32_t)vm->cpu.accumulator - operand_value;
            vm->cpu.accumulator = (int16_t)result;
            update_flags(vm, result);
            break;
            
        case OP_MUL:
            if (resolve_operand(vm, mode, operand, &operand_value) != RESULT_OK) {
                return RESULT_ERROR;
            }
            result = (int32_t)vm->cpu.accumulator * operand_value;
            vm->cpu.accumulator = (int16_t)result;
            update_flags(vm, result);
            break;
            
        case OP_DIV:
            if (resolve_operand(vm, mode, operand, &operand_value) != RESULT_OK) {
                return RESULT_ERROR;
            }
            if (operand_value == 0) {
                return vm_set_error(vm, "Division by zero");
            }
            result = (int32_t)vm->cpu.accumulator / operand_value;
            vm->cpu.accumulator = (int16_t)result;
            update_flags(vm, result);
            break;
            
        case OP_AND:
            if (resolve_operand(vm, mode, operand, &operand_value) != RESULT_OK) {
                return RESULT_ERROR;
            }
            vm->cpu.accumulator &= operand_value;
            update_flags(vm, vm->cpu.accumulator);
            break;
            
        case OP_OR:
            if (resolve_operand(vm, mode, operand, &operand_value) != RESULT_OK) {
                return RESULT_ERROR;
            }
            vm->cpu.accumulator |= operand_value;
            update_flags(vm, vm->cpu.accumulator);
            break;
            
        case OP_XOR:
            if (resolve_operand(vm, mode, operand, &operand_value) != RESULT_OK) {
                return RESULT_ERROR;
            }
            vm->cpu.accumulator ^= operand_value;
            update_flags(vm, vm->cpu.accumulator);
            break;
            
        case OP_CMP:
            if (resolve_operand(vm, mode, operand, &operand_value) != RESULT_OK) {
                return RESULT_ERROR;
            }
            result = (int32_t)vm->cpu.accumulator - operand_value;
            update_flags(vm, result);
            break;
            
        case OP_JMP:
            if (!vm_is_valid_address(operand)) {
                return vm_set_error(vm, "Invalid jump address 0x%04X", operand);
            }
            vm->cpu.pc = operand;
            break;
            
        case OP_JZ:
            if (vm->cpu.flags.zero) {
                if (!vm_is_valid_address(operand)) {
                    return vm_set_error(vm, "Invalid jump address 0x%04X", operand);
                }
                vm->cpu.pc = operand;
            }
            break;
            
        case OP_JNZ:
            if (!vm->cpu.flags.zero) {
                if (!vm_is_valid_address(operand)) {
                    return vm_set_error(vm, "Invalid jump address 0x%04X", operand);
                }
                vm->cpu.pc = operand;
            }
            break;
            
        case OP_JSR:
            if (!vm_is_valid_address(operand)) {
                return vm_set_error(vm, "Invalid subroutine address 0x%04X", operand);
            }
            if (vm->cpu.sp == 0) {
                return vm_set_error(vm, "Stack overflow");
            }
            vm->memory[vm->cpu.sp] = vm->cpu.pc;
            vm->cpu.sp--;
            vm->cpu.pc = operand;
            break;
            
        case OP_RTS:
            if (operand == 0) {
                // Return from subroutine
                if (vm->cpu.sp >= STACK_TOP) {
                    return vm_set_error(vm, "Stack underflow");
                }
                vm->cpu.sp++;
                vm->cpu.pc = vm->memory[vm->cpu.sp];
            } else {
                // Halt with exit code
                vm->state = VM_HALTED;
                if (vm->debug_enabled) {
                    printf("Program halted with exit code %d after %llu cycles\n", 
                           operand, vm->cycle_count);
                    printf("Final accumulator value: %d\n", vm->cpu.accumulator);
                }
                return RESULT_HALT;
            }
            break;
            
        default:
            return vm_set_error(vm, "Invalid opcode 0x%X", opcode);
    }
    
    return RESULT_OK;
}

result_t vm_run(sap_vm_t *vm, uint64_t max_cycles) {
    if (vm->debug_enabled) {
        printf("Starting run at PC=0x%04X, state=%s\n", vm->cpu.pc, vm_state_to_string(vm->state));
    }
    
    vm->state = VM_RUNNING;
    result_t result = RESULT_OK;
    
    for (uint64_t i = 0; i < max_cycles && result == RESULT_OK; i++) {
        result = vm_step(vm);
        if (result == RESULT_BREAKPOINT) {
            printf("Breakpoint hit at PC=0x%04X\n", vm->last_pc);
            break;
        }
    }
    
    if (vm->state == VM_RUNNING && result == RESULT_OK) {
        vm->state = VM_STOPPED;
        printf("Execution stopped after %llu cycles (limit reached)\n", max_cycles);
    }
    
    return result;
}

result_t vm_run_until_halt(sap_vm_t *vm) {
    return vm_run(vm, UINT64_MAX);
}

uint16_t vm_encode_instruction(opcode_t opcode, addressing_mode_t mode, uint16_t operand) {
    return ((opcode & 0xF) << OPCODE_SHIFT) | 
           ((mode & 0x3) << ADDR_MODE_SHIFT) | 
           (operand & OPERAND_MASK);
}

void vm_decode_instruction(uint16_t instruction, opcode_t *opcode, 
                         addressing_mode_t *mode, uint16_t *operand) {
    *opcode = (instruction & OPCODE_MASK) >> OPCODE_SHIFT;
    *mode = (instruction & ADDR_MODE_MASK) >> ADDR_MODE_SHIFT;
    *operand = instruction & OPERAND_MASK;
}

const char *opcode_to_string(opcode_t opcode) {
    static const char *opcodes[] = {
        "NOP", "LDA", "STA", "ADD", "SUB", "MUL", "DIV", "AND",
        "OR", "XOR", "CMP", "JMP", "JZ", "JNZ", "JSR", "RTS"
    };
    return (opcode <= 0xF) ? opcodes[opcode] : "???";
}

const char *addressing_mode_to_string(addressing_mode_t mode) {
    static const char *modes[] = {"#", "", "@", ",X"};
    return (mode <= 3) ? modes[mode] : "?";
}

const char *vm_state_to_string(vm_state_t state) {
    switch (state) {
        case VM_STOPPED: return "STOPPED";
        case VM_RUNNING: return "RUNNING";
        case VM_HALTED: return "HALTED";
        case VM_ERROR: return "ERROR";
        case VM_BREAKPOINT: return "BREAKPOINT";
        default: return "UNKNOWN";
    }
}

static void print_formatted_address(FILE *out, const char *label, uint16_t addr) {
    fprintf(out, "%-8s: 0x%04X (%u)\n", label, addr, addr);
}

static void print_formatted_value(FILE *out, const char *label, int value, bool as_hex) {
    if (as_hex) {
        fprintf(out, "%-8s: %d (0x%04X)\n", label, value, (uint16_t)value);
    } else {
        fprintf(out, "%-8s: %d\n", label, value);
    }
}

void vm_print_state(sap_vm_t *vm) {
    printf("VM State: %s | Cycles: %llu\n", vm_state_to_string(vm->state), vm->cycle_count);
    print_formatted_address(stdout, "PC", vm->cpu.pc);
    print_formatted_value(stdout, "ACC", vm->cpu.accumulator, true);
    print_formatted_value(stdout, "X", vm->cpu.x_reg, true);
    print_formatted_address(stdout, "SP", vm->cpu.sp);
    printf("Flags    : Z:%d N:%d C:%d O:%d\n", 
           vm->cpu.flags.zero, vm->cpu.flags.negative, 
           vm->cpu.flags.carry, vm->cpu.flags.overflow);
    if (vm->state == VM_ERROR) {
        printf("Last Error: %s\n", vm->last_error);
    }
    printf("----------------------------------------\n");
}

void vm_print_memory(sap_vm_t *vm, uint16_t start, uint16_t end) {
    if (end >= MEMORY_SIZE) end = MEMORY_SIZE - 1;
    printf("Memory [0x%04X - 0x%04X]:\n", start, end);
    for (uint16_t addr = start; addr <= end && addr < MEMORY_SIZE; addr += 8) {
        printf("0x%04X: ", addr);
        for (int i = 0; i < 8 && (addr + i) <= end; i++) {
            printf("%6d ", vm->memory[addr + i]);
        }
        printf("\n");
    }
    printf("\n");
}

void vm_print_disassembly(sap_vm_t *vm, uint16_t start, uint16_t count) {
    printf("Disassembly from 0x%04X:\n", start);
    for (uint16_t i = 0; i < count && (start + i) < MEMORY_SIZE; i++) {
        uint16_t addr = start + i;
        uint16_t instruction = vm->memory[addr];
        if (instruction == 0) continue;
        
        opcode_t opcode;
        addressing_mode_t mode;
        uint16_t operand;
        vm_decode_instruction(instruction, &opcode, &mode, &operand);
        
        printf("0x%04X: %04X  %s", addr, instruction, opcode_to_string(opcode));
        if (opcode != OP_NOP && opcode != OP_RTS) {
            printf(" %s%d", addressing_mode_to_string(mode), operand);
        }
        if (addr == vm->cpu.pc) {
            printf(" <-- PC");
        }
        printf("\n");
    }
    printf("\n");
}


