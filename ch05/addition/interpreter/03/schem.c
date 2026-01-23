#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

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
}

void free_object_pool() {
    for (size_t i = 0; i < object_pool.count; i++) {
        free(object_pool.objects[i]);
    }
    free(object_pool.objects);
}

LispObject *make_number(double value) {
    LispObject *obj = malloc(sizeof(LispObject));
    obj->type = TYPE_NUMBER;
    obj->marked = false;
    obj->number = value;
    if (object_pool.count >= object_pool.capacity) {
        object_pool.capacity *= 2;
        object_pool.objects = realloc(object_pool.objects, object_pool.capacity * sizeof(LispObject *));
    }
    object_pool.objects[object_pool.count++] = obj;
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
    }
    object_pool.objects[object_pool.count++] = obj;
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
    }
    object_pool.objects[object_pool.count++] = obj;
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
    }
    object_pool.objects[object_pool.count++] = obj;
    return obj;
}

LispList *cons(LispObject *car, LispList *cdr) {
    LispList *list = malloc(sizeof(LispList));
    list->car = car;
    list->cdr = cdr;
    return list;
}

void mark(LispObject *obj) {
    if (obj == NULL || obj->marked) return;
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
            mark(env->value);
        }
        env = env->next;
    }
}

void sweep() {
    size_t i = 0;
    while (i < object_pool.count) {
        if (!object_pool.objects[i]->marked) {
            free(object_pool.objects[i]);
            object_pool.objects[i] = object_pool.objects[--object_pool.count];
        } else {
            object_pool.objects[i]->marked = false;
            i++;
        }
    }
}

void gc(Environment *env) {
    mark_environment(env);
    sweep();
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
}

LispObject *eval(LispObject *expr, Environment *env);

LispObject *eval_tail_recursive(LispObject *expr, Environment *env, bool is_top_level) {
    while (1) {
        switch (expr->type) {
            case TYPE_NUMBER:
            case TYPE_SYMBOL:
                return expr->type == TYPE_SYMBOL ? env_lookup(env, expr->symbol) : expr;
            case TYPE_FUNCTION:
                return expr;
            case TYPE_LIST: {
                if (!is_top_level) return expr;
                LispList *list = expr->list;
                if (!list) return expr;
                LispObject *car = list->car;
                LispList *cdr = list->cdr;
                if (car->type == TYPE_SYMBOL) {
                    if (strcmp(car->symbol, "quote") == 0) {
                        return cdr->car;
                    } else if (strcmp(car->symbol, "define") == 0) {
                        LispObject *name = cdr->car;
                        LispObject *value = eval_tail_recursive(cdr->cdr->car, env, true);
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
                LispObject *fn_obj = eval_tail_recursive(car, env, true);
                if (fn_obj->type != TYPE_FUNCTION) {
                    fprintf(stderr, "Error: Not a function: %s\n", car->type == TYPE_SYMBOL ? car->symbol : "<unknown>");
                    exit(1);
                }
                LispList *args = NULL;
                LispList **tail = &args;
                LispList *current_arg = cdr;
                while (current_arg != NULL) {
                    LispObject *arg_val = eval_tail_recursive(current_arg->car, env, false);
                    *tail = cons(arg_val, NULL);
                    tail = &(*tail)->cdr;
                    current_arg = current_arg->cdr;
                }
                if (!fn_obj->fn->is_builtin) {
                    Environment *new_env = malloc(sizeof(Environment));
                    new_env->parent = fn_obj->fn->env;
                    new_env->symbol = NULL;
                    new_env->value = NULL;
                    new_env->next = NULL;
                    LispList *params = fn_obj->fn->params;
                    LispList *arg_values = args;
                    while (params && arg_values) {
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
    return eval_tail_recursive(expr, env, true);
}

LispObject *builtin_map(LispList *args) {
    if (!args || !args->cdr || args->cdr->cdr) {
        fprintf(stderr, "Error: map requires exactly two arguments\n");
        exit(EXIT_FAILURE);
    }
    LispObject *fn_obj = args->car;
    LispObject *list_obj = args->cdr->car;
    if (fn_obj->type != TYPE_FUNCTION) {
        fprintf(stderr, "Error: First argument to map must be a function\n");
        exit(EXIT_FAILURE);
    }
    if (list_obj->type != TYPE_LIST) {
        fprintf(stderr, "Error: Second argument to map must be a list\n");
        exit(EXIT_FAILURE);
    }
    if (!list_obj->list) return make_list(NULL);
    LispList *current = list_obj->list;
    LispList *result = NULL;
    LispList **result_tail = &result;
    while (current) {
        LispList *fn_args = cons(current->car, NULL);
        LispObject *mapped_value;
        if (fn_obj->fn->is_builtin) {
            mapped_value = fn_obj->fn->builtin(fn_args);
        } else {
            Environment *new_env = malloc(sizeof(Environment));
            new_env->parent = fn_obj->fn->env;
            new_env->next = NULL;
            LispList *params = fn_obj->fn->params;
            if (params) {
                env_define(new_env, params->car->symbol, current->car);
            }
            mapped_value = eval(fn_obj->fn->body, new_env);
        }
        *result_tail = cons(mapped_value, NULL);
        result_tail = &(*result_tail)->cdr;
        current = current->cdr;
    }
    return make_list(result);
}

LispObject *builtin_reduce(LispList *args) {
    if (!args || !args->cdr || !args->cdr->cdr) {
        fprintf(stderr, "Error: reduce requires three arguments\n");
        exit(EXIT_FAILURE);
    }
    LispObject *fn_obj = args->car;
    LispObject *initial = args->cdr->car;
    LispObject *list_obj = args->cdr->cdr->car;
    if (fn_obj->type != TYPE_FUNCTION) {
        fprintf(stderr, "Error: First argument to reduce must be a function\n");
        exit(EXIT_FAILURE);
    }
    if (list_obj->type != TYPE_LIST) {
        fprintf(stderr, "Error: Third argument to reduce must be a list\n");
        exit(EXIT_FAILURE);
    }
    LispObject *accumulator = initial;
    LispList *current = list_obj->list;
    while (current) {
        LispList *fn_args = cons(accumulator, cons(current->car, NULL));
        if (fn_obj->fn->is_builtin) {
            accumulator = fn_obj->fn->builtin(fn_args);
        } else {
            Environment *new_env = malloc(sizeof(Environment));
            new_env->parent = fn_obj->fn->env;
            new_env->next = NULL;
            LispList *params = fn_obj->fn->params;
            if (params && params->cdr) {
                env_define(new_env, params->car->symbol, accumulator);
                env_define(new_env, params->cdr->car->symbol, current->car);
            }
            accumulator = eval(fn_obj->fn->body, new_env);
        }
        current = current->cdr;
    }
    return accumulator;
}

LispObject *builtin_add(LispList *args) {
    double result = 0;
    while (args) {
        if (args->car->type != TYPE_NUMBER) {
            fprintf(stderr, "Error: + requires number arguments\n");
            exit(EXIT_FAILURE);
        }
        result += args->car->number;
        args = args->cdr;
    }
    return make_number(result);
}

LispObject *builtin_sub(LispList *args) {
    if (!args) {
        fprintf(stderr, "Error: - requires at least one argument\n");
        exit(EXIT_FAILURE);
    }
    double result = args->car->number;
    args = args->cdr;
    if (!args) return make_number(-result);
    while (args) {
        if (args->car->type != TYPE_NUMBER) {
            fprintf(stderr, "Error: - requires number arguments\n");
            exit(EXIT_FAILURE);
        }
        result -= args->car->number;
        args = args->cdr;
    }
    return make_number(result);
}

LispObject *builtin_mul(LispList *args) {
    double result = 1;
    while (args) {
        if (args->car->type != TYPE_NUMBER) {
            fprintf(stderr, "Error: * requires number arguments\n");
            exit(EXIT_FAILURE);
        }
        result *= args->car->number;
        args = args->cdr;
    }
    return make_number(result);
}

LispObject *builtin_if(LispList *args) {
    if (!args || !args->cdr || !args->cdr->cdr) {
        fprintf(stderr, "Error: if requires three arguments\n");
        exit(EXIT_FAILURE);
    }
    LispObject *cond = args->car;
    if (cond->type != TYPE_NUMBER) {
        fprintf(stderr, "Error: if condition must be a number\n");
        exit(EXIT_FAILURE);
    }
    return cond->number != 0 ? args->cdr->car : args->cdr->cdr->car;
}

LispObject *builtin_eq(LispList *args) {
    if (!args || !args->cdr) {
        fprintf(stderr, "Error: eq? requires two arguments\n");
        exit(EXIT_FAILURE);
    }
    LispObject *a = args->car;
    LispObject *b = args->cdr->car;
    if (a->type != TYPE_NUMBER || b->type != TYPE_NUMBER) {
        fprintf(stderr, "Error: eq? requires number arguments\n");
        exit(EXIT_FAILURE);
    }
    return a->number == b->number ? make_number(1) : make_number(0);
}

LispObject *builtin_list(LispList *args) {
    return make_list(args);
}

LispList *make_list_from_array(LispObject **objects, int count) {
    LispList *list = NULL;
    for (int i = count - 1; i >= 0; i--) {
        list = cons(objects[i], list);
    }
    return list;
}

void print_object(LispObject *obj) {
    if (!obj) {
        printf("nil");
        return;
    }
    switch (obj->type) {
        case TYPE_NUMBER:
            printf("%g", obj->number);
            break;
        case TYPE_SYMBOL:
            printf("%s", obj->symbol);
            break;
        case TYPE_FUNCTION:
            printf("<function>");
            break;
        case TYPE_LIST: {
            printf("(");
            LispList *list = obj->list;
            while (list) {
                print_object(list->car);
                list = list->cdr;
                if (list) printf(" ");
            }
            printf(")");
            break;
        }
    }
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
    LispFunction *map_fn = malloc(sizeof(LispFunction));
    map_fn->is_builtin = true;
    map_fn->builtin = builtin_map;
    env_define(env, "map", make_function(map_fn));
    LispFunction *reduce_fn = malloc(sizeof(LispFunction));
    reduce_fn->is_builtin = true;
    reduce_fn->builtin = builtin_reduce;
    env_define(env, "reduce", make_function(reduce_fn));
    LispFunction *list_fn = malloc(sizeof(LispFunction));
    list_fn->is_builtin = true;
    list_fn->builtin = builtin_list;
    env_define(env, "list", make_function(list_fn));
    return env;
}

void run_tests() {
    Environment *env = default_environment();
    LispObject *num = make_number(42);
    LispObject *result = eval(num, env);
    printf("Test 1: %f\n", result->number);
    LispObject *symbol = make_symbol("x");
    env_define(env, "x", make_number(10));
    result = eval(symbol, env);
    printf("Test 2: %f\n", result->number);
    LispObject *one = make_number(1);
    LispObject *two = make_number(2);
    LispObject *three = make_number(3);
    LispObject *plus = make_symbol("+");
    LispObject *args[] = {plus, one, two, three};
    LispList *expr = make_list_from_array(args, 4);
    result = eval(make_list(expr), env);
    printf("Test 3: %f\n", result->number);
    LispObject *list_sym = make_symbol("list");
    LispObject *list_args[] = {list_sym, one, two, three};
    LispList *list_expr = make_list_from_array(list_args, 4);
    LispObject *test_list = eval(make_list(list_expr), env);
    printf("List object: ");
    print_object(test_list);
    printf("\n");
    LispObject *lambda = make_symbol("lambda");
    LispObject *x_param = make_symbol("x");
    LispObject *times = make_symbol("*");
    LispList *params = cons(x_param, NULL);
    LispObject *body_args[] = {times, x_param, x_param};
    LispList *body_expr = make_list_from_array(body_args, 3);
    LispObject *lambda_args[] = {lambda, make_list(params), make_list(body_expr)};
    LispList *lambda_expr = make_list_from_array(lambda_args, 3);
    LispObject *square_fn = eval(make_list(lambda_expr), env);
    printf("Created lambda function\n");
    LispObject *map = make_symbol("map");
    LispObject *map_args[] = {map, square_fn, test_list};
    LispList *map_expr = make_list_from_array(map_args, 3);
    printf("Map expression: ");
    print_object(make_list(map_expr));
    printf("\n");
    LispObject *map_result = eval(make_list(map_expr), env);
    printf("Result: ");
    print_object(map_result);
    printf("\n");
    gc(env);
}

int main() {
    init_object_pool();
    run_tests();
    free_object_pool();
    return 0;
}