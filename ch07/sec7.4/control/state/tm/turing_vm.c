#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <ctype.h>

#define MAX_TAPE 2000
#define MAX_PROGRAM 100
#define MAX_DATA 50
#define MAX_LABEL 20

/*
 * TURING MACHINE VIRTUAL MACHINE
 * 
 * A Turing-complete virtual machine with:
 * - Instruction set (LOAD, ADD, SUB, AND, OR, NOT, XOR, ..)
 * - Registers (A, B, C)
 * - Program counter
 * - Conditional jumps
 * - Labels for control flow
 * 
 * TAPE LAYOUT:
 * [PROGRAM] | [DATA] | [OUTPUT]
 */

// Instruction opcodes
typedef enum {
    OP_NOP,      // No operation
    OP_LOAD_A,   // Load next data value into A
    OP_LOAD_B,   // Load next data value into B
    OP_LOAD_C,   // Load next data value into C
    OP_STORE,    // Store A to output
    OP_ADD,      // A = A + B
    OP_SUB,      // A = A - B (with underflow handling)
    OP_AND,      // A = A & B
    OP_OR,       // A = A | B
    OP_XOR,      // A = A ^ B
    OP_NOT_A,    // A = ~A
    OP_NOT_B,    // B = ~B
    OP_COPY_AB,  // B = A
    OP_COPY_BA,  // A = B
    OP_COPY_AC,  // C = A
    OP_SWAP_AB,  // Swap A and B
    OP_JMP,      // Unconditional jump
    OP_JZ,       // Jump if A == 0
    OP_JNZ,      // Jump if A != 0
    OP_JEQ,      // Jump if A == B
    OP_HALT,     // Stop execution
    OP_INVALID
} Opcode;

// Instruction structure
typedef struct {
    Opcode op;
    int operand;  // For jumps: target instruction index
    char label[MAX_LABEL]; // For jump targets
} Instruction;

// Label mapping for jumps
typedef struct {
    char name[MAX_LABEL];
    int address;
} Label;

// VM state
typedef struct {

    // Registers (binary numbers as strings)
    char reg_a[100];
    char reg_b[100];
    char reg_c[100];
    
    // Program and data
    Instruction program[MAX_PROGRAM];
    char data[MAX_DATA][100];
    int program_size;
    int data_size;
    int data_ptr; // Points to next data to load
    
    // Control
    int pc; // Program counter
    int steps; // Step counter
    bool halted;
    
    // Output
    char output[MAX_DATA][100];
    int output_size;
    
    // Labels
    Label labels[MAX_PROGRAM];
    int label_count;
    
    bool verbose;
} VM;

// Fwd decl
void binary_add(const char *a, const char *b, char *result);
void binary_sub(const char *a, const char *b, char *result);
void binary_and(const char *a, const char *b, char *result);
void binary_or(const char *a, const char *b, char *result);
void binary_xor(const char *a, const char *b, char *result);
void binary_not(const char *input, char *result);
int binary_compare(const char *a, const char *b);

// Init VM
void vm_init(VM *vm, bool verbose) {
    strcpy(vm->reg_a, "0");
    strcpy(vm->reg_b, "0");
    strcpy(vm->reg_c, "0");
    vm->program_size = 0;
    vm->data_size = 0;
    vm->data_ptr = 0;
    vm->pc = 0;
    vm->steps = 0;
    vm->halted = false;
    vm->output_size = 0;
    vm->label_count = 0;
    vm->verbose = verbose;
}

// Helper: Remove leading zeros but keep at least one digit
void normalize_binary(char *bin) {
    if (bin[0] == '\0') {
        strcpy(bin, "0");
        return;
    }
    
    char *p = bin;
    while (*p == '0' && *(p+1) != '\0') p++;
    
    if (p != bin) {
        memmove(bin, p, strlen(p) + 1);
    }
    
    if (bin[0] == '\0') {
        strcpy(bin, "0");
    }
}

// Binary addition
void binary_add(const char *a, const char *b, char *result) {
    int len_a = strlen(a);
    int len_b = strlen(b);
    int max_len = (len_a > len_b ? len_a : len_b) + 1;
    
    char temp[200] = {0};
    int carry = 0;
    int pos = 0;
    
    int i = len_a - 1;
    int j = len_b - 1;
    
    while (i >= 0 || j >= 0 || carry) {
        int bit_a = (i >= 0) ? (a[i] - '0') : 0;
        int bit_b = (j >= 0) ? (b[j] - '0') : 0;
        
        int sum = bit_a + bit_b + carry;
        temp[pos++] = (sum % 2) + '0';
        carry = sum / 2;
        
        i--;
        j--;
    }
    
    temp[pos] = '\0';
    
    // Reverse
    for (int k = 0; k < pos; k++) {
        result[k] = temp[pos - 1 - k];
    }
    result[pos] = '\0';
    
    normalize_binary(result);
}

// Binary subtraction (returns 0 if b > a, no negative numbers)
void binary_sub(const char *a, const char *b, char *result) {
    // Simple implementation: if b > a, return 0
    if (binary_compare(b, a) > 0) {
        strcpy(result, "0");
        return;
    }
    
    int len_a = strlen(a);
    int len_b = strlen(b);
    
    char temp[200] = {0};
    int borrow = 0;
    int pos = 0;
    
    int i = len_a - 1;
    int j = len_b - 1;
    
    while (i >= 0) {
        int bit_a = a[i] - '0';
        int bit_b = (j >= 0) ? (b[j] - '0') : 0;
        
        int diff = bit_a - bit_b - borrow;
        
        if (diff < 0) {
            diff += 2;
            borrow = 1;
        } else {
            borrow = 0;
        }
        
        temp[pos++] = diff + '0';
        
        i--;
        j--;
    }
    
    temp[pos] = '\0';
    
    // Reverse
    for (int k = 0; k < pos; k++) {
        result[k] = temp[pos - 1 - k];
    }
    result[pos] = '\0';
    
    normalize_binary(result);
}

// Binary AND
void binary_and(const char *a, const char *b, char *result) {
    int len_a = strlen(a);
    int len_b = strlen(b);
    int max_len = (len_a > len_b ? len_a : len_b);
    
    char temp[200] = {0};
    int pos = 0;
    
    int i = len_a - 1;
    int j = len_b - 1;
    
    while (i >= 0 || j >= 0) {
        int bit_a = (i >= 0) ? (a[i] - '0') : 0;
        int bit_b = (j >= 0) ? (b[j] - '0') : 0;
        
        temp[pos++] = (bit_a && bit_b) ? '1' : '0';
        
        i--;
        j--;
    }
    
    temp[pos] = '\0';
    
    // Reverse
    for (int k = 0; k < pos; k++) {
        result[k] = temp[pos - 1 - k];
    }
    result[pos] = '\0';
    
    normalize_binary(result);
}

// Binary OR
void binary_or(const char *a, const char *b, char *result) {
    int len_a = strlen(a);
    int len_b = strlen(b);
    
    char temp[200] = {0};
    int pos = 0;
    
    int i = len_a - 1;
    int j = len_b - 1;
    
    while (i >= 0 || j >= 0) {
        int bit_a = (i >= 0) ? (a[i] - '0') : 0;
        int bit_b = (j >= 0) ? (b[j] - '0') : 0;
        
        temp[pos++] = (bit_a || bit_b) ? '1' : '0';
        
        i--;
        j--;
    }
    
    temp[pos] = '\0';
    
    // Reverse
    for (int k = 0; k < pos; k++) {
        result[k] = temp[pos - 1 - k];
    }
    result[pos] = '\0';
    
    normalize_binary(result);
}

// Binary XOR
void binary_xor(const char *a, const char *b, char *result) {
    int len_a = strlen(a);
    int len_b = strlen(b);
    
    char temp[200] = {0};
    int pos = 0;
    
    int i = len_a - 1;
    int j = len_b - 1;
    
    while (i >= 0 || j >= 0) {
        int bit_a = (i >= 0) ? (a[i] - '0') : 0;
        int bit_b = (j >= 0) ? (b[j] - '0') : 0;
        
        temp[pos++] = (bit_a ^ bit_b) ? '1' : '0';
        
        i--;
        j--;
    }
    
    temp[pos] = '\0';
    
    // Reverse
    for (int k = 0; k < pos; k++) {
        result[k] = temp[pos - 1 - k];
    }
    result[pos] = '\0';
    
    normalize_binary(result);
}

// Binary NOT (flip all bits)
void binary_not(const char *input, char *result) {
    int len = strlen(input);
    for (int i = 0; i < len; i++) {
        result[i] = (input[i] == '1') ? '0' : '1';
    }
    result[len] = '\0';
}

// Compare two binary numbers: returns -1 if a < b, 0 if equal, 1 if a > b
int binary_compare(const char *a, const char *b) {
    int len_a = strlen(a);
    int len_b = strlen(b);
    
    if (len_a < len_b) return -1;
    if (len_a > len_b) return 1;
    
    return strcmp(a, b);
}

// Get opcode name for display
const char* opcode_name(Opcode op) {
    switch(op) {
        case OP_NOP: return "NOP";
        case OP_LOAD_A: return "LOAD_A";
        case OP_LOAD_B: return "LOAD_B";
        case OP_LOAD_C: return "LOAD_C";
        case OP_STORE: return "STORE";
        case OP_ADD: return "ADD";
        case OP_SUB: return "SUB";
        case OP_AND: return "AND";
        case OP_OR: return "OR";
        case OP_XOR: return "XOR";
        case OP_NOT_A: return "NOT_A";
        case OP_NOT_B: return "NOT_B";
        case OP_COPY_AB: return "COPY_AB";
        case OP_COPY_BA: return "COPY_BA";
        case OP_COPY_AC: return "COPY_AC";
        case OP_SWAP_AB: return "SWAP_AB";
        case OP_JMP: return "JMP";
        case OP_JZ: return "JZ";
        case OP_JNZ: return "JNZ";
        case OP_JEQ: return "JEQ";
        case OP_HALT: return "HALT";
        default: return "INVALID";
    }
}

// Add label
void vm_add_label(VM *vm, const char *name, int address) {
    if (vm->label_count >= MAX_PROGRAM) return;
    
    strcpy(vm->labels[vm->label_count].name, name);
    vm->labels[vm->label_count].address = address;
    vm->label_count++;
}

// Find label address
int vm_find_label(VM *vm, const char *name) {
    for (int i = 0; i < vm->label_count; i++) {
        if (strcmp(vm->labels[i].name, name) == 0) {
            return vm->labels[i].address;
        }
    }
    return -1;
}

// Add instruction
void vm_add_instruction(VM *vm, Opcode op, const char *label) {
    if (vm->program_size >= MAX_PROGRAM) return;
    
    vm->program[vm->program_size].op = op;
    vm->program[vm->program_size].operand = 0;
    if (label) {
        strcpy(vm->program[vm->program_size].label, label);
    } else {
        vm->program[vm->program_size].label[0] = '\0';
    }
    vm->program_size++;
}

// Add data
void vm_add_data(VM *vm, const char *value) {
    if (vm->data_size >= MAX_DATA) return;
    strcpy(vm->data[vm->data_size], value);
    vm->data_size++;
}

// Execute one instruction
void vm_step(VM *vm) {
    if (vm->halted || vm->pc >= vm->program_size) {
        vm->halted = true;
        return;
    }
    
    Instruction *inst = &vm->program[vm->pc];
    vm->steps++;
    
    if (vm->verbose) {
        printf("  [%3d] %-10s  A=%-8s B=%-8s C=%-8s", vm->pc,
                opcode_name(inst->op), vm->reg_a, vm->reg_b, vm->reg_c);
    }
    
    char temp[200];
    
    switch (inst->op) {
        case OP_NOP:
            break;
            
        case OP_LOAD_A:
            if (vm->data_ptr < vm->data_size) {
                strcpy(vm->reg_a, vm->data[vm->data_ptr++]);
            } else {
                strcpy(vm->reg_a, "0");
            }
            break;
            
        case OP_LOAD_B:
            if (vm->data_ptr < vm->data_size) {
                strcpy(vm->reg_b, vm->data[vm->data_ptr++]);
            } else {
                strcpy(vm->reg_b, "0");
            }
            break;
            
        case OP_LOAD_C:
            if (vm->data_ptr < vm->data_size) {
                strcpy(vm->reg_c, vm->data[vm->data_ptr++]);
            } else {
                strcpy(vm->reg_c, "0");
            }
            break;
            
        case OP_STORE:
            if (vm->output_size < MAX_DATA) {
                strcpy(vm->output[vm->output_size++], vm->reg_a);
            }
            break;
            
        case OP_ADD:
            binary_add(vm->reg_a, vm->reg_b, temp);
            strcpy(vm->reg_a, temp);
            break;
            
        case OP_SUB:
            binary_sub(vm->reg_a, vm->reg_b, temp);
            strcpy(vm->reg_a, temp);
            break;
            
        case OP_AND:
            binary_and(vm->reg_a, vm->reg_b, temp);
            strcpy(vm->reg_a, temp);
            break;
            
        case OP_OR:
            binary_or(vm->reg_a, vm->reg_b, temp);
            strcpy(vm->reg_a, temp);
            break;
            
        case OP_XOR:
            binary_xor(vm->reg_a, vm->reg_b, temp);
            strcpy(vm->reg_a, temp);
            break;
            
        case OP_NOT_A:
            binary_not(vm->reg_a, temp);
            strcpy(vm->reg_a, temp);
            break;
            
        case OP_NOT_B:
            binary_not(vm->reg_b, temp);
            strcpy(vm->reg_b, temp);
            break;
            
        case OP_COPY_AB:
            strcpy(vm->reg_b, vm->reg_a);
            break;
            
        case OP_COPY_BA:
            strcpy(vm->reg_a, vm->reg_b);
            break;
            
        case OP_COPY_AC:
            strcpy(vm->reg_c, vm->reg_a);
            break;
            
        case OP_SWAP_AB:
            strcpy(temp, vm->reg_a);
            strcpy(vm->reg_a, vm->reg_b);
            strcpy(vm->reg_b, temp);
            break;
            
        case OP_JMP:
            if (inst->label[0]) {
                int addr = vm_find_label(vm, inst->label);
                if (addr >= 0) {
                    vm->pc = addr;
                    if (vm->verbose) printf("  -> jump to %d", addr);
                    if (vm->verbose) printf("\n");
                    return;
                }
            }
            break;
            
        case OP_JZ:
            if (strcmp(vm->reg_a, "0") == 0) {
                if (inst->label[0]) {
                    int addr = vm_find_label(vm, inst->label);
                    if (addr >= 0) {
                        vm->pc = addr;
                        if (vm->verbose) printf("  -> jump to %d", addr);
                        if (vm->verbose) printf("\n");
                        return;
                    }
                }
            }
            break;
            
        case OP_JNZ:
            if (strcmp(vm->reg_a, "0") != 0) {
                if (inst->label[0]) {
                    int addr = vm_find_label(vm, inst->label);
                    if (addr >= 0) {
                        vm->pc = addr;
                        if (vm->verbose) printf("  -> jump to %d", addr);
                        if (vm->verbose) printf("\n");
                        return;
                    }
                }
            }
            break;
            
        case OP_JEQ:
            if (binary_compare(vm->reg_a, vm->reg_b) == 0) {
                if (inst->label[0]) {
                    int addr = vm_find_label(vm, inst->label);
                    if (addr >= 0) {
                        vm->pc = addr;
                        if (vm->verbose) printf("  -> jump to %d", addr);
                        if (vm->verbose) printf("\n");
                        return;
                    }
                }
            }
            break;
            
        case OP_HALT:
            vm->halted = true;
            break;
            
        default:
            vm->halted = true;
            break;
    }
    
    if (vm->verbose) printf("\n");
    vm->pc++;
}

// Run until halt
void vm_run(VM *vm, int max_steps) {
    while (!vm->halted && vm->steps < max_steps) {
        vm_step(vm);
    }
}

// program listing
void vm_print_program(VM *vm) {
    printf("PROGRAM:\n");
    printf("--------\n");
    for (int i = 0; i < vm->program_size; i++) {
        printf("  [%3d] %-10s", i, opcode_name(vm->program[i].op));
        if (vm->program[i].label[0]) {
            printf(" %s", vm->program[i].label);
        }
        printf("\n");
    }
    printf("\n");
}

// data
void vm_print_data(VM *vm) {
    printf("DATA:\n");
    printf("-----\n");
    for (int i = 0; i < vm->data_size; i++) {
        printf("  [%d] %s\n", i, vm->data[i]);
    }
    printf("\n");
}

// output
void vm_print_output(VM *vm) {
    printf("OUTPUT:\n");
    printf("-------\n");
    for (int i = 0; i < vm->output_size; i++) {
        printf("  [%d] %s\n", i, vm->output[i]);
    }
    printf("\n");
}

int main(int argc, char *argv[]) {
    printf("  Turing Machine VM\n");
    printf("  Programmable ALU with Control Flow\n\n");
    
    bool verbose = false;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--verbose") == 0) {
            verbose = true;
        }
    }
    
    //  PROGRAM 1: Simple Addition 
    printf("PROGRAM 1: Simple Addition (1011 + 110)\n\n");
    {
        VM vm;
        vm_init(&vm, verbose);
        
        // Program: Load two numbers and add them
        vm_add_instruction(&vm, OP_LOAD_A, NULL);
        vm_add_instruction(&vm, OP_LOAD_B, NULL);
        vm_add_instruction(&vm, OP_ADD, NULL);
        vm_add_instruction(&vm, OP_STORE, NULL);
        vm_add_instruction(&vm, OP_HALT, NULL);
        
        // Data
        vm_add_data(&vm, "1011");  // 11
        vm_add_data(&vm, "110");   // 6
        
        if (verbose) {
            vm_print_program(&vm);
            vm_print_data(&vm);
            printf("EXEC:\n");
            printf("-----\n");
        }
        
        vm_run(&vm, 1000);
        
        printf("Result: %s (Expected: 10001)\n", vm.output[0]);
        printf("Steps: %d\n\n", vm.steps);
    }
    
    //  PROGRAM 2: Multiple Operations 
    printf("PROGRAM 2: Multiple Operations\n");
    printf("  Compute: (A + B) AND (C XOR B)\n\n");
    {
        VM vm;
        vm_init(&vm, verbose);
        
        // Program
        vm_add_instruction(&vm, OP_LOAD_A, NULL);      // A = 1010
        vm_add_instruction(&vm, OP_LOAD_B, NULL);      // B = 1100
        vm_add_instruction(&vm, OP_LOAD_C, NULL);      // C = 1111
        vm_add_instruction(&vm, OP_ADD, NULL);         // A = A + B = 10110
        vm_add_instruction(&vm, OP_COPY_AC, NULL);     // C = A = 10110
        vm_add_instruction(&vm, OP_COPY_BA, NULL);     // A = B = 1100
        vm_add_instruction(&vm, OP_LOAD_B, NULL);      // B = 1111 (reload original C)
        vm_add_instruction(&vm, OP_XOR, NULL);         // A = A XOR B = 0011
        vm_add_instruction(&vm, OP_COPY_BA, NULL);     // B = A
        vm_add_instruction(&vm, OP_COPY_AC, NULL);     // C = A (save for later)
        vm_add_instruction(&vm, OP_LOAD_A, NULL);      // A = 10110 (the sum we saved)
        vm_add_instruction(&vm, OP_COPY_AB, NULL);     // B = A
        vm_add_instruction(&vm, OP_COPY_BA, NULL);     // A = saved XOR result
        vm_add_instruction(&vm, OP_LOAD_B, NULL);      // B = 10110
        vm_add_instruction(&vm, OP_AND, NULL);         // A = 10110 AND 0011
        vm_add_instruction(&vm, OP_STORE, NULL);
        vm_add_instruction(&vm, OP_HALT, NULL);
        
        // Data
        vm_add_data(&vm, "1010");  // A
        vm_add_data(&vm, "1100");  // B
        vm_add_data(&vm, "1111");  // C
        vm_add_data(&vm, "1111");  // Original C for XOR
        vm_add_data(&vm, "10110"); // Sum result
        vm_add_data(&vm, "10110"); // Sum result again
        
        if (verbose) {
            vm_print_program(&vm);
            vm_print_data(&vm);
            printf("EXEC:\n");
            printf("-----\n");
        }
        
        vm_run(&vm, 1000);
        
        printf("Result: %s\n", vm.output[0]);
        printf("Steps: %d\n\n", vm.steps);
    }
    
    //  PROGRAM 3: Loop with Conditional 
    printf("PROGRAM 3: Countdown Loop\n");
    printf("  Count down from 5 to 0\n\n");
    {
        VM vm;
        vm_init(&vm, verbose);
        
        // Labels
        vm_add_label(&vm, "LOOP", 1);
        vm_add_label(&vm, "END", 5);
        
        // Program
        vm_add_instruction(&vm, OP_LOAD_A, NULL);      // A = 101 (5)
        vm_add_instruction(&vm, OP_STORE, NULL);       // LOOP: Store current value
        vm_add_instruction(&vm, OP_LOAD_B, NULL);      // B = 1 (decrement)
        vm_add_instruction(&vm, OP_SUB, NULL);         // A = A - 1
        vm_add_instruction(&vm, OP_JNZ, "LOOP");       // If A != 0, jump to LOOP
        vm_add_instruction(&vm, OP_STORE, NULL);       // END: Store final 0
        vm_add_instruction(&vm, OP_HALT, NULL);
        
        // Data
        vm_add_data(&vm, "101");   // 5
        for (int i = 0; i < 10; i++) {
            vm_add_data(&vm, "1");  // Decrement value
        }
        
        if (verbose) {
            vm_print_program(&vm);
            vm_print_data(&vm);
            printf("EXEC:\n");
            printf("-----\n");
        }
        
        vm_run(&vm, 1000);
        
        printf("Output sequence: ");
        for (int i = 0; i < vm.output_size; i++) {
            printf("%s ", vm.output[i]);
        }
        printf("\n");
        printf("Steps: %d\n\n", vm.steps);
    }
    
    //  PROGRAM 4: Bit Manipulation 
    printf("PROGRAM 4: Bit Manipulation Chain\n");
    printf("  Apply XOR, NOT, AND operations\n\n");
    {
        VM vm;
        vm_init(&vm, verbose);
        
        // Program: (A XOR B), then NOT result, then AND with C
        vm_add_instruction(&vm, OP_LOAD_A, NULL);      // A = 1010
        vm_add_instruction(&vm, OP_LOAD_B, NULL);      // B = 1100
        vm_add_instruction(&vm, OP_XOR, NULL);         // A = 1010 XOR 1100 = 0110
        vm_add_instruction(&vm, OP_STORE, NULL);       // Store XOR result
        vm_add_instruction(&vm, OP_NOT_A, NULL);       // A = NOT 0110 = 1001
        vm_add_instruction(&vm, OP_STORE, NULL);       // Store NOT result
        vm_add_instruction(&vm, OP_LOAD_B, NULL);      // B = 1111
        vm_add_instruction(&vm, OP_AND, NULL);         // A = 1001 AND 1111 = 1001
        vm_add_instruction(&vm, OP_STORE, NULL);       // Store final result
        vm_add_instruction(&vm, OP_HALT, NULL);
        
        // Data
        vm_add_data(&vm, "1010");
        vm_add_data(&vm, "1100");
        vm_add_data(&vm, "1111");
        
        if (verbose) {
            vm_print_program(&vm);
            vm_print_data(&vm);
            printf("EXEC:\n");
            printf("-----\n");
        }
        
        vm_run(&vm, 1000);
        
        printf("Results:\n");
        printf("  XOR:   %s\n", vm.output[0]);
        printf("  NOT:   %s\n", vm.output[1]);
        printf("  Final: %s\n", vm.output[2]);
        printf("Steps: %d\n\n", vm.steps);
    }
    
    printf("All done.\n\n");
    printf("Usage: %s [-v|--verbose]\n", argv[0]);
    printf("   -v, --verbose: Show step-by-step execution with register states\n\n");
    
    return 0;
}
