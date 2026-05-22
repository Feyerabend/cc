#pragma once
#include "term.h"


/*
 * Normalization by Evaluation.
 *
 *  eval : Env   × Term → Val     (term to semantic value)
 *  vapp : Val   × Val  → Val     (apply a value to an argument)
 * quote : depth × Val  → Term    (reify value back to normal-form term)
 *    nf : Term  → Term           (full normalization, empty env, depth 0)
 */

Val  *nbe_eval (Arena *a, Env  *env, Term *t);
Val  *nbe_vapp (Arena *a, Val  *fun, Val  *arg);
Val  *nbe_vfst (Arena *a, Val  *v);
Val  *nbe_vsnd (Arena *a, Val  *v);
Val  *nbe_vj (Arena *a, Val  *ty, Val *lhs, Val *motive, Val *base, Val *endpoint, Val *proof);
Val  *nbe_vnatrec (Arena *a, Val *motive, Val *base, Val *step, Val *n);
Val  *nbe_vboolrec (Arena *a, Val *motive, Val *tcase, Val *fcase, Val *b);
Val  *nbe_vwrec    (Arena *a, Val *motive, Val *step,  Val *w);
Val  *nbe_vabort   (Arena *a, Val *motive, Val *e);
Val  *nbe_vunitrec (Arena *a, Val *motive, Val *base, Val *s);
Val  *nbe_vcase    (Arena *a, Val *motive, Val *lcase, Val *rcase, Val *s);
Term *nbe_quote(Arena *a, int   depth, Val  *v);
Term *nbe_nf (Arena *a, Term *t);
