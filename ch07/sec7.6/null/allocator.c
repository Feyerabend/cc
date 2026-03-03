#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

// allocator

#define MEMORY_POOL_SIZE 1024
uint8_t memory_pool[MEMORY_POOL_SIZE];

typedef struct BlockHeader {
    size_t size;
    int is_free;
    struct BlockHeader* next;
    int is_null_object; // flag to identify if this is null object
} BlockHeader;

// define our null object (global singleton, careful ..)
BlockHeader null_block_header;
void* null_block;

// fwd decl
void merge_free_blocks();
void memory_init();

// init null object
void init_null_object() {
    null_block_header.size = 0;
    null_block_header.is_free = 0;
    null_block_header.next = NULL;
    null_block_header.is_null_object = 1;
    
    // null block points to area right after header
    null_block = (void*)((uint8_t*)&null_block_header + sizeof(BlockHeader));
}

BlockHeader* free_list = NULL;

void memory_init() {
    // first ..
    init_null_object();
    
    // .. then init main memory pool
    free_list = (BlockHeader*)memory_pool;
    free_list->size = MEMORY_POOL_SIZE - sizeof(BlockHeader);
    free_list->is_free = 1;
    free_list->next = NULL;
    free_list->is_null_object = 0;
}

// pointer is null object?
int is_null_object(void* ptr) {
    if (ptr == null_block)
        return 1;
    
    // if, we can safely check header
    if (ptr != NULL) {
        BlockHeader* block = (BlockHeader*)((uint8_t*)ptr - sizeof(BlockHeader));
        return block->is_null_object;
    }
    
    return 0;
}

// merging adjacent free blocks
void merge_free_blocks() {
    BlockHeader* current = (BlockHeader*)memory_pool;
    while (current != NULL && current->next != NULL) {
        BlockHeader* next_block = current->next;
        if (current->is_free && next_block->is_free) {
            current->size += sizeof(BlockHeader) + next_block->size;
            current->next = next_block->next;
        } else {
            current = next_block;
        }
    }
}

// allocator (malloc equivalent)
void* mem_malloc(size_t size) {
    BlockHeader* current = free_list;
    while (current != NULL) {
        if (current->is_free && current->size >= size) {
            current->is_free = 0;
            return (void*)((uint8_t*)current + sizeof(BlockHeader));
        }
        current = current->next;
    }
    // instead of returning NULL, return null object
    return null_block;
}

void mem_free(void* ptr) {
    // if null object, do nothing (no-op)
    if (is_null_object(ptr))
        return;
        
    // regular free logic for real blocks
    BlockHeader* block = (BlockHeader*)((uint8_t*)ptr - sizeof(BlockHeader));
    block->is_free = 1;
    merge_free_blocks();
}

// alloc memory for existing block (realloc equivalent)
void* mem_realloc(void* ptr, size_t new_size) {
    // if given null block, treat as malloc
    if (is_null_object(ptr))
        return mem_malloc(new_size);
    
    BlockHeader* old_block = (BlockHeader*)((uint8_t*)ptr - sizeof(BlockHeader));
    if (old_block->size >= new_size)
        return ptr;  // if the block is already large enough

    void* new_ptr = mem_malloc(new_size);
    if (!is_null_object(new_ptr)) {
        memcpy(new_ptr, ptr, old_block->size);
        mem_free(ptr);
    }
    return new_ptr;
}

// machine

typedef struct Machine {
    void* allocated_blocks[10];
    int block_count;
} Machine;

void machine_init(Machine* machine) {
    machine->block_count = 0;
}

void* machine_alloc(Machine* machine, size_t size) {
    void* addr = mem_malloc(size);
    
    // only add to allocated blocks, if a real block
    if (!is_null_object(addr)) {
        machine->allocated_blocks[machine->block_count++] = addr;
        printf("Allocated %zu bytes at address %p\n", size, addr);
    } else {
        printf("Failed to allocate %zu bytes, using null object\n", size);
    }
    
    return addr;
}

void machine_free(Machine* machine, void* addr) {
    if (is_null_object(addr)) {
        printf("Attempted to free null object (no-op)\n");
        return;
    }
    
    mem_free(addr);
    printf("Freed memory at address %p\n", addr);
}

void* machine_realloc(Machine* machine, void* addr, size_t new_size) {
    void* new_addr = mem_realloc(addr, new_size);
    
    if (is_null_object(new_addr)) {
        printf("Failed to reallocate memory to %zu bytes, using null object\n", new_size);
    } else if (is_null_object(addr)) {
        printf("Reallocated from null object to %p, new size: %zu bytes\n", new_addr, new_size);
        // add to allocated blocks
        machine->allocated_blocks[machine->block_count++] = new_addr;
    } else {
        printf("Reallocated memory from %p to %p, new size: %zu bytes\n", addr, new_addr, new_size);
    }
    
    return new_addr;
}

void machine_store(void* addr, int offset, int value) {
    // safe store - do nothing if null object
    if (is_null_object(addr)) {
        printf("Attempted to store value %d at null object (no-op)\n", value);
        return;
    }
    
    int* block = (int*)((uint8_t*)addr + offset);
    *block = value;
    printf("Stored value %d at offset %d\n", value, offset);
}

int machine_load(void* addr, int offset) {
    // safe load - return 0 if null object
    if (is_null_object(addr)) {
        printf("Attempted to load from null object, returning 0\n");
        return 0;
    }
    
    int* block = (int*)((uint8_t*)addr + offset);
    int value = *block;
    printf("Loaded value %d from offset %d\n", value, offset);
    return value;
}



int main() {
    memory_init();
    Machine machine;
    machine_init(&machine);
    const int z = sizeof(int);

    // 1: allocate small block for 3 integers
    void* block = machine_alloc(&machine, 3 * z);

    // 2: store values in block (simulating "dynamic array")
    machine_store(block, 0 * z, 10);
    machine_store(block, 1 * z, 20);
    machine_store(block, 2 * z, 30);

    // 3: expand block (add more numbers, i.e. reallocating)
    block = machine_realloc(&machine, block, 6 * z);

    // 4: add more values in expanded block
    machine_store(block, 3 * z, 40);
    machine_store(block, 4 * z, 50);
    machine_store(block, 5 * z, 60);

    // 5: retrieve values (from "dynamic array")
    for (int i = 0; i < 6; i++) {
        machine_load(block, i * z);
    }
    
    // 6: replace value at offset (where 50 lives)
    machine_store(block, 4 * z, 90);

    // 7: retrieve values
    for (int i = 0; i < 6; i++) {
        machine_load(block, i * z);
    }

    // 8: free block
    machine_free(&machine, block);
    
    // 9: Test null object pattern
    printf("\n-- Testing Null Object Pattern --\n");
    
    // Try to allocate beyond memory capacity
    void* too_large = machine_alloc(&machine, MEMORY_POOL_SIZE * 2);
    
    // Try operations on null object
    machine_store(too_large, 0, 100);  // This should not crash
    int val = machine_load(too_large, 0);  // This should return 0
    printf("Loaded value from null object: %d\n", val);
    
    // Try realloc on null object
    void* reallocated = machine_realloc(&machine, too_large, 10);
    
    // Free the null object (should be no-op)
    machine_free(&machine, too_large);

    return 0;
}

