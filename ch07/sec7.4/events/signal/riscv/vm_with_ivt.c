/*
 * RISC-V VM with Interrupt Vector Table - Complete Example
 * 
 * This demonstrates:
 * 1. Multiple handlers per interrupt (like pthread.c)
 * 2. Immediate and queued dispatch modes (like queue.c)
 * 3. IVT-based interrupt routing (like sig.c)
 */

#define _POSIX_C_SOURCE 200112L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include "riscv_vm.h"
#include "riscv_interrupt.h"

/* Example interrupt numbers */
#define IRQ_TIMER           0
#define IRQ_INSTRUCTION     1
#define IRQ_WATCHPOINT      2
#define IRQ_BREAKPOINT      3

/* Timer-based interrupt source */
typedef struct {
    unsigned long period;
    unsigned long counter;
} timer_source_t;

/* Instruction count based interrupt */
typedef struct {
    unsigned long threshold;
    unsigned long last_count;
    riscv_vm_t *vm;
} instruction_count_source_t;

/* Memory watchpoint interrupt */
typedef struct {
    uint32_t watch_addr;
    uint32_t last_value;
    int initialized;
    riscv_vm_t *vm;
} watchpoint_source_t;

/* Global interrupt controller */
interrupt_controller_t *g_ic = NULL;

/* Signal handler to trigger VM interrupt */
void sigusr1_handler(int sig) {
    (void)sig;
    if (g_ic) {
        printf("\n[HOST] Received SIGUSR1, firing IRQ_BREAKPOINT\n");
        interrupt_fire(g_ic, IRQ_BREAKPOINT);
    }
}

/* Example interrupt handlers */

void timer_handler_A(riscv_vm_t *vm, int irq, void *data) {
    (void)data;
    printf("[IRQ %d] Timer Handler A - PC=0x%08x, instructions=%lu\n",
           irq, vm->pc, vm->instruction_count);
}

void timer_handler_B(riscv_vm_t *vm, int irq, void *data) {
    (void)data;
    printf("[IRQ %d] Timer Handler B - Registers: a0=0x%x, a1=0x%x\n",
           irq, vm->regs[10], vm->regs[11]);
}

void instruction_count_handler(riscv_vm_t *vm, int irq, void *data) {
    unsigned long *milestone = (unsigned long *)data;
    (void)vm;
    printf("[IRQ %d] Milestone reached: %lu instructions executed\n",
           irq, *milestone);
    *milestone += 10000;  /* Next milestone */
}

void watchpoint_handler(riscv_vm_t *vm, int irq, void *data) {
    uint32_t *addr = (uint32_t *)data;
    uint32_t value = read_mem(vm, *addr, 4, 0);
    printf("[IRQ %d] Watchpoint triggered! Address 0x%08x changed to 0x%08x\n",
           irq, *addr, value);
}

void breakpoint_handler(riscv_vm_t *vm, int irq, void *data) {
    (void)data;
    printf("[IRQ %d] Breakpoint! Halting execution.\n", irq);
    printf("PC=0x%08x, SP=0x%08x\n", vm->pc, vm->regs[2]);
    print_regs(vm);
    vm->running = 0;
}

/* Advanced: Context-saving interrupt handler */
void context_save_handler(riscv_vm_t *vm, int irq, void *data) {
    uint32_t *stack_save = (uint32_t *)data;
    
    printf("[IRQ %d] Saving context to stack...\n", irq);
    
    /* Push PC onto stack */
    vm->regs[2] -= 4;
    write_mem(vm, vm->regs[2], vm->pc, 4);
    
    /* Push a few registers */
    vm->regs[2] -= 4;
    write_mem(vm, vm->regs[2], vm->regs[10], 4);  /* a0 */
    vm->regs[2] -= 4;
    write_mem(vm, vm->regs[2], vm->regs[11], 4);  /* a1 */
    
    *stack_save = vm->regs[2];  /* Save stack pointer */
    
    /* Could jump to ISR here */
    /* vm->pc = 0x1000;  // ISR address */
}

/* Custom interrupt source: PC-based breakpoint */
typedef struct {
    uint32_t breakpoint_pc;
    riscv_vm_t *vm;
} breakpoint_source_t;

/* Interrupt check functions */
int check_timer(void *user_data) {
    timer_source_t *timer = (timer_source_t *)user_data;
    
    timer->counter++;
    if (timer->counter >= timer->period) {
        timer->counter = 0;
        return IRQ_TIMER;
    }
    return -1;
}

int check_instruction_count(void *user_data) {
    instruction_count_source_t *src = (instruction_count_source_t *)user_data;
    
    if (src->vm->instruction_count >= src->last_count + src->threshold) {
        src->last_count = src->vm->instruction_count;
        return IRQ_INSTRUCTION;
    }
    return -1;
}

int check_watchpoint(void *user_data) {
    watchpoint_source_t *wp = (watchpoint_source_t *)user_data;
    uint32_t current_value;
    
    if (wp->watch_addr >= wp->vm->mem_size) {
        return -1;
    }
    
    current_value = read_mem(wp->vm, wp->watch_addr, 4, 0);
    
    if (!wp->initialized) {
        wp->last_value = current_value;
        wp->initialized = 1;
        return -1;
    }
    
    if (current_value != wp->last_value) {
        wp->last_value = current_value;
        return IRQ_WATCHPOINT;
    }
    
    return -1;
}

int check_breakpoint(void *user_data) {
    breakpoint_source_t *bp = (breakpoint_source_t *)user_data;
    if (bp->vm->pc == bp->breakpoint_pc) {
        return IRQ_BREAKPOINT;
    }
    return -1;
}

/* Main program */
int main(int argc, char *argv[]) {
    riscv_vm_t *vm;
    interrupt_controller_t *ic;
    const char *binary_file;
    
    /* Interrupt source data */
    timer_source_t timer_src = {1000, 0};
    instruction_count_source_t inst_src;
    watchpoint_source_t wp_src;
    breakpoint_source_t bp_src;
    unsigned long milestone = 10000;
    uint32_t watch_addr = 0x100;
    uint32_t stack_save = 0;
    
    /* Initialize structures */
    memset(&inst_src, 0, sizeof(inst_src));
    memset(&wp_src, 0, sizeof(wp_src));
    memset(&bp_src, 0, sizeof(bp_src));
    
    if (argc < 2) {
        printf("RISC-V VM with Interrupt Vector Table Demo\n");
        printf("Usage: %s <binary_file> [options]\n\n", argv[0]);
        printf("Options:\n");
        printf("  -q         Use queued dispatch mode\n");
        printf("  -b ADDR    Set breakpoint at address (hex)\n");
        printf("  -w ADDR    Set memory watchpoint (hex)\n");
        printf("\n");
        printf("While running, send SIGUSR1 to trigger breakpoint:\n");
        printf("  kill -USR1 <pid>\n");
        return 1;
    }
    
    binary_file = argv[1];
    
    /* Create VM */
    vm = vm_create(DEFAULT_MEM_SIZE, 1, 0);
    if (!vm) {
        fprintf(stderr, "Failed to create VM\n");
        return 1;
    }
    
    /* Create interrupt controller */
    ic = interrupt_controller_create(vm);
    if (!ic) {
        fprintf(stderr, "Failed to create interrupt controller\n");
        vm_destroy(vm);
        return 1;
    }
    
    g_ic = ic;
    
    /* Parse options */
    {
        int i;
        for (i = 2; i < argc; i++) {
            if (strcmp(argv[i], "-q") == 0) {
                interrupt_set_mode(ic, DISPATCH_QUEUED);
                printf("Using QUEUED dispatch mode\n");
            } else if (strcmp(argv[i], "-b") == 0 && i + 1 < argc) {
                bp_src.breakpoint_pc = strtoul(argv[++i], NULL, 16);
                printf("Breakpoint set at PC=0x%08x\n", bp_src.breakpoint_pc);
            } else if (strcmp(argv[i], "-w") == 0 && i + 1 < argc) {
                watch_addr = strtoul(argv[++i], NULL, 16);
                printf("Watchpoint set at 0x%08x\n", watch_addr);
            }
        }
    }
    
    /* Register signal handler for external interrupts */
    {
        struct sigaction sa;
        sa.sa_handler = sigusr1_handler;
        sa.sa_flags = 0;
        sigemptyset(&sa.sa_mask);
        sigaction(SIGUSR1, &sa, NULL);
        printf("PID: %d (send SIGUSR1 for breakpoint)\n", getpid());
    }
    
    /* Register interrupt handlers in IVT */
    
    /* Timer - multiple handlers */
    interrupt_register_handler(ic, IRQ_TIMER, timer_handler_A, NULL);
    interrupt_register_handler(ic, IRQ_TIMER, timer_handler_B, NULL);
    
    /* Instruction count */
    inst_src.threshold = 10000;
    inst_src.last_count = 0;
    inst_src.vm = vm;
    interrupt_register_handler(ic, IRQ_INSTRUCTION, 
                              instruction_count_handler, 
                              &milestone);
    
    /* Watchpoint */
    wp_src.watch_addr = watch_addr;
    wp_src.vm = vm;
    wp_src.initialized = 0;
    interrupt_register_handler(ic, IRQ_WATCHPOINT, 
                              watchpoint_handler, 
                              &watch_addr);
    
    /* Breakpoint - multiple handlers */
    bp_src.vm = vm;
    interrupt_register_handler(ic, IRQ_BREAKPOINT, 
                              context_save_handler, 
                              &stack_save);
    interrupt_register_handler(ic, IRQ_BREAKPOINT, 
                              breakpoint_handler, 
                              NULL);
    
    /* Set up interrupt sources as VM interrupt check */
    vm_set_interrupt_handler(vm,
        /* Check function - polls all sources */
        (int (*)(void *))NULL,  /* We'll check manually in loop */
        /* Handler - fires interrupt in IC */
        (void (*)(void *, int))NULL,
        ic);
    
    /* Load program */
    if (vm_load_program(vm, binary_file) != 0) {
        interrupt_controller_destroy(ic);
        vm_destroy(vm);
        return 1;
    }
    
    printf("\n=== Starting execution ===\n");
    printf("Interrupts configured:\n");
    printf("  IRQ %d: Timer (every %lu instructions)\n", 
           IRQ_TIMER, timer_src.period);
    printf("  IRQ %d: Instruction milestone (every %lu)\n", 
           IRQ_INSTRUCTION, inst_src.threshold);
    printf("  IRQ %d: Memory watchpoint (addr 0x%08x)\n", 
           IRQ_WATCHPOINT, watch_addr);
    printf("  IRQ %d: Breakpoint (SIGUSR1 or PC match)\n\n", 
           IRQ_BREAKPOINT);
    
    /* Main execution loop with interrupt checking */
    while (vm->running) {
        int irq;
        
        /* Execute one instruction */
        vm_step(vm);
        
        /* Check interrupt sources */
        irq = check_timer(&timer_src);
        if (irq >= 0) interrupt_fire(ic, irq);
        
        irq = check_instruction_count(&inst_src);
        if (irq >= 0) interrupt_fire(ic, irq);
        
        irq = check_watchpoint(&wp_src);
        if (irq >= 0) interrupt_fire(ic, irq);
        
        irq = check_breakpoint(&bp_src);
        if (irq >= 0) interrupt_fire(ic, irq);
        
        /* If using queued mode, process queue periodically */
        if (ic->mode == DISPATCH_QUEUED && 
            vm->instruction_count % 100 == 0) {
            interrupt_process_queue(ic);
        }
    }
    
    printf("\n=== Execution completed ===\n");
    
    /* Final queue processing if in queued mode */
    if (ic->mode == DISPATCH_QUEUED) {
        int processed = interrupt_process_queue(ic);
        if (processed > 0) {
            printf("Processed %d queued interrupts\n", processed);
        }
    }
    
    /* Print statistics */
    interrupt_print_stats(ic);
    print_regs(vm);
    
    /* Cleanup */
    interrupt_controller_destroy(ic);
    vm_destroy(vm);
    
    return 0;
}
