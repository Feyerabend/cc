#ifndef PL0_H
#define PL0_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>

/* Forward declarations */
typedef struct ASTNode ASTNode;
typedef struct Visitor Visitor;
typedef struct Scope Scope;

/* Token kinds */
typedef enum {
    TOK_NUM,
    TOK_OP,
    TOK_WS,
    TOK_KW,
    TOK_ID,
    TOK_SEMI,
    TOK_ASGN,
    TOK_COMMA,
    TOK_EOF
} TokenKind;

/* Token structure */
typedef struct {
    char token[256];
    TokenKind kind;
} Token;

/* Token Iterator */
typedef struct TokenIterator {
    struct PL0Lexer* lexer;
    Token current;
    bool has_next;
} TokenIterator;

/* Lexer */
typedef struct PL0Lexer {
    char* code;
    int position;
    TokenIterator* iterator;
} PL0Lexer;

/* AST Node types */
typedef enum {
    NODE_BLOCK,
    NODE_ASSIGN,
    NODE_CALL,
    NODE_READ,
    NODE_WRITE,
    NODE_COMPOUND,
    NODE_IF,
    NODE_WHILE,
    NODE_OPERATION,
    NODE_VARIABLE,
    NODE_NUMBER
} NodeType;

/* AST Node base structure */
struct ASTNode {
    NodeType type;
    void* data;
    void* (*accept)(struct ASTNode*, Visitor*);
};

/* Specific node data structures */
typedef struct {
    char** variables;
    int var_count;
    struct {
        char* name;
        ASTNode* body;
    }* procedures;
    int proc_count;
    ASTNode* statement;
} BlockData;

typedef struct {
    char* var_name;
    ASTNode* expression;
} AssignData;

typedef struct {
    char* proc_name;
} CallData;

typedef struct {
    char* var_name;
} ReadData;

typedef struct {
    ASTNode* expression;
} WriteData;

typedef struct {
    ASTNode** statements;
    int count;
} CompoundData;

typedef struct {
    ASTNode* condition;
    ASTNode* then_statement;
} IfData;

typedef struct {
    ASTNode* condition;
    ASTNode* body;
} WhileData;

typedef struct {
    char operator;
    ASTNode* left;
    ASTNode* right;
} OperationData;

typedef struct {
    char* name;
} VariableData;

typedef struct {
    int value;
} NumberData;

/* Scope structure */
typedef struct ScopeVar {
    char* name;
    int value;
    struct ScopeVar* next;
} ScopeVar;

typedef struct ScopeProc {
    char* name;
    ASTNode* body;
    Scope* def_scope;
    struct ScopeProc* next;
} ScopeProc;

struct Scope {
    Scope* parent;
    ScopeVar* variables;
    ScopeProc* procedures;
};

/* Visitor interface */
struct Visitor {
    void* context;
    void* (*visit_block)(Visitor*, ASTNode*);
    void* (*visit_assign)(Visitor*, ASTNode*);
    void* (*visit_call)(Visitor*, ASTNode*);
    void* (*visit_read)(Visitor*, ASTNode*);
    void* (*visit_write)(Visitor*, ASTNode*);
    void* (*visit_compound)(Visitor*, ASTNode*);
    void* (*visit_if)(Visitor*, ASTNode*);
    void* (*visit_while)(Visitor*, ASTNode*);
    void* (*visit_operation)(Visitor*, ASTNode*);
    void* (*visit_variable)(Visitor*, ASTNode*);
    void* (*visit_number)(Visitor*, ASTNode*);
};

/* Interpreter context */
typedef struct {
    Scope* scope;
} InterpreterContext;

/* AST Builder */
typedef struct {
    TokenIterator* iterator;
} ASTBuilder;

/* Function declarations */

/* Lexer functions */
PL0Lexer* lexer_create(const char* code);
void lexer_destroy(PL0Lexer* lexer);
bool lexer_next_token(PL0Lexer* lexer);
TokenIterator* lexer_get_iterator(PL0Lexer* lexer);

/* Token Iterator functions */
bool iterator_next(TokenIterator* iter, const char* expected_kind, const char* when_token);

/* AST Builder functions */
ASTBuilder* builder_create(PL0Lexer* lexer);
void builder_destroy(ASTBuilder* builder);
ASTNode* builder_build(ASTBuilder* builder);
ASTNode* builder_build_block(ASTBuilder* builder);
ASTNode* builder_build_statement(ASTBuilder* builder);
ASTNode* builder_build_expression(ASTBuilder* builder, const char* operators, ASTNode* (*term_builder)(ASTBuilder*));
ASTNode* builder_build_term(ASTBuilder* builder);
ASTNode* builder_build_factor(ASTBuilder* builder);

/* AST Node creation functions */
ASTNode* node_create_block(char** variables, int var_count, 
                           void* procedures, int proc_count, 
                           ASTNode* statement);
ASTNode* node_create_assign(const char* var_name, ASTNode* expression);
ASTNode* node_create_call(const char* proc_name);
ASTNode* node_create_read(const char* var_name);
ASTNode* node_create_write(ASTNode* expression);
ASTNode* node_create_compound(ASTNode** statements, int count);
ASTNode* node_create_if(ASTNode* condition, ASTNode* then_statement);
ASTNode* node_create_while(ASTNode* condition, ASTNode* body);
ASTNode* node_create_operation(char operator, ASTNode* left, ASTNode* right);
ASTNode* node_create_variable(const char* name);
ASTNode* node_create_number(int value);
void node_destroy(ASTNode* node);

/* Scope functions */
Scope* scope_create(Scope* parent);
void scope_destroy(Scope* scope);
void scope_add_variable(Scope* scope, const char* name, int value);
void scope_add_procedure(Scope* scope, const char* name, ASTNode* body, Scope* def_scope);
ScopeVar* scope_find_variable(Scope* scope, const char* name);
ScopeProc* scope_find_procedure(Scope* scope, const char* name);

/* Interpreter functions */
Visitor* interpreter_create(void);
void interpreter_destroy(Visitor* visitor);
void interpreter_interpret(Visitor* visitor, ASTNode* ast);

/* Visitor implementations */
void* visit_block_impl(Visitor* v, ASTNode* node);
void* visit_assign_impl(Visitor* v, ASTNode* node);
void* visit_call_impl(Visitor* v, ASTNode* node);
void* visit_read_impl(Visitor* v, ASTNode* node);
void* visit_write_impl(Visitor* v, ASTNode* node);
void* visit_compound_impl(Visitor* v, ASTNode* node);
void* visit_if_impl(Visitor* v, ASTNode* node);
void* visit_while_impl(Visitor* v, ASTNode* node);
void* visit_operation_impl(Visitor* v, ASTNode* node);
void* visit_variable_impl(Visitor* v, ASTNode* node);
void* visit_number_impl(Visitor* v, ASTNode* node);

/* Utility functions */
bool is_keyword(const char* str);
TokenKind get_token_kind(const char* token);
int apply_operator(char op, int left, int right);

#endif /* PL0_H */
