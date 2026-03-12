
#include <stdio.h>
#include <stdlib.h>

#include "effect.h"

// automatic backtracking search

Effect eff_amb(int* choices, int count, Continuation* k) {
    return eff_choose(choices, count, k);
}

Effect eff_require(int condition, Continuation* k) {
    if (!condition) {
        return eff_error("Requirement failed");
    }
    return k->resume(k, NULL);
}

// Find Pythagorean triples
typedef struct {
    int step;
    int a, b, c;
} PythagoreanContext;

Effect pythagorean_resume(Continuation* k, void* value) {
    PythagoreanContext* ctx = (PythagoreanContext*)k->context;
    int choice = value ? *(int*)value : 0;
    
    switch(ctx->step) {
        case 0: { // Choose 'a'
            ctx->a = choice;
            ctx->step = 1;
            int choices[] = {1, 2, 3, 4, 5};
            return eff_amb(choices, 5, k);
        }
        
        case 1: { // Choose 'b'
            ctx->b = choice;
            ctx->step = 2;
            int choices[] = {1, 2, 3, 4, 5};
            return eff_amb(choices, 5, k);
        }
        
        case 2: { // Choose 'c'
            ctx->c = choice;
            // Require Pythagorean condition
            int satisfies = (ctx->a * ctx->a + ctx->b * ctx->b == ctx->c * ctx->c);
            if (!satisfies) {
                return eff_error("Not a Pythagorean triple");
            }
            
            // Also require a < b < c (avoid duplicates)
            if (!(ctx->a < ctx->b && ctx->b < ctx->c)) {
                return eff_error("Invalid ordering");
            }
            
            int* result = malloc(sizeof(int) * 3);
            result[0] = ctx->a;
            result[1] = ctx->b;
            result[2] = ctx->c;
            return eff_return(result);
        }
        
        default:
            return eff_error("Invalid step");
    }
}

void handle_amb(Effect eff) {
    typedef struct {
        Effect effect;
        void* context_copy;
    } Frame;
    
    Frame stack[1000];
    int sp = 0;
    stack[sp++] = (Frame){eff, NULL};
    
    printf("Searching for Pythagorean triples...\n");
    int solutions = 0;
    
    while (sp > 0) {
        Frame frame = stack[--sp];
        Effect current = frame.effect;
        
        if (current.tag == EFF_RETURN) {
            int* triple = (int*)current.data.return_val;
            printf("Found: %d² + %d² = %d²\n", triple[0], triple[1], triple[2]);
            solutions++;
            free(triple);
            continue;
        }
        
        if (current.tag == EFF_ERROR) {
            // Backtrack (just pop from stack)
            continue;
        }
        
        if (current.tag == EFF_NONDETERMINISM) {
            // Push all branches
            for (int i = current.data.choice.count - 1; i >= 0; i--) {
                PythagoreanContext* new_ctx = malloc(sizeof(PythagoreanContext));
                if (current.continuation->context) {
                    memcpy(new_ctx, current.continuation->context, 
                           sizeof(PythagoreanContext));
                }
                
                Continuation* new_k = malloc(sizeof(Continuation));
                memcpy(new_k, current.continuation, sizeof(Continuation));
                new_k->context = new_ctx;
                
                int choice = current.data.choice.choices[i];
                Effect next = new_k->resume(new_k, &choice);
                stack[sp++] = (Frame){next, new_ctx};
            }
        }
    }
    
    printf("Total solutions found: %d\n", solutions);
}
