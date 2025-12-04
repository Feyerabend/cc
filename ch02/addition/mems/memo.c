#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#define MEMORY_POOL_SIZE 1024 // max memory
#define BLOCK_SIZE 64
#define BLOCK_COUNT (MEMORY_POOL_SIZE / BLOCK_SIZE)

uint8_t memory_pool[MEMORY_POOL_SIZE];

typedef struct BlockHeader {
    int is_free;
    int ref_count; // ref. count for automatic deallocation
    struct BlockHeader* next;  // next block in free list
} BlockHeader;

BlockHeader* free_list = NULL;

void memory_pool_init() {
    free_list = (BlockHeader*)memory_pool;
    BlockHeader* current = free_list;

    for (int i = 0; i < BLOCK_COUNT; ++i) {
        current->is_free = 1;
        current->ref_count = 0;  // ref. count starts at 0
        if (i == BLOCK_COUNT - 1) {
            current->next = NULL;
        } else {
            current->next = (BlockHeader*)((uint8_t*)current + BLOCK_SIZE);
        }
        current = current->next;
    }
}

// allocate memory from pool
void* pool_malloc() {
    BlockHeader* current = free_list;

    // find first free block
    while (current != NULL && !current->is_free) {
        current = current->next;
    }

    if (current != NULL) {
        current->is_free = 0;  // mark block as allocated
        current->ref_count = 1;  // init. ref. count to 1
        return (void*)((uint8_t*)current + sizeof(BlockHeader));  // return block address (after header)
    }

    return NULL;  // no free blocks
}

// increment ref. count of block
void pool_retain(void* ptr) {
    if (ptr == NULL) return;

    BlockHeader* block = (BlockHeader*)((uint8_t*)ptr - sizeof(BlockHeader));
    block->ref_count++;  // increase ref. count
}

// decrement ref. count of block, free if count reaches zero
void pool_release(void* ptr) {
    if (ptr == NULL) return;

    BlockHeader* block = (BlockHeader*)((uint8_t*)ptr - sizeof(BlockHeader));
    block->ref_count--;

    if (block->ref_count == 0) {
        block->is_free = 1;  // free block, if ref. count is 0
        printf("Block at address %p is now freed\n", ptr);
    }
}

// Object structures
typedef struct {
    char name[32];  // Person's name
    int age;        // Person's age
} Person;

typedef struct {
    char brand[32];  // Computer's brand
    int year;        // Manufacture year
} Computer;

// allocate and initialize a person
Person* create_person(const char* name, int age) {
    Person* person = (Person*)pool_malloc();
    if (person != NULL) {
        strncpy(person->name, name, sizeof(person->name) - 1);
        person->age = age;
        printf("Created person: %s, age %d\n", person->name, person->age);
    }
    return person;
}

// allocate and initialize a computer
Computer* create_computer(const char* brand, int year) {
    Computer* computer = (Computer*)pool_malloc();
    if (computer != NULL) {
        strncpy(computer->brand, brand, sizeof(computer->brand) - 1);
        computer->year = year;
        printf("Created computer: %s, year %d\n", computer->brand, computer->year);
    }
    return computer;
}


int main() {
    memory_pool_init();

    // create
    Person* alice = create_person("Alice", 30);
    Computer* zx81 = create_computer("ZX81", 1981);

    // retain references to objects (simulating shared usage)
    pool_retain(alice);  // increment ref. count for Alice
    pool_retain(zx81); // increment ref. count for ZX81

    // release one reference to Alice (but not fully freed yet)
    pool_release(alice);  // decrease ref_count to 1 (not yet freed)

    // fully release Alice (now ref_count reaches 0, Alice is freed)
    pool_release(alice);  // now Alice is freed

    // release ZX81 (fully released)
    pool_release(zx81);  // now ZX81 is freed

    // create
    Person* bob = create_person("Bob", 25);

    // another example of retaining and releasing
    pool_retain(bob);  // increment ref. count for Bob
    pool_release(bob); // decrement ref. count (not freed yet)
    pool_release(bob); // now Bob is freed

    return 0;
}
