// arena.h
#ifndef ARENA_H
#define ARENA_H

#include <stddef.h>
#include <stdint.h>

#define ARENA_BLOCK_SIZE (64 * 1024) // 64KB blocks

typedef struct ArenaBlock {
    struct ArenaBlock *next;
    size_t size;
    size_t used;
    uint8_t data[];
} ArenaBlock;

typedef struct {
    ArenaBlock *current;
    ArenaBlock *first;
} Arena;

Arena* arena_create(void);
void* arena_alloc(Arena *arena, size_t size);
void arena_free(Arena *arena);
void arena_reset(Arena *arena);

#endif
