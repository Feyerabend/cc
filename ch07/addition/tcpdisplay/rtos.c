#include "rtos.h"
#include "pico/stdlib.h"
#include "hardware/sync.h"
#include <string.h>

/*
 * RTOS Implementation - RP2350 / Cortex-M33
 *
 * NOTE: Tasks must NOT use floating-point. The RP2350 FPU is enabled by
 * default; saving S16-S31 / FPSCR is not implemented here.
 */

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
    /* Start at the top of the stack array (highest address) */
    uint32_t *sp = &tcb->stack[TASK_STACK_SIZE - 1];

    /* Hardware exception frame - saved by Cortex-M33 on exception entry */
    *sp-- = 0x01000000u;          /* xPSR    Thumb bit set             */
    *sp-- = (uint32_t)function;   /* PC      task entry point          */
    *sp-- = 0xFFFFFFFDu;          /* LR      EXC_RETURN: thread/PSP    */
    *sp-- = 0x12121212u;          /* R12                               */
    *sp-- = 0x03030303u;          /* R3                                */
    *sp-- = 0x02020202u;          /* R2                                */
    *sp-- = 0x01010101u;          /* R1                                */
    *sp-- = (uint32_t)param;      /* R0      first argument to task    */

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
 *  1. Mark the outgoing task READY (unless it is BLOCKED/SUSPENDED).
 *  2. Scan all tasks for the highest-priority READY one.
 *  3. Mark the winner RUNNING.
 */
uint8_t select_next_task(void)
{
    /* Step 1   demote current task from RUNNING -> READY so it can be
     * considered again, unless it blocked itself.  */
    if (tasks[current_task].state == TASK_RUNNING) {
        tasks[current_task].state = TASK_READY;
    }

    /* Step 2   find highest priority among all READY tasks */
    uint8_t best_priority = 0;
    for (uint8_t i = 0; i < num_tasks; i++) {
        if (tasks[i].state == TASK_READY &&
            tasks[i].priority > best_priority) {
            best_priority = tasks[i].priority;
        }
    }

    /* Step 3   round-robin among tasks that share the best priority  */
    uint8_t start = (current_task + 1) % num_tasks;
    for (uint8_t i = 0; i < num_tasks; i++) {
        uint8_t idx = (start + i) % num_tasks;
        if (tasks[idx].state == TASK_READY &&
            tasks[idx].priority == best_priority) {
            tasks[idx].state = TASK_RUNNING;
            return idx;
        }
    }

    /* Fallback: keep current task (handles single-task or all-idle) */
    tasks[current_task].state = TASK_RUNNING;
    return current_task;
}

/* ------------------------------------------------------------------ */
/*  SysTick - 1 ms tick, wakes blocked tasks, pends context switch    */
/* ------------------------------------------------------------------ */
void isr_systick(void)
{
    tick_count++;

    /*
     * Timeline: record a per-task ACTIVE bitmask every 4 ms.
     * Bit N = 1  - task N is READY or RUNNING  (active)
     * Bit N = 0  - task N is BLOCKED/SUSPENDED
     * 4 ms/entry x 280 entries = 1120 ms of scrolling history.
     * Sampling every 4 ms makes the 500 ms LED block and 100 ms
     * counter block visible as clear horizontal patterns.
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
    *(volatile uint32_t *)0xE000ED04u = (1u << 28);
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
 * pendsv_switch() - called from PendSV assembly.
 *
 * Receives the just-saved PSP value, persists it in the current TCB,
 * runs the scheduler to pick the next task, then returns a pointer to
 * the new task's stack_ptr so the assembly can load the new PSP.
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
    }
    first_switch = false;

    current_task = select_next_task();
    return (uint32_t **)&tasks[current_task].stack_ptr;
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
        "BX     R2                 \n"  /* EXC_RETURN → back to task */
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

    /* Set PendSV to lowest priority (full 8-bit field on M33) */
    *(volatile uint32_t *)0xE000ED20u |= 0x00FF0000u;  /* SHPR3 bits 23:16  */

    /* Configure SysTick — 1 ms @ 150 MHz (RP2350 default system clock) */
    *(volatile uint32_t *)0xE000E010u = 0u;             /* CSR   disable    */
    *(volatile uint32_t *)0xE000E014u = 150000u - 1u;   /* RVR   reload     */
    *(volatile uint32_t *)0xE000E018u = 0u;             /* CVR   clear      */
    *(volatile uint32_t *)0xE000E010u = 0x7u;           /* CSR   enable+irq */

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

        /* Pend PendSV — it will do the first "context restore" */
        "LDR    R0, =0xE000ED04             \n"
        "LDR    R1, =0x10000000             \n"
        "STR    R1, [R0]                    \n"

        /* Enable interrupts — PendSV fires immediately */
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
    *(volatile uint32_t *)0xE000ED04u = (1u << 28);
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
