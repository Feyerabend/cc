// css_parser.c
#include "css_parser.h"
#include <stdio.h>
#include <string.h>
#include <ctype.h>

Lexer* lexer_create(const char *input, Arena *arena) {
    Lexer *lexer = arena_alloc(arena, sizeof(Lexer));
    lexer->input = input;
    lexer->pos = 0;
    lexer->length = strlen(input);
    lexer->arena = arena;
    return lexer;
}

void skip_whitespace(Lexer *lexer) {
    while (lexer->pos < lexer->length) {
        if (isspace(lexer->input[lexer->pos])) {
            lexer->pos++;
        } else if (lexer->pos + 1 < lexer->length && 
                   lexer->input[lexer->pos] == '/' && 
                   lexer->input[lexer->pos + 1] == '*') {
            lexer->pos += 2;
            while (lexer->pos + 1 < lexer->length) {
                if (lexer->input[lexer->pos] == '*' && 
                    lexer->input[lexer->pos + 1] == '/') {
                    lexer->pos += 2;
                    break;
                }
                lexer->pos++;
            }
        } else {
            break;
        }
    }
}

Token lexer_next_token(Lexer *lexer) {
    Token token = {TOK_ERROR, NULL};
    skip_whitespace(lexer);
    
    if (lexer->pos >= lexer->length) {
        token.type = TOK_EOF;
        return token;
    }
    
    char current = lexer->input[lexer->pos];
    
    if (current == '{') {
        token.type = TOK_LBRACE;
        lexer->pos++;
        return token;
    }
    if (current == '}') {
        token.type = TOK_RBRACE;
        lexer->pos++;
        return token;
    }
    if (current == ':') {
        token.type = TOK_COLON;
        lexer->pos++;
        return token;
    }
    if (current == ';') {
        token.type = TOK_SEMICOLON;
        lexer->pos++;
        return token;
    }
    
    size_t start = lexer->pos;
    while (lexer->pos < lexer->length && 
           !isspace(lexer->input[lexer->pos]) &&
           lexer->input[lexer->pos] != '{' &&
           lexer->input[lexer->pos] != '}' &&
           lexer->input[lexer->pos] != ':' &&
           lexer->input[lexer->pos] != ';') {
        lexer->pos++;
    }
    
    if (lexer->pos > start) {
        size_t len = lexer->pos - start;
        token.value = arena_alloc(lexer->arena, len + 1);
        strncpy(token.value, lexer->input + start, len);
        token.value[len] = '\0';
        token.type = TOK_SELECTOR;
        return token;
    }
    
    return token;
}

CSSStylesheet* stylesheet_create(Arena *arena) {
    CSSStylesheet *sheet = arena_alloc(arena, sizeof(CSSStylesheet));
    sheet->first_rule = NULL;
    sheet->last_rule = NULL;
    sheet->arena = arena;
    return sheet;
}

CSSRule* parse_rule(Lexer *lexer) {
    Token token = lexer_next_token(lexer);
    
    if (token.type == TOK_EOF) {
        return NULL;
    }
    
    CSSRule *rule = arena_alloc(lexer->arena, sizeof(CSSRule));
    rule->selector = token.value;
    rule->declarations = NULL;
    rule->decl_count = 0;
    rule->next = NULL;
    
    token = lexer_next_token(lexer);
    if (token.type != TOK_LBRACE) {
        printf("Error: Expected '{'\n");
        return NULL;
    }
    
    int capacity = 10;
    rule->declarations = arena_alloc(lexer->arena, capacity * sizeof(CSSDeclaration));
    
    while (true) {
        Token prop_token = lexer_next_token(lexer);
        
        if (prop_token.type == TOK_RBRACE) {
            break;
        }
        
        if (prop_token.type == TOK_EOF) {
            printf("Error: Unexpected EOF\n");
            break;
        }
        
        if (rule->decl_count >= capacity) {
            capacity *= 2;
            CSSDeclaration *new_decls = arena_alloc(lexer->arena, capacity * sizeof(CSSDeclaration));
            memcpy(new_decls, rule->declarations, rule->decl_count * sizeof(CSSDeclaration));
            rule->declarations = new_decls;
        }
        
        rule->declarations[rule->decl_count].property = prop_token.value;
        
        Token colon = lexer_next_token(lexer);
        if (colon.type != TOK_COLON) {
            printf("Error: Expected ':'\n");
            break;
        }
        
        Token val_token = lexer_next_token(lexer);
        rule->declarations[rule->decl_count].value = val_token.value;
        rule->decl_count++;
        
        Token semi = lexer_next_token(lexer);
        if (semi.type != TOK_SEMICOLON) {
            printf("Warning: Expected ';'\n");
        }
    }
    
    return rule;
}

void parse_stylesheet(Lexer *lexer, CSSStylesheet *sheet) {
    while (true) {
        CSSRule *rule = parse_rule(lexer);
        if (!rule) break;
        
        if (!sheet->first_rule) {
            sheet->first_rule = rule;
            sheet->last_rule = rule;
        } else {
            sheet->last_rule->next = rule;
            sheet->last_rule = rule;
        }
    }
}

void stylesheet_print(CSSStylesheet *sheet) {
    CSSRule *rule = sheet->first_rule;
    while (rule) {
        printf("%s {\n", rule->selector);
        for (int i = 0; i < rule->decl_count; i++) {
            printf("  %s: %s;\n", 
                   rule->declarations[i].property,
                   rule->declarations[i].value);
        }
        printf("}\n\n");
        rule = rule->next;
    }
}
