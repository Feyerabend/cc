
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

        // request choice for a
        case 0: {
            ctx->step = 1;

            int* choices = malloc(sizeof(int)*5);
            int vals[5] = {1,2,3,4,5};
            memcpy(choices, vals, sizeof(vals));

            return eff_amb(choices,5,k);
        }

        // receive a, choose b
        case 1: {
            ctx->a = choice;
            ctx->step = 2;

            int* choices = malloc(sizeof(int)*5);
            int vals[5] = {1,2,3,4,5};
            memcpy(choices, vals, sizeof(vals));

            return eff_amb(choices,5,k);
        }

        // receive b, choose c
        case 2: {
            ctx->b = choice;
            ctx->step = 3;

            int* choices = malloc(sizeof(int)*5);
            int vals[5] = {1,2,3,4,5};
            memcpy(choices, vals, sizeof(vals));

            return eff_amb(choices,5,k);
        }

        // receive c and test constraints
        case 3: {

            ctx->c = choice;

            if (!(ctx->a * ctx->a + ctx->b * ctx->b ==
                  ctx->c * ctx->c)) {
                return eff_error("Not Pythagorean");
            }

            if (!(ctx->a < ctx->b && ctx->b < ctx->c)) {
                return eff_error("Ordering");
            }

            int* result = malloc(sizeof(int)*3);
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
    } Frame;

    Frame stack[1000];
    int sp = 0;

    stack[sp++] = (Frame){eff};

    printf("Searching for Pythagorean triples..\n");

    int solutions = 0;

    while (sp > 0) {

        Frame frame = stack[--sp];
        Effect current = frame.effect;

        if (current.tag == EFF_RETURN) {

            int* triple = (int*)current.data.return_val;

            printf("Found: %d^2 + %d^2 = %d^2\n",
                   triple[0], triple[1], triple[2]);

            solutions++;

            free(triple);
            continue;
        }

        if (current.tag == EFF_ERROR) {
            continue;
        }

        if (current.tag == EFF_NONDETERMINISM) {

            for (int i = current.data.choice.count - 1; i >= 0; i--) {

                Continuation* new_k = malloc(sizeof(Continuation));
                memcpy(new_k,current.continuation,sizeof(Continuation));

                PythagoreanContext* new_ctx =
                    malloc(sizeof(PythagoreanContext));

                memcpy(new_ctx,
                       current.continuation->context,
                       sizeof(PythagoreanContext));

                new_k->context = new_ctx;

                int choice = current.data.choice.choices[i];

                Effect next = new_k->resume(new_k,&choice);

                stack[sp++] = (Frame){next};
            }
        }
    }

    printf("Total solutions found: %d\n",solutions);
}




int main() {

    PythagoreanContext* ctx =
        malloc(sizeof(PythagoreanContext));

    ctx->step = 0;
    ctx->a = ctx->b = ctx->c = 0;

    Continuation k = {
        .resume = pythagorean_resume,
        .context = ctx,
        .parent = NULL
    };

    Effect eff = k.resume(&k,NULL);

    handle_amb(eff);

    free(ctx);

    return 0;
}