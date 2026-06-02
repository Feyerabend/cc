#include <stdio.h>
#include <stdlib.h>
#include "eval.h"
#include "check.h"   /* conv() — mutual dependency: check.c uses nbe_eval, eval.c uses conv */
#include "defs.h"

/* ── HIT path constructor sentinel levels
 *
 * Sentinel level for path ctor ctor_idx of family fam_idx:
 *   -(1000 + fam_idx * 64 + ctor_idx)
 * Range: [-1000, -17383] — below all existing sentinels (-999..-985).
 * IND_MAX_CTORS=64 and MAX_IND_DEFS=256 (from defs.c/parse.c).
 */
#define HIT_PATH_CTR_STRIDE 64
static inline int hit_path_sentinel(int fam_idx, int ci) {
    return -(1000 + fam_idx * HIT_PATH_CTR_STRIDE + ci);
}
/* Returns 1 and fills fam_out/ctor_out if lvl is a valid HIT path sentinel. */
static inline int hit_path_sentinel_decode(int lvl, int *fam_out, int *ctor_out) {
    if (lvl > -1000) return 0;
    int x = -(lvl + 1000);
    *fam_out  = x / HIT_PATH_CTR_STRIDE;
    *ctor_out = x % HIT_PATH_CTR_STRIDE;
    if (*fam_out >= ind_count()) return 0;
    IndDef *fam = ind_get(*fam_out);
    if (*ctor_out >= fam->n_ctors) return 0;
    return fam->ctors[*ctor_out].is_path_ctor;
}

/* Build Env from SP_APP spine nodes (head → dB 0, next → dB 1, …). */
static Env *spine_to_env(Arena *a, Spine *sp) {
    if (!sp || sp->kind != SP_APP) return NULL;
    return env_cons(a, sp->val, spine_to_env(a, sp->next));
}

/* ── Environment lookup */

static Val *env_lookup(Arena *a, Env *env, int idx, int orig) {
    for (; env && idx > 0; env = env->next, idx--);
    if (!env) {
        fprintf(stderr, "eval: free variable at de Bruijn index %d\n", orig);
        return vl_neutral(a, -(orig + 1), NULL);
    }
    return env->val;
}

/* ── Projections on values */

/* Synthetic fst/snd tubes: env=[tube], body = FST/SND(APP(VAR(1), VAR(0))). */
static Val *make_fst_tube(Arena *a, Val *tube) {
    Env  *env  = env_cons(a, tube, NULL);
    Term *body = tm_fst(a, tm_app(a, tm_var(a, 1), tm_var(a, 0)));
    return vl_lam(a, "i", env, body);
}
static Val *make_snd_tube(Arena *a, Val *tube) {
    Env  *env  = env_cons(a, tube, NULL);
    Term *body = tm_snd(a, tm_app(a, tm_var(a, 1), tm_var(a, 0)));
    return vl_lam(a, "i", env, body);
}

Val *nbe_vfst(Arena *a, Val *v) {
    if (v->tag == VL_PAIR)    return v->pair.fst;
    if (v->tag == VL_NEUTRAL)
        return vl_neutral(a, v->neutral.lvl, spine_fst(a, v->neutral.spine));
    /* fst (hcomp (Σ A B) φ u base) = hcomp A φ (λi. fst (u i)) (fst base)
       Always correct regardless of whether B is dependent. */
    if (v->tag == VL_HCOMP && v->hcomp_s.ty->tag == VL_SIGMA)
        return nbe_vhcomp(a, v->hcomp_s.ty->pi.dom,
                          v->hcomp_s.face,
                          make_fst_tube(a, v->hcomp_s.tube),
                          nbe_vfst(a, v->hcomp_s.base));
    /* fst (comp (λi. Σ(x:A i). B) φ u base) = comp (λi. A i) φ (λi. fst(u i)) (fst base) */
    if (v->tag == VL_COMP) {
        Val *fam = v->hcomp_s.ty;
        if ((fam->tag == VL_LAM || fam->tag == VL_PATHABS) &&
            fam->lam.env == NULL && fam->lam.body->tag == TM_SIG)
            return nbe_vcomp(a, vl_lam(a, "i", NULL, fam->lam.body->pi.dom),
                             v->hcomp_s.face,
                             make_fst_tube(a, v->hcomp_s.tube),
                             nbe_vfst(a, v->hcomp_s.base));
    }
    fprintf(stderr, "vfst: not a pair (tag=%d)\n", (int)v->tag); exit(1);
}

Val *nbe_vsnd(Arena *a, Val *v) {
    if (v->tag == VL_PAIR)    return v->pair.snd;
    if (v->tag == VL_NEUTRAL)
        return vl_neutral(a, v->neutral.lvl, spine_snd(a, v->neutral.spine));
    /* snd (hcomp (Σ A B) φ u base) — exact formula using fill:
     *   = comp (λi. B(fill (λ_.A) φ (λi.fst(u i)) (fst base) i)) φ (λi.snd(u i)) (snd base)
     *
     * B depends only on x (not on i, since the Σ type is fixed).
     * B_lam = λx. B(x) captures sigma->pi.env; const_A = λ_. A as a constant II→Type.
     *
     * Family body env (after applying to i):
     *   [i(0), B_lam(1), const_A(2), face(3), fst_tube(4), fst_base(5)]
     * Body = APP(VAR(1), FILL(VAR(2), VAR(3), VAR(4), VAR(5), VAR(0)))
     *      = B_lam(fill const_A φ fst_tube fst_base i) = B(fill_i)  ✓
     */
    if (v->tag == VL_HCOMP && v->hcomp_s.ty->tag == VL_SIGMA) {
        Val *sigma     = v->hcomp_s.ty;
        Val *A_dom     = sigma->pi.dom;
        Val *face_val  = v->hcomp_s.face;
        Val *fst_tube  = make_fst_tube(a, v->hcomp_s.tube);
        Val *fst_base  = nbe_vfst(a, v->hcomp_s.base);
        Val *snd_tube  = make_snd_tube(a, v->hcomp_s.tube);
        Val *snd_base  = nbe_vsnd(a, v->hcomp_s.base);
        Val *B_lam     = vl_lam(a, "x", sigma->pi.env, sigma->pi.cod);
        Val *const_A   = vl_lam(a, "_", env_cons(a, A_dom, NULL), tm_var(a, 1));
        Term *fill_i   = tm_fill(a, tm_var(a,2), tm_var(a,3), tm_var(a,4), tm_var(a,5), tm_var(a,0));
        Term *fam_body = tm_app(a, tm_var(a,1), fill_i);
        Env  *fam_env  = env_cons(a, B_lam,
                         env_cons(a, const_A,
                         env_cons(a, face_val,
                         env_cons(a, fst_tube,
                         env_cons(a, fst_base, NULL)))));
        Val  *B_fill_fam = vl_lam(a, "i", fam_env, fam_body);
        return nbe_vcomp(a, B_fill_fam, face_val, snd_tube, snd_base);
    }
    /* snd (comp (λi. Σ(x:A i). B i x) φ u p) — exact formula:
     *   = comp (λi. B(fill A_fam φ fst_u fst_p i, i)) φ (λi.snd(u i)) (snd p)
     *
     * Requires closed family (fam->lam.env == NULL).
     * B depends on both x and i: B_cod = fam->lam.body->pi.cod with VAR(0)=x, VAR(1)=i.
     * B_2_val = λi. λx. B_cod  — curried B taking i first, then x.
     *
     * Family body env (after applying to i):
     *   [i(0), B_2_val(1), A_fam(2), face(3), fst_tube(4), fst_base(5)]
     * Body = APP(APP(VAR(1), VAR(0)), FILL(VAR(2), VAR(3), VAR(4), VAR(5), VAR(0)))
     *      = B_2_val(i)(fill A_fam φ fst_tube fst_p i) = B(fill_i, i)  ✓
     */
    if (v->tag == VL_COMP) {
        Val *fam = v->hcomp_s.ty;
        if ((fam->tag == VL_LAM || fam->tag == VL_PATHABS) &&
            fam->lam.env == NULL && fam->lam.body->tag == TM_SIG) {
            Val *A_fam    = vl_lam(a, "i", NULL, fam->lam.body->pi.dom);
            Val *B_2_val  = vl_lam(a, "i", NULL, tm_lam(a, "x", fam->lam.body->pi.cod));
            Val *face_val = v->hcomp_s.face;
            Val *fst_tube = make_fst_tube(a, v->hcomp_s.tube);
            Val *fst_base = nbe_vfst(a, v->hcomp_s.base);
            Val *snd_tube = make_snd_tube(a, v->hcomp_s.tube);
            Val *snd_base = nbe_vsnd(a, v->hcomp_s.base);
            Term *fill_i   = tm_fill(a, tm_var(a,2), tm_var(a,3), tm_var(a,4), tm_var(a,5), tm_var(a,0));
            Term *fam_body = tm_app(a, tm_app(a, tm_var(a,1), tm_var(a,0)), fill_i);
            Env  *fam_env  = env_cons(a, B_2_val,
                             env_cons(a, A_fam,
                             env_cons(a, face_val,
                             env_cons(a, fst_tube,
                             env_cons(a, fst_base, NULL)))));
            Val  *B_fill_fam = vl_lam(a, "i", fam_env, fam_body);
            return nbe_vcomp(a, B_fill_fam, face_val, snd_tube, snd_base);
        }
    }
    fprintf(stderr, "vsnd: not a pair (tag=%d)\n", (int)v->tag); exit(1);
}

/* ── Nat recursor */

Val *nbe_vnatrec(Arena *a, Val *motive, Val *base, Val *step, Val *n) {
    if (n->tag == VL_ZERO)
        return base;
    if (n->tag == VL_SUCC) {
        Val *prev = nbe_vnatrec(a, motive, base, step, n->succ);
        return nbe_vapp(a, nbe_vapp(a, step, n->succ), prev);
    }
    if (n->tag == VL_NEUTRAL)
        return vl_neutral(a, n->neutral.lvl,
                          spine_natrec(a, motive, base, step,
                                       n->neutral.spine));
    fprintf(stderr, "vnatrec: not a Nat\n"); exit(1);
}

/* ── Bool eliminator */

Val *nbe_vboolrec(Arena *a, Val *motive, Val *tcase, Val *fcase, Val *b) {
    if (b->tag == VL_TRUE)    return tcase;
    if (b->tag == VL_FALSE)   return fcase;
    if (b->tag == VL_NEUTRAL)
        return vl_neutral(a, b->neutral.lvl,
                          spine_boolrec(a, motive, tcase, fcase,
                                        b->neutral.spine));
    fprintf(stderr, "vboolrec: not a Bool\n"); exit(1);
}

/* ── Empty eliminator (ex falso) */

Val *nbe_vabort(Arena *a, Val *motive, Val *e) {
    if (e->tag == VL_NEUTRAL)
        return vl_neutral(a, e->neutral.lvl,
                          spine_abort(a, motive, e->neutral.spine));
    fprintf(stderr, "vabort: scrutinee is not neutral (Empty has no constructors)\n");
    exit(1);
}

/* ── Circle recursor
 *
 * β-rule: S1rec B b l base ≡ b  (fires when scrut = VL_BASE)
 * Stays neutral on any other neutral scrutinee.
 */

Val *nbe_vcircrec(Arena *a, Val *motive, Val *base_case, Val *loop_case, Val *s) {
    if (s->tag == VL_BASE)    return base_case;
    if (s->tag == VL_NEUTRAL)
        return vl_neutral(a, s->neutral.lvl,
                          spine_circrec(a, motive, base_case, loop_case,
                                        s->neutral.spine));
    fprintf(stderr, "vcircrec: not a circle value\n"); exit(1);
}

/* ── Truncation eliminator
 *
 * β-rule: truncrec A B f (trint A a) ≡ f a
 * trint A a is a neutral with lvl=TRINT_CONST_LVL and spine [SP_APP a, SP_APP A].
 * (spine head = most recently applied = a; next = A)
 */

Val *nbe_vtruncret(Arena *a, Val *ty_a, Val *ty_b, Val *func, Val *t) {
    if (t->tag == VL_NEUTRAL && t->neutral.lvl == TRINT_CONST_LVL) {
        Spine *sp = t->neutral.spine;
        if (sp && sp->kind == SP_APP &&
            sp->next && sp->next->kind == SP_APP &&
            !sp->next->next)
            return nbe_vapp(a, func, sp->val);  /* f a */
    }
    if (t->tag == VL_NEUTRAL)
        return vl_neutral(a, t->neutral.lvl,
                          spine_truncrec(a, ty_a, ty_b, func, t->neutral.spine));
    fprintf(stderr, "vtruncret: scrutinee is not a truncated value\n");
    exit(1);
}

/* ── Interval operations (Phase L2 Stage 6)
 *
 * imin l r : II — interval meet (∧);  i0∧x=i0, i1∧x=x, x∧i0=i0, x∧i1=x
 * imax l r : II — interval join (∨);  i0∨x=x,  i1∨x=i1, x∨i0=x,  x∨i1=i1
 * ineg  v  : II — interval flip (~);  ~i0=i1,  ~i1=i0,  otherwise stuck
 *
 * Convention: i0 = VL_NEUTRAL(IZERO_CONST_LVL), i1 = VL_NEUTRAL(IONE_CONST_LVL).
 *
 * After endpoint absorptions, De Morgan normalisation, and complement detection,
 * a final fallback checks Boolean tautology / contradiction by exhaustive
 * variable enumeration (2^n, n ≤ MAX_FACE_VARS).  This catches identities
 * like  imax (imax φ1 φ2) (imax ~φ1 ~φ2) = i1  that are not of the form
 * x∨~x but are still universally true in the two-element Boolean algebra.
 *
 * DESIGN INVARIANT: eval_face_bits uses NO nbe_ calls — only local bit
 * arithmetic — so there is no re-entrant path back into nbe_vimin/nbe_vimax.
 */

#define MAX_FACE_VARS 8

/* A "face variable" is a VL_NEUTRAL at a user-controlled depth level:
   non-negative and not the TRANSP_PROBE_LVL synthetic probe. */
static int face_var_p(int lvl) {
    return lvl >= 0 && lvl != TRANSP_PROBE_LVL;
}

/* Collect distinct face-variable levels from v into lvls[0..n).
   Returns updated n, or max+1 on overflow (stops traversal early). */
static int collect_face_vars(Val *v, int *lvls, int n, int max) {
    if (!v || n > max) return n;
    switch (v->tag) {
    case VL_NEUTRAL:
        if (face_var_p(v->neutral.lvl)) {
            for (int i = 0; i < n; i++)
                if (lvls[i] == v->neutral.lvl) return n;
            if (n == max) return max + 1;    /* overflow: too many distinct vars */
            lvls[n++] = v->neutral.lvl;
        }
        return n;
    case VL_INEG:
        return collect_face_vars(v->succ, lvls, n, max);
    case VL_IMIN:
    case VL_IMAX:
        n = collect_face_vars(v->pair.fst, lvls, n, max);
        return collect_face_vars(v->pair.snd, lvls, n, max);
    default:
        return n;
    }
}

/* Evaluate a face expression to 0 (i0), 1 (i1), or -1 (unknown/other).
   vars in lvls[i] are given concrete value vals[i] ∈ {0,1}.
   NO nbe_ calls — safe to invoke from inside nbe_vimin/nbe_vimax. */
static int eval_face_bits(Val *v, int *lvls, int *vals, int n) {
    if (!v) return -1;
    switch (v->tag) {
    case VL_NEUTRAL:
        if (v->neutral.lvl == IZERO_CONST_LVL) return 0;
        if (v->neutral.lvl == IONE_CONST_LVL)  return 1;
        for (int i = 0; i < n; i++)
            if (lvls[i] == v->neutral.lvl) return vals[i];
        return -1;   /* unsubstituted neutral (probe, or out-of-range var) */
    case VL_INEG: {
        int x = eval_face_bits(v->succ, lvls, vals, n);
        if (x == 0) return 1;
        if (x == 1) return 0;
        return -1;
    }
    case VL_IMIN: {
        int a = eval_face_bits(v->pair.fst, lvls, vals, n);
        int b = eval_face_bits(v->pair.snd, lvls, vals, n);
        if (a == 0 || b == 0) return 0;   /* 0∧x = 0 */
        if (a == 1) return b;              /* 1∧x = x */
        if (b == 1) return a;
        return -1;
    }
    case VL_IMAX: {
        int a = eval_face_bits(v->pair.fst, lvls, vals, n);
        int b = eval_face_bits(v->pair.snd, lvls, vals, n);
        if (a == 1 || b == 1) return 1;   /* 1∨x = 1 */
        if (a == 0) return b;              /* 0∨x = x */
        if (b == 0) return a;
        return -1;
    }
    default:
        return -1;
    }
}

/* Check: imax(l,r) = i1 for all 2^n variable assignments.
   vals[] is scratch space for the current assignment.
   Returns 1 if tautology (every assignment gives i1), 0 otherwise.
   Conservative: if any assignment yields unknown (-1), returns 0. */
static int face_imax_taut(Val *l, Val *r,
                          int *lvls, int *vals, int n, int idx) {
    if (idx == n) {
        int lv = eval_face_bits(l, lvls, vals, n);
        int rv = eval_face_bits(r, lvls, vals, n);
        return lv == 1 || rv == 1;  /* 1∨x=1; if both ≤0 or unknown → not proved */
    }
    vals[idx] = 0;
    if (!face_imax_taut(l, r, lvls, vals, n, idx + 1)) return 0;
    vals[idx] = 1;
    return face_imax_taut(l, r, lvls, vals, n, idx + 1);
}

/* Check: imin(l,r) = i0 for all 2^n variable assignments. */
static int face_imin_contra(Val *l, Val *r,
                            int *lvls, int *vals, int n, int idx) {
    if (idx == n) {
        int lv = eval_face_bits(l, lvls, vals, n);
        int rv = eval_face_bits(r, lvls, vals, n);
        return lv == 0 || rv == 0;
    }
    vals[idx] = 0;
    if (!face_imin_contra(l, r, lvls, vals, n, idx + 1)) return 0;
    vals[idx] = 1;
    return face_imin_contra(l, r, lvls, vals, n, idx + 1);
}
Val *nbe_vimin(Arena *a, Val *l, Val *r) {
    if (l->tag == VL_NEUTRAL) {
        if (l->neutral.lvl == IZERO_CONST_LVL) return l;   /* i0 ∧ r = i0 */
        if (l->neutral.lvl == IONE_CONST_LVL)  return r;   /* i1 ∧ r = r  */
    }
    if (r->tag == VL_NEUTRAL) {
        if (r->neutral.lvl == IZERO_CONST_LVL) return r;   /* l ∧ i0 = i0 */
        if (r->neutral.lvl == IONE_CONST_LVL)  return l;   /* l ∧ i1 = l  */
    }
    /* x ∧ x = x (idempotency) */
    if (conv(a, 0, l, r)) return l;
    /* x ∧ (x ∨ y) = x  (absorption: meet absorbs join) */
    if (r->tag == VL_IMAX &&
        (conv(a, 0, r->pair.fst, l) || conv(a, 0, r->pair.snd, l))) return l;
    if (l->tag == VL_IMAX &&
        (conv(a, 0, l->pair.fst, r) || conv(a, 0, l->pair.snd, r))) return r;
    /* x ∧ ~x = i0 — compute ~l and ~r, compare structurally (not pointer-equal).
     * Needed because De Morgan rules eagerly reduce ~(l∨r) to ~l∧~r, so the
     * complement may no longer be a VL_INEG wrapper around the same pointer. */
    if (conv(a, 0, nbe_vineg(a, l), r)) return vl_neutral(a, IZERO_CONST_LVL, NULL);
    if (conv(a, 0, nbe_vineg(a, r), l)) return vl_neutral(a, IZERO_CONST_LVL, NULL);
    /* Full Boolean lattice check: enumerate all variable assignments. */
    {
        int lvls[MAX_FACE_VARS], vals[MAX_FACE_VARS], n = 0;
        n = collect_face_vars(l, lvls, n, MAX_FACE_VARS);
        n = collect_face_vars(r, lvls, n, MAX_FACE_VARS);
        if (n <= MAX_FACE_VARS && face_imin_contra(l, r, lvls, vals, n, 0))
            return vl_neutral(a, IZERO_CONST_LVL, NULL);
    }
    return vl_imin(a, l, r);
}

Val *nbe_vimax(Arena *a, Val *l, Val *r) {
    if (l->tag == VL_NEUTRAL) {
        if (l->neutral.lvl == IZERO_CONST_LVL) return r;   /* i0 ∨ r = r  */
        if (l->neutral.lvl == IONE_CONST_LVL)  return l;   /* i1 ∨ r = i1 */
    }
    if (r->tag == VL_NEUTRAL) {
        if (r->neutral.lvl == IZERO_CONST_LVL) return l;   /* l ∨ i0 = l  */
        if (r->neutral.lvl == IONE_CONST_LVL)  return r;   /* l ∨ i1 = i1 */
    }
    /* x ∨ x = x (idempotency) */
    if (conv(a, 0, l, r)) return l;
    /* x ∨ (x ∧ y) = x  (absorption: join absorbs meet) */
    if (r->tag == VL_IMIN &&
        (conv(a, 0, r->pair.fst, l) || conv(a, 0, r->pair.snd, l))) return l;
    if (l->tag == VL_IMIN &&
        (conv(a, 0, l->pair.fst, r) || conv(a, 0, l->pair.snd, r))) return r;
    /* x ∨ ~x = i1 — compute ~l and ~r, compare structurally (not pointer-equal). */
    if (conv(a, 0, nbe_vineg(a, l), r)) return vl_neutral(a, IONE_CONST_LVL, NULL);
    if (conv(a, 0, nbe_vineg(a, r), l)) return vl_neutral(a, IONE_CONST_LVL, NULL);
    /* Full Boolean lattice check: enumerate all variable assignments. */
    {
        int lvls[MAX_FACE_VARS], vals[MAX_FACE_VARS], n = 0;
        n = collect_face_vars(l, lvls, n, MAX_FACE_VARS);
        n = collect_face_vars(r, lvls, n, MAX_FACE_VARS);
        if (n <= MAX_FACE_VARS && face_imax_taut(l, r, lvls, vals, n, 0))
            return vl_neutral(a, IONE_CONST_LVL, NULL);
    }
    return vl_imax(a, l, r);
}

Val *nbe_vineg(Arena *a, Val *v) {
    if (v->tag == VL_NEUTRAL) {
        if (v->neutral.lvl == IZERO_CONST_LVL)
            return vl_neutral(a, IONE_CONST_LVL,  NULL);  /* ~i0 = i1 */
        if (v->neutral.lvl == IONE_CONST_LVL)
            return vl_neutral(a, IZERO_CONST_LVL, NULL);  /* ~i1 = i0 */
    }
    /* De Morgan: ~(l∧r) = ~l∨~r,  ~(l∨r) = ~l∧~r,  ~~x = x */
    if (v->tag == VL_IMIN)
        return nbe_vimax(a, nbe_vineg(a, v->pair.fst), nbe_vineg(a, v->pair.snd));
    if (v->tag == VL_IMAX)
        return nbe_vimin(a, nbe_vineg(a, v->pair.fst), nbe_vineg(a, v->pair.snd));
    if (v->tag == VL_INEG)
        return v->succ;  /* ~~x = x */
    return vl_ineg(a, v);
}

/* ── Level max (Phase M1)
 *
 * lmax : Level → Level → Level
 *   lmax lzero r         = r
 *   lmax l lzero         = l
 *   lmax (lsuc m) (lsuc n) = lsuc (lmax m n)
 *   lmax l r (neutral)   = VL_LMAX l r  (stuck)
 */
Val *nbe_vlmax(Arena *a, Val *l, Val *r) {
    if (l->tag == VL_LZERO) return r;
    if (r->tag == VL_LZERO) return l;
    if (l->tag == VL_LSUC && r->tag == VL_LSUC)
        return vl_lsuc(a, nbe_vlmax(a, l->succ, r->succ));
    return vl_lmax(a, l, r);
}

/* ── IsOne φ (Phase L2 Stage 7)
 *
 * IsOne : II → Type
 *   IsOne i0 = Empty,  IsOne i1 = Unit,  IsOne neutral = stuck VL_ISONE.
 * Compositional rules for imin/imax/ineg follow interval laws.
 */
Val *nbe_visone(Arena *a, Val *phi) {
    if (phi->tag == VL_NEUTRAL) {
        if (phi->neutral.lvl == IZERO_CONST_LVL) return vl_empty(a);
        if (phi->neutral.lvl == IONE_CONST_LVL)  return vl_unit(a);
    }
    /* imax φ ψ = i1 iff φ=i1 or ψ=i1 or ψ=~φ (x∨~x=i1) */
    if (phi->tag == VL_IMAX) {
        Val *l = phi->pair.fst, *r = phi->pair.snd;
        int l1 = (l->tag == VL_NEUTRAL && l->neutral.lvl == IONE_CONST_LVL);
        int r1 = (r->tag == VL_NEUTRAL && r->neutral.lvl == IONE_CONST_LVL);
        int l0 = (l->tag == VL_NEUTRAL && l->neutral.lvl == IZERO_CONST_LVL);
        int r0 = (r->tag == VL_NEUTRAL && r->neutral.lvl == IZERO_CONST_LVL);
        if (l1 || r1) return vl_unit(a);
        if (l0 && r0) return vl_empty(a);
        /* x ∨ ~x: complementation → always i1 */
        if ((r->tag == VL_INEG && r->succ == l) ||
            (l->tag == VL_INEG && l->succ == r)) return vl_unit(a);
    }
    /* imin φ ψ = i1 iff φ=i1 and ψ=i1; = i0 if either is i0 or ψ=~φ (x∧~x=i0) */
    if (phi->tag == VL_IMIN) {
        Val *l = phi->pair.fst, *r = phi->pair.snd;
        int l0 = (l->tag == VL_NEUTRAL && l->neutral.lvl == IZERO_CONST_LVL);
        int r0 = (r->tag == VL_NEUTRAL && r->neutral.lvl == IZERO_CONST_LVL);
        int l1 = (l->tag == VL_NEUTRAL && l->neutral.lvl == IONE_CONST_LVL);
        int r1 = (r->tag == VL_NEUTRAL && r->neutral.lvl == IONE_CONST_LVL);
        if (l0 || r0) return vl_empty(a);
        if (l1 && r1) return vl_unit(a);
        /* x ∧ ~x: complementation → always i0 */
        if ((r->tag == VL_INEG && r->succ == l) ||
            (l->tag == VL_INEG && l->succ == r)) return vl_empty(a);
    }
    /* ineg: IsOne(~i0) = Unit,  IsOne(~i1) = Empty */
    if (phi->tag == VL_INEG) {
        Val *v = phi->succ;
        if (v->tag == VL_NEUTRAL && v->neutral.lvl == IZERO_CONST_LVL) return vl_unit(a);
        if (v->tag == VL_NEUTRAL && v->neutral.lvl == IONE_CONST_LVL)  return vl_empty(a);
    }
    return vl_isone(a, phi);
}

/* ── primSub (PRIM-1, CCHM §5)
 *
 * primSub A φ u a : A
 *   φ = i1 (IsOne φ = Unit)  →  u star
 *   φ = i0 (IsOne φ = Empty) →  a
 *   neutral φ               →  VL_PRIMSUB stuck
 *
 * Uses nbe_visone for full lattice reduction (imax/imin/ineg concrete cases).
 */
Val *nbe_vprimsub(Arena *a, Val *ty, Val *phi, Val *u, Val *out) {
    Val *iso = nbe_visone(a, phi);
    if (iso->tag == VL_UNIT)  return nbe_vapp(a, u, vl_star(a));
    if (iso->tag == VL_EMPTY) return out;
    return vl_primsub(a, ty, phi, u, out);
}


/* ── Glue type former (Phase L2 Stage 5 / Stage 7d)
 *
 * Glue A φ T e : Type
 *   A=base type, φ:II face, T=fiber type, e:Equiv T A (homotopy equivalence).
 *   Equiv T A = Σ(fwd:T→A). Σ(inv:A→T). Σ(sect:Π(y:A).Path A (fwd(inv y)) y).
 *               Π(x:T). Path T (inv(fwd x)) x
 * β-rules: φ=i0 → A (base),  φ=i1 → T (fiber),  otherwise stuck VL_GLUE.
 */
Val *nbe_vglue_ty(Arena *a, Val *A, Val *phi, Val *T, Val *e) {
    if (phi->tag == VL_NEUTRAL) {
        if (phi->neutral.lvl == IZERO_CONST_LVL) return A;
        if (phi->neutral.lvl == IONE_CONST_LVL)  return T;
    }
    return vl_glue(a, A, phi, T, e);
}

/* ── Glue intro: glue φ t a (Phase L2 Stage 7d)
 *
 * glue φ t a : Glue A φ T e
 *   φ=i0 → a  (Glue A i0 T e = A)
 *   φ=i1 → t star  (Glue A i1 T e = T; t : Partial i1 T = Π(_:Unit).T)
 *   otherwise → stuck VL_GLUEELEM(φ, t, a)
 */
Val *nbe_vglueelem(Arena *a, Val *phi, Val *t, Val *base) {
    if (phi->tag == VL_NEUTRAL) {
        if (phi->neutral.lvl == IZERO_CONST_LVL) return base;
        if (phi->neutral.lvl == IONE_CONST_LVL)  return nbe_vapp(a, t, vl_star(a));
    }
    return vl_glueelem(a, phi, t, base);
}

/* ── Unglue elim: unglue φ e x (Phase L2 Stage 7d)
 *
 * unglue φ e x : A  where x : Glue A φ T e
 *   β: unglue _ e (glue _ t a) = a               (fires on VL_GLUEELEM)
 *   φ=i0 → x  (x : A already, Glue A i0 T e = A)
 *   φ=i1 → fst(e)(x)  (fst(e) : T→A, x : T)
 *   otherwise → stuck VL_UNGLUE(φ, e, x)
 *
 * Guard on e at i1: e must be VL_PAIR (concrete Equiv Σ-value) or VL_NEUTRAL
 * (stuck variable).  nbe_vfst/nbe_vsnd only handle these two tags — any other
 * (VL_LAM, VL_FIX, etc.) would crash.  In well-typed code, e : Equiv T A always
 * evaluates to VL_PAIR or VL_NEUTRAL; other tags indicate a type-checker bypass.
 */
Val *nbe_vunglue(Arena *a, Val *phi, Val *e, Val *x) {
    /* β-rule: unglue fires on any VL_GLUEELEM, regardless of face */
    if (x->tag == VL_GLUEELEM) return x->glue_elem_s.base;

    if (phi->tag == VL_NEUTRAL) {
        if (phi->neutral.lvl == IZERO_CONST_LVL)
            return x;  /* identity: Glue A i0 T e = A */
        if (phi->neutral.lvl == IONE_CONST_LVL) {
            if (e->tag == VL_PAIR || e->tag == VL_NEUTRAL)
                return nbe_vapp(a, nbe_vfst(a, e), x);
        }
    }
    return vl_unglue(a, phi, e, x);
}

/* Forward declaration for mutual recursion (nbe_vcomp calls nbe_vtransp which is defined later) */
Val *nbe_vcomp(Arena *a, Val *fam, Val *face, Val *tube, Val *base);

/* ── Homogeneous composition (Phase L2 Stage 4 + Stage 6 structural rules)
 *
 * hcomp A φ u base : A
 * β-rules: φ=i0 → base,  φ=i1 → u i1,  otherwise structural or stuck.
 *
 * Stage 6 — structural Π rule:
 *   hcomp (Π(x:A). B x) φ u base  =  λx. hcomp (B x) φ (λi. u i x) (base x)
 *
 * Requires: ty->tag == VL_PI (the composition type is a Pi type).
 * VL_PI is "applied" via nbe_vapp (which evaluates the codomain at a given x —
 * see the VL_PI case added to nbe_vapp).
 *
 * The result VL_LAM has env=[phi, tube, base, ty].
 * In env [x(0), phi(1), tube(2), base(3), ty(4)] after the outer λ fires:
 *   B x  = TM_APP(VAR(4), VAR(0))         — ty applied to x via VL_PI codomain rule
 *   φ    = TM_VAR(1)
 *   λi. u i x: inner body in env [i(0), x(1), phi(2), tube(3), base(4), ty(5)]:
 *           = TM_APP(TM_APP(VAR(3), VAR(0)), VAR(1)) = tube i x
 *   base x = TM_APP(VAR(3), VAR(0))
 */
Val *nbe_vhcomp(Arena *a, Val *ty, Val *face, Val *tube, Val *base) {
    if (face->tag == VL_NEUTRAL) {
        if (face->neutral.lvl == IZERO_CONST_LVL) return base;
        if (face->neutral.lvl == IONE_CONST_LVL)
            return nbe_vapp(a, tube, face);  /* tube i1 */
    }
    /* Stage 6: structural Π rule */
    if (ty->tag == VL_PI) {
        Term *tube_body = tm_app(a, tm_app(a, tm_var(a, 3), tm_var(a, 0)), tm_var(a, 1));
        Term *body      = tm_hcomp(a,
                              tm_app(a, tm_var(a, 4), tm_var(a, 0)),
                              tm_var(a, 1),
                              tm_lam(a, "i", tube_body),
                              tm_app(a, tm_var(a, 3), tm_var(a, 0)));
        Env *env = env_cons(a, face, env_cons(a, tube, env_cons(a, base, env_cons(a, ty, NULL))));
        return vl_lam(a, "x", env, body);
    }

    /* Stage 7b: structural Σ rule
     *   hcomp (Σ(x:A). B x) φ u base = (a', b')
     *   a' = hcomp A φ (λi. fst(u i)) (fst base)
     *   b' = hcomp B_val φ (λi. snd(u i)) (snd base)    [when B-family is constant]
     *
     * B-family constancy: probe path_j = hcomp A (imin φ (ineg j)) fst_tube fst_base
     * at j = TRANSP_PROBE_LVL.  If B(path_probe) doesn't mention the probe variable,
     * B is constant along the hcomp path (covers constant B and trivial-A-path cases).
     *
     * Synthetic tubes work for any tube tag (VL_LAM / VL_NEUTRAL / VL_FIX):
     *   env = [tube];  body = FST/SND(APP(VAR(1), VAR(0)))
     *   VAR(0) = i (binder),  VAR(1) = tube (from env).
     */
    if (ty->tag == VL_SIGMA) {
        /* Build synthetic fst/snd tubes */
        Env  *tube_env = env_cons(a, tube, NULL);
        Term *app_ui   = tm_app(a, tm_var(a, 1), tm_var(a, 0)); /* tube(i) */
        Val  *fst_tube = vl_lam(a, "i", tube_env, tm_fst(a, app_ui));
        Val  *snd_tube = vl_lam(a, "i", tube_env, tm_snd(a, app_ui));

        Val *dom_v    = ty->pi.dom;
        Val *fst_base = nbe_vfst(a, base);
        Val *snd_base = nbe_vsnd(a, base);

        /* Probe B-family constancy: does B vary along the hcomp path in A? */
        Val  *probe_i    = vl_neutral(a, TRANSP_PROBE_LVL, NULL);
        Val  *probe_face = nbe_vimin(a, face, nbe_vineg(a, probe_i));
        Val  *probe_path = nbe_vhcomp(a, dom_v, probe_face, fst_tube, fst_base);
        Val  *probe_B    = nbe_eval(a, env_cons(a, probe_path, ty->pi.env), ty->pi.cod);
        Term *probe_B_q  = nbe_quote(a, TRANSP_PROBE_LVL + 1, probe_B);
        if (term_mentions_var(probe_B_q, 0))
            return vl_hcomp(a, ty, face, tube, base);  /* dependent B — stay stuck */

        /* Constant B-family: both components reduce */
        Val *a_prime = nbe_vhcomp(a, dom_v, face, fst_tube, fst_base);
        Val *B_val   = nbe_eval(a, env_cons(a, fst_base, ty->pi.env), ty->pi.cod);
        Val *b_prime = nbe_vhcomp(a, B_val, face, snd_tube, snd_base);
        return vl_pair(a, a_prime, b_prime);
    }

    /* Stage 7c: structural Path rule
     *   hcomp (Path A a b) φ u base = ⟨j⟩ hcomp A (imax φ (∂j)) (λi. u i @ j) (base @ j)
     *   where ∂j = imax j (ineg j).
     *
     * VL_PATHABS env = [φ, A, lhs, rhs, tube, base].
     * After ⟨j⟩ fires, eval env = [j(0), φ(1), A(2), lhs(3), rhs(4), tube(5), base(6)].
     *
     * Outer body term references:
     *   VAR(0)=j  VAR(1)=φ  VAR(2)=A  VAR(5)=tube  VAR(6)=base
     *
     * Inner λi fires in env [i(0), j(1), φ(2), A(3), lhs(4), rhs(5), tube(6), base(7)]:
     *   inner body = TM_PATHAPP(TM_APP(VAR(6), VAR(0)), VAR(1))  →  (tube i) @ j
     *
     * The rule always fires for Path types with neutral face (no constancy probe needed
     * — Path A a b doesn't have a varying codomain the way Σ does).
     */
    if (ty->tag == VL_PATH) {
        /* ∂ j = imax j (ineg j) */
        Term *del_j  = tm_imax(a, tm_var(a, 0), tm_ineg(a, tm_var(a, 0)));
        /* imax φ (∂ j) */
        Term *face_j = tm_imax(a, tm_var(a, 1), del_j);
        /* inner tube body: (tube i) @ j
         * in env [i(0), j(1), ..., tube(6), base(7)] */
        Term *inner  = tm_pathapp(a, tm_app(a, tm_var(a, 6), tm_var(a, 0)), tm_var(a, 1));
        /* outer body: hcomp A (imax φ (∂j)) (λi. tube i @ j) (base @ j)
         * in env [j(0), φ(1), A(2), ..., tube(5), base(6)] */
        Term *body   = tm_hcomp(a,
                           tm_var(a, 2),                               /* A */
                           face_j,
                           tm_lam(a, "i", inner),
                           tm_pathapp(a, tm_var(a, 6), tm_var(a, 0))); /* base @ j */
        Env *penv = env_cons(a, face,
                    env_cons(a, ty->id.ty,
                    env_cons(a, ty->id.lhs,
                    env_cons(a, ty->id.rhs,
                    env_cons(a, tube,
                    env_cons(a, base, NULL))))));
        return vl_pathabs(a, "j", penv, body);
    }

    /* PathP structural rule (heterogeneous paths):
     *   hcomp (PathP fam a b) φ u base = ⟨j⟩ hcomp (fam j) (imax φ (∂j)) (λi. u i @ j) (base @ j)
     *
     * VL_PATHABS env = [φ, fam, lhs, rhs, tube, base].
     * After ⟨j⟩ fires, env = [j(0), φ(1), fam(2), lhs(3), rhs(4), tube(5), base(6)].
     * Inner λi: [i(0), j(1), φ(2), fam(3), ..., tube(6), base(7)].
     *   fam j  = APP(VAR(2), VAR(0))   in outer body
     *   inner  = PATHAPP(APP(VAR(6), VAR(0)), VAR(1))  same as Path rule
     */
    if (ty->tag == VL_PATHP) {
        Term *del_j  = tm_imax(a, tm_var(a, 0), tm_ineg(a, tm_var(a, 0)));
        Term *face_j = tm_imax(a, tm_var(a, 1), del_j);
        Term *inner  = tm_pathapp(a, tm_app(a, tm_var(a, 6), tm_var(a, 0)), tm_var(a, 1));
        Term *fam_j  = tm_app(a, tm_var(a, 2), tm_var(a, 0));   /* fam j */
        Term *body   = tm_hcomp(a,
                           fam_j,
                           face_j,
                           tm_lam(a, "i", inner),
                           tm_pathapp(a, tm_var(a, 6), tm_var(a, 0)));
        Env *penv = env_cons(a, face,
                    env_cons(a, ty->id.ty,              /* fam */
                    env_cons(a, ty->id.lhs,
                    env_cons(a, ty->id.rhs,
                    env_cons(a, tube,
                    env_cons(a, base, NULL))))));
        return vl_pathabs(a, "j", penv, body);
    }

    /* Stage 7d Phase C: hcomp-Glue structural rule
     *
     *   hcomp (Glue A φ T e) ψ u base =
     *     glue φ [φ ↦ λ_. e.inv(a')] a'
     *   where a' = hcomp A ψ (λi. unglue φ e (u i)) (unglue φ e base)
     *
     * Derivation:
     *   1. Project each tube element and base to A via unglue.
     *   2. Compose the A-projections with hcomp A.
     *   3. Re-glue: the A-result a' plus the T-component e.inv(a') (trusted coherent
     *      via e.sect: e.fwd(e.inv(a')) ≡ a').
     *
     * Guard: e must be VL_PAIR or VL_NEUTRAL — nbe_vfst/nbe_vsnd only handle
     * these two tags (both crash on VL_FIX, VL_LAM, etc.).  For other tags
     * (type-checker bypass), stays stuck as VL_HCOMP.
     *
     * Synthetic unglue tube env layout (λi body):
     *   utube_env = [tube, e_val, phi]  →  VAR(0)=tube, VAR(1)=e_val, VAR(2)=phi
     *   After λi fires: [i(0), tube(1), e_val(2), phi(3)]
     *   body: TM_UNGLUE(VAR(3), VAR(2), APP(VAR(1),VAR(0)))  →  unglue phi e (tube i)
     *
     * Partial element λ(_:IsOne φ). t_prime:
     *   Constant-Pi trick: env=[t_prime], body=VAR(1).
     *   When applied: env=[arg, t_prime], VAR(1)=t_prime.
     *
     * Limitation: the result at neutral ψ is VL_GLUEELEM (re-glued form). The
     * endpoint equations hcomp...i0 = base and hcomp...i1 = u(i1) hold definitionally
     * (β fires before this rule), but the equation for neutral ψ holds only up to
     * Glue-η (the uniqueness law for glue elements), which is not yet enforced.
     */
    if (ty->tag == VL_GLUE) {
        Val *A_val = ty->glue_s.base;
        Val *phi   = ty->glue_s.face;
        Val *e_val = ty->glue_s.equiv;
        if (e_val->tag != VL_PAIR && e_val->tag != VL_NEUTRAL)
            return vl_hcomp(a, ty, face, tube, base);

        /* Synthetic unglue tube: λi. unglue φ e_val (tube i) */
        Env  *utube_env  = env_cons(a, tube,
                           env_cons(a, e_val,
                           env_cons(a, phi, NULL)));
        Term *app_ui     = tm_app(a, tm_var(a, 1), tm_var(a, 0));
        Term *unglue_bdy = tm_unglue(a, tm_var(a, 3), tm_var(a, 2), app_ui);
        Val  *unglue_tube = vl_lam(a, "i", utube_env, unglue_bdy);

        Val *unglue_base = nbe_vunglue(a, phi, e_val, base);
        Val *a_prime     = nbe_vhcomp(a, A_val, face, unglue_tube, unglue_base);

        Val *e_inv   = nbe_vfst(a, nbe_vsnd(a, e_val));
        Val *t_prime = nbe_vapp(a, e_inv, a_prime);

        Val *partial = vl_lam(a, "_", env_cons(a, t_prime, NULL), tm_var(a, 1));
        return nbe_vglueelem(a, phi, partial, a_prime);
    }

    return vl_hcomp(a, ty, face, tube, base);
}

/* ── Heterogeneous composition (Phase L2 comp primitive)
 *
 * comp (λi. A i) φ u base : A i1
 *
 * Reduction rules:
 *   φ = i1 → u i1                             (tube covers everything)
 *   φ = i0 → transp (λi. A i) base            (no tube constraint: pure transport)
 *   Constant family → hcomp (A i1) φ u base   (degenerate: no transport needed)
 *   Π family (constant domain, closed) → λx. comp (λi.B i x) φ (λi.u i x) (base x)
 *   Σ family (constant domain and B, closed) → (comp A-fam φ fst-tube fst-base,
 *                                                hcomp B φ snd-tube snd-base)
 *   Path family (closed) → ⟨j⟩ comp (λi.A i) (imax φ (∂j)) (λi.u i @ j) (base @ j)
 *   Otherwise → VL_COMP(fam, φ, u, base) stuck
 */
Val *nbe_vcomp(Arena *a, Val *fam, Val *face, Val *tube, Val *base) {
    /* β-rules at interval endpoints */
    if (face->tag == VL_NEUTRAL) {
        if (face->neutral.lvl == IONE_CONST_LVL)
            return nbe_vapp(a, tube, face);          /* u i1 */
        if (face->neutral.lvl == IZERO_CONST_LVL)
            return nbe_vtransp(a, fam, base);        /* pure transport */
    }

    /* Must be a LAM/PATHABS family to proceed */
    if (fam->tag != VL_LAM && fam->tag != VL_PATHABS)
        return vl_comp(a, fam, face, tube, base);

    /* Probe family at TRANSP_PROBE_LVL */
    Val *i_probe = vl_neutral(a, TRANSP_PROBE_LVL, NULL);
    Val *a_i     = nbe_vapp(a, fam, i_probe);
    Term *a_i_q  = nbe_quote(a, TRANSP_PROBE_LVL + 1, a_i);

    /* Constant family: comp = hcomp at i1 fiber */
    if (!term_mentions_var(a_i_q, 0)) {
        Val *i1v = vl_neutral(a, IONE_CONST_LVL, NULL);
        return nbe_vhcomp(a, nbe_vapp(a, fam, i1v), face, tube, base);
    }

    /* Structural Π rule — constant domain, closed family.
     *
     *   comp (λi. Π(x:A). B i x) φ u f  =  λx. comp (λi. B i x) φ (λi. u i x) (f x)
     */
    if (a_i->tag == VL_PI &&
        fam->lam.env == NULL &&
        (fam->tag == VL_LAM || fam->tag == VL_PATHABS) &&
        fam->lam.body->tag == TM_PI)
    {
        Term *dom_q = nbe_quote(a, TRANSP_PROBE_LVL + 1, a_i->pi.dom);
        if (!term_mentions_var(dom_q, 0)) {
            Term *inner_fam  = tm_lam(a, "i",
                                  tm_app(a, tm_app(a, tm_var(a, 5), tm_var(a, 0)),
                                             tm_var(a, 1)));
            Term *inner_tube = tm_lam(a, "i",
                                  tm_app(a, tm_app(a, tm_var(a, 3), tm_var(a, 0)),
                                             tm_var(a, 1)));
            Term *body = tm_comp(a, inner_fam, tm_var(a, 1), inner_tube,
                                 tm_app(a, tm_var(a, 3), tm_var(a, 0)));
            Env *env = env_cons(a, face,
                       env_cons(a, tube,
                       env_cons(a, base,
                       env_cons(a, fam, NULL))));
            return vl_lam(a, "x", env, body);
        }
    }

    /* Structural Σ rule — constant domain and constant B-family, closed family.
     *
     *   comp (λi. Σ(x:A i). B) φ u p  =  (a', b')
     *   a' = comp (λi. A i) φ (λi. fst(u i)) (fst p)
     *   b' = hcomp B φ (λi. snd(u i)) (snd p)     [B is constant]
     */
    if (a_i->tag == VL_SIGMA &&
        fam->lam.env == NULL &&
        (fam->tag == VL_LAM || fam->tag == VL_PATHABS) &&
        fam->lam.body->tag == TM_SIG &&
        (base->tag == VL_PAIR || base->tag == VL_NEUTRAL))
    {
        /* Build synthetic fst/snd tubes */
        Env  *tube_env = env_cons(a, tube, NULL);
        Term *app_ui   = tm_app(a, tm_var(a, 1), tm_var(a, 0));
        Val  *fst_tube = vl_lam(a, "i", tube_env, tm_fst(a, app_ui));
        Val  *snd_tube = vl_lam(a, "i", tube_env, tm_snd(a, app_ui));
        Val  *fst_base = nbe_vfst(a, base);
        Val  *snd_base = nbe_vsnd(a, base);

        /* A-subfamily: λi. A i  (domain part of fam) */
        Val *A_fam = vl_lam(a, "i", NULL, fam->lam.body->pi.dom);

        /* Probe B-family constancy along the comp path in A */
        Val  *probe_i    = vl_neutral(a, TRANSP_PROBE_LVL, NULL);
        Val  *probe_face = nbe_vimin(a, face, nbe_vineg(a, probe_i));
        Val  *probe_a    = nbe_vcomp(a, A_fam, probe_face, fst_tube, fst_base);
        Val  *probe_B    = nbe_eval(a, env_cons(a, probe_a, a_i->pi.env), a_i->pi.cod);
        Term *probe_B_q  = nbe_quote(a, TRANSP_PROBE_LVL + 1, probe_B);
        if (term_mentions_var(probe_B_q, 0))
            return vl_comp(a, fam, face, tube, base);  /* dependent B: stuck */

        Val *a_prime = nbe_vcomp(a, A_fam, face, fst_tube, fst_base);
        Val *B_val   = nbe_eval(a, env_cons(a, fst_base, a_i->pi.env), a_i->pi.cod);
        Val *b_prime = nbe_vhcomp(a, B_val, face, snd_tube, snd_base);
        return vl_pair(a, a_prime, b_prime);
    }

    /* Structural Path rule — closed family.
     *
     *   comp (λi. Path (A i) (a i) (b i)) φ u p₀
     *     = ⟨j⟩ comp (λi. A i) (imax φ (∂j)) (λi. u i @ j) (p₀ @ j)
     */
    if (a_i->tag == VL_PATH &&
        fam->lam.env == NULL &&
        (fam->tag == VL_LAM || fam->tag == VL_PATHABS) &&
        fam->lam.body->tag == TM_PATH &&
        (base->tag == VL_PATHABS || base->tag == VL_NEUTRAL || base->tag == VL_REFL))
    {
        /* A-subfamily from the Path's type field */
        Val *A_fam = vl_lam(a, "i", NULL, fam->lam.body->id.ty);

        Term *del_j  = tm_imax(a, tm_var(a, 0), tm_ineg(a, tm_var(a, 0)));
        Term *face_j = tm_imax(a, tm_var(a, 1), del_j);
        Term *inner  = tm_pathapp(a, tm_app(a, tm_var(a, 6), tm_var(a, 0)), tm_var(a, 1));
        Term *body   = tm_comp(a,
                           tm_var(a, 2),              /* A_fam */
                           face_j,
                           tm_lam(a, "i", inner),
                           tm_pathapp(a, tm_var(a, 6), tm_var(a, 0)));
        Env *penv = env_cons(a, face,
                    env_cons(a, A_fam,
                    env_cons(a, a_i->id.lhs,
                    env_cons(a, a_i->id.rhs,
                    env_cons(a, tube,
                    env_cons(a, base, NULL))))));
        return vl_pathabs(a, "j", penv, body);
    }

    /* Structural PathP rule — closed family.
     *
     *   comp (λi. PathP (F i) (a i) (b i)) φ u p₀
     *     = ⟨j⟩ comp (λi. F i j) (imax φ (∂j)) (λi. u i @ j) (p₀ @ j)
     *
     * F_tm = fam->lam.body->id.ty  (term: F i, dB0=i, closed env)
     *
     * penv = [face, tube, base]
     * After j fires: [j(0), face(1), tube(2), base(3)]
     * Inner λi:      [i(0), j(1),    face(2), tube(3), base(4)]
     *
     *   inner_fam body: APP(F_tm, VAR(1))        F_tm sees dB0=i, VAR(1)=j → F i j
     *   face_j:         imax(VAR(1), ∂VAR(0))    imax(φ, ∂j)
     *   tube_body:      pathapp(app(VAR(3), VAR(0)), VAR(1))   (tube i) @ j
     *   base_app:       pathapp(VAR(3), VAR(0))   base @ j
     */
    /* Peel TM_ANN from fam body (handles (\i. (PathP ... : Type)) annotation). */
    Term *cpp_body = (fam->tag == VL_LAM || fam->tag == VL_PATHABS)
                     ? fam->lam.body : NULL;
    if (cpp_body && cpp_body->tag == TM_ANN && cpp_body->ann.term->tag == TM_PATHP)
        cpp_body = cpp_body->ann.term;

    if (a_i->tag == VL_PATHP &&
        (fam->tag == VL_LAM || fam->tag == VL_PATHABS) &&
        fam->lam.env == NULL &&
        cpp_body && cpp_body->tag == TM_PATHP &&
        (base->tag == VL_PATHABS || base->tag == VL_NEUTRAL || base->tag == VL_REFL))
    {
        Term *F_tm      = cpp_body->id.ty;
        Term *del_j     = tm_imax(a, tm_var(a, 0), tm_ineg(a, tm_var(a, 0)));
        Term *face_j    = tm_imax(a, tm_var(a, 1), del_j);
        Term *inner_fam = tm_lam(a, "i", tm_app(a, F_tm, tm_var(a, 1)));
        Term *tube_body = tm_pathapp(a,
                              tm_app(a, tm_var(a, 3), tm_var(a, 0)),
                              tm_var(a, 1));
        Term *base_app  = tm_pathapp(a, tm_var(a, 3), tm_var(a, 0));
        Term *body = tm_comp(a,
                         inner_fam,
                         face_j,
                         tm_lam(a, "i", tube_body),
                         base_app);
        Env *penv = env_cons(a, face,
                    env_cons(a, tube,
                    env_cons(a, base, NULL)));
        return vl_pathabs(a, "j", penv, body);
    }

    return vl_comp(a, fam, face, tube, base);
}

/* ── fill (Phase L2 — comp at variable interval point)
 *
 * fill fam φ u base i : fam i
 *
 * Definitionally:
 *   fill fam φ u base i = comp (λj. fam(imin i j)) (imax φ (~i)) (λj. u(imin i j)) base
 *
 * Always reduces — no VL_FILL; result is whatever nbe_vcomp produces.
 *
 * De Bruijn layout for the two inner lambdas (env = [outer_val, idx]):
 *   after applying to j: VAR(0)=j, VAR(1)=outer_val, VAR(2)=idx
 *   body = APP(VAR(1), IMIN(VAR(2), VAR(0)))
 */
Val *nbe_vfill(Arena *a, Val *fam, Val *face, Val *tube, Val *base, Val *idx) {
    /* CCHM spec: fill fam φ u base i0 = base (even for incoherent tubes). */
    if (idx->tag == VL_NEUTRAL && idx->neutral.lvl == IZERO_CONST_LVL) return base;
    /* λj. fam(imin idx j) */
    Term *inner_body = tm_app(a, tm_var(a, 1), tm_imin(a, tm_var(a, 2), tm_var(a, 0)));
    Val  *fam_lam    = vl_lam(a, "j", env_cons(a, fam,  env_cons(a, idx, NULL)), inner_body);
    /* imax φ (~idx) */
    Val  *face_r     = nbe_vimax(a, face, nbe_vineg(a, idx));
    /* λj. u(imin idx j) — same body, different outer_val */
    Val  *tube_lam   = vl_lam(a, "j", env_cons(a, tube, env_cons(a, idx, NULL)), inner_body);
    return nbe_vcomp(a, fam_lam, face_r, tube_lam, base);
}

/* ── Transport (Phase L2 Stage 3 + Stage 4 structural rules)
 *
 * transp A_fun x : A_fun i1
 *
 * Stage 3: constant family → x.
 * Stage 4: Π/Σ with constant domain (closed family only):
 *   transp (λi. Π(x:A). B i x) f  =  λx. transp (λi. B i x) (f x)
 *   transp (λi. Σ(x:A). B i x) p  =  (fst p, transp (λi. B i (fst p)) (snd p))
 * Stage 5a: Glue (closed family only):
 *   transp (λi. Glue A i T e) x    =  e (transp (λi. T) x)
 * Stage 5b: ua computation:
 *   transp (λi. ua f @ i) x        =  f x
 * Otherwise stays stuck as VL_TRANSP(A_fun, x).
 *
 * "Closed family" means a_fun->lam.env == NULL.
 * Non-closed families remain stuck (quoting outer neutrals would produce
 * stale de Bruijn indices).
 */
static Term *quote(Arena *a, int depth, Val *v);  /* forward decl */

Val *nbe_vtransp(Arena *a, Val *a_fun, Val *x) {
    Val *i_probe = vl_neutral(a, TRANSP_PROBE_LVL, NULL);
    Val *a_i;
    if (a_fun->tag == VL_LAM)
        a_i = nbe_vapp(a, a_fun, i_probe);
    else if (a_fun->tag == VL_PATHABS)
        a_i = nbe_vpathapp(a, a_fun, i_probe);
    else
        return vl_transp(a, a_fun, x);

    /* Quote at PROBE+1 so the probe appears as de Bruijn var 0. */
    Term *a_i_q = quote(a, TRANSP_PROBE_LVL + 1, a_i);
    if (!term_mentions_var(a_i_q, 0))
        return x;  /* constant family: transp (λ_. B) x = x */

    /* Stage 4: structural Π rule (constant domain, closed family).
     *
     * Requires: a_fun is a closed LAM/PATHABS whose body is TM_PI with a
     * domain that does not mention i (= the probe variable after quoting).
     *
     * The result is:  λ(x:A). transp (λi. B i x) (elem x)
     * built as VL_LAM with env=[a_fun, elem] and synthetic body:
     *   TM_TRANSP( TM_LAM("i", APP(LAM("_x", cod_tm), VAR 1)),
     *              TM_APP(VAR 2, VAR 0) )
     * In env=[x(0), a_fun(1), elem(2)] after the outer λ fires:
     *   VAR 0=x, VAR 1=a_fun, VAR 2=elem; the inner LAM swaps the de Bruijn
     *   indices so that cod_tm sees [x(0), i(1),...] as expected.
     *
     * Closed-family check guarantees cod_tm references only VAR 0 (x) and
     * VAR 1 (i), so the duplicate at VAR 2+ does not matter.
     */
    if (a_i->tag == VL_PI &&
        a_fun->lam.env == NULL &&
        (a_fun->tag == VL_LAM || a_fun->tag == VL_PATHABS) &&
        a_fun->lam.body->tag == TM_PI)
    {
        /* Check domain is constant in i. */
        Term *dom_q = quote(a, TRANSP_PROBE_LVL + 1, a_i->pi.dom);
        if (!term_mentions_var(dom_q, 0)) {
            Term *cod_tm = a_fun->lam.body->pi.cod;
            /* inner family body: in env [i(0), x(1), ...], gives B i x
             * via APP(LAM("_x", cod_tm), VAR 1) which evaluates cod_tm with
             * x at index 0 and i at index 1 (swapping 0↔1 effectively). */
            Term *inner = tm_app(a, tm_lam(a, "_x", cod_tm), tm_var(a, 1));
            Term *fam   = tm_lam(a, "i", inner);
            Term *elmt  = tm_app(a, tm_var(a, 2), tm_var(a, 0));
            Term *body  = tm_transp(a, fam, elmt);
            /* env=[a_fun(0), elem(1)]; when x prepended: [x(0), a_fun(1), elem(2)] */
            Env  *env   = env_cons(a, a_fun, env_cons(a, x, NULL));
            return vl_lam(a, "x", env, body);
        }
    }

    /* Stage 4: structural Σ rule (constant domain, closed family).
     *
     * transp (λi. Σ(x:A). B i x) p  =  (fst p, transp (λi. B i (fst p)) (snd p))
     *
     * The inner family uses the same closed-env trick as the Π case.
     */
    if (a_i->tag == VL_SIGMA &&
        a_fun->lam.env == NULL &&
        (a_fun->tag == VL_LAM || a_fun->tag == VL_PATHABS) &&
        a_fun->lam.body->tag == TM_SIG &&
        (x->tag == VL_PAIR || x->tag == VL_NEUTRAL))  /* guard: vfst/vsnd only work on these */
    {
        Term *dom_q = quote(a, TRANSP_PROBE_LVL + 1, a_i->pi.dom);
        if (!term_mentions_var(dom_q, 0)) {
            Val  *fst_p  = nbe_vfst(a, x);
            Val  *snd_p  = nbe_vsnd(a, x);
            Term *cod_tm = a_fun->lam.body->pi.cod;
            /* inner family for snd: in env [i(0), fst_p(1), ...] gives B i (fst p) */
            Term *inner  = tm_app(a, tm_lam(a, "_x", cod_tm), tm_var(a, 1));
            /* Build VL_LAM for the family applied at fst_p directly. */
            Env  *env_f  = env_cons(a, fst_p, NULL);
            Val  *family = vl_lam(a, "i", env_f, inner);
            Val  *snd_v  = nbe_vtransp(a, family, snd_p);
            return vl_pair(a, fst_p, snd_v);
        }
    }

    /* PRIM-1: transp-PathP structural rule (closed family).
     *
     *   transp (λi. PathP (F i) (α i) (β i)) p
     *     = ⟨j⟩ comp (λi. F i j) (∂j) (λi. primSub (F i j) (~j) (λ_. α i) (β i)) (p @ j)
     *
     * where ∂j = imax j (~j).
     *
     * F_tm = fam->lam.body->id.ty   (closed: VAR(0)=i)
     * a_tm = fam->lam.body->id.lhs  (α; closed: VAR(0)=i)
     * b_tm = fam->lam.body->id.rhs  (β; closed: VAR(0)=i)
     *
     * penv = [x]; after j fires: [j(0), x(1)].
     *
     * inner_fam body (context [i(0), j(1), x(2)]):
     *   APP(F_tm, VAR(1))  →  F(VAR(0)=i) applied to VAR(1)=j  →  F i j
     *
     * tube_body (context [i(0), j(1), x(2)]):
     *   primSub (F i j)
     *           (ineg j = ineg VAR(1))
     *           (λ_. APP(LAM("_x", a_tm), VAR(1)))   : λ_. α i
     *           b_tm                                  : β i
     *
     * base_app (context [j(0), x(1)]): pathapp(VAR(1), VAR(0)) = p @ j
     *
     * Endpoint check (j=i0):
     *   ∂(i0)=i1, comp returns tube(i=i1):
     *     primSub _ (ineg i0=i1) _ _ = u(star) = α(i1) = α 1  ✓
     * Endpoint check (j=i1):
     *   ∂(i1)=i1, comp returns tube(i=i1):
     *     primSub _ (ineg i1=i0) _ (β i1) = β 1               ✓
     *
     * Guard: x must be VL_PATHABS/VL_NEUTRAL/VL_REFL (path-like).
     * TM_ANN peeling: (\i. (PathP ... : Type)) has body TM_ANN(TM_PATHP,...);
     * strip the annotation to reach TM_PATHP (same as comp-PathP limitation fix).
     */
    /* Peel TM_ANN wrapper from fam body to reach TM_PATHP, if present. */
    Term *pathp_body = (a_fun->tag == VL_LAM || a_fun->tag == VL_PATHABS)
                       ? a_fun->lam.body : NULL;
    if (pathp_body && pathp_body->tag == TM_ANN
                   && pathp_body->ann.term->tag == TM_PATHP)
        pathp_body = pathp_body->ann.term;

    if (a_i->tag == VL_PATHP &&
        a_fun->lam.env == NULL &&
        pathp_body && pathp_body->tag == TM_PATHP &&
        (x->tag == VL_PATHABS || x->tag == VL_NEUTRAL || x->tag == VL_REFL))
    {
        Term *F_tm = pathp_body->id.ty;
        Term *a_tm = pathp_body->id.lhs;  /* α */
        Term *b_tm = pathp_body->id.rhs;  /* β */

        /* inner_fam = λi. F i j  (in context [i(0), j(1), x(2)]) */
        Term *inner_fam = tm_lam(a, "i", tm_app(a, F_tm, tm_var(a, 1)));

        /* ∂j = imax(j, ~j)  (in context [j(0), x(1)]) */
        Term *del_j = tm_imax(a, tm_var(a, 0), tm_ineg(a, tm_var(a, 0)));

        /* u_lam = λ_. α i
         * In context [_(0), i(1), j(2), x(3)] after the λ_ fires:
         *   APP(LAM("_x", a_tm), VAR(1)) → α_tm[_x=i] = α i  */
        Term *u_lam = tm_lam(a, "_",
                         tm_app(a, tm_lam(a, "_x", a_tm), tm_var(a, 1)));

        /* tube_body = primSub (F i j) (ineg j) (λ_. α i) (β i)
         * In context [i(0), j(1), x(2)]:
         *   F i j  = APP(F_tm, VAR(1))
         *   ineg j = ineg(VAR(1))
         *   u      = u_lam  (λ_. α i, built above)
         *   out    = b_tm   (β i; VAR(0)=i ✓) */
        Term *tube_body = tm_primsub(a,
                              tm_app(a, F_tm, tm_var(a, 1)),
                              tm_ineg(a, tm_var(a, 1)),
                              u_lam,
                              b_tm);
        Term *tube_lam = tm_lam(a, "i", tube_body);

        /* base_app = p @ j  (in context [j(0), x(1)]) */
        Term *base_app = tm_pathapp(a, tm_var(a, 1), tm_var(a, 0));

        /* body = comp (λi. F i j) (∂j) tube_lam (p @ j) */
        Term *body = tm_comp(a, inner_fam, del_j, tube_lam, base_app);

        Env *penv = env_cons(a, x, NULL);
        return vl_pathabs(a, "j", penv, body);
    }

    /* Stage 5 / Stage 7d: Glue-transp rule (closed family only).
     *
     * When the probed type is VL_GLUE(A, probe, T, e) (face = probe variable):
     *   transp (λi. Glue A i T e) x = e.inv (transp (λi. T) x)
     *
     * e : Equiv T A = Σ(fwd:T→A). Σ(inv:A→T). sect. retr
     * We extract inv = fst(snd e) : A → T and apply it to the inner transport.
     * For constant T the inner transp reduces to x, so the result is e.inv x.
     *
     * "Closed family" guard (a_fun->lam.env == NULL) matches the Π/Σ rules:
     * non-closed families are left stuck to avoid quoting outer neutrals at
     * TRANSP_PROBE_LVL which produces stale de Bruijn indices.
     *
     * Guard on e_val: only fire if e is a VL_PAIR or VL_NEUTRAL (the two
     * tags nbe_vsnd handles).  Any other tag (e.g. VL_LAM from untyped code
     * that bypasses the type checker) leaves the result stuck rather than
     * crashing with "vsnd: not a pair".
     */
    if (a_i->tag == VL_GLUE &&
        a_fun->lam.env == NULL &&
        (a_fun->tag == VL_LAM || a_fun->tag == VL_PATHABS))
    {
        Val *phi = a_i->glue_s.face;
        if (phi->tag == VL_NEUTRAL && phi->neutral.lvl == TRANSP_PROBE_LVL) {
            Val  *T_val  = a_i->glue_s.fiber;
            Val  *e_val  = a_i->glue_s.equiv;
            if (e_val->tag == VL_PAIR || e_val->tag == VL_NEUTRAL) {
                Term *T_q    = quote(a, TRANSP_PROBE_LVL + 1, T_val);
                Val  *T_famv = nbe_eval(a, NULL, tm_lam(a, "i", T_q));
                Val  *inner  = nbe_vtransp(a, T_famv, x);
                Val  *e_inv  = nbe_vfst(a, nbe_vsnd(a, e_val));
                return nbe_vapp(a, e_inv, inner);
            }
        }
    }

    /* Stage 5: ua computation rule.
     *
     * transp (λi. ua f @ i) x = f x
     *
     * At probe level the family evaluates to the neutral:
     *   neutral(UA_CONST_LVL,  SP_PATHAPP(probe) → SP_APP(f) → NULL)
     * We pattern-match this spine to extract f.
     *
     * Safety guard: only fire when f is function-like (VL_LAM / VL_PATHABS /
     * VL_NEUTRAL / VL_FIX).  Any other tag (e.g. VL_PAIR from an ill-typed
     * single-arg ua) would crash nbe_vapp; fall through to VL_TRANSP instead.
     */
    if (a_i->tag == VL_NEUTRAL &&
        a_i->neutral.lvl == UA_CONST_LVL &&
        a_i->neutral.spine != NULL &&
        a_i->neutral.spine->kind == SP_PATHAPP &&
        a_i->neutral.spine->val != NULL &&
        a_i->neutral.spine->val->tag == VL_NEUTRAL &&
        a_i->neutral.spine->val->neutral.lvl == TRANSP_PROBE_LVL &&
        a_i->neutral.spine->next != NULL &&
        a_i->neutral.spine->next->kind == SP_APP &&
        a_i->neutral.spine->next->next == NULL)
    {
        Val *f_val = a_i->neutral.spine->next->val;
        if (f_val->tag == VL_LAM    || f_val->tag == VL_PATHABS ||
            f_val->tag == VL_NEUTRAL || f_val->tag == VL_FIX)
            return nbe_vapp(a, f_val, x);
        /* Non-function f (ill-typed usage) → stay stuck. */
    }

    return vl_transp(a, a_fun, x);
}

/* ── Path application
 *
 * β-rule: (⟨i⟩ t) @ r  ≡  t[r/i]
 * VL_PATHABS is a closure (reuses lam layout: name, env, body).
 * When the path is a neutral, stay stuck with SP_PATHAPP spine.
 */
Val *nbe_vpathapp(Arena *a, Val *path, Val *r) {
    if (path->tag == VL_PATHABS)
        return nbe_eval(a, env_cons(a, r, path->lam.env), path->lam.body);
    if (path->tag == VL_NEUTRAL) {
        /* HIT path ctor endpoint equations */
        {
            int hit_fam, hit_ci;
            if (hit_path_sentinel_decode(path->neutral.lvl, &hit_fam, &hit_ci)) {
                if (r->tag == VL_NEUTRAL &&
                    (r->neutral.lvl == IZERO_CONST_LVL ||
                     r->neutral.lvl == IONE_CONST_LVL)) {
                    CtorDef *hctor = &ind_get(hit_fam)->ctors[hit_ci];
                    Spine *sp = path->neutral.spine;
                    /* 2-cell second dimension: first dim (SP_PATHAPP) already on spine.
                     * (c args @ i) @ j0/j1 = carrier_lhs/carrier_rhs                  */
                    if (hctor->is_2cell && sp && sp->kind == SP_PATHAPP) {
                        Term *ep_tm = (r->neutral.lvl == IZERO_CONST_LVL)
                                      ? hctor->path_carrier_lhs_term
                                      : hctor->path_carrier_rhs_term;
                        Env *ep_env = spine_to_env(a, sp->next);
                        return nbe_eval(a, ep_env, ep_tm);
                    }
                    /* 1-cell (or 2-cell first dimension): c args @ j0/j1 = lhs/rhs */
                    Term *ep_tm = (r->neutral.lvl == IZERO_CONST_LVL)
                                  ? hctor->path_lhs_term : hctor->path_rhs_term;
                    Env *ep_env = spine_to_env(a, sp);
                    return nbe_eval(a, ep_env, ep_tm);
                }
            }
        }
        return vl_neutral(a, path->neutral.lvl,
                          spine_pathapp(a, r, path->neutral.spine));
    }
    /* (refl a) @ r = a  for any r : II  (refl is the constant path at a) */
    if (path->tag == VL_REFL)
        return path->refl;
    /* VL_COMP / VL_HCOMP: stuck path element (e.g., comp over non-structural PathP
     * family used as a base or tube element).  Return a stuck neutral anchored on
     * the face variable — conv-stable (two equal stucks compare equal) without
     * crashing.  The quoting is approximate (only the face level is preserved);
     * this is a known limitation documented in GRAND_PLAN.md. */
    if (path->tag == VL_COMP || path->tag == VL_HCOMP) {
        Val *face = path->hcomp_s.face;
        int lvl   = (face->tag == VL_NEUTRAL) ? face->neutral.lvl : TRANSP_PROBE_LVL;
        Spine *sp = (face->tag == VL_NEUTRAL) ? face->neutral.spine : NULL;
        return vl_neutral(a, lvl, spine_pathapp(a, r, sp));
    }
    if (path->tag == VL_PATH || path->tag == VL_PATHP) {
        fprintf(stderr, "vpathapp: applied @ to a path TYPE value, not a path element "
                        "(did you mean to use the path element, not its type?)\n");
        exit(1);
    }
    fprintf(stderr, "vpathapp: path element has unexpected val tag %d\n"
                    "  (well-typed path elements are VL_PATHABS, VL_NEUTRAL, VL_REFL;\n"
                    "   VL_COMP/VL_HCOMP are handled as stuck; VL_PATH/PATHP are type errors)\n",
            path->tag);
    exit(1);
}

/* ── Quotient eliminator
 *
 * β-rule: quotrec A R B f coh (qin A R a) ≡ f a
 * qin A R a is neutral with lvl=QIN_CONST_LVL, spine [SP_APP a, SP_APP R, SP_APP A]
 */

Val *nbe_vquotrec(Arena *a, Val *ty_a, Val *rel, Val *ty_b,
                  Val *func, Val *coh, Val *t) {
    if (t->tag == VL_NEUTRAL && t->neutral.lvl == QIN_CONST_LVL) {
        Spine *sp = t->neutral.spine;
        /* spine is [a, R, A] — head = a (most recently applied) */
        if (sp && sp->kind == SP_APP &&
            sp->next && sp->next->kind == SP_APP &&
            sp->next->next && sp->next->next->kind == SP_APP &&
            !sp->next->next->next)
            return nbe_vapp(a, func, sp->val);  /* f a */
    }
    if (t->tag == VL_NEUTRAL)
        return vl_neutral(a, t->neutral.lvl,
                          spine_quotrec(a, ty_a, rel, ty_b, func, coh,
                                        t->neutral.spine));
    fprintf(stderr, "vquotrec: scrutinee is not a quotient element\n");
    exit(1);
}

/* ── Sum eliminator */

Val *nbe_vcase(Arena *a, Val *motive, Val *lcase, Val *rcase, Val *s) {
    if (s->tag == VL_INL)    return nbe_vapp(a, lcase, s->inj);
    if (s->tag == VL_INR)    return nbe_vapp(a, rcase, s->inj);
    if (s->tag == VL_NEUTRAL)
        return vl_neutral(a, s->neutral.lvl,
                          spine_casesplit(a, motive, lcase, rcase, s->neutral.spine));
    fprintf(stderr, "vcase: not a Sum value\n"); exit(1);
}

/* ── Unit eliminator */

Val *nbe_vunitrec(Arena *a, Val *motive, Val *base, Val *s) {
    if (s->tag == VL_STAR)    return base;
    if (s->tag == VL_NEUTRAL)
        return vl_neutral(a, s->neutral.lvl,
                          spine_unitrec(a, motive, base, s->neutral.spine));
    fprintf(stderr, "vunitrec: not a Unit value\n"); exit(1);
}

/* ── W-type eliminator
 *
 * β-rule: wrec P s (sup a f) ≡ s a f (λb. wrec P s (f b))
 *
 * The IH λb. wrec P s (f b) is built as a VL_LAM whose body is a synthetic
 * TM_WREC term.  The closure captures [children, step, motive] so that when
 * applied to b the env is [b(0), children(1), step(2), motive(3)].
 */

Val *nbe_vwrec(Arena *a, Val *motive, Val *step, Val *w) {
    if (w->tag == VL_SUP) {
        Val *label    = w->pair.fst;
        Val *children = w->pair.snd;
        Env *captured = env_cons(a, children,
                        env_cons(a, step,
                        env_cons(a, motive, NULL)));
        /* body: wrec(VAR 3, VAR 2, APP(VAR 1, VAR 0)) */
        Term *body = tm_wrec(a, tm_var(a, 3), tm_var(a, 2),
                             tm_app(a, tm_var(a, 1), tm_var(a, 0)));
        Val *ih = vl_lam(a, "b", captured, body);
        return nbe_vapp(a, nbe_vapp(a, nbe_vapp(a, step, label), children), ih);
    }
    if (w->tag == VL_NEUTRAL)
        return vl_neutral(a, w->neutral.lvl,
                          spine_wrec(a, motive, step, w->neutral.spine));
    fprintf(stderr, "vwrec: not a W-type value\n"); exit(1);
}

/* ── J eliminator */

Val *nbe_vj(Arena *a, Val *ty, Val *lhs, Val *motive,
            Val *base, Val *endpoint, Val *proof) {
    if (proof->tag == VL_REFL) return base;
    /* VL_PATHABS: fire β if the path is constant at lhs (≡ refl lhs).
     * Probe with TRANSP_PROBE_LVL: if the body doesn't mention the probe and
     * equals lhs at i0, the path is definitionally refl lhs.
     *
     * Depth for conv: TRANSP_PROBE_LVL + 2 ensures fresh neutrals created
     * inside conv don't collide with real variable levels (0..depth-1).
     *
     * Stuck level: TRANSP_PROBE_LVL ensures stuck J-on-pathabs values are
     * conv-comparable by spine but distinguishable from real neutrals.
     * NOTE: quoting a stuck J-on-pathabs produces a malformed TM_VAR (display
     * bug only — the value is correct for evaluation purposes). */
    if (proof->tag == VL_PATHABS) {
        Val *probe  = vl_neutral(a, TRANSP_PROBE_LVL, NULL);
        Val *at_prb = nbe_vpathapp(a, proof, probe);
        Term *qt    = nbe_quote(a, TRANSP_PROBE_LVL + 1, at_prb);
        if (!term_mentions_var(qt, 0)) {
            /* Constant path — check if it equals lhs */
            Val *i0v = vl_neutral(a, IZERO_CONST_LVL, NULL);
            Val *at0 = nbe_vpathapp(a, proof, i0v);
            if (conv(a, TRANSP_PROBE_LVL + 2, at0, lhs)) return base;
            /* Constant but doesn't match lhs: malformed application, stay stuck. */
            return vl_jstuck(a, ty, lhs, motive, base, endpoint, proof);
        }
        /* Non-constant path: cubical J computation rule.
         *
         *   J A a B b (⟨i⟩ p i) = transp (λi. B (p i) (⟨j⟩ p (i ∧ j))) b
         *
         * At i=0: B (p 0) (⟨j⟩ p 0) = B a refl  (type of b) ✓
         * At i=1: B (p 1) (⟨j⟩ p j) = B endpoint proof      ✓
         *
         * Family env = [proof, motive]; after lambda fires with i:
         *   VAR(0)=i, VAR(1)=proof, VAR(2)=motive.
         * Inside ⟨j⟩ body: VAR(0)=j, VAR(1)=i, VAR(2)=proof, VAR(3)=motive. */
        Term *p_at_i = tm_pathapp(a, tm_var(a, 1), tm_var(a, 0));
        Term *p_imin = tm_pathapp(a, tm_var(a, 2),
                           tm_imin(a, tm_var(a, 1), tm_var(a, 0)));
        Term *contr  = tm_pathabs(a, "j", p_imin);
        Term *body   = tm_app(a, tm_app(a, tm_var(a, 2), p_at_i), contr);
        Env  *fam_env = env_cons(a, proof, env_cons(a, motive, NULL));
        Val  *family  = vl_pathabs(a, "i", fam_env, body);
        return nbe_vtransp(a, family, base);
    }
    if (proof->tag == VL_NEUTRAL)
        return vl_neutral(a, proof->neutral.lvl,
                          spine_j(a, ty, lhs, motive, base, endpoint,
                                  proof->neutral.spine));
    fprintf(stderr, "vj: not an identity proof (tag=%d)\n", (int)proof->tag);
    exit(1);
}

/* ── Inductive family eliminator */

Val *nbe_vindrec(Arena *a, int fam_idx, Val *motive, Val **cases, Val *scrut) {
    if (scrut->tag == VL_INDCON) {
        if (scrut->indcon.fam_idx != fam_idx) {
            fprintf(stderr,
                    "vindrec: scrutinee is constructor of '%s' (family %d),"
                    " expected '%s' (family %d)\n",
                    ind_get(scrut->indcon.fam_idx)->name, scrut->indcon.fam_idx,
                    ind_get(fam_idx)->name, fam_idx);
            exit(1);
        }
        int k        = scrut->indcon.ctor_idx;
        IndDef *fam  = ind_get(fam_idx);
        if (k < 0 || k >= fam->n_ctors) {
            fprintf(stderr,
                    "vindrec: constructor index %d out of range [0,%d) for '%s'\n",
                    k, fam->n_ctors, fam->name);
            exit(1);
        }
        int n_params = fam->n_params;
        Val *c = cases[k];
        /* Skip param args: case functions take only the ctor-local args. */
        for (int i = n_params; i < scrut->indcon.n_args; i++) {
            Val *arg = scrut->indcon.args[i];
            c = nbe_vapp(a, c, arg);
            int ap = i - n_params;  /* position among ctor args for is_recursive */
            if (ind_is_recursive_pos(fam_idx, k, ap))
                c = nbe_vapp(a, c, nbe_vindrec(a, fam_idx, motive, cases, arg));
        }
        return c;
    }
    if (scrut->tag == VL_NEUTRAL) {
        /* HIT path ctor case: scrutinee is path_ctor args @ r (1-cell)
         *                      or path_ctor args @ i @ j (2-cell)       */
        {
            int hit_fam, hit_ci;
            if (hit_path_sentinel_decode(scrut->neutral.lvl, &hit_fam, &hit_ci) &&
                hit_fam == fam_idx) {
                Spine *sp = scrut->neutral.spine;
                CtorDef *hctor = &ind_get(fam_idx)->ctors[hit_ci];
                int harity = hctor->arity;
                /* 2-cell: (c args @ i) @ j  →  (case_c args @ i) @ j */
                if (hctor->is_2cell && sp && sp->kind == SP_PATHAPP &&
                    sp->next && sp->next->kind == SP_PATHAPP) {
                    Val *j_val = sp->val;          /* second dimension */
                    Val *i_val = sp->next->val;    /* first  dimension */
                    Val **hargs = harity > 0
                        ? (Val **)arena_alloc(a, harity * sizeof(Val *)) : NULL;
                    int hj = 0;
                    for (Spine *s = sp->next->next;
                         s && s->kind == SP_APP && hj < harity; s = s->next, hj++)
                        hargs[hj] = s->val;
                    for (int lo = 0, hi2 = harity-1; lo < hi2; lo++, hi2--)
                        { Val *t2 = hargs[lo]; hargs[lo] = hargs[hi2]; hargs[hi2] = t2; }
                    Val *hc = cases[hit_ci];
                    for (int hk = 0; hk < harity; hk++) hc = nbe_vapp(a, hc, hargs[hk]);
                    return nbe_vpathapp(a, nbe_vpathapp(a, hc, i_val), j_val);
                }
                /* 1-cell: c args @ r  →  case_c args @ r */
                if (sp && sp->kind == SP_PATHAPP) {
                    Val *r = sp->val;
                    Val **hargs = harity > 0
                        ? (Val **)arena_alloc(a, harity * sizeof(Val *)) : NULL;
                    int hj = 0;
                    for (Spine *s = sp->next;
                         s && s->kind == SP_APP && hj < harity; s = s->next, hj++)
                        hargs[hj] = s->val;
                    for (int lo = 0, hi2 = harity-1; lo < hi2; lo++, hi2--)
                        { Val *t2 = hargs[lo]; hargs[lo] = hargs[hi2]; hargs[hi2] = t2; }
                    Val *hc = cases[hit_ci];
                    for (int hk = 0; hk < harity; hk++) hc = nbe_vapp(a, hc, hargs[hk]);
                    return nbe_vpathapp(a, hc, r);
                }
            }
        }
        int n = ind_get(fam_idx)->n_ctors;
        return vl_neutral(a, scrut->neutral.lvl,
                          spine_indrec(a, fam_idx, motive, n, cases,
                                       scrut->neutral.spine));
    }
    fprintf(stderr,
            "vindrec: scrutinee has tag %d, expected VL_INDCON of '%s' or VL_NEUTRAL\n",
            scrut->tag, ind_get(fam_idx)->name);
    exit(1);
}

/* ── Eval */

Val *nbe_vapp(Arena *a, Val *fun, Val *arg) {
    switch (fun->tag) {
    case VL_LAM:
        return nbe_eval(a, env_cons(a, arg, fun->lam.env), fun->lam.body);
    case VL_PATHABS:
        /* A path used as a plain function: same closure structure, treat as APP.
         * The type system ensures arg : II in well-typed terms. */
        return nbe_eval(a, env_cons(a, arg, fun->lam.env), fun->lam.body);
    case VL_NEUTRAL: {
        /* Phase L2 Stage 6 — funext full application:
         *   funext A B f g h  →  ⟨i⟩ λx. h x @ i
         *
         * When fun = neutral(FUNEXT_CONST_LVL) with 4 spine entries (A,B,f,g already
         * applied), applying to h (the 5th arg) fires the reduction.
         *
         * Body TM_PATHAPP(TM_APP(VAR(2),VAR(0)), VAR(1)):
         *   pathabs env=[h]: when applied at r → VL_LAM("x", env=[r,h], body)
         *   when LAM applied at x_val → env=[x_val, r, h]
         *     VAR(0)=x_val, VAR(1)=r, VAR(2)=h → (h x_val) @ r ✓
         */
        if (fun->neutral.lvl == FUNEXT_CONST_LVL) {
            int n = 0;
            for (Spine *s = fun->neutral.spine; s; s = s->next) n++;
            if (n == 4) {
                Term *body = tm_pathapp(a,
                                 tm_app(a, tm_var(a, 2), tm_var(a, 0)),
                                 tm_var(a, 1));
                return vl_pathabs(a, "i", env_cons(a, arg, NULL), tm_lam(a, "x", body));
            }
        }
        return vl_neutral(a, fun->neutral.lvl,
                          spine_cons(a, arg, fun->neutral.spine));
    }
    case VL_FIX:
        /* (fix f) arg → (f (fix f)) arg  — unfold one step */
        return nbe_vapp(a, nbe_vapp(a, fun->fix_fun, vl_fix(a, fun->fix_fun)), arg);
    case VL_PI:
    case VL_SIGMA:
    case VL_W:
        /* Codomain application: used by hcomp structural rules to compute B(x).
         * In well-typed terms Pi/Sigma/W never appear in function position; this
         * case is for synthetic TM_APP bodies in hcomp rule closures only. */
        return nbe_eval(a, env_cons(a, arg, fun->pi.env), fun->pi.cod);
    default:
        fprintf(stderr, "vapp: not a function\n"); exit(1);
    }
}

Val *nbe_eval(Arena *a, Env *env, Term *t) {
    switch (t->tag) {
    case TM_VAR:  return env_lookup(a, env, t->idx, t->idx);
    case TM_LAM:  return vl_lam(a, t->lam.name, env, t->lam.body);
    case TM_APP:  return nbe_vapp(a, nbe_eval(a, env, t->app.fun),
                                     nbe_eval(a, env, t->app.arg));
    case TM_PI:   return vl_pi   (a, t->pi.name, nbe_eval(a, env, t->pi.dom), env, t->pi.cod);
    case TM_SIG:  return vl_sigma(a, t->pi.name, nbe_eval(a, env, t->pi.dom), env, t->pi.cod);
    case TM_UNI:  return vl_uni(a, t->ulevel);
    case TM_ANN:  return nbe_eval(a, env, t->ann.term);
    case TM_PAIR: return vl_pair(a, nbe_eval(a, env, t->pair.fst),
                                    nbe_eval(a, env, t->pair.snd));
    case TM_FST:  return nbe_vfst(a, nbe_eval(a, env, t->elim));
    case TM_SND:  return nbe_vsnd(a, nbe_eval(a, env, t->elim));
    case TM_ID:   return vl_id(a, nbe_eval(a, env, t->id.ty),
                                  nbe_eval(a, env, t->id.lhs),
                                  nbe_eval(a, env, t->id.rhs));
    case TM_REFL: return vl_refl(a, nbe_eval(a, env, t->refl));
    case TM_UA:     return vl_neutral(a, UA_CONST_LVL,     NULL);
    case TM_FUNEXT: return vl_neutral(a, FUNEXT_CONST_LVL, NULL);
    case TM_NAT:    return vl_nat(a);
    case TM_ZERO:   return vl_zero(a);
    case TM_SUCC:   return vl_succ(a, nbe_eval(a, env, t->elim));
    case TM_NATREC: return nbe_vnatrec(a,
                        nbe_eval(a, env, t->natrec.motive),
                        nbe_eval(a, env, t->natrec.base),
                        nbe_eval(a, env, t->natrec.step),
                        nbe_eval(a, env, t->natrec.scrut));
    case TM_GLOBAL: return def_get(t->idx)->val;
    case TM_BOOL:   return vl_bool(a);
    case TM_TRUE:   return vl_true(a);
    case TM_FALSE:  return vl_false(a);
    case TM_BOOLREC: return nbe_vboolrec(a,
                        nbe_eval(a, env, t->boolrec.motive),
                        nbe_eval(a, env, t->boolrec.tcase),
                        nbe_eval(a, env, t->boolrec.fcase),
                        nbe_eval(a, env, t->boolrec.scrut));
    case TM_J:    return nbe_vj(a,
                      nbe_eval(a, env, t->j.ty),
                      nbe_eval(a, env, t->j.lhs),
                      nbe_eval(a, env, t->j.motive),
                      nbe_eval(a, env, t->j.base),
                      nbe_eval(a, env, t->j.endpoint),
                      nbe_eval(a, env, t->j.proof));
    case TM_W:
        return vl_w(a, t->pi.name, nbe_eval(a, env, t->pi.dom), env, t->pi.cod);
    case TM_SUP:
        return vl_sup(a, nbe_eval(a, env, t->sup.label),
                         nbe_eval(a, env, t->sup.children));
    case TM_WREC:
        return nbe_vwrec(a,
                   nbe_eval(a, env, t->wrec.motive),
                   nbe_eval(a, env, t->wrec.step),
                   nbe_eval(a, env, t->wrec.scrut));
    case TM_EMPTY:
        return vl_empty(a);
    case TM_ABORT:
        return nbe_vabort(a,
                   nbe_eval(a, env, t->abort_t.motive),
                   nbe_eval(a, env, t->abort_t.scrut));
    case TM_UNIT:
        return vl_unit(a);
    case TM_STAR:
        return vl_star(a);
    case TM_UNITREC:
        return nbe_vunitrec(a,
                   nbe_eval(a, env, t->unitrec_t.motive),
                   nbe_eval(a, env, t->unitrec_t.base),
                   nbe_eval(a, env, t->unitrec_t.scrut));
    case TM_SUM:
        return vl_sum(a, nbe_eval(a, env, t->sum_t.left),
                         nbe_eval(a, env, t->sum_t.right));
    case TM_INL:
        return vl_inl(a, nbe_eval(a, env, t->elim));
    case TM_INR:
        return vl_inr(a, nbe_eval(a, env, t->elim));
    case TM_CASESPLIT:
        return nbe_vcase(a,
                   nbe_eval(a, env, t->casesplit_t.motive),
                   nbe_eval(a, env, t->casesplit_t.lcase),
                   nbe_eval(a, env, t->casesplit_t.rcase),
                   nbe_eval(a, env, t->casesplit_t.scrut));
    case TM_TRUNC:   return vl_neutral(a, TRUNC_CONST_LVL,  NULL);
    case TM_TRINT:   return vl_neutral(a, TRINT_CONST_LVL,  NULL);
    case TM_SQUASH:  return vl_neutral(a, SQUASH_CONST_LVL, NULL);
    case TM_QUOT:    return vl_neutral(a, QUOT_CONST_LVL, NULL);
    case TM_QIN:     return vl_neutral(a, QIN_CONST_LVL,  NULL);
    case TM_QEQS:    return vl_neutral(a, QEQS_CONST_LVL, NULL);
    case TM_QUOTREC:
        return nbe_vquotrec(a,
                   nbe_eval(a, env, t->quotrec_t.ty_a),
                   nbe_eval(a, env, t->quotrec_t.rel),
                   nbe_eval(a, env, t->quotrec_t.ty_b),
                   nbe_eval(a, env, t->quotrec_t.func),
                   nbe_eval(a, env, t->quotrec_t.coh),
                   nbe_eval(a, env, t->quotrec_t.scrut));
    case TM_TRUNCREC:
        return nbe_vtruncret(a,
                   nbe_eval(a, env, t->truncrec_t.ty_a),
                   nbe_eval(a, env, t->truncrec_t.ty_b),
                   nbe_eval(a, env, t->truncrec_t.func),
                   nbe_eval(a, env, t->truncrec_t.scrut));
    case TM_CIRCLE:  return vl_circle(a);
    case TM_BASE:    return vl_base(a);
    case TM_LOOP:    return vl_neutral(a, LOOP_CONST_LVL, NULL);
    case TM_CIRCREC:
        return nbe_vcircrec(a,
                   nbe_eval(a, env, t->circrec_t.motive),
                   nbe_eval(a, env, t->circrec_t.base_case),
                   nbe_eval(a, env, t->circrec_t.loop_case),
                   nbe_eval(a, env, t->circrec_t.scrut));
    case TM_INDTYPE: {
        int n = t->indtype.n_args;
        Val **args = n > 0 ? (Val **)arena_alloc(a, n * sizeof(Val *)) : NULL;
        for (int i = 0; i < n; i++) args[i] = nbe_eval(a, env, t->indtype.args[i]);
        return vl_indtype(a, t->indtype.fam_idx, n, args);
    }
    case TM_INDCON: {
        int n = t->indcon.n_args;
        Val **args = n > 0 ? (Val **)arena_alloc(a, n * sizeof(Val *)) : NULL;
        for (int i = 0; i < n; i++) args[i] = nbe_eval(a, env, t->indcon.args[i]);
        int fam_idx2  = t->indcon.fam_idx;
        int ctor_idx2 = t->indcon.ctor_idx;
        if (ind_get(fam_idx2)->ctors[ctor_idx2].is_path_ctor) {
            /* Path constructor: return sentinel neutral.
             * Spine: params first (outermost → back), then ctor args (innermost → head).
             * Resulting order: [ctor_arg_{n-1}, …, ctor_arg_0, param_{p-1}, …, param_0] */
            int n_params2 = ind_get(fam_idx2)->n_params;
            Spine *sp2 = NULL;
            for (int j = 0;          j < n_params2; j++) sp2 = spine_cons(a, args[j], sp2);
            for (int j = n_params2;  j < n;         j++) sp2 = spine_cons(a, args[j], sp2);
            return vl_neutral(a, hit_path_sentinel(fam_idx2, ctor_idx2), sp2);
        }
        return vl_indcon(a, fam_idx2, ctor_idx2, n, args);
    }
    case TM_INDREC: {
        int fam_idx = t->indrec.fam_idx;
        int n       = t->indrec.n_cases;
        int expect  = ind_get(fam_idx)->n_ctors;
        if (n != expect) {
            fprintf(stderr,
                    "eval: indrec for '%s' has %d case(s), expected %d\n",
                    ind_get(fam_idx)->name, n, expect);
            exit(1);
        }
        Val *motive = t->indrec.motive ? nbe_eval(a, env, t->indrec.motive) : NULL;
        Val **cases = n > 0 ? (Val **)arena_alloc(a, n * sizeof(Val *)) : NULL;
        for (int i = 0; i < n; i++) cases[i] = nbe_eval(a, env, t->indrec.cases[i]);
        Val *scrut = nbe_eval(a, env, t->indrec.scrut);
        return nbe_vindrec(a, fam_idx, motive, cases, scrut);
    }

    case TM_FIX:
        return vl_fix(a, nbe_eval(a, env, t->fix.body));
    case TM_LEVEL: return vl_level(a);
    case TM_LZERO: return vl_lzero(a);
    case TM_LSUC:  return vl_lsuc(a, nbe_eval(a, env, t->elim));
    case TM_LMAX: {
        Val *l = nbe_eval(a, env, t->app.fun);
        Val *r = nbe_eval(a, env, t->app.arg);
        return nbe_vlmax(a, l, r);
    }
    case TM_UNI_V: {
        Val *lv = nbe_eval(a, env, t->uni_v_lvl);
        /* Concrete level: collapse to VL_UNI */
        int n = 0; Val *cur = lv;
        while (cur->tag == VL_LSUC) { n++; cur = cur->succ; }
        if (cur->tag == VL_LZERO) return vl_uni(a, n);
        return vl_uni_v(a, lv);  /* neutral level */
    }

    case TM_HOLE:
        fprintf(stderr, "eval: TM_HOLE reached — term not elaborated\n");
        exit(1);

    /* Phase L2 — cubical interval */
    case TM_INTERVAL: return vl_neutral(a, INTERVAL_CONST_LVL, NULL);
    case TM_IZERO:    return vl_neutral(a, IZERO_CONST_LVL,    NULL);
    case TM_IONE:     return vl_neutral(a, IONE_CONST_LVL,     NULL);
    case TM_PATHABS:
        return vl_pathabs(a, t->lam.name,
                          env, t->lam.body);
    case TM_PATHAPP:
        return nbe_vpathapp(a,
                   nbe_eval(a, env, t->app.fun),
                   nbe_eval(a, env, t->app.arg));
    case TM_PATH:
        return vl_path(a,
                   nbe_eval(a, env, t->id.ty),
                   nbe_eval(a, env, t->id.lhs),
                   nbe_eval(a, env, t->id.rhs));
    case TM_PATHP:
        return vl_pathp(a,
                   nbe_eval(a, env, t->id.ty),
                   nbe_eval(a, env, t->id.lhs),
                   nbe_eval(a, env, t->id.rhs));
    case TM_TRANSP:
        return nbe_vtransp(a,
                           nbe_eval(a, env, t->app.fun),
                           nbe_eval(a, env, t->app.arg));
    case TM_HCOMP:
        return nbe_vhcomp(a,
                          nbe_eval(a, env, t->hcomp_t.ty),
                          nbe_eval(a, env, t->hcomp_t.face),
                          nbe_eval(a, env, t->hcomp_t.tube),
                          nbe_eval(a, env, t->hcomp_t.base));
    case TM_COMP:
        return nbe_vcomp(a,
                         nbe_eval(a, env, t->hcomp_t.ty),
                         nbe_eval(a, env, t->hcomp_t.face),
                         nbe_eval(a, env, t->hcomp_t.tube),
                         nbe_eval(a, env, t->hcomp_t.base));
    case TM_FILL:
        return nbe_vfill(a,
                         nbe_eval(a, env, t->fill_t.fam),
                         nbe_eval(a, env, t->fill_t.face),
                         nbe_eval(a, env, t->fill_t.tube),
                         nbe_eval(a, env, t->fill_t.base),
                         nbe_eval(a, env, t->fill_t.idx));
    case TM_GLUE:
        return nbe_vglue_ty(a,
                            nbe_eval(a, env, t->glue_t.base),
                            nbe_eval(a, env, t->glue_t.face),
                            nbe_eval(a, env, t->glue_t.fiber),
                            nbe_eval(a, env, t->glue_t.equiv));
    case TM_IMIN:
        return nbe_vimin(a, nbe_eval(a, env, t->app.fun),
                            nbe_eval(a, env, t->app.arg));
    case TM_IMAX:
        return nbe_vimax(a, nbe_eval(a, env, t->app.fun),
                            nbe_eval(a, env, t->app.arg));
    case TM_INEG:
        return nbe_vineg(a, nbe_eval(a, env, t->elim));

    /* Phase L2 Stage 7 — IsOne */
    case TM_ISONE:
        return nbe_visone(a, nbe_eval(a, env, t->elim));

    /* Phase L2 Stage 7d — glue intro / unglue elim */
    case TM_GLUEELEM:
        return nbe_vglueelem(a,
                             nbe_eval(a, env, t->glue_elem_t.face),
                             nbe_eval(a, env, t->glue_elem_t.partial),
                             nbe_eval(a, env, t->glue_elem_t.base));
    case TM_UNGLUE:
        return nbe_vunglue(a,
                           nbe_eval(a, env, t->unglue_t.face),
                           nbe_eval(a, env, t->unglue_t.equiv),
                           nbe_eval(a, env, t->unglue_t.elem));
    case TM_PRIMSUB:
        return nbe_vprimsub(a,
                            nbe_eval(a, env, t->primsub_t.ty),
                            nbe_eval(a, env, t->primsub_t.face),
                            nbe_eval(a, env, t->primsub_t.u),
                            nbe_eval(a, env, t->primsub_t.a));

    /* Phase M4 — pattern matching */
    case TM_MATCH: {
        Val *scrut_v = nbe_eval(a, env, t->match_s.scrut);
        int fam_idx = t->match_s.fam_idx;
        int n_arms  = t->match_s.n_arms;
        MatchArm *arms = t->match_s.arms;
        /* Helper: find arm by ctor_idx */
#define FIND_ARM_IDX(cid) ({ int _ai = -1; for (int _i = 0; _i < n_arms; _i++) if (arms[_i].ctor_idx == (cid)) { _ai = _i; break; } _ai; })
        if (fam_idx == -1) { /* Nat */
            int zero_ai = FIND_ARM_IDX(0);
            int succ_ai = FIND_ARM_IDX(1);
            /* If the succ arm has an IH binder, desugar to natrec. */
            if (succ_ai >= 0 && arms[succ_ai].ih_name) {
                if (zero_ai < 0) goto match_bad;
                Val *base = nbe_eval(a, env, arms[zero_ai].body);
                /* step = \m'. \ih. body_s  (body has dB 0=ih, 1=m') */
                Term *step_tm = tm_lam(a, arms[succ_ai].n_binds > 0
                                           ? arms[succ_ai].names[0] : "_",
                                       tm_lam(a, arms[succ_ai].ih_name,
                                              arms[succ_ai].body));
                Val *step = nbe_eval(a, env, step_tm);
                return nbe_vnatrec(a, NULL, base, step, scrut_v);
            }
            if (scrut_v->tag == VL_ZERO) {
                if (zero_ai < 0) goto match_bad;
                return nbe_eval(a, env, arms[zero_ai].body);
            }
            if (scrut_v->tag == VL_SUCC) {
                if (succ_ai < 0) goto match_bad;
                Env *arm_env = arms[succ_ai].n_binds > 0
                    ? env_cons(a, scrut_v->succ, env) : env;
                return nbe_eval(a, arm_env, arms[succ_ai].body);
            }
        } else if (fam_idx == -2) { /* Bool */
            if (scrut_v->tag == VL_TRUE) {
                int ai = FIND_ARM_IDX(0);
                if (ai < 0) goto match_bad;
                return nbe_eval(a, env, arms[ai].body);
            }
            if (scrut_v->tag == VL_FALSE) {
                int ai = FIND_ARM_IDX(1);
                if (ai < 0) goto match_bad;
                return nbe_eval(a, env, arms[ai].body);
            }
        } else { /* User inductive */
            IndDef *fam = ind_get(fam_idx);
            if (scrut_v->tag == VL_INDCON && scrut_v->indcon.fam_idx == fam_idx) {
                int k = scrut_v->indcon.ctor_idx;
                int ai = FIND_ARM_IDX(k);
                if (ai < 0) goto match_bad;
                int n_params = fam->n_params;
                int arity = arms[ai].n_binds;
                Env *arm_env = env;
                /* Add args in forward order: last arg ends up at de Bruijn 0 */
                for (int j = 0; j < arity; j++)
                    arm_env = env_cons(a, scrut_v->indcon.args[n_params + j], arm_env);
                return nbe_eval(a, arm_env, arms[ai].body);
            }
        }
        /* Neutral scrutinee: build stuck VL_NEUTRAL with SP_MATCH spine */
        if (scrut_v->tag == VL_NEUTRAL) {
            MatchClosure *cls = (MatchClosure *)arena_alloc(a, n_arms * sizeof(MatchClosure));
            for (int i = 0; i < n_arms; i++) {
                cls[i].ctor_idx = arms[i].ctor_idx;
                cls[i].n_binds  = arms[i].n_binds;
                for (int j = 0; j < arms[i].n_binds; j++)
                    cls[i].names[j] = arms[i].names[j];
                cls[i].env  = env;
                cls[i].body = arms[i].body;
            }
            return vl_neutral(a, scrut_v->neutral.lvl,
                              spine_match(a, fam_idx, n_arms, cls,
                                          scrut_v->neutral.spine));
        }
    match_bad:
        fprintf(stderr, "eval: match: unexpected scrutinee tag %d for fam_idx %d\n",
                scrut_v->tag, fam_idx);
        exit(1);
#undef FIND_ARM_IDX
    }

    default:
        fprintf(stderr, "eval: unhandled term tag %d\n", t->tag);
        exit(1);
    }
}

/* ── Quote */

static Term *quote(Arena *a, int depth, Val *v);

static Term *quote_spine(Arena *a, int depth, Term *head, Spine *sp) {
    if (!sp) return head;
    Term *inner = quote_spine(a, depth, head, sp->next);
    switch (sp->kind) {
    case SP_APP: return tm_app(a, inner, quote(a, depth, sp->val));
    case SP_FST: return tm_fst(a, inner);
    case SP_SND: return tm_snd(a, inner);
    case SP_J:
        return tm_j(a,
                    quote(a, depth, sp->j.ty),
                    quote(a, depth, sp->j.lhs),
                    quote(a, depth, sp->j.motive),
                    quote(a, depth, sp->j.base),
                    quote(a, depth, sp->j.endpoint),
                    inner);
    case SP_NATREC:
        return tm_natrec(a,
                         sp->natrec.motive ? quote(a, depth, sp->natrec.motive) : tm_hole(a, -1),
                         quote(a, depth, sp->natrec.base),
                         quote(a, depth, sp->natrec.step),
                         inner);
    case SP_BOOLREC:
        return tm_boolrec(a,
                          quote(a, depth, sp->boolrec.motive),
                          quote(a, depth, sp->boolrec.tcase),
                          quote(a, depth, sp->boolrec.fcase),
                          inner);
    case SP_WREC:
        return tm_wrec(a,
                       quote(a, depth, sp->wrec.motive),
                       quote(a, depth, sp->wrec.step),
                       inner);
    case SP_ABORT:
        return tm_abort(a, quote(a, depth, sp->abort_s.motive), inner);
    case SP_UNITREC:
        return tm_unitrec(a,
                          quote(a, depth, sp->unitrec_s.motive),
                          quote(a, depth, sp->unitrec_s.base),
                          inner);
    case SP_CASESPLIT:
        return tm_casesplit(a,
                            quote(a, depth, sp->casesplit_s.motive),
                            quote(a, depth, sp->casesplit_s.lcase),
                            quote(a, depth, sp->casesplit_s.rcase),
                            inner);
    case SP_TRUNCREC:
        return tm_truncrec(a,
                           quote(a, depth, sp->truncrec_s.ty_a),
                           quote(a, depth, sp->truncrec_s.ty_b),
                           quote(a, depth, sp->truncrec_s.func),
                           inner);
    case SP_QUOTREC:
        return tm_quotrec(a,
                          quote(a, depth, sp->quotrec_s.ty_a),
                          quote(a, depth, sp->quotrec_s.rel),
                          quote(a, depth, sp->quotrec_s.ty_b),
                          quote(a, depth, sp->quotrec_s.func),
                          quote(a, depth, sp->quotrec_s.coh),
                          inner);
    case SP_CIRCREC:
        return tm_circrec(a,
                          quote(a, depth, sp->circrec_s.motive),
                          quote(a, depth, sp->circrec_s.base_case),
                          quote(a, depth, sp->circrec_s.loop_case),
                          inner);
    case SP_INDREC: {
        int n = sp->indrec.n_cases;
        Term **cases = n > 0 ? (Term **)arena_alloc(a, n * sizeof(Term *)) : NULL;
        for (int i = 0; i < n; i++) cases[i] = quote(a, depth, sp->indrec.cases[i]);
        Term *motive = sp->indrec.motive ? quote(a, depth, sp->indrec.motive) : NULL;
        return tm_indrec(a, sp->indrec.fam_idx, motive, n, cases, inner);
    }
    case SP_PATHAPP:
        return tm_pathapp(a, inner, quote(a, depth, sp->val));
    case SP_MATCH: {
        int n = sp->match_sp.n_arms;
        MatchClosure *cls = sp->match_sp.arms;
        MatchArm *arms = n > 0 ? (MatchArm *)arena_alloc(a, n * sizeof(MatchArm)) : NULL;
        for (int i = 0; i < n; i++) {
            arms[i].ctor_idx = cls[i].ctor_idx;
            arms[i].n_binds  = cls[i].n_binds;
            for (int j = 0; j < cls[i].n_binds; j++)
                arms[i].names[j] = cls[i].names[j];
            /* Open body with fresh neutrals (same order as eval) */
            Env *e = cls[i].env;
            int d = depth;
            for (int j = 0; j < cls[i].n_binds; j++) {
                Val *fresh = vl_neutral(a, d++, NULL);
                e = env_cons(a, fresh, e);
            }
            Val *body_v = nbe_eval(a, e, cls[i].body);
            arms[i].body = quote(a, d, body_v);
        }
        return tm_match(a, inner, sp->match_sp.fam_idx, n, arms);
    }
    default:
        fprintf(stderr, "quote_spine: unhandled spine kind %d\n", sp->kind);
        exit(1);
    }
}

static Term *quote(Arena *a, int depth, Val *v) {
    switch (v->tag) {
    case VL_LAM: {
        Val *fresh = vl_neutral(a, depth, NULL);
        Val *body  = nbe_eval(a, env_cons(a, fresh, v->lam.env), v->lam.body);
        return tm_lam(a, v->lam.name, quote(a, depth + 1, body));
    }
    case VL_PATHABS: {
        /* Quote ⟨i⟩ body: apply to a fresh interval neutral, quote the body */
        Val *fresh = vl_neutral(a, depth, NULL);
        Val *body  = nbe_eval(a, env_cons(a, fresh, v->lam.env), v->lam.body);
        return tm_pathabs(a, v->lam.name, quote(a, depth + 1, body));
    }
    case VL_PI: {
        Term *dom  = quote(a, depth, v->pi.dom);
        Val  *fresh = vl_neutral(a, depth, NULL);
        Val  *cod   = nbe_eval(a, env_cons(a, fresh, v->pi.env), v->pi.cod);
        return tm_pi(a, v->pi.name, dom, quote(a, depth + 1, cod));
    }
    case VL_SIGMA: {
        Term *dom  = quote(a, depth, v->pi.dom);
        Val  *fresh = vl_neutral(a, depth, NULL);
        Val  *cod   = nbe_eval(a, env_cons(a, fresh, v->pi.env), v->pi.cod);
        return tm_sig(a, v->pi.name, dom, quote(a, depth + 1, cod));
    }
    case VL_UNI:
        return tm_uni(a, v->ulevel);
    case VL_NEUTRAL: {
        Term *head;
        if      (v->neutral.lvl == UA_CONST_LVL)     head = tm_ua(a);
        else if (v->neutral.lvl == FUNEXT_CONST_LVL) head = tm_funext(a);
        else if (v->neutral.lvl == TRUNC_CONST_LVL)  head = tm_trunc(a);
        else if (v->neutral.lvl == TRINT_CONST_LVL)  head = tm_trint(a);
        else if (v->neutral.lvl == SQUASH_CONST_LVL) head = tm_squash(a);
        else if (v->neutral.lvl == LOOP_CONST_LVL)   head = tm_loop(a);
        else if (v->neutral.lvl == QUOT_CONST_LVL)      head = tm_quot(a);
        else if (v->neutral.lvl == QIN_CONST_LVL)       head = tm_qin(a);
        else if (v->neutral.lvl == QEQS_CONST_LVL)      head = tm_qeq(a);
        else if (v->neutral.lvl == INTERVAL_CONST_LVL)  head = tm_interval(a);
        else if (v->neutral.lvl == IZERO_CONST_LVL)     head = tm_izero(a);
        else if (v->neutral.lvl == IONE_CONST_LVL)      head = tm_ione(a);
        else {
            /* General HIT path ctor sentinels: reconstruct TM_INDCON.
             * Spine ordering (head = last applied):
             *   1-cell: [SP_PATHAPP(r),    SP_APP(args)...]
             *   2-cell: [SP_PATHAPP(j), SP_PATHAPP(i), SP_APP(args)...]
             * Quoted form: indcon(args) / indcon(args)@r / (indcon(args)@i)@j */
            int qt_fam, qt_ci;
            if (hit_path_sentinel_decode(v->neutral.lvl, &qt_fam, &qt_ci)) {
                Spine *qt_sp = v->neutral.spine;
                Val *qt_dim2 = NULL; /* outermost pathapp (j for 2-cell, r for 1-cell) */
                Val *qt_dim1 = NULL; /* first pathapp for 2-cell (i) */
                CtorDef *qt_ctor = &ind_get(qt_fam)->ctors[qt_ci];
                if (qt_sp && qt_sp->kind == SP_PATHAPP) {
                    qt_dim2 = qt_sp->val; qt_sp = qt_sp->next;
                    /* 2-cell: strip second SP_PATHAPP (first dimension) */
                    if (qt_ctor->is_2cell && qt_sp && qt_sp->kind == SP_PATHAPP) {
                        qt_dim1 = qt_sp->val; qt_sp = qt_sp->next;
                    }
                }
                /* qt_sp now points at the first SP_APP (ctor args + params) */
                IndDef *qt_fam_def = ind_get(qt_fam);
                int qt_n_params    = qt_fam_def->n_params;
                int qt_arity       = qt_ctor->arity;
                int qt_ntot        = qt_n_params + qt_arity;
                Val **qt_svals = qt_ntot > 0
                    ? (Val **)arena_alloc(a, qt_ntot * sizeof(Val *)) : NULL;
                int qt_ni = 0;
                for (Spine *s = qt_sp; s && s->kind == SP_APP && qt_ni < qt_ntot;
                     s = s->next, qt_ni++)
                    qt_svals[qt_ni] = s->val;
                Term **qt_targs = qt_ntot > 0
                    ? (Term **)arena_alloc(a, qt_ntot * sizeof(Term *)) : NULL;
                for (int qi = 0; qi < qt_ntot; qi++)
                    qt_targs[qi] = (qi < qt_ni)
                        ? quote(a, depth, qt_svals[qt_ntot - 1 - qi])
                        : tm_var(a, 0);  /* malformed fallback */
                Term *qt_t = tm_indcon(a, qt_fam, qt_ci, qt_ntot, qt_targs);
                if (qt_dim1) qt_t = tm_pathapp(a, qt_t, quote(a, depth, qt_dim1));
                if (qt_dim2) qt_t = tm_pathapp(a, qt_t, quote(a, depth, qt_dim2));
                return qt_t;
            }
            head = tm_var(a, depth - v->neutral.lvl - 1);
        }
        return quote_spine(a, depth, head, v->neutral.spine);
    }
    case VL_PAIR:
        return tm_pair(a, quote(a, depth, v->pair.fst),
                          quote(a, depth, v->pair.snd));
    case VL_ID:
        return tm_id(a, quote(a, depth, v->id.ty),
                        quote(a, depth, v->id.lhs),
                        quote(a, depth, v->id.rhs));
    case VL_TRANSP:
        return tm_transp(a, quote(a, depth, v->transp_s.family),
                            quote(a, depth, v->transp_s.elem));
    case VL_HCOMP:
        return tm_hcomp(a, quote(a, depth, v->hcomp_s.ty),
                           quote(a, depth, v->hcomp_s.face),
                           quote(a, depth, v->hcomp_s.tube),
                           quote(a, depth, v->hcomp_s.base));
    case VL_COMP:
        return tm_comp(a, quote(a, depth, v->hcomp_s.ty),
                          quote(a, depth, v->hcomp_s.face),
                          quote(a, depth, v->hcomp_s.tube),
                          quote(a, depth, v->hcomp_s.base));
    case VL_GLUE:
        return tm_glue(a, quote(a, depth, v->glue_s.base),
                          quote(a, depth, v->glue_s.face),
                          quote(a, depth, v->glue_s.fiber),
                          quote(a, depth, v->glue_s.equiv));
    case VL_IMIN:
        return tm_imin(a, quote(a, depth, v->pair.fst), quote(a, depth, v->pair.snd));
    case VL_IMAX:
        return tm_imax(a, quote(a, depth, v->pair.fst), quote(a, depth, v->pair.snd));
    case VL_INEG:
        return tm_ineg(a, quote(a, depth, v->succ));
    case VL_ISONE:
        return tm_isone(a, quote(a, depth, v->succ));
    case VL_GLUEELEM:
        return tm_glueelem(a, quote(a, depth, v->glue_elem_s.face),
                              quote(a, depth, v->glue_elem_s.partial),
                              quote(a, depth, v->glue_elem_s.base));
    case VL_UNGLUE:
        return tm_unglue(a, quote(a, depth, v->unglue_s.face),
                            quote(a, depth, v->unglue_s.equiv),
                            quote(a, depth, v->unglue_s.elem));
    case VL_JSTUCK:
        return tm_j(a, quote(a, depth, v->jstuck_s.ty),
                       quote(a, depth, v->jstuck_s.lhs),
                       quote(a, depth, v->jstuck_s.motive),
                       quote(a, depth, v->jstuck_s.base),
                       quote(a, depth, v->jstuck_s.endpoint),
                       quote(a, depth, v->jstuck_s.proof));
    case VL_PRIMSUB:
        return tm_primsub(a, quote(a, depth, v->primsub_s.ty),
                             quote(a, depth, v->primsub_s.face),
                             quote(a, depth, v->primsub_s.u),
                             quote(a, depth, v->primsub_s.out));
    case VL_PATH:
        return tm_path(a, quote(a, depth, v->id.ty),
                          quote(a, depth, v->id.lhs),
                          quote(a, depth, v->id.rhs));
    case VL_PATHP:
        return tm_pathp(a, quote(a, depth, v->id.ty),
                           quote(a, depth, v->id.lhs),
                           quote(a, depth, v->id.rhs));
    case VL_REFL:
        return tm_refl(a, quote(a, depth, v->refl));
    case VL_NAT:   return tm_nat(a);
    case VL_ZERO:  return tm_zero(a);
    case VL_SUCC:  return tm_succ(a, quote(a, depth, v->succ));
    case VL_BOOL:  return tm_bool(a);
    case VL_TRUE:  return tm_true(a);
    case VL_FALSE: return tm_false(a);
    case VL_W: {
        Term *dom   = quote(a, depth, v->pi.dom);
        Val  *fresh = vl_neutral(a, depth, NULL);
        Val  *cod   = nbe_eval(a, env_cons(a, fresh, v->pi.env), v->pi.cod);
        return tm_w(a, v->pi.name, dom, quote(a, depth + 1, cod));
    }
    case VL_SUP:
        return tm_sup(a, quote(a, depth, v->pair.fst),
                         quote(a, depth, v->pair.snd));
    case VL_EMPTY:
        return tm_empty(a);
    case VL_UNIT:
        return tm_unit(a);
    case VL_STAR:
        return tm_star(a);
    case VL_SUM:
        return tm_sum(a, quote(a, depth, v->pair.fst),
                         quote(a, depth, v->pair.snd));
    case VL_INL:
        return tm_inl(a, quote(a, depth, v->inj));
    case VL_INR:
        return tm_inr(a, quote(a, depth, v->inj));
    case VL_CIRCLE: return tm_circle(a);
    case VL_BASE:   return tm_base(a);
    /* Suspension HIT type value */
    case VL_INDTYPE: {
        int n = v->indtype.n_args;
        Term **args = n > 0 ? (Term **)arena_alloc(a, n * sizeof(Term *)) : NULL;
        for (int i = 0; i < n; i++) args[i] = quote(a, depth, v->indtype.args[i]);
        return tm_indtype(a, v->indtype.fam_idx, n, args);
    }
    case VL_INDCON: {
        int n = v->indcon.n_args;
        Term **args = n > 0 ? (Term **)arena_alloc(a, n * sizeof(Term *)) : NULL;
        for (int i = 0; i < n; i++) args[i] = quote(a, depth, v->indcon.args[i]);
        return tm_indcon(a, v->indcon.fam_idx, v->indcon.ctor_idx, n, args);
    }
    case VL_FIX:
        return tm_fix(a, quote(a, depth, v->fix_fun));
    case VL_LEVEL: return tm_level(a);
    case VL_LZERO: return tm_lzero(a);
    case VL_LSUC:  return tm_lsuc(a, quote(a, depth, v->succ));
    case VL_LMAX:  return tm_lmax(a, quote(a, depth, v->pair.fst),
                                     quote(a, depth, v->pair.snd));
    case VL_UNI_V:
        if (!v->uni_v_lvl) {
            /* VL_UNI_V(NULL) is the checker's omega sentinel; nbe_eval never
               produces it, so quote should never see it with closed terms. */
            fprintf(stderr, "quote: internal error: VL_UNI_V with NULL level\n");
            exit(1);
        }
        return tm_uni_v(a, quote(a, depth, v->uni_v_lvl));
    default:
        fprintf(stderr, "quote: unhandled val tag %d\n", v->tag);
        exit(1);
    }
}

Term *nbe_quote(Arena *a, int depth, Val *v) { return quote(a, depth, v); }

Term *nbe_nf(Arena *a, Term *t) {
    return nbe_quote(a, 0, nbe_eval(a, NULL, t));
}
