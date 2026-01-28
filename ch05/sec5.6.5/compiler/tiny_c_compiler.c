/*
 * tiny_c_compiler.c
 * 
 * A small C compiler with CFG-based optimisation
 * Supports: variables, arithmetic, if/else, while, functions
 * Optimissations:
 *   1. constant folding,
 *   2. dead code elimination
 *
 * Target: Generates C code (self-hosting)
 *
 * Compile: gcc -o tcc tiny_c_compiler.c -lm
 * Usage: ./tcc < input.c > output.c && gcc output.c -o program
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdarg.h>

#define MAX_TOKENS 2000
#define MAX_BLOCKS 200
#define MAX_INSTRS 1000
#define MAX_VARS 100
#define MAX_FUNCS 20
#define MAX_IDENT 64

/*  TOKEN TYPES  */
typedef enum {
    TOK_EOF, TOK_INT, TOK_RETURN, TOK_IF, TOK_ELSE, TOK_WHILE,
    TOK_IDENT, TOK_NUMBER, TOK_STRING,
    TOK_LPAREN, TOK_RPAREN, TOK_LBRACE, TOK_RBRACE,
    TOK_SEMICOLON, TOK_COMMA,
    TOK_ASSIGN,  // =
    TOK_PLUS, TOK_MINUS, TOK_STAR, TOK_SLASH,  // + - * /
    TOK_EQ, TOK_NE, TOK_LT, TOK_LE, TOK_GT, TOK_GE,  // == != < <= > >=
    TOK_AND, TOK_OR  // && ||
} TokenType;

typedef struct {
    TokenType type;
    char text[MAX_IDENT];
    int value;
} Token;

/*  THREE-ADDRESS CODE INSTRUCTIONS  */
typedef enum {
    OP_NOP,
    OP_CONST,     // dst = const
    OP_COPY,      // dst = src1
    OP_ADD,       // dst = src1 + src2
    OP_SUB,       // dst = src1 - src2
    OP_MUL,       // dst = src1 * src2
    OP_DIV,       // dst = src1 / src2
    OP_LT, OP_LE, OP_GT, OP_GE, OP_EQ, OP_NE,
    OP_JUMP,      // unconditional jump
    OP_BRANCH,    // conditional branch (if src1 goto target)
    OP_CALL,      // dst = call func(args)
    OP_RETURN,    // return src1
    OP_PARAM,     // push parameter
    OP_LABEL      // label for jumps
} OpCode;

typedef struct {
    OpCode op;
    int dst, src1, src2;  // operand indices (into temp array or var table)
    int value;            // for constants
    int target;           // for jumps (block id)
    char label[32];       // for labels/functions
    int dead;             // mark for dead code elimination
} Instruction;

/*  BASIC BLOCK  */
typedef struct BasicBlock {
    int id;
    Instruction instrs[100];
    int num_instrs;
    int successors[2];
    int num_successors;
    int predecessors[10];
    int num_predecessors;
    int visited;
    int reachable;
} BasicBlock;

/*  CONTROL FLOW GRAPH  */
typedef struct {
    BasicBlock blocks[MAX_BLOCKS];
    int num_blocks;
} CFG;

/*  FUNCTION  */
typedef struct {
    char name[MAX_IDENT];
    int num_params;
    char params[10][MAX_IDENT];
    CFG cfg;
    int num_locals;
    char locals[MAX_VARS][MAX_IDENT];
} Function;

/*  GLOBAL STATE  */
Token tokens[MAX_TOKENS];
int num_tokens = 0;
int current_token = 0;

Function functions[MAX_FUNCS];
int num_functions = 0;
Function* current_func = NULL;

int temp_counter = 0;
int label_counter = 0;
int block_counter = 0;

char input[50000];

/*  ERROR HANDLING  */
void error(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    fprintf(stderr, "Error: ");
    vfprintf(stderr, fmt, args);
    fprintf(stderr, "\n");
    va_end(args);
    exit(1);
}

/*  LEXER  */
void add_token(TokenType type, const char* text, int value) {
    if (num_tokens >= MAX_TOKENS) error("Too many tokens");
    tokens[num_tokens].type = type;
    strncpy(tokens[num_tokens].text, text, MAX_IDENT - 1);
    tokens[num_tokens].value = value;
    num_tokens++;
}

void tokenize(char* src) {
    int i = 0;
    while (src[i]) {
        // Skip whitespace
        while (isspace(src[i])) i++;
        if (!src[i]) break;
        
        // Comments
        if (src[i] == '/' && src[i+1] == '/') {
            while (src[i] && src[i] != '\n') i++;
            continue;
        }
        
        // Keywords and identifiers
        if (isalpha(src[i]) || src[i] == '_') {
            char buf[MAX_IDENT];
            int j = 0;
            while (isalnum(src[i]) || src[i] == '_') buf[j++] = src[i++];
            buf[j] = '\0';
            
            if (strcmp(buf, "int") == 0) add_token(TOK_INT, buf, 0);
            else if (strcmp(buf, "return") == 0) add_token(TOK_RETURN, buf, 0);
            else if (strcmp(buf, "if") == 0) add_token(TOK_IF, buf, 0);
            else if (strcmp(buf, "else") == 0) add_token(TOK_ELSE, buf, 0);
            else if (strcmp(buf, "while") == 0) add_token(TOK_WHILE, buf, 0);
            else add_token(TOK_IDENT, buf, 0);
            continue;
        }
        
        // Numbers
        if (isdigit(src[i])) {
            int val = 0;
            while (isdigit(src[i])) val = val * 10 + (src[i++] - '0');
            add_token(TOK_NUMBER, "", val);
            continue;
        }
        
        // Operators and punctuation
        switch (src[i]) {
            case '(': add_token(TOK_LPAREN, "(", 0); i++; break;
            case ')': add_token(TOK_RPAREN, ")", 0); i++; break;
            case '{': add_token(TOK_LBRACE, "{", 0); i++; break;
            case '}': add_token(TOK_RBRACE, "}", 0); i++; break;
            case ';': add_token(TOK_SEMICOLON, ";", 0); i++; break;
            case ',': add_token(TOK_COMMA, ",", 0); i++; break;
            case '+': add_token(TOK_PLUS, "+", 0); i++; break;
            case '-': add_token(TOK_MINUS, "-", 0); i++; break;
            case '*': add_token(TOK_STAR, "*", 0); i++; break;
            case '/': add_token(TOK_SLASH, "/", 0); i++; break;
            case '=':
                if (src[i+1] == '=') { add_token(TOK_EQ, "==", 0); i += 2; }
                else { add_token(TOK_ASSIGN, "=", 0); i++; }
                break;
            case '!':
                if (src[i+1] == '=') { add_token(TOK_NE, "!=", 0); i += 2; }
                else i++;
                break;
            case '<':
                if (src[i+1] == '=') { add_token(TOK_LE, "<=", 0); i += 2; }
                else { add_token(TOK_LT, "<", 0); i++; }
                break;
            case '>':
                if (src[i+1] == '=') { add_token(TOK_GE, ">=", 0); i += 2; }
                else { add_token(TOK_GT, ">", 0); i++; }
                break;
            case '&':
                if (src[i+1] == '&') { add_token(TOK_AND, "&&", 0); i += 2; }
                else i++;
                break;
            case '|':
                if (src[i+1] == '|') { add_token(TOK_OR, "||", 0); i += 2; }
                else i++;
                break;
            default: i++;
        }
    }
    add_token(TOK_EOF, "", 0);
}

Token peek() {
    return tokens[current_token];
}

Token consume() {
    return tokens[current_token++];
}

int match(TokenType type) {
    if (peek().type == type) {
        consume();
        return 1;
    }
    return 0;
}

void expect(TokenType type) {
    if (!match(type)) error("Expected token type %d", type);
}

/*  IR GENERATION  */
int new_temp() {
    return 1000 + temp_counter++;
}

int get_var_index(const char* name) {
    for (int i = 0; i < current_func->num_locals; i++) {
        if (strcmp(current_func->locals[i], name) == 0) return i;
    }
    // Add new local
    if (current_func->num_locals >= MAX_VARS) error("Too many variables");
    strcpy(current_func->locals[current_func->num_locals], name);
    return current_func->num_locals++;
}

BasicBlock* new_block() {
    CFG* cfg = &current_func->cfg;
    if (cfg->num_blocks >= MAX_BLOCKS) error("Too many blocks");
    BasicBlock* b = &cfg->blocks[cfg->num_blocks];
    b->id = cfg->num_blocks++;
    b->num_instrs = 0;
    b->num_successors = 0;
    b->num_predecessors = 0;
    b->visited = 0;
    b->reachable = 0;
    return b;
}

void emit(BasicBlock* block, Instruction instr) {
    if (block->num_instrs >= 100) error("Block too large");
    block->instrs[block->num_instrs++] = instr;
}

void add_successor(BasicBlock* from, BasicBlock* to) {
    if (from->num_successors >= 2) return;
    from->successors[from->num_successors++] = to->id;
    to->predecessors[to->num_predecessors++] = from->id;
}

/*  PARSER  */
int parse_expr(BasicBlock* block);
BasicBlock* parse_stmt(BasicBlock* block);

int parse_primary(BasicBlock* block) {
    Token tok = peek();
    
    if (tok.type == TOK_NUMBER) {
        consume();
        int t = new_temp();
        Instruction instr = {OP_CONST, t, 0, 0, tok.value, 0, "", 0};
        emit(block, instr);
        return t;
    }
    
    if (tok.type == TOK_IDENT) {
        consume();
        
        // Check for function call
        if (peek().type == TOK_LPAREN) {
            expect(TOK_LPAREN);
            
            // Parse arguments
            int arg_count = 0;
            while (peek().type != TOK_RPAREN) {
                int arg = parse_expr(block);
                Instruction param = {OP_PARAM, 0, arg, 0, 0, 0, "", 0};
                emit(block, param);
                arg_count++;
                if (peek().type == TOK_COMMA) consume();
            }
            expect(TOK_RPAREN);
            
            int t = new_temp();
            Instruction call = {OP_CALL, t, 0, 0, arg_count, 0, "", 0};
            strcpy(call.label, tok.text);
            emit(block, call);
            return t;
        }
        
        // Variable reference
        int var = get_var_index(tok.text);
        int t = new_temp();
        Instruction instr = {OP_COPY, t, var, 0, 0, 0, "", 0};
        emit(block, instr);
        return t;
    }
    
    if (tok.type == TOK_LPAREN) {
        consume();
        int result = parse_expr(block);
        expect(TOK_RPAREN);
        return result;
    }
    
    error("Unexpected token in expression");
    return 0;
}

int parse_term(BasicBlock* block) {
    int left = parse_primary(block);
    
    while (peek().type == TOK_STAR || peek().type == TOK_SLASH) {
        TokenType op = consume().type;
        int right = parse_primary(block);
        int t = new_temp();
        Instruction instr = {op == TOK_STAR ? OP_MUL : OP_DIV, t, left, right, 0, 0, "", 0};
        emit(block, instr);
        left = t;
    }
    
    return left;
}

int parse_arith(BasicBlock* block) {
    int left = parse_term(block);
    
    while (peek().type == TOK_PLUS || peek().type == TOK_MINUS) {
        TokenType op = consume().type;
        int right = parse_term(block);
        int t = new_temp();
        Instruction instr = {op == TOK_PLUS ? OP_ADD : OP_SUB, t, left, right, 0, 0, "", 0};
        emit(block, instr);
        left = t;
    }
    
    return left;
}

int parse_comparison(BasicBlock* block) {
    int left = parse_arith(block);
    
    TokenType tt = peek().type;
    if (tt == TOK_LT || tt == TOK_LE || tt == TOK_GT || 
        tt == TOK_GE || tt == TOK_EQ || tt == TOK_NE) {
        consume();
        int right = parse_arith(block);
        int t = new_temp();
        OpCode op = (tt == TOK_LT ? OP_LT : tt == TOK_LE ? OP_LE : 
                     tt == TOK_GT ? OP_GT : tt == TOK_GE ? OP_GE :
                     tt == TOK_EQ ? OP_EQ : OP_NE);
        Instruction instr = {op, t, left, right, 0, 0, "", 0};
        emit(block, instr);
        return t;
    }
    
    return left;
}

int parse_expr(BasicBlock* block) {
    return parse_comparison(block);
}

BasicBlock* parse_stmt(BasicBlock* block) {
    Token tok = peek();
    
    // Variable declaration with optional initialisation
    if (tok.type == TOK_INT) {
        consume();
        Token name = consume();
        if (name.type != TOK_IDENT) error("Expected variable name");
        int var = get_var_index(name.text);
        
        if (match(TOK_ASSIGN)) {
            int expr = parse_expr(block);
            Instruction instr = {OP_COPY, var, expr, 0, 0, 0, "", 0};
            emit(block, instr);
        }
        expect(TOK_SEMICOLON);
        return block;
    }
    
    // Assignment
    if (tok.type == TOK_IDENT) {
        Token name = consume();
        if (match(TOK_ASSIGN)) {
            int var = get_var_index(name.text);
            int expr = parse_expr(block);
            Instruction instr = {OP_COPY, var, expr, 0, 0, 0, "", 0};
            emit(block, instr);
            expect(TOK_SEMICOLON);
        }
        return block;
    }
    
    // Return statement
    if (match(TOK_RETURN)) {
        int expr = parse_expr(block);
        Instruction instr = {OP_RETURN, 0, expr, 0, 0, 0, "", 0};
        emit(block, instr);
        expect(TOK_SEMICOLON);
        return block;
    }
    
    // If statement
    if (match(TOK_IF)) {
        expect(TOK_LPAREN);
        int cond = parse_expr(block);
        expect(TOK_RPAREN);
        
        BasicBlock* then_block = new_block();
        BasicBlock* else_block = new_block();
        BasicBlock* merge_block = new_block();
        
        Instruction branch = {OP_BRANCH, 0, cond, 0, 0, then_block->id, "", 0};
        emit(block, branch);
        add_successor(block, then_block);
        add_successor(block, else_block);
        
        // Parse then branch
        expect(TOK_LBRACE);
        BasicBlock* then_end = then_block;
        while (!match(TOK_RBRACE)) {
            then_end = parse_stmt(then_end);
        }
        Instruction jump1 = {OP_JUMP, 0, 0, 0, 0, merge_block->id, "", 0};
        emit(then_end, jump1);
        add_successor(then_end, merge_block);
        
        // Parse else branch
        BasicBlock* else_end = else_block;
        if (match(TOK_ELSE)) {
            expect(TOK_LBRACE);
            while (!match(TOK_RBRACE)) {
                else_end = parse_stmt(else_end);
            }
        }
        Instruction jump2 = {OP_JUMP, 0, 0, 0, 0, merge_block->id, "", 0};
        emit(else_end, jump2);
        add_successor(else_end, merge_block);
        
        return merge_block;
    }
    
    // While loop
    if (match(TOK_WHILE)) {
        expect(TOK_LPAREN);
        
        BasicBlock* cond_block = new_block();
        Instruction jump_to_cond = {OP_JUMP, 0, 0, 0, 0, cond_block->id, "", 0};
        emit(block, jump_to_cond);
        add_successor(block, cond_block);
        
        int cond = parse_expr(cond_block);
        expect(TOK_RPAREN);
        
        BasicBlock* body_block = new_block();
        BasicBlock* exit_block = new_block();
        
        Instruction branch = {OP_BRANCH, 0, cond, 0, 0, body_block->id, "", 0};
        emit(cond_block, branch);
        add_successor(cond_block, body_block);
        add_successor(cond_block, exit_block);
        
        // Parse body
        expect(TOK_LBRACE);
        BasicBlock* body_end = body_block;
        while (!match(TOK_RBRACE)) {
            body_end = parse_stmt(body_end);
        }
        
        Instruction back_jump = {OP_JUMP, 0, 0, 0, 0, cond_block->id, "", 0};
        emit(body_end, back_jump);
        add_successor(body_end, cond_block);
        
        return exit_block;
    }
    
    return block;
}

void parse_function() {
    expect(TOK_INT);
    Token name = consume();
    
    if (num_functions >= MAX_FUNCS) error("Too many functions");
    current_func = &functions[num_functions++];
    strcpy(current_func->name, name.text);
    current_func->num_params = 0;
    current_func->num_locals = 0;
    current_func->cfg.num_blocks = 0;
    
    expect(TOK_LPAREN);
    // Parse parameters (simplified - just names)
    while (peek().type == TOK_INT) {
        consume();
        Token param = consume();
        strcpy(current_func->params[current_func->num_params++], param.text);
        get_var_index(param.text);
        if (peek().type == TOK_COMMA) consume();
    }
    expect(TOK_RPAREN);
    
    expect(TOK_LBRACE);
    BasicBlock* entry = new_block();
    BasicBlock* current = entry;
    
    while (!match(TOK_RBRACE)) {
        current = parse_stmt(current);
    }
}


/*  OPTIMISATIONS  */

// Mark reachable blocks
void mark_reachable(CFG* cfg) {
    if (cfg->num_blocks == 0) return;
    
    int queue[MAX_BLOCKS], front = 0, back = 0;
    
    queue[back++] = 0;
    cfg->blocks[0].reachable = 1;
    
    while (front < back) {
        int bid = queue[front++];
        BasicBlock* b = &cfg->blocks[bid];
        
        for (int i = 0; i < b->num_successors; i++) {
            int succ = b->successors[i];
            if (!cfg->blocks[succ].reachable) {
                cfg->blocks[succ].reachable = 1;
                queue[back++] = succ;
            }
        }
    }
}

// Dead code elimination
void eliminate_dead_code(CFG* cfg) {
    mark_reachable(cfg);
    
    for (int i = 0; i < cfg->num_blocks; i++) {
        BasicBlock* b = &cfg->blocks[i];
        if (!b->reachable) {
            b->num_instrs = 0;
            continue;
        }
        
        // Remove instructions that don't contribute to output
        for (int j = 0; j < b->num_instrs; j++) {
            Instruction* instr = &b->instrs[j];
            
            // Keep: returns, calls, branches, jumps
            if (instr->op == OP_RETURN || instr->op == OP_CALL ||
                instr->op == OP_BRANCH || instr->op == OP_JUMP) {
                continue;
            }
            
            // Keep any instruction that writes to a variable (not a temp)
            // Variables might be used across blocks or in loops
            if (instr->dst < 1000) {
                continue;
            }
            
            // Check if result is used
            int dst = instr->dst;
            int used = 0;
            
            for (int k = j + 1; k < b->num_instrs; k++) {
                if (b->instrs[k].src1 == dst || b->instrs[k].src2 == dst) {
                    used = 1;
                    break;
                }
            }
            
            if (!used) instr->dead = 1;
        }
    }
}

// Constant folding
void constant_folding(CFG* cfg) {
    for (int i = 0; i < cfg->num_blocks; i++) {
        BasicBlock* b = &cfg->blocks[i];
        
        for (int j = 0; j < b->num_instrs; j++) {
            Instruction* instr = &b->instrs[j];
            
            // Check if both operands are constants
            if (instr->op >= OP_ADD && instr->op <= OP_DIV) {
                Instruction* src1_instr = NULL;
                Instruction* src2_instr = NULL;
                
                // Find source instructions
                for (int k = 0; k < j; k++) {
                    if (b->instrs[k].dst == instr->src1 && b->instrs[k].op == OP_CONST)
                        src1_instr = &b->instrs[k];
                    if (b->instrs[k].dst == instr->src2 && b->instrs[k].op == OP_CONST)
                        src2_instr = &b->instrs[k];
                }
                
                if (src1_instr && src2_instr) {
                    int val1 = src1_instr->value;
                    int val2 = src2_instr->value;
                    int result = 0;
                    
                    switch (instr->op) {
                        case OP_ADD: result = val1 + val2; break;
                        case OP_SUB: result = val1 - val2; break;
                        case OP_MUL: result = val1 * val2; break;
                        case OP_DIV: if (val2 != 0) result = val1 / val2; break;
                        default: break;
                    }
                    
                    instr->op = OP_CONST;
                    instr->value = result;
                    instr->src1 = instr->src2 = 0;
                }
            }
        }
    }
}

// Future: Common subexpression elimination can be added here
void common_subexpression_elimination(CFG* cfg) {
    // Not implemented in this version
}

void optimize(Function* func) {
    constant_folding(&func->cfg);
    eliminate_dead_code(&func->cfg);
}

/*  CODE GENERATION  */

void generate_c_code() {
    printf("#include <stdio.h>\n\n");
    
    for (int f = 0; f < num_functions; f++) {
        Function* func = &functions[f];
        
        printf("int %s(", func->name);
        for (int i = 0; i < func->num_params; i++) {
            printf("int %s", func->params[i]);
            if (i < func->num_params - 1) printf(", ");
        }
        printf(") {\n");
        
        // Declare locals and temps
        for (int i = func->num_params; i < func->num_locals; i++) {
            printf("    int %s;\n", func->locals[i]);
        }
        printf("    int t[%d] = {0};\n", temp_counter);
        
        // Generate code for each block
        CFG* cfg = &func->cfg;
        for (int b = 0; b < cfg->num_blocks; b++) {
            BasicBlock* block = &cfg->blocks[b];
            if (!block->reachable) continue;
            
            printf("L%d:\n", block->id);
            
            for (int i = 0; i < block->num_instrs; i++) {
                Instruction* instr = &block->instrs[i];
                if (instr->dead) continue;
                
                char dst[64], src1[64], src2[64];
                
                if (instr->dst < 1000) sprintf(dst, "%s", func->locals[instr->dst]);
                else sprintf(dst, "t[%d]", instr->dst - 1000);
                
                if (instr->src1 < 1000 && instr->src1 >= 0) sprintf(src1, "%s", func->locals[instr->src1]);
                else if (instr->src1 >= 1000) sprintf(src1, "t[%d]", instr->src1 - 1000);
                
                if (instr->src2 < 1000 && instr->src2 >= 0) sprintf(src2, "%s", func->locals[instr->src2]);
                else if (instr->src2 >= 1000) sprintf(src2, "t[%d]", instr->src2 - 1000);
                
                switch (instr->op) {
                    case OP_PARAM:
                        // Skip - handled by OP_CALL
                        break;
                    case OP_CONST:
                        printf("    %s = %d;\n", dst, instr->value);
                        break;
                    case OP_COPY:
                        printf("    %s = %s;\n", dst, src1);
                        break;
                    case OP_ADD:
                        printf("    %s = %s + %s;\n", dst, src1, src2);
                        break;
                    case OP_SUB:
                        printf("    %s = %s - %s;\n", dst, src1, src2);
                        break;
                    case OP_MUL:
                        printf("    %s = %s * %s;\n", dst, src1, src2);
                        break;
                    case OP_DIV:
                        printf("    %s = %s / %s;\n", dst, src1, src2);
                        break;
                    case OP_LT:
                        printf("    %s = %s < %s;\n", dst, src1, src2);
                        break;
                    case OP_LE:
                        printf("    %s = %s <= %s;\n", dst, src1, src2);
                        break;
                    case OP_GT:
                        printf("    %s = %s > %s;\n", dst, src1, src2);
                        break;
                    case OP_GE:
                        printf("    %s = %s >= %s;\n", dst, src1, src2);
                        break;
                    case OP_EQ:
                        printf("    %s = %s == %s;\n", dst, src1, src2);
                        break;
                    case OP_NE:
                        printf("    %s = %s != %s;\n", dst, src1, src2);
                        break;
                    case OP_BRANCH:
                        printf("    if (%s) goto L%d; else goto L%d;\n", 
                               src1, instr->target, block->successors[1]);
                        break;
                    case OP_JUMP:
                        printf("    goto L%d;\n", instr->target);
                        break;
                    case OP_RETURN:
                        printf("    return %s;\n", src1);
                        break;
                    case OP_CALL: {
                        // Collect parameters from preceding OP_PARAM instructions
                        int params[10];
                        int param_count = 0;
                        for (int k = i - 1; k >= 0 && param_count < instr->value; k--) {
                            if (block->instrs[k].op == OP_PARAM) {
                                params[param_count++] = block->instrs[k].src1;
                            }
                        }
                        
                        printf("    %s = %s(", dst, instr->label);
                        for (int p = param_count - 1; p >= 0; p--) {
                            if (params[p] < 1000) 
                                printf("%s", func->locals[params[p]]);
                            else 
                                printf("t[%d]", params[p] - 1000);
                            if (p > 0) printf(", ");
                        }
                        printf(");\n");
                        break;
                    }
                    default:
                        break;
                }
            }
        }
        
        printf("}\n\n");
    }
}


int main() {

    // Read input
    int len = fread(input, 1, sizeof(input) - 1, stdin);
    input[len] = '\0';
    
    // Tokenize
    tokenize(input);
    
    // Parse all functions
    while (peek().type != TOK_EOF) {
        parse_function();
    }
    
    // Optimise each function
    for (int i = 0; i < num_functions; i++) {
        optimize(&functions[i]);
    }
    
    // Generate C code
    generate_c_code();
    
    return 0;
}
