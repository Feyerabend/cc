#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#define DEBUG(msg, ...) printf("[DEBUG] " msg "\n", ##__VA_ARGS__)

typedef enum {
    TYPE_NUMBER,
    TYPE_SYMBOL,
    TYPE_LIST,
    TYPE_FUNCTION
} LispType;

typedef struct LispObject {
    LispType type;
    bool marked;
    union {
        double number;
        char *symbol;
        struct LispList *list;
        struct LispFunction *fn;
    };
} LispObject;

typedef struct LispList {
    LispObject *car;
    struct LispList *cdr;
} LispList;

typedef struct LispFunction {
    bool is_builtin;
    union {
        LispObject *(*builtin)(struct LispList *);
        struct {
            struct LispList *params;
            LispObject *body;
            struct Environment *env;
        };
    };
} LispFunction;

typedef struct Environment {
    struct Environment *parent;
    char *symbol;
    LispObject *value;
    struct Environment *next;
} Environment;

typedef struct {
    LispObject **objects;
    size_t count;
    size_t capacity;
} ObjectPool;

ObjectPool object_pool;

void init_object_pool() {
    object_pool.capacity = 1024;
    object_pool.count = 0;
    object_pool.objects = malloc(object_pool.capacity * sizeof(LispObject *));
    DEBUG("Init object pool with capacity %zu", object_pool.capacity);
}

void free_object_pool() {
    for (size_t i = 0; i < object_pool.count; i++) {
        free(object_pool.objects[i]);
    }
    free(object_pool.objects);
    DEBUG("Freed object pool");
}

LispObject *make_number(double value) {
    LispObject *obj = malloc(sizeof(LispObject));
    obj->type = TYPE_NUMBER;
    obj->marked = false;
    obj->number = value;

    if (object_pool.count >= object_pool.capacity) {
        object_pool.capacity *= 2;
        object_pool.objects = realloc(object_pool.objects, object_pool.capacity * sizeof(LispObject *));
        DEBUG("Expanded object pool capacity to %zu", object_pool.capacity);
    }
    object_pool.objects[object_pool.count++] = obj;

    DEBUG("Created number object: %f", value);
    return obj;
}

LispObject *make_symbol(char *value) {
    LispObject *obj = malloc(sizeof(LispObject));
    obj->type = TYPE_SYMBOL;
    obj->marked = false;
    obj->symbol = strdup(value);

    if (object_pool.count >= object_pool.capacity) {
        object_pool.capacity *= 2;
        object_pool.objects = realloc(object_pool.objects, object_pool.capacity * sizeof(LispObject *));
        DEBUG("Expanded object pool capacity to %zu", object_pool.capacity);
    }
    object_pool.objects[object_pool.count++] = obj;

    DEBUG("Created symbol object: %s", value);
    return obj;
}

LispObject *make_list(LispList *list) {
    LispObject *obj = malloc(sizeof(LispObject));
    obj->type = TYPE_LIST;
    obj->marked = false;
    obj->list = list;

    if (object_pool.count >= object_pool.capacity) {
        object_pool.capacity *= 2;
        object_pool.objects = realloc(object_pool.objects, object_pool.capacity * sizeof(LispObject *));
        DEBUG("Expanded object pool capacity to %zu", object_pool.capacity);
    }
    object_pool.objects[object_pool.count++] = obj;

    DEBUG("Created list object");
    return obj;
}

LispObject *make_function(LispFunction *fn) {
    LispObject *obj = malloc(sizeof(LispObject));
    obj->type = TYPE_FUNCTION;
    obj->marked = false;
    obj->fn = fn;

    if (object_pool.count >= object_pool.capacity) {
        object_pool.capacity *= 2;
        object_pool.objects = realloc(object_pool.objects, object_pool.capacity * sizeof(LispObject *));
        DEBUG("Expanded object pool capacity to %zu", object_pool.capacity);
    }
    object_pool.objects[object_pool.count++] = obj;

    DEBUG("Created function object");
    return obj;
}

LispList *cons(LispObject *car, LispList *cdr) {
    LispList *list = malloc(sizeof(LispList));
    list->car = car;
    list->cdr = cdr;
    DEBUG("Created cons: car=%p, cdr=%p", (void *)car, (void *)cdr);
    return list;
}

void mark(LispObject *obj) {
    if (obj == NULL || obj->marked) return;
    DEBUG("Marking object: %p (type: %d)", (void *)obj, obj->type);
    obj->marked = true;

    switch (obj->type) {
        case TYPE_LIST:
            if (obj->list) {
                mark(obj->list->car);
                mark((LispObject *)obj->list->cdr);
            }
            break;
        case TYPE_FUNCTION:
            if (!obj->fn->is_builtin) {
                mark((LispObject *)obj->fn->params);
                mark(obj->fn->body);
            }
            break;
        default:
            break;
    }
}

void mark_environment(Environment *env) {
    while (env) {
        if (env->value) {
            DEBUG("Marking environment value: %p", (void *)env->value);
            mark(env->value);
        }
        env = env->next;
    }
}

void sweep() {
    size_t i = 0;
    DEBUG("Starting sweep phase");
    while (i < object_pool.count) {
        if (!object_pool.objects[i]->marked) {
            DEBUG("Sweeping object: %p (type: %d)", (void *)object_pool.objects[i], object_pool.objects[i]->type);
            free(object_pool.objects[i]);
            object_pool.objects[i] = object_pool.objects[--object_pool.count];
        } else {
            DEBUG("Object %p is still reachable, unmarking", (void *)object_pool.objects[i]);
            object_pool.objects[i]->marked = false;
            i++;
        }
    }
    DEBUG("Sweep phase completed");
}

void gc(Environment *env) {
    DEBUG("Starting garbage collection");
    mark_environment(env);
    sweep();
    DEBUG("Garbage collection completed");
}

LispObject *env_lookup(Environment *env, char *symbol) {
    while (env != NULL) {
        Environment *frame = env;
        while (frame != NULL) {
            if (frame->symbol != NULL && strcmp(frame->symbol, symbol) == 0) {
                return frame->value;
            }
            frame = frame->next;
        }
        env = env->parent;
    }
    fprintf(stderr, "Unbound symbol: %s\n", symbol);
    exit(1);
}

void env_define(Environment *env, char *symbol, LispObject *value) {
    Environment *frame = malloc(sizeof(Environment));
    frame->parent = NULL;
    frame->symbol = strdup(symbol);
    frame->value = value;
    frame->next = env->next;
    env->next = frame;
    DEBUG("Defined symbol: %s -> %p", symbol, (void *)value);
}

LispObject *eval_tail_recursive(LispObject *expr, Environment *env) {
    while (1) {
        switch (expr->type) {
            case TYPE_NUMBER:
                return expr;
            case TYPE_SYMBOL:
                return env_lookup(env, expr->symbol);
            case TYPE_FUNCTION:
                return expr;
            case TYPE_LIST: {
                LispList *list = expr->list;
                if (!list) return expr;

                LispObject *car = list->car;
                LispList *cdr = list->cdr;

                if (car->type == TYPE_SYMBOL) {
                    if (strcmp(car->symbol, "quote") == 0) {
                        return cdr->car;
                    } else if (strcmp(car->symbol, "define") == 0) {
                        LispObject *name = cdr->car;
                        LispObject *value = eval_tail_recursive(cdr->cdr->car, env);
                        env_define(env, name->symbol, value);
                        return value;
                    } else if (strcmp(car->symbol, "lambda") == 0) {
                        LispFunction *fn = malloc(sizeof(LispFunction));
                        fn->is_builtin = false;
                        fn->params = cdr->car->list;
                        fn->body = cdr->cdr->car;
                        fn->env = env;
                        return make_function(fn);
                    }
                }

                LispObject *fn_obj = eval_tail_recursive(car, env);
                if (!fn_obj || fn_obj->type != TYPE_FUNCTION) {
                    printf("Error: Not a function: %s\n", (car->type == TYPE_SYMBOL) ? car->symbol : "<unknown>");
                    exit(1);
                }

                LispList *args = NULL;
                LispList **tail = &args;
                while (cdr != NULL) {
                    LispObject *arg_val = eval_tail_recursive(cdr->car, env);
                    *tail = cons(arg_val, NULL);
                    tail = &(*tail)->cdr;
                    cdr = cdr->cdr;
                }

                if (!fn_obj->fn->is_builtin) {
                    Environment *new_env = malloc(sizeof(Environment));
                    new_env->parent = fn_obj->fn->env;
                    new_env->symbol = NULL;
                    new_env->value = NULL;
                    new_env->next = NULL;

                    LispList *params = fn_obj->fn->params;
                    LispList *arg_values = args;
                    while (params != NULL && arg_values != NULL) {
                        env_define(new_env, params->car->symbol, arg_values->car);
                        params = params->cdr;
                        arg_values = arg_values->cdr;
                    }

                    expr = fn_obj->fn->body;
                    env = new_env;
                    continue;
                } else {
                    return fn_obj->fn->builtin(args);
                }
            }
            default:
                fprintf(stderr, "Invalid expression type: %d\n", expr->type);
                exit(EXIT_FAILURE);
        }
    }
}

LispObject *eval(LispObject *expr, Environment *env) {
    return eval_tail_recursive(expr, env);
}

LispObject *builtin_add(LispList *args) {
    double result = 0;
    while (args != NULL) {
        result += args->car->number;
        args = args->cdr;
    }
    return make_number(result);
}

LispObject *builtin_sub(LispList *args) {
    double result = args->car->number;
    args = args->cdr;
    while (args != NULL) {
        result -= args->car->number;
        args = args->cdr;
    }
    return make_number(result);
}

LispObject *builtin_mul(LispList *args) {
    double result = 1;
    while (args != NULL) {
        result *= args->car->number;
        args = args->cdr;
    }
    return make_number(result);
}

LispObject *builtin_if(LispList *args) {
    LispObject *cond = args->car;
    LispObject *then_expr = args->cdr->car;
    LispObject *else_expr = args->cdr->cdr->car;
    return (cond->number != 0) ? then_expr : else_expr;
}

LispObject *builtin_eq(LispList *args) {
    LispObject *a = args->car;
    LispObject *b = args->cdr->car;
    return (a->number == b->number) ? make_number(1) : make_number(0);
}

Environment *default_environment() {
    Environment *env = malloc(sizeof(Environment));
    env->parent = NULL;
    env->symbol = NULL;
    env->value = NULL;
    env->next = NULL;

    LispFunction *add_fn = malloc(sizeof(LispFunction));
    add_fn->is_builtin = true;
    add_fn->builtin = builtin_add;
    env_define(env, "+", make_function(add_fn));

    LispFunction *sub_fn = malloc(sizeof(LispFunction));
    sub_fn->is_builtin = true;
    sub_fn->builtin = builtin_sub;
    env_define(env, "-", make_function(sub_fn));

    LispFunction *mul_fn = malloc(sizeof(LispFunction));
    mul_fn->is_builtin = true;
    mul_fn->builtin = builtin_mul;
    env_define(env, "*", make_function(mul_fn));

    LispFunction *if_fn = malloc(sizeof(LispFunction));
    if_fn->is_builtin = true;
    if_fn->builtin = builtin_if;
    env_define(env, "if", make_function(if_fn));

    LispFunction *eq_fn = malloc(sizeof(LispFunction));
    eq_fn->is_builtin = true;
    eq_fn->builtin = builtin_eq;
    env_define(env, "eq?", make_function(eq_fn));

    return env;
}

LispList *make_list_from_array(LispObject **objects, int count) {
    LispList *list = NULL;
    for (int i = count - 1; i >= 0; i--) {
        list = cons(objects[i], list);
    }
    return list;
}

void run_tests() {
    Environment *env = default_environment();

    LispObject *num = make_number(42);
    LispObject *result = eval(num, env);
    printf("Test 1: %f (expected: 42.0)\n", result->number);

    LispObject *symbol = make_symbol("x");
    env_define(env, "x", make_number(10));
    result = eval(symbol, env);
    printf("Test 2: %f (expected: 10.0)\n", result->number);

    LispObject *one = make_number(1);
    LispObject *two = make_number(2);
    LispObject *three = make_number(3);
    LispObject *plus = make_symbol("+");
    LispObject *args[] = {plus, one, two, three};
    LispList *expr = make_list_from_array(args, 4);
    result = eval(make_list(expr), env);
    printf("Test 3: %f (expected: 6.0)\n", result->number);

    gc(env);
}

int main() {
    init_object_pool();
    run_tests();
    free_object_pool();
    return 0;
}