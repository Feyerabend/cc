/*
 * VM Dispatch Illustration
 * 
 * This VM demonstrates different instruction dispatch strategies:
 * 1. Switch-based dispatch (portable, simple)
 * 2. Computed goto (GCC/Clang extension, faster)
 *
 * The VM is as usually a simple stack-based machine
 * with basic arithmetic operations.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

/* Instruction Set */
typedef enum {
    OP_PUSH,    // Push immediate value onto stack
    OP_POP,     // Pop value from stack
    OP_ADD,     // Pop two values, push their sum
    OP_SUB,     // Pop two values, push their difference
    OP_MUL,     // Pop two values, push their product
    OP_DIV,     // Pop two values, push their quotient
    OP_PRINT,   // Print top of stack (without popping)
    OP_HALT,    // Stop execution
    OP_DUP,     // Duplicate top of stack
    OP_SWAP,    // Swap top two stack values
} OpCode;

typedef struct {
    OpCode op;
    int32_t operand;
} Instruction;

/* VM State */
#define STACK_SIZE 256

typedef struct {
    int32_t stack[STACK_SIZE];
    int sp;  // Stack pointer
    int ip;  // Instruction pointer
} VM;

void vm_init(VM *vm) {
    vm->sp = 0;
    vm->ip = 0;
    memset(vm->stack, 0, sizeof(vm->stack));
}

void vm_push(VM *vm, int32_t value) {
    if (vm->sp >= STACK_SIZE) {
        fprintf(stderr, "Stack overflow!\n");
        exit(1);
    }
    vm->stack[vm->sp++] = value;
}

int32_t vm_pop(VM *vm) {
    if (vm->sp <= 0) {
        fprintf(stderr, "Stack underflow!\n");
        exit(1);
    }
    return vm->stack[--vm->sp];
}

/* Strategy 1: Switch-based Dispatch */
/*
 * This is the most portable approach. The compiler generates a jump table
 * or a series of comparisons. Modern compilers often optimize this well,
 * but it has inherent overhead from the switch statement itself.
 */
void vm_run_switch(VM *vm, Instruction *program, int program_size) {
    vm_init(vm);
    
    while (vm->ip < program_size) {
        Instruction inst = program[vm->ip++];
        
        switch (inst.op) {
            case OP_PUSH:
                vm_push(vm, inst.operand);
                break;
                
            case OP_POP:
                vm_pop(vm);
                break;
                
            case OP_ADD: {
                int32_t b = vm_pop(vm);
                int32_t a = vm_pop(vm);
                vm_push(vm, a + b);
                break;
            }
            
            case OP_SUB: {
                int32_t b = vm_pop(vm);
                int32_t a = vm_pop(vm);
                vm_push(vm, a - b);
                break;
            }
            
            case OP_MUL: {
                int32_t b = vm_pop(vm);
                int32_t a = vm_pop(vm);
                vm_push(vm, a * b);
                break;
            }
            
            case OP_DIV: {
                int32_t b = vm_pop(vm);
                int32_t a = vm_pop(vm);
                if (b == 0) {
                    fprintf(stderr, "Division by zero!\n");
                    exit(1);
                }
                vm_push(vm, a / b);
                break;
            }
            
            case OP_PRINT:
                if (vm->sp > 0) {
                    printf("%d\n", vm->stack[vm->sp - 1]);
                }
                break;
                
            case OP_DUP:
                if (vm->sp > 0) {
                    vm_push(vm, vm->stack[vm->sp - 1]);
                }
                break;
                
            case OP_SWAP:
                if (vm->sp >= 2) {
                    int32_t temp = vm->stack[vm->sp - 1];
                    vm->stack[vm->sp - 1] = vm->stack[vm->sp - 2];
                    vm->stack[vm->sp - 2] = temp;
                }
                break;
                
            case OP_HALT:
                return;
        }
    }
}

/* Strategy 2: Computed Goto (GCC/Clang) */
/*
 * Computed goto uses GCC's "labels as values" extension. Instead of using
 * a switch statement, we maintain a dispatch table of label addresses and
 * jump directly to the appropriate handler using "goto *address".
 * 
 * This eliminates the switch overhead and gives better branch prediction
 * because each instruction type directly jumps to the next, creating
 * predictable patterns for the CPU.
 * 
 * Performance gain: typically 15-30% faster than switch-based dispatch.
 */
#ifdef __GNUC__
void vm_run_computed_goto(VM *vm, Instruction *program, int program_size) {
    vm_init(vm);
    
    // Dispatch table: array of label addresses
    // This is initialized once and stays in cache
    static void *dispatch_table[] = {
        &&op_push,
        &&op_pop,
        &&op_add,
        &&op_sub,
        &&op_mul,
        &&op_div,
        &&op_print,
        &&op_halt,
        &&op_dup,
        &&op_swap,
    };
    
    // Macro to fetch next instruction and dispatch to its handler
    #define DISPATCH() do { \
        if (vm->ip >= program_size) return; \
        goto *dispatch_table[program[vm->ip++].op]; \
    } while(0)
    
    DISPATCH();  // Initial dispatch
    
    op_push:
        vm_push(vm, program[vm->ip - 1].operand);
        DISPATCH();
    
    op_pop:
        vm_pop(vm);
        DISPATCH();
    
    op_add: {
        int32_t b = vm_pop(vm);
        int32_t a = vm_pop(vm);
        vm_push(vm, a + b);
        DISPATCH();
    }
    
    op_sub: {
        int32_t b = vm_pop(vm);
        int32_t a = vm_pop(vm);
        vm_push(vm, a - b);
        DISPATCH();
    }
    
    op_mul: {
        int32_t b = vm_pop(vm);
        int32_t a = vm_pop(vm);
        vm_push(vm, a * b);
        DISPATCH();
    }
    
    op_div: {
        int32_t b = vm_pop(vm);
        int32_t a = vm_pop(vm);
        if (b == 0) {
            fprintf(stderr, "Division by zero!\n");
            exit(1);
        }
        vm_push(vm, a / b);
        DISPATCH();
    }
    
    op_print:
        if (vm->sp > 0) {
            printf("%d\n", vm->stack[vm->sp - 1]);
        }
        DISPATCH();
    
    op_dup:
        if (vm->sp > 0) {
            vm_push(vm, vm->stack[vm->sp - 1]);
        }
        DISPATCH();
    
    op_swap:
        if (vm->sp >= 2) {
            int32_t temp = vm->stack[vm->sp - 1];
            vm->stack[vm->sp - 1] = vm->stack[vm->sp - 2];
            vm->stack[vm->sp - 2] = temp;
        }
        DISPATCH();
    
    op_halt:
        return;
        
    #undef DISPATCH
}
#endif


/* Demo Programs */

// Program to compute: (10 + 5) * 3 - 2
Instruction demo_program[] = {
    {OP_PUSH, 10},
    {OP_PUSH, 5},
    {OP_ADD, 0},
    {OP_PUSH, 3},
    {OP_MUL, 0},
    {OP_PUSH, 2},
    {OP_SUB, 0},
    {OP_PRINT, 0},
    {OP_HALT, 0}
};

// Benchmark program: lots of arithmetic
#define BENCHMARK_SIZE 15000
Instruction benchmark_program[BENCHMARK_SIZE];
int benchmark_actual_size = 0;

void init_benchmark_program() {
    int idx = 0;
    
    // Initialize with a value
    benchmark_program[idx++] = (Instruction){OP_PUSH, 1};
    
    // Repeatedly add, multiply, etc.
    for (int i = 0; i < 2000 && idx < BENCHMARK_SIZE - 10; i++) {
        benchmark_program[idx++] = (Instruction){OP_PUSH, 2};
        benchmark_program[idx++] = (Instruction){OP_ADD, 0};
        benchmark_program[idx++] = (Instruction){OP_PUSH, 3};
        benchmark_program[idx++] = (Instruction){OP_MUL, 0};
        benchmark_program[idx++] = (Instruction){OP_PUSH, 1000000};
        benchmark_program[idx++] = (Instruction){OP_DIV, 0};
    }
    
    benchmark_program[idx++] = (Instruction){OP_HALT, 0};
    benchmark_actual_size = idx;
    printf("Benchmark program has %d instructions\n", benchmark_actual_size);
}


int main() {
    VM vm;
    
    printf("=== VM Dispatch Strategies Demo ===\n\n");
    printf("This demonstrates different ways to dispatch instructions in a VM.\n");
    printf("Modern VMs (like CPython, Ruby, LuaJIT) use these techniques.\n\n");
    
    printf("Running demo program: (10 + 5) * 3 - 2\n");
    printf("Expected result: 43\n\n");
    
    printf("1. Switch-based dispatch:\n");
    printf("   - Most portable (works everywhere)\n");
    printf("   - Compiler may optimize into jump table\n");
    printf("   - Some overhead from switch machinery\n");
    printf("   Result: ");
    vm_run_switch(&vm, demo_program, sizeof(demo_program) / sizeof(Instruction));
    
#ifdef __GNUC__
    printf("\n2. Computed goto dispatch:\n");
    printf("   - GCC/Clang extension (non-portable)\n");
    printf("   - Direct jumps via goto *address\n");
    printf("   - Better branch prediction\n");
    printf("   - Typically 15-30%% faster than switch\n");
    printf("   Result: ");
    vm_run_computed_goto(&vm, demo_program, sizeof(demo_program) / sizeof(Instruction));
#else
    printf("\n2. Computed goto dispatch:\n");
    printf("   Not available (requires GCC/Clang)\n");
#endif
    
    // Benchmark
    printf("\n\n=== Performance Benchmark ===\n");
    init_benchmark_program();
    
    clock_t start, end;
    double cpu_time;
    int iterations = 1000;
    
    printf("\nRunning %d iterations...\n\n", iterations);
    
    // Switch dispatch
    start = clock();
    for (int i = 0; i < iterations; i++) {
        vm_run_switch(&vm, benchmark_program, benchmark_actual_size);
    }
    end = clock();
    cpu_time = ((double)(end - start)) / CLOCKS_PER_SEC;
    double switch_time = cpu_time;
    printf("Switch dispatch:  %.4f seconds (baseline)\n", cpu_time);
    
#ifdef __GNUC__
    // Computed goto
    start = clock();
    for (int i = 0; i < iterations; i++) {
        vm_run_computed_goto(&vm, benchmark_program, benchmark_actual_size);
    }
    end = clock();
    cpu_time = ((double)(end - start)) / CLOCKS_PER_SEC;
    double speedup = (switch_time - cpu_time) / switch_time * 100.0;
    printf("Computed goto:    %.4f seconds (%.1f%% faster)\n", cpu_time, speedup);
#endif

/*  printf("\nWhy Computed Goto is Faster:\n");
    printf("1. Direct jumps: goto *address is a single indirect branch\n");
    printf("2. Better prediction: Each instruction type creates predictable patterns\n");
    printf("3. Tighter code: No switch statement overhead\n");
    printf("4. Cache friendly: Dispatch table stays in cache\n");
    
    printf("\nReal World Usage:\n");
    printf("- CPython used computed goto for years (optional)\n");
    printf("- LuaJIT uses direct threading (similar concept)\n");
    printf("- Many interpreters prefer this over switch\n");
    printf("- Trade-off: portability vs performance\n"); */
    
    return 0;
}
