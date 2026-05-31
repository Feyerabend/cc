#include "bridge.h"
#include "reduce.h"
#include "../core/eval.h"
#include "../core/defs.h"

/* val_to_node
 * Wrap a core Val* in a ND_CORE heap node marked WHNF+NF.
 */
NodeRef val_to_node(Heap *h, Val *v) {
    NodeRef r = heap_alloc(h);
    h->nodes[r].tag   = (uint8_t)ND_CORE;
    h->nodes[r].flags = NF_WHNF | NF_NF;
    h->nodes[r].aux   = v;
    return r;
}

/* SentCtx — stack of Pi/Sigma/W binder sentinels.
 * Each entry is a heap ND_VAR(BINDER_LVL) node whose NodeRef is unique.
 * sent_lookup maps a sentinel NodeRef to its de Bruijn index (0 = innermost).
 */
typedef struct SentCtx SentCtx;
struct SentCtx {
    NodeRef  sentinel;
    SentCtx *outer;
};

static int sent_lookup(SentCtx *ctx, NodeRef sent) {
    int idx = 0;
    while (ctx) {
        if (ctx->sentinel == sent) return idx;
        idx++;
        ctx = ctx->outer;
    }
    return -1;
}

/* Forward declaration */
static Term *node_to_term_ctx(Heap *h, NodeRef r, Arena *a, SentCtx *ctx);

/* force_cod — normalize a Pi/Sigma/W cod thunk with a fresh binder sentinel.
 *
 * Creates a copy of the thunk with the sentinel prepended to its env, forces
 * it, then serializes the result. If cod_r is not a thunk (already forced),
 * falls through to plain node_to_term_ctx.
 */
static Term *force_cod(Heap *h, NodeRef cod_r, Arena *a, SentCtx *ctx) {
    cod_r = node_deref(h, cod_r);
    if (cod_r == NULL_REF) return NULL;
    if (h->nodes[cod_r].tag != ND_THUNK)
        return node_to_term_ctx(h, cod_r, a, ctx);

    /* Capture before any heap mutation */
    void    *body    = h->nodes[cod_r].aux;
    NodeRef  old_env = h->nodes[cod_r].ch[0];

    /* Build extended env with fresh BINDER_LVL sentinel at index 0 */
    NodeRef sentinel = mk_var(h, BINDER_LVL);
    NodeRef new_env  = mk_env(h, sentinel, old_env);
    NodeRef copy     = mk_thunk(h, body, new_env);
    nf(h, a, copy);

    SentCtx new_ctx = { sentinel, ctx };
    return node_to_term_ctx(h, copy, a, &new_ctx);
}

/* node_to_term_ctx — recursive core; passes sentinel context through. */
static Term *node_to_term_ctx(Heap *h, NodeRef r, Arena *a, SentCtx *ctx) {
    r = node_deref(h, r);
    if (r == NULL_REF) return NULL;

    switch ((NodeTag)h->nodes[r].tag) {

    case ND_REF:
        return node_to_term_ctx(h, h->nodes[r].ch[0], a, ctx);

    /* Thunk: return stored Term* directly (correct when no open de Bruijn refs) */
    case ND_THUNK:
        return (Term *)h->nodes[r].aux;

    /* Atomic types */
    case ND_NAT:   return tm_nat(a);
    case ND_BOOL:  return tm_bool(a);
    case ND_UNIT:  return tm_unit(a);
    case ND_EMPTY: return tm_empty(a);
    case ND_S1:    return tm_circle(a);
    case ND_TRUNC: return tm_trunc(a);
    case ND_TRINT: return tm_trint(a);
    case ND_UNI:   return tm_uni(a, h->nodes[r].ulvl);

    /* Canonical constructors (no children) */
    case ND_ZERO:  return tm_zero(a);
    case ND_TRUE:  return tm_true(a);
    case ND_FALSE: return tm_false(a);
    case ND_STAR:  return tm_star(a);
    case ND_BASE:  return tm_base(a);
    case ND_LOOP:  return tm_loop(a);

    /* Canonical constructors (one child) */
    case ND_SUCC: {
        NodeRef c0 = h->nodes[r].ch[0];
        Term *pred = node_to_term_ctx(h, c0, a, ctx);
        return pred ? tm_succ(a, pred) : NULL;
    }
    case ND_REFL: {
        NodeRef c0 = h->nodes[r].ch[0];
        Term *t = node_to_term_ctx(h, c0, a, ctx);
        return t ? tm_refl(a, t) : NULL;
    }
    case ND_INL: {
        NodeRef c0 = h->nodes[r].ch[0];
        Term *t = node_to_term_ctx(h, c0, a, ctx);
        return t ? tm_inl(a, t) : NULL;
    }
    case ND_INR: {
        NodeRef c0 = h->nodes[r].ch[0];
        Term *t = node_to_term_ctx(h, c0, a, ctx);
        return t ? tm_inr(a, t) : NULL;
    }

    /* Canonical constructors (two children) */
    case ND_PAIR: {
        NodeRef c0 = h->nodes[r].ch[0], c1 = h->nodes[r].ch[1];
        Term *fst = node_to_term_ctx(h, c0, a, ctx);
        Term *snd = node_to_term_ctx(h, c1, a, ctx);
        return (fst && snd) ? tm_pair(a, fst, snd) : NULL;
    }
    case ND_SUP: {
        NodeRef c0 = h->nodes[r].ch[0], c1 = h->nodes[r].ch[1];
        Term *label    = node_to_term_ctx(h, c0, a, ctx);
        Term *children = node_to_term_ctx(h, c1, a, ctx);
        return (label && children) ? tm_sup(a, label, children) : NULL;
    }

    /* Dependent types — cod uses force_cod to extend sentinel context */
    case ND_PI: {
        NodeRef dom_r = h->nodes[r].ch[0];
        NodeRef cod_r = h->nodes[r].ch[1];
        char   *name  = h->nodes[r].name;
        Term *dom = node_to_term_ctx(h, dom_r, a, ctx);
        Term *cod = force_cod(h, cod_r, a, ctx);
        return (dom && cod) ? tm_pi(a, name, dom, cod) : NULL;
    }
    case ND_SIGMA: {
        NodeRef dom_r = h->nodes[r].ch[0];
        NodeRef cod_r = h->nodes[r].ch[1];
        char   *name  = h->nodes[r].name;
        Term *dom = node_to_term_ctx(h, dom_r, a, ctx);
        Term *cod = force_cod(h, cod_r, a, ctx);
        return (dom && cod) ? tm_sig(a, name, dom, cod) : NULL;
    }
    case ND_W: {
        NodeRef dom_r = h->nodes[r].ch[0];
        NodeRef cod_r = h->nodes[r].ch[1];
        char   *name  = h->nodes[r].name;
        Term *dom = node_to_term_ctx(h, dom_r, a, ctx);
        Term *cod = force_cod(h, cod_r, a, ctx);
        return (dom && cod) ? tm_w(a, name, dom, cod) : NULL;
    }
    case ND_ID: {
        NodeRef c0 = h->nodes[r].ch[0], c1 = h->nodes[r].ch[1], c2 = h->nodes[r].ch[2];
        Term *ty  = node_to_term_ctx(h, c0, a, ctx);
        Term *lhs = node_to_term_ctx(h, c1, a, ctx);
        Term *rhs = node_to_term_ctx(h, c2, a, ctx);
        return (ty && lhs && rhs) ? tm_id(a, ty, lhs, rhs) : NULL;
    }
    case ND_SUM: {
        NodeRef c0 = h->nodes[r].ch[0], c1 = h->nodes[r].ch[1];
        Term *left  = node_to_term_ctx(h, c0, a, ctx);
        Term *right = node_to_term_ctx(h, c1, a, ctx);
        return (left && right) ? tm_sum(a, left, right) : NULL;
    }

    /* Application (may be stuck neutral) */
    case ND_APP: {
        NodeRef c0 = h->nodes[r].ch[0], c1 = h->nodes[r].ch[1];
        Term *fun = node_to_term_ctx(h, c0, a, ctx);
        Term *arg = node_to_term_ctx(h, c1, a, ctx);
        return (fun && arg) ? tm_app(a, fun, arg) : NULL;
    }

    /* Lambda (only handles no-env case) */
    case ND_LAM:
        if (h->nodes[r].ch[0] != NULL_REF) return NULL;
        return tm_lam(a, h->nodes[r].name, (Term *)h->nodes[r].aux);

    /* Open variable — only serializable if it's a BINDER_LVL sentinel */
    case ND_VAR:
        if (h->nodes[r].lvl == BINDER_LVL) {
            int idx = sent_lookup(ctx, r);
            return idx >= 0 ? tm_var(a, idx) : NULL;
        }
        return NULL;

    /* Global / axiom constants */
    case ND_GLOBAL: {
        int idx = h->nodes[r].lvl;
        if (idx >= 0) return tm_global(a, idx);
        if (idx == -1) return tm_ua(a);
        if (idx == -2) return tm_funext(a);
        if (idx == -3) return tm_squash(a);
        return NULL;
    }

    /* Eliminators */
    case ND_FST: {
        NodeRef c0 = h->nodes[r].ch[0];
        Term *s = node_to_term_ctx(h, c0, a, ctx);
        return s ? tm_fst(a, s) : NULL;
    }
    case ND_SND: {
        NodeRef c0 = h->nodes[r].ch[0];
        Term *s = node_to_term_ctx(h, c0, a, ctx);
        return s ? tm_snd(a, s) : NULL;
    }
    case ND_NATREC: {
        NodeRef c0 = h->nodes[r].ch[0], c1 = h->nodes[r].ch[1];
        NodeRef c2 = h->nodes[r].ch[2], c3 = h->nodes[r].ch[3];
        Term *motive = node_to_term_ctx(h, c0, a, ctx);
        Term *base   = node_to_term_ctx(h, c1, a, ctx);
        Term *step   = node_to_term_ctx(h, c2, a, ctx);
        Term *scrut  = node_to_term_ctx(h, c3, a, ctx);
        return (motive && base && step && scrut)
               ? tm_natrec(a, motive, base, step, scrut) : NULL;
    }
    case ND_BOOLREC: {
        NodeRef c0 = h->nodes[r].ch[0], c1 = h->nodes[r].ch[1];
        NodeRef c2 = h->nodes[r].ch[2], c3 = h->nodes[r].ch[3];
        Term *motive = node_to_term_ctx(h, c0, a, ctx);
        Term *tcase  = node_to_term_ctx(h, c1, a, ctx);
        Term *fcase  = node_to_term_ctx(h, c2, a, ctx);
        Term *scrut  = node_to_term_ctx(h, c3, a, ctx);
        return (motive && tcase && fcase && scrut)
               ? tm_boolrec(a, motive, tcase, fcase, scrut) : NULL;
    }
    case ND_S1REC: {
        NodeRef c0 = h->nodes[r].ch[0], c1 = h->nodes[r].ch[1];
        NodeRef c2 = h->nodes[r].ch[2], c3 = h->nodes[r].ch[3];
        Term *motive    = node_to_term_ctx(h, c0, a, ctx);
        Term *base_case = node_to_term_ctx(h, c1, a, ctx);
        Term *loop_case = node_to_term_ctx(h, c2, a, ctx);
        Term *scrut     = node_to_term_ctx(h, c3, a, ctx);
        return (motive && base_case && loop_case && scrut)
               ? tm_circrec(a, motive, base_case, loop_case, scrut) : NULL;
    }
    case ND_TRUNCREC: {
        NodeRef c0 = h->nodes[r].ch[0], c1 = h->nodes[r].ch[1];
        NodeRef c2 = h->nodes[r].ch[2], c3 = h->nodes[r].ch[3];
        Term *ty_a  = node_to_term_ctx(h, c0, a, ctx);
        Term *ty_b  = node_to_term_ctx(h, c1, a, ctx);
        Term *func  = node_to_term_ctx(h, c2, a, ctx);
        Term *scrut = node_to_term_ctx(h, c3, a, ctx);
        return (ty_a && ty_b && func && scrut)
               ? tm_truncrec(a, ty_a, ty_b, func, scrut) : NULL;
    }
    case ND_CASESPLIT: {
        NodeRef c0 = h->nodes[r].ch[0], c1 = h->nodes[r].ch[1];
        NodeRef c2 = h->nodes[r].ch[2], c3 = h->nodes[r].ch[3];
        Term *motive = node_to_term_ctx(h, c0, a, ctx);
        Term *lcase  = node_to_term_ctx(h, c1, a, ctx);
        Term *rcase  = node_to_term_ctx(h, c2, a, ctx);
        Term *scrut  = node_to_term_ctx(h, c3, a, ctx);
        return (motive && lcase && rcase && scrut)
               ? tm_casesplit(a, motive, lcase, rcase, scrut) : NULL;
    }
    case ND_UNITREC: {
        NodeRef c0 = h->nodes[r].ch[0], c1 = h->nodes[r].ch[1], c2 = h->nodes[r].ch[2];
        Term *motive = node_to_term_ctx(h, c0, a, ctx);
        Term *base   = node_to_term_ctx(h, c1, a, ctx);
        Term *scrut  = node_to_term_ctx(h, c2, a, ctx);
        return (motive && base && scrut)
               ? tm_unitrec(a, motive, base, scrut) : NULL;
    }
    case ND_ABORT: {
        NodeRef c0 = h->nodes[r].ch[0], c1 = h->nodes[r].ch[1];
        Term *motive = node_to_term_ctx(h, c0, a, ctx);
        Term *scrut  = node_to_term_ctx(h, c1, a, ctx);
        return (motive && scrut) ? tm_abort(a, motive, scrut) : NULL;
    }
    case ND_J: {
        NodeRef c0 = h->nodes[r].ch[0], c1 = h->nodes[r].ch[1], c2 = h->nodes[r].ch[2];
        NodeRef c3 = h->nodes[r].ch[3], c4 = h->nodes[r].ch[4], c5 = h->nodes[r].ch[5];
        Term *ty       = node_to_term_ctx(h, c0, a, ctx);
        Term *lhs      = node_to_term_ctx(h, c1, a, ctx);
        Term *motive   = node_to_term_ctx(h, c2, a, ctx);
        Term *base     = node_to_term_ctx(h, c3, a, ctx);
        Term *endpoint = node_to_term_ctx(h, c4, a, ctx);
        Term *proof    = node_to_term_ctx(h, c5, a, ctx);
        return (ty && lhs && motive && base && endpoint && proof)
               ? tm_j(a, ty, lhs, motive, base, endpoint, proof) : NULL;
    }
    case ND_WREC: {
        NodeRef c0 = h->nodes[r].ch[0], c1 = h->nodes[r].ch[1], c2 = h->nodes[r].ch[2];
        Term *motive = node_to_term_ctx(h, c0, a, ctx);
        Term *step   = node_to_term_ctx(h, c1, a, ctx);
        Term *scrut  = node_to_term_ctx(h, c2, a, ctx);
        return (motive && step && scrut)
               ? tm_wrec(a, motive, step, scrut) : NULL;
    }

    /* Core wrapper: quote Val* back to a Term */
    case ND_CORE:
        return nbe_quote(a, 0, (Val *)h->nodes[r].aux);

    /* Inductive type former */
    case ND_INDTYPE: {
        int fam_idx = h->nodes[r].lvl;
        IndDef *fam = ind_get(fam_idx);
        int n       = fam->n_params + fam->n_indices;
        if (n > 6) return NULL;
        Term **args = n > 0 ? (Term **)arena_alloc(a, n * sizeof(Term *)) : NULL;
        for (int i = 0; i < n; i++) {
            args[i] = node_to_term_ctx(h, h->nodes[r].ch[i], a, ctx);
            if (!args[i]) return NULL;
        }
        return tm_indtype(a, fam_idx, n, args);
    }
    /* Inductive constructor */
    case ND_INDCON: {
        int packed   = h->nodes[r].lvl;
        int fam_idx  = (packed >> 16) & 0xFFFF;
        int ctor_idx = packed & 0xFFFF;
        IndDef *fam  = ind_get(fam_idx);
        if (ctor_idx >= fam->n_ctors) return NULL;
        int n        = fam->n_params + fam->ctors[ctor_idx].arity;
        if (n > 6) return NULL;
        Term **args  = n > 0 ? (Term **)arena_alloc(a, n * sizeof(Term *)) : NULL;
        for (int i = 0; i < n; i++) {
            args[i] = node_to_term_ctx(h, h->nodes[r].ch[i], a, ctx);
            if (!args[i]) return NULL;
        }
        return tm_indcon(a, fam_idx, ctor_idx, n, args);
    }
    /* Stuck inductive eliminator */
    case ND_INDREC: {
        int fam_idx = h->nodes[r].lvl;
        IndDef *fam = ind_get(fam_idx);
        int n       = fam->n_ctors;
        if (n > 4) return NULL;
        Term *scrut = node_to_term_ctx(h, h->nodes[r].ch[0], a, ctx);
        if (!scrut) return NULL;
        Term *motive = h->nodes[r].ch[1] != NULL_REF
                      ? node_to_term_ctx(h, h->nodes[r].ch[1], a, ctx) : NULL;
        Term **cases = n > 0 ? (Term **)arena_alloc(a, n * sizeof(Term *)) : NULL;
        for (int i = 0; i < n; i++) {
            cases[i] = node_to_term_ctx(h, h->nodes[r].ch[2+i], a, ctx);
            if (!cases[i]) return NULL;
        }
        return tm_indrec(a, fam_idx, motive, n, cases, scrut);
    }

    case ND_FIX: {
        Term *body = node_to_term_ctx(h, h->nodes[r].ch[0], a, ctx);
        return body ? tm_fix(a, body) : NULL;
    }

    /* Level terms (universe polymorphism) */
    case ND_LEVEL: return tm_level(a);
    case ND_LZERO: return tm_lzero(a);
    case ND_LSUC: {
        Term *pred = node_to_term_ctx(h, h->nodes[r].ch[0], a, ctx);
        return pred ? tm_lsuc(a, pred) : NULL;
    }
    case ND_UNI_V: {
        Term *lvl = node_to_term_ctx(h, h->nodes[r].ch[0], a, ctx);
        return lvl ? tm_uni_v(a, lvl) : NULL;
    }

    /* Cannot serialize */
    case ND_ENV:
    case ND_BLACKHOLE_TAG:
    default:
        return NULL;
    }
}

/* node_to_term — public entry point */
Term *node_to_term(Heap *h, NodeRef r, Arena *a) {
    return node_to_term_ctx(h, r, a, NULL);
}
