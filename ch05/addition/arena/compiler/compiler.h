#ifndef COMPILER_REFACTOR_H
#define COMPILER_REFACTOR_H

#include <stddef.h>
#include <stdbool.h>


/* ERROR HANDLING */

typedef enum {
    ERR_NONE = 0,
    ERR_MEMORY,
    ERR_FILE_IO,
    ERR_SYNTAX,
    ERR_SEMANTIC,
    ERR_UNDEFINED_SYMBOL,
    ERR_TYPE_MISMATCH,
    ERR_INVALID_OPERATION
} ErrorCode;

typedef struct {
    ErrorCode code;
    char message[256];
    int line;
    int column;
} CompilerError;

typedef struct {
    bool has_error;
    CompilerError error;
} Result;

#define OK ((Result){.has_error = false})
#define ERROR(code, msg) ((Result){.has_error = true, .error = {code, msg, 0, 0}})


/* MEMORY ARENA */

typedef struct ArenaBlock {
    void *memory;
    size_t used;
    size_t capacity;
    struct ArenaBlock *next;
} ArenaBlock;

typedef struct {
    ArenaBlock *current;
    size_t default_block_size;
} Arena;

Arena *arena_create(size_t block_size);
void *arena_alloc(Arena *arena, size_t size);
char *arena_strdup(Arena *arena, const char *str);
void arena_destroy(Arena *arena);


/* TOKEN STREAM (replaces global token array) */

typedef enum {
    TOKEN_NOP,
    TOKEN_IDENT,
    TOKEN_NUMBER,
    TOKEN_LPAREN,
    TOKEN_RPAREN,
    TOKEN_TIMES,
    TOKEN_SLASH,
    TOKEN_PLUS,
    TOKEN_MINUS,
    TOKEN_EQL,
    TOKEN_NEQ,
    TOKEN_LSS,
    TOKEN_LEQ,
    TOKEN_GTR,
    TOKEN_GEQ,
    TOKEN_CALL,
    TOKEN_BEGIN,
    TOKEN_SEMICOLON,
    TOKEN_END,
    TOKEN_IF,
    TOKEN_WHILE,
    TOKEN_BECOMES,
    TOKEN_THEN,
    TOKEN_DO,
    TOKEN_CONST,
    TOKEN_COMMA,
    TOKEN_VAR,
    TOKEN_PROCEDURE,
    TOKEN_PERIOD,
    TOKEN_EOF
} TokenType;

typedef struct {
    TokenType type;
    char *value;
    int line;
    int column;
} Token;

typedef struct {
    Token *tokens;
    size_t count;
    size_t capacity;
    size_t position;
    Arena *arena;
} TokenStream;

TokenStream *token_stream_create(Arena *arena);
Result token_stream_add(TokenStream *stream, TokenType type, const char *value, int line, int col);
Token *token_stream_peek(TokenStream *stream);
Token *token_stream_next(TokenStream *stream);
bool token_stream_match(TokenStream *stream, TokenType type);
bool token_stream_is_eof(TokenStream *stream);


/* AST (with arena allocation) */

typedef enum {
    AST_PROGRAM,
    AST_BLOCK,
    AST_CONST_DECL,
    AST_VAR_DECL,
    AST_PROC_DECL,
    AST_ASSIGNMENT,
    AST_CALL,
    AST_IF,
    AST_WHILE,
    AST_CONDITION,
    AST_BINARY_OP,
    AST_UNARY_OP,
    AST_IDENTIFIER,
    AST_NUMBER
} ASTNodeType;

typedef struct ASTNode {
    ASTNodeType type;
    char *value;
    int symbol_id;
    struct ASTNode **children;
    size_t child_count;
    size_t child_capacity;
    int line;
    int column;
} ASTNode;

ASTNode *ast_create_node(Arena *arena, ASTNodeType type, const char *value);
Result ast_add_child(ASTNode *parent, ASTNode *child);
const char *ast_type_name(ASTNodeType type);


/* PARSER (with better/proper error handling) */

typedef struct {
    TokenStream *tokens;
    Arena *arena;
    CompilerError last_error;
} Parser;

Parser *parser_create(TokenStream *tokens, Arena *arena);
ASTNode *parser_parse_program(Parser *parser, Result *result);
void parser_destroy(Parser *parser);


/* SYMBOL TABLE (improved structure) */

typedef enum {
    SYMBOL_CONST,
    SYMBOL_VAR,
    SYMBOL_PROCEDURE
} SymbolKind;

typedef struct Symbol {
    int id;
    char *name;
    SymbolKind kind;
    int value;  // for constants
    struct Symbol *next;
} Symbol;

typedef struct Scope {
    char *name;
    Symbol *symbols;
    struct Scope *parent;
    struct Scope *next;  // for procedure scopes
} Scope;

typedef struct {
    Scope *global;
    Scope *current;
    Arena *arena;
    int next_id;
} SymbolTable;

SymbolTable *symbol_table_create(Arena *arena);
Scope *symbol_table_enter_scope(SymbolTable *table, const char *name);
void symbol_table_exit_scope(SymbolTable *table);
Result symbol_table_add(SymbolTable *table, const char *name, SymbolKind kind, int value);
Symbol *symbol_table_lookup(SymbolTable *table, const char *name);
Symbol *symbol_table_lookup_local(SymbolTable *table, const char *name);


/* TAC GENERATION (with arena allocation) */

typedef enum {
    TAC_LABEL,
    TAC_ASSIGN,
    TAC_BINARY_OP,
    TAC_UNARY_OP,
    TAC_LOAD,
    TAC_GOTO,
    TAC_IF_FALSE,
    TAC_CALL,
    TAC_RETURN
} TACOpcode;

typedef struct TACInstruction {
    TACOpcode opcode;
    char *op;       // operator string for binary/unary ops
    char *arg1;
    char *arg2;
    char *result;
    struct TACInstruction *next;
} TACInstruction;

typedef struct {
    TACInstruction *head;
    TACInstruction *tail;
    Arena *arena;
    int temp_counter;
    int label_counter;
} TACGenerator;

TACGenerator *tac_create(Arena *arena);
char *tac_new_temp(TACGenerator *gen);
char *tac_new_label(TACGenerator *gen);
void tac_emit(TACGenerator *gen, TACOpcode opcode, const char *op, 
              const char *arg1, const char *arg2, const char *result);
Result tac_generate_from_ast(TACGenerator *gen, ASTNode *node, SymbolTable *symtab);


/* COMPILER CONTEXT (encapsulates all components) */

typedef struct {
    Arena *arena;
    TokenStream *tokens;
    Parser *parser;
    ASTNode *ast;
    SymbolTable *symtab;
    TACGenerator *tac;
    CompilerError errors[100];
    size_t error_count;
} CompilerContext;

CompilerContext *compiler_context_create();
Result compiler_compile_file(CompilerContext *ctx, const char *filename);
void compiler_context_destroy(CompilerContext *ctx);

#endif /* COMPILER_REFACTOR_H */
