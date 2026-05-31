#pragma once
#include "node.h"
#include "../core/arena.h"
#include "../core/term.h"

/*
 * node_to_term  : serialize an NF heap node back to a core Term.
 *
 * Precondition: r must be in full normal form (nf() already called).
 *
 * PI/SIGMA/W cod thunks are forced with a fresh BINDER_LVL sentinel to
 * recover the correct de Bruijn term.  Other ND_THUNK nodes (rare after
 * nf()) are returned as their raw stored Term*.
 *
 * Returns NULL on failure (LAM with captured env, open VAR, etc.).
 */
Term   *node_to_term(Heap *h, NodeRef r, Arena *a);

/*
 * val_to_node : wrap a core Val* in a ND_CORE heap node.
 * The result is marked WHNF+NF and treated as an opaque stable value.
 */
NodeRef val_to_node(Heap *h, Val *v);
