#pragma once
#include "arena.h"

/* Sentinel neutral levels for axiom constants.
 *
 * Valid neutral levels come from two sources:
 *   - depth-based (fresh variables): always >= 0
 *   - env_lookup free-variable errors: -(idx+1), i.e. -1, -2, -3, ...
 *
 * Sentinels must not collide with either range.  The env_lookup path
 * uses -(idx+1), so de Bruijn index N produces level -(N+1).  At N=997
 * that yields -998, and at N=998 it yields -999.  Both are astronomically
 * unreachable in any real term, but code that dispatches on these values
 * (quote, val_print_inner) always checks sentinels BEFORE computing a
 * de Bruijn index, so the check is safe regardless.                       */
#define UA_CONST_LVL     (-999)
#define FUNEXT_CONST_LVL (-998)

/* ── Syntax (de Bruijn) */

typedef enum {
    TM_VAR,   /* de Bruijn index                         */
    TM_LAM,   /* λ name. body                            */
    TM_APP,   /* (fun arg)                               */
    TM_PI,    /* Π name : dom. cod                       */
    TM_UNI,   /* Type_level                              */
    TM_ANN,   /* (term : type)  explicit annotation      */
    TM_SIG,   /* Σ name : dom. cod   dependent pair type */
    TM_PAIR,  /* (fst , snd)         constructor         */
    TM_FST,   /* fst term            first projection    */
    TM_SND,   /* snd term            second projection   */
    TM_ID,    /* Id A a b            identity type       */
    TM_REFL,  /* refl a              reflexivity         */
    TM_J,     /* J A a P d b p       path eliminator     */
    TM_UA,    /* ua                  univalence axiom    */
    TM_FUNEXT,/* funext              function extensionality axiom */
    TM_NAT,   /* Nat                 natural number type */
    TM_ZERO,  /* zero                zero constructor    */
    TM_SUCC,  /* succ n              successor           */
    TM_NATREC,/* natrec P z s n      recursor            */
    TM_BOOL,  /* Bool                boolean type        */
    TM_TRUE,  /* true                true constructor    */
    TM_FALSE, /* false               false constructor   */
    TM_BOOLREC,/* boolrec P pt pf b  eliminator          */
    TM_GLOBAL, /* global def (index into def table)       */
} TermTag;

typedef struct Term Term;
struct Term {
    TermTag tag;
    union {
        int                              idx;    /* VAR  */
        struct { char *name; Term *body; }       lam;    /* LAM  */
        struct { Term *fun;  Term *arg;  }       app;    /* APP  */
        struct { char *name; Term *dom; Term *cod; }     pi;  /* PI, SIG */
        int                              ulevel; /* UNI  */
        struct { Term *term; Term *type; }       ann;    /* ANN  */
        struct { Term *fst;  Term *snd;  }       pair;   /* PAIR */
        Term                            *elim;   /* FST, SND */
        struct { Term *ty; Term *lhs; Term *rhs; }       id;    /* ID   */
        Term                            *refl;           /* REFL */
        struct { Term *ty; Term *lhs; Term *motive;
                 Term *base; Term *endpoint; Term *proof; } j;  /* J       */
        struct { Term *motive; Term *base; Term *step;
                 Term *scrut; }                              natrec;  /* NATREC  */
        struct { Term *motive; Term *tcase; Term *fcase;
                 Term *scrut; }                              boolrec; /* BOOLREC */
    };
};

/* ── Semantic values (NbE) */

typedef struct Val   Val;
typedef struct Env   Env;
typedef struct Spine Spine;

struct Env {
    Val  *val;
    Env  *next;
};

/*
 * Spine: sequence of eliminators applied to a neutral head.
 * head = most recently applied (outermost when quoting).
 */
typedef enum { SP_APP, SP_FST, SP_SND, SP_J, SP_NATREC, SP_BOOLREC } SpineKind;
struct Spine {
    SpineKind kind;
    union {
        Val *val;   /* SP_APP */
        struct { Val *ty; Val *lhs; Val *motive; Val *base; Val *endpoint; } j;       /* SP_J       */
        struct { Val *motive; Val *base; Val *step; }                        natrec;  /* SP_NATREC  */
        struct { Val *motive; Val *tcase; Val *fcase; }                      boolrec; /* SP_BOOLREC */
    };
    Spine *next;
};

typedef enum {
    VL_LAM,
    VL_PI,
    VL_UNI,
    VL_NEUTRAL,
    VL_SIGMA,  /* Σ type value                         */
    VL_PAIR,   /* pair value                           */
    VL_ID,     /* Id type value                        */
    VL_REFL,   /* refl value                           */
    VL_NAT,    /* Nat type                             */
    VL_ZERO,   /* zero                                 */
    VL_SUCC,   /* succ (pred)                          */
    VL_BOOL,   /* Bool type                            */
    VL_TRUE,   /* true                                 */
    VL_FALSE,  /* false                                */
} ValTag;

struct Val {
    ValTag tag;
    union {
        struct { char *name; Env *env; Term *body; }          lam;
        struct { char *name; Val *dom; Env *env; Term *cod; } pi;   /* PI, SIGMA share layout */
        int                                                   ulevel;
        struct { int lvl; Spine *spine; }                     neutral;
        struct { Val *fst; Val *snd; }                        pair;
        struct { Val *ty; Val *lhs; Val *rhs; }               id;
        Val                                                  *refl;
        Val                                                  *succ;  /* VL_SUCC: predecessor */
    };
};

/* ── Term constructors */

Term *tm_var (Arena *a, int idx);
Term *tm_lam (Arena *a, char *name, Term *body);
Term *tm_app (Arena *a, Term *fun,  Term *arg);
Term *tm_pi  (Arena *a, char *name, Term *dom, Term *cod);
Term *tm_uni (Arena *a, int level);
Term *tm_ann (Arena *a, Term *term, Term *type);
Term *tm_sig (Arena *a, char *name, Term *dom, Term *cod);
Term *tm_pair(Arena *a, Term *fst,  Term *snd);
Term *tm_fst (Arena *a, Term *t);
Term *tm_snd (Arena *a, Term *t);
Term *tm_id  (Arena *a, Term *ty, Term *lhs, Term *rhs);
Term *tm_refl(Arena *a, Term *t);
Term *tm_j   (Arena *a, Term *ty, Term *lhs, Term *motive,
              Term *base, Term *endpoint, Term *proof);
Term *tm_ua     (Arena *a);
Term *tm_funext (Arena *a);
Term *tm_nat    (Arena *a);
Term *tm_zero   (Arena *a);
Term *tm_succ   (Arena *a, Term *n);
Term *tm_natrec (Arena *a, Term *motive, Term *base, Term *step, Term *scrut);
Term *tm_bool   (Arena *a);
Term *tm_true   (Arena *a);
Term *tm_false  (Arena *a);
Term *tm_boolrec(Arena *a, Term *motive, Term *tcase, Term *fcase, Term *scrut);
Term *tm_global (Arena *a, int idx);

/* ── Value constructors */

Val  *vl_lam    (Arena *a, char *name, Env *env, Term *body);
Val  *vl_pi     (Arena *a, char *name, Val *dom, Env *env, Term *cod);
Val  *vl_uni    (Arena *a, int level);
Val  *vl_neutral(Arena *a, int lvl, Spine *spine);
Val  *vl_sigma  (Arena *a, char *name, Val *dom, Env *env, Term *cod);
Val  *vl_pair   (Arena *a, Val *fst, Val *snd);
Val  *vl_id     (Arena *a, Val *ty, Val *lhs, Val *rhs);
Val  *vl_refl   (Arena *a, Val *v);
Val  *vl_nat    (Arena *a);
Val  *vl_zero   (Arena *a);
Val  *vl_succ   (Arena *a, Val *pred);
Val  *vl_bool   (Arena *a);
Val  *vl_true   (Arena *a);
Val  *vl_false  (Arena *a);

/* ── Env / Spine constructors */

Env   *env_cons  (Arena *a, Val *val, Env *next);
Spine *spine_cons(Arena *a, Val *val, Spine *next);   /* SP_APP */
Spine *spine_fst (Arena *a,           Spine *next);   /* SP_FST */
Spine *spine_snd (Arena *a,           Spine *next);   /* SP_SND */
Spine *spine_j      (Arena *a, Val *ty, Val *lhs, Val *motive,
                     Val *base, Val *endpoint, Spine *next);  /* SP_J      */
Spine *spine_natrec (Arena *a, Val *motive, Val *base, Val *step,
                     Spine *next);                            /* SP_NATREC  */
Spine *spine_boolrec(Arena *a, Val *motive, Val *tcase, Val *fcase,
                     Spine *next);                            /* SP_BOOLREC */

/* ── Printing context (name list, innermost = index 0) */

typedef struct Ctx Ctx;
struct Ctx { char *name; Ctx *next; };

/* ── Printing */

void term_print     (Term *t);
void term_fprint    (FILE *f, Term *t);
void term_fprint_ctx(FILE *f, Term *t, Ctx *ctx, int prec);
void val_print      (Val  *v, int depth);
