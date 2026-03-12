
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "effects.h"


typedef struct {
    int step;
    int x;
} LogicCtx;

typedef struct {
    char* key;
    int value;
} KV;

typedef struct {
    KV log[32];
    int count;
} Tx;

typedef struct {
    Effect effect;
    Tx tx;
} Frame;



Effect logic_resume(Continuation* k, void* value) {
    LogicCtx* ctx = k->context;

    switch (ctx->step) {

        case 0: {
            ctx->step = 1;

            int* choices = malloc(sizeof(int)*3);
            choices[0] = 1;
            choices[1] = 2;
            choices[2] = 3;

            return eff_choose(choices, 3, k);
        }

        case 1: {
            ctx->x = *(int*)value;
            ctx->step = 2;
            return eff_put("x", ctx->x, k);
        }

        case 2: {
            if (ctx->x <= 1)
                return eff_error("constraint");
            ctx->step = 3;
            return eff_get("x",k);
        }

        case 3: {
            int v = *(int*)value;
            int* result = malloc(sizeof(int));
            *result = v;

            return eff_return(result);
        }

        default:
            return eff_error("invalid");
    }
}



void handle_logic(Effect eff) {
    Frame stack[128];
    int sp = 0;

    stack[sp++] = (Frame){eff,{0}};

    printf("Running logic transaction\n\n");

    while (sp > 0) {
        Frame frame = stack[--sp];
        Effect cur = frame.effect;

        if (cur.tag == EFF_RETURN) {
            int* r = cur.data.return_val;

            printf("SUCCESS branch result = %d\n",*r);
            printf("Committed writes:\n");
            for (int i = 0;i < frame.tx.count; i++)
                printf("  %s = %d\n",
                    frame.tx.log[i].key,
                    frame.tx.log[i].value);
            printf("\n");

            free(r);
            continue;
        }

        if (cur.tag == EFF_ERROR) {
            printf("Branch aborted (rollback)\n");
            continue;
        }

        if (cur.tag == EFF_NONDETERMINISM) {
            for (int i = cur.data.choice.count-1; i >= 0; i--) {
                Continuation* nk = malloc(sizeof(Continuation));
                memcpy(nk,cur.continuation,sizeof(Continuation));

                LogicCtx* nctx = malloc(sizeof(LogicCtx));
                memcpy(nctx,cur.continuation->context,sizeof(LogicCtx));

                nk->context = nctx;
                int choice = cur.data.choice.choices[i];
                Effect next = nk->resume(nk,&choice);
                stack[sp++] = (Frame){next,frame.tx};
            }

            continue;
        }


        if (cur.tag == EFF_STATE_PUT) {
            if (frame.tx.count < 32) {
                frame.tx.log[frame.tx.count++] =
                    (KV){
                        cur.data.put.key,
                        cur.data.put.value
                    };
            }

            Effect next =
                cur.continuation->resume(
                    cur.continuation,
                    NULL
                );

            stack[sp++] = (Frame){next,frame.tx};
            continue;
        }


        if (cur.tag == EFF_STATE_GET) {
            int v = 0;

            for (int i = frame.tx.count-1; i >= 0; i--) {
                if (strcmp(frame.tx.log[i].key, cur.data.get.key) == 0) {
                    v = frame.tx.log[i].value;
                    break;
                }

                Effect next =
                    cur.continuation->resume(
                        cur.continuation,
                        &v
                    );

                stack[sp++] = (Frame){next,frame.tx};

                continue;
            }
        }
    }
}

int main() {
    LogicCtx* ctx = malloc(sizeof(LogicCtx));

    ctx->step = 0;
    ctx->x = 0;

    Continuation k = {
        .resume = logic_resume,
        .context = ctx,
        .parent = NULL
    };

    Effect eff = k.resume(&k, NULL);
    handle_logic(eff);

    free(ctx);
}
