#ifndef RTOS_QUEUE_H
#define RTOS_QUEUE_H

#include <stdint.h>
#include <stdbool.h>

/*
 * rtos_queue.h - Thread-safe message queue for inter-task communication.
 *
 * Design: fixed-capacity ring buffer backed by caller-supplied storage.
 * No dynamic allocation - fits the embedded philosophy of this RTOS.
 *
 * Usage pattern:
 *
 *   // 1. Declare static storage (item type x capacity)
 *   static sensor_reading_t q_storage[8];
 *   static rtos_queue_t     q;
 *
 *   // 2. Initialise once before rtos_start()
 *   rtos_queue_init(&q, q_storage, sizeof(sensor_reading_t), 8);
 *
 *   // 3. Producer task
 *   rtos_queue_send(&q, &reading, RTOS_WAIT_FOREVER);
 *
 *   // 4. Consumer task
 *   rtos_queue_receive(&q, &out, RTOS_WAIT_FOREVER);
 *
 * Blocking behaviour:
 *   Both rtos_queue_send and rtos_queue_receive can block by calling
 *   task_delay(1) in a loop until the condition is met or the timeout
 *   expires.  This is the same cooperative-blocking pattern used by
 *   rtos_mutex_lock and rtos_semaphore_wait.
 */

/* Sentinel timeout values passed to send / receive */
#define RTOS_NO_WAIT       0u
#define RTOS_WAIT_FOREVER  0xFFFFFFFFu

typedef struct {
    void     *buf;       /* pointer to caller-supplied flat item storage */
    uint16_t  item_size; /* size of each item in bytes                   */
    uint16_t  capacity;  /* maximum number of items                      */
    uint16_t  head;      /* dequeue index (next item to read)            */
    uint16_t  tail;      /* enqueue index (next slot to write)           */
    uint16_t  count;     /* items currently in the queue                 */
} rtos_queue_t;

/*
 * Initialise a queue backed by caller-supplied storage.
 *
 *   q         - queue handle (must be zero-initialised or freshly declared)
 *   storage   - flat byte array; must be at least item_size x capacity bytes
 *   item_size - size of one message in bytes
 *   capacity  - maximum number of messages the queue can hold at once
 */
void rtos_queue_init(rtos_queue_t *q, void *storage,
                     uint16_t item_size, uint16_t capacity);

/*
 * Enqueue one item (copies item_size bytes from *item).
 *
 *   timeout_ms - RTOS_NO_WAIT:      return false immediately if full
 *                RTOS_WAIT_FOREVER: block until a slot is free
 *                N ms:              block up to N ms, then return false
 *
 * Returns true if the item was enqueued, false on timeout.
 * Safe to call from any task; NOT safe from ISR context.
 */
bool rtos_queue_send(rtos_queue_t *q, const void *item, uint32_t timeout_ms);

/*
 * Dequeue one item (copies item_size bytes into *item).
 * Same timeout semantics as rtos_queue_send.
 * Returns true if an item was dequeued, false on timeout.
 */
bool rtos_queue_receive(rtos_queue_t *q, void *item, uint32_t timeout_ms);

/*
 * Non-blocking peek: copy the front item without removing it.
 * Returns false if the queue is empty.
 */
bool rtos_queue_peek(const rtos_queue_t *q, void *item);

/* Query helpers - all non-blocking, safe from any context */
uint16_t rtos_queue_count(const rtos_queue_t *q);
bool     rtos_queue_is_full(const rtos_queue_t *q);
bool     rtos_queue_is_empty(const rtos_queue_t *q);

#endif /* RTOS_QUEUE_H */
