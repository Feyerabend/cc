#pragma once
#include "term.h"

/*
 * Global definition table.
 *
 * Each definition stores its name, NbE type value, and NbE value in a
 * permanent arena that is never freed, so they survive arena_free_all()
 * calls in the REPL loop.
 *
 * Globals unfold transparently: TM_GLOBAL evaluates to def->val, so
 * `id Nat zero` reduces to `zero` when id = λA x. x.  This gives the
 * right definitional-equality behaviour for MLTT.
 */

typedef struct {
    char *name;
    Val  *type;  /* type  of the definition as a semantic value */
    Val  *val;   /* value of the definition as a semantic value */
} Def;

/* Register a pre-built definition; returns its index. */
int  def_add   (char *name, Val *type, Val *val);
/* Lookup by name (most-recent first); returns index or -1. */
int  def_lookup(const char *name);
/* Access by index (0-based). */
Def *def_get   (int idx);
/* Total number of registered definitions. */
int  def_count (void);

/*
 * Parse src, typecheck, evaluate, and register as name.
 * All allocation uses the permanent arena; the result survives
 * arena_free_all().  Returns the def index on success, -1 on failure.
 * src must be a type-inferrable term (annotate bare lambdas/pairs).
 */
int  def_define(const char *name, const char *src);

/*
 * Parse expr_src and type_src (may be NULL), evaluate both, and register
 * as name — without type-checking.  Use when the expression contains bare
 * lambdas that the bidirectional checker cannot infer.  All allocation uses
 * the permanent arena.  Returns the def index on success, -1 on failure.
 */
int  def_define_nocheck(const char *name, const char *type_src, const char *expr_src);

/* ── Inductive family table ────────────────────────────────────────────────
 *
 * User-declared inductive families are stored here, separate from the flat
 * Def table.  Every family also registers its type constructor and each of
 * its constructors as ordinary Def globals (so the name resolver can find
 * them), but the structural information — arity, index telescope, return
 * index expressions — lives here.
 *
 * All char* and Term* pointers stored in CtorDef / IndDef must be in
 * permanent storage (perm arena or static memory).  ind_add copies the
 * IndDef struct by value; the caller-owned CtorDef array pointed to by
 * ctors must outlive the table entry.
 */

typedef struct {
    char    *name;          /* constructor name, e.g. "cons"                */
    int      arity;         /* number of non-IH arguments                   */
    Term    *telescope;     /* Π-type of args in param context              */
    int      n_ret_indices; /* == family's n_indices                        */
    Term   **ret_indices;   /* index exprs in return type                   */
    char    *is_recursive;  /* is_recursive[i] != 0 if arg i is recursive  */
    int      def_idx;       /* Def-table index for this ctor's global; -1   */
} CtorDef;

typedef struct {
    char     *name;         /* family name, e.g. "Vec"                      */
    int       n_params;     /* number of uniform type parameters            */
    char    **param_names;  /* parameter names (NULL if n_params == 0)      */
    Term    **param_types;  /* parameter types, closed Terms                */
    int       n_indices;    /* number of value indices                      */
    Term    **index_types;  /* index types in param context                 */
    int       n_ctors;
    CtorDef  *ctors;        /* array of n_ctors CtorDefs                    */
    int       type_def_idx; /* Def index for the type constructor; -1       */
    int       elim_def_idx; /* Def index for the eliminator; -1             */
} IndDef;

/* Register family; copies *def by value; returns fam_idx. */
int     ind_add   (IndDef *def);
/* Access by fam_idx; fatal if out of range. */
IndDef *ind_get   (int fam_idx);
/* Lookup by name (most-recent first); returns fam_idx or -1. */
int     ind_lookup(const char *name);
/* Total number of registered families. */
int     ind_count (void);
/* Returns 1 if arg_pos of ctor_idx in fam_idx is a recursive position. */
int     ind_is_recursive_pos(int fam_idx, int ctor_idx, int arg_pos);

/* Permanent arena used by def_define / ind_add.  Terms and values stored
   here survive arena_free_all() calls in the REPL loop. */
Arena  *def_perm_arena(void);
