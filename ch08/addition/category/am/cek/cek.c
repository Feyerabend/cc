#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// gcc -std=c99 -O2 cek.c -o cek

typedef struct GCObject GCObject;

struct GCObject {
    int marked;
    GCObject *next;
};

GCObject *gc_objects = NULL;

void *gc_alloc(size_t size) {
    GCObject *obj = malloc(size);
    if (!obj) { fprintf(stderr, "Out of memory\n"); exit(1); }
    obj->marked = 0;
    obj->next = gc_objects;
    gc_objects = obj;
    return obj;
}


typedef enum { T_VAR, T_LAM, T_APP, T_INT } TermTag;

typedef struct Term Term;

struct Term {
    TermTag tag;
    union {
        char *var;
        struct { char *param; Term *body; } lam;
        struct { Term *fun, *arg; } app;
        int intval;
    };
};



typedef enum { V_CLOSURE, V_INT, V_PRIM } ValueTag;

typedef struct Env Env;
typedef struct Kont Kont;

typedef struct Value {
    GCObject gc;
    ValueTag tag;
    union {
        struct { char *param; Term *body; Env *env; } clo;
        int intval;
    };
} Value;



struct Env {
    GCObject gc;
    char *name;
    Value *value;
    Env *next;
};

Env *env_extend(Env *env, char *name, Value *v) {
    Env *e = gc_alloc(sizeof(Env));
    e->name = name;
    e->value = v;
    e->next = env;
    return e;
}

Value *env_lookup(Env *env, char *name) {
    while (env) {
        if (!strcmp(env->name, name))
            return env->value;
        env = env->next;
    }
    fprintf(stderr, "Unbound variable: %s\n", name);
    exit(1);
}



typedef enum { K_HALT, K_ARG, K_FUN } KontTag;

struct Kont {
    GCObject gc;
    KontTag tag;
    union {
        struct { Term *arg; Env *env; Kont *next; } arg;
        struct { Value *fun; Kont *next; } fun;
    };
};



typedef struct {
    Term *control;
    Env *env;
    Kont *kont;
    Value *value;
} State;


// GC
void mark_value(Value *v);
void mark_env(Env *e);
void mark_kont(Kont *k);

void mark_value(Value *v) {
    if (!v || v->gc.marked) return;
    v->gc.marked = 1;
    if (v->tag == V_CLOSURE)
        mark_env(v->clo.env);
}

void mark_env(Env *e) {
    while (e && !e->gc.marked) {
        e->gc.marked = 1;
        mark_value(e->value);
        e = e->next;
    }
}

void mark_kont(Kont *k) {
    while (k && !k->gc.marked) {
        k->gc.marked = 1;
        if (k->tag == K_ARG) mark_env(k->arg.env);
        if (k->tag == K_FUN) mark_value(k->fun.fun);
        k = (k->tag == K_ARG) ? k->arg.next : k->fun.next;
    }
}

void gc_collect(State *s) {
    mark_value(s->value);
    mark_env(s->env);
    mark_kont(s->kont);

    GCObject **p = &gc_objects;
    while (*p) {
        if (!(*p)->marked) {
            GCObject *dead = *p;
            *p = dead->next;
            free(dead);
        } else {
            (*p)->marked = 0;
            p = &(*p)->next;
        }
    }
}


// cek step
void step(State *s) {
    if (s->control) {
        Term *t = s->control;

        if (t->tag == T_VAR) {
            s->value = env_lookup(s->env, t->var);
            s->control = NULL;
            return;
        }

        if (t->tag == T_INT) {
            Value *v = gc_alloc(sizeof(Value));
            v->tag = V_INT;
            v->intval = t->intval;
            s->value = v;
            s->control = NULL;
            return;
        }

        if (t->tag == T_LAM) {
            Value *v = gc_alloc(sizeof(Value));
            v->tag = V_CLOSURE;
            v->clo.param = t->lam.param;
            v->clo.body = t->lam.body;
            v->clo.env = s->env;
            s->value = v;
            s->control = NULL;
            return;
        }

        if (t->tag == T_APP) {
            Kont *k = gc_alloc(sizeof(Kont));
            k->tag = K_ARG;
            k->arg.arg = t->app.arg;
            k->arg.env = s->env;
            k->arg.next = s->kont;
            s->kont = k;
            s->control = t->app.fun;
            return;
        }
    }

    if (s->kont->tag == K_HALT)
        return;

    if (s->kont->tag == K_ARG) {
        Kont *k = s->kont;
        Kont *next = gc_alloc(sizeof(Kont));
        next->tag = K_FUN;
        next->fun.fun = s->value;
        next->fun.next = k->arg.next;
        s->kont = next;
        s->env = k->arg.env;
        s->control = k->arg.arg;
        return;
    }

    if (s->kont->tag == K_FUN) {
        Kont *k = s->kont;
        Value *fun = k->fun.fun;

        if (fun->tag != V_CLOSURE) {
            fprintf(stderr, "Attempt to apply non-function\n");
            exit(1);
        }

        Env *new_env = env_extend(fun->clo.env,
                                  fun->clo.param,
                                  s->value);
        s->kont = k->fun.next;
        s->env = new_env;
        s->control = fun->clo.body;
        return;
    }
}



Value *run(Term *t) {
    State s;
    s.control = t;
    s.env = NULL;
    s.kont = gc_alloc(sizeof(Kont));
    s.kont->tag = K_HALT;
    s.value = NULL;

    while (!(s.control == NULL && s.kont->tag == K_HALT)) {
        step(&s);
        gc_collect(&s);
    }
    return s.value;
}



Term *Var(char *x) {
    Term *t = malloc(sizeof(Term));
    t->tag = T_VAR; t->var = x; return t;
}

Term *Lam(char *x, Term *b) {
    Term *t = malloc(sizeof(Term));
    t->tag = T_LAM; t->lam.param = x; t->lam.body = b; return t;
}

Term *App(Term *f, Term *a) {
    Term *t = malloc(sizeof(Term));
    t->tag = T_APP; t->app.fun = f; t->app.arg = a; return t;
}

Term *Int(int n) {
    Term *t = malloc(sizeof(Term));
    t->tag = T_INT; t->intval = n; return t;
}



// helper
void expect_int(char *name, Term *t, int expected) {
    Value *v = run(t);
    if (v->tag != V_INT || v->intval != expected) {
        fprintf(stderr,
                "Test %s failed: expected %d, got %d\n",
                name, expected,
                v->tag == V_INT ? v->intval : -1);
        exit(1);
    }
    printf("Test %s passed\n", name);
}


// tests
Term *test_id(void) {
    return App(
        Lam("x", Var("x")),
        Int(7)
    );
} // (λx. x) 7

Term *test_const(void) {
    return App(
        App(
            Lam("x", Lam("y", Var("x"))),
            Int(10)
        ),
        Int(99)
    );
} // (λx. λy. x) 10 99

Term *test_nested(void) {
    return App(
        Lam("x",
            App(
                Lam("y", Var("y")),
                Var("x")
            )
        ),
        Int(5)
    );
} // (λx. (λy. y) x) 5

Term *test_closure(void) {
    return App(
        Lam("x",
            App(
                Lam("f", App(Var("f"), Int(0))),
                Lam("y", Var("x"))
            )
        ),
        Int(42)
    );
} // (λx. (λf. f 0) (λy. x)) 42

Term *test_shadow(void) {
    return App(
        Lam("x",
            App(
                Lam("x", Var("x")),
                Int(3)
            )
        ),
        Int(1)
    );
} // (λx. (λx. x) 3) 1

Term *test_tail(void) {
    Term *loop =
        Lam("f",
            App(
                Var("f"),
                Var("f")
            )
        );

    return App(loop, loop);
} // (λf. f f) (λf. f f)
// infinite loop to test tail call optimisation



int main(void) {
    expect_int("id", test_id(), 7); // (λx. x) 7
    expect_int("const", test_const(), 10); // (λx. λy. x) 10 99
    expect_int("nested", test_nested(), 5); // (λx. (λy. y) x) 5
    expect_int("closure", test_closure(), 42); // (λx. (λf. f 0) (λy. x)) 42
    expect_int("shadow", test_shadow(), 3); // (λx. (λx. x) 3) 1

    printf("All terminating tests passed.\n");

    // Uncomment to stress-test tail calls
    // Warning: this have to be terminated by you
    // run(test_tail()); 

    return 0;
}



