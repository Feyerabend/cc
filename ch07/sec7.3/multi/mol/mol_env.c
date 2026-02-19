// mol_env.c
#include "mol.h"

Env *env_new(Env *parent) {
    Env *e = calloc(1, sizeof(Env));
    e->parent = parent;
    return e;
}

/* define a fresh binding in THIS scope */
void env_define(Env *env, const char *name, Value *val) {
    /* check for duplicate in current frame (update if found) */
    for (EnvEntry *e = env->head; e; e = e->next) {
        if (strcmp(e->name, name) == 0) {
            *e->box = val;
            return;
        }
    }
    EnvEntry *entry = malloc(sizeof(EnvEntry));
    entry->name = strdup(name);
    entry->box  = malloc(sizeof(Value *));
    *entry->box = val;
    entry->next = env->head;
    env->head   = entry;
}

/* walk up scope chain */
Value *env_lookup(Env *env, const char *name) {
    for (Env *scope = env; scope; scope = scope->parent) {
        for (EnvEntry *e = scope->head; e; e = e->next) {
            if (strcmp(e->name, name) == 0)
                return *e->box;
        }
    }
    return NULL;
}

/* mutate the box for letrec back-patching */
void env_update_box(Env *env, const char *name, Value *val) {
    for (Env *scope = env; scope; scope = scope->parent) {
        for (EnvEntry *e = scope->head; e; e = e->next) {
            if (strcmp(e->name, name) == 0) {
                *e->box = val;
                return;
            }
        }
    }
    fprintf(stderr, "env_update_box: name not found: %s\n", name);
    exit(1);
}

/* ── built-in functions ─────────────────────────────────────────────────── */

static Value *builtin_print(Value **args, int argc) {
    for (int i = 0; i < argc; i++) {
        if (i) printf(" ");
        print_value(args[i]);
    }
    printf("\n");
    return make_null();
}

static Value *builtin_to_string(Value **args, int argc) {
    (void)argc;
    char buf[256];
    Value *v = args[0];
    switch (v->type) {
        case VAL_INT:    snprintf(buf, sizeof(buf), "%lld", (long long)v->data.int_val); return make_string(buf);
        case VAL_BOOL:   return make_string(v->data.bool_val ? "true" : "false");
        case VAL_STRING: return v;
        case VAL_NULL:   return make_string("null");
        default:         return make_string("<value>");
    }
}

static Value *builtin_int_of(Value **args, int argc) {
    (void)argc;
    Value *v = args[0];
    if (v->type == VAL_INT) return v;
    if (v->type == VAL_BOOL) return make_int(v->data.bool_val);
    if (v->type == VAL_STRING) return make_int(atoll(v->data.str_val));
    return make_int(0);
}

static Value *builtin_type_of(Value **args, int argc) {
    (void)argc;
    switch (args[0]->type) {
        case VAL_INT:     return make_string("int");
        case VAL_BOOL:    return make_string("bool");
        case VAL_STRING:  return make_string("string");
        case VAL_STRUCT:  return make_string("struct");
        case VAL_CLOSURE: return make_string("fn");
        case VAL_BUILTIN: return make_string("builtin");
        case VAL_LIST:    return make_string("list");
        case VAL_NULL:    return make_string("null");
        default:          return make_string("unknown");
    }
}

/* list builtins */
static Value *builtin_cons(Value **args, int argc) {
    (void)argc;
    return make_list_cons(args[0], args[1]);
}
static Value *builtin_head(Value **args, int argc) {
    (void)argc;
    if (args[0]->type != VAL_LIST || !args[0]->data.cons_val) {
        fprintf(stderr, "head: empty list\n"); exit(1);
    }
    return args[0]->data.cons_val->head;
}
static Value *builtin_tail(Value **args, int argc) {
    (void)argc;
    if (args[0]->type != VAL_LIST || !args[0]->data.cons_val) {
        fprintf(stderr, "tail: empty list\n"); exit(1);
    }
    return args[0]->data.cons_val->tail;
}
static Value *builtin_is_nil(Value **args, int argc) {
    (void)argc;
    return make_bool(args[0]->type == VAL_LIST && !args[0]->data.cons_val);
}
static Value *builtin_is_list(Value **args, int argc) {
    (void)argc;
    return make_bool(args[0]->type == VAL_LIST);
}

/* list builder: list(1,2,3) */
static Value *builtin_list(Value **args, int argc) {
    Value *result = make_list_nil();
    for (int i = argc - 1; i >= 0; i--)
        result = make_list_cons(args[i], result);
    return result;
}

/* map(f, lst) */
static Value *builtin_map(Value **args, int argc) {
    (void)argc;
    Value *f   = args[0];
    Value *lst = args[1];
    Value *result = make_list_nil();
    /* collect items */
    Value *items[4096]; int n = 0;
    while (lst->type == VAL_LIST && lst->data.cons_val) {
        items[n++] = lst->data.cons_val->head;
        lst = lst->data.cons_val->tail;
    }
    for (int i = n - 1; i >= 0; i--) {
        Value *mapped;
        if (f->type == VAL_BUILTIN) {
            mapped = f->data.builtin_val->fn(&items[i], 1);
        } else if (f->type == VAL_CLOSURE) {
            Closure *c = f->data.closure_val;
            Env *call_env = env_new(c->env);
            env_define(call_env, c->params[0], items[i]);
            mapped = eval(c->body, call_env);
        } else { fprintf(stderr, "map: not a function\n"); exit(1); }
        result = make_list_cons(mapped, result);
    }
    return result;
}

/* filter(f, lst) */
static Value *builtin_filter(Value **args, int argc) {
    (void)argc;
    Value *f   = args[0];
    Value *lst = args[1];
    Value *result = make_list_nil();
    Value *items[4096]; int n = 0;
    while (lst->type == VAL_LIST && lst->data.cons_val) {
        items[n++] = lst->data.cons_val->head;
        lst = lst->data.cons_val->tail;
    }
    for (int i = n - 1; i >= 0; i--) {
        Value *test;
        if (f->type == VAL_BUILTIN) {
            test = f->data.builtin_val->fn(&items[i], 1);
        } else if (f->type == VAL_CLOSURE) {
            Closure *c = f->data.closure_val;
            Env *call_env = env_new(c->env);
            env_define(call_env, c->params[0], items[i]);
            test = eval(c->body, call_env);
        } else { fprintf(stderr, "filter: not a function\n"); exit(1); }
        if (is_truthy(test)) result = make_list_cons(items[i], result);
    }
    return result;
}

/* foldl(f, init, lst) */
static Value *builtin_foldl(Value **args, int argc) {
    (void)argc;
    Value *f   = args[0];
    Value *acc = args[1];
    Value *lst = args[2];
    while (lst->type == VAL_LIST && lst->data.cons_val) {
        Value *item = lst->data.cons_val->head;
        if (f->type == VAL_BUILTIN) {
            Value *fargs[2] = {acc, item};
            acc = f->data.builtin_val->fn(fargs, 2);
        } else if (f->type == VAL_CLOSURE) {
            Closure *c = f->data.closure_val;
            Env *call_env = env_new(c->env);
            env_define(call_env, c->params[0], acc);
            env_define(call_env, c->params[1], item);
            acc = eval(c->body, call_env);
        } else { fprintf(stderr, "foldl: not a function\n"); exit(1); }
        lst = lst->data.cons_val->tail;
    }
    return acc;
}

/* len(lst) */
static Value *builtin_len(Value **args, int argc) {
    (void)argc;
    if (args[0]->type == VAL_STRING)
        return make_int((int64_t)strlen(args[0]->data.str_val));
    int64_t n = 0;
    Value *lst = args[0];
    while (lst->type == VAL_LIST && lst->data.cons_val) { n++; lst = lst->data.cons_val->tail; }
    return make_int(n);
}

/* append(lst1, lst2) */
static Value *builtin_append(Value **args, int argc) {
    (void)argc;
    Value *lst = args[0];
    Value *items[4096]; int n = 0;
    while (lst->type == VAL_LIST && lst->data.cons_val) {
        items[n++] = lst->data.cons_val->head;
        lst = lst->data.cons_val->tail;
    }
    Value *result = args[1];
    for (int i = n - 1; i >= 0; i--)
        result = make_list_cons(items[i], result);
    return result;
}

/* string operations */
static Value *builtin_str_concat(Value **args, int argc) {
    size_t total = 0;
    for (int i = 0; i < argc; i++) {
        if (args[i]->type == VAL_STRING) total += strlen(args[i]->data.str_val);
    }
    char *buf = malloc(total + 1); buf[0] = '\0';
    for (int i = 0; i < argc; i++)
        if (args[i]->type == VAL_STRING) strcat(buf, args[i]->data.str_val);
    Value *r = make_string(buf); free(buf); return r;
}

static Value *builtin_assert(Value **args, int argc) {
    (void)argc;
    if (!is_truthy(args[0])) {
        const char *msg = (argc > 1 && args[1]->type == VAL_STRING)
                        ? args[1]->data.str_val : "assertion failed";
        fprintf(stderr, "AssertionError: %s\n", msg);
        exit(1);
    }
    return make_null();
}

static Value *builtin_error(Value **args, int argc) {
    (void)argc;
    const char *msg = (args[0]->type == VAL_STRING) ? args[0]->data.str_val : "error";
    fprintf(stderr, "Error: %s\n", msg);
    exit(1);
}

/* compose: compose(f, g) = fn(x) f(g(x)) — done in mol itself via builtins,
   but convenient to have it native */
static Value *builtin_not(Value **args, int argc) {
    (void)argc;
    return make_bool(!is_truthy(args[0]));
}

/* math */
static Value *builtin_abs(Value **args, int argc) {
    (void)argc;
    int64_t n = args[0]->data.int_val;
    return make_int(n < 0 ? -n : n);
}
static Value *builtin_max(Value **args, int argc) {
    (void)argc;
    return make_int(args[0]->data.int_val > args[1]->data.int_val
                    ? args[0]->data.int_val : args[1]->data.int_val);
}
static Value *builtin_min(Value **args, int argc) {
    (void)argc;
    return make_int(args[0]->data.int_val < args[1]->data.int_val
                    ? args[0]->data.int_val : args[1]->data.int_val);
}

/* make_global_env: populate with all builtins */
Env *make_global_env(void) {
    Env *env = env_new(NULL);
    /* predefine nil */
    env_define(env, "nil",  make_list_nil());
    env_define(env, "true",  make_bool(1));
    env_define(env, "false", make_bool(0));
    env_define(env, "null",  make_null());

#define DEF(name, fn, arity) env_define(env, name, make_builtin(name, fn, arity))
    DEF("print",     builtin_print,      -1);
    DEF("to_string", builtin_to_string,   1);
    DEF("int_of",    builtin_int_of,      1);
    DEF("type_of",   builtin_type_of,     1);
    DEF("not",       builtin_not,         1);
    DEF("abs",       builtin_abs,         1);
    DEF("max",       builtin_max,         2);
    DEF("min",       builtin_min,         2);
    DEF("assert",    builtin_assert,     -1);
    DEF("error",     builtin_error,       1);

    DEF("cons",      builtin_cons,        2);
    DEF("head",      builtin_head,        1);
    DEF("tail",      builtin_tail,        1);
    DEF("nil?",      builtin_is_nil,      1);
    DEF("list?",     builtin_is_list,     1);
    DEF("list",      builtin_list,       -1);
    DEF("len",       builtin_len,         1);
    DEF("append",    builtin_append,      2);
    DEF("map",       builtin_map,         2);
    DEF("filter",    builtin_filter,      2);
    DEF("foldl",     builtin_foldl,       3);

    DEF("str_concat",builtin_str_concat, -1);
#undef DEF
    return env;
}

/* keep backward-compat alias */
Env *make_env(void) { return make_global_env(); }
