#include <stdio.h>
#include <stdlib.h>
#include "check.h"
#include "parse.h"
#include "defs.h"

/* ── ua type cache */
/* Parsed and evaluated once; lives in a permanent arena never freed.   */

static Arena ua_arena  = {NULL};
static Val  *ua_type_v = NULL;

static Val *get_ua_type(void) {
    if (ua_type_v) return ua_type_v;
    Term *ty = parse(&ua_arena,
        "Π(A : Type_1). Π(B : Type_1)."
        " (Σ(f : A → B). Σ(g : B → A)."
        "  Σ(_ : Π(b : B). Id B (f (g b)) b)."
        "  Π(a : A). Id A (g (f a)) a)"
        " → Id Type_1 A B");
    if (!ty) { fprintf(stderr, "internal: ua type parse failed\n"); exit(1); }
    ua_type_v = nbe_eval(&ua_arena, NULL, ty);
    return ua_type_v;
}

static Arena funext_arena  = {NULL};
static Val  *funext_type_v = NULL;

static Val *get_funext_type(void) {
    if (funext_type_v) return funext_type_v;
    /* funext : Π(A : Type). Π(B : A → Type).
     *          Π(f : Π(x:A). B x). Π(g : Π(x:A). B x).
     *          (Π(x : A). Id (B x) (f x) (g x))
     *          → Id (Π(x:A). B x) f g                    */
    Term *ty = parse(&funext_arena,
        "Π(A : Type). Π(B : Π(_ : A). Type)."
        " Π(f : Π(x : A). B x). Π(g : Π(x : A). B x)."
        " Π(_ : Π(x : A). Id (B x) (f x) (g x))."
        " Id (Π(x : A). B x) f g");
    if (!ty) { fprintf(stderr, "internal: funext type parse failed\n"); exit(1); }
    funext_type_v = nbe_eval(&funext_arena, NULL, ty);
    return funext_type_v;
}

/* ── TCtx lookup */

static Val *tctx_lookup(TCtx *ctx, int idx) {
    for (; ctx && idx > 0; ctx = ctx->next, idx--);
    return ctx ? ctx->type : NULL;
}

/* Convert TCtx to Ctx (names only) for pretty-printing. */
static Ctx *tctx_to_ctx(Arena *a, TCtx *tc) {
    if (!tc) return NULL;
    Ctx *c = (Ctx *)arena_alloc(a, sizeof(Ctx));
    c->name = tc->name;
    c->next = tctx_to_ctx(a, tc->next);
    return c;
}

/* ── Conversion */

static int conv_spine(Arena *a, int depth, Spine *sp1, Spine *sp2);

int conv(Arena *a, int depth, Val *u, Val *v) {
    /* Eta for functions */
    if (u->tag == VL_LAM || v->tag == VL_LAM) {
        ValTag other = (u->tag == VL_LAM) ? v->tag : u->tag;
        if (other != VL_LAM && other != VL_NEUTRAL) return 0;
        Val *fresh = vl_neutral(a, depth, NULL);
        return conv(a, depth + 1, nbe_vapp(a, u, fresh), nbe_vapp(a, v, fresh));
    }
    /* Eta for pairs: (a, b) ≡ p  iff  fst p ≡ a  and  snd p ≡ b */
    if (u->tag == VL_PAIR || v->tag == VL_PAIR) {
        ValTag other = (u->tag == VL_PAIR) ? v->tag : u->tag;
        if (other != VL_PAIR && other != VL_NEUTRAL) return 0;
        return conv(a, depth, nbe_vfst(a, u), nbe_vfst(a, v)) &&
               conv(a, depth, nbe_vsnd(a, u), nbe_vsnd(a, v));
    }
    if (u->tag != v->tag) return 0;
    switch (u->tag) {
    case VL_UNI:
        return u->ulevel == v->ulevel;
    case VL_PI:
    case VL_SIGMA: {
        if (!conv(a, depth, u->pi.dom, v->pi.dom)) return 0;
        Val *fresh = vl_neutral(a, depth, NULL);
        Val *uc = nbe_eval(a, env_cons(a, fresh, u->pi.env), u->pi.cod);
        Val *vc = nbe_eval(a, env_cons(a, fresh, v->pi.env), v->pi.cod);
        return conv(a, depth + 1, uc, vc);
    }
    case VL_NEUTRAL:
        if (u->neutral.lvl != v->neutral.lvl) return 0;
        return conv_spine(a, depth, u->neutral.spine, v->neutral.spine);
    case VL_ID:
        return conv(a, depth, u->id.ty,  v->id.ty)  &&
               conv(a, depth, u->id.lhs, v->id.lhs) &&
               conv(a, depth, u->id.rhs, v->id.rhs);
    case VL_REFL:
        return conv(a, depth, u->refl, v->refl);
    case VL_NAT:
    case VL_ZERO:
    case VL_BOOL:
    case VL_TRUE:
    case VL_FALSE:
    case VL_EMPTY:
    case VL_UNIT:
    case VL_STAR:
        return 1;  /* canonical constants — equal to themselves */
    case VL_SUM:
        return conv(a, depth, u->pair.fst, v->pair.fst) &&
               conv(a, depth, u->pair.snd, v->pair.snd);
    case VL_INL:
    case VL_INR:
        return conv(a, depth, u->inj, v->inj);
    case VL_SUCC:
        return conv(a, depth, u->succ, v->succ);
    case VL_W: {
        if (!conv(a, depth, u->pi.dom, v->pi.dom)) return 0;
        Val *fresh = vl_neutral(a, depth, NULL);
        Val *uc = nbe_eval(a, env_cons(a, fresh, u->pi.env), u->pi.cod);
        Val *vc = nbe_eval(a, env_cons(a, fresh, v->pi.env), v->pi.cod);
        return conv(a, depth + 1, uc, vc);
    }
    case VL_SUP:
        return conv(a, depth, u->pair.fst, v->pair.fst) &&
               conv(a, depth, u->pair.snd, v->pair.snd);
    case VL_LAM:
    case VL_PAIR:
        return 0;  /* unreachable: handled by eta cases above */
    default:
        fprintf(stderr, "conv: unhandled val tag %d\n", u->tag);
        exit(1);
    }
}

static int conv_spine(Arena *a, int depth, Spine *sp1, Spine *sp2) {
    if (!sp1 && !sp2) return 1;
    if (!sp1 || !sp2) return 0;
    if (sp1->kind != sp2->kind) return 0;
    if (sp1->kind == SP_APP) {
        if (!conv(a, depth, sp1->val, sp2->val)) return 0;
    } else if (sp1->kind == SP_NATREC) {
        if (!conv(a, depth, sp1->natrec.motive, sp2->natrec.motive)) return 0;
        if (!conv(a, depth, sp1->natrec.base,   sp2->natrec.base))   return 0;
        if (!conv(a, depth, sp1->natrec.step,   sp2->natrec.step))   return 0;
    } else if (sp1->kind == SP_BOOLREC) {
        if (!conv(a, depth, sp1->boolrec.motive, sp2->boolrec.motive)) return 0;
        if (!conv(a, depth, sp1->boolrec.tcase,  sp2->boolrec.tcase))  return 0;
        if (!conv(a, depth, sp1->boolrec.fcase,  sp2->boolrec.fcase))  return 0;
    } else if (sp1->kind == SP_J) {
        if (!conv(a, depth, sp1->j.ty,       sp2->j.ty))       return 0;
        if (!conv(a, depth, sp1->j.lhs,      sp2->j.lhs))      return 0;
        if (!conv(a, depth, sp1->j.motive,   sp2->j.motive))   return 0;
        if (!conv(a, depth, sp1->j.base,     sp2->j.base))     return 0;
        if (!conv(a, depth, sp1->j.endpoint, sp2->j.endpoint)) return 0;
    } else if (sp1->kind == SP_WREC) {
        if (!conv(a, depth, sp1->wrec.motive, sp2->wrec.motive)) return 0;
        if (!conv(a, depth, sp1->wrec.step,   sp2->wrec.step))   return 0;
    } else if (sp1->kind == SP_ABORT) {
        if (!conv(a, depth, sp1->abort_s.motive, sp2->abort_s.motive)) return 0;
    } else if (sp1->kind == SP_UNITREC) {
        if (!conv(a, depth, sp1->unitrec_s.motive, sp2->unitrec_s.motive)) return 0;
        if (!conv(a, depth, sp1->unitrec_s.base,   sp2->unitrec_s.base))   return 0;
    } else if (sp1->kind == SP_CASESPLIT) {
        if (!conv(a, depth, sp1->casesplit_s.motive, sp2->casesplit_s.motive)) return 0;
        if (!conv(a, depth, sp1->casesplit_s.lcase,  sp2->casesplit_s.lcase))  return 0;
        if (!conv(a, depth, sp1->casesplit_s.rcase,  sp2->casesplit_s.rcase))  return 0;
    }
    /* SP_FST, SP_SND: no payload — kind equality (checked above) is sufficient. */
    return conv_spine(a, depth, sp1->next, sp2->next);
}

/* ── Helpers */

static int as_universe(Val *v, int *level) {
    if (!v || v->tag != VL_UNI) return 0;
    *level = v->ulevel; return 1;
}
static int imax(int a, int b) { return a > b ? a : b; }

/* ── Infer */

Val *infer(Arena *a, int depth, TCtx *tctx, Env *env, Term *t) {
    switch (t->tag) {

    case TM_VAR: {
        Val *ty = tctx_lookup(tctx, t->idx);
        if (!ty) {
            fprintf(stderr, "type error: variable at index %d out of scope\n", t->idx);
            return NULL;
        }
        return ty;
    }

    case TM_UNI:
        return vl_uni(a, t->ulevel + 1);

    case TM_PI:
    case TM_SIG: {
        /* Π/Σ(x : A). B  :  Type_{max(i,j)} */
        Val *dty = infer(a, depth, tctx, env, t->pi.dom);
        if (!dty) return NULL;
        int i;
        if (!as_universe(dty, &i)) {
            fprintf(stderr, "type error: %s domain is not a type\n",
                    t->tag == TM_PI ? "Π" : "Σ");
            return NULL;
        }
        Val *domv  = nbe_eval(a, env, t->pi.dom);
        Val *fresh = vl_neutral(a, depth, NULL);
        TCtx ext   = { t->pi.name, domv, tctx };
        Val *cty   = infer(a, depth + 1, &ext, env_cons(a, fresh, env), t->pi.cod);
        if (!cty) return NULL;
        int j;
        if (!as_universe(cty, &j)) {
            fprintf(stderr, "type error: %s codomain is not a type\n",
                    t->tag == TM_PI ? "Π" : "Σ");
            return NULL;
        }
        return vl_uni(a, imax(i, j));
    }

    case TM_APP: {
        Val *fty = infer(a, depth, tctx, env, t->app.fun);
        if (!fty) return NULL;
        if (fty->tag != VL_PI) {
            fprintf(stderr, "type error: applied non-function\n");
            return NULL;
        }
        if (!check(a, depth, tctx, env, t->app.arg, fty->pi.dom)) return NULL;
        Val *argv = nbe_eval(a, env, t->app.arg);
        return nbe_eval(a, env_cons(a, argv, fty->pi.env), fty->pi.cod);
    }

    case TM_FST: {
        Val *pty = infer(a, depth, tctx, env, t->elim);
        if (!pty) return NULL;
        if (pty->tag != VL_SIGMA) {
            fprintf(stderr, "type error: fst applied to non-Σ type\n");
            return NULL;
        }
        return pty->pi.dom;
    }

    case TM_SND: {
        Val *pty = infer(a, depth, tctx, env, t->elim);
        if (!pty) return NULL;
        if (pty->tag != VL_SIGMA) {
            fprintf(stderr, "type error: snd applied to non-Σ type\n");
            return NULL;
        }
        /* snd p : B(fst p) — instantiate codomain with fst of the pair */
        Val *pv  = nbe_eval(a, env, t->elim);
        Val *fst = nbe_vfst(a, pv);
        return nbe_eval(a, env_cons(a, fst, pty->pi.env), pty->pi.cod);
    }

    case TM_ANN: {
        Val *tty = infer(a, depth, tctx, env, t->ann.type);
        if (!tty) return NULL;
        int ignored;
        if (!as_universe(tty, &ignored)) {
            fprintf(stderr, "type error: annotation is not a type\n");
            return NULL;
        }
        Val *tyv = nbe_eval(a, env, t->ann.type);
        if (!check(a, depth, tctx, env, t->ann.term, tyv)) return NULL;
        return tyv;
    }

    case TM_ID: {
        /* Id(A, a, b) : Type_i  where  A : Type_i */
        Val *Aty = infer(a, depth, tctx, env, t->id.ty);
        if (!Aty) return NULL;
        int i;
        if (!as_universe(Aty, &i)) {
            fprintf(stderr, "type error: Id type argument is not a type\n");
            return NULL;
        }
        Val *A_val = nbe_eval(a, env, t->id.ty);
        if (!check(a, depth, tctx, env, t->id.lhs, A_val)) return NULL;
        if (!check(a, depth, tctx, env, t->id.rhs, A_val)) return NULL;
        return vl_uni(a, i);
    }

    case TM_REFL: {
        /* refl(a) : Id(infer(a), a, a) */
        Val *aty = infer(a, depth, tctx, env, t->refl);
        if (!aty) return NULL;
        Val *av = nbe_eval(a, env, t->refl);
        return vl_id(a, aty, av, av);
    }

    case TM_J: {
        /* J A a P d b p : P b p
         * A : Type_i,  a : A,  P : Π(b:A). Id(A,a,b) → Type_k,
         * d : P a (refl a),  b : A,  p : Id(A,a,b)               */
        Val *Aty = infer(a, depth, tctx, env, t->j.ty);
        if (!Aty) return NULL;
        int i;
        if (!as_universe(Aty, &i)) {
            fprintf(stderr, "type error: J: first argument is not a type\n");
            return NULL;
        }
        Val *A_val = nbe_eval(a, env, t->j.ty);
        if (!check(a, depth, tctx, env, t->j.lhs, A_val)) return NULL;
        Val *a_val = nbe_eval(a, env, t->j.lhs);

        /* Check P : Π(b:A). Id(A,a,b) → Type_k */
        Val *P_ty = infer(a, depth, tctx, env, t->j.motive);
        if (!P_ty) return NULL;
        if (P_ty->tag != VL_PI) {
            fprintf(stderr, "type error: J: motive is not a function\n");
            return NULL;
        }
        if (!conv(a, depth, P_ty->pi.dom, A_val)) {
            fprintf(stderr, "type error: J: motive domain does not match A\n");
            return NULL;
        }
        Val *fresh_b = vl_neutral(a, depth, NULL);
        Val *P_cod   = nbe_eval(a, env_cons(a, fresh_b, P_ty->pi.env), P_ty->pi.cod);
        if (P_cod->tag != VL_PI) {
            fprintf(stderr, "type error: J: motive codomain is not a function\n");
            return NULL;
        }
        Val *exp_id = vl_id(a, A_val, a_val, fresh_b);
        if (!conv(a, depth + 1, P_cod->pi.dom, exp_id)) {
            fprintf(stderr, "type error: J: motive second argument is not Id(A,a,b)\n");
            return NULL;
        }
        Val *fresh_p  = vl_neutral(a, depth + 1, NULL);
        Val *P_result = nbe_eval(a, env_cons(a, fresh_p, P_cod->pi.env), P_cod->pi.cod);
        int k;
        if (!as_universe(P_result, &k)) {
            fprintf(stderr, "type error: J: motive does not map into a universe\n");
            return NULL;
        }

        /* Check d : P a (refl a) */
        Val *P_val  = nbe_eval(a, env, t->j.motive);
        Val *d_ty   = nbe_vapp(a, nbe_vapp(a, P_val, a_val), vl_refl(a, a_val));
        if (!check(a, depth, tctx, env, t->j.base, d_ty)) return NULL;

        /* Check b : A and p : Id(A,a,b) */
        if (!check(a, depth, tctx, env, t->j.endpoint, A_val)) return NULL;
        Val *b_val = nbe_eval(a, env, t->j.endpoint);
        Val *id_ty = vl_id(a, A_val, a_val, b_val);
        if (!check(a, depth, tctx, env, t->j.proof, id_ty)) return NULL;
        Val *p_val = nbe_eval(a, env, t->j.proof);

        return nbe_vapp(a, nbe_vapp(a, P_val, b_val), p_val);
    }

    case TM_NAT:
        return vl_uni(a, 0);  /* Nat : Type */

    case TM_ZERO:
        return vl_nat(a);

    case TM_SUCC: {
        if (!check(a, depth, tctx, env, t->elim, vl_nat(a))) return NULL;
        return vl_nat(a);
    }

    case TM_NATREC: {
        /* natrec P z s n : P n
         * P : Nat → Type_i,  z : P zero,
         * s : Π(m:Nat). P m → P(succ m),  n : Nat     */
        Val *P_ty = infer(a, depth, tctx, env, t->natrec.motive);
        if (!P_ty) return NULL;
        if (P_ty->tag != VL_PI) {
            fprintf(stderr, "type error: natrec: motive is not a function\n");
            return NULL;
        }
        if (!conv(a, depth, P_ty->pi.dom, vl_nat(a))) {
            fprintf(stderr, "type error: natrec: motive domain is not Nat\n");
            return NULL;
        }
        Val *fresh0 = vl_neutral(a, depth, NULL);
        Val *P_cod  = nbe_eval(a, env_cons(a, fresh0, P_ty->pi.env), P_ty->pi.cod);
        int i;
        if (!as_universe(P_cod, &i)) {
            fprintf(stderr, "type error: natrec: motive does not map into a universe\n");
            return NULL;
        }
        Val *P_val = nbe_eval(a, env, t->natrec.motive);
        /* Check z : P zero */
        if (!check(a, depth, tctx, env, t->natrec.base,
                   nbe_vapp(a, P_val, vl_zero(a)))) return NULL;
        /* Check s : Π(m:Nat). P m → P(succ m)
         * Infer s's type and verify its structure structurally. */
        Val *s_ity = infer(a, depth, tctx, env, t->natrec.step);
        if (!s_ity) return NULL;
        if (s_ity->tag != VL_PI) {
            fprintf(stderr, "type error: natrec: step is not a function\n");
            return NULL;
        }
        if (!conv(a, depth, s_ity->pi.dom, vl_nat(a))) {
            fprintf(stderr, "type error: natrec: step domain is not Nat\n");
            return NULL;
        }
        Val *fresh_m = vl_neutral(a, depth, NULL);    /* outer Pi var (m : Nat) */
        Val *s_cod   = nbe_eval(a, env_cons(a, fresh_m, s_ity->pi.env), s_ity->pi.cod);
        if (s_cod->tag != VL_PI) {
            fprintf(stderr, "type error: natrec: step codomain is not a function\n");
            return NULL;
        }
        Val *P_m = nbe_vapp(a, P_val, fresh_m);
        if (!conv(a, depth + 1, s_cod->pi.dom, P_m)) {
            fprintf(stderr, "type error: natrec: step arg type is not P m\n");
            return NULL;
        }
        Val *fresh_pm = vl_neutral(a, depth + 1, NULL); /* inner Pi var (r : P m) */
        Val *s_result = nbe_eval(a, env_cons(a, fresh_pm, s_cod->pi.env), s_cod->pi.cod);
        if (!conv(a, depth + 2, s_result, nbe_vapp(a, P_val, vl_succ(a, fresh_m)))) {
            fprintf(stderr, "type error: natrec: step return type is not P(succ m)\n");
            return NULL;
        }
        /* Check n : Nat */
        if (!check(a, depth, tctx, env, t->natrec.scrut, vl_nat(a))) return NULL;
        return nbe_vapp(a, P_val, nbe_eval(a, env, t->natrec.scrut));
    }

    case TM_BOOL:
        return vl_uni(a, 0);  /* Bool : Type */

    case TM_TRUE:
        return vl_bool(a);

    case TM_FALSE:
        return vl_bool(a);

    case TM_BOOLREC: {
        /* boolrec P pt pf b : P b
         * P : Bool → Type_i,  pt : P true,  pf : P false,  b : Bool */
        Val *P_ty = infer(a, depth, tctx, env, t->boolrec.motive);
        if (!P_ty) return NULL;
        if (P_ty->tag != VL_PI) {
            fprintf(stderr, "type error: boolrec: motive is not a function\n");
            return NULL;
        }
        if (!conv(a, depth, P_ty->pi.dom, vl_bool(a))) {
            fprintf(stderr, "type error: boolrec: motive domain is not Bool\n");
            return NULL;
        }
        Val *fresh = vl_neutral(a, depth, NULL);
        Val *P_cod = nbe_eval(a, env_cons(a, fresh, P_ty->pi.env), P_ty->pi.cod);
        int i;
        if (!as_universe(P_cod, &i)) {
            fprintf(stderr, "type error: boolrec: motive does not map into a universe\n");
            return NULL;
        }
        Val *P_val = nbe_eval(a, env, t->boolrec.motive);
        if (!check(a, depth, tctx, env, t->boolrec.tcase,
                   nbe_vapp(a, P_val, vl_true(a))))  return NULL;
        if (!check(a, depth, tctx, env, t->boolrec.fcase,
                   nbe_vapp(a, P_val, vl_false(a)))) return NULL;
        if (!check(a, depth, tctx, env, t->boolrec.scrut, vl_bool(a))) return NULL;
        return nbe_vapp(a, P_val, nbe_eval(a, env, t->boolrec.scrut));
    }

    case TM_UNIT:
        return vl_uni(a, 0);  /* Unit : Type */

    case TM_STAR:
        return vl_unit(a);    /* star : Unit */

    case TM_UNITREC: {
        /* unitrec P ps s : P s
         * P : Unit → Type_i,  ps : P star,  s : Unit         */
        Val *P_ty = infer(a, depth, tctx, env, t->unitrec_t.motive);
        if (!P_ty) return NULL;
        if (P_ty->tag != VL_PI) {
            fprintf(stderr, "type error: unitrec: motive is not a function\n");
            return NULL;
        }
        if (!conv(a, depth, P_ty->pi.dom, vl_unit(a))) {
            fprintf(stderr, "type error: unitrec: motive domain is not Unit\n");
            return NULL;
        }
        Val *fresh = vl_neutral(a, depth, NULL);
        Val *P_cod = nbe_eval(a, env_cons(a, fresh, P_ty->pi.env), P_ty->pi.cod);
        int i;
        if (!as_universe(P_cod, &i)) {
            fprintf(stderr, "type error: unitrec: motive does not map into a universe\n");
            return NULL;
        }
        Val *P_val = nbe_eval(a, env, t->unitrec_t.motive);
        if (!check(a, depth, tctx, env, t->unitrec_t.base,
                   nbe_vapp(a, P_val, vl_star(a)))) return NULL;
        if (!check(a, depth, tctx, env, t->unitrec_t.scrut, vl_unit(a))) return NULL;
        return nbe_vapp(a, P_val, nbe_eval(a, env, t->unitrec_t.scrut));
    }

    case TM_EMPTY:
        return vl_uni(a, 0);  /* Empty : Type */

    case TM_ABORT: {
        /* abort A e : A
         * A : Type_i  (any level),  e : Empty              */
        Val *Aty = infer(a, depth, tctx, env, t->abort_t.motive);
        if (!Aty) return NULL;
        int i;
        if (!as_universe(Aty, &i)) {
            fprintf(stderr, "type error: abort: first argument is not a type\n");
            return NULL;
        }
        Val *A_val = nbe_eval(a, env, t->abort_t.motive);
        if (!check(a, depth, tctx, env, t->abort_t.scrut, vl_empty(a))) return NULL;
        return A_val;
    }

    case TM_SUM: {
        /* Sum A B : Type_{max(i,j)} */
        Val *Aty = infer(a, depth, tctx, env, t->sum_t.left);
        if (!Aty) return NULL;
        int i;
        if (!as_universe(Aty, &i)) {
            fprintf(stderr, "type error: Sum left type is not a type\n");
            return NULL;
        }
        Val *Bty = infer(a, depth, tctx, env, t->sum_t.right);
        if (!Bty) return NULL;
        int j;
        if (!as_universe(Bty, &j)) {
            fprintf(stderr, "type error: Sum right type is not a type\n");
            return NULL;
        }
        return vl_uni(a, imax(i, j));
    }

    case TM_INL:
        fprintf(stderr,
            "type error: cannot infer type of inl — wrap in annotation: ((inl a) : Sum A B)\n");
        return NULL;

    case TM_INR:
        fprintf(stderr,
            "type error: cannot infer type of inr — wrap in annotation: ((inr b) : Sum A B)\n");
        return NULL;

    case TM_CASESPLIT: {
        /* case P fl fr s : P s
         * P : Sum A B → Type_k
         * fl : Π(a:A). P (inl a)
         * fr : Π(b:B). P (inr b)
         * s : Sum A B                             */
        Val *P_ty = infer(a, depth, tctx, env, t->casesplit_t.motive);
        if (!P_ty) return NULL;
        if (P_ty->tag != VL_PI) {
            fprintf(stderr, "type error: case: motive is not a function\n");
            return NULL;
        }
        Val *Sum_ty = P_ty->pi.dom;
        if (Sum_ty->tag != VL_SUM) {
            fprintf(stderr, "type error: case: motive domain is not a Sum type\n");
            return NULL;
        }
        Val *A = Sum_ty->pair.fst;
        Val *B = Sum_ty->pair.snd;
        {
            Val *fresh = vl_neutral(a, depth, NULL);
            Val *P_cod = nbe_eval(a, env_cons(a, fresh, P_ty->pi.env), P_ty->pi.cod);
            int k;
            if (!as_universe(P_cod, &k)) {
                fprintf(stderr, "type error: case: motive codomain is not a universe\n");
                return NULL;
            }
        }
        Val *P_val = nbe_eval(a, env, t->casesplit_t.motive);
        /* Check fl : Π(a:A). P(inl a)
         * Synthetic Pi: cod = APP(VAR 1, INL(VAR 0)), env = [P_val]
         * so when opened with fresh_a: VAR 0 = fresh_a, VAR 1 = P_val */
        Val *fl_exp = vl_pi(a, "a", A,
                            env_cons(a, P_val, NULL),
                            tm_app(a, tm_var(a, 1), tm_inl(a, tm_var(a, 0))));
        if (!check(a, depth, tctx, env, t->casesplit_t.lcase, fl_exp)) return NULL;
        /* Check fr : Π(b:B). P(inr b) */
        Val *fr_exp = vl_pi(a, "b", B,
                            env_cons(a, P_val, NULL),
                            tm_app(a, tm_var(a, 1), tm_inr(a, tm_var(a, 0))));
        if (!check(a, depth, tctx, env, t->casesplit_t.rcase, fr_exp)) return NULL;
        /* Check s : Sum A B */
        if (!check(a, depth, tctx, env, t->casesplit_t.scrut, Sum_ty)) return NULL;
        Val *s_val = nbe_eval(a, env, t->casesplit_t.scrut);
        return nbe_vapp(a, P_val, s_val);
    }

    case TM_W: {
        /* W(x:A).B(x) : Type_{max(i,j)} — same rule as Π/Σ */
        Val *dty = infer(a, depth, tctx, env, t->pi.dom);
        if (!dty) return NULL;
        int i;
        if (!as_universe(dty, &i)) {
            fprintf(stderr, "type error: W domain is not a type\n");
            return NULL;
        }
        Val *domv  = nbe_eval(a, env, t->pi.dom);
        Val *fresh = vl_neutral(a, depth, NULL);
        TCtx ext   = { t->pi.name, domv, tctx };
        Val *cty   = infer(a, depth + 1, &ext, env_cons(a, fresh, env), t->pi.cod);
        if (!cty) return NULL;
        int j;
        if (!as_universe(cty, &j)) {
            fprintf(stderr, "type error: W codomain is not a type\n");
            return NULL;
        }
        return vl_uni(a, imax(i, j));
    }

    case TM_WREC: {
        /* wrec P s w : P w
         * P : W(x:A).B(x) → Type_k
         * s : Π(a:A). Π(f:B(a)→W). Π(ih:Π(b:B(a)).P(f b)). P(sup a f)
         * w : W(x:A).B(x)
         */
        Val *P_ty = infer(a, depth, tctx, env, t->wrec.motive);
        if (!P_ty) return NULL;
        if (P_ty->tag != VL_PI) {
            fprintf(stderr, "type error: wrec: motive is not a function\n");
            return NULL;
        }
        Val *W_ty = P_ty->pi.dom;
        if (W_ty->tag != VL_W) {
            fprintf(stderr, "type error: wrec: motive domain is not a W type\n");
            return NULL;
        }
        {
            Val *fresh = vl_neutral(a, depth, NULL);
            Val *pcod  = nbe_eval(a, env_cons(a, fresh, P_ty->pi.env), P_ty->pi.cod);
            int kk;
            if (!as_universe(pcod, &kk)) {
                fprintf(stderr, "type error: wrec: motive codomain is not a universe\n");
                return NULL;
            }
        }
        Val *P_val = nbe_eval(a, env, t->wrec.motive);
        Val *A     = W_ty->pi.dom;

        /* Check step s structurally */
        Val *s_ity = infer(a, depth, tctx, env, t->wrec.step);
        if (!s_ity) return NULL;
        if (s_ity->tag != VL_PI) {
            fprintf(stderr, "type error: wrec: step is not a function\n");
            return NULL;
        }
        if (!conv(a, depth, s_ity->pi.dom, A)) {
            fprintf(stderr, "type error: wrec: step domain is not A\n");
            return NULL;
        }
        int d = depth;
        Val *fa    = vl_neutral(a, d++, NULL);   /* fa : A */
        Val *B_fa  = nbe_eval(a, env_cons(a, fa, W_ty->pi.env), W_ty->pi.cod);
        Val *s_cod1 = nbe_eval(a, env_cons(a, fa, s_ity->pi.env), s_ity->pi.cod);

        /* s_cod1 : Π(f: B(fa)→W). ... */
        if (s_cod1->tag != VL_PI) {
            fprintf(stderr, "type error: wrec: step second argument missing\n");
            return NULL;
        }
        Val *f_ty = s_cod1->pi.dom;
        if (f_ty->tag != VL_PI) {
            fprintf(stderr, "type error: wrec: step arg 2 is not B(a)→W\n");
            return NULL;
        }
        if (!conv(a, d, f_ty->pi.dom, B_fa)) {
            fprintf(stderr, "type error: wrec: step arg 2 domain is not B(a)\n");
            return NULL;
        }
        Val *fb1   = vl_neutral(a, d++, NULL);   /* fb1 : B(fa) — opens f_ty cod */
        Val *f_cod = nbe_eval(a, env_cons(a, fb1, f_ty->pi.env), f_ty->pi.cod);
        if (!conv(a, d, f_cod, W_ty)) {
            fprintf(stderr, "type error: wrec: step arg 2 codomain is not W\n");
            return NULL;
        }
        Val *ff    = vl_neutral(a, d++, NULL);   /* ff : B(fa)→W */
        Val *s_cod2 = nbe_eval(a, env_cons(a, ff, s_cod1->pi.env), s_cod1->pi.cod);

        /* s_cod2 : Π(ih: Π(b:B(fa)).P(ff b)). ... */
        if (s_cod2->tag != VL_PI) {
            fprintf(stderr, "type error: wrec: step third argument missing\n");
            return NULL;
        }
        Val *ih_ty = s_cod2->pi.dom;
        if (ih_ty->tag != VL_PI) {
            fprintf(stderr, "type error: wrec: step arg 3 is not Π(b:B(a)).P(f b)\n");
            return NULL;
        }
        if (!conv(a, d, ih_ty->pi.dom, B_fa)) {
            fprintf(stderr, "type error: wrec: step arg 3 domain is not B(a)\n");
            return NULL;
        }
        Val *fb2    = vl_neutral(a, d++, NULL);   /* fb2 : B(fa) — opens ih cod */
        Val *ih_cod = nbe_eval(a, env_cons(a, fb2, ih_ty->pi.env), ih_ty->pi.cod);
        if (!conv(a, d, ih_cod, nbe_vapp(a, P_val, nbe_vapp(a, ff, fb2)))) {
            fprintf(stderr, "type error: wrec: step arg 3 codomain is not P(f b)\n");
            return NULL;
        }
        Val *fih    = vl_neutral(a, d++, NULL);   /* fih : ih type */
        Val *s_res  = nbe_eval(a, env_cons(a, fih, s_cod2->pi.env), s_cod2->pi.cod);
        Val *sup_af = vl_sup(a, fa, ff);
        if (!conv(a, d, s_res, nbe_vapp(a, P_val, sup_af))) {
            fprintf(stderr, "type error: wrec: step result is not P(sup a f)\n");
            return NULL;
        }

        /* Check w : W(x:A).B(x) */
        if (!check(a, depth, tctx, env, t->wrec.scrut, W_ty)) return NULL;
        Val *w_val = nbe_eval(a, env, t->wrec.scrut);
        return nbe_vapp(a, P_val, w_val);
    }

    case TM_UA:
        return get_ua_type();

    case TM_FUNEXT:
        return get_funext_type();

    case TM_GLOBAL:
        return def_get(t->idx)->type;

    case TM_LAM:
        fprintf(stderr,
            "type error: cannot infer type of λ — wrap in annotation: (\\%s. ... : Π(%s:T). ...)\n",
            t->lam.name, t->lam.name);
        return NULL;

    case TM_PAIR:
        fprintf(stderr,
            "type error: cannot infer type of pair — wrap in annotation: ((a, b) : Σ(x:A). B)\n");
        return NULL;

    case TM_SUP:
        fprintf(stderr,
            "type error: cannot infer type of sup — wrap in annotation: "
            "((sup a f) : W(x:A). B)\n");
        return NULL;

    default:
        fprintf(stderr, "infer: unhandled term tag %d\n", t->tag);
        exit(1);
    }
}

/* ── Check */

int check(Arena *a, int depth, TCtx *tctx, Env *env, Term *t, Val *ty) {
    /* Lambda checks against Pi */
    if (t->tag == TM_LAM) {
        if (ty->tag != VL_PI) {
            fprintf(stderr, "type error: expected Π type when checking λ\n");
            return 0;
        }
        Val *fresh = vl_neutral(a, depth, NULL);
        Val *codv  = nbe_eval(a, env_cons(a, fresh, ty->pi.env), ty->pi.cod);
        TCtx ext   = { t->lam.name, ty->pi.dom, tctx };
        return check(a, depth + 1, &ext, env_cons(a, fresh, env), t->lam.body, codv);
    }
    /* sup checks against W */
    if (t->tag == TM_SUP) {
        if (ty->tag != VL_W) {
            fprintf(stderr, "type error: expected W type when checking sup\n");
            return 0;
        }
        Val *A = ty->pi.dom;
        if (!check(a, depth, tctx, env, t->sup.label, A)) return 0;
        Val *a_val = nbe_eval(a, env, t->sup.label);
        Val *B_a   = nbe_eval(a, env_cons(a, a_val, ty->pi.env), ty->pi.cod);
        /* Build expected type for children: Π(_:B(a)). W(x:A).B(x)
         * Closure env = [ty], body = TM_VAR(1) — so VAR(1) in [b, ty] = ty.
         * This constant codomain lets unannotated lambdas be accepted.       */
        Val *f_exp_ty = vl_pi(a, "_", B_a, env_cons(a, ty, NULL), tm_var(a, 1));
        return check(a, depth, tctx, env, t->sup.children, f_exp_ty);
    }
    /* Pair checks against Sigma */
    if (t->tag == TM_PAIR) {
        if (ty->tag != VL_SIGMA) {
            fprintf(stderr, "type error: expected Σ type when checking pair\n");
            return 0;
        }
        if (!check(a, depth, tctx, env, t->pair.fst, ty->pi.dom)) return 0;
        Val *fstv = nbe_eval(a, env, t->pair.fst);
        Val *sndt = nbe_eval(a, env_cons(a, fstv, ty->pi.env), ty->pi.cod);
        return check(a, depth, tctx, env, t->pair.snd, sndt);
    }
    /* inl/inr check against Sum */
    if (t->tag == TM_INL) {
        if (ty->tag != VL_SUM) {
            fprintf(stderr, "type error: expected Sum type when checking inl\n");
            return 0;
        }
        return check(a, depth, tctx, env, t->elim, ty->pair.fst);
    }
    if (t->tag == TM_INR) {
        if (ty->tag != VL_SUM) {
            fprintf(stderr, "type error: expected Sum type when checking inr\n");
            return 0;
        }
        return check(a, depth, tctx, env, t->elim, ty->pair.snd);
    }
    /* Everything else: infer and convert */
    Val *ity = infer(a, depth, tctx, env, t);
    if (!ity) return 0;
    if (!conv(a, depth, ity, ty)) {
        Ctx *ctx = tctx_to_ctx(a, tctx);
        fprintf(stderr, "type error: type mismatch\n");
        fprintf(stderr, "  inferred: "); term_fprint_ctx(stderr, nbe_quote(a, depth, ity), ctx, 0); fprintf(stderr, "\n");
        fprintf(stderr, "  expected: "); term_fprint_ctx(stderr, nbe_quote(a, depth, ty),  ctx, 0); fprintf(stderr, "\n");
        return 0;
    }
    return 1;
}

/* ── Pretty-print */

void val_print_tctx(Arena *a, Val *v, int depth, TCtx *tctx) {
    term_fprint_ctx(stdout, nbe_quote(a, depth, v), tctx_to_ctx(a, tctx), 0);
}
