#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

// VM Instructions
typedef enum {
    OP_PUSH,      // Push value onto stack
    OP_POP,       // Pop value from stack
    OP_ADD,       // Add two values
    OP_SUB,       // Subtract
    OP_PRINT,     // Print top of stack
    OP_YIELD,     // Suspend coroutine, yield control
    OP_CALL,      // Call another coroutine
    OP_RETURN,    // Return from coroutine
    OP_HALT,      // Stop execution
    OP_JMP,       // Jump to address
    OP_JZ,        // Jump if zero
    OP_LOAD,      // Load from local variable
    OP_STORE,     // Store to local variable
} OpCode;

// Coroutine states
typedef enum {
    CO_READY,     // Ready to run
    CO_RUNNING,   // Currently running
    CO_SUSPENDED, // Suspended (yielded)
    CO_DEAD,      // Finished execution
} CoState;

#define STACK_SIZE 256
#define MAX_LOCALS 16
#define MAX_COROUTINES 8

// Coroutine structure
typedef struct {
    int id;
    CoState state;
    uint8_t *code;        // Bytecode
    int code_size;
    int pc;               // Program counter
    int stack[STACK_SIZE];
    int sp;               // Stack pointer
    int locals[MAX_LOCALS]; // Local variables
    int resume_value;     // Value to resume with
} Coroutine;

// Virtual Machine
typedef struct {
    Coroutine coroutines[MAX_COROUTINES];
    int num_coroutines;
    int current_coroutine;
} VM;

// Init VM
void vm_init(VM *vm) {
    vm->num_coroutines = 0;
    vm->current_coroutine = -1;
}

// Create a new coroutine
int vm_create_coroutine(VM *vm, uint8_t *code, int code_size) {
    if (vm->num_coroutines >= MAX_COROUTINES) {
        printf("Error: Maximum coroutines reached\n");
        return -1;
    }
    
    Coroutine *co = &vm->coroutines[vm->num_coroutines];
    co->id = vm->num_coroutines;
    co->state = CO_READY;
    co->code = malloc(code_size);
    memcpy(co->code, code, code_size);
    co->code_size = code_size;
    co->pc = 0;
    co->sp = 0;
    co->resume_value = 0;
    memset(co->locals, 0, sizeof(co->locals));
    
    return vm->num_coroutines++;
}

// Push value onto stack
void stack_push(Coroutine *co, int value) {
    if (co->sp >= STACK_SIZE) {
        printf("Error: Stack overflow in coroutine %d\n", co->id);
        exit(1);
    }
    co->stack[co->sp++] = value;
}

// Pop value from stack
int stack_pop(Coroutine *co) {
    if (co->sp <= 0) {
        printf("Error: Stack underflow in coroutine %d\n", co->id);
        exit(1);
    }
    return co->stack[--co->sp];
}

// Read next byte from code
uint8_t read_byte(Coroutine *co) {
    return co->code[co->pc++];
}

// Read next int (4 bytes) from code
int read_int(Coroutine *co) {
    int value = *(int *)&co->code[co->pc];
    co->pc += 4;
    return value;
}

// Execute one step of a coroutine
// Returns 1 to continue, 0 to yield/halt
int vm_step(VM *vm, Coroutine *co) {
    if (co->pc >= co->code_size) {
        co->state = CO_DEAD;
        return 0;
    }
    
    OpCode op = read_byte(co);
    
    switch (op) {
        case OP_PUSH: {
            int value = read_int(co);
            stack_push(co, value);
            break;
        }
        
        case OP_POP:
            stack_pop(co);
            break;
        
        case OP_ADD: {
            int b = stack_pop(co);
            int a = stack_pop(co);
            stack_push(co, a + b);
            break;
        }
        
        case OP_SUB: {
            int b = stack_pop(co);
            int a = stack_pop(co);
            stack_push(co, a - b);
            break;
        }
        
        case OP_PRINT: {
            int value = stack_pop(co);
            printf("[Coroutine %d] Value: %d\n", co->id, value);
            break;
        }
        
        case OP_YIELD:
            printf("[Coroutine %d] Yielding..\n", co->id);
            co->state = CO_SUSPENDED;
            return 0; // Stop execution
        
        case OP_RETURN:
            printf("[Coroutine %d] Returning\n", co->id);
            co->state = CO_DEAD;
            return 0;
        
        case OP_HALT:
            co->state = CO_DEAD;
            return 0;
        
        case OP_JMP: {
            int addr = read_int(co);
            co->pc = addr;
            break;
        }
        
        case OP_JZ: {
            int addr = read_int(co);
            int value = stack_pop(co);
            if (value == 0) {
                co->pc = addr;
            }
            break;
        }
        
        case OP_LOAD: {
            int index = read_int(co);
            stack_push(co, co->locals[index]);
            break;
        }
        
        case OP_STORE: {
            int index = read_int(co);
            co->locals[index] = stack_pop(co);
            break;
        }
        
        default:
            printf("Error: Unknown opcode %d\n", op);
            co->state = CO_DEAD;
            return 0;
    }
    
    return 1; // Continue execution
}

// Resume a coroutine
void vm_resume(VM *vm, int co_id) {
    if (co_id < 0 || co_id >= vm->num_coroutines) {
        printf("Error: Invalid coroutine ID %d\n", co_id);
        return;
    }
    
    Coroutine *co = &vm->coroutines[co_id];
    
    if (co->state == CO_DEAD) {
        printf("[Coroutine %d] Already finished\n", co_id);
        return;
    }
    
    if (co->state == CO_SUSPENDED) {
        printf("[Coroutine %d] Resuming...\n", co_id);
        co->state = CO_RUNNING;
    } else if (co->state == CO_READY) {
        printf("[Coroutine %d] Starting...\n", co_id);
        co->state = CO_RUNNING;
    }
    
    vm->current_coroutine = co_id;
    
    // Execute until yield or halt
    while (co->state == CO_RUNNING && vm_step(vm, co)) {
        // Keep executing
    }
    
    vm->current_coroutine = -1;
}

// Helper function to write bytecode
void write_byte(uint8_t **ptr, uint8_t byte) {
    **ptr = byte;
    (*ptr)++;
}

void write_int(uint8_t **ptr, int value) {
    *(int *)*ptr = value;
    *ptr += 4;
}

// Cleanup
void vm_cleanup(VM *vm) {
    for (int i = 0; i < vm->num_coroutines; i++) {
        free(vm->coroutines[i].code);
    }
}

int main() {
    printf("Coroutine Virtual Machine Demo\n\n");
    
    VM vm;
    vm_init(&vm);
    
    // Coroutine 1: Counter that yields after each count
    uint8_t code1[256];
    uint8_t *p1 = code1;
    
    // for (i = 0; i < 5; i++) { print(i); yield; }
    write_byte(&p1, OP_PUSH);  write_int(&p1, 0);     // i = 0
    write_byte(&p1, OP_STORE); write_int(&p1, 0);     // store in local[0]
    
    int loop_start = p1 - code1;
    write_byte(&p1, OP_LOAD);  write_int(&p1, 0);     // load i
    write_byte(&p1, OP_PUSH);  write_int(&p1, 5);     // check if >= 5
    write_byte(&p1, OP_SUB);                          // i - 5
    int end_check1 = p1 - code1;
    write_byte(&p1, OP_JZ);    write_int(&p1, 0);     // will patch later
    
    write_byte(&p1, OP_LOAD);  write_int(&p1, 0);     // load i
    write_byte(&p1, OP_PRINT);                        // print i
    write_byte(&p1, OP_YIELD);                        // yield control
    
    write_byte(&p1, OP_LOAD);  write_int(&p1, 0);     // load i
    write_byte(&p1, OP_PUSH);  write_int(&p1, 1);     // push 1
    write_byte(&p1, OP_ADD);                          // i + 1
    write_byte(&p1, OP_STORE); write_int(&p1, 0);     // store i
    
    write_byte(&p1, OP_JMP);   write_int(&p1, loop_start); // loop
    
    int end_addr1 = p1 - code1;
    *(int *)&code1[end_check1 + 1] = end_addr1;  // patch jump address
    
    write_byte(&p1, OP_RETURN);
    
    int co1 = vm_create_coroutine(&vm, code1, p1 - code1);
    
    // Coroutine 2: Different counter
    uint8_t code2[256];
    uint8_t *p2 = code2;
    
    // for (i = 100; i < 103; i++) { print(i); yield; }
    write_byte(&p2, OP_PUSH);  write_int(&p2, 100);   // i = 100
    write_byte(&p2, OP_STORE); write_int(&p2, 0);
    
    int loop_start2 = p2 - code2;
    write_byte(&p2, OP_LOAD);  write_int(&p2, 0);     // load i
    write_byte(&p2, OP_PUSH);  write_int(&p2, 103);   // check if >= 103
    write_byte(&p2, OP_SUB);                          // i - 103
    int end_check = p2 - code2;
    write_byte(&p2, OP_JZ);    write_int(&p2, 0);     // will fill in later
    
    write_byte(&p2, OP_LOAD);  write_int(&p2, 0);
    write_byte(&p2, OP_PRINT);
    write_byte(&p2, OP_YIELD);
    
    write_byte(&p2, OP_LOAD);  write_int(&p2, 0);
    write_byte(&p2, OP_PUSH);  write_int(&p2, 1);
    write_byte(&p2, OP_ADD);
    write_byte(&p2, OP_STORE); write_int(&p2, 0);
    
    write_byte(&p2, OP_JMP);   write_int(&p2, loop_start2);
    
    int end_addr = p2 - code2;
    *(int *)&code2[end_check + 1] = end_addr;  // patch jump address
    
    write_byte(&p2, OP_RETURN);
    
    int co2 = vm_create_coroutine(&vm, code2, p2 - code2);
    
    // Coroutine 3: Simple calculator
    uint8_t code3[128];
    uint8_t *p3 = code3;
    
    write_byte(&p3, OP_PUSH);  write_int(&p3, 10);
    write_byte(&p3, OP_PUSH);  write_int(&p3, 20);
    write_byte(&p3, OP_ADD);
    write_byte(&p3, OP_PRINT);
    write_byte(&p3, OP_YIELD);
    
    write_byte(&p3, OP_PUSH);  write_int(&p3, 50);
    write_byte(&p3, OP_PUSH);  write_int(&p3, 15);
    write_byte(&p3, OP_SUB);
    write_byte(&p3, OP_PRINT);
    write_byte(&p3, OP_RETURN);
    
    int co3 = vm_create_coroutine(&vm, code3, p3 - code3);
    
    printf("--- Interleaved Execution ---\n");
    printf("Demonstrating cooperative multitasking:\n\n");
    
    // Interleave execution of all coroutines
    int active_coroutines = 3;
    while (active_coroutines > 0) {
        active_coroutines = 0;
        
        if (vm.coroutines[co1].state != CO_DEAD) {
            vm_resume(&vm, co1);
            if (vm.coroutines[co1].state != CO_DEAD) active_coroutines++;
        }
        
        if (vm.coroutines[co2].state != CO_DEAD) {
            vm_resume(&vm, co2);
            if (vm.coroutines[co2].state != CO_DEAD) active_coroutines++;
        }
        
        if (vm.coroutines[co3].state != CO_DEAD) {
            vm_resume(&vm, co3);
            if (vm.coroutines[co3].state != CO_DEAD) active_coroutines++;
        }
        
        printf("\n");
    }
    
    printf("--- All done ---\n");
    
    vm_cleanup(&vm);
    return 0;
}
