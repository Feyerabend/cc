// mol_parser.c
#include "mol.h"

/*
 * Grammar (informal):
 *
 * program    := expr (';' expr)*
 * expr       := let_expr | letrec_expr | if_expr | lambda | or_expr
 * let_expr   := 'let' id '=' expr ';' expr
 * letrec_expr:= 'letrec' id '=' expr ';' expr
 * if_expr    := 'if' expr 'then' expr ('else' expr)?   -- 'then' is optional (just whitespace)
 *             Actually: 'if' '(' expr ')' expr 'else' expr
 * lambda     := 'fn' '(' params ')' expr
 * or_expr    := and_expr ('or' and_expr)*
 * and_expr   := comparison ('and' comparison)*
 * comparison := additive (op additive)?
 * additive   := multiplicative (('+' | '-' | '++') multiplicative)*
 * multiplicative := unary (('*' | '/' | '%') unary)*
 * unary      := ('-' | '!' | 'not') unary | postfix
 * postfix    := primary ('(' args ')' | '.' id ('(' args ')')?  | '[' expr ']')*
 * primary    := INT | STRING | 'true' | 'false' | 'null' | id
 *             | '(' expr ')' | '{' fields '}' | '[' items ']'
 */

/* -- helpers -- */

static int at(Lexer *lex, TokenType t) { return lex->current.type == t; }

static Expr *set_line(Expr *e, int line) { if (e) e->line = line; return e; }

/* -- forward decls -- */
static Expr *parse_or(Lexer *lex);
static Expr *parse_unary(Lexer *lex);
static Expr *parse_postfix(Lexer *lex);
static Expr *parse_primary(Lexer *lex);

/* -- lambda ─-- */

static Expr *parse_lambda(Lexer *lex) {
    int line = lex->current.line;
    expect(lex, TOK_FN);
    /* optional name for named lambdas: fn name(params) body */
    char *lname = NULL;
    if (at(lex, TOK_ID)) {
        /* peek: is the next thing a '(' ? */
        lname = strdup(lex->current.text);
        next_token(lex);
    }
    expect(lex, TOK_LPAREN);
    char *params[MAX_PARAMS];
    int param_count = 0, variadic = 0;
    if (!at(lex, TOK_RPAREN)) {
        do {
            if (at(lex, TOK_DOTDOT)) {
                next_token(lex);
                params[param_count++] = expect_id(lex);
                variadic = 1;
                break;
            }
            if (!at(lex, TOK_ID)) {
                fprintf(stderr, "Line %d: expected param name\n", lex->current.line);
                exit(1);
            }
            params[param_count++] = strdup(lex->current.text);
            next_token(lex);
            if (at(lex, TOK_COMMA)) next_token(lex);
            else break;
        } while (1);
    }
    expect(lex, TOK_RPAREN);
    Expr *body = parse_expr(lex);
    Expr *e = expr_lambda(params, param_count, variadic, body, lname);
    for (int i = 0; i < param_count; i++) free(params[i]);
    free(lname);
    return set_line(e, line);
}

/* -- struct literal -- */

static Expr *parse_struct_lit(Lexer *lex) {
    int line = lex->current.line;
    expect(lex, TOK_LBRACE);
    char *names[MAX_FIELDS];
    Expr *exprs[MAX_FIELDS];
    int n = 0;
    if (!at(lex, TOK_RBRACE)) {
        do {
            if (!at(lex, TOK_ID)) {
                fprintf(stderr, "Line %d: expected field name\n", lex->current.line);
                exit(1);
            }
            names[n] = strdup(lex->current.text);
            next_token(lex);
            expect(lex, TOK_COLON);
            exprs[n] = parse_expr(lex);
            n++;
            if (at(lex, TOK_COMMA)) next_token(lex);
            else break;
        } while (!at(lex, TOK_RBRACE) && !at(lex, TOK_EOF));
    }
    expect(lex, TOK_RBRACE);
    Expr *e = expr_create(names, exprs, n);
    for (int i = 0; i < n; i++) free(names[i]);
    return set_line(e, line);
}

/* -- list literal -- */

static Expr *parse_list_lit(Lexer *lex) {
    int line = lex->current.line;
    expect(lex, TOK_LBRACK);
    /* build via cons/nil — emit call to list() builtin with all items */
    Expr *items[MAX_FIELDS];
    int n = 0;
    if (!at(lex, TOK_RBRACK)) {
        do {
            items[n++] = parse_expr(lex);
            if (at(lex, TOK_COMMA)) next_token(lex);
            else break;
        } while (!at(lex, TOK_RBRACK) && !at(lex, TOK_EOF));
    }
    expect(lex, TOK_RBRACK);
    if (n == 0) return set_line(expr_literal(make_list_nil()), line);
    /* emit list(e1, e2, ...) call */
    Expr *list_fn = expr_var("list");
    return set_line(expr_call(list_fn, items, n), line);
}

/* -- primary -- */

static Expr *parse_primary(Lexer *lex) {
    int line = lex->current.line;
    if (at(lex, TOK_INT)) {
        int64_t v = lex->current.int_val;
        next_token(lex);
        return set_line(expr_literal(make_int(v)), line);
    }
    if (at(lex, TOK_STRING)) {
        Value *s = make_string(lex->current.text);
        next_token(lex);
        return set_line(expr_literal(s), line);
    }
    if (at(lex, TOK_TRUE))  { next_token(lex); return set_line(expr_literal(make_bool(1)), line); }
    if (at(lex, TOK_FALSE)) { next_token(lex); return set_line(expr_literal(make_bool(0)), line); }
    if (at(lex, TOK_NULL))  { next_token(lex); return set_line(expr_literal(make_null()),  line); }
    if (at(lex, TOK_ID)) {
        char *name = strdup(lex->current.text);
        next_token(lex);
        Expr *e = set_line(expr_var(name), line);
        free(name);
        return e;
    }
    if (at(lex, TOK_FN))     return parse_lambda(lex);
    if (at(lex, TOK_LBRACE)) return parse_struct_lit(lex);
    if (at(lex, TOK_LBRACK)) return parse_list_lit(lex);
    if (at(lex, TOK_LPAREN)) {
        next_token(lex);
        Expr *e = parse_expr(lex);
        expect(lex, TOK_RPAREN);
        return e;
    }
    fprintf(stderr, "Line %d: unexpected token '%s'\n", line,
            lex->current.text ? lex->current.text : "(none)");
    exit(1);
}

/* -- postfix: calls, field access, method calls -- */

static Expr *parse_args(Lexer *lex, Expr **args_out, int *argc_out) {
    expect(lex, TOK_LPAREN);
    Expr *args[MAX_PARAMS];
    int argc = 0;
    if (!at(lex, TOK_RPAREN)) {
        do {
            if (argc >= MAX_PARAMS) { fprintf(stderr, "too many args\n"); exit(1); }
            args[argc++] = parse_expr(lex);
            if (at(lex, TOK_COMMA)) next_token(lex);
            else break;
        } while (!at(lex, TOK_RPAREN) && !at(lex, TOK_EOF));
    }
    expect(lex, TOK_RPAREN);
    for (int i = 0; i < argc; i++) args_out[i] = args[i];
    *argc_out = argc;
    return NULL;
}

static Expr *parse_postfix(Lexer *lex) {
    int line = lex->current.line;
    Expr *e = parse_primary(lex);
    while (1) {
        if (at(lex, TOK_LPAREN)) {
            Expr *args[MAX_PARAMS]; int argc;
            parse_args(lex, args, &argc);
            e = set_line(expr_call(e, args, argc), line);
        } else if (at(lex, TOK_DOT)) {
            next_token(lex);
            char *field = expect_id(lex);
            if (at(lex, TOK_LPAREN)) {
                /* method call (vcall) */
                Expr *args[MAX_PARAMS]; int argc;
                parse_args(lex, args, &argc);
                e = set_line(expr_vcall(e, field, args, argc), line);
            } else if (at(lex, TOK_EQ)) {
                /* field assignment: obj.field = expr */
                next_token(lex);
                Expr *val = parse_expr(lex);
                e = set_line(expr_assign(e, field, val), line);
            } else {
                e = set_line(expr_access(e, field), line);
            }
            free(field);
        } else {
            break;
        }
    }
    return e;
}

/* -- unary -- */

static Expr *parse_unary(Lexer *lex) {
    int line = lex->current.line;
    if (at(lex, TOK_MINUS)) {
        next_token(lex);
        return set_line(expr_unop("-", parse_unary(lex)), line);
    }
    if (at(lex, TOK_BANG) || at(lex, TOK_NOT)) {
        next_token(lex);
        return set_line(expr_unop("!", parse_unary(lex)), line);
    }
    return parse_postfix(lex);
}

/* -- multiplicative -- */

static Expr *parse_multiplicative(Lexer *lex) {
    Expr *left = parse_unary(lex);
    while (at(lex, TOK_STAR) || at(lex, TOK_SLASH) || at(lex, TOK_PERCENT)) {
        int line = lex->current.line;
        char *op = strdup(lex->current.text);
        next_token(lex);
        left = set_line(expr_binop(op, left, parse_unary(lex)), line);
        free(op);
    }
    return left;
}

/* -- additive -- */

static Expr *parse_additive(Lexer *lex) {
    Expr *left = parse_multiplicative(lex);
    while (at(lex, TOK_PLUS) || at(lex, TOK_MINUS)) {
        int line = lex->current.line;
        char *op = strdup(lex->current.text);
        /* handle ++ as a special concat op */
        if (strcmp(op, "++") == 0 || strcmp(op, "+") == 0 || strcmp(op, "-") == 0) {
            next_token(lex);
            left = set_line(expr_binop(op, left, parse_multiplicative(lex)), line);
            free(op);
        } else {
            free(op); break;
        }
    }
    return left;
}

/* -- comparison -- */

static Expr *parse_comparison(Lexer *lex) {
    Expr *left = parse_additive(lex);
    while (at(lex, TOK_EQEQ) || at(lex, TOK_NEQ) ||
           at(lex, TOK_LT)   || at(lex, TOK_GT)  ||
           at(lex, TOK_LTE)  || at(lex, TOK_GTE)) {
        int line = lex->current.line;
        char *op = strdup(lex->current.text);
        next_token(lex);
        left = set_line(expr_binop(op, left, parse_additive(lex)), line);
        free(op);
    }
    return left;
}

/* -- and / or -- */

static Expr *parse_and(Lexer *lex) {
    Expr *left = parse_comparison(lex);
    while (at(lex, TOK_AND)) {
        int line = lex->current.line;
        next_token(lex);
        left = set_line(expr_and(left, parse_comparison(lex)), line);
    }
    return left;
}

static Expr *parse_or(Lexer *lex) {
    Expr *left = parse_and(lex);
    while (at(lex, TOK_OR)) {
        int line = lex->current.line;
        next_token(lex);
        left = set_line(expr_or(left, parse_and(lex)), line);
    }
    return left;
}

/* -- if/else -- */

static Expr *parse_if(Lexer *lex) {
    int line = lex->current.line;
    expect(lex, TOK_IF);
    /* support both 'if (cond)' and 'if cond' */
    int parens = at(lex, TOK_LPAREN);
    if (parens) next_token(lex);
    Expr *cond = parse_or(lex);
    if (parens) expect(lex, TOK_RPAREN);
    Expr *then = parse_expr(lex);
    Expr *els  = NULL;
    if (at(lex, TOK_ELSE)) {
        next_token(lex);
        els = parse_expr(lex);
    } else {
        els = expr_literal(make_null()); /* else null */
    }
    return set_line(expr_if(cond, then, els), line);
}

/* -- top-level expr -- */

Expr *parse_expr(Lexer *lex) {
    int line = lex->current.line;

    /* let id = expr [ ; expr ] */
    if (at(lex, TOK_LET)) {
        next_token(lex);
        char *name = expect_id(lex);
        expect(lex, TOK_EQ);
        Expr *val  = parse_expr(lex);
        Expr *body;
        if (at(lex, TOK_SEMI)) {
            next_token(lex);
            body = at(lex, TOK_EOF) ? expr_var(name) : parse_expr(lex);
        } else {
            body = expr_var(name); /* bare `let x = e` — body defaults to x */
        }
        Expr *e = set_line(expr_let(name, val, body), line);
        free(name); return e;
    }

    /* letrec id = expr [ ; expr ] */
    if (at(lex, TOK_LETREC)) {
        next_token(lex);
        char *name = expect_id(lex);
        expect(lex, TOK_EQ);
        Expr *val  = parse_expr(lex);
        Expr *body;
        if (at(lex, TOK_SEMI)) {
            next_token(lex);
            body = at(lex, TOK_EOF) ? expr_var(name) : parse_expr(lex);
        } else {
            body = expr_var(name); /* bare `letrec f = fn..` — body defaults to f */
        }
        Expr *e = set_line(expr_letrec(name, val, body), line);
        free(name); return e;
    }

    /* if ... */
    if (at(lex, TOK_IF)) return parse_if(lex);

    /* fn ... */
    if (at(lex, TOK_FN)) return parse_lambda(lex);

    return parse_or(lex);
}

/* -- program -- */

Expr *parse_program(Lexer *lex) {
    Expr *exprs[MAX_SEQ];
    int n = 0;
    while (!at(lex, TOK_EOF)) {
        if (n >= MAX_SEQ) { fprintf(stderr, "too many top-level expressions\n"); exit(1); }
        exprs[n++] = parse_expr(lex);
        if (at(lex, TOK_SEMI)) next_token(lex);
    }
    if (n == 0) return expr_literal(make_null());
    if (n == 1) return exprs[0];
    return expr_seq(exprs, n);
}

Expr *parse(const char *input) {
    Lexer *lex = make_lexer(input);
    Expr  *result = parse_program(lex);
    free(lex->current.text);
    free(lex);
    return result;
}
