#ifndef EVENTSCRIPT_H
#define EVENTSCRIPT_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

/* AST */

typedef enum {
    AST_NUMBER,
    AST_STRING,
    AST_IDENTIFIER,
    AST_BINARY_OP,
    AST_PRINT,
    AST_EVENT_EMIT,
    AST_EVENT_ON,
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
        // Literals
        struct { int value; } number;
        struct { char *value; } string;
        struct { char *name; } identifier;
        
        // Binary operation
        struct {
            BinaryOp op;
            ASTNode *left;
            ASTNode *right;
        } binary;
        
        // Print statement
        struct { ASTNode *expr; } print;
        
        // Event emit: emit "event_name", data
        struct {
            char *event_name;
            ASTNode *data;
        } emit;
        
        // Event handler: on "event_name" { ... }
        struct {
            char *event_name;
            ASTNode *body;
        } on;
        
        // Function definition: fn name(params) { body }
        struct {
            char *name;
            char **params;
            size_t param_count;
            ASTNode *body;
        } function;
        
        // Function call
        struct {
            char *name;
            ASTNode **args;
            size_t arg_count;
        } call;
        
        // Block of statements
        struct {
            ASTNode **statements;
            size_t count;
        } block;
        
        // Program (top-level)
        struct {
            ASTNode **statements;
            size_t count;
        } program;
    };
};

/* Bytecode + VM */

typedef enum {
    OP_CONST,       // Push constant
    OP_ADD_OP,      // Add top two stack values
    OP_SUB_OP,      // Subtract
    OP_MUL_OP,      // Multiply
    OP_DIV_OP,      // Divide
    OP_PRINT_OP,    // Print top of stack
    OP_EMIT,        // Emit event (event_name, data)
    OP_REGISTER,    // Register event handler
    OP_CALL_FN,     // Call function
    OP_RETURN,      // Return from function
    OP_HALT,        // Stop execution
    OP_LOAD,        // Load variable
    OP_STORE,       // Store variable
    OP_POP          // Pop stack
} OpCode;

typedef enum {
    VAL_NUMBER,
    VAL_STRING,
    VAL_HANDLER,    // Event handler (function pointer)
    VAL_NIL
} ValueType;

typedef struct {
    ValueType type;
    union {
        int number;
        char *string;
        size_t handler_pc;  // Program counter for handler
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

/* Event Handler Registry */
typedef struct EventHandler {
    char *event_name;
    size_t handler_pc;  // Bytecode position
    struct EventHandler *next;
} EventHandler;

/* Virtual Machine */
typedef struct {
    Bytecode *bytecode;
    Value stack[256];
    int sp;  // Stack pointer
    size_t pc;  // Program counter
    
    // Event system
    EventQueueEntry *event_queue_head;
    EventQueueEntry *event_queue_tail;
    EventHandler *handlers;
    
    // Variable storage (simple global vars)
    struct {
        char *name;
        Value value;
    } globals[64];
    size_t global_count;
    
    bool running;
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
void vm_event_loop(VM *vm);  // Process event queue

// Helper
void value_print(Value v);
const char *opcode_name(OpCode op);

#endif // EVENTSCRIPT_H
