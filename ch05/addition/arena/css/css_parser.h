// css_parser.h
#ifndef CSS_PARSER_H
#define CSS_PARSER_H

#include "arena.h"
#include <stdbool.h>

typedef enum {
    TOK_SELECTOR,
    TOK_LBRACE,
    TOK_RBRACE,
    TOK_PROPERTY,
    TOK_COLON,
    TOK_VALUE,
    TOK_SEMICOLON,
    TOK_EOF,
    TOK_ERROR
} TokenType;

typedef struct {
    TokenType type;
    char *value;
} Token;

typedef struct {
    char *property;
    char *value;
} CSSDeclaration;

typedef struct CSSRule {
    char *selector;
    CSSDeclaration *declarations;
    int decl_count;
    struct CSSRule *next;
} CSSRule;

typedef struct {
    const char *input;
    size_t pos;
    size_t length;
    Arena *arena;
} Lexer;

typedef struct {
    CSSRule *first_rule;
    CSSRule *last_rule;
    Arena *arena;
} CSSStylesheet;

Lexer* lexer_create(const char *input, Arena *arena);
Token lexer_next_token(Lexer *lexer);
void skip_whitespace(Lexer *lexer);

CSSStylesheet* stylesheet_create(Arena *arena);
CSSRule* parse_rule(Lexer *lexer);
void parse_stylesheet(Lexer *lexer, CSSStylesheet *sheet);
void stylesheet_print(CSSStylesheet *sheet);

#endif
