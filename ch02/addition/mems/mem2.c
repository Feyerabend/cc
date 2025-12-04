#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

// --- allocator ---
#define MEMORY_POOL_SIZE 1024 * 2
uint8_t memory_pool[MEMORY_POOL_SIZE];

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
    printf("Memory initialized: %zu bytes available\n", free_list->size);
}

// block splitting function
void split_block(BlockHeader* block, size_t size) {
    BlockHeader* new_block = (BlockHeader*)((uint8_t*)block + sizeof(BlockHeader) + size);
    new_block->size = block->size - sizeof(BlockHeader) - size;
    new_block->is_free = 1;
    new_block->next = block->next;

    block->size = size;
    block->next = new_block;

    printf("Block split: allocated %zu bytes, created new block of %zu bytes\n", size, new_block->size);
}

// merging adjacent free blocks
void merge_free_blocks() {
    BlockHeader* current = (BlockHeader*)memory_pool;
    while (current != NULL && current->next != NULL) {
        BlockHeader* next_block = current->next;
        if (current->is_free && next_block->is_free) {
            current->size += sizeof(BlockHeader) + next_block->size;
            current->next = next_block->next;
            printf("Merged blocks: new size %zu\n", current->size);
        } else {
            current = next_block;
        }
    }
}

// allocator function (malloc equivalent)
void* mem_malloc(size_t size) {
    BlockHeader* current = free_list;
    while (current != NULL) {
        if (current->is_free && current->size >= size) {
            if (current->size > size + sizeof(BlockHeader)) {
                split_block(current, size);  // split block if it's large enough
            }
            current->is_free = 0;
            printf("Allocated %zu bytes at address %p\n", size, (void*)((uint8_t*)current + sizeof(BlockHeader)));
            return (void*)((uint8_t*)current + sizeof(BlockHeader));
        }
        current = current->next;
    }
    printf("Memory allocation failed for %zu bytes\n", size);
    return NULL;
}

void mem_free(void* ptr) {
    if (ptr == NULL) return;
    BlockHeader* block = (BlockHeader*)((uint8_t*)ptr - sizeof(BlockHeader));
    block->is_free = 1;
    printf("Freed block at address %p\n", ptr);
    merge_free_blocks();
}

// --- machine & objects ---

// object types
typedef enum { INT_OBJECT, FLOAT_OBJECT, STRING_OBJECT } ObjectType;

typedef struct {
    ObjectType type;
} Object;

typedef struct {
    Object base;
    int value;
} IntObject;

typedef struct {
    Object base;
    float value;
} FloatObject;

typedef struct {
    Object base;
    char* value;
} StringObject;

// --- machine ---
typedef struct Machine {
    void** array;
    size_t size;
} Machine;

void machine_init(Machine* vm, size_t initial_size) {
    vm->array = (void**)mem_malloc(initial_size * sizeof(void*));
    if (vm->array == NULL) {
        printf("Memory allocation failed for VM array!\n");
        exit(1);
    }
    vm->size = initial_size;
    for (size_t i = 0; i < initial_size; i++) {
        vm->array[i] = NULL;
    }
}

void machine_add(Machine* vm, size_t index, ObjectType type, void* value) {
    if (index >= vm->size) {
        printf("Index out of bounds: %zu\n", index);
        return;
    }

    if (type == INT_OBJECT) {
        IntObject* obj = (IntObject*)mem_malloc(sizeof(IntObject));
        if (obj == NULL) {
            printf("Memory allocation failed for IntObject!\n");
            return;
        }
        obj->base.type = INT_OBJECT;
        obj->value = *(int*)value;
        vm->array[index] = obj;

    } else if (type == FLOAT_OBJECT) {
        FloatObject* obj = (FloatObject*)mem_malloc(sizeof(FloatObject));
        if (obj == NULL) {
            printf("Memory allocation failed for FloatObject!\n");
            return;
        }
        obj->base.type = FLOAT_OBJECT;
        obj->value = *(float*)value;
        vm->array[index] = obj;

    } else if (type == STRING_OBJECT) {
        StringObject* obj = (StringObject*)mem_malloc(sizeof(StringObject));
        if (obj == NULL) {
            printf("Memory allocation failed for StringObject!\n");
            return;
        }
        obj->base.type = STRING_OBJECT;
        obj->value = strdup((char*)value);
        if (obj->value == NULL) {
            printf("Memory allocation failed for string copy!\n");
            mem_free(obj);
            return;
        }
        vm->array[index] = obj;
    }
}

void machine_display(Machine* vm) {
    printf("Array contents (object references):\n");
    for (size_t i = 0; i < vm->size; i++) {
        Object* obj = (Object*)vm->array[i];
        if (obj == NULL) {
            printf("[%zu]: NULL\n", i);
        } else {
            switch (obj->type) {
                case INT_OBJECT: {
                    IntObject* int_obj = (IntObject*)obj;
                    printf("[%zu]: INT = %d\n", i, int_obj->value);
                    break;
                }
                case FLOAT_OBJECT: {
                    FloatObject* float_obj = (FloatObject*)obj;
                    printf("[%zu]: FLOAT = %f\n", i, float_obj->value);
                    break;
                }
                case STRING_OBJECT: {
                    StringObject* str_obj = (StringObject*)obj;
                    printf("[%zu]: STRING = %s\n", i, str_obj->value);
                    break;
                }
                default:
                    printf("[%zu]: UNKNOWN OBJECT\n", i);
            }
        }
    }
}

void machine_delete(Machine* vm, size_t index) {
    if (index >= vm->size || vm->array[index] == NULL) return;

    Object* obj = (Object*)vm->array[index];
    if (obj->type == STRING_OBJECT) {
        StringObject* str_obj = (StringObject*)obj;
        free(str_obj->value);  // free duplicated string!
    }
    mem_free(obj);
    vm->array[index] = NULL;
}

// sample
int main() {
    memory_init();
    Machine vm;
    machine_init(&vm, 5);

    // new objects
    int int_val = 42;
    machine_add(&vm, 0, INT_OBJECT, &int_val);

    float float_val = 3.14f;
    machine_add(&vm, 1, FLOAT_OBJECT, &float_val);

    char str_val[] = "Hello, World!";
    machine_add(&vm, 2, STRING_OBJECT, str_val);

    // display array contents
    machine_display(&vm);

    machine_delete(&vm, 2);

    char str_val2[] = "Hi, to you!";
    machine_add(&vm, 3, STRING_OBJECT, str_val2);

    machine_display(&vm);

    // clean
    for (size_t i = 0; i < vm.size; i++) {
        machine_delete(&vm, i);
    }
    mem_free(vm.array);

    return 0;
}
