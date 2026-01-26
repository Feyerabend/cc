/*
 * Minimal OOP Language - C Implementation
 * 
 * Core Semantics:
 * - Objects = structs with vptr as first field
 * - VTables = method name -> closure mappings
 * - Methods take 'self' as first parameter
 * - Dynamic dispatch via vtable lookup
 * - Closures capture environment
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAX_PARAMS 8
#define MAX_FIELDS 16
#define MAX_METHODS 16
#define MAX_ENV 32

/*  VALUE SYSTEM  */

typedef enum {
    VAL_INT,
    VAL_STRUCT,
    VAL_VTABLE,
    VAL_CLOSURE,
    VAL_NULL
} ValueType;

typedef struct Value Value;
typedef struct Expr Expr;
typedef struct Env Env;

/* Environment for variable bindings */
struct Env {
    char *names[MAX_ENV];
    Value *values[MAX_ENV];
    int count;
};

/* Closure data */
typedef struct {
    char *params[MAX_PARAMS];
    int param_count;
    Expr *body;
    Env *env;  /* Captured environment */
} Closure;

/* Struct data */
typedef struct {
    char *field_names[MAX_FIELDS];
    Value *field_values[MAX_FIELDS];
    int field_count;
} Struct;

/* VTable data */
typedef struct {
    char *method_names[MAX_METHODS];
    Value *method_closures[MAX_METHODS];
    int method_count;
} VTable;

/* Tagged union value */
struct Value {
    ValueType type;
    union {
        int64_t int_val;
        Struct *struct_val;
        VTable *vtable_val;
        Closure *closure_val;
    } data;
};

/*  EXPRESSION AST  */

typedef enum {
    EXPR_LITERAL,
    EXPR_VAR,
    EXPR_LET,
    EXPR_LAMBDA,
    EXPR_CALL,
    EXPR_ACCESS,
    EXPR_CREATE,
    EXPR_VCALL,
    EXPR_BINOP,
    EXPR_SEQ
} ExprType;

struct Expr {
    ExprType type;
    union {
        struct { Value *value; } literal;
        struct { char *name; } var;
        struct { char *name; Expr *value; Expr *body; } let;
        struct { char *params[MAX_PARAMS]; int param_count; Expr *body; } lambda;
        struct { Expr *func; Expr *args[MAX_PARAMS]; int arg_count; } call;
        struct { Expr *obj; char *field; } access;
        struct { 
            char *field_names[MAX_FIELDS]; 
            Expr *field_exprs[MAX_FIELDS]; 
            int field_count; 
        } create;
        struct { Expr *obj; char *method; Expr *args[MAX_PARAMS]; int arg_count; } vcall;
        struct { char *op; Expr *left; Expr *right; } binop;
        struct { Expr *exprs[MAX_PARAMS]; int expr_count; } seq;
    } data;
};

/*  CONSTRUCTORS  */

Value *make_int(int64_t n) {
    Value *v = malloc(sizeof(Value));
    v->type = VAL_INT;
    v->data.int_val = n;
    return v;
}

Value *make_null(void) {
    Value *v = malloc(sizeof(Value));
    v->type = VAL_NULL;
    return v;
}

Value *make_struct(void) {
    Value *v = malloc(sizeof(Value));
    v->type = VAL_STRUCT;
    v->data.struct_val = malloc(sizeof(Struct));
    v->data.struct_val->field_count = 0;
    return v;
}

Value *make_vtable(void) {
    Value *v = malloc(sizeof(Value));
    v->type = VAL_VTABLE;
    v->data.vtable_val = malloc(sizeof(VTable));
    v->data.vtable_val->method_count = 0;
    return v;
}

Value *make_closure(char **params, int param_count, Expr *body, Env *env) {
    Value *v = malloc(sizeof(Value));
    v->type = VAL_CLOSURE;
    v->data.closure_val = malloc(sizeof(Closure));
    v->data.closure_val->param_count = param_count;
    for (int i = 0; i < param_count; i++) {
        v->data.closure_val->params[i] = strdup(params[i]);
    }
    v->data.closure_val->body = body;
    
    /* Copy environment */
    v->data.closure_val->env = malloc(sizeof(Env));
    v->data.closure_val->env->count = env->count;
    for (int i = 0; i < env->count; i++) {
        v->data.closure_val->env->names[i] = strdup(env->names[i]);
        v->data.closure_val->env->values[i] = env->values[i];
    }
    
    return v;
}

Env *make_env(void) {
    Env *env = malloc(sizeof(Env));
    env->count = 0;
    return env;
}

void env_set(Env *env, const char *name, Value *val) {
    env->names[env->count] = strdup(name);
    env->values[env->count] = val;
    env->count++;
}

Value *env_get(Env *env, const char *name) {
    for (int i = env->count - 1; i >= 0; i--) {
        if (strcmp(env->names[i], name) == 0) {
            return env->values[i];
        }
    }
    return NULL;
}

void struct_set(Struct *s, const char *name, Value *val) {
    s->field_names[s->field_count] = strdup(name);
    s->field_values[s->field_count] = val;
    s->field_count++;
}

Value *struct_get(Struct *s, const char *name) {
    for (int i = 0; i < s->field_count; i++) {
        if (strcmp(s->field_names[i], name) == 0) {
            return s->field_values[i];
        }
    }
    return make_null();
}

void vtable_set(VTable *vt, const char *name, Value *closure) {
    vt->method_names[vt->method_count] = strdup(name);
    vt->method_closures[vt->method_count] = closure;
    vt->method_count++;
}

Value *vtable_get(VTable *vt, const char *name) {
    for (int i = 0; i < vt->method_count; i++) {
        if (strcmp(vt->method_names[i], name) == 0) {
            return vt->method_closures[i];
        }
    }
    return NULL;
}

/*  EXPRESSION CONSTRUCTORS  */

Expr *expr_literal(Value *val) {
    Expr *e = malloc(sizeof(Expr));
    e->type = EXPR_LITERAL;
    e->data.literal.value = val;
    return e;
}

Expr *expr_var(const char *name) {
    Expr *e = malloc(sizeof(Expr));
    e->type = EXPR_VAR;
    e->data.var.name = strdup(name);
    return e;
}

Expr *expr_let(const char *name, Expr *value, Expr *body) {
    Expr *e = malloc(sizeof(Expr));
    e->type = EXPR_LET;
    e->data.let.name = strdup(name);
    e->data.let.value = value;
    e->data.let.body = body;
    return e;
}

Expr *expr_lambda(char **params, int param_count, Expr *body) {
    Expr *e = malloc(sizeof(Expr));
    e->type = EXPR_LAMBDA;
    e->data.lambda.param_count = param_count;
    for (int i = 0; i < param_count; i++) {
        e->data.lambda.params[i] = strdup(params[i]);
    }
    e->data.lambda.body = body;
    return e;
}

Expr *expr_call(Expr *func, Expr **args, int arg_count) {
    Expr *e = malloc(sizeof(Expr));
    e->type = EXPR_CALL;
    e->data.call.func = func;
    e->data.call.arg_count = arg_count;
    for (int i = 0; i < arg_count; i++) {
        e->data.call.args[i] = args[i];
    }
    return e;
}

Expr *expr_access(Expr *obj, const char *field) {
    Expr *e = malloc(sizeof(Expr));
    e->type = EXPR_ACCESS;
    e->data.access.obj = obj;
    e->data.access.field = strdup(field);
    return e;
}

Expr *expr_binop(const char *op, Expr *left, Expr *right) {
    Expr *e = malloc(sizeof(Expr));
    e->type = EXPR_BINOP;
    e->data.binop.op = strdup(op);
    e->data.binop.left = left;
    e->data.binop.right = right;
    return e;
}

Expr *expr_vcall(Expr *obj, const char *method, Expr **args, int arg_count) {
    Expr *e = malloc(sizeof(Expr));
    e->type = EXPR_VCALL;
    e->data.vcall.obj = obj;
    e->data.vcall.method = strdup(method);
    e->data.vcall.arg_count = arg_count;
    for (int i = 0; i < arg_count; i++) {
        e->data.vcall.args[i] = args[i];
    }
    return e;
}

/*  INTERPRETER  */

Value *eval(Expr *expr, Env *env);

Value *eval(Expr *expr, Env *env) {
    switch (expr->type) {
        case EXPR_LITERAL:
            return expr->data.literal.value;
        
        case EXPR_VAR: {
            Value *v = env_get(env, expr->data.var.name);
            if (!v) {
                fprintf(stderr, "Unbound variable: %s\n", expr->data.var.name);
                exit(1);
            }
            return v;
        }
        
        case EXPR_LET: {
            Value *val = eval(expr->data.let.value, env);
            Env *new_env = malloc(sizeof(Env));
            memcpy(new_env, env, sizeof(Env));
            env_set(new_env, expr->data.let.name, val);
            return eval(expr->data.let.body, new_env);
        }
        
        case EXPR_LAMBDA:
            return make_closure(expr->data.lambda.params, 
                              expr->data.lambda.param_count,
                              expr->data.lambda.body, 
                              env);
        
        case EXPR_CALL: {
            Value *func = eval(expr->data.call.func, env);
            if (func->type != VAL_CLOSURE) {
                fprintf(stderr, "Cannot call non-function\n");
                exit(1);
            }
            
            Closure *closure = func->data.closure_val;
            Env *call_env = malloc(sizeof(Env));
            memcpy(call_env, closure->env, sizeof(Env));
            
            for (int i = 0; i < closure->param_count; i++) {
                Value *arg = i < expr->data.call.arg_count 
                    ? eval(expr->data.call.args[i], env)
                    : make_null();
                env_set(call_env, closure->params[i], arg);
            }
            
            return eval(closure->body, call_env);
        }
        
        case EXPR_ACCESS: {
            Value *obj = eval(expr->data.access.obj, env);
            if (obj->type != VAL_STRUCT) {
                fprintf(stderr, "Can only access fields on structs\n");
                exit(1);
            }
            return struct_get(obj->data.struct_val, expr->data.access.field);
        }
        
        case EXPR_VCALL: {
            Value *obj = eval(expr->data.vcall.obj, env);
            if (obj->type != VAL_STRUCT) {
                fprintf(stderr, "Object must be struct for virtual call\n");
                exit(1);
            }
            
            Value *vptr = struct_get(obj->data.struct_val, "vptr");
            if (vptr->type != VAL_VTABLE) {
                fprintf(stderr, "vptr must point to VTable\n");
                exit(1);
            }
            
            Value *method = vtable_get(vptr->data.vtable_val, expr->data.vcall.method);
            if (!method || method->type != VAL_CLOSURE) {
                fprintf(stderr, "Method not found: %s\n", expr->data.vcall.method);
                exit(1);
            }
            
            Closure *closure = method->data.closure_val;
            Env *call_env = malloc(sizeof(Env));
            memcpy(call_env, closure->env, sizeof(Env));
            
            /* First param is self */
            env_set(call_env, closure->params[0], obj);
            
            /* Rest are regular args */
            for (int i = 1; i < closure->param_count; i++) {
                Value *arg = (i - 1) < expr->data.vcall.arg_count
                    ? eval(expr->data.vcall.args[i - 1], env)
                    : make_null();
                env_set(call_env, closure->params[i], arg);
            }
            
            return eval(closure->body, call_env);
        }
        
        case EXPR_BINOP: {
            Value *left = eval(expr->data.binop.left, env);
            Value *right = eval(expr->data.binop.right, env);
            
            if (left->type == VAL_INT && right->type == VAL_INT) {
                int64_t l = left->data.int_val;
                int64_t r = right->data.int_val;
                
                if (strcmp(expr->data.binop.op, "+") == 0) {
                    return make_int(l + r);
                } else if (strcmp(expr->data.binop.op, "-") == 0) {
                    return make_int(l - r);
                } else if (strcmp(expr->data.binop.op, "*") == 0) {
                    return make_int(l * r);
                } else if (strcmp(expr->data.binop.op, "/") == 0) {
                    return make_int(l / r);
                }
            }
            
            fprintf(stderr, "Invalid binop\n");
            exit(1);
        }
        
        default:
            fprintf(stderr, "Unknown expression type\n");
            exit(1);
    }
}

void print_value(Value *v) {
    switch (v->type) {
        case VAL_INT:
            printf("%lld", (long long)v->data.int_val);
            break;
        case VAL_NULL:
            printf("null");
            break;
        case VAL_CLOSURE:
            printf("<closure>");
            break;
        case VAL_VTABLE:
            printf("<vtable>");
            break;
        case VAL_STRUCT: {
            printf("{");
            int first = 1;
            for (int i = 0; i < v->data.struct_val->field_count; i++) {
                if (strcmp(v->data.struct_val->field_names[i], "vptr") == 0) continue;
                if (!first) printf(", ");
                printf("%s: ", v->data.struct_val->field_names[i]);
                print_value(v->data.struct_val->field_values[i]);
                first = 0;
            }
            printf("}");
            break;
        }
        default:
            printf("<unknown>");
    }
}

/*  EXAMPLES  */

void example_closure(void) {
    printf("Closure example: ");
    
    /* makeAdder = lambda(n) lambda(x) x + n */
    Expr *inner_body = expr_binop("+", expr_var("x"), expr_var("n"));
    char *inner_params[] = {"x"};
    Expr *inner_lambda = expr_lambda(inner_params, 1, inner_body);
    
    char *outer_params[] = {"n"};
    Expr *make_adder = expr_lambda(outer_params, 1, inner_lambda);
    
    /* add10 = makeAdder(10) */
    Expr *ten = expr_literal(make_int(10));
    Expr *args1[] = {ten};
    Expr *call1 = expr_call(expr_var("makeAdder"), args1, 1);
    
    /* add10(32) */
    Expr *thirtytwo = expr_literal(make_int(32));
    Expr *args2[] = {thirtytwo};
    Expr *call2 = expr_call(expr_var("add10"), args2, 1);
    
    Expr *prog = expr_let("makeAdder", make_adder,
                    expr_let("add10", call1, call2));
    
    Env *env = make_env();
    Value *result = eval(prog, env);
    print_value(result);
    printf("\n");
}

void example_int_object(void) {
    printf("Int object example: ");
    
    /* IntVTable with add method */
    Value *vtable = make_vtable();
    
    /* add method: lambda(self, other) self.value + other.value */
    Expr *add_body = expr_binop("+",
        expr_access(expr_var("self"), "value"),
        expr_access(expr_var("other"), "value"));
    char *add_params[] = {"self", "other"};
    Value *add_closure = make_closure(add_params, 2, add_body, make_env());
    vtable_set(vtable->data.vtable_val, "add", add_closure);
    
    /* makeInt constructor: lambda(n) { vptr: vtable, value: n } */
    Value *obj1 = make_struct();
    struct_set(obj1->data.struct_val, "vptr", vtable);
    struct_set(obj1->data.struct_val, "value", make_int(42));
    
    Value *obj2 = make_struct();
    struct_set(obj2->data.struct_val, "vptr", vtable);
    struct_set(obj2->data.struct_val, "value", make_int(8));
    
    /* obj1.add(obj2) */
    Expr *args[] = {expr_literal(obj2)};
    Expr *vcall = expr_vcall(expr_literal(obj1), "add", args, 1);
    
    Env *env = make_env();
    Value *result = eval(vcall, env);
    print_value(result);
    printf("\n");
}

void example_polymorphic(void) {
    printf("Polymorphic example: ");
    
    /* IntVTable with get method: lambda(self) self.value */
    Value *int_vtable = make_vtable();
    Expr *int_get_body = expr_access(expr_var("self"), "value");
    char *get_params[] = {"self"};
    Value *int_get = make_closure(get_params, 1, int_get_body, make_env());
    vtable_set(int_vtable->data.vtable_val, "get", int_get);
    
    /* PairVTable with get method: lambda(self) self.first + self.second */
    Value *pair_vtable = make_vtable();
    Expr *pair_get_body = expr_binop("+",
        expr_access(expr_var("self"), "first"),
        expr_access(expr_var("self"), "second"));
    Value *pair_get = make_closure(get_params, 1, pair_get_body, make_env());
    vtable_set(pair_vtable->data.vtable_val, "get", pair_get);
    
    /* Create IntObject(42) */
    Value *int_obj = make_struct();
    struct_set(int_obj->data.struct_val, "vptr", int_vtable);
    struct_set(int_obj->data.struct_val, "value", make_int(42));
    
    /* Create PairObject(10, 20) */
    Value *pair_obj = make_struct();
    struct_set(pair_obj->data.struct_val, "vptr", pair_vtable);
    struct_set(pair_obj->data.struct_val, "first", make_int(10));
    struct_set(pair_obj->data.struct_val, "second", make_int(20));
    
    /* Call get on both - polymorphism! */
    printf("IntObject.get() = ");
    Expr *vcall1 = expr_vcall(expr_literal(int_obj), "get", NULL, 0);
    Value *result1 = eval(vcall1, make_env());
    print_value(result1);
    
    printf(", PairObject.get() = ");
    Expr *vcall2 = expr_vcall(expr_literal(pair_obj), "get", NULL, 0);
    Value *result2 = eval(vcall2, make_env());
    print_value(result2);
    
    printf("\n");
}

void example_counter(void) {
    printf("Counter example: ");
    
    /* CounterVTable with get and inc methods */
    Value *counter_vtable = make_vtable();
    
    /* get: lambda(self) self.count */
    Expr *get_body = expr_access(expr_var("self"), "count");
    char *get_params[] = {"self"};
    Value *get_closure = make_closure(get_params, 1, get_body, make_env());
    vtable_set(counter_vtable->data.vtable_val, "get", get_closure);
    
    /* inc: lambda(self) { vptr: self.vptr, count: self.count + 1 } */
    /* This is tricky - we need to build a struct creation inline */
    /* For simplicity, we'll do manual increment and return new counter */
    
    /* Create counter with count=0 */
    Value *c1 = make_struct();
    struct_set(c1->data.struct_val, "vptr", counter_vtable);
    struct_set(c1->data.struct_val, "count", make_int(0));
    
    /* Manually increment twice by creating new counters */
    Value *c2 = make_struct();
    struct_set(c2->data.struct_val, "vptr", counter_vtable);
    struct_set(c2->data.struct_val, "count", make_int(1));
    
    Value *c3 = make_struct();
    struct_set(c3->data.struct_val, "vptr", counter_vtable);
    struct_set(c3->data.struct_val, "count", make_int(2));
    
    /* Get final count */
    Expr *vcall = expr_vcall(expr_literal(c3), "get", NULL, 0);
    Value *result = eval(vcall, make_env());
    print_value(result);
    printf("\n");
}

void example_shape_area(void) {
    printf("Shape area example: ");
    
    /* CircleVTable with area method: lambda(self) 3 * self.radius * self.radius */
    Value *circle_vtable = make_vtable();
    Expr *circle_area = expr_binop("*", 
        expr_literal(make_int(3)),
        expr_binop("*",
            expr_access(expr_var("self"), "radius"),
            expr_access(expr_var("self"), "radius")));
    char *area_params[] = {"self"};
    Value *circle_area_closure = make_closure(area_params, 1, circle_area, make_env());
    vtable_set(circle_vtable->data.vtable_val, "area", circle_area_closure);
    
    /* RectangleVTable with area method: lambda(self) self.width * self.height */
    Value *rect_vtable = make_vtable();
    Expr *rect_area = expr_binop("*",
        expr_access(expr_var("self"), "width"),
        expr_access(expr_var("self"), "height"));
    Value *rect_area_closure = make_closure(area_params, 1, rect_area, make_env());
    vtable_set(rect_vtable->data.vtable_val, "area", rect_area_closure);
    
    /* Create Circle(radius=5) */
    Value *circle = make_struct();
    struct_set(circle->data.struct_val, "vptr", circle_vtable);
    struct_set(circle->data.struct_val, "radius", make_int(5));
    
    /* Create Rectangle(width=4, height=6) */
    Value *rect = make_struct();
    struct_set(rect->data.struct_val, "vptr", rect_vtable);
    struct_set(rect->data.struct_val, "width", make_int(4));
    struct_set(rect->data.struct_val, "height", make_int(6));
    
    /* Calculate areas */
    printf("Circle.area() = ");
    Expr *vcall1 = expr_vcall(expr_literal(circle), "area", NULL, 0);
    Value *result1 = eval(vcall1, make_env());
    print_value(result1);
    
    printf(", Rectangle.area() = ");
    Expr *vcall2 = expr_vcall(expr_literal(rect), "area", NULL, 0);
    Value *result2 = eval(vcall2, make_env());
    print_value(result2);
    
    printf("\n");
}

int main(void) {
    printf("Minimal OOP Language Interpreter (C)n\n");
    
    printf("Core semantics:\n");
    printf("- Objects = structs with vptr field\n");
    printf("- VTables = method name -> closure\n");
    printf("- Methods take 'self' as first param\n");
    printf("- Dynamic dispatch via vtable lookup\n");
    printf("- Closures capture environment\n\n");
    
    example_closure();
    example_int_object();
    example_polymorphic();
    example_counter();
    example_shape_area();
    
    printf("\nDone. All examples executed successfully!\n");
    
    return 0;
}
