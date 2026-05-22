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
