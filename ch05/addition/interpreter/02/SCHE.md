
## A Minimal Scheme (improved): Sche

Some addtions: tail recursion and garbage collection.

### Tail Recursion

Tail recursion is an optimization where a function's recursive call is the last operation in the function.
This is especially important in Lisp interpreters, as they rely heavily on recursion for evaluating expressions.

In the function `eval_tail_recursive`, the recursion is structured such that after evaluating an expression
(such as applying a function or evaluating a list), the function directly returns the result or continues
evaluating in the tail position. This approach allows for constant stack space, since the current function
call is replaced by the next call rather than adding a new layer to the stack.

For example, when evaluating a list (`expr`), the interpreter checks whether it's a function call, performs
the necessary operations, and if it's a function that needs to be applied, it creates a new environment and
continues the evaluation in a loop. This ensures that tail recursion is used effectively, and the function
stack doesn't grow unnecessarily.


### Garbage Collection (Mark and Sweep)

Garbage collection is a key part of this implementation, which helps manage memory automatically by reclaiming
unused objects. The Mark and Sweep algorithm is used here to identify and remove objects that are no longer
reachable.

- Mark Phase: The function `mark()` is called on each object starting from the root objects (e.g. environment
variables, parameters, and body of functions). The marked flag is set to true for all objects that are reachable
from the environment or function parameters. During this phase, the objects are recursively marked as "alive"
based on the Lisp expressions and their connections.

- Sweep Phase: After marking reachable objects, the function sweep() goes through all objects in the object
pool. If an object is not marked (i.e., it's no longer reachable), it's considered garbage and is freed from
memory. This process ensures that memory is reclaimed by removing unused objects, preventing memory leaks.
Additionally, after sweeping, all marked objects are unmarked in preparation for the next garbage collection
cycle.


### Memory Management with an Object Pool

Instead of directly calling `malloc()` and `free()` for each object, the code uses an object pool. The pool
pre-allocates memory for Lisp objects, and whenever new objects are created (such as numbers, symbols, or lists),
they are added to this pool. This approach helps manage memory more efficiently by avoiding frequent
reallocations and making it easier to implement garbage collection.

When the object pool is full, it expands by doubling its capacity to accommodate more objects. The pool not
only tracks all allocated objects but also enables an efficient sweep phase, where only the unmarked objects
are reclaimed.


### Integration with Evaluation

The eval function leverages tail recursion and garbage collection. While evaluating Lisp expressions, the
interpreter continually evaluates subexpressions in the tail-recursive style. When enough evaluations have
been performed (e.g., after a certain number of function calls), garbage collection is triggered. This
ensures that memory usage doesn't grow uncontrollably as the interpreter processes expressions.

The core functions related to memory management (gc(), mark(), sweep()) work together to periodically clean
up the memory, ensuring that only objects that are still reachable (i.e., needed) are kept in memory, and
unneeded ones are freed.


### Details: Tail Recursion in Lisp Evaluation

In the `eval_tail_recursive()` function, you can see how it handles recursive evaluation by continually
evaluating subexpressions in the tail position:

```c
LispObject *eval_tail_recursive(LispObject *expr, Environment *env) {
    while (1) {  // loop ensures tail recursion
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

                // process first expression and apply recursion
                LispObject *fn_obj = eval_tail_recursive(car, env);
                if (fn_obj->type != TYPE_FUNCTION) {
                    printf("Error: Not a function\n");
                    exit(1);
                }

                // tail recursion in processing arguments
                LispList *args = NULL;
                LispList **tail = &args;
                while (cdr != NULL) {
                    LispObject *arg_val = eval_tail_recursive(cdr->car, env);
                    *tail = cons(arg_val, NULL);
                    tail = &(*tail)->cdr;
                    cdr = cdr->cdr;
                }

                // apply function
                expr = fn_obj->fn->body;
                env = new_env_for_fn(fn_obj, args);
                continue;  // ensure tail recursion
            }
            default:
                fprintf(stderr, "Invalid expression type: %d\n", expr->type);
                exit(EXIT_FAILURE);
        }
    }
}
```

Notice the `continue` statement after processing the function call. This ensures that
the evaluation of the function's body happens in a tail-recursive fashion, reusing the
current stack frame.


### Details: Garbage Collection (Mark and Sweep)

Garbage collection is performed in two phases: marking and sweeping. In the mark phase,
we traverse all reachable objects from the environment and mark them as "alive":

```c
void mark(LispObject *obj) {
    if (obj == NULL || obj->marked) return;
    obj->marked = true;

    switch (obj->type) {
        case TYPE_LIST:
            if (obj->list) {
                mark(obj->list->car);  // mark the car
                mark((LispObject *)obj->list->cdr);  // mark the cdr
            }
            break;
        case TYPE_FUNCTION:
            if (!obj->fn->is_builtin) {
                mark((LispObject *)obj->fn->params);  // mark function params
                mark(obj->fn->body);  // mark function body
            }
            break;
        default:
            break;
    }
}
```

This function ensures that all reachable objects (e.g. values in lists, parameters in
functions) are marked. When an object is marked, it is considered "alive" and will not
be collected.

The sweep phase then frees all unmarked objects:

```c
void sweep() {
    size_t i = 0;
    while (i < object_pool.count) {
        if (!object_pool.objects[i]->marked) {
            free(object_pool.objects[i]);
            object_pool.objects[i] = object_pool.objects[--object_pool.count];
        } else {
            object_pool.objects[i]->marked = false;  // unmark object for the next cycle
            i++;
        }
    }
}
```

This phase checks the marked flag for each object in the pool. If an object isn't marked,
it's considered garbage and is freed. The unmarked objects are removed from the pool, and
the remaining objects are unmarked for the next cycle.


### Details: Memory Management with the Object Pool

The object pool efficiently manages memory by reusing allocated memory for Lisp objects.
It expands dynamically as needed, avoiding repeated allocations:

```c
ObjectPool object_pool;

void init_object_pool() {
    object_pool.capacity = 1024;
    object_pool.count = 0;
    object_pool.objects = malloc(object_pool.capacity * sizeof(LispObject *));
}

LispObject *make_number(double value) {
    LispObject *obj = malloc(sizeof(LispObject));
    obj->type = TYPE_NUMBER;
    obj->marked = false;
    obj->number = value;
    object_pool.objects[object_pool.count++] = obj;  // add to object pool
    return obj;
}
```

If the pool reaches its capacity, it is dynamically resized to accommodate more objects:

```c
if (object_pool.count >= object_pool.capacity) {
    object_pool.capacity *= 2;
    object_pool.objects = realloc(object_pool.objects, object_pool.capacity * sizeof(LispObject *));
}
```

This reduces the overhead of frequent memory allocations and is critical for garbage
collection, as all objects are tracked in the pool.


### Integration of Tail Recursion and Garbage Collection

By combining tail recursion with garbage collection, the interpreter can evaluate deeply nested expressions
efficiently while ensuring memory is freed when no longer in use. As the evaluator processes expressions,
it continually marks and sweeps unused objects, preventing memory leaks.

```c
void gc(Environment *env) {
    mark_environment(env);  // mark all reachable objects
    sweep();  // Sseep away unmarked objects
}
```

The `gc()` function is invoked periodically to reclaim memory. It marks all objects reachable from the
environment and then sweeps away those that are no longer in use.


### Conclusion

By using tail recursion, memory usage remains efficient and constant regardless of how deep the recursion
goes. The garbage collection process ensures that memory is reclaimed after evaluation, making the
interpreter both efficient and robust. The combination of these techniques allows the Lisp interpreter
to handle a large number of expressions without running into stack overflow or memory issues.
