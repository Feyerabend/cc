#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "effects.h"

#define MAX_VARS 16
#define MAX_RULES 16


/* Logic term / variable */

typedef enum { VAR, ATOM } TermType;

typedef struct {
    TermType type;
    char* name;    // variable name or atom
    int value;     // assigned value for VAR
} Term;


/* Clause (fact or rule) */

typedef struct {
    Term head[MAX_VARS];
    int head_len;
    Term body[MAX_VARS];
    int body_len;
} Clause;



/* Program context */

typedef struct {
    int step;
    int clause_index;
    int arg_index;
} LogicCtx;


/* Knowledge base */

Clause KB[MAX_RULES];
int KB_count = 0;


/* Helper: add a fact */
void add_fact(char* atom) {
    Clause c = {0};
    c.head[0].type = ATOM;
    c.head[0].name = atom;
    c.head_len = 1;
    c.body_len = 0;
    KB[KB_count++] = c;
}

/* Helper: unify head and query */
int unify(Term* t1, Term* t2) {
    if (t1->type == ATOM && t2->type == ATOM)
        return strcmp(t1->name,t2->name) == 0;

    if (t1->type == VAR) {
        t1->value = t2->value;
        return 1;
    }

    if (t2->type == VAR) {
        t2->value = t1->value;
        return 1;
    }

    return 0;
}

/* Logic engine (resumes choices) */

Effect logic_resume(Continuation* k, void* value) {
    LogicCtx* ctx = k->context;

    if(ctx->clause_index >= KB_count)
        return eff_error("no more clauses");

    Clause* c = &KB[ctx->clause_index];

    if (ctx->step == 0) {
        // choose next clause
        int* choices = malloc(sizeof(int)*(KB_count-ctx->clause_index));
        for (int i = 0;i < KB_count-ctx->clause_index; i++)
            choices[i] = ctx->clause_index+i;
        ctx->step = 1;
        return eff_choose(choices, KB_count-ctx->clause_index, k);
    }

    if (ctx->step == 1) {
        ctx->clause_index = *(int*)value;

        // unify head with query
        Term query = {ATOM,"a",0}; // example query
        if (!unify(&c->head[0], &query))
            return eff_error("unify fail");

        ctx->step = 2;

        if (c->body_len>0) {
            // recurse on body (not fully implemented)
            return eff_error("body not implemented");
        }

        // success: return clause_index
        int* result = malloc(sizeof(int));
        *result = ctx->clause_index;
        return eff_return(result);
    }

    return eff_error("invalid step");
}


/* Effect handler (DFS/backtracking) */

typedef struct {
    Effect effect;
} Frame;

void handle_logic(Effect eff) {
    Frame stack[128];
    int sp=0;
    stack[sp++] = (Frame){eff};

    while (sp > 0) {
        Frame frame = stack[--sp];
        Effect cur = frame.effect;

        if (cur.tag == EFF_RETURN) {
            int* r = cur.data.return_val;
            printf("Success: clause %d\n",*r);
            free(r);
            continue;
        }

        if (cur.tag == EFF_ERROR) {
            // backtrack
            continue;
        }

        if (cur.tag == EFF_NONDETERMINISM) {
            for (int i = cur.data.choice.count-1; i>=0; i--) {
                Continuation* nk = malloc(sizeof(Continuation));
                memcpy(nk,cur.continuation,sizeof(Continuation));

                LogicCtx* nctx = malloc(sizeof(LogicCtx));
                memcpy(nctx,cur.continuation->context,sizeof(LogicCtx));

                nk->context = nctx;
                int choice = cur.data.choice.choices[i];
                Effect next = nk->resume(nk,&choice);
                stack[sp++] = (Frame){next};
            }
        }
    }
}


int main() {
    // add some facts
    add_fact("a");
    add_fact("b");
    add_fact("c");

    LogicCtx* ctx = malloc(sizeof(LogicCtx));
    ctx->step = 0;
    ctx->clause_index = 0;

    Continuation k = {logic_resume, ctx, NULL};

    Effect e = k.resume(&k,NULL);

    handle_logic(e);

    free(ctx);
    return 0;
}
