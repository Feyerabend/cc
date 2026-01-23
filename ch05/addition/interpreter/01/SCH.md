
## A Minimal Scheme: Sch

The code 'sch.c' implements a minimalist Scheme-like interpreter in C, capturing
the core features of Lisp: symbolic expressions (S-expressions), lists, function
application, and an environment for variable bindings. Historically, Lisp (developed
by John McCarthy in the late 1950s) is built around the concept of symbolic computing,
using linked list structures (pairs/cons cells) to represent both data and code.
This implementation reflects the essence of Scheme, a dialect of Lisp known for its
simplicity and lexical scoping.


### Building from Pairs to Larger Expressions

At the core of this interpreter is the pair (cons cell), represented here as LispList:

```c
typedef struct LispList {
    LispObject *car;
    struct LispList *cdr;
} LispList;
```

This forms the foundation of lists. A list is recursively defined: it consists of a
first element (car) and a rest (cdr). The cons function constructs lists:

```c
LispList *cons(LispObject *car, LispList *cdr) {
    LispList *list = malloc(sizeof(LispList));
    list->car = car;
    list->cdr = cdr;
    return list;
}
```

Building up from this, larger structures like quoted lists, function calls, and even
entire programs are represented as nested lists.


### The Environment: Managing Variable Bindings

The environment allows for variable storage and lookup:

```c
typedef struct Environment {
    struct Environment *parent;
    char *symbol;
    LispObject *value;
    struct Environment *next;
} Environment;
```

It supports lexical scoping: each function has its own environment linked to a parent,
allowing local variables while maintaining global definitions.


### Evaluation and Function Application

The eval function is central, determining how each expression is interpreted:

```c
LispObject *eval(LispObject *expr, Environment *env) {
    switch (expr->type) {
        case TYPE_NUMBER:
            return expr;
        case TYPE_SYMBOL:
            return env_lookup(env, expr->symbol);
        case TYPE_FUNCTION:
            return expr;
        case TYPE_LIST: {
            LispList *list = expr->list;
            if (list == NULL) return expr;
            LispObject *car = list->car;
            LispList *cdr = list->cdr;
..
```
- Numbers evaluate to themselves.
- Symbols are looked up in the environment.
- Function applications are handled recursively.

When evaluating a list, it checks if the first symbol is a special form (e.g. 
quote, define, lambda) or a function call. A function call evaluates arguments
and applies the function:

```c
LispObject *apply_function(LispObject *fn, LispList *args) {
    if (fn->fn->is_builtin) {
        return fn->fn->builtin(args);
    } else {
        LispFunction *user_fn = fn->fn;
        Environment *new_env = malloc(sizeof(Environment));
        new_env->parent = user_fn->env;

        LispList *params = user_fn->params;
        LispList *arg_values = args;
        while (params != NULL && arg_values != NULL) {
            env_define(new_env, params->car->symbol, arg_values->car);
            params = params->cdr;
            arg_values = arg_values->cdr;
        }
        return eval(user_fn->body, new_env);
    }
}
```

For user-defined functions, it creates a new environment with the function's
parameters bound to their arguments, then evaluates the function body.


### Lambda: First-Class Functions

Functions in Lisp are first-class, meaning they can be created dynamically.
The lambda special form allows function creation:

```c
..
} else if (strcmp(car->symbol, "lambda") == 0) {
    LispFunction *fn = malloc(sizeof(LispFunction));
    fn->is_builtin = false;
    fn->params = cdr->car->list;
    fn->body = cdr->cdr->car;
    fn->env = env;
    return make_function(fn);
}
..
```

Here, lambda constructs a new LispFunction object that captures its environment
for lexical scoping.


### The apply Function

The apply_function function is key to evaluating function applications. It takes
a function and arguments, evaluates them if necessary, and either calls a built-in
function or evaluates the user-defined function's body in a new environment.


### Minimalist but Functional

Despite its simplicity, this implementation captures fundamental Lisp features:
- Pairs and lists via cons
- Symbolic computation via eval
- Lexical scoping with environments
- First-class functions via lambda
- Function application via apply

It lacks macros, tail-call optimisation, and garbage collection, but as a "minimal Scheme,"
it is a great starting point for understanding Lisp interpreters.
