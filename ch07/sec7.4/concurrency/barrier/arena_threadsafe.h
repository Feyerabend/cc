#ifndef ARENA_THREADSAFE_H
#define ARENA_THREADSAFE_H

#include "atomic.h"
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

/*
 * Thread-Safe Arena Allocator
 * 
 * Uses memory barriers and atomic operations to provide safe concurrent
 * allocation from multiple threads. Each thread can allocate independently
 * without lock contention in most cases.
 */

typedef struct ArenaBlock {
    void *memory;
    atomic_size_t used;
    size_t capacity;
    _Atomic(struct ArenaBlock*) next;
} ArenaBlock;

typedef struct {
    _Atomic(ArenaBlock*) current;
    atomic_size_t default_block_size;
    Spinlock block_creation_lock;  // Only for creating new blocks
    atomic_size_t total_allocated;
    atomic_size_t total_blocks;
} ThreadSafeArena;

/* Create a thread-safe arena */
static inline ThreadSafeArena* ts_arena_create(size_t block_size) {
    ThreadSafeArena *arena = malloc(sizeof(ThreadSafeArena));
    if (!arena) return NULL;
    
    atomic_store_explicit(&arena->current, NULL, memory_order_relaxed);
    atomic_store_explicit(&arena->default_block_size, block_size, memory_order_relaxed);
    spinlock_init(&arena->block_creation_lock);
    atomic_store_explicit(&arena->total_allocated, 0, memory_order_relaxed);
    atomic_store_explicit(&arena->total_blocks, 0, memory_order_relaxed);
    
    return arena;
}

/* Create a new arena block */
static inline ArenaBlock* ts_arena_block_create(size_t size) {
    ArenaBlock *block = malloc(sizeof(ArenaBlock));
    if (!block) return NULL;
    
    block->memory = malloc(size);
    if (!block->memory) {
        free(block);
        return NULL;
    }
    
    block->capacity = size;
    atomic_store_explicit(&block->used, 0, memory_order_relaxed);
    atomic_store_explicit(&block->next, NULL, memory_order_relaxed);
    
    return block;
}

/* Allocate from thread-safe arena */
static inline void* ts_arena_alloc(ThreadSafeArena *arena, size_t size) {
    // Align to 8 bytes
    size = (size + 7) & ~7;
    
    // Try to allocate from current block using CAS
    ArenaBlock *current = atomic_load_explicit(&arena->current, memory_order_acquire);
    
    if (current) {
        // Optimistic allocation attempt
        size_t old_used = atomic_load_explicit(&current->used, memory_order_relaxed);
        
        while (old_used + size <= current->capacity) {
            // Try to reserve space with CAS
            if (atomic_compare_exchange_weak_explicit(&current->used, &old_used, 
                                                       old_used + size,
                                                       memory_order_release,
                                                       memory_order_relaxed)) {
                // Success! We reserved the space
                void *ptr = (char*)current->memory + old_used;
                atomic_fetch_add_explicit(&arena->total_allocated, size, memory_order_relaxed);
                return ptr;
            }
            // CAS failed, reload and retry
            old_used = atomic_load_explicit(&current->used, memory_order_relaxed);
        }
    }
    
    // Need a new block - acquire lock to prevent multiple threads creating blocks
    spinlock_lock(&arena->block_creation_lock);
    
    // Double-check after acquiring lock
    current = atomic_load_explicit(&arena->current, memory_order_acquire);
    if (current) {
        size_t used = atomic_load_explicit(&current->used, memory_order_relaxed);
        if (used + size <= current->capacity) {
            // Another thread created a block while we were waiting
            size_t old_used = used;
            if (atomic_compare_exchange_strong_explicit(&current->used, &old_used,
                                                         old_used + size,
                                                         memory_order_release,
                                                         memory_order_relaxed)) {
                spinlock_unlock(&arena->block_creation_lock);
                void *ptr = (char*)current->memory + old_used;
                atomic_fetch_add_explicit(&arena->total_allocated, size, memory_order_relaxed);
                return ptr;
            }
        }
    }
    
    // Create new block
    size_t default_size = atomic_load_explicit(&arena->default_block_size, memory_order_relaxed);
    size_t block_size = size > default_size ? size : default_size;
    ArenaBlock *new_block = ts_arena_block_create(block_size);
    
    if (!new_block) {
        spinlock_unlock(&arena->block_creation_lock);
        return NULL;
    }
    
    // Allocate from new block
    atomic_store_explicit(&new_block->used, size, memory_order_relaxed);
    void *ptr = new_block->memory;
    
    // Link new block (with memory barrier to ensure block is fully initialized)
    ArenaBlock *old_current = atomic_load_explicit(&arena->current, memory_order_relaxed);
    atomic_store_explicit(&new_block->next, old_current, memory_order_relaxed);
    
    // Release barrier ensures new block is visible to other threads
    atomic_store_explicit(&arena->current, new_block, memory_order_release);
    
    atomic_fetch_add_explicit(&arena->total_allocated, size, memory_order_relaxed);
    atomic_fetch_add_explicit(&arena->total_blocks, 1, memory_order_relaxed);
    
    spinlock_unlock(&arena->block_creation_lock);
    
    return ptr;
}

/* Thread-safe string duplication */
static inline char* ts_arena_strdup(ThreadSafeArena *arena, const char *str) {
    if (!str) return NULL;
    size_t len = strlen(str) + 1;
    char *copy = ts_arena_alloc(arena, len);
    if (copy) {
        memcpy(copy, str, len);
    }
    return copy;
}

/* Get statistics */
static inline size_t ts_arena_total_allocated(ThreadSafeArena *arena) {
    return atomic_load_explicit(&arena->total_allocated, memory_order_relaxed);
}

static inline size_t ts_arena_total_blocks(ThreadSafeArena *arena) {
    return atomic_load_explicit(&arena->total_blocks, memory_order_relaxed);
}

/* Destroy thread-safe arena */
static inline void ts_arena_destroy(ThreadSafeArena *arena) {
    if (!arena) return;
    
    ArenaBlock *block = atomic_load_explicit(&arena->current, memory_order_acquire);
    while (block) {
        ArenaBlock *next = atomic_load_explicit(&block->next, memory_order_relaxed);
        free(block->memory);
        free(block);
        block = next;
    }
    free(arena);
}

#endif /* ARENA_THREADSAFE_H */
