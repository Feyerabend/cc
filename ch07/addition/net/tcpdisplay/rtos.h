#ifndef RTOS_H
#define RTOS_H

#include <stdint.h>
#include <stdbool.h>

/*
 * Minimal Real-Time Operating System for RP2350 (Raspberry Pi Pico 2W)
 *
 * Demonstrates:
 * - Context Switching: Saving/restoring CPU state between tasks
 * - Re-entrancy: Safe concurrent access via mutexes
 * - Event-Driven: SysTick interrupt triggers preemptive scheduling
 * - State Management: Task control blocks maintain execution state
 */

#define MAX_TASKS       8
#define TASK_STACK_SIZE 1024  // 32-bit words per task stack (4 KB — needed for lwIP)

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
 * IMPORTANT: stack_ptr MUST be the very first field.
 * The PendSV assembly loads the TCB address and uses offset 0 for stack_ptr.
 * Do not reorder fields without updating the assembly offsets.
 */
typedef struct {
    uint32_t        *stack_ptr;             // offset 0  — must be first!
    uint32_t         stack[TASK_STACK_SIZE]; // offset 4
    task_state_t     state;                 // offset 4 + 1024 = 1028
    task_priority_t  priority;
    uint8_t          _pad[2];               // keep 4-byte alignment
    uint32_t         wake_time;
    const char      *name;
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

/* Called from pendsv_switch() */
uint8_t select_next_task(void);

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

#endif /* RTOS_H */
