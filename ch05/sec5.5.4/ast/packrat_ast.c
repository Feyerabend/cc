#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// AST Node Types
typedef enum {
    NODE_NUMBER,
    NODE_VARIABLE,
    NODE_BINOP,
    NODE_ASSIGNMENT,
    NODE_IF,
    NODE_WHILE,
    NODE_PROGRAM
} NodeType;

typedef struct ASTNode ASTNode;
typedef struct ASTList ASTList;

struct ASTList {
    ASTNode *node;
    ASTList *next;
};

struct ASTNode {
    NodeType type;
    union {
        int number;
        char *variable;
        struct {
            char *op;
            ASTNode *left;
            ASTNode *right;
        } binop;
        struct {
            char *var;
            ASTNode *expr;
        } assignment;
        struct {
            ASTNode *condition;
            ASTList *then_branch;
            ASTList *else_branch;
        } if_stmt;
        struct {
            ASTNode *condition;
            ASTList *body;
        } while_stmt;
        ASTList *program;
    } data;
};

// Parse Result
typedef struct {
    int success;
    ASTNode *node;
    int pos;
} ParseResult;

// Memo Table Entry
typedef struct MemoEntry {
    int is_set;
    ParseResult result;
} MemoEntry;

// Parser State
typedef struct {
    const char *input;
    int length;
    MemoEntry **memo;
    int num_rules;
} Parser;

// Rule IDs for memoization
enum {
    RULE_EXPR,
    RULE_ARITH,
    RULE_TERM,
    RULE_PRIMARY,
    RULE_STMT,
    RULE_ASSIGNMENT,
    RULE_IF,
    RULE_WHILE,
    NUM_RULES
};

// Helper functions
ASTNode *make_number(int value) {
    ASTNode *node = malloc(sizeof(ASTNode));
    node->type = NODE_NUMBER;
    node->data.number = value;
    return node;
}

ASTNode *make_variable(const char *name) {
    ASTNode *node = malloc(sizeof(ASTNode));
    node->type = NODE_VARIABLE;
    node->data.variable = strdup(name);
    return node;
}

ASTNode *make_binop(const char *op, ASTNode *left, ASTNode *right) {
    ASTNode *node = malloc(sizeof(ASTNode));
    node->type = NODE_BINOP;
    node->data.binop.op = strdup(op);
    node->data.binop.left = left;
    node->data.binop.right = right;
    return node;
}

ASTNode *make_assignment(const char *var, ASTNode *expr) {
    ASTNode *node = malloc(sizeof(ASTNode));
    node->type = NODE_ASSIGNMENT;
    node->data.assignment.var = strdup(var);
    node->data.assignment.expr = expr;
    return node;
}

ASTNode *make_if(ASTNode *cond, ASTList *then_br, ASTList *else_br) {
    ASTNode *node = malloc(sizeof(ASTNode));
    node->type = NODE_IF;
    node->data.if_stmt.condition = cond;
    node->data.if_stmt.then_branch = then_br;
    node->data.if_stmt.else_branch = else_br;
    return node;
}

ASTNode *make_while(ASTNode *cond, ASTList *body) {
    ASTNode *node = malloc(sizeof(ASTNode));
    node->type = NODE_WHILE;
    node->data.while_stmt.condition = cond;
    node->data.while_stmt.body = body;
    return node;
}

ASTNode *make_program(ASTList *stmts) {
    ASTNode *node = malloc(sizeof(ASTNode));
    node->type = NODE_PROGRAM;
    node->data.program = stmts;
    return node;
}

ASTList *cons(ASTNode *node, ASTList *next) {
    ASTList *list = malloc(sizeof(ASTList));
    list->node = node;
    list->next = next;
    return list;
}

// Parser initialization
Parser *parser_create(const char *input) {
    Parser *p = malloc(sizeof(Parser));
    p->input = input;
    p->length = strlen(input);
    p->num_rules = NUM_RULES;
    
    p->memo = malloc(p->length * sizeof(MemoEntry*));
    for (int i = 0; i < p->length; i++) {
        p->memo[i] = calloc(NUM_RULES, sizeof(MemoEntry));
    }
    
    return p;
}

void parser_free(Parser *p) {
    for (int i = 0; i < p->length; i++) {
        free(p->memo[i]);
    }
    free(p->memo);
    free(p);
}

// Skip whitespace
int skip_ws(Parser *p, int pos) {
    while (pos < p->length && isspace(p->input[pos])) {
        pos++;
    }
    return pos;
}

// Match string
int match_str(Parser *p, int pos, const char *str, int *new_pos) {
    pos = skip_ws(p, pos);
    int len = strlen(str);
    if (pos + len <= p->length && strncmp(p->input + pos, str, len) == 0) {
        *new_pos = skip_ws(p, pos + len);
        return 1;
    }
    return 0;
}

// Parse number
ParseResult parse_number(Parser *p, int pos) {
    ParseResult r = {0, NULL, pos};
    pos = skip_ws(p, pos);
    
    if (pos >= p->length || !isdigit(p->input[pos])) {
        return r;
    }
    
    int value = 0;
    while (pos < p->length && isdigit(p->input[pos])) {
        value = value * 10 + (p->input[pos] - '0');
        pos++;
    }
    
    r.success = 1;
    r.node = make_number(value);
    r.pos = skip_ws(p, pos);
    return r;
}

// Parse identifier
int parse_ident(Parser *p, int pos, char *buf, int *new_pos) {
    pos = skip_ws(p, pos);
    
    if (pos >= p->length || !(isalpha(p->input[pos]) || p->input[pos] == '_')) {
        return 0;
    }
    
    int i = 0;
    while (pos < p->length && (isalnum(p->input[pos]) || p->input[pos] == '_')) {
        buf[i++] = p->input[pos++];
    }
    buf[i] = '\0';
    *new_pos = skip_ws(p, pos);
    return 1;
}

// Forward declarations
ParseResult parse_expr(Parser *p, int pos);
ParseResult parse_stmt(Parser *p, int pos);

// Parse primary expression
ParseResult parse_primary(Parser *p, int pos) {
    if (pos >= p->length || pos < 0) {
        return (ParseResult){0, NULL, pos};
    }
    
    if (p->memo[pos][RULE_PRIMARY].is_set) {
        return p->memo[pos][RULE_PRIMARY].result;
    }
    
    ParseResult r;
    
    // Try number
    r = parse_number(p, pos);
    if (r.success) {
        p->memo[pos][RULE_PRIMARY] = (MemoEntry){1, r};
        return r;
    }
    
    // Try parenthesised expression
    int new_pos;
    if (match_str(p, pos, "(", &new_pos)) {
        r = parse_expr(p, new_pos);
        if (r.success && match_str(p, r.pos, ")", &new_pos)) {
            r.pos = new_pos;
            p->memo[pos][RULE_PRIMARY] = (MemoEntry){1, r};
            return r;
        }
    }
    
    // Try variable
    char ident[256];
    if (parse_ident(p, pos, ident, &new_pos)) {
        r.success = 1;
        r.node = make_variable(ident);
        r.pos = new_pos;
        p->memo[pos][RULE_PRIMARY] = (MemoEntry){1, r};
        return r;
    }
    
    r = (ParseResult){0, NULL, pos};
    p->memo[pos][RULE_PRIMARY] = (MemoEntry){1, r};
    return r;
}

// Parse term (handles * and /)
ParseResult parse_term(Parser *p, int pos) {
    if (pos >= p->length || pos < 0) {
        return (ParseResult){0, NULL, pos};
    }
    
    if (p->memo[pos][RULE_TERM].is_set) {
        return p->memo[pos][RULE_TERM].result;
    }
    
    ParseResult r = parse_primary(p, pos);
    if (!r.success) {
        p->memo[pos][RULE_TERM] = (MemoEntry){1, r};
        return r;
    }
    
    ASTNode *left = r.node;
    pos = r.pos;
    
    while (1) {
        int new_pos;
        char *op = NULL;
        
        if (match_str(p, pos, "*", &new_pos)) {
            op = "*";
        } else if (match_str(p, pos, "/", &new_pos)) {
            op = "/";
        } else {
            break;
        }
        
        ParseResult right = parse_primary(p, new_pos);
        if (!right.success) break;
        
        left = make_binop(op, left, right.node);
        pos = right.pos;
    }
    
    r.node = left;
    r.pos = pos;
    p->memo[pos][RULE_TERM] = (MemoEntry){1, r};
    return r;
}

// Parse arithmetic (handles + and -)
ParseResult parse_arith(Parser *p, int pos) {
    if (pos >= p->length || pos < 0) {
        return (ParseResult){0, NULL, pos};
    }
    
    if (p->memo[pos][RULE_ARITH].is_set) {
        return p->memo[pos][RULE_ARITH].result;
    }
    
    ParseResult r = parse_term(p, pos);
    if (!r.success) {
        p->memo[pos][RULE_ARITH] = (MemoEntry){1, r};
        return r;
    }
    
    ASTNode *left = r.node;
    pos = r.pos;
    
    while (1) {
        int new_pos;
        char *op = NULL;
        
        if (match_str(p, pos, "+", &new_pos)) {
            op = "+";
        } else if (match_str(p, pos, "-", &new_pos)) {
            op = "-";
        } else {
            break;
        }
        
        ParseResult right = parse_term(p, new_pos);
        if (!right.success) break;
        
        left = make_binop(op, left, right.node);
        pos = right.pos;
    }
    
    r.node = left;
    r.pos = pos;
    p->memo[pos][RULE_ARITH] = (MemoEntry){1, r};
    return r;
}

// Parse expression (handles comparisons)
ParseResult parse_expr(Parser *p, int pos) {
    if (pos >= p->length || pos < 0) {
        return (ParseResult){0, NULL, pos};
    }
    
    if (p->memo[pos][RULE_EXPR].is_set) {
        return p->memo[pos][RULE_EXPR].result;
    }
    
    ParseResult r = parse_arith(p, pos);
    if (!r.success) {
        p->memo[pos][RULE_EXPR] = (MemoEntry){1, r};
        return r;
    }
    
    ASTNode *left = r.node;
    pos = r.pos;
    
    const char *ops[] = {"==", "!=", "<=", ">=", "<", ">", NULL};
    for (int i = 0; ops[i]; i++) {
        int new_pos;
        if (match_str(p, pos, ops[i], &new_pos)) {
            ParseResult right = parse_arith(p, new_pos);
            if (right.success) {
                r.node = make_binop(ops[i], left, right.node);
                r.pos = right.pos;
                p->memo[pos][RULE_EXPR] = (MemoEntry){1, r};
                return r;
            }
        }
    }
    
    r.node = left;
    r.pos = pos;
    p->memo[pos][RULE_EXPR] = (MemoEntry){1, r};
    return r;
}

// Parse assignment
ParseResult parse_assignment(Parser *p, int pos) {
    int saved = pos;
    char ident[256];
    int new_pos;
    
    if (parse_ident(p, pos, ident, &new_pos) && match_str(p, new_pos, "=", &pos)) {
        ParseResult r = parse_expr(p, pos);
        if (r.success && match_str(p, r.pos, ";", &new_pos)) {
            r.node = make_assignment(ident, r.node);
            r.pos = new_pos;
            return r;
        }
    }
    
    return (ParseResult){0, NULL, saved};
}

// Parse if statement
ParseResult parse_if(Parser *p, int pos) {
    int new_pos;
    
    if (!match_str(p, pos, "if", &new_pos)) {
        return (ParseResult){0, NULL, pos};
    }
    
    if (!match_str(p, new_pos, "(", &pos)) {
        return (ParseResult){0, NULL, pos};
    }
    
    ParseResult cond = parse_expr(p, pos);
    if (!cond.success) return (ParseResult){0, NULL, pos};
    
    if (!match_str(p, cond.pos, ")", &pos)) {
        return (ParseResult){0, NULL, pos};
    }
    
    if (!match_str(p, pos, "{", &pos)) {
        return (ParseResult){0, NULL, pos};
    }
    
    ASTList *then_br = NULL, *tail = NULL;
    while (!match_str(p, pos, "}", &new_pos)) {
        ParseResult s = parse_stmt(p, pos);
        if (!s.success) break;
        
        ASTList *node = cons(s.node, NULL);
        if (!then_br) {
            then_br = tail = node;
        } else {
            tail->next = node;
            tail = node;
        }
        pos = s.pos;
    }
    pos = new_pos;
    
    ASTList *else_br = NULL;
    if (match_str(p, pos, "else", &new_pos)) {
        if (!match_str(p, new_pos, "{", &pos)) {
            return (ParseResult){0, NULL, pos};
        }
        
        tail = NULL;
        while (!match_str(p, pos, "}", &new_pos)) {
            ParseResult s = parse_stmt(p, pos);
            if (!s.success) break;
            
            ASTList *node = cons(s.node, NULL);
            if (!else_br) {
                else_br = tail = node;
            } else {
                tail->next = node;
                tail = node;
            }
            pos = s.pos;
        }
        pos = new_pos;
    }
    
    return (ParseResult){1, make_if(cond.node, then_br, else_br), pos};
}

// Parse while statement
ParseResult parse_while(Parser *p, int pos) {
    int new_pos;
    
    if (!match_str(p, pos, "while", &new_pos)) {
        return (ParseResult){0, NULL, pos};
    }
    
    if (!match_str(p, new_pos, "(", &pos)) {
        return (ParseResult){0, NULL, pos};
    }
    
    ParseResult cond = parse_expr(p, pos);
    if (!cond.success) return (ParseResult){0, NULL, pos};
    
    if (!match_str(p, cond.pos, ")", &pos)) {
        return (ParseResult){0, NULL, pos};
    }
    
    if (!match_str(p, pos, "{", &pos)) {
        return (ParseResult){0, NULL, pos};
    }
    
    ASTList *body = NULL, *tail = NULL;
    while (!match_str(p, pos, "}", &new_pos)) {
        ParseResult s = parse_stmt(p, pos);
        if (!s.success) break;
        
        ASTList *node = cons(s.node, NULL);
        if (!body) {
            body = tail = node;
        } else {
            tail->next = node;
            tail = node;
        }
        pos = s.pos;
    }
    pos = new_pos;
    
    return (ParseResult){1, make_while(cond.node, body), pos};
}

// Parse statement
ParseResult parse_stmt(Parser *p, int pos) {
    ParseResult r;
    
    r = parse_if(p, pos);
    if (r.success) return r;
    
    r = parse_while(p, pos);
    if (r.success) return r;
    
    r = parse_assignment(p, pos);
    if (r.success) return r;
    
    return (ParseResult){0, NULL, pos};
}

// Parse program
ASTNode *parse_program(Parser *p) {
    int pos = skip_ws(p, 0);
    ASTList *stmts = NULL, *tail = NULL;
    
    while (pos < p->length) {
        ParseResult r = parse_stmt(p, pos);
        if (!r.success) break;
        
        ASTList *node = cons(r.node, NULL);
        if (!stmts) {
            stmts = tail = node;
        } else {
            tail->next = node;
            tail = node;
        }
        pos = r.pos;
    }
    
    return make_program(stmts);
}

// Print AST
void print_indent(int level) {
    for (int i = 0; i < level; i++) printf("  ");
}

void print_list(ASTList *list, int indent);

void print_ast(ASTNode *node, int indent) {
    if (!node) return;
    
    print_indent(indent);
    switch (node->type) {
        case NODE_NUMBER:
            printf("Number: %d\n", node->data.number);
            break;
        case NODE_VARIABLE:
            printf("Variable: %s\n", node->data.variable);
            break;
        case NODE_BINOP:
            printf("BinOp: %s\n", node->data.binop.op);
            print_ast(node->data.binop.left, indent + 1);
            print_ast(node->data.binop.right, indent + 1);
            break;
        case NODE_ASSIGNMENT:
            printf("Assignment: %s\n", node->data.assignment.var);
            print_ast(node->data.assignment.expr, indent + 1);
            break;
        case NODE_IF:
            printf("If:\n");
            print_indent(indent + 1);
            printf("Condition:\n");
            print_ast(node->data.if_stmt.condition, indent + 2);
            print_indent(indent + 1);
            printf("Then:\n");
            print_list(node->data.if_stmt.then_branch, indent + 2);
            if (node->data.if_stmt.else_branch) {
                print_indent(indent + 1);
                printf("Else:\n");
                print_list(node->data.if_stmt.else_branch, indent + 2);
            }
            break;
        case NODE_WHILE:
            printf("While:\n");
            print_indent(indent + 1);
            printf("Condition:\n");
            print_ast(node->data.while_stmt.condition, indent + 2);
            print_indent(indent + 1);
            printf("Body:\n");
            print_list(node->data.while_stmt.body, indent + 2);
            break;
        case NODE_PROGRAM:
            printf("Program:\n");
            print_list(node->data.program, indent + 1);
            break;
    }
}

void print_list(ASTList *list, int indent) {
    while (list) {
        print_ast(list->node, indent);
        list = list->next;
    }
}

int main() {
    const char *code = 
        "x = 10;"
        "y = 20;"
        "if (x < y) {"
        "    z = x + y;"
        "    unused = 42;"
        "} else {"
        "    z = x - y;"
        "}"
        "result = z * 2;"
        "dead = 99;";
    
    Parser *parser = parser_create(code);
    ASTNode *ast = parse_program(parser);
    
    printf("Parsed successfully!\n\n");
    print_ast(ast, 0);
    
    parser_free(parser);
    return 0;
}
