// new_vm.c - A simple virtual machine built entirely from state machines,
// but now more Turing coomplete.
// Each instruction is a state machine, VM orchestration is a state machine
// compile: gcc -std=c99 -O2 -Wall -Wextra -o vm_demo new_vm.c
#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <inttypes.h>
#include <string.h>

#ifndef VM_MEM_SIZE
#define VM_MEM_SIZE 256
#endif

#ifndef VM_STACK_SIZE  
#define VM_STACK_SIZE 32
#endif

#ifndef VM_CALL_STACK_SIZE
#define VM_CALL_STACK_SIZE 16
#endif

// VM Instructions
typedef enum {
    OP_NOP = 0,    // No operation
    OP_LOAD,       // Load immediate value to stack
    OP_STORE,      // Store top of stack to memory[addr]
    OP_FETCH,      // Load from memory[addr] to stack
    OP_ADD,        // Pop two values, push sum
    OP_SUB,        // Pop two values, push difference (b-a)
    OP_MUL,        // Pop two values, push product
    OP_DIV,        // Pop two values, push quotient (b/a)
    OP_MOD,        // Pop two values, push remainder (b%a)
    OP_DUP,        // Duplicate top of stack
    OP_SWAP,       // Swap top two stack elements
    OP_POP,        // Pop and discard top element
    OP_JMP,        // Unconditional jump to address
    OP_BEZ,        // Branch if top of stack is zero
    OP_BNZ,        // Branch if top of stack is non-zero
    OP_BLT,        // Branch if second < top (pops both)
    OP_BGT,        // Branch if second > top (pops both)
    OP_CALL,       // Call subroutine (pushes return address)
    OP_RET,        // Return from subroutine
    OP_PRINT,      // Print top of stack (for demo purposes)
    OP_HALT,       // Stop execution
    OP_INVALID
} OpCode;

// VM States
typedef enum {
    VM_UNINIT = 0,
    VM_READY,         // Ready to fetch next instruction
    VM_FETCHING,      // Fetching instruction from memory
    VM_DECODING,      // Decoding instruction
    VM_EXECUTING,     // Executing instruction via instruction SM
    VM_HALTED,        // Program completed normally
    VM_ERROR          // Error state
} VMState;

// Instruction State Machine States (ISMS generic for all instructions)
typedef enum {
    INST_UNINIT = 0,
    INST_INIT,        // Initialize instruction
    INST_OPERAND,     // Fetch operand if needed
    INST_EXECUTE,     // Perform operation
    INST_COMPLETE,    // Instruction complete
    INST_ERROR        // Instruction error
} InstState;

// VM Events
typedef enum {
    VM_EV_INIT = 0,   // Initialize VM
    VM_EV_STEP,       // Execute one step
    VM_EV_RESET,      // Reset VM
    VM_EV_GET_STATE   // Get current state
} VMEvent;

// Instruction Events
typedef enum {
    INST_EV_INIT = 0, // Initialize instruction with opcode
    INST_EV_STEP,     // Execute one step of instruction
    INST_EV_RESET,    // Reset instruction
    INST_EV_GET_STATE // Get instruction state
} InstEvent;

// Instruction State Machine
typedef struct {
    OpCode      opcode;
    InstState   state;
    uint32_t    operand;      // For instructions that need operands
    bool        needs_operand; // Does this instruction need an operand?
    int         step_count;   // Internal step counter
} InstructionSM;

// Virtual Machine
typedef struct {
    VMState         state;
    uint32_t        memory[VM_MEM_SIZE];      // Program and data memory
    uint32_t        stack[VM_STACK_SIZE];     // Execution stack
    int             sp;                       // Stack pointer (-1 = empty)
    uint32_t        call_stack[VM_CALL_STACK_SIZE]; // Return addresses
    int             csp;                      // Call stack pointer (-1 = empty)
    uint32_t        pc;                       // Program counter
    uint32_t        ir;                       // Instruction register
    InstructionSM   inst_sm;                  // Current instruction state machine
    bool            debug;                    // Debug output flag
} VirtualMachine;

// Helpers for stack operations
static bool vm_push(VirtualMachine *vm, uint32_t value) {
    if (vm->sp >= VM_STACK_SIZE - 1) return false;
    vm->stack[++vm->sp] = value;
    return true;
}

static bool vm_pop(VirtualMachine *vm, uint32_t *value) {
    if (vm->sp < 0) return false;
    if (value) *value = vm->stack[vm->sp];
    vm->sp--;
    return true;
}

// Helpers for call stack
static bool vm_call_push(VirtualMachine *vm, uint32_t addr) {
    if (vm->csp >= VM_CALL_STACK_SIZE - 1) return false;
    vm->call_stack[++vm->csp] = addr;
    return true;
}

static bool vm_call_pop(VirtualMachine *vm, uint32_t *addr) {
    if (vm->csp < 0) return false;
    if (addr) *addr = vm->call_stack[vm->csp];
    vm->csp--;
    return true;
}

static const char* vm_state_name(VMState s) {
    switch (s) {
        case VM_UNINIT:   return "UNINIT";
        case VM_READY:    return "READY";
        case VM_FETCHING: return "FETCHING";
        case VM_DECODING: return "DECODING";
        case VM_EXECUTING: return "EXECUTING";
        case VM_HALTED:   return "HALTED";
        case VM_ERROR:    return "ERROR";
        default:          return "?";
    }
}

static const char* inst_state_name(InstState s) {
    switch (s) {
        case INST_UNINIT:   return "UNINIT";
        case INST_INIT:     return "INIT";
        case INST_OPERAND:  return "OPERAND";
        case INST_EXECUTE:  return "EXECUTE";
        case INST_COMPLETE: return "COMPLETE";
        case INST_ERROR:    return "ERROR";
        default:            return "?";
    }
}

static const char* opcode_name(OpCode op) {
    switch (op) {
        case OP_NOP:     return "NOP";
        case OP_LOAD:    return "LOAD";
        case OP_STORE:   return "STORE";
        case OP_FETCH:   return "FETCH";
        case OP_ADD:     return "ADD";
        case OP_SUB:     return "SUB";
        case OP_MUL:     return "MUL";
        case OP_DIV:     return "DIV";
        case OP_MOD:     return "MOD";
        case OP_DUP:     return "DUP";
        case OP_SWAP:    return "SWAP";
        case OP_POP:     return "POP";
        case OP_JMP:     return "JMP";
        case OP_BEZ:     return "BEZ";
        case OP_BNZ:     return "BNZ";
        case OP_BLT:     return "BLT";
        case OP_BGT:     return "BGT";
        case OP_CALL:    return "CALL";
        case OP_RET:     return "RET";
        case OP_PRINT:   return "PRINT";
        case OP_HALT:    return "HALT";
        case OP_INVALID: return "INVALID";
        default:         return "?";
    }
}

// Instruction State Machine (handles execution of individual instructions)
bool instruction_step(InstructionSM *inst, VirtualMachine *vm, InstEvent ev, uint32_t param) {
    if (!inst || !vm) return false;

    if (inst->state == INST_ERROR && ev != INST_EV_RESET) {
        return false;
    }

    switch (ev) {
    case INST_EV_INIT: {
        inst->opcode = (OpCode)param;
        inst->state = INST_INIT;
        inst->operand = 0;
        inst->step_count = 0;
        
        // determine if this instruction needs an operand
        switch (inst->opcode) {
        case OP_LOAD:
        case OP_STORE:
        case OP_FETCH:
        case OP_JMP:
        case OP_BEZ:
        case OP_BNZ:
        case OP_BLT:
        case OP_BGT:
        case OP_CALL:
            inst->needs_operand = true;
            break;
        default:
            inst->needs_operand = false;
            break;
        }
        return true;
    }

    case INST_EV_STEP: {
        switch (inst->state) {
        case INST_INIT: {
            if (inst->needs_operand) {
                inst->state = INST_OPERAND;
            } else {
                inst->state = INST_EXECUTE;
            }
            return true;
        }

        case INST_OPERAND: {
            // fetch operand from next memory location
            if (vm->pc + 1 >= VM_MEM_SIZE) {
                inst->state = INST_ERROR;
                return true;
            }
            inst->operand = vm->memory[vm->pc + 1];
            vm->pc++; // consume operand
            inst->state = INST_EXECUTE;
            return true;
        }

        case INST_EXECUTE: {
            // execute actual instruction
            uint32_t a, b;
            switch (inst->opcode) {
            case OP_NOP:
                // nothing I tell you
                break;
                
            case OP_MUL:
                if (!vm_pop(vm, &a) || !vm_pop(vm, &b)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                if (!vm_push(vm, b * a)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                break;
                
            case OP_BNZ:
                // branch if non-zero
                if (!vm_pop(vm, &a)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                if (a != 0) {
                    if (inst->operand >= VM_MEM_SIZE) {
                        inst->state = INST_ERROR;
                        return true;
                    }
                    vm->pc = inst->operand - 1;
                }
                break;
                
            case OP_BLT:
                // branch if less than (second < top)
                if (!vm_pop(vm, &a) || !vm_pop(vm, &b)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                if (b < a) {
                    if (inst->operand >= VM_MEM_SIZE) {
                        inst->state = INST_ERROR;
                        return true;
                    }
                    vm->pc = inst->operand - 1;
                }
                break;
                
            case OP_BGT:
                // branch if greater than (second > top)
                if (!vm_pop(vm, &a) || !vm_pop(vm, &b)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                if (b > a) {
                    if (inst->operand >= VM_MEM_SIZE) {
                        inst->state = INST_ERROR;
                        return true;
                    }
                    vm->pc = inst->operand - 1;
                }
                break;
                
            case OP_CALL:
                // call subroutine, push return address, jump
                if (!vm_call_push(vm, vm->pc + 1)) { // +1 for next instruction
                    inst->state = INST_ERROR;
                    return true;
                }
                if (inst->operand >= VM_MEM_SIZE) {
                    inst->state = INST_ERROR;
                    return true;
                }
                vm->pc = inst->operand - 1;
                break;
                
            case OP_RET:
                // return from subroutine
                if (!vm_call_pop(vm, &a)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                vm->pc = a - 1; // -1 because VM will increment
                break;
                
            case OP_PRINT:
                // print top of stack (no pop)
                if (vm->sp < 0) {
                    inst->state = INST_ERROR;
                    return true;
                }
                printf("PRINT: %" PRIu32 "\n", vm->stack[vm->sp]);
                break;
                
            case OP_DIV:
                if (!vm_pop(vm, &a) || !vm_pop(vm, &b)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                if (a == 0) { // div by zero
                    inst->state = INST_ERROR;
                    return true;
                }
                if (!vm_push(vm, b / a)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                break;
                
            case OP_MOD:
                if (!vm_pop(vm, &a) || !vm_pop(vm, &b)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                if (a == 0) { // mod by zero
                    inst->state = INST_ERROR;
                    return true;
                }
                if (!vm_push(vm, b % a)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                break;
                
            case OP_DUP:
                if (vm->sp < 0) {
                    inst->state = INST_ERROR;
                    return true;
                }
                if (!vm_push(vm, vm->stack[vm->sp])) {
                    inst->state = INST_ERROR;
                    return true;
                }
                break;
                
            case OP_SWAP:
                if (vm->sp < 1) { // need at least 2 elements
                    inst->state = INST_ERROR;
                    return true;
                }
                a = vm->stack[vm->sp];
                vm->stack[vm->sp] = vm->stack[vm->sp - 1];
                vm->stack[vm->sp - 1] = a;
                break;
                
            case OP_POP:
                if (!vm_pop(vm, NULL)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                break;
                
            case OP_LOAD:
                if (!vm_push(vm, inst->operand)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                break;
                
            case OP_STORE:
                if (!vm_pop(vm, &a) || inst->operand >= VM_MEM_SIZE) {
                    inst->state = INST_ERROR;
                    return true;
                }
                vm->memory[inst->operand] = a;
                break;
                
            case OP_FETCH:
                if (inst->operand >= VM_MEM_SIZE) {
                    inst->state = INST_ERROR;
                    return true;
                }
                if (!vm_push(vm, vm->memory[inst->operand])) {
                    inst->state = INST_ERROR;
                    return true;
                }
                break;
                
            case OP_ADD:
                if (!vm_pop(vm, &a) || !vm_pop(vm, &b)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                if (!vm_push(vm, b + a)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                break;
                
            case OP_SUB:
                if (!vm_pop(vm, &a) || !vm_pop(vm, &b)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                if (!vm_push(vm, b - a)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                break;
                
            case OP_JMP:
                // unconditional jump, set PC to operand - 1 
                // (will be incremented after instruction completes)
                if (inst->operand >= VM_MEM_SIZE) {
                    inst->state = INST_ERROR;
                    return true;
                }
                vm->pc = inst->operand - 1; // -1 because VM will increment PC
                break;
                
            case OP_BEZ:
                // branch if zero, pop value, jump if zero
                if (!vm_pop(vm, &a)) {
                    inst->state = INST_ERROR;
                    return true;
                }
                if (a == 0) {
                    if (inst->operand >= VM_MEM_SIZE) {
                        inst->state = INST_ERROR;
                        return true;
                    }
                    vm->pc = inst->operand - 1; // -1 because VM will increment PC
                }
                break;
                
            case OP_HALT:
                // special case: HALT completes immediately and signals VM
                break;
                
            default:
                inst->state = INST_ERROR;
                return true;
            }
            
            inst->state = INST_COMPLETE;
            return true;
        }

        case INST_COMPLETE:
        case INST_ERROR: {
            // already done
            return true;
        }

        default:
            inst->state = INST_ERROR;
            return true;
        }
    }

    case INST_EV_RESET: {
        inst->opcode = OP_INVALID;
        inst->state = INST_UNINIT;
        inst->operand = 0;
        inst->needs_operand = false;
        inst->step_count = 0;
        return true;
    }

    case INST_EV_GET_STATE: {
        return true; // state is accessible directly
    }

    default:
        return false;
    }
}

// VM State Machine: orchestrates instruction execution
bool vm_step(VirtualMachine *vm, VMEvent ev, uint32_t param, uint32_t *result) {
    if (!vm) return false;

    if (vm->state == VM_ERROR && ev != VM_EV_RESET) {
        return false;
    }

    switch (ev) {
    case VM_EV_INIT: {
        vm->state = VM_READY;
        vm->sp = -1;    // Empty stack
        vm->csp = -1;   // Empty call stack
        vm->pc = 0;     // Start at beginning
        vm->ir = 0;
        vm->debug = (param & 1) != 0; // param & 1 enables debug
        memset(vm->stack, 0, sizeof(vm->stack));
        memset(vm->call_stack, 0, sizeof(vm->call_stack));
        instruction_step(&vm->inst_sm, vm, INST_EV_RESET, 0);
        return true;
    }

    case VM_EV_STEP: {
        if (vm->debug) {
            printf("VM Step: state=%s pc=%" PRIu32 " sp=%d\n", 
                   vm_state_name(vm->state), vm->pc, vm->sp);
        }

        switch (vm->state) {
        case VM_READY: {
            vm->state = VM_FETCHING;
            return true;
        }

        case VM_FETCHING: {
            if (vm->pc >= VM_MEM_SIZE) {
                vm->state = VM_ERROR;
                return true;
            }
            vm->ir = vm->memory[vm->pc];
            vm->state = VM_DECODING;
            return true;
        }

        case VM_DECODING: {
            // Init instruction state machine with the opcode
            if (!instruction_step(&vm->inst_sm, vm, INST_EV_INIT, vm->ir)) {
                vm->state = VM_ERROR;
                return true;
            }
            vm->state = VM_EXECUTING;
            return true;
        }

        case VM_EXECUTING: {
            // Step the instruction state machine
            if (!instruction_step(&vm->inst_sm, vm, INST_EV_STEP, 0)) {
                vm->state = VM_ERROR;
                return true;
            }

            if (vm->inst_sm.state == INST_ERROR) {
                vm->state = VM_ERROR;
                return true;
            }

            if (vm->inst_sm.state == INST_COMPLETE) {
                // check for HALT instruction
                if (vm->inst_sm.opcode == OP_HALT) {
                    vm->state = VM_HALTED;
                } else {
                    vm->pc++; // move to next instruction
                    vm->state = VM_READY;
                }
                // reset instruction SM for next instruction
                instruction_step(&vm->inst_sm, vm, INST_EV_RESET, 0);
            }
            return true;
        }

        case VM_HALTED:
        case VM_ERROR: {
            // no more execution
            return true;
        }

        default:
            vm->state = VM_ERROR;
            return true;
        }
    }

    case VM_EV_RESET: {
        vm->state = VM_UNINIT;
        vm->sp = -1;
        vm->csp = -1;
        vm->pc = 0;
        vm->ir = 0;
        vm->debug = false;
        memset(vm->memory, 0, sizeof(vm->memory));
        memset(vm->stack, 0, sizeof(vm->stack));
        memset(vm->call_stack, 0, sizeof(vm->call_stack));
        instruction_step(&vm->inst_sm, vm, INST_EV_RESET, 0);
        return true;
    }

    case VM_EV_GET_STATE: {
        if (result) *result = vm->state;
        return true;
    }

    default:
        return false;
    }
}

// Helper to load a program into VM memory
void vm_load_program(VirtualMachine *vm, uint32_t *program, int length) {
    if (!vm || !program || length <= 0) return;
    
    int copy_length = (length > VM_MEM_SIZE) ? VM_MEM_SIZE : length;
    memcpy(vm->memory, program, copy_length * sizeof(uint32_t));
}

// Helper to run VM until halt or error
bool vm_run(VirtualMachine *vm, bool debug) {
    if (!vm) return false;
    
    vm_step(vm, VM_EV_INIT, debug ? 1 : 0, NULL);
    
    int max_steps = 1000; // safety limit
    while ((vm->state != VM_HALTED && vm->state != VM_ERROR) && max_steps-- > 0) {
        vm_step(vm, VM_EV_STEP, 0, NULL);
    }
    
    return vm->state == VM_HALTED;
}

// debug function to print VM state
void vm_print_state(const VirtualMachine *vm) {
    if (!vm) return;
    
    printf("--- VM State ---\n");
    printf("State: %s\n", vm_state_name(vm->state));
    printf("PC: %" PRIu32 ", IR: %" PRIu32 " (%s), SP: %d, CSP: %d\n", 
           vm->pc, vm->ir, opcode_name((OpCode)vm->ir), vm->sp, vm->csp);
    
    printf("Stack: [");
    for (int i = 0; i <= vm->sp; i++) {
        printf("%s%" PRIu32, i ? ", " : "", vm->stack[i]);
    }
    printf("]\n");
    
    printf("Call Stack: [");
    for (int i = 0; i <= vm->csp; i++) {
        printf("%s%" PRIu32, i ? ", " : "", vm->call_stack[i]);
    }
    printf("]\n");
    
    printf("Instruction SM: %s\n", inst_state_name(vm->inst_sm.state));
    printf("------------\n");
}

// --------- demo ----------
int main(void) {
    VirtualMachine vm = {0};

    printf("--- VM with State Machine Instructions ---\n\n");

    // Program 1: Load two numbers and add them
    printf("Program 1: Load 10 and 20, add them\n");
    uint32_t prog1[] = {
        OP_LOAD, 10,    // Load 10
        OP_LOAD, 20,    // Load 20  
        OP_ADD,         // Add them
        OP_PRINT,       // Print result
        OP_HALT         // Stop
    };
    
    vm_load_program(&vm, prog1, sizeof(prog1)/sizeof(prog1[0]));
    vm_run(&vm, false);
    vm_print_state(&vm);
    
    printf("\nProgram 2: Arithmetic with memory operations\n");
    vm_step(&vm, VM_EV_RESET, 0, NULL);
    
    uint32_t prog2[] = {
        OP_LOAD, 15,    // Load 15
        OP_STORE, 100,  // Store to memory[100]
        OP_FETCH, 100,  // Fetch from memory[100] (gets 15)
        OP_LOAD, 5,     // Load 5
        OP_SUB,         // 15 - 5 = 10 (order matters: second - top)
        OP_PRINT,       // Print result
        OP_HALT
    };
    
    vm_load_program(&vm, prog2, sizeof(prog2)/sizeof(prog2[0]));
    vm_run(&vm, false);
    vm_print_state(&vm);

    /*
    printf("\nProgram 3: Loop example (count down from 5) - WITH DEBUG\n");
    vm_step(&vm, VM_EV_RESET, 0, NULL);
    
    // First, let's test a simple decrement without loop to verify the logic
    uint32_t simple_test[] = {
        OP_LOAD, 5,     // Load 5
        OP_STORE, 50,   // Store at memory[50]
        OP_FETCH, 50,   // Fetch it back
        OP_PRINT,       // Should print 5
        OP_LOAD, 1,     // Load 1
        OP_SUB,         // 5 - 1 = 4
        OP_PRINT,       // Should print 4
        OP_STORE, 50,   // Store 4 back to memory[50]
        OP_FETCH, 50,   // Fetch it back
        OP_PRINT,       // Should print 4 (verifying store worked)
        OP_HALT
    };
    
    printf("Simple decrement test:\n");
    vm_load_program(&vm, simple_test, sizeof(simple_test)/sizeof(simple_test[0]));
    vm_run(&vm, false);
    vm_print_state(&vm);*/
    
    // Now let's try a proper loop
    printf("\nLoop test:\n");
    vm_step(&vm, VM_EV_RESET, 0, NULL);
    
    uint32_t prog3[] = {
        OP_LOAD, 3,     // Address 0: Load 3
        OP_STORE, 50,   // Address 2: Store to memory[50]
        
        // Loop starts at address 4
        OP_FETCH, 50,   // Address 4: get counter: [counter]
        OP_DUP,         // Address 6: duplicate it: [counter, counter]
        OP_BEZ, 19,     // Address 7: if zero, exit to 19 (consumes one): [counter] or []
        OP_DUP,         // Address 9: duplicate remaining: [counter, counter]  
        OP_PRINT,       // Address 10: print the counter (without popping)
        OP_POP,         // Address 11: remove the printed value: [counter]
        OP_LOAD, 1,     // Address 12: load 1: [counter, 1]
        OP_SUB,         // Address 14: counter - 1: [counter-1]
        OP_STORE, 50,   // Address 15: store decremented counter: []
        OP_JMP, 4,      // Address 17: jump back to FETCH (address 4)
        
        // Exit (address 19)
        OP_POP,         // Address 19: clean up any remaining zero
        OP_HALT         // Address 20: end
    };
    
    vm_load_program(&vm, prog3, sizeof(prog3)/sizeof(prog3[0]));
    vm_run(&vm, false);
    vm_print_state(&vm);
    
    printf("\nProgram 4: Stack manipulation demo\n");
    vm_step(&vm, VM_EV_RESET, 0, NULL);
    
    uint32_t prog4[] = {
        OP_LOAD, 10,    // Load 10
        OP_LOAD, 20,    // Load 20 (stack: [10, 20])
        OP_DUP,         // Duplicate top (stack: [10, 20, 20])
        OP_PRINT,       // Print: 20
        OP_SWAP,        // Swap top two (stack: [10, 20, 20])
        OP_PRINT,       // Print: 20 
        OP_POP,         // Remove one 20 (stack: [10, 20])
        OP_ADD,         // Add: 10 + 20 = 30
        OP_PRINT,       // Print: 30
        OP_HALT
    };
    
    vm_load_program(&vm, prog4, sizeof(prog4)/sizeof(prog4[0]));
    vm_run(&vm, false);
    vm_print_state(&vm);

    printf("\nProgram 5: Error handling test (stack underflow)\n");
    vm_step(&vm, VM_EV_RESET, 0, NULL);
    
    uint32_t prog5[] = {
        OP_LOAD, 42,    // Load one value
        OP_ADD,         // Try to add (but need two values!)
        OP_HALT
    };
    
    vm_load_program(&vm, prog5, sizeof(prog5)/sizeof(prog5[0]));
    vm_run(&vm, false);
    vm_print_state(&vm);

    return 0;
}
