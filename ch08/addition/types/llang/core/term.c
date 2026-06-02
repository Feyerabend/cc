#include <stdio.h>
#include "term.h"
#include "defs.h"

/* -- Term constructors */

static inline Term *term_alloc(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->loc = (SrcLoc){0, 0, NULL};
    return t;
}

Term *tm_var(Arena *a, int idx) {
    Term *t = term_alloc(a);
    t->tag = TM_VAR; t->idx = idx; return t;
}
Term *tm_lam(Arena *a, char *name, Term *body) {
    Term *t = term_alloc(a);
    t->tag = TM_LAM; t->lam.name = name; t->lam.body = body; return t;
}
Term *tm_app(Arena *a, Term *fun, Term *arg) {
    Term *t = term_alloc(a);
    t->tag = TM_APP; t->app.fun = fun; t->app.arg = arg; return t;
}
Term *tm_pi(Arena *a, char *name, Term *dom, Term *cod) {
    Term *t = term_alloc(a);
    t->tag = TM_PI; t->pi.name = name; t->pi.dom = dom; t->pi.cod = cod; return t;
}
Term *tm_uni(Arena *a, int level) {
    Term *t = term_alloc(a);
    t->tag = TM_UNI; t->ulevel = level; return t;
}
Term *tm_ann(Arena *a, Term *term, Term *type) {
    Term *t = term_alloc(a);
    t->tag = TM_ANN; t->ann.term = term; t->ann.type = type; return t;
}
Term *tm_sig(Arena *a, char *name, Term *dom, Term *cod) {
    Term *t = term_alloc(a);
    t->tag = TM_SIG; t->pi.name = name; t->pi.dom = dom; t->pi.cod = cod; return t;
}
Term *tm_pair(Arena *a, Term *fst, Term *snd) {
    Term *t = term_alloc(a);
    t->tag = TM_PAIR; t->pair.fst = fst; t->pair.snd = snd; return t;
}
Term *tm_fst(Arena *a, Term *body) {
    Term *t = term_alloc(a);
    t->tag = TM_FST; t->elim = body; return t;
}
Term *tm_snd(Arena *a, Term *body) {
    Term *t = term_alloc(a);
    t->tag = TM_SND; t->elim = body; return t;
}
Term *tm_id(Arena *a, Term *ty, Term *lhs, Term *rhs) {
    Term *t = term_alloc(a);
    t->tag = TM_ID; t->id.ty = ty; t->id.lhs = lhs; t->id.rhs = rhs; return t;
}
Term *tm_refl(Arena *a, Term *witness) {
    Term *t = term_alloc(a);
    t->tag = TM_REFL; t->refl = witness; return t;
}
Term *tm_j(Arena *a, Term *ty, Term *lhs, Term *motive,
           Term *base, Term *endpoint, Term *proof) {
    Term *t = term_alloc(a);
    t->tag = TM_J;
    t->j.ty = ty; t->j.lhs = lhs; t->j.motive = motive;
    t->j.base = base; t->j.endpoint = endpoint; t->j.proof = proof;
    return t;
}
Term *tm_ua(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_UA; return t;
}
Term *tm_funext(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_FUNEXT; return t;
}
Term *tm_nat(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_NAT; return t;
}
Term *tm_zero(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_ZERO; return t;
}
Term *tm_succ(Arena *a, Term *n) {
    Term *t = term_alloc(a);
    t->tag = TM_SUCC; t->elim = n; return t;
}
Term *tm_natrec(Arena *a, Term *motive, Term *base, Term *step, Term *scrut) {
    Term *t = term_alloc(a);
    t->tag = TM_NATREC;
    t->natrec.motive = motive; t->natrec.base = base;
    t->natrec.step   = step;   t->natrec.scrut = scrut;
    return t;
}
Term *tm_bool(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_BOOL; return t;
}
Term *tm_true(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_TRUE; return t;
}
Term *tm_false(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_FALSE; return t;
}
Term *tm_boolrec(Arena *a, Term *motive, Term *tcase, Term *fcase, Term *scrut) {
    Term *t = term_alloc(a);
    t->tag = TM_BOOLREC;
    t->boolrec.motive = motive; t->boolrec.tcase = tcase;
    t->boolrec.fcase  = fcase;  t->boolrec.scrut = scrut;
    return t;
}
Term *tm_global(Arena *a, int idx) {
    Term *t = term_alloc(a);
    t->tag = TM_GLOBAL; t->idx = idx; return t;
}
Term *tm_w(Arena *a, char *name, Term *dom, Term *cod) {
    Term *t = term_alloc(a);
    t->tag = TM_W; t->pi.name = name; t->pi.dom = dom; t->pi.cod = cod; return t;
}
Term *tm_sup(Arena *a, Term *label, Term *children) {
    Term *t = term_alloc(a);
    t->tag = TM_SUP; t->sup.label = label; t->sup.children = children; return t;
}
Term *tm_wrec(Arena *a, Term *motive, Term *step, Term *scrut) {
    Term *t = term_alloc(a);
    t->tag = TM_WREC;
    t->wrec.motive = motive; t->wrec.step = step; t->wrec.scrut = scrut; return t;
}
Term *tm_empty(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_EMPTY; return t;
}
Term *tm_abort(Arena *a, Term *motive, Term *scrut) {
    Term *t = term_alloc(a);
    t->tag = TM_ABORT; t->abort_t.motive = motive; t->abort_t.scrut = scrut; return t;
}
Term *tm_unit(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_UNIT; return t;
}
Term *tm_star(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_STAR; return t;
}
Term *tm_unitrec(Arena *a, Term *motive, Term *base, Term *scrut) {
    Term *t = term_alloc(a);
    t->tag = TM_UNITREC;
    t->unitrec_t.motive = motive; t->unitrec_t.base = base; t->unitrec_t.scrut = scrut;
    return t;
}
Term *tm_sum(Arena *a, Term *left, Term *right) {
    Term *t = term_alloc(a);
    t->tag = TM_SUM; t->sum_t.left = left; t->sum_t.right = right; return t;
}
Term *tm_inl(Arena *a, Term *inner) {
    Term *t = term_alloc(a);
    t->tag = TM_INL; t->elim = inner; return t;
}
Term *tm_inr(Arena *a, Term *inner) {
    Term *t = term_alloc(a);
    t->tag = TM_INR; t->elim = inner; return t;
}
Term *tm_casesplit(Arena *a, Term *motive, Term *lcase, Term *rcase, Term *scrut) {
    Term *t = term_alloc(a);
    t->tag = TM_CASESPLIT;
    t->casesplit_t.motive = motive; t->casesplit_t.lcase = lcase;
    t->casesplit_t.rcase  = rcase;  t->casesplit_t.scrut = scrut;
    return t;
}
Term *tm_trunc(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_TRUNC; return t;
}
Term *tm_trint(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_TRINT; return t;
}
Term *tm_squash(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_SQUASH; return t;
}
Term *tm_truncrec(Arena *a, Term *ty_a, Term *ty_b, Term *func, Term *scrut) {
    Term *t = term_alloc(a);
    t->tag = TM_TRUNCREC;
    t->truncrec_t.ty_a = ty_a; t->truncrec_t.ty_b = ty_b;
    t->truncrec_t.func = func; t->truncrec_t.scrut = scrut;
    return t;
}
Term *tm_quot(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_QUOT; return t;
}
Term *tm_qin(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_QIN; return t;
}
Term *tm_qeq(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_QEQS; return t;
}
Term *tm_quotrec(Arena *a, Term *ty_a, Term *rel, Term *ty_b,
                 Term *func, Term *coh, Term *scrut) {
    Term *t = term_alloc(a);
    t->tag = TM_QUOTREC;
    t->quotrec_t.ty_a  = ty_a;
    t->quotrec_t.rel   = rel;
    t->quotrec_t.ty_b  = ty_b;
    t->quotrec_t.func  = func;
    t->quotrec_t.coh   = coh;
    t->quotrec_t.scrut = scrut;
    return t;
}
Term *tm_circle(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_CIRCLE; return t;
}
Term *tm_base(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_BASE; return t;
}
Term *tm_loop(Arena *a) {
    Term *t = term_alloc(a);
    t->tag = TM_LOOP; return t;
}
Term *tm_circrec(Arena *a, Term *motive, Term *base_case, Term *loop_case, Term *scrut) {
    Term *t = term_alloc(a);
    t->tag = TM_CIRCREC;
    t->circrec_t.motive    = motive;    t->circrec_t.base_case = base_case;
    t->circrec_t.loop_case = loop_case; t->circrec_t.scrut     = scrut;
    return t;
}
Term *tm_indtype(Arena *a, int fam_idx, int n_args, Term **args) {
    Term *t = term_alloc(a);
    t->tag = TM_INDTYPE;
    t->indtype.fam_idx = fam_idx; t->indtype.n_args = n_args; t->indtype.args = args;
    return t;
}
Term *tm_indcon(Arena *a, int fam_idx, int ctor_idx, int n_args, Term **args) {
    Term *t = term_alloc(a);
    t->tag = TM_INDCON;
    t->indcon.fam_idx = fam_idx; t->indcon.ctor_idx = ctor_idx;
    t->indcon.n_args  = n_args;  t->indcon.args     = args;
    return t;
}
Term *tm_indrec(Arena *a, int fam_idx, Term *motive, int n_cases, Term **cases, Term *scrut) {
    Term *t = term_alloc(a);
    t->tag = TM_INDREC;
    t->indrec.fam_idx = fam_idx; t->indrec.motive  = motive;
    t->indrec.n_cases = n_cases; t->indrec.cases   = cases;
    t->indrec.scrut   = scrut;
    return t;
}

Term *tm_fix(Arena *a, Term *body) {
    Term *t = term_alloc(a);
    t->tag = TM_FIX; t->fix.body = body; return t;
}

/* -- Value constructors */

Val *vl_lam(Arena *a, char *name, Env *env, Term *body) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_LAM; v->lam.name = name; v->lam.env = env; v->lam.body = body; return v;
}
Val *vl_pi(Arena *a, char *name, Val *dom, Env *env, Term *cod) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_PI; v->pi.name = name; v->pi.dom = dom; v->pi.env = env; v->pi.cod = cod; return v;
}
Val *vl_uni(Arena *a, int level) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_UNI; v->ulevel = level; return v;
}
Val *vl_neutral(Arena *a, int lvl, Spine *spine) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_NEUTRAL; v->neutral.lvl = lvl; v->neutral.spine = spine; return v;
}
Val *vl_sigma(Arena *a, char *name, Val *dom, Env *env, Term *cod) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_SIGMA; v->pi.name = name; v->pi.dom = dom; v->pi.env = env; v->pi.cod = cod; return v;
}
Val *vl_pair(Arena *a, Val *fst, Val *snd) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_PAIR; v->pair.fst = fst; v->pair.snd = snd; return v;
}
Val *vl_id(Arena *a, Val *ty, Val *lhs, Val *rhs) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_ID; v->id.ty = ty; v->id.lhs = lhs; v->id.rhs = rhs; return v;
}
Val *vl_refl(Arena *a, Val *witness) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_REFL; v->refl = witness; return v;
}
Val *vl_nat(Arena *a) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    *v = (Val){.tag = VL_NAT}; return v;
}
Val *vl_zero(Arena *a) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    *v = (Val){.tag = VL_ZERO}; return v;
}
Val *vl_succ(Arena *a, Val *pred) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    *v = (Val){.tag = VL_SUCC, .succ = pred}; return v;
}
Val *vl_bool(Arena *a) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    *v = (Val){.tag = VL_BOOL}; return v;
}
Val *vl_true(Arena *a) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    *v = (Val){.tag = VL_TRUE}; return v;
}
Val *vl_false(Arena *a) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    *v = (Val){.tag = VL_FALSE}; return v;
}
Val *vl_w(Arena *a, char *name, Val *dom, Env *env, Term *cod) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_W; v->pi.name = name; v->pi.dom = dom; v->pi.env = env; v->pi.cod = cod; return v;
}
Val *vl_sup(Arena *a, Val *label, Val *children) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_SUP; v->pair.fst = label; v->pair.snd = children; return v;
}
Val *vl_empty(Arena *a) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    *v = (Val){.tag = VL_EMPTY}; return v;
}
Val *vl_unit(Arena *a) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    *v = (Val){.tag = VL_UNIT}; return v;
}
Val *vl_star(Arena *a) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    *v = (Val){.tag = VL_STAR}; return v;
}
Val *vl_sum(Arena *a, Val *left, Val *right) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_SUM; v->pair.fst = left; v->pair.snd = right; return v;
}
Val *vl_inl(Arena *a, Val *inner) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_INL; v->inj = inner; return v;
}
Val *vl_inr(Arena *a, Val *inner) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_INR; v->inj = inner; return v;
}
Val *vl_circle(Arena *a) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    *v = (Val){.tag = VL_CIRCLE}; return v;
}
Val *vl_base(Arena *a) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    *v = (Val){.tag = VL_BASE}; return v;
}
Val *vl_indtype(Arena *a, int fam_idx, int n_args, Val **args) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_INDTYPE;
    v->indtype.fam_idx = fam_idx; v->indtype.n_args = n_args; v->indtype.args = args;
    return v;
}
Val *vl_indcon(Arena *a, int fam_idx, int ctor_idx, int n_args, Val **args) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_INDCON;
    v->indcon.fam_idx = fam_idx; v->indcon.ctor_idx = ctor_idx;
    v->indcon.n_args  = n_args;  v->indcon.args     = args;
    return v;
}

Val *vl_fix(Arena *a, Val *fun) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_FIX; v->fix_fun = fun; return v;
}

/* Phase M1 — level terms */
Term *tm_level(Arena *a) { Term *t = term_alloc(a); t->tag = TM_LEVEL; return t; }
Term *tm_lzero(Arena *a) { Term *t = term_alloc(a); t->tag = TM_LZERO; return t; }
Term *tm_lsuc (Arena *a, Term *body) { Term *t = term_alloc(a); t->tag = TM_LSUC; t->elim = body; return t; }
Term *tm_lmax (Arena *a, Term *l, Term *r) {
    Term *t = term_alloc(a);
    t->tag = TM_LMAX; t->app.fun = l; t->app.arg = r; return t;
}
Term *tm_uni_v(Arena *a, Term *lvl)  { Term *t = term_alloc(a); t->tag = TM_UNI_V; t->uni_v_lvl = lvl; return t; }
Val  *vl_level(Arena *a) { Val *v = (Val *)arena_alloc(a, sizeof(Val)); v->tag = VL_LEVEL; return v; }
Val  *vl_lzero(Arena *a) { Val *v = (Val *)arena_alloc(a, sizeof(Val)); v->tag = VL_LZERO; return v; }
Val  *vl_lsuc (Arena *a, Val *pred) { Val *v = (Val *)arena_alloc(a, sizeof(Val)); v->tag = VL_LSUC; v->succ = pred; return v; }
Val  *vl_lmax (Arena *a, Val *l, Val *r) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_LMAX; v->pair.fst = l; v->pair.snd = r; return v;
}
Val  *vl_uni_v(Arena *a, Val *lvl)  { Val *v = (Val *)arena_alloc(a, sizeof(Val)); v->tag = VL_UNI_V; v->uni_v_lvl = lvl; return v; }

/* Phase M2 — holes */
Term *tm_hole(Arena *a, int id) { Term *t = term_alloc(a); t->tag = TM_HOLE; t->idx = id; return t; }

/* Phase L2 — cubical interval */
Term *tm_interval(Arena *a) { Term *t = term_alloc(a); t->tag = TM_INTERVAL; return t; }
Term *tm_izero   (Arena *a) { Term *t = term_alloc(a); t->tag = TM_IZERO; return t; }
Term *tm_ione    (Arena *a) { Term *t = term_alloc(a); t->tag = TM_IONE;  return t; }
/* Phase L2 Stage 3 — transp */
Term *tm_transp(Arena *a, Term *family, Term *elem) {
    Term *t = term_alloc(a);
    t->tag = TM_TRANSP; t->app.fun = family; t->app.arg = elem; return t;
}
Val *vl_transp(Arena *a, Val *family, Val *elem) {
    Val *v = arena_alloc(a, sizeof(Val));
    v->tag = VL_TRANSP; v->transp_s.family = family; v->transp_s.elem = elem; return v;
}
int term_mentions_var(Term *t, int idx) {
    if (!t) return 0;
    switch (t->tag) {
    case TM_VAR:      return t->idx == idx;
    case TM_LAM:
    case TM_PATHABS:  return term_mentions_var(t->lam.body, idx + 1);
    case TM_PI: case TM_SIG: case TM_W:
        return term_mentions_var(t->pi.dom, idx) ||
               term_mentions_var(t->pi.cod, idx + 1);
    case TM_APP: case TM_PATHAPP: case TM_TRANSP:
        return term_mentions_var(t->app.fun, idx) ||
               term_mentions_var(t->app.arg, idx);
    case TM_HCOMP:
    case TM_COMP:
        return term_mentions_var(t->hcomp_t.ty,   idx) ||
               term_mentions_var(t->hcomp_t.face, idx) ||
               term_mentions_var(t->hcomp_t.tube, idx) ||
               term_mentions_var(t->hcomp_t.base, idx);
    case TM_FILL:
        return term_mentions_var(t->fill_t.fam,   idx) ||
               term_mentions_var(t->fill_t.face,  idx) ||
               term_mentions_var(t->fill_t.tube,  idx) ||
               term_mentions_var(t->fill_t.base,  idx) ||
               term_mentions_var(t->fill_t.idx,   idx);
    case TM_GLUE:
        return term_mentions_var(t->glue_t.base,  idx) ||
               term_mentions_var(t->glue_t.face,  idx) ||
               term_mentions_var(t->glue_t.fiber, idx) ||
               term_mentions_var(t->glue_t.equiv, idx);
    case TM_IMIN: case TM_IMAX: case TM_LMAX:
        return term_mentions_var(t->app.fun, idx) ||
               term_mentions_var(t->app.arg, idx);
    case TM_INEG:
    case TM_ISONE:
        return term_mentions_var(t->elim, idx);
    case TM_GLUEELEM:
        return term_mentions_var(t->glue_elem_t.face,    idx) ||
               term_mentions_var(t->glue_elem_t.partial, idx) ||
               term_mentions_var(t->glue_elem_t.base,    idx);
    case TM_UNGLUE:
        return term_mentions_var(t->unglue_t.face,  idx) ||
               term_mentions_var(t->unglue_t.equiv, idx) ||
               term_mentions_var(t->unglue_t.elem,  idx);
    case TM_PRIMSUB:
        return term_mentions_var(t->primsub_t.ty,   idx) ||
               term_mentions_var(t->primsub_t.face, idx) ||
               term_mentions_var(t->primsub_t.u,    idx) ||
               term_mentions_var(t->primsub_t.a,    idx);
    case TM_ANN:
        return term_mentions_var(t->ann.term, idx) ||
               term_mentions_var(t->ann.type, idx);
    case TM_PAIR:
        return term_mentions_var(t->pair.fst, idx) ||
               term_mentions_var(t->pair.snd, idx);
    case TM_FST: case TM_SND: case TM_SUCC: case TM_INL: case TM_INR: case TM_LSUC:
        return term_mentions_var(t->elim, idx);
    case TM_ID: case TM_PATH: case TM_PATHP:
        return term_mentions_var(t->id.ty,  idx) ||
               term_mentions_var(t->id.lhs, idx) ||
               term_mentions_var(t->id.rhs, idx);
    case TM_REFL:     return term_mentions_var(t->refl, idx);
    case TM_J:
        return term_mentions_var(t->j.ty,       idx) ||
               term_mentions_var(t->j.lhs,      idx) ||
               term_mentions_var(t->j.motive,   idx) ||
               term_mentions_var(t->j.base,     idx) ||
               term_mentions_var(t->j.endpoint, idx) ||
               term_mentions_var(t->j.proof,    idx);
    case TM_NATREC:
        return term_mentions_var(t->natrec.motive, idx) ||
               term_mentions_var(t->natrec.base,   idx) ||
               term_mentions_var(t->natrec.step,   idx) ||
               term_mentions_var(t->natrec.scrut,  idx);
    case TM_BOOLREC:
        return term_mentions_var(t->boolrec.motive, idx) ||
               term_mentions_var(t->boolrec.tcase,  idx) ||
               term_mentions_var(t->boolrec.fcase,  idx) ||
               term_mentions_var(t->boolrec.scrut,  idx);
    case TM_SUP:
        return term_mentions_var(t->sup.label,    idx) ||
               term_mentions_var(t->sup.children, idx);
    case TM_WREC:
        return term_mentions_var(t->wrec.motive, idx) ||
               term_mentions_var(t->wrec.step,   idx) ||
               term_mentions_var(t->wrec.scrut,  idx);
    case TM_ABORT:
        return term_mentions_var(t->abort_t.motive, idx) ||
               term_mentions_var(t->abort_t.scrut,  idx);
    case TM_UNITREC:
        return term_mentions_var(t->unitrec_t.motive, idx) ||
               term_mentions_var(t->unitrec_t.base,   idx) ||
               term_mentions_var(t->unitrec_t.scrut,  idx);
    case TM_SUM:
        return term_mentions_var(t->sum_t.left,  idx) ||
               term_mentions_var(t->sum_t.right, idx);
    case TM_CASESPLIT:
        return term_mentions_var(t->casesplit_t.motive, idx) ||
               term_mentions_var(t->casesplit_t.lcase,  idx) ||
               term_mentions_var(t->casesplit_t.rcase,  idx) ||
               term_mentions_var(t->casesplit_t.scrut,  idx);
    case TM_TRUNCREC:
        return term_mentions_var(t->truncrec_t.ty_a,  idx) ||
               term_mentions_var(t->truncrec_t.ty_b,  idx) ||
               term_mentions_var(t->truncrec_t.func,  idx) ||
               term_mentions_var(t->truncrec_t.scrut, idx);
    case TM_QUOTREC:
        return term_mentions_var(t->quotrec_t.ty_a,  idx) ||
               term_mentions_var(t->quotrec_t.rel,   idx) ||
               term_mentions_var(t->quotrec_t.ty_b,  idx) ||
               term_mentions_var(t->quotrec_t.func,  idx) ||
               term_mentions_var(t->quotrec_t.coh,   idx) ||
               term_mentions_var(t->quotrec_t.scrut, idx);
    case TM_CIRCREC:
        return term_mentions_var(t->circrec_t.motive,    idx) ||
               term_mentions_var(t->circrec_t.base_case, idx) ||
               term_mentions_var(t->circrec_t.loop_case, idx) ||
               term_mentions_var(t->circrec_t.scrut,     idx);
    case TM_INDTYPE: {
        for (int i = 0; i < t->indtype.n_args; i++)
            if (term_mentions_var(t->indtype.args[i], idx)) return 1;
        return 0;
    }
    case TM_INDCON: {
        for (int i = 0; i < t->indcon.n_args; i++)
            if (term_mentions_var(t->indcon.args[i], idx)) return 1;
        return 0;
    }
    case TM_INDREC:
        if (term_mentions_var(t->indrec.motive, idx)) return 1;
        for (int i = 0; i < t->indrec.n_cases; i++)
            if (term_mentions_var(t->indrec.cases[i], idx)) return 1;
        return term_mentions_var(t->indrec.scrut, idx);
    case TM_FIX:      return term_mentions_var(t->fix.body, idx);
    case TM_UNI_V:    return term_mentions_var(t->uni_v_lvl, idx);
    case TM_MATCH: {
        if (term_mentions_var(t->match_s.scrut, idx)) return 1;
        for (int i = 0; i < t->match_s.n_arms; i++) {
            MatchArm *arm = &t->match_s.arms[i];
            int shift = arm->n_binds + (arm->ih_name ? 1 : 0);
            if (term_mentions_var(arm->body, idx + shift)) return 1;
        }
        return 0;
    }
    default:          return 0;  /* 0-arg constants: TM_NAT, TM_BOOL, TM_UNI, etc. */
    }
}
/* Phase L2 Stage 4 — hcomp */
Term *tm_hcomp(Arena *a, Term *ty, Term *face, Term *tube, Term *base) {
    Term *t = term_alloc(a);
    t->tag = TM_HCOMP; t->hcomp_t.ty = ty; t->hcomp_t.face = face;
    t->hcomp_t.tube = tube; t->hcomp_t.base = base; return t;
}
Val *vl_hcomp(Arena *a, Val *ty, Val *face, Val *tube, Val *base) {
    Val *v = arena_alloc(a, sizeof(Val));
    v->tag = VL_HCOMP; v->hcomp_s.ty = ty; v->hcomp_s.face = face;
    v->hcomp_s.tube = tube; v->hcomp_s.base = base; return v;
}
/* Phase L2 Stage 4b — comp (heterogeneous composition) */
Term *tm_comp(Arena *a, Term *fam, Term *face, Term *tube, Term *base) {
    Term *t = term_alloc(a);
    t->tag = TM_COMP;
    t->hcomp_t.ty   = fam;
    t->hcomp_t.face = face;
    t->hcomp_t.tube = tube;
    t->hcomp_t.base = base;
    return t;
}
Val *vl_comp(Arena *a, Val *fam, Val *face, Val *tube, Val *base) {
    Val *v = arena_alloc(a, sizeof(Val));
    v->tag = VL_COMP;
    v->hcomp_s.ty   = fam;
    v->hcomp_s.face = face;
    v->hcomp_s.tube = tube;
    v->hcomp_s.base = base;
    return v;
}
/* Phase L2 fill (comp at variable point) */
Term *tm_fill(Arena *a, Term *fam, Term *face, Term *tube, Term *base, Term *idx) {
    Term *t = term_alloc(a);
    t->tag          = TM_FILL;
    t->fill_t.fam   = fam;
    t->fill_t.face  = face;
    t->fill_t.tube  = tube;
    t->fill_t.base  = base;
    t->fill_t.idx   = idx;
    return t;
}

/* Phase L2 Stage 6 — interval operations */
Term *tm_imin(Arena *a, Term *l, Term *r) {
    Term *t = term_alloc(a);
    t->tag = TM_IMIN; t->app.fun = l; t->app.arg = r; return t;
}
Term *tm_imax(Arena *a, Term *l, Term *r) {
    Term *t = term_alloc(a);
    t->tag = TM_IMAX; t->app.fun = l; t->app.arg = r; return t;
}
Term *tm_ineg(Arena *a, Term *v) {
    Term *t = term_alloc(a);
    t->tag = TM_INEG; t->elim = v; return t;
}
Val *vl_imin(Arena *a, Val *l, Val *r) {
    Val *v = arena_alloc(a, sizeof(Val));
    v->tag = VL_IMIN; v->pair.fst = l; v->pair.snd = r; return v;
}
Val *vl_imax(Arena *a, Val *l, Val *r) {
    Val *v = arena_alloc(a, sizeof(Val));
    v->tag = VL_IMAX; v->pair.fst = l; v->pair.snd = r; return v;
}
Val *vl_ineg(Arena *a, Val *v_in) {
    Val *v = arena_alloc(a, sizeof(Val));
    v->tag = VL_INEG; v->succ = v_in; return v;
}

/* Phase L2 Stage 7 — partial elements */
Term *tm_isone(Arena *a, Term *face) {
    Term *t = term_alloc(a);
    t->tag = TM_ISONE; t->elim = face; return t;
}
Val *vl_isone(Arena *a, Val *face) {
    Val *v = arena_alloc(a, sizeof(Val));
    v->tag = VL_ISONE; v->succ = face; return v;  /* face stored in succ field */
}

/* Phase L2 Stage 5 — Glue type former */
Term *tm_glue(Arena *a, Term *base, Term *face, Term *fiber, Term *equiv) {
    Term *t = term_alloc(a);
    t->tag = TM_GLUE; t->glue_t.base = base; t->glue_t.face = face;
    t->glue_t.fiber = fiber; t->glue_t.equiv = equiv; return t;
}
Val *vl_glue(Arena *a, Val *base, Val *face, Val *fiber, Val *equiv) {
    Val *v = arena_alloc(a, sizeof(Val));
    v->tag = VL_GLUE; v->glue_s.base = base; v->glue_s.face = face;
    v->glue_s.fiber = fiber; v->glue_s.equiv = equiv; return v;
}

/* Phase L2 Stage 7d — glue intro / unglue elim */
Term *tm_glueelem(Arena *a, Term *face, Term *partial, Term *base) {
    Term *t = term_alloc(a);
    t->tag = TM_GLUEELEM;
    t->glue_elem_t.face    = face;
    t->glue_elem_t.partial = partial;
    t->glue_elem_t.base    = base;
    return t;
}
Val *vl_glueelem(Arena *a, Val *face, Val *partial, Val *base) {
    Val *v = arena_alloc(a, sizeof(Val));
    v->tag = VL_GLUEELEM;
    v->glue_elem_s.face    = face;
    v->glue_elem_s.partial = partial;
    v->glue_elem_s.base    = base;
    return v;
}
Term *tm_unglue(Arena *a, Term *face, Term *equiv, Term *elem) {
    Term *t = term_alloc(a);
    t->tag = TM_UNGLUE;
    t->unglue_t.face  = face;
    t->unglue_t.equiv = equiv;
    t->unglue_t.elem  = elem;
    return t;
}
Val *vl_unglue(Arena *a, Val *face, Val *equiv, Val *elem) {
    Val *v = arena_alloc(a, sizeof(Val));
    v->tag = VL_UNGLUE;
    v->unglue_s.face  = face;
    v->unglue_s.equiv = equiv;
    v->unglue_s.elem  = elem;
    return v;
}
Val *vl_jstuck(Arena *a, Val *ty, Val *lhs, Val *motive, Val *base, Val *endpoint, Val *proof) {
    Val *v = arena_alloc(a, sizeof(Val));
    v->tag = VL_JSTUCK;
    v->jstuck_s.ty       = ty;
    v->jstuck_s.lhs      = lhs;
    v->jstuck_s.motive   = motive;
    v->jstuck_s.base     = base;
    v->jstuck_s.endpoint = endpoint;
    v->jstuck_s.proof    = proof;
    return v;
}

/* PRIM-1 — primSub */
Term *tm_primsub(Arena *a, Term *ty, Term *face, Term *u, Term *out) {
    Term *t = term_alloc(a);
    t->tag = TM_PRIMSUB;
    t->primsub_t.ty   = ty;
    t->primsub_t.face = face;
    t->primsub_t.u    = u;
    t->primsub_t.a    = out;
    return t;
}
Val *vl_primsub(Arena *a, Val *ty, Val *face, Val *u, Val *out) {
    Val *v = arena_alloc(a, sizeof(Val));
    v->tag = VL_PRIMSUB;
    v->primsub_s.ty   = ty;
    v->primsub_s.face = face;
    v->primsub_s.u    = u;
    v->primsub_s.out  = out;
    return v;
}

Term *tm_pathabs (Arena *a, char *name, Term *body) {
    Term *t = term_alloc(a);
    t->tag = TM_PATHABS; t->lam.name = name; t->lam.body = body; return t;
}
Term *tm_pathapp (Arena *a, Term *path, Term *r) {
    Term *t = term_alloc(a);
    t->tag = TM_PATHAPP; t->app.fun = path; t->app.arg = r; return t;
}
Term *tm_path    (Arena *a, Term *ty, Term *lhs, Term *rhs) {
    Term *t = term_alloc(a);
    t->tag = TM_PATH; t->id.ty = ty; t->id.lhs = lhs; t->id.rhs = rhs; return t;
}
Term *tm_pathp   (Arena *a, Term *fam, Term *lhs, Term *rhs) {
    Term *t = term_alloc(a);
    t->tag = TM_PATHP; t->id.ty = fam; t->id.lhs = lhs; t->id.rhs = rhs; return t;
}

/* -- Env / Spine constructors */

Env *env_cons(Arena *a, Val *val, Env *next) {
    Env *e = (Env *)arena_alloc(a, sizeof(Env));
    e->val = val; e->next = next; return e;
}
Spine *spine_cons(Arena *a, Val *val, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_APP; s->val = val; s->next = next; return s;
}
Spine *spine_fst(Arena *a, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_FST; s->val = NULL; s->next = next; return s;
}
Spine *spine_snd(Arena *a, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_SND; s->val = NULL; s->next = next; return s;
}
Spine *spine_j(Arena *a, Val *ty, Val *lhs, Val *motive,
               Val *base, Val *endpoint, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_J;
    s->j.ty = ty; s->j.lhs = lhs; s->j.motive = motive;
    s->j.base = base; s->j.endpoint = endpoint;
    s->next = next; return s;
}
Spine *spine_natrec(Arena *a, Val *motive, Val *base, Val *step, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_NATREC;
    s->natrec.motive = motive; s->natrec.base = base; s->natrec.step = step;
    s->next = next; return s;
}
Spine *spine_boolrec(Arena *a, Val *motive, Val *tcase, Val *fcase, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_BOOLREC;
    s->boolrec.motive = motive; s->boolrec.tcase = tcase; s->boolrec.fcase = fcase;
    s->next = next; return s;
}
Spine *spine_wrec(Arena *a, Val *motive, Val *step, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_WREC;
    s->wrec.motive = motive; s->wrec.step = step;
    s->next = next; return s;
}
Spine *spine_abort(Arena *a, Val *motive, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_ABORT;
    s->abort_s.motive = motive;
    s->next = next; return s;
}
Spine *spine_unitrec(Arena *a, Val *motive, Val *base, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_UNITREC;
    s->unitrec_s.motive = motive; s->unitrec_s.base = base;
    s->next = next; return s;
}
Spine *spine_casesplit(Arena *a, Val *motive, Val *lcase, Val *rcase, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_CASESPLIT;
    s->casesplit_s.motive = motive; s->casesplit_s.lcase = lcase;
    s->casesplit_s.rcase  = rcase;
    s->next = next; return s;
}
Spine *spine_truncrec(Arena *a, Val *ty_a, Val *ty_b, Val *func, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_TRUNCREC;
    s->truncrec_s.ty_a = ty_a; s->truncrec_s.ty_b = ty_b;
    s->truncrec_s.func = func;
    s->next = next; return s;
}
Spine *spine_quotrec(Arena *a, Val *ty_a, Val *rel, Val *ty_b,
                     Val *func, Val *coh, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_QUOTREC;
    s->quotrec_s.ty_a = ty_a; s->quotrec_s.rel  = rel;
    s->quotrec_s.ty_b = ty_b; s->quotrec_s.func = func;
    s->quotrec_s.coh  = coh;
    s->next = next; return s;
}
Spine *spine_circrec(Arena *a, Val *motive, Val *base_case, Val *loop_case, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_CIRCREC;
    s->circrec_s.motive    = motive;    s->circrec_s.base_case = base_case;
    s->circrec_s.loop_case = loop_case;
    s->next = next; return s;
}
Spine *spine_indrec(Arena *a, int fam_idx, Val *motive, int n_cases, Val **cases, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_INDREC;
    s->indrec.fam_idx = fam_idx; s->indrec.motive  = motive;
    s->indrec.n_cases = n_cases; s->indrec.cases   = cases;
    s->next = next; return s;
}
Spine *spine_pathapp(Arena *a, Val *r, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_PATHAPP;
    s->val  = r;  /* reuse SP_APP's val field */
    s->next = next; return s;
}
/* Phase M4 — pattern matching */
Term *tm_match(Arena *a, Term *scrut, int fam_idx, int n_arms, MatchArm *arms) {
    Term *t = term_alloc(a);
    t->tag = TM_MATCH;
    t->match_s.scrut   = scrut;
    t->match_s.fam_idx = fam_idx;
    t->match_s.n_arms  = n_arms;
    t->match_s.arms    = arms;
    return t;
}
Spine *spine_match(Arena *a, int fam_idx, int n_arms, MatchClosure *arms, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_MATCH;
    s->match_sp.fam_idx = fam_idx;
    s->match_sp.n_arms  = n_arms;
    s->match_sp.arms    = arms;
    s->next = next; return s;
}
Val *vl_pathabs(Arena *a, char *name, Env *env, Term *body) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_PATHABS;
    v->lam.name = name; v->lam.env = env; v->lam.body = body;
    return v;
}
Val *vl_path(Arena *a, Val *ty, Val *lhs, Val *rhs) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_PATH;
    v->id.ty = ty; v->id.lhs = lhs; v->id.rhs = rhs;
    return v;
}
Val *vl_pathp(Arena *a, Val *fam, Val *lhs, Val *rhs) {
    Val *v = (Val *)arena_alloc(a, sizeof(Val));
    v->tag = VL_PATHP;
    v->id.ty = fam; v->id.lhs = lhs; v->id.rhs = rhs;
    return v;
}

/* -- Printing */

static const char *ctx_lookup(Ctx *ctx, int idx) {
    for (; ctx && idx > 0; ctx = ctx->next, idx--);
    return ctx ? ctx->name : "?";
}

void term_fprint_ctx(FILE *f, Term *t, Ctx *ctx, int prec) {
    if (!t) { fprintf(f, "<null>"); return; }
    switch (t->tag) {
    case TM_VAR:
        fprintf(f, "%s", ctx_lookup(ctx, t->idx));
        break;
    case TM_LAM: {
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "λ%s. ", t->lam.name);
        Ctx c = { t->lam.name, ctx };
        term_fprint_ctx(f, t->lam.body, &c, 0);
        if (prec > 0) fprintf(f, ")");
        break;
    }
    case TM_APP: {
        if (prec > 1) fprintf(f, "(");
        term_fprint_ctx(f, t->app.fun, ctx, 1);
        fprintf(f, " ");
        term_fprint_ctx(f, t->app.arg, ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    }
    case TM_PI: {
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "Π(%s : ", t->pi.name);
        term_fprint_ctx(f, t->pi.dom, ctx, 0);
        fprintf(f, "). ");
        Ctx c = { t->pi.name, ctx };
        term_fprint_ctx(f, t->pi.cod, &c, 0);
        if (prec > 0) fprintf(f, ")");
        break;
    }
    case TM_SIG: {
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "Σ(%s : ", t->pi.name);
        term_fprint_ctx(f, t->pi.dom, ctx, 0);
        fprintf(f, "). ");
        Ctx c = { t->pi.name, ctx };
        term_fprint_ctx(f, t->pi.cod, &c, 0);
        if (prec > 0) fprintf(f, ")");
        break;
    }
    case TM_UNI:
        if (t->ulevel == 0) fprintf(f, "Type");
        else fprintf(f, "Type_%d", t->ulevel);
        break;
    case TM_ANN:
        fprintf(f, "(");
        term_fprint_ctx(f, t->ann.term, ctx, 0);
        fprintf(f, " : ");
        term_fprint_ctx(f, t->ann.type, ctx, 0);
        fprintf(f, ")");
        break;
    case TM_PAIR:
        fprintf(f, "(");
        term_fprint_ctx(f, t->pair.fst, ctx, 0);
        fprintf(f, ", ");
        term_fprint_ctx(f, t->pair.snd, ctx, 0);
        fprintf(f, ")");
        break;
    case TM_FST:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "fst ");
        term_fprint_ctx(f, t->elim, ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case TM_SND:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "snd ");
        term_fprint_ctx(f, t->elim, ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case TM_ID:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "Id ");
        term_fprint_ctx(f, t->id.ty,  ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->id.lhs, ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->id.rhs, ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_REFL:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "refl ");
        term_fprint_ctx(f, t->refl, ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case TM_J:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "J ");
        term_fprint_ctx(f, t->j.ty,       ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->j.lhs,      ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->j.motive,   ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->j.base,     ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->j.endpoint, ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->j.proof,    ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_UA:
        fprintf(f, "ua");
        break;
    case TM_NAT:
        fprintf(f, "Nat");
        break;
    case TM_ZERO:
        fprintf(f, "zero");
        break;
    case TM_SUCC:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "succ ");
        term_fprint_ctx(f, t->elim, ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case TM_NATREC:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "natrec ");
        term_fprint_ctx(f, t->natrec.motive, ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->natrec.base,   ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->natrec.step,   ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->natrec.scrut,  ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_FUNEXT: fprintf(f, "funext"); break;
    case TM_GLOBAL:
        fprintf(f, "%s", def_get(t->idx)->name);
        break;
    case TM_BOOL:  fprintf(f, "Bool");  break;
    case TM_TRUE:  fprintf(f, "true");  break;
    case TM_FALSE: fprintf(f, "false"); break;
    case TM_BOOLREC:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "boolrec ");
        term_fprint_ctx(f, t->boolrec.motive, ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->boolrec.tcase,  ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->boolrec.fcase,  ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->boolrec.scrut,  ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_W: {
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "W(%s : ", t->pi.name);
        term_fprint_ctx(f, t->pi.dom, ctx, 0);
        fprintf(f, "). ");
        Ctx cw = { t->pi.name, ctx };
        term_fprint_ctx(f, t->pi.cod, &cw, 0);
        if (prec > 0) fprintf(f, ")");
        break;
    }
    case TM_SUP:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "sup ");
        term_fprint_ctx(f, t->sup.label,    ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->sup.children, ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case TM_WREC:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "wrec ");
        term_fprint_ctx(f, t->wrec.motive, ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->wrec.step,   ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->wrec.scrut,  ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_EMPTY:
        fprintf(f, "Empty");
        break;
    case TM_ABORT:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "abort ");
        term_fprint_ctx(f, t->abort_t.motive, ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->abort_t.scrut,  ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case TM_UNIT:
        fprintf(f, "Unit");
        break;
    case TM_STAR:
        fprintf(f, "star");
        break;
    case TM_UNITREC:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "unitrec ");
        term_fprint_ctx(f, t->unitrec_t.motive, ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->unitrec_t.base,   ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->unitrec_t.scrut,  ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_SUM:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "Sum ");
        term_fprint_ctx(f, t->sum_t.left,  ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->sum_t.right, ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_INL:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "inl ");
        term_fprint_ctx(f, t->elim, ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case TM_INR:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "inr ");
        term_fprint_ctx(f, t->elim, ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case TM_CASESPLIT:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "case ");
        term_fprint_ctx(f, t->casesplit_t.motive, ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->casesplit_t.lcase,  ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->casesplit_t.rcase,  ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->casesplit_t.scrut,  ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_TRUNC:  fprintf(f, "trunc");  break;
    case TM_TRINT:  fprintf(f, "trint");  break;
    case TM_SQUASH: fprintf(f, "squash"); break;
    case TM_QUOT:    fprintf(f, "Quot");    break;
    case TM_QIN:     fprintf(f, "qin");     break;
    case TM_QEQS:    fprintf(f, "qeq");     break;
    case TM_QUOTREC:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "quotrec ");
        term_fprint_ctx(f, t->quotrec_t.ty_a,  ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->quotrec_t.rel,   ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->quotrec_t.ty_b,  ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->quotrec_t.func,  ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->quotrec_t.coh,   ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->quotrec_t.scrut, ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_CIRCLE: fprintf(f, "S1");     break;
    case TM_BASE:   fprintf(f, "base");   break;
    case TM_LOOP:   fprintf(f, "loop");   break;
    case TM_TRUNCREC:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "truncrec ");
        term_fprint_ctx(f, t->truncrec_t.ty_a, ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->truncrec_t.ty_b, ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->truncrec_t.func, ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->truncrec_t.scrut, ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_CIRCREC:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "S1rec ");
        term_fprint_ctx(f, t->circrec_t.motive,    ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->circrec_t.base_case, ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->circrec_t.loop_case, ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->circrec_t.scrut,     ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_INDTYPE: {
        IndDef *fam = ind_get(t->indtype.fam_idx);
        if (t->indtype.n_args > 0 && prec > 1) fprintf(f, "(");
        fprintf(f, "%s", fam->name);
        for (int i = 0; i < t->indtype.n_args; i++) {
            fprintf(f, " ");
            term_fprint_ctx(f, t->indtype.args[i], ctx, 2);
        }
        if (t->indtype.n_args > 0 && prec > 1) fprintf(f, ")");
        break;
    }
    case TM_INDCON: {
        IndDef *fam = ind_get(t->indcon.fam_idx);
        const char *cname = fam->ctors[t->indcon.ctor_idx].name;
        if (t->indcon.n_args > 0 && prec > 1) fprintf(f, "(");
        fprintf(f, "%s", cname);
        for (int i = 0; i < t->indcon.n_args; i++) {
            fprintf(f, " ");
            term_fprint_ctx(f, t->indcon.args[i], ctx, 2);
        }
        if (t->indcon.n_args > 0 && prec > 1) fprintf(f, ")");
        break;
    }
    case TM_INDREC: {
        IndDef *fam = ind_get(t->indrec.fam_idx);
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "indrec %s", fam->name);
        if (t->indrec.motive) {
            fprintf(f, " ");
            term_fprint_ctx(f, t->indrec.motive, ctx, 2);
        }
        for (int i = 0; i < t->indrec.n_cases; i++) {
            fprintf(f, " ");
            term_fprint_ctx(f, t->indrec.cases[i], ctx, 2);
        }
        fprintf(f, " ");
        term_fprint_ctx(f, t->indrec.scrut, ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    }
    case TM_FIX:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "fix ");
        term_fprint_ctx(f, t->fix.body, ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_LEVEL: fprintf(f, "Level"); break;
    case TM_LZERO: fprintf(f, "lzero"); break;
    case TM_LSUC:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "lsuc ");
        term_fprint_ctx(f, t->elim, ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case TM_LMAX:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "lmax ");
        term_fprint_ctx(f, t->app.fun, ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->app.arg, ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case TM_UNI_V:
        fprintf(f, "Type_(");
        if (t->uni_v_lvl) term_fprint_ctx(f, t->uni_v_lvl, ctx, 0);
        else fprintf(f, "?");
        fprintf(f, ")");
        break;
    case TM_HOLE:
        if (t->idx < 0) fprintf(f, "_");
        else fprintf(f, "?%d", t->idx);
        break;
    /* Phase L2 */
    case TM_INTERVAL: fprintf(f, "II");   break;
    case TM_IZERO:    fprintf(f, "i0");   break;
    case TM_IONE:     fprintf(f, "i1");   break;
    case TM_PATHABS: {
        char *n = t->lam.name ? t->lam.name : "_";
        fprintf(f, "<%s> ", n);
        Ctx inner = { n, ctx };
        term_fprint_ctx(f, t->lam.body, &inner, 0);
        break;
    }
    case TM_PATHAPP:
        fprintf(f, "(");
        term_fprint_ctx(f, t->app.fun, ctx, 1);
        fprintf(f, " @ ");
        term_fprint_ctx(f, t->app.arg, ctx, 2);
        fprintf(f, ")");
        break;
    case TM_PATH:
        fprintf(f, "Path ");
        term_fprint_ctx(f, t->id.ty,  ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->id.lhs, ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->id.rhs, ctx, 2);
        break;
    case TM_PATHP:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "PathP ");
        term_fprint_ctx(f, t->id.ty,  ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->id.lhs, ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->id.rhs, ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_TRANSP:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "transp ");
        term_fprint_ctx(f, t->app.fun, ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->app.arg, ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_HCOMP:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "hcomp ");
        term_fprint_ctx(f, t->hcomp_t.ty,   ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->hcomp_t.face, ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->hcomp_t.tube, ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->hcomp_t.base, ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_COMP:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "comp ");
        term_fprint_ctx(f, t->hcomp_t.ty,   ctx, 2);
        fputc(' ', f);
        term_fprint_ctx(f, t->hcomp_t.face, ctx, 2);
        fputc(' ', f);
        term_fprint_ctx(f, t->hcomp_t.tube, ctx, 2);
        fputc(' ', f);
        term_fprint_ctx(f, t->hcomp_t.base, ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_FILL:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "fill ");
        term_fprint_ctx(f, t->fill_t.fam,  ctx, 2);
        fputc(' ', f);
        term_fprint_ctx(f, t->fill_t.face, ctx, 2);
        fputc(' ', f);
        term_fprint_ctx(f, t->fill_t.tube, ctx, 2);
        fputc(' ', f);
        term_fprint_ctx(f, t->fill_t.base, ctx, 2);
        fputc(' ', f);
        term_fprint_ctx(f, t->fill_t.idx,  ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_GLUE:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "Glue ");
        term_fprint_ctx(f, t->glue_t.base,  ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->glue_t.face,  ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->glue_t.fiber, ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->glue_t.equiv, ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_IMIN:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "imin ");
        term_fprint_ctx(f, t->app.fun, ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->app.arg, ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case TM_IMAX:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "imax ");
        term_fprint_ctx(f, t->app.fun, ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->app.arg, ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case TM_INEG:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "ineg ");
        term_fprint_ctx(f, t->elim, ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case TM_MATCH: {
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "match ");
        term_fprint_ctx(f, t->match_s.scrut, ctx, 2);
        fprintf(f, " of");
        for (int i = 0; i < t->match_s.n_arms; i++) {
            MatchArm *arm = &t->match_s.arms[i];
            int fam_idx = t->match_s.fam_idx;
            fprintf(f, " | ");
            /* print constructor name */
            if (fam_idx == -1) {
                fprintf(f, arm->ctor_idx == 0 ? "zero" : "succ");
            } else if (fam_idx == -2) {
                fprintf(f, arm->ctor_idx == 0 ? "true" : "false");
            } else {
                IndDef *fam = ind_get(fam_idx);
                if (arm->ctor_idx < fam->n_ctors)
                    fprintf(f, "%s", fam->ctors[arm->ctor_idx].name);
                else
                    fprintf(f, "<ctor%d>", arm->ctor_idx);
            }
            /* print binder names (fields + optional IH) */
            for (int j = 0; j < arm->n_binds; j++)
                fprintf(f, " %s", arm->names[j]);
            if (arm->ih_name) fprintf(f, " %s", arm->ih_name);
            fprintf(f, " => ");
            /* build extended ctx for body: fields first, then ih innermost */
            Ctx *body_ctx = ctx;
            Ctx ctx_exts[MATCH_MAX_BINDS + 1];
            for (int j = 0; j < arm->n_binds; j++) {
                ctx_exts[j].name = arm->names[j];
                ctx_exts[j].next = body_ctx;
                body_ctx = &ctx_exts[j];
            }
            if (arm->ih_name) {
                ctx_exts[arm->n_binds].name = arm->ih_name;
                ctx_exts[arm->n_binds].next = body_ctx;
                body_ctx = &ctx_exts[arm->n_binds];
            }
            term_fprint_ctx(f, arm->body, body_ctx, 0);
        }
        if (prec > 0) fprintf(f, ")");
        break;
    }
    case TM_ISONE:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "IsOne ");
        term_fprint_ctx(f, t->elim, ctx, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case TM_GLUEELEM:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "glue ");
        term_fprint_ctx(f, t->glue_elem_t.face,    ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->glue_elem_t.partial, ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->glue_elem_t.base,    ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_UNGLUE:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "unglue ");
        term_fprint_ctx(f, t->unglue_t.face,  ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->unglue_t.equiv, ctx, 2);
        fprintf(f, " ");
        term_fprint_ctx(f, t->unglue_t.elem,  ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case TM_PRIMSUB:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "primSub ");
        term_fprint_ctx(f, t->primsub_t.ty,   ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->primsub_t.face, ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->primsub_t.u,    ctx, 2); fprintf(f, " ");
        term_fprint_ctx(f, t->primsub_t.a,    ctx, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    default:
        fprintf(f, "<unknown term %d>", t->tag);
        break;
    }
}

void term_print (Term *t)          { term_fprint_ctx(stdout, t, NULL, 0); }
void term_fprint(FILE *f, Term *t) { term_fprint_ctx(f,      t, NULL, 0); }

/* -- val_print (debug; codomains shown as closures) ------------------- */

static void val_print_inner(FILE *f, Val *v, int depth, int prec);

static void spine_print(FILE *f, Spine *sp, int depth) {
    if (!sp) return;
    spine_print(f, sp->next, depth);
    switch (sp->kind) {
    case SP_APP:
        fprintf(f, " ");
        val_print_inner(f, sp->val, depth, 2);
        break;
    case SP_FST: fprintf(f, ".fst"); break;
    case SP_SND: fprintf(f, ".snd"); break;
    case SP_J:      fprintf(f, ".J(...)"); break;
    case SP_NATREC:  fprintf(f, ".natrec(...)");  break;
    case SP_BOOLREC: fprintf(f, ".boolrec(...)"); break;
    case SP_WREC:    fprintf(f, ".wrec(...)");    break;
    case SP_ABORT:      fprintf(f, ".abort(...)");      break;
    case SP_UNITREC:    fprintf(f, ".unitrec(...)");    break;
    case SP_CASESPLIT:  fprintf(f, ".case(...)");       break;
    case SP_TRUNCREC:   fprintf(f, ".truncrec(...)");   break;
    case SP_CIRCREC:    fprintf(f, ".S1rec(...)");      break;
    case SP_INDREC:     fprintf(f, ".indrec(...)");     break;
    case SP_QUOTREC:    fprintf(f, ".quotrec(...)");    break;
    case SP_PATHAPP:
        fprintf(f, " @ ");
        val_print_inner(f, sp->val, depth, 2);
        break;
    default: fprintf(f, ".<unknown spine %d>", sp->kind); break;
    }
}

static void val_print_inner(FILE *f, Val *v, int depth, int prec) {
    if (!v) { fprintf(f, "<null>"); return; }
    switch (v->tag) {
    case VL_LAM:      fprintf(f, "λ%s.<body>",    v->lam.name); break;
    case VL_PATHABS:  fprintf(f, "<%s><body>",    v->lam.name ? v->lam.name : "_"); break;
    case VL_PATH:
        fprintf(f, "Path ");
        val_print_inner(f, v->id.ty,  depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->id.lhs, depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->id.rhs, depth, 2);
        break;
    case VL_PATHP:
        fprintf(f, "PathP ");
        val_print_inner(f, v->id.ty,  depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->id.lhs, depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->id.rhs, depth, 2);
        break;
    case VL_PI:   fprintf(f, "Π(%s:...)<cod>", v->pi.name); break;
    case VL_SIGMA:fprintf(f, "Σ(%s:...)<cod>", v->pi.name); break;
    case VL_UNI:
        if (v->ulevel == 0) fprintf(f, "Type");
        else fprintf(f, "Type_%d", v->ulevel);
        break;
    case VL_NEUTRAL: {
        int has_spine = v->neutral.spine != NULL;
        if (prec > 1 && has_spine) fprintf(f, "(");
        if      (v->neutral.lvl == UA_CONST_LVL)     fprintf(f, "ua");
        else if (v->neutral.lvl == FUNEXT_CONST_LVL) fprintf(f, "funext");
        else if (v->neutral.lvl == TRUNC_CONST_LVL)  fprintf(f, "trunc");
        else if (v->neutral.lvl == TRINT_CONST_LVL)  fprintf(f, "trint");
        else if (v->neutral.lvl == SQUASH_CONST_LVL) fprintf(f, "squash");
        else if (v->neutral.lvl == LOOP_CONST_LVL)   fprintf(f, "loop");
        else if (v->neutral.lvl == QUOT_CONST_LVL)      fprintf(f, "Quot");
        else if (v->neutral.lvl == QIN_CONST_LVL)       fprintf(f, "qin");
        else if (v->neutral.lvl == QEQS_CONST_LVL)      fprintf(f, "qeq");
        else if (v->neutral.lvl == INTERVAL_CONST_LVL)  fprintf(f, "II");
        else if (v->neutral.lvl == IZERO_CONST_LVL)     fprintf(f, "i0");
        else if (v->neutral.lvl == IONE_CONST_LVL)      fprintf(f, "i1");
        else fprintf(f, "$%d", v->neutral.lvl);
        spine_print(f, v->neutral.spine, depth);
        if (prec > 1 && has_spine) fprintf(f, ")");
        break;
    }
    case VL_PAIR:
        fprintf(f, "(");
        val_print_inner(f, v->pair.fst, depth, 0);
        fprintf(f, ", ");
        val_print_inner(f, v->pair.snd, depth, 0);
        fprintf(f, ")");
        break;
    case VL_ID:
        fprintf(f, "Id");
        break;
    case VL_NAT:   fprintf(f, "Nat");   break;
    case VL_ZERO:  fprintf(f, "zero");  break;
    case VL_BOOL:  fprintf(f, "Bool");  break;
    case VL_TRUE:  fprintf(f, "true");  break;
    case VL_FALSE: fprintf(f, "false"); break;
    case VL_SUCC:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "succ ");
        val_print_inner(f, v->succ, depth, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case VL_REFL:
        fprintf(f, "refl(");
        val_print_inner(f, v->refl, depth, 0);
        fprintf(f, ")");
        break;
    case VL_W:     fprintf(f, "W(%s:...)<cod>", v->pi.name); break;
    case VL_EMPTY: fprintf(f, "Empty"); break;
    case VL_UNIT:  fprintf(f, "Unit");  break;
    case VL_STAR:  fprintf(f, "star");  break;
    case VL_SUM:
        fprintf(f, "Sum(");
        val_print_inner(f, v->pair.fst, depth, 0);
        fprintf(f, ", ");
        val_print_inner(f, v->pair.snd, depth, 0);
        fprintf(f, ")");
        break;
    case VL_INL:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "inl ");
        val_print_inner(f, v->inj, depth, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case VL_INR:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "inr ");
        val_print_inner(f, v->inj, depth, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case VL_CIRCLE: fprintf(f, "S1");   break;
    case VL_BASE:   fprintf(f, "base"); break;
    case VL_INDTYPE: {
        IndDef *fam = ind_get(v->indtype.fam_idx);
        if (v->indtype.n_args > 0 && prec > 1) fprintf(f, "(");
        fprintf(f, "%s", fam->name);
        for (int i = 0; i < v->indtype.n_args; i++) {
            fprintf(f, " ");
            val_print_inner(f, v->indtype.args[i], depth, 2);
        }
        if (v->indtype.n_args > 0 && prec > 1) fprintf(f, ")");
        break;
    }
    case VL_INDCON: {
        IndDef *fam = ind_get(v->indcon.fam_idx);
        const char *cname = fam->ctors[v->indcon.ctor_idx].name;
        if (v->indcon.n_args > 0 && prec > 1) fprintf(f, "(");
        fprintf(f, "%s", cname);
        for (int i = 0; i < v->indcon.n_args; i++) {
            fprintf(f, " ");
            val_print_inner(f, v->indcon.args[i], depth, 2);
        }
        if (v->indcon.n_args > 0 && prec > 1) fprintf(f, ")");
        break;
    }
    case VL_SUP:
        fprintf(f, "sup(");
        val_print_inner(f, v->pair.fst, depth, 0);
        fprintf(f, ", ");
        val_print_inner(f, v->pair.snd, depth, 0);
        fprintf(f, ")");
        break;
    case VL_FIX:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "fix ");
        val_print_inner(f, v->fix_fun, depth, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case VL_LEVEL: fprintf(f, "Level"); break;
    case VL_LZERO: fprintf(f, "lzero"); break;
    case VL_LSUC:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "lsuc ");
        val_print_inner(f, v->succ, depth, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case VL_LMAX:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "lmax ");
        val_print_inner(f, v->pair.fst, depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->pair.snd, depth, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case VL_UNI_V:
        fprintf(f, "Type_(");
        if (v->uni_v_lvl) val_print_inner(f, v->uni_v_lvl, depth, 0);
        else fprintf(f, "?");
        fprintf(f, ")");
        break;
    case VL_TRANSP:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "transp ");
        val_print_inner(f, v->transp_s.family, depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->transp_s.elem, depth, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case VL_HCOMP:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "hcomp ");
        val_print_inner(f, v->hcomp_s.ty,   depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->hcomp_s.face, depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->hcomp_s.tube, depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->hcomp_s.base, depth, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case VL_COMP:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "comp ");
        val_print_inner(f, v->hcomp_s.ty,   depth, 2); fputc(' ', f);
        val_print_inner(f, v->hcomp_s.face, depth, 2); fputc(' ', f);
        val_print_inner(f, v->hcomp_s.tube, depth, 2); fputc(' ', f);
        val_print_inner(f, v->hcomp_s.base, depth, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case VL_GLUE:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "Glue ");
        val_print_inner(f, v->glue_s.base,  depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->glue_s.face,  depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->glue_s.fiber, depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->glue_s.equiv, depth, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case VL_IMIN:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "imin ");
        val_print_inner(f, v->pair.fst, depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->pair.snd, depth, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case VL_IMAX:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "imax ");
        val_print_inner(f, v->pair.fst, depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->pair.snd, depth, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case VL_INEG:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "ineg ");
        val_print_inner(f, v->succ, depth, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case VL_ISONE:
        if (prec > 1) fprintf(f, "(");
        fprintf(f, "IsOne ");
        val_print_inner(f, v->succ, depth, 2);
        if (prec > 1) fprintf(f, ")");
        break;
    case VL_GLUEELEM:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "glue ");
        val_print_inner(f, v->glue_elem_s.face,    depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->glue_elem_s.partial, depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->glue_elem_s.base,    depth, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case VL_UNGLUE:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "unglue ");
        val_print_inner(f, v->unglue_s.face,  depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->unglue_s.equiv, depth, 2);
        fprintf(f, " ");
        val_print_inner(f, v->unglue_s.elem,  depth, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case VL_JSTUCK:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "J ");
        val_print_inner(f, v->jstuck_s.ty,       depth, 2); fprintf(f, " ");
        val_print_inner(f, v->jstuck_s.lhs,      depth, 2); fprintf(f, " ");
        val_print_inner(f, v->jstuck_s.motive,   depth, 2); fprintf(f, " ");
        val_print_inner(f, v->jstuck_s.base,     depth, 2); fprintf(f, " ");
        val_print_inner(f, v->jstuck_s.endpoint, depth, 2); fprintf(f, " ");
        val_print_inner(f, v->jstuck_s.proof,    depth, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    case VL_PRIMSUB:
        if (prec > 0) fprintf(f, "(");
        fprintf(f, "primSub ");
        val_print_inner(f, v->primsub_s.ty,   depth, 2); fprintf(f, " ");
        val_print_inner(f, v->primsub_s.face, depth, 2); fprintf(f, " ");
        val_print_inner(f, v->primsub_s.u,    depth, 2); fprintf(f, " ");
        val_print_inner(f, v->primsub_s.out,  depth, 2);
        if (prec > 0) fprintf(f, ")");
        break;
    default: fprintf(f, "<unknown val %d>", v->tag); break;
    }
}

void val_print(Val *v, int depth) { val_print_inner(stdout, v, depth, 0); }
