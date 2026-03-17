/*
 * raster.h - scanline rasterizer (internal to gfx.c / raster.c)
 *
 * Inspired by DisplayList.PaintBits, REdge, Curve, RRun from the Flash Java.
 * Ported to C with these simplifications:
 *  - Bezier curves are subdivided into line segments before rasterization
 *    (simpler, fast enough at 320 x 240)
 *  - No antialiasing super-sample pass (single-pixel precision)
 *  - Even-odd fill rule only (matches the most common Flash usage)
 *  - Solid and gradient fills supported; bitmap fills omitted
 *
 * Memory is all stack / static  no malloc needed.
 */

#pragma once
#include "gfx.h"

/* -- tunables */
#define RASTER_MAX_EDGES      1024  /* total edge pool per render call        */
#define RASTER_MAX_ACTIVE      128  /* max simultaneous active edges          */
#define RASTER_CURVE_TOL         2  /* flatness tolerance (pixels) for bezier */

/* -- an edge as used by the scanline rasterizer */
/* Lines only (beziers pre-subdivided).  Sorted into a y-indexed bucket list.  */
typedef struct raster_edge {
    int16_t              y1, y2;    /* inclusive top, exclusive bottom          */
    fx32                 x;         /* current x at y = y1 (16.16)             */
    fx32                 dx;        /* x increment per scanline (16.16)        */
    uint8_t              fill_id;   /* 1-based fill style that this edge bounds */
    int8_t               dir;       /* +1 going down, -1 going up (winding)   */
    struct raster_edge  *next;      /* bucket list linkage                     */
} raster_edge_t;

/* -- rasterizer context (one per render call - lives on the stack) */
typedef struct {
    /* edge pool */
    raster_edge_t  pool[RASTER_MAX_EDGES];
    int            pool_used;

    /* y-indexed bucket: y_table[y] is the head of edges starting at y */
    raster_edge_t *y_table[GFX_H];

    /* active edge list (sorted by x each scanline) */
    raster_edge_t *ael[RASTER_MAX_ACTIVE];
    int            ael_n;

    /* output framebuffer */
    gfx_color_t   *fb;

    /* fill styles from the current shape (pointer, not copy) */
    const gfx_fill_t *fills;
    uint8_t           n_fills;

    /* color transform to apply to all fills */
    gfx_cx_t  cx;
} raster_ctx_t;


/* -- public interface (used by gfx.c) */

/* Rasterise one shape into fb.
   mat       shape-local --> screen transform (integer pixel space)
   fills     fill style array (1-indexed, fills[0] unused)
   n_fills   number of valid entries (so fills[1..n_fills] are valid)
   cx        colour transform
   cmds      path command array
   n_cmds    length
*/
void raster_shape(gfx_color_t        *fb,
                  gfx_mat_t           mat,
                  const gfx_fill_t   *fills,
                  uint8_t             n_fills,
                  gfx_cx_t            cx,
                  const gfx_cmd_t    *cmds,
                  uint16_t            n_cmds);

/* Draw a stroked outline of the same path.
   lines    line style array (1-indexed)
*/
void raster_stroke(gfx_color_t        *fb,
                   gfx_mat_t           mat,
                   const gfx_line_t   *lines,
                   uint8_t             n_lines,
                   gfx_cx_t            cx,
                   const gfx_cmd_t    *cmds,
                   uint16_t            n_cmds);
