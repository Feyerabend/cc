#include <stdio.h>
#include <string.h>
#include "termcheck.h"

/* ── Structural termination checker
 *
 * Algorithm (de Bruijn levels, not indices):
 *
 *   Variable at de Bruijn index i in a term at current depth d has level:
 *       lvl = d - i - 1
 *
 *   Levels are stable across binder entry: entering a binder increments d
 *   but does not change existing levels.  A fresh binder at depth d gets
 *   level d.
 *
 *   We track two properties per level:
 *     smaller[lvl]  = 1  iff lvl is STRICTLY smaller than the decreasing arg
 *     leq[lvl]      = 1  iff lvl is ≤ the decreasing arg (includes decr itself)
 *
 *   Initially: leq[decr_lvl] = 1, smaller[decr_lvl] = 0.
 *   When match scrutinises a leq variable, all arm binders get both flags set.
 *
 *   check_t silently returns 0 for any violation (no printing).  The caller
 *   is responsible for printing a diagnostic on overall failure.
 */

#define MAX_LEV  512
#define MAX_ARGS  64

typedef struct {
    int  f_lvl;              /* de Bruijn level of the recursive function */
    int  arity;              /* number of explicit argument lambdas         */
    int  decr_pos;           /* 0-indexed position of the decreasing arg    */
    char smaller[MAX_LEV];   /* smaller[l] = 1: strictly smaller than decr  */
    char leq[MAX_LEV];       /* leq[l]     = 1: ≤ decr (decr or smaller)    */
} TCtx;

/* ── Forward declaration */
static int check_t(Term *t, int depth, TCtx *ctx);

/* ── Helpers */

/* Strip TM_ANN wrappers from the outside of t. */
static Term *strip_ann(Term *t) {
    while (t && t->tag == TM_ANN) t = t->ann.term;
    return t;
}

/* Return the de Bruijn level of a variable (possibly ANN-wrapped), or -1.
 * Returns -1 if t is not (after stripping) a TM_VAR, or level is out of range. */
static int var_level(Term *t, int depth) {
    t = strip_ann(t);
    if (!t || t->tag != TM_VAR) return -1;
    int lv = depth - t->idx - 1;
    return (lv >= 0 && lv < MAX_LEV) ? lv : -1;
}

/* Collect the application spine of t into args[] (reverse order).
 * args[0] = last arg, args[n-1] = first arg.
 * Returns the head term (not TM_APP) and sets *n_args.                    */
static Term *collect_spine(Term *t, Term *args[], int *n_args) {
    *n_args = 0;
    while (t->tag == TM_APP && *n_args < MAX_ARGS) {
        args[(*n_args)++] = t->app.arg;
        t = t->app.fun;
    }
    return t;
}

/* ── Main traversal */

static int check_t(Term *t, int depth, TCtx *ctx) {
    if (!t) return 1;

    switch (t->tag) {

    /* ── Trivial leaves (no subterms) ── */
    case TM_UA: case TM_FUNEXT: case TM_NAT: case TM_ZERO:
    case TM_BOOL: case TM_TRUE: case TM_FALSE:
    case TM_UNIT: case TM_STAR: case TM_EMPTY:
    case TM_CIRCLE: case TM_BASE: case TM_LOOP:
    case TM_INTERVAL: case TM_IZERO: case TM_IONE:
    case TM_TRUNC: case TM_TRINT: case TM_SQUASH:
    case TM_QUOT: case TM_QIN: case TM_QEQS:
    case TM_LEVEL: case TM_LZERO:
    case TM_HOLE:
    case TM_UNI:
    case TM_GLOBAL:
        return 1;

    /* ── Variable ── */
    case TM_VAR: {
        int lv = depth - t->idx - 1;
        /* f appears bare (not as head of a full application) — invalid */
        if (lv == ctx->f_lvl) return 0;
        return 1;
    }

    /* ── Lambda / path abstraction: one new binder ── */
    case TM_LAM:
    case TM_PATHABS:
        return check_t(t->lam.body, depth + 1, ctx);

    /* ── Application — spine collection ── */
    case TM_APP: {
        Term *args[MAX_ARGS];
        int n_args;
        Term *head = collect_spine(t, args, &n_args);

        /* Check whether head is the recursive function f */
        {
            Term *h = strip_ann(head);
            if (h && h->tag == TM_VAR) {
                int head_lv = depth - h->idx - 1;
                if (head_lv == ctx->f_lvl) {
                    /* Recursive call: must be fully applied with a smaller
                     * decreasing argument. */
                    if (n_args != ctx->arity) return 0;
                    /* args is in reverse: args[0]=last, args[n-1]=first.
                     * Decreasing arg is at position decr_pos from the front. */
                    Term *decr_arg = args[ctx->arity - 1 - ctx->decr_pos];
                    int dlv = var_level(decr_arg, depth);
                    if (dlv < 0 || !ctx->smaller[dlv]) return 0;
                    /* Also scan all args for nested f occurrences */
                    for (int i = 0; i < n_args; i++)
                        if (!check_t(args[i], depth, ctx)) return 0;
                    return 1;
                }
            }
        }
        /* Not a recursive call — recurse into head and all args */
        if (!check_t(head, depth, ctx)) return 0;
        for (int i = 0; i < n_args; i++)
            if (!check_t(args[i], depth, ctx)) return 0;
        return 1;
    }

    /* ── Dependent types: dom at current depth, cod under one binder ── */
    case TM_PI: case TM_SIG: case TM_W:
        return check_t(t->pi.dom, depth, ctx)
            && check_t(t->pi.cod, depth + 1, ctx);

    /* ── Annotation: check both sides ── */
    case TM_ANN:
        return check_t(t->ann.term, depth, ctx)
            && check_t(t->ann.type, depth, ctx);

    /* ── Pair ── */
    case TM_PAIR:
        return check_t(t->pair.fst, depth, ctx)
            && check_t(t->pair.snd, depth, ctx);

    /* ── Single-subterm eliminators (reuse t->elim) ── */
    case TM_FST: case TM_SND:
    case TM_SUCC:
    case TM_INL: case TM_INR:
    case TM_INEG:
    case TM_LSUC:
    case TM_ISONE:
        return check_t(t->elim, depth, ctx);

    /* ── Id / Path type ── */
    case TM_ID: case TM_PATH:
        return check_t(t->id.ty,  depth, ctx)
            && check_t(t->id.lhs, depth, ctx)
            && check_t(t->id.rhs, depth, ctx);

    case TM_REFL:
        return check_t(t->refl, depth, ctx);

    /* ── J eliminator ── */
    case TM_J:
        return check_t(t->j.ty,       depth, ctx)
            && check_t(t->j.lhs,      depth, ctx)
            && check_t(t->j.motive,   depth, ctx)
            && check_t(t->j.base,     depth, ctx)
            && check_t(t->j.endpoint, depth, ctx)
            && check_t(t->j.proof,    depth, ctx);

    /* ── Built-in recursors: recurse into all subterms ── */
    case TM_NATREC:
        return check_t(t->natrec.motive, depth, ctx)
            && check_t(t->natrec.base,   depth, ctx)
            && check_t(t->natrec.step,   depth, ctx)
            && check_t(t->natrec.scrut,  depth, ctx);

    case TM_BOOLREC:
        return check_t(t->boolrec.motive, depth, ctx)
            && check_t(t->boolrec.tcase,  depth, ctx)
            && check_t(t->boolrec.fcase,  depth, ctx)
            && check_t(t->boolrec.scrut,  depth, ctx);

    case TM_WREC:
        return check_t(t->wrec.motive, depth, ctx)
            && check_t(t->wrec.step,   depth, ctx)
            && check_t(t->wrec.scrut,  depth, ctx);

    case TM_SUP:
        return check_t(t->sup.label,    depth, ctx)
            && check_t(t->sup.children, depth, ctx);

    case TM_ABORT:
        return check_t(t->abort_t.motive, depth, ctx)
            && check_t(t->abort_t.scrut,  depth, ctx);

    case TM_UNITREC:
        return check_t(t->unitrec_t.motive, depth, ctx)
            && check_t(t->unitrec_t.base,   depth, ctx)
            && check_t(t->unitrec_t.scrut,  depth, ctx);

    case TM_SUM:
        return check_t(t->sum_t.left,  depth, ctx)
            && check_t(t->sum_t.right, depth, ctx);

    case TM_CASESPLIT:
        return check_t(t->casesplit_t.motive, depth, ctx)
            && check_t(t->casesplit_t.lcase,  depth, ctx)
            && check_t(t->casesplit_t.rcase,  depth, ctx)
            && check_t(t->casesplit_t.scrut,  depth, ctx);

    case TM_TRUNCREC:
        return check_t(t->truncrec_t.ty_a,  depth, ctx)
            && check_t(t->truncrec_t.ty_b,  depth, ctx)
            && check_t(t->truncrec_t.func,  depth, ctx)
            && check_t(t->truncrec_t.scrut, depth, ctx);

    case TM_QUOTREC:
        return check_t(t->quotrec_t.ty_a,  depth, ctx)
            && check_t(t->quotrec_t.rel,    depth, ctx)
            && check_t(t->quotrec_t.ty_b,   depth, ctx)
            && check_t(t->quotrec_t.func,   depth, ctx)
            && check_t(t->quotrec_t.coh,    depth, ctx)
            && check_t(t->quotrec_t.scrut,  depth, ctx);

    case TM_CIRCREC:
        return check_t(t->circrec_t.motive,    depth, ctx)
            && check_t(t->circrec_t.base_case,  depth, ctx)
            && check_t(t->circrec_t.loop_case,  depth, ctx)
            && check_t(t->circrec_t.scrut,      depth, ctx);

    /* ── Inductive types / constructors / recursors ── */
    case TM_INDTYPE: {
        for (int i = 0; i < t->indtype.n_args; i++)
            if (!check_t(t->indtype.args[i], depth, ctx)) return 0;
        return 1;
    }
    case TM_INDCON: {
        for (int i = 0; i < t->indcon.n_args; i++)
            if (!check_t(t->indcon.args[i], depth, ctx)) return 0;
        return 1;
    }
    case TM_INDREC: {
        if (!check_t(t->indrec.motive, depth, ctx)) return 0;
        for (int i = 0; i < t->indrec.n_cases; i++)
            if (!check_t(t->indrec.cases[i], depth, ctx)) return 0;
        return check_t(t->indrec.scrut, depth, ctx);
    }

    /* ── Nested fix: cannot verify inline non-let-rec fix ── */
    case TM_FIX:
        return 0;

    /* ── Universe at a variable level ── */
    case TM_UNI_V:
        return check_t(t->uni_v_lvl, depth, ctx);

    /* ── Path application / transport / interval ops (reuse app.{fun,arg}) ── */
    case TM_PATHAPP:
    case TM_TRANSP:
    case TM_IMIN:
    case TM_IMAX:
    case TM_LMAX:
        return check_t(t->app.fun, depth, ctx)
            && check_t(t->app.arg, depth, ctx);

    /* ── hcomp ── */
    case TM_HCOMP:
        return check_t(t->hcomp_t.ty,   depth, ctx)
            && check_t(t->hcomp_t.face, depth, ctx)
            && check_t(t->hcomp_t.tube, depth, ctx)
            && check_t(t->hcomp_t.base, depth, ctx);

    /* ── Glue type ── */
    case TM_GLUE:
        return check_t(t->glue_t.base,  depth, ctx)
            && check_t(t->glue_t.face,  depth, ctx)
            && check_t(t->glue_t.fiber, depth, ctx)
            && check_t(t->glue_t.equiv, depth, ctx);

    case TM_GLUEELEM:
        return check_t(t->glue_elem_t.face,    depth, ctx)
            && check_t(t->glue_elem_t.partial, depth, ctx)
            && check_t(t->glue_elem_t.base,    depth, ctx);

    case TM_UNGLUE:
        return check_t(t->unglue_t.face,  depth, ctx)
            && check_t(t->unglue_t.equiv, depth, ctx)
            && check_t(t->unglue_t.elem,  depth, ctx);

    case TM_PRIMSUB:
        return check_t(t->primsub_t.ty,   depth, ctx)
            && check_t(t->primsub_t.face, depth, ctx)
            && check_t(t->primsub_t.u,    depth, ctx)
            && check_t(t->primsub_t.a,    depth, ctx);

    /* ── Pattern matching ── */
    case TM_MATCH: {
        Term *scrut = t->match_s.scrut;
        if (!check_t(scrut, depth, ctx)) return 0;

        /* Determine if scrutinee is a (≤ decr) variable.
         * Strip TM_ANN: 'match (n : Nat) of' is the same as 'match n of'. */
        int scrut_lv  = var_level(scrut, depth);   /* strips TM_ANN internally */
        int scrut_leq = (scrut_lv >= 0 && ctx->leq[scrut_lv]);

        for (int i = 0; i < t->match_s.n_arms; i++) {
            MatchArm *arm = &t->match_s.arms[i];
            int nb = arm->n_binds;
            int ih_extra = (arm->ih_name != NULL) ? 1 : 0;

            /* When scrutinee is ≤ decr, field binders are strictly smaller.
             * Levels for the nb new binders: depth, depth+1, ..., depth+nb-1.
             * The IH binder at depth+nb is a value, not a structural element.
             * Save existing values and extend. */
            char sv_sm [MATCH_MAX_BINDS];
            char sv_leq[MATCH_MAX_BINDS];
            if (scrut_leq) {
                for (int j = 0; j < nb; j++) {
                    int lv = depth + j;
                    if (lv < MAX_LEV) {
                        sv_sm[j]         = ctx->smaller[lv];
                        sv_leq[j]        = ctx->leq[lv];
                        ctx->smaller[lv] = 1;
                        ctx->leq[lv]     = 1;
                    } else {
                        sv_sm[j] = sv_leq[j] = 0; /* out-of-range: skip */
                    }
                }
            }

            int ok = check_t(arm->body, depth + nb + ih_extra, ctx);

            /* Restore */
            if (scrut_leq) {
                for (int j = 0; j < nb; j++) {
                    int lv = depth + j;
                    if (lv < MAX_LEV) {
                        ctx->smaller[lv] = sv_sm[j];
                        ctx->leq[lv]     = sv_leq[j];
                    }
                }
            }

            if (!ok) return 0;
        }
        return 1;
    }

    default:
        /* Unknown / future tag: conservatively pass.
         * Tags without de Bruijn binders are harmless to skip.         */
        return 1;
    }
}

/* ── Public entry point */

int term_check_structural(Term *fix_body, const char *name) {
    if (!name) name = "<anonymous>";

    /* fix_body = \f. args_body.  f is de Bruijn level 0.
     * If not a lambda (e.g. ANN-wrapped), strip annotation first. */
    fix_body = strip_ann(fix_body);
    if (!fix_body || fix_body->tag != TM_LAM) {
        /* No outer lambda: either trivially non-recursive or ill-typed.
         * Let the type checker handle ill-formedness.  If the body contains
         * a self-call (f = VAR at level 0) without arguments, the type
         * checker will reject it.                                         */
        return 1;
    }

    Term *args_body = fix_body->lam.body;

    /* Count arity: strip leading lambdas.  Cap at MAX_ARGS. */
    int arity = 0;
    {
        Term *p = args_body;
        while (p && p->tag == TM_LAM && arity < MAX_ARGS) {
            arity++;
            p = p->lam.body;
        }
    }

    if (arity == 0) {
        /* Zero-arity fix: no decreasing argument.
         * Pass iff the body contains no self-call (f at level 0). */
        TCtx ctx;
        memset(&ctx, 0, sizeof ctx);
        ctx.f_lvl    = 0;
        ctx.arity    = 0;
        ctx.decr_pos = 0;
        if (check_t(args_body, 1, &ctx)) return 1;
        fprintf(stderr,
            "termination: '%s' is self-referential with no arguments\n",
            name);
        return 0;
    }

    /* Try each argument position as the decreasing one.
     * f has level 0; argument i (0-indexed) has level i+1.
     * Start check_t from args_body at depth 1 (inside \f).             */
    for (int decr_pos = 0; decr_pos < arity; decr_pos++) {
        TCtx ctx;
        memset(&ctx, 0, sizeof ctx);
        ctx.f_lvl    = 0;
        ctx.arity    = arity;
        ctx.decr_pos = decr_pos;
        int decr_lvl = decr_pos + 1;
        ctx.leq[decr_lvl] = 1;

        if (check_t(args_body, 1, &ctx))
            return 1;
    }

    fprintf(stderr,
        "termination: '%s' is not structurally recursive on any argument\n"
        "  (recursive calls must use a pattern-match binder of the decreasing argument)\n",
        name);
    return 0;
}
