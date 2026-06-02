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
#define QUOT_CONST_LVL  (-993)  /* Quot : Type → (A→A→Type) → Type  */
#define QIN_CONST_LVL   (-992)  /* qin  : Π(A). Π(R). A → Quot A R  */
#define QEQS_CONST_LVL  (-991)  /* qeq  : path axiom (stuck)         */
/* Phase L2 — cubical interval */
#define INTERVAL_CONST_LVL (-990)  /* II : Type  — the interval        */
#define IZERO_CONST_LVL    (-989)  /* i0 : II   — left endpoint        */
#define IONE_CONST_LVL     (-988)  /* i1 : II   — right endpoint       */
/* Phase L2 Stage 3 — transp probe: a level above any real de Bruijn depth */
#define TRANSP_PROBE_LVL   (999999)

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
    TM_QUOT,     /* Quot         type former (0-arg sentinel)  */
    TM_QIN,      /* qin          intro (0-arg sentinel)        */
    TM_QEQS,     /* qeq          path axiom (0-arg sentinel)   */
    TM_QUOTREC,  /* quotrec A R B f coh x  eliminator (6-arg)  */
    TM_TRUNCREC, /* truncrec A B f t   eliminator (4-arg)            */
    TM_CIRCLE,   /* S1                 circle type (canonical)       */
    TM_BASE,     /* base               point of S¹ (canonical)      */
    TM_LOOP,     /* loop               non-trivial path (sentinel)   */
    TM_CIRCREC,  /* S1rec B b l s      recursor (4-arg)              */
    TM_INDTYPE,  /* inductive type former applied to params+indices   */
    TM_INDCON,   /* inductive constructor applied to args             */
    TM_INDREC,   /* inductive eliminator                             */
    TM_FIX,      /* fix f          general fixpoint (trusted)        */
    /* Phase M1 — universe polymorphism */
    TM_LEVEL,    /* Level          the type of universe levels        */
    TM_LZERO,    /* lzero          level zero                        */
    TM_LSUC,     /* lsuc ℓ         level successor; uses t->elim     */
    TM_LMAX,     /* lmax ℓ₁ ℓ₂     level max; reuses app.{fun=l, arg=r} */
    TM_UNI_V,    /* Type_ℓ         universe at a level expression    */
    /* Phase M2 — implicit arguments via elaboration */
    TM_HOLE,     /* _              hole; idx = meta id (-1 = unassigned, ≥0 = assigned) */
    /* Phase L2 — cubical interval */
    TM_INTERVAL, /* II             interval type (0-arg sentinel)                        */
    TM_IZERO,    /* i0             left endpoint (0-arg sentinel)                        */
    TM_IONE,     /* i1             right endpoint (0-arg sentinel)                       */
    TM_PATHABS,  /* <i> body       path abstraction; reuses lam.{name,body}              */
    TM_PATHAPP,  /* p @ r          path application; reuses app.{fun,arg}                */
    TM_PATH,     /* Path A a b     path type; reuses id.{ty,lhs,rhs}                     */
    TM_PATHP,    /* PathP fam a b  heterogeneous path type; id.{ty=fam:II→Type,lhs,rhs}  */
    /* Phase L2 Stage 3 — transp */
    TM_TRANSP,   /* transp A x     transport; reuses app.{fun=family, arg=elem}           */
    /* Phase L2 Stage 4 — hcomp */
    TM_HCOMP,    /* hcomp A φ u b  homogeneous composition                                */
    TM_COMP,     /* comp F φ u b   heterogeneous composition; reuses hcomp_t.{ty=fam,...} */
    TM_FILL,     /* fill F φ u b i comp at variable point i; fill_t.{fam,face,tube,base,idx} */
    /* Phase L2 Stage 5 — Glue types */
    TM_GLUE,     /* Glue A φ T e   glue type former; φ=i0→A, φ=i1→T, e:Equiv T A        */
    /* Phase L2 Stage 6 — interval operations (face lattice) */
    TM_IMIN,     /* imin i j       interval meet  (∧); reuses app.{fun=l, arg=r}         */
    TM_IMAX,     /* imax i j       interval join  (∨); reuses app.{fun=l, arg=r}         */
    TM_INEG,     /* ineg i         interval flip  (~); reuses elim = operand             */
    /* Phase M4 — pattern matching */
    TM_MATCH,    /* match scrut of | ctor names* => body ...  (case split, no IH)        */
    /* Phase L2 Stage 7 — partial elements */
    TM_ISONE,    /* IsOne φ    face-predicate type; φ:II→Type; reuses elim=face          */
    /* Phase L2 Stage 7d — glue intro / unglue elim */
    TM_GLUEELEM, /* glue φ t a  glue intro; φ:II, t:Partial φ T, a:A → Glue A φ T e    */
    TM_UNGLUE,   /* unglue φ e x  glue elim; φ:II, e:Equiv T A, x:Glue A φ T e → A    */
    /* PRIM-1 — primSub */
    TM_PRIMSUB,  /* primSub A φ u a  : A   (partial-element join; CCHM §5)             */
} TermTag;

/* Source location: 1-based line/col recorded by the parser; 0/0 = unknown. */
typedef struct { int line; int col; const char *file; } SrcLoc;

/* Phase M4 — surface pattern-matching arm (one constructor branch) */
#define MATCH_MAX_BINDS 8
typedef struct Term Term;
typedef struct MatchArm MatchArm;
struct MatchArm {
    int   ctor_idx;               /* constructor index: Nat 0=zero/1=succ, Bool 0=true/1=false */
    int   n_binds;                /* number of user-visible field binders (no IH)               */
    char *names[MATCH_MAX_BINDS]; /* field binder names (m' etc.; innermost = last = dB 0)      */
    char *ih_name;                /* induction hypothesis binder name, or NULL (dB 0 in body)   */
    Term *body;                   /* arm body; if ih_name: dB 0=ih, 1..n_binds=fields           */
};

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
        struct { Term *ty_a; Term *rel; Term *ty_b;
                 Term *func; Term *coh; Term *scrut; } quotrec_t;  /* QUOTREC */
        struct { Term *motive; Term *base_case; Term *loop_case;
                 Term *scrut; }                              circrec_t;   /* CIRCREC  */
        struct { int fam_idx; int n_args;  Term **args;  }               indtype; /* TM_INDTYPE */
        struct { int fam_idx; int ctor_idx; int n_args; Term **args;  }  indcon;  /* TM_INDCON  */
        struct { int fam_idx; Term *motive; int n_cases; Term **cases; Term *scrut; }  indrec;  /* TM_INDREC  */
        struct { Term *body; }                                                        fix;     /* TM_FIX     */
        struct { Term *scrut; int fam_idx; int n_arms; MatchArm *arms; } match_s; /* TM_MATCH  */
        Term                                                                         *uni_v_lvl; /* TM_UNI_V */
        struct { Term *ty; Term *face; Term *tube; Term *base; }                      hcomp_t;  /* TM_HCOMP  */
        struct { Term *fam; Term *face; Term *tube; Term *base; Term *idx; }          fill_t;   /* TM_FILL   */
        struct { Term *base; Term *face; Term *fiber; Term *equiv; }                  glue_t;      /* TM_GLUE      */
        struct { Term *face; Term *partial; Term *base; }                             glue_elem_t; /* TM_GLUEELEM  */
        struct { Term *face; Term *equiv;   Term *elem;  }                            unglue_t;    /* TM_UNGLUE    */
        struct { Term *ty; Term *face; Term *u; Term *a; }                            primsub_t;   /* TM_PRIMSUB   */
        /* Suspension HIT */
    };
    SrcLoc loc; /* source position filled by parser; 0/0 = unknown/synthesised */
};

/* ── Semantic values (NbE) */

typedef struct Val   Val;
typedef struct Env   Env;
typedef struct Spine Spine;

struct Env {
    Val  *val;
    Env  *next;
};

/* Phase M4 — stuck pattern-match arm closure (stored in SP_MATCH spine entry) */
typedef struct MatchClosure MatchClosure;
struct MatchClosure {
    int   ctor_idx;
    int   n_binds;
    char *names[MATCH_MAX_BINDS];
    char *ih_name;  /* IH binder name, or NULL */
    Env  *env;   /* captured outer environment at eval time */
    Term *body;  /* arm body (de Bruijn, binders 0..n_binds-1 + ih over env) */
};

/*
 * Spine: sequence of eliminators applied to a neutral head.
 * head = most recently applied (outermost when quoting).
 */
typedef enum { SP_APP, SP_FST, SP_SND, SP_J, SP_NATREC, SP_BOOLREC, SP_WREC, SP_ABORT, SP_UNITREC, SP_CASESPLIT, SP_TRUNCREC, SP_CIRCREC, SP_INDREC, SP_QUOTREC, SP_PATHAPP, SP_MATCH } SpineKind;
/* SP_PATHAPP: stuck path application p@r; interval value r stored in val field */
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
        struct { Val *ty_a; Val *rel; Val *ty_b; Val *func; Val *coh; } quotrec_s;  /* SP_QUOTREC */
        struct { Val *motive; Val *base_case; Val *loop_case; }              circrec_s;   /* SP_CIRCREC   */
        struct { int fam_idx; Val *motive; int n_cases; Val **cases; }       indrec;      /* SP_INDREC    */
        struct { int fam_idx; int n_arms; MatchClosure *arms; }             match_sp;    /* SP_MATCH     */
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
    VL_INDTYPE, /* inductive type former value          */
    VL_INDCON,  /* inductive constructor value          */
    VL_FIX,     /* fix f  — fixpoint (fun not applied)  */
    /* Phase M1 — universe polymorphism */
    VL_LEVEL,    /* Level type value                     */
    VL_LZERO,    /* level zero                           */
    VL_LSUC,     /* lsuc v  — successor level; uses succ */
    VL_LMAX,     /* lmax stuck (neutral levels); reuses pair.{fst,snd} */
    VL_UNI_V,    /* Type at variable level               */
    /* Phase L2 — cubical interval */
    VL_PATHABS,  /* ⟨i⟩ body       path closure; reuses lam.{name,env,body}    */
    VL_PATH,     /* Path A a b     path type value; reuses id.{ty,lhs,rhs}     */
    VL_PATHP,    /* PathP fam a b  heterogeneous path; id.{ty=fam,lhs=a,rhs=b} */
    /* Phase L2 Stage 3 */
    VL_TRANSP,   /* transp A x     stuck transport (non-constant family)        */
    /* Phase L2 Stage 4 */
    VL_HCOMP,    /* hcomp A φ u b  stuck composition (non-endpoint face)        */
    VL_COMP,     /* comp F φ u b   stuck comp (non-endpoint face, non-structural family) */
    /* Phase L2 Stage 5 */
    VL_GLUE,     /* Glue A φ T e   stuck glue type (non-endpoint face)          */
    /* Phase L2 Stage 6 — interval operations */
    VL_IMIN,     /* imin l r       stuck meet;  reuses pair.{fst=l, snd=r}      */
    VL_IMAX,     /* imax l r       stuck join;  reuses pair.{fst=l, snd=r}      */
    VL_INEG,     /* ineg v         stuck flip;  reuses succ = operand           */
    /* Phase L2 Stage 7 — partial elements */
    VL_ISONE,    /* IsOne φ (stuck neutral face); face stored in succ field      */
    /* Phase L2 Stage 7d — glue intro / unglue elim */
    VL_GLUEELEM, /* glue φ t a  stuck glue element (non-endpoint face)           */
    VL_UNGLUE,   /* unglue φ e x  stuck unglue (non-endpoint face, non-glue x)  */
    VL_JSTUCK,   /* J stuck on non-trivial VL_PATHABS; jstuck_s.{ty,lhs,motive,base,endpoint,proof} */
    /* PRIM-1 — primSub */
    VL_PRIMSUB,  /* primSub A φ u a  stuck (neutral face); primsub_s.{ty,face,u,out} */
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
        struct { int fam_idx; int n_args; Val **args; }               indtype; /* VL_INDTYPE */
        struct { int fam_idx; int ctor_idx; int n_args; Val **args; } indcon;  /* VL_INDCON  */
        Val                                                          *fix_fun;    /* VL_FIX     */
        Val                                                          *uni_v_lvl; /* VL_UNI_V   */
        struct { Val *family; Val *elem; }                            transp_s;  /* VL_TRANSP  */
        struct { Val *ty; Val *face; Val *tube; Val *base; }          hcomp_s;   /* VL_HCOMP   */
        struct { Val *base; Val *face; Val *fiber; Val *equiv; }      glue_s;      /* VL_GLUE      */
        struct { Val *face; Val *partial; Val *base; }                glue_elem_s; /* VL_GLUEELEM  */
        struct { Val *face; Val *equiv;   Val *elem; }                unglue_s;    /* VL_UNGLUE    */
        struct { Val *ty; Val *lhs; Val *motive; Val *base;
                 Val *endpoint; Val *proof; }                         jstuck_s;    /* VL_JSTUCK    */
        struct { Val *ty; Val *face; Val *u; Val *out; }              primsub_s;   /* VL_PRIMSUB   */
        /* VL_LSUC reuses succ (same layout: single Val*) */
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
Term  *tm_quot    (Arena *a);
Term  *tm_qin     (Arena *a);
Term  *tm_qeq     (Arena *a);
Term  *tm_quotrec (Arena *a, Term *ty_a, Term *rel, Term *ty_b,
                   Term *func, Term *coh, Term *scrut);
Spine *spine_quotrec(Arena *a, Val *ty_a, Val *rel, Val *ty_b,
                     Val *func, Val *coh, Spine *next);
Term *tm_circle   (Arena *a);
Term *tm_base     (Arena *a);
Term *tm_loop     (Arena *a);
Term *tm_circrec  (Arena *a, Term *motive, Term *base_case, Term *loop_case, Term *scrut);
Term *tm_indtype  (Arena *a, int fam_idx, int n_args,  Term **args);
Term *tm_indcon   (Arena *a, int fam_idx, int ctor_idx, int n_args, Term **args);
Term *tm_indrec   (Arena *a, int fam_idx, Term *motive, int n_cases, Term **cases, Term *scrut);
Term *tm_fix      (Arena *a, Term *body);
Term *tm_level    (Arena *a);
Term *tm_lzero    (Arena *a);
Term *tm_lsuc     (Arena *a, Term *t);
Term *tm_lmax     (Arena *a, Term *l, Term *r);
Val  *vl_lmax     (Arena *a, Val *l, Val *r);
Term *tm_uni_v    (Arena *a, Term *lvl);
Term *tm_hole     (Arena *a, int id);
/* Phase L2 — cubical interval */
Term  *tm_interval (Arena *a);
Term  *tm_izero    (Arena *a);
Term  *tm_ione     (Arena *a);
Term  *tm_pathabs  (Arena *a, char *name, Term *body);
Term  *tm_pathapp  (Arena *a, Term *path, Term *r);
Term  *tm_path     (Arena *a, Term *ty, Term *lhs, Term *rhs);
Term  *tm_pathp    (Arena *a, Term *fam, Term *lhs, Term *rhs);
Val   *vl_pathabs  (Arena *a, char *name, Env *env, Term *body);
Val   *vl_path     (Arena *a, Val *ty, Val *lhs, Val *rhs);
Val   *vl_pathp    (Arena *a, Val *fam, Val *lhs, Val *rhs);
Spine *spine_pathapp(Arena *a, Val *r, Spine *next);
/* Phase L2 Stage 3 — transp */
Term  *tm_transp   (Arena *a, Term *family, Term *elem);
Val   *vl_transp   (Arena *a, Val *family, Val *elem);
int    term_mentions_var(Term *t, int idx);
/* Phase L2 Stage 4 — hcomp */
Term  *tm_hcomp    (Arena *a, Term *ty, Term *face, Term *tube, Term *base);
Val   *vl_hcomp    (Arena *a, Val *ty, Val *face, Val *tube, Val *base);
/* Phase L2 Stage 4b — comp (heterogeneous composition) */
Term  *tm_comp     (Arena *a, Term *fam, Term *face, Term *tube, Term *base);
Val   *vl_comp     (Arena *a, Val  *fam, Val  *face, Val  *tube, Val  *base);
Term  *tm_fill     (Arena *a, Term *fam, Term *face, Term *tube, Term *base, Term *idx);
/* Phase L2 Stage 5 — Glue types */
Term  *tm_glue     (Arena *a, Term *base, Term *face, Term *fiber, Term *equiv);
Val   *vl_glue     (Arena *a, Val *base, Val *face, Val *fiber, Val *equiv);
/* Phase L2 Stage 6 — interval operations */
Term  *tm_imin     (Arena *a, Term *l, Term *r);
Term  *tm_imax     (Arena *a, Term *l, Term *r);
Term  *tm_ineg     (Arena *a, Term *v);
Val   *vl_imin     (Arena *a, Val *l, Val *r);
Val   *vl_imax     (Arena *a, Val *l, Val *r);
Val   *vl_ineg     (Arena *a, Val *v);
/* Phase M4 — pattern matching */
Term  *tm_match    (Arena *a, Term *scrut, int fam_idx, int n_arms, MatchArm *arms);
Spine *spine_match (Arena *a, int fam_idx, int n_arms, MatchClosure *arms, Spine *next);
/* Phase L2 Stage 7 — partial elements */
Term  *tm_isone    (Arena *a, Term *face);
Val   *vl_isone    (Arena *a, Val *face);
/* Phase L2 Stage 7d — glue intro / unglue elim */
Term  *tm_glueelem (Arena *a, Term *face, Term *partial, Term *base);
Val   *vl_glueelem (Arena *a, Val *face, Val *partial, Val *base);
Term  *tm_unglue   (Arena *a, Term *face, Term *equiv, Term *elem);
Val   *vl_unglue   (Arena *a, Val *face, Val *equiv, Val *elem);
Val   *vl_jstuck   (Arena *a, Val *ty, Val *lhs, Val *motive, Val *base, Val *endpoint, Val *proof);
/* PRIM-1 — primSub */
Term  *tm_primsub  (Arena *a, Term *ty, Term *face, Term *u, Term *out);
Val   *vl_primsub  (Arena *a, Val *ty, Val *face, Val *u, Val *out);
Val   *nbe_vprimsub(Arena *a, Val *ty, Val *face, Val *u, Val *out);
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
Val  *vl_indtype(Arena *a, int fam_idx, int n_args,   Val **args);
Val  *vl_indcon (Arena *a, int fam_idx, int ctor_idx, int n_args, Val **args);
Val  *vl_fix    (Arena *a, Val *fun);
Val  *vl_level  (Arena *a);
Val  *vl_lzero  (Arena *a);
Val  *vl_lsuc   (Arena *a, Val *pred);
Val  *vl_uni_v  (Arena *a, Val *lvl);

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
Spine *spine_indrec   (Arena *a, int fam_idx, Val *motive, int n_cases, Val **cases,
                       Spine *next);                          /* SP_INDREC    */

/* ── Printing context (name list, innermost = index 0) */

typedef struct Ctx Ctx;
struct Ctx { char *name; Ctx *next; };

/* ── Printing */

void term_print     (Term *t);
void term_fprint    (FILE *f, Term *t);
void term_fprint_ctx(FILE *f, Term *t, Ctx *ctx, int prec);
void val_print      (Val  *v, int depth);
