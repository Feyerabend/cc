#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

// --- memory allocator ---

#define MEMORY_POOL_SIZE 1000
#define MAX_BLOCKS 20  // max number of blocks table can track

// Blocks must be aligned for any type, like the memory malloc returns.
// The pool starts aligned, and all sizes are rounded up to ALIGNMENT.
#define ALIGNMENT _Alignof(max_align_t)
#define ALIGN_UP(n) (((n) + ALIGNMENT - 1) & ~(size_t) (ALIGNMENT - 1))

_Alignas(max_align_t) uint8_t memory_pool[MEMORY_POOL_SIZE];

// End of the part of the pool that holds whole aligned blocks
#define POOL_END (memory_pool + (MEMORY_POOL_SIZE & ~(size_t) (ALIGNMENT - 1)))

typedef struct BlockHeader {
    size_t size;
    int is_free;
} BlockHeader;

// Header size rounded up, so the data after it is aligned too
#define HEADER_SIZE ALIGN_UP(sizeof(BlockHeader))

typedef struct BlockTableEntry {
    BlockHeader* block;
    int in_use;
} BlockTableEntry;

BlockTableEntry block_table[MAX_BLOCKS];

void memory_init() {
    memset(memory_pool, 0, MEMORY_POOL_SIZE);
    memset(block_table, 0, sizeof(block_table));

    BlockHeader* initial_block = (BlockHeader*)memory_pool;
    initial_block->size = (size_t) (POOL_END - memory_pool) - HEADER_SIZE;
    initial_block->is_free = 1;

    block_table[0].block = initial_block;
    block_table[0].in_use = 1;
}

// find available block in the table
BlockHeader* find_free_block(size_t size) {
    for (int i = 0; i < MAX_BLOCKS; i++) {
        BlockTableEntry* entry = &block_table[i];
        if (entry->in_use && entry->block->is_free && entry->block->size >= size) {
            entry->block->is_free = 0;
            return entry->block;
        }
    }
    return NULL;
}

// allocator (malloc equivalent)
void* mem_malloc(size_t size) {
    size = ALIGN_UP(size) + HEADER_SIZE;  // total size with header
    BlockHeader* block = find_free_block(size - HEADER_SIZE);

    if (block) {
        size_t remaining_size = block->size + HEADER_SIZE - size;

        // add remaining free space as a new block in the table; if it is
        // too small for a block, it stays part of this one
        if (remaining_size > HEADER_SIZE) {
            block->size = size - HEADER_SIZE;
            BlockHeader* new_block = (BlockHeader*)((uint8_t*)block + size);
            new_block->size = remaining_size - HEADER_SIZE;
            new_block->is_free = 1;

            for (int i = 0; i < MAX_BLOCKS; i++) {
                if (!block_table[i].in_use) {
                    block_table[i].block = new_block;
                    block_table[i].in_use = 1;
                    break;
                }
            }
        }
        return (uint8_t*)block + HEADER_SIZE;
    }
    return NULL;
}

// free
void mem_free(void* ptr) {
    if (!ptr) return;
    BlockHeader* block = (BlockHeader*)((uint8_t*)ptr - HEADER_SIZE);
    block->is_free = 1;
}

// free at last!
void free_all() {
    BlockHeader* current = (BlockHeader*)memory_pool;
    while ((uint8_t*)current < POOL_END) {
        current->is_free = 1;
        current = (BlockHeader*)((uint8_t*)current + HEADER_SIZE + current->size);
    }
    printf("All blocks freed.\n");
}

void defragment() {
    uint8_t* compact_ptr = memory_pool;
    int table_index = 0;

    // compact occupied blocks to start of memory pool
    for (int i = 0; i < MAX_BLOCKS; i++) {
        BlockHeader* block = block_table[i].block;
        if (block && !block->is_free) {
            size_t total_size = HEADER_SIZE + block->size;
            if ((uint8_t*)block != compact_ptr) {
                memmove(compact_ptr, block, total_size);
                block_table[table_index].block = (BlockHeader*)compact_ptr;
            }
            compact_ptr += total_size;
            table_index++;
        }
    }

    // single free block at the end
    if (compact_ptr + HEADER_SIZE < POOL_END) {
        BlockHeader* new_free_block = (BlockHeader*)compact_ptr;
        new_free_block->size = (size_t) (POOL_END - compact_ptr) - HEADER_SIZE;
        new_free_block->is_free = 1;

        block_table[table_index].block = new_free_block;
        block_table[table_index].in_use = 1;
        table_index++;
    }

    // mark any remaining table entries as unused
    for (int i = table_index; i < MAX_BLOCKS; i++) {
        block_table[i].in_use = 0;
    }
}

// print memory state
void print_memory() {
    printf("Memory Pool Status:\n");
    for (int i = 0; i < MAX_BLOCKS; i++) {
        if (block_table[i].in_use) {
            BlockHeader* block = block_table[i].block;
            printf("  Block at %p - Size: %zu bytes, %s\n",
                   (void*)block, block->size, block->is_free ? "Free" : "Occupied");
        }
    }
    printf("\n");
}


int main() {
    memory_init();
    print_memory();

    // initial allocations
    printf("Allocating int block (4 bytes each).\n");
    int* int_block = (int*)mem_malloc(4 * sizeof(int));
    for (int i = 0; i < 4; i++) int_block[i] = i + 1;

    printf("Allocating float block (4 bytes each).\n");
    float* float_block = (float*)mem_malloc(4 * sizeof(float));
    for (int i = 0; i < 4; i++) float_block[i] = (i + 1) * 1.5;

    printf("Allocating string block (16 bytes).\n");
    char* string_block1 = (char*)mem_malloc(16 * sizeof(char));
    strcpy(string_block1, "Hello, World!");

    printf("Allocating second string block (24 bytes).\n");
    char* string_block2 = (char*)mem_malloc(24 * sizeof(char));
    strcpy(string_block2, "Memory Management!");

    print_memory();

    // Free some blocks to create fragmentation
    printf("Freeing int and first string block:\n");
    mem_free(int_block);
    mem_free(string_block1);

    print_memory();

    // Further allocations to fragment the memory
    printf("Allocating small char block (8 bytes).\n");
    char* small_char_block = (char*)mem_malloc(8 * sizeof(char));
    strcpy(small_char_block, "Test");

    printf("Allocating additional float block (8 bytes).\n");
    float* float_block2 = (float*)mem_malloc(2 * sizeof(float));
    for (int i = 0; i < 2; i++) float_block2[i] = (i + 1) * 2.5;

    print_memory();

    // defragment memory to consolidate free space
    printf("Defragmenting memory:\n");
    defragment();
    print_memory();

    // new allocation after defragmentation
    printf("Allocating large string block (32 bytes).\n");
    char* large_string_block = (char*)mem_malloc(32 * sizeof(char));
    strcpy(large_string_block, "Post-defragmentation test!");

    print_memory();

    // free all remaining blocks
    printf("Freeing remaining blocks:\n");
    mem_free(float_block);
    mem_free(string_block2);
    mem_free(small_char_block);
    mem_free(float_block2);
    mem_free(large_string_block);

    print_memory();

    // cleanup: free all blocks and reset pool
    printf("Final cleanup with free_all:\n");
    free_all();
    print_memory();
    
    return 0;
}