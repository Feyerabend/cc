/*
 * gfx.h  2D vector graphics API for Pico 2 VGA
 *
 * Inspired by the Flash (SWF) Java renderer:
 *  Matrix          gfx_mat_t     (16.16 fixed-point affine)
 *  ColorTransform  gfx_cx_t
 *  RColor          gfx_fill_t   (solid / linear / radial gradient)
 *  SCharacter      gfx_shape_t  (fill styles + line styles + path)
 *  DisplayList     gfx_scene_t  (depth-sorted objects)
 *
 * Coordinate system: pixels (integers).  Path commands are in shape-local
 * space; the per-object matrix maps them to screen space.
 *
 * Colors: RGB565 throughout (matches the VGA framebuffer format).
 */

#pragma once
#include <stdint.h>
#include <stdbool.h>

/* -- screen constants */
#define GFX_W  320
#define GFX_H  240

/* -- fixed-point 16.16 */
typedef int32_t  fx32;        /* 16.16 fixed point                            */
#define FX_ONE   0x00010000   /* 1.0                                          */
#define FX_HALF  0x00008000   /* 0.5  (used for rounding)                     */
#define FX_MUL(a,b) ((fx32)(((int64_t)(a)*(b)+FX_HALF)>>16))
#define FX_DIV(a,b) ((fx32)(((int64_t)(a)<<16)/(b)))
#define FX_INT(a)   ((a)>>16)
#define FX_FRAC(a)  ((a)&0xFFFF)
#define FX_FROM_INT(a) ((fx32)(a)<<16)
#define FX_ROUND(a) (FX_INT((a)+FX_HALF))

/* -- RGB565 color */
typedef uint16_t gfx_color_t;

#define GFX_RGB(r,g,b) ((gfx_color_t)((((r)&0xF8u)<<8)|(((g)&0xFCu)<<3)|((b)>>3)))
#define GFX_R(c) ((uint8_t)(((c)>>8)&0xF8u))
#define GFX_G(c) ((uint8_t)(((c)>>3)&0xFCu))
#define GFX_B(c) ((uint8_t)(((c)<<3)&0xF8u))

/* common colors */
#define GFX_BLACK   GFX_RGB(  0,  0,  0)
#define GFX_WHITE   GFX_RGB(255,255,255)
#define GFX_RED     GFX_RGB(255,  0,  0)
#define GFX_GREEN   GFX_RGB(  0,255,  0)
#define GFX_BLUE    GFX_RGB(  0,  0,255)
#define GFX_YELLOW  GFX_RGB(255,255,  0)
#define GFX_CYAN    GFX_RGB(  0,255,255)
#define GFX_MAGENTA GFX_RGB(255,  0,255)

/* -- color transform (like Flash ColorTransform) */
/* result = clamp( channel * mul/256 + add ) */
typedef struct {
    int16_t r_mul, g_mul, b_mul;   /* default 256  (= x1.0) */
    int16_t r_add, g_add, b_add;   /* default 0 */
} gfx_cx_t;

static inline gfx_color_t gfx_cx_apply(gfx_cx_t cx, gfx_color_t c) {
    int r = GFX_R(c) * cx.r_mul / 256 + cx.r_add;
    int g = GFX_G(c) * cx.g_mul / 256 + cx.g_add;
    int b = GFX_B(c) * cx.b_mul / 256 + cx.b_add;
    r = r<0?0:r>255?255:r;
    g = g<0?0:g>255?255:g;
    b = b<0?0:b>255?255:b;
    return GFX_RGB(r, g, b);
}

/* -- 2 x 3 affine matrix (16.16 fixed-point scale/rotate, integer translate) - */
/*  |a  b  tx|   */
/*  |c  d  ty|  (same layout as Flash / SWF Matrix)  */
typedef struct {
    fx32 a, b, c, d;   /* 16.16  identity: a = d = FX_ONE, b = c = 0  */
    int32_t tx, ty;    /* pixels (integer) */
} gfx_mat_t;

extern const gfx_mat_t GFX_MAT_IDENTITY;

gfx_mat_t gfx_mat_concat(gfx_mat_t m1, gfx_mat_t m2);
gfx_mat_t gfx_mat_invert(gfx_mat_t m);
gfx_mat_t gfx_mat_scale(float sx, float sy);
gfx_mat_t gfx_mat_rotate(float radians);
gfx_mat_t gfx_mat_translate(int32_t tx, int32_t ty);

/* transform a point (integer in, integer out, rounding) */
void gfx_mat_transform(gfx_mat_t m, int32_t x, int32_t y, int32_t *ox, int32_t *oy);

/* -- fill style  */
#define GFX_MAX_STOPS  8

typedef enum {
    GFX_FILL_SOLID  = 0,
    GFX_FILL_LINEAR = 1,   /* linear gradient along x-axis in gradient space */
    GFX_FILL_RADIAL = 2,   /* radial gradient centred at origin               */
} gfx_fill_type_t;

typedef struct {
    uint8_t     ratio;  /* 0-255, maps to [0,1] along gradient axis */
    gfx_color_t color;
} gfx_stop_t;

typedef struct {
    gfx_fill_type_t type;
    union {
        gfx_color_t solid;          /* GFX_FILL_SOLID */
        struct {                     /* GFX_FILL_LINEAR / GFX_FILL_RADIAL */
            gfx_mat_t  mat;          /* gradient-space   shape-space transform */
            gfx_stop_t stops[GFX_MAX_STOPS];
            uint8_t    n_stops;
        };
    };
} gfx_fill_t;

/* -- line style */
typedef struct {
    uint16_t    width;   /* pixels x 256  (8.8 fixed, 0 = hairline) */
    gfx_color_t color;
} gfx_line_t;

/* -- path commands */
/* Coordinates are in shape-local pixel space. */
/* fill0 = fill to the LEFT of the directed edge (winding convention)  */
/* fill1 = fill to the RIGHT  */
/* A state record (move/style-change) always precedes geometry.  */
typedef enum {
    GFX_CMD_MOVE  = 0,  /* moveTo(x,y); also sets f0,f1,ls */
    GFX_CMD_LINE  = 1,  /* lineTo(x,y) */
    GFX_CMD_CURVE = 2,  /* quadraticCurveTo(cx,cy, x,y) */
} gfx_cmd_type_t;

typedef struct {
    gfx_cmd_type_t type;
    uint8_t        f0, f1;  /* fill style indices (1-based); 0 = none    */
    uint8_t        ls;      /* line style index  (1-based); 0 = none     */
    int16_t        x,  y;   /* endpoint (or destination of move)         */
    int16_t        cx, cy;  /* control point (GFX_CMD_CURVE only)        */
} gfx_cmd_t;

/* -- shape */
#define GFX_MAX_FILLS  16
#define GFX_MAX_LINES   8
#define GFX_MAX_CMDS  512

typedef struct {
    gfx_fill_t fills[GFX_MAX_FILLS]; /* 1-indexed (fills[0] unused) */
    gfx_line_t lines[GFX_MAX_LINES]; /* 1-indexed (lines[0] unused) */
    uint8_t    n_fills, n_lines;

    gfx_cmd_t  cmds[GFX_MAX_CMDS];
    uint16_t   n_cmds;
} gfx_shape_t;

/* -- shape builder helpers */
void gfx_shape_init(gfx_shape_t *s);

/* returns 1-based fill index */
uint8_t gfx_shape_add_fill_solid(gfx_shape_t *s, gfx_color_t color);
uint8_t gfx_shape_add_fill_linear(gfx_shape_t *s, gfx_mat_t mat, const gfx_stop_t *stops, uint8_t n);
uint8_t gfx_shape_add_fill_radial(gfx_shape_t *s, gfx_mat_t mat, const gfx_stop_t *stops, uint8_t n);
/* returns 1-based line index */
uint8_t gfx_shape_add_line(gfx_shape_t *s, uint16_t width, gfx_color_t color);

/* path commands  call after adding all styles */
void gfx_shape_move (gfx_shape_t *s, int16_t x, int16_t y, uint8_t f0, uint8_t f1, uint8_t ls);
void gfx_shape_line (gfx_shape_t *s, int16_t x, int16_t y);
void gfx_shape_curve(gfx_shape_t *s, int16_t cx, int16_t cy, int16_t x, int16_t y);

/* -- display object  */
typedef struct gfx_obj gfx_obj_t;
struct gfx_obj {
    gfx_shape_t  *shape;
    gfx_mat_t     mat;
    gfx_cx_t      cx;          /* color transform applied to all fills  */
    uint16_t      depth;       /* painter's sort key (ascending = back-->front)*/
    gfx_obj_t    *next;        /* intrusive linked list for scene  */
};

/* -- scene (display list) */
#define GFX_MAX_OBJECTS  64

typedef struct {
    gfx_obj_t  pool[GFX_MAX_OBJECTS];
    uint32_t   used;         /* bitmask of used slots */
    gfx_obj_t *head;         /* linked list sorted by depth */
} gfx_scene_t;

void gfx_scene_init  (gfx_scene_t *scene);
gfx_obj_t *gfx_scene_alloc (gfx_scene_t *scene);
void gfx_scene_free  (gfx_scene_t *scene, gfx_obj_t *obj);
/* insert / update object at given depth (replaces existing at same depth) */
gfx_obj_t *gfx_scene_place (gfx_scene_t *scene, gfx_shape_t *shape, uint16_t depth, gfx_mat_t mat, gfx_cx_t cx);
void gfx_scene_remove(gfx_scene_t *scene, uint16_t depth);

/* -- rendering */
/* Render the entire scene into a 320 x 240 RGB565 framebuffer.
   Call from core 0 while core 1 displays the other buffer. */
void gfx_render(const gfx_scene_t *scene, gfx_color_t bg, gfx_color_t *fb);

/* lower-level: render a single object into fb */
void gfx_render_obj(const gfx_obj_t *obj, gfx_color_t *fb);

/* -- convenience: instant pixel / line / rect (no shape needed) */
void gfx_fb_clear (gfx_color_t *fb, gfx_color_t c);
void gfx_fb_pixel (gfx_color_t *fb, int x, int y, gfx_color_t c);
void gfx_fb_hline (gfx_color_t *fb, int x, int y, int w, gfx_color_t c);
void gfx_fb_vline (gfx_color_t *fb, int x, int y, int h, gfx_color_t c);
void gfx_fb_rect  (gfx_color_t *fb, int x, int y, int w, int h, gfx_color_t c);
void gfx_fb_line  (gfx_color_t *fb, int x0, int y0, int x1, int y1, gfx_color_t c);
