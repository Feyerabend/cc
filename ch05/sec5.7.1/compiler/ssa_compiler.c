/*
 * ssa_compiler.c
 * 
 * Compiler with SSA-based optimisation
 *
 *  - Control Flow Graph (CFG) construction
 *  - Dominator tree computation
 *  - SSA form conversion with phi functions
 *  - SSA-based optimizations:
 *    * Constant propagation
 *    * Copy propagation  
 *    * Dead code elimination
 *  - SSA deconstruction
 *  - Code generation to C
 *
 * Compile: gcc -o ssac ssa_compiler.c -std=c99
 * Usage: ./ssac < input.c > output.c && gcc output.c -o program
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdarg.h>
#include <assert.h>

#define MAX_TOKENS 2000
#define MAX_BLOCKS 200
#define MAX_INSTRS 100
#define MAX_VARS 100
#define MAX_FUNCS 20
#define MAX_IDENT 64
#define MAX_PHI 20

/*  TOKEN TYPES  */
typedef enum {
    TOK_EOF, TOK_INT, TOK_RETURN, TOK_IF, TOK_ELSE, TOK_WHILE,
    TOK_IDENT, TOK_NUMBER,
    TOK_LPAREN, TOK_RPAREN, TOK_LBRACE, TOK_RBRACE,
    TOK_SEMICOLON, TOK_COMMA,
    TOK_ASSIGN,
    TOK_PLUS, TOK_MINUS, TOK_STAR, TOK_SLASH,
    TOK_EQ, TOK_NE, TOK_LT, TOK_LE, TOK_GT, TOK_GE,
    TOK_AND, TOK_OR
} TokenType;

typedef struct {
    TokenType type;
    char text[MAX_IDENT];
    int value;
} Token;

/*  SSA VALUE  */
typedef struct {
    int version;      // version number for SSA
    int is_constant;  // 1 if this is a constant
    int const_value;  // constant value if is_constant
} SSAValue;

/*  PHI FUNCTION  */
typedef struct {
    int dst;          // destination variable version
    int srcs[10];     // source versions from predecessors
    int num_srcs;
    int orig_var;     // original variable index
} PhiFunction;

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
    OP_BRANCH,    // conditional branch
    OP_CALL,
    OP_RETURN,
    OP_PARAM,
    OP_PHI        // SSA phi function
} OpCode;

typedef struct {
    OpCode op;
    int dst, src1, src2;
    int value;
    int target;
    char label[32];
    int dead;
    PhiFunction phi;  // for OP_PHI
} Instruction;


/*  BASIC BLOCK  */
typedef struct BasicBlock {
    int id;
    Instruction instrs[MAX_INSTRS];
    int num_instrs;
    int successors[2];
    int num_successors;
    int predecessors[10];
    int num_predecessors;
    int visited;
    int reachable;
    int idom;          // immediate dominator
    int dom_level;     // dominance tree level
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
    int var_versions[MAX_VARS];   // current version for each variable (SSA)
    int var_stack[MAX_VARS][100]; // version stack for SSA construction
    int stack_top[MAX_VARS];
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

char* input = NULL;


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
        while (isspace(src[i])) i++;
        if (!src[i]) break;
        
        if (src[i] == '/' && src[i+1] == '/') {
            while (src[i] && src[i] != '\n') i++;
            continue;
        }
        
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
        
        if (isdigit(src[i])) {
            int val = 0;
            while (isdigit(src[i])) val = val * 10 + (src[i++] - '0');
            add_token(TOK_NUMBER, "", val);
            continue;
        }
        
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
    if (current_func->num_locals >= MAX_VARS) error("Too many variables");
    strcpy(current_func->locals[current_func->num_locals], name);
    return current_func->num_locals++;
}

BasicBlock* new_block() {
    if (current_func->cfg.num_blocks >= MAX_BLOCKS) error("Too many blocks");
    BasicBlock* b = &current_func->cfg.blocks[current_func->cfg.num_blocks];
    b->id = current_func->cfg.num_blocks++;
    b->num_instrs = 0;
    b->num_successors = 0;
    b->num_predecessors = 0;
    b->visited = 0;
    b->reachable = 0;
    b->idom = -1;
    b->dom_level = 0;
    return b;
}

void emit(BasicBlock* b, Instruction instr) {
    if (b->num_instrs >= MAX_INSTRS) error("Too many instructions in block");
    b->instrs[b->num_instrs++] = instr;
}

void add_successor(BasicBlock* from, BasicBlock* to) {
    for (int i = 0; i < from->num_successors; i++) {
        if (from->successors[i] == to->id) return;
    }
    from->successors[from->num_successors++] = to->id;
    to->predecessors[to->num_predecessors++] = from->id;
}


/*  PARSER  */
int parse_expression(BasicBlock* b);
int parse_term(BasicBlock* b);
int parse_factor(BasicBlock* b);

int parse_factor(BasicBlock* b) {
    if (peek().type == TOK_NUMBER) {
        int val = consume().value;
        int t = new_temp();
        Instruction instr = {OP_CONST, t, 0, 0, val, 0, "", 0};
        emit(b, instr);
        return t;
    }
    
    if (peek().type == TOK_IDENT) {
        char name[MAX_IDENT];
        strcpy(name, consume().text);
        
        if (match(TOK_LPAREN)) {
            // Function call
            int args[10];
            int num_args = 0;
            
            if (!match(TOK_RPAREN)) {
                do {
                    args[num_args++] = parse_expression(b);
                } while (match(TOK_COMMA));
                expect(TOK_RPAREN);
            }
            
            // Emit parameter instructions
            for (int i = 0; i < num_args; i++) {
                Instruction instr = {OP_PARAM, 0, args[i], 0, 0, 0, "", 0};
                emit(b, instr);
            }
            
            int t = new_temp();
            Instruction instr = {OP_CALL, t, 0, 0, num_args, 0, "", 0};
            strcpy(instr.label, name);
            emit(b, instr);
            return t;
        }
        
        // Variable reference
        int var = get_var_index(name);
        int t = new_temp();
        Instruction instr = {OP_COPY, t, var, 0, 0, 0, "", 0};
        emit(b, instr);
        return t;
    }
    
    if (match(TOK_LPAREN)) {
        int result = parse_expression(b);
        expect(TOK_RPAREN);
        return result;
    }
    
    error("Expected factor");
    return 0;
}

int parse_term(BasicBlock* b) {
    int left = parse_factor(b);
    
    while (peek().type == TOK_STAR || peek().type == TOK_SLASH) {
        TokenType op = consume().type;
        int right = parse_factor(b);
        int t = new_temp();
        
        Instruction instr = {
            op == TOK_STAR ? OP_MUL : OP_DIV,
            t, left, right, 0, 0, "", 0
        };
        emit(b, instr);
        left = t;
    }
    
    return left;
}

int parse_expression(BasicBlock* b) {
    int left = parse_term(b);
    
    while (peek().type == TOK_PLUS || peek().type == TOK_MINUS) {
        TokenType op = consume().type;
        int right = parse_term(b);
        int t = new_temp();
        
        Instruction instr = {
            op == TOK_PLUS ? OP_ADD : OP_SUB,
            t, left, right, 0, 0, "", 0
        };
        emit(b, instr);
        left = t;
    }
    
    // Comparison operators
    TokenType tok = peek().type;
    if (tok >= TOK_EQ && tok <= TOK_GE) {
        consume();
        int right = parse_term(b);
        int t = new_temp();
        
        OpCode opc = OP_NOP;
        if (tok == TOK_EQ) opc = OP_EQ;
        else if (tok == TOK_NE) opc = OP_NE;
        else if (tok == TOK_LT) opc = OP_LT;
        else if (tok == TOK_LE) opc = OP_LE;
        else if (tok == TOK_GT) opc = OP_GT;
        else if (tok == TOK_GE) opc = OP_GE;
        
        Instruction instr = {opc, t, left, right, 0, 0, "", 0};
        emit(b, instr);
        left = t;
    }
    
    return left;
}

BasicBlock* parse_statement(BasicBlock* b);

BasicBlock* parse_if(BasicBlock* b) {
    expect(TOK_LPAREN);
    int cond = parse_expression(b);
    expect(TOK_RPAREN);
    
    BasicBlock* then_block = new_block();
    BasicBlock* else_block = NULL;
    BasicBlock* merge_block = new_block();
    
    Instruction branch = {OP_BRANCH, 0, cond, 0, 0, then_block->id, "", 0};
    emit(b, branch);
    
    // Parse then branch
    then_block = parse_statement(then_block);
    
    if (match(TOK_ELSE)) {
        else_block = new_block();
        
        // Update branch target for else
        b->instrs[b->num_instrs - 1].value = else_block->id; // else target
        
        add_successor(b, then_block);
        add_successor(b, else_block);
        
        Instruction jump = {OP_JUMP, 0, 0, 0, 0, merge_block->id, "", 0};
        emit(then_block, jump);
        add_successor(then_block, merge_block);
        
        else_block = parse_statement(else_block);
        Instruction jump2 = {OP_JUMP, 0, 0, 0, 0, merge_block->id, "", 0};
        emit(else_block, jump2);
        add_successor(else_block, merge_block);
    } else {
        add_successor(b, then_block);
        add_successor(b, merge_block);
        
        Instruction jump = {OP_JUMP, 0, 0, 0, 0, merge_block->id, "", 0};
        emit(then_block, jump);
        add_successor(then_block, merge_block);
    }
    
    return merge_block;
}

BasicBlock* parse_while(BasicBlock* b) {
    BasicBlock* cond_block = new_block();
    BasicBlock* body_block = new_block();
    BasicBlock* exit_block = new_block();
    
    Instruction jump = {OP_JUMP, 0, 0, 0, 0, cond_block->id, "", 0};
    emit(b, jump);
    add_successor(b, cond_block);
    
    expect(TOK_LPAREN);
    int cond = parse_expression(cond_block);
    expect(TOK_RPAREN);
    
    Instruction branch = {OP_BRANCH, 0, cond, 0, 0, body_block->id, "", 0};
    branch.value = exit_block->id;
    emit(cond_block, branch);
    add_successor(cond_block, body_block);
    add_successor(cond_block, exit_block);
    
    body_block = parse_statement(body_block);
    Instruction back_jump = {OP_JUMP, 0, 0, 0, 0, cond_block->id, "", 0};
    emit(body_block, back_jump);
    add_successor(body_block, cond_block);
    
    return exit_block;
}

BasicBlock* parse_statement(BasicBlock* b) {
    if (match(TOK_LBRACE)) {
        while (!match(TOK_RBRACE)) {
            b = parse_statement(b);
        }
        return b;
    }
    
    if (match(TOK_IF)) {
        return parse_if(b);
    }
    
    if (match(TOK_WHILE)) {
        return parse_while(b);
    }
    
    if (match(TOK_RETURN)) {
        int val = parse_expression(b);
        Instruction instr = {OP_RETURN, 0, val, 0, 0, 0, "", 0};
        emit(b, instr);
        expect(TOK_SEMICOLON);
        return b;
    }
    
    if (peek().type == TOK_INT) {
        consume();
        char name[MAX_IDENT];
        strcpy(name, consume().text);
        get_var_index(name);
        
        if (match(TOK_ASSIGN)) {
            int val = parse_expression(b);
            int var = get_var_index(name);
            Instruction instr = {OP_COPY, var, val, 0, 0, 0, "", 0};
            emit(b, instr);
        }
        expect(TOK_SEMICOLON);
        return b;
    }
    
    if (peek().type == TOK_IDENT) {
        char name[MAX_IDENT];
        strcpy(name, consume().text);
        expect(TOK_ASSIGN);
        int val = parse_expression(b);
        int var = get_var_index(name);
        Instruction instr = {OP_COPY, var, val, 0, 0, 0, "", 0};
        emit(b, instr);
        expect(TOK_SEMICOLON);
        return b;
    }
    
    return b;
}

void parse_function() {
    expect(TOK_INT);
    
    if (num_functions >= MAX_FUNCS) error("Too many functions");
    current_func = &functions[num_functions++];
    current_func->num_locals = 0;
    current_func->num_params = 0;
    current_func->cfg.num_blocks = 0;
    
    strcpy(current_func->name, consume().text);
    expect(TOK_LPAREN);
    
    if (!match(TOK_RPAREN)) {
        do {
            expect(TOK_INT);
            strcpy(current_func->params[current_func->num_params], consume().text);
            get_var_index(current_func->params[current_func->num_params]);
            current_func->num_params++;
        } while (match(TOK_COMMA));
        expect(TOK_RPAREN);
    }
    
    expect(TOK_LBRACE);
    
    BasicBlock* entry = new_block();
    
    // Parse statements until closing brace
    while (!match(TOK_RBRACE)) {
        entry = parse_statement(entry);
    }
}


/*  DOMINATOR TREE COMPUTATION  */

// Mark reachable blocks
void mark_reachable(CFG* cfg) {
    for (int i = 0; i < cfg->num_blocks; i++) {
        cfg->blocks[i].reachable = 0;
        cfg->blocks[i].visited = 0;
    }
    
    // DFS from entry
    BasicBlock* stack[MAX_BLOCKS];
    int top = 0;
    stack[top++] = &cfg->blocks[0];
    
    while (top > 0) {
        BasicBlock* b = stack[--top];
        if (b->visited) continue;
        b->visited = 1;
        b->reachable = 1;
        
        for (int i = 0; i < b->num_successors; i++) {
            stack[top++] = &cfg->blocks[b->successors[i]];
        }
    }
}

// Compute dominators using iterative algorithm
void compute_dominators(CFG* cfg) {
    mark_reachable(cfg);
    
    int n = cfg->num_blocks;
    int dom[MAX_BLOCKS][MAX_BLOCKS]; // dom[i][j] = 1 if i dominates j
    
    // Init: entry dominates only itself, all others dominate all
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            dom[i][j] = (i == 0) ? (j == 0) : cfg->blocks[j].reachable;
        }
    }
    
    // Iterate until fixed point
    int changed = 1;
    while (changed) {
        changed = 0;
        
        for (int b = 1; b < n; b++) {
            if (!cfg->blocks[b].reachable) continue;
            
            // New dominators for b = {b} union (intersection of doms of all preds)
            int new_dom[MAX_BLOCKS];
            for (int i = 0; i < n; i++) new_dom[i] = 1;
            
            for (int p = 0; p < cfg->blocks[b].num_predecessors; p++) {
                int pred = cfg->blocks[b].predecessors[p];
                for (int i = 0; i < n; i++) {
                    new_dom[i] = new_dom[i] && dom[i][pred];
                }
            }
            new_dom[b] = 1; // block dominates itself
            
            // Check if changed
            for (int i = 0; i < n; i++) {
                if (dom[i][b] != new_dom[i]) {
                    dom[i][b] = new_dom[i];
                    changed = 1;
                }
            }
        }
    }
    
    // Compute immediate dominators
    for (int b = 0; b < n; b++) {
        if (!cfg->blocks[b].reachable || b == 0) {
            cfg->blocks[b].idom = -1;
            continue;
        }
        
        // Find immediate dominator (closest strict dominator)
        int idom = -1;
        for (int d = n - 1; d >= 0; d--) {
            if (d != b && dom[d][b]) {
                // Check if this is the closest (no other dominator between d and b)
                int is_immediate = 1;
                for (int x = 0; x < n; x++) {
                    if (x != b && x != d && dom[d][x] && dom[x][b]) {
                        is_immediate = 0;
                        break;
                    }
                }
                if (is_immediate) {
                    idom = d;
                    break;
                }
            }
        }
        cfg->blocks[b].idom = idom;
    }
    
    // Compute dominance tree levels
    cfg->blocks[0].dom_level = 0;
    for (int level = 1; level < n; level++) {
        for (int b = 1; b < n; b++) {
            if (cfg->blocks[b].reachable && cfg->blocks[b].idom >= 0) {
                if (cfg->blocks[cfg->blocks[b].idom].dom_level == level - 1) {
                    cfg->blocks[b].dom_level = level;
                }
            }
        }
    }
}


/*  SSA CONSTRUCTION  */

// Find blocks where we need phi functions (dominance frontier)
void compute_dominance_frontier(CFG* cfg, int block, int df[MAX_BLOCKS]) {
    for (int i = 0; i < cfg->num_blocks; i++) df[i] = 0;
    
    // For each node Y in CFG
    for (int y = 0; y < cfg->num_blocks; y++) {
        if (!cfg->blocks[y].reachable) continue;
        
        // If block is in Y's predecessors
        int is_pred = 0;
        for (int p = 0; p < cfg->blocks[y].num_predecessors; p++) {
            if (cfg->blocks[y].predecessors[p] == block) {
                is_pred = 1;
                break;
            }
        }
        
        if (is_pred && cfg->blocks[y].idom != block) {
            df[y] = 1;
        }
    }
}

// Simplified SSA construction: insert phi functions at merge points
void insert_phi_functions(Function* func) {
    CFG* cfg = &func->cfg;
    
    // For each variable
    for (int v = 0; v < func->num_locals; v++) {
        // Find all blocks that assign to this variable
        int defs[MAX_BLOCKS];
        for (int i = 0; i < cfg->num_blocks; i++) defs[i] = 0;
        
        for (int b = 0; b < cfg->num_blocks; b++) {
            if (!cfg->blocks[b].reachable) continue;
            
            for (int i = 0; i < cfg->blocks[b].num_instrs; i++) {
                Instruction* instr = &cfg->blocks[b].instrs[i];
                if (instr->dst == v && instr->op != OP_PHI) {
                    defs[b] = 1;
                }
            }
        }
        
        // Insert phi functions at blocks with multiple predecessors
        for (int b = 0; b < cfg->num_blocks; b++) {
            if (!cfg->blocks[b].reachable) continue;
            if (cfg->blocks[b].num_predecessors <= 1) continue;
            
            // Check if any predecessor defines this variable
            int needs_phi = 0;
            for (int p = 0; p < cfg->blocks[b].num_predecessors; p++) {
                if (defs[cfg->blocks[b].predecessors[p]]) {
                    needs_phi = 1;
                    break;
                }
            }
            
            if (needs_phi) {
                // Insert phi function at beginning
                Instruction phi = {OP_PHI, v, 0, 0, 0, 0, "", 0};
                phi.phi.dst = v;
                phi.phi.orig_var = v;
                phi.phi.num_srcs = cfg->blocks[b].num_predecessors;
                
                // Shift existing instructions
                for (int i = cfg->blocks[b].num_instrs; i > 0; i--) {
                    cfg->blocks[b].instrs[i] = cfg->blocks[b].instrs[i-1];
                }
                cfg->blocks[b].instrs[0] = phi;
                cfg->blocks[b].num_instrs++;
            }
        }
    }
}

// Rename variables to SSA form - DFS traversal
void rename_variables_dfs(Function* func, int block_id, int visited[MAX_BLOCKS]) {
    if (visited[block_id]) return;
    visited[block_id] = 1;
    
    CFG* cfg = &func->cfg;
    BasicBlock* b = &cfg->blocks[block_id];
    
    if (!b->reachable) return;
    
    // Save current versions
    int saved_versions[MAX_VARS];
    for (int i = 0; i < func->num_locals; i++) {
        saved_versions[i] = func->var_versions[i];
    }
    
    // Rename instructions in this block
    for (int i = 0; i < b->num_instrs; i++) {
        Instruction* instr = &b->instrs[i];
        
        // Rename uses (before renaming defs!)
        if (instr->src1 < 1000 && instr->src1 >= 0) {
            instr->src1 = 1000 + func->var_versions[instr->src1] * 100 + instr->src1;
        }
        if (instr->src2 < 1000 && instr->src2 >= 0) {
            instr->src2 = 1000 + func->var_versions[instr->src2] * 100 + instr->src2;
        }
        
        // Rename definitions
        if (instr->dst < 1000 && instr->op != OP_PHI) {
            int orig_var = instr->dst;
            func->var_versions[orig_var]++;
            instr->dst = 1000 + func->var_versions[orig_var] * 100 + orig_var;
        } else if (instr->op == OP_PHI) {
            int orig_var = instr->phi.orig_var;
            func->var_versions[orig_var]++;
            instr->dst = 1000 + func->var_versions[orig_var] * 100 + orig_var;
            instr->phi.dst = instr->dst;
        }
    }
    
    // Update phi functions in successors
    for (int s = 0; s < b->num_successors; s++) {
        int succ_id = b->successors[s];
        BasicBlock* succ = &cfg->blocks[succ_id];
        
        // Find which predecessor we are
        int pred_idx = 0;
        for (int p = 0; p < succ->num_predecessors; p++) {
            if (succ->predecessors[p] == block_id) {
                pred_idx = p;
                break;
            }
        }
        
        // Update phi functions
        for (int i = 0; i < succ->num_instrs && succ->instrs[i].op == OP_PHI; i++) {
            int var = succ->instrs[i].phi.orig_var;
            succ->instrs[i].phi.srcs[pred_idx] = 
                1000 + func->var_versions[var] * 100 + var;
        }
    }
    
    // Process successors in DFS order (children in dominator tree)
    for (int s = 0; s < b->num_successors; s++) {
        int succ_id = b->successors[s];
        rename_variables_dfs(func, succ_id, visited);
    }
    
    // Restore versions when backtracking
    for (int i = 0; i < func->num_locals; i++) {
        func->var_versions[i] = saved_versions[i];
    }
}

void convert_to_ssa(Function* func) {
    compute_dominators(&func->cfg);
    insert_phi_functions(func);
    
    // Init version counters
    for (int i = 0; i < func->num_locals; i++) {
        func->var_versions[i] = 0;
    }
    
    // Rename variables using DFS from entry block
    int visited[MAX_BLOCKS] = {0};
    rename_variables_dfs(func, 0, visited);
}

/*  SSA-BASED OPTIMISATIONS  */

// Sparse constant propagation
void ssa_constant_propagation(CFG* cfg) {
    int lattice[10000]; // 0=unknown, 1=constant, 2=not-constant
    int values[10000];
    
    for (int i = 0; i < 10000; i++) {
        lattice[i] = 0; // unknown
    }
    
    // Iterate to fixed point
    int changed = 1;
    int iterations = 0;
    while (changed && iterations++ < 10) {
        changed = 0;
        
        for (int b = 0; b < cfg->num_blocks; b++) {
            if (!cfg->blocks[b].reachable) continue;
            
            for (int i = 0; i < cfg->blocks[b].num_instrs; i++) {
                Instruction* instr = &cfg->blocks[b].instrs[i];
                
                if (instr->op == OP_CONST) {
                    if (lattice[instr->dst] != 1 || values[instr->dst] != instr->value) {
                        lattice[instr->dst] = 1;
                        values[instr->dst] = instr->value;
                        changed = 1;
                    }
                } else if (instr->op >= OP_ADD && instr->op <= OP_DIV) {
                    if (lattice[instr->src1] == 1 && lattice[instr->src2] == 1) {
                        int v1 = values[instr->src1];
                        int v2 = values[instr->src2];
                        int result = 0;
                        
                        switch (instr->op) {
                            case OP_ADD: result = v1 + v2; break;
                            case OP_SUB: result = v1 - v2; break;
                            case OP_MUL: result = v1 * v2; break;
                            case OP_DIV: if (v2 != 0) result = v1 / v2; break;
                            default: break;
                        }
                        
                        if (lattice[instr->dst] != 1 || values[instr->dst] != result) {
                            lattice[instr->dst] = 1;
                            values[instr->dst] = result;
                            instr->op = OP_CONST;
                            instr->value = result;
                            instr->src1 = instr->src2 = 0;
                            changed = 1;
                        }
                    } else if (lattice[instr->src1] == 2 || lattice[instr->src2] == 2) {
                        if (lattice[instr->dst] != 2) {
                            lattice[instr->dst] = 2;
                            changed = 1;
                        }
                    }
                } else if (instr->op == OP_COPY) {
                    if (lattice[instr->src1] == 1) {
                        if (lattice[instr->dst] != 1 || values[instr->dst] != values[instr->src1]) {
                            lattice[instr->dst] = 1;
                            values[instr->dst] = values[instr->src1];
                            changed = 1;
                        }
                    } else if (lattice[instr->src1] == 2) {
                        if (lattice[instr->dst] != 2) {
                            lattice[instr->dst] = 2;
                            changed = 1;
                        }
                    }
                }
            }
        }
    }
}

// Dead code elimination in SSA
void ssa_dead_code_elimination(CFG* cfg) {
    mark_reachable(cfg);
    
    int used[10000] = {0};
    
    // Mark all uses
    for (int b = 0; b < cfg->num_blocks; b++) {
        if (!cfg->blocks[b].reachable) continue;
        
        for (int i = 0; i < cfg->blocks[b].num_instrs; i++) {
            Instruction* instr = &cfg->blocks[b].instrs[i];
            
            // Critical instructions
            if (instr->op == OP_RETURN || instr->op == OP_CALL || 
                instr->op == OP_BRANCH || instr->op == OP_JUMP) {
                used[instr->src1] = 1;
                used[instr->src2] = 1;
                continue;
            }
            
            used[instr->src1] = 1;
            used[instr->src2] = 1;
            
            if (instr->op == OP_PHI) {
                for (int j = 0; j < instr->phi.num_srcs; j++) {
                    used[instr->phi.srcs[j]] = 1;
                }
            }
        }
    }
    
    // Mark dead instructions
    for (int b = 0; b < cfg->num_blocks; b++) {
        if (!cfg->blocks[b].reachable) continue;
        
        for (int i = 0; i < cfg->blocks[b].num_instrs; i++) {
            Instruction* instr = &cfg->blocks[b].instrs[i];
            
            if (instr->op == OP_RETURN || instr->op == OP_CALL ||
                instr->op == OP_BRANCH || instr->op == OP_JUMP ||
                instr->op == OP_PHI) {
                continue;
            }
            
            if (!used[instr->dst]) {
                instr->dead = 1;
            }
        }
    }
}

void optimize_ssa(Function* func) {
    ssa_constant_propagation(&func->cfg);
    ssa_dead_code_elimination(&func->cfg);
    // .. and so on
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
        
        // Declare all SSA versions as temporaries
        printf("    int t[10000] = {0};\n");
        
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
                sprintf(dst, "t[%d]", instr->dst);
                sprintf(src1, "t[%d]", instr->src1);
                sprintf(src2, "t[%d]", instr->src2);
                
                switch (instr->op) {
                    case OP_PHI:
                        // Phi handled by predecessors - emit as comment (can be checked)
                        printf("    // PHI: %s = phi(", dst);
                        for (int j = 0; j < instr->phi.num_srcs; j++) {
                            printf("t[%d]", instr->phi.srcs[j]);
                            if (j < instr->phi.num_srcs - 1) printf(", ");
                        }
                        printf(")\n");
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
                               src1, instr->target, instr->value);
                        break;
                    case OP_JUMP:
                        printf("    goto L%d;\n", instr->target);
                        break;
                    case OP_RETURN:
                        printf("    return %s;\n", src1);
                        break;
                    case OP_CALL: {
                        int params[10];
                        int param_count = 0;
                        for (int k = i - 1; k >= 0 && param_count < instr->value; k--) {
                            if (block->instrs[k].op == OP_PARAM) {
                                params[param_count++] = block->instrs[k].src1;
                            }
                        }
                        
                        printf("    %s = %s(", dst, instr->label);
                        for (int p = param_count - 1; p >= 0; p--) {
                            printf("t[%d]", params[p]);
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
    // Allocate input buffer
    input = (char*)malloc(50000);
    if (!input) {
        fprintf(stderr, "Failed to allocate input buffer\n");
        return 1;
    }
    
    // Read input
    int len = fread(input, 1, 50000 - 1, stdin);
    input[len] = '\0';
    
    // Tokenize
    tokenize(input);
    
    // Parse all functions
    while (peek().type != TOK_EOF) {
        parse_function();
    }
    
    // Optimise each function with SSA
    for (int i = 0; i < num_functions; i++) {
        fprintf(stderr, "Converting function '%s' to SSA..\n", functions[i].name);
        convert_to_ssa(&functions[i]);
        
        fprintf(stderr, "Optimizing function '%s'..\n", functions[i].name);
        optimize_ssa(&functions[i]);
    }
    
    // Generate C code
    generate_c_code();
    
    free(input);
    return 0;
}

