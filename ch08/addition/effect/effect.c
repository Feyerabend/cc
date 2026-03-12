#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>


typedef enum {
    EFF_RETURN,
    EFF_STATE_GET,
    EFF_STATE_PUT,
    EFF_ASYNC,
    EFF_ERROR,
    EFF_NONDETERMINISM
} EffectTag;

// Forward decl
struct Effect;
struct Continuation;

typedef struct Effect (*ResumeFn)(struct Continuation* k, void* value);

// Continuation - captures "rest of computation"
typedef struct Continuation {
    ResumeFn resume;
    void* context;
    struct Continuation* parent;
} Continuation;

// Effect structure
typedef struct Effect {
    EffectTag tag;
    union {
        void* return_val;
        struct { int dummy; } get;
        struct { int value; } put;
        struct { void* (*computation)(void*); void* arg; } async;
        struct { char* message; } error;
        struct { int* choices; int count; } choice;
    } data;
    Continuation* continuation;
} Effect;


// constructors for effects

Effect eff_return(void* value) {
    Effect e = {.tag = EFF_RETURN, .data.return_val = value};
    return e;
}

Effect eff_get(Continuation* k) {
    Effect e = {.tag = EFF_STATE_GET, .continuation = k};
    return e;
}

Effect eff_put(int value, Continuation* k) {
    Effect e = {.tag = EFF_STATE_PUT, .data.put.value = value, .continuation = k};
    return e;
}

Effect eff_error(char* msg) {
    Effect e = {.tag = EFF_ERROR, .data.error.message = msg};
    return e;
}

Effect eff_choose(int* choices, int count, Continuation* k) {
    Effect e = {
        .tag = EFF_NONDETERMINISM,
        .data.choice.choices = choices,
        .data.choice.count = count,
        .continuation = k
    };
    return e;
}



// example: a counter that increments state,
// but throws an error if it exceeds a certain limit.

typedef struct {
    int step;
    Continuation* k;
} CounterContext;

Effect counter_resume(Continuation* k, void* value) {
    CounterContext* ctx = (CounterContext*)k->context;
    int current_value = value ? *(int*)value : 0;
    
    switch(ctx->step) {
        case 0: // Get current state
            printf("Step 0: Got state = %d\n", current_value);
            ctx->step = 1;
            return eff_put(current_value + 1, k);
            
        case 1: // After putting new state
            printf("Step 1: Put new state\n");
            ctx->step = 2;
            return eff_get(k);
            
        case 2: // Get updated state
            printf("Step 2: Got updated state = %d\n", current_value);
            if (current_value > 5) {
                return eff_error("Counter exceeded limit!");
            }
            ctx->step = 3;
            return eff_return(&current_value);
            
        default:
            return eff_return(NULL);
    }
}

Effect start_counter() {
    CounterContext* ctx = malloc(sizeof(CounterContext));
    ctx->step = 0;
    
    Continuation* k = malloc(sizeof(Continuation));
    k->resume = counter_resume;
    k->context = ctx;
    k->parent = NULL;
    
    ctx->k = k;
    
    return eff_get(k);
}


// Handler of state effects 
// This handler maintains an integer state and responds
// to GET and PUT effects accordingly. It also handles errors gracefully.

typedef struct {
    int state;
} StateHandler;

void* handle_state(Effect eff, StateHandler* handler) {
    Effect current = eff;
    
    while (current.tag != EFF_RETURN && current.tag != EFF_ERROR) {
        switch (current.tag) {
            case EFF_STATE_GET: {
                printf("[State Handler] GET -> %d\n", handler->state);
                current = current.continuation->resume(current.continuation, &handler->state);
                break;
            }
            
            case EFF_STATE_PUT: {
                handler->state = current.data.put.value;
                printf("[State Handler] PUT <- %d\n", handler->state);
                current = current.continuation->resume(current.continuation, NULL);
                break;
            }
            
            default:
                printf("[State Handler] Unhandled effect: %d\n", current.tag);
                return NULL;
        }
    }
    
    if (current.tag == EFF_ERROR) {
        printf("[State Handler] Error caught: %s\n", current.data.error.message);
        return NULL;
    }
    
    return current.data.return_val;
}


// EXAMPLE: Non-determinism handler (explores multiple paths)

typedef struct ChoiceContext {
    int step;
    int path;
} ChoiceContext;

Effect choice_resume(Continuation* k, void* value) {
    ChoiceContext* ctx = (ChoiceContext*)k->context;
    int choice = value ? *(int*)value : 0;
    
    switch(ctx->step) {
        case 0: {
            printf("  Path %d: Chose %d at first branch\n", ctx->path, choice);
            ctx->step = 1;
            int choices[] = {10, 20};
            return eff_choose(choices, 2, k);
        }
        
        case 1: {
            printf("  Path %d: Chose %d at second branch\n", ctx->path, choice);
            int* result = malloc(sizeof(int));
            *result = choice;
            return eff_return(result);
        }
        
        default:
            return eff_return(NULL);
    }
}

Effect start_nondeterministic(int path) {
    ChoiceContext* ctx = malloc(sizeof(ChoiceContext));
    ctx->step = 0;
    ctx->path = path;
    
    Continuation* k = malloc(sizeof(Continuation));
    k->resume = choice_resume;
    k->context = ctx;
    k->parent = NULL;
    
    int choices[] = {1, 2, 3};
    return eff_choose(choices, 3, k);
}

// Handler that explores ALL paths
void handle_nondeterminism(Effect eff) {
    typedef struct {
        Effect effect;
        int choice_index;
    } StackFrame;
    
    StackFrame stack[100];
    int sp = 0;
    
    stack[sp++] = (StackFrame){eff, 0};
    
    int path_num = 0;
    
    while (sp > 0) {
        StackFrame frame = stack[--sp];
        Effect current = frame.effect;
        
        if (current.tag == EFF_RETURN) {
            printf("Path %d completed with result: %d\n\n", 
                   path_num++, *(int*)current.data.return_val);
            continue;
        }
        
        if (current.tag == EFF_NONDETERMINISM) {
            // Push all choice branches onto stack
            for (int i = current.data.choice.count - 1; i >= 0; i--) {
                int choice = current.data.choice.choices[i];
                Effect next = current.continuation->resume(
                    current.continuation, 
                    &choice
                );
                stack[sp++] = (StackFrame){next, i};
            }
        }
    }
}


// composed handler that combines state and error handling

typedef struct {
    int state;
    char error_msg[256];
    int has_error;
} ComposedHandler;

void* handle_state_and_error(Effect eff, ComposedHandler* handler) {
    Effect current = eff;
    
    while (1) {
        if (current.tag == EFF_RETURN) {
            return current.data.return_val;
        }
        
        if (current.tag == EFF_ERROR) {
            strcpy(handler->error_msg, current.data.error.message);
            handler->has_error = 1;
            return NULL;
        }
        
        switch (current.tag) {
            case EFF_STATE_GET:
                current = current.continuation->resume(current.continuation, &handler->state);
                break;
                
            case EFF_STATE_PUT:
                handler->state = current.data.put.value;
                current = current.continuation->resume(current.continuation, NULL);
                break;
                
            default:
                return NULL;
        }
    }
}



int main() {
    printf("-- DEMO 1: Stateful Computation --\n");
    StateHandler state_handler = {.state = 3};
    Effect counter = start_counter();
    void* result = handle_state(counter, &state_handler);
    printf("Final result: %p\n\n", result);
    
    printf("-- DEMO 2: Error Handling --\n");
    state_handler.state = 5; // This will trigger error
    counter = start_counter();
    result = handle_state(counter, &state_handler);
    printf("Final result after error: %p\n\n", result);
    
    printf("-- DEMO 3: Non-determinism (exploring all paths) --\n");
    Effect nd = start_nondeterministic(0);
    handle_nondeterminism(nd);
    
    printf("-- DEMO 4: Composed Handlers --\n");
    ComposedHandler composed = {.state = 2, .has_error = 0};
    counter = start_counter();
    result = handle_state_and_error(counter, &composed);
    if (composed.has_error) {
        printf("Caught error: %s\n", composed.error_msg);
    } else {
        printf("Success with final state: %d\n", composed.state);
    }
    
    return 0;
}
