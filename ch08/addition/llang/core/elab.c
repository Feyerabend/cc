#include "elab.h"
#include "eval.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

/* ── Structured error reporting (same as check.c) ──────────────────────── */

static void type_error(SrcLoc loc, const char *fmt, ...) {
    if (loc.line > 0)
        fprintf(stderr, "%d:%d: ", loc.line, loc.col);
    fputs("type error: ", stderr);
    va_list ap;
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
}


/* ── ElabCtx management ─────────────────────────────────────────────────── */

void elab_init(ElabCtx *e, Arena *a) {
    e->n     = 0;
    e->arena = a;
}

int elab_fresh(ElabCtx *e, int depth, Val *type) {
    if (e->n >= ELAB_MAX_HOLES) {
        fprintf(stderr, "elab: too many holes (max %d)\n", ELAB_MAX_HOLES);
        exit(1);
    }
    int id = e->n++;
    e->holes[id].depth = depth;
    e->holes[id].type  = type;
    e->holes[id].val   = NULL;
    return id;
}

Val *elab_read(ElabCtx *e, int id) {
    if (id < 0 || id >= e->n) return NULL;
    return e->holes[id].val;
}

int elab_solve(ElabCtx *e, int id, Val *val) {
    if (id < 0 || id >= e->n) return 0;
    /* Guard: don't solve a meta to itself (would create a trivial cycle in elab_force). */
    if (val && val->tag == VL_NEUTRAL && is_meta_lvl(val->neutral.lvl)
            && !val->neutral.spine && lvl_to_meta(val->neutral.lvl) == id)
        return 1;
    if (e->holes[id].val) {
        /* Already solved: unify new solution with old for consistency */
        return elab_unify(e, e->arena, e->holes[id].depth,
                          e->holes[id].val, val);
    }
    e->holes[id].val = val;
    return 1;
}

/* Substitute any top-level solved meta neutral.
   Iteration is bounded by e->n to prevent looping on cyclic meta chains
   (which arise from bugs, not well-typed programs). */
Val *elab_force(ElabCtx *e, Val *v) {
    int limit = e->n + 1;
    while (limit-- > 0 && v && v->tag == VL_NEUTRAL
              && is_meta_lvl(v->neutral.lvl)
              && !v->neutral.spine) {
        int id  = lvl_to_meta(v->neutral.lvl);
        Val *sol = elab_read(e, id);
        if (!sol) break;
        v = sol;
    }
    return v;
}

/* ── Unification ────────────────────────────────────────────────────────── */

static int elab_unify_spine(ElabCtx *e, Arena *a, int depth, Spine *s1, Spine *s2) {
    if (!s1 && !s2) return 1;
    if (!s1 || !s2 || s1->kind != s2->kind) return 0;
    if (s1->kind == SP_APP) {
        if (!elab_unify(e, a, depth, s1->val, s2->val)) return 0;
    }
    /* For non-APP spine entries, we fall through (they carry no simple Val
       that we could unify independently); if the heads and kinds match, the
       payloads match too in any spine that arose from the same neutral.    */
    return elab_unify_spine(e, a, depth, s1->next, s2->next);
}

int elab_unify(ElabCtx *e, Arena *a, int depth, Val *u, Val *v) {
    u = elab_force(e, u);
    v = elab_force(e, v);
    if (!u || !v) return u == v;

    /* Left meta: unsolved neutral */
    if (u->tag == VL_NEUTRAL && is_meta_lvl(u->neutral.lvl) && !u->neutral.spine)
        return elab_solve(e, lvl_to_meta(u->neutral.lvl), v);

    /* Right meta: unsolved neutral */
    if (v->tag == VL_NEUTRAL && is_meta_lvl(v->neutral.lvl) && !v->neutral.spine)
        return elab_solve(e, lvl_to_meta(v->neutral.lvl), u);

    /* Eta for functions */
    if (u->tag == VL_LAM || v->tag == VL_LAM) {
        Val *fresh = vl_neutral(a, depth, NULL);
        return elab_unify(e, a, depth + 1,
                          nbe_vapp(a, u, fresh), nbe_vapp(a, v, fresh));
    }

    if (u->tag != v->tag) return 0;

    switch (u->tag) {
    case VL_UNI:
        return u->ulevel == v->ulevel;

    case VL_NEUTRAL:
        if (u->neutral.lvl != v->neutral.lvl) return 0;
        return elab_unify_spine(e, a, depth, u->neutral.spine, v->neutral.spine);

    case VL_PI:
    case VL_SIGMA:
    case VL_W: {
        if (!elab_unify(e, a, depth, u->pi.dom, v->pi.dom)) return 0;
        Val *fresh = vl_neutral(a, depth, NULL);
        Val *uc = nbe_eval(a, env_cons(a, fresh, u->pi.env), u->pi.cod);
        Val *vc = nbe_eval(a, env_cons(a, fresh, v->pi.env), v->pi.cod);
        return elab_unify(e, a, depth + 1, uc, vc);
    }

    case VL_ID:
        return elab_unify(e, a, depth, u->id.ty,  v->id.ty)  &&
               elab_unify(e, a, depth, u->id.lhs, v->id.lhs) &&
               elab_unify(e, a, depth, u->id.rhs, v->id.rhs);

    case VL_REFL:
        return elab_unify(e, a, depth, u->refl, v->refl);

    case VL_SUCC:
    case VL_LSUC:
        return elab_unify(e, a, depth, u->succ, v->succ);

    case VL_LMAX:
        return elab_unify(e, a, depth, u->pair.fst, v->pair.fst) &&
               elab_unify(e, a, depth, u->pair.snd, v->pair.snd);

    case VL_UNI_V:
        return elab_unify(e, a, depth, u->uni_v_lvl, v->uni_v_lvl);

    case VL_INL:
    case VL_INR:
        return elab_unify(e, a, depth, u->inj, v->inj);

    case VL_PAIR:
    case VL_SUM:
    case VL_SUP:
        return elab_unify(e, a, depth, u->pair.fst, v->pair.fst) &&
               elab_unify(e, a, depth, u->pair.snd, v->pair.snd);

    case VL_INDTYPE: {
        if (u->indtype.fam_idx != v->indtype.fam_idx) return 0;
        if (u->indtype.n_args  != v->indtype.n_args)  return 0;
        for (int i = 0; i < u->indtype.n_args; i++)
            if (!elab_unify(e, a, depth, u->indtype.args[i], v->indtype.args[i])) return 0;
        return 1;
    }

    case VL_INDCON: {
        if (u->indcon.fam_idx  != v->indcon.fam_idx)  return 0;
        if (u->indcon.ctor_idx != v->indcon.ctor_idx) return 0;
        if (u->indcon.n_args   != v->indcon.n_args)   return 0;
        for (int i = 0; i < u->indcon.n_args; i++)
            if (!elab_unify(e, a, depth, u->indcon.args[i], v->indcon.args[i])) return 0;
        return 1;
    }

    case VL_FIX:
        return elab_unify(e, a, depth, u->fix_fun, v->fix_fun);

    /* Canonical constants with no payload to unify */
    case VL_NAT: case VL_ZERO: case VL_BOOL: case VL_TRUE: case VL_FALSE:
    case VL_EMPTY: case VL_UNIT: case VL_STAR: case VL_CIRCLE: case VL_BASE:
    case VL_LEVEL: case VL_LZERO:
        return 1;

    default:
        /* Fall back to regular conv for any remaining cases */
        return conv(a, depth, u, v);
    }
}

/* ── Meta-aware evaluation ──────────────────────────────────────────────── */

Val *elab_eval(ElabCtx *e, Arena *a, int depth, Env *env, Term *t) {
    if (t->tag == TM_HOLE) {
        if (t->idx >= 0) {
            Val *sol = elab_read(e, t->idx);
            if (sol) return sol;
            return vl_neutral(a, meta_to_lvl(t->idx), NULL);
        }
        return vl_neutral(a, META_LVL_BASE, NULL);
    }
    if (t->tag == TM_APP) {
        Val *fv = elab_eval(e, a, depth, env, t->app.fun);
        Val *av = elab_eval(e, a, depth, env, t->app.arg);
        return nbe_vapp(a, fv, av);
    }
    if (t->tag == TM_REFL) {
        return vl_refl(a, elab_eval(e, a, depth, env, t->refl));
    }
    if (t->tag == TM_PAIR) {
        Val *fv = elab_eval(e, a, depth, env, t->pair.fst);
        Val *sv = elab_eval(e, a, depth, env, t->pair.snd);
        return vl_pair(a, fv, sv);
    }
    if (t->tag == TM_FST) return nbe_vfst(a, elab_eval(e, a, depth, env, t->elim));
    if (t->tag == TM_SND) return nbe_vsnd(a, elab_eval(e, a, depth, env, t->elim));
    if (t->tag == TM_SUCC) return vl_succ(a, elab_eval(e, a, depth, env, t->elim));
    if (t->tag == TM_INL)  return vl_inl(a,  elab_eval(e, a, depth, env, t->elim));
    if (t->tag == TM_INR)  return vl_inr(a,  elab_eval(e, a, depth, env, t->elim));
    if (t->tag == TM_ANN)  return elab_eval(e, a, depth, env, t->ann.term);
    /* Lambda / path abstraction: substitute solved metas in the body before
       closing, so the closure body is hole-free and won't crash on application. */
    if (t->tag == TM_LAM) {
        Term *body = elab_subst(e, a, depth + 1, t->lam.body);
        return vl_lam(a, t->lam.name, env, body ? body : t->lam.body);
    }
    if (t->tag == TM_PATHABS) {
        Term *body = elab_subst(e, a, depth + 1, t->lam.body);
        return vl_pathabs(a, t->lam.name, env, body ? body : t->lam.body);
    }
    /* All other terms must be hole-free by the time elab_eval is called —
       elab_check processes sub-terms before elab_eval is invoked on them. */
    return nbe_eval(a, env, t);
}

/* ── Elaboration ────────────────────────────────────────────────────────── */

int elab_check(ElabCtx *e, Arena *a, int depth, TCtx *tctx, Env *env, Term *t, Val *ty) {
    ty = elab_force(e, ty);

    /* Hole in check position: assign a fresh meta of the expected type. */
    if (t->tag == TM_HOLE) {
        if (t->idx < 0)
            t->idx = elab_fresh(e, depth, ty);  /* mutate: assign id */
        else
            e->holes[t->idx].type = ty;          /* re-record type if needed */
        return 1;
    }

    /* Lambda against Pi: peel one layer bidirectionally. */
    if (t->tag == TM_LAM) {
        if (ty->tag != VL_PI) {
            type_error(t->loc, "expected Π type when checking λ\n");
            print_type(a, depth, tctx, "got", ty);
            return 0;
        }
        Val *fresh = vl_neutral(a, depth, NULL);
        Val *cod   = nbe_eval(a, env_cons(a, fresh, ty->pi.env), ty->pi.cod);
        TCtx ext   = { t->lam.name, ty->pi.dom, tctx };
        return elab_check(e, a, depth + 1, &ext,
                          env_cons(a, fresh, env), t->lam.body, cod);
    }

    /* fix body : ty  requires  body : ty → ty */
    if (t->tag == TM_FIX) {
        Val *fn_ty = vl_pi(a, "_", ty, env_cons(a, ty, NULL), tm_var(a, 1));
        return elab_check(e, a, depth, tctx, env, t->fix.body, fn_ty);
    }

    /* sup against W: check label and children bidirectionally. */
    if (t->tag == TM_SUP) {
        if (ty->tag != VL_W) {
            type_error(t->loc, "expected W type when checking sup\n");
            print_type(a, depth, tctx, "got", ty);
            return 0;
        }
        Val *A = ty->pi.dom;
        if (!elab_check(e, a, depth, tctx, env, t->sup.label, A)) return 0;
        Val *a_val = elab_eval(e, a, depth, env, t->sup.label);
        Val *B_a   = nbe_eval(a, env_cons(a, a_val, ty->pi.env), ty->pi.cod);
        Val *f_exp = vl_pi(a, "_", B_a, env_cons(a, ty, NULL), tm_var(a, 1));
        return elab_check(e, a, depth, tctx, env, t->sup.children, f_exp);
    }

    /* Pair against Sigma: check components. */
    if (t->tag == TM_PAIR) {
        if (ty->tag != VL_SIGMA) {
            type_error(t->loc, "expected Σ type when checking pair\n");
            print_type(a, depth, tctx, "got", ty);
            return 0;
        }
        if (!elab_check(e, a, depth, tctx, env, t->pair.fst, ty->pi.dom)) return 0;
        Val *fstv = elab_eval(e, a, depth, env, t->pair.fst);
        Val *sndt = nbe_eval(a, env_cons(a, fstv, ty->pi.env), ty->pi.cod);
        return elab_check(e, a, depth, tctx, env, t->pair.snd, sndt);
    }

    /* inl / inr against Sum. */
    if (t->tag == TM_INL) {
        if (ty->tag != VL_SUM) {
            type_error(t->loc, "expected Sum type when checking inl\n");
            print_type(a, depth, tctx, "got", ty);
            return 0;
        }
        return elab_check(e, a, depth, tctx, env, t->elim, ty->pair.fst);
    }
    if (t->tag == TM_INR) {
        if (ty->tag != VL_SUM) {
            type_error(t->loc, "expected Sum type when checking inr\n");
            print_type(a, depth, tctx, "got", ty);
            return 0;
        }
        return elab_check(e, a, depth, tctx, env, t->elim, ty->pair.snd);
    }

    /* rfl / refl against Id type */
    if (t->tag == TM_REFL && ty->tag == VL_ID) {
        if (t->refl->tag == TM_HOLE) {
            if (t->refl->idx < 0)
                t->refl->idx = elab_fresh(e, depth, ty->id.ty);
            if (!elab_solve(e, t->refl->idx, ty->id.lhs)) return 0;
            if (!elab_unify(e, a, depth, ty->id.lhs, ty->id.rhs)) {
                type_error(t->loc, "rfl: Id endpoints not definitionally equal\n");
                return 0;
            }
            return 1;
        }
        if (!elab_check(e, a, depth, tctx, env, t->refl, ty->id.ty)) return 0;
        Val *av = elab_eval(e, a, depth, env, t->refl);
        if (!elab_unify(e, a, depth, av, ty->id.lhs)) {
            type_error(t->loc, "refl: element does not match Id left endpoint\n");
            return 0;
        }
        if (!elab_unify(e, a, depth, av, ty->id.rhs)) {
            type_error(t->loc, "refl: element does not match Id right endpoint\n");
            return 0;
        }
        return 1;
    }

    /* refl against Path type */
    /* refl checks against PathP type via elaboration */
    if (t->tag == TM_REFL && ty->tag == VL_PATHP) {
        Val *i0v    = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *fam_i0 = nbe_vapp(a, ty->id.ty, i0v);
        if (t->refl->tag == TM_HOLE) {
            if (t->refl->idx < 0)
                t->refl->idx = elab_fresh(e, depth, fam_i0);
            if (!elab_solve(e, t->refl->idx, ty->id.lhs)) return 0;
            if (!elab_unify(e, a, depth, ty->id.lhs, ty->id.rhs)) {
                type_error(t->loc, "rfl: PathP endpoints not definitionally equal\n");
                return 0;
            }
            return 1;
        }
        if (!elab_check(e, a, depth, tctx, env, t->refl, fam_i0)) return 0;
        Val *av = elab_eval(e, a, depth, env, t->refl);
        if (!elab_unify(e, a, depth, av, ty->id.lhs)) {
            type_error(t->loc, "refl: element does not match PathP left endpoint\n");
            return 0;
        }
        if (!elab_unify(e, a, depth, av, ty->id.rhs)) {
            type_error(t->loc, "refl: element does not match PathP right endpoint\n");
            return 0;
        }
        return 1;
    }
    if (t->tag == TM_REFL && ty->tag == VL_PATH) {
        if (t->refl->tag == TM_HOLE) {
            if (t->refl->idx < 0)
                t->refl->idx = elab_fresh(e, depth, ty->id.ty);
            if (!elab_solve(e, t->refl->idx, ty->id.lhs)) return 0;
            if (!elab_unify(e, a, depth, ty->id.lhs, ty->id.rhs)) {
                type_error(t->loc, "rfl: Path endpoints not definitionally equal\n");
                return 0;
            }
            return 1;
        }
        if (!elab_check(e, a, depth, tctx, env, t->refl, ty->id.ty)) return 0;
        Val *av = elab_eval(e, a, depth, env, t->refl);
        if (!elab_unify(e, a, depth, av, ty->id.lhs)) {
            type_error(t->loc, "refl: element does not match path left endpoint\n");
            return 0;
        }
        if (!elab_unify(e, a, depth, av, ty->id.rhs)) {
            type_error(t->loc, "refl: element does not match path right endpoint\n");
            return 0;
        }
        return 1;
    }

    /* Everything else: infer the type and unify with expected. */
    Val *ity = elab_infer(e, a, depth, tctx, env, t);
    if (!ity) return 0;
    if (!elab_unify(e, a, depth, ity, ty)) {
        type_error(t->loc, "type mismatch\n");
        fprintf(stderr, "  inferred: ");
        term_fprint(stderr, nbe_quote(a, depth, ity));
        fprintf(stderr, "\n  expected: ");
        term_fprint(stderr, nbe_quote(a, depth, ty));
        fprintf(stderr, "\n");
        return 0;
    }
    return 1;
}

Val *elab_infer(ElabCtx *e, Arena *a, int depth, TCtx *tctx, Env *env, Term *t) {
    if (t->tag == TM_HOLE) {
        fprintf(stderr,
                "type error: cannot infer type of _; use (expr : type) annotation\n");
        return NULL;
    }

    if (t->tag == TM_APP) {
        /* Meta-aware application: recurse on fun, then check arg. */
        Val *fty = elab_infer(e, a, depth, tctx, env, t->app.fun);
        if (!fty) return NULL;
        fty = elab_force(e, fty);
        if (!fty || fty->tag != VL_PI) {
            type_error(t->loc, "applied non-function\n");
            return NULL;
        }
        if (!elab_check(e, a, depth, tctx, env, t->app.arg, fty->pi.dom)) return NULL;
        Val *argv = elab_eval(e, a, depth, env, t->app.arg);
        return nbe_eval(a, env_cons(a, argv, fty->pi.env), fty->pi.cod);
    }

    /* Type annotation: validate the annotation type with regular infer (annotation
       types shouldn't themselves have holes), then use elab_check for the term so
       holes in the annotated expression get solved against the known type. */
    if (t->tag == TM_ANN) {
        Val *aty = infer(a, depth, tctx, env, t->ann.type);
        if (!aty) return NULL;
        /* Mirror as_universe() from check.c: annotation must live in some universe. */
        if (aty->tag != VL_UNI && aty->tag != VL_UNI_V) {
            type_error(t->loc, "annotation is not a type\n");
            return NULL;
        }
        Val *ty_v = nbe_eval(a, env, t->ann.type);
        if (!elab_check(e, a, depth, tctx, env, t->ann.term, ty_v)) return NULL;
        return ty_v;
    }

    /* hcomp: elaborate each sub-term before delegating to regular infer. */
    if (t->tag == TM_HCOMP) {
        Val *ii_ty = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        Val *A_ty  = elab_infer(e, a, depth, tctx, env, t->hcomp_t.ty);
        if (!A_ty) return NULL;
        if (A_ty->tag != VL_UNI && A_ty->tag != VL_UNI_V) {
            type_error(t->loc, "hcomp: A must be a Type\n");
            return NULL;
        }
        if (!elab_check(e, a, depth, tctx, env, t->hcomp_t.face, ii_ty)) return NULL;
        Val *A_val   = elab_eval(e, a, depth, env, t->hcomp_t.ty);
        Val *tube_ty = vl_pi(a, "_", ii_ty, env_cons(a, A_val, NULL), tm_var(a, 1));
        if (!elab_check(e, a, depth, tctx, env, t->hcomp_t.tube, tube_ty)) return NULL;
        if (!elab_check(e, a, depth, tctx, env, t->hcomp_t.base, A_val)) return NULL;
        return A_val;
    }

    /* Glue: elaborate each sub-term so holes inside the equiv field are solved. */
    if (t->tag == TM_GLUE) {
        Val *ii_ty = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        Val *A_ty  = elab_infer(e, a, depth, tctx, env, t->glue_t.base);
        if (!A_ty) return NULL;
        if (A_ty->tag != VL_UNI && A_ty->tag != VL_UNI_V) {
            type_error(t->loc, "Glue: base A must be a Type\n");
            return NULL;
        }
        if (!elab_check(e, a, depth, tctx, env, t->glue_t.face, ii_ty)) return NULL;
        Val *T_ty  = elab_infer(e, a, depth, tctx, env, t->glue_t.fiber);
        if (!T_ty) return NULL;
        if (T_ty->tag != VL_UNI && T_ty->tag != VL_UNI_V) {
            type_error(t->loc, "Glue: fiber T must be a Type\n");
            return NULL;
        }
        Val *A_val    = elab_eval(e, a, depth, env, t->glue_t.base);
        Val *T_val    = elab_eval(e, a, depth, env, t->glue_t.fiber);
        Val *equiv_ty = make_equiv_type(a, T_val, A_val);
        if (!elab_check(e, a, depth, tctx, env, t->glue_t.equiv, equiv_ty)) {
            type_error(t->loc, "Glue: equivalence e must have type Equiv T A\n");
            return NULL;
        }
        int kA = (A_ty->tag == VL_UNI) ? (int)A_ty->ulevel : 0;
        int kT = (T_ty->tag == VL_UNI) ? (int)T_ty->ulevel : 0;
        return vl_uni(a, kA > kT ? kA : kT);
    }

    /* TM_UNGLUE: delegate to infer (which has the full type rule). */
    if (t->tag == TM_UNGLUE)
        return infer(a, depth, tctx, env, t);

    /* PRIM-1: primSub A φ u a — elaborate sub-terms before delegating. */
    if (t->tag == TM_PRIMSUB) {
        Val *ii_ty = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        Val *A_ty  = elab_infer(e, a, depth, tctx, env, t->primsub_t.ty);
        if (!A_ty) return NULL;
        if (A_ty->tag != VL_UNI && A_ty->tag != VL_UNI_V) {
            type_error(t->loc, "primSub: A must be a Type\n");
            return NULL;
        }
        if (!elab_check(e, a, depth, tctx, env, t->primsub_t.face, ii_ty)) return NULL;
        Val *A_val  = elab_eval(e, a, depth, env, t->primsub_t.ty);
        Val *phi_v  = elab_eval(e, a, depth, env, t->primsub_t.face);
        Val *iso    = nbe_visone(a, phi_v);
        Val *u_ty   = vl_pi(a, "_", iso, env_cons(a, A_val, NULL), tm_var(a, 1));
        if (!elab_check(e, a, depth, tctx, env, t->primsub_t.u, u_ty)) return NULL;
        if (!elab_check(e, a, depth, tctx, env, t->primsub_t.a, A_val)) return NULL;
        return A_val;
    }

    /* TM_GLUEELEM is check-only; infer falls through to error in infer(). */

    /* Delegate to the regular bidirectional checker for all other terms. */
    return infer(a, depth, tctx, env, t);
}

/* ── Substitution ───────────────────────────────────────────────────────── */

Term *elab_subst(ElabCtx *e, Arena *a, int depth, Term *t) {
    if (!t) return NULL;

    switch (t->tag) {
    case TM_HOLE: {
        if (t->idx < 0) {
            fprintf(stderr, "elab: unassigned hole (missing elaboration pass)\n");
            return NULL;
        }
        Val *sol = elab_read(e, t->idx);
        if (!sol) {
            fprintf(stderr, "elab: unsolved hole (type: ");
            if (e->holes[t->idx].type)
                term_fprint(stderr,
                    nbe_quote(a, e->holes[t->idx].depth, e->holes[t->idx].type));
            else
                fprintf(stderr, "unknown");
            fprintf(stderr, "); add explicit argument\n");
            return NULL;
        }
        return nbe_quote(a, e->holes[t->idx].depth, sol);
    }

    case TM_APP: {
        Term *f = elab_subst(e, a, depth, t->app.fun);
        Term *x = elab_subst(e, a, depth, t->app.arg);
        if (!f || !x) return NULL;
        return tm_app(a, f, x);
    }

    case TM_LAM: {
        Term *b = elab_subst(e, a, depth + 1, t->lam.body);
        if (!b) return NULL;
        return tm_lam(a, t->lam.name, b);
    }

    case TM_ANN: {
        Term *tm = elab_subst(e, a, depth, t->ann.term);
        Term *ty = elab_subst(e, a, depth, t->ann.type);
        if (!tm || !ty) return NULL;
        return tm_ann(a, tm, ty);
    }

    case TM_PI:
    case TM_SIG:
    case TM_W: {
        Term *dom = elab_subst(e, a, depth, t->pi.dom);
        Term *cod = elab_subst(e, a, depth + 1, t->pi.cod);
        if (!dom || !cod) return NULL;
        if (t->tag == TM_PI)  return tm_pi (a, t->pi.name, dom, cod);
        if (t->tag == TM_SIG) return tm_sig(a, t->pi.name, dom, cod);
        return tm_w(a, t->pi.name, dom, cod);
    }

    case TM_PAIR: {
        Term *f = elab_subst(e, a, depth, t->pair.fst);
        Term *s = elab_subst(e, a, depth, t->pair.snd);
        if (!f || !s) return NULL;
        return tm_pair(a, f, s);
    }

    /* Single-child elim terms. */
    case TM_FST:   { Term *x = elab_subst(e, a, depth, t->elim); if (!x) return NULL; return tm_fst(a, x); }
    case TM_SND:   { Term *x = elab_subst(e, a, depth, t->elim); if (!x) return NULL; return tm_snd(a, x); }
    case TM_SUCC:  { Term *x = elab_subst(e, a, depth, t->elim); if (!x) return NULL; return tm_succ(a, x); }
    case TM_INL:   { Term *x = elab_subst(e, a, depth, t->elim); if (!x) return NULL; return tm_inl(a, x); }
    case TM_INR:   { Term *x = elab_subst(e, a, depth, t->elim); if (!x) return NULL; return tm_inr(a, x); }
    case TM_REFL:  { Term *x = elab_subst(e, a, depth, t->refl); if (!x) return NULL; return tm_refl(a, x); }
    case TM_LSUC:  { Term *x = elab_subst(e, a, depth, t->elim); if (!x) return NULL; return tm_lsuc(a, x); }
    case TM_LMAX:  { Term *l = elab_subst(e, a, depth, t->app.fun); if (!l) return NULL;
                     Term *r = elab_subst(e, a, depth, t->app.arg); if (!r) return NULL;
                     return tm_lmax(a, l, r); }
    case TM_UNI_V: { Term *x = elab_subst(e, a, depth, t->uni_v_lvl); if (!x) return NULL; return tm_uni_v(a, x); }

    case TM_FIX: {
        Term *b = elab_subst(e, a, depth + 1, t->fix.body);
        if (!b) return NULL;
        return tm_fix(a, b);
    }

    case TM_ID: {
        Term *ty2 = elab_subst(e, a, depth, t->id.ty);
        Term *lhs = elab_subst(e, a, depth, t->id.lhs);
        Term *rhs = elab_subst(e, a, depth, t->id.rhs);
        if (!ty2 || !lhs || !rhs) return NULL;
        return tm_id(a, ty2, lhs, rhs);
    }

    case TM_SUP: {
        Term *lb = elab_subst(e, a, depth, t->sup.label);
        Term *ch = elab_subst(e, a, depth, t->sup.children);
        if (!lb || !ch) return NULL;
        return tm_sup(a, lb, ch);
    }

    case TM_ABORT: {
        Term *mo = elab_subst(e, a, depth, t->abort_t.motive);
        Term *sc = elab_subst(e, a, depth, t->abort_t.scrut);
        if (!mo || !sc) return NULL;
        return tm_abort(a, mo, sc);
    }

    case TM_NATREC: {
        Term *mo = elab_subst(e, a, depth,     t->natrec.motive);
        Term *ba = elab_subst(e, a, depth,     t->natrec.base);
        Term *st = elab_subst(e, a, depth + 2, t->natrec.step);
        Term *sc = elab_subst(e, a, depth,     t->natrec.scrut);
        if (!mo || !ba || !st || !sc) return NULL;
        return tm_natrec(a, mo, ba, st, sc);
    }

    case TM_BOOLREC: {
        Term *mo = elab_subst(e, a, depth, t->boolrec.motive);
        Term *tc = elab_subst(e, a, depth, t->boolrec.tcase);
        Term *fc = elab_subst(e, a, depth, t->boolrec.fcase);
        Term *sc = elab_subst(e, a, depth, t->boolrec.scrut);
        if (!mo || !tc || !fc || !sc) return NULL;
        return tm_boolrec(a, mo, tc, fc, sc);
    }

    case TM_UNITREC: {
        Term *mo = elab_subst(e, a, depth, t->unitrec_t.motive);
        Term *ba = elab_subst(e, a, depth, t->unitrec_t.base);
        Term *sc = elab_subst(e, a, depth, t->unitrec_t.scrut);
        if (!mo || !ba || !sc) return NULL;
        return tm_unitrec(a, mo, ba, sc);
    }

    case TM_CASESPLIT: {
        Term *mo = elab_subst(e, a, depth, t->casesplit_t.motive);
        Term *lc = elab_subst(e, a, depth, t->casesplit_t.lcase);
        Term *rc = elab_subst(e, a, depth, t->casesplit_t.rcase);
        Term *sc = elab_subst(e, a, depth, t->casesplit_t.scrut);
        if (!mo || !lc || !rc || !sc) return NULL;
        return tm_casesplit(a, mo, lc, rc, sc);
    }

    case TM_SUM: {
        Term *l = elab_subst(e, a, depth, t->sum_t.left);
        Term *r = elab_subst(e, a, depth, t->sum_t.right);
        if (!l || !r) return NULL;
        return tm_sum(a, l, r);
    }

    case TM_WREC: {
        Term *mo = elab_subst(e, a, depth, t->wrec.motive);
        Term *st = elab_subst(e, a, depth, t->wrec.step);
        Term *sc = elab_subst(e, a, depth, t->wrec.scrut);
        if (!mo || !st || !sc) return NULL;
        return tm_wrec(a, mo, st, sc);
    }

    case TM_J: {
        Term *ty2 = elab_subst(e, a, depth, t->j.ty);
        Term *lhs = elab_subst(e, a, depth, t->j.lhs);
        Term *mo  = elab_subst(e, a, depth, t->j.motive);
        Term *ba  = elab_subst(e, a, depth, t->j.base);
        Term *ep  = elab_subst(e, a, depth, t->j.endpoint);
        Term *pr  = elab_subst(e, a, depth, t->j.proof);
        if (!ty2 || !lhs || !mo || !ba || !ep || !pr) return NULL;
        return tm_j(a, ty2, lhs, mo, ba, ep, pr);
    }

    case TM_TRUNCREC: {
        Term *ta = elab_subst(e, a, depth, t->truncrec_t.ty_a);
        Term *tb = elab_subst(e, a, depth, t->truncrec_t.ty_b);
        Term *fn = elab_subst(e, a, depth, t->truncrec_t.func);
        Term *sc = elab_subst(e, a, depth, t->truncrec_t.scrut);
        if (!ta || !tb || !fn || !sc) return NULL;
        return tm_truncrec(a, ta, tb, fn, sc);
    }

    case TM_QUOTREC: {
        Term *ta = elab_subst(e, a, depth, t->quotrec_t.ty_a);
        Term *rl = elab_subst(e, a, depth, t->quotrec_t.rel);
        Term *tb = elab_subst(e, a, depth, t->quotrec_t.ty_b);
        Term *fn = elab_subst(e, a, depth, t->quotrec_t.func);
        Term *co = elab_subst(e, a, depth, t->quotrec_t.coh);
        Term *sc = elab_subst(e, a, depth, t->quotrec_t.scrut);
        if (!ta || !rl || !tb || !fn || !co || !sc) return NULL;
        return tm_quotrec(a, ta, rl, tb, fn, co, sc);
    }

    case TM_CIRCREC: {
        Term *mo = elab_subst(e, a, depth, t->circrec_t.motive);
        Term *bc = elab_subst(e, a, depth, t->circrec_t.base_case);
        Term *lc = elab_subst(e, a, depth, t->circrec_t.loop_case);
        Term *sc = elab_subst(e, a, depth, t->circrec_t.scrut);
        if (!mo || !bc || !lc || !sc) return NULL;
        return tm_circrec(a, mo, bc, lc, sc);
    }
    case TM_INDTYPE: {
        int n = t->indtype.n_args;
        Term **args = n > 0 ? (Term **)arena_alloc(a, n * sizeof(Term *)) : NULL;
        for (int i = 0; i < n; i++) {
            args[i] = elab_subst(e, a, depth, t->indtype.args[i]);
            if (!args[i]) return NULL;
        }
        return tm_indtype(a, t->indtype.fam_idx, n, args);
    }

    case TM_INDCON: {
        int n = t->indcon.n_args;
        Term **args = n > 0 ? (Term **)arena_alloc(a, n * sizeof(Term *)) : NULL;
        for (int i = 0; i < n; i++) {
            args[i] = elab_subst(e, a, depth, t->indcon.args[i]);
            if (!args[i]) return NULL;
        }
        return tm_indcon(a, t->indcon.fam_idx, t->indcon.ctor_idx, n, args);
    }

    case TM_INDREC: {
        Term *mo = elab_subst(e, a, depth, t->indrec.motive);
        Term *sc = elab_subst(e, a, depth, t->indrec.scrut);
        if (!mo || !sc) return NULL;
        int n = t->indrec.n_cases;
        Term **cases = n > 0 ? (Term **)arena_alloc(a, n * sizeof(Term *)) : NULL;
        for (int i = 0; i < n; i++) {
            cases[i] = elab_subst(e, a, depth, t->indrec.cases[i]);
            if (!cases[i]) return NULL;
        }
        return tm_indrec(a, t->indrec.fam_idx, mo, n, cases, sc);
    }

    case TM_PATHABS: {
        Term *b = elab_subst(e, a, depth + 1, t->lam.body);
        if (!b) return NULL;
        return tm_pathabs(a, t->lam.name, b);
    }
    case TM_PATHAPP: {
        Term *path = elab_subst(e, a, depth, t->app.fun);
        Term *r    = elab_subst(e, a, depth, t->app.arg);
        if (!path || !r) return NULL;
        return tm_pathapp(a, path, r);
    }
    case TM_PATH: {
        Term *ty  = elab_subst(e, a, depth, t->id.ty);
        Term *lhs = elab_subst(e, a, depth, t->id.lhs);
        Term *rhs = elab_subst(e, a, depth, t->id.rhs);
        if (!ty || !lhs || !rhs) return NULL;
        return tm_path(a, ty, lhs, rhs);
    }
    case TM_PATHP: {
        Term *fam = elab_subst(e, a, depth, t->id.ty);
        Term *lhs = elab_subst(e, a, depth, t->id.lhs);
        Term *rhs = elab_subst(e, a, depth, t->id.rhs);
        if (!fam || !lhs || !rhs) return NULL;
        return tm_pathp(a, fam, lhs, rhs);
    }
    case TM_TRANSP: {
        Term *fam  = elab_subst(e, a, depth, t->app.fun);
        Term *elem = elab_subst(e, a, depth, t->app.arg);
        if (!fam || !elem) return NULL;
        return tm_transp(a, fam, elem);
    }
    case TM_HCOMP: {
        Term *ty   = elab_subst(e, a, depth, t->hcomp_t.ty);
        Term *face = elab_subst(e, a, depth, t->hcomp_t.face);
        Term *tube = elab_subst(e, a, depth, t->hcomp_t.tube);
        Term *base = elab_subst(e, a, depth, t->hcomp_t.base);
        if (!ty || !face || !tube || !base) return NULL;
        return tm_hcomp(a, ty, face, tube, base);
    }
    case TM_COMP: {
        Term *fam  = elab_subst(e, a, depth, t->hcomp_t.ty);
        Term *face = elab_subst(e, a, depth, t->hcomp_t.face);
        Term *tube = elab_subst(e, a, depth, t->hcomp_t.tube);
        Term *base = elab_subst(e, a, depth, t->hcomp_t.base);
        if (!fam || !face || !tube || !base) return NULL;
        return tm_comp(a, fam, face, tube, base);
    }
    case TM_FILL: {
        Term *fam  = elab_subst(e, a, depth, t->fill_t.fam);
        Term *face = elab_subst(e, a, depth, t->fill_t.face);
        Term *tube = elab_subst(e, a, depth, t->fill_t.tube);
        Term *base = elab_subst(e, a, depth, t->fill_t.base);
        Term *idx  = elab_subst(e, a, depth, t->fill_t.idx);
        if (!fam || !face || !tube || !base || !idx) return NULL;
        return tm_fill(a, fam, face, tube, base, idx);
    }
    case TM_GLUE: {
        Term *b = elab_subst(e, a, depth, t->glue_t.base);
        Term *f = elab_subst(e, a, depth, t->glue_t.face);
        Term *fi = elab_subst(e, a, depth, t->glue_t.fiber);
        Term *eq = elab_subst(e, a, depth, t->glue_t.equiv);
        if (!b || !f || !fi || !eq) return NULL;
        return tm_glue(a, b, f, fi, eq);
    }
    case TM_IMIN: case TM_IMAX: {
        Term *l = elab_subst(e, a, depth, t->app.fun);
        Term *r = elab_subst(e, a, depth, t->app.arg);
        if (!l || !r) return NULL;
        return (t->tag == TM_IMIN) ? tm_imin(a, l, r) : tm_imax(a, l, r);
    }
    case TM_INEG: {
        Term *v = elab_subst(e, a, depth, t->elim);
        if (!v) return NULL;
        return tm_ineg(a, v);
    }
    case TM_ISONE: {
        Term *v = elab_subst(e, a, depth, t->elim);
        if (!v) return NULL;
        return tm_isone(a, v);
    }
    case TM_GLUEELEM: {
        Term *face    = elab_subst(e, a, depth, t->glue_elem_t.face);
        Term *partial = elab_subst(e, a, depth, t->glue_elem_t.partial);
        Term *base    = elab_subst(e, a, depth, t->glue_elem_t.base);
        if (!face || !partial || !base) return NULL;
        return tm_glueelem(a, face, partial, base);
    }
    case TM_UNGLUE: {
        Term *face  = elab_subst(e, a, depth, t->unglue_t.face);
        Term *equiv = elab_subst(e, a, depth, t->unglue_t.equiv);
        Term *elem  = elab_subst(e, a, depth, t->unglue_t.elem);
        if (!face || !equiv || !elem) return NULL;
        return tm_unglue(a, face, equiv, elem);
    }
    case TM_PRIMSUB: {
        Term *ty   = elab_subst(e, a, depth, t->primsub_t.ty);
        Term *face = elab_subst(e, a, depth, t->primsub_t.face);
        Term *u    = elab_subst(e, a, depth, t->primsub_t.u);
        Term *out  = elab_subst(e, a, depth, t->primsub_t.a);
        if (!ty || !face || !u || !out) return NULL;
        return tm_primsub(a, ty, face, u, out);
    }
    case TM_MATCH: {
        Term *scrut = elab_subst(e, a, depth, t->match_s.scrut);
        if (!scrut) return NULL;
        int n = t->match_s.n_arms;
        MatchArm *arms = n > 0 ? (MatchArm *)arena_alloc(a, n * sizeof(MatchArm)) : NULL;
        for (int i = 0; i < n; i++) {
            arms[i].ctor_idx = t->match_s.arms[i].ctor_idx;
            arms[i].n_binds  = t->match_s.arms[i].n_binds;
            arms[i].ih_name  = t->match_s.arms[i].ih_name;
            for (int j = 0; j < arms[i].n_binds; j++)
                arms[i].names[j] = t->match_s.arms[i].names[j];
            int binder_depth = arms[i].n_binds + (arms[i].ih_name ? 1 : 0);
            Term *body = elab_subst(e, a, depth + binder_depth,
                                    t->match_s.arms[i].body);
            if (!body) return NULL;
            arms[i].body = body;
        }
        return tm_match(a, scrut, t->match_s.fam_idx, n, arms);
    }

    /* Leaves: no sub-terms that can contain holes. */
    default:
        return t;
    }
}

/* ── Hole detection ─────────────────────────────────────────────────────── */

int term_has_holes(Term *t) {
    if (!t) return 0;
    switch (t->tag) {
    case TM_HOLE: return 1;
    case TM_APP:  return term_has_holes(t->app.fun) || term_has_holes(t->app.arg);
    case TM_LAM:  return term_has_holes(t->lam.body);
    case TM_ANN:  return term_has_holes(t->ann.term) || term_has_holes(t->ann.type);
    case TM_PI: case TM_SIG: case TM_W:
        return term_has_holes(t->pi.dom) || term_has_holes(t->pi.cod);
    case TM_PAIR:
        return term_has_holes(t->pair.fst) || term_has_holes(t->pair.snd);
    case TM_FST: case TM_SND: case TM_SUCC:
    case TM_INL: case TM_INR: case TM_LSUC:
        return term_has_holes(t->elim);
    case TM_LMAX:
        return term_has_holes(t->app.fun) || term_has_holes(t->app.arg);
    case TM_REFL:  return term_has_holes(t->refl);
    case TM_UNI_V: return term_has_holes(t->uni_v_lvl);
    case TM_FIX:   return term_has_holes(t->fix.body);
    case TM_ID:
        return term_has_holes(t->id.ty) || term_has_holes(t->id.lhs) || term_has_holes(t->id.rhs);
    case TM_SUP:
        return term_has_holes(t->sup.label) || term_has_holes(t->sup.children);
    case TM_SUM:
        return term_has_holes(t->sum_t.left) || term_has_holes(t->sum_t.right);
    case TM_ABORT:
        return term_has_holes(t->abort_t.motive) || term_has_holes(t->abort_t.scrut);
    case TM_NATREC:
        return term_has_holes(t->natrec.motive) || term_has_holes(t->natrec.base) ||
               term_has_holes(t->natrec.step)   || term_has_holes(t->natrec.scrut);
    case TM_BOOLREC:
        return term_has_holes(t->boolrec.motive) || term_has_holes(t->boolrec.tcase) ||
               term_has_holes(t->boolrec.fcase)  || term_has_holes(t->boolrec.scrut);
    case TM_UNITREC:
        return term_has_holes(t->unitrec_t.motive) || term_has_holes(t->unitrec_t.base) ||
               term_has_holes(t->unitrec_t.scrut);
    case TM_CASESPLIT:
        return term_has_holes(t->casesplit_t.motive) || term_has_holes(t->casesplit_t.lcase) ||
               term_has_holes(t->casesplit_t.rcase)  || term_has_holes(t->casesplit_t.scrut);
    case TM_WREC:
        return term_has_holes(t->wrec.motive) || term_has_holes(t->wrec.step) ||
               term_has_holes(t->wrec.scrut);
    case TM_J:
        return term_has_holes(t->j.ty)       || term_has_holes(t->j.lhs)      ||
               term_has_holes(t->j.motive)   || term_has_holes(t->j.base)     ||
               term_has_holes(t->j.endpoint) || term_has_holes(t->j.proof);
    case TM_TRUNCREC:
        return term_has_holes(t->truncrec_t.ty_a) || term_has_holes(t->truncrec_t.ty_b) ||
               term_has_holes(t->truncrec_t.func) || term_has_holes(t->truncrec_t.scrut);
    case TM_QUOTREC:
        return term_has_holes(t->quotrec_t.ty_a) || term_has_holes(t->quotrec_t.rel)  ||
               term_has_holes(t->quotrec_t.ty_b) || term_has_holes(t->quotrec_t.func) ||
               term_has_holes(t->quotrec_t.coh)  || term_has_holes(t->quotrec_t.scrut);
    case TM_CIRCREC:
        return term_has_holes(t->circrec_t.motive)    || term_has_holes(t->circrec_t.base_case) ||
               term_has_holes(t->circrec_t.loop_case) || term_has_holes(t->circrec_t.scrut);
    case TM_INDTYPE:
        for (int i = 0; i < t->indtype.n_args; i++)
            if (term_has_holes(t->indtype.args[i])) return 1;
        return 0;
    case TM_INDCON:
        for (int i = 0; i < t->indcon.n_args; i++)
            if (term_has_holes(t->indcon.args[i])) return 1;
        return 0;
    case TM_INDREC:
        if (term_has_holes(t->indrec.motive) || term_has_holes(t->indrec.scrut)) return 1;
        for (int i = 0; i < t->indrec.n_cases; i++)
            if (term_has_holes(t->indrec.cases[i])) return 1;
        return 0;
    case TM_PATHABS: return term_has_holes(t->lam.body);
    case TM_PATHAPP: return term_has_holes(t->app.fun) || term_has_holes(t->app.arg);
    case TM_PATH:
    case TM_PATHP:   return term_has_holes(t->id.ty) || term_has_holes(t->id.lhs)
                                                      || term_has_holes(t->id.rhs);
    case TM_TRANSP:  return term_has_holes(t->app.fun) || term_has_holes(t->app.arg);
    case TM_HCOMP:
    case TM_COMP:
        return term_has_holes(t->hcomp_t.ty)   || term_has_holes(t->hcomp_t.face) ||
               term_has_holes(t->hcomp_t.tube) || term_has_holes(t->hcomp_t.base);
    case TM_FILL:
        return term_has_holes(t->fill_t.fam)   || term_has_holes(t->fill_t.face) ||
               term_has_holes(t->fill_t.tube)  || term_has_holes(t->fill_t.base) ||
               term_has_holes(t->fill_t.idx);
    case TM_GLUE:
        return term_has_holes(t->glue_t.base)  || term_has_holes(t->glue_t.face) ||
               term_has_holes(t->glue_t.fiber) || term_has_holes(t->glue_t.equiv);
    case TM_IMIN: case TM_IMAX:
        return term_has_holes(t->app.fun) || term_has_holes(t->app.arg);
    case TM_INEG:
    case TM_ISONE:
        return term_has_holes(t->elim);
    case TM_GLUEELEM:
        return term_has_holes(t->glue_elem_t.face)    ||
               term_has_holes(t->glue_elem_t.partial) ||
               term_has_holes(t->glue_elem_t.base);
    case TM_UNGLUE:
        return term_has_holes(t->unglue_t.face)  ||
               term_has_holes(t->unglue_t.equiv) ||
               term_has_holes(t->unglue_t.elem);
    case TM_PRIMSUB:
        return term_has_holes(t->primsub_t.ty)   ||
               term_has_holes(t->primsub_t.face) ||
               term_has_holes(t->primsub_t.u)    ||
               term_has_holes(t->primsub_t.a);
    case TM_MATCH:
        if (term_has_holes(t->match_s.scrut)) return 1;
        for (int i = 0; i < t->match_s.n_arms; i++)
            if (term_has_holes(t->match_s.arms[i].body)) return 1;
        return 0;
    default: return 0;
    }
}
