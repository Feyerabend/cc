// vm_sm.c - A simple virtual machine built entirely from state machines
// Each instruction is a state machine, VM orchestration is a state machine
// Compile: gcc -std=c99 -O2 -Wall -Wextra -o vm_demo vm_sm.c
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

// VM Instructions (simplified set)
typedef enum {
    OP_NOP = 0,    // No operation
    OP_LOAD,       // Load immediate value to stack
    OP_STORE,      // Store top of stack to memory[addr]
    OP_FETCH,      // Load from memory[addr] to stack
    OP_ADD,        // Pop two values, push sum
    OP_SUB,        // Pop two values, push difference (b-a)
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

// Instruction State Machine States (generic for all instructions)
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
    uint32_t        memory[VM_MEM_SIZE];  // Program and data memory
    uint32_t        stack[VM_STACK_SIZE]; // Execution stack
    int             sp;                   // Stack pointer (-1 = empty)
    uint32_t        pc;                   // Program counter
    uint32_t        ir;                   // Instruction register
    InstructionSM   inst_sm;              // Current instruction state machine
    bool            debug;                // Debug output flag
} VirtualMachine;

// Helper functions for stack operations
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
        case OP_HALT:    return "HALT";
        case OP_INVALID: return "INVALID";
        default:         return "?";
    }
}

// Instruction State Machine - handles execution of individual instructions
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
            vm->pc++; // consume the operand
            inst->state = INST_EXECUTE;
            return true;
        }

        case INST_EXECUTE: {
            // execute actual instruction
            uint32_t a, b;
            switch (inst->opcode) {
            case OP_NOP:
                // do not do anything
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
        vm->sp = -1;  // Empty stack
        vm->pc = 0;   // Start at beginning
        vm->ir = 0;
        vm->debug = (param & 1) != 0; // param & 1 enables debug
        memset(vm->stack, 0, sizeof(vm->stack));
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
        vm->pc = 0;
        vm->ir = 0;
        vm->debug = false;
        memset(vm->memory, 0, sizeof(vm->memory));
        memset(vm->stack, 0, sizeof(vm->stack));
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

// Debug function to print VM state
void vm_print_state(const VirtualMachine *vm) {
    if (!vm) return;
    
    printf("=== VM State ===\n");
    printf("State: %s\n", vm_state_name(vm->state));
    printf("PC: %" PRIu32 ", IR: %" PRIu32 " (%s), SP: %d\n", 
           vm->pc, vm->ir, opcode_name((OpCode)vm->ir), vm->sp);
    
    printf("Stack: [");
    for (int i = 0; i <= vm->sp; i++) {
        printf("%s%" PRIu32, i ? ", " : "", vm->stack[i]);
    }
    printf("]\n");
    
    printf("Instruction SM: %s\n", inst_state_name(vm->inst_sm.state));
    printf("--------------------\n");
}

// --------- Demo ----------
int main(void) {
    VirtualMachine vm = {0};
    
    printf("--- Simple VM with State Machine Instructions ---\n\n");

    // Program 1: Load two numbers and add them
    printf("Program 1: Load 10 and 20, add them\n");
    uint32_t prog1[] = {
        OP_LOAD, 10,    // Load 10
        OP_LOAD, 20,    // Load 20  
        OP_ADD,         // Add them
        OP_HALT         // Stop
    };
    
    vm_load_program(&vm, prog1, sizeof(prog1)/sizeof(prog1[0]));
    vm_run(&vm, true);
    vm_print_state(&vm);
    
    printf("\nProgram 2: Arithmetic with memory operations\n");
    vm_step(&vm, VM_EV_RESET, 0, NULL);
    
    uint32_t prog2[] = {
        OP_LOAD, 15,    // Load 15
        OP_STORE, 100,  // Store to memory[100]
        OP_LOAD, 5,     // Load 5
        OP_FETCH, 100,  // Fetch from memory[100] (gets 15)
        OP_SUB,         // 15 - 5 = 10
        OP_HALT
    };
    
    vm_load_program(&vm, prog2, sizeof(prog2)/sizeof(prog2[0]));
    vm_run(&vm, true);
    vm_print_state(&vm);
    
    printf("\nProgram 3: Stack underflow error test\n");
    vm_step(&vm, VM_EV_RESET, 0, NULL);
    
    uint32_t prog3[] = {
        OP_LOAD, 42,    // Load one value
        OP_ADD,         // Try to add (but need two values!)
        OP_HALT
    };
    
    vm_load_program(&vm, prog3, sizeof(prog3)/sizeof(prog3[0]));
    vm_run(&vm, true);
    vm_print_state(&vm);

    return 0;
}

