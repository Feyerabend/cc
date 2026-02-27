#define _POSIX_C_SOURCE 200809L
#include "eventscript.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

Bytecode *bytecode_create(void) {
    Bytecode *bc = calloc(1, sizeof(Bytecode));
    bc->capacity = 256;
    bc->code = malloc(bc->capacity);
    bc->const_capacity = 64;
    bc->constants = malloc(bc->const_capacity * sizeof(Value));
    return bc;
}

void bytecode_free(Bytecode *bc) {
    if (!bc) return;
    free(bc->code);
    for (size_t i = 0; i < bc->const_count; i++) {
        if (bc->constants[i].type == VAL_STRING) {
            free(bc->constants[i].string);
        }
    }
    free(bc->constants);
    free(bc);
}

void bytecode_write(Bytecode *bc, uint8_t byte) {
    if (bc->size >= bc->capacity) {
        bc->capacity *= 2;
        bc->code = realloc(bc->code, bc->capacity);
    }
    bc->code[bc->size++] = byte;
}

size_t bytecode_add_constant(Bytecode *bc, Value value) {
    if (bc->const_count >= bc->const_capacity) {
        bc->const_capacity *= 2;
        bc->constants = realloc(bc->constants, bc->const_capacity * sizeof(Value));
    }
    bc->constants[bc->const_count] = value;
    return bc->const_count++;
}

static void compile_expr(ASTNode *node, Bytecode *bc);

static void compile_stmt(ASTNode *node, Bytecode *bc) {
    switch (node->type) {
        case AST_PRINT: {
            compile_expr(node->print.expr, bc);
            bytecode_write(bc, OP_PRINT_OP);
            break;
        }
        
        case AST_EVENT_EMIT: {
            // Push event name
            Value event_name = {.type = VAL_STRING, .string = strdup(node->emit.event_name)};
            size_t name_idx = bytecode_add_constant(bc, event_name);
            bytecode_write(bc, OP_CONST);
            bytecode_write(bc, (uint8_t)name_idx);
            
            // Push data
            compile_expr(node->emit.data, bc);
            
            // Emit instruction
            bytecode_write(bc, OP_EMIT);
            break;
        }
        
        case AST_EVENT_ON: {
            // Push event name
            Value event_name = {.type = VAL_STRING, .string = strdup(node->on.event_name)};
            size_t name_idx = bytecode_add_constant(bc, event_name);
            
            bytecode_write(bc, OP_CONST);
            bytecode_write(bc, (uint8_t)name_idx);
            
            // The handler will start right after the REGISTER instruction
            size_t handler_pc = bc->size + 2;  // After REGISTER opcode + handler_pc byte
            
            bytecode_write(bc, OP_REGISTER);
            bytecode_write(bc, (uint8_t)(handler_pc & 0xFF));
            
            // Compile handler body (but it will be jumped over during main execution)
            if (node->on.body->type == AST_BLOCK) {
                for (size_t i = 0; i < node->on.body->block.count; i++) {
                    compile_stmt(node->on.body->block.statements[i], bc);
                }
            } else {
                compile_stmt(node->on.body, bc);
            }
            bytecode_write(bc, OP_RETURN);
            
            break;
        }
        
        case AST_BLOCK: {
            for (size_t i = 0; i < node->block.count; i++) {
                compile_stmt(node->block.statements[i], bc);
            }
            break;
        }
        
        default:
            // Treat as expression statement
            compile_expr(node, bc);
            bytecode_write(bc, OP_POP);
            break;
    }
}

static void compile_expr(ASTNode *node, Bytecode *bc) {
    switch (node->type) {
        case AST_NUMBER: {
            Value v = {.type = VAL_NUMBER, .number = node->number.value};
            size_t idx = bytecode_add_constant(bc, v);
            bytecode_write(bc, OP_CONST);
            bytecode_write(bc, (uint8_t)idx);
            break;
        }
        
        case AST_STRING: {
            Value v = {.type = VAL_STRING, .string = strdup(node->string.value)};
            size_t idx = bytecode_add_constant(bc, v);
            bytecode_write(bc, OP_CONST);
            bytecode_write(bc, (uint8_t)idx);
            break;
        }
        
        case AST_BINARY_OP: {
            compile_expr(node->binary.left, bc);
            compile_expr(node->binary.right, bc);
            switch (node->binary.op) {
                case OP_ADD: bytecode_write(bc, OP_ADD_OP); break;
                case OP_SUB: bytecode_write(bc, OP_SUB_OP); break;
                case OP_MUL: bytecode_write(bc, OP_MUL_OP); break;
                case OP_DIV: bytecode_write(bc, OP_DIV_OP); break;
                default: break;
            }
            break;
        }
        
        default:
            fprintf(stderr, "Cannot compile expression type %d\n", node->type);
            break;
    }
}

void compile(ASTNode *ast, Bytecode *bc) {
    if (ast->type == AST_PROGRAM) {
        for (size_t i = 0; i < ast->program.count; i++) {
            compile_stmt(ast->program.statements[i], bc);
        }
    } else {
        compile_stmt(ast, bc);
    }
    bytecode_write(bc, OP_HALT);
}
