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
    default:
        fprintf(stderr, "quote: unhandled val tag %d\n", v->tag);
        exit(1);
    }
}

Term *nbe_quote(Arena *a, int depth, Val *v) { return quote(a, depth, v); }

Term *nbe_nf(Arena *a, Term *t) {
    return nbe_quote(a, 0, nbe_eval(a, NULL, t));
}
