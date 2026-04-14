#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>


// Error Propagation in C
//
// Alternative to the Null Object pattern.
// Instead of collapsing failure into neutral behaviour,
// we propagate failure explicitly via error codes.
//
// The key structural change from mem.c / allocator.c:
//
//   void* mem_malloc(size_t size)              // old: NULL on failure
//   int   mem_malloc(size_t size, void** out)  // new: error code + out-param
//
// This preserves failure information at every call site.
// The caller always knows *why* something failed, not just *that* it did.


#define MEMORY_POOL_SIZE 1024
uint8_t memory_pool[MEMORY_POOL_SIZE];


// Error codes

typedef enum {
    ERR_OK            =  0,
    ERR_OUT_OF_MEMORY = -1,
    ERR_NULL_PTR      = -2,
    ERR_INVALID_SIZE  = -3,
} MemError;

const char* mem_error_str(MemError err) {
    switch (err) {
        case ERR_OK:            return "OK";
        case ERR_OUT_OF_MEMORY: return "out of memory";
        case ERR_NULL_PTR:      return "null pointer";
        case ERR_INVALID_SIZE:  return "invalid size";
        default:                return "unknown error";
    }
}


// Allocator internals (unchanged from mem.c)

typedef struct BlockHeader {
    size_t size;
    int is_free;
    struct BlockHeader* next;
} BlockHeader;

BlockHeader* free_list = NULL;

void memory_init() {
    free_list = (BlockHeader*)memory_pool;
    free_list->size = MEMORY_POOL_SIZE - sizeof(BlockHeader);
    free_list->is_free = 1;
    free_list->next = NULL;
}

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


// Allocator API - explicit error propagation
//
// Every function returns a MemError.
// Outputs are written through pointer parameters.
// Callers cannot ignore failure without a deliberate cast.

// mem_malloc: allocate `size` bytes, write address to *out_ptr.
// Returns ERR_OUT_OF_MEMORY if no block is large enough.
MemError mem_malloc(size_t size, void** out_ptr) {
    if (out_ptr == NULL) return ERR_NULL_PTR;
    if (size == 0)       return ERR_INVALID_SIZE;

    BlockHeader* current = free_list;
    while (current != NULL) {
        if (current->is_free && current->size >= size) {
            current->is_free = 0;
            *out_ptr = (void*)((uint8_t*)current + sizeof(BlockHeader));
            return ERR_OK;
        }
        current = current->next;
    }

    *out_ptr = NULL; // make the out-param safe to inspect
    return ERR_OUT_OF_MEMORY;
}

// mem_free: release a previously allocated block.
MemError mem_free(void* ptr) {
    if (ptr == NULL) return ERR_NULL_PTR;

    BlockHeader* block = (BlockHeader*)((uint8_t*)ptr - sizeof(BlockHeader));
    block->is_free = 1;
    merge_free_blocks();
    return ERR_OK;
}

// mem_realloc: resize an existing allocation.
// If ptr is NULL, behaves like mem_malloc.
// On failure, the original allocation is left untouched.
MemError mem_realloc(void* ptr, size_t new_size, void** out_ptr) {
    if (out_ptr == NULL) return ERR_NULL_PTR;
    if (new_size == 0)   return ERR_INVALID_SIZE;

    if (ptr == NULL) return mem_malloc(new_size, out_ptr);

    BlockHeader* old_block = (BlockHeader*)((uint8_t*)ptr - sizeof(BlockHeader));
    if (old_block->size >= new_size) {
        *out_ptr = ptr; // already fits - no move needed
        return ERR_OK;
    }

    void* new_ptr = NULL;
    MemError err = mem_malloc(new_size, &new_ptr);
    if (err != ERR_OK) {
        *out_ptr = ptr; // leave original intact; caller decides what to do
        return err;
    }

    memcpy(new_ptr, ptr, old_block->size);
    mem_free(ptr); // original successfully migrated; safe to release
    *out_ptr = new_ptr;
    return ERR_OK;
}


// Machine layer - propagates errors up to the caller
//
// Compare with allocator.c: there, machine_* functions
// absorbed failure silently via the null object.
// Here, every failure is surfaced as a MemError.
// The caller decides what to do with it.


typedef struct Machine {
    void* allocated_blocks[10];
    int block_count;
} Machine;

void machine_init(Machine* machine) {
    machine->block_count = 0;
}

MemError machine_alloc(Machine* machine, size_t size, void** out_addr) {
    MemError err = mem_malloc(size, out_addr);
    if (err == ERR_OK) {
        machine->allocated_blocks[machine->block_count++] = *out_addr;
        printf("  Allocated %zu bytes at %p\n", size, *out_addr);
    } else {
        printf("  [ERROR] machine_alloc(%zu): %s\n", size, mem_error_str(err));
    }
    return err;
}

MemError machine_free(Machine* machine, void* addr) {
    MemError err = mem_free(addr);
    if (err == ERR_OK) {
        printf("  Freed memory at %p\n", addr);
    } else {
        printf("  [ERROR] machine_free(%p): %s\n", addr, mem_error_str(err));
    }
    return err;
}

MemError machine_realloc(Machine* machine, void* addr, size_t new_size, void** out_addr) {
    MemError err = mem_realloc(addr, new_size, out_addr);
    if (err == ERR_OK) {
        printf("  Reallocated %p -> %p (%zu bytes)\n", addr, *out_addr, new_size);
    } else {
        // Original pointer untouched - caller still owns it
        printf("  [ERROR] machine_realloc(%zu): %s - original block preserved\n",
               new_size, mem_error_str(err));
    }
    return err;
}

MemError machine_store(void* addr, int offset, int value) {
    if (addr == NULL) {
        printf("  [ERROR] machine_store: null pointer\n");
        return ERR_NULL_PTR;
    }
    int* slot = (int*)((uint8_t*)addr + offset);
    *slot = value;
    printf("  Stored %d at offset %d\n", value, offset);
    return ERR_OK;
}

MemError machine_load(void* addr, int offset, int* out_value) {
    if (addr == NULL || out_value == NULL) {
        printf("  [ERROR] machine_load: null pointer\n");
        return ERR_NULL_PTR;
    }
    *out_value = *((int*)((uint8_t*)addr + offset));
    printf("  Loaded %d from offset %d\n", *out_value, offset);
    return ERR_OK;
}


// Helper: abort if a critical allocation fails.
//
// This is the explicit policy decision the Null Object pattern
// hides: if allocation failure is catastrophic, say so loudly.

#define REQUIRE_OK(expr)                                 \
    do {                                                 \
        MemError _e = (expr);                            \
        if (_e != ERR_OK) {                              \
            fprintf(stderr, "Fatal: %s failed: %s\n",    \
                    #expr, mem_error_str(_e));           \
            exit(1);                                     \
        }                                                \
    } while (0)



int main() {
    memory_init();
    Machine machine;
    machine_init(&machine);
    const int z = sizeof(int);
    MemError err;
    void* block = NULL;
    int val = 0;

    printf("-- Normal path --\n");

    // 1: allocate block for 3 integers - abort on failure (critical path)
    REQUIRE_OK(machine_alloc(&machine, 3 * z, &block));

    // 2: store values
    REQUIRE_OK(machine_store(block, 0 * z, 10));
    REQUIRE_OK(machine_store(block, 1 * z, 20));
    REQUIRE_OK(machine_store(block, 2 * z, 30));

    // 3: expand block - abort on failure
    REQUIRE_OK(machine_realloc(&machine, block, 6 * z, &block));

    // 4: store more values
    REQUIRE_OK(machine_store(block, 3 * z, 40));
    REQUIRE_OK(machine_store(block, 4 * z, 50));
    REQUIRE_OK(machine_store(block, 5 * z, 60));

    // 5: read all values
    printf("  * reading 6 values *\n");
    for (int i = 0; i < 6; i++) {
        REQUIRE_OK(machine_load(block, i * z, &val));
    }

    // 6: overwrite slot 4
    REQUIRE_OK(machine_store(block, 4 * z, 90));

    // 7: read again
    printf("  * reading after update *\n");
    for (int i = 0; i < 6; i++) {
        REQUIRE_OK(machine_load(block, i * z, &val));
    }

    // 8: free
    REQUIRE_OK(machine_free(&machine, block));
    block = NULL;


    // Error path: allocation failure is explicit, not silent

    printf("\n-- Error propagation path --\n");

    void* too_large = NULL;
    err = machine_alloc(&machine, MEMORY_POOL_SIZE * 2, &too_large);

    // The caller can now make a deliberate choice:
    if (err != ERR_OK) {
        printf("  Allocation failed with: %s\n", mem_error_str(err));
        printf("  Policy decision: skip dependent work, do not store/load\n");

        // Unlike the Null Object pattern:
        //   machine_store(too_large, 0, 100)  would silently succeed with 0 written
        //
        // Here the failure is *known*. We choose not to proceed.
        // No write happens. No silent zero is returned from a load.
        // The difference matters when the stored value must be trusted.
    }

    // Attempting to use a null pointer is also an explicit error:
    err = machine_store(too_large, 0, 100);
    printf("  machine_store on NULL returned: %s\n", mem_error_str(err));

    err = machine_load(too_large, 0, &val);
    printf("  machine_load on NULL returned: %s (val unchanged: %d)\n",
           mem_error_str(err), val);

    // Realloc on a failed allocation - again, explicit:
    void* recovered = NULL;
    err = machine_realloc(&machine, too_large, 10, &recovered);
    if (err == ERR_OK) {
        printf("  Recovered allocation at %p\n", recovered);
        REQUIRE_OK(machine_free(&machine, recovered));
    } else {
        printf("  Could not recover: %s\n", mem_error_str(err));
    }

    printf("\n");
    printf("  Null Object  - failure becomes neutral behaviour; load returns 0\n");
    printf("  Error codes  - failure is preserved; caller decides what 0 means\n");

    return 0;
}
