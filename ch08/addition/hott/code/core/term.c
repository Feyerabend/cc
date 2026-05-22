#include <stdio.h>
#include "term.h"
#include "defs.h"

/* -- Term constructors */

Term *tm_var(Arena *a, int idx) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_VAR; t->idx = idx; return t;
}
Term *tm_lam(Arena *a, char *name, Term *body) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_LAM; t->lam.name = name; t->lam.body = body; return t;
}
Term *tm_app(Arena *a, Term *fun, Term *arg) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_APP; t->app.fun = fun; t->app.arg = arg; return t;
}
Term *tm_pi(Arena *a, char *name, Term *dom, Term *cod) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_PI; t->pi.name = name; t->pi.dom = dom; t->pi.cod = cod; return t;
}
Term *tm_uni(Arena *a, int level) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_UNI; t->ulevel = level; return t;
}
Term *tm_ann(Arena *a, Term *term, Term *type) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_ANN; t->ann.term = term; t->ann.type = type; return t;
}
Term *tm_sig(Arena *a, char *name, Term *dom, Term *cod) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_SIG; t->pi.name = name; t->pi.dom = dom; t->pi.cod = cod; return t;
}
Term *tm_pair(Arena *a, Term *fst, Term *snd) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_PAIR; t->pair.fst = fst; t->pair.snd = snd; return t;
}
Term *tm_fst(Arena *a, Term *body) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_FST; t->elim = body; return t;
}
Term *tm_snd(Arena *a, Term *body) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_SND; t->elim = body; return t;
}
Term *tm_id(Arena *a, Term *ty, Term *lhs, Term *rhs) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_ID; t->id.ty = ty; t->id.lhs = lhs; t->id.rhs = rhs; return t;
}
Term *tm_refl(Arena *a, Term *witness) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_REFL; t->refl = witness; return t;
}
Term *tm_j(Arena *a, Term *ty, Term *lhs, Term *motive,
           Term *base, Term *endpoint, Term *proof) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_J;
    t->j.ty = ty; t->j.lhs = lhs; t->j.motive = motive;
    t->j.base = base; t->j.endpoint = endpoint; t->j.proof = proof;
    return t;
}
Term *tm_ua(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_UA}; return t;
}
Term *tm_funext(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_FUNEXT}; return t;
}
Term *tm_nat(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_NAT}; return t;
}
Term *tm_zero(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_ZERO}; return t;
}
Term *tm_succ(Arena *a, Term *n) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_SUCC, .elim = n}; return t;
}
Term *tm_natrec(Arena *a, Term *motive, Term *base, Term *step, Term *scrut) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_NATREC,
                .natrec = {motive, base, step, scrut}};
    return t;
}
Term *tm_bool(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_BOOL}; return t;
}
Term *tm_true(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_TRUE}; return t;
}
Term *tm_false(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_FALSE}; return t;
}
Term *tm_boolrec(Arena *a, Term *motive, Term *tcase, Term *fcase, Term *scrut) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_BOOLREC;
    t->boolrec.motive = motive; t->boolrec.tcase = tcase;
    t->boolrec.fcase  = fcase;  t->boolrec.scrut = scrut;
    return t;
}
Term *tm_global(Arena *a, int idx) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_GLOBAL; t->idx = idx; return t;
}
Term *tm_w(Arena *a, char *name, Term *dom, Term *cod) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_W; t->pi.name = name; t->pi.dom = dom; t->pi.cod = cod; return t;
}
Term *tm_sup(Arena *a, Term *label, Term *children) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_SUP; t->sup.label = label; t->sup.children = children; return t;
}
Term *tm_wrec(Arena *a, Term *motive, Term *step, Term *scrut) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_WREC;
    t->wrec.motive = motive; t->wrec.step = step; t->wrec.scrut = scrut; return t;
}
Term *tm_empty(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_EMPTY}; return t;
}
Term *tm_abort(Arena *a, Term *motive, Term *scrut) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_ABORT; t->abort_t.motive = motive; t->abort_t.scrut = scrut; return t;
}
Term *tm_unit(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_UNIT}; return t;
}
Term *tm_star(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_STAR}; return t;
}
Term *tm_unitrec(Arena *a, Term *motive, Term *base, Term *scrut) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_UNITREC;
    t->unitrec_t.motive = motive; t->unitrec_t.base = base; t->unitrec_t.scrut = scrut;
    return t;
}
Term *tm_sum(Arena *a, Term *left, Term *right) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_SUM; t->sum_t.left = left; t->sum_t.right = right; return t;
}
Term *tm_inl(Arena *a, Term *inner) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_INL; t->elim = inner; return t;
}
Term *tm_inr(Arena *a, Term *inner) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_INR; t->elim = inner; return t;
}
Term *tm_casesplit(Arena *a, Term *motive, Term *lcase, Term *rcase, Term *scrut) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_CASESPLIT;
    t->casesplit_t.motive = motive; t->casesplit_t.lcase = lcase;
    t->casesplit_t.rcase  = rcase;  t->casesplit_t.scrut = scrut;
    return t;
}
Term *tm_trunc(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_TRUNC}; return t;
}
Term *tm_trint(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_TRINT}; return t;
}
Term *tm_squash(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_SQUASH}; return t;
}
Term *tm_truncrec(Arena *a, Term *ty_a, Term *ty_b, Term *func, Term *scrut) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_TRUNCREC;
    t->truncrec_t.ty_a = ty_a; t->truncrec_t.ty_b = ty_b;
    t->truncrec_t.func = func; t->truncrec_t.scrut = scrut;
    return t;
}
Term *tm_circle(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_CIRCLE}; return t;
}
Term *tm_base(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_BASE}; return t;
}
Term *tm_loop(Arena *a) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    *t = (Term){.tag = TM_LOOP}; return t;
}
Term *tm_circrec(Arena *a, Term *motive, Term *base_case, Term *loop_case, Term *scrut) {
    Term *t = (Term *)arena_alloc(a, sizeof(Term));
    t->tag = TM_CIRCREC;
    t->circrec_t.motive    = motive;    t->circrec_t.base_case = base_case;
    t->circrec_t.loop_case = loop_case; t->circrec_t.scrut     = scrut;
    return t;
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
Spine *spine_circrec(Arena *a, Val *motive, Val *base_case, Val *loop_case, Spine *next) {
    Spine *s = (Spine *)arena_alloc(a, sizeof(Spine));
    s->kind = SP_CIRCREC;
    s->circrec_s.motive    = motive;    s->circrec_s.base_case = base_case;
    s->circrec_s.loop_case = loop_case;
    s->next = next; return s;
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
    default: fprintf(f, ".<unknown spine %d>", sp->kind); break;
    }
}

static void val_print_inner(FILE *f, Val *v, int depth, int prec) {
    if (!v) { fprintf(f, "<null>"); return; }
    switch (v->tag) {
    case VL_LAM:  fprintf(f, "λ%s.<body>", v->lam.name); break;
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
    case VL_SUP:
        fprintf(f, "sup(");
        val_print_inner(f, v->pair.fst, depth, 0);
        fprintf(f, ", ");
        val_print_inner(f, v->pair.snd, depth, 0);
        fprintf(f, ")");
        break;
    default: fprintf(f, "<unknown val %d>", v->tag); break;
    }
}

void val_print(Val *v, int depth) { val_print_inner(stdout, v, depth, 0); }
