#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include "check.h"
#include "parse.h"
#include "defs.h"

/* ── Structured error reporting ─────────────────────────────────────────────
 * type_error(loc, fmt, ...): print "LINE:COL: type error: MSG\n".
 * loc.line==0 means source position is unknown; the prefix is omitted.
 * Callers are responsible for the trailing '\n' in fmt. */

static void type_error(SrcLoc loc, const char *fmt, ...) {
    if (loc.line > 0)
        fprintf(stderr, "%d:%d: ", loc.line, loc.col);
    fputs("type error: ", stderr);
    va_list ap;
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
}

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

/* ── Equiv type template
 * Represents: Equiv T A = Σ(fwd:T→A). Σ(inv:A→T).
 *             Σ(_:Π(y:A). Path A (fwd(inv y)) y).
 *             Π(x:T). Path T (inv(fwd x)) x
 *
 * Stored as a closed \T.\A. lambda so make_equiv_type can apply it. */
static Arena equiv_tmpl_arena  = {NULL};
static Val  *equiv_tmpl_v      = NULL;

static Val *get_equiv_tmpl(void) {
    if (equiv_tmpl_v) return equiv_tmpl_v;
    Term *ty = parse(&equiv_tmpl_arena,
        "\\T. \\A."
        " Σ(fwd : T → A)."
        " Σ(inv : A → T)."
        " Σ(_ : Π(y : A). Path A (fwd (inv y)) y)."
        " Π(x : T). Path T (inv (fwd x)) x");
    if (!ty) { fprintf(stderr, "internal: equiv type template parse failed\n"); exit(1); }
    equiv_tmpl_v = nbe_eval(&equiv_tmpl_arena, NULL, ty);
    return equiv_tmpl_v;
}

Val *make_equiv_type(Arena *a, Val *T_val, Val *A_val) {
    Val *tmpl = get_equiv_tmpl();
    return nbe_vapp(a, nbe_vapp(a, tmpl, T_val), A_val);
}

static Arena trunc_arena  = {NULL};
static Val  *trunc_type_v = NULL;

static Val *get_trunc_type(void) {
    if (trunc_type_v) return trunc_type_v;
    Term *ty = parse(&trunc_arena, "Π(_ : Type). Type");
    if (!ty) { fprintf(stderr, "internal: trunc type parse failed\n"); exit(1); }
    trunc_type_v = nbe_eval(&trunc_arena, NULL, ty);
    return trunc_type_v;
}

static Arena trint_arena  = {NULL};
static Val  *trint_type_v = NULL;

static Val *get_trint_type(void) {
    if (trint_type_v) return trint_type_v;
    Term *ty = parse(&trint_arena,
        "Π(A : Type). Π(_ : A). trunc A");
    if (!ty) { fprintf(stderr, "internal: trint type parse failed\n"); exit(1); }
    trint_type_v = nbe_eval(&trint_arena, NULL, ty);
    return trint_type_v;
}

static Arena squash_arena  = {NULL};
static Val  *squash_type_v = NULL;

static Val *get_squash_type(void) {
    if (squash_type_v) return squash_type_v;
    Term *ty = parse(&squash_arena,
        "Π(A : Type). Π(x : trunc A). Π(y : trunc A). Id (trunc A) x y");
    if (!ty) { fprintf(stderr, "internal: squash type parse failed\n"); exit(1); }
    squash_type_v = nbe_eval(&squash_arena, NULL, ty);
    return squash_type_v;
}

static Arena quot_arena  = {NULL};
static Val  *quot_type_v = NULL;

static Val *get_quot_type(void) {
    if (quot_type_v) return quot_type_v;
    Term *ty = parse(&quot_arena,
        "Π(A : Type). Π(_ : Π(_ : A). Π(_ : A). Type). Type");
    if (!ty) { fprintf(stderr, "internal: Quot type parse failed\n"); exit(1); }
    quot_type_v = nbe_eval(&quot_arena, NULL, ty);
    return quot_type_v;
}

static Arena qin_arena  = {NULL};
static Val  *qin_type_v = NULL;

static Val *get_qin_type(void) {
    if (qin_type_v) return qin_type_v;
    Term *ty = parse(&qin_arena,
        "Π(A : Type). Π(R : Π(_ : A). Π(_ : A). Type). Π(_ : A). Quot A R");
    if (!ty) { fprintf(stderr, "internal: qin type parse failed\n"); exit(1); }
    qin_type_v = nbe_eval(&qin_arena, NULL, ty);
    return qin_type_v;
}

static Arena qeq_arena  = {NULL};
static Val  *qeq_type_v = NULL;

static Val *get_qeq_type(void) {
    if (qeq_type_v) return qeq_type_v;
    Term *ty = parse(&qeq_arena,
        "Π(A : Type). Π(R : Π(_ : A). Π(_ : A). Type). Π(a : A). Π(b : A). Π(_ : R a b). Id (Quot A R) (qin A R a) (qin A R b)");
    if (!ty) { fprintf(stderr, "internal: qeq type parse failed\n"); exit(1); }
    qeq_type_v = nbe_eval(&qeq_arena, NULL, ty);
    return qeq_type_v;
}

static Arena loop_arena  = {NULL};
static Val  *loop_type_v = NULL;

static Val *get_loop_type(void) {
    if (loop_type_v) return loop_type_v;
    Term *ty = parse(&loop_arena, "Id S1 base base");
    if (!ty) { fprintf(stderr, "internal: loop type parse failed\n"); exit(1); }
    loop_type_v = nbe_eval(&loop_arena, NULL, ty);
    return loop_type_v;
}

static Arena funext_arena  = {NULL};
static Val  *funext_type_v = NULL;

static Val *get_funext_type(void) {
    if (funext_type_v) return funext_type_v;
    /* funext : Π(A : Type). Π(B : A → Type).
     *          Π(f : Π(x:A). B x). Π(g : Π(x:A). B x).
     *          (Π(x : A). Path (B x) (f x) (g x))
     *          → Path (Π(x:A). B x) f g
     *
     * Uses Path (cubical) rather than Id (propositional) — this makes funext
     * computable: funext A B f g h = ⟨i⟩ λx. h x @ i.                      */
    Term *ty = parse(&funext_arena,
        "Π(A : Type). Π(B : Π(_ : A). Type)."
        " Π(f : Π(x : A). B x). Π(g : Π(x : A). B x)."
        " Π(_ : Π(x : A). Path (B x) (f x) (g x))."
        " Path (Π(x : A). B x) f g");
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

/* Pretty-print one labelled type line: "  LABEL: TYPE\n" */
void print_type(Arena *a, int depth, TCtx *tctx, const char *label, Val *v) {
    Ctx *ctx = tctx_to_ctx(a, tctx);
    fprintf(stderr, "  %s: ", label);
    term_fprint_ctx(stderr, nbe_quote(a, depth, v), ctx, 0);
    fprintf(stderr, "\n");
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
    /* Eta for path abstractions: p ≡ <i> p @ i
     * Valid path element tags: VL_PATHABS, VL_NEUTRAL, VL_REFL.
     * VL_REFL: (refl a) @ r = a for any r, so (refl a) ≡ <j> a by eta. */
    if (u->tag == VL_PATHABS || v->tag == VL_PATHABS) {
        ValTag other = (u->tag == VL_PATHABS) ? v->tag : u->tag;
        if (other != VL_PATHABS && other != VL_NEUTRAL && other != VL_REFL) return 0;
        Val *fresh = vl_neutral(a, depth, NULL);  /* fresh interval variable */
        return conv(a, depth + 1, nbe_vpathapp(a, u, fresh), nbe_vpathapp(a, v, fresh));
    }
    /* Eta for pairs: (a, b) ≡ p  iff  fst p ≡ a  and  snd p ≡ b */
    if (u->tag == VL_PAIR || v->tag == VL_PAIR) {
        ValTag other = (u->tag == VL_PAIR) ? v->tag : u->tag;
        if (other != VL_PAIR && other != VL_NEUTRAL) return 0;
        return conv(a, depth, nbe_vfst(a, u), nbe_vfst(a, v)) &&
               conv(a, depth, nbe_vsnd(a, u), nbe_vsnd(a, v));
    }
    /* Cross-tag: Path A a b ≡ PathP (λ_. A) a b when fam is constant at A */
    if ((u->tag == VL_PATH && v->tag == VL_PATHP) ||
        (u->tag == VL_PATHP && v->tag == VL_PATH)) {
        Val *path  = (u->tag == VL_PATH)  ? u : v;
        Val *pathp = (u->tag == VL_PATHP) ? u : v;
        Val *fresh = vl_neutral(a, depth, NULL);
        Val *fam_at_fresh = nbe_vapp(a, pathp->id.ty, fresh);
        if (!conv(a, depth + 1, path->id.ty, fam_at_fresh)) return 0;
        return conv(a, depth, path->id.lhs, pathp->id.lhs) &&
               conv(a, depth, path->id.rhs, pathp->id.rhs);
    }
    /* Unit η: the sole inhabitant of Unit is star.  In a well-typed context,
     * if one value is star and the other is a neutral (a bound variable of
     * type Unit), they are definitionally equal.  This fires when Π η-expansion
     * applies a λx.body to a fresh neutral x : Unit, then compares x with star. */
    if ((u->tag == VL_STAR && v->tag == VL_NEUTRAL) ||
        (u->tag == VL_NEUTRAL && v->tag == VL_STAR)) return 1;
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
    case VL_PATH:
        return conv(a, depth, u->id.ty,  v->id.ty)  &&
               conv(a, depth, u->id.lhs, v->id.lhs) &&
               conv(a, depth, u->id.rhs, v->id.rhs);
    case VL_PATHP:
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
    case VL_CIRCLE:
    case VL_BASE:
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
    case VL_INDTYPE:
        if (u->indtype.fam_idx != v->indtype.fam_idx) return 0;
        if (u->indtype.n_args  != v->indtype.n_args)  return 0;
        for (int i = 0; i < u->indtype.n_args; i++)
            if (!conv(a, depth, u->indtype.args[i], v->indtype.args[i])) return 0;
        return 1;
    case VL_INDCON:
        if (u->indcon.fam_idx  != v->indcon.fam_idx)  return 0;
        if (u->indcon.ctor_idx != v->indcon.ctor_idx) return 0;
        if (u->indcon.n_args   != v->indcon.n_args)   return 0;
        for (int i = 0; i < u->indcon.n_args; i++)
            if (!conv(a, depth, u->indcon.args[i], v->indcon.args[i])) return 0;
        return 1;
    case VL_FIX:
        return conv(a, depth, u->fix_fun, v->fix_fun);
    case VL_TRANSP:
        return conv(a, depth, u->transp_s.family, v->transp_s.family) &&
               conv(a, depth, u->transp_s.elem,   v->transp_s.elem);
    case VL_HCOMP:
    case VL_COMP:
        return conv(a, depth, u->hcomp_s.ty,   v->hcomp_s.ty)   &&
               conv(a, depth, u->hcomp_s.face, v->hcomp_s.face) &&
               conv(a, depth, u->hcomp_s.tube, v->hcomp_s.tube) &&
               conv(a, depth, u->hcomp_s.base, v->hcomp_s.base);
    case VL_GLUE:
        return conv(a, depth, u->glue_s.base,  v->glue_s.base)  &&
               conv(a, depth, u->glue_s.face,  v->glue_s.face)  &&
               conv(a, depth, u->glue_s.fiber, v->glue_s.fiber) &&
               conv(a, depth, u->glue_s.equiv, v->glue_s.equiv);
    case VL_IMIN:
    case VL_IMAX:
        return conv(a, depth, u->pair.fst, v->pair.fst) &&
               conv(a, depth, u->pair.snd, v->pair.snd);
    case VL_INEG:
    case VL_ISONE:
        return conv(a, depth, u->succ, v->succ);
    case VL_GLUEELEM:
        return conv(a, depth, u->glue_elem_s.face,    v->glue_elem_s.face)    &&
               conv(a, depth, u->glue_elem_s.partial, v->glue_elem_s.partial) &&
               conv(a, depth, u->glue_elem_s.base,    v->glue_elem_s.base);
    case VL_UNGLUE:
        return conv(a, depth, u->unglue_s.face,  v->unglue_s.face)  &&
               conv(a, depth, u->unglue_s.equiv, v->unglue_s.equiv) &&
               conv(a, depth, u->unglue_s.elem,  v->unglue_s.elem);
    case VL_JSTUCK:
        return conv(a, depth, u->jstuck_s.ty,       v->jstuck_s.ty)       &&
               conv(a, depth, u->jstuck_s.lhs,      v->jstuck_s.lhs)      &&
               conv(a, depth, u->jstuck_s.motive,   v->jstuck_s.motive)   &&
               conv(a, depth, u->jstuck_s.base,     v->jstuck_s.base)     &&
               conv(a, depth, u->jstuck_s.endpoint, v->jstuck_s.endpoint) &&
               conv(a, depth, u->jstuck_s.proof,    v->jstuck_s.proof);
    case VL_PRIMSUB:
        return conv(a, depth, u->primsub_s.face, v->primsub_s.face) &&
               conv(a, depth, u->primsub_s.u,    v->primsub_s.u)    &&
               conv(a, depth, u->primsub_s.out,  v->primsub_s.out);
    case VL_LEVEL:
    case VL_LZERO:
        return 1;
    case VL_LSUC:
        return conv(a, depth, u->succ, v->succ);
    case VL_LMAX:
        return conv(a, depth, u->pair.fst, v->pair.fst) &&
               conv(a, depth, u->pair.snd, v->pair.snd);
    case VL_UNI_V:
        /* Type_(l1) ≡ Type_(l2)  iff  l1 ≡ l2;  NULL means omega (≡ itself) */
        if (!u->uni_v_lvl || !v->uni_v_lvl) return u->uni_v_lvl == v->uni_v_lvl;
        return conv(a, depth, u->uni_v_lvl, v->uni_v_lvl);
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
    } else if (sp1->kind == SP_TRUNCREC) {
        if (!conv(a, depth, sp1->truncrec_s.ty_a, sp2->truncrec_s.ty_a)) return 0;
        if (!conv(a, depth, sp1->truncrec_s.ty_b, sp2->truncrec_s.ty_b)) return 0;
        if (!conv(a, depth, sp1->truncrec_s.func,  sp2->truncrec_s.func))  return 0;
    } else if (sp1->kind == SP_QUOTREC) {
        if (!conv(a, depth, sp1->quotrec_s.ty_a, sp2->quotrec_s.ty_a)) return 0;
        if (!conv(a, depth, sp1->quotrec_s.rel,  sp2->quotrec_s.rel))  return 0;
        if (!conv(a, depth, sp1->quotrec_s.ty_b, sp2->quotrec_s.ty_b)) return 0;
        if (!conv(a, depth, sp1->quotrec_s.func, sp2->quotrec_s.func)) return 0;
        if (!conv(a, depth, sp1->quotrec_s.coh,  sp2->quotrec_s.coh))  return 0;
    } else if (sp1->kind == SP_CIRCREC) {
        if (!conv(a, depth, sp1->circrec_s.motive,    sp2->circrec_s.motive))    return 0;
        if (!conv(a, depth, sp1->circrec_s.base_case, sp2->circrec_s.base_case)) return 0;
        if (!conv(a, depth, sp1->circrec_s.loop_case, sp2->circrec_s.loop_case)) return 0;
    } else if (sp1->kind == SP_INDREC) {
        if (sp1->indrec.fam_idx != sp2->indrec.fam_idx) return 0;
        int n = sp1->indrec.n_cases;
        if (sp2->indrec.n_cases != n) return 0;
        if ((sp1->indrec.motive == NULL) != (sp2->indrec.motive == NULL)) return 0;
        if (sp1->indrec.motive && !conv(a, depth, sp1->indrec.motive, sp2->indrec.motive)) return 0;
        for (int i = 0; i < n; i++)
            if (!conv(a, depth, sp1->indrec.cases[i], sp2->indrec.cases[i])) return 0;
    } else if (sp1->kind == SP_PATHAPP) {
        if (!conv(a, depth, sp1->val, sp2->val)) return 0;
    } else if (sp1->kind == SP_MATCH) {
        if (sp1->match_sp.fam_idx != sp2->match_sp.fam_idx) return 0;
        int n = sp1->match_sp.n_arms;
        if (sp2->match_sp.n_arms != n) return 0;
        for (int i = 0; i < n; i++) {
            MatchClosure *c1 = &sp1->match_sp.arms[i];
            MatchClosure *c2 = &sp2->match_sp.arms[i];
            if (c1->ctor_idx != c2->ctor_idx || c1->n_binds != c2->n_binds) return 0;
            Env *e1 = c1->env, *e2 = c2->env;
            int d = depth;
            for (int j = 0; j < c1->n_binds; j++) {
                Val *fresh = vl_neutral(a, d++, NULL);
                e1 = env_cons(a, fresh, e1);
                e2 = env_cons(a, fresh, e2);
            }
            Val *v1 = nbe_eval(a, e1, c1->body);
            Val *v2 = nbe_eval(a, e2, c2->body);
            if (!conv(a, d, v1, v2)) return 0;
        }
    }
    /* SP_FST, SP_SND: no payload — kind equality (checked above) is sufficient. */
    return conv_spine(a, depth, sp1->next, sp2->next);
}

/* ── Helpers */

static int as_universe(Val *v, int *level) {
    if (!v) return 0;
    if (v->tag == VL_UNI)   { *level = v->ulevel; return 1; }
    if (v->tag == VL_UNI_V) { *level = -1;        return 1; }  /* variable level */
    return 0;
}
static int imax(int a, int b) {
    if (a < 0 || b < 0) return -1;  /* -1 = variable level, dominates */
    return a > b ? a : b;
}
static Val *uni_at(Arena *a, int level) {
    return level >= 0 ? vl_uni(a, level) : vl_uni_v(a, NULL);
}

/* ── HIT path sentinel (mirrors eval.c) */
#define HIT_PATH_CTR_STRIDE_C 64
static inline int hit_path_sentinel_c(int fam_idx, int ci) {
    return -(1000 + fam_idx * HIT_PATH_CTR_STRIDE_C + ci);
}
/* Decode a HIT path sentinel (mirrors eval.c's static hit_path_sentinel_decode). */
static inline int hit_path_sentinel_decode_c(int lvl, int *fam_out, int *ctor_out) {
    if (lvl > -1000) return 0;
    int x = -(lvl + 1000);
    *fam_out  = x / HIT_PATH_CTR_STRIDE_C;
    *ctor_out = x % HIT_PATH_CTR_STRIDE_C;
    if (*fam_out >= ind_count()) return 0;
    IndDef *fam = ind_get(*fam_out);
    if (*ctor_out >= fam->n_ctors) return 0;
    return fam->ctors[*ctor_out].is_path_ctor;
}

/* Compute rec(v) = indrec P eval_cases v for a concrete endpoint.
 *   VL_INDCON endpoints:      apply eval_cases[ci] to ctor args.
 *   HIT path-sentinel neutral: apply eval_cases[ci] to ctor args from spine.
 *   Anything else:             approximation P_approx(v).
 * Used for both carrier endpoints (points) and outer endpoints (1-cell path vals). */
static Val *hit_compute_rec(Arena *a, Val *v, int fam_idx, int n_params,
                             Val **eval_cases, Val *P_approx) {
    if (v->tag == VL_INDCON && v->indcon.fam_idx == fam_idx &&
        eval_cases && eval_cases[v->indcon.ctor_idx]) {
        Val *c = eval_cases[v->indcon.ctor_idx];
        for (int j = n_params; j < v->indcon.n_args; j++)
            c = nbe_vapp(a, c, v->indcon.args[j]);
        return c;
    }
    if (v->tag == VL_NEUTRAL && eval_cases) {
        int ef, ec;
        if (hit_path_sentinel_decode_c(v->neutral.lvl, &ef, &ec) &&
            ef == fam_idx && eval_cases[ec]) {
            Val *c = eval_cases[ec];
            int ep_arity = ind_get(fam_idx)->ctors[ec].arity;
            Val **ep_args = ep_arity > 0
                ? (Val **)arena_alloc(a, ep_arity * sizeof(Val *)) : NULL;
            int ej = 0;
            for (Spine *s = v->neutral.spine;
                 s && s->kind == SP_APP && ej < ep_arity; s = s->next, ej++)
                ep_args[ej] = s->val;
            for (int lo = 0, hi = ep_arity-1; lo < hi; lo++, hi--)
                { Val *t2 = ep_args[lo]; ep_args[lo] = ep_args[hi]; ep_args[hi] = t2; }
            for (int ej2 = 0; ej2 < ep_arity; ej2++) c = nbe_vapp(a, c, ep_args[ej2]);
            return c;
        }
    }
    return nbe_vapp(a, P_approx, v);
}

/* ── indrec PATH case type-checker ─────────────────────────────────────────
 *
 * For a path ctor c : Π(args). Path T lhs rhs, the expected case type is:
 *   Π(args). PathP (λi. P(c args @ i)) (rec lhs) (rec rhs)
 * where rec x = indrec P eval_cases x.
 * eval_cases[k] = NULL for path ctors (not yet computed); must not be called
 * for endpoint values that are those ctors.
 * Strips lambda binders, builds the PathP type, and checks the body.
 * Returns 1 on success, 0 on failure (error already printed).
 */
static int check_indrec_path_case(
    Arena *a, int depth, TCtx *tctx, Env *env,
    Term *case_t, Val *tele_v,
    int fam_idx, int ci, IndDef *fam,
    int n_params, Val **param_vals, Val *P_val,
    Val **eval_cases)
{
    CtorDef *ctor = &fam->ctors[ci];
    int arity = ctor->arity;

    Val **arg_freshes = arity > 0
        ? (Val **)arena_alloc(a, arity * sizeof(Val *)) : NULL;

    for (int i = 0; i < arity; i++) {
        /* Strip annotation wrapper so annotated lambdas (expr : ty) also work */
        if (case_t->tag == TM_ANN) case_t = case_t->ann.term;
        if (!tele_v || tele_v->tag != VL_PI) {
            type_error(case_t->loc, "'indrec' for '%s' path case '%s': telescope too short at arg %d\n",
                    fam->name, ctor->name, i);
            return 0;
        }
        Val *arg_ty = tele_v->pi.dom;
        if (case_t->tag != TM_LAM) {
            type_error(case_t->loc, "'indrec' for '%s' path case '%s': expected lambda at arg %d\n"
                    "  hint: write  \\%s. body  or annotate\n",
                    fam->name, ctor->name, i, ctor->name);
            return 0;
        }
        Val *k_fresh = vl_neutral(a, depth, NULL);
        TCtx *k_node = (TCtx *)arena_alloc(a, sizeof(TCtx));
        k_node->name = case_t->lam.name; k_node->type = arg_ty; k_node->next = tctx;
        tctx  = k_node;
        env   = env_cons(a, k_fresh, env);
        depth++;
        arg_freshes[i] = k_fresh;
        case_t = case_t->lam.body;
        tele_v = nbe_eval(a, env_cons(a, k_fresh, tele_v->pi.env), tele_v->pi.cod);
    }

    /* For indexed families (n_indices > 0) the motive has type
     *   Π(i₁:I₁). … Π(iₙ:Iₙ). FamType params i₁…iₙ → Type
     * and the PathP family must be  λi. P idx₁…idxₙ (pc @ i).
     * The index values live in the carrier of the path ctor's return type:
     * after the telescope loop, tele_v = VL_PATH(carrier, lhs, rhs) where
     * carrier = VL_INDTYPE(fam, [param_vals..., idx_vals...]).
     * Pre-applying P to the idx_vals gives P_for_fam = P idx₁…idxₙ,
     * so the PathP body stays  APP(VAR(2), PATHAPP(VAR(1), VAR(0)))  unchanged
     * but VAR(2) now refers to P_for_fam instead of bare P. */
    Val *P_for_fam = P_val;
    if (fam->n_indices > 0 &&
        tele_v && (tele_v->tag == VL_PATH || tele_v->tag == VL_PATHP) &&
        tele_v->id.ty && tele_v->id.ty->tag == VL_INDTYPE &&
        tele_v->id.ty->indtype.fam_idx == fam_idx) {
        Val *carrier = tele_v->id.ty;
        for (int j = n_params; j < carrier->indtype.n_args; j++)
            P_for_fam = nbe_vapp(a, P_for_fam, carrier->indtype.args[j]);
    }

    /* Build eval env for endpoint terms:
     * dB 0 = arg_freshes[arity-1] (last arg), …, dB arity-1 = arg_freshes[0],
     * dB arity = param_vals[n_params-1] (last param), …
     * Built by prepending params first, then ctor args (each prepend becomes new dB 0). */
    Env *ep_env = NULL;
    for (int j = 0; j < n_params; j++)
        ep_env = env_cons(a, param_vals[j], ep_env);
    for (int j = 0; j < arity; j++)
        ep_env = env_cons(a, arg_freshes[j], ep_env);

    Val *lhs_val = nbe_eval(a, ep_env, ctor->path_lhs_term);
    Val *rhs_val = nbe_eval(a, ep_env, ctor->path_rhs_term);
    /* Endpoint values: rec(lhs), rec(rhs).
     * For 1-cell: lhs/rhs are points or VL_NEUTRAL path-ctor sentinels.
     * For 2-cell: lhs/rhs are the OUTER path endpoints (1-cell path ctor vals);
     *             carrier endpoints come from path_carrier_{lhs,rhs}_term. */
    int np = ind_get(fam_idx)->n_params;
    Val *rec_lhs = hit_compute_rec(a, lhs_val, fam_idx, np, eval_cases, P_for_fam);
    Val *rec_rhs = hit_compute_rec(a, rhs_val, fam_idx, np, eval_cases, P_for_fam);

    /* Build path ctor val = c args (sentinel neutral) */
    Spine *pc_sp = NULL;
    for (int j = 0; j < n_params; j++)
        pc_sp = spine_cons(a, param_vals[j], pc_sp);
    for (int j = 0; j < arity; j++)
        pc_sp = spine_cons(a, arg_freshes[j], pc_sp);
    Val *pc_val = vl_neutral(a, hit_path_sentinel_c(fam_idx, ci), pc_sp);

    Val *exp_pathp;

    if (ctor->is_2cell) {
        /* 2-cell ctor: expected case type is a nested PathP:
         *   PathP (λi. PathP (λj. P ((pc@i)@j)) (rec l) (rec r)) (rec p) (rec q)
         * where p,q = outer lhs/rhs (= rec_lhs, rec_rhs above)
         *       l,r = carrier (inner path) lhs/rhs.                             */
        Val *cl_val = nbe_eval(a, ep_env, ctor->path_carrier_lhs_term);
        Val *cr_val = nbe_eval(a, ep_env, ctor->path_carrier_rhs_term);
        Val *rec_cl = hit_compute_rec(a, cl_val, fam_idx, np, eval_cases, P_for_fam);
        Val *rec_cr = hit_compute_rec(a, cr_val, fam_idx, np, eval_cases, P_for_fam);

        /* Inner PathP family: λj. P_for_fam ((pc @ i) @ j)
         * outer_fam_env = [pc_val, P_for_fam, rec_cl, rec_cr]
         * After outer λi applied: [i(0), pc(1), P(2), rec_cl(3), rec_cr(4)]
         * After inner λj applied: [j(0), i(1), pc(2), P(3), rec_cl(4), rec_cr(5)]
         * inner_body = APP(VAR(3), PATHAPP(PATHAPP(VAR(2), VAR(1)), VAR(0)))
         * outer_body = PATHP(TM_LAM("j", inner_body), VAR(3), VAR(4))           */
        Term *inner_body = tm_app(a, tm_var(a, 3),
            tm_pathapp(a, tm_pathapp(a, tm_var(a, 2), tm_var(a, 1)), tm_var(a, 0)));
        Term *outer_body = tm_pathp(a,
            tm_lam(a, "j", inner_body), tm_var(a, 3), tm_var(a, 4));
        Env *outer_fam_env = env_cons(a, pc_val,
                             env_cons(a, P_for_fam,
                             env_cons(a, rec_cl,
                             env_cons(a, rec_cr, NULL))));
        Val *outer_fam = vl_lam(a, "i", outer_fam_env, outer_body);

        exp_pathp = vl_pathp(a, outer_fam, rec_lhs, rec_rhs);

        if (!check(a, depth, tctx, env, case_t, exp_pathp)) {
            type_error(case_t->loc,
                "'indrec' for '%s' 2-cell path case '%s' body: type mismatch\n"
                "  expected: PathP (λi. PathP (λj. P (c args @ i @ j)) (rec l) (rec r))"
                " (rec p) (rec q)\n",
                fam->name, ctor->name);
            return 0;
        }
        return 1;
    }

    /* 1-cell ctor: PathP (λi. P_for_fam (pc_val @ i)) (rec lhs) (rec rhs)
     * fam_env = [pc_val, P_for_fam].  After applying i: [i(0), pc(1), P(2)].
     * body = APP(VAR(2), PATHAPP(VAR(1), VAR(0))) = P_for_fam (pc_val @ i)      */
    Env *fam_env = env_cons(a, pc_val, env_cons(a, P_for_fam, NULL));
    Term *fam_body = tm_app(a, tm_var(a, 2), tm_pathapp(a, tm_var(a, 1), tm_var(a, 0)));
    Val *fam_lam = vl_lam(a, "i", fam_env, fam_body);

    exp_pathp = vl_pathp(a, fam_lam, rec_lhs, rec_rhs);

    if (!check(a, depth, tctx, env, case_t, exp_pathp)) {
        type_error(case_t->loc, "'indrec' for '%s' path case '%s' body: type mismatch\n"
                "  expected: PathP (λi. P idx₁…idxₙ (c args @ i)) (rec lhs) (rec rhs)\n",
                fam->name, ctor->name);
        return 0;
    }
    return 1;
}

/* ── indrec case type-checker via lambda peeling ───────────────────────────
 *
 * When `infer` cannot determine the case term's type (e.g., bare lambdas),
 * this helper strips TM_LAM binders one by one and checks each against the
 * corresponding ctor argument type (from the evaluated telescope).  IH binders
 * are also stripped at recursive positions.  The final body is checked against
 * the motive applied to the synthesized constructor.
 *
 * This is the CORRECT fix for LIMIT-3: instead of calling `infer` (which
 * fails on bare lambdas), we use `check` at the body level, which avoids the
 * need for a type annotation on every recursive case.
 *
 * Returns 1 on success, 0 on failure (error already printed).
 */
static int check_indrec_case_peel(
    Arena *a, int depth, TCtx *tctx, Env *env,
    Term *case_t, Val *tele_v,               /* evaluated ctor telescope    */
    int fam_idx, int ci, IndDef *fam,
    int n_params, Val **param_vals, Val *P_val)
{
    CtorDef *ctor = &fam->ctors[ci];
    int arity = ctor->arity;

    /* arg_freshes[i] = the neutral introduced for ctor arg i (not IHs) */
    Val **arg_freshes = arity > 0
        ? (Val **)arena_alloc(a, arity * sizeof(Val *)) : NULL;

    for (int i = 0; i < arity; i++) {
        if (!tele_v || tele_v->tag != VL_PI) {
            type_error(case_t->loc, "'indrec' for '%s' case '%s': telescope too short at arg %d\n",
                    fam->name, ctor->name, i);
            return 0;
        }
        Val *arg_ty = tele_v->pi.dom;

        /* Expect a lambda binder for this arg */
        if (case_t->tag != TM_LAM) {
            type_error(case_t->loc, "'indrec' for '%s' case '%s': expected lambda at arg %d\n"
                    "  hint: write  \\%s. body  or annotate with its full type\n",
                    fam->name, ctor->name, i, ctor->name);
            return 0;
        }

        Val *k_fresh = vl_neutral(a, depth, NULL);
        /* arena-allocate TCtx so it survives multiple loop iterations */
        TCtx *k_node = (TCtx *)arena_alloc(a, sizeof(TCtx));
        k_node->name = case_t->lam.name; k_node->type = arg_ty; k_node->next = tctx;
        tctx  = k_node;
        env   = env_cons(a, k_fresh, env);
        depth++;
        arg_freshes[i] = k_fresh;
        case_t  = case_t->lam.body;
        tele_v  = nbe_eval(a, env_cons(a, k_fresh, tele_v->pi.env), tele_v->pi.cod);

        /* Recursive position: expect an IH lambda after the arg */
        if (ind_is_recursive_pos(fam_idx, ci, i)) {
            Val *IH_ty = P_val;
            if (arg_ty->tag == VL_INDTYPE)
                for (int j = n_params; j < arg_ty->indtype.n_args; j++)
                    IH_ty = nbe_vapp(a, IH_ty, arg_ty->indtype.args[j]);
            IH_ty = nbe_vapp(a, IH_ty, k_fresh);

            if (case_t->tag != TM_LAM) {
                type_error(case_t->loc, "'indrec' for '%s' case '%s': expected IH lambda at arg %d\n"
                        "  hint: write  \\%s. \\ih. body\n",
                        fam->name, ctor->name, i, ctor->name);
                return 0;
            }
            Val *ih_fresh = vl_neutral(a, depth, NULL);
            TCtx *ih_node = (TCtx *)arena_alloc(a, sizeof(TCtx));
            ih_node->name = case_t->lam.name; ih_node->type = IH_ty; ih_node->next = tctx;
            tctx  = ih_node;
            env   = env_cons(a, ih_fresh, env);
            depth++;
            /* ih_fresh NOT added to arg_freshes — IH is not a ctor field */
            case_t = case_t->lam.body;
        }
    }

    /* All arg (and IH) lambdas peeled.  Compute expected body type:
     * P applied to return indices (for indexed families) then to synth_con.  */
    int n_total = n_params + arity;
    Val **con_args = n_total > 0 ? (Val **)arena_alloc(a, n_total * sizeof(Val *)) : NULL;
    for (int i = 0; i < n_params; i++) con_args[i]          = param_vals[i];
    for (int i = 0; i < arity;    i++) con_args[n_params + i] = arg_freshes[i];
    Val *synth_con = vl_indcon(a, fam_idx, ci, n_total, con_args);

    Val *exp_result = P_val;
    if (tele_v && tele_v->tag == VL_INDTYPE)
        for (int j = n_params; j < tele_v->indtype.n_args; j++)
            exp_result = nbe_vapp(a, exp_result, tele_v->indtype.args[j]);
    exp_result = nbe_vapp(a, exp_result, synth_con);

    if (!check(a, depth, tctx, env, case_t, exp_result)) {
        type_error(case_t->loc, "'indrec' for '%s' case '%s' body: type mismatch\n",
                fam->name, ctor->name);
        return 0;
    }
    return 1;
}

/* ── Infer */

Val *infer(Arena *a, int depth, TCtx *tctx, Env *env, Term *t) {
    switch (t->tag) {

    case TM_VAR: {
        Val *ty = tctx_lookup(tctx, t->idx);
        if (!ty) {
            type_error(t->loc, "variable at index %d out of scope\n", t->idx);
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
            type_error(t->loc, "%s domain is not a type\n",
                    t->tag == TM_PI ? "Π" : "Σ");
            print_type(a, depth, tctx, "got", dty);
            return NULL;
        }
        Val *domv  = nbe_eval(a, env, t->pi.dom);
        Val *fresh = vl_neutral(a, depth, NULL);
        TCtx ext   = { t->pi.name, domv, tctx };
        Val *cty   = infer(a, depth + 1, &ext, env_cons(a, fresh, env), t->pi.cod);
        if (!cty) return NULL;
        int j;
        if (!as_universe(cty, &j)) {
            type_error(t->loc, "%s codomain is not a type\n",
                    t->tag == TM_PI ? "Π" : "Σ");
            print_type(a, depth + 1, tctx, "got", cty);
            return NULL;
        }
        return uni_at(a, imax(i, j));
    }

    case TM_APP: {
        Val *fty = infer(a, depth, tctx, env, t->app.fun);
        if (!fty) return NULL;
        if (fty->tag != VL_PI) {
            type_error(t->loc, "applied non-function\n");
            print_type(a, depth, tctx, "got", fty);
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
            type_error(t->loc, "fst applied to non-Σ type\n");
            print_type(a, depth, tctx, "got", pty);
            return NULL;
        }
        return pty->pi.dom;
    }

    case TM_SND: {
        Val *pty = infer(a, depth, tctx, env, t->elim);
        if (!pty) return NULL;
        if (pty->tag != VL_SIGMA) {
            type_error(t->loc, "snd applied to non-Σ type\n");
            print_type(a, depth, tctx, "got", pty);
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
            type_error(t->loc, "annotation is not a type\n");
            print_type(a, depth, tctx, "got", tty);
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
            type_error(t->loc, "Id type argument is not a type\n");
            print_type(a, depth, tctx, "got", Aty);
            return NULL;
        }
        Val *A_val = nbe_eval(a, env, t->id.ty);
        if (!check(a, depth, tctx, env, t->id.lhs, A_val)) return NULL;
        if (!check(a, depth, tctx, env, t->id.rhs, A_val)) return NULL;
        return uni_at(a, i);
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
            type_error(t->loc, "J: first argument is not a type\n");
            return NULL;
        }
        Val *A_val = nbe_eval(a, env, t->j.ty);
        if (!check(a, depth, tctx, env, t->j.lhs, A_val)) return NULL;
        Val *a_val = nbe_eval(a, env, t->j.lhs);

        /* Check P : Π(b:A). Id(A,a,b) → Type_k */
        Val *P_ty = infer(a, depth, tctx, env, t->j.motive);
        if (!P_ty) return NULL;
        if (P_ty->tag != VL_PI) {
            type_error(t->loc, "J: motive is not a function\n");
            return NULL;
        }
        if (!conv(a, depth, P_ty->pi.dom, A_val)) {
            type_error(t->loc, "J: motive domain does not match A\n");
            return NULL;
        }
        Val *fresh_b = vl_neutral(a, depth, NULL);
        Val *P_cod   = nbe_eval(a, env_cons(a, fresh_b, P_ty->pi.env), P_ty->pi.cod);
        if (P_cod->tag != VL_PI) {
            type_error(t->loc, "J: motive codomain is not a function\n");
            return NULL;
        }
        /* Motive second arg must be Id A a b or Path A a b */
        Val *exp_id   = vl_id(a, A_val, a_val, fresh_b);
        Val *exp_path = vl_path(a, A_val, a_val, fresh_b);
        if (!conv(a, depth + 1, P_cod->pi.dom, exp_id) &&
            !conv(a, depth + 1, P_cod->pi.dom, exp_path)) {
            type_error(t->loc, "J: motive second argument must be Id or Path\n");
            return NULL;
        }
        Val *fresh_p  = vl_neutral(a, depth + 1, NULL);
        Val *P_result = nbe_eval(a, env_cons(a, fresh_p, P_cod->pi.env), P_cod->pi.cod);
        int k;
        if (!as_universe(P_result, &k)) {
            type_error(t->loc, "J: motive does not map into a universe\n");
            return NULL;
        }

        /* Check d : P a (refl a) */
        Val *P_val  = nbe_eval(a, env, t->j.motive);
        Val *d_ty   = nbe_vapp(a, nbe_vapp(a, P_val, a_val), vl_refl(a, a_val));
        if (!check(a, depth, tctx, env, t->j.base, d_ty)) return NULL;

        /* Check b : A and p : Id(A,a,b) or Path A a b or PathP (λ_.A) a b */
        if (!check(a, depth, tctx, env, t->j.endpoint, A_val)) return NULL;
        Val *b_val   = nbe_eval(a, env, t->j.endpoint);
        Val *id_ty   = vl_id(a, A_val, a_val, b_val);
        Val *path_ty = vl_path(a, A_val, a_val, b_val);
        Val *proof_ty = infer(a, depth, tctx, env, t->j.proof);
        if (!proof_ty) return NULL;
        if (!conv(a, depth, proof_ty, id_ty) &&
            !conv(a, depth, proof_ty, path_ty)) {
            type_error(t->loc, "J: proof must have type Id A a b or Path A a b\n");
            print_type(a, depth, tctx, "got", proof_ty);
            return NULL;
        }
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
            type_error(t->loc, "natrec: motive is not a function\n");
            return NULL;
        }
        if (!conv(a, depth, P_ty->pi.dom, vl_nat(a))) {
            type_error(t->loc, "natrec: motive domain is not Nat\n");
            return NULL;
        }
        Val *fresh0 = vl_neutral(a, depth, NULL);
        Val *P_cod  = nbe_eval(a, env_cons(a, fresh0, P_ty->pi.env), P_ty->pi.cod);
        int i;
        if (!as_universe(P_cod, &i)) {
            type_error(t->loc, "natrec: motive does not map into a universe\n");
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
            type_error(t->loc, "natrec: step is not a function\n");
            return NULL;
        }
        if (!conv(a, depth, s_ity->pi.dom, vl_nat(a))) {
            type_error(t->loc, "natrec: step domain is not Nat\n");
            return NULL;
        }
        Val *fresh_m = vl_neutral(a, depth, NULL);    /* outer Pi var (m : Nat) */
        Val *s_cod   = nbe_eval(a, env_cons(a, fresh_m, s_ity->pi.env), s_ity->pi.cod);
        if (s_cod->tag != VL_PI) {
            type_error(t->loc, "natrec: step codomain is not a function\n");
            return NULL;
        }
        Val *P_m = nbe_vapp(a, P_val, fresh_m);
        if (!conv(a, depth + 1, s_cod->pi.dom, P_m)) {
            type_error(t->loc, "natrec: step arg type is not P m\n");
            return NULL;
        }
        Val *fresh_pm = vl_neutral(a, depth + 1, NULL); /* inner Pi var (r : P m) */
        Val *s_result = nbe_eval(a, env_cons(a, fresh_pm, s_cod->pi.env), s_cod->pi.cod);
        if (!conv(a, depth + 2, s_result, nbe_vapp(a, P_val, vl_succ(a, fresh_m)))) {
            type_error(t->loc, "natrec: step return type is not P(succ m)\n");
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
            type_error(t->loc, "boolrec: motive is not a function\n");
            return NULL;
        }
        if (!conv(a, depth, P_ty->pi.dom, vl_bool(a))) {
            type_error(t->loc, "boolrec: motive domain is not Bool\n");
            return NULL;
        }
        Val *fresh = vl_neutral(a, depth, NULL);
        Val *P_cod = nbe_eval(a, env_cons(a, fresh, P_ty->pi.env), P_ty->pi.cod);
        int i;
        if (!as_universe(P_cod, &i)) {
            type_error(t->loc, "boolrec: motive does not map into a universe\n");
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
            type_error(t->loc, "unitrec: motive is not a function\n");
            return NULL;
        }
        if (!conv(a, depth, P_ty->pi.dom, vl_unit(a))) {
            type_error(t->loc, "unitrec: motive domain is not Unit\n");
            return NULL;
        }
        Val *fresh = vl_neutral(a, depth, NULL);
        Val *P_cod = nbe_eval(a, env_cons(a, fresh, P_ty->pi.env), P_ty->pi.cod);
        int i;
        if (!as_universe(P_cod, &i)) {
            type_error(t->loc, "unitrec: motive does not map into a universe\n");
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
            type_error(t->loc, "abort: first argument is not a type\n");
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
            type_error(t->loc, "Sum left type is not a type\n");
            return NULL;
        }
        Val *Bty = infer(a, depth, tctx, env, t->sum_t.right);
        if (!Bty) return NULL;
        int j;
        if (!as_universe(Bty, &j)) {
            type_error(t->loc, "Sum right type is not a type\n");
            return NULL;
        }
        return uni_at(a, imax(i, j));
    }

    case TM_INL:
        type_error(t->loc, "cannot infer type of inl — wrap in annotation: ((inl a) : Sum A B)\n");
        return NULL;

    case TM_INR:
        type_error(t->loc, "cannot infer type of inr — wrap in annotation: ((inr b) : Sum A B)\n");
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
            type_error(t->loc, "case: motive is not a function\n");
            return NULL;
        }
        Val *Sum_ty = P_ty->pi.dom;
        if (Sum_ty->tag != VL_SUM) {
            type_error(t->loc, "case: motive domain is not a Sum type\n");
            return NULL;
        }
        Val *A = Sum_ty->pair.fst;
        Val *B = Sum_ty->pair.snd;
        {
            Val *fresh = vl_neutral(a, depth, NULL);
            Val *P_cod = nbe_eval(a, env_cons(a, fresh, P_ty->pi.env), P_ty->pi.cod);
            int k;
            if (!as_universe(P_cod, &k)) {
                type_error(t->loc, "case: motive codomain is not a universe\n");
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
            type_error(t->loc, "W domain is not a type\n");
            return NULL;
        }
        Val *domv  = nbe_eval(a, env, t->pi.dom);
        Val *fresh = vl_neutral(a, depth, NULL);
        TCtx ext   = { t->pi.name, domv, tctx };
        Val *cty   = infer(a, depth + 1, &ext, env_cons(a, fresh, env), t->pi.cod);
        if (!cty) return NULL;
        int j;
        if (!as_universe(cty, &j)) {
            type_error(t->loc, "W codomain is not a type\n");
            return NULL;
        }
        return uni_at(a, imax(i, j));
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
            type_error(t->loc, "wrec: motive is not a function\n");
            return NULL;
        }
        Val *W_ty = P_ty->pi.dom;
        if (W_ty->tag != VL_W) {
            type_error(t->loc, "wrec: motive domain is not a W type\n");
            return NULL;
        }
        {
            Val *fresh = vl_neutral(a, depth, NULL);
            Val *pcod  = nbe_eval(a, env_cons(a, fresh, P_ty->pi.env), P_ty->pi.cod);
            int kk;
            if (!as_universe(pcod, &kk)) {
                type_error(t->loc, "wrec: motive codomain is not a universe\n");
                return NULL;
            }
        }
        Val *P_val = nbe_eval(a, env, t->wrec.motive);
        Val *A     = W_ty->pi.dom;

        /* Check step s structurally */
        Val *s_ity = infer(a, depth, tctx, env, t->wrec.step);
        if (!s_ity) return NULL;
        if (s_ity->tag != VL_PI) {
            type_error(t->loc, "wrec: step is not a function\n");
            return NULL;
        }
        if (!conv(a, depth, s_ity->pi.dom, A)) {
            type_error(t->loc, "wrec: step domain is not A\n");
            return NULL;
        }
        int d = depth;
        Val *fa    = vl_neutral(a, d++, NULL);   /* fa : A */
        Val *B_fa  = nbe_eval(a, env_cons(a, fa, W_ty->pi.env), W_ty->pi.cod);
        Val *s_cod1 = nbe_eval(a, env_cons(a, fa, s_ity->pi.env), s_ity->pi.cod);

        /* s_cod1 : Π(f: B(fa)→W). ... */
        if (s_cod1->tag != VL_PI) {
            type_error(t->loc, "wrec: step second argument missing\n");
            return NULL;
        }
        Val *f_ty = s_cod1->pi.dom;
        if (f_ty->tag != VL_PI) {
            type_error(t->loc, "wrec: step arg 2 is not B(a)→W\n");
            return NULL;
        }
        if (!conv(a, d, f_ty->pi.dom, B_fa)) {
            type_error(t->loc, "wrec: step arg 2 domain is not B(a)\n");
            return NULL;
        }
        Val *fb1   = vl_neutral(a, d++, NULL);   /* fb1 : B(fa) — opens f_ty cod */
        Val *f_cod = nbe_eval(a, env_cons(a, fb1, f_ty->pi.env), f_ty->pi.cod);
        if (!conv(a, d, f_cod, W_ty)) {
            type_error(t->loc, "wrec: step arg 2 codomain is not W\n");
            return NULL;
        }
        Val *ff    = vl_neutral(a, d++, NULL);   /* ff : B(fa)→W */
        Val *s_cod2 = nbe_eval(a, env_cons(a, ff, s_cod1->pi.env), s_cod1->pi.cod);

        /* s_cod2 : Π(ih: Π(b:B(fa)).P(ff b)). ... */
        if (s_cod2->tag != VL_PI) {
            type_error(t->loc, "wrec: step third argument missing\n");
            return NULL;
        }
        Val *ih_ty = s_cod2->pi.dom;
        if (ih_ty->tag != VL_PI) {
            type_error(t->loc, "wrec: step arg 3 is not Π(b:B(a)).P(f b)\n");
            return NULL;
        }
        if (!conv(a, d, ih_ty->pi.dom, B_fa)) {
            type_error(t->loc, "wrec: step arg 3 domain is not B(a)\n");
            return NULL;
        }
        Val *fb2    = vl_neutral(a, d++, NULL);   /* fb2 : B(fa) — opens ih cod */
        Val *ih_cod = nbe_eval(a, env_cons(a, fb2, ih_ty->pi.env), ih_ty->pi.cod);
        if (!conv(a, d, ih_cod, nbe_vapp(a, P_val, nbe_vapp(a, ff, fb2)))) {
            type_error(t->loc, "wrec: step arg 3 codomain is not P(f b)\n");
            return NULL;
        }
        Val *fih    = vl_neutral(a, d++, NULL);   /* fih : ih type */
        Val *s_res  = nbe_eval(a, env_cons(a, fih, s_cod2->pi.env), s_cod2->pi.cod);
        Val *sup_af = vl_sup(a, fa, ff);
        if (!conv(a, d, s_res, nbe_vapp(a, P_val, sup_af))) {
            type_error(t->loc, "wrec: step result is not P(sup a f)\n");
            return NULL;
        }

        /* Check w : W(x:A).B(x) */
        if (!check(a, depth, tctx, env, t->wrec.scrut, W_ty)) return NULL;
        Val *w_val = nbe_eval(a, env, t->wrec.scrut);
        return nbe_vapp(a, P_val, w_val);
    }

    case TM_TRUNC:
        return get_trunc_type();   /* Π(_ : Type). Type */

    case TM_TRINT:
        return get_trint_type();   /* Π(A : Type). Π(_ : A). trunc A */

    case TM_SQUASH:
        return get_squash_type();  /* Π(A : Type). Π(x : trunc A). Π(y : trunc A). Id (trunc A) x y */

    case TM_QUOT:
        /* Known limitation: Quot A R always lives at Type_0 regardless of level(A).
         * Universe-polymorphic quotients (A : Type_k, k > 0) are not supported. */
        return get_quot_type();   /* Π(A : Type). Π(_ : A→A→Type). Type */

    case TM_QIN:
        return get_qin_type();    /* Π(A). Π(R). A → Quot A R */

    case TM_QEQS:
        return get_qeq_type();    /* Π(A). Π(R). Π(a). Π(b). R a b → Id (Quot A R) (qin a) (qin b) */

    case TM_QUOTREC: {
        /* quotrec A R B f coh x : B
         * A : Type,  R : A→A→Type,  B : Type,  f : A→B,  coh : trusted,  x : Quot A R */
        Val *Aty = infer(a, depth, tctx, env, t->quotrec_t.ty_a);
        if (!Aty) return NULL;
        int i;
        if (!as_universe(Aty, &i)) {
            type_error(t->loc, "quotrec: A is not a type\n");
            return NULL;
        }
        Val *A_val = nbe_eval(a, env, t->quotrec_t.ty_a);
        Val *Bty = infer(a, depth, tctx, env, t->quotrec_t.ty_b);
        if (!Bty) return NULL;
        int j;
        if (!as_universe(Bty, &j)) {
            type_error(t->loc, "quotrec: B is not a type\n");
            return NULL;
        }
        Val *B_val = nbe_eval(a, env, t->quotrec_t.ty_b);
        /* Check f : A → B */
        Val *f_ty = vl_pi(a, "_", A_val, env_cons(a, B_val, NULL), tm_var(a, 1));
        if (!check(a, depth, tctx, env, t->quotrec_t.func, f_ty)) return NULL;
        /* coh : trusted — not type-checked */
        /* Check x : Quot A R */
        Val *R_val = nbe_eval(a, env, t->quotrec_t.rel);
        Val *quot_AR = vl_neutral(a, QUOT_CONST_LVL,
                           spine_cons(a, R_val, spine_cons(a, A_val, NULL)));
        if (!check(a, depth, tctx, env, t->quotrec_t.scrut, quot_AR)) return NULL;
        return B_val;
    }

    case TM_TRUNCREC: {
        /* truncrec A B f t : B
         * A : Type_i,  B : Type_j,  f : A → B,  t : trunc A    */
        Val *Aty = infer(a, depth, tctx, env, t->truncrec_t.ty_a);
        if (!Aty) return NULL;
        int i;
        if (!as_universe(Aty, &i)) {
            type_error(t->loc, "truncrec: first argument is not a type\n");
            return NULL;
        }
        Val *A_val = nbe_eval(a, env, t->truncrec_t.ty_a);
        Val *Bty = infer(a, depth, tctx, env, t->truncrec_t.ty_b);
        if (!Bty) return NULL;
        int j;
        if (!as_universe(Bty, &j)) {
            type_error(t->loc, "truncrec: second argument is not a type\n");
            return NULL;
        }
        Val *B_val = nbe_eval(a, env, t->truncrec_t.ty_b);
        /* Check f : A → B (constant codomain B) */
        Val *f_ty = vl_pi(a, "_", A_val, env_cons(a, B_val, NULL), tm_var(a, 1));
        if (!check(a, depth, tctx, env, t->truncrec_t.func, f_ty)) return NULL;
        /* Check t : trunc A */
        Val *trunc_A = vl_neutral(a, TRUNC_CONST_LVL, spine_cons(a, A_val, NULL));
        if (!check(a, depth, tctx, env, t->truncrec_t.scrut, trunc_A)) return NULL;
        return B_val;
    }

    case TM_CIRCLE:
        return vl_uni(a, 0);   /* S¹ : Type */

    case TM_BASE:
        return vl_circle(a);   /* base : S¹ */

    case TM_LOOP:
        return get_loop_type();  /* loop : Id S¹ base base */

    case TM_CIRCREC: {
        /* S1rec B b l s : B
         * B : Type_i,  b : B,  l : Id B b b,  s : S¹          */
        Val *Bty = infer(a, depth, tctx, env, t->circrec_t.motive);
        if (!Bty) return NULL;
        int i;
        if (!as_universe(Bty, &i)) {
            type_error(t->loc, "S1rec: motive is not a type\n");
            return NULL;
        }
        Val *B_val = nbe_eval(a, env, t->circrec_t.motive);
        if (!check(a, depth, tctx, env, t->circrec_t.base_case, B_val)) return NULL;
        Val *b_val = nbe_eval(a, env, t->circrec_t.base_case);
        /* Check l : Id B b b */
        Val *l_ty = vl_id(a, B_val, b_val, b_val);
        if (!check(a, depth, tctx, env, t->circrec_t.loop_case, l_ty)) return NULL;
        if (!check(a, depth, tctx, env, t->circrec_t.scrut, vl_circle(a))) return NULL;
        return B_val;
    }

    case TM_UA:
        return get_ua_type();

    case TM_FUNEXT:
        return get_funext_type();

    case TM_GLOBAL:
        return def_get(t->idx)->type;

    case TM_LAM:
        type_error(t->loc, "cannot infer type of λ — wrap in annotation: (\\%s. ... : Π(%s:T). ...)\n",
            t->lam.name, t->lam.name);
        return NULL;

    case TM_PAIR:
        type_error(t->loc, "cannot infer type of pair — wrap in annotation: ((a, b) : Σ(x:A). B)\n");
        return NULL;

    case TM_SUP:
        type_error(t->loc, "cannot infer type of sup — wrap in annotation: "
            "((sup a f) : W(x:A). B)\n");
        return NULL;

    case TM_INDTYPE: {
        IndDef *fam   = ind_get(t->indtype.fam_idx);
        int n_params  = fam->n_params;
        int n_indices = fam->n_indices;
        if (t->indtype.n_args != n_params + n_indices) {
            type_error(t->loc, "'%s' expects %d argument(s), got %d\n",
                    fam->name, n_params + n_indices, t->indtype.n_args);
            return NULL;
        }
        /* Check param args against param_types (closed terms) */
        for (int i = 0; i < n_params; i++) {
            if (!fam->param_types || !fam->param_types[i]) {
                type_error(t->loc, "'%s': parameter type %d not defined\n", fam->name, i);
                return NULL;
            }
            Val *pty = nbe_eval(a, NULL, fam->param_types[i]);
            if (!check(a, depth, tctx, env, t->indtype.args[i], pty)) return NULL;
        }
        /* Build param env: VAR(0) = last param evaluated in typing env */
        Env *param_env = NULL;
        for (int i = 0; i < n_params; i++) {
            Val *pv = nbe_eval(a, env, t->indtype.args[i]);
            param_env = env_cons(a, pv, param_env);
        }
        /* Check index args against index_types in param context */
        Env *idx_env = param_env;
        for (int j = 0; j < n_indices; j++) {
            if (fam->index_types && fam->index_types[j]) {
                Val *ity = nbe_eval(a, idx_env, fam->index_types[j]);
                if (!check(a, depth, tctx, env, t->indtype.args[n_params + j], ity)) return NULL;
            }
            Val *iv = nbe_eval(a, env, t->indtype.args[n_params + j]);
            idx_env = env_cons(a, iv, idx_env);
        }
        return vl_uni(a, 0);
    }

    case TM_INDCON: {
        int fam_idx  = t->indcon.fam_idx;
        IndDef *fam  = ind_get(fam_idx);
        int ctor_idx = t->indcon.ctor_idx;
        if (ctor_idx < 0 || ctor_idx >= fam->n_ctors) {
            type_error(t->loc, "'%s': invalid constructor index %d\n",
                    fam->name, ctor_idx);
            return NULL;
        }
        CtorDef *ctor = &fam->ctors[ctor_idx];
        int n_params  = fam->n_params;
        int arity     = ctor->arity;
        if (t->indcon.n_args != n_params + arity) {
            type_error(t->loc, "constructor '%s' of '%s': expected %d argument(s), got %d\n",
                    ctor->name, fam->name, n_params + arity, t->indcon.n_args);
            return NULL;
        }
        /* Check param args (closed param_types) */
        Val **param_vals = n_params > 0
            ? (Val **)arena_alloc(a, n_params * sizeof(Val *)) : NULL;
        for (int i = 0; i < n_params; i++) {
            if (!fam->param_types || !fam->param_types[i]) {
                type_error(t->loc, "'%s': parameter type %d not defined\n", fam->name, i);
                return NULL;
            }
            Val *pty = nbe_eval(a, NULL, fam->param_types[i]);
            if (!check(a, depth, tctx, env, t->indcon.args[i], pty)) return NULL;
            param_vals[i] = nbe_eval(a, env, t->indcon.args[i]);
        }
        /* Build param env */
        Env *param_env = NULL;
        for (int i = 0; i < n_params; i++)
            param_env = env_cons(a, param_vals[i], param_env);
        /* Check ctor args by walking the telescope */
        if (arity == 0) {
            /* No args: compute return type from ret_indices or telescope */
            if (ctor->telescope) {
                Val *ret = nbe_eval(a, param_env, ctor->telescope);
                if (ret->tag != VL_INDTYPE || ret->indtype.fam_idx != fam_idx) {
                    type_error(t->loc, "constructor '%s' return type is not '%s'\n",
                            ctor->name, fam->name);
                    return NULL;
                }
                return ret;
            }
            /* Fallback: build return type from n_indices (unindexed families) */
            return vl_indtype(a, fam_idx, n_params, param_vals);
        }
        if (!ctor->telescope) {
            type_error(t->loc, "constructor '%s' of '%s' has no telescope (cannot check)\n",
                    ctor->name, fam->name);
            return NULL;
        }
        Val *tele = nbe_eval(a, param_env, ctor->telescope);
        for (int i = 0; i < arity; i++) {
            if (tele->tag != VL_PI) {
                type_error(t->loc, "constructor '%s': telescope shorter than arity at arg %d\n",
                        ctor->name, i);
                return NULL;
            }
            if (!check(a, depth, tctx, env, t->indcon.args[n_params + i], tele->pi.dom))
                return NULL;
            Val *av = nbe_eval(a, env, t->indcon.args[n_params + i]);
            tele = nbe_eval(a, env_cons(a, av, tele->pi.env), tele->pi.cod);
        }
        if (tele->tag != VL_INDTYPE || tele->indtype.fam_idx != fam_idx) {
            type_error(t->loc, "constructor '%s' return type is not '%s'\n",
                    ctor->name, fam->name);
            return NULL;
        }
        return tele;
    }

    case TM_INDREC: {
        int fam_idx   = t->indrec.fam_idx;
        IndDef *fam   = ind_get(fam_idx);
        int n_params  = fam->n_params;
        int n_indices = fam->n_indices;
        int n_ctors   = fam->n_ctors;
        if (t->indrec.n_cases != n_ctors) {
            type_error(t->loc, "'indrec' for '%s': expected %d case(s), got %d\n",
                    fam->name, n_ctors, t->indrec.n_cases);
            return NULL;
        }
        /* Infer scrutinee type first to extract param vals and index vals */
        Val *scrut_ty = infer(a, depth, tctx, env, t->indrec.scrut);
        if (!scrut_ty) return NULL;
        if (scrut_ty->tag != VL_INDTYPE || scrut_ty->indtype.fam_idx != fam_idx) {
            type_error(t->loc, "'indrec' for '%s': scrutinee is not of this family\n",
                    fam->name);
            return NULL;
        }
        /* Extract param vals from scrutinee type */
        Val **param_vals = n_params > 0
            ? (Val **)arena_alloc(a, n_params * sizeof(Val *)) : NULL;
        for (int i = 0; i < n_params; i++)
            param_vals[i] = scrut_ty->indtype.args[i];
        Env *param_env = NULL;
        for (int i = 0; i < n_params; i++)
            param_env = env_cons(a, param_vals[i], param_env);
        /* Check motive type:
           Π(i1:I1). ... Π(iN:IN). IndType(fam, params, i1..iN) → Type_k */
        Val *P_ty = infer(a, depth, tctx, env, t->indrec.motive);
        if (!P_ty) return NULL;
        int d = depth;
        Env *idx_env = param_env;
        Val **idx_freshs = n_indices > 0
            ? (Val **)arena_alloc(a, n_indices * sizeof(Val *)) : NULL;
        for (int j = 0; j < n_indices; j++) {
            if (P_ty->tag != VL_PI) {
                type_error(t->loc, "'indrec' for '%s': motive missing index Π (index %d)\n",
                        fam->name, j);
                return NULL;
            }
            if (fam->index_types && fam->index_types[j]) {
                Val *exp_idx_ty = nbe_eval(a, idx_env, fam->index_types[j]);
                if (!conv(a, d, P_ty->pi.dom, exp_idx_ty)) {
                    type_error(t->loc, "'indrec' for '%s': motive index %d type mismatch\n",
                            fam->name, j);
                    return NULL;
                }
            }
            idx_freshs[j] = vl_neutral(a, d++, NULL);
            idx_env = env_cons(a, idx_freshs[j], idx_env);
            P_ty = nbe_eval(a, env_cons(a, idx_freshs[j], P_ty->pi.env), P_ty->pi.cod);
        }
        /* P_ty must now be Π(_ : IndType(fam, params, idx_freshs)). Type_k */
        if (P_ty->tag != VL_PI) {
            type_error(t->loc, "'indrec' for '%s': motive does not take a scrutinee\n",
                    fam->name);
            return NULL;
        }
        {
            int n_total = n_params + n_indices;
            Val **exp_args = n_total > 0
                ? (Val **)arena_alloc(a, n_total * sizeof(Val *)) : NULL;
            for (int i = 0; i < n_params;  i++) exp_args[i]          = param_vals[i];
            for (int j = 0; j < n_indices; j++) exp_args[n_params + j] = idx_freshs[j];
            Val *exp_scrut_ty = vl_indtype(a, fam_idx, n_total, exp_args);
            if (!conv(a, d, P_ty->pi.dom, exp_scrut_ty)) {
                type_error(t->loc, "'indrec' for '%s': motive scrutinee type mismatch\n",
                        fam->name);
                return NULL;
            }
        }
        {
            Val *scrut_fresh = vl_neutral(a, d, NULL);
            Val *P_cod = nbe_eval(a, env_cons(a, scrut_fresh, P_ty->pi.env), P_ty->pi.cod);
            int k;
            if (!as_universe(P_cod, &k)) {
                type_error(t->loc, "'indrec' for '%s': motive does not map into a universe\n",
                        fam->name);
                return NULL;
            }
        }
        Val *P_val = nbe_eval(a, env, t->indrec.motive);
        /* eval_cases[ci]: evaluated value of case ci, filled as point ctors are checked.
         * Path ctor cases need eval_cases for endpoint computation (rec lhs / rec rhs). */
        Val **eval_cases = (Val **)arena_alloc(a, n_ctors * sizeof(Val *));
        for (int ci2 = 0; ci2 < n_ctors; ci2++) eval_cases[ci2] = NULL;
        /* Check each case structurally against the constructor telescope.
         * Strategy: try `infer` first (works for annotated cases, atoms, globals).
         * If `infer` fails (e.g., bare lambda \k. \ih. body), fall back to
         * check_indrec_case_peel which strips lambdas and checks the body
         * against the motive applied to the synthesized constructor.
         * This fixes LIMIT-3: bare lambda cases no longer require annotation. */
        for (int ci = 0; ci < n_ctors; ci++) {
            CtorDef *ctor = &fam->ctors[ci];
            int arity = ctor->arity;
            Val *tele = NULL;
            if (ctor->telescope)
                tele = nbe_eval(a, param_env, ctor->telescope);
            /* Path ctor case: use dedicated PathP type checker */
            if (ctor->is_path_ctor) {
                if (!check_indrec_path_case(a, depth, tctx, env,
                                             t->indrec.cases[ci], tele,
                                             fam_idx, ci, fam,
                                             n_params, param_vals, P_val, eval_cases))
                    return NULL;
                /* Store the evaluated path case so later 2-cell cases can use it
                 * as rec(p) or rec(q) via hit_compute_rec.                        */
                eval_cases[ci] = nbe_eval(a, env, t->indrec.cases[ci]);
                continue;
            }
            Val *case_ty = infer(a, depth, tctx, env, t->indrec.cases[ci]);
            if (!case_ty) {
                /* infer failed — try lambda peeling for bare lambda cases */
                if (!check_indrec_case_peel(a, depth, tctx, env,
                                              t->indrec.cases[ci], tele,
                                              fam_idx, ci, fam,
                                              n_params, param_vals, P_val)) {
                    /* error already printed by check_indrec_case_peel */
                    return NULL;
                }
                /* Store evaluated case for path ctor endpoint computation */
                eval_cases[ci] = nbe_eval(a, env, t->indrec.cases[ci]);
                continue;  /* case OK via peeling; proceed to next case */
            }
            int dc = depth;
            Val **arg_vs = arity > 0
                ? (Val **)arena_alloc(a, arity * sizeof(Val *)) : NULL;
            for (int i = 0; i < arity; i++) {
                if (!tele || tele->tag != VL_PI) {
                    type_error(t->loc, "'indrec' for '%s': case %d ('%s') telescope too short\n",
                            fam->name, ci, ctor->name);
                    return NULL;
                }
                if (case_ty->tag != VL_PI) {
                    type_error(t->loc, "'indrec' for '%s': case %d ('%s') missing arg %d\n",
                            fam->name, ci, ctor->name, i);
                    return NULL;
                }
                Val *tele_dom = tele->pi.dom;
                if (!conv(a, dc, case_ty->pi.dom, tele_dom)) {
                    type_error(t->loc, "'indrec' for '%s': case %d ('%s') arg %d type mismatch\n",
                            fam->name, ci, ctor->name, i);
                    return NULL;
                }
                Val *fresh = vl_neutral(a, dc++, NULL);
                arg_vs[i] = fresh;
                tele     = nbe_eval(a, env_cons(a, fresh, tele->pi.env),    tele->pi.cod);
                case_ty  = nbe_eval(a, env_cons(a, fresh, case_ty->pi.env), case_ty->pi.cod);
                /* Recursive position: case must also take an IH */
                if (ind_is_recursive_pos(fam_idx, ci, i)) {
                    if (case_ty->tag != VL_PI) {
                        type_error(t->loc, "'indrec' for '%s': case %d ('%s') missing IH for arg %d\n",
                                fam->name, ci, ctor->name, i);
                        return NULL;
                    }
                    /* IH type: P idx... fresh  where fresh : tele_dom = VL_INDTYPE(fam,...) */
                    Val *IH_ty = P_val;
                    if (tele_dom->tag == VL_INDTYPE)
                        for (int j = n_params; j < tele_dom->indtype.n_args; j++)
                            IH_ty = nbe_vapp(a, IH_ty, tele_dom->indtype.args[j]);
                    IH_ty = nbe_vapp(a, IH_ty, fresh);
                    if (!conv(a, dc, case_ty->pi.dom, IH_ty)) {
                        type_error(t->loc, "'indrec' for '%s': case %d ('%s') IH type mismatch for arg %d\n",
                                fam->name, ci, ctor->name, i);
                        return NULL;
                    }
                    Val *ih_fresh = vl_neutral(a, dc++, NULL);
                    case_ty = nbe_eval(a, env_cons(a, ih_fresh, case_ty->pi.env), case_ty->pi.cod);
                }
            }
            /* Nullary indexed ctor without telescope: cannot determine return indices */
            if (!tele && arity == 0 && n_indices > 0) {
                type_error(t->loc, "'indrec' for '%s': case %d ('%s') is a nullary constructor"
                        " without a telescope — cannot determine return indices\n",
                        fam->name, ci, ctor->name);
                return NULL;
            }
            /* Expected result: P ret_idxs... synth_con */
            int n_total_con = n_params + arity;
            Val **synth_args = n_total_con > 0
                ? (Val **)arena_alloc(a, n_total_con * sizeof(Val *)) : NULL;
            for (int i = 0; i < n_params; i++) synth_args[i]          = param_vals[i];
            for (int i = 0; i < arity;    i++) synth_args[n_params + i] = arg_vs[i];
            Val *synth_con = vl_indcon(a, fam_idx, ci, n_total_con, synth_args);
            Val *exp_result = P_val;
            /* Apply P to return indices from tele (the remaining VL_INDTYPE after walking) */
            if (tele && tele->tag == VL_INDTYPE)
                for (int j = n_params; j < tele->indtype.n_args; j++)
                    exp_result = nbe_vapp(a, exp_result, tele->indtype.args[j]);
            exp_result = nbe_vapp(a, exp_result, synth_con);
            if (!conv(a, dc, case_ty, exp_result)) {
                type_error(t->loc, "'indrec' for '%s': case %d ('%s') result type mismatch\n",
                        fam->name, ci, ctor->name);
                return NULL;
            }
            /* Store evaluated case for path ctor endpoint computation */
            eval_cases[ci] = nbe_eval(a, env, t->indrec.cases[ci]);
        }
        /* Return type: P scrut_idxs... scrut_val */
        Val *ret = P_val;
        for (int j = n_params; j < scrut_ty->indtype.n_args; j++)
            ret = nbe_vapp(a, ret, scrut_ty->indtype.args[j]);
        ret = nbe_vapp(a, ret, nbe_eval(a, env, t->indrec.scrut));
        return ret;
    }

    case TM_FIX: {
        /* Infer mode: infer body type and return its domain as the result type.
         * Annotation is recommended: (fix body : T) for non-trivial cases. */
        Val *body_ty = infer(a, depth, tctx, env, t->fix.body);
        if (!body_ty) return NULL;
        if (body_ty->tag != VL_PI) {
            type_error(t->loc, "'fix': body must have function type\n");
            return NULL;
        }
        return body_ty->pi.dom;
    }

    /* Phase M1 — level terms */
    case TM_LEVEL:
        return vl_uni(a, 0);  /* Level : Type_0 */
    case TM_LZERO:
        return vl_level(a);   /* lzero : Level */
    case TM_LSUC:
        if (!check(a, depth, tctx, env, t->elim, vl_level(a))) return NULL;
        return vl_level(a);   /* lsuc ℓ : Level */
    case TM_LMAX:
        if (!check(a, depth, tctx, env, t->app.fun, vl_level(a))) return NULL;
        if (!check(a, depth, tctx, env, t->app.arg, vl_level(a))) return NULL;
        return vl_level(a);   /* lmax l r : Level */
    case TM_UNI_V: {
        /* Type_ℓ : Type_(lsuc ℓ) — collapse to VL_UNI(n) if ℓ is concrete */
        if (!check(a, depth, tctx, env, t->uni_v_lvl, vl_level(a))) return NULL;
        Val *lv = nbe_eval(a, env, t->uni_v_lvl);
        Val *succ_lv = vl_lsuc(a, lv);
        int n = 0; Val *cur = succ_lv;
        while (cur->tag == VL_LSUC) { n++; cur = cur->succ; }
        if (cur->tag == VL_LZERO) return vl_uni(a, n);
        return vl_uni_v(a, succ_lv);
    }

    case TM_HOLE:
        fprintf(stderr, "infer: TM_HOLE reached — term not elaborated; "
                        "use (expr : type) annotation or elab_infer\n");
        return NULL;

    /* Phase L2 — cubical interval */
    case TM_INTERVAL:
        return vl_uni(a, 0);   /* II : Type_0 */

    case TM_IZERO:
    case TM_IONE:
        return vl_neutral(a, INTERVAL_CONST_LVL, NULL);  /* i0, i1 : II */

    case TM_PATH: {
        /* Path A a b : Type_i  when  A : Type_i,  a b : A */
        Val *Aty = infer(a, depth, tctx, env, t->id.ty);
        if (!Aty) return NULL;
        int i;
        if (!as_universe(Aty, &i)) {
            type_error(t->loc, "Path: first argument not a type\n");
            return NULL;
        }
        Val *A_val = nbe_eval(a, env, t->id.ty);
        if (!check(a, depth, tctx, env, t->id.lhs, A_val)) return NULL;
        if (!check(a, depth, tctx, env, t->id.rhs, A_val)) return NULL;
        return Aty;  /* Path A a b lives in same universe as A */
    }

    case TM_PATHP: {
        /* PathP fam a b : Type_k
         *   fam : Π(_:II). Type_k
         *   a   : fam i0
         *   b   : fam i1                                    */
        Val *ii_ty  = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        Val *fam_ty = infer(a, depth, tctx, env, t->id.ty);
        if (!fam_ty) return NULL;
        if (fam_ty->tag != VL_PI) {
            type_error(t->loc, "PathP: family must be Π(_:II). Type_k\n");
            return NULL;
        }
        if (!conv(a, depth, fam_ty->pi.dom, ii_ty)) {
            type_error(t->loc, "PathP: family domain must be II\n");
            return NULL;
        }
        Val *cod_probe = nbe_eval(a, env_cons(a, vl_neutral(a, depth, NULL), fam_ty->pi.env),
                                  fam_ty->pi.cod);
        int k;
        if (!as_universe(cod_probe, &k)) {
            type_error(t->loc, "PathP: family codomain must be a universe\n");
            return NULL;
        }
        Val *fam_val = nbe_eval(a, env, t->id.ty);
        Val *i0v     = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *i1v     = vl_neutral(a, IONE_CONST_LVL,  NULL);
        Val *A_0     = nbe_vapp(a, fam_val, i0v);
        Val *A_1     = nbe_vapp(a, fam_val, i1v);
        if (!check(a, depth, tctx, env, t->id.lhs, A_0)) return NULL;
        if (!check(a, depth, tctx, env, t->id.rhs, A_1)) return NULL;
        return vl_uni(a, k);
    }

    case TM_PATHABS: {
        /* ⟨i⟩ body infer:
         *   - If body's type is CONSTANT in i → Path A t0 t1  (original)
         *   - If body's type VARIES with i   → PathP (λi. body_ty) t0 t1  (auto)
         * Detection: quote body_ty at depth+1; term_mentions_var(bty_term, 0)
         * checks whether the fresh i (= VAR(0) in the inner context) appears. */
        Val *i_ty    = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        Val *i_val   = vl_neutral(a, depth, NULL);
        TCtx inner_tctx = { t->lam.name, i_ty, tctx };
        Env *inner_env  = env_cons(a, i_val, env);
        Val *body_ty    = infer(a, depth + 1, &inner_tctx, inner_env, t->lam.body);
        if (!body_ty) return NULL;
        Val *i0v = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *i1v = vl_neutral(a, IONE_CONST_LVL,  NULL);
        Val *t0  = nbe_eval(a, env_cons(a, i0v, env), t->lam.body);
        Val *t1  = nbe_eval(a, env_cons(a, i1v, env), t->lam.body);
        Term *bty_term = nbe_quote(a, depth + 1, body_ty);
        if (term_mentions_var(bty_term, 0)) {
            /* Varying type → PathP (λi. body_ty) t0 t1 */
            Val *fam_lam = vl_lam(a, t->lam.name, env, bty_term);
            return vl_pathp(a, fam_lam, t0, t1);
        }
        /* Constant type → Path A t0 t1 */
        Val *A = nbe_eval(a, env_cons(a, i0v, env), bty_term);
        return vl_path(a, A, t0, t1);
    }

    case TM_PATHAPP: {
        /* p @ r : A  where p : Path A a b,  or p : PathP fam a b → fam r */
        Val *p_ty = infer(a, depth, tctx, env, t->app.fun);
        if (!p_ty) return NULL;
        Val *ii_ty = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        if (p_ty->tag == VL_PATH) {
            if (!check(a, depth, tctx, env, t->app.arg, ii_ty)) return NULL;
            return p_ty->id.ty;  /* A */
        }
        if (p_ty->tag == VL_PATHP) {
            /* PathP fam a b: result type = fam r */
            if (!check(a, depth, tctx, env, t->app.arg, ii_ty)) return NULL;
            Val *r_val = nbe_eval(a, env, t->app.arg);
            return nbe_vapp(a, p_ty->id.ty, r_val);  /* fam r */
        }
        if (p_ty->tag == VL_PI) {
            /* Plain function Π(i:II).T — also accepted for backwards compat */
            if (!check(a, depth, tctx, env, t->app.arg, ii_ty)) return NULL;
            Val *r_val = nbe_eval(a, env, t->app.arg);
            return nbe_eval(a, env_cons(a, r_val, p_ty->pi.env), p_ty->pi.cod);
        }
        type_error(t->loc, "path application: expected Path, PathP, or Π(_:II).T\n");
        return NULL;
    }

    case TM_HCOMP: {
        /* hcomp A φ u base : A
         * A : Type_k   φ : II   u : II → A   base : A
         *
         * We check the tube bidirectionally against Π(_:II).A.
         * The Pi type is built so its codomain always evaluates to A_val:
         *   vl_pi("_", ii_ty, [A_val], VAR 1)
         * When applied to i: eval([i, A_val], VAR 1) = A_val. ✓
         */
        Val *ii_ty = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        Val *A_ty  = infer(a, depth, tctx, env, t->hcomp_t.ty);
        if (!A_ty) return NULL;
        int k;
        if (!as_universe(A_ty, &k)) {
            type_error(t->loc, "hcomp: A must be a Type\n");
            return NULL;
        }
        if (!check(a, depth, tctx, env, t->hcomp_t.face, ii_ty)) return NULL;
        Val *A_val = nbe_eval(a, env, t->hcomp_t.ty);
        /* Constant Pi type: Π(_:II). A_val */
        Val *tube_ty = vl_pi(a, "_", ii_ty, env_cons(a, A_val, NULL), tm_var(a, 1));
        if (!check(a, depth, tctx, env, t->hcomp_t.tube, tube_ty)) {
            type_error(t->loc, "hcomp: tube must have type II → A\n");
            return NULL;
        }
        if (!check(a, depth, tctx, env, t->hcomp_t.base, A_val)) return NULL;
        return A_val;
    }

    case TM_COMP: {
        /* comp fam φ u base : fam i1
         *   fam : Π(_:II). Type_k
         *   φ   : II
         *   u   : Π(_:II). fam_? (relaxed: checked against A at a fresh II neutral)
         *   base : fam i0                                                          */
        Val *ii_ty = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        Val *fam_ty = infer(a, depth, tctx, env, t->hcomp_t.ty);
        if (!fam_ty) return NULL;
        if (fam_ty->tag != VL_PI) {
            type_error(t->loc, "comp: family must be a Π type\n");
            return NULL;
        }
        if (!conv(a, depth, fam_ty->pi.dom, ii_ty)) {
            type_error(t->loc, "comp: family domain must be II\n");
            return NULL;
        }
        if (!check(a, depth, tctx, env, t->hcomp_t.face, ii_ty)) return NULL;
        Val *fam_val = nbe_eval(a, env, t->hcomp_t.ty);
        Val *i0v     = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *i1v     = vl_neutral(a, IONE_CONST_LVL,  NULL);
        Val *A_0     = nbe_vapp(a, fam_val, i0v);
        Val *A_1     = nbe_vapp(a, fam_val, i1v);
        /* Tube type: Π(_:II). A_mid (relaxed — uses type at a fresh neutral) */
        Val *A_mid   = nbe_vapp(a, fam_val, vl_neutral(a, depth, NULL));
        Val *tube_ty = vl_pi(a, "_", ii_ty, env_cons(a, A_mid, NULL), tm_var(a, 1));
        if (!check(a, depth, tctx, env, t->hcomp_t.tube, tube_ty)) {
            type_error(t->loc, "comp: tube must have type Π(_:II). A\n");
            return NULL;
        }
        if (!check(a, depth, tctx, env, t->hcomp_t.base, A_0)) return NULL;
        return A_1;
    }

    case TM_FILL: {
        /* fill fam φ u base i : fam i
         *   fam  : Π(_:II). Type_k
         *   φ    : II
         *   u    : Π(_:II). fam mid    (relaxed tube type)
         *   base : fam i0
         *   i    : II
         *   result : fam i                                      */
        Val *ii_ty  = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        Val *fam_ty = infer(a, depth, tctx, env, t->fill_t.fam);
        if (!fam_ty) return NULL;
        if (fam_ty->tag != VL_PI) {
            type_error(t->loc, "fill: family must be a Π type\n");
            return NULL;
        }
        if (!conv(a, depth, fam_ty->pi.dom, ii_ty)) {
            type_error(t->loc, "fill: family domain must be II\n");
            return NULL;
        }
        if (!check(a, depth, tctx, env, t->fill_t.face, ii_ty)) return NULL;
        Val *fam_val = nbe_eval(a, env, t->fill_t.fam);
        Val *i0v     = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *A_0     = nbe_vapp(a, fam_val, i0v);
        Val *A_mid   = nbe_vapp(a, fam_val, vl_neutral(a, depth, NULL));
        Val *tube_ty = vl_pi(a, "_", ii_ty, env_cons(a, A_mid, NULL), tm_var(a, 1));
        if (!check(a, depth, tctx, env, t->fill_t.tube, tube_ty)) {
            type_error(t->loc, "fill: tube must have type Π(_:II). A\n");
            return NULL;
        }
        if (!check(a, depth, tctx, env, t->fill_t.base, A_0)) return NULL;
        if (!check(a, depth, tctx, env, t->fill_t.idx,  ii_ty)) return NULL;
        Val *idx_val = nbe_eval(a, env, t->fill_t.idx);
        return nbe_vapp(a, fam_val, idx_val);
    }

    case TM_IMIN:
    case TM_IMAX: {
        /* imin/imax : II → II → II */
        Val *ii_ty = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        if (!check(a, depth, tctx, env, t->app.fun, ii_ty)) return NULL;
        if (!check(a, depth, tctx, env, t->app.arg, ii_ty)) return NULL;
        return ii_ty;
    }
    case TM_INEG: {
        /* ineg : II → II */
        Val *ii_ty = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        if (!check(a, depth, tctx, env, t->elim, ii_ty)) return NULL;
        return ii_ty;
    }

    case TM_ISONE: {
        /* IsOne : II → Type₀ */
        Val *ii_ty = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        if (!check(a, depth, tctx, env, t->elim, ii_ty)) {
            type_error(t->loc, "IsOne: argument must be of type II\n");
            return NULL;
        }
        return vl_uni(a, 0);
    }

    case TM_GLUE: {
        /* Glue A φ T e : Type_k
         * A : Type_k,  φ : II,  T : Type_j,
         * e : Equiv T A = Σ(fwd:T→A). Σ(inv:A→T). Σ(sect). retr
         * Returns Type at level max(k, j). */
        Val *ii_ty = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        Val *A_ty  = infer(a, depth, tctx, env, t->glue_t.base);
        if (!A_ty) return NULL;
        int kA;
        if (!as_universe(A_ty, &kA)) {
            type_error(t->loc, "Glue: base A must be a Type\n");
            return NULL;
        }
        if (!check(a, depth, tctx, env, t->glue_t.face, ii_ty)) {
            type_error(t->loc, "Glue: face φ must have type II\n");
            return NULL;
        }
        Val *T_ty  = infer(a, depth, tctx, env, t->glue_t.fiber);
        if (!T_ty) return NULL;
        int kT;
        if (!as_universe(T_ty, &kT)) {
            type_error(t->loc, "Glue: fiber T must be a Type\n");
            return NULL;
        }
        Val *A_val = nbe_eval(a, env, t->glue_t.base);
        Val *T_val = nbe_eval(a, env, t->glue_t.fiber);
        /* equiv_ty = Equiv T A = Σ(fwd:T→A).Σ(inv:A→T).Σ(sect:...).retr */
        Val *equiv_ty = make_equiv_type(a, T_val, A_val);
        if (!check(a, depth, tctx, env, t->glue_t.equiv, equiv_ty)) {
            type_error(t->loc, "Glue: equivalence e must have type Equiv T A\n");
            return NULL;
        }
        int k = kA > kT ? kA : kT;
        return vl_uni(a, k);
    }

    case TM_TRANSP: {
        /* transp A x : A i1
         * A : Π(i : II). Type_k   x : A i0 */
        Val *A_ty = infer(a, depth, tctx, env, t->app.fun);
        if (!A_ty) return NULL;
        if (A_ty->tag != VL_PI) {
            type_error(t->loc, "transp: family must be Π(i:II).Type, got non-Pi\n");
            return NULL;
        }
        Val *ii_val = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        if (!conv(a, depth, A_ty->pi.dom, ii_val)) {
            type_error(t->loc, "transp: family domain must be II\n");
            return NULL;
        }
        Val *fresh_i = vl_neutral(a, depth, NULL);
        Val *cod_ty  = nbe_eval(a, env_cons(a, fresh_i, A_ty->pi.env), A_ty->pi.cod);
        int k;
        if (!as_universe(cod_ty, &k)) {
            type_error(t->loc, "transp: family codomain must be a universe\n");
            return NULL;
        }
        Val *A_val = nbe_eval(a, env, t->app.fun);
        Val *i0v   = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *A_i0  = nbe_vapp(a, A_val, i0v);
        if (!check(a, depth, tctx, env, t->app.arg, A_i0)) return NULL;
        Val *i1v   = vl_neutral(a, IONE_CONST_LVL, NULL);
        return nbe_vapp(a, A_val, i1v);
    }

    /* Phase L2 Stage 7d — unglue elim (infer mode)
     *
     * unglue φ e x : A
     *   Neutral φ: x must have inferred type VL_GLUE; extract A from that.
     *   Concrete φ=i0: x : A (Glue A i0 T e = A); extract A/T from e's type.
     *   Concrete φ=i1: x : T (Glue A i1 T e = T); extract A/T from e's type.
     *
     * A/T extraction from e : Equiv T A = Σ(fwd:T→A)...:
     *   fwd_ty = e_ty->pi.dom = VL_PI(T → A);  T = fwd_ty->pi.dom;
     *   A = fwd_ty->pi.cod eval'd at a fresh var (non-dependent Pi).
     */
    case TM_UNGLUE: {
        Val *ii_ty = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        if (!check(a, depth, tctx, env, t->unglue_t.face, ii_ty)) {
            type_error(t->loc, "unglue: face must have type II\n");
            return NULL;
        }
        Val *phi_v = nbe_eval(a, env, t->unglue_t.face);
        Val *x_ty  = infer(a, depth, tctx, env, t->unglue_t.elem);
        if (!x_ty) return NULL;

        /* ── Neutral face: x must have VL_GLUE type (existing logic) */
        if (x_ty->tag == VL_GLUE) {
            if (!conv(a, depth, phi_v, x_ty->glue_s.face)) {
                type_error(t->loc, "unglue: face does not match Glue type face\n");
                return NULL;
            }
            Val *A_val = x_ty->glue_s.base;
            Val *e_ty  = x_ty->glue_s.equiv;
            Val *e_v   = nbe_eval(a, env, t->unglue_t.equiv);
            if (!conv(a, depth, e_v, e_ty)) {
                type_error(t->loc, "unglue: equivalence does not match Glue type\n");
                return NULL;
            }
            return A_val;
        }

        /* ── Concrete face (i0 or i1): extract A/T from e : Equiv T A */
        int phi_i0 = (phi_v->tag == VL_NEUTRAL && phi_v->neutral.lvl == IZERO_CONST_LVL);
        int phi_i1 = (phi_v->tag == VL_NEUTRAL && phi_v->neutral.lvl == IONE_CONST_LVL);
        if (!phi_i0 && !phi_i1) {
            type_error(t->loc, "unglue: element must have Glue type"
                    " (for non-i0/i1 faces, x must be explicitly typed as Glue)\n");
            return NULL;
        }
        /* Infer e's type; it should be Σ(fwd:T→A)... */
        Val *e_full_ty = infer(a, depth, tctx, env, t->unglue_t.equiv);
        if (!e_full_ty || e_full_ty->tag != VL_SIGMA) {
            type_error(t->loc, "unglue: equiv must have Equiv (Σ) type\n");
            return NULL;
        }
        Val *fwd_ty = e_full_ty->pi.dom;  /* T → A */
        if (!fwd_ty || fwd_ty->tag != VL_PI) {
            type_error(t->loc, "unglue: equiv first component must be T→A\n");
            return NULL;
        }
        Val *T_val  = fwd_ty->pi.dom;
        Val *fresh  = vl_neutral(a, depth, NULL);
        Val *A_val  = nbe_eval(a, env_cons(a, fresh, fwd_ty->pi.env), fwd_ty->pi.cod);

        if (phi_i0) {
            /* unglue i0 e x = x; x : A */
            if (!conv(a, depth, x_ty, A_val)) {
                type_error(t->loc, "unglue i0: element type does not match A\n");
                return NULL;
            }
        } else {
            /* unglue i1 e x = fst(e)(x); x : T */
            if (!conv(a, depth, x_ty, T_val)) {
                type_error(t->loc, "unglue i1: element type does not match T\n");
                return NULL;
            }
        }
        return A_val;
    }

    case TM_PRIMSUB: {
        /* primSub A φ u a : A
         *   A : Type_k    φ : II
         *   u : IsOne φ → A   a : A   */
        Val *ii_ty  = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        Val *A_ty   = infer(a, depth, tctx, env, t->primsub_t.ty);
        if (!A_ty) return NULL;
        int k;
        if (!as_universe(A_ty, &k)) {
            type_error(t->loc, "primSub: A must be a Type\n");
            return NULL;
        }
        if (!check(a, depth, tctx, env, t->primsub_t.face, ii_ty)) return NULL;
        Val *A_val  = nbe_eval(a, env, t->primsub_t.ty);
        Val *phi_v  = nbe_eval(a, env, t->primsub_t.face);
        Val *iso    = nbe_visone(a, phi_v);
        Val *u_ty   = vl_pi(a, "_", iso, env_cons(a, A_val, NULL), tm_var(a, 1));
        if (!check(a, depth, tctx, env, t->primsub_t.u, u_ty)) return NULL;
        if (!check(a, depth, tctx, env, t->primsub_t.a, A_val)) return NULL;
        return A_val;
    }

    /* Phase M4 — pattern matching */
    case TM_MATCH: {
        Val *scrut_ty = infer(a, depth, tctx, env, t->match_s.scrut);
        if (!scrut_ty) return NULL;
        int fam_idx = t->match_s.fam_idx;
        int n_arms  = t->match_s.n_arms;
        MatchArm *arms = t->match_s.arms;
        /* verify scrutinee type and coverage count */
        int n_ctors;
        if (fam_idx == -1) {
            if (scrut_ty->tag != VL_NAT) {
                type_error(t->loc, "match: scrutinee must be Nat\n"); return NULL;
            }
            n_ctors = 2;
        } else if (fam_idx == -2) {
            if (scrut_ty->tag != VL_BOOL) {
                type_error(t->loc, "match: scrutinee must be Bool\n"); return NULL;
            }
            n_ctors = 2;
        } else {
            IndDef *fam = ind_get(fam_idx);
            if (scrut_ty->tag != VL_INDTYPE || scrut_ty->indtype.fam_idx != fam_idx) {
                type_error(t->loc, "match: scrutinee must be of type '%s'\n", fam->name);
                return NULL;
            }
            n_ctors = fam->n_ctors;
        }
        if (n_arms != n_ctors) {
            type_error(t->loc, "match: expected %d arm(s), got %d\n", n_ctors, n_arms);
            return NULL;
        }
        /* Infer return type from first arm; check all remaining arms against it */
        Val *ret_ty = NULL;
        unsigned int seen_ctors = 0;
        for (int i = 0; i < n_arms; i++) {
            MatchArm *arm = &arms[i];
            /* Validate: no duplicate constructor arms */
            if (arm->ctor_idx < (int)(sizeof(seen_ctors)*8)) {
                if (seen_ctors & (1u << arm->ctor_idx)) {
                    type_error(t->loc, "match: duplicate arm for constructor %d\n",
                            arm->ctor_idx);
                    return NULL;
                }
                seen_ctors |= (1u << arm->ctor_idx);
            }
            /* Validate binder count against built-in constructor arity */
            if (fam_idx == -1) {
                int max_binds = (arm->ctor_idx == 1) ? 1 : 0;
                if (arm->n_binds > max_binds) {
                    type_error(t->loc, "match: arm '%s' has %d binder(s), at most %d expected\n",
                            arm->ctor_idx == 0 ? "zero" : "succ", arm->n_binds, max_binds);
                    return NULL;
                }
            } else if (fam_idx == -2) {
                if (arm->n_binds > 0) {
                    type_error(t->loc, "match: Bool arm '%s' takes no binders\n",
                            arm->ctor_idx == 0 ? "true" : "false");
                    return NULL;
                }
            }
            /* Validate IH: currently only supported for Nat succ */
            if (arm->ih_name) {
                if (!(fam_idx == -1 && arm->ctor_idx == 1)) {
                    type_error(t->loc, "match: IH binder only supported for Nat succ arm\n");
                    return NULL;
                }
                if (!ret_ty) {
                    type_error(t->loc,
                        "match: cannot infer IH type — write zero arm first or add a type annotation\n");
                    return NULL;
                }
            }
            TCtx *arm_tctx = tctx;
            Env  *arm_env  = env;
            int   arm_depth = depth;
            TCtx  tctx_exts[MATCH_MAX_BINDS + 1];
            if (fam_idx == -1 && arm->ctor_idx == 1 && arm->n_binds > 0) {
                tctx_exts[0].name = arm->names[0];
                tctx_exts[0].type = vl_nat(a);
                tctx_exts[0].next = arm_tctx;
                arm_tctx = &tctx_exts[0];
                arm_env = env_cons(a, vl_neutral(a, arm_depth++, NULL), arm_env);
            } else if (fam_idx >= 0 && arm->n_binds > 0) {
                IndDef *fam = ind_get(fam_idx);
                CtorDef *ctor = &fam->ctors[arm->ctor_idx];
                int n_params = fam->n_params;
                Env *param_env = NULL;
                for (int pi = 0; pi < n_params; pi++)
                    param_env = env_cons(a, scrut_ty->indtype.args[pi], param_env);
                Val *tele = ctor->telescope ? nbe_eval(a, param_env, ctor->telescope) : NULL;
                TCtx *cur_tctx = arm_tctx;
                for (int j = 0; j < arm->n_binds; j++) {
                    if (!tele || tele->tag != VL_PI) {
                        type_error(t->loc, "match: arm '%s': telescope too short at field %d\n",
                                ctor->name, j);
                        return NULL;
                    }
                    tctx_exts[j].name = arm->names[j];
                    tctx_exts[j].type = tele->pi.dom;
                    tctx_exts[j].next = cur_tctx;
                    cur_tctx = &tctx_exts[j];
                    Val *fresh = vl_neutral(a, arm_depth++, NULL);
                    arm_env = env_cons(a, fresh, arm_env);
                    tele = nbe_eval(a, env_cons(a, fresh, tele->pi.env), tele->pi.cod);
                }
                arm_tctx = cur_tctx;
            }
            /* IH binder: innermost, type = ret_ty (already validated above) */
            if (arm->ih_name && ret_ty) {
                int ih_idx = arm->n_binds;
                tctx_exts[ih_idx].name = arm->ih_name;
                tctx_exts[ih_idx].type = ret_ty;
                tctx_exts[ih_idx].next = arm_tctx;
                arm_tctx = &tctx_exts[ih_idx];
                arm_env = env_cons(a, vl_neutral(a, arm_depth++, NULL), arm_env);
            }
            if (i == 0) {
                ret_ty = infer(a, arm_depth, arm_tctx, arm_env, arm->body);
                if (!ret_ty) return NULL;
            } else {
                if (!check(a, arm_depth, arm_tctx, arm_env, arm->body, ret_ty)) return NULL;
            }
        }
        return ret_ty;
    }

    default:
        fprintf(stderr, "infer: unhandled term tag %d\n", t->tag);
        exit(1);
    }
}

/* ── Glue η helpers ─────────────────────────────────────────────────────── */

/* η-expand a Glue element to VL_GLUEELEM form.
 * x : Glue A φ T e  →  glue φ [φ ↦ λ_. e.inv(unglue φ e x)] (unglue φ e x)
 * VL_GLUEELEM values are returned unchanged; this is a no-op for concrete φ
 * too (nbe_vglueelem fires at i0/i1 immediately). */
static Val *glue_eta_expand(Arena *a, Val *x, Val *glue_ty) {
    if (x->tag == VL_GLUEELEM) return x;
    Val *phi = glue_ty->glue_s.face;
    Val *e   = glue_ty->glue_s.equiv;
    /* Guard: nbe_vfst/nbe_vsnd only handle VL_PAIR and VL_NEUTRAL safely.
       Any other tag (VL_LAM, VL_FIX, etc.) crashes nbe_vsnd — same guard as
       in eval.c for transp-Glue and hcomp-Glue. */
    if (e->tag != VL_PAIR && e->tag != VL_NEUTRAL) return x;
    Val *base  = nbe_vunglue(a, phi, e, x);
    Val *e_inv = nbe_vfst(a, nbe_vsnd(a, e));
    Val *fiber = nbe_vapp(a, e_inv, base);
    /* Constant partial element λ_. fiber.
       env=[fiber], body=VAR(1): in env [arg(0), fiber(1)], VAR(1) = fiber. */
    Val *partial = vl_lam(a, "_", env_cons(a, fiber, NULL), tm_var(a, 1));
    return nbe_vglueelem(a, phi, partial, base);
}

/* Typed conv: delegates to conv but applies Glue η-expansion when the shared
 * type is VL_GLUE.  Call this instead of conv whenever the type of u and v
 * is known at the call site. */
static int conv_at(Arena *a, int depth, Val *u, Val *v, Val *ty) {
    if (ty && ty->tag == VL_GLUE) {
        u = glue_eta_expand(a, u, ty);
        v = glue_eta_expand(a, v, ty);
    }
    return conv(a, depth, u, v);
}

/* ── Check */

int check(Arena *a, int depth, TCtx *tctx, Env *env, Term *t, Val *ty) {
    /* PathP abstraction: ⟨i⟩ body : PathP fam a b
     * Check body : fam i with i : II in scope, then verify endpoints. */
    if (t->tag == TM_PATHABS && ty->tag == VL_PATHP) {
        Val *fam_val  = ty->id.ty;
        Val *path_lhs = ty->id.lhs;
        Val *path_rhs = ty->id.rhs;
        Val *i_ty  = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        Val *i_val = vl_neutral(a, depth, NULL);
        TCtx inner_tctx = { t->lam.name, i_ty, tctx };
        Env *inner_env  = env_cons(a, i_val, env);
        Val *body_ty    = nbe_vapp(a, fam_val, i_val);  /* fam i */
        if (!check(a, depth + 1, &inner_tctx, inner_env, t->lam.body, body_ty)) return 0;
        Val *i0v = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *i1v = vl_neutral(a, IONE_CONST_LVL,  NULL);
        Val *t0  = nbe_eval(a, env_cons(a, i0v, env), t->lam.body);
        Val *t1  = nbe_eval(a, env_cons(a, i1v, env), t->lam.body);
        Val *ty0 = nbe_vapp(a, fam_val, i0v);
        Val *ty1 = nbe_vapp(a, fam_val, i1v);
        if (!conv_at(a, depth, t0, path_lhs, ty0)) {
            type_error(t->loc, "PathP left endpoint mismatch\n");
            return 0;
        }
        if (!conv_at(a, depth, t1, path_rhs, ty1)) {
            type_error(t->loc, "PathP right endpoint mismatch\n");
            return 0;
        }
        return 1;
    }
    /* Path abstraction checks against Path type: intro rule for paths */
    if (t->tag == TM_PATHABS && ty->tag == VL_PATH) {
        Val *path_A   = ty->id.ty;
        Val *path_lhs = ty->id.lhs;
        Val *path_rhs = ty->id.rhs;
        /* Check body : A with i : II in scope */
        Val *i_ty  = vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        Val *i_val = vl_neutral(a, depth, NULL);
        TCtx inner_tctx = { t->lam.name, i_ty, tctx };
        Env *inner_env  = env_cons(a, i_val, env);
        if (!check(a, depth + 1, &inner_tctx, inner_env, t->lam.body, path_A)) return 0;
        /* Verify left endpoint: body[i0/i] ≡ path_lhs */
        Val *i0v = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *t0  = nbe_eval(a, env_cons(a, i0v, env), t->lam.body);
        if (!conv_at(a, depth, t0, path_lhs, path_A)) {
            type_error(t->loc, "path left endpoint mismatch\n");
            return 0;
        }
        /* Verify right endpoint: body[i1/i] ≡ path_rhs */
        Val *i1v = vl_neutral(a, IONE_CONST_LVL, NULL);
        Val *t1  = nbe_eval(a, env_cons(a, i1v, env), t->lam.body);
        if (!conv_at(a, depth, t1, path_rhs, path_A)) {
            type_error(t->loc, "path right endpoint mismatch\n");
            return 0;
        }
        return 1;
    }
    /* rfl / refl checks against Id type */
    if (t->tag == TM_REFL && ty->tag == VL_ID) {
        if (t->refl->tag == TM_HOLE) {
            if (!conv(a, depth, ty->id.lhs, ty->id.rhs)) {
                type_error(t->loc, "rfl: Id endpoints not definitionally equal\n");
                return 0;
            }
            /* Fill hole so nbe_eval(t) works if caller needs the value */
            t->refl = nbe_quote(a, depth, ty->id.lhs);
            return 1;
        }
        if (!check(a, depth, tctx, env, t->refl, ty->id.ty)) return 0;
        Val *av = nbe_eval(a, env, t->refl);
        if (!conv_at(a, depth, av, ty->id.lhs, ty->id.ty)) {
            type_error(t->loc, "refl: element does not match Id left endpoint\n");
            return 0;
        }
        if (!conv_at(a, depth, av, ty->id.rhs, ty->id.ty)) {
            type_error(t->loc, "refl: element does not match Id right endpoint\n");
            return 0;
        }
        return 1;
    }
    /* refl checks against PathP type: both endpoints must be in fam i0 ≡ fam i1 */
    if (t->tag == TM_REFL && ty->tag == VL_PATHP) {
        Val *i0v     = vl_neutral(a, IZERO_CONST_LVL, NULL);
        Val *fam_i0  = nbe_vapp(a, ty->id.ty, i0v);
        if (t->refl->tag == TM_HOLE) {
            if (!conv(a, depth, ty->id.lhs, ty->id.rhs)) {
                type_error(t->loc, "rfl: PathP endpoints not definitionally equal\n");
                return 0;
            }
            t->refl = nbe_quote(a, depth, ty->id.lhs);
            return 1;
        }
        if (!check(a, depth, tctx, env, t->refl, fam_i0)) return 0;
        Val *av = nbe_eval(a, env, t->refl);
        if (!conv_at(a, depth, av, ty->id.lhs, fam_i0)) {
            type_error(t->loc, "refl: element does not match PathP left endpoint\n");
            return 0;
        }
        if (!conv_at(a, depth, av, ty->id.rhs, fam_i0)) {
            type_error(t->loc, "refl: element does not match PathP right endpoint\n");
            return 0;
        }
        return 1;
    }
    /* refl checks against Path type */
    if (t->tag == TM_REFL && ty->tag == VL_PATH) {
        if (t->refl->tag == TM_HOLE) {
            if (!conv(a, depth, ty->id.lhs, ty->id.rhs)) {
                type_error(t->loc, "rfl: Path endpoints not definitionally equal\n");
                return 0;
            }
            /* Fill hole so nbe_eval(t) works if caller needs the value */
            t->refl = nbe_quote(a, depth, ty->id.lhs);
            return 1;
        }
        if (!check(a, depth, tctx, env, t->refl, ty->id.ty)) return 0;
        Val *av = nbe_eval(a, env, t->refl);
        if (!conv_at(a, depth, av, ty->id.lhs, ty->id.ty)) {
            type_error(t->loc, "refl: element does not match path left endpoint\n");
            return 0;
        }
        if (!conv_at(a, depth, av, ty->id.rhs, ty->id.ty)) {
            type_error(t->loc, "refl: element does not match path right endpoint\n");
            return 0;
        }
        return 1;
    }
    /* Lambda checks against Pi */
    if (t->tag == TM_LAM) {
        if (ty->tag != VL_PI) {
            type_error(t->loc, "expected Π type when checking λ\n");
            print_type(a, depth, tctx, "got", ty);
            return 0;
        }
        Val *fresh = vl_neutral(a, depth, NULL);
        Val *codv  = nbe_eval(a, env_cons(a, fresh, ty->pi.env), ty->pi.cod);
        TCtx ext   = { t->lam.name, ty->pi.dom, tctx };
        return check(a, depth + 1, &ext, env_cons(a, fresh, env), t->lam.body, codv);
    }
    /* fix body : ty   requires   body : ty -> ty */
    if (t->tag == TM_FIX) {
        Val *fn_ty = vl_pi(a, "_", ty, env_cons(a, ty, NULL), tm_var(a, 1));
        return check(a, depth, tctx, env, t->fix.body, fn_ty);
    }
    /* sup checks against W */
    if (t->tag == TM_SUP) {
        if (ty->tag != VL_W) {
            type_error(t->loc, "expected W type when checking sup\n");
            print_type(a, depth, tctx, "got", ty);
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
            type_error(t->loc, "expected Σ type when checking pair\n");
            print_type(a, depth, tctx, "got", ty);
            return 0;
        }
        if (!check(a, depth, tctx, env, t->pair.fst, ty->pi.dom)) return 0;
        Val *fstv = nbe_eval(a, env, t->pair.fst);
        Val *sndt = nbe_eval(a, env_cons(a, fstv, ty->pi.env), ty->pi.cod);
        return check(a, depth, tctx, env, t->pair.snd, sndt);
    }
    /* Phase L2 Stage 7d — glue intro (check mode only)
     *
     * glue φ t a  checked against  Glue A φ' T e:
     *   φ must conv φ'; t : Partial φ T; a : A.
     *   Coherence (fst(e)(t itIs) ≡ a when φ=i1) is trusted (like quotrec coh).
     */
    if (t->tag == TM_GLUEELEM) {
        if (ty->tag != VL_GLUE) {
            /* Concrete-face: glue i0 t a = a, glue i1 t a = t star.
             * We don't need the full Glue structure — check by reduction:
             *   φ=i0 → value is a; check a : ty.
             *   φ=i1 → value is t star; check t : Π(_:Unit). ty.  */
            Val *phi_v = nbe_eval(a, env, t->glue_elem_t.face);
            int phi_i0 = (phi_v->tag == VL_NEUTRAL && phi_v->neutral.lvl == IZERO_CONST_LVL);
            int phi_i1 = (phi_v->tag == VL_NEUTRAL && phi_v->neutral.lvl == IONE_CONST_LVL);
            if (phi_i0) {
                return check(a, depth, tctx, env, t->glue_elem_t.base, ty);
            } else if (phi_i1) {
                Val *unit_ty  = vl_unit(a);
                Val *tube_ty  = vl_pi(a, "_", unit_ty, env_cons(a, ty, NULL), tm_var(a, 1));
                return check(a, depth, tctx, env, t->glue_elem_t.partial, tube_ty);
            }
            type_error(t->loc, "glue: expected Glue type"
                    " (for non-endpoint faces, annotate with the Glue type)\n");
            return 0;
        }
        Val *A_val   = ty->glue_s.base;
        Val *phi_ty  = ty->glue_s.face;
        Val *T_val   = ty->glue_s.fiber;
        Val *phi_v   = nbe_eval(a, env, t->glue_elem_t.face);
        if (!conv(a, depth, phi_v, phi_ty)) {
            type_error(t->loc, "glue: face does not match Glue face\n");
            return 0;
        }
        /* Check partial : Partial φ T = Π(_:IsOne φ). T */
        Val *isone_phi  = nbe_visone(a, phi_v);
        Val *partial_ty = vl_pi(a, "_", isone_phi, env_cons(a, T_val, NULL), tm_var(a, 1));
        if (!check(a, depth, tctx, env, t->glue_elem_t.partial, partial_ty)) {
            type_error(t->loc, "glue: partial element must have type Partial φ T\n");
            return 0;
        }
        /* Check base : A */
        if (!check(a, depth, tctx, env, t->glue_elem_t.base, A_val)) {
            type_error(t->loc, "glue: base element must have type A\n");
            return 0;
        }
        return 1;
    }
    /* inl/inr check against Sum */
    if (t->tag == TM_INL) {
        if (ty->tag != VL_SUM) {
            type_error(t->loc, "expected Sum type when checking inl\n");
            print_type(a, depth, tctx, "got", ty);
            return 0;
        }
        return check(a, depth, tctx, env, t->elim, ty->pair.fst);
    }
    if (t->tag == TM_INR) {
        if (ty->tag != VL_SUM) {
            type_error(t->loc, "expected Sum type when checking inr\n");
            print_type(a, depth, tctx, "got", ty);
            return 0;
        }
        return check(a, depth, tctx, env, t->elim, ty->pair.snd);
    }
    /* Phase M4 — pattern matching in check mode */
    if (t->tag == TM_MATCH) {
        Val *scrut_ty = infer(a, depth, tctx, env, t->match_s.scrut);
        if (!scrut_ty) return 0;
        int fam_idx = t->match_s.fam_idx;
        int n_arms  = t->match_s.n_arms;
        MatchArm *arms = t->match_s.arms;
        int n_ctors;
        if (fam_idx == -1) {
            if (scrut_ty->tag != VL_NAT) {
                type_error(t->loc, "match: scrutinee must be Nat\n"); return 0;
            }
            n_ctors = 2;
        } else if (fam_idx == -2) {
            if (scrut_ty->tag != VL_BOOL) {
                type_error(t->loc, "match: scrutinee must be Bool\n"); return 0;
            }
            n_ctors = 2;
        } else {
            IndDef *fam = ind_get(fam_idx);
            if (scrut_ty->tag != VL_INDTYPE || scrut_ty->indtype.fam_idx != fam_idx) {
                type_error(t->loc, "match: scrutinee must be of type '%s'\n", fam->name);
                return 0;
            }
            n_ctors = fam->n_ctors;
        }
        if (n_arms != n_ctors) {
            type_error(t->loc, "match: expected %d arm(s), got %d\n", n_ctors, n_arms);
            return 0;
        }
        unsigned int seen_ctors2 = 0;
        for (int i = 0; i < n_arms; i++) {
            MatchArm *arm = &arms[i];
            /* Validate: no duplicate constructor arms */
            if (arm->ctor_idx < (int)(sizeof(seen_ctors2)*8)) {
                if (seen_ctors2 & (1u << arm->ctor_idx)) {
                    type_error(t->loc, "match: duplicate arm for constructor %d\n",
                            arm->ctor_idx);
                    return 0;
                }
                seen_ctors2 |= (1u << arm->ctor_idx);
            }
            /* Validate binder count against built-in constructor arity */
            if (fam_idx == -1) {
                int max_binds = (arm->ctor_idx == 1) ? 1 : 0;
                if (arm->n_binds > max_binds) {
                    type_error(t->loc, "match: arm '%s' has %d binder(s), at most %d expected\n",
                            arm->ctor_idx == 0 ? "zero" : "succ", arm->n_binds, max_binds);
                    return 0;
                }
            } else if (fam_idx == -2) {
                if (arm->n_binds > 0) {
                    type_error(t->loc, "match: Bool arm '%s' takes no binders\n",
                            arm->ctor_idx == 0 ? "true" : "false");
                    return 0;
                }
            }
            /* Validate IH: currently only supported for Nat succ */
            if (arm->ih_name) {
                if (!(fam_idx == -1 && arm->ctor_idx == 1)) {
                    type_error(t->loc, "match: IH binder only supported for Nat succ arm\n");
                    return 0;
                }
            }
            TCtx *arm_tctx = tctx;
            Env  *arm_env  = env;
            int   arm_depth = depth;
            TCtx  tctx_exts[MATCH_MAX_BINDS + 1];
            if (fam_idx == -1 && arm->ctor_idx == 1 && arm->n_binds > 0) {
                tctx_exts[0].name = arm->names[0];
                tctx_exts[0].type = vl_nat(a);
                tctx_exts[0].next = arm_tctx;
                arm_tctx = &tctx_exts[0];
                arm_env = env_cons(a, vl_neutral(a, arm_depth++, NULL), arm_env);
            } else if (fam_idx >= 0 && arm->n_binds > 0) {
                IndDef *fam = ind_get(fam_idx);
                CtorDef *ctor = &fam->ctors[arm->ctor_idx];
                int n_params = fam->n_params;
                Env *param_env = NULL;
                for (int pi = 0; pi < n_params; pi++)
                    param_env = env_cons(a, scrut_ty->indtype.args[pi], param_env);
                Val *tele = ctor->telescope ? nbe_eval(a, param_env, ctor->telescope) : NULL;
                TCtx *cur_tctx = arm_tctx;
                for (int j = 0; j < arm->n_binds; j++) {
                    if (!tele || tele->tag != VL_PI) {
                        type_error(t->loc, "match: arm '%s': telescope too short\n",
                                ctor->name);
                        return 0;
                    }
                    tctx_exts[j].name = arm->names[j];
                    tctx_exts[j].type = tele->pi.dom;
                    tctx_exts[j].next = cur_tctx;
                    cur_tctx = &tctx_exts[j];
                    Val *fresh = vl_neutral(a, arm_depth++, NULL);
                    arm_env = env_cons(a, fresh, arm_env);
                    tele = nbe_eval(a, env_cons(a, fresh, tele->pi.env), tele->pi.cod);
                }
                arm_tctx = cur_tctx;
            }
            /* IH binder: innermost, type = ty (the check type = constant motive) */
            if (arm->ih_name) {
                int ih_idx = arm->n_binds;
                tctx_exts[ih_idx].name = arm->ih_name;
                tctx_exts[ih_idx].type = ty;
                tctx_exts[ih_idx].next = arm_tctx;
                arm_tctx = &tctx_exts[ih_idx];
                arm_env = env_cons(a, vl_neutral(a, arm_depth++, NULL), arm_env);
            }
            if (!check(a, arm_depth, arm_tctx, arm_env, arm->body, ty)) return 0;
        }
        return 1;
    }
    /* Everything else: infer and convert */
    Val *ity = infer(a, depth, tctx, env, t);
    if (!ity) return 0;
    if (!conv(a, depth, ity, ty)) {
        type_error(t->loc, "type mismatch\n");
        print_type(a, depth, tctx, "inferred", ity);
        print_type(a, depth, tctx, "expected", ty);
        return 0;
    }
    return 1;
}

/* ── Pretty-print */

void val_print_tctx(Arena *a, Val *v, int depth, TCtx *tctx) {
    term_fprint_ctx(stdout, nbe_quote(a, depth, v), tctx_to_ctx(a, tctx), 0);
}
