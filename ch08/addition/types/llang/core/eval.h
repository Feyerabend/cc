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
Val  *nbe_vtruncret(Arena *a, Val *ty_a,  Val *ty_b,  Val *func,  Val *t);
Val  *nbe_vpathapp (Arena *a, Val *path, Val *r);  /* Phase L2 */
Val  *nbe_vtransp  (Arena *a, Val *a_fun, Val *x); /* Phase L2 Stage 3 */
Val  *nbe_vhcomp   (Arena *a, Val *ty, Val *face, Val *tube, Val *base); /* Phase L2 Stage 4 */
Val  *nbe_vcomp    (Arena *a, Val *fam, Val *face, Val *tube, Val *base); /* Phase L2 Stage 4b — comp */
Val  *nbe_vfill    (Arena *a, Val *fam, Val *face, Val *tube, Val *base, Val *idx); /* Phase L2 fill */
Val  *nbe_vglue_ty (Arena *a, Val *base, Val *face, Val *fiber, Val *equiv); /* Phase L2 Stage 5 */
Val  *nbe_vlmax    (Arena *a, Val *l, Val *r); /* Phase M1 — level max */
Val  *nbe_vimin    (Arena *a, Val *l, Val *r); /* Phase L2 Stage 6 */
Val  *nbe_vimax    (Arena *a, Val *l, Val *r);
Val  *nbe_vineg    (Arena *a, Val *v);
Val  *nbe_visone   (Arena *a, Val *phi);       /* Phase L2 Stage 7 */
Val  *nbe_vglueelem(Arena *a, Val *face, Val *partial, Val *base); /* Phase L2 Stage 7d */
Val  *nbe_vunglue  (Arena *a, Val *face, Val *equiv,   Val *elem);
Val  *nbe_vcircrec (Arena *a, Val *motive, Val *base_case, Val *loop_case, Val *s);
Val  *nbe_vindrec  (Arena *a, int fam_idx, Val *motive, Val **cases, Val *scrut);
Term *nbe_quote(Arena *a, int   depth, Val  *v);
Term *nbe_nf (Arena *a, Term *t);
