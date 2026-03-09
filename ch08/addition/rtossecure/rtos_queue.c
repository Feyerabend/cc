#include "rtos_queue.h"
#include "rtos.h"
#include "hardware/sync.h"
#include <string.h>

/*
 * rtos_queue.c - Message queue implementation.
 *
 * Concurrency model:
 *   All mutations of the queue state (head, tail, count) are wrapped
 *   in save_and_disable_interrupts / restore_interrupts critical sections,
 *   matching the same pattern used by rtos_mutex and rtos_semaphore.
 *
 *   Blocking is achieved by calling task_delay(1) and retrying - the same
 *   cooperative-yield pattern used throughout this RTOS.  This means:
 *   - Callers must be in task context (not ISR).
 *   - A blocked sender/receiver relinquishes the CPU to other tasks.
 */

void rtos_queue_init(rtos_queue_t *q, void *storage,
                     uint16_t item_size, uint16_t capacity)
{
    q->buf       = storage;
    q->item_size = item_size;
    q->capacity  = capacity;
    q->head      = 0;
    q->tail      = 0;
    q->count     = 0;
}

bool rtos_queue_send(rtos_queue_t *q, const void *item, uint32_t timeout_ms)
{
    /* Pre-compute deadline (only meaningful for finite timeouts) */
    uint32_t deadline = (timeout_ms != RTOS_WAIT_FOREVER)
                        ? tick_count + timeout_ms : 0u;

    while (1) {
        uint32_t saved = save_and_disable_interrupts();

        if (q->count < q->capacity) {
            /* Slot available: copy item into the tail slot */
            uint8_t *slot = (uint8_t *)q->buf + (q->tail * q->item_size);
            memcpy(slot, item, q->item_size);
            q->tail = (uint16_t)((q->tail + 1u) % q->capacity);
            q->count++;
            restore_interrupts(saved);
            return true;
        }

        restore_interrupts(saved);

        /* Queue full: check timeout before blocking */
        if (timeout_ms == RTOS_NO_WAIT) return false;
        if (timeout_ms != RTOS_WAIT_FOREVER &&
            (int32_t)(deadline - tick_count) <= 0) return false;

        task_delay(1);   /* yield; a consumer may free a slot during this delay */
    }
}

bool rtos_queue_receive(rtos_queue_t *q, void *item, uint32_t timeout_ms)
{
    uint32_t deadline = (timeout_ms != RTOS_WAIT_FOREVER)
                        ? tick_count + timeout_ms : 0u;

    while (1) {
        uint32_t saved = save_and_disable_interrupts();

        if (q->count > 0) {
            /* Item available: copy out of head slot */
            const uint8_t *slot = (const uint8_t *)q->buf + (q->head * q->item_size);
            memcpy(item, slot, q->item_size);
            q->head = (uint16_t)((q->head + 1u) % q->capacity);
            q->count--;
            restore_interrupts(saved);
            return true;
        }

        restore_interrupts(saved);

        if (timeout_ms == RTOS_NO_WAIT) return false;
        if (timeout_ms != RTOS_WAIT_FOREVER &&
            (int32_t)(deadline - tick_count) <= 0) return false;

        task_delay(1);   /* yield; a producer may add an item during this delay */
    }
}

bool rtos_queue_peek(const rtos_queue_t *q, void *item)
{
    uint32_t saved = save_and_disable_interrupts();
    if (q->count == 0) {
        restore_interrupts(saved);
        return false;
    }
    const uint8_t *slot = (const uint8_t *)q->buf + (q->head * q->item_size);
    memcpy(item, slot, q->item_size);
    restore_interrupts(saved);
    return true;
}

uint16_t rtos_queue_count(const rtos_queue_t *q)   { return q->count; }
bool     rtos_queue_is_full(const rtos_queue_t *q)  { return q->count == q->capacity; }
bool     rtos_queue_is_empty(const rtos_queue_t *q) { return q->count == 0; }
