#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "cpu.h"

// Implements fundamental logic gates used in higher-level circuits

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


// Implements adders for binary arithmetic

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

    // Overflow detection for signed arithmetic
    bool msb_a = (a >> 7) & 1;
    bool msb_b = (b >> 7) & 1;
    bool msb_sum = (sum >> 7) & 1;
    result.overflow = (msb_a && msb_b && !msb_sum) || (!msb_a && !msb_b && msb_sum);

    return result;
}

// Implements 8-bit bitwise operations using logic gates

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

// Arithmetic Logic Unit with flag support

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

// Microcode ROM and init

#define MAX_MICRO_STEPS 8
#define NUM_OPCODES 16

MicroInstruction microcode_rom[NUM_OPCODES][MAX_MICRO_STEPS];
static bool microcode_initialized = false;

void init_microcode(void) {
    if (microcode_initialized) return;

    memset(microcode_rom, 0, sizeof(microcode_rom));

    // ADD (opcode 0x00)
    microcode_rom[0x00][0] = (MicroInstruction){
        .signals = {
            .alu_enable = true,
            .alu_operation = 0,
            .reg_read_a_select = 0,
            .reg_read_b_select = 1,
            .pc_increment = true,
            .use_alu_result = true
        },
        .description = "ADD: Compute R0 + R1"
    };
    microcode_rom[0x00][1] = (MicroInstruction){
        .signals = {
            .reg_write_enable = true,
            .reg_write_select = 0,
            .end_instruction = true,
            .use_alu_result = true
        },
        .description = "ADD: Store result in R0"
    };

    // SUB (opcode 0x01)
    microcode_rom[0x01][0] = (MicroInstruction){
        .signals = {
            .alu_enable = true,
            .alu_operation = 1,
            .reg_read_a_select = 0,
            .reg_read_b_select = 1,
            .pc_increment = true,
            .use_alu_result = true
        },
        .description = "SUB: Compute R0 - R1"
    };
    microcode_rom[0x01][1] = (MicroInstruction){
        .signals = {
            .reg_write_enable = true,
            .reg_write_select = 0,
            .end_instruction = true,
            .use_alu_result = true
        },
        .description = "SUB: Store result in R0"
    };

    // LOAD (opcode 0x08)
    microcode_rom[0x08][0] = (MicroInstruction){
        .signals = {
            .fetch_next_byte = true,
            .pc_increment = true
        },
        .description = "LOAD: Fetch address byte"
    };
    microcode_rom[0x08][1] = (MicroInstruction){
        .signals = {
            .mem_read = true,
            .mem_use_immediate_addr = true
        },
        .description = "LOAD: Read from memory"
    };
    microcode_rom[0x08][2] = (MicroInstruction){
        .signals = {
            .reg_write_enable = true,
            .reg_write_select = 0,
            .end_instruction = true,
            .use_alu_result = false
        },
        .description = "LOAD: Store in R0"
    };

    // HALT (opcode 0xFF -> index 0x0F)
    microcode_rom[0x0F][0] = (MicroInstruction){
        .signals = {
            .halt_cpu = true,
            .end_instruction = true
        },
        .description = "HALT: Stop CPU"
    };

    // Other ALU operations (AND, OR, XOR, NOT, SHL, SHR)
    for (int op = 0x02; op <= 0x07; op++) {
        microcode_rom[op][0] = (MicroInstruction){
            .signals = {
                .alu_enable = true,
                .alu_operation = op,
                .reg_read_a_select = 0,
                .reg_read_b_select = 1,
                .pc_increment = true,
                .use_alu_result = true
            },
            .description = "ALU operation"
        };
        microcode_rom[op][1] = (MicroInstruction){
            .signals = {
                .reg_write_enable = true,
                .reg_write_select = 0,
                .end_instruction = true,
                .use_alu_result = true
            },
            .description = "Store ALU result"
        };
    }

    microcode_initialized = true;
}


// Virtual Machine with microcode execution

void init_vm(VM *vm) {
    memset(vm->registers, 0, sizeof(vm->registers));
    memset(vm->memory, 0, sizeof(vm->memory));
    vm->pc = 0;
    vm->flags = (ALUFlags){0};
    vm->running = true;
    vm->current_instruction = 0;
    vm->micro_step = 0;
    vm->fetched_byte = 0;
    vm->alu_result = (ALUResult){0};
    vm->memory_data = 0;

    init_microcode();
}

uint8_t fetch(VM *vm) {
    return vm->memory[vm->pc++];
}

void execute_microinstruction(VM *vm, const MicroInstruction *micro) {
    const ControlSignals *signals = &micro->signals;

    printf("    Microcode: %s\n", micro->description);

    if (signals->alu_enable) {
        uint8_t a = vm->registers[signals->reg_read_a_select];
        uint8_t b = signals->alu_use_immediate ? signals->immediate_value : vm->registers[signals->reg_read_b_select];
        vm->alu_result = enhanced_alu(a, b, signals->alu_operation);
        vm->flags = vm->alu_result.flags;

        printf("      ALU: %d op %d = %d (flags: Z=%d C=%d O=%d N=%d)\n",
               a, b, vm->alu_result.result,
               vm->flags.zero, vm->flags.carry, vm->flags.overflow, vm->flags.negative);
    }

    if (signals->reg_write_enable) {
        vm->registers[signals->reg_write_select] = signals->use_alu_result ? vm->alu_result.result : vm->memory_data;
        printf("      REG: R%d = %d\n", signals->reg_write_select, vm->registers[signals->reg_write_select]);
    }

    if (signals->mem_read) {
        uint8_t addr = signals->mem_use_immediate_addr ? vm->fetched_byte : vm->registers[0];
        vm->memory_data = vm->memory[addr];
        printf("      MEM: Read memory[%d] = %d\n", addr, vm->memory_data);
    }

    if (signals->mem_write) {
        uint8_t addr = signals->mem_use_immediate_addr ? vm->fetched_byte : vm->registers[0];
        vm->memory[addr] = vm->registers[signals->reg_read_a_select];
        printf("      MEM: Write memory[%d] = %d\n", addr, vm->memory[addr]);
    }

    if (signals->pc_increment) {
        printf("      PC: Increment to %d\n", vm->pc);
    }

    if (signals->pc_jump) {
        vm->pc = vm->fetched_byte;
        printf("      PC: Jump to %d\n", vm->pc);
    }

    if (signals->pc_jump_conditional) {
        bool should_jump = false;
        switch (signals->jump_condition) {
            case 0: should_jump = vm->flags.zero; break;
            case 1: should_jump = vm->flags.carry; break;
            case 2: should_jump = vm->flags.overflow; break;
            case 3: should_jump = vm->flags.negative; break;
        }
        if (should_jump) {
            vm->pc = vm->fetched_byte;
            printf("      PC: Conditional jump to %d\n", vm->pc);
        } else {
            printf("      PC: Conditional jump not taken\n");
        }
    }

    if (signals->fetch_next_byte) {
        vm->fetched_byte = fetch(vm);
        printf("      FETCH: Next byte = %d\n", vm->fetched_byte);
    }

    if (signals->halt_cpu) {
        vm->running = false;
        printf("      CPU: HALT\n");
    }
}

void run_vm(VM *vm) {
    int cycle = 0;
    while (vm->running && cycle < 1000) {
        if (vm->micro_step == 0) {
            vm->current_instruction = fetch(vm);
            printf("Cycle %d: PC=%d, Instruction=0x%02X, R0=%d, R1=%d, R2=%d, R3=%d\n",
                   cycle, vm->pc - 1, vm->current_instruction,
                   vm->registers[0], vm->registers[1], vm->registers[2], vm->registers[3]);
        }

        uint8_t opcode_index = (vm->current_instruction == 0xFF) ? 0x0F : vm->current_instruction;
        const MicroInstruction *micro = &microcode_rom[opcode_index][vm->micro_step];

        execute_microinstruction(vm, micro);

        if (micro->signals.end_instruction || vm->micro_step >= MAX_MICRO_STEPS) {
            printf("    End of instruction\n");
            vm->micro_step = 0;
        } else {
            vm->micro_step++;
        }

        cycle++;
    }
}