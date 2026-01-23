// arena.c
#include "arena.h"
#include <stdlib.h>
#include <string.h>

Arena* arena_create(void) {
    Arena *arena = malloc(sizeof(Arena));
    arena->current = NULL;
    arena->first = NULL;
    return arena;
}

static ArenaBlock* arena_block_create(size_t min_size) {
    size_t size = min_size > ARENA_BLOCK_SIZE ? min_size : ARENA_BLOCK_SIZE;
    ArenaBlock *block = malloc(sizeof(ArenaBlock) + size);
    block->next = NULL;
    block->size = size;
    block->used = 0;
    return block;
}

void* arena_alloc(Arena *arena, size_t size) {
    if (size == 0) return NULL;
    
    // Align to 8 bytes
    size = (size + 7) & ~7;
    
    if (!arena->current || arena->current->used + size > arena->current->size) {
        ArenaBlock *new_block = arena_block_create(size);
        
        if (!arena->first) {
            arena->first = new_block;
            arena->current = new_block;
        } else {
            arena->current->next = new_block;
            arena->current = new_block;
        }
    }
    
    void *ptr = arena->current->data + arena->current->used;
    arena->current->used += size;
    return ptr;
}

void arena_free(Arena *arena) {
    ArenaBlock *block = arena->first;
    while (block) {
        ArenaBlock *next = block->next;
        free(block);
        block = next;
    }
    free(arena);
}

void arena_reset(Arena *arena) {
    ArenaBlock *block = arena->first;
    while (block) {
        block->used = 0;
        block = block->next;
    }
    arena->current = arena->first;
}
