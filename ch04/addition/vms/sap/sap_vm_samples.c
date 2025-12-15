#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>
#include <stdint.h>
#include "sap_vm.h"
#include "sap_vm_config.h"
#include "sap_vm_samples.h"

typedef struct {
    const char *name;
    const char *alias;
    void (*loader)(sap_vm_t *vm);
    const char *description;
} sample_program_t;

static void load_fibonacci_program(sap_vm_t *vm);
static void load_factorial_program(sap_vm_t *vm);
static void load_subroutine_demo(sap_vm_t *vm);
static void load_counting_demo(sap_vm_t *vm);
static void load_arithmetic_demo(sap_vm_t *vm);
static void load_simple_loop(sap_vm_t *vm);
static void load_memory_test(sap_vm_t *vm);

static const sample_program_t sample_programs[] = {
    {"fibonacci", "fib", load_fibonacci_program, "Calculate 10th Fibonacci number (iterative)"},
    {"factorial", "fact", load_factorial_program, "Calculate 5! factorial (iterative)"},
    {"subroutine", "sub", load_subroutine_demo, "Subroutine call demo (6 * 7 = 42)"},
    {"counting", "count", load_counting_demo, "Simple counting loop (1 to 10)"},
    {"arithmetic", "arith", load_arithmetic_demo, "Arithmetic operations demo"},
    {"loop", "lp", load_simple_loop, "Simple loop test"},
    {"memtest", "mt", load_memory_test, "Memory access test"},
    {NULL, NULL, NULL, NULL}
};

void print_sample_programs(void) {
    for (const sample_program_t *prog = sample_programs; prog->name; prog++) {
        printf("  %s", prog->name);
        if (prog->alias) printf(", %s", prog->alias);
        printf("%*s - %s\n", (int)(20 - strlen(prog->name) - (prog->alias ? strlen(prog->alias) + 2 : 0)), "", prog->description);
    }
}

void cmd_load_sample(sap_vm_t *vm, const char *program_name) {
    if (!program_name || strlen(program_name) == 0) {
        printf("Available sample programs:\n");
        print_sample_programs();
        return;
    }
    
    char prog_name[64];
    strncpy(prog_name, program_name, sizeof(prog_name) - 1);
    prog_name[sizeof(prog_name) - 1] = '\0';
    
    for (char *p = prog_name; *p; p++) {
        *p = tolower(*p);
    }
    
    vm_reset(vm);
    
    for (const sample_program_t *prog = sample_programs; prog->name; prog++) {
        if (strcmp(prog_name, prog->name) == 0 || (prog->alias && strcmp(prog_name, prog->alias) == 0)) {
            prog->loader(vm);
            printf("Loaded '%s' program successfully.\n", prog->name);
            printf("Use 'disasm' to see the code, 'run' to execute.\n");
            return;
        }
    }
    
    printf("Unknown program: %s\n", program_name);
    printf("Available programs:\n");
    print_sample_programs();
}

static void load_fibonacci_program(sap_vm_t *vm) {
    uint16_t addr = PROGRAM_START;
    uint16_t data_addr = DATA_MEMORY_START;
    
    // Initialize data memory  
    vm->memory[data_addr + 0] = 10;  // n (which Fibonacci number to calculate)
    vm->memory[data_addr + 1] = 0;   // a = F(0) 
    vm->memory[data_addr + 2] = 1;   // b = F(1)
    vm->memory[data_addr + 3] = 0;   // temp for swapping
    
    // Handle n == 0: return 0
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 0);  // Load n
    vm->memory[addr++] = vm_encode_instruction(OP_CMP, ADDR_IMMEDIATE, 0);           // Compare with 0
    uint16_t return_zero_addr = addr;
    vm->memory[addr++] = vm_encode_instruction(OP_JZ, ADDR_DIRECT, 0);               // Will patch later
    
    // Handle n == 1: return 1  
    vm->memory[addr++] = vm_encode_instruction(OP_CMP, ADDR_IMMEDIATE, 1);           // Compare with 1
    uint16_t return_one_addr = addr;
    vm->memory[addr++] = vm_encode_instruction(OP_JZ, ADDR_DIRECT, 0);               // Will patch later
    
    // For n >= 2: Use n as a countdown counter
    // We'll do (n-1) iterations to get F(n)
    vm->memory[addr++] = vm_encode_instruction(OP_SUB, ADDR_IMMEDIATE, 1);           // n = n - 1 (number of iterations needed)
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 0);  // Store back to n
    
    // Main loop: repeat n-1 times
    uint16_t loop_start = addr;
    
    // temp = a + b (next Fibonacci number)
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 1);  // Load a
    vm->memory[addr++] = vm_encode_instruction(OP_ADD, ADDR_DIRECT, data_addr + 2);  // Add b  
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 3);  // Store temp
    
    // a = b
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 2);  // Load b
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 1);  // Store to a
    
    // b = temp
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 3);  // Load temp
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 2);  // Store to b
    
    // Decrement counter and check if done
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 0);  // Load counter
    vm->memory[addr++] = vm_encode_instruction(OP_SUB, ADDR_IMMEDIATE, 1);           // Decrement
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 0);  // Store back
    vm->memory[addr++] = vm_encode_instruction(OP_JNZ, ADDR_DIRECT, loop_start);     // If not zero, continue loop
    
    // Done: return final result (b contains F(n))
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 2);  // Load result
    vm->memory[addr++] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);           // Halt
    
    // Return 0 for n=0
    uint16_t return_zero_target = addr;
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_IMMEDIATE, 0);           // Load 0
    vm->memory[addr++] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);           // Halt
    
    // Return 1 for n=1  
    uint16_t return_one_target = addr;
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_IMMEDIATE, 1);           // Load 1
    vm->memory[addr++] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);           // Halt
    
    // Patch the forward jumps
    vm->memory[return_zero_addr] = vm_encode_instruction(OP_JZ, ADDR_DIRECT, return_zero_target);
    vm->memory[return_one_addr] = vm_encode_instruction(OP_JZ, ADDR_DIRECT, return_one_target);
}


static void load_factorial_program(sap_vm_t *vm) {
    uint16_t addr = PROGRAM_START;
    uint16_t data_addr = DATA_MEMORY_START + 10;
    
    // Initialize data memory
    vm->memory[data_addr + 0] = 5;   // n (calculate 5!) - will be used as countdown counter
    vm->memory[data_addr + 1] = 1;   // result (accumulator for factorial)
    
    // Handle special case n <= 1, return 1
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 0);  // Load n
    vm->memory[addr++] = vm_encode_instruction(OP_CMP, ADDR_IMMEDIATE, 0);           // Compare with 0
    uint16_t return_one_addr = addr;
    vm->memory[addr++] = vm_encode_instruction(OP_JZ, ADDR_DIRECT, 0);               // If n=0, return 1 (patch later)
    vm->memory[addr++] = vm_encode_instruction(OP_CMP, ADDR_IMMEDIATE, 1);           // Compare with 1
    uint16_t return_one_addr2 = addr;
    vm->memory[addr++] = vm_encode_instruction(OP_JZ, ADDR_DIRECT, 0);               // If n=1, return 1 (patch later)
    
    // Main loop: multiply result by current n, then decrement n
    // Continue while n > 1
    uint16_t loop_start = addr;
    
    // result = result * n
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 1);  // Load result
    vm->memory[addr++] = vm_encode_instruction(OP_MUL, ADDR_DIRECT, data_addr + 0);  // Multiply by n
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 1);  // Store back to result
    
    // Decrement n
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 0);  // Load n
    vm->memory[addr++] = vm_encode_instruction(OP_SUB, ADDR_IMMEDIATE, 1);           // Decrement
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 0);  // Store back to n
    
    // Check if n > 1 (continue if n > 1)
    vm->memory[addr++] = vm_encode_instruction(OP_SUB, ADDR_IMMEDIATE, 1);           // n - 1
    vm->memory[addr++] = vm_encode_instruction(OP_JNZ, ADDR_DIRECT, loop_start);     // If n-1 != 0 (n > 1), continue loop
    
    // Load final result and exit
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 1);  // Load final result
    vm->memory[addr++] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);           // Halt
    
    // Return 1 for n <= 1
    uint16_t return_one_target = addr;
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_IMMEDIATE, 1);           // Load 1
    vm->memory[addr++] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);           // Halt
    
    // Patch the forward jumps
    vm->memory[return_one_addr] = vm_encode_instruction(OP_JZ, ADDR_DIRECT, return_one_target);
    vm->memory[return_one_addr2] = vm_encode_instruction(OP_JZ, ADDR_DIRECT, return_one_target);
}


static void load_subroutine_demo(sap_vm_t *vm) {
    uint16_t addr = PROGRAM_START;
    uint16_t data_addr = DATA_MEMORY_START + 20;
    uint16_t sub_addr = PROGRAM_START + 20;  // Place subroutine later in memory
    
    // Initialize test data
    vm->memory[data_addr + 0] = 6;   // a
    vm->memory[data_addr + 1] = 7;   // b  
    vm->memory[data_addr + 2] = 0;   // result
    vm->memory[data_addr + 3] = 0;   // temp_a (parameter for subroutine)
    vm->memory[data_addr + 4] = 0;   // temp_b (parameter for subroutine)
    
    // Main program: Load parameters and call subroutine
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 0);  // Load a
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 3);  // Store to temp_a
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 1);  // Load b
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 4);  // Store to temp_b
    vm->memory[addr++] = vm_encode_instruction(OP_JSR, ADDR_DIRECT, sub_addr);       // Call multiply subroutine
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 2);  // Store result
    vm->memory[addr++] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);           // Halt
    
    // Multiplication subroutine: multiply temp_a * temp_b using repeated addition
    addr = sub_addr;
    vm->memory[data_addr + 5] = 0;   // counter for subroutine
    
    // Initialize accumulator to 0
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_IMMEDIATE, 0);
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 5);  // Clear counter
    
    // Loop: add temp_a to ACC, temp_b times
    uint16_t mult_loop = addr;
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 5);  // Load counter
    vm->memory[addr++] = vm_encode_instruction(OP_CMP, ADDR_DIRECT, data_addr + 4);  // Compare with temp_b
    uint16_t mult_done = addr + 2;
    vm->memory[addr++] = vm_encode_instruction(OP_JZ, ADDR_DIRECT, mult_done);       // If equal, done
    
    // Add temp_a to accumulator
    vm->memory[addr++] = vm_encode_instruction(OP_ADD, ADDR_DIRECT, data_addr + 3);  // Add temp_a
    
    // Increment counter
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 5);  // Load counter
    vm->memory[addr++] = vm_encode_instruction(OP_ADD, ADDR_IMMEDIATE, 1);           // Increment
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 5);  // Store back
    
    // Continue loop
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_IMMEDIATE, 0);           // Clear ACC for next iteration
    vm->memory[addr++] = vm_encode_instruction(OP_JMP, ADDR_DIRECT, mult_loop);      // Loop back
    
    // Return from subroutine (result should be in ACC)
    mult_done = addr;
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 3);  // Load temp_a * counter
    vm->memory[addr++] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 0);           // Return
}

static void load_counting_demo(sap_vm_t *vm) {
    uint16_t addr = PROGRAM_START;
    uint16_t data_addr = DATA_MEMORY_START + 30;
    
    // Initialize data
    vm->memory[data_addr + 0] = 10;  // limit
    vm->memory[data_addr + 1] = 0;   // counter (start at 0)
    
    // Main loop
    uint16_t loop_addr = addr;
    
    // Increment counter first
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 1);  // Load counter
    vm->memory[addr++] = vm_encode_instruction(OP_ADD, ADDR_IMMEDIATE, 1);           // Increment
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 1);  // Store back
    
    // Check if counter < limit
    vm->memory[addr++] = vm_encode_instruction(OP_SUB, ADDR_DIRECT, data_addr + 0);  // counter - limit
    uint16_t done_addr = addr + 2;
    vm->memory[addr++] = vm_encode_instruction(OP_JZ, ADDR_DIRECT, done_addr);       // If counter == limit, done
    
    // If counter < limit, continue (negative result means counter < limit)
    vm->memory[addr++] = vm_encode_instruction(OP_JMP, ADDR_DIRECT, loop_addr);      // Loop back
    
    // Load final counter value and exit
    done_addr = addr;
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 1);  // Load final counter
    vm->memory[addr++] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);           // Halt
}

static void load_arithmetic_demo(sap_vm_t *vm) {
    uint16_t addr = PROGRAM_START;
    uint16_t data_addr = DATA_MEMORY_START + 40;
    
    // Initialize test data
    vm->memory[data_addr + 0] = 12;  // a
    vm->memory[data_addr + 1] = 8;   // b  
    vm->memory[data_addr + 2] = 3;   // c
    vm->memory[data_addr + 3] = 15;  // d
    vm->memory[data_addr + 4] = 3;   // e
    vm->memory[data_addr + 5] = 2;   // f
    vm->memory[data_addr + 6] = 0;   // temp1 for (a + b) * c
    vm->memory[data_addr + 7] = 0;   // temp2 for d / e
    
    // Calculate (a + b) * c
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 0);  // Load a
    vm->memory[addr++] = vm_encode_instruction(OP_ADD, ADDR_DIRECT, data_addr + 1);  // Add b -> (a + b)
    vm->memory[addr++] = vm_encode_instruction(OP_MUL, ADDR_DIRECT, data_addr + 2);  // Multiply by c -> (a + b) * c
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 6);  // Store temp1
    
    // Calculate d / e
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 3);  // Load d
    vm->memory[addr++] = vm_encode_instruction(OP_DIV, ADDR_DIRECT, data_addr + 4);  // Divide by e -> d / e
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 7);  // Store temp2
    
    // Calculate final result: temp1 - temp2 + f
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 6);  // Load temp1
    vm->memory[addr++] = vm_encode_instruction(OP_SUB, ADDR_DIRECT, data_addr + 7);  // Subtract temp2
    vm->memory[addr++] = vm_encode_instruction(OP_ADD, ADDR_DIRECT, data_addr + 5);  // Add f
    
    vm->memory[addr++] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);           // Halt
}

static void load_simple_loop(sap_vm_t *vm) {
    uint16_t addr = PROGRAM_START;
    uint16_t data_addr = DATA_MEMORY_START + 50;
    
    // Initialize: sum = 0, i = 1
    vm->memory[data_addr + 0] = 0;   // sum
    vm->memory[data_addr + 1] = 1;   // i (counter)
    vm->memory[data_addr + 2] = 5;   // limit
    
    // Loop: sum += i; i++; while i <= limit
    uint16_t loop_start = addr;
    
    // sum += i
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 0);  // Load sum
    vm->memory[addr++] = vm_encode_instruction(OP_ADD, ADDR_DIRECT, data_addr + 1);  // Add i
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 0);  // Store sum
    
    // i++
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 1);  // Load i
    vm->memory[addr++] = vm_encode_instruction(OP_ADD, ADDR_IMMEDIATE, 1);           // Increment
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 1);  // Store i
    
    // Check if i <= limit
    vm->memory[addr++] = vm_encode_instruction(OP_SUB, ADDR_DIRECT, data_addr + 2);  // i - limit
    uint16_t done_addr = addr + 2;
    vm->memory[addr++] = vm_encode_instruction(OP_JZ, ADDR_DIRECT, done_addr);       // If i > limit, done
    
    // Continue if i <= limit (negative or zero result)
    vm->memory[addr++] = vm_encode_instruction(OP_JMP, ADDR_DIRECT, loop_start);
    
    // Load final sum and halt
    done_addr = addr;
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 0);  // Load sum
    vm->memory[addr++] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);           // Halt
}

static void load_memory_test(sap_vm_t *vm) {
    uint16_t addr = PROGRAM_START;
    uint16_t data_addr = DATA_MEMORY_START + 60;
    
    // Initialize test data
    vm->memory[data_addr + 0] = 100;  // value to store
    vm->memory[data_addr + 1] = 0;    // will hold loaded value
    
    // Store and load test
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 0);  // Load 100
    vm->memory[addr++] = vm_encode_instruction(OP_STA, ADDR_DIRECT, data_addr + 1);  // Store to second location
    vm->memory[addr++] = vm_encode_instruction(OP_LDA, ADDR_DIRECT, data_addr + 1);  // Load back
    vm->memory[addr++] = vm_encode_instruction(OP_ADD, ADDR_IMMEDIATE, 23);          // Add 23 -> 123
    vm->memory[addr++] = vm_encode_instruction(OP_RTS, ADDR_IMMEDIATE, 1);           // Halt
}


