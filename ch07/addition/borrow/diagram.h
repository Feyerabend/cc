/*
 * diagram.h  —  Renderer for BC events and diagnostics.
 *
 * Knows nothing about how checking decisions are made.
 * Reads bc->events[] and bc->diags[]; never calls bc_* functions.
 *
 * String-diagram notation
 * ───────────────────────
 * Wires represent values flowing through time (top → bottom).
 * Operations are horizontal events that connect or sever wires.
 *
 *   [name]─────owns──────►  alive ownership wire
 *   [name]·····&T········►  shared borrow wire
 *   [name]═════&mut══════►  mutable borrow wire
 *   [name]╌╌╌╌ moved ╌╌╌   dead (moved out)
 *   [name]✗  dropped        dead (destructor run)
 *   [name]~~✗~~~~~~~~~~~~~~► DANGLING borrow (error)
 *   [name]▣ FileHandle       live resource wire
 *
 * For each event:
 *   1. Header: event number, op name, operands, BLOCKED marker
 *   2. Ownership + resource wires (current state after event)
 *   3. Borrow wires
 *   4. Diagnostics attached to this event (with provenance)
 */

#ifndef DIAGRAM_H
#define DIAGRAM_H

#include "checker.h"

typedef struct {
    int show_resources;    /* render resource wires separately         */
    int show_generations;  /* show generation number on vars           */
    int show_scope_depth;  /* annotate wires with scope depth          */
    int show_provenance;   /* show cause_event in diagnostics          */
    int compact;           /* one-line-per-var, skip empty sections    */
    int colour;            /* ANSI colour output                       */
} DiagOpts;

DiagOpts diag_default_opts(void);

void diag_render_event  (const BC *bc, int event_idx, const DiagOpts *opts);
void diag_render_all    (const BC *bc, const DiagOpts *opts);
void diag_render_final  (const BC *bc, const DiagOpts *opts);
void diag_render_summary(const BC *bc, const DiagOpts *opts);

#endif /* DIAGRAM_H */
