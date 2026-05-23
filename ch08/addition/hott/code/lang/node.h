#pragma once
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../core/arena.h"

/* Node reference */
typedef uint32_t NodeRef;
#define NULL_REF ((NodeRef)0xFFFFFFFFu)

/* Flags */
#define NF_WHNF      0x01u   /* weak head normal form */
#define NF_NF        0x02u   /* full normal form */
#define NF_BLACKHOLE 0x04u   /* cycle guard (transient) */

/* Node tags */
typedef enum {
    /* Structural */
    ND_APP,          /* ch[0]=fun, ch[1]=arg */
    ND_LAM,          /* ch[0]=env_ref; name=binder; aux=Term* body */
    ND_ENV,          /* ch[0]=val_ref, ch[1]=next_ref */
    ND_VAR,          /* lvl=open level (sentinel / open variable) */
    ND_REF,          /* ch[0]=target (indirection for sharing) */
    ND_THUNK,        /* ch[0]=env_ref; aux=Term* expr (lazy) */
    ND_BLACKHOLE_TAG,/* cycle guard node */

    /* Types */
    ND_PI,           /* ch[0]=dom, ch[1]=cod; name=binder */
    ND_SIGMA,        /* ch[0]=dom, ch[1]=cod; name=binder */
    ND_ID,           /* ch[0]=ty, ch[1]=lhs, ch[2]=rhs */
    ND_UNI,          /* ulvl=universe level */
    ND_W,            /* ch[0]=dom, ch[1]=cod; name=binder */
    ND_SUM,          /* ch[0]=left, ch[1]=right */

    /* Canonical constructors */
    ND_ZERO,
    ND_SUCC,         /* ch[0]=pred */
    ND_NAT,
    ND_TRUE,
    ND_FALSE,
    ND_BOOL,
    ND_STAR,
    ND_UNIT,
    ND_EMPTY,
    ND_PAIR,         /* ch[0]=fst, ch[1]=snd */
    ND_REFL,         /* ch[0]=term */
    ND_INL,          /* ch[0]=val */
    ND_INR,          /* ch[0]=val */
    ND_SUP,          /* ch[0]=label, ch[1]=children */
    ND_S1,
    ND_BASE,
    ND_TRUNC,
    ND_TRINT,

    /* Sentinels (permanently stuck) */
    ND_LOOP,

    /* Eliminators (Phase 1+) */
    ND_FST,          /* ch[0]=scrut */
    ND_SND,          /* ch[0]=scrut */
    ND_NATREC,       /* ch[0]=motive, ch[1]=base, ch[2]=step, ch[3]=scrut */
    ND_BOOLREC,      /* ch[0]=motive, ch[1]=tcase, ch[2]=fcase, ch[3]=scrut */
    ND_S1REC,        /* ch[0]=motive, ch[1]=base, ch[2]=loop_case, ch[3]=scrut */
    ND_TRUNCREC,     /* ch[0]=ty_a, ch[1]=ty_b, ch[2]=func, ch[3]=scrut */
    ND_CASESPLIT,    /* ch[0]=motive, ch[1]=lcase, ch[2]=rcase, ch[3]=scrut */
    ND_ABORT,        /* ch[0]=motive, ch[1]=scrut */
    ND_UNITREC,      /* ch[0]=motive, ch[1]=base, ch[2]=scrut */
    ND_J,            /* ch[0]=ty, ch[1]=lhs, ch[2]=motive, ch[3]=base, ch[4]=endpoint, ch[5]=scrut */
    ND_WREC,         /* ch[0]=motive, ch[1]=step, ch[2]=scrut */

    /* Global definition reference */
    ND_GLOBAL,       /* lvl=def_index (negative = axiom constant) */

    /* Bridge to core (Phase 3) */
    ND_CORE,         /* aux=Val* from core NbE */
} NodeTag;

/* Node */
typedef struct {
    uint8_t  tag;
    uint8_t  flags;
    uint16_t _pad;
    NodeRef  ch[6];
    char    *name;   /* binder name for ND_LAM, ND_PI, ND_SIGMA, ND_W */
    union {
        int   lvl;   /* ND_VAR: open level; ND_GLOBAL: def index */
        int   ulvl;  /* ND_UNI: universe level */
        void *aux;   /* ND_LAM: Term* body, ND_THUNK: Term* expr, ND_CORE: Val* */
    };
} Node;

/* Heap */
typedef struct {
    Node   *nodes;
    size_t  size;
    size_t  cap;
} Heap;

/* Heap ops */
void    heap_init (Heap *h);
void    heap_free (Heap *h);
NodeRef heap_alloc(Heap *h);

/* Deref: follow ND_REF indirections */
static inline NodeRef node_deref(Heap *h, NodeRef r) {
    while (r != NULL_REF && h->nodes[r].tag == ND_REF)
        r = h->nodes[r].ch[0];
    return r;
}

/* Environment */
NodeRef env_lookup(Heap *h, NodeRef env, int idx);

/* Constructors */
NodeRef mk_app   (Heap *h, NodeRef fun, NodeRef arg);
NodeRef mk_lam   (Heap *h, char *name, NodeRef env, void *body_term);
NodeRef mk_env   (Heap *h, NodeRef val, NodeRef next);
NodeRef mk_var   (Heap *h, int lvl);
NodeRef mk_thunk (Heap *h, void *expr_term, NodeRef env);
NodeRef mk_zero  (Heap *h);
NodeRef mk_succ  (Heap *h, NodeRef pred);
NodeRef mk_nat   (Heap *h);
NodeRef mk_true  (Heap *h);
NodeRef mk_false (Heap *h);
NodeRef mk_bool  (Heap *h);
NodeRef mk_star  (Heap *h);
NodeRef mk_unit  (Heap *h);
NodeRef mk_empty (Heap *h);
NodeRef mk_pair  (Heap *h, NodeRef fst, NodeRef snd);
NodeRef mk_refl  (Heap *h, NodeRef t);
NodeRef mk_inl   (Heap *h, NodeRef t);
NodeRef mk_inr   (Heap *h, NodeRef t);
NodeRef mk_sum   (Heap *h, NodeRef l, NodeRef r);
NodeRef mk_s1    (Heap *h);
NodeRef mk_base  (Heap *h);
NodeRef mk_loop  (Heap *h);
NodeRef mk_trunc (Heap *h);
NodeRef mk_trint (Heap *h);
NodeRef mk_uni   (Heap *h, int ulvl);
NodeRef mk_global(Heap *h, int idx);

/* Spine frames
 * Records the non-scrutinee args of a stuck eliminator.
 * Allocated in Arena.  arg layout by tag:
 *   FST/SND      : nargs=0
 *   ABORT        : nargs=1  args=[motive]
 *   UNITREC/WREC : nargs=2  args=[motive, base/step]
 *   NATREC/BOOLREC/S1REC/TRUNCREC/CASESPLIT : nargs=3  args=[ch0..ch2]
 *   J            : nargs=5  args=[ty, lhs, motive, base, endpoint]
 */
typedef struct SpineFrame SpineFrame;
struct SpineFrame {
    NodeTag      tag;
    NodeRef      args[5];
    int          nargs;
    SpineFrame  *next;  /* towards head (inner frame) */
};

/* Sentinel level for PI/SIGMA/W binder variables during cod serialization.
 * Must not collide with real open-variable levels (≥ 0) or core axiom
 * sentinels (-994 … -999).  Each mk_var(h, BINDER_LVL) call creates a
 * distinct heap node; NodeRef identity distinguishes nested binders. */
#define BINDER_LVL (-10001)

/* Neutral helpers (public for reduce.c and conv) */
int     node_is_elim_tag(NodeTag t);
NodeRef node_scrut_of   (Heap *h, NodeRef r);

/* Convertibility */
int node_conv(Heap *h, Arena *a, NodeRef r1, NodeRef r2);

/* Printer */
void node_print     (Heap *h, NodeRef r, int depth, int prec);
void node_dump_graph(Heap *h);
