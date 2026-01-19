#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "compiler.h"


/* ARENA IMPLEMENTATION */

Arena *arena_create(size_t block_size) {
    Arena *arena = malloc(sizeof(Arena));
    if (!arena) return NULL;
    
    arena->default_block_size = block_size;
    arena->current = NULL;
    return arena;
}

static ArenaBlock *arena_block_create(size_t size) {
    ArenaBlock *block = malloc(sizeof(ArenaBlock));
    if (!block) return NULL;
    
    block->memory = malloc(size);
    if (!block->memory) {
        free(block);
        return NULL;
    }
    
    block->capacity = size;
    block->used = 0;
    block->next = NULL;
    return block;
}

void *arena_alloc(Arena *arena, size_t size) {
    // Align to 8 bytes
    size = (size + 7) & ~7;
    
    if (!arena->current || arena->current->used + size > arena->current->capacity) {
        size_t block_size = size > arena->default_block_size ? size : arena->default_block_size;
        ArenaBlock *new_block = arena_block_create(block_size);
        if (!new_block) return NULL;
        
        new_block->next = arena->current;
        arena->current = new_block;
    }
    
    void *ptr = (char*)arena->current->memory + arena->current->used;
    arena->current->used += size;
    return ptr;
}

char *arena_strdup(Arena *arena, const char *str) {
    if (!str) return NULL;
    size_t len = strlen(str) + 1;
    char *copy = arena_alloc(arena, len);
    if (copy) {
        memcpy(copy, str, len);
    }
    return copy;
}

void arena_destroy(Arena *arena) {
    if (!arena) return;
    
    ArenaBlock *block = arena->current;
    while (block) {
        ArenaBlock *next = block->next;
        free(block->memory);
        free(block);
        block = next;
    }
    free(arena);
}


/* TOKEN STREAM IMPLEMENTATION */

TokenStream *token_stream_create(Arena *arena) {
    TokenStream *stream = malloc(sizeof(TokenStream));
    if (!stream) return NULL;
    
    stream->capacity = 256;
    stream->tokens = malloc(sizeof(Token) * stream->capacity);
    if (!stream->tokens) {
        free(stream);
        return NULL;
    }
    
    stream->count = 0;
    stream->position = 0;
    stream->arena = arena;
    return stream;
}

Result token_stream_add(TokenStream *stream, TokenType type, const char *value, int line, int col) {
    if (stream->count >= stream->capacity) {
        stream->capacity *= 2;
        Token *new_tokens = realloc(stream->tokens, sizeof(Token) * stream->capacity);
        if (!new_tokens) {
            return ERROR(ERR_MEMORY, "Failed to expand token stream");
        }
        stream->tokens = new_tokens;
    }
    
    Token *token = &stream->tokens[stream->count++];
    token->type = type;
    token->value = value ? arena_strdup(stream->arena, value) : NULL;
    token->line = line;
    token->column = col;
    
    return OK;
}

Token *token_stream_peek(TokenStream *stream) {
    if (stream->position >= stream->count) {
        static Token eof = {.type = TOKEN_EOF};
        return &eof;
    }
    return &stream->tokens[stream->position];
}

Token *token_stream_next(TokenStream *stream) {
    if (stream->position >= stream->count) {
        static Token eof = {.type = TOKEN_EOF};
        return &eof;
    }
    return &stream->tokens[stream->position++];
}

bool token_stream_match(TokenStream *stream, TokenType type) {
    Token *token = token_stream_peek(stream);
    if (token->type == type) {
        token_stream_next(stream);
        return true;
    }
    return false;
}

bool token_stream_is_eof(TokenStream *stream) {
    return token_stream_peek(stream)->type == TOKEN_EOF;
}


/* AST IMPLEMENTATION */

ASTNode *ast_create_node(Arena *arena, ASTNodeType type, const char *value) {
    ASTNode *node = arena_alloc(arena, sizeof(ASTNode));
    if (!node) return NULL;
    
    node->type = type;
    node->value = value ? arena_strdup(arena, value) : NULL;
    node->symbol_id = -1;
    node->children = NULL;
    node->child_count = 0;
    node->child_capacity = 0;
    node->line = 0;
    node->column = 0;
    
    return node;
}

Result ast_add_child(ASTNode *parent, ASTNode *child) {
    if (!parent || !child) {
        return ERROR(ERR_INVALID_OPERATION, "Cannot add NULL child to AST");
    }
    
    if (parent->child_count >= parent->child_capacity) {
        size_t new_capacity = parent->child_capacity == 0 ? 4 : parent->child_capacity * 2;
        ASTNode **new_children = realloc(parent->children, sizeof(ASTNode*) * new_capacity);
        if (!new_children) {
            return ERROR(ERR_MEMORY, "Failed to expand AST children array");
        }
        parent->children = new_children;
        parent->child_capacity = new_capacity;
    }
    
    parent->children[parent->child_count++] = child;
    return OK;
}

const char *ast_type_name(ASTNodeType type) {
    static const char *names[] = {
        "PROGRAM", "BLOCK", "CONST_DECL", "VAR_DECL", "PROC_DECL",
        "ASSIGNMENT", "CALL", "IF", "WHILE", "CONDITION",
        "BINARY_OP", "UNARY_OP", "IDENTIFIER", "NUMBER"
    };
    return type < sizeof(names)/sizeof(names[0]) ? names[type] : "UNKNOWN";
}

/* SYMBOL TABLE IMPLEMENTATION */

SymbolTable *symbol_table_create(Arena *arena) {
    SymbolTable *table = malloc(sizeof(SymbolTable));
    if (!table) return NULL;
    
    table->arena = arena;
    table->next_id = 1;
    table->global = arena_alloc(arena, sizeof(Scope));
    table->global->name = arena_strdup(arena, "global");
    table->global->symbols = NULL;
    table->global->parent = NULL;
    table->global->next = NULL;
    table->current = table->global;
    
    return table;
}

Scope *symbol_table_enter_scope(SymbolTable *table, const char *name) {
    Scope *scope = arena_alloc(table->arena, sizeof(Scope));
    scope->name = arena_strdup(table->arena, name);
    scope->symbols = NULL;
    scope->parent = table->current;
    scope->next = NULL;
    table->current = scope;
    return scope;
}

void symbol_table_exit_scope(SymbolTable *table) {
    if (table->current && table->current->parent) {
        table->current = table->current->parent;
    }
}

Result symbol_table_add(SymbolTable *table, const char *name, SymbolKind kind, int value) {
    // Check for duplicate in current scope
    Symbol *existing = symbol_table_lookup_local(table, name);
    if (existing) {
        return ERROR(ERR_SEMANTIC, "Symbol already defined in current scope");
    }
    
    Symbol *symbol = arena_alloc(table->arena, sizeof(Symbol));
    symbol->id = table->next_id++;
    symbol->name = arena_strdup(table->arena, name);
    symbol->kind = kind;
    symbol->value = value;
    symbol->next = table->current->symbols;
    table->current->symbols = symbol;
    
    return OK;
}

Symbol *symbol_table_lookup(SymbolTable *table, const char *name) {
    for (Scope *scope = table->current; scope; scope = scope->parent) {
        for (Symbol *sym = scope->symbols; sym; sym = sym->next) {
            if (strcmp(sym->name, name) == 0) {
                return sym;
            }
        }
    }
    return NULL;
}

Symbol *symbol_table_lookup_local(SymbolTable *table, const char *name) {
    for (Symbol *sym = table->current->symbols; sym; sym = sym->next) {
        if (strcmp(sym->name, name) == 0) {
            return sym;
        }
    }
    return NULL;
}

