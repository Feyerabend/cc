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
#define TRUNC_CONST_LVL  (-997)  /* trunc : Type → Type              */
#define TRINT_CONST_LVL  (-996)  /* trint : Π(A:Type). A → trunc A   */
#define SQUASH_CONST_LVL (-995)  /* squash path axiom                */
#define LOOP_CONST_LVL   (-994)  /* loop : Id S¹ base base           */

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
    TM_W,      /* W(x : A). B x     well-founded tree type */
    TM_SUP,    /* sup label children  constructor          */
    TM_WREC,   /* wrec P s w          eliminator           */
    TM_EMPTY,  /* Empty               empty type (⊥)       */
    TM_ABORT,  /* abort A e           ex falso              */
    TM_UNIT,   /* Unit                unit type (⊤)        */
    TM_STAR,   /* star                sole constructor      */
    TM_UNITREC,/* unitrec P ps s      eliminator            */
    TM_SUM,    /* Sum A B             disjoint union type   */
    TM_INL,    /* inl a               left injection        */
    TM_INR,    /* inr b               right injection       */
    TM_CASESPLIT,/* case P fl fr s    eliminator            */
    TM_TRUNC,    /* trunc              type former (0-arg sentinel)  */
    TM_TRINT,    /* trint              intro |_|  (0-arg sentinel)   */
    TM_SQUASH,   /* squash             path axiom (0-arg sentinel)   */
    TM_TRUNCREC, /* truncrec A B f t   eliminator (4-arg)            */
    TM_CIRCLE,   /* S1                 circle type (canonical)       */
    TM_BASE,     /* base               point of S¹ (canonical)      */
    TM_LOOP,     /* loop               non-trivial path (sentinel)   */
    TM_CIRCREC,  /* S1rec B b l s      recursor (4-arg)              */
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
        Term                            *elim;   /* FST, SND, SUCC, INL, INR */
        struct { Term *ty; Term *lhs; Term *rhs; }       id;    /* ID   */
        Term                            *refl;           /* REFL */
        struct { Term *ty; Term *lhs; Term *motive;
                 Term *base; Term *endpoint; Term *proof; } j;  /* J       */
        struct { Term *motive; Term *base; Term *step;
                 Term *scrut; }                              natrec;  /* NATREC  */
        struct { Term *motive; Term *tcase; Term *fcase;
                 Term *scrut; }                              boolrec; /* BOOLREC */
        /* TM_W  reuses  pi.{name,dom,cod}  (same layout as TM_PI/TM_SIG)       */
        struct { Term *label; Term *children; }              sup;     /* SUP     */
        struct { Term *motive; Term *step; Term *scrut; }    wrec;    /* WREC    */
        struct { Term *motive; Term *scrut; }                abort_t;   /* ABORT    */
        struct { Term *motive; Term *base; Term *scrut; }    unitrec_t; /* UNITREC  */
        struct { Term *left; Term *right; }                  sum_t;      /* SUM      */
        struct { Term *motive; Term *lcase; Term *rcase;
                 Term *scrut; }                              casesplit_t; /* CASESPLIT*/
        struct { Term *ty_a; Term *ty_b; Term *func;
                 Term *scrut; }                              truncrec_t;  /* TRUNCREC */
        struct { Term *motive; Term *base_case; Term *loop_case;
                 Term *scrut; }                              circrec_t;   /* CIRCREC  */
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
typedef enum { SP_APP, SP_FST, SP_SND, SP_J, SP_NATREC, SP_BOOLREC, SP_WREC, SP_ABORT, SP_UNITREC, SP_CASESPLIT, SP_TRUNCREC, SP_CIRCREC } SpineKind;
struct Spine {
    SpineKind kind;
    union {
        Val *val;   /* SP_APP */
        struct { Val *ty; Val *lhs; Val *motive; Val *base; Val *endpoint; } j;       /* SP_J       */
        struct { Val *motive; Val *base; Val *step; }                        natrec;  /* SP_NATREC  */
        struct { Val *motive; Val *tcase; Val *fcase; }                      boolrec; /* SP_BOOLREC */
        struct { Val *motive; Val *step; }                                   wrec;    /* SP_WREC    */
        struct { Val *motive; }                                              abort_s;   /* SP_ABORT   */
        struct { Val *motive; Val *base; }                                   unitrec_s;   /* SP_UNITREC   */
        struct { Val *motive; Val *lcase; Val *rcase; }                      casesplit_s; /* SP_CASESPLIT */
        struct { Val *ty_a;   Val *ty_b;  Val *func;  }                      truncrec_s;  /* SP_TRUNCREC  */
        struct { Val *motive; Val *base_case; Val *loop_case; }              circrec_s;   /* SP_CIRCREC   */
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
    /* VL_W reuses pi.{name,dom,env,cod} (same layout as VL_PI, VL_SIGMA)      */
    VL_W,      /* W(x:A).B type value                  */
    /* VL_SUP reuses pair.{fst,snd} as {label,children}                        */
    VL_SUP,    /* sup(label, children) value           */
    VL_EMPTY,  /* Empty type value (⊥)                 */
    VL_UNIT,   /* Unit type value (⊤)                  */
    VL_STAR,   /* star — sole element of Unit          */
    VL_SUM,    /* Sum A B type: pair.fst=A, pair.snd=B */
    VL_INL,    /* left injection: inj = wrapped value  */
    VL_INR,    /* right injection: inj = wrapped value */
    VL_CIRCLE, /* S¹ type (canonical)                  */
    VL_BASE,   /* base point of S¹ (canonical)        */
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
        Val                                                  *inj;   /* VL_INL, VL_INR       */
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
Term *tm_w      (Arena *a, char *name, Term *dom, Term *cod);
Term *tm_sup    (Arena *a, Term *label, Term *children);
Term *tm_wrec   (Arena *a, Term *motive, Term *step, Term *scrut);
Term *tm_empty  (Arena *a);
Term *tm_abort  (Arena *a, Term *motive, Term *scrut);
Term *tm_unit   (Arena *a);
Term *tm_star   (Arena *a);
Term *tm_unitrec(Arena *a, Term *motive, Term *base, Term *scrut);
Term *tm_sum      (Arena *a, Term *left, Term *right);
Term *tm_inl      (Arena *a, Term *t);
Term *tm_inr      (Arena *a, Term *t);
Term *tm_casesplit(Arena *a, Term *motive, Term *lcase, Term *rcase, Term *scrut);
Term *tm_trunc    (Arena *a);
Term *tm_trint    (Arena *a);
Term *tm_squash   (Arena *a);
Term *tm_truncrec (Arena *a, Term *ty_a, Term *ty_b, Term *func, Term *scrut);
Term *tm_circle   (Arena *a);
Term *tm_base     (Arena *a);
Term *tm_loop     (Arena *a);
Term *tm_circrec  (Arena *a, Term *motive, Term *base_case, Term *loop_case, Term *scrut);

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
Val  *vl_w      (Arena *a, char *name, Val *dom, Env *env, Term *cod);
Val  *vl_sup    (Arena *a, Val *label, Val *children);
Val  *vl_empty  (Arena *a);
Val  *vl_unit   (Arena *a);
Val  *vl_star   (Arena *a);
Val  *vl_sum    (Arena *a, Val *left, Val *right);
Val  *vl_inl    (Arena *a, Val *v);
Val  *vl_inr    (Arena *a, Val *v);
Val  *vl_circle (Arena *a);
Val  *vl_base   (Arena *a);

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
Spine *spine_wrec   (Arena *a, Val *motive, Val *step,
                     Spine *next);                            /* SP_WREC    */
Spine *spine_abort  (Arena *a, Val *motive,
                     Spine *next);                            /* SP_ABORT   */
Spine *spine_unitrec(Arena *a, Val *motive, Val *base,
                     Spine *next);                            /* SP_UNITREC   */
Spine *spine_casesplit(Arena *a, Val *motive, Val *lcase, Val *rcase,
                       Spine *next);                          /* SP_CASESPLIT */
Spine *spine_truncrec (Arena *a, Val *ty_a,  Val *ty_b,  Val *func,
                       Spine *next);                          /* SP_TRUNCREC  */
Spine *spine_circrec  (Arena *a, Val *motive, Val *base_case, Val *loop_case,
                       Spine *next);                          /* SP_CIRCREC   */

/* ── Printing context (name list, innermost = index 0) */

typedef struct Ctx Ctx;
struct Ctx { char *name; Ctx *next; };

/* ── Printing */

void term_print     (Term *t);
void term_fprint    (FILE *f, Term *t);
void term_fprint_ctx(FILE *f, Term *t, Ctx *ctx, int prec);
void val_print      (Val  *v, int depth);
