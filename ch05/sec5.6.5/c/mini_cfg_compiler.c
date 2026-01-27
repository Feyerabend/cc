/*
 * mini_cfg_compiler.c
 * 
 * A very adapted minimal compiler that parses
 * simple C-like code and only shows how it
 * builds a Control Flow Graph (CFG).
 * The idea is to illustrate CFG construction.
 * 
 * Supported syntax:
 * - Variable assignments: x = 5;
 * - Conditionals: if (condition) { ... } else { ... }
 * - Loops: while (condition) { ... }
 * - Return statements: return x;
 *
 * Compile the compiler
 *. gcc -o mini_cfg mini_cfg_compiler.c
 *
 * Run with test programs
 * ./mini_cfg < test1_ifelse.c
 * ./mini_cfg < test2_while.c
 * ./mini_cfg < test3_nested.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_BLOCKS 100
#define MAX_STMT_LEN 256
#define MAX_EDGES 200

/* Basic Block structure */
typedef struct BasicBlock {
    int id;
    char statement[MAX_STMT_LEN];
    int successors[4];  /* Can have up to 4 successors (enough for most cases here) */
    int num_successors;
    int is_condition;   /* 1 if this is a conditional block */
} BasicBlock;

/* Control Flow Graph */
typedef struct CFG {
    BasicBlock blocks[MAX_BLOCKS];
    int num_blocks;
    int current_block_id;
} CFG;

/* Global CFG */
CFG cfg;

/* Token types */
typedef enum {
    TOK_IF, TOK_ELSE, TOK_WHILE, TOK_RETURN,
    TOK_IDENT, TOK_NUMBER, TOK_LBRACE, TOK_RBRACE,
    TOK_LPAREN, TOK_RPAREN, TOK_SEMICOLON,
    TOK_ASSIGN, TOK_COMPARE, TOK_EOF, TOK_UNKNOWN
} TokenType;

typedef struct {
    TokenType type;
    char value[MAX_STMT_LEN];
} Token;

/* Lexer state */
char input[10000];
int pos = 0;

/* Init CFG */
void init_cfg() {
    cfg.num_blocks = 0;
    cfg.current_block_id = 0;
}

/* Create a new basic block */
int create_block(const char* stmt, int is_cond) {
    if (cfg.num_blocks >= MAX_BLOCKS) {
        fprintf(stderr, "Error: Too many basic blocks\n");
        exit(1);
    }
    
    int id = cfg.num_blocks++;
    BasicBlock* block = &cfg.blocks[id];
    block->id = id;
    strncpy(block->statement, stmt, MAX_STMT_LEN - 1);
    block->statement[MAX_STMT_LEN - 1] = '\0';
    block->num_successors = 0;
    block->is_condition = is_cond;
    
    return id;
}

/* Add edge from one block to another */
void add_edge(int from, int to) {
    if (from >= cfg.num_blocks || to >= cfg.num_blocks) {
        fprintf(stderr, "Error: Invalid block IDs in edge\n");
        return;
    }
    
    BasicBlock* block = &cfg.blocks[from];
    if (block->num_successors < 4) {
        block->successors[block->num_successors++] = to;
    }
}

/* Skip whitespace */
void skip_whitespace() {
    while (input[pos] && isspace(input[pos])) pos++;
}

/* Get next token */
Token get_token() {
    Token tok = {TOK_UNKNOWN, ""};
    skip_whitespace();
    
    if (!input[pos]) {
        tok.type = TOK_EOF;
        return tok;
    }
    
    /* Check for keywords and identifiers */
    if (isalpha(input[pos]) || input[pos] == '_') {
        int i = 0;
        while (isalnum(input[pos]) || input[pos] == '_') {
            tok.value[i++] = input[pos++];
        }
        tok.value[i] = '\0';
        
        if (strcmp(tok.value, "if") == 0) tok.type = TOK_IF;
        else if (strcmp(tok.value, "else") == 0) tok.type = TOK_ELSE;
        else if (strcmp(tok.value, "while") == 0) tok.type = TOK_WHILE;
        else if (strcmp(tok.value, "return") == 0) tok.type = TOK_RETURN;
        else tok.type = TOK_IDENT;
        return tok;
    }
    
    /* Check for numbers */
    if (isdigit(input[pos])) {
        int i = 0;
        while (isdigit(input[pos])) {
            tok.value[i++] = input[pos++];
        }
        tok.value[i] = '\0';
        tok.type = TOK_NUMBER;
        return tok;
    }
    
    /* Check for operators and punctuation */
    switch (input[pos]) {
        case '{': tok.type = TOK_LBRACE; tok.value[0] = input[pos++]; break;
        case '}': tok.type = TOK_RBRACE; tok.value[0] = input[pos++]; break;
        case '(': tok.type = TOK_LPAREN; tok.value[0] = input[pos++]; break;
        case ')': tok.type = TOK_RPAREN; tok.value[0] = input[pos++]; break;
        case ';': tok.type = TOK_SEMICOLON; tok.value[0] = input[pos++]; break;
        case '=':
            if (input[pos + 1] == '=') {
                tok.type = TOK_COMPARE;
                tok.value[0] = '='; tok.value[1] = '='; tok.value[2] = '\0';
                pos += 2;
            } else {
                tok.type = TOK_ASSIGN;
                tok.value[0] = input[pos++];
            }
            break;
        case '<':
        case '>':
        case '!':
            tok.type = TOK_COMPARE;
            tok.value[0] = input[pos++];
            if (input[pos] == '=') {
                tok.value[1] = input[pos++];
                tok.value[2] = '\0';
            }
            break;
        case '+':
        case '-':
        case '*':
        case '/':
            tok.value[0] = input[pos++];
            break;
        default:
            pos++;
    }
    
    return tok;
}

/* Peek at next token without consuming */
Token peek_token() {
    int saved_pos = pos;
    Token tok = get_token();
    pos = saved_pos;
    return tok;
}

/* Frwd decl */
int parse_statement();
int parse_block();

/* Parse a condition (simplified - just read until closing paren) */
void parse_condition(char* cond_str) {
    Token tok = get_token(); /* consume '(' */
    int depth = 1;
    int i = 0;
    
    while (depth > 0 && i < MAX_STMT_LEN - 1) {
        tok = get_token();
        if (tok.type == TOK_LPAREN) depth++;
        else if (tok.type == TOK_RPAREN) depth--;
        
        if (depth > 0) {
            if (i > 0) cond_str[i++] = ' ';
            strncpy(&cond_str[i], tok.value, MAX_STMT_LEN - i - 1);
            i += strlen(tok.value);
        }
    }
    cond_str[i] = '\0';
}

/* Parse an if statement */
int parse_if() {
    char cond[MAX_STMT_LEN];
    parse_condition(cond);
    
    char stmt[MAX_STMT_LEN];
    snprintf(stmt, MAX_STMT_LEN, "if (%s)", cond);
    int if_block = create_block(stmt, 1);
    
    /* Parse true branch */
    int true_start = parse_statement();
    add_edge(if_block, true_start);
    
    /* Check for else */
    Token tok = peek_token();
    int merge_block = create_block("merge", 0);
    
    if (tok.type == TOK_ELSE) {
        get_token(); /* consume 'else' */
        int false_start = parse_statement();
        add_edge(if_block, false_start);
        
        /* Both branches merge */
        int last_true = cfg.num_blocks - 2;
        int last_false = cfg.num_blocks - 1;
        if (last_true >= 0) add_edge(last_true, merge_block);
        if (last_false >= 0) add_edge(last_false, merge_block);
    } else {
        /* No else branch - condition can skip directly to merge */
        add_edge(if_block, merge_block);
        int last_true = cfg.num_blocks - 2;
        if (last_true >= 0) add_edge(last_true, merge_block);
    }
    
    return if_block;
}

/* Parse a while loop */
int parse_while() {
    char cond[MAX_STMT_LEN];
    parse_condition(cond);
    
    char stmt[MAX_STMT_LEN];
    snprintf(stmt, MAX_STMT_LEN, "while (%s)", cond);
    int while_block = create_block(stmt, 1);
    
    /* Parse loop body */
    int body_start = parse_statement();
    add_edge(while_block, body_start);
    
    /* Create exit block */
    int exit_block = create_block("loop exit", 0);
    add_edge(while_block, exit_block);
    
    /* Back edge from body to condition */
    int last_body = body_start;
    while (last_body < cfg.num_blocks - 1 && 
           cfg.blocks[last_body].num_successors > 0) {
        last_body = cfg.blocks[last_body].successors[0];
    }
    add_edge(last_body, while_block);
    
    return while_block;
}

/* Parse a block of statements */
int parse_block() {
    Token tok = get_token(); /* consume '{' */
    int first_block = -1;
    
    while (peek_token().type != TOK_RBRACE && peek_token().type != TOK_EOF) {
        int block = parse_statement();
        if (first_block == -1) first_block = block;
    }
    
    get_token(); /* consume '}' */
    return first_block >= 0 ? first_block : create_block("empty block", 0);
}

/* Parse a single statement */
int parse_statement() {
    Token tok = peek_token();
    
    if (tok.type == TOK_IF) {
        get_token(); /* consume 'if' */
        return parse_if();
    }
    
    if (tok.type == TOK_WHILE) {
        get_token(); /* consume 'while' */
        return parse_while();
    }
    
    if (tok.type == TOK_LBRACE) {
        return parse_block();
    }
    
    /* Parse simple statement (assignment or return) */
    char stmt[MAX_STMT_LEN] = "";
    int i = 0;
    
    while (tok.type != TOK_SEMICOLON && tok.type != TOK_EOF) {
        tok = get_token();
        if (tok.type != TOK_SEMICOLON) {
            if (i > 0) stmt[i++] = ' ';
            strncpy(&stmt[i], tok.value, MAX_STMT_LEN - i - 1);
            i += strlen(tok.value);
        }
        tok = peek_token();
    }
    
    if (peek_token().type == TOK_SEMICOLON) {
        get_token(); /* consume ';' */
    }
    
    return create_block(stmt, 0);
}

/* Print CFG in text format */
void print_cfg_text() {
    printf("\n-- Control Flow Graph (text) --\n\n");
    for (int i = 0; i < cfg.num_blocks; i++) {
        BasicBlock* block = &cfg.blocks[i];
        printf("Block %d: %s\n", block->id, block->statement);
        printf("  Successors: ");
        if (block->num_successors == 0) {
            printf("(exit)\n");
        } else {
            for (int j = 0; j < block->num_successors; j++) {
                printf("%d ", block->successors[j]);
            }
            printf("\n");
        }
        printf("\n");
    }
}

/* Print CFG in DOT format for Graphviz */
void print_cfg_dot() {
    printf("\n-- DOT Format (copy/paste into graphviz) --\n\n");
    printf("digraph CFG {\n");
    printf("  node [shape=box, style=rounded];\n\n");
    
    for (int i = 0; i < cfg.num_blocks; i++) {
        BasicBlock* block = &cfg.blocks[i];
        /* Escape quotes in label */
        printf("  %d [label=\"%s\"", block->id, block->statement);
        if (block->is_condition) {
            printf(", shape=diamond");
        }
        printf("];\n");
        
        for (int j = 0; j < block->num_successors; j++) {
            printf("  %d -> %d", block->id, block->successors[j]);
            /* Label true/false for conditions */
            if (block->is_condition && j < 2) {
                printf(" [label=\"%s\"]", j == 0 ? "true" : "false");
            }
            printf(";\n");
        }
    }
    
    printf("}\n");
}

int main() {
    /* Read entire input */
    int len = fread(input, 1, sizeof(input) - 1, stdin);
    input[len] = '\0';
    
    printf("-- Input Program --\n%s\n", input);
    
    /* Init and parse */
    init_cfg();
    
    /* Add start block */
    int start = create_block("START", 0);
    
    /* Parse all statements */
    while (peek_token().type != TOK_EOF) {
        int stmt_block = parse_statement();
        if (start == 0 && stmt_block > 0) {
            add_edge(start, stmt_block);
        }
    }
    
    /* Add end block */
    int end = create_block("END", 0);
    for (int i = 0; i < cfg.num_blocks - 1; i++) {
        if (cfg.blocks[i].num_successors == 0) {
            add_edge(i, end);
        }
    }
    
    /* Print results */
    print_cfg_text();
    print_cfg_dot();
    
    return 0;
}
