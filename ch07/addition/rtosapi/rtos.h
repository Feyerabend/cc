#ifndef RTOS_H
#define RTOS_H

#include <stdint.h>
#include <stdbool.h>

/*
 * rtos.h - Public API for the Pico 2W minimal preemptive RTOS
 *
 * Target: RP2350 (Raspberry Pi Pico 2W), dual Cortex-M33 @ 150 MHz
 *
 * RTOS concepts implemented:
 *   - Preemptive scheduling: SysTick fires every 1 ms; PendSV switches context
 *   - Priority-based dispatch: highest-priority READY task always runs next
 *   - Round-robin tie-breaking: equal-priority tasks share CPU in rotation
 *   - Task blocking: task_delay() suspends a task until a future tick
 *   - Mutex / Semaphore: basic synchronisation primitives
 *
 * Constraints (educational scope):
 *   - Up to MAX_TASKS tasks with statically allocated stacks
 *   - Tasks must NOT use floating-point (FPU context is not saved)
 *   - No priority inheritance (classic priority inversion is possible)
 *   - All tasks run on Core 0; Core 1 is reserved for the display loop
 */

#define MAX_TASKS       8
#define TASK_STACK_SIZE 256   // 32-bit words per task stack
#define RTOS_STACK_CANARY 0xDEADBEEFu

typedef enum {
    TASK_READY,
    TASK_RUNNING,
    TASK_BLOCKED,
    TASK_SUSPENDED
} task_state_t;

typedef uint8_t task_priority_t;
typedef void (*task_function_t)(void *param);

/*
 * Task Control Block (TCB)
 *
 * ASSEMBLY CONSTRAINT: stack_ptr MUST remain the very first field (offset 0).
 * The PendSV handler reads it with a plain LDR from the TCB base address.
 * Do NOT reorder fields without updating the inline assembly in rtos.c.
 *
 * Memory layout:
 *   offset  0 : stack_ptr  (4 bytes - pointer into stack[])
 *   offset  4 : stack[]    (TASK_STACK_SIZE × 4 bytes = 1024 bytes)
 *   offset 1028: state, priority, pad, wake_time, name
 */
typedef struct {
    uint32_t        *stack_ptr;              /* [offset 0] active stack pointer - MUST be first */
    uint32_t         stack[TASK_STACK_SIZE]; /* [offset 4] per-task stack storage               */
    task_state_t     state;
    task_priority_t  priority;
    uint8_t          _pad[2];               /* explicit padding for 4-byte alignment            */
    uint32_t         wake_time;             /* tick_count value at which to unblock             */
    const char      *name;                  /* human-readable label (display / debugging)       */
    uint32_t  run_ticks;    /* ticks (ms) spent in RUNNING state - written by isr_systick */
    uint32_t  switch_count; /* times selected by select_next_task */
} task_control_block_t;

/* Mutex */
typedef struct {
    volatile bool        locked;
    task_control_block_t *owner;
} rtos_mutex_t;

/* Semaphore */
typedef struct {
    volatile uint32_t count;
    uint32_t          max_count;
} rtos_semaphore_t;

/* Core RTOS API */
void rtos_init(void);
void rtos_start(void);

void task_create(task_function_t function,
                 const char     *name,
                 task_priority_t priority,
                 void           *param);

void task_yield(void);
void task_delay(uint32_t ms);

void rtos_mutex_init(rtos_mutex_t *mutex);
void rtos_mutex_lock(rtos_mutex_t *mutex);
void rtos_mutex_unlock(rtos_mutex_t *mutex);

void rtos_semaphore_init(rtos_semaphore_t *sem, uint32_t initial, uint32_t max);
void rtos_semaphore_wait(rtos_semaphore_t *sem);
void rtos_semaphore_signal(rtos_semaphore_t *sem);

uint32_t rtos_get_tick_count(void);

/* ------------------------------------------------------------------ */
/*  Scheduler timeline - sampled every 4 ms by isr_systick.           */
/*  Each entry is the index of current_task at that moment (0/1/2).   */
/*  280 entries x 4 ms = 1120 ms of scrolling history.                */
/*  Core 1 reads these for visualisation; core 0 writes them.         */
/* ------------------------------------------------------------------ */
#define RTOS_TIMELINE_LEN  280

extern task_control_block_t  tasks[MAX_TASKS];
extern uint8_t               current_task;
extern volatile uint32_t     tick_count;
extern volatile uint8_t      rtos_timeline[RTOS_TIMELINE_LEN];
extern volatile uint16_t     rtos_timeline_pos;

/* ------------------------------------------------------------------ */
/*  Task statistics - returned by rtos_stats_get()                    */
/* ------------------------------------------------------------------ */

/*
 * Per-task snapshot.  cpu_percent is run_ticks / uptime_ms x 100.
 * stack_peak_words is computed by scanning the stack for the first
 * word that is not RTOS_STACK_CANARY (filled at task creation).
 */
typedef struct {
    const char      *name;
    task_state_t     state;
    task_priority_t  priority;
    uint32_t         run_ticks;         /* ms spent running since boot         */
    uint32_t         switch_count;      /* scheduler selections since boot     */
    uint8_t          cpu_percent;       /* lifetime CPU%                       */
    uint16_t         stack_peak_words;  /* max stack depth seen (32-bit words) */
    uint16_t         stack_size_words;  /* total stack allocation              */
} rtos_task_stats_t;

typedef struct {
    uint32_t          uptime_ms;
    uint8_t           num_tasks;
    rtos_task_stats_t tasks[MAX_TASKS];
} rtos_stats_t;

/*
 * Snapshot all task statistics into *out.
 * Safe to call from any task or Core 1 (takes a consistent copy).
 */
void rtos_stats_get(rtos_stats_t *out);

#endif /* RTOS_H */
