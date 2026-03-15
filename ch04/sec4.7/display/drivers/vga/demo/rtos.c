#include "rtos.h"
#include "pico/stdlib.h"
#include "pico/rand.h"
#include "hardware/sync.h"
#include <string.h>

/*
 * rtos.c - Preemptive RTOS kernel for RP2350 / Cortex-M33
 *
 * NOTE: Tasks must NOT use floating-point. The RP2350 FPU is enabled by
 * default; saving S16-S31 / FPSCR is not implemented here.
 */

/* ------------------------------------------------------------------ */
/*  ARM Cortex-M33 system control register addresses                  */
/* ------------------------------------------------------------------ */
/* Interrupt Control and State Register - bit 28 = PENDSVSET          */
#define SCB_ICSR        (*(volatile uint32_t *)0xE000ED04u)
/* System Handler Priority Register 3 - bits 23:16 = PendSV priority  */
#define SCB_SHPR3       (*(volatile uint32_t *)0xE000ED20u)
/* SysTick Control and Status Register                                */
#define SYST_CSR        (*(volatile uint32_t *)0xE000E010u)
/* SysTick Reload Value Register                                      */
#define SYST_RVR        (*(volatile uint32_t *)0xE000E014u)
/* SysTick Current Value Register                                     */
#define SYST_CVR        (*(volatile uint32_t *)0xE000E018u)

/* SYST_CSR bit fields */
#define SYST_CSR_ENABLE    (1u << 0)   /* counter enable                 */
#define SYST_CSR_TICKINT   (1u << 1)   /* generate SysTick exception     */
#define SYST_CSR_CLKSOURCE (1u << 2)   /* 1 = processor clock            */
#define SYST_CSR_ENABLE_ALL (SYST_CSR_ENABLE | SYST_CSR_TICKINT | SYST_CSR_CLKSOURCE)

/* System clock and desired tick period */
#define SYSTICK_CLOCK_HZ   150000000u  /* RP2350 default: 150 MHz        */
#define SYSTICK_PERIOD_MS  1u
#define SYSTICK_RELOAD     (SYSTICK_CLOCK_HZ / 1000u * SYSTICK_PERIOD_MS - 1u)

/* ------------------------------------------------------------------ */
/*  Global RTOS state (must be non-static so assembly can reference)  */
/* ------------------------------------------------------------------ */
task_control_block_t tasks[MAX_TASKS];
uint8_t              current_task   = 0;
static uint8_t       num_tasks      = 0;
volatile uint32_t    tick_count     = 0;
static bool          scheduler_running = false;

volatile uint8_t     rtos_timeline[RTOS_TIMELINE_LEN];
volatile uint16_t    rtos_timeline_pos = 0;

/* ------------------------------------------------------------------ */
/*  Stack protection globals                                          */
/* ------------------------------------------------------------------ */
/*
 * __stack_chk_guard - GCC's -fstack-protector-strong uses this symbol
 * as the canary value for compiler-generated function-level protection.
 * Initialised from the RP2350 TRNG in rtos_init() so it is different
 * every boot.  Must be global (extern linkage) so the linker finds it.
 */
uintptr_t __stack_chk_guard = 0;

/*
 * session_stack_guard - same random value, used as the per-task bottom-
 * of-stack guard word (written to stack[0] in task_stack_init).
 * Kept as a separate copy (same value, different variable) so the RTOS
 * kernel check path does not go through the GCC guard mechanism itself.
 */
static uint32_t session_stack_guard = 0;

/*
 * rtos_last_fault - written by pendsv_switch() or __stack_chk_fail().
 * Core 1 reads it to render the fault overlay on the display.
 */
volatile rtos_fault_t rtos_last_fault = {false, 0, NULL, 0};

/* ------------------------------------------------------------------ */
/*  Stack frame initialisation                                        */
/* ------------------------------------------------------------------ */
/*
 * Build an initial exception return frame so that PendSV can "restore"
 * a brand-new task as if it had been interrupted before.
 *
 * Cortex-M33 hardware-stacked frame (top of stack after interrupt):
 *   xPSR, PC, LR, R12, R3, R2, R1, R0   (R0 = param, pushed last->lowest addr)
 *
 * Software-stacked (by PendSV save path):
 *   R11, R10, R9, R8, R7, R6, R5, R4    (pushed above hardware frame)
 *
 * Stack grows downward; stack_ptr points to the last-pushed word (R4).
 */
static void task_stack_init(task_control_block_t *tcb,
                            task_function_t       function,
                            void                 *param)
{
    /* Fill the entire stack with a canary pattern so that
     * rtos_stats_get() can scan from the bottom to find the
     * high-watermark.  The frame construction below will
     * overwrite the top 16 words with real values.          */
    for (int i = 0; i < TASK_STACK_SIZE; i++)
        tcb->stack[i] = RTOS_STACK_CANARY;

    /* Place a random guard word at the very bottom of the stack (stack[0]).
     * This is the first word a growing-downward stack would corrupt on
     * overflow.  pendsv_switch() checks this word on every context switch.
     * Must come AFTER the canary fill so it overwrites position 0.         */
    tcb->stack[0] = session_stack_guard;

    /* Start at the top of the stack array (highest address) */
    uint32_t *sp = &tcb->stack[TASK_STACK_SIZE - 1];

    /* Hardware exception frame - saved by Cortex-M33 on exception entry */
    *sp-- = 0x01000000u;          /* xPSR  - Thumb bit set             */
    *sp-- = (uint32_t)function;   /* PC    - task entry point          */
    *sp-- = 0xFFFFFFFDu;          /* LR    - EXC_RETURN: thread/PSP    */
    *sp-- = 0x12121212u;          /* R12                               */
    *sp-- = 0x03030303u;          /* R3                                */
    *sp-- = 0x02020202u;          /* R2                                */
    *sp-- = 0x01010101u;          /* R1                                */
    *sp-- = (uint32_t)param;      /* R0    - first argument to task    */

    /* Software-saved frame - PendSV saves/restores these manually */
    *sp-- = 0x11111111u;          /* R11 */
    *sp-- = 0x10101010u;          /* R10 */
    *sp-- = 0x09090909u;          /* R9  */
    *sp-- = 0x08080808u;          /* R8  */
    *sp-- = 0x07070707u;          /* R7  */
    *sp-- = 0x06060606u;          /* R6  */
    *sp-- = 0x05050505u;          /* R5  */
    *sp-- = 0x04040404u;          /* R4  */

    /* sp now points to the last-written word (R4's slot).          */
    /* After the decrement above sp is one below R4, so add 1 back. */
    tcb->stack_ptr = sp + 1;
}

/* ------------------------------------------------------------------ */
/*  RTOS init                                                         */
/* ------------------------------------------------------------------ */
void rtos_init(void)
{
    memset(tasks, 0, sizeof(tasks));
    num_tasks         = 0;
    current_task      = 0;
    tick_count        = 0;
    scheduler_running = false;

    /*
     * Draw a random session canary from the RP2350 hardware TRNG.
     * This value is used in two places:
     *   1. __stack_chk_guard - GCC's -fstack-protector-strong checks this
     *      at function exit; an attacker cannot predict the value to bypass.
     *   2. session_stack_guard - written to stack[0] of every task and
     *      verified in pendsv_switch() on every context switch.
     *
     * The TRNG ring oscillators need a moment to stabilise.  get_rand_32()
     * (pico SDK) handles this automatically and includes a FIPS health test.
     * We reject the pathological values 0 and RTOS_STACK_CANARY so the
     * guard is always distinguishable from an uninitialised or canary slot.
     */
    uint32_t rng = get_rand_32();
    if (rng == 0u || rng == RTOS_STACK_CANARY) {
        rng ^= 0xA5A5A5A5u;
    }
    session_stack_guard = rng;
    __stack_chk_guard   = (uintptr_t)rng;
}

/* ------------------------------------------------------------------ */
/*  Task creation                                                     */
/* ------------------------------------------------------------------ */
void task_create(task_function_t function,
                 const char     *name,
                 task_priority_t priority,
                 void           *param)
{
    if (num_tasks >= MAX_TASKS) return;

    uint32_t saved = save_and_disable_interrupts();

    task_control_block_t *tcb = &tasks[num_tasks];
    memset(tcb, 0, sizeof(*tcb));

    tcb->state    = TASK_READY;
    tcb->priority = priority;
    tcb->name     = name;

    task_stack_init(tcb, function, param);

    num_tasks++;

    restore_interrupts(saved);
}

/* ------------------------------------------------------------------ */
/*  Scheduler - priority-based with round-robin among equals          */
/* ------------------------------------------------------------------ */
/*
 * select_next_task() is an internal kernel function called only from
 * pendsv_switch().  It must not appear in the public API (rtos.h).
 *
 * Algorithm:
 *  1. Demote the outgoing task RUNNING -> READY (unless BLOCKED/SUSPENDED).
 *  2. Scan all tasks for the highest priority among READY tasks.
 *  3. Round-robin among tasks sharing that best priority.
 *  4. Mark the winner RUNNING and return its index.
 */
static uint8_t select_next_task(void)
{
    /* Step 1 - demote current task from RUNNING -> READY so it can be
     * considered again, unless it blocked itself.  */
    if (tasks[current_task].state == TASK_RUNNING) {
        tasks[current_task].state = TASK_READY;
    }

    /* Step 2 - find highest priority among all READY tasks */
    uint8_t best_priority = 0;
    for (uint8_t i = 0; i < num_tasks; i++) {
        if (tasks[i].state == TASK_READY &&
            tasks[i].priority > best_priority) {
            best_priority = tasks[i].priority;
        }
    }

    /* Step 3 - round-robin among tasks that share the best priority  */
    uint8_t start = (current_task + 1) % num_tasks;
    for (uint8_t i = 0; i < num_tasks; i++) {
        uint8_t idx = (start + i) % num_tasks;
        if (tasks[idx].state == TASK_READY &&
            tasks[idx].priority == best_priority) {
            tasks[idx].switch_count++;
            tasks[idx].state = TASK_RUNNING;
            return idx;
        }
    }

    /* Fallback: keep current task (handles single-task or all-idle) */
    tasks[current_task].switch_count++;
    tasks[current_task].state = TASK_RUNNING;
    return current_task;
}

/* ------------------------------------------------------------------ */
/*  SysTick - 1 ms tick, wakes blocked tasks, pends context switch    */
/* ------------------------------------------------------------------ */
void isr_systick(void)
{
    tick_count++;
    tasks[current_task].run_ticks++;   /* account CPU time to the running task */

    /*
     * Timeline: record the index of the running task every 4 ms.
     * Each entry is the current_task index (0, 1, 2, ...) at that moment.
     * The display uses this to colour-code which task owned the CPU.
     *
     * Sampling rate: 4 ms/entry x 280 entries = 1120 ms of scrolling history.
     * This rate makes the 200 ms LED block and 80/20 ms Counter rhythm
     * visible as clear horizontal patterns at 4 ms/pixel.
     */
    static uint8_t tl_div = 0;
    if (++tl_div >= 4) {
        tl_div = 0;
        rtos_timeline[rtos_timeline_pos % RTOS_TIMELINE_LEN] = current_task;
        rtos_timeline_pos++;
    }

    if (!scheduler_running) return;

    /* Wake any task whose delay has expired */
    for (uint8_t i = 0; i < num_tasks; i++) {
        if (tasks[i].state   == TASK_BLOCKED &&
            tasks[i].wake_time != 0          &&
            tick_count >= tasks[i].wake_time) {
            tasks[i].state     = TASK_READY;
            tasks[i].wake_time = 0;
        }
    }

    /* Request a context switch via PendSV (lowest-priority handler) */
    SCB_ICSR = (1u << 28);  /* PENDSVSET */
}

/* ------------------------------------------------------------------ */
/*  PendSV - context switch (Cortex-M33 / Thumb-2)                    */
/* ------------------------------------------------------------------ */
/*
 * On Cortex-M33, STMDB/LDMIA support the full R0-R12 register list,
 * so we can save R4-R11 in a single instruction - no MSP shuttle.
 *
 * Hardware automatically saves {R0-R3, R12, LR, PC, xPSR} on PSP
 * when the exception fires.  We save/restore the remaining callee-saved
 * registers R4-R11 manually.
 *
 * Software stack frame layout (grows downward, low addr at bottom):
 *
 *   [higher addr]  ... hardware frame (xPSR, PC, LR, R12, R3-R0) ...
 *                  R11
 *                  R10
 *                  R9
 *                  R8
 *                  R7
 *                  R6
 *                  R5
 *   stack_ptr ->   R4    <- TCB.stack_ptr points here after save
 *
 * STMDB R0!, {R4-R11}  decrements R0 by 32 then stores R4 at lowest
 * address - exactly matching task_stack_init's layout.
 */

/*
 * pendsv_switch() - C bridge called by name from the PendSV naked handler.
 *
 * Cannot be static: the assembler resolves "BL pendsv_switch" at link time
 * and requires external linkage.  It must not appear in the public header
 * (rtos.h) because it is an implementation detail; only isr_pendsv calls it.
 *
 * Receives the just-saved PSP value, persists it in the outgoing TCB,
 * runs the scheduler to select the next task, and returns a pointer to
 * that task's stack_ptr field so the assembly restore path can load the new PSP.
 */
uint32_t **pendsv_switch(uint32_t *saved_sp)
{
    /* Skip save on the very first call: rtos_start sets PSP to the
     * pre-built task frame and immediately pends PendSV. The CPU
     * auto-pushes a spurious hw frame before the save runs, which
     * would corrupt tasks[0].stack_ptr. Skip it so the pre-built
     * frame stays intact and task 0 starts correctly. */
    static bool first_switch = true;
    if (!first_switch) {
        tasks[current_task].stack_ptr = saved_sp;

        /*
         * Stack guard check - verify the outgoing task's bottom-of-stack
         * guard word is intact.  A runaway stack pointer overwrites this
         * word before it can corrupt any other TCB.  Only the first fault
         * is recorded (rtos_last_fault.active prevents overwrite).
         *
         * session_stack_guard == 0 means rtos_init() has not yet been
         * called; skip the check to avoid a false alarm on startup.
         */
        if (session_stack_guard != 0u &&
            tasks[current_task].stack[0] != session_stack_guard &&
            !rtos_last_fault.active) {
            rtos_last_fault.active     = true;
            rtos_last_fault.task_index = current_task;
            rtos_last_fault.task_name  = tasks[current_task].name;
            rtos_last_fault.tick       = tick_count;
            tasks[current_task].state  = TASK_SUSPENDED;
        }
    }
    first_switch = false;

    current_task = select_next_task();
    return (uint32_t **)&tasks[current_task].stack_ptr;
}

/*
 * __stack_chk_fail - called by GCC's -fstack-protector-strong when it
 * detects that a function's stack canary has been overwritten before the
 * function returns.  This means a local buffer overflow occurred inside
 * the currently running task.
 *
 * Strategy: record the fault (task + tick), mark the task SUSPENDED so
 * the scheduler will never return to it, then trigger a PendSV context
 * switch.  The function never returns (noreturn) - we spin in WFI until
 * PendSV fires and switches to a healthy task.
 *
 * Note: we cannot call task_delay() here because the stack is corrupt.
 * Directly writing PENDSVSET and spinning in WFI is the safe path.
 */
__attribute__((noreturn)) void __stack_chk_fail(void)
{
    if (!rtos_last_fault.active) {
        rtos_last_fault.active     = true;
        rtos_last_fault.task_index = current_task;
        rtos_last_fault.task_name  = tasks[current_task].name;
        rtos_last_fault.tick       = tick_count;
    }
    tasks[current_task].state = TASK_SUSPENDED;
    SCB_ICSR = (1u << 28);          /* PENDSVSET - switch away now */
    while (1) __asm volatile("wfi");
}

/*
 * PendSV_Handler - Cortex-M33 context switch.
 *
 * Thumb-2 instructions used (all valid on M33):
 *   MRS/MSR PSP          - read/write process stack pointer
 *   STMDB Rn!, {R4-R11}  - save 8 regs, decrement-before, writeback
 *   LDMIA Rn!, {R4-R11}  - load 8 regs, increment-after, writeback
 *   PUSH/POP {LR}        - uses MSP (handler mode)
 *   BL, BX, CPSID/CPSIE  - standard
 */
__attribute__((naked)) void isr_pendsv(void)
{
    __asm volatile (
        "CPSID  I                  \n"  /* disable interrupts */

        /* -- SAVE outgoing task context -- */
        "MRS    R0, PSP            \n"  /* R0 = process stack pointer */
        "STMDB  R0!, {R4-R11}      \n"  /* save R4-R11, R0 -= 32 */

        /* -- SWITCH: save old SP, select next task, get new SP ptr -- */
        "PUSH   {LR}               \n"  /* preserve EXC_RETURN */
        "BL     pendsv_switch      \n"  /* R0=saved PSP in, R0=&new_sp out */
        "POP    {R2}               \n"  /* R2 = EXC_RETURN */

        /* -- RESTORE incoming task context -- */
        "LDR    R0, [R0]           \n"  /* R0 = new task's stack_ptr */
        "LDMIA  R0!, {R4-R11}      \n"  /* restore R4-R11, R0 += 32 */

        /* Update PSP; CPU auto-restores hw frame on exception return */
        "MSR    PSP, R0            \n"

        "CPSIE  I                  \n"  /* re-enable interrupts */
        "BX     R2                 \n"  /* EXC_RETURN -> back to task */
    );
}

/* ------------------------------------------------------------------ */
/*  Start the scheduler                                               */
/* ------------------------------------------------------------------ */
/*
 *  1. Set PSP to tasks[0].stack_ptr so the CPU has a valid process stack.
 *  2. Switch to using PSP in Thread mode (CONTROL bit 1).
 *  3. Configure SysTick.
 *  4. Mark task 0 RUNNING, trigger PendSV - let the normal switch path
 *     restore the first task's register frame and branch to its PC.
 */
void rtos_start(void)
{
    if (num_tasks == 0) return;

    /* Set PendSV to lowest priority - full 8-bit field on Cortex-M33
     * (Cortex-M0+ only has 2 bits; always use the full value on M33)   */
    SCB_SHPR3 |= 0x00FF0000u;  /* SHPR3 bits 23:16 = PendSV priority    */

    /* Configure SysTick for SYSTICK_PERIOD_MS (1 ms) tick              */
    SYST_CSR = 0u;             /* disable while reconfiguring           */
    SYST_RVR = SYSTICK_RELOAD; /* reload value = clock/1000 - 1         */
    SYST_CVR = 0u;             /* clear current value (resets on write) */
    SYST_CSR = SYST_CSR_ENABLE_ALL; /* enable, IRQ, processor clock     */

    scheduler_running = true;

    /* Mark first task as running */
    tasks[0].state = TASK_RUNNING;
    current_task   = 0;

    /*
     * Set PSP to tasks[0].stack_ptr and switch Thread mode to use PSP.
     * Then trigger PendSV - it will restore the full register frame of
     * task 0 and branch to its entry function via EXC_RETURN.
     *
     * We set LR = 0xFFFFFFFD (EXC_RETURN: Thread mode, PSP, no FPU)
     * before triggering PendSV so that BX LR in PendSV exits correctly.
     *
     * NOTE: After "MSR CONTROL, R1" + ISB we are using PSP.  The MSP
     * still holds the original main() stack, which is fine - the CPU
     * only uses MSP while in handler mode after this point.
     */
    __asm volatile (
        /* Load tasks[0].stack_ptr into PSP */
        "LDR    R0, =tasks                  \n"
        "LDR    R0, [R0, #0]                \n"  /* stack_ptr is at offset 0 */
        "MSR    PSP, R0                     \n"

        /* Switch to PSP in Thread mode */
        "MOVS   R1, #2                      \n"
        "MSR    CONTROL, R1                 \n"
        "ISB                                \n"

        /* Pend PendSV - it will do the first "context restore" */
        "LDR    R0, =0xE000ED04             \n"
        "LDR    R1, =0x10000000             \n"
        "STR    R1, [R0]                    \n"

        /* Enable interrupts - PendSV fires immediately */
        "CPSIE  I                           \n"

        /* Spin; PendSV will branch away to task 0's entry function */
        "1: WFI                             \n"
        "B      1b                          \n"
        : : : "r0", "r1"
    );
}

/* ------------------------------------------------------------------ */
/*  Yield / Delay                                                     */
/* ------------------------------------------------------------------ */
void task_yield(void)
{
    SCB_ICSR = (1u << 28);  /* PENDSVSET - request context switch */
}

void task_delay(uint32_t ms)
{
    uint32_t saved = save_and_disable_interrupts();

    tasks[current_task].wake_time = tick_count + ms;
    tasks[current_task].state     = TASK_BLOCKED;

    restore_interrupts(saved);

    task_yield();
}

uint32_t rtos_get_tick_count(void)
{
    return tick_count;
}

/* ------------------------------------------------------------------ */
/*  Mutex                                                             */
/* ------------------------------------------------------------------ */
void rtos_mutex_init(rtos_mutex_t *mutex)
{
    mutex->locked = false;
    mutex->owner  = NULL;
}

void rtos_mutex_lock(rtos_mutex_t *mutex)
{
    while (1) {
        uint32_t saved = save_and_disable_interrupts();
        if (!mutex->locked) {
            mutex->locked = true;
            mutex->owner  = &tasks[current_task];
            restore_interrupts(saved);
            return;
        }
        restore_interrupts(saved);
        task_delay(1);  /* block properly so lower-priority tasks can run */
    }
}

void rtos_mutex_unlock(rtos_mutex_t *mutex)
{
    uint32_t saved = save_and_disable_interrupts();
    if (mutex->owner == &tasks[current_task]) {
        mutex->locked = false;
        mutex->owner  = NULL;
    }
    restore_interrupts(saved);
}

/* ------------------------------------------------------------------ */
/*  Semaphore                                                         */
/* ------------------------------------------------------------------ */
void rtos_semaphore_init(rtos_semaphore_t *sem, uint32_t initial, uint32_t max)
{
    sem->count     = initial;
    sem->max_count = max;
}

void rtos_semaphore_wait(rtos_semaphore_t *sem)
{
    while (1) {
        uint32_t saved = save_and_disable_interrupts();
        if (sem->count > 0) {
            sem->count--;
            restore_interrupts(saved);
            return;
        }
        restore_interrupts(saved);
        task_delay(1);  /* block properly so lower-priority tasks can run */
    }
}

void rtos_semaphore_signal(rtos_semaphore_t *sem)
{
    uint32_t saved = save_and_disable_interrupts();
    if (sem->count < sem->max_count) {
        sem->count++;
    }
    restore_interrupts(saved);
}

/* ------------------------------------------------------------------ */
/*  Statistics snapshot                                               */
/* ------------------------------------------------------------------ */
void rtos_stats_get(rtos_stats_t *out)
{
    /* Snapshot uptime atomically so all per-task percentages use the
     * same denominator - avoids CPU% summing to > 100 on wrap.      */
    uint32_t uptime = tick_count;
    out->uptime_ms = uptime;
    out->num_tasks = num_tasks;

    for (uint8_t i = 0; i < num_tasks; i++) {
        rtos_task_stats_t            *s   = &out->tasks[i];
        const task_control_block_t   *tcb = &tasks[i];

        s->name             = tcb->name;
        s->state            = tcb->state;
        s->priority         = tcb->priority;
        s->run_ticks        = tcb->run_ticks;
        s->switch_count     = tcb->switch_count;
        s->stack_size_words = TASK_STACK_SIZE;

        /* Lifetime CPU%: avoid divide-by-zero on the very first tick */
        s->cpu_percent = uptime
            ? (uint8_t)((uint64_t)tcb->run_ticks * 100u / uptime)
            : 0u;

        /* Stack high-watermark: count consecutive canary words from
         * stack[1] upward (stack[0] is the random security guard word,
         * not a canary, so it must be excluded from the scan).        */
        uint16_t free_words = 0;
        while ((free_words + 1u) < TASK_STACK_SIZE &&
               tcb->stack[1u + free_words] == RTOS_STACK_CANARY) {
            free_words++;
        }
        /* Peak = total usable words minus untouched canary words.
         * Usable = TASK_STACK_SIZE - 1 (guard word is always reserved). */
        s->stack_peak_words = (TASK_STACK_SIZE - 1u) - free_words;
    }
}
