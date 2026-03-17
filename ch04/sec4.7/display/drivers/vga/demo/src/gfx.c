/*
 * gfx.c   2D graphics API implementation
 *
 * Covers:
 *  - Fixed-point matrix operations (ported from Matrix.java)
 *  - Shape / fill / line style builders
 *  - Scene (display list) management
 *  - High-level render entry point (delegates to raster.c)
 *  - Immediate-mode framebuffer helpers
 */

#include "gfx.h"
#include "raster.h"
#include <string.h>
#include <math.h>
#include <stdlib.h>

/* identity matrix */
const gfx_mat_t GFX_MAT_IDENTITY = {
    .a  = FX_ONE, .b = 0,
    .c  = 0,      .d = FX_ONE,
    .tx = 0,      .ty = 0
};

/* matrix operations */

/* Concatenate m1 then m2 (equivalent to Matrix.concat in Java).
   result = m1 * m2  (m1 applied first, then m2) */
gfx_mat_t gfx_mat_concat(gfx_mat_t m1, gfx_mat_t m2) {
    gfx_mat_t r;
    r.a  = FX_MUL(m1.a, m2.a) + FX_MUL(m1.b, m2.c);
    r.b  = FX_MUL(m1.a, m2.b) + FX_MUL(m1.b, m2.d);
    r.c  = FX_MUL(m1.c, m2.a) + FX_MUL(m1.d, m2.c);
    r.d  = FX_MUL(m1.c, m2.b) + FX_MUL(m1.d, m2.d);
    r.tx = FX_ROUND(FX_MUL(FX_FROM_INT(m1.tx), m2.a)
                  + FX_MUL(FX_FROM_INT(m1.ty), m2.c)) + m2.tx;
    r.ty = FX_ROUND(FX_MUL(FX_FROM_INT(m1.tx), m2.b)
                  + FX_MUL(FX_FROM_INT(m1.ty), m2.d)) + m2.ty;
    return r;
}

gfx_mat_t gfx_mat_invert(gfx_mat_t m) {
    gfx_mat_t r = GFX_MAT_IDENTITY;
    if (m.b == 0 && m.c == 0) {
        /* axis-aligned   simple reciprocal */
        if (m.a != 0) r.a = (fx32)(((int64_t)FX_ONE * FX_ONE) / m.a);
        if (m.d != 0) r.d = (fx32)(((int64_t)FX_ONE * FX_ONE) / m.d);
        r.tx = -FX_ROUND(FX_MUL(r.a, FX_FROM_INT(m.tx)));
        r.ty = -FX_ROUND(FX_MUL(r.d, FX_FROM_INT(m.ty)));
    } else {
        double fa = m.a / 65536.0, fb = m.b / 65536.0;
        double fc = m.c / 65536.0, fd = m.d / 65536.0;
        double det = fa * fd - fb * fc;
        if (det != 0.0) {
            det = 1.0 / det;
            r.a  = (fx32)( fd * det * 65536.0);
            r.b  = (fx32)(-fb * det * 65536.0);
            r.c  = (fx32)(-fc * det * 65536.0);
            r.d  = (fx32)( fa * det * 65536.0);
            /* translate: -inv * t */
            double nx = -(r.a / 65536.0 * m.tx + r.b / 65536.0 * m.ty);
            double ny = -(r.c / 65536.0 * m.tx + r.d / 65536.0 * m.ty);
            r.tx = (int32_t)nx;
            r.ty = (int32_t)ny;
        }
    }
    return r;
}

gfx_mat_t gfx_mat_scale(float sx, float sy) {
    gfx_mat_t m = GFX_MAT_IDENTITY;
    m.a = (fx32)(sx * 65536.0f);
    m.d = (fx32)(sy * 65536.0f);
    return m;
}

gfx_mat_t gfx_mat_rotate(float radians) {
    float s = sinf(radians), c = cosf(radians);
    gfx_mat_t m = GFX_MAT_IDENTITY;
    m.a =  (fx32)(c * 65536.0f);
    m.b =  (fx32)(s * 65536.0f);
    m.c = -(fx32)(s * 65536.0f);
    m.d =  (fx32)(c * 65536.0f);
    return m;
}

gfx_mat_t gfx_mat_translate(int32_t tx, int32_t ty) {
    gfx_mat_t m = GFX_MAT_IDENTITY;
    m.tx = tx; m.ty = ty;
    return m;
}

void gfx_mat_transform(gfx_mat_t m, int32_t x, int32_t y, int32_t *ox, int32_t *oy) {
    fx32 fx = FX_FROM_INT(x), fy = FX_FROM_INT(y);
    *ox = FX_ROUND(FX_MUL(m.a, fx) + FX_MUL(m.b, fy)) + m.tx;
    *oy = FX_ROUND(FX_MUL(m.c, fx) + FX_MUL(m.d, fy)) + m.ty;
}

/* shape builder */

void gfx_shape_init(gfx_shape_t *s) {
    memset(s, 0, sizeof(*s));
}

uint8_t gfx_shape_add_fill_solid(gfx_shape_t *s, gfx_color_t color) {
    if (s->n_fills >= GFX_MAX_FILLS - 1) return 0;
    uint8_t idx = ++s->n_fills;          /* 1-based */
    s->fills[idx].type  = GFX_FILL_SOLID;
    s->fills[idx].solid = color;
    return idx;
}

uint8_t gfx_shape_add_fill_linear(gfx_shape_t *s, gfx_mat_t mat, const gfx_stop_t *stops, uint8_t n) {
    if (s->n_fills >= GFX_MAX_FILLS - 1) return 0;
    uint8_t idx = ++s->n_fills;
    gfx_fill_t *f = &s->fills[idx];
    f->type = GFX_FILL_LINEAR;
    f->mat = mat;
    f->n_stops = n < GFX_MAX_STOPS ? n : GFX_MAX_STOPS;
    memcpy(f->stops, stops, f->n_stops * sizeof(gfx_stop_t));
    return idx;
}

uint8_t gfx_shape_add_fill_radial(gfx_shape_t *s, gfx_mat_t mat, const gfx_stop_t *stops, uint8_t n) {
    uint8_t idx = gfx_shape_add_fill_linear(s, mat, stops, n);
    if (idx) s->fills[idx].type = GFX_FILL_RADIAL;
    return idx;
}

uint8_t gfx_shape_add_line(gfx_shape_t *s, uint16_t width, gfx_color_t color) {
    if (s->n_lines >= GFX_MAX_LINES - 1) return 0;
    uint8_t idx = ++s->n_lines;
    s->lines[idx].width = width;
    s->lines[idx].color = color;
    return idx;
}

void gfx_shape_move(gfx_shape_t *s, int16_t x, int16_t y, uint8_t f0, uint8_t f1, uint8_t ls) {
    if (s->n_cmds >= GFX_MAX_CMDS) return;
    gfx_cmd_t *c = &s->cmds[s->n_cmds++];
    c->type = GFX_CMD_MOVE;
    c->x = x; c->y = y;
    c->f0 = f0; c->f1 = f1; c->ls = ls;
}

void gfx_shape_line(gfx_shape_t *s, int16_t x, int16_t y) {
    if (s->n_cmds >= GFX_MAX_CMDS) return;
    gfx_cmd_t *c = &s->cmds[s->n_cmds++];
    c->type = GFX_CMD_LINE;
    c->x = x; c->y = y;
}

void gfx_shape_curve(gfx_shape_t *s, int16_t cx, int16_t cy, int16_t x, int16_t y) {
    if (s->n_cmds >= GFX_MAX_CMDS) return;
    gfx_cmd_t *c = &s->cmds[s->n_cmds++];
    c->type = GFX_CMD_CURVE;
    c->cx = cx; c->cy = cy;
    c->x  = x;  c->y  = y;
}


/* scene */

void gfx_scene_init(gfx_scene_t *scene) {
    memset(scene, 0, sizeof(*scene));
}

gfx_obj_t *gfx_scene_alloc(gfx_scene_t *scene) {
    for (int i = 0; i < GFX_MAX_OBJECTS; i++) {
        if (!(scene->used & (1u << i))) {
            scene->used |= (1u << i);
            memset(&scene->pool[i], 0, sizeof(gfx_obj_t));
            return &scene->pool[i];
        }
    }
    return NULL;
}

void gfx_scene_free(gfx_scene_t *scene, gfx_obj_t *obj) {
    int idx = (int)(obj - scene->pool);
    if (idx >= 0 && idx < GFX_MAX_OBJECTS)
        scene->used &= ~(1u << idx);
}

/* Insert sorted by depth (ascending).  Replaces existing at same depth. */
gfx_obj_t *gfx_scene_place(gfx_scene_t *scene, gfx_shape_t *shape, uint16_t depth, gfx_mat_t mat, gfx_cx_t cx) {
    /* remove existing at this depth first */
    gfx_scene_remove(scene, depth);

    gfx_obj_t *obj = gfx_scene_alloc(scene);
    if (!obj) return NULL;
    obj->shape = shape;
    obj->mat   = mat;
    obj->cx    = cx;
    obj->depth = depth;

    /* insert into sorted linked list */
    gfx_obj_t **pp = &scene->head;
    while (*pp && (*pp)->depth <= depth)
        pp = &(*pp)->next;
    obj->next = *pp;
    *pp = obj;
    return obj;
}

void gfx_scene_remove(gfx_scene_t *scene, uint16_t depth) {
    gfx_obj_t **pp = &scene->head;
    while (*pp) {
        if ((*pp)->depth == depth) {
            gfx_obj_t *del = *pp;
            *pp = del->next;
            gfx_scene_free(scene, del);
            return;
        }
        pp = &(*pp)->next;
    }
}


/* rendering */

void gfx_render_obj(const gfx_obj_t *obj, gfx_color_t *fb) {
    const gfx_shape_t *s = obj->shape;
    if (!s || !s->n_cmds) return;

    /* fills */
    if (s->n_fills)
        raster_shape(fb, obj->mat,
                     s->fills, s->n_fills,
                     obj->cx,
                     s->cmds,  s->n_cmds);
    /* strokes */
    if (s->n_lines)
        raster_stroke(fb, obj->mat,
                      s->lines, s->n_lines,
                      obj->cx,
                      s->cmds,  s->n_cmds);
}

void gfx_render(const gfx_scene_t *scene, gfx_color_t bg, gfx_color_t *fb) {
    gfx_fb_clear(fb, bg);
    for (const gfx_obj_t *o = scene->head; o; o = o->next)
        gfx_render_obj(o, fb);
}


/* immediate-mode framebuffer helpers */

void gfx_fb_clear(gfx_color_t *fb, gfx_color_t c) {
    /* Unroll: fill as 32-bit pairs for speed */
    uint32_t v32 = ((uint32_t)c << 16) | c;
    uint32_t *p = (uint32_t *)fb;
    for (int i = 0; i < GFX_W * GFX_H / 2; i++) p[i] = v32;
}

void gfx_fb_pixel(gfx_color_t *fb, int x, int y, gfx_color_t c) {
    if ((unsigned)x < GFX_W && (unsigned)y < GFX_H)
        fb[y * GFX_W + x] = c;
}

void gfx_fb_hline(gfx_color_t *fb, int x, int y, int w, gfx_color_t c) {
    if ((unsigned)y >= GFX_H) return;
    if (x < 0) { w += x; x = 0; }
    if (x + w > GFX_W) w = GFX_W - x;
    if (w <= 0) return;
    gfx_color_t *p = fb + y * GFX_W + x;
    /* align to 32-bit boundary */
    if (((uintptr_t)p & 2) && w > 0) { *p++ = c; w--; }
    /* bulk 32-bit writes (2 pixels at a time) */
    uint32_t v32 = ((uint32_t)c << 16) | c;
    uint32_t *wp = (uint32_t *)p;
    for (; w >= 2; w -= 2) *wp++ = v32;
    if (w) *(gfx_color_t *)wp = c;
}

void gfx_fb_vline(gfx_color_t *fb, int x, int y, int h, gfx_color_t c) {
    if ((unsigned)x >= GFX_W) return;
    if (y < 0) { h += y; y = 0; }
    if (y + h > GFX_H) h = GFX_H - y;
    for (int i = 0; i < h; i++) fb[(y+i) * GFX_W + x] = c;
}

void gfx_fb_rect(gfx_color_t *fb, int x, int y, int w, int h, gfx_color_t c) {
    for (int dy = 0; dy < h; dy++)
        gfx_fb_hline(fb, x, y + dy, w, c);
}

/* Bresenham line */
void gfx_fb_line(gfx_color_t *fb, int x0, int y0, int x1, int y1, gfx_color_t c) {
    int dx = abs(x1 - x0), dy = abs(y1 - y0);
    int sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
    int err = dx - dy;
    while (1) {
        gfx_fb_pixel(fb, x0, y0, c);
        if (x0 == x1 && y0 == y1) break;
        int e2 = 2 * err;
        if (e2 > -dy) { err -= dy; x0 += sx; }
        if (e2 <  dx) { err += dx; y0 += sy; }
    }
}

/* experiment wu ..
static inline void gfx_fb_pixel_alpha(gfx_color_t *fb, int x, int y, gfx_color_t c, int alpha) {
    gfx_color_t *dst = &fb[y * GFX_W + x];
    gfx_color_t bg   = *dst;

    int a  = alpha;
    int ia = 255 - a;

    uint8_t r = (GFX_R(c) * a + GFX_R(bg) * ia) >> 8;
    uint8_t g = (GFX_G(c) * a + GFX_G(bg) * ia) >> 8;
    uint8_t b = (GFX_B(c) * a + GFX_B(bg) * ia) >> 8;

    *dst = GFX_RGB(r, g, b);
}
*/