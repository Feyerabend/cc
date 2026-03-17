/*
 * raster.c   scanline polygon rasterizer
 *
 * Algorithm (from Flash/DisplayList.PaintBits, ported to C):
 *
 *  1. Walk path commands; apply matrix to vertices.
 *  2. For each straight segment (beziers subdivided), emit an edge into a
 *     y-indexed bucket table.
 *  3. For each scanline y (top-->bottom):
 *     a. Move edges whose y1 == y from bucket to active edge list (AEL).
 *     b. Sort AEL by current x.
 *     c. Walk AEL in pairs, toggling fill state at each edge (even-odd).
 *     d. Fill horizontal spans between matched pairs.
 *     e. Advance each edge's x by dx; remove edges where y2 == y+1.
 *  4. For strokes: re-walk path, draw Bresenham segments with the given width.
 *
 * Gradient fills: at each filled span a colour is looked up from a 256-entry
 * ramp computed from the stop list.  The gradient matrix maps screen --> gradient
 * space to get the sample position.
 */

#include "raster.h"
#include "gfx.h"
#include <string.h>
#include <stdlib.h>
#include <math.h>

/* clipping */
#define CLIP_X(x) ((x)<0?0:(x)>=GFX_W?GFX_W-1:(x))
#define CLIP_Y(y) ((y)<0?0:(y)>=GFX_H?GFX_H-1:(y))

/* gradient ramp */
/* Build a 256-entry RGB565 ramp from stops.  Stored on the stack. */
static void build_ramp(uint16_t ramp[256], const gfx_stop_t *stops, uint8_t n, gfx_cx_t cx) {
    if (!n) { for (int i=0;i<256;i++) ramp[i]=0; return; }
    int si = 0;
    for (int i = 0; i < 256; i++) {
        while (si < n-1 && stops[si+1].ratio <= i) si++;
        int a_ratio = stops[si].ratio;
        int b_ratio = (si < n-1) ? stops[si+1].ratio : 255;
        gfx_color_t ca = stops[si].color;
        gfx_color_t cb = (si < n-1) ? stops[si+1].color : stops[n-1].color;
        int t = (b_ratio > a_ratio)
              ? ((i - a_ratio) * 256) / (b_ratio - a_ratio)
              : 0;
        int r = (GFX_R(ca) * (256-t) + GFX_R(cb) * t) >> 8;
        int g = (GFX_G(ca) * (256-t) + GFX_G(cb) * t) >> 8;
        int b = (GFX_B(ca) * (256-t) + GFX_B(cb) * t) >> 8;
        /* apply colour transform */
        r = r * cx.r_mul / 256 + cx.r_add; r = r<0?0:r>255?255:r;
        g = g * cx.g_mul / 256 + cx.g_add; g = g<0?0:g>255?255:g;
        b = b * cx.b_mul / 256 + cx.b_add; b = b<0?0:b>255?255:b;
        ramp[i] = GFX_RGB(r, g, b);
    }
}

/* fill span */
static void fill_span(gfx_color_t *row,
                       int x0, int x1, int y,
                       const gfx_fill_t *fill, gfx_cx_t cx,
                       uint16_t ramp[256] /* scratch, pre-filled if gradient */)
{
    if (x0 > x1) { int t=x0; x0=x1; x1=t; }
    x0 = CLIP_X(x0); x1 = CLIP_X(x1);
    if (x0 > x1) return;

    if (fill->type == GFX_FILL_SOLID) {
        gfx_color_t c = gfx_cx_apply(cx, fill->solid);
        gfx_color_t *p = row + x0;
        int n = x1 - x0 + 1;
        /* align to 32-bit boundary */
        if (((uintptr_t)p & 2) && n > 0) { *p++ = c; n--; }
        /* bulk 32-bit writes (2 pixels at a time) */
        uint32_t v32 = ((uint32_t)c << 16) | c;
        uint32_t *wp = (uint32_t *)p;
        for (; n >= 2; n -= 2) *wp++ = v32;
        if (n) *(gfx_color_t *)wp = c;
        return;
    }

    /* gradient: map (x, y) through the inverse gradient matrix */
    /* gradient space: 0-256 maps to x in gradient coords */
    const gfx_mat_t *m = &fill->mat;
    /* We need inv(m) to map screen --> gradient.  Pre-compute per span. */
    /* For speed, use approximate: sample at x0, step by column. */
    /* inv(m).a is the x step per screen pixel. */
    /* This is precomputed from gfx_mat_invert in a full implementation; */
    /* here we re-derive cheaply for axis-aligned gradients (common case). */

    /* Simple approach: compute t for each pixel using the transform. */
    /* grad_x_at_screen(sx, sy) = m.a * sx + m.b * sy + m.tx */
    /* For a linear gradient, t = clamp(grad_x / 256, 0, 255) */
    for (int x = x0; x <= x1; x++) {
        int gx = FX_ROUND(FX_MUL(m->a, FX_FROM_INT(x)) + FX_MUL(m->b, FX_FROM_INT(y))) + m->tx;
        int gy = FX_ROUND(FX_MUL(m->c, FX_FROM_INT(x)) + FX_MUL(m->d, FX_FROM_INT(y))) + m->ty;
        int t;
        if (fill->type == GFX_FILL_LINEAR) {
            t = gx;
        } else { /* radial */
            t = (int)sqrtf((float)(gx*gx + gy*gy));
        }
        t = t < 0 ? 0 : t > 255 ? 255 : t;
        row[x] = ramp[t];
    }
}

/* edge emission */
static void emit_edge(raster_ctx_t *ctx, int x0, int y0, int x1, int y1, uint8_t fill_id) 
{
    /* horizontal edges contribute nothing */
    if (y0 == y1) return;

    /* ensure y0 <= y1 */
    int8_t dir = 1;
    if (y0 > y1) { int t; t=x0; x0=x1; x1=t; t=y0; y0=y1; y1=t; dir=-1; }

    /* clip to framebuffer vertically */
    if (y1 <= 0 || y0 >= GFX_H) return;
    int cy0 = y0 < 0 ? 0 : y0;
    int cy1 = y1 > GFX_H ? GFX_H : y1;

    if (ctx->pool_used >= RASTER_MAX_EDGES) return;
    raster_edge_t *e = &ctx->pool[ctx->pool_used++];

    int dy = y1 - y0;
    e->y1      = (int16_t)cy0;
    e->y2      = (int16_t)cy1;
    e->dx      = FX_DIV((x1 - x0) << 16, dy);   /* 16.16 step per scanline */
    e->x       = FX_FROM_INT(x0);
    if (cy0 > y0) e->x += (int32_t)(cy0 - y0) * e->dx;
    e->fill_id = fill_id;
    e->dir     = dir;
    e->next    = ctx->y_table[cy0];
    ctx->y_table[cy0] = e;
}

/* bezier subdivision    line segments */
/* De Casteljau for quadratic bezier; emits edges when flat enough. */
static void subdivide_curve(raster_ctx_t *ctx,
                             int ax, int ay, int cx, int cy, int bx, int by,
                             uint8_t fill_id, int depth)
{
    /* flatness test: distance of control point from line ab */
    int mx = (ax + bx) / 2, my = (ay + by) / 2;
    int ex = cx - mx,       ey = cy - my;
    int flat = abs(ex) + abs(ey);  /* taxicab flatness */

    if (flat <= RASTER_CURVE_TOL || depth >= 8) {
        emit_edge(ctx, ax, ay, bx, by, fill_id);
        return;
    }

    /* split at t=0.5 */
    int m1x = (ax + cx) / 2, m1y = (ay + cy) / 2;
    int m2x = (cx + bx) / 2, m2y = (cy + by) / 2;
    int m3x = (m1x + m2x) / 2, m3y = (m1y + m2y) / 2;
    subdivide_curve(ctx, ax, ay, m1x, m1y, m3x, m3y, fill_id, depth+1);
    subdivide_curve(ctx, m3x, m3y, m2x, m2y, bx, by, fill_id, depth+1);
}

/* build edge table from path commands */
static void build_edges(raster_ctx_t *ctx, gfx_mat_t mat,
                         const gfx_cmd_t *cmds, uint16_t n_cmds)
{
    int px = 0, py = 0;   /* current transformed screen position */
    uint8_t f0 = 0, f1 = 0;

    for (uint16_t i = 0; i < n_cmds; i++) {
        const gfx_cmd_t *cmd = &cmds[i];
        switch (cmd->type) {

        case GFX_CMD_MOVE: {
            int32_t nx, ny;
            gfx_mat_transform(mat, cmd->x, cmd->y, &nx, &ny);
            px = (int)nx; py = (int)ny;
            f0 = cmd->f0; f1 = cmd->f1;
            break;
        }

        case GFX_CMD_LINE: {
            int32_t nx, ny;
            gfx_mat_transform(mat, cmd->x, cmd->y, &nx, &ny);
            /* emit for fill0 (left side, forward direction) */
            if (f0) emit_edge(ctx, px, py, (int)nx, (int)ny, f0);
            /* fill1 (right side, same geometry    even-odd handles both) */
            if (f1 && f1 != f0) emit_edge(ctx, px, py, (int)nx, (int)ny, f1);
            px = (int)nx; py = (int)ny;
            break;
        }

        case GFX_CMD_CURVE: {
            int32_t cx2, cy2, ex, ey;
            gfx_mat_transform(mat, cmd->cx, cmd->cy, &cx2, &cy2);
            gfx_mat_transform(mat, cmd->x,  cmd->y,  &ex,  &ey);
            if (f0)
                subdivide_curve(ctx, px, py, (int)cx2, (int)cy2, (int)ex, (int)ey, f0, 0);
            if (f1 && f1 != f0)
                subdivide_curve(ctx, px, py, (int)cx2, (int)cy2, (int)ex, (int)ey, f1, 0);
            px = (int)ex; py = (int)ey;
            break;
        }
        }
    }
}

/* AEL insertion sort by current x */
static void ael_insert(raster_ctx_t *ctx, raster_edge_t *e)
{
    if (ctx->ael_n >= RASTER_MAX_ACTIVE) return;
    int pos = ctx->ael_n;
    /* insertion sort */
    while (pos > 0 && ctx->ael[pos-1]->x > e->x) {
        ctx->ael[pos] = ctx->ael[pos-1];
        pos--;
    }
    ctx->ael[pos] = e;
    ctx->ael_n++;
}

static void ael_sort(raster_ctx_t *ctx)
{
    /* Insertion sort (AEL is nearly sorted most frames) */
    for (int i = 1; i < ctx->ael_n; i++) {
        raster_edge_t *key = ctx->ael[i];
        int j = i - 1;
        while (j >= 0 && ctx->ael[j]->x > key->x) {
            ctx->ael[j+1] = ctx->ael[j];
            j--;
        }
        ctx->ael[j+1] = key;
    }
}

/* main rasterizer */
void raster_shape(gfx_color_t        *fb,
                  gfx_mat_t           mat,
                  const gfx_fill_t   *fills,
                  uint8_t             n_fills,
                  gfx_cx_t            cx,
                  const gfx_cmd_t    *cmds,
                  uint16_t            n_cmds)
{
    /* Static: raster_ctx_t is ~20 KB   far too large for the 8 KB core stack */
    static raster_ctx_t ctx;
    /* Static: gradient ramps, 16 fills x 512 bytes = 8 KB */
    static uint16_t ramps[GFX_MAX_FILLS][256];

    memset(&ctx, 0, sizeof(ctx));
    ctx.fb      = fb;
    ctx.fills   = fills;
    ctx.n_fills = n_fills;
    ctx.cx      = cx;

    /* Build edge table once for all fills (previously rebuilt per fill). */
    build_edges(&ctx, mat, cmds, n_cmds);
    if (ctx.pool_used == 0) return;

    /* Pre-build gradient ramps for all fills. */
    for (uint8_t fid = 1; fid <= n_fills; fid++) {
        if (fills[fid].type != GFX_FILL_SOLID)
            build_ramp(ramps[fid - 1], fills[fid].stops, fills[fid].n_stops, cx);
    }

    /* Single scanline pass   all fills rendered in one sweep. */
    for (int y = 0; y < GFX_H; y++) {

        /* 1. move new edges into AEL */
        raster_edge_t *e = ctx.y_table[y];
        while (e) {
            raster_edge_t *nxt = e->next;
            ael_insert(&ctx, e);
            e = nxt;
        }

        /* 2. sort AEL by x */
        ael_sort(&ctx);

        gfx_color_t *row = fb + y * GFX_W;

        /* 3. even-odd fill per fill id (one pass per fill over the AEL) */
        for (uint8_t fid = 1; fid <= n_fills; fid++) {
            const gfx_fill_t *fill = &fills[fid];
            uint16_t *ramp = ramps[fid - 1];
            int inside = 0, span_x = 0;
            for (int k = 0; k < ctx.ael_n; k++) {
                if (ctx.ael[k]->fill_id != fid) continue;
                int ex = FX_ROUND(ctx.ael[k]->x);
                if (inside) {
                    fill_span(row, span_x, ex - 1, y, fill, cx, ramp);
                    inside = 0;
                } else {
                    span_x = ex;
                    inside = 1;
                }
            }
        }

        /* 4. advance edges, remove finished ones */
        int write = 0;
        for (int k = 0; k < ctx.ael_n; k++) {
            raster_edge_t *ae = ctx.ael[k];
            ae->x += ae->dx;
            if (ae->y2 > y + 1)
                ctx.ael[write++] = ae;
        }
        ctx.ael_n = write;
    }
}

/* stroke rasterizer */
/* Simple Bresenham approach; thick lines (>1px) expand via multiple offsets.  */

static void stroke_line(gfx_color_t *fb,
                         int x0, int y0, int x1, int y1,
                         int half_w, gfx_color_t color)
{
    if (half_w <= 0) {
        gfx_fb_line(fb, x0, y0, x1, y1, color);
        return;
    }
    /* Thick: draw multiple offset lines.  For small widths this is fine.    */
    int dx = x1 - x0, dy = y1 - y0;
    float len = sqrtf((float)(dx*dx + dy*dy));
    if (len < 0.5f) return;
    float nx = -dy / len, ny = dx / len;
    for (int t = -half_w; t <= half_w; t++) {
        int ox = (int)(nx * t + 0.5f), oy = (int)(ny * t + 0.5f);
        gfx_fb_line(fb, x0+ox, y0+oy, x1+ox, y1+oy, color);
    }
}

/* probably got to go alpha here .. not retro but looks nicer with
   weird widths and curves.  Wu line algorithm is a bit more complex
   but not too bad.
   stroke rasterizer, antialiased */
/*
static void stroke_line_wu(gfx_color_t *fb,
                           int x0, int y0, int x1, int y1,
                           int half_w, gfx_color_t color)
{
    if (half_w <= 0) {
        gfx_fb_line_wu(fb, x0, y0, x1, y1, color);
        return;
    }

    int dx = x1 - x0, dy = y1 - y0;
    float len = sqrtf((float)(dx * dx + dy * dy));
    if (len < 0.5f) return;

    float nx = -dy / len, ny = dx / len;

    for (int t = -half_w; t <= half_w; t++) {
        int ox = (int)(nx * t + 0.5f), oy = (int)(ny * t + 0.5f);
        gfx_fb_line_wu(fb, x0 + ox, y0 + oy, x1 + ox, y1 + oy, color);
    }
}
*/

static void stroke_curve_seg(gfx_color_t *fb,
                              int ax, int ay, int cx, int cy, int bx, int by,
                              int half_w, gfx_color_t color, int depth)
{
    int mx = (ax+bx)/2, my = (ay+by)/2;
    int flat = abs(cx-mx) + abs(cy-my);
    if (flat <= 2 || depth >= 6) {
        stroke_line(fb, ax, ay, bx, by, half_w, color);
        return;
    }
    int m1x=(ax+cx)/2, m1y=(ay+cy)/2;
    int m2x=(cx+bx)/2, m2y=(cy+by)/2;
    int m3x=(m1x+m2x)/2, m3y=(m1y+m2y)/2;
    stroke_curve_seg(fb, ax, ay, m1x, m1y, m3x, m3y, half_w, color, depth+1);
    stroke_curve_seg(fb, m3x, m3y, m2x, m2y, bx, by, half_w, color, depth+1);
}

void raster_stroke(gfx_color_t        *fb,
                   gfx_mat_t           mat,
                   const gfx_line_t   *lines,
                   uint8_t             n_lines,
                   gfx_cx_t            cx,
                   const gfx_cmd_t    *cmds,
                   uint16_t            n_cmds)
{
    (void)n_lines;  /* bounds checking omitted: cur_ls is validated via cmd->ls */
    int32_t px = 0, py = 0;
    uint8_t cur_ls = 0;

    for (uint16_t i = 0; i < n_cmds; i++) {
        const gfx_cmd_t *cmd = &cmds[i];
        switch (cmd->type) {

        case GFX_CMD_MOVE: {
            int32_t nx, ny;
            gfx_mat_transform(mat, cmd->x, cmd->y, &nx, &ny);
            px = nx; py = ny;
            cur_ls = cmd->ls;
            break;
        }

        case GFX_CMD_LINE: {
            if (!cur_ls) { int32_t nx,ny; gfx_mat_transform(mat,cmd->x,cmd->y,&nx,&ny); px=nx;py=ny; break; }
            const gfx_line_t *ls = &lines[cur_ls];
            int32_t nx, ny;
            gfx_mat_transform(mat, cmd->x, cmd->y, &nx, &ny);
            gfx_color_t c = gfx_cx_apply(cx, ls->color);
            int half_w = ls->width / 512;   /* width is 8.8, half in pixels */
            stroke_line(fb, (int)px, (int)py, (int)nx, (int)ny, half_w, c);
            px = nx; py = ny;
            break;
        }

        case GFX_CMD_CURVE: {
            if (!cur_ls) { int32_t ex,ey; gfx_mat_transform(mat,cmd->x,cmd->y,&ex,&ey); px=ex;py=ey; break; }
            const gfx_line_t *ls = &lines[cur_ls];
            int32_t cx2,cy2,ex,ey;
            gfx_mat_transform(mat, cmd->cx, cmd->cy, &cx2, &cy2);
            gfx_mat_transform(mat, cmd->x,  cmd->y,  &ex,  &ey);
            gfx_color_t c = gfx_cx_apply(cx, ls->color);
            int half_w = ls->width / 512;
            stroke_curve_seg(fb,(int)px,(int)py,(int)cx2,(int)cy2,(int)ex,(int)ey,half_w,c,0);
            px = ex; py = ey;
            break;
        }
        }
    }
}
