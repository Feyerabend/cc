#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STACK_SIZE 100
#define LOCALS_SIZE 10
#define TRUE 1
#define FALSE 0

typedef enum {
    ADD,
    ALLOC,
    CALL,
    CRET,
    DEALLOC,
    HALT,
    JZ,
    LD,
    MUL,
    POP,
    PRINT,
    PUSH,
    RET,
    ST,
    SUB
} Opcode;

typedef struct {
    int stack[STACK_SIZE];
    int locals[LOCALS_SIZE];
    int sp;
    int returnValue;
    int returnAddress;
} Frame;

typedef struct FrameStack {
    Frame* frames[STACK_SIZE];
    int fp;
} FrameStack;

typedef struct {
    int pc;
    int sp;
    int locals[LOCALS_SIZE];
    int stack[STACK_SIZE];
} State;

typedef struct {
    State* states;
    int size;
    int capacity;
} StateHistory;

typedef struct VM {
    int* code;
    int pc;
    int code_length;
    FrameStack fstack;
    StateHistory history;  // history for time travel debugging
    int debug;
} VM;

void freeVM(VM* vm);

char message[100];

void error(VM* vm, const char* message) {
    printf("Error: %s\n", message);
    freeVM(vm);
    exit(EXIT_FAILURE);
}

int next(VM* vm) {
    if (vm->pc >= vm->code_length) {
        error(vm, "Program counter out of bounds");
    }
    return vm->code[vm->pc++];
}

void initFrameStack(FrameStack* fstack) {
    fstack->fp = -1;
}

int pushFrame(VM* vm) {
    if (vm->fstack.fp >= STACK_SIZE - 1) {
        error(vm, "Frame stack overflow");
    }
    Frame* frame = (Frame*) malloc(sizeof(Frame));
    frame->sp = -1;
    frame->returnValue = 0;
    frame->returnAddress = 0;
    vm->fstack.frames[++(vm->fstack.fp)] = frame;
    return vm->fstack.fp;
}

int popFrame(VM* vm) {
    if (vm->fstack.fp < 0) {
        error(vm, "Frame stack underflow");
    }
    Frame* currentFrame = vm->fstack.frames[vm->fstack.fp];
    vm->pc = currentFrame->returnAddress;
    free(currentFrame);
    vm->fstack.fp--;
    return vm->fstack.fp + 1;
}

Frame* getFrame(VM* vm, int frameIndex) {
    if (frameIndex < 0 || frameIndex > vm->fstack.fp) {
        snprintf(message, sizeof(message), "Invalid frame index: %d", frameIndex);
        error(vm, message);
        return NULL;
    }
    return vm->fstack.frames[frameIndex];
}

void push(VM* vm, int value) {
    Frame* frame = vm->fstack.frames[vm->fstack.fp];
    if (frame->sp >= STACK_SIZE - 1) {
        error(vm, "Stack overflow in frame");
    }
    frame->stack[++(frame->sp)] = value;
}

int pop(VM* vm) {
    Frame* frame = vm->fstack.frames[vm->fstack.fp];
    if (frame->sp < 0) {
        error(vm, "Stack underflow in frame");
    }
    return frame->stack[(frame->sp)--];
}

void store(VM* vm, int index) {
    int value = pop(vm);
    vm->fstack.frames[vm->fstack.fp]->locals[index] = value;
}

void load(VM* vm, int index) {
    int value = vm->fstack.frames[vm->fstack.fp]->locals[index];
    push(vm, value);
}

void transferStackToLocals(VM* vm, int num) {
    Frame* currentFrame = vm->fstack.frames[vm->fstack.fp];
    Frame* prevFrame = vm->fstack.frames[vm->fstack.fp - 1];
    for (int i = 0; i < num; ++i) {
        currentFrame->locals[i] = prevFrame->stack[prevFrame->sp--];
    }
}

void transferStackToReturnValue(VM* vm) {
    Frame* srcFrame = vm->fstack.frames[vm->fstack.fp];
    Frame* destFrame = vm->fstack.frames[vm->fstack.fp - 1];
    int value = srcFrame->stack[srcFrame->sp--];
    destFrame->returnValue = value;
}

VM* newVM(int* code, int code_length) {
    VM* vm = (VM*)malloc(sizeof(VM));
    if (vm == NULL) {
        return NULL;
    }
    vm->code = code;
    vm->pc = 0;
    vm->code_length = code_length;
    initFrameStack(&(vm->fstack));
    
    // init state history
    vm->history.size = 0;
    vm->history.capacity = 10; // init capacity
    vm->history.states = (State*)malloc(sizeof(State) * vm->history.capacity);
    
    return vm;
}

void freeVM(VM* vm) {
    while (vm->fstack.fp >= 0) {
        popFrame(vm);
    }
    free(vm->history.states); // free the state history
    free(vm);
}

void saveState(VM* vm) {
    if (vm->history.size >= vm->history.capacity) {
        vm->history.capacity *= 2; // double capacity
        vm->history.states = realloc(vm->history.states, sizeof(State) * vm->history.capacity);
    }
    
    State* state = &vm->history.states[vm->history.size++];
    state->pc = vm->pc;
    state->sp = vm->fstack.frames[vm->fstack.fp]->sp;
    memcpy(state->locals, vm->fstack.frames[vm->fstack.fp]->locals, sizeof(int) * LOCALS_SIZE);
    memcpy(state->stack, vm->fstack.frames[vm->fstack.fp]->stack, sizeof(int) * STACK_SIZE);
}

void run(VM* vm) {
    int opcode, addr, num;
    Frame* fr;

    while (TRUE) {
        saveState(vm); // capture current state
        opcode = next(vm);
        switch (opcode) {

            case CALL:
                num = next(vm);
                addr = next(vm);
                int frm = pushFrame(vm);
                fr = getFrame(vm, frm);
                fr->returnAddress = vm->pc;
                if (num > 0) {
                    transferStackToLocals(vm, num);
                }
                vm->pc = addr;
                break;

            case RET:
                if (vm->fstack.fp > 0) {
                    transferStackToReturnValue(vm);
                }
                fr = vm->fstack.frames[vm->fstack.fp];
                vm->pc = fr->returnAddress;
                popFrame(vm);
                break;

            case PUSH:
                push(vm, next(vm));
                break;

            case POP:
                pop(vm);
                break;

            case LD:
                load(vm, next(vm));
                break;

            case ST:
                store(vm, next(vm));
                break;

            case CRET:
                push(vm, vm->fstack.frames[vm->fstack.fp]->returnValue);
                break;

            case PRINT:
                printf("PRINT: %d\n", pop(vm));
                break;

            case ADD:
                push(vm, pop(vm) + pop(vm));
                break;

            case SUB:
                num = pop(vm);
                push(vm, pop(vm) - num);
                break;

            case MUL:
                push(vm, pop(vm) * pop(vm));
                break;

            case JZ:
                num = pop(vm);
                addr = next(vm);
                if (num <= 0)
                    vm->pc = addr;
                break;

            case HALT:
                return;

            default:
                printf("Unknown opcode: %d\n", opcode);
                return;
        }
    }
}

int main() {
    int code[] = {
        // Main Program
        PUSH, 5,                // Push the initial value n = 5
        CALL, 1, 8,             // Call factorial(5)
        CRET,                   // Retrieve the result of factorial(5)
        PRINT,                  // Print the result
        HALT,                   // End of program

        // Function factorial (Address 8)
        LD, 0,                  // Load n (the argument)
        PUSH, 1,                // Push constant 1
        SUB,                    // Subtract to check if n == 1
        JZ, 28,                 // Jump to base case if n == 1

        // Recursive Case (if n > 1)
        LD, 0,                  // Load n again (the argument)
        LD, 0,                  // Load n again (for factorial(n - 1))
        PUSH, 1,                // Push constant 1
        SUB,                    // Calculate n - 1
        CALL, 1, 8,             // Call factorial(n - 1)
        CRET,                   // Get factorial(n - 1)
        MUL,                    // Calculate n * factorial(n - 1)
        RET,                    // Return the result of n * factorial(n - 1)

        // Base Case (Address 28)
        PUSH, 1,                // Push 1 (factorial of 1 is 1)
        RET                     // Return 1
    };

    int code_size = sizeof(code) / sizeof(code[0]);

    VM* vm = newVM(code, code_size);
    vm->debug = 1;  // debugging to capture snapshots

    // snapshot
    printf("Running the program...\n");
    pushFrame(vm);  // initial frame for main function
    run(vm);

    // Time Travel Debugging: display snapshots of states after execution
    printf("\nSnapshots taken during execution:\n");
    for (int i = 0; i < vm->history.size; i++) {
        State* state = &vm->history.states[i];
        printf("Snapshot %d: PC = %d, SP = %d, ReturnValue = %d\n",
               i, state->pc, state->sp, vm->fstack.frames[vm->fstack.fp]->returnValue);
        printf("Locals: ");
        for (int j = 0; j < LOCALS_SIZE; j++) {
            printf("%d ", state->locals[j]);
        }
        printf("\nStack: ");
        for (int j = 0; j <= state->sp; j++) {
            printf("%d ", state->stack[j]);
        }
        printf("\n\n");
    }

    freeVM(vm);
    return 0;
}
