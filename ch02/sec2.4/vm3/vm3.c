#include <stdio.h>
#include <stdlib.h>

#include "vm3.h"

VM* newVM(int* code, int pc) {
    VM* vm = (VM*) malloc(sizeof(VM));
    if (vm == NULL)
        return NULL;
    vm->stack = (int*) malloc(sizeof(int) * STACK_SIZE);
    if (vm->stack == NULL)
        return NULL;

    vm->code = code;
    vm->pc = pc;
    vm->sp = -1;
    vm->fp = 0;

    return vm;
}

void freeVM(VM* vm) {
    if (vm != NULL) {
        free(vm->stack);
        free(vm);
    }
}

int pop(VM* vm) {
    return vm->stack[(vm->sp)--];
}

void push(VM* vm, int v) {
    if (vm->sp + 1 >= STACK_SIZE) {
        fprintf(stderr, "Stack overflow\n");
        exit(1);
    }
    vm->stack[++(vm->sp)] = v;
}

int nextcode(VM* vm) {
    return vm->code[(vm->pc)++];
}

void print_stack(VM* vm) {
    printf("Stack: ");
    for (int i = 0; i <= vm->sp; i++) {
        printf("%d ", vm->stack[i]);
    }
    printf("\n");
}

void print_vm_state(VM* vm) {
    printf("PC: %d, SP: %d, FP: %d\n", vm->pc, vm->sp, vm->fp);
    print_stack(vm);
}

void run(VM* vm) {
    int a, b, v, addr, rval;

    do {
        // DEBUG print_vm_state(vm);

        int opcode = nextcode(vm);
        // DEBUG printf("Executing opcode %d\n", opcode);

        switch (opcode) {
            case HALT:
                return;

            case SET:
                v = nextcode(vm);
                push(vm, v);
                break;

            case SETZ:
                push(vm, 0);
                break;

            case ADD:
                b = pop(vm);
                a = pop(vm);
                push(vm, a + b);
                break;

            case SUB:
                b = pop(vm);
                a = pop(vm);
                push(vm, a - b);
                break;

            case MUL:
                b = pop(vm);
                a = pop(vm);
                push(vm, a * b);
                break;

            case MOD:
                b = pop(vm);
                a = pop(vm);
                push(vm, a % b);
                break;

            case INC:
                a = pop(vm);
                push(vm, a + 1);
                break;

            case DEC:
                a = pop(vm);
                push(vm, a - 1);
                break;

            case CALL:
                addr = nextcode(vm);     // address to jump to
                push(vm, vm->fp);        // save current frame pointer
                push(vm, vm->pc);        // save return address
                vm->fp = vm->sp;         // set new frame pointer
                vm->pc = addr;           // jump to function address
                break;

            case RET:
                rval = pop(vm);          // get return value
                vm->sp = vm->fp;         // restore stack pointer
                vm->pc = pop(vm);        // get return address
                vm->fp = pop(vm);        // restore previous frame pointer
                push(vm, rval);          // push return value onto stack
                break;

            case LD:
                addr = nextcode(vm);     // get local variable index
                v = vm->stack[vm->fp + addr];
                push(vm, v);
                break;

            case ST:
                v = pop(vm);
                addr = nextcode(vm);     // get local variable index
                vm->stack[vm->fp + addr] = v;
                break;

            case AND:
                b = pop(vm);
                a = pop(vm);
                push(vm, a & b);
                break;

            case OR:
                b = pop(vm);
                a = pop(vm);
                push(vm, a | b);
                break;

            case LSH:
                b = pop(vm);
                a = pop(vm);
                push(vm, a << b);
                break;

            case RSH:
                b = pop(vm);
                a = pop(vm);
                push(vm, a >> b);
                break;

            case EQ:
                b = pop(vm);
                a = pop(vm);
                push(vm, (a == b) ? TRUE : FALSE);
                break;

            case EQZ:
                a = pop(vm);
                push(vm, (a == 0) ? TRUE : FALSE);
                break;

            case JP:
                vm->pc = nextcode(vm);
                break;

            case JPNZ:
                addr = nextcode(vm);
                v = pop(vm);
                if (v != 0) {
                    vm->pc = addr;
                }
                break;

            case JPZ:
                addr = nextcode(vm);
                v = pop(vm);
                if (v == 0) {
                    vm->pc = addr;
                }
                break;

            case LOAD:
                addr = nextcode(vm);  // global address
                v = vm->stack[addr];  // load from global
                push(vm, v);
                break;

            case STORE:
                v = pop(vm);          // pop value from stack
                addr = nextcode(vm);  // global address
                vm->stack[addr] = v;  // store in global
                break;

            case DUP:
                a = pop(vm);
                push(vm, a);
                push(vm, a);
                break;

            case DROP:
                pop(vm);
                break;

            case PRINT:
                v = pop(vm);
                printf("%d\n", v);
                break;

            case PRNT:
                v = pop(vm);
                printf("%d", v);
                break;

            default:
                fprintf(stderr, "Unknown opcode %d at PC %d\n", opcode, vm->pc - 1);
                exit(1);
        }

        // print current state after executing instruction
        // DEBUG print_vm_state(vm);

    } while (1);
}
