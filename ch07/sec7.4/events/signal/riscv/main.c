/*
 * RISC-V RV32IM Virtual Machine - Main Program
 * ANSI C implementation
 */

#include "riscv_vm.h"
#include <signal.h>

/* Global VM for signal handling */
static riscv_vm_t *g_vm = NULL;

/* Signal handler for Ctrl+C */
void signal_handler(int sig) {
    if (sig == SIGINT) {
        printf("\n\nExecution interrupted by user\n");
        if (g_vm) {
            g_vm->running = 0;
        }
    }
}

/* Print usage */
void print_usage(const char *progname) {
    printf("Usage: %s [options] <binary_file>\n", progname);
    printf("Options:\n");
    printf("  -d          Enable debug mode\n");
    printf("  -t          Trace instruction execution\n");
    printf("  -r          Print final register state\n");
    printf("  -m start:len  Dump memory region (hex format)\n");
    printf("  -h          Show this help message\n");
}

/* Example interrupt handler implementation */
int example_interrupt_check(void *user_data) {
    /* Return -1 for no interrupt, or interrupt number (0+) if triggered */
    /* This is where you'd check hardware, timers, etc. */
    (void)user_data;  /* Unused */
    return -1;
}

void example_interrupt_handler(void *user_data, int interrupt_num) {
    riscv_vm_t *vm = (riscv_vm_t *)user_data;
    
    /* Handle the interrupt */
    printf("Interrupt %d triggered at PC=0x%08x\n", interrupt_num, vm->pc);
    
    /* You could:
     * - Save context to stack
     * - Jump to interrupt vector
     * - Set special registers
     * - Etc.
     */
}

int main(int argc, char *argv[]) {
    riscv_vm_t *vm;
    int debug = 0, trace = 0, print_regs_flag = 0;
    int memdump = 0;
    uint32_t memdump_start = 0, memdump_len = 0;
    const char *filename = NULL;
    int i;
    
    /* Parse command line arguments */
    for (i = 1; i < argc; i++) {
        if (argv[i][0] == '-') {
            switch (argv[i][1]) {
                case 'd':
                    debug = 1;
                    break;
                case 't':
                    trace = 1;
                    break;
                case 'r':
                    print_regs_flag = 1;
                    break;
                case 'm':
                    if (i + 1 < argc) {
                        char *sep;
                        memdump = 1;
                        sep = strchr(argv[++i], ':');
                        if (sep) {
                            *sep = '\0';
                            memdump_start = strtoul(argv[i], NULL, 16);
                            memdump_len = strtoul(sep + 1, NULL, 16);
                        } else {
                            memdump_start = strtoul(argv[i], NULL, 16);
                            memdump_len = 64;
                        }
                    }
                    break;
                case 'h':
                    print_usage(argv[0]);
                    return 0;
                default:
                    fprintf(stderr, "Unknown option: %s\n", argv[i]);
                    print_usage(argv[0]);
                    return 1;
            }
        } else {
            filename = argv[i];
        }
    }
    
    if (!filename) {
        fprintf(stderr, "Error: No binary file specified\n");
        print_usage(argv[0]);
        return 1;
    }
    
    /* Create VM */
    vm = vm_create(DEFAULT_MEM_SIZE, debug, trace);
    if (!vm) {
        fprintf(stderr, "Error: Failed to create VM\n");
        return 1;
    }
    
    g_vm = vm;
    
    /* Set up signal handler */
    signal(SIGINT, signal_handler);
    
    /* Optional: Set up interrupt handler */
    /* Uncomment to enable interrupt support:
    vm_set_interrupt_handler(vm, 
                            example_interrupt_check,
                            example_interrupt_handler,
                            vm);
    */
    
    /* Load program */
    if (vm_load_program(vm, filename) != 0) {
        vm_destroy(vm);
        return 1;
    }
    
    /* Execute */
    vm_execute(vm);
    
    /* Print statistics if debug mode */
    if (debug) {
        printf("\nExecution completed\n");
        printf("Instructions executed: %lu\n", 
               (unsigned long)vm->instruction_count);
    }
    
    /* Print registers if requested */
    if (print_regs_flag || debug) {
        print_regs(vm);
    }
    
    /* Memory dump if requested */
    if (memdump) {
        dump_memory(vm, memdump_start, memdump_len);
    }
    
    /* Clean up */
    vm_destroy(vm);
    
    return 0;
}
