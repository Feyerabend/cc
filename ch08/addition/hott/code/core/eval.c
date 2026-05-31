#include <stdio.h>
#include <stdlib.h>
#include "eval.h"
#include "defs.h"

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

Val *nbe_vfst(Arena *a, Val *v) {
    if (v->tag == VL_PAIR)    return v->pair.fst;
    if (v->tag == VL_NEUTRAL)
        return vl_neutral(a, v->neutral.lvl, spine_fst(a, v->neutral.spine));
    fprintf(stderr, "vfst: not a pair\n"); exit(1);
}

Val *nbe_vsnd(Arena *a, Val *v) {
    if (v->tag == VL_PAIR)    return v->pair.snd;
    if (v->tag == VL_NEUTRAL)
        return vl_neutral(a, v->neutral.lvl, spine_snd(a, v->neutral.spine));
    fprintf(stderr, "vsnd: not a pair\n"); exit(1);
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
    if (proof->tag == VL_NEUTRAL)
        return vl_neutral(a, proof->neutral.lvl,
                          spine_j(a, ty, lhs, motive, base, endpoint,
                                  proof->neutral.spine));
    fprintf(stderr, "vj: not an identity proof\n"); exit(1);
}

/* ── Eval */

Val *nbe_vapp(Arena *a, Val *fun, Val *arg) {
    switch (fun->tag) {
    case VL_LAM:
        return nbe_eval(a, env_cons(a, arg, fun->lam.env), fun->lam.body);
    case VL_NEUTRAL:
        return vl_neutral(a, fun->neutral.lvl,
                          spine_cons(a, arg, fun->neutral.spine));
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
                         quote(a, depth, sp->natrec.motive),
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
    case SP_CIRCREC:
        return tm_circrec(a,
                          quote(a, depth, sp->circrec_s.motive),
                          quote(a, depth, sp->circrec_s.base_case),
                          quote(a, depth, sp->circrec_s.loop_case),
                          inner);
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
        else head = tm_var(a, depth - v->neutral.lvl - 1);
        return quote_spine(a, depth, head, v->neutral.spine);
    }
    case VL_PAIR:
        return tm_pair(a, quote(a, depth, v->pair.fst),
                          quote(a, depth, v->pair.snd));
    case VL_ID:
        return tm_id(a, quote(a, depth, v->id.ty),
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
    default:
        fprintf(stderr, "quote: unhandled val tag %d\n", v->tag);
        exit(1);
    }
}

Term *nbe_quote(Arena *a, int depth, Val *v) { return quote(a, depth, v); }

Term *nbe_nf(Arena *a, Term *t) {
    return nbe_quote(a, 0, nbe_eval(a, NULL, t));
}
