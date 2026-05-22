#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "defs.h"
#include "arena.h"
#include "parse.h"
#include "eval.h"
#include "check.h"

#define MAX_DEFS 1024

static Def   table[MAX_DEFS];
static int   ntable = 0;
static Arena perm   = {NULL};   /* permanent arena: never freed */

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

Def *def_get(int idx)  { return &table[idx]; }
int  def_count(void)   { return ntable; }

int def_define(const char *name, const char *src) {
    char *name_perm = arena_strdup(&perm, name);
    Term *t = parse(&perm, src);
    if (!t) return -1;
    Val *type = infer(&perm, 0, NULL, NULL, t);
    if (!type) return -1;
    Val *val = nbe_eval(&perm, NULL, t);
    return def_add(name_perm, type, val);
}
