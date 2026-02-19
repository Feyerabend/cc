// mol_eval.c
#include "mol.h"

/* apply a callable with a list of already-evaluated args */
static Value *apply(Value *func, Value **args, int argc, int line) {
    if (func->type == VAL_BUILTIN) {
        Builtin *b = func->data.builtin_val;
        if (b->arity >= 0 && b->arity != argc) {
            fprintf(stderr, "Line %d: builtin '%s' expects %d args, got %d\n",
                    line, b->name, b->arity, argc);
            exit(1);
        }
        return b->fn(args, argc);
    }
    if (func->type == VAL_CLOSURE) {
        Closure *c = func->data.closure_val;
        /* variadic: last param gets remaining as list */
        int min_args = c->variadic ? c->param_count - 1 : c->param_count;
        if (c->variadic) {
            if (argc < min_args) {
                fprintf(stderr, "Line %d: closure expects at least %d args, got %d\n",
                        line, min_args, argc);
                exit(1);
            }
        } else if (c->param_count != argc) {
            fprintf(stderr, "Line %d: closure '%s' expects %d args, got %d\n",
                    line, c->name ? c->name : "?", c->param_count, argc);
            exit(1);
        }
        Env *call_env = env_new(c->env);
        /* bind self-name for recursion */
        if (c->name) env_define(call_env, c->name, func);
        for (int i = 0; i < min_args; i++)
            env_define(call_env, c->params[i], args[i]);
        if (c->variadic) {
            /* collect rest as list */
            Value *rest = make_list_nil();
            for (int i = argc - 1; i >= min_args; i--)
                rest = make_list_cons(args[i], rest);
            env_define(call_env, c->params[min_args], rest);
        }
        return eval(c->body, call_env);
    }
    fprintf(stderr, "Line %d: cannot call value of type %d\n", line, func->type);
    exit(1);
}

Value *eval(Expr *expr, Env *env) {
    /* trampoline for tail-call-ish sequences */
tail_call:
    switch (expr->type) {

    case EXPR_LITERAL:
        return expr->data.literal.value;

    case EXPR_VAR: {
        Value *v = env_lookup(env, expr->data.var.name);
        if (!v) {
            fprintf(stderr, "Line %d: undefined variable '%s'\n",
                    expr->line, expr->data.var.name);
            exit(1);
        }
        return v;
    }

    case EXPR_LET: {
        Value *val = eval(expr->data.let.value, env);
        Env *new_env = env_new(env);
        env_define(new_env, expr->data.let.name, val);
        /* tail-recurse into body */
        env  = new_env;
        expr = expr->data.let.body;
        goto tail_call;
    }

    case EXPR_LETREC: {
        /* create a placeholder box, eval the value (which may close over it),
           then back-patch the box */
        Env *new_env = env_new(env);
        env_define(new_env, expr->data.letrec.name, make_null()); /* placeholder */
        Value *val = eval(expr->data.letrec.value, new_env);
        /* if it's a closure, set its name for friendly recursion */
        if (val->type == VAL_CLOSURE && !val->data.closure_val->name)
            val->data.closure_val->name = strdup(expr->data.letrec.name);
        env_update_box(new_env, expr->data.letrec.name, val);
        env  = new_env;
        expr = expr->data.letrec.body;
        goto tail_call;
    }

    case EXPR_LAMBDA:
        return make_closure(
            expr->data.lambda.params,
            expr->data.lambda.param_count,
            expr->data.lambda.variadic,
            expr->data.lambda.body,
            env,
            expr->data.lambda.name);

    case EXPR_CALL: {
        Value *func = eval(expr->data.call.func, env);
        int argc = expr->data.call.arg_count;
        Value **args = malloc(argc * sizeof(Value *));
        for (int i = 0; i < argc; i++)
            args[i] = eval(expr->data.call.args[i], env);
        Value *r = apply(func, args, argc, expr->line);
        free(args);
        return r;
    }

    case EXPR_ACCESS: {
        Value *obj = eval(expr->data.access.obj, env);
        if (obj->type != VAL_STRUCT) {
            fprintf(stderr, "Line %d: field access on non-struct\n", expr->line);
            exit(1);
        }
        return struct_get(obj->data.struct_val, expr->data.access.field);
    }

    case EXPR_ASSIGN: {
        Value *obj = eval(expr->data.assign.obj, env);
        if (obj->type != VAL_STRUCT) {
            fprintf(stderr, "Line %d: field assign on non-struct\n", expr->line);
            exit(1);
        }
        Value *val = eval(expr->data.assign.value, env);
        struct_set(obj->data.struct_val, expr->data.assign.field, val);
        return val;
    }

    case EXPR_CREATE: {
        Value *obj = make_struct();
        for (int i = 0; i < expr->data.create.field_count; i++) {
            Value *fv = eval(expr->data.create.field_exprs[i], env);
            struct_set(obj->data.struct_val,
                       expr->data.create.field_names[i], fv);
        }
        return obj;
    }

    case EXPR_VCALL: {
        Value *obj = eval(expr->data.vcall.obj, env);
        if (obj->type != VAL_STRUCT) {
            fprintf(stderr, "Line %d: method call on non-struct\n", expr->line);
            exit(1);
        }
        Value *vptr = struct_get(obj->data.struct_val, "vptr");
        if (vptr->type != VAL_STRUCT) {
            fprintf(stderr, "Line %d: object has no vtable\n", expr->line);
            exit(1);
        }
        Value *method = struct_get(vptr->data.struct_val, expr->data.vcall.method);
        if (method->type != VAL_CLOSURE && method->type != VAL_BUILTIN) {
            fprintf(stderr, "Line %d: method '%s' not found or not callable\n",
                    expr->line, expr->data.vcall.method);
            exit(1);
        }
        int argc = expr->data.vcall.arg_count + 1; /* +1 for self */
        Value **args = malloc(argc * sizeof(Value *));
        args[0] = obj;
        for (int i = 0; i < expr->data.vcall.arg_count; i++)
            args[i + 1] = eval(expr->data.vcall.args[i], env);
        Value *r = apply(method, args, argc, expr->line);
        free(args);
        return r;
    }

    case EXPR_IF: {
        Value *cond = eval(expr->data.ifelse.cond, env);
        if (is_truthy(cond)) {
            expr = expr->data.ifelse.then;
        } else {
            expr = expr->data.ifelse.els;
        }
        goto tail_call;
    }

    case EXPR_SEQ: {
        int n = expr->data.seq.expr_count;
        for (int i = 0; i < n - 1; i++)
            eval(expr->data.seq.exprs[i], env);
        /* tail on last */
        expr = expr->data.seq.exprs[n - 1];
        goto tail_call;
    }

    case EXPR_AND: {
        Value *left = eval(expr->data.and_or.left, env);
        if (!is_truthy(left)) return left;
        expr = expr->data.and_or.right;
        goto tail_call;
    }

    case EXPR_OR: {
        Value *left = eval(expr->data.and_or.left, env);
        if (is_truthy(left)) return left;
        expr = expr->data.and_or.right;
        goto tail_call;
    }

    case EXPR_BINOP: {
        const char *op = expr->data.binop.op;

        /* string concatenation via ++ */
        if (strcmp(op, "++") == 0) {
            Value *l = eval(expr->data.binop.left,  env);
            Value *r = eval(expr->data.binop.right, env);
            if (l->type == VAL_STRING && r->type == VAL_STRING) {
                size_t ll = strlen(l->data.str_val), rl = strlen(r->data.str_val);
                char *buf = malloc(ll + rl + 1);
                strcpy(buf, l->data.str_val);
                strcat(buf, r->data.str_val);
                Value *res = make_string(buf); free(buf); return res;
            }
            /* list append via ++ */
            if (l->type == VAL_LIST && r->type == VAL_LIST) {
                /* re-use append logic inline */
                Value *items[4096]; int n = 0;
                Value *lst = l;
                while (lst->type == VAL_LIST && lst->data.cons_val) {
                    items[n++] = lst->data.cons_val->head;
                    lst = lst->data.cons_val->tail;
                }
                Value *result = r;
                for (int i = n - 1; i >= 0; i--)
                    result = make_list_cons(items[i], result);
                return result;
            }
            fprintf(stderr, "Line %d: ++ requires strings or lists\n", expr->line);
            exit(1);
        }

        Value *left  = eval(expr->data.binop.left,  env);
        Value *right = eval(expr->data.binop.right, env);

        /* equality works across types */
        if (strcmp(op, "==") == 0) return make_bool(values_equal(left, right));
        if (strcmp(op, "!=") == 0) return make_bool(!values_equal(left, right));

        /* integer ops */
        if (left->type == VAL_INT && right->type == VAL_INT) {
            int64_t l = left->data.int_val, r = right->data.int_val;
            if (strcmp(op, "+")  == 0) return make_int(l + r);
            if (strcmp(op, "-")  == 0) return make_int(l - r);
            if (strcmp(op, "*")  == 0) return make_int(l * r);
            if (strcmp(op, "/")  == 0) {
                if (r == 0) { fprintf(stderr, "division by zero\n"); exit(1); }
                return make_int(l / r);
            }
            if (strcmp(op, "%")  == 0) {
                if (r == 0) { fprintf(stderr, "modulo by zero\n"); exit(1); }
                return make_int(l % r);
            }
            if (strcmp(op, "<")  == 0) return make_bool(l < r);
            if (strcmp(op, ">")  == 0) return make_bool(l > r);
            if (strcmp(op, "<=") == 0) return make_bool(l <= r);
            if (strcmp(op, ">=") == 0) return make_bool(l >= r);
        }

        fprintf(stderr, "Line %d: invalid operator '%s' for types %d, %d\n",
                expr->line, op, left->type, right->type);
        exit(1);
    }

    case EXPR_UNOP: {
        Value *v = eval(expr->data.unop.operand, env);
        const char *op = expr->data.unop.op;
        if (strcmp(op, "-") == 0 && v->type == VAL_INT)
            return make_int(-v->data.int_val);
        if (strcmp(op, "!") == 0 || strcmp(op, "not") == 0)
            return make_bool(!is_truthy(v));
        fprintf(stderr, "Line %d: invalid unary op '%s'\n", expr->line, op);
        exit(1);
    }

    default:
        fprintf(stderr, "Unknown expression type %d\n", expr->type);
        exit(1);
    }
}

/* ── printing ────────────────────────────────────────────────────────────── */

void print_value(Value *v) {
    switch (v->type) {
    case VAL_INT:
        printf("%lld", (long long)v->data.int_val); break;
    case VAL_BOOL:
        printf("%s", v->data.bool_val ? "true" : "false"); break;
    case VAL_STRING:
        printf("%s", v->data.str_val); break;
    case VAL_NULL:
        printf("null"); break;
    case VAL_CLOSURE:
        if (v->data.closure_val->name)
            printf("<fn:%s>", v->data.closure_val->name);
        else printf("<fn>");
        break;
    case VAL_BUILTIN:
        printf("<builtin:%s>", v->data.builtin_val->name); break;
    case VAL_LIST:
        printf("[");
        for (Value *cur = v; cur->type == VAL_LIST && cur->data.cons_val;
             cur = cur->data.cons_val->tail) {
            print_value(cur->data.cons_val->head);
            if (cur->data.cons_val->tail->type == VAL_LIST &&
                cur->data.cons_val->tail->data.cons_val)
                printf(", ");
        }
        printf("]"); break;
    case VAL_STRUCT: {
        printf("{");
        int first = 1;
        Struct *s = v->data.struct_val;
        for (int i = 0; i < s->field_count; i++) {
            if (strcmp(s->field_names[i], "vptr") == 0) continue;
            if (!first) printf(", ");
            printf("%s: ", s->field_names[i]);
            print_value(s->field_values[i]);
            first = 0;
        }
        printf("}"); break;
    }
    default: printf("<unknown>");
    }
}

void println_value(Value *v) { print_value(v); printf("\n"); }
