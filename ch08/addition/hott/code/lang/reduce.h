#pragma once
#include "node.h"
#include "../core/arena.h"
#include "../core/term.h"

/*
 * translate a core Term into the graph heap.
 * env is the current ND_ENV chain (NULL_REF for top-level).
 * Bound variables in t are looked up via env; free variables fatal.
 */
NodeRef term_to_node(Heap *h, Arena *a, Term *t, NodeRef env);

/*
 * Reduce root to full normal form in place.
 * Children are normalized recursively after forcing to WHNF.
 */
void nf(Heap *h, Arena *a, NodeRef root);
