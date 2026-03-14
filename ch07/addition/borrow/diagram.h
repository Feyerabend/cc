/*
 * diagram.h    Renderer for BC events and diagnostics.
 * Knows nothing about how checking decisions are made.
 */

#ifndef DIAGRAM_H
#define DIAGRAM_H

#include "checker.h"

typedef struct {
    int show_resources;
    int show_regions;
    int show_generations;
    int show_scope_depth;
    int show_provenance;
    int compact;
    int colour;
} DiagOpts;

DiagOpts diag_default_opts(void);

void diag_render_event  (const BC *bc, int event_idx, const DiagOpts *opts);
void diag_render_all    (const BC *bc, const DiagOpts *opts);
void diag_render_summary(const BC *bc, const DiagOpts *opts);

#endif /* DIAGRAM_H */
