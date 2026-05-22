#pragma once
#include "node.h"
#include "../core/arena.h"
#include "../core/term.h"

/*
 * node_to_term  : serialize an NF heap node back to a core Term.
 *
 * Precondition: r must be in full normal form (nf() already called).
 *
 * Correctness note: ND_THUNK nodes are returned as their stored Term*
 * (aux field) without evaluating the env chain.  This is exact for
 * structural thunks (PI/SIGMA/W/ID cod: de Bruijn indices are valid in
 * the output context).  Stuck-APP arg thunks with captured environments
 * are similarly returned as-is; callers must ensure these thunks do not
 * contain free de Bruijn references before relying on the result.
 *
 * Returns NULL on failure (LAM with captured env, open VAR, etc.).
 */
Term   *node_to_term(Heap *h, NodeRef r, Arena *a);

/*
 * val_to_node : wrap a core Val* in a ND_CORE heap node.
 * The result is marked WHNF+NF and treated as an opaque stable value.
 */
NodeRef val_to_node(Heap *h, Val *v);
