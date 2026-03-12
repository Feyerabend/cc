
#include "effect.h"


// Non-determinism with context isolation

typedef struct ChoiceContext {
    int step;
    int path;
    int first_choice;  // Store first choice
} ChoiceContext;

Effect choice_resume(Continuation* k, void* value) {
    ChoiceContext* ctx = (ChoiceContext*)k->context;
    int choice = value ? *(int*)value : 0;
    
    switch(ctx->step) {
        case 0: {
            printf("  Path %d: Chose %d at first branch\n", ctx->path, choice);
            ctx->first_choice = choice;  // Save it
            ctx->step = 1;
            int choices[] = {10, 20};
            return eff_choose(choices, 2, k);
        }
        
        case 1: {
            printf("  Path %d: Chose %d at second branch (after choosing %d)\n", 
                   ctx->path, choice, ctx->first_choice);
            int* result = malloc(sizeof(int));
            *result = ctx->first_choice + choice;  // Combine both choices
            return eff_return(result);
        }
        
        default:
            return eff_return(NULL);
    }
}

// creates fresh contexts for each path
void handle_nondeterminism(Effect eff) {
    typedef struct {
        Effect effect;
        ChoiceContext* ctx;  // Each path gets its own context
    } StackFrame;
    
    StackFrame stack[100];
    int sp = 0;
    
    stack[sp++] = (StackFrame){eff, NULL};
    
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
            // Create fresh context for each branch
            for (int i = current.data.choice.count - 1; i >= 0; i--) {
                int choice = current.data.choice.choices[i];
                
                // Clone the continuation with fresh context
                ChoiceContext* new_ctx = malloc(sizeof(ChoiceContext));
                if (current.continuation->context) {
                    memcpy(new_ctx, current.continuation->context, sizeof(ChoiceContext));
                } else {
                    new_ctx->step = 0;
                    new_ctx->path = path_num;
                    new_ctx->first_choice = 0;
                }
                new_ctx->path = path_num++;
                
                Continuation* new_k = malloc(sizeof(Continuation));
                memcpy(new_k, current.continuation, sizeof(Continuation));
                new_k->context = new_ctx;
                
                Effect next = new_k->resume(new_k, &choice);
                stack[sp++] = (StackFrame){next, new_ctx};
            }
            path_num -= current.data.choice.count; // Adjust counter
        }
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





int main() {
    
    printf("-- DEMO A: Non-determinism (exploring all paths) --\n");
    Effect nd = start_nondeterministic(0);
    handle_nondeterminism(nd);
        
    return 0;
}
