#define _POSIX_C_SOURCE 200809L
#include "eventscript.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

VM *vm_create(Bytecode *bc) {
    VM *vm = calloc(1, sizeof(VM));
    vm->bytecode = bc;
    vm->sp = 0;
    vm->pc = 0;
    vm->running = true;
    return vm;
}

void vm_free(VM *vm) {
    if (!vm) return;
    
    // Free event queue
    EventQueueEntry *eq = vm->event_queue_head;
    while (eq) {
        EventQueueEntry *next = eq->next;
        free(eq->event_name);
        if (eq->data.type == VAL_STRING) {
            free(eq->data.string);
        }
        free(eq);
        eq = next;
    }
    
    // Free handlers
    EventHandler *eh = vm->handlers;
    while (eh) {
        EventHandler *next = eh->next;
        free(eh->event_name);
        free(eh);
        eh = next;
    }
    
    free(vm);
}

void value_print(Value v) {
    switch (v.type) {
        case VAL_NUMBER:
            printf("%d", v.number);
            break;
        case VAL_STRING:
            printf("%s", v.string);
            break;
        case VAL_NIL:
            printf("nil");
            break;
        default:
            printf("<value>");
            break;
    }
}

const char *opcode_name(OpCode op) {
    switch (op) {
        case OP_CONST: return "CONST";
        case OP_ADD_OP: return "ADD";
        case OP_SUB_OP: return "SUB";
        case OP_MUL_OP: return "MUL";
        case OP_DIV_OP: return "DIV";
        case OP_PRINT_OP: return "PRINT";
        case OP_EMIT: return "EMIT";
        case OP_REGISTER: return "REGISTER";
        case OP_RETURN: return "RETURN";
        case OP_HALT: return "HALT";
        case OP_POP: return "POP";
        case OP_LOAD: return "LOAD";
        case OP_STORE: return "STORE";
        case OP_CALL_FN: return "CALL";
        default: return "UNKNOWN";
    }
}

static void vm_push(VM *vm, Value v) {
    if (vm->sp >= 256) {
        fprintf(stderr, "Stack overflow\n");
        exit(1);
    }
    vm->stack[vm->sp++] = v;
}

static Value vm_pop(VM *vm) {
    if (vm->sp <= 0) {
        fprintf(stderr, "Stack underflow\n");
        exit(1);
    }
    return vm->stack[--vm->sp];
}

static void vm_enqueue_event(VM *vm, const char *event_name, Value data) {
    EventQueueEntry *entry = calloc(1, sizeof(EventQueueEntry));
    entry->event_name = strdup(event_name);
    entry->data = data;
    entry->next = NULL;
    
    if (!vm->event_queue_head) {
        vm->event_queue_head = vm->event_queue_tail = entry;
    } else {
        vm->event_queue_tail->next = entry;
        vm->event_queue_tail = entry;
    }
    
    printf("[EVENT QUEUE] Enqueued: %s\n", event_name);
}

static void vm_register_handler(VM *vm, const char *event_name, size_t handler_pc) {
    EventHandler *handler = calloc(1, sizeof(EventHandler));
    handler->event_name = strdup(event_name);
    handler->handler_pc = handler_pc;
    handler->next = vm->handlers;
    vm->handlers = handler;
    
    printf("[HANDLER] Registered '%s' at PC=%zu\n", event_name, handler_pc);
}

void vm_run(VM *vm) {
    printf("\n** VM EXECUTION START **\n");
    
    while (vm->running && vm->pc < vm->bytecode->size) {
        uint8_t instruction = vm->bytecode->code[vm->pc++];
        
        printf("[PC=%zu] %s ", vm->pc - 1, opcode_name(instruction));
        
        switch (instruction) {
            case OP_CONST: {
                uint8_t const_idx = vm->bytecode->code[vm->pc++];
                Value v = vm->bytecode->constants[const_idx];
                vm_push(vm, v);
                printf("(idx=%d) -> ", const_idx);
                value_print(v);
                printf("\n");
                break;
            }
            
            case OP_ADD_OP:
            case OP_SUB_OP:
            case OP_MUL_OP:
            case OP_DIV_OP: {
                Value b = vm_pop(vm);
                Value a = vm_pop(vm);
                Value result = {.type = VAL_NUMBER};
                
                if (a.type == VAL_NUMBER && b.type == VAL_NUMBER) {
                    switch (instruction) {
                        case OP_ADD_OP: result.number = a.number + b.number; break;
                        case OP_SUB_OP: result.number = a.number - b.number; break;
                        case OP_MUL_OP: result.number = a.number * b.number; break;
                        case OP_DIV_OP: result.number = a.number / b.number; break;
                        default: break;
                    }
                    vm_push(vm, result);
                    printf("-> %d\n", result.number);
                } else {
                    printf("Type error in arithmetic\n");
                }
                break;
            }
            
            case OP_PRINT_OP: {
                Value v = vm_pop(vm);
                printf("-> OUTPUT: ");
                value_print(v);
                printf("\n");
                break;
            }
            
            case OP_EMIT: {
                Value data = vm_pop(vm);
                Value event_name = vm_pop(vm);
                if (event_name.type == VAL_STRING) {
                    vm_enqueue_event(vm, event_name.string, data);
                }
                printf("\n");
                break;
            }
            
            case OP_REGISTER: {
                uint8_t handler_pc = vm->bytecode->code[vm->pc++];
                Value event_name = vm_pop(vm);
                if (event_name.type == VAL_STRING) {
                    vm_register_handler(vm, event_name.string, handler_pc);
                }
                
                // Skip to the RETURN at the end of this handler
                while (vm->pc < vm->bytecode->size && 
                       vm->bytecode->code[vm->pc] != OP_RETURN) {
                    vm->pc++;
                }
                if (vm->pc < vm->bytecode->size) {
                    vm->pc++;  // Skip the RETURN too
                }
                
                printf("\n");
                break;
            }
            
            case OP_RETURN: {
                printf("(return from handler)\n");
                vm->running = false;  // For now, just stop
                break;
            }
            
            case OP_POP: {
                vm_pop(vm);
                printf("\n");
                break;
            }
            
            case OP_HALT: {
                printf("\n=== HALT ===\n");
                vm->running = false;
                break;
            }
            
            default:
                printf("Unknown opcode: %d\n", instruction);
                vm->running = false;
                break;
        }
    }
}

void vm_event_loop(VM *vm) {
    printf("\n** EVENT LOOP START **\n");
    
    int iterations = 0;
    const int MAX_ITERATIONS = 100;
    
    while (vm->event_queue_head && iterations++ < MAX_ITERATIONS) {
        // Dequeue event
        EventQueueEntry *event = vm->event_queue_head;
        vm->event_queue_head = event->next;
        if (!vm->event_queue_head) {
            vm->event_queue_tail = NULL;
        }
        
        printf("\n[EVENT LOOP] Processing: %s (data=", event->event_name);
        value_print(event->data);
        printf(")\n");
        
        // Find and execute handlers
        EventHandler *handler = vm->handlers;
        bool found = false;
        while (handler) {
            if (strcmp(handler->event_name, event->event_name) == 0) {
                found = true;
                printf("[EVENT LOOP] Executing handler at PC=%zu\n", handler->handler_pc);
                
                // Push event data onto stack for handler to use
                vm_push(vm, event->data);
                
                // Save current PC and jump to handler
                size_t saved_pc = vm->pc;
                vm->pc = handler->handler_pc;
                vm->running = true;
                
                // Execute handler
                while (vm->running && vm->pc < vm->bytecode->size) {
                    uint8_t instruction = vm->bytecode->code[vm->pc++];
                    
                    switch (instruction) {
                        case OP_CONST: {
                            uint8_t const_idx = vm->bytecode->code[vm->pc++];
                            vm_push(vm, vm->bytecode->constants[const_idx]);
                            break;
                        }
                        case OP_PRINT_OP: {
                            Value v = vm_pop(vm);
                            printf("  [HANDLER OUTPUT] ");
                            value_print(v);
                            printf("\n");
                            break;
                        }
                        case OP_ADD_OP:
                        case OP_SUB_OP:
                        case OP_MUL_OP:
                        case OP_DIV_OP: {
                            Value b = vm_pop(vm);
                            Value a = vm_pop(vm);
                            Value result = {.type = VAL_NUMBER};
                            if (a.type == VAL_NUMBER && b.type == VAL_NUMBER) {
                                switch (instruction) {
                                    case OP_ADD_OP: result.number = a.number + b.number; break;
                                    case OP_SUB_OP: result.number = a.number - b.number; break;
                                    case OP_MUL_OP: result.number = a.number * b.number; break;
                                    case OP_DIV_OP: result.number = a.number / b.number; break;
                                    default: break;
                                }
                                vm_push(vm, result);
                            }
                            break;
                        }
                        case OP_EMIT: {
                            Value data = vm_pop(vm);
                            Value event_name = vm_pop(vm);
                            if (event_name.type == VAL_STRING) {
                                vm_enqueue_event(vm, event_name.string, data);
                            }
                            break;
                        }
                        case OP_POP:
                            vm_pop(vm);
                            break;
                        case OP_RETURN:
                            vm->running = false;
                            break;
                        default:
                            break;
                    }
                }
                
                // Restore PC
                vm->pc = saved_pc;
            }
            handler = handler->next;
        }
        
        if (!found) {
            printf("[EVENT LOOP] No handler for: %s\n", event->event_name);
        }
        
        // Free event
        free(event->event_name);
        if (event->data.type == VAL_STRING) {
            free(event->data.string);
        }
        free(event);
    }
    
    printf("\n** EVENT LOOP END **\n");
}
