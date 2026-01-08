/*
 * Affine Type System Interpreter in C
 * 
 * Demonstrates:
 * - Affine type tracking (use at most once)
 * - Move semantics vs copy semantics
 * - Use-after-move detection
 * - Explicit memory management
 * 
 * Compile: gcc -o affine affine.c -Wall -std=c99
 * Run: ./affine
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#define MAX_VARS 100
#define MAX_HEAP 1000
#define MAX_NAME 32


// MEMORY MANAGEMENT

typedef struct {
    int addr;
    int value;
    bool allocated;
} HeapSlot;

typedef struct {
    HeapSlot slots[MAX_HEAP];
    int next_addr;
    int allocations;
    int deallocations;
} Memory;

Memory memory;

void memory_init() {
    memory.next_addr = 1000;
    memory.allocations = 0;
    memory.deallocations = 0;
    for (int i = 0; i < MAX_HEAP; i++) {
        memory.slots[i].allocated = false;
    }
}

int memory_alloc(int value) {
    // Find free slot
    for (int i = 0; i < MAX_HEAP; i++) {
        if (!memory.slots[i].allocated) {
            memory.slots[i].addr = memory.next_addr;
            memory.slots[i].value = value;
            memory.slots[i].allocated = true;
            memory.allocations++;
            
            printf("    ALLOC: address %d = %d\n", memory.next_addr, value);
            
            return memory.next_addr++;
        }
    }
    
    fprintf(stderr, "Out of memory!\n");
    exit(1);
}

int memory_read(int addr) {
    for (int i = 0; i < MAX_HEAP; i++) {
        if (memory.slots[i].allocated && memory.slots[i].addr == addr) {
            return memory.slots[i].value;
        }
    }
    
    fprintf(stderr, "Invalid memory access: %d\n", addr);
    exit(1);
}

void memory_free(int addr) {
    for (int i = 0; i < MAX_HEAP; i++) {
        if (memory.slots[i].allocated && memory.slots[i].addr == addr) {
            printf("     FREE: address %d (was %d)\n", addr, memory.slots[i].value);
            memory.slots[i].allocated = false;
            memory.deallocations++;
            return;
        }
    }
    
    fprintf(stderr, "Double free or invalid free: %d\n", addr);
}

void memory_stats() {
    printf("\n Memory Stats:\n");
    printf("   Allocations: %d\n", memory.allocations);
    printf("   Deallocations: %d\n", memory.deallocations);
    printf("   Leaked: %d\n", memory.allocations - memory.deallocations);
    
    int leaked = 0;
    printf("   Still allocated: [");
    for (int i = 0; i < MAX_HEAP; i++) {
        if (memory.slots[i].allocated) {
            if (leaked > 0) printf(", ");
            printf("%d", memory.slots[i].addr);
            leaked++;
        }
    }
    printf("]\n");
}


// AFFINE TYPE SYSTEM

typedef enum {
    TYPE_VALUE,      // Unrestricted (copyable)
    TYPE_AFFINE,     // Use at most once
    TYPE_REFERENCE   // Borrowed reference
} TypeKind;

typedef struct {
    TypeKind kind;
} Type;

typedef struct {
    char name[MAX_NAME];
    Type type;
    int value;           // The actual value (address for affine types)
    bool consumed;       // Has this been consumed?
    int consumed_at;     // Line where consumed
    bool in_use;         // Is this slot in use?
} VarInfo;

typedef struct {
    VarInfo vars[MAX_VARS];
    int count;
    int current_line;
    int error_count;
} AffineChecker;

AffineChecker checker;

void checker_init() {
    checker.count = 0;
    checker.current_line = 0;
    checker.error_count = 0;
    for (int i = 0; i < MAX_VARS; i++) {
        checker.vars[i].in_use = false;
    }
}

const char* type_name(TypeKind kind) {
    switch (kind) {
        case TYPE_VALUE: return "value";
        case TYPE_AFFINE: return "affine";
        case TYPE_REFERENCE: return "reference";
        default: return "unknown";
    }
}

VarInfo* find_var(const char* name) {
    for (int i = 0; i < checker.count; i++) {
        if (checker.vars[i].in_use && strcmp(checker.vars[i].name, name) == 0) {
            return &checker.vars[i];
        }
    }
    return NULL;
}

void checker_error(const char* msg) {
    printf("  ERROR (line %d): %s\n", checker.current_line, msg);
    checker.error_count++;
}

void checker_log(const char* msg) {
    printf("  [%d] %s\n", checker.current_line, msg);
}

void checker_declare(const char* name, Type type, int value) {
    if (checker.count >= MAX_VARS) {
        fprintf(stderr, "Too many variables!\n");
        exit(1);
    }
    
    VarInfo* var = &checker.vars[checker.count++];
    strncpy(var->name, name, MAX_NAME - 1);
    var->name[MAX_NAME - 1] = '\0';
    var->type = type;
    var->value = value;
    var->consumed = false;
    var->consumed_at = -1;
    var->in_use = true;
    
    char log_msg[256];
    snprintf(log_msg, sizeof(log_msg), "DECLARE %s: %s", name, type_name(type.kind));
    checker_log(log_msg);
}

bool checker_consume(const char* name) {
    VarInfo* var = find_var(name);
    
    if (var == NULL) {
        char msg[256];
        snprintf(msg, sizeof(msg), "Variable '%s' not found", name);
        checker_error(msg);
        return false;
    }
    
    if (var->consumed) {
        char msg[256];
        snprintf(msg, sizeof(msg), 
                 "Use after move: '%s' was already consumed at line %d", 
                 name, var->consumed_at);
        checker_error(msg);
        return false;
    }
    
    if (var->type.kind == TYPE_AFFINE) {
        var->consumed = true;
        var->consumed_at = checker.current_line;
        
        char log_msg[256];
        snprintf(log_msg, sizeof(log_msg), "CONSUME %s (affine type)", name);
        checker_log(log_msg);
    } else {
        char log_msg[256];
        snprintf(log_msg, sizeof(log_msg), "USE %s (copyable type)", name);
        checker_log(log_msg);
    }
    
    return true;
}

bool checker_check_use(const char* name) {
    VarInfo* var = find_var(name);
    
    if (var == NULL) {
        char msg[256];
        snprintf(msg, sizeof(msg), "Variable '%s' not found", name);
        checker_error(msg);
        return false;
    }
    
    if (var->consumed) {
        char msg[256];
        snprintf(msg, sizeof(msg), 
                 "Use after move: '%s' was consumed at line %d", 
                 name, var->consumed_at);
        checker_error(msg);
        return false;
    }
    
    char log_msg[256];
    snprintf(log_msg, sizeof(log_msg), "READ %s", name);
    checker_log(log_msg);
    
    return true;
}

bool checker_copy(const char* name) {
    VarInfo* var = find_var(name);
    
    if (var == NULL) {
        char msg[256];
        snprintf(msg, sizeof(msg), "Variable '%s' not found", name);
        checker_error(msg);
        return false;
    }
    
    if (var->consumed) {
        char msg[256];
        snprintf(msg, sizeof(msg), "Cannot copy consumed variable '%s'", name);
        checker_error(msg);
        return false;
    }
    
    char log_msg[256];
    snprintf(log_msg, sizeof(log_msg), "COPY %s (original still valid)", name);
    checker_log(log_msg);
    
    return true;
}

void checker_drop(const char* name) {
    VarInfo* var = find_var(name);
    if (var && !var->consumed) {
        checker_consume(name);
    }
}


// INTERPRETER OPERATIONS

// Create new heap value (affine type)
void op_new(const char* var_name, int value) {
    int addr = memory_alloc(value);
    Type type = { .kind = TYPE_AFFINE };
    checker_declare(var_name, type, addr);
}

// Move variable (consumes source)
void op_move(const char* dst, const char* src) {
    VarInfo* src_var = find_var(src);
    
    if (src_var == NULL) {
        return;
    }
    
    if (src_var->type.kind == TYPE_AFFINE) {
        if (!checker_consume(src)) {
            return;
        }
    }
    
    checker_declare(dst, src_var->type, src_var->value);
}

// Copy variable (doesn't consume source)
void op_copy(const char* dst, const char* src) {
    VarInfo* src_var = find_var(src);
    
    if (src_var == NULL || !checker_copy(src)) {
        return;
    }
    
    // Copy the heap value
    int old_addr = src_var->value;
    int old_value = memory_read(old_addr);
    int new_addr = memory_alloc(old_value);
    
    Type type = { .kind = TYPE_AFFINE };
    checker_declare(dst, type, new_addr);
}

// Print variable
void op_print(const char* var_name) {
    VarInfo* var = find_var(var_name);
    
    if (var == NULL || !checker_check_use(var_name)) {
        return;
    }
    
    int value;
    if (var->type.kind == TYPE_AFFINE) {
        value = memory_read(var->value);
    } else {
        value = var->value;
    }
    
    printf("    OUTPUT: %d\n", value);
}

// Drop variable (free memory)
void op_drop(const char* var_name) {
    VarInfo* var = find_var(var_name);
    
    if (var == NULL) {
        return;
    }
    
    if (var->type.kind == TYPE_AFFINE) {
        memory_free(var->value);
    }
    
    checker_drop(var_name);
}

// Arithmetic (reads values, doesn't consume unless affine)
void op_add(const char* result_name, const char* a_name, const char* b_name) {
    VarInfo* a = find_var(a_name);
    VarInfo* b = find_var(b_name);
    
    if (a == NULL || b == NULL) {
        return;
    }
    
    if (!checker_check_use(a_name) || !checker_check_use(b_name)) {
        return;
    }
    
    int a_val = (a->type.kind == TYPE_AFFINE) ? memory_read(a->value) : a->value;
    int b_val = (b->type.kind == TYPE_AFFINE) ? memory_read(b->value) : b->value;
    
    Type type = { .kind = TYPE_VALUE };
    checker_declare(result_name, type, a_val + b_val);
}


// EXAMPLES

void example_basic() {
    printf("\n--------------------------------------------------\n");
    printf("EXAMPLE 1: Basic Affine Types\n");
    printf("--------------------------------------------------\n");
    
    memory_init();
    checker_init();
    
    checker.current_line = 1;
    printf("\n  Line 1: let x = new(42)\n");
    op_new("x", 42);
    
    checker.current_line = 2;
    printf("\n  Line 2: let y = x (move)\n");
    op_move("y", "x");
    
    checker.current_line = 3;
    printf("\n  Line 3: print(y)\n");
    op_print("y");
    
    checker.current_line = 4;
    printf("\n  Line 4: drop(y)\n");
    op_drop("y");
    
    printf("--------------------------------------------------\n");
    memory_stats();
    
    if (checker.error_count == 0) {
        printf("\n  No affine type errors!\n");
    } else {
        printf("\n  Found %d affine type errors\n", checker.error_count);
    }
}

void example_use_after_move() {
    printf("\n--------------------------------------------------\n");
    printf("EXAMPLE 2: Use After Move (ERROR)\n");
    printf("--------------------------------------------------\n");
    
    memory_init();
    checker_init();
    
    checker.current_line = 1;
    printf("\n  Line 1: let x = new(100)\n");
    op_new("x", 100);
    
    checker.current_line = 2;
    printf("\n  Line 2: let y = x (move)\n");
    op_move("y", "x");
    
    checker.current_line = 3;
    printf("\n  Line 3: print(y)\n");
    op_print("y");
    
    checker.current_line = 4;
    printf("\n  Line 4: print(x) -- ERROR!\n");
    op_print("x");  // This will error!
    
    printf("--------------------------------------------------\n");
    memory_stats();
    
    if (checker.error_count == 0) {
        printf("\n  No affine type errors!\n");
    } else {
        printf("\n  Found %d affine type errors\n", checker.error_count);
    }
}

void example_copy() {
    printf("\n--------------------------------------------------\n");
    printf("EXAMPLE 3: Explicit Copy\n");
    printf("--------------------------------------------------\n");
    
    memory_init();
    checker_init();
    
    checker.current_line = 1;
    printf("\n  Line 1: let x = new(42)\n");
    op_new("x", 42);
    
    checker.current_line = 2;
    printf("\n  Line 2: let y = copy(x)\n");
    op_copy("y", "x");
    
    checker.current_line = 3;
    printf("\n  Line 3: print(x)\n");
    op_print("x");
    
    checker.current_line = 4;
    printf("\n  Line 4: print(y)\n");
    op_print("y");
    
    checker.current_line = 5;
    printf("\n  Line 5: drop(x)\n");
    op_drop("x");
    
    checker.current_line = 6;
    printf("\n  Line 6: drop(y)\n");
    op_drop("y");
    
    printf("--------------------------------------------------\n");
    memory_stats();
    
    if (checker.error_count == 0) {
        printf("\n  No affine type errors!\n");
    } else {
        printf("\n  Found %d affine type errors\n", checker.error_count);
    }
}

void example_arithmetic() {
    printf("\n--------------------------------------------------\n");
    printf("EXAMPLE 4: Arithmetic\n");
    printf("--------------------------------------------------\n");
    
    memory_init();
    checker_init();
    
    checker.current_line = 1;
    printf("\n  Line 1: let x = new(10)\n");
    op_new("x", 10);
    
    checker.current_line = 2;
    printf("\n  Line 2: let y = new(20)\n");
    op_new("y", 20);
    
    checker.current_line = 3;
    printf("\n  Line 3: let sum = x + y\n");
    op_add("sum", "x", "y");
    
    checker.current_line = 4;
    printf("\n  Line 4: print(sum)\n");
    op_print("sum");
    
    checker.current_line = 5;
    printf("\n  Line 5: drop(x)\n");
    op_drop("x");
    
    checker.current_line = 6;
    printf("\n  Line 6: drop(y)\n");
    op_drop("y");
    
    printf("--------------------------------------------------\n");
    memory_stats();
    
    if (checker.error_count == 0) {
        printf("\n  No affine type errors!\n");
    } else {
        printf("\n  Found %d affine type errors\n", checker.error_count);
    }
}

void example_memory_leak() {
    printf("\n--------------------------------------------------\n");
    printf("EXAMPLE 5: Memory Leak (no drop)\n");
    printf("--------------------------------------------------\n");
    
    memory_init();
    checker_init();
    
    checker.current_line = 1;
    printf("\n  Line 1: let x = new(42)\n");
    op_new("x", 42);
    
    checker.current_line = 2;
    printf("\n  Line 2: print(x)\n");
    op_print("x");
    
    printf("\n  (forgot to drop x - memory leak!)\n");
    
    printf("--------------------------------------------------\n");
    memory_stats();
    
    if (checker.error_count == 0) {
        printf("\n  No affine type errors!\n");
    } else {
        printf("\n  Found %d affine type errors\n", checker.error_count);
    }
}


// MAIN

int main() {
    example_basic();
    example_use_after_move();
    example_copy();
    example_arithmetic();
    example_memory_leak();
    
    printf("\n--------------------------------------------------\n");
    printf("Key Concepts Demonstrated:\n");
    printf("--------------------------------------------------\n");
    printf(" Affine types: values used at most once\n");
    printf(" Move semantics: assignment consumes source\n");
    printf(" Use-after-move detection\n");
    printf(" Explicit copy vs implicit move\n");
    printf(" Memory management tied to ownership\n");
    printf(" Memory leak detection\n\n");
    
    return 0;
}
