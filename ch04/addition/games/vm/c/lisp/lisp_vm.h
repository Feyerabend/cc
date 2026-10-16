#ifndef LISP_VM_H
#define LISP_VM_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <setjmp.h>

// Memory configuration
#ifndef LISP_HEAP_SIZE
#define LISP_HEAP_SIZE          8192  // Number of value cells
#endif
#define LISP_MAX_SYMBOLS        256   // Max unique symbols
#define LISP_NAME_POOL_SIZE     4096  // Bytes for symbol names
#define LISP_TEXT_POOL_SIZE     4096  // Bytes for string literals in source code
#define LISP_STRING_SLOTS       32    // Strings created at run time (number->string)
#define LISP_STRING_SLOT_SIZE   16
#define LISP_MAX_SPRITES        32
#define LISP_SPRITE_MAX_SIZE    32    // Max sprite dimension (32x32)
#define LISP_ERROR_SIZE         96

// Max nesting of eval calls. Each level uses C stack, so this must
// fit the stack the interpreter runs on (see main.c).
#ifndef LISP_MAX_DEPTH
#define LISP_MAX_DEPTH          200
#endif

// Transparent sprite colour (magenta)
#define LISP_TRANSPARENT 0xF81F

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

typedef struct lisp_value lisp_value_t;
typedef struct lisp_vm lisp_vm_t;

// Built-in functions receive their arguments already evaluated, as a list
typedef lisp_value_t *(*lisp_builtin_fn)(lisp_vm_t *vm, lisp_value_t *args);

typedef struct {
    bool in_use;
    uint8_t width;
    uint8_t height;
    uint16_t data[LISP_SPRITE_MAX_SIZE * LISP_SPRITE_MAX_SIZE];
} lisp_sprite_t;

// A tagged union. Every value, including numbers, lives in a heap cell.
struct lisp_value {
    uint8_t type;
    uint8_t marked;
    union {
        int32_t number;
        struct {
            const char *name;
            lisp_value_t *value;   // Global value, NULL when undefined
        } symbol;
        struct {
            lisp_value_t *car;
            lisp_value_t *cdr;
        } cons;
        struct {
            const char *name;
            lisp_builtin_fn fn;
        } builtin;
        struct {
            lisp_value_t *params;  // List of parameter symbols
            lisp_value_t *body;    // List of body expressions
            lisp_value_t *env;     // Captured local environment
        } lambda;
        struct {
            const char *text;
            int16_t slot;          // Run-time string slot, -1 for literals
        } string;
        lisp_sprite_t *sprite;
        lisp_value_t *next_free;   // Used while the cell is on the free list
    } as;
};

struct lisp_vm {
    // Cell heap with a free list and a mark-sweep collector
    lisp_value_t heap[LISP_HEAP_SIZE];
    lisp_value_t *free_list;
    size_t cells_used;
    uint32_t gc_count;
    lisp_value_t nil;              // The empty list, not part of the heap

    // Interned symbols; each symbol also holds its global value
    lisp_value_t *symbols[LISP_MAX_SYMBOLS];
    size_t symbol_count;
    char name_pool[LISP_NAME_POOL_SIZE];
    size_t name_pool_used;

    // String storage
    char text_pool[LISP_TEXT_POOL_SIZE];
    size_t text_pool_used;
    char string_slots[LISP_STRING_SLOTS][LISP_STRING_SLOT_SIZE];
    bool string_slot_used[LISP_STRING_SLOTS];

    lisp_sprite_t sprites[LISP_MAX_SPRITES];

    // Symbols for the special forms, compared by pointer in eval
    lisp_value_t *s_quote, *s_if, *s_cond, *s_else, *s_when, *s_and, *s_or;
    lisp_value_t *s_begin, *s_let, *s_define, *s_set, *s_lambda, *s_while;

    // Game callbacks, set from Lisp (see lisp_game.c)
    lisp_value_t *on_update;
    lisp_value_t *on_button[4];    // A, B, X, Y
    bool running;

    // Errors longjmp back to the active top-level call
    jmp_buf *error_jmp;
    int depth;
    char error[LISP_ERROR_SIZE];

    // Start of the C stack region scanned by the collector
    void *stack_base;
};

// Type tests
#define IS_NIL(v)     ((v)->type == LISP_NIL)
#define IS_NUMBER(v)  ((v)->type == LISP_NUMBER)
#define IS_SYMBOL(v)  ((v)->type == LISP_SYMBOL)
#define IS_CONS(v)    ((v)->type == LISP_CONS)
#define IS_BUILTIN(v) ((v)->type == LISP_BUILTIN)
#define IS_LAMBDA(v)  ((v)->type == LISP_LAMBDA)
#define IS_STRING(v)  ((v)->type == LISP_STRING)
#define IS_SPRITE(v)  ((v)->type == LISP_SPRITE)

// Setup. The VM is large, so make it a static or global variable.
void lisp_init(lisp_vm_t *vm);
void lisp_register_builtins(lisp_vm_t *vm);
void lisp_define_builtin(lisp_vm_t *vm, const char *name, lisp_builtin_fn fn);
void lisp_define(lisp_vm_t *vm, const char *name, lisp_value_t *value);

// Top level entry points. They catch errors: on error they return NULL
// and leave a message in lisp_error(vm).
// lisp_run evaluates every expression in source and returns the last value.
// lisp_call calls a function with no arguments.
// A returned value is only safe to use until the next call into the VM.
lisp_value_t *lisp_run(lisp_vm_t *vm, const char *source);
lisp_value_t *lisp_call(lisp_vm_t *vm, lisp_value_t *fn);
const char *lisp_error(lisp_vm_t *vm);

// Garbage collection runs by itself when the heap is full
void lisp_gc(lisp_vm_t *vm);

// Raise an error from inside evaluation (does not return)
void lisp_fail(lisp_vm_t *vm, const char *fmt, ...);

// Construction
lisp_value_t *lisp_number(lisp_vm_t *vm, int32_t n);
lisp_value_t *lisp_symbol(lisp_vm_t *vm, const char *name, size_t len);
lisp_value_t *lisp_cons(lisp_vm_t *vm, lisp_value_t *car, lisp_value_t *cdr);
lisp_value_t *lisp_string(lisp_vm_t *vm, const char *text);
lisp_value_t *lisp_bool(lisp_vm_t *vm, bool b);
lisp_value_t *lisp_nil(lisp_vm_t *vm);
lisp_value_t *lisp_make_sprite(lisp_vm_t *vm, int32_t w, int32_t h);

// Access
lisp_value_t *lisp_car(lisp_vm_t *vm, lisp_value_t *v);
lisp_value_t *lisp_cdr(lisp_vm_t *vm, lisp_value_t *v);
lisp_value_t *lisp_nth(lisp_vm_t *vm, lisp_value_t *list, size_t n);
size_t lisp_length(lisp_value_t *list);
int32_t lisp_to_int(lisp_vm_t *vm, lisp_value_t *v);
bool lisp_truthy(lisp_value_t *v);

// Evaluation
lisp_value_t *lisp_eval(lisp_vm_t *vm, lisp_value_t *expr, lisp_value_t *env);
lisp_value_t *lisp_apply(lisp_vm_t *vm, lisp_value_t *fn, lisp_value_t *args);

// Printing to stdout
void lisp_print(lisp_value_t *v);

#endif // LISP_VM_H
