// mol.h — Enhanced Mol Language
#ifndef MOL_H
#define MOL_H

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>

#define MAX_PARAMS  32
#define MAX_FIELDS  64
#define MAX_INPUT 65536
#define MAX_SEQ     64

/* ────────────────── FORWARD DECLS ────────────────────────────────────────── */
typedef struct Value   Value;
typedef struct Expr    Expr;
typedef struct Env     Env;

/* ────────────────── VALUES ───────────────────────────────────────────────── */

typedef enum {
    VAL_INT, VAL_BOOL, VAL_STRING, VAL_STRUCT,
    VAL_CLOSURE, VAL_BUILTIN, VAL_LIST, VAL_NULL,
} ValueType;

typedef struct {
    char  **params;
    int     param_count;
    int     variadic;   /* 1 => last param collects remaining args as list */
    Expr   *body;
    Env    *env;
    char   *name;
} Closure;

typedef Value *(*BuiltinFn)(Value **args, int argc);
typedef struct { char *name; BuiltinFn fn; int arity; /* -1=variadic */ } Builtin;

typedef struct {
    char  **field_names;
    Value **field_values;
    int     field_count;
    int     field_cap;
} Struct;

typedef struct Cons { Value *head; Value *tail; } Cons;

struct Value {
    ValueType type;
    union {
        int64_t   int_val;
        int       bool_val;
        char     *str_val;
        Struct   *struct_val;
        Closure  *closure_val;
        Builtin  *builtin_val;
        Cons     *cons_val;   /* NULL => nil */
    } data;
};

/* ────────────────── AST ──────────────────────────────────────────────────── */

typedef enum {
    EXPR_LITERAL, EXPR_VAR,
    EXPR_LET,    /* let x = e; body  — non-recursive */
    EXPR_LETREC, /* letrec f = fn...; body  — recursive */
    EXPR_LAMBDA, EXPR_CALL,
    EXPR_ACCESS, EXPR_ASSIGN, EXPR_CREATE, EXPR_VCALL,
    EXPR_BINOP, EXPR_UNOP,
    EXPR_IF,
    EXPR_SEQ,
    EXPR_AND, EXPR_OR,
} ExprType;

struct Expr {
    ExprType type;
    int      line;
    union {
        struct { Value *value; }                            literal;
        struct { char  *name; }                             var;
        struct { char  *name; Expr *value; Expr *body; }   let;
        struct { char  *name; Expr *value; Expr *body; }   letrec;
        struct {
            char **params; int param_count; int variadic;
            Expr  *body;   char *name;
        } lambda;
        struct { Expr *func; Expr **args; int arg_count; }       call;
        struct { Expr *obj;  char *field; }                      access;
        struct { Expr *obj;  char *field; Expr *value; }         assign;
        struct { char **field_names; Expr **field_exprs; int field_count; } create;
        struct { Expr *obj; char *method; Expr **args; int arg_count; }     vcall;
        struct { char *op; Expr *left;    Expr *right; }         binop;
        struct { char *op; Expr *operand; }                      unop;
        struct { Expr *cond; Expr *then;  Expr *els; }           ifelse;
        struct { Expr **exprs; int expr_count; }                 seq;
        struct { Expr *left;   Expr *right; }                    and_or;
    } data;
};

/* ────────────────── LEXER ────────────────────────────────────────────────── */

typedef enum {
    TOK_EOF, TOK_INT, TOK_STRING, TOK_ID,
    TOK_LET, TOK_LETREC, TOK_FN, TOK_NULL, TOK_TRUE, TOK_FALSE,
    TOK_IF, TOK_ELSE, TOK_AND, TOK_OR, TOK_NOT,
    TOK_LPAREN, TOK_RPAREN, TOK_LBRACE, TOK_RBRACE, TOK_LBRACK, TOK_RBRACK,
    TOK_COMMA, TOK_DOT, TOK_SEMI, TOK_COLON,
    TOK_PLUS, TOK_MINUS, TOK_STAR, TOK_SLASH, TOK_PERCENT,
    TOK_EQ, TOK_EQEQ, TOK_NEQ, TOK_LT, TOK_GT, TOK_LTE, TOK_GTE,
    TOK_DOTDOT, /* .. for variadic rest marker */
    TOK_BANG,
} TokenType;

typedef struct { TokenType type; char *text; int64_t int_val; int line; } Token;
typedef struct { const char *input; int pos; int line; Token current; } Lexer;

/* ────────────────── ENV ──────────────────────────────────────────────────── */

typedef struct EnvEntry {
    char            *name;
    Value          **box;  /* pointer-to-pointer enables letrec mutation */
    struct EnvEntry *next;
} EnvEntry;

struct Env {
    EnvEntry *head;
    Env      *parent;
};

/* ────────────────── PROTOTYPES ───────────────────────────────────────────── */

/* values */
Value *make_int(int64_t n);
Value *make_bool(int b);
Value *make_string(const char *s);
Value *make_null(void);
Value *make_struct(void);
Value *make_list_nil(void);
Value *make_list_cons(Value *h, Value *t);
Value *make_closure(char **params, int param_count, int variadic,
                    Expr *body, Env *env, const char *name);
Value *make_builtin(const char *name, BuiltinFn fn, int arity);
int    is_truthy(Value *v);
int    values_equal(Value *a, Value *b);
void   struct_set(Struct *s, const char *name, Value *val);
Value *struct_get(Struct *s, const char *name);

/* env */
Env   *env_new(Env *parent);
void   env_define(Env *env, const char *name, Value *val);
Value *env_lookup(Env *env, const char *name);
void   env_update_box(Env *env, const char *name, Value *val);
Env   *make_global_env(void);

/* ast */
Expr *expr_literal(Value *val);
Expr *expr_var(const char *name);
Expr *expr_let(const char *name, Expr *value, Expr *body);
Expr *expr_letrec(const char *name, Expr *value, Expr *body);
Expr *expr_lambda(char **params, int param_count, int variadic,
                  Expr *body, const char *name);
Expr *expr_call(Expr *func, Expr **args, int arg_count);
Expr *expr_access(Expr *obj, const char *field);
Expr *expr_assign(Expr *obj, const char *field, Expr *value);
Expr *expr_create(char **field_names, Expr **field_exprs, int field_count);
Expr *expr_vcall(Expr *obj, const char *method, Expr **args, int arg_count);
Expr *expr_binop(const char *op, Expr *left, Expr *right);
Expr *expr_unop(const char *op, Expr *operand);
Expr *expr_if(Expr *cond, Expr *then, Expr *els);
Expr *expr_seq(Expr **exprs, int expr_count);
Expr *expr_and(Expr *left, Expr *right);
Expr *expr_or(Expr *left, Expr *right);

/* eval */
Value *eval(Expr *expr, Env *env);
void   print_value(Value *v);
void   println_value(Value *v);

/* lexer */
Lexer *make_lexer(const char *input);
void   next_token(Lexer *lex);
int    match(Lexer *lex, TokenType type);
void   expect(Lexer *lex, TokenType type);
char  *expect_id(Lexer *lex);

/* parser */
Expr *parse_expr(Lexer *lex);
Expr *parse_program(Lexer *lex);
Expr *parse(const char *input);

/* runner */
void run_code(const char *code);
void run_file(const char *path);
void run_repl(void);

#endif /* MOL_H */
