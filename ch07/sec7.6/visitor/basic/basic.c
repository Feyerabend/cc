/*
 * basic.c  —  BASIC Interpreter in C
 *
 * Demonstrates the Visitor Pattern in pure C:
 *   - Expression nodes are plain structs with a tag (ExprKind enum).
 *   - The "visitor" is a struct of function pointers, one per node kind.
 *   - Double-dispatch is achieved by expr->accept(expr, visitor).
 *
 * Robustness features (this revision):
 *   - Single top-level setjmp guard per executed line; eval_str() does NOT
 *     install its own setjmp, so errors always propagate to the right handler.
 *   - SIGINT (Ctrl-C) sets g_interrupted; run_program() checks it every step
 *     and returns to the REPL cleanly.
 *   - BREAK command halts a running program from within IF..THEN or at prompt.
 *   - HELP command with full command/function reference.
 *   - did_you_mean() suggestion on unknown commands (Levenshtein distance).
 *   - Decimal number literals supported (e.g. 3.14).
 *   - trim() uses a rotating ring of buffers to avoid aliasing in nested calls.
 *   - compare_lines() uses subtraction-safe comparison.
 *   - All commands validate arguments before acting.
 *
 * Build:
 *   cc -std=c11 -Wall -Wextra -o basic basic.c
 *
 * Usage:
 *   ./basic          — interactive REPL
 *   ./basic prog.bas — load and run a program file
 */

#include <ctype.h>
#include <signal.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>

/* 
 * Configuration
 */
#define MAX_LINES     1000
#define MAX_LINE_LEN   256
#define MAX_VARS       256
#define MAX_STACK      256
#define MAX_LOOPS       64
#define MAX_STEPS  1000000
#define VAR_NAME_LEN    32
#define TRIM_BUFS        8

/* 
 * SIGINT — Ctrl-C sets a flag; run_program() polls it
 */
static volatile sig_atomic_t g_interrupted = 0;
static void sigint_handler(int sig) { (void)sig; g_interrupted = 1; }

/* 
 * Error handling  (longjmp-based)
 *
 * ONE global jmp_buf. eval_str() does NOT install its own setjmp — it lets
 * errors propagate outward to whichever guard is active (run_program or
 * feed_line), so errors are always reported in the right context.
 *  */
typedef enum {
    ERR_NONE = 0,
    ERR_PARSER,
    ERR_EXECUTION,
    ERR_STACK,
    ERR_UNDEFINED_LINE,
    ERR_DIVISION_BY_ZERO,
    ERR_TYPE,
    ERR_BREAK
} ErrorKind;

static jmp_buf  g_run_jmp;   /* used inside run_program() */
static jmp_buf  g_feed_jmp;  /* used inside feed_line() */
static jmp_buf *g_active_jmp = NULL;  /* points to whichever is live */
static ErrorKind g_err_kind = ERR_NONE;
static char      g_err_msg[256];

static void raise_error(ErrorKind kind, const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(g_err_msg, sizeof g_err_msg, fmt, ap);
    va_end(ap);
    g_err_kind = kind;
    if (g_active_jmp) longjmp(*g_active_jmp, 1);
    abort(); /* no guard active — should never happen */
}

/* 
 * Value  (tagged union: number or string)
 */
typedef enum { VAL_NUM, VAL_STR } ValKind;
typedef struct {
    ValKind kind;
    union { double num; char str[MAX_LINE_LEN]; };
} Value;

static inline Value val_num(double n)       { Value v; v.kind=VAL_NUM; v.num=n; return v; }
static inline Value val_str(const char *s)  {
    Value v; v.kind=VAL_STR;
    strncpy(v.str, s ? s : "", sizeof v.str - 1);
    v.str[sizeof v.str - 1] = '\0';
    return v;
}
static inline bool val_truthy(Value v) {
    return (v.kind == VAL_NUM) ? (v.num != 0.0) : (v.str[0] != '\0');
}

/* 
 * trim() — uses a ring of TRIM_BUFS static buffers to avoid aliasing
 */
static const char *trim(const char *s) {
    static char bufs[TRIM_BUFS][MAX_LINE_LEN];
    static int  slot = 0;
    char *buf = bufs[slot++ % TRIM_BUFS];
    while (isspace((unsigned char)*s)) s++;
    strncpy(buf, s, MAX_LINE_LEN - 1); buf[MAX_LINE_LEN-1] = '\0';
    int len = (int)strlen(buf);
    while (len > 0 && isspace((unsigned char)buf[len-1])) buf[--len] = '\0';
    return buf;
}

/* 
 * AST node hierarchy
 */
typedef enum { EXPR_NUMBER, EXPR_STRING, EXPR_VARIABLE, EXPR_BINARY, EXPR_FUNCTION } ExprKind;

struct Expr; struct ExprVisitor;
typedef Value (*AcceptFn)(struct Expr *, struct ExprVisitor *);

typedef struct Expr {
    ExprKind kind;
    AcceptFn accept;
    union {
        double number;
        char   string [MAX_LINE_LEN];
        char   varname[VAR_NAME_LEN];
        struct { struct Expr *left; char op; struct Expr *right; } binary;
        struct { char name[VAR_NAME_LEN]; struct Expr *args[8]; int argc; } func;
    };
} Expr;

/* 
 * Visitor interface  (one function pointer per node kind)
 */
typedef struct ExprVisitor {
    Value (*visit_number)  (struct ExprVisitor *, Expr *);
    Value (*visit_string)  (struct ExprVisitor *, Expr *);
    Value (*visit_variable)(struct ExprVisitor *, Expr *);
    Value (*visit_binary)  (struct ExprVisitor *, Expr *);
    Value (*visit_function)(struct ExprVisitor *, Expr *);
} ExprVisitor;

/* accept() shims — each performs the second dispatch into the visitor */
static Value accept_number  (Expr *e, ExprVisitor *v) { return v->visit_number  (v,e); }
static Value accept_string  (Expr *e, ExprVisitor *v) { return v->visit_string  (v,e); }
static Value accept_variable(Expr *e, ExprVisitor *v) { return v->visit_variable(v,e); }
static Value accept_binary  (Expr *e, ExprVisitor *v) { return v->visit_binary  (v,e); }
static Value accept_function(Expr *e, ExprVisitor *v) { return v->visit_function(v,e); }

/* 
 * Expression arena  (bump allocator; reset before each parse)
 */
#define ARENA_SIZE 4096
static Expr g_arena[ARENA_SIZE];
static int  g_arena_top = 0;

static Expr *alloc_expr(ExprKind kind, AcceptFn fn) {
    if (g_arena_top >= ARENA_SIZE) raise_error(ERR_EXECUTION, "Expression arena exhausted");
    Expr *e = &g_arena[g_arena_top++];
    memset(e, 0, sizeof *e);
    e->kind = kind; e->accept = fn;
    return e;
}
static void arena_reset(void) { g_arena_top = 0; }

/* 
 * Interpreter state  (global singleton)
 */
typedef struct { int lineno; char text[MAX_LINE_LEN]; }    ProgramLine;
typedef struct { char name[VAR_NAME_LEN]; Value value; }   Variable;
typedef struct {
    char varname[VAR_NAME_LEN];
    int    start_pc;
    double end_value;
    double step;
} ForLoop;

static struct {
    ProgramLine lines[MAX_LINES]; int line_count;
    Variable    vars [MAX_VARS];  int var_count;
    int  call_stack[MAX_STACK];   int stack_top;
    ForLoop loops[MAX_LOOPS];     int loop_count;
    int pc;   /* index into lines[], -1 = halted */
} G;

static void state_reset(void) { memset(&G, 0, sizeof G); G.pc = -1; }

static Variable *find_var(const char *name) {
    for (int i = 0; i < G.var_count; i++)
        if (strcmp(G.vars[i].name, name) == 0) return &G.vars[i];
    return NULL;
}
static Variable *get_or_create_var(const char *name) {
    Variable *v = find_var(name);
    if (v) return v;
    if (G.var_count >= MAX_VARS) raise_error(ERR_EXECUTION, "Variable table full");
    v = &G.vars[G.var_count++];
    strncpy(v->name, name, VAR_NAME_LEN - 1); v->name[VAR_NAME_LEN-1] = '\0';
    v->value = (name[strlen(name)-1] == '$') ? val_str("") : val_num(0.0);
    return v;
}
static void  set_var(const char *n, Value v) { get_or_create_var(n)->value = v; }
static Value get_var(const char *n)          { return get_or_create_var(n)->value; }

static int find_line_idx(int lineno) {
    for (int i = 0; i < G.line_count; i++)
        if (G.lines[i].lineno == lineno) return i;
    return -1;
}
static int cmp_lines(const void *a, const void *b) {
    int la = ((ProgramLine *)a)->lineno, lb = ((ProgramLine *)b)->lineno;
    return (la > lb) - (la < lb);
}
static void store_line(int lineno, const char *text) {
    int idx = find_line_idx(lineno);
    if (idx < 0) {
        if (G.line_count >= MAX_LINES)
            raise_error(ERR_EXECUTION, "Program too large (max %d lines)", MAX_LINES);
        idx = G.line_count++;
    }
    G.lines[idx].lineno = lineno;
    strncpy(G.lines[idx].text, text, MAX_LINE_LEN-1); G.lines[idx].text[MAX_LINE_LEN-1]='\0';
    qsort(G.lines, G.line_count, sizeof(ProgramLine), cmp_lines);
}

/* 
 * EvaluationVisitor — computes a Value by walking the AST
 */
static Value ev_number  (ExprVisitor *v, Expr *e) { (void)v; return val_num(e->number); }
static Value ev_string  (ExprVisitor *v, Expr *e) { (void)v; return val_str(e->string); }
static Value ev_variable(ExprVisitor *v, Expr *e) { (void)v; return get_var(e->varname); }

static Value ev_binary(ExprVisitor *v, Expr *e) {
    Value L = e->binary.left ->accept(e->binary.left,  v);
    Value R = e->binary.right->accept(e->binary.right, v);
    char op = e->binary.op;

    if (op == '+' && (L.kind == VAL_STR || R.kind == VAL_STR)) {
        char ls[MAX_LINE_LEN], rs[MAX_LINE_LEN], buf[MAX_LINE_LEN*2];
        if (L.kind == VAL_NUM) snprintf(ls, sizeof ls, "%g", L.num);
        else strncpy(ls, L.str, sizeof ls-1);
        if (R.kind == VAL_NUM) snprintf(rs, sizeof rs, "%g", R.num);
        else strncpy(rs, R.str, sizeof rs-1);
        snprintf(buf, sizeof buf, "%s%s", ls, rs);
        return val_str(buf);
    }
    if (L.kind != VAL_NUM || R.kind != VAL_NUM)
        raise_error(ERR_TYPE, "Operator '%c' requires numbers (got %s and %s)",
            op, L.kind==VAL_STR?"string":"number", R.kind==VAL_STR?"string":"number");

    switch (op) {
        case '+': return val_num(L.num + R.num);
        case '-': return val_num(L.num - R.num);
        case '*': return val_num(L.num * R.num);
        case '/':
            if (R.num == 0.0) raise_error(ERR_DIVISION_BY_ZERO, "Division by zero");
            return val_num(L.num / R.num);
        case '=': return val_num(L.num == R.num ? 1 : 0);
        case '<': return val_num(L.num <  R.num ? 1 : 0);
        case '>': return val_num(L.num >  R.num ? 1 : 0);
    }
    raise_error(ERR_EXECUTION, "Unknown operator '%c'", op);
    return val_num(0);
}

static Value ev_function(ExprVisitor *v, Expr *e) {
    Value argv[8];
    for (int i = 0; i < e->func.argc; i++)
        argv[i] = e->func.args[i]->accept(e->func.args[i], v);
    const char *fn = e->func.name;

    char s0[MAX_LINE_LEN] = {0};
    if (e->func.argc > 0) {
        if (argv[0].kind == VAL_STR) strncpy(s0, argv[0].str, sizeof s0 - 1);
        else snprintf(s0, sizeof s0, "%g", argv[0].num);
    }
    if (strcmp(fn, "LEN")   == 0) {
        if (e->func.argc < 1) raise_error(ERR_PARSER, "LEN$ needs 1 argument");
        return val_num((double)strlen(s0));
    }
    if (strcmp(fn, "STR")   == 0) {
        if (e->func.argc < 1) raise_error(ERR_PARSER, "STR$ needs 1 argument");
        return val_str(s0);
    }
    if (strcmp(fn, "LEFT")  == 0) {
        if (e->func.argc < 2) raise_error(ERR_PARSER, "LEFT$ needs (string, n)");
        int n = (int)argv[1].num; if (n < 0) n = 0;
        char buf[MAX_LINE_LEN] = {0};
        strncpy(buf, s0, (size_t)n < sizeof buf-1 ? (size_t)n : sizeof buf-1);
        return val_str(buf);
    }
    if (strcmp(fn, "RIGHT") == 0) {
        if (e->func.argc < 2) raise_error(ERR_PARSER, "RIGHT$ needs (string, n)");
        int n = (int)argv[1].num, len = (int)strlen(s0);
        int start = len - n; if (start < 0) start = 0;
        return val_str(s0 + start);
    }
    if (strcmp(fn, "MID")   == 0) {
        if (e->func.argc < 2) raise_error(ERR_PARSER, "MID$ needs (string, start[, len])");
        int start = (int)argv[1].num - 1, slen = (int)strlen(s0);
        if (start < 0) start = 0;
        if (start > slen) start = slen;
        int n = (e->func.argc >= 3) ? (int)argv[2].num : slen - start;
        if (n < 0) n = 0;
        char buf[MAX_LINE_LEN] = {0};
        strncpy(buf, s0+start, (size_t)n < sizeof buf-1 ? (size_t)n : sizeof buf-1);
        return val_str(buf);
    }
    raise_error(ERR_PARSER, "Unknown function %s$ (available: LEN STR LEFT RIGHT MID)", fn);
    return val_num(0);
}

static ExprVisitor g_eval_visitor = {
    .visit_number   = ev_number,
    .visit_string   = ev_string,
    .visit_variable = ev_variable,
    .visit_binary   = ev_binary,
    .visit_function = ev_function,
};
static Value evaluate(Expr *e) { return e->accept(e, &g_eval_visitor); }

/* 
 * Recursive-descent parser
 *
 * Uses global cursor P. Must be called inside a setjmp guard.
 * eval_str() does NOT set up its own guard — errors propagate upward.
 */
static const char *P;
static void skip_ws(void) { while (*P==' '||*P=='\t') P++; }

static Expr *parse_expr(void);
static Expr *parse_term(void);
static Expr *parse_factor(void);

static Expr *parse_number_lit(void) {
    double n = 0; bool has = false;
    while (isdigit((unsigned char)*P)) { n = n*10 + (*P++ - '0'); has = true; }
    if (!has) raise_error(ERR_PARSER, "Expected digit near '%s'", P);
    if (*P == '.') {
        P++; double f = 0.1;
        while (isdigit((unsigned char)*P)) { n += (*P++ - '0')*f; f *= 0.1; }
    }
    skip_ws();
    Expr *e = alloc_expr(EXPR_NUMBER, accept_number); e->number = n; return e;
}

static Expr *parse_string_lit(void) {
    P++;  /* skip '"' */
    const char *start = P;
    while (*P && *P != '"') P++;
    if (!*P) raise_error(ERR_PARSER, "Unterminated string literal");
    Expr *e = alloc_expr(EXPR_STRING, accept_string);
    size_t len = (size_t)(P - start);
    if (len >= MAX_LINE_LEN) len = MAX_LINE_LEN - 1;
    strncpy(e->string, start, len); e->string[len] = '\0';
    P++; skip_ws();
    return e;
}

static Expr *parse_variable(void) {
    if (!isalpha((unsigned char)*P))
        raise_error(ERR_PARSER, "Expected variable name, got '%c'", *P ? *P : '?');
    const char *start = P;
    while (isalnum((unsigned char)*P) || *P == '$') P++;
    Expr *e = alloc_expr(EXPR_VARIABLE, accept_variable);
    size_t len = (size_t)(P - start);
    if (len >= VAR_NAME_LEN) len = VAR_NAME_LEN - 1;
    strncpy(e->varname, start, len); e->varname[len] = '\0';
    skip_ws();
    return e;
}

static bool try_parse_function(Expr **out) {
    const char *save = P;
    char name[VAR_NAME_LEN] = {0}; int ni = 0;
    while (isupper((unsigned char)*P) && ni < VAR_NAME_LEN-1) name[ni++] = *P++;
    if (!ni || *P != '$') { P = save; return false; }
    P++;
    if (*P != '(') { P = save; return false; }
    P++; skip_ws();

    Expr *e = alloc_expr(EXPR_FUNCTION, accept_function);
    strncpy(e->func.name, name, VAR_NAME_LEN-1); e->func.argc = 0;

    while (*P && *P != ')') {
        if (e->func.argc >= 8) raise_error(ERR_PARSER, "Too many args to %s$()", name);
        e->func.args[e->func.argc++] = parse_expr();
        skip_ws();
        if (*P == ',') { P++; skip_ws(); }
    }
    if (*P != ')') raise_error(ERR_PARSER, "Missing ')' after %s$()", name);
    P++; skip_ws();
    *out = e; return true;
}

static Expr *parse_factor(void) {
    skip_ws();
    if (!*P) raise_error(ERR_PARSER, "Unexpected end of expression");
    Expr *e;
    if (try_parse_function(&e)) return e;
    if (*P == '(') {
        P++; skip_ws(); e = parse_expr(); skip_ws();
        if (*P != ')') raise_error(ERR_PARSER, "Missing closing ')'");
        P++; skip_ws(); return e;
    }
    if (*P == '"')                  return parse_string_lit();
    if (isdigit((unsigned char)*P)) return parse_number_lit();
    if (isalpha((unsigned char)*P)) return parse_variable();
    raise_error(ERR_PARSER, "Unexpected character: '%c'", *P);
    return NULL;
}

static Expr *parse_term(void) {
    Expr *left = parse_factor(); skip_ws();
    while (*P == '*' || *P == '/') {
        char op = *P++; skip_ws();
        Expr *b = alloc_expr(EXPR_BINARY, accept_binary);
        b->binary.left = left; b->binary.op = op; b->binary.right = parse_factor();
        left = b; skip_ws();
    }
    return left;
}

static Expr *parse_expr(void) {
    Expr *left = parse_term(); skip_ws();
    while (*P=='+' || *P=='-' || *P=='=' || *P=='<' || *P=='>') {
        char op = *P++; skip_ws();
        Expr *b = alloc_expr(EXPR_BINARY, accept_binary);
        b->binary.left = left; b->binary.op = op; b->binary.right = parse_term();
        left = b; skip_ws();
    }
    return left;
}

/* Caller must have an active setjmp guard */
static Value eval_str(const char *src) {
    if (!src || !*src) raise_error(ERR_PARSER, "Empty expression");
    arena_reset(); P = src;
    return evaluate(parse_expr());
}

/* 
 * "Did you mean?" — Levenshtein distance for command suggestions
 */
static int levenshtein(const char *a, const char *b) {
    int la = (int)strlen(a), lb = (int)strlen(b);
    if (la > 31 || lb > 31) return 99;
    int dp[32][32];
    for (int i = 0; i <= la; i++) dp[i][0] = i;
    for (int j = 0; j <= lb; j++) dp[0][j] = j;
    for (int i = 1; i <= la; i++)
        for (int j = 1; j <= lb; j++) {
            int c   = (tolower((unsigned char)a[i-1]) == tolower((unsigned char)b[j-1])) ? 0 : 1;
            int del = dp[i-1][j]+1, ins = dp[i][j-1]+1, sub = dp[i-1][j-1]+c;
            dp[i][j] = del < ins ? (del < sub ? del : sub) : (ins < sub ? ins : sub);
        }
    return dp[la][lb];
}

static const char *g_cmd_names[] = {
    "PRINT","INPUT","LET","IF","GOTO","GOSUB","RETURN",
    "FOR","NEXT","RUN","LIST","REN","BREAK","STOP","END","BYE","HELP", NULL
};

static void suggest_command(const char *unknown) {
    const char *best = NULL; int best_d = 99;
    for (int i = 0; g_cmd_names[i]; i++) {
        int d = levenshtein(unknown, g_cmd_names[i]);
        if (d < best_d) { best_d = d; best = g_cmd_names[i]; }
    }
    if (best && best_d <= 3) fprintf(stderr, "         Did you mean: %s ?\n", best);
}

/* 
 * Command implementations
 */
static void execute_line(const char *line);  /* forward */

static void cmd_print(const char *args) {
    if (!*args) { puts(""); return; }
    char buf[MAX_LINE_LEN];
    strncpy(buf, args, MAX_LINE_LEN-1); buf[MAX_LINE_LEN-1] = '\0';
    bool first = true;
    char *tok = strtok(buf, ";");
    while (tok) {
        const char *t = trim(tok);
        if (*t) {
            Value v = eval_str(t);
            if (!first) printf(" ");
            if (v.kind == VAL_NUM) {
                if (v.num == (long long)v.num) printf("%lld", (long long)v.num);
                else printf("%g", v.num);
            } else printf("%s", v.str);
            first = false;
        }
        tok = strtok(NULL, ";");
    }
    puts("");
}

static void cmd_input(const char *args) {
    const char *varname = trim(args);
    const char *prompt  = "> ";
    static char pbuf[MAX_LINE_LEN + 2];
    char tmp[MAX_LINE_LEN];
    strncpy(tmp, args, MAX_LINE_LEN-1); tmp[MAX_LINE_LEN-1] = '\0';
    char *semi = strchr(tmp, ';');
    if (semi) {
        *semi = '\0'; varname = trim(semi+1);
        Value pv = eval_str(trim(tmp));
        if (pv.kind == VAL_STR) snprintf(pbuf, sizeof pbuf, "%s ", pv.str);
        else                    snprintf(pbuf, sizeof pbuf, "%g ", pv.num);
        prompt = pbuf;
    }
    if (!*varname) { fprintf(stderr, "[INPUT] Missing variable name\n"); return; }
    printf("%s", prompt); fflush(stdout);
    char line[MAX_LINE_LEN] = {0};
    if (!fgets(line, sizeof line, stdin)) return;
    line[strcspn(line, "\n")] = '\0';
    const char *vn = trim(varname);
    if (vn[strlen(vn)-1] == '$') {
        set_var(vn, val_str(line));
    } else {
        char *end; double d = strtod(line, &end);
        if (end != line && (*end=='\0' || isspace((unsigned char)*end)))
            set_var(vn, val_num(d));
        else { fprintf(stderr, "[INPUT] '%s' is not a number — storing 0\n", line); set_var(vn, val_num(0)); }
    }
}

static void cmd_let(const char *args) {
    const char *eq = strchr(args, '=');
    if (!eq) { fprintf(stderr, "[LET] Missing '=' in: %s\n", args); return; }
    char varname[VAR_NAME_LEN];
    size_t nlen = (size_t)(eq - args);
    if (nlen >= VAR_NAME_LEN) nlen = VAR_NAME_LEN-1;
    strncpy(varname, args, nlen); varname[nlen] = '\0';
    const char *vn = trim(varname);
    if (!*vn) { fprintf(stderr, "[LET] Empty variable name\n"); return; }
    set_var(vn, eval_str(trim(eq+1)));
}

static void cmd_if(const char *args) {
    char buf[MAX_LINE_LEN], upper[MAX_LINE_LEN];
    strncpy(buf,   args, MAX_LINE_LEN-1); buf[MAX_LINE_LEN-1]   = '\0';
    strncpy(upper, args, MAX_LINE_LEN-1); upper[MAX_LINE_LEN-1] = '\0';
    for (int i = 0; upper[i]; i++) upper[i] = (char)toupper((unsigned char)upper[i]);
    char *tp = strstr(upper, "THEN");
    if (!tp) { fprintf(stderr, "[IF] Missing THEN\n"); return; }
    size_t clen = (size_t)(tp - upper);
    char cond[MAX_LINE_LEN]; strncpy(cond, buf, clen); cond[clen] = '\0';
    if (val_truthy(eval_str(trim(cond)))) {
        const char *stmt = trim(buf + clen + 4);
        if (*stmt) execute_line(stmt);
    }
}

static void cmd_goto(const char *args) {
    const char *t = trim(args);
    if (!*t) { fprintf(stderr, "[GOTO] Missing line number\n"); return; }
    int lineno = (int)eval_str(t).num;
    int idx    = find_line_idx(lineno);
    if (idx < 0) raise_error(ERR_UNDEFINED_LINE, "GOTO %d: line does not exist", lineno);
    G.pc = idx;
}

static void cmd_gosub(const char *args) {
    if (G.stack_top >= MAX_STACK) raise_error(ERR_STACK, "GOSUB stack overflow");
    int lineno = (int)eval_str(trim(args)).num;
    int idx    = find_line_idx(lineno);
    if (idx < 0) raise_error(ERR_UNDEFINED_LINE, "GOSUB %d: line does not exist", lineno);
    G.call_stack[G.stack_top++] = G.pc;
    G.pc = idx;
}

static void cmd_return(const char *args) {
    (void)args;
    if (G.stack_top <= 0) { fprintf(stderr, "[RETURN] without GOSUB — halting\n"); G.pc = -1; return; }
    G.pc = G.call_stack[--G.stack_top];
}

static void cmd_for(const char *args) {
    if (G.loop_count >= MAX_LOOPS) raise_error(ERR_EXECUTION, "FOR depth limit (%d) reached", MAX_LOOPS);
    const char *eq = strchr(args, '=');
    if (!eq) { fprintf(stderr, "[FOR] Missing '='\n"); return; }
    char varname[VAR_NAME_LEN];
    size_t nlen = (size_t)(eq - args); if (nlen >= VAR_NAME_LEN) nlen = VAR_NAME_LEN-1;
    strncpy(varname, args, nlen); varname[nlen] = '\0';
    const char *vn = trim(varname);

    char rest[MAX_LINE_LEN], rupper[MAX_LINE_LEN];
    strncpy(rest,   eq+1, MAX_LINE_LEN-1); rest[MAX_LINE_LEN-1]   = '\0';
    strncpy(rupper, rest, MAX_LINE_LEN-1); rupper[MAX_LINE_LEN-1] = '\0';
    for (int i = 0; rupper[i]; i++) rupper[i] = (char)toupper((unsigned char)rupper[i]);

    char *tp = strstr(rupper, "TO");
    while (tp) {
        bool ok = (tp == rupper || isspace((unsigned char)tp[-1])) &&
                  (!tp[2]     || isspace((unsigned char)tp[2]));
        if (ok) break;
        tp = strstr(tp+1, "TO");
    }
    if (!tp) { fprintf(stderr, "[FOR] Missing TO\n"); return; }

    size_t slen = (size_t)(tp - rupper);
    char start_str[MAX_LINE_LEN]; strncpy(start_str, rest, slen); start_str[slen] = '\0';

    Value sv = eval_str(trim(start_str));
    Value ev_val = eval_str(trim(rest + slen + 2));
    set_var(vn, sv);

    int slot = -1;
    for (int i = 0; i < G.loop_count; i++)
        if (strcmp(G.loops[i].varname, vn) == 0) { slot = i; break; }
    if (slot < 0) slot = G.loop_count++;

    strncpy(G.loops[slot].varname, vn, VAR_NAME_LEN-1);
    G.loops[slot].start_pc  = G.pc;
    G.loops[slot].end_value = ev_val.num;
    G.loops[slot].step      = 1.0;
}

static void cmd_next(const char *args) {
    const char *vn = trim(args);
    if (!*vn) { fprintf(stderr, "[NEXT] Missing variable name\n"); return; }
    int slot = -1;
    for (int i = 0; i < G.loop_count; i++)
        if (strcmp(G.loops[i].varname, vn) == 0) { slot = i; break; }
    if (slot < 0) { fprintf(stderr, "[NEXT] NEXT %s without FOR\n", vn); return; }

    Value cur = get_var(vn);
    cur.num += G.loops[slot].step;
    set_var(vn, cur);
    if (cur.num <= G.loops[slot].end_value)
        G.pc = G.loops[slot].start_pc + 1;
    else
        G.loops[slot] = G.loops[--G.loop_count];
}

static void cmd_list(const char *args) {
    (void)args;
    if (!G.line_count) { puts("[LIST] No program loaded."); return; }
    for (int i = 0; i < G.line_count; i++)
        printf("%5d  %s\n", G.lines[i].lineno, G.lines[i].text);
}

static void cmd_ren(const char *args) {
    (void)args;
    if (!G.line_count) { puts("[REN] No program to renumber."); return; }
    int new_nums[MAX_LINES];
    for (int i = 0; i < G.line_count; i++) new_nums[i] = 10 + i*10;
    for (int i = 0; i < G.line_count; i++) {
        char *t = G.lines[i].text, upper[MAX_LINE_LEN];
        for (int j = 0; t[j]; j++) upper[j] = (char)toupper((unsigned char)t[j]);
        upper[strlen(t)] = '\0';
        const char *kw = NULL; int kwlen = 0;
        if (strstr(upper,"GOSUB")) { kw=strstr(upper,"GOSUB"); kwlen=5; }
        else if (strstr(upper,"GOTO")) { kw=strstr(upper,"GOTO"); kwlen=4; }
        if (kw) {
            int off = (int)(kw-upper)+kwlen, old = atoi(t+off);
            for (int j = 0; j < G.line_count; j++) {
                if (G.lines[j].lineno == old) {
                    char rep[MAX_LINE_LEN];
                    snprintf(rep, sizeof rep, "%.*s %d", (int)(kw-upper)+kwlen, t, new_nums[j]);
                    strncpy(t, rep, MAX_LINE_LEN-1);
                    break;
                }
            }
        }
    }
    for (int i = 0; i < G.line_count; i++) G.lines[i].lineno = new_nums[i];
    puts("[REN] Program renumbered.");
}

static void cmd_break(const char *args) { (void)args; raise_error(ERR_BREAK, "BREAK"); }

static void run_program(void);
static void cmd_run (const char *a) {
    (void)a;
    if (!G.line_count) { puts("[RUN] No program loaded."); return; }
    G.pc = 0; run_program();
}
static void cmd_stop(const char *a) { (void)a; puts("Program stopped."); G.pc = -1; }
static void cmd_bye (const char *a) { (void)a; puts("Bye!"); exit(0); }

static void cmd_help(const char *args) {
    (void)args;
    puts(
"Commands\n"
"  PRINT expr [; expr ...]   Print values (semicolons separate items)\n"
"  INPUT [prompt ;] var      Read input (string vars end with $)\n"
"  LET var = expr            Assign  (LET is optional: X = expr works)\n"
"  IF cond THEN stmt         Conditional single-line branch\n"
"  GOTO lineno               Jump to a line number\n"
"  GOSUB lineno              Call subroutine  (stack limit: 256)\n"
"  RETURN                    Return from subroutine\n"
"  FOR var = start TO end    Begin counted loop  (depth limit: 64)\n"
"  NEXT var                  End of counted loop\n"
"  RUN                       Run stored program from first line\n"
"  LIST                      Print the stored program\n"
"  REN                       Renumber stored lines in steps of 10\n"
"  BREAK                     Halt a running program (also usable in IF..THEN)\n"
"  STOP / END                Halt program execution\n"
"  BYE                       Exit the interpreter\n"
"  HELP                      Show this message\n"
"\n"
"Built-in functions\n"
"  LEFT$(s, n)               First n characters of s\n"
"  RIGHT$(s, n)              Last n characters of s\n"
"  MID$(s, i, n)             n chars from position i (1-based)\n"
"  LEN$(s)                   Length of s\n"
"  STR$(x)                   Convert number x to string\n"
"\n"
"Operators:  + - * /  =  <  >\n"
"  + on strings performs concatenation.\n"
"\n"
"Tips\n"
"  Lines starting with a number are stored in the program.\n"
"  Lines without a number are executed immediately.\n"
"  Press Ctrl-C during RUN to interrupt and return to the prompt.\n"
"  Type BREAK inside a running program (e.g. via IF..THEN) to halt."
    );
    puts("");
}

/* 
 * Command dispatch table
 */
typedef void (*CmdFn)(const char *);
typedef struct { const char *name; CmdFn fn; } CmdEntry;

static CmdEntry g_commands[] = {
    {"PRINT",cmd_print}, {"INPUT",cmd_input}, {"LET",cmd_let},
    {"IF",cmd_if},       {"GOTO",cmd_goto},   {"GOSUB",cmd_gosub},
    {"RETURN",cmd_return},{"FOR",cmd_for},    {"NEXT",cmd_next},
    {"RUN",cmd_run},     {"LIST",cmd_list},   {"REN",cmd_ren},
    {"BREAK",cmd_break}, {"STOP",cmd_stop},   {"END",cmd_stop},
    {"BYE",cmd_bye},     {"HELP",cmd_help},
    {NULL, NULL}
};

static void execute_line(const char *line) {
    const char *s = trim(line);
    if (!*s) return;

    char kw[32] = {0}; int ki = 0;
    const char *rest = s;
    while (*rest && !isspace((unsigned char)*rest) && ki < 31)
        kw[ki++] = (char)toupper((unsigned char)*rest++);
    while (isspace((unsigned char)*rest)) rest++;

    for (CmdEntry *ce = g_commands; ce->name; ce++) {
        if (strcmp(ce->name, kw) == 0) { ce->fn(rest); return; }
    }
    if (strchr(s, '=')) { cmd_let(s); return; }  /* implicit LET */

    fprintf(stderr, "[SYNTAX] Unknown command: '%s'\n", kw);
    suggest_command(kw);
}

/* 
 * Program runner
 */
static void run_program(void) {
    int steps = 0;
    g_interrupted = 0;

    while (G.pc >= 0 && G.pc < G.line_count) {
        if (g_interrupted) {
            printf("\nInterrupted at line %d.\n", G.lines[G.pc].lineno);
            g_interrupted = 0;
            G.pc = -1;
            return;
        }
        if (++steps > MAX_STEPS) {
            fprintf(stderr,
                "[RUN] Step limit (%d) reached — possible infinite loop.\n"
                "      Press Ctrl-C or use BREAK to halt.\n", MAX_STEPS);
            G.pc = -1;
            return;
        }

        int saved_pc = G.pc;
        int lineno   = G.lines[G.pc].lineno;

        g_active_jmp = &g_run_jmp;
        if (setjmp(g_run_jmp)) {
            if (g_err_kind == ERR_BREAK)
                printf("Break at line %d.\n", lineno);
            else
                fprintf(stderr, "[ERROR at line %d] %s\n", lineno, g_err_msg);
            G.pc = -1;
            g_active_jmp = NULL;
            return;
        }

        execute_line(G.lines[G.pc].text);

        if (G.pc == saved_pc) G.pc++;
    }
}

/* 
 * REPL / file loader
 */
static void feed_line(const char *raw) {
    const char *s = trim(raw);
    if (!*s) return;

    if (isdigit((unsigned char)*s)) {
        int lineno = 0;
        while (isdigit((unsigned char)*s)) { lineno = lineno*10 + (*s++ - '0'); }
        while (isspace((unsigned char)*s)) s++;
        g_active_jmp = &g_feed_jmp;
        if (setjmp(g_feed_jmp)) { g_active_jmp = NULL; fprintf(stderr, "[STORE] %s\n", g_err_msg); return; }
        store_line(lineno, s);
    } else {
        g_active_jmp = &g_feed_jmp;
        if (setjmp(g_feed_jmp)) {
            g_active_jmp = NULL;
            if (g_err_kind != ERR_BREAK) fprintf(stderr, "[ERROR] %s\n", g_err_msg);
            return;
        }
        execute_line(s);
    }
}

/* 
 * main
 */
int main(int argc, char *argv[]) {
    state_reset();
    signal(SIGINT, sigint_handler);

    if (argc > 1) {
        FILE *fp = fopen(argv[1], "r");
        if (!fp) { perror(argv[1]); return 1; }
        char line[MAX_LINE_LEN];
        while (fgets(line, sizeof line, fp)) {
            line[strcspn(line, "\n")] = '\0';
            feed_line(line);
        }
        fclose(fp);
        G.pc = 0;
        run_program();
    } else {
        puts("BASIC Interpreter  (type HELP for commands, BYE to quit)");
        char line[MAX_LINE_LEN];
        for (;;) {
            if (g_interrupted) { puts(""); g_interrupted = 0; }
            printf("> "); fflush(stdout);
            if (!fgets(line, sizeof line, stdin)) { puts(""); break; }
            line[strcspn(line, "\n")] = '\0';
            feed_line(line);
        }
    }
    return 0;
}
