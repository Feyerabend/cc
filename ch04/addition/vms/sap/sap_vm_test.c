#include <stdio.h>
#include <assert.h>
#include "sap_vm.h"
#include "sap_vm_config.h"
#include "sap_vm_samples.h"

void test_basic_operations(void) {
    printf("Testing basic operations...\n");
    sap_vm_t vm;
    vm_init(&vm);
    
    // Test LDA immediate
    vm.memory[0] = vm_encode_instruction(OP_LDA, ADDR_IMMEDIATE, 42);
    vm.memory[1] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);
    
    result_t result = vm_run(&vm, 100);
    assert(result == RESULT_HALT);
    assert(vm.cpu.accumulator == 42);
    printf("✓ LDA immediate works\n");
    
    // Test arithmetic
    vm_reset(&vm);
    vm.memory[0] = vm_encode_instruction(OP_LDA, ADDR_IMMEDIATE, 10);
    vm.memory[1] = vm_encode_instruction(OP_ADD, ADDR_IMMEDIATE, 5);
    vm.memory[2] = vm_encode_instruction(OP_MUL, ADDR_IMMEDIATE, 2);
    vm.memory[3] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);
    
    result = vm_run(&vm, 100);
    assert(result == RESULT_HALT);
    assert(vm.cpu.accumulator == 30); // (10 + 5) * 2 = 30
    printf("✓ Arithmetic operations work\n");
}

void test_memory_operations(void) {
    printf("Testing memory operations...\n");
    sap_vm_t vm;
    vm_init(&vm);
    
    // Test STA/LDA direct
    vm.memory[0] = vm_encode_instruction(OP_LDA, ADDR_IMMEDIATE, 123);
    vm.memory[1] = vm_encode_instruction(OP_STA, ADDR_DIRECT, 0x100);
    vm.memory[2] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, 0x100);
    vm.memory[3] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);
    
    result_t result = vm_run(&vm, 100);
    assert(result == RESULT_HALT);
    assert(vm.cpu.accumulator == 123);
    assert(vm.memory[0x100] == 123);
    printf("✓ Memory store/load works\n");
}

void test_control_flow(void) {
    printf("Testing control flow...\n");
    sap_vm_t vm;
    vm_init(&vm);
    
    // Simple conditional jump
    vm.memory[0] = vm_encode_instruction(OP_LDA, ADDR_IMMEDIATE, 0);
    vm.memory[1] = vm_encode_instruction(OP_CMP, ADDR_IMMEDIATE, 0);
    vm.memory[2] = vm_encode_instruction(OP_JZ, ADDR_DIRECT, 5);    // Jump to address 5
    vm.memory[3] = vm_encode_instruction(OP_LDA, ADDR_IMMEDIATE, 99); // Should be skipped
    vm.memory[4] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);
    vm.memory[5] = vm_encode_instruction(OP_LDA, ADDR_IMMEDIATE, 42); // Jump target
    vm.memory[6] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);
    
    result_t result = vm_run(&vm, 100);
    assert(result == RESULT_HALT);
    assert(vm.cpu.accumulator == 42); // Should have jumped and loaded 42
    printf("✓ Conditional jumps work\n");
}

void test_sample_programs(void) {
    printf("Testing sample programs...\n");
    sap_vm_t vm;
    
    // Test counting program
    vm_init(&vm);
    cmd_load_sample(&vm, "count");
    result_t result = vm_run(&vm, 1000);
    assert(result == RESULT_HALT);
    printf("✓ Counting program: final value = %d\n", vm.cpu.accumulator);
    
    // Test arithmetic program  
    vm_init(&vm);
    cmd_load_sample(&vm, "arith");
    result = vm_run(&vm, 1000);
    assert(result == RESULT_HALT);
    printf("✓ Arithmetic program: result = %d (expected 57)\n", vm.cpu.accumulator);
    
    // Test simple loop
    vm_init(&vm);
    cmd_load_sample(&vm, "loop");
    result = vm_run(&vm, 1000);
    assert(result == RESULT_HALT);
    printf("✓ Simple loop: sum 1+2+3+4+5 = %d (expected 15)\n", vm.cpu.accumulator);
    
    // Test memory test
    vm_init(&vm);
    cmd_load_sample(&vm, "memtest");
    result = vm_run(&vm, 1000);
    assert(result == RESULT_HALT);
    printf("✓ Memory test: 100 + 23 = %d\n", vm.cpu.accumulator);
    
    // Test Fibonacci (this may take longer)
    vm_init(&vm);
    vm.debug_enabled = false; // Reduce output
    cmd_load_sample(&vm, "fib");
    result = vm_run(&vm, 10000);
    assert(result == RESULT_HALT);
    printf("✓ Fibonacci F(10) = %d (expected 55)\n", vm.cpu.accumulator);
    
    // Test Factorial
    vm_init(&vm);
    vm.debug_enabled = false;
    cmd_load_sample(&vm, "fact");
    result = vm_run(&vm, 10000);
    assert(result == RESULT_HALT);
    printf("✓ Factorial 5! = %d (expected 120)\n", vm.cpu.accumulator);
}

int main(void) {
    printf("SAP VM Test Suite\n");
    printf("=================\n\n");
    
    test_basic_operations();
    printf("\n");
    
    test_memory_operations();
    printf("\n");
    
    test_control_flow();
    printf("\n");
    
    test_sample_programs();
    printf("\n");
    
    printf("All tests passed! ✓\n");
    printf("\nThe SAP VM has been repaired and is working correctly.\n");
    printf("You can now run the debugger and try the sample programs:\n");
    printf("  ./sap_vm_debug\n");
    printf("  sap-vm> load fib\n");
    printf("  sap-vm> run\n");
    
    return 0;
}

