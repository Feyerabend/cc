/*
 * RISC-V VM Interrupt System
 * Implements IVT (Interrupt Vector Table) with multiple dispatch modes
 */

#ifndef RISCV_INTERRUPT_H
#define RISCV_INTERRUPT_H

#include "riscv_vm.h"

/* Interrupt configuration */
#define MAX_INTERRUPT_HANDLERS 10
#define MAX_INTERRUPTS 32
#define INTERRUPT_QUEUE_SIZE 16

/* Interrupt handler function pointer */
typedef void (*interrupt_handler_fn)(riscv_vm_t *vm, int irq_num, void *data);

/* Single interrupt handler entry */
typedef struct {
    interrupt_handler_fn handler;
    void *user_data;
    int enabled;
} interrupt_handler_entry_t;

/* Interrupt Vector Table entry - multiple handlers per interrupt */
typedef struct {
    interrupt_handler_entry_t handlers[MAX_INTERRUPT_HANDLERS];
    int handler_count;
    int enabled;  /* Master enable for this interrupt */
} ivt_entry_t;

/* Interrupt queue for deferred handling */
typedef struct {
    int queue[INTERRUPT_QUEUE_SIZE];
    int head;
    int tail;
    int count;
} interrupt_queue_t;

/* Main interrupt controller */
typedef struct {
    ivt_entry_t ivt[MAX_INTERRUPTS];
    interrupt_queue_t queue;
    int global_enabled;
    
    /* Statistics */
    unsigned long interrupts_fired[MAX_INTERRUPTS];
    unsigned long interrupts_queued;
    unsigned long interrupts_dropped;
    
    /* Dispatch mode */
    enum {
        DISPATCH_IMMEDIATE,  /* Call handlers immediately */
        DISPATCH_QUEUED      /* Queue for later processing */
    } mode;
    
    riscv_vm_t *vm;
} interrupt_controller_t;

/* Public API */
interrupt_controller_t *interrupt_controller_create(riscv_vm_t *vm);
void interrupt_controller_destroy(interrupt_controller_t *ic);

/* Register/unregister handlers */
int interrupt_register_handler(interrupt_controller_t *ic, 
                               int irq_num,
                               interrupt_handler_fn handler,
                               void *user_data);

int interrupt_unregister_handler(interrupt_controller_t *ic,
                                 int irq_num,
                                 interrupt_handler_fn handler);

/* Enable/disable */
void interrupt_enable(interrupt_controller_t *ic, int irq_num);
void interrupt_disable(interrupt_controller_t *ic, int irq_num);
void interrupt_enable_global(interrupt_controller_t *ic);
void interrupt_disable_global(interrupt_controller_t *ic);

/* Fire an interrupt */
void interrupt_fire(interrupt_controller_t *ic, int irq_num);

/* Process queued interrupts (for DISPATCH_QUEUED mode) */
int interrupt_process_queue(interrupt_controller_t *ic);

/* Set dispatch mode */
void interrupt_set_mode(interrupt_controller_t *ic, int mode);

/* Statistics */
void interrupt_print_stats(interrupt_controller_t *ic);

#endif /* RISCV_INTERRUPT_H */
