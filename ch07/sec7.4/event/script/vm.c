#define _POSIX_C_SOURCE 200809L
#include "eventscript.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/select.h>

VM *vm_create(Bytecode *bc) {
    VM *vm = calloc(1, sizeof(VM));
    vm->bytecode = bc;
    vm->sp = 0;
    vm->pc = 0;
    vm->running = true;
    vm->loop_active = false;
    vm->timers = NULL;
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
    
    // Free timers
    TimerEntry *te = vm->timers;
    while (te) {
        TimerEntry *next = te->next;
        free(te->event_name);
        if (te->data.type == VAL_STRING) {
            free(te->data.string);
        }
        free(te);
        te = next;
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
        case OP_TIMER: return "TIMER";
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

static void vm_schedule_timer(VM *vm, int delay_ms, const char *event_name, Value data) {
    TimerEntry *timer = calloc(1, sizeof(TimerEntry));
    timer->event_name = strdup(event_name);
    timer->data = data;
    
    // Calculate trigger time
    gettimeofday(&timer->trigger_time, NULL);
    timer->trigger_time.tv_sec += delay_ms / 1000;
    timer->trigger_time.tv_usec += (delay_ms % 1000) * 1000;
    
    // Normalize microseconds
    if (timer->trigger_time.tv_usec >= 1000000) {
        timer->trigger_time.tv_sec += timer->trigger_time.tv_usec / 1000000;
        timer->trigger_time.tv_usec %= 1000000;
    }
    
    // Insert in sorted order (earliest first)
    TimerEntry **current = &vm->timers;
    while (*current) {
        if (timer->trigger_time.tv_sec < (*current)->trigger_time.tv_sec ||
            (timer->trigger_time.tv_sec == (*current)->trigger_time.tv_sec &&
             timer->trigger_time.tv_usec < (*current)->trigger_time.tv_usec)) {
            break;
        }
        current = &(*current)->next;
    }
    timer->next = *current;
    *current = timer;
    
    printf("[TIMER] Scheduled '%s' for +%dms\n", event_name, delay_ms);
}

static void vm_register_handler(VM *vm, const char *event_name, size_t handler_pc) {
    EventHandler *handler = calloc(1, sizeof(EventHandler));
    handler->event_name = strdup(event_name);
    handler->handler_pc = handler_pc;
    handler->next = vm->handlers;
    vm->handlers = handler;
    
    printf("[HANDLER] Registered '%s' at PC=%zu\n", event_name, handler_pc);
}

static void vm_execute_handler(VM *vm, size_t handler_pc, Value event_data) {
    // Push event data onto stack
    vm_push(vm, event_data);
    
    // Save current PC and jump to handler
    size_t saved_pc = vm->pc;
    vm->pc = handler_pc;
    bool saved_running = vm->running;
    vm->running = true;
    
    // Execute handler bytecode
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
            case OP_TIMER: {
                Value data = vm_pop(vm);
                Value event_name = vm_pop(vm);
                Value delay = vm_pop(vm);
                if (delay.type == VAL_NUMBER && event_name.type == VAL_STRING) {
                    vm_schedule_timer(vm, delay.number, event_name.string, data);
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
    
    // Restore state
    vm->pc = saved_pc;
    vm->running = saved_running;
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
                    printf("Type error\n");
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
            
            case OP_TIMER: {
                Value data = vm_pop(vm);
                Value event_name = vm_pop(vm);
                Value delay = vm_pop(vm);
                if (delay.type == VAL_NUMBER && event_name.type == VAL_STRING) {
                    vm_schedule_timer(vm, delay.number, event_name.string, data);
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
                
                // Skip to RETURN
                while (vm->pc < vm->bytecode->size && 
                       vm->bytecode->code[vm->pc] != OP_RETURN) {
                    vm->pc++;
                }
                if (vm->pc < vm->bytecode->size) {
                    vm->pc++;
                }
                
                printf("\n");
                break;
            }
            
            case OP_RETURN: {
                printf("(return)\n");
                vm->running = false;
                break;
            }
            
            case OP_POP: {
                vm_pop(vm);
                printf("\n");
                break;
            }
            
            case OP_HALT: {
                printf("\n** HALT **\n");
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

// Process event queue once
void vm_event_loop(VM *vm) {
    printf("\n** EVENT LOOP (Single Pass) **\n");
    
    while (vm->event_queue_head) {
        EventQueueEntry *event = vm->event_queue_head;
        vm->event_queue_head = event->next;
        if (!vm->event_queue_head) {
            vm->event_queue_tail = NULL;
        }
        
        printf("\n[EVENT] Processing: %s (data=", event->event_name);
        value_print(event->data);
        printf(")\n");
        
        // Find and execute matching handlers
        EventHandler *handler = vm->handlers;
        bool found = false;
        while (handler) {
            if (strcmp(handler->event_name, event->event_name) == 0) {
                found = true;
                printf("[EVENT] Executing handler at PC=%zu\n", handler->handler_pc);
                vm_execute_handler(vm, handler->handler_pc, event->data);
            }
            handler = handler->next;
        }
        
        if (!found) {
            printf("[EVENT] No handler for: %s\n", event->event_name);
        }
        
        free(event->event_name);
        if (event->data.type == VAL_STRING) {
            free(event->data.string);
        }
        free(event);
    }
    
    printf("\n** EVENT LOOP END **\n");
}

// TRUE EVENT LOOP - Continuous operation with timers
void vm_event_loop_forever(VM *vm) {
    printf("\n** EVENT LOOP (Continuous Mode) **\n");
    printf("[LOOP] Entering continuous event loop...\n");
    printf("[LOOP] Press Ctrl+C to stop\n\n");
    
    vm->loop_active = true;
    int iteration = 0;
    
    while (vm->loop_active) {
        struct timeval now, timeout;
        gettimeofday(&now, NULL);
        
        // Check for expired timers
        while (vm->timers) {
            TimerEntry *timer = vm->timers;
            
            if (timer->trigger_time.tv_sec < now.tv_sec ||
                (timer->trigger_time.tv_sec == now.tv_sec &&
                 timer->trigger_time.tv_usec <= now.tv_usec)) {
                
                // Timer expired - enqueue event
                printf("[TIMER FIRED] '%s' triggered\n", timer->event_name);
                vm_enqueue_event(vm, timer->event_name, timer->data);
                
                // Remove timer
                vm->timers = timer->next;
                free(timer->event_name);
                if (timer->data.type == VAL_STRING) {
                    free(timer->data.string);
                }
                free(timer);
            } else {
                break;  // No more expired timers
            }
        }
        
        // Process event queue
        while (vm->event_queue_head) {
            EventQueueEntry *event = vm->event_queue_head;
            vm->event_queue_head = event->next;
            if (!vm->event_queue_head) {
                vm->event_queue_tail = NULL;
            }
            
            printf("\n[EVENT #%d] Processing: %s (data=", ++iteration, event->event_name);
            value_print(event->data);
            printf(")\n");
            
            // Execute handlers
            EventHandler *handler = vm->handlers;
            while (handler) {
                if (strcmp(handler->event_name, event->event_name) == 0) {
                    printf("[EVENT] → Handler at PC=%zu\n", handler->handler_pc);
                    vm_execute_handler(vm, handler->handler_pc, event->data);
                }
                handler = handler->next;
            }
            
            free(event->event_name);
            if (event->data.type == VAL_STRING) {
                free(event->data.string);
            }
            free(event);
        }
        
        // Calculate sleep time until next timer
        if (vm->timers) {
            TimerEntry *next_timer = vm->timers;
            timeout.tv_sec = next_timer->trigger_time.tv_sec - now.tv_sec;
            timeout.tv_usec = next_timer->trigger_time.tv_usec - now.tv_usec;
            
            if (timeout.tv_usec < 0) {
                timeout.tv_sec--;
                timeout.tv_usec += 1000000;
            }
            
            if (timeout.tv_sec < 0) {
                timeout.tv_sec = 0;
                timeout.tv_usec = 0;
            }
        } else {
            // No timers - check every 100ms
            timeout.tv_sec = 0;
            timeout.tv_usec = 100000;
        }
        
        // Non-blocking wait (using select for portability)
        select(0, NULL, NULL, NULL, &timeout);
        
        // Exit if no more timers and no events
        if (!vm->timers && !vm->event_queue_head) {
            printf("\n[LOOP] No pending events or timers - exiting\n");
            break;
        }
    }
    
    printf("\n** EVENT LOOP STOPPED **\n");
}
