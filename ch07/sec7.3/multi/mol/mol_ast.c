// mol_ast.c
#include "mol.h"

static Expr *new_expr(ExprType t) {
    Expr *e = calloc(1, sizeof(Expr));
    e->type = t;
    return e;
}

Expr *expr_literal(Value *val) {
    Expr *e = new_expr(EXPR_LITERAL);
    e->data.literal.value = val; return e;
}
Expr *expr_var(const char *name) {
    Expr *e = new_expr(EXPR_VAR);
    e->data.var.name = strdup(name); return e;
}
Expr *expr_let(const char *name, Expr *value, Expr *body) {
    Expr *e = new_expr(EXPR_LET);
    e->data.let.name = strdup(name);
    e->data.let.value = value;
    e->data.let.body  = body; return e;
}
Expr *expr_letrec(const char *name, Expr *value, Expr *body) {
    Expr *e = new_expr(EXPR_LETREC);
    e->data.letrec.name  = strdup(name);
    e->data.letrec.value = value;
    e->data.letrec.body  = body; return e;
}
Expr *expr_lambda(char **params, int param_count, int variadic,
                  Expr *body, const char *name) {
    Expr *e = new_expr(EXPR_LAMBDA);
    e->data.lambda.param_count = param_count;
    e->data.lambda.variadic    = variadic;
    e->data.lambda.params = malloc(param_count * sizeof(char *));
    for (int i = 0; i < param_count; i++)
        e->data.lambda.params[i] = strdup(params[i]);
    e->data.lambda.body = body;
    e->data.lambda.name = name ? strdup(name) : NULL;
    return e;
}
Expr *expr_call(Expr *func, Expr **args, int arg_count) {
    Expr *e = new_expr(EXPR_CALL);
    e->data.call.func      = func;
    e->data.call.arg_count = arg_count;
    e->data.call.args = malloc(arg_count * sizeof(Expr *));
    for (int i = 0; i < arg_count; i++) e->data.call.args[i] = args[i];
    return e;
}
Expr *expr_access(Expr *obj, const char *field) {
    Expr *e = new_expr(EXPR_ACCESS);
    e->data.access.obj   = obj;
    e->data.access.field = strdup(field); return e;
}
Expr *expr_assign(Expr *obj, const char *field, Expr *value) {
    Expr *e = new_expr(EXPR_ASSIGN);
    e->data.assign.obj   = obj;
    e->data.assign.field = strdup(field);
    e->data.assign.value = value; return e;
}
Expr *expr_create(char **field_names, Expr **field_exprs, int field_count) {
    Expr *e = new_expr(EXPR_CREATE);
    e->data.create.field_count = field_count;
    e->data.create.field_names  = malloc(field_count * sizeof(char *));
    e->data.create.field_exprs  = malloc(field_count * sizeof(Expr *));
    for (int i = 0; i < field_count; i++) {
        e->data.create.field_names[i] = strdup(field_names[i]);
        e->data.create.field_exprs[i] = field_exprs[i];
    }
    return e;
}
Expr *expr_vcall(Expr *obj, const char *method, Expr **args, int arg_count) {
    Expr *e = new_expr(EXPR_VCALL);
    e->data.vcall.obj        = obj;
    e->data.vcall.method     = strdup(method);
    e->data.vcall.arg_count  = arg_count;
    e->data.vcall.args = malloc(arg_count * sizeof(Expr *));
    for (int i = 0; i < arg_count; i++) e->data.vcall.args[i] = args[i];
    return e;
}
Expr *expr_binop(const char *op, Expr *left, Expr *right) {
    Expr *e = new_expr(EXPR_BINOP);
    e->data.binop.op    = strdup(op);
    e->data.binop.left  = left;
    e->data.binop.right = right; return e;
}
Expr *expr_unop(const char *op, Expr *operand) {
    Expr *e = new_expr(EXPR_UNOP);
    e->data.unop.op      = strdup(op);
    e->data.unop.operand = operand; return e;
}
Expr *expr_if(Expr *cond, Expr *then, Expr *els) {
    Expr *e = new_expr(EXPR_IF);
    e->data.ifelse.cond = cond;
    e->data.ifelse.then = then;
    e->data.ifelse.els  = els; return e;
}
Expr *expr_seq(Expr **exprs, int expr_count) {
    Expr *e = new_expr(EXPR_SEQ);
    e->data.seq.expr_count = expr_count;
    e->data.seq.exprs = malloc(expr_count * sizeof(Expr *));
    for (int i = 0; i < expr_count; i++) e->data.seq.exprs[i] = exprs[i];
    return e;
}
Expr *expr_and(Expr *left, Expr *right) {
    Expr *e = new_expr(EXPR_AND);
    e->data.and_or.left = left; e->data.and_or.right = right; return e;
}
Expr *expr_or(Expr *left, Expr *right) {
    Expr *e = new_expr(EXPR_OR);
    e->data.and_or.left = left; e->data.and_or.right = right; return e;
}
