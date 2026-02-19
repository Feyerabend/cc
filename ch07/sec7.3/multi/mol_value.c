// mol_value.c
#include "mol.h"

Value *make_int(int64_t n) {
    Value *v = malloc(sizeof(Value));
    v->type = VAL_INT; v->data.int_val = n; return v;
}
Value *make_bool(int b) {
    Value *v = malloc(sizeof(Value));
    v->type = VAL_BOOL; v->data.bool_val = (b ? 1 : 0); return v;
}
Value *make_string(const char *s) {
    Value *v = malloc(sizeof(Value));
    v->type = VAL_STRING; v->data.str_val = strdup(s); return v;
}
Value *make_null(void) {
    Value *v = malloc(sizeof(Value));
    v->type = VAL_NULL; return v;
}
Value *make_struct(void) {
    Value *v = malloc(sizeof(Value));
    v->type = VAL_STRUCT;
    Struct *s = calloc(1, sizeof(Struct));
    s->field_cap = 8;
    s->field_names  = malloc(s->field_cap * sizeof(char *));
    s->field_values = malloc(s->field_cap * sizeof(Value *));
    v->data.struct_val = s; return v;
}
Value *make_list_nil(void) {
    Value *v = malloc(sizeof(Value));
    v->type = VAL_LIST; v->data.cons_val = NULL; return v;
}
Value *make_list_cons(Value *h, Value *t) {
    Value *v = malloc(sizeof(Value));
    v->type = VAL_LIST;
    Cons *c = malloc(sizeof(Cons));
    c->head = h; c->tail = t;
    v->data.cons_val = c; return v;
}
Value *make_closure(char **params, int param_count, int variadic,
                    Expr *body, Env *env, const char *name) {
    Value *v = malloc(sizeof(Value));
    v->type = VAL_CLOSURE;
    Closure *c = calloc(1, sizeof(Closure));
    c->param_count = param_count;
    c->variadic    = variadic;
    c->params = malloc(param_count * sizeof(char *));
    for (int i = 0; i < param_count; i++) c->params[i] = strdup(params[i]);
    c->body = body;
    c->env  = env;
    c->name = name ? strdup(name) : NULL;
    v->data.closure_val = c; return v;
}
Value *make_builtin(const char *name, BuiltinFn fn, int arity) {
    Value *v = malloc(sizeof(Value));
    v->type = VAL_BUILTIN;
    Builtin *b = malloc(sizeof(Builtin));
    b->name = strdup(name); b->fn = fn; b->arity = arity;
    v->data.builtin_val = b; return v;
}

int is_truthy(Value *v) {
    switch (v->type) {
        case VAL_NULL:   return 0;
        case VAL_BOOL:   return v->data.bool_val;
        case VAL_INT:    return v->data.int_val != 0;
        case VAL_STRING: return v->data.str_val[0] != '\0';
        case VAL_LIST:   return v->data.cons_val != NULL;
        default:         return 1;
    }
}

int values_equal(Value *a, Value *b) {
    if (a->type != b->type) return 0;
    switch (a->type) {
        case VAL_INT:    return a->data.int_val  == b->data.int_val;
        case VAL_BOOL:   return a->data.bool_val == b->data.bool_val;
        case VAL_STRING: return strcmp(a->data.str_val, b->data.str_val) == 0;
        case VAL_NULL:   return 1;
        default:         return a == b; /* pointer equality for others */
    }
}

void struct_set(Struct *s, const char *name, Value *val) {
    /* update existing */
    for (int i = 0; i < s->field_count; i++) {
        if (strcmp(s->field_names[i], name) == 0) {
            s->field_values[i] = val; return;
        }
    }
    /* grow if needed */
    if (s->field_count >= s->field_cap) {
        s->field_cap *= 2;
        s->field_names  = realloc(s->field_names,  s->field_cap * sizeof(char *));
        s->field_values = realloc(s->field_values, s->field_cap * sizeof(Value *));
    }
    s->field_names [s->field_count] = strdup(name);
    s->field_values[s->field_count] = val;
    s->field_count++;
}

Value *struct_get(Struct *s, const char *name) {
    for (int i = 0; i < s->field_count; i++)
        if (strcmp(s->field_names[i], name) == 0)
            return s->field_values[i];
    return make_null();
}
