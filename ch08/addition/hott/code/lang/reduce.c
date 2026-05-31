#include "node.h"
#include "reduce.h"
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

        /* Stuck: fun is not a LAM or unfoldable GLOBAL */
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

    /* ND_ABORT: always stuck (Empty has no constructors) */

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
    /* Six children (J) */
    case ND_J:
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
    default:
        break;
    }
    h->nodes[r].flags |= NF_NF;
}
