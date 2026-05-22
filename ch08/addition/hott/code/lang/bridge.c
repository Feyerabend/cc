#include "bridge.h"
#include "../core/eval.h"

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

/* node_to_term
 * Convert an NF heap node to a core Term.
 */
Term *node_to_term(Heap *h, NodeRef r, Arena *a) {
    r = node_deref(h, r);
    if (r == NULL_REF) return NULL;

    Node *n = &h->nodes[r];

    switch ((NodeTag)n->tag) {

    /* Indirection (should be consumed by node_deref, but be safe) */
    case ND_REF:
        return node_to_term(h, n->ch[0], a);

    /* Thunk: return stored Term* directly (see header for caveats) */
    case ND_THUNK:
        return (Term *)n->aux;

    /* Atomic types */
    case ND_NAT:   return tm_nat(a);
    case ND_BOOL:  return tm_bool(a);
    case ND_UNIT:  return tm_unit(a);
    case ND_EMPTY: return tm_empty(a);
    case ND_S1:    return tm_circle(a);
    case ND_TRUNC: return tm_trunc(a);
    case ND_TRINT: return tm_trint(a);
    case ND_UNI:   return tm_uni(a, n->ulvl);

    /* Canonical constructors (no children) */
    case ND_ZERO:  return tm_zero(a);
    case ND_TRUE:  return tm_true(a);
    case ND_FALSE: return tm_false(a);
    case ND_STAR:  return tm_star(a);
    case ND_BASE:  return tm_base(a);
    case ND_LOOP:  return tm_loop(a);

    /* Canonical constructors (one child) */
    case ND_SUCC: {
        Term *pred = node_to_term(h, n->ch[0], a);
        return pred ? tm_succ(a, pred) : NULL;
    }
    case ND_REFL: {
        Term *t = node_to_term(h, n->ch[0], a);
        return t ? tm_refl(a, t) : NULL;
    }
    case ND_INL: {
        Term *t = node_to_term(h, n->ch[0], a);
        return t ? tm_inl(a, t) : NULL;
    }
    case ND_INR: {
        Term *t = node_to_term(h, n->ch[0], a);
        return t ? tm_inr(a, t) : NULL;
    }

    /* Canonical constructors (two children) */
    case ND_PAIR: {
        Term *fst = node_to_term(h, n->ch[0], a);
        Term *snd = node_to_term(h, n->ch[1], a);
        return (fst && snd) ? tm_pair(a, fst, snd) : NULL;
    }
    case ND_SUP: {
        Term *label    = node_to_term(h, n->ch[0], a);
        Term *children = node_to_term(h, n->ch[1], a);
        return (label && children) ? tm_sup(a, label, children) : NULL;
    }

    /* Dependent types */
    case ND_PI: {
        Term *dom = node_to_term(h, n->ch[0], a);
        Term *cod = node_to_term(h, n->ch[1], a);
        return (dom && cod) ? tm_pi(a, n->name, dom, cod) : NULL;
    }
    case ND_SIGMA: {
        Term *dom = node_to_term(h, n->ch[0], a);
        Term *cod = node_to_term(h, n->ch[1], a);
        return (dom && cod) ? tm_sig(a, n->name, dom, cod) : NULL;
    }
    case ND_W: {
        Term *dom = node_to_term(h, n->ch[0], a);
        Term *cod = node_to_term(h, n->ch[1], a);
        return (dom && cod) ? tm_w(a, n->name, dom, cod) : NULL;
    }
    case ND_ID: {
        Term *ty  = node_to_term(h, n->ch[0], a);
        Term *lhs = node_to_term(h, n->ch[1], a);
        Term *rhs = node_to_term(h, n->ch[2], a);
        return (ty && lhs && rhs) ? tm_id(a, ty, lhs, rhs) : NULL;
    }
    case ND_SUM: {
        Term *left  = node_to_term(h, n->ch[0], a);
        Term *right = node_to_term(h, n->ch[1], a);
        return (left && right) ? tm_sum(a, left, right) : NULL;
    }

    /* Application (may be stuck neutral) */
    case ND_APP: {
        Term *fun = node_to_term(h, n->ch[0], a);
        Term *arg = node_to_term(h, n->ch[1], a);
        return (fun && arg) ? tm_app(a, fun, arg) : NULL;
    }

    /* Lambda (only handles no-env case) */
    case ND_LAM:
        /* LAM with captured env cannot be serialized without substitution */
        if (n->ch[0] != NULL_REF) return NULL;
        return tm_lam(a, n->name, (Term *)n->aux);

    /* Global / axiom constants */
    case ND_GLOBAL: {
        int idx = n->lvl;
        if (idx >= 0) return tm_global(a, idx);
        if (idx == -1) return tm_ua(a);
        if (idx == -2) return tm_funext(a);
        if (idx == -3) return tm_squash(a);
        return NULL;
    }

    /* Eliminators */
    case ND_FST: {
        Term *s = node_to_term(h, n->ch[0], a);
        return s ? tm_fst(a, s) : NULL;
    }
    case ND_SND: {
        Term *s = node_to_term(h, n->ch[0], a);
        return s ? tm_snd(a, s) : NULL;
    }
    case ND_NATREC: {
        Term *motive = node_to_term(h, n->ch[0], a);
        Term *base   = node_to_term(h, n->ch[1], a);
        Term *step   = node_to_term(h, n->ch[2], a);
        Term *scrut  = node_to_term(h, n->ch[3], a);
        return (motive && base && step && scrut)
               ? tm_natrec(a, motive, base, step, scrut) : NULL;
    }
    case ND_BOOLREC: {
        Term *motive = node_to_term(h, n->ch[0], a);
        Term *tcase  = node_to_term(h, n->ch[1], a);
        Term *fcase  = node_to_term(h, n->ch[2], a);
        Term *scrut  = node_to_term(h, n->ch[3], a);
        return (motive && tcase && fcase && scrut)
               ? tm_boolrec(a, motive, tcase, fcase, scrut) : NULL;
    }
    case ND_S1REC: {
        Term *motive    = node_to_term(h, n->ch[0], a);
        Term *base_case = node_to_term(h, n->ch[1], a);
        Term *loop_case = node_to_term(h, n->ch[2], a);
        Term *scrut     = node_to_term(h, n->ch[3], a);
        return (motive && base_case && loop_case && scrut)
               ? tm_circrec(a, motive, base_case, loop_case, scrut) : NULL;
    }
    case ND_TRUNCREC: {
        Term *ty_a  = node_to_term(h, n->ch[0], a);
        Term *ty_b  = node_to_term(h, n->ch[1], a);
        Term *func  = node_to_term(h, n->ch[2], a);
        Term *scrut = node_to_term(h, n->ch[3], a);
        return (ty_a && ty_b && func && scrut)
               ? tm_truncrec(a, ty_a, ty_b, func, scrut) : NULL;
    }
    case ND_CASESPLIT: {
        Term *motive = node_to_term(h, n->ch[0], a);
        Term *lcase  = node_to_term(h, n->ch[1], a);
        Term *rcase  = node_to_term(h, n->ch[2], a);
        Term *scrut  = node_to_term(h, n->ch[3], a);
        return (motive && lcase && rcase && scrut)
               ? tm_casesplit(a, motive, lcase, rcase, scrut) : NULL;
    }
    case ND_UNITREC: {
        Term *motive = node_to_term(h, n->ch[0], a);
        Term *base   = node_to_term(h, n->ch[1], a);
        Term *scrut  = node_to_term(h, n->ch[2], a);
        return (motive && base && scrut)
               ? tm_unitrec(a, motive, base, scrut) : NULL;
    }
    case ND_ABORT: {
        Term *motive = node_to_term(h, n->ch[0], a);
        Term *scrut  = node_to_term(h, n->ch[1], a);
        return (motive && scrut) ? tm_abort(a, motive, scrut) : NULL;
    }
    case ND_J: {
        Term *ty       = node_to_term(h, n->ch[0], a);
        Term *lhs      = node_to_term(h, n->ch[1], a);
        Term *motive   = node_to_term(h, n->ch[2], a);
        Term *base     = node_to_term(h, n->ch[3], a);
        Term *endpoint = node_to_term(h, n->ch[4], a);
        Term *proof    = node_to_term(h, n->ch[5], a);
        return (ty && lhs && motive && base && endpoint && proof)
               ? tm_j(a, ty, lhs, motive, base, endpoint, proof) : NULL;
    }
    case ND_WREC: {
        Term *motive = node_to_term(h, n->ch[0], a);
        Term *step   = node_to_term(h, n->ch[1], a);
        Term *scrut  = node_to_term(h, n->ch[2], a);
        return (motive && step && scrut)
               ? tm_wrec(a, motive, step, scrut) : NULL;
    }

    /* Core wrapper: quote Val* back to a Term */
    case ND_CORE:
        return nbe_quote(a, 0, (Val *)n->aux);

    /* Cannot serialize */
    case ND_VAR:
    case ND_ENV:
    case ND_BLACKHOLE_TAG:
    default:
        return NULL;
    }
}
