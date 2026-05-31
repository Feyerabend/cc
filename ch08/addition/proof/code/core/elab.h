#pragma once
#include "term.h"
#include "check.h"

/*
 * Implicit arguments via first-order pattern unification.
 *
 * Underscores '_' in source parse to TM_HOLE(-1).  The elaborator
 * processes a term top-down, creating metavariables for each hole and
 * solving them via elab_unify when enough information is available.
 *
 * Metas are represented as VL_NEUTRAL with level <= META_LVL_BASE.
 * Meta id k  ↔  neutral level (META_LVL_BASE - k).
 * This range is well clear of axiom sentinels (-994..-999) and the
 * free-variable error range (-(de_bruijn_idx+1), at most a few hundred).
 *
 * Usage:
 *   if (term_has_holes(t)) {
 *       ElabCtx e; elab_init(&e, arena);
 *       Val  *ty = elab_infer(&e, arena, 0, NULL, NULL, t);   // or elab_check
 *       if (!ty) { error; }
 *       t = elab_subst(&e, arena, 0, t);
 *       if (!t) { unsolved holes; }
 *   }
 *   // Then use t normally with infer / check / nbe_nf.
 */

#define ELAB_MAX_HOLES 64
#define META_LVL_BASE  (-2000)

static inline int is_meta_lvl(int lvl) { return lvl <= META_LVL_BASE; }
static inline int lvl_to_meta(int lvl)  { return META_LVL_BASE - lvl; }
static inline int meta_to_lvl(int id)   { return META_LVL_BASE - id; }

typedef struct {
    int  depth;   /* de Bruijn depth at which this hole was created */
    Val *type;    /* expected type (may contain other meta neutrals) */
    Val *val;     /* solution — NULL while unsolved                  */
} ElabHole;

typedef struct {
    int      n;
    ElabHole holes[ELAB_MAX_HOLES];
    Arena   *arena;  /* scratch arena for consistency checks in elab_solve */
} ElabCtx;

void  elab_init  (ElabCtx *e, Arena *a);
int   elab_fresh (ElabCtx *e, int depth, Val *type);
Val  *elab_read  (ElabCtx *e, int id);
int   elab_solve (ElabCtx *e, int id, Val *val);
Val  *elab_force (ElabCtx *e, Val *v);

/* Structural unification solving metas.  Returns 1 on success, 0 on failure. */
int   elab_unify (ElabCtx *e, Arena *a, int depth, Val *u, Val *v);

/* Meta-aware evaluation: substitutes solved holes, leaves unsolved as neutrals. */
Val  *elab_eval  (ElabCtx *e, Arena *a, Env *env, Term *t);

/* Elaboration: like check/infer but fills holes.
   expected = NULL means infer mode; non-NULL means check mode. */
int   elab_check (ElabCtx *e, Arena *a, int depth, TCtx *tctx, Env *env, Term *t, Val *ty);
Val  *elab_infer (ElabCtx *e, Arena *a, int depth, TCtx *tctx, Env *env, Term *t);

/* Post-elaboration: replace every TM_HOLE(id) with its quoted solution.
   Returns NULL if any holes remain unsolved. */
Term *elab_subst (ElabCtx *e, Arena *a, int depth, Term *t);

/* Returns 1 if t contains any TM_HOLE node (fast pre-check). */
int   term_has_holes(Term *t);
