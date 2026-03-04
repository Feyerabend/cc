#define _POSIX_C_SOURCE 200809L
#include "pl0.h"

// to silence unused parameter warnings
// that in this case are derived from
// the object-oriented builder/visitor pattern,
// as per usual in C implementations
#define UNUSED(x) (void)(x)


bool is_keyword(const char* str) {
    const char* keywords[] = {
        "begin", "end.", "end", "if", "then", "while", 
        "do", "var", "!", "?", "call", "procedure"
    };
    int count = sizeof(keywords) / sizeof(keywords[0]);
    for (int i = 0; i < count; i++) {
        if (strcmp(str, keywords[i]) == 0) {
            return true;
        }
    }
    return false;
}

TokenKind get_token_kind(const char* token) {
    if (isdigit(token[0])) {
        return TOK_NUM;
    } else if (strchr("+-*/<>=()", token[0]) && strlen(token) == 1) {
        return TOK_OP;
    } else if (isspace(token[0])) {
        return TOK_WS;
    } else if (strcmp(token, ";") == 0) {
        return TOK_SEMI;
    } else if (strcmp(token, ":=") == 0) {
        return TOK_ASGN;
    } else if (strcmp(token, ",") == 0) {
        return TOK_COMMA;
    } else if (is_keyword(token)) {
        return TOK_KW;
    } else if (isalpha(token[0])) {
        return TOK_ID;
    }
    return TOK_EOF;
}

int apply_operator(char op, int left, int right) {
    switch (op) {
        case '+': return left + right;
        case '-': return left - right;
        case '*': return left * right;
        case '/': return left / right;
        case '<': return left < right;
        case '>': return left > right;
        case '=': return left == right;
        default:
            fprintf(stderr, "Unknown operator: %c\n", op);
            exit(1);
    }
}

// lexer

PL0Lexer* lexer_create(const char* code) {
    PL0Lexer* lexer = (PL0Lexer*)malloc(sizeof(PL0Lexer));
    lexer->code = (char*)malloc(strlen(code) + 2);
    strcpy(lexer->code, code);
    strcat(lexer->code, ";");  // force termination
    lexer->position = 0;
    
    lexer->iterator = (TokenIterator*)malloc(sizeof(TokenIterator));
    lexer->iterator->lexer = lexer;
    lexer->iterator->has_next = true;
    
    lexer_next_token(lexer);  // initialize first token
    return lexer;
}

void lexer_destroy(PL0Lexer* lexer) {
    if (lexer) {
        free(lexer->code);
        free(lexer->iterator);
        free(lexer);
    }
}

bool lexer_next_token(PL0Lexer* lexer) {
    char* code = lexer->code + lexer->position;
    
    // Skip whitespace
    while (*code && isspace(*code)) {
        code++;
        lexer->position++;
    }
    
    if (*code == '\0') {
        lexer->iterator->current.kind = TOK_EOF;
        strcpy(lexer->iterator->current.token, "");
        return false;
    }
    
    char token[256] = {0};
    int len = 0;
    
    // Number
    if (isdigit(*code)) {
        while (isdigit(*code)) {
            token[len++] = *code++;
        }
        lexer->iterator->current.kind = TOK_NUM;
    }
    // Assignment operator
    else if (*code == ':' && *(code + 1) == '=') {
        token[len++] = *code++;
        token[len++] = *code++;
        lexer->iterator->current.kind = TOK_ASGN;
    }
    // Single character operators
    else if (strchr("+-*/<>=()", *code)) {
        token[len++] = *code++;
        lexer->iterator->current.kind = TOK_OP;
    }
    // Semicolon
    else if (*code == ';') {
        token[len++] = *code++;
        lexer->iterator->current.kind = TOK_SEMI;
    }
    // Comma
    else if (*code == ',') {
        token[len++] = *code++;
        lexer->iterator->current.kind = TOK_COMMA;
    }
    // Identifier or keyword
    else if (isalpha(*code) || *code == '!' || *code == '?') {
        while (isalnum(*code) || *code == '!' || *code == '?') {
            token[len++] = *code++;
        }
        // Check for "end."
        if (strcmp(token, "end") == 0 && *code == '.') {
            token[len++] = *code++;
        }
        
        lexer->iterator->current.kind = is_keyword(token) ? TOK_KW : TOK_ID;
    }
    else {
        fprintf(stderr, "Unexpected character: %c\n", *code);
        exit(1);
    }
    
    token[len] = '\0';
    strcpy(lexer->iterator->current.token, token);
    lexer->position += len;
    
    return true;
}

TokenIterator* lexer_get_iterator(PL0Lexer* lexer) {
    return lexer->iterator;
}

bool iterator_next(TokenIterator* iter, const char* expected_kind, const char* when_token) {
    if (when_token && strcmp(iter->current.token, when_token) != 0) {
        return false;
    }
    
    if (expected_kind) {
        const char* kind_names[] = {
            "num", "op", "ws", "kw", "id", "semi", "asgn", "comma", "eof"
        };
        TokenKind expected = TOK_EOF;
        for (int i = 0; i < 9; i++) {
            if (strcmp(expected_kind, kind_names[i]) == 0) {
                expected = (TokenKind)i;
                break;
            }
        }
        
        if (iter->current.kind != expected) {
            fprintf(stderr, "Expected %s but got %s\n", expected_kind, kind_names[iter->current.kind]);
            exit(1);
        }
    }
    
    return lexer_next_token(iter->lexer);
}


// AST

void* accept_generic(ASTNode* node, Visitor* visitor) {
    switch (node->type) {
        case NODE_BLOCK: return visitor->visit_block(visitor, node);
        case NODE_ASSIGN: return visitor->visit_assign(visitor, node);
        case NODE_CALL: return visitor->visit_call(visitor, node);
        case NODE_READ: return visitor->visit_read(visitor, node);
        case NODE_WRITE: return visitor->visit_write(visitor, node);
        case NODE_COMPOUND: return visitor->visit_compound(visitor, node);
        case NODE_IF: return visitor->visit_if(visitor, node);
        case NODE_WHILE: return visitor->visit_while(visitor, node);
        case NODE_OPERATION: return visitor->visit_operation(visitor, node);
        case NODE_VARIABLE: return visitor->visit_variable(visitor, node);
        case NODE_NUMBER: return visitor->visit_number(visitor, node);
    }
    return NULL;
}

ASTNode* node_create_block(char** variables, int var_count, 
                           void* procedures, int proc_count, 
                           ASTNode* statement) {
    ASTNode* node = (ASTNode*)malloc(sizeof(ASTNode));
    node->type = NODE_BLOCK;
    node->accept = accept_generic;
    
    BlockData* data = (BlockData*)malloc(sizeof(BlockData));
    data->variables = variables;
    data->var_count = var_count;
    data->procedures = procedures;
    data->proc_count = proc_count;
    data->statement = statement;
    
    node->data = data;
    return node;
}

ASTNode* node_create_assign(const char* var_name, ASTNode* expression) {
    ASTNode* node = (ASTNode*)malloc(sizeof(ASTNode));
    node->type = NODE_ASSIGN;
    node->accept = accept_generic;
    
    AssignData* data = (AssignData*)malloc(sizeof(AssignData));
    data->var_name = strdup(var_name);
    data->expression = expression;
    
    node->data = data;
    return node;
}

ASTNode* node_create_call(const char* proc_name) {
    ASTNode* node = (ASTNode*)malloc(sizeof(ASTNode));
    node->type = NODE_CALL;
    node->accept = accept_generic;
    
    CallData* data = (CallData*)malloc(sizeof(CallData));
    data->proc_name = strdup(proc_name);
    
    node->data = data;
    return node;
}

ASTNode* node_create_read(const char* var_name) {
    ASTNode* node = (ASTNode*)malloc(sizeof(ASTNode));
    node->type = NODE_READ;
    node->accept = accept_generic;
    
    ReadData* data = (ReadData*)malloc(sizeof(ReadData));
    data->var_name = strdup(var_name);
    
    node->data = data;
    return node;
}

ASTNode* node_create_write(ASTNode* expression) {
    ASTNode* node = (ASTNode*)malloc(sizeof(ASTNode));
    node->type = NODE_WRITE;
    node->accept = accept_generic;
    
    WriteData* data = (WriteData*)malloc(sizeof(WriteData));
    data->expression = expression;
    
    node->data = data;
    return node;
}

ASTNode* node_create_compound(ASTNode** statements, int count) {
    ASTNode* node = (ASTNode*)malloc(sizeof(ASTNode));
    node->type = NODE_COMPOUND;
    node->accept = accept_generic;
    
    CompoundData* data = (CompoundData*)malloc(sizeof(CompoundData));
    data->statements = statements;
    data->count = count;
    
    node->data = data;
    return node;
}

ASTNode* node_create_if(ASTNode* condition, ASTNode* then_statement) {
    ASTNode* node = (ASTNode*)malloc(sizeof(ASTNode));
    node->type = NODE_IF;
    node->accept = accept_generic;
    
    IfData* data = (IfData*)malloc(sizeof(IfData));
    data->condition = condition;
    data->then_statement = then_statement;
    
    node->data = data;
    return node;
}

ASTNode* node_create_while(ASTNode* condition, ASTNode* body) {
    ASTNode* node = (ASTNode*)malloc(sizeof(ASTNode));
    node->type = NODE_WHILE;
    node->accept = accept_generic;
    
    WhileData* data = (WhileData*)malloc(sizeof(WhileData));
    data->condition = condition;
    data->body = body;
    
    node->data = data;
    return node;
}

ASTNode* node_create_operation(char operator, ASTNode* left, ASTNode* right) {
    ASTNode* node = (ASTNode*)malloc(sizeof(ASTNode));
    node->type = NODE_OPERATION;
    node->accept = accept_generic;
    
    OperationData* data = (OperationData*)malloc(sizeof(OperationData));
    data->operator = operator;
    data->left = left;
    data->right = right;
    
    node->data = data;
    return node;
}

ASTNode* node_create_variable(const char* name) {
    ASTNode* node = (ASTNode*)malloc(sizeof(ASTNode));
    node->type = NODE_VARIABLE;
    node->accept = accept_generic;
    
    VariableData* data = (VariableData*)malloc(sizeof(VariableData));
    data->name = strdup(name);
    
    node->data = data;
    return node;
}

ASTNode* node_create_number(int value) {
    ASTNode* node = (ASTNode*)malloc(sizeof(ASTNode));
    node->type = NODE_NUMBER;
    node->accept = accept_generic;
    
    NumberData* data = (NumberData*)malloc(sizeof(NumberData));
    data->value = value;
    
    node->data = data;
    return node;
}

void node_destroy(ASTNode* node) {
    if (!node) return;
    
    switch (node->type) {
        case NODE_BLOCK: {
            BlockData* data = (BlockData*)node->data;
            for (int i = 0; i < data->var_count; i++) {
                free(data->variables[i]);
            }
            free(data->variables);
            
            for (int i = 0; i < data->proc_count; i++) {
                free(data->procedures[i].name);
                node_destroy(data->procedures[i].body);
            }
            free(data->procedures);
            
            node_destroy(data->statement);
            free(data);
            break;
        }
        case NODE_ASSIGN: {
            AssignData* data = (AssignData*)node->data;
            free(data->var_name);
            node_destroy(data->expression);
            free(data);
            break;
        }
        case NODE_CALL: {
            CallData* data = (CallData*)node->data;
            free(data->proc_name);
            free(data);
            break;
        }
        case NODE_READ: {
            ReadData* data = (ReadData*)node->data;
            free(data->var_name);
            free(data);
            break;
        }
        case NODE_WRITE: {
            WriteData* data = (WriteData*)node->data;
            node_destroy(data->expression);
            free(data);
            break;
        }
        case NODE_COMPOUND: {
            CompoundData* data = (CompoundData*)node->data;
            for (int i = 0; i < data->count; i++) {
                node_destroy(data->statements[i]);
            }
            free(data->statements);
            free(data);
            break;
        }
        case NODE_IF: {
            IfData* data = (IfData*)node->data;
            node_destroy(data->condition);
            node_destroy(data->then_statement);
            free(data);
            break;
        }
        case NODE_WHILE: {
            WhileData* data = (WhileData*)node->data;
            node_destroy(data->condition);
            node_destroy(data->body);
            free(data);
            break;
        }
        case NODE_OPERATION: {
            OperationData* data = (OperationData*)node->data;
            node_destroy(data->left);
            node_destroy(data->right);
            free(data);
            break;
        }
        case NODE_VARIABLE: {
            VariableData* data = (VariableData*)node->data;
            free(data->name);
            free(data);
            break;
        }
        case NODE_NUMBER: {
            free(node->data);
            break;
        }
    }
    
    free(node);
}


// AST builder

ASTBuilder* builder_create(PL0Lexer* lexer) {
    ASTBuilder* builder = (ASTBuilder*)malloc(sizeof(ASTBuilder));
    builder->iterator = lexer_get_iterator(lexer);
    return builder;
}

void builder_destroy(ASTBuilder* builder) {
    free(builder);
}

ASTNode* builder_build(ASTBuilder* builder) {
    return builder_build_block(builder);
}

ASTNode* builder_build_block(ASTBuilder* builder) {
    TokenIterator* iter = builder->iterator;
    
    // Variable declarations
    char** variables = NULL;
    int var_count = 0;
    int var_capacity = 0;
    
    while (iterator_next(iter, "kw", "var")) {
        while (true) {
            if (var_count >= var_capacity) {
                var_capacity = var_capacity == 0 ? 4 : var_capacity * 2;
                variables = (char**)realloc(variables, var_capacity * sizeof(char*));
            }
            
            variables[var_count++] = strdup(iter->current.token);
            iterator_next(iter, "id", NULL);
            
            if (!iterator_next(iter, "comma", ",")) {
                break;
            }
        }
        iterator_next(iter, "semi", NULL);
    }
    
    // Procedure declarations
    struct { char* name; ASTNode* body; }* procedures = NULL;
    int proc_count = 0;
    int proc_capacity = 0;
    
    while (iterator_next(iter, "kw", "procedure")) {
        if (proc_count >= proc_capacity) {
            proc_capacity = proc_capacity == 0 ? 4 : proc_capacity * 2;
            procedures = realloc(procedures, proc_capacity * sizeof(*procedures));
        }
        
        procedures[proc_count].name = strdup(iter->current.token);
        iterator_next(iter, "id", NULL);
        iterator_next(iter, "semi", NULL);
        
        procedures[proc_count].body = builder_build_block(builder);
        proc_count++;
        
        iterator_next(iter, "semi", NULL);
    }
    
    // Main statement
    ASTNode* statement = builder_build_statement(builder);
    
    return node_create_block(variables, var_count, procedures, proc_count, statement);
}

ASTNode* builder_build_statement(ASTBuilder* builder) {
    TokenIterator* iter = builder->iterator;
    
    if (iter->current.kind == TOK_ID) {
        // Assignment
        char* var_name = strdup(iter->current.token);
        iterator_next(iter, "id", NULL);
        iterator_next(iter, "asgn", NULL);
        ASTNode* expr = builder_build_expression(builder, "+-", builder_build_term);
        return node_create_assign(var_name, expr);
    }
    else if (strcmp(iter->current.token, "call") == 0) {
        // Procedure call
        iterator_next(iter, "kw", NULL);
        char* proc_name = strdup(iter->current.token);
        iterator_next(iter, "id", NULL);
        return node_create_call(proc_name);
    }
    else if (strcmp(iter->current.token, "?") == 0) {
        // Read
        iterator_next(iter, "kw", NULL);
        char* var_name = strdup(iter->current.token);
        iterator_next(iter, "id", NULL);
        return node_create_read(var_name);
    }
    else if (strcmp(iter->current.token, "!") == 0) {
        // Write
        iterator_next(iter, "kw", NULL);
        ASTNode* expr = builder_build_expression(builder, "+-", builder_build_term);
        return node_create_write(expr);
    }
    else if (strcmp(iter->current.token, "begin") == 0) {
        // Compound statement
        iterator_next(iter, "kw", NULL);
        
        ASTNode** statements = NULL;
        int count = 0;
        int capacity = 0;
        
        while (strcmp(iter->current.token, "end") != 0 && 
               strcmp(iter->current.token, "end.") != 0) {
            if (count >= capacity) {
                capacity = capacity == 0 ? 4 : capacity * 2;
                statements = (ASTNode**)realloc(statements, capacity * sizeof(ASTNode*));
            }
            
            statements[count++] = builder_build_statement(builder);
            iterator_next(iter, "semi", ";");
        }
        
        iterator_next(iter, "kw", NULL);
        return node_create_compound(statements, count);
    }
    else if (strcmp(iter->current.token, "if") == 0) {
        // If statement
        iterator_next(iter, "kw", NULL);
        ASTNode* left_expr = builder_build_expression(builder, "+-", builder_build_term);
        char op = iter->current.token[0];
        iterator_next(iter, "op", NULL);
        ASTNode* right_expr = builder_build_expression(builder, "+-", builder_build_term);
        ASTNode* condition = node_create_operation(op, left_expr, right_expr);
        iterator_next(iter, "kw", "then");
        ASTNode* then_stmt = builder_build_statement(builder);
        return node_create_if(condition, then_stmt);
    }
    else if (strcmp(iter->current.token, "while") == 0) {
        // While statement
        iterator_next(iter, "kw", NULL);
        ASTNode* left_expr = builder_build_expression(builder, "+-", builder_build_term);
        char op = iter->current.token[0];
        iterator_next(iter, "op", NULL);
        ASTNode* right_expr = builder_build_expression(builder, "+-", builder_build_term);
        ASTNode* condition = node_create_operation(op, left_expr, right_expr);
        iterator_next(iter, "kw", "do");
        ASTNode* body = builder_build_statement(builder);
        return node_create_while(condition, body);
    }
    
    return NULL;
}

ASTNode* builder_build_term(ASTBuilder* builder) {
    return builder_build_expression(builder, "*/", builder_build_factor);
}

ASTNode* builder_build_expression(ASTBuilder* builder, const char* operators, 
                                   ASTNode* (*term_builder)(ASTBuilder*)) {
    TokenIterator* iter = builder->iterator;
    
    ASTNode* left = term_builder(builder);
    
    while (strchr(operators, iter->current.token[0]) != NULL && 
           strlen(iter->current.token) == 1) {
        char op = iter->current.token[0];
        iterator_next(iter, "op", NULL);
        ASTNode* right = term_builder(builder);
        left = node_create_operation(op, left, right);
    }
    
    return left;
}

ASTNode* builder_build_factor(ASTBuilder* builder) {
    TokenIterator* iter = builder->iterator;
    
    if (iter->current.kind == TOK_ID) {
        char* name = strdup(iter->current.token);
        iterator_next(iter, "id", NULL);
        return node_create_variable(name);
    }
    else if (iter->current.kind == TOK_NUM) {
        int value = atoi(iter->current.token);
        iterator_next(iter, "num", NULL);
        return node_create_number(value);
    }
    else if (strcmp(iter->current.token, "(") == 0) {
        iterator_next(iter, "op", NULL);
        ASTNode* expr = builder_build_expression(builder, "+-", builder_build_term);
        iterator_next(iter, "op", NULL);
        return expr;
    }
    
    return NULL;
}


// Scope

Scope* scope_create(Scope* parent) {
    Scope* scope = (Scope*)malloc(sizeof(Scope));
    scope->parent = parent;
    scope->variables = NULL;
    scope->procedures = NULL;
    return scope;
}

void scope_destroy(Scope* scope) {
    if (!scope) return;
    
    ScopeVar* var = scope->variables;
    while (var) {
        ScopeVar* next = var->next;
        free(var->name);
        free(var);
        var = next;
    }
    
    ScopeProc* proc = scope->procedures;
    while (proc) {
        ScopeProc* next = proc->next;
        free(proc->name);
        free(proc);
        proc = next;
    }
    
    free(scope);
}

void scope_add_variable(Scope* scope, const char* name, int value) {
    ScopeVar* var = (ScopeVar*)malloc(sizeof(ScopeVar));
    var->name = strdup(name);
    var->value = value;
    var->next = scope->variables;
    scope->variables = var;
}

void scope_add_procedure(Scope* scope, const char* name, ASTNode* body, Scope* def_scope) {
    ScopeProc* proc = (ScopeProc*)malloc(sizeof(ScopeProc));
    proc->name = strdup(name);
    proc->body = body;
    proc->def_scope = def_scope;
    proc->next = scope->procedures;
    scope->procedures = proc;
}

ScopeVar* scope_find_variable(Scope* scope, const char* name) {
    if (!scope) {
        fprintf(stderr, "Variable '%s' not found\n", name);
        exit(1);
    }
    
    ScopeVar* var = scope->variables;
    while (var) {
        if (strcmp(var->name, name) == 0) {
            return var;
        }
        var = var->next;
    }
    
    return scope_find_variable(scope->parent, name);
}

ScopeProc* scope_find_procedure(Scope* scope, const char* name) {
    if (!scope) {
        fprintf(stderr, "Procedure '%s' not found\n", name);
        exit(1);
    }
    
    ScopeProc* proc = scope->procedures;
    while (proc) {
        if (strcmp(proc->name, name) == 0) {
            return proc;
        }
        proc = proc->next;
    }
    
    return scope_find_procedure(scope->parent, name);
}


// interpreter (visitor)

void* visit_block_impl(Visitor* v, ASTNode* node) {
    InterpreterContext* ctx = (InterpreterContext*)v->context;
    BlockData* data = (BlockData*)node->data;
    
    Scope* new_scope = scope_create(ctx->scope);
    
    // Add variables
    for (int i = 0; i < data->var_count; i++) {
        scope_add_variable(new_scope, data->variables[i], 0);
    }
    
    // Add procedures
    for (int i = 0; i < data->proc_count; i++) {
        scope_add_procedure(new_scope, data->procedures[i].name, 
                          data->procedures[i].body, new_scope);
    }
    
    // Execute statement in new scope
    Scope* old_scope = ctx->scope;
    ctx->scope = new_scope;
    
    data->statement->accept(data->statement, v);
    
    ctx->scope = old_scope;
    scope_destroy(new_scope);
    
    return NULL;
}

void* visit_assign_impl(Visitor* v, ASTNode* node) {
    InterpreterContext* ctx = (InterpreterContext*)v->context;
    AssignData* data = (AssignData*)node->data;
    
    int value = (long)data->expression->accept(data->expression, v);
    ScopeVar* var = scope_find_variable(ctx->scope, data->var_name);
    var->value = value;
    
    return NULL;
}

void* visit_call_impl(Visitor* v, ASTNode* node) {
    InterpreterContext* ctx = (InterpreterContext*)v->context;
    CallData* data = (CallData*)node->data;
    
    ScopeProc* proc = scope_find_procedure(ctx->scope, data->proc_name);
    
    Scope* old_scope = ctx->scope;
    ctx->scope = scope_create(proc->def_scope);
    
    proc->body->accept(proc->body, v);
    
    Scope* temp = ctx->scope;
    ctx->scope = old_scope;
    scope_destroy(temp);
    
    return NULL;
}

void* visit_read_impl(Visitor* v, ASTNode* node) {
    InterpreterContext* ctx = (InterpreterContext*)v->context;
    ReadData* data = (ReadData*)node->data;
    
    int value;
    printf("> ");
    if (scanf("%d", &value) != 1) {
        fprintf(stderr, "Invalid input\n");
        exit(1);
    }
    
    ScopeVar* var = scope_find_variable(ctx->scope, data->var_name);
    var->value = value;
    
    return NULL;
}

void* visit_write_impl(Visitor* v, ASTNode* node) {
    WriteData* data = (WriteData*)node->data;
    int value = (long)data->expression->accept(data->expression, v);
    printf("%d\n", value);
    return NULL;
}

void* visit_compound_impl(Visitor* v, ASTNode* node) {
    CompoundData* data = (CompoundData*)node->data;
    
    for (int i = 0; i < data->count; i++) {
        data->statements[i]->accept(data->statements[i], v);
    }
    
    return NULL;
}

void* visit_if_impl(Visitor* v, ASTNode* node) {
    IfData* data = (IfData*)node->data;
    
    int condition = (long)data->condition->accept(data->condition, v);
    if (condition) {
        data->then_statement->accept(data->then_statement, v);
    }
    
    return NULL;
}

void* visit_while_impl(Visitor* v, ASTNode* node) {
    WhileData* data = (WhileData*)node->data;
    
    while ((long)data->condition->accept(data->condition, v)) {
        data->body->accept(data->body, v);
    }
    
    return NULL;
}

void* visit_operation_impl(Visitor* v, ASTNode* node) {
    OperationData* data = (OperationData*)node->data;
    
    int left = (long)data->left->accept(data->left, v);
    int right = (long)data->right->accept(data->right, v);
    
    int result = apply_operator(data->operator, left, right);
    return (void*)(long)result;
}

void* visit_variable_impl(Visitor* v, ASTNode* node) {
    InterpreterContext* ctx = (InterpreterContext*)v->context;
    VariableData* data = (VariableData*)node->data;
    
    ScopeVar* var = scope_find_variable(ctx->scope, data->name);
    return (void*)(long)var->value;
}

void* visit_number_impl(Visitor* v, ASTNode* node) {
    UNUSED(v); // number nodes don't need the context,
               // but for the visitor pattern we still need to implement this
    NumberData* data = (NumberData*)node->data;
    return (void*)(long)data->value;
}


Visitor* interpreter_create(void) {
    Visitor* visitor = (Visitor*)malloc(sizeof(Visitor));
    
    InterpreterContext* ctx = (InterpreterContext*)malloc(sizeof(InterpreterContext));
    ctx->scope = NULL;
    
    visitor->context = ctx;
    visitor->visit_block = visit_block_impl;
    visitor->visit_assign = visit_assign_impl;
    visitor->visit_call = visit_call_impl;
    visitor->visit_read = visit_read_impl;
    visitor->visit_write = visit_write_impl;
    visitor->visit_compound = visit_compound_impl;
    visitor->visit_if = visit_if_impl;
    visitor->visit_while = visit_while_impl;
    visitor->visit_operation = visit_operation_impl;
    visitor->visit_variable = visit_variable_impl;
    visitor->visit_number = visit_number_impl;
    
    return visitor;
}

void interpreter_destroy(Visitor* visitor) {
    if (visitor) {
        free(visitor->context);
        free(visitor);
    }
}

void interpreter_interpret(Visitor* visitor, ASTNode* ast) {
    InterpreterContext* ctx = (InterpreterContext*)visitor->context;
    ctx->scope = scope_create(NULL);
    ast->accept(ast, visitor);
}




int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
        return 1;
    }
    
    // Read file
    FILE* file = fopen(argv[1], "r");
    if (!file) {
        fprintf(stderr, "Error opening file: %s\n", argv[1]);
        return 1;
    }
    
    fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    fseek(file, 0, SEEK_SET);
    
    char* code = (char*)malloc(file_size + 1);
    fread(code, 1, file_size, file);
    code[file_size] = '\0';
    fclose(file);
    
    // Create lexer
    PL0Lexer* lexer = lexer_create(code);
    free(code);
    
    // Build AST using the builder pattern
    ASTBuilder* builder = builder_create(lexer);
    ASTNode* ast = builder_build(builder);
    
    // Interpret
    Visitor* interpreter = interpreter_create();
    interpreter_interpret(interpreter, ast);
    
    // Cleanup
    interpreter_destroy(interpreter);
    node_destroy(ast);
    builder_destroy(builder);
    lexer_destroy(lexer);
    
    return 0;
}
