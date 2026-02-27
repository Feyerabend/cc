/*
 * RISC-V RV32IM Virtual Machine - Implementation
 * ANSI C implementation
 */

#include "riscv_vm.h"

/* ABI register names */
const char *reg_names[NUM_REGISTERS] = {
    "zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2",
    "s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5",
    "a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7",
    "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6"
};

/* Helper macros */
#define TO_SIGNED(x) ((int32_t)(x))
#define TO_UNSIGNED(x) ((uint32_t)(x))

/* Create new VM instance */
riscv_vm_t *vm_create(size_t mem_size, int debug, int trace) {
    riscv_vm_t *vm = (riscv_vm_t *)malloc(sizeof(riscv_vm_t));
    if (!vm) return NULL;
    
    vm->memory = (uint8_t *)calloc(mem_size, 1);
    if (!vm->memory) {
        free(vm);
        return NULL;
    }
    
    vm->mem_size = mem_size;
    vm->debug = debug;
    vm->trace = trace;
    vm->interrupt_check = NULL;
    vm->interrupt_handler = NULL;
    vm->interrupt_user_data = NULL;
    
    vm_reset(vm);
    return vm;
}

/* Destroy VM instance */
void vm_destroy(riscv_vm_t *vm) {
    if (vm) {
        if (vm->memory) free(vm->memory);
        free(vm);
    }
}

/* Reset VM state */
void vm_reset(riscv_vm_t *vm) {
    int i;
    for (i = 0; i < NUM_REGISTERS; i++) {
        vm->regs[i] = 0;
    }
    vm->pc = 0;
    vm->running = 1;
    vm->instruction_count = 0;
    vm->output_len = 0;
    vm->output[0] = '\0';
    memset(vm->memory, 0, vm->mem_size);
}

/* Load program from file */
int vm_load_program(riscv_vm_t *vm, const char *filename) {
    FILE *f;
    size_t bytes_read;
    
    f = fopen(filename, "rb");
    if (!f) {
        fprintf(stderr, "Error: Cannot open file %s\n", filename);
        return -1;
    }
    
    bytes_read = fread(vm->memory, 1, vm->mem_size, f);
    fclose(f);
    
    if (vm->debug) {
        printf("Loaded %lu bytes into memory\n", (unsigned long)bytes_read);
    }
    
    return 0;
}

/* Sign extend a value */
int32_t sign_extend(int32_t val, int bits) {
    int32_t mask = 1 << (bits - 1);
    if (val & mask) {
        return val | (~((1 << bits) - 1));
    }
    return val;
}

/* Read from memory */
uint32_t read_mem(riscv_vm_t *vm, uint32_t addr, int size, int is_signed) {
    uint32_t val = 0;
    
    if (addr + size > vm->mem_size) {
        fprintf(stderr, "Memory access out of bounds: 0x%08x\n", addr);
        vm->running = 0;
        return 0;
    }
    
    if (size == 1) {
        val = vm->memory[addr];
        if (is_signed && (val & 0x80)) {
            val |= 0xFFFFFF00;
        }
    } else if (size == 2) {
        val = vm->memory[addr] | (vm->memory[addr+1] << 8);
        if (is_signed && (val & 0x8000)) {
            val |= 0xFFFF0000;
        }
    } else if (size == 4) {
        val = vm->memory[addr] |
              (vm->memory[addr+1] << 8) |
              (vm->memory[addr+2] << 16) |
              (vm->memory[addr+3] << 24);
    }
    
    return val;
}

/* Write to memory */
void write_mem(riscv_vm_t *vm, uint32_t addr, uint32_t val, int size) {
    if (addr + size > vm->mem_size) {
        fprintf(stderr, "Memory access out of bounds: 0x%08x\n", addr);
        vm->running = 0;
        return;
    }
    
    if (size == 1) {
        vm->memory[addr] = val & 0xFF;
    } else if (size == 2) {
        vm->memory[addr] = val & 0xFF;
        vm->memory[addr+1] = (val >> 8) & 0xFF;
    } else if (size == 4) {
        vm->memory[addr] = val & 0xFF;
        vm->memory[addr+1] = (val >> 8) & 0xFF;
        vm->memory[addr+2] = (val >> 16) & 0xFF;
        vm->memory[addr+3] = (val >> 24) & 0xFF;
    }
}

/* Decode instruction */
instruction_t decode(uint32_t word) {
    instruction_t instr;
    uint8_t opcode_bits;
    
    instr.opcode = OP_UNKNOWN;
    opcode_bits = word & 0x7F;
    instr.rd = (word >> 7) & 0x1F;
    instr.funct3 = (word >> 12) & 0x7;
    instr.rs1 = (word >> 15) & 0x1F;
    instr.rs2 = (word >> 20) & 0x1F;
    instr.funct7 = (word >> 25) & 0x7F;
    instr.imm = 0;
    
    /* R-type instructions */
    if (opcode_bits == 0x33) {
        if (instr.funct7 == 0x00) {
            switch (instr.funct3) {
                case 0x0: instr.opcode = OP_ADD; break;
                case 0x4: instr.opcode = OP_XOR; break;
                case 0x6: instr.opcode = OP_OR; break;
                case 0x7: instr.opcode = OP_AND; break;
                case 0x1: instr.opcode = OP_SLL; break;
                case 0x5: instr.opcode = OP_SRL; break;
                case 0x2: instr.opcode = OP_SLT; break;
                case 0x3: instr.opcode = OP_SLTU; break;
            }
        } else if (instr.funct7 == 0x20) {
            switch (instr.funct3) {
                case 0x0: instr.opcode = OP_SUB; break;
                case 0x5: instr.opcode = OP_SRA; break;
            }
        } else if (instr.funct7 == 0x01) {  /* M extension */
            switch (instr.funct3) {
                case 0x0: instr.opcode = OP_MUL; break;
                case 0x1: instr.opcode = OP_MULH; break;
                case 0x2: instr.opcode = OP_MULHSU; break;
                case 0x3: instr.opcode = OP_MULHU; break;
                case 0x4: instr.opcode = OP_DIV; break;
                case 0x5: instr.opcode = OP_DIVU; break;
                case 0x6: instr.opcode = OP_REM; break;
                case 0x7: instr.opcode = OP_REMU; break;
            }
        }
    }
    /* I-type arithmetic */
    else if (opcode_bits == 0x13) {
        instr.imm = sign_extend(word >> 20, 12);
        switch (instr.funct3) {
            case 0x0: instr.opcode = OP_ADDI; break;
            case 0x4: instr.opcode = OP_XORI; break;
            case 0x6: instr.opcode = OP_ORI; break;
            case 0x7: instr.opcode = OP_ANDI; break;
            case 0x2: instr.opcode = OP_SLTI; break;
            case 0x3: instr.opcode = OP_SLTIU; break;
            case 0x1:
                instr.opcode = OP_SLLI;
                instr.imm &= 0x1F;
                break;
            case 0x5:
                instr.imm &= 0x1F;
                if ((word >> 25) == 0x00) {
                    instr.opcode = OP_SRLI;
                } else if ((word >> 25) == 0x20) {
                    instr.opcode = OP_SRAI;
                }
                break;
        }
    }
    /* Loads */
    else if (opcode_bits == 0x03) {
        instr.imm = sign_extend(word >> 20, 12);
        switch (instr.funct3) {
            case 0x0: instr.opcode = OP_LB; break;
            case 0x1: instr.opcode = OP_LH; break;
            case 0x2: instr.opcode = OP_LW; break;
            case 0x4: instr.opcode = OP_LBU; break;
            case 0x5: instr.opcode = OP_LHU; break;
        }
    }
    /* Stores */
    else if (opcode_bits == 0x23) {
        instr.imm = sign_extend(((word >> 25) << 5) | ((word >> 7) & 0x1F), 12);
        switch (instr.funct3) {
            case 0x0: instr.opcode = OP_SB; break;
            case 0x1: instr.opcode = OP_SH; break;
            case 0x2: instr.opcode = OP_SW; break;
        }
    }
    /* Branches */
    else if (opcode_bits == 0x63) {
        instr.imm = sign_extend(
            ((word >> 31) << 12) | (((word >> 7) & 1) << 11) |
            (((word >> 25) & 0x3F) << 5) | (((word >> 8) & 0xF) << 1),
            13);
        switch (instr.funct3) {
            case 0x0: instr.opcode = OP_BEQ; break;
            case 0x1: instr.opcode = OP_BNE; break;
            case 0x4: instr.opcode = OP_BLT; break;
            case 0x5: instr.opcode = OP_BGE; break;
            case 0x6: instr.opcode = OP_BLTU; break;
            case 0x7: instr.opcode = OP_BGEU; break;
        }
    }
    /* JAL */
    else if (opcode_bits == 0x6F) {
        instr.opcode = OP_JAL;
        instr.imm = sign_extend(
            ((word >> 31) << 20) | (((word >> 12) & 0xFF) << 12) |
            (((word >> 20) & 1) << 11) | (((word >> 21) & 0x3FF) << 1),
            21);
    }
    /* JALR */
    else if (opcode_bits == 0x67) {
        instr.opcode = OP_JALR;
        instr.imm = sign_extend(word >> 20, 12);
    }
    /* LUI */
    else if (opcode_bits == 0x37) {
        instr.opcode = OP_LUI;
        instr.imm = word >> 12;
    }
    /* AUIPC */
    else if (opcode_bits == 0x17) {
        instr.opcode = OP_AUIPC;
        instr.imm = word >> 12;
    }
    /* System */
    else if (opcode_bits == 0x73) {
        if (instr.funct3 == 0) {
            if ((word >> 20) == 0) {
                instr.opcode = OP_ECALL;
            } else if ((word >> 20) == 1) {
                instr.opcode = OP_EBREAK;
            }
        }
    }
    
    return instr;
}

/* Execute single instruction */
void execute(riscv_vm_t *vm, instruction_t *instr) {
    uint32_t addr;
    int32_t s1, s2;
    int64_t result64;
    uint64_t uresult64;
    
    switch (instr->opcode) {
        /* R-type arithmetic */
        case OP_ADD:
            vm->regs[instr->rd] = vm->regs[instr->rs1] + vm->regs[instr->rs2];
            vm->pc += 4;
            break;
        case OP_SUB:
            vm->regs[instr->rd] = vm->regs[instr->rs1] - vm->regs[instr->rs2];
            vm->pc += 4;
            break;
        case OP_XOR:
            vm->regs[instr->rd] = vm->regs[instr->rs1] ^ vm->regs[instr->rs2];
            vm->pc += 4;
            break;
        case OP_OR:
            vm->regs[instr->rd] = vm->regs[instr->rs1] | vm->regs[instr->rs2];
            vm->pc += 4;
            break;
        case OP_AND:
            vm->regs[instr->rd] = vm->regs[instr->rs1] & vm->regs[instr->rs2];
            vm->pc += 4;
            break;
        case OP_SLL:
            vm->regs[instr->rd] = vm->regs[instr->rs1] << (vm->regs[instr->rs2] & 0x1F);
            vm->pc += 4;
            break;
        case OP_SRL:
            vm->regs[instr->rd] = vm->regs[instr->rs1] >> (vm->regs[instr->rs2] & 0x1F);
            vm->pc += 4;
            break;
        case OP_SRA:
            s1 = TO_SIGNED(vm->regs[instr->rs1]);
            vm->regs[instr->rd] = s1 >> (vm->regs[instr->rs2] & 0x1F);
            vm->pc += 4;
            break;
        case OP_SLT:
            s1 = TO_SIGNED(vm->regs[instr->rs1]);
            s2 = TO_SIGNED(vm->regs[instr->rs2]);
            vm->regs[instr->rd] = (s1 < s2) ? 1 : 0;
            vm->pc += 4;
            break;
        case OP_SLTU:
            vm->regs[instr->rd] = (vm->regs[instr->rs1] < vm->regs[instr->rs2]) ? 1 : 0;
            vm->pc += 4;
            break;
            
        /* M extension */
        case OP_MUL:
            vm->regs[instr->rd] = vm->regs[instr->rs1] * vm->regs[instr->rs2];
            vm->pc += 4;
            break;
        case OP_MULH:
            result64 = (int64_t)TO_SIGNED(vm->regs[instr->rs1]) * 
                       (int64_t)TO_SIGNED(vm->regs[instr->rs2]);
            vm->regs[instr->rd] = (uint32_t)(result64 >> 32);
            vm->pc += 4;
            break;
        case OP_MULHSU:
            result64 = (int64_t)TO_SIGNED(vm->regs[instr->rs1]) * 
                       (uint64_t)vm->regs[instr->rs2];
            vm->regs[instr->rd] = (uint32_t)(result64 >> 32);
            vm->pc += 4;
            break;
        case OP_MULHU:
            uresult64 = (uint64_t)vm->regs[instr->rs1] * 
                        (uint64_t)vm->regs[instr->rs2];
            vm->regs[instr->rd] = (uint32_t)(uresult64 >> 32);
            vm->pc += 4;
            break;
        case OP_DIV:
            s1 = TO_SIGNED(vm->regs[instr->rs1]);
            s2 = TO_SIGNED(vm->regs[instr->rs2]);
            if (s2 == 0) {
                vm->regs[instr->rd] = 0xFFFFFFFF;
            } else if (s1 == (int32_t)0x80000000 && s2 == -1) {
                vm->regs[instr->rd] = 0x80000000;
            } else {
                vm->regs[instr->rd] = s1 / s2;
            }
            vm->pc += 4;
            break;
        case OP_DIVU:
            if (vm->regs[instr->rs2] == 0) {
                vm->regs[instr->rd] = 0xFFFFFFFF;
            } else {
                vm->regs[instr->rd] = vm->regs[instr->rs1] / vm->regs[instr->rs2];
            }
            vm->pc += 4;
            break;
        case OP_REM:
            s1 = TO_SIGNED(vm->regs[instr->rs1]);
            s2 = TO_SIGNED(vm->regs[instr->rs2]);
            if (s2 == 0) {
                vm->regs[instr->rd] = vm->regs[instr->rs1];
            } else if (s1 == (int32_t)0x80000000 && s2 == -1) {
                vm->regs[instr->rd] = 0;
            } else {
                vm->regs[instr->rd] = s1 % s2;
            }
            vm->pc += 4;
            break;
        case OP_REMU:
            if (vm->regs[instr->rs2] == 0) {
                vm->regs[instr->rd] = vm->regs[instr->rs1];
            } else {
                vm->regs[instr->rd] = vm->regs[instr->rs1] % vm->regs[instr->rs2];
            }
            vm->pc += 4;
            break;
            
        /* I-type arithmetic */
        case OP_ADDI:
            vm->regs[instr->rd] = vm->regs[instr->rs1] + instr->imm;
            vm->pc += 4;
            break;
        case OP_XORI:
            vm->regs[instr->rd] = vm->regs[instr->rs1] ^ instr->imm;
            vm->pc += 4;
            break;
        case OP_ORI:
            vm->regs[instr->rd] = vm->regs[instr->rs1] | instr->imm;
            vm->pc += 4;
            break;
        case OP_ANDI:
            vm->regs[instr->rd] = vm->regs[instr->rs1] & instr->imm;
            vm->pc += 4;
            break;
        case OP_SLTI:
            s1 = TO_SIGNED(vm->regs[instr->rs1]);
            vm->regs[instr->rd] = (s1 < instr->imm) ? 1 : 0;
            vm->pc += 4;
            break;
        case OP_SLTIU:
            vm->regs[instr->rd] = (vm->regs[instr->rs1] < (uint32_t)instr->imm) ? 1 : 0;
            vm->pc += 4;
            break;
        case OP_SLLI:
            vm->regs[instr->rd] = vm->regs[instr->rs1] << (instr->imm & 0x1F);
            vm->pc += 4;
            break;
        case OP_SRLI:
            vm->regs[instr->rd] = vm->regs[instr->rs1] >> (instr->imm & 0x1F);
            vm->pc += 4;
            break;
        case OP_SRAI:
            s1 = TO_SIGNED(vm->regs[instr->rs1]);
            vm->regs[instr->rd] = s1 >> (instr->imm & 0x1F);
            vm->pc += 4;
            break;
            
        /* Loads */
        case OP_LB:
            addr = vm->regs[instr->rs1] + instr->imm;
            vm->regs[instr->rd] = read_mem(vm, addr, 1, 1);
            vm->pc += 4;
            break;
        case OP_LH:
            addr = vm->regs[instr->rs1] + instr->imm;
            vm->regs[instr->rd] = read_mem(vm, addr, 2, 1);
            vm->pc += 4;
            break;
        case OP_LW:
            addr = vm->regs[instr->rs1] + instr->imm;
            vm->regs[instr->rd] = read_mem(vm, addr, 4, 0);
            if (vm->trace) {
                printf("         LW: addr=0x%08x -> val=0x%08x\n", 
                       addr, vm->regs[instr->rd]);
            }
            vm->pc += 4;
            break;
        case OP_LBU:
            addr = vm->regs[instr->rs1] + instr->imm;
            vm->regs[instr->rd] = read_mem(vm, addr, 1, 0);
            vm->pc += 4;
            break;
        case OP_LHU:
            addr = vm->regs[instr->rs1] + instr->imm;
            vm->regs[instr->rd] = read_mem(vm, addr, 2, 0);
            vm->pc += 4;
            break;
            
        /* Stores */
        case OP_SB:
            addr = vm->regs[instr->rs1] + instr->imm;
            write_mem(vm, addr, vm->regs[instr->rs2], 1);
            vm->pc += 4;
            break;
        case OP_SH:
            addr = vm->regs[instr->rs1] + instr->imm;
            write_mem(vm, addr, vm->regs[instr->rs2], 2);
            vm->pc += 4;
            break;
        case OP_SW:
            addr = vm->regs[instr->rs1] + instr->imm;
            write_mem(vm, addr, vm->regs[instr->rs2], 4);
            vm->pc += 4;
            break;
            
        /* Branches */
        case OP_BEQ:
            if (vm->regs[instr->rs1] == vm->regs[instr->rs2]) {
                vm->pc = vm->pc + instr->imm;
            } else {
                vm->pc += 4;
            }
            break;
        case OP_BNE:
            if (vm->regs[instr->rs1] != vm->regs[instr->rs2]) {
                vm->pc = vm->pc + instr->imm;
            } else {
                vm->pc += 4;
            }
            break;
        case OP_BLT:
            s1 = TO_SIGNED(vm->regs[instr->rs1]);
            s2 = TO_SIGNED(vm->regs[instr->rs2]);
            if (s1 < s2) {
                vm->pc = vm->pc + instr->imm;
            } else {
                vm->pc += 4;
            }
            break;
        case OP_BGE:
            s1 = TO_SIGNED(vm->regs[instr->rs1]);
            s2 = TO_SIGNED(vm->regs[instr->rs2]);
            if (s1 >= s2) {
                vm->pc = vm->pc + instr->imm;
            } else {
                vm->pc += 4;
            }
            break;
        case OP_BLTU:
            if (vm->regs[instr->rs1] < vm->regs[instr->rs2]) {
                vm->pc = vm->pc + instr->imm;
            } else {
                vm->pc += 4;
            }
            break;
        case OP_BGEU:
            if (vm->regs[instr->rs1] >= vm->regs[instr->rs2]) {
                vm->pc = vm->pc + instr->imm;
            } else {
                vm->pc += 4;
            }
            break;
            
        /* Jumps */
        case OP_JAL:
            vm->regs[instr->rd] = vm->pc + 4;
            if (vm->trace) {
                printf("         JAL: jumping to 0x%08x, saving PC+4=0x%08x to %s\n",
                       vm->pc + instr->imm, vm->pc + 4, reg_names[instr->rd]);
            }
            vm->pc = vm->pc + instr->imm;
            break;
        case OP_JALR:
            addr = vm->pc + 4;
            vm->pc = (vm->regs[instr->rs1] + instr->imm) & 0xFFFFFFFE;
            if (vm->trace) {
                printf("         JALR: jumping to 0x%08x, saving PC+4=0x%08x to %s\n",
                       vm->pc, addr, reg_names[instr->rd]);
            }
            vm->regs[instr->rd] = addr;
            break;
            
        /* Upper immediate */
        case OP_LUI:
            vm->regs[instr->rd] = instr->imm << 12;
            vm->pc += 4;
            break;
        case OP_AUIPC:
            vm->regs[instr->rd] = vm->pc + (instr->imm << 12);
            vm->pc += 4;
            break;
            
        /* System */
        case OP_ECALL:
            handle_syscall(vm);
            vm->pc += 4;
            break;
        case OP_EBREAK:
            if (vm->debug) {
                printf("EBREAK encountered\n");
            }
            vm->running = 0;
            break;
            
        default:
            fprintf(stderr, "Unknown opcode at PC=0x%08x\n", vm->pc);
            vm->running = 0;
            break;
    }
    
    /* x0 is always 0 */
    vm->regs[0] = 0;
}

/* Handle system calls */
void handle_syscall(riscv_vm_t *vm) {
    uint32_t syscall_num = vm->regs[17];  /* a7 */
    uint32_t addr;
    char buffer[32];
    size_t len;
    
    switch (syscall_num) {
        case 1:  /* Print integer */
            printf("%d", TO_SIGNED(vm->regs[10]));
            sprintf(buffer, "%d", TO_SIGNED(vm->regs[10]));
            len = strlen(buffer);
            if (vm->output_len + len < MAX_OUTPUT_LEN) {
                strcat(vm->output, buffer);
                vm->output_len += len;
            }
            break;
            
        case 4:  /* Print string */
            addr = vm->regs[10];  /* a0 */
            while (addr < vm->mem_size && vm->memory[addr] != 0) {
                putchar(vm->memory[addr]);
                if (vm->output_len < MAX_OUTPUT_LEN - 1) {
                    vm->output[vm->output_len++] = vm->memory[addr];
                    vm->output[vm->output_len] = '\0';
                }
                addr++;
            }
            break;
            
        case 10:  /* Exit */
            vm->running = 0;
            break;
            
        case 11:  /* Print character */
            putchar(vm->regs[10] & 0xFF);
            if (vm->output_len < MAX_OUTPUT_LEN - 1) {
                vm->output[vm->output_len++] = vm->regs[10] & 0xFF;
                vm->output[vm->output_len] = '\0';
            }
            break;
            
        default:
            if (vm->debug) {
                printf("Unknown syscall: %u\n", syscall_num);
            }
            break;
    }
}

/* Execute VM */
void vm_execute(riscv_vm_t *vm) {
    while (vm->running) {
        vm_step(vm);
        
        /* Check for interrupts if handler is set */
        if (vm->interrupt_check && vm->interrupt_handler) {
            int interrupt_num = vm->interrupt_check(vm->interrupt_user_data);
            if (interrupt_num >= 0) {
                vm->interrupt_handler(vm->interrupt_user_data, interrupt_num);
            }
        }
    }
}

/* Execute single step */
void vm_step(riscv_vm_t *vm) {
    uint32_t word;
    instruction_t instr;
    
    if (!vm->running) return;
    
    /* Fetch */
    if (vm->pc + 4 > vm->mem_size) {
        fprintf(stderr, "PC out of bounds: 0x%08x\n", vm->pc);
        vm->running = 0;
        return;
    }
    
    word = read_mem(vm, vm->pc, 4, 0);
    
    /* Decode */
    instr = decode(word);
    
    if (vm->trace) {
        printf("0x%08x: %s\n", vm->pc, opcode_to_string(instr.opcode));
    }
    
    /* Execute */
    execute(vm, &instr);
    
    vm->instruction_count++;
}

/* Set interrupt handler */
void vm_set_interrupt_handler(riscv_vm_t *vm,
                               int (*check_fn)(void *),
                               void (*handler_fn)(void *, int),
                               void *user_data) {
    vm->interrupt_check = check_fn;
    vm->interrupt_handler = handler_fn;
    vm->interrupt_user_data = user_data;
}

/* Print registers */
void print_regs(riscv_vm_t *vm) {
    int i, j;
    
    printf("\n=== Register State ===\n");
    for (i = 0; i < 32; i += 4) {
        for (j = 0; j < 4 && i + j < 32; j++) {
            printf("%4s=0x%08x  ", reg_names[i + j], vm->regs[i + j]);
        }
        printf("\n");
    }
    printf("\n");
}

/* Dump memory */
void dump_memory(riscv_vm_t *vm, uint32_t start, uint32_t length) {
    uint32_t i, j;
    
    printf("\n=== Memory Dump [0x%04x - 0x%04x] ===\n", start, start + length);
    for (i = start; i < start + length; i += 16) {
        printf("0x%04x: ", i);
        
        /* Hex values */
        for (j = 0; j < 16 && i + j < start + length; j++) {
            printf("%02x ", vm->memory[i + j]);
        }
        
        /* Padding */
        for (; j < 16; j++) {
            printf("   ");
        }
        
        printf(" ");
        
        /* ASCII values */
        for (j = 0; j < 16 && i + j < start + length; j++) {
            unsigned char c = vm->memory[i + j];
            printf("%c", (c >= 32 && c < 127) ? c : '.');
        }
        
        printf("\n");
    }
    printf("\n");
}

/* Convert opcode to string */
const char *opcode_to_string(opcode_t op) {
    static const char *names[] = {
        "ADD", "SUB", "XOR", "OR", "AND",
        "SLL", "SRL", "SRA", "SLT", "SLTU",
        "MUL", "MULH", "MULHSU", "MULHU",
        "DIV", "DIVU", "REM", "REMU",
        "ADDI", "XORI", "ORI", "ANDI",
        "SLTI", "SLTIU",
        "SLLI", "SRLI", "SRAI",
        "LB", "LH", "LW", "LBU", "LHU",
        "SB", "SH", "SW",
        "BEQ", "BNE", "BLT", "BGE", "BLTU", "BGEU",
        "JAL", "JALR",
        "LUI", "AUIPC",
        "ECALL", "EBREAK",
        "UNKNOWN"
    };
    
    if (op >= 0 && op <= OP_UNKNOWN) {
        return names[op];
    }
    return "INVALID";
}
