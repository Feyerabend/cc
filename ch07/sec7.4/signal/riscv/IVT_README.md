
## RISC-V VM with Interrupt Vector Table

This version of the RISC-V VM implements an interrupt handling system
inspired by Unix signal handling patterns (`sig.c`, `pthread.c`, `queue.c`).


#### 1. Interrupt Vector Table (IVT)
- *Multiple handlers per interrupt* - Like `sig.c` and `pthread.c`,
  you can register multiple handlers for the same interrupt
- *32 interrupt vectors* - Support for up to 32 different interrupt types
- *Per-handler enable/disable* - Fine-grained control over which handlers execute


#### 2. Dispatch Modes

__Immediate Dispatch (like `sig.c` and `pthread.c`)__

Handlers execute immediately when the interrupt fires:
```c
interrupt_set_mode(ic, DISPATCH_IMMEDIATE);
```

__Queued Dispatch (like `queue.c`)__

Interrupts are queued and processed later:
```c
interrupt_set_mode(ic, DISPATCH_QUEUED);
/* Later... */
interrupt_process_queue(ic);
```


#### 3. Built-in Interrupt Sources
- *Timer* - Fire every N instructions
- *Instruction count* - Milestone-based interrupts
- *Memory watchpoint* - Trigger when memory location changes
- *Breakpoint* - Stop at specific PC address or via signal


### Building

```bash
make              # Build both versions
make riscv_vm     # Basic VM only
make vm_with_ivt  # VM with interrupt system
```

This produces two executables:
- `riscv_vm` - Basic VM (original functionality)
- `vm_with_ivt` - VM with full interrupt support



#### Basic Usage

```bash
./vm_with_ivt program.bin
```

#### With Options

```bash
# Queued dispatch mode
./vm_with_ivt -q program.bin

# Set breakpoint at address
./vm_with_ivt -b 0x1000 program.bin

# Set memory watchpoint
./vm_with_ivt -w 0x100 program.bin

# Combine options
./vm_with_ivt -q -b 0x1000 -w 0x100 program.bin
```

#### External Interrupt (Signal)

While the VM is running, you can trigger an interrupt from another terminal:

```bash
# Get the PID from VM output
kill -USR1 <pid>
```

This will fire the breakpoint interrupt.


### Programming Guide

#### Creating an Interrupt Controller

```c
#include "riscv_interrupt.h"

riscv_vm_t *vm = vm_create(65536, 1, 0);
interrupt_controller_t *ic = interrupt_controller_create(vm);
```

#### Registering Interrupt Handlers

```c
void my_handler(riscv_vm_t *vm, int irq_num, void *user_data) {
    printf("IRQ %d at PC=0x%08x\n", irq_num, vm->pc);
    /* Handle interrupt */
}

/* Register handler for IRQ 5 */
interrupt_register_handler(ic, 5, my_handler, NULL);

/* Register multiple handlers for same interrupt */
interrupt_register_handler(ic, 5, another_handler, some_data);
interrupt_register_handler(ic, 5, yet_another, more_data);
```

#### Firing Interrupts

```c
/* Fire interrupt 5 */
interrupt_fire(ic, 5);

/* All registered handlers for IRQ 5 will execute */
```

#### Enable/Disable Control

```c
/* Disable specific interrupt */
interrupt_disable(ic, 5);

/* Enable it again */
interrupt_enable(ic, 5);

/* Disable all interrupts */
interrupt_disable_global(ic);

/* Re-enable all */
interrupt_enable_global(ic);
```

#### Creating Custom Interrupt Sources

```c
/* Define your source state */
typedef struct {
    int condition;
    riscv_vm_t *vm;
} my_source_t;

/* Check function returns IRQ number or -1 */
int check_my_interrupt(void *user_data) {
    my_source_t *src = (my_source_t *)user_data;
    
    if (src->condition) {
        return 7;  /* IRQ 7 */
    }
    return -1;  /* No interrupt */
}

/* In your main loop */
while (vm->running) {
    vm_step(vm);
    
    int irq = check_my_interrupt(&my_src);
    if (irq >= 0) {
        interrupt_fire(ic, irq);
    }
}
```


### Example Patterns

#### 1. Timer-based Interrupt (like periodic timer)

```c
typedef struct {
    unsigned long period;
    unsigned long counter;
} timer_t;

int check_timer(void *data) {
    timer_t *t = (timer_t *)data;
    t->counter++;
    if (t->counter >= t->period) {
        t->counter = 0;
        return 0;  /* Timer IRQ */
    }
    return -1;
}

void timer_handler(riscv_vm_t *vm, int irq, void *data) {
    printf("Timer tick at instruction %lu\n", vm->instruction_count);
}

/* Setup */
timer_t timer = {1000, 0};
interrupt_register_handler(ic, 0, timer_handler, NULL);

/* In loop */
int irq = check_timer(&timer);
if (irq >= 0) interrupt_fire(ic, irq);
```

#### 2. Memory Watchpoint

```c
typedef struct {
    uint32_t addr;
    uint32_t last_value;
    int initialized;
    riscv_vm_t *vm;
} watchpoint_t;

int check_watchpoint(void *data) {
    watchpoint_t *wp = (watchpoint_t *)data;
    uint32_t current = read_mem(wp->vm, wp->addr, 4, 0);
    
    if (!wp->initialized) {
        wp->last_value = current;
        wp->initialized = 1;
        return -1;
    }
    
    if (current != wp->last_value) {
        wp->last_value = current;
        return 2;  /* Watchpoint IRQ */
    }
    return -1;
}

void watchpoint_handler(riscv_vm_t *vm, int irq, void *data) {
    watchpoint_t *wp = (watchpoint_t *)data;
    printf("Memory 0x%08x changed to 0x%08x\n", 
           wp->addr, wp->last_value);
}
```

#### 3. Context-Saving Interrupt Handler

```c
void isr_entry(riscv_vm_t *vm, int irq, void *data) {
    /* Save context to stack */
    vm->regs[2] -= 4;  /* sp */
    write_mem(vm, vm->regs[2], vm->pc, 4);  /* Save PC */
    
    /* Save registers */
    vm->regs[2] -= 4;
    write_mem(vm, vm->regs[2], vm->regs[10], 4);  /* a0 */
    
    /* Jump to ISR code */
    vm->pc = 0x1000;  /* ISR address in program */
}
```

#### 4. Multiple Handlers (Fan-out Pattern)

```c
void log_handler(riscv_vm_t *vm, int irq, void *data) {
    printf("[LOG] IRQ %d\n", irq);
}

void stats_handler(riscv_vm_t *vm, int irq, void *data) {
    /* Update statistics */
}

void action_handler(riscv_vm_t *vm, int irq, void *data) {
    /* Perform action */
}

/* All three will execute when IRQ 5 fires */
interrupt_register_handler(ic, 5, log_handler, NULL);
interrupt_register_handler(ic, 5, stats_handler, NULL);
interrupt_register_handler(ic, 5, action_handler, NULL);
```


### Architecture Details

#### IVT Structure

```
Interrupt Vector Table
┌---------------------------------┐
│ IRQ 0: [handler1, handler2, ..] │  <-- Timer
│ IRQ 1: [handler1, handler2, ..] │  <-- Instruction count
│ IRQ 2: [handler1, handler2, ..] │  <-- Watchpoint
│ IRQ 3: [handler1, handler2, ..] │  <-- Breakpoint
│  ..                             │
│ IRQ 31: [..]                    │
└---------------------------------┘
```

#### Immediate Dispatch Flow

```
Interrupt Source -> Check Function -> interrupt_fire()
                                          v
                                    IVT Lookup
                                          v
                                    For each handler:
                                      - Check enabled
                                      - Call handler(vm, irq, data)
```

#### Queued Dispatch Flow

```
Interrupt Source -> Check Function --> interrupt_fire()
                                           v
                                      Add to Queue
                                           v
                                        (Later)
                                           v
                                 interrupt_process_queue()
                                           v
                                    Dispatch from queue
```

### Comparison to Signal Handlers

| Feature | sig.c | pthread.c | queue.c | This VM |
|---------|-------|-----------|---------|---------|
| Multiple handlers | + | + | - | + |
| Immediate dispatch | + | - | - | + |
| Threaded dispatch | - | + | - | - |
| Queued dispatch | - | - | + | + |
| Priority system | - | - | - | - |
| Enable/disable | - | - | - | + |
| Statistics | - | - | - | + |

### Advanced Use Cases

#### Simulating Hardware Interrupts

```c
/* Timer chip simulation */
typedef struct {
    uint32_t counter;
    uint32_t compare;
    int enabled;
} timer_chip_t;

int check_timer_chip(void *data) {
    timer_chip_t *chip = data;
    if (!chip->enabled) return -1;
    
    chip->counter++;
    if (chip->counter >= chip->compare) {
        chip->counter = 0;
        return IRQ_TIMER;
    }
    return -1;
}

/* Memory-mapped control */
/* Write to 0xFFFF0000 to set compare value */
/* Write to 0xFFFF0004 to enable/disable */
```

#### Debugger Integration

```c
/* Set breakpoints */
void set_breakpoint(uint32_t addr) {
    breakpoint_list[num_breakpoints++] = addr;
}

int check_breakpoints(void *data) {
    riscv_vm_t *vm = data;
    for (int i = 0; i < num_breakpoints; i++) {
        if (vm->pc == breakpoint_list[i]) {
            return IRQ_BREAKPOINT;
        }
    }
    return -1;
}

void breakpoint_handler(riscv_vm_t *vm, int irq, void *data) {
    printf("Breakpoint hit at 0x%08x\n", vm->pc);
    print_regs(vm);
    vm->running = 0;  /* Stop execution */
}
```

#### Performance Profiling

```c
typedef struct {
    unsigned long samples[65536];  /* PC histogram */
} profiler_t;

void profile_handler(riscv_vm_t *vm, int irq, void *data) {
    profiler_t *prof = data;
    if (vm->pc < 65536) {
        prof->samples[vm->pc]++;
    }
}

/* Sample every 1000 instructions */
timer_t sample_timer = {1000, 0};
interrupt_register_handler(ic, IRQ_TIMER, profile_handler, &profiler);
```

### Statistics

The interrupt controller tracks:
- Total interrupts fired per IRQ
- Interrupts queued (in queued mode)
- Interrupts dropped (queue full)
- Handler counts per interrupt

View with:
```c
interrupt_print_stats(ic);
```

### Limitations

- Maximum 32 interrupt types (configurable in header)
- Maximum 10 handlers per interrupt (configurable)
- Queue size of 16 (configurable)
- No interrupt priority system (handlers execute in registration order)
- No nested interrupt support

### Future Enhancements / Projects

Possible additions:
- Priority-based scheduling
- Nested interrupt support
- Per-handler priority
- Interrupt masking at handler level
- Software interrupts (inter-handler messaging)
- Atomic operations for multi-threaded scenarios

