#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "defs.h"
#include "arena.h"
#include "parse.h"
#include "eval.h"
#include "check.h"
#include "elab.h"
#include "termcheck.h"

#define MAX_DEFS     1024
#define MAX_IND_DEFS  256

static Def    table[MAX_DEFS];
static int    ntable = 0;
static Arena  perm   = {NULL};   /* permanent arena: never freed */

static IndDef ind_table[MAX_IND_DEFS];
static int    n_ind = 0;

int def_add(char *name, Val *type, Val *val) {
    if (ntable >= MAX_DEFS) {
        fprintf(stderr, "def: global definition limit (%d) exceeded\n", MAX_DEFS);
        exit(1);
    }
    table[ntable] = (Def){name, type, val};
    return ntable++;
}

int def_lookup(const char *name) {
    for (int i = ntable - 1; i >= 0; i--)
        if (strcmp(table[i].name, name) == 0) return i;
    return -1;
}

Def        *def_get  (int idx)  { return &table[idx]; }
int         def_count(void)    { return ntable; }
const char *def_name (int idx) { return table[idx].name; }

/* Create an alias: same type/val as src_idx but registered under name. */
int def_alias(const char *name, int src_idx) {
    char *name_perm = arena_strdup(&perm, name);
    return def_add(name_perm, table[src_idx].type, table[src_idx].val);
}

int def_define(const char *name, const char *src) {
    char *name_perm = arena_strdup(&perm, name);
    Term *t = parse(&perm, src);
    if (!t) return -1;
    if (term_has_holes(t)) {
        ElabCtx e; elab_init(&e, &perm);
        Val *type = elab_infer(&e, &perm, 0, NULL, NULL, t);
        if (!type) return -1;
        type = elab_force(&e, type);
        t = elab_subst(&e, &perm, 0, t);
        if (!t) return -1;
        Val *val = nbe_eval(&perm, NULL, t);
        return def_add(name_perm, type, val);
    }
    Val *type = infer(&perm, 0, NULL, NULL, t);
    if (!type) return -1;
    Val *val = nbe_eval(&perm, NULL, t);
    return def_add(name_perm, type, val);
}

int def_define_nocheck(const char *name, const char *type_src, const char *expr_src) {
    char *name_perm = arena_strdup(&perm, name);
    Term *t = parse(&perm, expr_src);
    if (!t) return -1;
    /* Structural termination check for let rec (fix at the top level) */
    if (t->tag == TM_FIX) {
        if (!term_check_structural(t->fix.body, name)) return -1;
    }
    Val *type = NULL;
    if (type_src) {
        Term *ty = parse(&perm, type_src);
        if (!ty) return -1;
        type = nbe_eval(&perm, NULL, ty);
    }
    Val *val = nbe_eval(&perm, NULL, t);
    return def_add(name_perm, type, val);
}

/* ── Inductive family table ──────────────────────────────────────────────── */

int ind_add(IndDef *def) {
    if (n_ind >= MAX_IND_DEFS) {
        fprintf(stderr, "ind: inductive family limit (%d) exceeded\n", MAX_IND_DEFS);
        exit(1);
    }
    ind_table[n_ind] = *def;
    return n_ind++;
}

IndDef *ind_get(int fam_idx) {
    if (fam_idx < 0 || fam_idx >= n_ind) {
        fprintf(stderr, "ind_get: index %d out of range (have %d families)\n",
                fam_idx, n_ind);
        exit(1);
    }
    return &ind_table[fam_idx];
}

int ind_lookup(const char *name) {
    for (int i = n_ind - 1; i >= 0; i--)
        if (strcmp(ind_table[i].name, name) == 0) return i;
    return -1;
}

int ind_count(void) { return n_ind; }

Arena *def_perm_arena(void) { return &perm; }

int ind_is_recursive_pos(int fam_idx, int ctor_idx, int arg_pos) {
    CtorDef *ctor = &ind_get(fam_idx)->ctors[ctor_idx];
    return (ctor->is_recursive && ctor->is_recursive[arg_pos]) ? 1 : 0;
}

int ind_find_ctor(const char *name, int *fam_out, int *ctor_out) {
    for (int fi = n_ind - 1; fi >= 0; fi--) {  /* most-recent first, matches ind_lookup */
        IndDef *fam = &ind_table[fi];
        for (int ci = 0; ci < fam->n_ctors; ci++) {
            if (strcmp(fam->ctors[ci].name, name) == 0) {
                *fam_out  = fi;
                *ctor_out = ci;
                return 1;
            }
        }
    }
    return 0;
}
