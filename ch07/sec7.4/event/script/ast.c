#define _POSIX_C_SOURCE 200809L
#include "eventscript.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

ASTNode *ast_number(int value) {
    ASTNode *node = calloc(1, sizeof(ASTNode));
    node->type = AST_NUMBER;
    node->number.value = value;
    return node;
}

ASTNode *ast_string(const char *str) {
    ASTNode *node = calloc(1, sizeof(ASTNode));
    node->type = AST_STRING;
    node->string.value = strdup(str);
    return node;
}

ASTNode *ast_identifier(const char *name) {
    ASTNode *node = calloc(1, sizeof(ASTNode));
    node->type = AST_IDENTIFIER;
    node->identifier.name = strdup(name);
    return node;
}

ASTNode *ast_binary(BinaryOp op, ASTNode *left, ASTNode *right) {
    ASTNode *node = calloc(1, sizeof(ASTNode));
    node->type = AST_BINARY_OP;
    node->binary.op = op;
    node->binary.left = left;
    node->binary.right = right;
    return node;
}

ASTNode *ast_print(ASTNode *expr) {
    ASTNode *node = calloc(1, sizeof(ASTNode));
    node->type = AST_PRINT;
    node->print.expr = expr;
    return node;
}

ASTNode *ast_emit(const char *event_name, ASTNode *data) {
    ASTNode *node = calloc(1, sizeof(ASTNode));
    node->type = AST_EVENT_EMIT;
    node->emit.event_name = strdup(event_name);
    node->emit.data = data;
    return node;
}

ASTNode *ast_on(const char *event_name, ASTNode *body) {
    ASTNode *node = calloc(1, sizeof(ASTNode));
    node->type = AST_EVENT_ON;
    node->on.event_name = strdup(event_name);
    node->on.body = body;
    return node;
}

ASTNode *ast_timer(int delay_ms, const char *event_name, ASTNode *data) {
    ASTNode *node = calloc(1, sizeof(ASTNode));
    node->type = AST_TIMER_AFTER;
    node->timer.delay_ms = delay_ms;
    node->timer.event_name = strdup(event_name);
    node->timer.data = data;
    return node;
}

ASTNode *ast_block(ASTNode **statements, size_t count) {
    ASTNode *node = calloc(1, sizeof(ASTNode));
    node->type = AST_BLOCK;
    node->block.statements = statements;
    node->block.count = count;
    return node;
}

ASTNode *ast_program(ASTNode **statements, size_t count) {
    ASTNode *node = calloc(1, sizeof(ASTNode));
    node->type = AST_PROGRAM;
    node->program.statements = statements;
    node->program.count = count;
    return node;
}

void ast_free(ASTNode *node) {
    if (!node) return;
    
    switch (node->type) {
        case AST_STRING:
            free(node->string.value);
            break;
        case AST_IDENTIFIER:
            free(node->identifier.name);
            break;
        case AST_BINARY_OP:
            ast_free(node->binary.left);
            ast_free(node->binary.right);
            break;
        case AST_PRINT:
            ast_free(node->print.expr);
            break;
        case AST_EVENT_EMIT:
            free(node->emit.event_name);
            ast_free(node->emit.data);
            break;
        case AST_EVENT_ON:
            free(node->on.event_name);
            ast_free(node->on.body);
            break;
        case AST_TIMER_AFTER:
            free(node->timer.event_name);
            ast_free(node->timer.data);
            break;
        case AST_BLOCK:
        case AST_PROGRAM:
            for (size_t i = 0; i < node->block.count; i++)
                ast_free(node->block.statements[i]);
            free(node->block.statements);
            break;
        default:
            break;
    }
    
    free(node);
}
