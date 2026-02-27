#ifndef EVENTSCRIPT_H
#define EVENTSCRIPT_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <time.h>
#include <sys/time.h>

/* AST */

typedef enum {
    AST_NUMBER,
    AST_STRING,
    AST_IDENTIFIER,
    AST_BINARY_OP,
    AST_PRINT,
    AST_EVENT_EMIT,
    AST_EVENT_ON,
    AST_TIMER_AFTER,
    AST_FUNCTION,
    AST_CALL,
    AST_BLOCK,
    AST_PROGRAM
} ASTNodeType;

typedef enum {
    OP_ADD,
    OP_SUB,
    OP_MUL,
    OP_DIV,
    OP_EQ,
    OP_LT,
    OP_GT
} BinaryOp;

typedef struct ASTNode ASTNode;

struct ASTNode {
    ASTNodeType type;
    union {
        struct { int value; } number;
        struct { char *value; } string;
        struct { char *name; } identifier;
        
        struct {
            BinaryOp op;
            ASTNode *left;
            ASTNode *right;
        } binary;
        
        struct { ASTNode *expr; } print;
        
        struct {
            char *event_name;
            ASTNode *data;
        } emit;
        
        struct {
            char *event_name;
            ASTNode *body;
        } on;
        
        struct {
            int delay_ms;
            char *event_name;
            ASTNode *data;
        } timer;
        
        struct {
            char *name;
            char **params;
            size_t param_count;
            ASTNode *body;
        } function;
        
        struct {
            char *name;
            ASTNode **args;
            size_t arg_count;
        } call;
        
        struct {
            ASTNode **statements;
            size_t count;
        } block;
        
        struct {
            ASTNode **statements;
            size_t count;
        } program;
    };
};

/* Bytecode + VM */

typedef enum {
    OP_CONST,
    OP_ADD_OP,
    OP_SUB_OP,
    OP_MUL_OP,
    OP_DIV_OP,
    OP_PRINT_OP,
    OP_EMIT,
    OP_REGISTER,
    OP_TIMER,
    OP_CALL_FN,
    OP_RETURN,
    OP_HALT,
    OP_LOAD,
    OP_STORE,
    OP_POP
} OpCode;

typedef enum {
    VAL_NUMBER,
    VAL_STRING,
    VAL_HANDLER,
    VAL_NIL
} ValueType;

typedef struct {
    ValueType type;
    union {
        int number;
        char *string;
        size_t handler_pc;
    };
} Value;

typedef struct {
    uint8_t *code;
    size_t size;
    size_t capacity;
    Value *constants;
    size_t const_count;
    size_t const_capacity;
} Bytecode;

/* Event Queue Entry */
typedef struct EventQueueEntry {
    char *event_name;
    Value data;
    struct EventQueueEntry *next;
} EventQueueEntry;

/* Timer Entry */
typedef struct TimerEntry {
    char *event_name;
    Value data;
    struct timeval trigger_time;
    struct TimerEntry *next;
} TimerEntry;

/* Event Handler Registry */
typedef struct EventHandler {
    char *event_name;
    size_t handler_pc;
    struct EventHandler *next;
} EventHandler;

/* Virtual Machine */
typedef struct {
    Bytecode *bytecode;
    Value stack[256];
    int sp;
    size_t pc;
    
    // Event system
    EventQueueEntry *event_queue_head;
    EventQueueEntry *event_queue_tail;
    EventHandler *handlers;
    
    // NEW: Timer system
    TimerEntry *timers;
    
    // Variable storage
    struct {
        char *name;
        Value value;
    } globals[64];
    size_t global_count;
    
    bool running;
    bool loop_active;
} VM;

/* API */

// AST construction
ASTNode *ast_number(int value);
ASTNode *ast_string(const char *str);
ASTNode *ast_identifier(const char *name);
ASTNode *ast_binary(BinaryOp op, ASTNode *left, ASTNode *right);
ASTNode *ast_print(ASTNode *expr);
ASTNode *ast_emit(const char *event_name, ASTNode *data);
ASTNode *ast_on(const char *event_name, ASTNode *body);
ASTNode *ast_timer(int delay_ms, const char *event_name, ASTNode *data);  // NEW
ASTNode *ast_block(ASTNode **statements, size_t count);
ASTNode *ast_program(ASTNode **statements, size_t count);
void ast_free(ASTNode *node);

// Bytecode & Compiler
Bytecode *bytecode_create(void);
void bytecode_free(Bytecode *bc);
void bytecode_write(Bytecode *bc, uint8_t byte);
size_t bytecode_add_constant(Bytecode *bc, Value value);
void compile(ASTNode *ast, Bytecode *bc);

// VM
VM *vm_create(Bytecode *bc);
void vm_free(VM *vm);
void vm_run(VM *vm);
void vm_event_loop(VM *vm);
void vm_event_loop_forever(VM *vm);

// Helper
void value_print(Value v);
const char *opcode_name(OpCode op);

#endif // EVENTSCRIPT_H
