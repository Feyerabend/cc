#pragma once
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ARENA_BLOCK_SIZE (1 << 20)  /* 1 MB */

typedef struct ArenaBlock ArenaBlock;
struct ArenaBlock {
    ArenaBlock *next;
    size_t cap, used;
    uint8_t data[];
};

typedef struct { ArenaBlock *head; } Arena;

static inline ArenaBlock *arena_new_block(size_t min) {
    size_t cap = min > ARENA_BLOCK_SIZE ? min : ARENA_BLOCK_SIZE;
    ArenaBlock *b = (ArenaBlock *)malloc(sizeof(ArenaBlock) + cap);
    if (!b) { perror("arena"); exit(1); }
    b->next = NULL; b->cap = cap; b->used = 0;
    return b;
}

static inline void *arena_alloc(Arena *a, size_t n) {
    n = (n + 7) & ~(size_t)7;  /* 8-byte align */
    if (!a->head || a->head->used + n > a->head->cap) {
        ArenaBlock *b = arena_new_block(n);
        b->next = a->head;
        a->head = b;
    }
    void *p = a->head->data + a->head->used;
    a->head->used += n;
    return p;
}

static inline char *arena_strdup(Arena *a, const char *s) {
    size_t n = strlen(s) + 1;
    char *p = (char *)arena_alloc(a, n);
    memcpy(p, s, n);
    return p;
}

static inline void arena_free_all(Arena *a) {
    ArenaBlock *b = a->head;
    while (b) { ArenaBlock *nxt = b->next; free(b); b = nxt; }
    a->head = NULL;
}
