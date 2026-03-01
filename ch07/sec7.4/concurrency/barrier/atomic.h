#ifndef ATOMIC_H
#define ATOMIC_H

#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>

/*
 * Memory Barrier Utilities
 * 
 * This module provides portable memory barrier and atomic operation
 * primitives for the compiler. Useful for thread-safe arena allocation,
 * concurrent token stream access, and parallel compilation phases.
 */

/* Memory ordering semantics */
typedef enum {
    MEMORY_ORDER_RELAXED = memory_order_relaxed,
    MEMORY_ORDER_CONSUME = memory_order_consume,
    MEMORY_ORDER_ACQUIRE = memory_order_acquire,
    MEMORY_ORDER_RELEASE = memory_order_release,
    MEMORY_ORDER_ACQ_REL = memory_order_acq_rel,
    MEMORY_ORDER_SEQ_CST = memory_order_seq_cst
} MemoryOrder;

/* Atomic types commonly used in compiler */
typedef _Atomic(size_t) atomic_size_t;
typedef _Atomic(int) atomic_int;
typedef _Atomic(bool) atomic_bool;
typedef _Atomic(void*) atomic_ptr;

/* Memory barriers */

/* Full memory barrier - ensures all memory ops before are visible before ops after */
static inline void memory_barrier_full(void) {
    atomic_thread_fence(memory_order_seq_cst);
}

/* Acquire barrier - prevents reordering of loads after this point with ops before */
static inline void memory_barrier_acquire(void) {
    atomic_thread_fence(memory_order_acquire);
}

/* Release barrier - prevents reordering of stores before this point with ops after */
static inline void memory_barrier_release(void) {
    atomic_thread_fence(memory_order_release);
}

/* Compiler barrier - prevents compiler reordering, not CPU reordering */
static inline void compiler_barrier(void) {
    atomic_signal_fence(memory_order_seq_cst);
}

/* Atomic operations */

/* Atomic load */
static inline size_t atomic_load_size(atomic_size_t *ptr, MemoryOrder order) {
    return atomic_load_explicit(ptr, order);
}

static inline void* atomic_load_ptr(atomic_ptr *ptr, MemoryOrder order) {
    return atomic_load_explicit(ptr, order);
}

/* Atomic store */
static inline void atomic_store_size(atomic_size_t *ptr, size_t val, MemoryOrder order) {
    atomic_store_explicit(ptr, val, order);
}

static inline void atomic_store_ptr(atomic_ptr *ptr, void* val, MemoryOrder order) {
    atomic_store_explicit(ptr, val, order);
}

/* Atomic exchange */
static inline size_t atomic_exchange_size(atomic_size_t *ptr, size_t val, MemoryOrder order) {
    return atomic_exchange_explicit(ptr, val, order);
}

/* Atomic compare-and-swap */
static inline bool atomic_cas_size(atomic_size_t *ptr, size_t *expected, size_t desired, 
                                   MemoryOrder success, MemoryOrder failure) {
    return atomic_compare_exchange_strong_explicit(ptr, expected, desired, success, failure);
}

static inline bool atomic_cas_ptr(atomic_ptr *ptr, void **expected, void *desired,
                                  MemoryOrder success, MemoryOrder failure) {
    return atomic_compare_exchange_strong_explicit(ptr, expected, desired, success, failure);
}

/* Atomic fetch-and-add */
static inline size_t atomic_fetch_add_size(atomic_size_t *ptr, size_t val, MemoryOrder order) {
    return atomic_fetch_add_explicit(ptr, val, order);
}

static inline int atomic_fetch_add_int(atomic_int *ptr, int val, MemoryOrder order) {
    return atomic_fetch_add_explicit(ptr, val, order);
}

/* Atomic increment/decrement helpers */
static inline size_t atomic_increment_size(atomic_size_t *ptr) {
    return atomic_fetch_add_explicit(ptr, 1, memory_order_seq_cst) + 1;
}

static inline size_t atomic_decrement_size(atomic_size_t *ptr) {
    return atomic_fetch_sub_explicit(ptr, 1, memory_order_seq_cst) - 1;
}

/* Spinlock implementation using atomics */
typedef struct {
    atomic_bool locked;
} Spinlock;

static inline void spinlock_init(Spinlock *lock) {
    atomic_store_explicit(&lock->locked, false, memory_order_relaxed);
}

static inline void spinlock_lock(Spinlock *lock) {
    bool expected = false;
    while (!atomic_compare_exchange_weak_explicit(&lock->locked, &expected, true,
                                                   memory_order_acquire,
                                                   memory_order_relaxed)) {
        expected = false;
        // Spin with a pause hint (CPU-specific optimization)
        #if defined(__x86_64__) || defined(__i386__)
        __builtin_ia32_pause();
        #elif defined(__aarch64__)
        __asm__ __volatile__("yield" ::: "memory");
        #endif
    }
}

static inline bool spinlock_trylock(Spinlock *lock) {
    bool expected = false;
    return atomic_compare_exchange_strong_explicit(&lock->locked, &expected, true,
                                                    memory_order_acquire,
                                                    memory_order_relaxed);
}

static inline void spinlock_unlock(Spinlock *lock) {
    atomic_store_explicit(&lock->locked, false, memory_order_release);
}

/* Lock-free stack node */
typedef struct LockFreeNode {
    void *data;
    _Atomic(struct LockFreeNode*) next;
} LockFreeNode;

/* Lock-free stack */
typedef struct {
    _Atomic(LockFreeNode*) head;
    atomic_size_t size;
} LockFreeStack;

/* Initialize lock-free stack */
static inline void lfstack_init(LockFreeStack *stack) {
    atomic_store_explicit(&stack->head, NULL, memory_order_relaxed);
    atomic_store_explicit(&stack->size, 0, memory_order_relaxed);
}

/* Push to lock-free stack */
static inline void lfstack_push(LockFreeStack *stack, LockFreeNode *node) {
    LockFreeNode *old_head = atomic_load_explicit(&stack->head, memory_order_relaxed);
    do {
        atomic_store_explicit(&node->next, old_head, memory_order_relaxed);
    } while (!atomic_compare_exchange_weak_explicit(&stack->head, &old_head, node,
                                                     memory_order_release,
                                                     memory_order_relaxed));
    atomic_fetch_add_explicit(&stack->size, 1, memory_order_relaxed);
}

/* Pop from lock-free stack */
static inline LockFreeNode* lfstack_pop(LockFreeStack *stack) {
    LockFreeNode *old_head = atomic_load_explicit(&stack->head, memory_order_acquire);
    LockFreeNode *new_head;
    
    do {
        if (old_head == NULL) {
            return NULL;
        }
        new_head = atomic_load_explicit(&old_head->next, memory_order_relaxed);
    } while (!atomic_compare_exchange_weak_explicit(&stack->head, &old_head, new_head,
                                                     memory_order_release,
                                                     memory_order_acquire));
    
    atomic_fetch_sub_explicit(&stack->size, 1, memory_order_relaxed);
    return old_head;
}

/* Get stack size (approximate in concurrent scenarios) */
static inline size_t lfstack_size(LockFreeStack *stack) {
    return atomic_load_explicit(&stack->size, memory_order_relaxed);
}

#endif /* ATOMIC_H */
