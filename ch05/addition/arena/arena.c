/* 
 * ARENA ALLOCATOR
 * An arena allocator (also called a bump allocator or region allocator) is a
 * memory management strategy where you allocate from a large block of memory
 * and free everything at once when done.
 *
 * CONCEPTS:
 * - Fast allocation: Just bump a pointer forward
 * - No individual frees: Everything freed together
 * - Perfect for tree structures: AST, symbol tables, etc.
 * - Great cache locality: Related objects are near each other
 *
 * TRADE-OFFS:
 * Pros: Very fast, simple, no fragmentation, no leaks
 * Cons: Can't free individual objects, holds all memory until arena destroyed
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>
#include <stdbool.h>

#include <stdarg.h>
#include <time.h>


/* ARENA STRUCTURE */

// A single memory block in the arena
typedef struct ArenaBlock {
    void *memory;                // The actual memory
    size_t size;                 // Total size of this block
    size_t used;                 // How much we've used
    struct ArenaBlock *next;     // Next block (for growth)
} ArenaBlock;

// The arena itself
typedef struct Arena {
    ArenaBlock *current;         // Current block we're allocating from
    size_t default_block_size;   // Size for new blocks
    size_t total_allocated;      // Total memory allocated (for stats)
    size_t total_used;           // Total memory used (for stats)
} Arena;


/* CORE ARENA FUNCTIONS */

// Create a new arena with a default block size
Arena *arena_create(size_t block_size) {
    if (block_size == 0) {
        block_size = 64 * 1024;  // Default: 64KB
    }
    
    Arena *arena = malloc(sizeof(Arena));
    if (!arena) {
        return NULL;
    }
    
    arena->current = NULL;
    arena->default_block_size = block_size;
    arena->total_allocated = 0;
    arena->total_used = 0;
    
    return arena;
}

// Create a new memory block
static ArenaBlock *arena_block_create(size_t size) {
    ArenaBlock *block = malloc(sizeof(ArenaBlock));
    if (!block) {
        return NULL;
    }
    
    block->memory = malloc(size);
    if (!block->memory) {
        free(block);
        return NULL;
    }
    
    block->size = size;
    block->used = 0;
    block->next = NULL;
    
    return block;
}

// The core allocation function
void *arena_alloc(Arena *arena, size_t size) {
    // Align to 8 bytes for better performance and portability
    // This ensures pointers are properly aligned
    size_t aligned_size = (size + 7) & ~7;
    
    // Do we need a new block?
    if (!arena->current || arena->current->used + aligned_size > arena->current->size) {
        // Allocate a block big enough for this request
        size_t block_size = aligned_size > arena->default_block_size 
                          ? aligned_size 
                          : arena->default_block_size;
        
        ArenaBlock *new_block = arena_block_create(block_size);
        if (!new_block) {
            return NULL;
        }
        
        // Link it in (new blocks go at the front)
        new_block->next = arena->current;
        arena->current = new_block;
        arena->total_allocated += block_size;
    }
    
    // Allocate from current block
    void *ptr = (char*)arena->current->memory + arena->current->used;
    arena->current->used += aligned_size;
    arena->total_used += aligned_size;
    
    return ptr;
}

// Allocate and zero memory
void *arena_alloc_zero(Arena *arena, size_t size) {
    void *ptr = arena_alloc(arena, size);
    if (ptr) {
        memset(ptr, 0, size);
    }
    return ptr;
}

// Duplicate a string in the arena
char *arena_strdup(Arena *arena, const char *str) {
    if (!str) {
        return NULL;
    }
    
    size_t len = strlen(str) + 1;
    char *copy = arena_alloc(arena, len);
    if (copy) {
        memcpy(copy, str, len);
    }
    return copy;
}

// Format a string in the arena (like sprintf, but in arena)
char *arena_sprintf(Arena *arena, const char *fmt, ...) {
    va_list args, args_copy;
    
    // First pass: determine size needed
    va_start(args, fmt);
    va_copy(args_copy, args);
    int size = vsnprintf(NULL, 0, fmt, args);
    va_end(args);
    
    if (size < 0) {
        va_end(args_copy);
        return NULL;
    }
    
    // Allocate and format
    char *str = arena_alloc(arena, size + 1);
    if (str) {
        vsnprintf(str, size + 1, fmt, args_copy);
    }
    va_end(args_copy);
    
    return str;
}

// Destroy the entire arena
void arena_destroy(Arena *arena) {
    if (!arena) {
        return;
    }
    
    ArenaBlock *block = arena->current;
    while (block) {
        ArenaBlock *next = block->next;
        free(block->memory);
        free(block);
        block = next;
    }
    
    free(arena);
}

// Get statistics about the arena
void arena_stats(Arena *arena) {
    printf("Arena Statistics:\n");
    printf("  Total allocated: %zu bytes\n", arena->total_allocated);
    printf("  Total used:      %zu bytes\n", arena->total_used);
    printf("  Waste:           %zu bytes (%.1f%%)\n", 
           arena->total_allocated - arena->total_used,
           100.0 * (arena->total_allocated - arena->total_used) / arena->total_allocated);
    
    int block_count = 0;
    ArenaBlock *block = arena->current;
    while (block) {
        block_count++;
        block = block->next;
    }
    printf("  Blocks:          %d\n", block_count);
}


/* ADVANCED FEATURES */

// Save the current position (for temporary allocations)
typedef struct {
    ArenaBlock *block;
    size_t used;
} ArenaSavePoint;

ArenaSavePoint arena_save(Arena *arena) {
    ArenaSavePoint sp;
    sp.block = arena->current;
    sp.used = arena->current ? arena->current->used : 0;
    return sp;
}

// Restore to a saved position (free everything after this point)
void arena_restore(Arena *arena, ArenaSavePoint sp) {
    // Free all blocks after the saved one
    while (arena->current != sp.block) {
        ArenaBlock *next = arena->current->next;
        arena->total_allocated -= arena->current->size;
        arena->total_used -= arena->current->used;
        free(arena->current->memory);
        free(arena->current);
        arena->current = next;
    }
    
    // Reset the saved block's used pointer
    if (arena->current) {
        arena->total_used -= (arena->current->used - sp.used);
        arena->current->used = sp.used;
    }
}

// Reset arena without freeing memory (reuse allocations)
void arena_reset(Arena *arena) {
    ArenaBlock *block = arena->current;
    while (block) {
        block->used = 0;
        block = block->next;
    }
    arena->total_used = 0;
}


/* TYPED ALLOCATION MACROS (Type-safe convenience) */

#define arena_alloc_type(arena, type) \
    (type*)arena_alloc(arena, sizeof(type))

#define arena_alloc_array(arena, type, count) \
    (type*)arena_alloc(arena, sizeof(type) * (count))


/* EXAMPLE 1: Building an AST */

typedef enum { AST_NUMBER, AST_ADD, AST_MUL } ASTType;

typedef struct ASTNode {
    ASTType type;
    int value;
    struct ASTNode *left;
    struct ASTNode *right;
} ASTNode;

ASTNode *ast_create_number(Arena *arena, int value) {
    ASTNode *node = arena_alloc_type(arena, ASTNode);
    node->type = AST_NUMBER;
    node->value = value;
    node->left = NULL;
    node->right = NULL;
    return node;
}

ASTNode *ast_create_binop(Arena *arena, ASTType type, ASTNode *left, ASTNode *right) {
    ASTNode *node = arena_alloc_type(arena, ASTNode);
    node->type = type;
    node->value = 0;
    node->left = left;
    node->right = right;
    return node;
}

void ast_print(ASTNode *node, int depth) {
    for (int i = 0; i < depth; i++) printf("  ");
    
    switch (node->type) {
        case AST_NUMBER:
            printf("NUMBER %d\n", node->value);
            break;
        case AST_ADD:
            printf("ADD\n");
            ast_print(node->left, depth + 1);
            ast_print(node->right, depth + 1);
            break;
        case AST_MUL:
            printf("MUL\n");
            ast_print(node->left, depth + 1);
            ast_print(node->right, depth + 1);
            break;
    }
}

void example_ast() {
    printf("\n-- Example 1: Building an AST --\n");
    
    Arena *arena = arena_create(1024);
    
    // Build AST for: (2 + 3) * 4
    ASTNode *two = ast_create_number(arena, 2);
    ASTNode *three = ast_create_number(arena, 3);
    ASTNode *four = ast_create_number(arena, 4);
    
    ASTNode *add = ast_create_binop(arena, AST_ADD, two, three);
    ASTNode *mul = ast_create_binop(arena, AST_MUL, add, four);
    
    printf("Built AST:\n");
    ast_print(mul, 0);
    
    arena_stats(arena);
    
    // Destroy entire tree with one call!
    arena_destroy(arena);
    
    printf("  All memory freed with arena_destroy()\n");
}


/* EXAMPLE 2: String Interning */

typedef struct StringEntry {
    char *str;
    struct StringEntry *next;
} StringEntry;

typedef struct {
    Arena *arena;
    StringEntry *table[256];
} StringInterner;

StringInterner *interner_create() {
    StringInterner *intern = malloc(sizeof(StringInterner));
    intern->arena = arena_create(4096);
    memset(intern->table, 0, sizeof(intern->table));
    return intern;
}

static unsigned hash_string(const char *str) {
    unsigned hash = 5381;
    while (*str) {
        hash = ((hash << 5) + hash) + *str++;
    }
    return hash;
}

const char *interner_intern(StringInterner *intern, const char *str) {
    unsigned h = hash_string(str) % 256;
    
    // Check if already interned
    for (StringEntry *e = intern->table[h]; e; e = e->next) {
        if (strcmp(e->str, str) == 0) {
            return e->str;  // Return existing
        }
    }
    
    // Add new entry
    StringEntry *entry = arena_alloc_type(intern->arena, StringEntry);
    entry->str = arena_strdup(intern->arena, str);
    entry->next = intern->table[h];
    intern->table[h] = entry;
    
    return entry->str;
}

void interner_destroy(StringInterner *intern) {
    arena_destroy(intern->arena);
    free(intern);
}

void example_string_interning() {
    printf("\n-- Example 2: String Interning --\n");
    
    StringInterner *intern = interner_create();
    
    // Intern some strings
    const char *s1 = interner_intern(intern, "hello");
    const char *s2 = interner_intern(intern, "world");
    const char *s3 = interner_intern(intern, "hello");  // Same as s1
    
    printf("s1: %p '%s'\n", (void*)s1, s1);
    printf("s2: %p '%s'\n", (void*)s2, s2);
    printf("s3: %p '%s'\n", (void*)s3, s3);
    
    // s1 and s3 point to the same memory!
    assert(s1 == s3);
    printf("s1 == s3 (pointer equality) ok!\n");
    
    interner_destroy(intern);
}


/* EXAMPLE 3: Dynamic Array in Arena */

typedef struct {
    int *data;
    size_t count;
    size_t capacity;
    Arena *arena;
} IntArray;

IntArray *array_create(Arena *arena) {
    IntArray *arr = arena_alloc_type(arena, IntArray);
    arr->capacity = 8;
    arr->count = 0;
    arr->data = arena_alloc_array(arena, int, arr->capacity);
    arr->arena = arena;
    return arr;
}

void array_push(IntArray *arr, int value) {
    if (arr->count >= arr->capacity) {
        // Need to grow - allocate new array
        size_t new_capacity = arr->capacity * 2;
        int *new_data = arena_alloc_array(arr->arena, int, new_capacity);
        
        // Copy old data
        memcpy(new_data, arr->data, arr->count * sizeof(int));
        
        // Update array (old memory stays in arena, unused)
        arr->data = new_data;
        arr->capacity = new_capacity;
    }
    
    arr->data[arr->count++] = value;
}

void example_dynamic_array() {
    printf("\n-- Example 3: Dynamic Array --\n");
    
    Arena *arena = arena_create(1024);
    IntArray *arr = array_create(arena);
    
    // Add some numbers
    for (int i = 0; i < 20; i++) {
        array_push(arr, i * i);
    }
    
    printf("Array contents: ");
    for (size_t i = 0; i < arr->count; i++) {
        printf("%d ", arr->data[i]);
    }
    printf("\n");
    
    arena_stats(arena);
    arena_destroy(arena);
}


/* EXAMPLE 4: Temporary Allocations with Save/Restore */

void example_save_restore() {
    printf("\n-- Example 4: Save/Restore --\n");
    
    Arena *arena = arena_create(1024);
    
    // Allocate some permanent data
    char *name = arena_strdup(arena, "John Doe");
    printf("Allocated permanent: '%s'\n", name);
    
    // Save point for temporary allocations
    ArenaSavePoint sp = arena_save(arena);
    
    // Allocate temporary data
    char *temp1 = arena_strdup(arena, "temporary string 1");
    char *temp2 = arena_strdup(arena, "temporary string 2");
    int *temp_array = arena_alloc_array(arena, int, 100);
    
    printf("Allocated temporary data..\n");
    arena_stats(arena);
    
    // Restore - frees all temporary allocations!
    arena_restore(arena, sp);
    printf("\nAfter restore:\n");
    arena_stats(arena);
    
    // Permanent data still valid
    printf("Permanent data still valid: '%s'\n", name);
    
    arena_destroy(arena);
}


/* PERFORMANCE COMPARISON */

void benchmark_arena_vs_malloc() {
    printf("\n-- Performance Comparison --\n");
    
    const int ITERATIONS = 100000;
    clock_t start, end;
    
    // Test 1: Arena allocation
    start = clock();
    Arena *arena = arena_create(1024 * 1024);
    for (int i = 0; i < ITERATIONS; i++) {
        void *ptr = arena_alloc(arena, 64);
        (void)ptr;
    }
    arena_destroy(arena);
    end = clock();
    double arena_time = (double)(end - start) / CLOCKS_PER_SEC;
    
    // Test 2: malloc/free
    start = clock();
    void *ptrs[1000];
    /*
    for (int i = 0; i < ITERATIONS; i++) {
        ptrs[i % 1000] = malloc(64);
        if (i >= 1000) {
            free(ptrs[i % 1000]);
        }
    } */
    for (int i = 0; i < ITERATIONS; i++) {
        if (i >= 1000) {
            free(ptrs[i % 1000]);
        }
        ptrs[i % 1000] = malloc(64);
    }
    for (int i = 0; i < 1000; i++) {
        free(ptrs[i]);
    }
    end = clock();
    double malloc_time = (double)(end - start) / CLOCKS_PER_SEC;
    
    printf("Arena:  %.4f seconds\n", arena_time);
    printf("malloc: %.4f seconds\n", malloc_time);
    printf("Speedup: %.1fx faster\n", malloc_time / arena_time);
}



int main(void) {
    printf("Arena Allocator\n");
    
    example_ast();
    example_string_interning();
    example_dynamic_array();
    example_save_restore();
    benchmark_arena_vs_malloc();
    
    printf("\n  All examples completed successfully!\n");
    return 0;
}
