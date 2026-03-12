
#include <stdio.h>
#include <stdlib.h>

#include "effect.h"

#define N 4

typedef struct {
    int step;
    int cell;
    int grid[N][N];
} SudokuContext;


/* Check if placing value v at row r and column c
    is valid according to Sudoku rules */
int valid(SudokuContext* ctx, int r, int c, int v) {

    for (int i=0;i<N;i++)
        if (ctx->grid[r][i]==v || ctx->grid[i][c]==v)
            return 0;

    int br = (r/2)*2;
    int bc = (c/2)*2;

    for (int i=0;i<2;i++)
        for (int j=0;j<2;j++)
            if (ctx->grid[br+i][bc+j]==v)
                return 0;

    return 1;
}

/* Continuation function for Sudoku solver */
Effect sudoku_resume(Continuation* k, void* value) {
    SudokuContext* ctx = k->context;
    int choice = value ? *(int*)value : 0;

    if (ctx->cell >= N*N) {
        int* result = malloc(sizeof(int)*N*N);
        memcpy(result, ctx->grid, sizeof(ctx->grid));
        return eff_return(result);
    }

    int r = ctx->cell / N;
    int c = ctx->cell % N;

    if (ctx->step == 0) {
        int* choices = malloc(sizeof(int)*N);
        for (int i=0;i<N;i++)
            choices[i] = i+1;

        ctx->step = 1;

        return eff_choose(choices,N,k);
    }

    if (ctx->step == 1) {
        if (!valid(ctx,r,c,choice))
            return eff_error("constraint");

        ctx->grid[r][c] = choice;

        ctx->cell++;
        ctx->step = 0;

        return k->resume(k,NULL);
    }

    return eff_error("invalid");
}

/* Handler for non-deterministic effects */
void handle_amb(Effect eff) {

    /* Stack frame for handling effects */
    typedef struct {
        Effect effect;
    } Frame;

    Frame stack[10000];
    int sp=0;

    stack[sp++] = (Frame){eff};

    int solutions=0;

    while (sp > 0) {
        Effect cur = stack[--sp].effect;

        if (cur.tag==EFF_RETURN) {
            int* grid = cur.data.return_val;

            printf("Solution:\n");
            for (int r = 0; r < N; r++) {
                for(int c=0;c<N;c++)
                    printf("%d ",grid[r*N+c]);
                printf("\n");
            }
            printf("\n");

            free(grid);
            solutions++;
            continue;
        }

        if (cur.tag==EFF_ERROR)
            continue;

        if (cur.tag==EFF_NONDETERMINISM) {
            for (int i = cur.data.choice.count-1; i >= 0; i--) {
                Continuation* nk = malloc(sizeof(Continuation));
                memcpy(nk,cur.continuation,sizeof(Continuation));

                SudokuContext* nctx = malloc(sizeof(SudokuContext));
                memcpy(nctx,cur.continuation->context,sizeof(SudokuContext));

                nk->context = nctx;

                int choice = cur.data.choice.choices[i];

                Effect next = nk->resume(nk,&choice);

                stack[sp++] = (Frame){next};
            }
        }
    }

    printf("solutions: %d\n",solutions);
}


int main() {
    SudokuContext* ctx = malloc(sizeof(SudokuContext));
    memset(ctx->grid, 0, sizeof(ctx->grid));

    ctx->cell = 0;
    ctx->step = 0;

    Continuation k = {
        .resume = sudoku_resume,
        .context = ctx,
        .parent = NULL
    };

    Effect e = k.resume(&k, NULL);
    handle_amb(e);

    free(ctx);
}
