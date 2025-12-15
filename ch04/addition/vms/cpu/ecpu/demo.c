#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "cpu.h"

void demonstrate_instruction_encoding() {
    printf("\n--- INSTRUCTION ENCODING DEMONSTRATION ---\n");
    printf("Instructions are now 16-bit binary words with encoded operands:\n\n");
    
    // Show how instructions are encoded as binary numbers
    uint16_t add_instr = ENCODE_INSTRUCTION(OP_ADD, 0, 1);  // ADD R0, R1
    uint16_t load_instr = ENCODE_INSTRUCTION_IMM(OP_LOAD, 0, 100);  // LOAD R0, #100
    
    printf("ADD R0, R1 encoded as:  0x%04X (binary: ", add_instr);
    for (int i = 15; i >= 0; i--) {
        printf("%d", (add_instr >> i) & 1);
        if (i % 4 == 0 && i > 0) printf(" ");
    }
    printf(")\n");
    
    printf("  Opcode (bits 15-8): 0x%02X\n", (add_instr >> 8) & 0xFF);
    printf("  Reg A  (bits 7-6):  %d\n", (add_instr >> 6) & 0x3);
    printf("  Reg B  (bits 5-4):  %d\n", (add_instr >> 4) & 0x3);
    
    printf("\nLOAD R0, #100 encoded as: 0x%04X\n", load_instr);
    printf("  Opcode (bits 15-8): 0x%02X\n", (load_instr >> 8) & 0xFF);
    printf("  Reg A  (bits 7-6):  %d\n", (load_instr >> 6) & 0x3);
    printf("  Address (bits 7-0): %d\n", load_instr & 0xFF);
}

void demonstrate_pc_update() {
    printf("\n--- PC UPDATE DEMONSTRATION ---\n");
    printf("PC is automatically incremented unless overridden by control flow:\n\n");
    
    VM vm;
    init_vm(&vm);
    
    // Load a simple program: ADD R0,R1 then HALT
    int pc = 0;
    // ADD R0, R1 (16-bit instruction)
    vm.memory[pc++] = 0x00;  // Low byte of instruction
    vm.memory[pc++] = 0x00 | (0 << 6) | (1 << 4);  // High byte with reg encoding
    
    // HALT
    vm.memory[pc++] = 0xFF;  // Low byte 
    vm.memory[pc++] = 0xFF;  // High byte
    
    vm.registers[0] = 5;
    vm.registers[1] = 3;
    
    printf("Before execution: PC = %d\n", vm.pc);
    
    // Show fetch incrementing PC
    uint16_t instr1 = cpu_fetch(&vm);
    printf("After first fetch: PC = %d (incremented by 2 for 16-bit instruction)\n", vm.pc);
    
    // Decode and show the instruction
    DecodedInstruction decoded = decode_instruction(instr1);
    printf("Decoded instruction: Opcode=0x%02X, RegA=%d, RegB=%d\n", 
           decoded.opcode, decoded.reg_a, decoded.reg_b);
}

void demonstrate_control_flow_override() {
    printf("\n--- CONTROL FLOW OVERRIDE DEMONSTRATION ---\n");
    printf("Branches and jumps override automatic PC increment:\n\n");
    
    VM vm;
    init_vm(&vm);
    
    // Create a program with a jump
    int pc = 0;
    
    // JMP 10 (jump to address 10)
    vm.memory[pc++] = 0x0A;  // Low byte
    vm.memory[pc++] = 0x0A | (0 << 6);  // High byte with opcode
    
    // Some other instruction at address 2
    vm.memory[pc++] = 0xFF;  // HALT
    vm.memory[pc++] = 0xFF;
    
    // Target of jump at address 10
    vm.memory[10] = 0xFF;  // HALT  
    vm.memory[11] = 0xFF;
    
    printf("Initial PC: %d\n", vm.pc);
    
    // Execute one instruction cycle
    cpu_fetch(&vm);
    printf("After fetch (before execute): PC = %d\n", vm.pc);
    
    cpu_decode_and_execute(&vm);
    printf("After JMP execution: PC = %d (overridden to jump target)\n", vm.pc);
}

void demonstrate_memory_interface() {
    printf("\n--- MEMORY INTERFACE DEMONSTRATION ---\n");
    printf("CPU uses helper functions to interface with memory:\n\n");
    
    VM vm;
    init_vm(&vm);
    
    // Show memory interface functions
    printf("Writing value 42 to memory address 100...\n");
    mem_write(&vm, 100, 42);
    
    printf("Reading from memory address 100...\n");
    uint8_t value = mem_read(&vm, 100);
    printf("Read value: %d\n", value);
    
    // Show how LOAD instruction uses memory interface
    printf("\nDemonstrating LOAD instruction using memory interface:\n");
    vm.memory[50] = 99;  // Put test value in memory
    
    int pc = 0;
    // LOAD R0, 50
    vm.memory[pc++] = 0x08;  // LOAD opcode low byte
    vm.memory[pc++] = 0x08 | (0 << 6) | 50;  // High byte with reg and address
    
    // HALT
    vm.memory[pc++] = 0xFF;
    vm.memory[pc++] = 0xFF;
    
    printf("Before LOAD: R0 = %d, memory[50] = %d\n", vm.registers[0], vm.memory[50]);
    
    run_vm(&vm);  // This will show the memory interface in action
}

void demonstrate_full_cpu_cycle() {
    printf("\n--- FULL CPU CYCLE DEMONSTRATION ---\n");
    printf("Complete fetch-decode-execute cycle with a real program:\n\n");
    
    VM vm;
    init_vm(&vm);
    
    // Create a more complex program
    int pc = 0;
    
    // Initialize R0 and R1 with immediate loads (simulated with direct memory)
    vm.memory[100] = 10;  // Value to load into R0
    vm.memory[101] = 5;   // Value to load into R1
    
    // LOAD R0, 100  (Load 10 into R0)
    vm.memory[pc++] = OP_LOAD;
    vm.memory[pc++] = (0 << 6) | 100;
    
    // LOAD R1, 101  (Load 5 into R1)
    vm.memory[pc++] = OP_LOAD;
    vm.memory[pc++] = (1 << 6) | 101;
    
    // ADD R0, R1   (R0 = R0 + R1 = 10 + 5 = 15)
    vm.memory[pc++] = OP_ADD;
    vm.memory[pc++] = (0 << 6) | (1 << 4);
    
    // STORE R0, 102  (Store result to memory)
    vm.memory[pc++] = OP_STORE;
    vm.memory[pc++] = (0 << 6) | 102;
    
    // SUB R0, R1   (R0 = R0 - R1 = 15 - 5 = 10)
    vm.memory[pc++] = OP_SUB;
    vm.memory[pc++] = (0 << 6) | (1 << 4);
    
    // JZ 16  (Jump if zero - shouldn't happen)
    vm.memory[pc++] = OP_JZ;
    vm.memory[pc++] = 16;
    
    // SHL R0  (Shift left: 10 << 1 = 20)
    vm.memory[pc++] = OP_SHL;
    vm.memory[pc++] = (0 << 6);
    
    // HALT
    vm.memory[pc++] = OP_HALT;
    vm.memory[pc++] = 0xFF;
    
    // Run the program
    printf("Starting program execution...\n");
    run_vm(&vm);
    
    printf("\nFinal memory state:\n");
    printf("memory[100] = %d (original value)\n", vm.memory[100]);
    printf("memory[101] = %d (original value)\n", vm.memory[101]);
    printf("memory[102] = %d (stored result)\n", vm.memory[102]);
}

void demonstrate_alu_operations() {
    printf("\n--- ALU OPERATIONS DEMONSTRATION ---\n");
    printf("Testing all ALU operations with built-from-gates implementation:\n\n");
    
    VM vm;
    init_vm(&vm);
    
    // Test each ALU operation
    vm.registers[0] = 12;  // 0x0C = 00001100
    vm.registers[1] = 10;  // 0x0A = 00001010
    
    printf("Initial values: R0=%d (0x%02X), R1=%d (0x%02X)\n", 
           vm.registers[0], vm.registers[0], vm.registers[1], vm.registers[1]);
    
    // Test ADD
    ALUResult result = enhanced_alu(vm.registers[0], vm.registers[1], 0);
    printf("ADD: %d + %d = %d (Z=%d, C=%d, O=%d, N=%d)\n", 
           vm.registers[0], vm.registers[1], result.result,
           result.flags.zero, result.flags.carry, result.flags.overflow, result.flags.negative);
    
    // Test SUB
    result = enhanced_alu(vm.registers[0], vm.registers[1], 1);
    printf("SUB: %d - %d = %d (Z=%d, C=%d, O=%d, N=%d)\n", 
           vm.registers[0], vm.registers[1], result.result,
           result.flags.zero, result.flags.carry, result.flags.overflow, result.flags.negative);
    
    // Test AND
    result = enhanced_alu(vm.registers[0], vm.registers[1], 2);
    printf("AND: %d & %d = %d (binary: %d & %d = %d)\n", 
           vm.registers[0], vm.registers[1], result.result,
           vm.registers[0], vm.registers[1], result.result);
    
    // Test OR
    result = enhanced_alu(vm.registers[0], vm.registers[1], 3);
    printf("OR:  %d | %d = %d (binary: %d | %d = %d)\n", 
           vm.registers[0], vm.registers[1], result.result,
           vm.registers[0], vm.registers[1], result.result);
    
    // Test XOR
    result = enhanced_alu(vm.registers[0], vm.registers[1], 4);
    printf("XOR: %d ^ %d = %d (binary: %d ^ %d = %d)\n", 
           vm.registers[0], vm.registers[1], result.result,
           vm.registers[0], vm.registers[1], result.result);
    
    // Test NOT
    result = enhanced_alu(vm.registers[0], 0, 5);
    printf("NOT: ~%d = %d\n", vm.registers[0], result.result);
    
    // Test shifts
    result = enhanced_alu(vm.registers[0], 0, 6);
    printf("SHL: %d << 1 = %d (carry=%d)\n", vm.registers[0], result.result, result.flags.carry);
    
    result = enhanced_alu(vm.registers[0], 0, 7);
    printf("SHR: %d >> 1 = %d (carry=%d)\n", vm.registers[0], result.result, result.flags.carry);
}

void demonstrate_conditional_branching() {
    printf("\n--- CONDITIONAL BRANCHING DEMONSTRATION ---\n");
    printf("Testing conditional jumps based on ALU flags:\n\n");
    
    VM vm;
    init_vm(&vm);
    
    // Program that tests conditional jumps
    int pc = 0;
    
    // Load values for testing
    vm.memory[50] = 5;
    vm.memory[51] = 5;
    
    // LOAD R0, 50  (Load 5)
    vm.memory[pc++] = OP_LOAD;
    vm.memory[pc++] = (0 << 6) | 50;
    
    // LOAD R1, 51  (Load 5)
    vm.memory[pc++] = OP_LOAD;
    vm.memory[pc++] = (1 << 6) | 51;
    
    // SUB R0, R1   (5 - 5 = 0, should set zero flag)
    vm.memory[pc++] = OP_SUB;
    vm.memory[pc++] = (0 << 6) | (1 << 4);
    
    // JZ 14  (Jump if zero - should jump)
    vm.memory[pc++] = OP_JZ;
    vm.memory[pc++] = 14;
    
    // This shouldn't execute (skipped by jump)
    vm.memory[pc++] = OP_HALT;  // pc = 8
    vm.memory[pc++] = 0xFF;     // pc = 9
    
    // Jump target at pc = 14
    pc = 14;
    vm.memory[pc++] = OP_HALT;
    vm.memory[pc++] = 0xFF;
    
    printf("Program will subtract equal values and jump if zero...\n");
    run_vm(&vm);
    
    printf("\nTesting carry flag...\n");
    
    // Reset VM for carry test
    init_vm(&vm);
    pc = 0;
    
    // Load large values that will cause carry
    vm.memory[60] = 255;  // 0xFF
    vm.memory[61] = 1;
    
    // LOAD R0, 60
    vm.memory[pc++] = OP_LOAD;
    vm.memory[pc++] = (0 << 6) | 60;
    
    // LOAD R1, 61
    vm.memory[pc++] = OP_LOAD;
    vm.memory[pc++] = (1 << 6) | 61;
    
    // ADD R0, R1   (255 + 1 = 256, but wraps to 0 with carry)
    vm.memory[pc++] = OP_ADD;
    vm.memory[pc++] = (0 << 6) | (1 << 4);
    
    // JC 14  (Jump if carry set)
    vm.memory[pc++] = OP_JC;
    vm.memory[pc++] = 14;
    
    // Shouldn't execute
    vm.memory[pc++] = OP_HALT;
    vm.memory[pc++] = 0xFF;
    
    // Jump target
    pc = 14;
    vm.memory[pc++] = OP_HALT;
    vm.memory[pc++] = 0xFF;
    
    run_vm(&vm);
}

void demonstrate_logic_gates() {
    printf("\n--- LOGIC GATES DEMONSTRATION ---\n");
    printf("All CPU operations are built from fundamental logic gates:\n\n");
    
    // Test basic gates
    printf("Basic Gates:\n");
    printf("AND(1,1) = %d, AND(1,0) = %d, AND(0,1) = %d, AND(0,0) = %d\n",
           and_gate(1,1), and_gate(1,0), and_gate(0,1), and_gate(0,0));
    
    printf("OR(1,1) = %d,  OR(1,0) = %d,  OR(0,1) = %d,  OR(0,0) = %d\n",
           or_gate(1,1), or_gate(1,0), or_gate(0,1), or_gate(0,0));
    
    printf("XOR(1,1) = %d, XOR(1,0) = %d, XOR(0,1) = %d, XOR(0,0) = %d\n",
           xor_gate(1,1), xor_gate(1,0), xor_gate(0,1), xor_gate(0,0));
    
    printf("NOT(1) = %d, NOT(0) = %d\n", not_gate(1), not_gate(0));
    
    // Test adders built from gates
    printf("\nHalf Adder (built from XOR and AND gates):\n");
    HalfAdderResult ha = half_adder(1, 1);
    printf("HalfAdder(1,1): sum=%d, carry=%d\n", ha.sum, ha.carry);
    
    printf("\nFull Adder (built from two half adders):\n");
    FullAdderResult fa = full_adder(1, 1, 1);
    printf("FullAdder(1,1,1): sum=%d, carry_out=%d\n", fa.sum, fa.carry_out);
    
    // Test 8-bit operations built from gates
    printf("\n8-bit operations (built gate-by-gate):\n");
    uint8_t a = 0xAA;  // 10101010
    uint8_t b = 0x55;  // 01010101
    
    printf("8-bit AND: 0x%02X & 0x%02X = 0x%02X\n", a, b, bitwise_and_8bit(a, b));
    printf("8-bit OR:  0x%02X | 0x%02X = 0x%02X\n", a, b, bitwise_or_8bit(a, b));
    printf("8-bit XOR: 0x%02X ^ 0x%02X = 0x%02X\n", a, b, bitwise_xor_8bit(a, b));
    printf("8-bit NOT: ~0x%02X = 0x%02X\n", a, bitwise_not_8bit(a));
    
    // Test ripple carry adder
    printf("\nRipple Carry Adder (8 full adders chained):\n");
    AdderResult add_result = ripple_carry_adder_8bit(200, 100, false);
    printf("200 + 100 = %d (carry=%d, overflow=%d)\n", 
           add_result.sum, add_result.carry_out, add_result.overflow);
    
    // Test overflow
    add_result = ripple_carry_adder_8bit(200, 200, false);
    printf("200 + 200 = %d (carry=%d, overflow=%d) <- overflow because 400 > 255\n", 
           add_result.sum, add_result.carry_out, add_result.overflow);
}

int main() {
    printf("ENHANCED CPU SIMULATOR DEMONSTRATION\n");
    printf("------------------------------------=\n");
    printf("This demonstrates a CPU built from fundamental logic gates\n");
    printf("through a complete instruction set architecture.\n");
    
    // Run all demonstrations
    demonstrate_logic_gates();
    demonstrate_instruction_encoding();
    demonstrate_pc_update();
    demonstrate_control_flow_override();
    demonstrate_memory_interface();
    demonstrate_alu_operations();
    demonstrate_conditional_branching();
    demonstrate_full_cpu_cycle();
    
    printf("\n\n");
    printf("This CPU simulator demonstrates:\n");
    printf("- Logic gates as the foundation of all operations\n");
    printf("- Adders built from gates for arithmetic\n");
    printf("- ALU combining all logical and arithmetic operations\n");
    printf("- 16-bit instruction encoding with proper bit fields\n");
    printf("- Automatic PC increment with branch override\n");
    printf("- Memory interface abstraction\n");
    printf("- Complete fetch-decode-execute cycle\n");
    printf("- Conditional branching based on ALU flags\n");
    printf("- Real programs running on the simulated hardware\n");
    
    return 0;
}
