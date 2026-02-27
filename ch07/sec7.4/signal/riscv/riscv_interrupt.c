/*
 * RISC-V VM Interrupt System Implementation
 */

#include "riscv_interrupt.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Create interrupt controller */
interrupt_controller_t *interrupt_controller_create(riscv_vm_t *vm) {
    interrupt_controller_t *ic;
    int i, j;
    
    ic = (interrupt_controller_t *)calloc(1, sizeof(interrupt_controller_t));
    if (!ic) return NULL;
    
    ic->vm = vm;
    ic->global_enabled = 1;
    ic->mode = DISPATCH_IMMEDIATE;
    
    /* Initialize IVT */
    for (i = 0; i < MAX_INTERRUPTS; i++) {
        ic->ivt[i].enabled = 1;
        ic->ivt[i].handler_count = 0;
        for (j = 0; j < MAX_INTERRUPT_HANDLERS; j++) {
            ic->ivt[i].handlers[j].handler = NULL;
            ic->ivt[i].handlers[j].user_data = NULL;
            ic->ivt[i].handlers[j].enabled = 1;
        }
    }
    
    /* Initialize queue */
    ic->queue.head = 0;
    ic->queue.tail = 0;
    ic->queue.count = 0;
    
    return ic;
}

/* Destroy interrupt controller */
void interrupt_controller_destroy(interrupt_controller_t *ic) {
    if (ic) {
        free(ic);
    }
}

/* Register a handler for an interrupt */
int interrupt_register_handler(interrupt_controller_t *ic,
                               int irq_num,
                               interrupt_handler_fn handler,
                               void *user_data) {
    ivt_entry_t *entry;
    int i;
    
    if (!ic || irq_num < 0 || irq_num >= MAX_INTERRUPTS || !handler) {
        return -1;
    }
    
    entry = &ic->ivt[irq_num];
    
    /* Check if already registered */
    for (i = 0; i < entry->handler_count; i++) {
        if (entry->handlers[i].handler == handler) {
            return 0;  /* Already registered */
        }
    }
    
    /* Add new handler */
    if (entry->handler_count >= MAX_INTERRUPT_HANDLERS) {
        fprintf(stderr, "Interrupt %d: handler table full\n", irq_num);
        return -1;
    }
    
    entry->handlers[entry->handler_count].handler = handler;
    entry->handlers[entry->handler_count].user_data = user_data;
    entry->handlers[entry->handler_count].enabled = 1;
    entry->handler_count++;
    
    return 0;
}

/* Unregister a handler */
int interrupt_unregister_handler(interrupt_controller_t *ic,
                                int irq_num,
                                interrupt_handler_fn handler) {
    ivt_entry_t *entry;
    int i, j;
    
    if (!ic || irq_num < 0 || irq_num >= MAX_INTERRUPTS || !handler) {
        return -1;
    }
    
    entry = &ic->ivt[irq_num];
    
    /* Find and remove handler */
    for (i = 0; i < entry->handler_count; i++) {
        if (entry->handlers[i].handler == handler) {
            /* Shift remaining handlers down */
            for (j = i; j < entry->handler_count - 1; j++) {
                entry->handlers[j] = entry->handlers[j + 1];
            }
            entry->handler_count--;
            return 0;
        }
    }
    
    return -1;  /* Not found */
}

/* Enable/disable specific interrupt */
void interrupt_enable(interrupt_controller_t *ic, int irq_num) {
    if (ic && irq_num >= 0 && irq_num < MAX_INTERRUPTS) {
        ic->ivt[irq_num].enabled = 1;
    }
}

void interrupt_disable(interrupt_controller_t *ic, int irq_num) {
    if (ic && irq_num >= 0 && irq_num < MAX_INTERRUPTS) {
        ic->ivt[irq_num].enabled = 0;
    }
}

/* Global enable/disable */
void interrupt_enable_global(interrupt_controller_t *ic) {
    if (ic) ic->global_enabled = 1;
}

void interrupt_disable_global(interrupt_controller_t *ic) {
    if (ic) ic->global_enabled = 0;
}

/* Set dispatch mode */
void interrupt_set_mode(interrupt_controller_t *ic, int mode) {
    if (ic) {
        ic->mode = mode;
    }
}

/* Queue an interrupt for deferred processing */
static void queue_interrupt(interrupt_controller_t *ic, int irq_num) {
    if (ic->queue.count >= INTERRUPT_QUEUE_SIZE) {
        ic->interrupts_dropped++;
        if (ic->vm->debug) {
            fprintf(stderr, "Interrupt queue full, dropped IRQ %d\n", irq_num);
        }
        return;
    }
    
    ic->queue.queue[ic->queue.tail] = irq_num;
    ic->queue.tail = (ic->queue.tail + 1) % INTERRUPT_QUEUE_SIZE;
    ic->queue.count++;
    ic->interrupts_queued++;
}

/* Dispatch interrupt handlers immediately */
static void dispatch_immediate(interrupt_controller_t *ic, int irq_num) {
    ivt_entry_t *entry = &ic->ivt[irq_num];
    int i;
    
    if (ic->vm->debug) {
        printf("[IVT] IRQ %d fired, dispatching %d handlers\n", 
               irq_num, entry->handler_count);
    }
    
    for (i = 0; i < entry->handler_count; i++) {
        if (entry->handlers[i].enabled && entry->handlers[i].handler) {
            entry->handlers[i].handler(ic->vm, 
                                      irq_num, 
                                      entry->handlers[i].user_data);
        }
    }
}

/* Fire an interrupt */
void interrupt_fire(interrupt_controller_t *ic, int irq_num) {
    if (!ic || irq_num < 0 || irq_num >= MAX_INTERRUPTS) {
        return;
    }
    
    /* Check if interrupt is enabled */
    if (!ic->global_enabled || !ic->ivt[irq_num].enabled) {
        return;
    }
    
    /* Update statistics */
    ic->interrupts_fired[irq_num]++;
    
    /* Dispatch based on mode */
    if (ic->mode == DISPATCH_IMMEDIATE) {
        dispatch_immediate(ic, irq_num);
    } else {
        queue_interrupt(ic, irq_num);
    }
}

/* Process queued interrupts */
int interrupt_process_queue(interrupt_controller_t *ic) {
    int processed = 0;
    
    if (!ic) return 0;
    
    while (ic->queue.count > 0) {
        int irq_num = ic->queue.queue[ic->queue.head];
        ic->queue.head = (ic->queue.head + 1) % INTERRUPT_QUEUE_SIZE;
        ic->queue.count--;
        
        dispatch_immediate(ic, irq_num);
        processed++;
    }
    
    return processed;
}

/* Print interrupt statistics */
void interrupt_print_stats(interrupt_controller_t *ic) {
    int i;
    
    if (!ic) return;
    
    printf("\n=== Interrupt Statistics ===\n");
    printf("Mode: %s\n", ic->mode == DISPATCH_IMMEDIATE ? "IMMEDIATE" : "QUEUED");
    printf("Global enabled: %s\n", ic->global_enabled ? "YES" : "NO");
    printf("Queued: %lu, Dropped: %lu\n", 
           ic->interrupts_queued, ic->interrupts_dropped);
    
    printf("\nPer-interrupt counts:\n");
    for (i = 0; i < MAX_INTERRUPTS; i++) {
        if (ic->interrupts_fired[i] > 0) {
            printf("  IRQ %2d: %10lu fires, %d handlers, %s\n",
                   i, 
                   ic->interrupts_fired[i],
                   ic->ivt[i].handler_count,
                   ic->ivt[i].enabled ? "enabled" : "disabled");
        }
    }
    printf("\n");
}
