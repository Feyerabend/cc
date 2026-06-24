/*
 * calc.c — a tiny compiler written in the *classical* style: every object is
 * malloc'd individually and must be freed by hand.
 *
 * This is the brittle companion the arena essay (../README.md) argues against.
 * The whole point lives at the bottom of this file: free_tokens(), free_ast(),
 * and free_tac() are three separate hand-written cleanup walks, each of which
 * must mirror its allocation exactly or leak. Compare them with the single
 * arena_destroy() call in ../arena.c — that contrast is the lesson.
 *
 * The code here is correct (no leaks), so it shows the classical style done
 * *right*; the cost is the sheer amount of manual lifetime bookkeeping. Arenas
 * remove that bookkeeping rather than make it neater.
 *
 * Language — a small expression language with assignment and print:
 *
 *     program   := statement*
 *     statement := IDENT '=' expr ';'
 *                | 'print' expr ';'
 *     expr      := term  (('+' | '-') term)*
 *     term      := factor (('*' | '/') factor)*
 *     factor    := NUMBER | IDENT | '(' expr ')'
 *
 * Pipeline: lex -> parse (AST) -> generate three-address code (TAC) -> print.
 *
 * Build & run:  make run        (or: cc -std=c11 -Wall -Wextra -o calc calc.c)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdarg.h>

/* -- defensive allocation helpers (classical style: check every call) ------ */

static void *xmalloc(size_t n) {
    void *p = malloc(n);
    if (!p) { fprintf(stderr, "out of memory\n"); exit(1); }
    return p;
}

static char *xstrdup(const char *s) {
    size_t n = strlen(s) + 1;
    char *p = xmalloc(n);
    memcpy(p, s, n);
    return p;
}

static void die(const char *msg) {
    fprintf(stderr, "error: %s\n", msg);
    exit(1);
}

/* -- tokens ---------------------------------------------------------------- */

typedef enum {
    T_NUM, T_IDENT, T_PRINT,
    T_PLUS, T_MINUS, T_STAR, T_SLASH,
    T_LPAREN, T_RPAREN, T_ASSIGN, T_SEMI, T_EOF
} TokKind;

typedef struct {
    TokKind kind;
    char   *text;   /* malloc'd lexeme for T_NUM / T_IDENT, else NULL */
} Token;

typedef struct {
    Token *items;
    size_t count, cap;
} TokenList;

static void tokens_push(TokenList *t, TokKind kind, const char *text) {
    if (t->count == t->cap) {
        t->cap = t->cap ? t->cap * 2 : 16;
        t->items = realloc(t->items, t->cap * sizeof(Token));
        if (!t->items) die("out of memory growing token list");
    }
    t->items[t->count].kind = kind;
    t->items[t->count].text = text ? xstrdup(text) : NULL;
    t->count++;
}

static TokenList lex(const char *src) {
    TokenList t = {0};
    for (const char *p = src; *p; ) {
        if (isspace((unsigned char)*p)) { p++; continue; }
        if (isdigit((unsigned char)*p)) {
            const char *start = p;
            while (isdigit((unsigned char)*p)) p++;
            char *buf = xmalloc((size_t)(p - start) + 1);
            memcpy(buf, start, (size_t)(p - start));
            buf[p - start] = '\0';
            tokens_push(&t, T_NUM, buf);
            free(buf);
            continue;
        }
        if (isalpha((unsigned char)*p) || *p == '_') {
            const char *start = p;
            while (isalnum((unsigned char)*p) || *p == '_') p++;
            char *buf = xmalloc((size_t)(p - start) + 1);
            memcpy(buf, start, (size_t)(p - start));
            buf[p - start] = '\0';
            tokens_push(&t, strcmp(buf, "print") == 0 ? T_PRINT : T_IDENT, buf);
            free(buf);
            continue;
        }
        switch (*p) {
            case '+': tokens_push(&t, T_PLUS,   NULL); break;
            case '-': tokens_push(&t, T_MINUS,  NULL); break;
            case '*': tokens_push(&t, T_STAR,   NULL); break;
            case '/': tokens_push(&t, T_SLASH,  NULL); break;
            case '(': tokens_push(&t, T_LPAREN, NULL); break;
            case ')': tokens_push(&t, T_RPAREN, NULL); break;
            case '=': tokens_push(&t, T_ASSIGN, NULL); break;
            case ';': tokens_push(&t, T_SEMI,   NULL); break;
            default:  die("unexpected character");
        }
        p++;
    }
    tokens_push(&t, T_EOF, NULL);
    return t;
}

static void free_tokens(TokenList *t) {
    for (size_t i = 0; i < t->count; i++)
        free(t->items[i].text);   /* each lexeme was strdup'd */
    free(t->items);
}

/* -- AST ------------------------------------------------------------------- */

typedef enum { N_NUM, N_VAR, N_BIN, N_ASSIGN, N_PRINT } NodeKind;

typedef struct ASTNode {
    NodeKind kind;
    char    *text;          /* NUM literal, VAR name, or ASSIGN target */
    char     op;            /* N_BIN: one of + - * /                   */
    struct ASTNode *left;   /* BIN left; ASSIGN/PRINT expression       */
    struct ASTNode *right;  /* BIN right                               */
} ASTNode;

static ASTNode *node_new(NodeKind kind) {
    ASTNode *n = xmalloc(sizeof(ASTNode));
    n->kind = kind; n->text = NULL; n->op = 0;
    n->left = n->right = NULL;
    return n;
}

static void free_ast(ASTNode *n) {     /* recursive hand-written cleanup */
    if (!n) return;
    free_ast(n->left);
    free_ast(n->right);
    free(n->text);
    free(n);
}

/* -- parser (recursive descent) -------------------------------------------- */

typedef struct { TokenList *t; size_t pos; } Parser;

static Token *peek(Parser *p)  { return &p->t->items[p->pos]; }
static Token *advance(Parser *p) { return &p->t->items[p->pos++]; }

static void expect(Parser *p, TokKind kind, const char *what) {
    if (peek(p)->kind != kind) die(what);
    p->pos++;
}

static ASTNode *parse_expr(Parser *p);

static ASTNode *parse_factor(Parser *p) {
    Token *tok = peek(p);
    if (tok->kind == T_NUM || tok->kind == T_IDENT) {
        advance(p);
        ASTNode *n = node_new(tok->kind == T_NUM ? N_NUM : N_VAR);
        n->text = xstrdup(tok->text);
        return n;
    }
    if (tok->kind == T_LPAREN) {
        advance(p);
        ASTNode *n = parse_expr(p);
        expect(p, T_RPAREN, "expected ')'");
        return n;
    }
    die("expected number, identifier, or '('");
    return NULL;   /* unreachable */
}

static ASTNode *parse_term(Parser *p) {
    ASTNode *left = parse_factor(p);
    while (peek(p)->kind == T_STAR || peek(p)->kind == T_SLASH) {
        char op = peek(p)->kind == T_STAR ? '*' : '/';
        advance(p);
        ASTNode *n = node_new(N_BIN);
        n->op = op; n->left = left; n->right = parse_factor(p);
        left = n;
    }
    return left;
}

static ASTNode *parse_expr(Parser *p) {
    ASTNode *left = parse_term(p);
    while (peek(p)->kind == T_PLUS || peek(p)->kind == T_MINUS) {
        char op = peek(p)->kind == T_PLUS ? '+' : '-';
        advance(p);
        ASTNode *n = node_new(N_BIN);
        n->op = op; n->left = left; n->right = parse_term(p);
        left = n;
    }
    return left;
}

static ASTNode *parse_statement(Parser *p) {
    Token *tok = peek(p);
    if (tok->kind == T_PRINT) {
        advance(p);
        ASTNode *n = node_new(N_PRINT);
        n->left = parse_expr(p);
        expect(p, T_SEMI, "expected ';' after print");
        return n;
    }
    if (tok->kind == T_IDENT) {
        ASTNode *n = node_new(N_ASSIGN);
        n->text = xstrdup(tok->text);
        advance(p);
        expect(p, T_ASSIGN, "expected '=' in assignment");
        n->left = parse_expr(p);
        expect(p, T_SEMI, "expected ';' after assignment");
        return n;
    }
    die("expected a statement");
    return NULL;   /* unreachable */
}

/* program = dynamic array of statement nodes */
typedef struct { ASTNode **items; size_t count, cap; } Program;

static Program parse_program(TokenList *t) {
    Parser p = { t, 0 };
    Program prog = {0};
    while (peek(&p)->kind != T_EOF) {
        if (prog.count == prog.cap) {
            prog.cap = prog.cap ? prog.cap * 2 : 8;
            prog.items = realloc(prog.items, prog.cap * sizeof(ASTNode *));
            if (!prog.items) die("out of memory growing program");
        }
        prog.items[prog.count++] = parse_statement(&p);
    }
    return prog;
}

static void free_program(Program *prog) {
    for (size_t i = 0; i < prog->count; i++)
        free_ast(prog->items[i]);
    free(prog->items);
}

/* -- three-address code ---------------------------------------------------- */

typedef struct TAC { char *text; struct TAC *next; } TAC;
typedef struct { TAC *head, *tail; int temp; } TacGen;

static void emit(TacGen *g, const char *fmt, ...) {
    char buf[128];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof buf, fmt, ap);
    va_end(ap);
    TAC *instr = xmalloc(sizeof(TAC));
    instr->text = xstrdup(buf);
    instr->next = NULL;
    if (g->tail) g->tail->next = instr; else g->head = instr;
    g->tail = instr;
}

static char *new_temp(TacGen *g) {
    char buf[16];
    snprintf(buf, sizeof buf, "t%d", g->temp++);
    return xstrdup(buf);   /* caller owns and must free — the classic question */
}

/* Returns a freshly malloc'd "place" string the caller must free. */
static char *gen_expr(TacGen *g, ASTNode *n) {
    switch (n->kind) {
        case N_NUM:
        case N_VAR:
            return xstrdup(n->text);
        case N_BIN: {
            char *a = gen_expr(g, n->left);
            char *b = gen_expr(g, n->right);
            char *t = new_temp(g);
            emit(g, "%s = %s %c %s", t, a, n->op, b);
            free(a);
            free(b);
            return t;
        }
        default:
            die("not an expression");
            return NULL;   /* unreachable */
    }
}

static void gen_statement(TacGen *g, ASTNode *n) {
    char *place = gen_expr(g, n->left);
    if (n->kind == N_ASSIGN) emit(g, "%s = %s", n->text, place);
    else                     emit(g, "print %s", place);
    free(place);
}

static TacGen gen_program(Program *prog) {
    TacGen g = {0};
    for (size_t i = 0; i < prog->count; i++)
        gen_statement(&g, prog->items[i]);
    return g;
}

static void free_tac(TacGen *g) {
    for (TAC *i = g->head; i; ) {
        TAC *next = i->next;
        free(i->text);
        free(i);
        i = next;
    }
}

/* -- driver ---------------------------------------------------------------- */

int main(void) {
    const char *source =
        "a = 2 + 3 * 4;\n"
        "b = (a - 5) / 2;\n"
        "print a;\n"
        "print b;\n";

    printf("source:\n%s\n", source);

    TokenList tokens = lex(source);
    Program   prog   = parse_program(&tokens);
    TacGen    tac    = gen_program(&prog);

    printf("three-address code:\n");
    for (TAC *i = tac.head; i; i = i->next)
        printf("  %s\n", i->text);

    /* Classical cleanup: three separate hand-written walks, one per phase.
       Miss any one and you leak; free in the wrong order and you crash.
       The arena version (../arena.c) replaces all of this with one call. */
    free_tac(&tac);
    free_program(&prog);
    free_tokens(&tokens);

    return 0;
}
