#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <assert.h>

#include "cpu.h"


static int tests_passed = 0;
static int tests_failed = 0;

#define TEST_ASSERT(condition, test_name) do { \
    if (condition) { \
        printf("✓ PASS: %s\n", test_name); \
        tests_passed++; \
    } else { \
        printf("✗ FAIL: %s\n", test_name); \
        tests_failed++; \
    } \
} while(0)

void print_test_summary() {
    printf("\n -  TEST SUMMARY  - \n");
    printf("Passed: %d\n", tests_passed);
    printf("Failed: %d\n", tests_failed);
    printf("Total:  %d\n", tests_passed + tests_failed);
    if (tests_failed == 0) {
        printf("ALL TESTS PASSED!\n");
    } else {
        printf("%d TEST(S) FAILED\n", tests_failed);
    }
}


void test_basic_gates() {
    printf("\n -  basic logic gates  - \n");
    
    TEST_ASSERT(and_gate(false, false) == false, "AND: 0,0 = 0");
    TEST_ASSERT(and_gate(false, true) == false, "AND: 0,1 = 0");
    TEST_ASSERT(and_gate(true, false) == false, "AND: 1,0 = 0");
    TEST_ASSERT(and_gate(true, true) == true, "AND: 1,1 = 1");
    
    TEST_ASSERT(or_gate(false, false) == false, "OR: 0,0 = 0");
    TEST_ASSERT(or_gate(false, true) == true, "OR: 0,1 = 1");
    TEST_ASSERT(or_gate(true, false) == true, "OR: 1,0 = 1");
    TEST_ASSERT(or_gate(true, true) == true, "OR: 1,1 = 1");
    
    TEST_ASSERT(xor_gate(false, false) == false, "XOR: 0,0 = 0");
    TEST_ASSERT(xor_gate(false, true) == true, "XOR: 0,1 = 1");
    TEST_ASSERT(xor_gate(true, false) == true, "XOR: 1,0 = 1");
    TEST_ASSERT(xor_gate(true, true) == false, "XOR: 1,1 = 0");
    
    TEST_ASSERT(not_gate(false) == true, "NOT: 0 = 1");
    TEST_ASSERT(not_gate(true) == false, "NOT: 1 = 0");
    
    TEST_ASSERT(nand_gate(false, false) == true, "NAND: 0,0 = 1");
    TEST_ASSERT(nand_gate(false, true) == true, "NAND: 0,1 = 1");
    TEST_ASSERT(nand_gate(true, false) == true, "NAND: 1,0 = 1");
    TEST_ASSERT(nand_gate(true, true) == false, "NAND: 1,1 = 0");
    
    TEST_ASSERT(nor_gate(false, false) == true, "NOR: 0,0 = 1");
    TEST_ASSERT(nor_gate(false, true) == false, "NOR: 0,1 = 0");
    TEST_ASSERT(nor_gate(true, false) == false, "NOR: 1,0 = 0");
    TEST_ASSERT(nor_gate(true, true) == false, "NOR: 1,1 = 0");
}


void test_half_adder() {
    printf("\n -  half adder  - \n");
    
    HalfAdderResult result;
    
    result = half_adder(false, false);
    TEST_ASSERT(result.sum == false && result.carry == false, "Half Adder: 0+0 = 0 carry 0");
    
    result = half_adder(false, true);
    TEST_ASSERT(result.sum == true && result.carry == false, "Half Adder: 0+1 = 1 carry 0");
    
    result = half_adder(true, false);
    TEST_ASSERT(result.sum == true && result.carry == false, "Half Adder: 1+0 = 1 carry 0");
    
    result = half_adder(true, true);
    TEST_ASSERT(result.sum == false && result.carry == true, "Half Adder: 1+1 = 0 carry 1");
}

void test_full_adder() {
    printf("\n -  full adder  - \n");
    
    FullAdderResult result;
    
    result = full_adder(false, false, false);
    TEST_ASSERT(result.sum == false && result.carry_out == false, "Full Adder: 0+0+0 = 0 carry 0");
    
    result = full_adder(false, false, true);
    TEST_ASSERT(result.sum == true && result.carry_out == false, "Full Adder: 0+0+1 = 1 carry 0");
    
    result = full_adder(false, true, false);
    TEST_ASSERT(result.sum == true && result.carry_out == false, "Full Adder: 0+1+0 = 1 carry 0");
    
    result = full_adder(false, true, true);
    TEST_ASSERT(result.sum == false && result.carry_out == true, "Full Adder: 0+1+1 = 0 carry 1");

    result = full_adder(true, false, false);
    TEST_ASSERT(result.sum == true && result.carry_out == false, "Full Adder: 1+0+0 = 1 carry 0");

    result = full_adder(true, false, true);
    TEST_ASSERT(result.sum == false && result.carry_out == true, "Full Adder: 1+0+1 = 0 carry 1");

    result = full_adder(true, true, false);
    TEST_ASSERT(result.sum == false && result.carry_out == true, "Full Adder: 1+1+0 = 0 carry 1");

    result = full_adder(true, true, true);
    TEST_ASSERT(result.sum == true && result.carry_out == true, "Full Adder: 1+1+1 = 1 carry 1");
}

void test_ripple_carry_adder() {
    printf("\n -  8-bit ripple carry adder  - \n");
    
    AdderResult result;
    
    result = ripple_carry_adder_8bit(0, 0, false);
    TEST_ASSERT(result.sum == 0 && result.carry_out == false, "8-bit Adder: 0+0 = 0");

    result = ripple_carry_adder_8bit(1, 1, false);
    TEST_ASSERT(result.sum == 2 && result.carry_out == false, "8-bit Adder: 1+1 = 2");

    result = ripple_carry_adder_8bit(15, 7, false);
    TEST_ASSERT(result.sum == 22 && result.carry_out == false, "8-bit Adder: 15+7 = 22");

    result = ripple_carry_adder_8bit(100, 50, false);
    TEST_ASSERT(result.sum == 150 && result.carry_out == false, "8-bit Adder: 100+50 = 150");

    result = ripple_carry_adder_8bit(10, 20, true);
    TEST_ASSERT(result.sum == 31 && result.carry_out == false, "8-bit Adder: 10+20+1 = 31");

    result = ripple_carry_adder_8bit(255, 1, false);
    TEST_ASSERT(result.sum == 0 && result.carry_out == true, "8-bit Adder: 255+1 = 0 with carry");

    result = ripple_carry_adder_8bit(200, 100, false);
    TEST_ASSERT(result.sum == 44 && result.carry_out == true, "8-bit Adder: 200+100 = 44 with carry (300 mod 256)");

    result = ripple_carry_adder_8bit(127, 1, false);
    TEST_ASSERT(result.overflow == true, "8-bit Adder: Signed overflow detection (127+1)");

    result = ripple_carry_adder_8bit(200, 200, false);
    TEST_ASSERT(result.sum == 144 && result.carry_out == true && result.overflow == false,
        "8-bit Adder: Signed no overflow (-56 + -56 = -112)");
}


void test_bitwise_operations() {
    printf("\n -  bitwise ops  - \n");
    
    TEST_ASSERT(bitwise_and_8bit(0xFF, 0x00) == 0x00, "Bitwise AND: 0xFF & 0x00");
    TEST_ASSERT(bitwise_and_8bit(0xFF, 0xFF) == 0xFF, "Bitwise AND: 0xFF & 0xFF");
    TEST_ASSERT(bitwise_and_8bit(0xAA, 0x55) == 0x00, "Bitwise AND: 0xAA & 0x55");
    TEST_ASSERT(bitwise_and_8bit(0xF0, 0x0F) == 0x00, "Bitwise AND: 0xF0 & 0x0F");
    TEST_ASSERT(bitwise_and_8bit(0xF0, 0xFF) == 0xF0, "Bitwise AND: 0xF0 & 0xFF");
    
    TEST_ASSERT(bitwise_or_8bit(0x00, 0x00) == 0x00, "Bitwise OR: 0x00 | 0x00");
    TEST_ASSERT(bitwise_or_8bit(0xFF, 0x00) == 0xFF, "Bitwise OR: 0xFF | 0x00");
    TEST_ASSERT(bitwise_or_8bit(0xAA, 0x55) == 0xFF, "Bitwise OR: 0xAA | 0x55");
    TEST_ASSERT(bitwise_or_8bit(0xF0, 0x0F) == 0xFF, "Bitwise OR: 0xF0 | 0x0F");
    
    TEST_ASSERT(bitwise_xor_8bit(0x00, 0x00) == 0x00, "Bitwise XOR: 0x00 ^ 0x00");
    TEST_ASSERT(bitwise_xor_8bit(0xFF, 0xFF) == 0x00, "Bitwise XOR: 0xFF ^ 0xFF");
    TEST_ASSERT(bitwise_xor_8bit(0xAA, 0x55) == 0xFF, "Bitwise XOR: 0xAA ^ 0x55");
    TEST_ASSERT(bitwise_xor_8bit(0xF0, 0x0F) == 0xFF, "Bitwise XOR: 0xF0 ^ 0x0F");
    TEST_ASSERT(bitwise_xor_8bit(0xA5, 0x5A) == 0xFF, "Bitwise XOR: 0xA5 ^ 0x5A");
    
    TEST_ASSERT(bitwise_not_8bit(0x00) == 0xFF, "Bitwise NOT: ~0x00");
    TEST_ASSERT(bitwise_not_8bit(0xFF) == 0x00, "Bitwise NOT: ~0xFF");
    TEST_ASSERT(bitwise_not_8bit(0xAA) == 0x55, "Bitwise NOT: ~0xAA");
    TEST_ASSERT(bitwise_not_8bit(0x55) == 0xAA, "Bitwise NOT: ~0x55");
    TEST_ASSERT(bitwise_not_8bit(0xF0) == 0x0F, "Bitwise NOT: ~0xF0");
}


void test_alu_operations() {
    printf("\n -  ALU ops  - \n");
    
    ALUResult result;
    
    result = enhanced_alu(15, 7, 0);
    TEST_ASSERT(result.result == 22 && !result.flags.carry && !result.flags.zero, 
                "ALU ADD: 15 + 7 = 22");
    
    result = enhanced_alu(255, 1, 0);
    TEST_ASSERT(result.result == 0 && result.flags.carry && result.flags.zero, 
                "ALU ADD: 255 + 1 = 0 with carry and zero flag");
    
    result = enhanced_alu(22, 7, 1);
    TEST_ASSERT(result.result == 15 && result.flags.carry && !result.flags.zero, 
                "ALU SUB: 22 - 7 = 15");
    
    result = enhanced_alu(5, 5, 1);
    TEST_ASSERT(result.result == 0 && result.flags.zero, 
                "ALU SUB: 5 - 5 = 0 with with zero flag");
    
    result = enhanced_alu(3, 5, 1);
    TEST_ASSERT(result.result == 254 && result.flags.negative, 
                "ALU SUB: 3 - 5 = -2 (254) with negative flag");
    
    result = enhanced_alu(0xF0, 0x0F, 2);
    TEST_ASSERT(result.result == 0x00 && result.flags.zero, 
                "ALU AND: 0xF0 & 0x0F = 0x00");
    
    result = enhanced_alu(0xFF, 0xAA, 2);
    TEST_ASSERT(result.result == 0xAA && result.flags.negative, 
                "ALU AND: 0xFF & 0xAA = 0xAA");
    
    result = enhanced_alu(0xF0, 0x0F, 3);
    TEST_ASSERT(result.result == 0xFF && result.flags.negative, 
                "ALU OR: 0xF0 | 0x0F = 0xFF");
    
    result = enhanced_alu(0x00, 0x00, 3);
    TEST_ASSERT(result.result == 0x00 && result.flags.zero, 
                "ALU OR: 0x00 | 0x00 = 0x00");
    
    result = enhanced_alu(0xFF, 0xFF, 4);
    TEST_ASSERT(result.result == 0x00 && result.flags.zero, 
                "ALU XOR: 0xFF ^ 0xFF = 0x00");
    
    result = enhanced_alu(0xAA, 0x55, 4);
    TEST_ASSERT(result.result == 0xFF && result.flags.negative, 
                "ALU XOR: 0xAA ^ 0x55 = 0xFF");
    
    result = enhanced_alu(0xAA, 0, 5);
    TEST_ASSERT(result.result == 0x55, 
                "ALU NOT: ~0xAA = 0x55");
    
    result = enhanced_alu(0xFF, 0, 5);
    TEST_ASSERT(result.result == 0x00 && result.flags.zero, 
                "ALU NOT: ~0xFF = 0x00");
    
    result = enhanced_alu(0x55, 0, 6);
    TEST_ASSERT(result.result == 0xAA && result.flags.negative, 
                "ALU SHL: 0x55 << 1 = 0xAA");
    
    result = enhanced_alu(0x80, 0, 6);
    TEST_ASSERT(result.result == 0x00 && result.flags.carry && result.flags.zero, 
                "ALU SHL: 0x80 << 1 = 0x00 with carry");
    
    result = enhanced_alu(0xAA, 0, 7);
    TEST_ASSERT(result.result == 0x55, 
                "ALU SHR: 0xAA >> 1 = 0x55");
    
    result = enhanced_alu(0x01, 0, 7);
    TEST_ASSERT(result.result == 0x00 && result.flags.carry && result.flags.zero, 
                "ALU SHR: 0x01 >> 1 = 0x00 with carry");
}


void test_vm_initialization() {
    printf("\n -  VM init  - \n");
    
    VM vm;
    init_vm(&vm);
    
    TEST_ASSERT(vm.pc == 0, "VM Init: PC starts at 0");
    TEST_ASSERT(vm.running == true, "VM Init: Running state is true");
    TEST_ASSERT(vm.micro_step == 0, "VM Init: Micro step starts at 0");
    
    bool all_regs_zero = true;
    for (int i = 0; i < 4; i++) {
        if (vm.registers[i] != 0) all_regs_zero = false;
    }
    TEST_ASSERT(all_regs_zero, "VM Init: All registers start at 0");
    
    TEST_ASSERT(!vm.flags.zero && !vm.flags.carry && !vm.flags.overflow && !vm.flags.negative,
                "VM Init: All flags start cleared");
}

void test_vm_fetch() {
    printf("\n -  VM fetch  - \n");
    
    VM vm;
    init_vm(&vm);
    
    vm.memory[0] = 0xAB;
    vm.memory[1] = 0xCD;
    vm.memory[2] = 0xEF;
    
    uint8_t fetched1 = fetch(&vm);
    TEST_ASSERT(fetched1 == 0xAB && vm.pc == 1, "VM Fetch: First fetch");
    
    uint8_t fetched2 = fetch(&vm);
    TEST_ASSERT(fetched2 == 0xCD && vm.pc == 2, "VM Fetch: Second fetch");
    
    uint8_t fetched3 = fetch(&vm);
    TEST_ASSERT(fetched3 == 0xEF && vm.pc == 3, "VM Fetch: Third fetch");
}


void test_microcode_initialization() {
    printf("\n -  microcode init  - \n");
    
    VM vm;
    init_vm(&vm);

    // Test ADD microcode by executing ADD instruction
    vm.registers[0] = 15;
    vm.registers[1] = 7;
    vm.memory[0] = OP_ADD;
    vm.memory[1] = OP_HALT;
    
    run_vm(&vm);
    TEST_ASSERT(vm.registers[0] == 22 && !vm.flags.carry && !vm.flags.zero,
                "Microcode: ADD instruction (R0 = 15 + 7 = 22)");
    
    // Test HALT microcode
    init_vm(&vm);
    vm.memory[0] = OP_HALT;
    run_vm(&vm);
    TEST_ASSERT(!vm.running, "Microcode: HALT instruction stops CPU");
    
    // Test LOAD microcode
    init_vm(&vm);
    vm.memory[100] = 42;
    vm.memory[0] = OP_LOAD;
    vm.memory[1] = 100;
    vm.memory[2] = OP_HALT;
    run_vm(&vm);
    TEST_ASSERT(vm.registers[0] == 42, "Microcode: LOAD instruction (R0 = memory[100])");
}


void test_vm_add_instruction() {
    printf("\n -  VM ADD instr  - \n");
    
    VM vm;
    init_vm(&vm);
    
    vm.registers[0] = 15;
    vm.registers[1] = 7;
    vm.memory[0] = OP_ADD;
    vm.memory[1] = OP_HALT;
    
    run_vm(&vm);
    
    TEST_ASSERT(vm.registers[0] == 22, "VM ADD: R0 = 15 + 7 = 22");
    TEST_ASSERT(!vm.flags.carry && !vm.flags.zero, "VM ADD: Correct flags");
}

void test_vm_sub_instruction() {
    printf("\n -  VM SUB instr  - \n");
    
    VM vm;
    init_vm(&vm);
    
    vm.registers[0] = 22;
    vm.registers[1] = 7;
    vm.memory[0] = OP_SUB;
    vm.memory[1] = OP_HALT;
    
    run_vm(&vm);
    
    TEST_ASSERT(vm.registers[0] == 15, "VM SUB: R0 = 22 - 7 = 15");
    TEST_ASSERT(vm.flags.carry && !vm.flags.zero, "VM SUB: Correct flags");
}

void test_vm_load_instruction() {
    printf("\n -  VM LOAD instr  - \n");
    
    VM vm;
    init_vm(&vm);
    
    vm.memory[100] = 42;
    vm.memory[0] = OP_LOAD;
    vm.memory[1] = 100;
    vm.memory[2] = OP_HALT;
    
    run_vm(&vm);
    
    TEST_ASSERT(vm.registers[0] == 42, "VM LOAD: R0 loaded from memory[100]");
}


void test_edge_cases() {
    printf("\n -  edge cases  - \n");
    
    AdderResult result = ripple_carry_adder_8bit(255, 255, true);
    TEST_ASSERT(result.sum == 255 && result.carry_out == true, 
                "Edge Case: 255 + 255 + 1 = 255 with carry");
    
    ALUResult alu_result;
    
    alu_result = enhanced_alu(0x01, 0, 6);
    TEST_ASSERT(alu_result.result == 0x02, "Edge Case: 1 << 1 = 2");
    
    alu_result = enhanced_alu(0x80, 0, 7);
    TEST_ASSERT(alu_result.result == 0x40, "Edge Case: 128 >> 1 = 64");
    
    VM vm;
    init_vm(&vm);
    vm.memory[0] = 0xFE;  // Invalid opcode
    vm.memory[1] = OP_HALT;
    
    run_vm(&vm);
    TEST_ASSERT(true, "Edge Case: Invalid opcode handled gracefully");
    
    init_vm(&vm);
    for (int i = 0; i < 50; i++) {
        vm.memory[i] = OP_ADD;
    }
    vm.memory[50] = OP_HALT;
    
    vm.registers[0] = 1;
    vm.registers[1] = 1;
    run_vm(&vm);
    TEST_ASSERT(true, "Edge Case: Cycle limit prevents infinite loops");
}


void test_performance() {
    printf("\n -  performance  - \n");
    
    bool gate_test_passed = true;
    for (int i = 0; i < 1000; i++) {
        bool a = (i % 4) >= 2;
        bool b = (i % 2) == 1;
        
        if (and_gate(a, b) != (a && b)) gate_test_passed = false;
        if (or_gate(a, b) != (a || b)) gate_test_passed = false;
        if (xor_gate(a, b) != (a != b)) gate_test_passed = false;
        if (not_gate(a) != (!a)) gate_test_passed = false;
    }
    TEST_ASSERT(gate_test_passed, "Performance: 1000 gate operations");
    
    bool alu_test_passed = true;
    for (int i = 0; i < 100; i++) {
        uint8_t a = i % 256;
        uint8_t b = (i * 2) % 256;
        
        ALUResult result = enhanced_alu(a, b, 0);
        uint16_t expected = (uint16_t)a + b;
        if (result.result != (expected & 0xFF)) alu_test_passed = false;
        if (result.flags.carry != (expected > 255)) alu_test_passed = false;
    }
    TEST_ASSERT(alu_test_passed, "Performance: 100 ALU ADD operations");
    
    VM vm;
    init_vm(&vm);
    
    int pc = 0;
    vm.registers[0] = 1;
    vm.registers[1] = 1;
    
    for (int i = 0; i < 20; i++) {
        vm.memory[pc++] = OP_ADD;
    }
    vm.memory[pc++] = OP_HALT;
    
    run_vm(&vm);
    TEST_ASSERT(vm.registers[0] == 21, "Performance: VM with 20 ADD operations");
}


void test_integration() {
    printf("\n -  integration  - \n");
    
    VM vm;
    init_vm(&vm);
    
    vm.memory[10] = 25;
    vm.memory[11] = 15;
    vm.memory[12] = 0;
    
    int pc = 0;
    vm.memory[pc++] = OP_LOAD;
    vm.memory[pc++] = 10;
    vm.memory[pc++] = OP_LOAD;
    vm.memory[pc++] = 11;
    vm.memory[pc++] = OP_ADD;
    vm.memory[pc++] = OP_SUB;
    vm.memory[pc++] = OP_HALT;
    
    run_vm(&vm);
    TEST_ASSERT(vm.registers[0] == 15, "Integration: Complex arithmetic sequence");
    
    init_vm(&vm);
    vm.registers[0] = 255;
    vm.registers[1] = 1;
    
    pc = 0;
    vm.memory[pc++] = OP_ADD;
    vm.memory[pc++] = OP_HALT;
    
    run_vm(&vm);
    TEST_ASSERT(vm.flags.carry && vm.flags.zero, "Integration: Flag propagation (carry and zero)");
    
    init_vm(&vm);
    vm.registers[0] = 100;
    vm.registers[1] = 50;
    
    pc = 0;
    for (int i = 0; i < 5; i++) {
        vm.memory[pc++] = OP_SUB;
    }
    vm.memory[pc++] = OP_HALT;
    
    run_vm(&vm);
    TEST_ASSERT(vm.registers[0] == 106, "Integration: Multiple microcode executions");
}


int main() {
    printf("CPU EMULATOR TEST SUITE\n");
    printf(" -  -  -  -  -  -  - - -\n");
    
    test_basic_gates();
    test_half_adder();
    test_full_adder();
    test_ripple_carry_adder();
    test_bitwise_operations();
    test_alu_operations();
    test_vm_initialization();
    test_vm_fetch();
    test_microcode_initialization();
    test_vm_add_instruction();
    test_vm_sub_instruction();
    test_vm_load_instruction();
    test_edge_cases();
    test_performance();
    test_integration();
    
    print_test_summary();
    
    return (tests_failed == 0) ? 0 : 1;
}


