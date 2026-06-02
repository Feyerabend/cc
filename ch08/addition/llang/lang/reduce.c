#include "node.h"
#include "reduce.h"
#include "bridge.h"
#include "../core/arena.h"
#include "../core/term.h"
#include "../core/eval.h"
#include "../core/defs.h"

/* Forward declaration (force <-> term_to_node are in the same file) */
static NodeRef force(Heap *h, Arena *a, NodeRef r);

/* Walk the scrutinee chain of a stuck eliminator to find its head sentinel.
 * Returns the ND_VAR or ND_LOOP NodeRef, or NULL_REF if not a neutral chain. */
static __attribute__((unused)) NodeRef find_sentinel(Heap *h, NodeRef r) {
    r = node_deref(h, r);
    if (r == NULL_REF) return NULL_REF;
    NodeTag tag = (NodeTag)h->nodes[r].tag;
    if (tag == ND_LOOP || tag == ND_VAR) return r;
    if (!node_is_elim_tag(tag))          return NULL_REF;
    return find_sentinel(h, node_scrut_of(h, r));
}

/* 
 * term_to_node - translate a core Term into heap nodes.
 *
 * Bound variables are lazy: TM_LAM stores the unevaluated Term* body
 * plus the current env chain.  Applying the lambda creates a new env
 * node and instantiates the body at force time.
 *
 * TM_APP arguments become ND_THUNK nodes - not forced until demanded.
 * */
NodeRef term_to_node(Heap *h, Arena *a, Term *t, NodeRef env) {
    if (!t) { fprintf(stderr, "term_to_node: NULL\n"); exit(1); }
    switch (t->tag) {

    case TM_VAR:    return env_lookup(h, env, t->idx);
    case TM_LAM:    return mk_lam(h, t->lam.name, env, t->lam.body);
    case TM_APP: {
        NodeRef fun = term_to_node(h, a, t->app.fun, env);
        NodeRef arg = mk_thunk(h, t->app.arg, env);
        return mk_app(h, fun, arg);
    }
    case TM_ANN:    return term_to_node(h, a, t->ann.term, env);

    /* Canonical constructors */
    case TM_ZERO:   return mk_zero(h);
    case TM_SUCC:   return mk_succ(h, mk_thunk(h, t->elim, env));
    case TM_NAT:    return mk_nat(h);
    case TM_TRUE:   return mk_true(h);
    case TM_FALSE:  return mk_false(h);
    case TM_BOOL:   return mk_bool(h);
    case TM_STAR:   return mk_star(h);
    case TM_UNIT:   return mk_unit(h);
    case TM_EMPTY:  return mk_empty(h);
    case TM_PAIR:
        return mk_pair(h,
                       mk_thunk(h, t->pair.fst, env),
                       mk_thunk(h, t->pair.snd, env));
    case TM_REFL:   return mk_refl(h, mk_thunk(h, t->refl, env));
    case TM_INL:    return mk_inl(h, mk_thunk(h, t->elim, env));
    case TM_INR:    return mk_inr(h, mk_thunk(h, t->elim, env));
    case TM_SUM:
        return mk_sum(h,
                      mk_thunk(h, t->sum_t.left, env),
                      mk_thunk(h, t->sum_t.right, env));
    case TM_CIRCLE: return mk_s1(h);
    case TM_BASE:   return mk_base(h);
    case TM_LOOP:   return mk_loop(h);
    case TM_TRUNC:  return mk_trunc(h);
    case TM_TRINT:  return mk_trint(h);
    case TM_SQUASH: return mk_global(h, -3); /* axiom sentinel */
    case TM_QUOT:   return mk_quot(h);
    case TM_QIN:    return mk_qin(h);
    case TM_QEQS:   return mk_global(h, -4);  /* stuck axiom sentinel */
    /* Phase L2 — cubical interval: constants */
    case TM_INTERVAL: return mk_global(h, INTERVAL_CONST_LVL);
    case TM_IZERO:    return mk_global(h, IZERO_CONST_LVL);
    case TM_IONE:     return mk_global(h, IONE_CONST_LVL);
    /* Phase L2 — path/transp/hcomp: evaluate with core NbE.
     * For top-level (env == NULL_REF) call nbe_eval directly.
     * For nested context, force sub-nodes, bridge back to core terms, then eval. */
    case TM_PATH:
    case TM_PATHP:
    case TM_PATHABS:
    case TM_PATHAPP:
    case TM_TRANSP: {
        if (env == NULL_REF) {
            Val *v    = nbe_eval(a, NULL, t);
            Term *nft = nbe_quote(a, 0, v);
            if (nft->tag != t->tag)
                return term_to_node(h, a, nft, NULL_REF);
            return val_to_node(h, v);
        }
        NodeRef fam_ref  = term_to_node(h, a, t->app.fun, env);
        NodeRef elem_ref = term_to_node(h, a, t->app.arg, env);
        nf(h, a, fam_ref);  nf(h, a, elem_ref);
        fam_ref  = node_deref(h, fam_ref);
        elem_ref = node_deref(h, elem_ref);
        Term *fam_t  = node_to_term(h, fam_ref,  a);
        Term *elem_t = node_to_term(h, elem_ref, a);
        if (!fam_t || !elem_t)
            return val_to_node(h, vl_neutral(a, INTERVAL_CONST_LVL, NULL));
        Val *fam_v  = nbe_eval(a, NULL, fam_t);
        Val *elem_v = nbe_eval(a, NULL, elem_t);
        Val *result = nbe_vtransp(a, fam_v, elem_v);
        Term *nft   = nbe_quote(a, 0, result);
        return term_to_node(h, a, nft, NULL_REF);
    }
    case TM_HCOMP: {
        if (env == NULL_REF) {
            Val *v    = nbe_eval(a, NULL, t);
            Term *nft = nbe_quote(a, 0, v);
            if (nft->tag != t->tag)
                return term_to_node(h, a, nft, NULL_REF);
            return val_to_node(h, v);
        }
        /* Nested: normalize all 4 args, bridge to core terms, eval. */
        NodeRef ty_r   = term_to_node(h, a, t->hcomp_t.ty,   env);
        NodeRef face_r = term_to_node(h, a, t->hcomp_t.face, env);
        NodeRef tube_r = term_to_node(h, a, t->hcomp_t.tube, env);
        NodeRef base_r = term_to_node(h, a, t->hcomp_t.base, env);
        nf(h, a, ty_r);  nf(h, a, face_r);
        nf(h, a, tube_r); nf(h, a, base_r);
        ty_r   = node_deref(h, ty_r);
        face_r = node_deref(h, face_r);
        tube_r = node_deref(h, tube_r);
        base_r = node_deref(h, base_r);
        Term *ty_t   = node_to_term(h, ty_r,   a);
        Term *face_t = node_to_term(h, face_r,  a);
        Term *tube_t = node_to_term(h, tube_r,  a);
        Term *base_t = node_to_term(h, base_r,  a);
        if (!ty_t || !face_t || !tube_t || !base_t)
            return val_to_node(h, vl_neutral(a, INTERVAL_CONST_LVL, NULL));
        Val *ty_v   = nbe_eval(a, NULL, ty_t);
        Val *face_v = nbe_eval(a, NULL, face_t);
        Val *tube_v = nbe_eval(a, NULL, tube_t);
        Val *base_v = nbe_eval(a, NULL, base_t);
        Val *result = nbe_vhcomp(a, ty_v, face_v, tube_v, base_v);
        Term *nft   = nbe_quote(a, 0, result);
        return term_to_node(h, a, nft, NULL_REF);
    }
    case TM_COMP: {
        if (env == NULL_REF) {
            Val *v    = nbe_eval(a, NULL, t);
            Term *nft = nbe_quote(a, 0, v);
            if (nft->tag != t->tag)
                return term_to_node(h, a, nft, NULL_REF);
            return val_to_node(h, v);
        }
        NodeRef fam_r  = term_to_node(h, a, t->hcomp_t.ty,   env);
        NodeRef face_r = term_to_node(h, a, t->hcomp_t.face, env);
        NodeRef tube_r = term_to_node(h, a, t->hcomp_t.tube, env);
        NodeRef base_r = term_to_node(h, a, t->hcomp_t.base, env);
        nf(h, a, fam_r);  nf(h, a, face_r);
        nf(h, a, tube_r); nf(h, a, base_r);
        fam_r  = node_deref(h, fam_r);
        face_r = node_deref(h, face_r);
        tube_r = node_deref(h, tube_r);
        base_r = node_deref(h, base_r);
        Term *fam_t  = node_to_term(h, fam_r,  a);
        Term *face_t = node_to_term(h, face_r,  a);
        Term *tube_t = node_to_term(h, tube_r,  a);
        Term *base_t = node_to_term(h, base_r,  a);
        if (!fam_t || !face_t || !tube_t || !base_t)
            return val_to_node(h, vl_neutral(a, INTERVAL_CONST_LVL, NULL));
        Val *fam_v  = nbe_eval(a, NULL, fam_t);
        Val *face_v = nbe_eval(a, NULL, face_t);
        Val *tube_v = nbe_eval(a, NULL, tube_t);
        Val *base_v = nbe_eval(a, NULL, base_t);
        Val *result = nbe_vcomp(a, fam_v, face_v, tube_v, base_v);
        Term *nft   = nbe_quote(a, 0, result);
        return term_to_node(h, a, nft, NULL_REF);
    }
    case TM_FILL: {
        if (env == NULL_REF) {
            Val *v    = nbe_eval(a, NULL, t);
            Term *nft = nbe_quote(a, 0, v);
            return term_to_node(h, a, nft, NULL_REF);
        }
        NodeRef fam_r  = term_to_node(h, a, t->fill_t.fam,  env);
        NodeRef face_r = term_to_node(h, a, t->fill_t.face, env);
        NodeRef tube_r = term_to_node(h, a, t->fill_t.tube, env);
        NodeRef base_r = term_to_node(h, a, t->fill_t.base, env);
        NodeRef idx_r  = term_to_node(h, a, t->fill_t.idx,  env);
        nf(h, a, fam_r);  nf(h, a, face_r);
        nf(h, a, tube_r); nf(h, a, base_r); nf(h, a, idx_r);
        fam_r  = node_deref(h, fam_r);
        face_r = node_deref(h, face_r);
        tube_r = node_deref(h, tube_r);
        base_r = node_deref(h, base_r);
        idx_r  = node_deref(h, idx_r);
        Term *fam_t  = node_to_term(h, fam_r,  a);
        Term *face_t = node_to_term(h, face_r,  a);
        Term *tube_t = node_to_term(h, tube_r,  a);
        Term *base_t = node_to_term(h, base_r,  a);
        Term *idx_t  = node_to_term(h, idx_r,   a);
        if (!fam_t || !face_t || !tube_t || !base_t || !idx_t)
            return val_to_node(h, vl_neutral(a, INTERVAL_CONST_LVL, NULL));
        Val *fam_v  = nbe_eval(a, NULL, fam_t);
        Val *face_v = nbe_eval(a, NULL, face_t);
        Val *tube_v = nbe_eval(a, NULL, tube_t);
        Val *base_v = nbe_eval(a, NULL, base_t);
        Val *idx_v  = nbe_eval(a, NULL, idx_t);
        Val *result = nbe_vfill(a, fam_v, face_v, tube_v, base_v, idx_v);
        Term *nft   = nbe_quote(a, 0, result);
        return term_to_node(h, a, nft, NULL_REF);
    }
    case TM_GLUE: {
        if (env == NULL_REF) {
            Val *v    = nbe_eval(a, NULL, t);
            Term *nft = nbe_quote(a, 0, v);
            if (nft->tag != t->tag)
                return term_to_node(h, a, nft, NULL_REF);
            return val_to_node(h, v);
        }
        /* Nested: normalize all 4 args, bridge to core terms, eval. */
        NodeRef base_r  = term_to_node(h, a, t->glue_t.base,  env);
        NodeRef face_r  = term_to_node(h, a, t->glue_t.face,  env);
        NodeRef fiber_r = term_to_node(h, a, t->glue_t.fiber, env);
        NodeRef equiv_r = term_to_node(h, a, t->glue_t.equiv, env);
        nf(h, a, base_r);  nf(h, a, face_r);
        nf(h, a, fiber_r); nf(h, a, equiv_r);
        base_r  = node_deref(h, base_r);
        face_r  = node_deref(h, face_r);
        fiber_r = node_deref(h, fiber_r);
        equiv_r = node_deref(h, equiv_r);
        Term *base_t  = node_to_term(h, base_r,  a);
        Term *face_t  = node_to_term(h, face_r,  a);
        Term *fiber_t = node_to_term(h, fiber_r, a);
        Term *equiv_t = node_to_term(h, equiv_r, a);
        if (!base_t || !face_t || !fiber_t || !equiv_t)
            return val_to_node(h, vl_neutral(a, INTERVAL_CONST_LVL, NULL));
        Val *base_v  = nbe_eval(a, NULL, base_t);
        Val *face_v  = nbe_eval(a, NULL, face_t);
        Val *fiber_v = nbe_eval(a, NULL, fiber_t);
        Val *equiv_v = nbe_eval(a, NULL, equiv_t);
        Val *result  = nbe_vglue_ty(a, base_v, face_v, fiber_v, equiv_v);
        Term *nft    = nbe_quote(a, 0, result);
        return term_to_node(h, a, nft, NULL_REF);
    }
    /* Phase L2 Stage 6 — interval operations: imin/imax/ineg.
     * All evaluate via core NbE (same pattern as TM_GLUE). */
    case TM_IMIN:
    case TM_IMAX: {
        if (env == NULL_REF) {
            Val *v    = nbe_eval(a, NULL, t);
            Term *nft = nbe_quote(a, 0, v);
            if (nft->tag != t->tag)
                return term_to_node(h, a, nft, NULL_REF);
            return val_to_node(h, v);
        }
        NodeRef l_r = term_to_node(h, a, t->app.fun, env);
        NodeRef r_r = term_to_node(h, a, t->app.arg, env);
        nf(h, a, l_r); nf(h, a, r_r);
        l_r = node_deref(h, l_r); r_r = node_deref(h, r_r);
        Term *l_t = node_to_term(h, l_r, a);
        Term *r_t = node_to_term(h, r_r, a);
        if (!l_t || !r_t)
            return val_to_node(h, vl_neutral(a, INTERVAL_CONST_LVL, NULL));
        Val *l_v = nbe_eval(a, NULL, l_t);
        Val *r_v = nbe_eval(a, NULL, r_t);
        Val *res = (t->tag == TM_IMIN) ? nbe_vimin(a, l_v, r_v)
                                        : nbe_vimax(a, l_v, r_v);
        Term *nft = nbe_quote(a, 0, res);
        return term_to_node(h, a, nft, NULL_REF);
    }
    case TM_INEG: {
        if (env == NULL_REF) {
            Val *v    = nbe_eval(a, NULL, t);
            Term *nft = nbe_quote(a, 0, v);
            if (nft->tag != t->tag)
                return term_to_node(h, a, nft, NULL_REF);
            return val_to_node(h, v);
        }
        NodeRef v_r = term_to_node(h, a, t->elim, env);
        nf(h, a, v_r); v_r = node_deref(h, v_r);
        Term *v_t = node_to_term(h, v_r, a);
        if (!v_t)
            return val_to_node(h, vl_neutral(a, INTERVAL_CONST_LVL, NULL));
        Val *v_v  = nbe_eval(a, NULL, v_t);
        Val *res  = nbe_vineg(a, v_v);
        Term *nft = nbe_quote(a, 0, res);
        return term_to_node(h, a, nft, NULL_REF);
    }
    /* Phase L2 Stage 7 — IsOne φ: evaluate face, apply IsOne β-rules */
    case TM_ISONE: {
        NodeRef face_r = term_to_node(h, a, t->elim, env);
        nf(h, a, face_r); face_r = node_deref(h, face_r);
        Term *face_t = node_to_term(h, face_r, a);
        Val *face_v = face_t ? nbe_eval(a, NULL, face_t)
                             : vl_neutral(a, INTERVAL_CONST_LVL, NULL);
        Val *res  = nbe_visone(a, face_v);
        Term *nft = nbe_quote(a, 0, res);
        if (nft->tag != TM_ISONE)
            return term_to_node(h, a, nft, NULL_REF);
        return val_to_node(h, res);
    }
    /* Phase L2 Stage 7d — glue intro / unglue elim: evaluate via core NbE */
    case TM_GLUEELEM: {
        if (env == NULL_REF) {
            Val *v    = nbe_eval(a, NULL, t);
            Term *nft = nbe_quote(a, 0, v);
            if (nft->tag != t->tag) return term_to_node(h, a, nft, NULL_REF);
            return val_to_node(h, v);
        }
        NodeRef face_r    = term_to_node(h, a, t->glue_elem_t.face,    env);
        NodeRef partial_r = term_to_node(h, a, t->glue_elem_t.partial, env);
        NodeRef base_r    = term_to_node(h, a, t->glue_elem_t.base,    env);
        nf(h, a, face_r); nf(h, a, partial_r); nf(h, a, base_r);
        face_r    = node_deref(h, face_r);
        partial_r = node_deref(h, partial_r);
        base_r    = node_deref(h, base_r);
        Term *face_t    = node_to_term(h, face_r,    a);
        Term *partial_t = node_to_term(h, partial_r, a);
        Term *base_t    = node_to_term(h, base_r,    a);
        if (!face_t || !partial_t || !base_t)
            return val_to_node(h, vl_neutral(a, INTERVAL_CONST_LVL, NULL));
        Val *result = nbe_vglueelem(a, nbe_eval(a, NULL, face_t),
                                       nbe_eval(a, NULL, partial_t),
                                       nbe_eval(a, NULL, base_t));
        Term *nft = nbe_quote(a, 0, result);
        return term_to_node(h, a, nft, NULL_REF);
    }
    case TM_UNGLUE: {
        if (env == NULL_REF) {
            Val *v    = nbe_eval(a, NULL, t);
            Term *nft = nbe_quote(a, 0, v);
            if (nft->tag != t->tag) return term_to_node(h, a, nft, NULL_REF);
            return val_to_node(h, v);
        }
        NodeRef face_r  = term_to_node(h, a, t->unglue_t.face,  env);
        NodeRef equiv_r = term_to_node(h, a, t->unglue_t.equiv, env);
        NodeRef elem_r  = term_to_node(h, a, t->unglue_t.elem,  env);
        nf(h, a, face_r); nf(h, a, equiv_r); nf(h, a, elem_r);
        face_r  = node_deref(h, face_r);
        equiv_r = node_deref(h, equiv_r);
        elem_r  = node_deref(h, elem_r);
        Term *face_t  = node_to_term(h, face_r,  a);
        Term *equiv_t = node_to_term(h, equiv_r, a);
        Term *elem_t  = node_to_term(h, elem_r,  a);
        if (!face_t || !equiv_t || !elem_t)
            return val_to_node(h, vl_neutral(a, INTERVAL_CONST_LVL, NULL));
        Val *result = nbe_vunglue(a, nbe_eval(a, NULL, face_t),
                                     nbe_eval(a, NULL, equiv_t),
                                     nbe_eval(a, NULL, elem_t));
        Term *nft = nbe_quote(a, 0, result);
        return term_to_node(h, a, nft, NULL_REF);
    }
    case TM_PRIMSUB: {
        if (env == NULL_REF) {
            Val *v    = nbe_eval(a, NULL, t);
            Term *nft = nbe_quote(a, 0, v);
            if (nft->tag != t->tag) return term_to_node(h, a, nft, NULL_REF);
            return val_to_node(h, v);
        }
        NodeRef ty_r   = term_to_node(h, a, t->primsub_t.ty,   env);
        NodeRef face_r = term_to_node(h, a, t->primsub_t.face, env);
        NodeRef u_r    = term_to_node(h, a, t->primsub_t.u,    env);
        NodeRef out_r  = term_to_node(h, a, t->primsub_t.a,    env);
        nf(h, a, ty_r); nf(h, a, face_r); nf(h, a, u_r); nf(h, a, out_r);
        ty_r   = node_deref(h, ty_r);
        face_r = node_deref(h, face_r);
        u_r    = node_deref(h, u_r);
        out_r  = node_deref(h, out_r);
        Term *ty_t   = node_to_term(h, ty_r,   a);
        Term *face_t = node_to_term(h, face_r,  a);
        Term *u_t    = node_to_term(h, u_r,     a);
        Term *out_t  = node_to_term(h, out_r,   a);
        if (!ty_t || !face_t || !u_t || !out_t)
            return val_to_node(h, vl_neutral(a, INTERVAL_CONST_LVL, NULL));
        Val *result = nbe_vprimsub(a, nbe_eval(a, NULL, ty_t),
                                      nbe_eval(a, NULL, face_t),
                                      nbe_eval(a, NULL, u_t),
                                      nbe_eval(a, NULL, out_t));
        Term *nft = nbe_quote(a, 0, result);
        return term_to_node(h, a, nft, NULL_REF);
    }
    case TM_QUOTREC: {
        NodeRef r2 = heap_alloc(h);
        h->nodes[r2].tag   = ND_QUOTREC;
        h->nodes[r2].flags = 0;
        h->nodes[r2].ch[0] = mk_thunk(h, t->quotrec_t.ty_a,  env);
        h->nodes[r2].ch[1] = mk_thunk(h, t->quotrec_t.rel,   env);
        h->nodes[r2].ch[2] = mk_thunk(h, t->quotrec_t.ty_b,  env);
        h->nodes[r2].ch[3] = mk_thunk(h, t->quotrec_t.func,  env);
        h->nodes[r2].ch[4] = mk_thunk(h, t->quotrec_t.coh,   env);
        h->nodes[r2].ch[5] = mk_thunk(h, t->quotrec_t.scrut, env);
        return r2;
    }
    case TM_UNI:    return mk_uni(h, t->ulevel);
    case TM_UA:     return mk_global(h, -1);   /* axiom sentinel */
    case TM_FUNEXT: return mk_global(h, -2);   /* axiom sentinel */

    /* Types (lazy thunks for cod, since binder is in scope) */
    case TM_PI: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_PI;
        h->nodes[r].flags = NF_WHNF;
        h->nodes[r].ch[0] = mk_thunk(h, t->pi.dom, env);
        h->nodes[r].ch[1] = mk_thunk(h, t->pi.cod, env);
        h->nodes[r].name  = t->pi.name;
        return r;
    }
    case TM_SIG: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_SIGMA;
        h->nodes[r].flags = NF_WHNF;
        h->nodes[r].ch[0] = mk_thunk(h, t->pi.dom, env);
        h->nodes[r].ch[1] = mk_thunk(h, t->pi.cod, env);
        h->nodes[r].name  = t->pi.name;
        return r;
    }
    case TM_ID: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_ID;
        h->nodes[r].flags = NF_WHNF;
        h->nodes[r].ch[0] = mk_thunk(h, t->id.ty,  env);
        h->nodes[r].ch[1] = mk_thunk(h, t->id.lhs, env);
        h->nodes[r].ch[2] = mk_thunk(h, t->id.rhs, env);
        return r;
    }
    case TM_W: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_W;
        h->nodes[r].flags = NF_WHNF;
        h->nodes[r].ch[0] = mk_thunk(h, t->pi.dom, env);
        h->nodes[r].ch[1] = mk_thunk(h, t->pi.cod, env);
        h->nodes[r].name  = t->pi.name;
        return r;
    }

    /* Eliminators */
    case TM_FST: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_FST;
        h->nodes[r].ch[0] = mk_thunk(h, t->elim, env);
        return r;
    }
    case TM_SND: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_SND;
        h->nodes[r].ch[0] = mk_thunk(h, t->elim, env);
        return r;
    }
    case TM_NATREC: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_NATREC;
        h->nodes[r].ch[0] = mk_thunk(h, t->natrec.motive, env);
        h->nodes[r].ch[1] = mk_thunk(h, t->natrec.base,   env);
        h->nodes[r].ch[2] = mk_thunk(h, t->natrec.step,   env);
        h->nodes[r].ch[3] = mk_thunk(h, t->natrec.scrut,  env);
        return r;
    }
    case TM_BOOLREC: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_BOOLREC;
        h->nodes[r].ch[0] = mk_thunk(h, t->boolrec.motive, env);
        h->nodes[r].ch[1] = mk_thunk(h, t->boolrec.tcase,  env);
        h->nodes[r].ch[2] = mk_thunk(h, t->boolrec.fcase,  env);
        h->nodes[r].ch[3] = mk_thunk(h, t->boolrec.scrut,  env);
        return r;
    }
    case TM_CASESPLIT: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_CASESPLIT;
        h->nodes[r].ch[0] = mk_thunk(h, t->casesplit_t.motive, env);
        h->nodes[r].ch[1] = mk_thunk(h, t->casesplit_t.lcase,  env);
        h->nodes[r].ch[2] = mk_thunk(h, t->casesplit_t.rcase,  env);
        h->nodes[r].ch[3] = mk_thunk(h, t->casesplit_t.scrut,  env);
        return r;
    }
    case TM_ABORT: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_ABORT;
        h->nodes[r].ch[0] = mk_thunk(h, t->abort_t.motive, env);
        h->nodes[r].ch[1] = mk_thunk(h, t->abort_t.scrut,  env);
        return r;
    }
    case TM_UNITREC: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_UNITREC;
        h->nodes[r].ch[0] = mk_thunk(h, t->unitrec_t.motive, env);
        h->nodes[r].ch[1] = mk_thunk(h, t->unitrec_t.base,   env);
        h->nodes[r].ch[2] = mk_thunk(h, t->unitrec_t.scrut,  env);
        return r;
    }
    case TM_TRUNCREC: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_TRUNCREC;
        h->nodes[r].ch[0] = mk_thunk(h, t->truncrec_t.ty_a,  env);
        h->nodes[r].ch[1] = mk_thunk(h, t->truncrec_t.ty_b,  env);
        h->nodes[r].ch[2] = mk_thunk(h, t->truncrec_t.func,  env);
        h->nodes[r].ch[3] = mk_thunk(h, t->truncrec_t.scrut, env);
        return r;
    }
    case TM_CIRCREC: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_S1REC;
        h->nodes[r].ch[0] = mk_thunk(h, t->circrec_t.motive,    env);
        h->nodes[r].ch[1] = mk_thunk(h, t->circrec_t.base_case, env);
        h->nodes[r].ch[2] = mk_thunk(h, t->circrec_t.loop_case, env);
        h->nodes[r].ch[3] = mk_thunk(h, t->circrec_t.scrut,     env);
        return r;
    }
    case TM_J: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_J;
        h->nodes[r].ch[0] = mk_thunk(h, t->j.ty,       env);
        h->nodes[r].ch[1] = mk_thunk(h, t->j.lhs,      env);
        h->nodes[r].ch[2] = mk_thunk(h, t->j.motive,   env);
        h->nodes[r].ch[3] = mk_thunk(h, t->j.base,     env);
        h->nodes[r].ch[4] = mk_thunk(h, t->j.endpoint, env);
        h->nodes[r].ch[5] = mk_thunk(h, t->j.proof,    env);
        return r;
    }
    case TM_SUP: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_SUP;
        h->nodes[r].flags = NF_WHNF;
        h->nodes[r].ch[0] = mk_thunk(h, t->sup.label,    env);
        h->nodes[r].ch[1] = mk_thunk(h, t->sup.children, env);
        return r;
    }
    case TM_WREC: {
        NodeRef r = heap_alloc(h);
        h->nodes[r].tag   = ND_WREC;
        h->nodes[r].ch[0] = mk_thunk(h, t->wrec.motive, env);
        h->nodes[r].ch[1] = mk_thunk(h, t->wrec.step,   env);
        h->nodes[r].ch[2] = mk_thunk(h, t->wrec.scrut,  env);
        return r;
    }

    case TM_GLOBAL: return mk_global(h, t->idx);

    case TM_INDTYPE: {
        int n = t->indtype.n_args;
        if (n > NODE_MAX_CHILDREN) {
            fprintf(stderr, "term_to_node: ND_INDTYPE: too many params (%d, max %d)\n", n, NODE_MAX_CHILDREN);
            exit(1);
        }
        NodeRef r2 = heap_alloc(h);
        h->nodes[r2].tag   = ND_INDTYPE;
        h->nodes[r2].flags = NF_WHNF;
        h->nodes[r2].lvl   = t->indtype.fam_idx;
        for (int i = 0; i < n; i++)
            h->nodes[r2].ch[i] = mk_thunk(h, t->indtype.args[i], env);
        return r2;
    }
    case TM_INDCON: {
        int n = t->indcon.n_args;
        if (n > NODE_MAX_CHILDREN) {
            fprintf(stderr, "term_to_node: ND_INDCON: too many args (%d, max %d)\n", n, NODE_MAX_CHILDREN);
            exit(1);
        }
        NodeRef r2 = heap_alloc(h);
        h->nodes[r2].tag   = ND_INDCON;
        h->nodes[r2].flags = NF_WHNF;
        h->nodes[r2].lvl   = ((t->indcon.fam_idx & 0xFFFF) << 16) |
                              (t->indcon.ctor_idx & 0xFFFF);
        for (int i = 0; i < n; i++)
            h->nodes[r2].ch[i] = mk_thunk(h, t->indcon.args[i], env);
        return r2;
    }
    case TM_INDREC: {
        int n = t->indrec.n_cases;
        if (n > ND_MAX_CASES) {
            fprintf(stderr, "term_to_node: ND_INDREC: too many cases (%d, max %d)\n", n, ND_MAX_CASES);
            exit(1);
        }
        NodeRef r2 = heap_alloc(h);
        h->nodes[r2].tag   = ND_INDREC;
        h->nodes[r2].flags = 0;
        h->nodes[r2].lvl   = t->indrec.fam_idx;
        h->nodes[r2].ch[0] = mk_thunk(h, t->indrec.scrut, env);
        h->nodes[r2].ch[1] = t->indrec.motive
                             ? mk_thunk(h, t->indrec.motive, env) : NULL_REF;
        for (int i = 0; i < n; i++)
            h->nodes[r2].ch[2+i] = mk_thunk(h, t->indrec.cases[i], env);
        return r2;
    }

    case TM_FIX: {
        NodeRef r2 = heap_alloc(h);
        h->nodes[r2].tag   = ND_FIX;
        h->nodes[r2].flags = 0;
        h->nodes[r2].ch[0] = mk_thunk(h, t->fix.body, env);
        return r2;
    }

    /* Phase M1 — level terms (WHNF constants, never reduce) */
    case TM_LEVEL: { NodeRef r2 = heap_alloc(h); h->nodes[r2].tag = ND_LEVEL; h->nodes[r2].flags = NF_WHNF | NF_NF; return r2; }
    case TM_LZERO: { NodeRef r2 = heap_alloc(h); h->nodes[r2].tag = ND_LZERO; h->nodes[r2].flags = NF_WHNF | NF_NF; return r2; }
    case TM_LSUC: {
        NodeRef r2 = heap_alloc(h);
        h->nodes[r2].tag   = ND_LSUC;
        h->nodes[r2].flags = NF_WHNF;
        h->nodes[r2].ch[0] = mk_thunk(h, t->elim, env);
        return r2;
    }
    case TM_LMAX: {
        if (env == NULL_REF) {
            Val *v    = nbe_eval(a, NULL, t);
            Term *nft = nbe_quote(a, 0, v);
            if (nft->tag != TM_LMAX)
                return term_to_node(h, a, nft, NULL_REF);
            return val_to_node(h, v);
        }
        NodeRef l_r = term_to_node(h, a, t->app.fun, env);
        NodeRef r_r = term_to_node(h, a, t->app.arg, env);
        nf(h, a, l_r); nf(h, a, r_r);
        l_r = node_deref(h, l_r); r_r = node_deref(h, r_r);
        Term *l_t = node_to_term(h, l_r, a);
        Term *r_t = node_to_term(h, r_r, a);
        if (!l_t || !r_t)
            return val_to_node(h, vl_neutral(a, 0, NULL));
        Val *l_v = nbe_eval(a, NULL, l_t);
        Val *r_v = nbe_eval(a, NULL, r_t);
        Val *res = nbe_vlmax(a, l_v, r_v);
        Term *nft = nbe_quote(a, 0, res);
        return term_to_node(h, a, nft, NULL_REF);
    }
    case TM_UNI_V: {
        NodeRef r2 = heap_alloc(h);
        h->nodes[r2].tag   = ND_UNI_V;
        h->nodes[r2].flags = NF_WHNF;
        h->nodes[r2].ch[0] = mk_thunk(h, t->uni_v_lvl, env);
        return r2;
    }

    /* Phase M4 — pattern matching: normalize scrutinee, find arm, eval body */
    case TM_MATCH: {
        NodeRef scrut_r = term_to_node(h, a, t->match_s.scrut, env);
        nf(h, a, scrut_r);
        scrut_r = node_deref(h, scrut_r);
        Term *scrut_t = node_to_term(h, scrut_r, a);
        if (!scrut_t) {
            /* Scrutinee stuck — return as core Val */
            Val *v = nbe_eval(a, NULL, t);
            return val_to_node(h, v);
        }
        Val *scrut_v = nbe_eval(a, NULL, scrut_t);
        int fam_idx = t->match_s.fam_idx;
        int n_arms  = t->match_s.n_arms;
        MatchArm *arms = t->match_s.arms;
        int ai = -1;
        NodeRef arm_env = env;
        if (fam_idx == -1) { /* Nat */
            if (scrut_v->tag == VL_ZERO) {
                for (int i = 0; i < n_arms; i++) if (arms[i].ctor_idx == 0) { ai = i; break; }
            } else if (scrut_v->tag == VL_SUCC) {
                for (int i = 0; i < n_arms; i++) if (arms[i].ctor_idx == 1) { ai = i; break; }
                if (ai >= 0 && arms[ai].n_binds > 0)
                    arm_env = mk_env(h, val_to_node(h, scrut_v->succ), arm_env);
            }
        } else if (fam_idx == -2) { /* Bool */
            if (scrut_v->tag == VL_TRUE)  for (int i = 0; i < n_arms; i++) if (arms[i].ctor_idx == 0) { ai = i; break; }
            if (scrut_v->tag == VL_FALSE) for (int i = 0; i < n_arms; i++) if (arms[i].ctor_idx == 1) { ai = i; break; }
        } else { /* User inductive */
            IndDef *fam = ind_get(fam_idx);
            if (scrut_v->tag == VL_INDCON && scrut_v->indcon.fam_idx == fam_idx) {
                int k = scrut_v->indcon.ctor_idx;
                for (int i = 0; i < n_arms; i++) if (arms[i].ctor_idx == k) { ai = i; break; }
                if (ai >= 0) {
                    int n_params = fam->n_params;
                    int arity = arms[ai].n_binds;
                    for (int j = 0; j < arity; j++)
                        arm_env = mk_env(h, val_to_node(h, scrut_v->indcon.args[n_params + j]), arm_env);
                }
            }
        }
        if (ai < 0) {
            Val *v = nbe_eval(a, NULL, scrut_t);
            return val_to_node(h, v);
        }
        return term_to_node(h, a, arms[ai].body, arm_env);
    }

    default:
        fprintf(stderr, "term_to_node: unhandled tag %d\n", (int)t->tag);
        exit(1);
    }
}

/*
 * force - bring a node to WHNF.
 *
 * Reduction rules:
 *   β:  APP(LAM(env, body), arg) → instantiate body with env+arg
 *   δ:  APP(GLOBAL(idx), arg)    → unfold global via core's nbe_quote
 *   θ:  THUNK(expr, env)         → translate expr with env, then force
 *   ι:  eliminators on matching constructors (natrec/boolrec/fst/snd/
 *       case/unitrec/J/S1rec/truncrec)
 *
 * Stuck nodes (scrutinee is a sentinel or open neutral) are marked
 * WHNF in-place without overwriting with ND_REF (r2 == r would be
 * a self-referential indirection).
 * */
static NodeRef force(Heap *h, Arena *a, NodeRef r) {
    r = node_deref(h, r);
    if (r == NULL_REF) { fprintf(stderr, "force: NULL_REF\n"); exit(1); }
    if (h->nodes[r].flags & NF_WHNF)      return r;
    if (h->nodes[r].flags & NF_BLACKHOLE) {
        fprintf(stderr, "force: infinite loop (blackhole at node %u)\n", r);
        node_dump_graph(h);
        exit(1);
    }
    h->nodes[r].flags |= NF_BLACKHOLE;

    NodeTag tag = (NodeTag)h->nodes[r].tag;

    /* θ: thunk instantiation */
    if (tag == ND_THUNK) {
        Term   *expr = (Term *)h->nodes[r].aux;
        NodeRef env  = h->nodes[r].ch[0];
        NodeRef res  = term_to_node(h, a, expr, env);
        NodeRef r2   = force(h, a, res);
        h->nodes[r].tag   = ND_REF;
        h->nodes[r].flags = NF_WHNF;
        h->nodes[r].ch[0] = r2;
        h->nodes[r].aux   = NULL;
        return r2;
    }

    /* β / δ: application */
    if (tag == ND_APP) {
        NodeRef fun_ref = h->nodes[r].ch[0];
        NodeRef arg_ref = h->nodes[r].ch[1];  /* stable NodeRef - safe across alloc */
        NodeRef fun     = force(h, a, fun_ref);
        NodeTag ftag    = (NodeTag)h->nodes[fun].tag;

        if (ftag == ND_LAM) {
            /* β-reduction */
            void   *body    = h->nodes[fun].aux;
            NodeRef lam_env = h->nodes[fun].ch[0];
            NodeRef new_env = mk_env(h, arg_ref, lam_env);
            NodeRef body_r  = term_to_node(h, a, (Term *)body, new_env);
            NodeRef r2      = force(h, a, body_r);
            h->nodes[r].tag   = ND_REF;
            h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = r2;
            h->nodes[r].aux   = NULL;
            return r2;
        }

        if (ftag == ND_GLOBAL && h->nodes[fun].lvl >= 0) {
            /* δ: unfold global via core's quote, then re-apply */
            int  idx = h->nodes[fun].lvl;
            Def *def = def_get(idx);
            if (!def) { fprintf(stderr, "force: invalid global %d\n", idx); exit(1); }
            Term   *dt   = nbe_quote(a, 0, def->val);
            NodeRef dn   = term_to_node(h, a, dt, NULL_REF);
            NodeRef app2 = mk_app(h, dn, arg_ref);
            NodeRef r2   = force(h, a, app2);
            h->nodes[r].tag   = ND_REF;
            h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = r2;
            h->nodes[r].aux   = NULL;
            return r2;
        }

        if (ftag == ND_FIX) {
            /* ι-rule: (fix f) arg → (f (fix f)) arg */
            NodeRef f    = h->nodes[fun].ch[0];
            NodeRef self = heap_alloc(h);
            h->nodes[self].tag   = ND_FIX;
            h->nodes[self].flags = 0;
            h->nodes[self].ch[0] = f;
            NodeRef app1 = mk_app(h, f, self);       /* f (fix f) */
            NodeRef app2 = mk_app(h, app1, arg_ref);  /* (f (fix f)) arg */
            NodeRef r2   = force(h, a, app2);
            h->nodes[r].tag   = ND_REF;
            h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = r2;
            h->nodes[r].aux   = NULL;
            return r2;
        }

        if (ftag == ND_CORE) {
            /* ND_CORE wraps a core Val* (e.g. stuck transp/hcomp or a VL_LAM from
             * a core-NbE path).  Apply via core NbE: bridge arg, nbe_vapp, re-translate. */
            Val *fun_val = (Val *)h->nodes[fun].aux;
            nf(h, a, arg_ref);
            NodeRef arg_nf = node_deref(h, arg_ref);
            Term   *arg_t  = node_to_term(h, arg_nf, a);
            if (arg_t) {
                Val  *arg_v = nbe_eval(a, NULL, arg_t);
                Val  *res   = nbe_vapp(a, fun_val, arg_v);
                Term *res_t = nbe_quote(a, 0, res);
                NodeRef r2  = force(h, a, term_to_node(h, a, res_t, NULL_REF));
                h->nodes[r].tag   = ND_REF;
                h->nodes[r].flags = NF_WHNF;
                h->nodes[r].ch[0] = r2;
                h->nodes[r].aux   = NULL;
                return r2;
            }
            /* arg not bridgeable — stay stuck */
        }

        /* Stuck: fun is not a LAM or unfoldable GLOBAL or FIX or applicable CORE */
        h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
        return r;
    }

    /* Global in non-application position */
    if (tag == ND_GLOBAL) {
        int idx = h->nodes[r].lvl;
        if (idx < 0) {
            /* Axiom constant: ua, funext, squash - permanently stuck */
            h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
            return r;
        }
        Def *def = def_get(idx);
        if (!def) { fprintf(stderr, "force: invalid global %d\n", idx); exit(1); }
        Term   *dt = nbe_quote(a, 0, def->val);
        NodeRef dn = term_to_node(h, a, dt, NULL_REF);
        NodeRef r2 = force(h, a, dn);
        h->nodes[r].tag   = ND_REF;
        h->nodes[r].flags = NF_WHNF;
        h->nodes[r].ch[0] = r2;
        h->nodes[r].aux   = NULL;
        return r2;
    }

    /* ι-rules */

    if (tag == ND_FST) {
        NodeRef scrut = force(h, a, h->nodes[r].ch[0]);
        if (h->nodes[scrut].tag == ND_PAIR) {
            NodeRef r2 = h->nodes[scrut].ch[0];
            h->nodes[r].tag = ND_REF; h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = r2; h->nodes[r].aux = NULL;
            return force(h, a, r2);
        }
        h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
        return r;
    }

    if (tag == ND_SND) {
        NodeRef scrut = force(h, a, h->nodes[r].ch[0]);
        if (h->nodes[scrut].tag == ND_PAIR) {
            NodeRef r2 = h->nodes[scrut].ch[1];
            h->nodes[r].tag = ND_REF; h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = r2; h->nodes[r].aux = NULL;
            return force(h, a, r2);
        }
        h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
        return r;
    }

    if (tag == ND_NATREC) {
        NodeRef motive = h->nodes[r].ch[0];
        NodeRef base   = h->nodes[r].ch[1];
        NodeRef step   = h->nodes[r].ch[2];
        NodeRef scrut  = force(h, a, h->nodes[r].ch[3]);
        if (h->nodes[scrut].tag == ND_ZERO) {
            h->nodes[r].tag = ND_REF; h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = base; h->nodes[r].aux = NULL;
            return force(h, a, base);
        }
        if (h->nodes[scrut].tag == ND_SUCC) {
            NodeRef n   = h->nodes[scrut].ch[0];
            NodeRef rec = heap_alloc(h);
            h->nodes[rec].tag   = ND_NATREC;
            h->nodes[rec].ch[0] = motive;
            h->nodes[rec].ch[1] = base;
            h->nodes[rec].ch[2] = step;
            h->nodes[rec].ch[3] = n;
            NodeRef r2 = mk_app(h, mk_app(h, step, n), rec);
            h->nodes[r].tag = ND_REF; h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = r2; h->nodes[r].aux = NULL;
            return force(h, a, r2);
        }
        h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
        return r;
    }

    if (tag == ND_BOOLREC) {
        NodeRef tcase  = h->nodes[r].ch[1];
        NodeRef fcase  = h->nodes[r].ch[2];
        NodeRef scrut  = force(h, a, h->nodes[r].ch[3]);
        if (h->nodes[scrut].tag == ND_TRUE) {
            h->nodes[r].tag = ND_REF; h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = tcase; h->nodes[r].aux = NULL;
            return force(h, a, tcase);
        }
        if (h->nodes[scrut].tag == ND_FALSE) {
            h->nodes[r].tag = ND_REF; h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = fcase; h->nodes[r].aux = NULL;
            return force(h, a, fcase);
        }
        h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
        return r;
    }

    if (tag == ND_CASESPLIT) {
        NodeRef lcase  = h->nodes[r].ch[1];
        NodeRef rcase  = h->nodes[r].ch[2];
        NodeRef scrut  = force(h, a, h->nodes[r].ch[3]);
        if (h->nodes[scrut].tag == ND_INL) {
            NodeRef inner = h->nodes[scrut].ch[0];
            NodeRef r2 = mk_app(h, lcase, inner);
            h->nodes[r].tag = ND_REF; h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = r2; h->nodes[r].aux = NULL;
            return force(h, a, r2);
        }
        if (h->nodes[scrut].tag == ND_INR) {
            NodeRef inner = h->nodes[scrut].ch[0];
            NodeRef r2 = mk_app(h, rcase, inner);
            h->nodes[r].tag = ND_REF; h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = r2; h->nodes[r].aux = NULL;
            return force(h, a, r2);
        }
        h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
        return r;
    }

    if (tag == ND_UNITREC) {
        NodeRef base   = h->nodes[r].ch[1];
        NodeRef scrut  = force(h, a, h->nodes[r].ch[2]);
        if (h->nodes[scrut].tag == ND_STAR) {
            h->nodes[r].tag = ND_REF; h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = base; h->nodes[r].aux = NULL;
            return force(h, a, base);
        }
        h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
        return r;
    }

    if (tag == ND_J) {
        NodeRef base  = h->nodes[r].ch[3];
        NodeRef proof = force(h, a, h->nodes[r].ch[5]);
        if (h->nodes[proof].tag == ND_REFL) {
            h->nodes[r].tag = ND_REF; h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = base; h->nodes[r].aux = NULL;
            return force(h, a, base);
        }
        h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
        return r;
    }

    if (tag == ND_S1REC) {
        NodeRef base_case = h->nodes[r].ch[1];
        NodeRef scrut     = force(h, a, h->nodes[r].ch[3]);
        if (h->nodes[scrut].tag == ND_BASE) {
            h->nodes[r].tag = ND_REF; h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = base_case; h->nodes[r].aux = NULL;
            return force(h, a, base_case);
        }
        h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
        return r;
    }

    if (tag == ND_TRUNCREC) {
        NodeRef func  = h->nodes[r].ch[2];
        NodeRef scrut = force(h, a, h->nodes[r].ch[3]);
        /* trint is a bare constant; "trint a" is APP(ND_TRINT, a) */
        if (h->nodes[scrut].tag == ND_APP) {
            NodeRef fn = node_deref(h, h->nodes[scrut].ch[0]);
            if (h->nodes[fn].tag == ND_TRINT) {
                NodeRef inner = h->nodes[scrut].ch[1];
                NodeRef r2 = mk_app(h, func, inner);
                h->nodes[r].tag = ND_REF; h->nodes[r].flags = NF_WHNF;
                h->nodes[r].ch[0] = r2; h->nodes[r].aux = NULL;
                return force(h, a, r2);
            }
        }
        h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
        return r;
    }

    if (tag == ND_QUOTREC) {
        /* β-rule: quotrec A R B f coh (qin A R a) → f a
         * qin A R a = APP(APP(APP(ND_QIN, A), R), a)  */
        NodeRef scrut = force(h, a, h->nodes[r].ch[5]);
        if (h->nodes[scrut].tag == ND_APP) {
            NodeRef fn1   = node_deref(h, h->nodes[scrut].ch[0]);  /* APP(APP(QIN,A),R) */
            NodeRef arg_a = h->nodes[scrut].ch[1];                  /* a */
            if (h->nodes[fn1].tag == ND_APP) {
                NodeRef fn2 = node_deref(h, h->nodes[fn1].ch[0]);   /* APP(QIN,A) */
                if (h->nodes[fn2].tag == ND_APP) {
                    NodeRef head = node_deref(h, h->nodes[fn2].ch[0]);  /* QIN */
                    if (h->nodes[head].tag == ND_QIN) {
                        /* fire: return func a */
                        NodeRef func = h->nodes[r].ch[3];
                        NodeRef r2   = mk_app(h, func, arg_a);
                        h->nodes[r].tag   = ND_REF;
                        h->nodes[r].flags = NF_WHNF;
                        h->nodes[r].ch[0] = r2;
                        h->nodes[r].aux   = NULL;
                        return force(h, a, r2);
                    }
                }
            }
        }
        h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
        return r;
    }

    /* ND_ABORT: always stuck (Empty has no constructors) */

    if (tag == ND_INDREC) {
        int     fam_idx = h->nodes[r].lvl;
        IndDef *fam     = ind_get(fam_idx);
        int     n_ctors = fam->n_ctors;

        if (n_ctors > ND_MAX_CASES) {
            fprintf(stderr, "force: indrec '%s': %d constructors exceeds inline limit of %d\n",
                    fam->name, n_ctors, ND_MAX_CASES);
            exit(1);
        }

        /* Capture all NodeRef values before any heap allocs */
        NodeRef scrut_ch = h->nodes[r].ch[0];
        NodeRef motive   = h->nodes[r].ch[1];
        NodeRef cases[ND_MAX_CASES];
        for (int i = 0; i < n_ctors; i++)
            cases[i] = h->nodes[r].ch[2+i];

        NodeRef scrut = force(h, a, scrut_ch);

        if ((NodeTag)h->nodes[scrut].tag == ND_INDCON) {
            int packed   = h->nodes[scrut].lvl;
            int c_fam    = (packed >> 16) & 0xFFFF;
            int ctor_idx = packed & 0xFFFF;
            if (c_fam != fam_idx) {
                fprintf(stderr, "force: indrec '%s': scrutinee is constructor of family %d\n",
                        fam->name, c_fam);
                exit(1);
            }
            if (ctor_idx >= n_ctors) {
                fprintf(stderr, "force: indrec '%s': constructor index %d out of range [0,%d)\n",
                        fam->name, ctor_idx, n_ctors);
                exit(1);
            }
            CtorDef *ctor  = &fam->ctors[ctor_idx];
            int      n_par = fam->n_params;
            int      arity = ctor->arity;
            int      n_tot = n_par + arity;
            if (n_tot > 6) {
                fprintf(stderr, "force: indrec '%s': ctor '%s' has %d total args, exceeds limit of 6\n",
                        fam->name, ctor->name, n_tot);
                exit(1);
            }

            /* Capture ctor args before allocs */
            NodeRef con_args[6];
            for (int i = 0; i < n_tot; i++)
                con_args[i] = h->nodes[scrut].ch[i];

            /* Apply case function to ctor-local args only (skip shared params) */
            NodeRef result = cases[ctor_idx];
            for (int i = n_par; i < n_tot; i++) {
                NodeRef arg = con_args[i];
                result = mk_app(h, result, arg);
                int ap = i - n_par;
                if (ind_is_recursive_pos(fam_idx, ctor_idx, ap)) {
                    NodeRef ih = heap_alloc(h);
                    h->nodes[ih].tag   = ND_INDREC;
                    h->nodes[ih].flags = 0;
                    h->nodes[ih].lvl   = fam_idx;
                    h->nodes[ih].ch[0] = arg;
                    h->nodes[ih].ch[1] = motive;
                    for (int j = 0; j < n_ctors; j++)
                        h->nodes[ih].ch[2+j] = cases[j];
                    result = mk_app(h, result, ih);
                }
            }

            h->nodes[r].tag   = ND_REF;
            h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = result;
            h->nodes[r].aux   = NULL;
            return force(h, a, result);
        }
        /* HIT path ctor case: scrutinee is a core Val (e.g. path_ctor args @ r) */
        if ((NodeTag)h->nodes[scrut].tag == ND_CORE) {
            Val *scrut_v = (Val *)h->nodes[scrut].aux;
            /* Bridge motive and all cases to core Vals */
            nf(h, a, motive);
            Term *mot_t = node_to_term(h, node_deref(h, motive), a);
            if (!mot_t) { h->nodes[r].flags |= NF_WHNF; return r; }
            Val *mot_v = nbe_eval(a, NULL, mot_t);
            Val **cv = (Val **)arena_alloc(a, n_ctors * sizeof(Val *));
            int ok = 1;
            for (int bi = 0; bi < n_ctors && ok; bi++) {
                nf(h, a, cases[bi]);
                Term *c_t = node_to_term(h, node_deref(h, cases[bi]), a);
                if (!c_t) { ok = 0; break; }
                cv[bi] = nbe_eval(a, NULL, c_t);
            }
            if (!ok) { h->nodes[r].flags |= NF_WHNF; return r; }
            Val *res_v = nbe_vindrec(a, fam_idx, mot_v, cv, scrut_v);
            Term *res_t = nbe_quote(a, 0, res_v);
            NodeRef r2 = force(h, a, term_to_node(h, a, res_t, NULL_REF));
            h->nodes[r].tag   = ND_REF;
            h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = r2;
            h->nodes[r].aux   = NULL;
            return r2;
        }
        h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
        return r;
    }

    if (tag == ND_WREC) {
        NodeRef motive = h->nodes[r].ch[0];
        NodeRef step   = h->nodes[r].ch[1];
        NodeRef scrut  = force(h, a, h->nodes[r].ch[2]);
        if (h->nodes[scrut].tag == ND_SUP) {
            NodeRef label    = h->nodes[scrut].ch[0];  /* a : A */
            NodeRef children = h->nodes[scrut].ch[1];  /* f : B(a) → W(A,B) */

            /* Build IH = λx. WREC(P, s, APP(f, x))
             *
             * Capture P, s, f in an env chain so no serialization is needed.
             * When IH is applied to argument x, env = [x, P, s, f]:
             *   VAR(0) = x  (IH argument)
             *   VAR(1) = P  (motive)
             *   VAR(2) = s  (step)
             *   VAR(3) = f  (children function)
             */
            Term *ih_body = tm_wrec(a,
                                    tm_var(a, 1),
                                    tm_var(a, 2),
                                    tm_app(a, tm_var(a, 3), tm_var(a, 0)));
            NodeRef cap3   = mk_env(h, children, NULL_REF);
            NodeRef cap2   = mk_env(h, step,     cap3);
            NodeRef cap1   = mk_env(h, motive,   cap2);
            NodeRef ih     = mk_lam(h, "x",      cap1, ih_body);

            /* APP(APP(APP(step, label), children), IH) */
            NodeRef app1 = mk_app(h, step,             label);
            NodeRef app2 = mk_app(h, app1,             children);
            NodeRef app3 = mk_app(h, app2,             ih);

            h->nodes[r].tag   = ND_REF;
            h->nodes[r].flags = NF_WHNF;
            h->nodes[r].ch[0] = app3;
            h->nodes[r].aux   = NULL;
            return force(h, a, app3);
        }
        h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
        return r;
    }

    /* Unrecognized or stuck node */
    h->nodes[r].flags = (h->nodes[r].flags & ~NF_BLACKHOLE) | NF_WHNF;
    return r;
}

/* 
 * nf - force to WHNF, then recursively normalize all children.
 */
void nf(Heap *h, Arena *a, NodeRef root) {
    if (root == NULL_REF) return;
    NodeRef r = force(h, a, root);
    if (h->nodes[r].flags & NF_NF) return;

    NodeTag tag = (NodeTag)h->nodes[r].tag;

    switch (tag) {
    /* One child */
    case ND_SUCC:
    case ND_REFL:
    case ND_INL:
    case ND_INR:
    case ND_FST:
    case ND_SND:
        nf(h, a, h->nodes[r].ch[0]);
        break;
    /* Two children */
    case ND_PAIR:
    case ND_SUM:
    case ND_SUP:
    case ND_ABORT:
        nf(h, a, h->nodes[r].ch[0]);
        nf(h, a, h->nodes[r].ch[1]);
        break;
    /* Three children */
    case ND_UNITREC:
    case ND_WREC:
        nf(h, a, h->nodes[r].ch[0]);
        nf(h, a, h->nodes[r].ch[1]);
        nf(h, a, h->nodes[r].ch[2]);
        break;
    /* Four children */
    case ND_NATREC:
    case ND_BOOLREC:
    case ND_S1REC:
    case ND_TRUNCREC:
    case ND_CASESPLIT:
        nf(h, a, h->nodes[r].ch[0]);
        nf(h, a, h->nodes[r].ch[1]);
        nf(h, a, h->nodes[r].ch[2]);
        nf(h, a, h->nodes[r].ch[3]);
        break;
    /* Six children (J, QUOTREC) */
    case ND_J:
    case ND_QUOTREC:
        for (int i = 0; i < 6; i++) nf(h, a, h->nodes[r].ch[i]);
        break;
    /* Types with bindable cod: force dom only.
     * Forcing cod would require the binder variable to be in scope. */
    case ND_PI:
    case ND_SIGMA:
    case ND_W:
        nf(h, a, h->nodes[r].ch[0]);   /* dom: no binder in scope yet */
        break;
    /* Id type: all three children are binder-free */
    case ND_ID:
        nf(h, a, h->nodes[r].ch[0]);   /* type */
        nf(h, a, h->nodes[r].ch[1]);   /* lhs  */
        nf(h, a, h->nodes[r].ch[2]);   /* rhs  */
        break;
    /* Inductive constructors/types: normalize all args */
    case ND_INDTYPE: {
        int fam_idx = h->nodes[r].lvl;
        IndDef *fam = ind_get(fam_idx);
        int n_total = fam->n_params + fam->n_indices;
        int n = n_total < NODE_MAX_CHILDREN ? n_total : NODE_MAX_CHILDREN;
        for (int i = 0; i < n; i++)
            nf(h, a, h->nodes[r].ch[i]);
        break;
    }
    case ND_INDCON: {
        int packed   = h->nodes[r].lvl;
        int fam_idx  = (packed >> 16) & 0xFFFF;
        int ctor_idx = packed & 0xFFFF;
        IndDef *fam  = ind_get(fam_idx);
        if (ctor_idx >= fam->n_ctors) break;
        int n_total  = fam->n_params + fam->ctors[ctor_idx].arity;
        int n = n_total < NODE_MAX_CHILDREN ? n_total : NODE_MAX_CHILDREN;
        for (int i = 0; i < n; i++)
            nf(h, a, h->nodes[r].ch[i]);
        break;
    }
    /* Stuck indrec: normalize scrut, motive, and all cases */
    case ND_INDREC: {
        int fam_idx = h->nodes[r].lvl;
        IndDef *fam = ind_get(fam_idx);
        nf(h, a, h->nodes[r].ch[0]);  /* scrut */
        if (h->nodes[r].ch[1] != NULL_REF)
            nf(h, a, h->nodes[r].ch[1]);  /* motive */
        int nc = fam->n_ctors < ND_MAX_CASES ? fam->n_ctors : ND_MAX_CASES;
        for (int i = 0; i < nc; i++)
            nf(h, a, h->nodes[r].ch[2+i]);
        break;
    }
    case ND_FIX:
        nf(h, a, h->nodes[r].ch[0]);  /* normalize the body */
        break;
    case ND_LSUC:
    case ND_UNI_V:
        nf(h, a, h->nodes[r].ch[0]);
        break;
    default:
        break;
    }
    h->nodes[r].flags |= NF_NF;
}
