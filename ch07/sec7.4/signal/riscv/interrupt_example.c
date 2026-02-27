/*
 * Example: Timer Interrupt Implementation
 * 
 * This demonstrates how to implement a timer interrupt that fires
 * every N instructions.
 */

#include "riscv_vm.h"

/* Timer state */
typedef struct {
    riscv_vm_t *vm;
    unsigned long timer_period;
    unsigned long timer_counter;
    int enabled;
} timer_t;

/* Check if timer interrupt should fire */
int timer_check(void *user_data) {
    timer_t *timer = (timer_t *)user_data;
    
    if (!timer->enabled) {
        return -1;
    }
    
    timer->timer_counter++;
    
    if (timer->timer_counter >= timer->timer_period) {
        timer->timer_counter = 0;
        return 0;  /* Timer interrupt number */
    }
    
    return -1;  /* No interrupt */
}

/* Handle timer interrupt */
void timer_handler(void *user_data, int interrupt_num) {
    timer_t *timer = (timer_t *)user_data;
    riscv_vm_t *vm = timer->vm;
    
    (void)interrupt_num;  /* We know it's timer */
    
    printf("\n[TIMER INTERRUPT at PC=0x%08x, instruction %lu]\n",
           vm->pc, vm->instruction_count);
    
    /* Example: You could implement interrupt vector jumping here
     * 
     * Save return address to stack:
     * vm->regs[2] -= 4;  // sp
     * write_mem(vm, vm->regs[2], vm->pc, 4);
     * 
     * Jump to interrupt handler:
     * vm->pc = 0x1000;  // Interrupt vector address
     */
}

/* Example main showing timer usage */
int example_timer_main(int argc, char *argv[]) {
    riscv_vm_t *vm;
    timer_t timer;
    const char *filename;
    
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <binary_file>\n", argv[0]);
        return 1;
    }
    
    filename = argv[1];
    
    /* Create VM */
    vm = vm_create(DEFAULT_MEM_SIZE, 1, 0);
    if (!vm) {
        fprintf(stderr, "Failed to create VM\n");
        return 1;
    }
    
    /* Initialize timer */
    timer.vm = vm;
    timer.timer_period = 1000;  /* Fire every 1000 instructions */
    timer.timer_counter = 0;
    timer.enabled = 1;
    
    /* Register interrupt handler */
    vm_set_interrupt_handler(vm, timer_check, timer_handler, &timer);
    
    /* Load and run program */
    if (vm_load_program(vm, filename) != 0) {
        vm_destroy(vm);
        return 1;
    }
    
    vm_execute(vm);
    
    printf("\nFinal state:\n");
    print_regs(vm);
    
    vm_destroy(vm);
    return 0;
}

/*
 * INTERRUPT IMPLEMENTATION NOTES
 * 
 * 1. CONTEXT SWITCHING
 * When an interrupt fires, you typically need to:
 * - Save PC and important registers to a stack or special location
 * - Jump to an interrupt vector (fixed address or from a table)
 * - Execute interrupt service routine (ISR)
 * - Restore context and return
 * 
 * Example ISR entry:
 * 
 *   void handle_interrupt(void *data, int irq_num) {
 *       riscv_vm_t *vm = (riscv_vm_t *)data;
 *       uint32_t saved_pc = vm->pc;
 *       
 *       // Push PC onto stack
 *       vm->regs[2] -= 4;  // sp
 *       write_mem(vm, vm->regs[2], saved_pc, 4);
 *       
 *       // Push other registers if needed
 *       // ...
 *       
 *       // Jump to ISR
 *       vm->pc = interrupt_vector_table[irq_num];
 *   }
 * 
 * Then your RISC-V ISR code would end with:
 * - Pop registers
 * - JALR or JR to return
 * 
 * 
 * 2. INTERRUPT PRIORITIES
 * The check function can implement priorities:
 * 
 *   int check_interrupts(void *data) {
 *       if (critical_error) return IRQ_ERROR;
 *       if (timer_expired) return IRQ_TIMER;
 *       if (io_ready) return IRQ_IO;
 *       return -1;
 *   }
 * 
 * 
 * 3. INTERRUPT MASKING
 * You can implement enable/disable:
 * 
 *   typedef struct {
 *       int enabled;
 *       uint32_t mask;
 *   } interrupt_controller_t;
 *   
 *   int check_interrupts(void *data) {
 *       interrupt_controller_t *ic = data;
 *       if (!ic->enabled) return -1;
 *       
 *       if ((pending & ic->mask) & IRQ_TIMER) 
 *           return IRQ_TIMER;
 *       // ...
 *   }
 * 
 * 
 * 4. HARDWARE PERIPHERALS
 * Simulate memory-mapped I/O:
 * 
 *   - Reserve memory regions (e.g., 0xFFFF0000+)
 *   - Intercept reads/writes in read_mem/write_mem
 *   - Trigger interrupts when peripheral state changes
 * 
 * Example:
 * 
 *   void write_mem(vm, addr, val, size) {
 *       if (addr >= 0xFFFF0000) {
 *           // Memory-mapped peripheral
 *           handle_peripheral_write(addr, val);
 *           return;
 *       }
 *       // Normal memory write
 *       ...
 *   }
 * 
 * 
 * 5. REAL-TIME CONSTRAINTS
 * For cycle-accurate simulation or real-time response:
 * 
 *   - Keep interrupt check function fast (just flag checking)
 *   - Use actual time if simulating real hardware
 *   - Consider instruction timing tables for accuracy
 * 
 * Example with real time:
 * 
 *   int timer_check(void *data) {
 *       timer_t *t = data;
 *       struct timeval now;
 *       gettimeofday(&now, NULL);
 *       
 *       long elapsed = (now.tv_sec - t->last.tv_sec) * 1000000 +
 *                      (now.tv_usec - t->last.tv_usec);
 *       
 *       if (elapsed >= t->period_us) {
 *           t->last = now;
 *           return IRQ_TIMER;
 *       }
 *       return -1;
 *   }
 */
