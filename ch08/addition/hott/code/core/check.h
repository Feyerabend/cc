#pragma once
#include "term.h"
#include "eval.h"

/*
 * Bidirectional type checker for dependent type theory.
 *
 * TCtx is a parallel to Env: TCtx[i] holds the *type* (as a Val) of the
 * variable at de Bruijn index i.  Env[i] holds its *value*.
 *
 * Both lists are extended simultaneously when entering a binder:
 *   - TCtx gets the evaluated domain type
 *   - Env  gets a fresh neutral (vl_neutral at the current depth)
 */

typedef struct TCtx TCtx;
struct TCtx {
    char *name;   /* hint for error messages */
    Val  *type;
    TCtx *next;
};

/*
 * infer(a, depth, tctx, env, t)
 *   Returns the type of t as a semantic value, or NULL on error.
 *   Works for: Var, App, Pi, Type, annotated terms (t : T).
 *   Fails for bare Lam (no type annotation available).
 *
 * check(a, depth, tctx, env, t, ty)
 *   Verifies t has type ty.  Returns 1 on success, 0 on error.
 *   Works for Lam against a Pi type; falls back to infer + conv otherwise.
 *
 * conv(a, depth, u, v)
 *   Definitional equality.  Both u and v must be semantic values (output
 *   of nbe_eval).  Includes eta-expansion for functions.
 */

Val *infer(Arena *a, int depth, TCtx *tctx, Env *env, Term *t);
int  check(Arena *a, int depth, TCtx *tctx, Env *env, Term *t, Val *ty);
int  conv (Arena *a, int depth, Val  *u,    Val  *v);

/* Quote v to a term and print it (requires arena for scratch allocation). */
void val_print_tctx(Arena *a, Val *v, int depth, TCtx *tctx);
