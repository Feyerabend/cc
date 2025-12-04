#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

// memory pool with fixed block size
#define MEMORY_POOL_SIZE 1024
#define BLOCK_SIZE 32
#define BLOCK_COUNT (MEMORY_POOL_SIZE / BLOCK_SIZE)

uint8_t memory_pool[MEMORY_POOL_SIZE];

typedef struct BlockHeader {
    int is_free;
    struct BlockHeader* next;
} BlockHeader;

BlockHeader* free_list = NULL;

void memory_pool_init() {
    free_list = (BlockHeader*)memory_pool;

    // free list with all blocks
    BlockHeader* current = free_list;
    for (int i = 0; i < BLOCK_COUNT; ++i) {
        current->is_free = 1;  // blocks are free at start
        if (i == BLOCK_COUNT - 1) {
            current->next = NULL;  // no next block for last one
        } else {
            current->next = (BlockHeader*)((uint8_t*)current + BLOCK_SIZE);
        }
        current = current->next;
    }
}

// allocate memory from the pool (returns a block of BLOCK_SIZE bytes)
void* pool_malloc() {
    BlockHeader* current = free_list;

    // find first free block
    while (current != NULL && !current->is_free) {
        current = current->next;
    }

    if (current != NULL) {
        current->is_free = 0;  // mark block as allocated
        return (void*)((uint8_t*)current + sizeof(BlockHeader));  // return block address (after the header)
    }

    return NULL;  // no free blocks available
}

// free block (add back to pool)
void pool_free(void* ptr) {
    if (ptr == NULL) return;

    // BlockHeader from pointer
    BlockHeader* block = (BlockHeader*)((uint8_t*)ptr - sizeof(BlockHeader));
    block->is_free = 1;
}

// Machine struct to track allocations
typedef struct Machine {
    void* allocated_blocks[10];
    int block_count;
} Machine;

void machine_init(Machine* machine) {
    machine->block_count = 0;
}

void* machine_alloc(Machine* machine) {
    void* addr = pool_malloc();
    if (addr != NULL) {
        machine->allocated_blocks[machine->block_count++] = addr;
        printf("Allocated block at address %p\n", addr);
    }
    return addr;
}

void machine_free(Machine* machine, void* addr) {
    pool_free(addr);
    printf("Freed memory at address %p\n", addr);
}

void machine_store(void* addr, int offset, int value) {
    int* block = (int*)((uint8_t*)addr + offset);
    *block = value;
    printf("Stored value %d at offset %d\n", value, offset);
}

int machine_load(void* addr, int offset) {
    int* block = (int*)((uint8_t*)addr + offset);
    int value = *block;
    printf("Loaded value %d from offset %d\n", value, offset);
    return value;
}


int main() {
    memory_pool_init();

    Machine machine;
    machine_init(&machine);

    const int int_size = sizeof(int);

    // 1: allocate a block for storing integers
    void* block = machine_alloc(&machine);

    // 2: store values in the block (simulating use of the block)
    machine_store(block, 0 * int_size, 10);
    machine_store(block, 1 * int_size, 20);
    machine_store(block, 2 * int_size, 30);

    // 3: retrieve stored values
    for (int i = 0; i < 3; i++) {
        machine_load(block, i * int_size);
    }

    // 4: free the allocated block
    machine_free(&machine, block);

    return 0;
}