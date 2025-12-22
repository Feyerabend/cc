#ifndef LISP_VM_H
#define LISP_VM_H

#include <stdint.h>
#include <stdbool.h>
#include "display.h"

// ===== Memory Configuration =====
#define LISP_HEAP_SIZE 8192        // Number of cons cells
#define LISP_SYMBOL_TABLE_SIZE 256 // Max unique symbols
#define LISP_STACK_SIZE 256        // Evaluation stack depth
#define LISP_MAX_SPRITES 32        // Max sprites
#define LISP_SPRITE_MAX_SIZE 32    // Max sprite dimension (32x32)

// ===== Lisp Value Types =====
typedef enum {
    LISP_NIL,
    LISP_NUMBER,
    LISP_SYMBOL,
    LISP_CONS,
    LISP_BUILTIN,
    LISP_LAMBDA,
    LISP_STRING,
    LISP_SPRITE
} lisp_type_t;

// Forward declarations
typedef struct lisp_value lisp_value_t;
typedef lisp_value_t* (*lisp_builtin_fn)(lisp_value_t *args);

// Sprite data structure
typedef struct {
    uint8_t width;
    uint8_t height;
    uint16_t data[LISP_SPRITE_MAX_SIZE * LISP_SPRITE_MAX_SIZE];
} lisp_sprite_t;

// Cons cell - the fundamental building block
typedef struct lisp_cons {
    lisp_value_t *car;
    lisp_value_t *cdr;
} lisp_cons_t;

// Lambda closure
typedef struct {
    lisp_value_t *params;  // List of parameter symbols
    lisp_value_t *body;    // Body expression
    lisp_value_t *env;     // Captured environment (alist)
} lisp_lambda_t;

// Lisp value (tagged union)
struct lisp_value {
    lisp_type_t type;
    uint8_t marked;  // For GC
    union {
        int32_t number;
        uint16_t symbol_id;
        lisp_cons_t cons;
        lisp_builtin_fn builtin;
        lisp_lambda_t lambda;
        const char *string;
        lisp_sprite_t *sprite;
    } as;
};

// ===== Collision Detection =====
typedef struct {
    int16_t x, y;
    uint8_t w, h;
} lisp_rect_t;

// ===== VM State =====
typedef struct {
    // Memory pools
    lisp_value_t heap[LISP_HEAP_SIZE];
    size_t heap_used;
    
    // Symbol table
    const char *symbols[LISP_SYMBOL_TABLE_SIZE];
    size_t symbol_count;
    
    // Evaluation stack
    lisp_value_t *stack[LISP_STACK_SIZE];
    size_t stack_ptr;
    
    // Global environment (association list)
    lisp_value_t *global_env;
    
    // Sprites
    lisp_sprite_t sprites[LISP_MAX_SPRITES];
    size_t sprite_count;
    
    // Game callbacks
    lisp_value_t *on_update;
    lisp_value_t *on_button_callbacks[4];  // A, B, X, Y
    
    // Error state
    const char *error_msg;
    bool running;
} lisp_vm_t;

// ===== Core VM Functions =====
void lisp_init(lisp_vm_t *vm);
void lisp_deinit(lisp_vm_t *vm);

// Memory management
lisp_value_t* lisp_alloc(lisp_vm_t *vm, lisp_type_t type);
void lisp_gc(lisp_vm_t *vm);

// Construction
lisp_value_t* lisp_nil(lisp_vm_t *vm);
lisp_value_t* lisp_number(lisp_vm_t *vm, int32_t n);
lisp_value_t* lisp_symbol(lisp_vm_t *vm, const char *name);
lisp_value_t* lisp_cons(lisp_vm_t *vm, lisp_value_t *car, lisp_value_t *cdr);
lisp_value_t* lisp_string(lisp_vm_t *vm, const char *str);
lisp_value_t* lisp_builtin(lisp_vm_t *vm, lisp_builtin_fn fn);

// List operations
lisp_value_t* lisp_car(lisp_value_t *cons);
lisp_value_t* lisp_cdr(lisp_value_t *cons);
size_t lisp_length(lisp_value_t *list);
lisp_value_t* lisp_nth(lisp_value_t *list, size_t n);

// Parsing
lisp_value_t* lisp_parse(lisp_vm_t *vm, const char **code);

// Evaluation
lisp_value_t* lisp_eval(lisp_vm_t *vm, lisp_value_t *expr, lisp_value_t *env);
lisp_value_t* lisp_apply(lisp_vm_t *vm, lisp_value_t *fn, lisp_value_t *args, lisp_value_t *env);

// Environment
lisp_value_t* lisp_env_lookup(lisp_vm_t *vm, lisp_value_t *env, lisp_value_t *symbol);
lisp_value_t* lisp_env_define(lisp_vm_t *vm, lisp_value_t *env, lisp_value_t *symbol, lisp_value_t *value);
lisp_value_t* lisp_env_set(lisp_vm_t *vm, lisp_value_t *env, lisp_value_t *symbol, lisp_value_t *value);

// ===== Game-Specific Functions =====

// Sprite management
lisp_sprite_t* lisp_create_sprite(lisp_vm_t *vm, uint8_t w, uint8_t h, const uint16_t *data);
void lisp_draw_sprite(lisp_sprite_t *sprite, int16_t x, int16_t y);

// Collision detection
bool lisp_rect_collide(lisp_rect_t *a, lisp_rect_t *b);
bool lisp_point_in_rect(int16_t px, int16_t py, lisp_rect_t *rect);

// Game loop
void lisp_run_game(lisp_vm_t *vm);
void lisp_stop_game(lisp_vm_t *vm);
void lisp_update(lisp_vm_t *vm);  // Called every frame

// ===== Built-in Functions =====

// Graphics
lisp_value_t* lisp_builtin_clear(lisp_vm_t *vm, lisp_value_t *args);
lisp_value_t* lisp_builtin_fill_rect(lisp_vm_t *vm, lisp_value_t *args);
lisp_value_t* lisp_builtin_draw_text(lisp_vm_t *vm, lisp_value_t *args);
lisp_value_t* lisp_builtin_draw_sprite(lisp_vm_t *vm, lisp_value_t *args);

// Sprites
lisp_value_t* lisp_builtin_make_sprite(lisp_vm_t *vm, lisp_value_t *args);
lisp_value_t* lisp_builtin_sprite_set_pixel(lisp_vm_t *vm, lisp_value_t *args);

// Collision
lisp_value_t* lisp_builtin_collide(lisp_vm_t *vm, lisp_value_t *args);

// Math
lisp_value_t* lisp_builtin_add(lisp_vm_t *vm, lisp_value_t *args);
lisp_value_t* lisp_builtin_sub(lisp_vm_t *vm, lisp_value_t *args);
lisp_value_t* lisp_builtin_mul(lisp_vm_t *vm, lisp_value_t *args);
lisp_value_t* lisp_builtin_div(lisp_vm_t *vm, lisp_value_t *args);
lisp_value_t* lisp_builtin_lt(lisp_vm_t *vm, lisp_value_t *args);
lisp_value_t* lisp_builtin_gt(lisp_vm_t *vm, lisp_value_t *args);
lisp_value_t* lisp_builtin_eq(lisp_vm_t *vm, lisp_value_t *args);

// Control
lisp_value_t* lisp_builtin_start(lisp_vm_t *vm, lisp_value_t *args);
lisp_value_t* lisp_builtin_stop(lisp_vm_t *vm, lisp_value_t *args);

// Utilities
void lisp_print(lisp_value_t *value);
const char* lisp_type_name(lisp_type_t type);

#endif // LISP_VM_H