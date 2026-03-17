/*
 * demo.c   animated 2D scene
 *
 * Shows off the gfx API:
 *   - Star with radial gradient fill + rotation
 *   - Diamond with curved sides (quadratic bezier), solid fill, stroke
 *   - Circular orbiter approximated with 16 bezier arcs
 *   - Background: immediate-mode sine-wave colour bands
 *
 * All shapes are built once in demo_init(); each frame only the scene's
 * object matrices and colour transforms are updated.
 */

#include "demo.h"
#include "gfx.h"
#include <math.h>
#include <string.h>

/* helpers */
#define PI  3.14159265358979f
#define TAU (2.0f * PI)

static inline int16_t rnd(float v) { return (int16_t)(v + 0.5f); }

/*  STAR (5-pointed, radial gradient)  */
static void build_star(gfx_shape_t *s) {
    gfx_shape_init(s);

    /* radial gradient: white centre .. deep purple rim */
    gfx_stop_t stops[3] = {
        { .ratio =   0, .color = GFX_RGB(255, 255, 200) },
        { .ratio = 140, .color = GFX_RGB(220,  80, 255) },
        { .ratio = 255, .color = GFX_RGB( 60,   0, 140) },
    };
    /* gradient matrix: scale so radius 50 maps to gradient position 255 */
    gfx_mat_t gm = gfx_mat_scale(255.0f / 50.0f, 255.0f / 50.0f);
    uint8_t f1 = gfx_shape_add_fill_radial(s, gm, stops, 3);

    /* outline */
    uint8_t l1 = gfx_shape_add_line(s, 256, GFX_RGB(255, 220, 255)); /* 1px */

    /* 5 outer points at radius 50, inner notches at radius 21  */
    const float outer = 50.0f, inner = 21.0f;
    const int   pts   = 5;

    /* Compute vertices */
    int16_t ox[5], oy[5], ix[5], iy[5];
    for (int i = 0; i < pts; i++) {
        float ao = (float)i * TAU / pts - PI / 2.0f;
        float ai = ao + PI / pts;
        ox[i] = rnd(cosf(ao) * outer);
        oy[i] = rnd(sinf(ao) * outer);
        ix[i] = rnd(cosf(ai) * inner);
        iy[i] = rnd(sinf(ai) * inner);
    }

    /* First move */
    gfx_shape_move(s, ox[0], oy[0], f1, 0, l1);
    for (int i = 0; i < pts; i++) {
        gfx_shape_line(s, ix[i],             iy[i]);
        gfx_shape_line(s, ox[(i+1) % pts],   oy[(i+1) % pts]);
    }
    /* close — back to first outer point */
    gfx_shape_line(s, ox[0], oy[0]);
}

/*  DIAMOND (bulging sides via quadratic beziers, solid fill) */
static void build_diamond(gfx_shape_t *s) {
    gfx_shape_init(s);

    uint8_t f1 = gfx_shape_add_fill_solid(s, GFX_RGB(0, 200, 255));
    uint8_t l1 = gfx_shape_add_line(s, 512, GFX_RGB(255, 255, 255)); /* 2px */

    /* corners */
    int16_t vx[4] = {   0, 36,  0, -36 };
    int16_t vy[4] = { -36,  0, 30,    0 };
    /* bezier control points (bulge outward) */
    int16_t cx[4] = {  24, 24, -24, -24 };
    int16_t cy[4] = { -24, 18,  18, -24 };

    gfx_shape_move(s, vx[0], vy[0], f1, 0, l1);
    for (int i = 0; i < 4; i++) {
        int ni = (i + 1) % 4;
        gfx_shape_curve(s, cx[i], cy[i], vx[ni], vy[ni]);
    }
}

/* CIRCLE (16-segment bezier approximation, solid fill)  */
/* Each arc quarter is split into 4 sub-arcs.
   Control point factor for quadratic bezier circle: k approx. 0.5523 */
static void build_circle(gfx_shape_t *s, float radius) {
    gfx_shape_init(s);

    uint8_t f1 = gfx_shape_add_fill_solid(s, GFX_RGB(255, 120, 0));
    /* no stroke */

    const int segs = 16;
    float k = 0.5523f * (TAU / segs) / (PI / 2.0f); /* control arm scale */

    /* first point */
    float a0 = 0.0f;
    int16_t sx = rnd(cosf(a0) * radius), sy = rnd(sinf(a0) * radius);
    gfx_shape_move(s, sx, sy, f1, 0, 0);

    for (int i = 0; i < segs; i++) {
        float a1 = (float)(i + 1) * TAU / segs;
        float am = ((float)i + 0.5f) * TAU / segs;
        int16_t ex = rnd(cosf(a1) * radius);
        int16_t ey = rnd(sinf(a1) * radius);
        /* control point: midpoint pushed outward */
        int16_t qx = rnd(cosf(am) * radius / cosf(TAU / segs / 2.0f));
        int16_t qy = rnd(sinf(am) * radius / cosf(TAU / segs / 2.0f));
        gfx_shape_curve(s, qx, qy, ex, ey);
    }
    (void)k;
}

/*  BACKGROUND  immediate-mode sine bands  */
static void draw_background(gfx_color_t *fb, float t) {
    for (int y = 0; y < GFX_H; y++) {
        float wave = sinf(y * 0.05f + t * 1.3f) * 0.5f + 0.5f;
        float wave2= sinf(y * 0.09f - t * 0.8f) * 0.5f + 0.5f;
        uint8_t r = (uint8_t)(wave  * 40.0f + 10.0f);
        uint8_t g = (uint8_t)(wave2 * 20.0f +  5.0f);
        uint8_t b = (uint8_t)((wave + wave2) * 50.0f + 20.0f);
        gfx_color_t c = GFX_RGB(r, g, b);
        gfx_fb_hline(fb, 0, y, GFX_W, c);
    }
}


/*  PUBLIC API  */

void demo_init(demo_state_t *d) {
    memset(d, 0, sizeof(*d));

    build_star   (&d->star);
    build_diamond(&d->diamond);
    build_circle (&d->circle, 14.0f);

    gfx_scene_init(&d->scene);

    /* Place objects at fixed depths (back -> front) */
    static const gfx_cx_t cx_id = { 256,256,256, 0,0,0 }; /* identity cx   */

    gfx_scene_place(&d->scene, &d->star,    1,
                    gfx_mat_translate(GFX_W/2, GFX_H/2), cx_id);
    gfx_scene_place(&d->scene, &d->diamond, 2,
                    gfx_mat_translate(GFX_W/2, GFX_H/2), cx_id);
    gfx_scene_place(&d->scene, &d->circle,  3,
                    gfx_mat_translate(GFX_W/2, GFX_H/2), cx_id);

    /* Initial physics */
    d->diamond_x  = GFX_W / 2.0f;
    d->diamond_y  = GFX_H / 2.0f;
    d->diamond_vx = 70.0f;   /* pixels / second */
    d->diamond_vy = 50.0f;
    d->orbit_angle = 0.0f;
}

void demo_update(demo_state_t *d, float dt, gfx_color_t *fb) {
    d->t          += dt;
    d->star_angle += dt * 0.6f;   /* ~34 rpm */
    d->orbit_angle+= dt * 1.8f;

    /* -- diamond physics (box bounce) */
    d->diamond_x += d->diamond_vx * dt;
    d->diamond_y += d->diamond_vy * dt;
    const float margin = 40.0f;
    if (d->diamond_x < margin)        { d->diamond_x = margin;         d->diamond_vx = fabsf(d->diamond_vx); }
    if (d->diamond_x > GFX_W-margin)  { d->diamond_x = GFX_W-margin;   d->diamond_vx = -fabsf(d->diamond_vx);}
    if (d->diamond_y < margin)        { d->diamond_y = margin;         d->diamond_vy = fabsf(d->diamond_vy); }
    if (d->diamond_y > GFX_H-margin)  { d->diamond_y = GFX_H-margin;   d->diamond_vy = -fabsf(d->diamond_vy);}

    /* -- build matrices */
    /* Star: rotate around screen centre */
    gfx_mat_t star_mat =
        gfx_mat_concat(gfx_mat_rotate(d->star_angle), gfx_mat_translate(GFX_W/2, GFX_H/2));

    /* Diamond: translate to bouncing position */
    gfx_mat_t dia_mat = gfx_mat_translate((int32_t)d->diamond_x, (int32_t)d->diamond_y);

    /* Orbiter: orbit around the star */
    float ox = cosf(d->orbit_angle) * 70.0f + GFX_W / 2.0f;
    float oy = sinf(d->orbit_angle) * 50.0f + GFX_H / 2.0f;
    gfx_mat_t orb_mat = gfx_mat_translate((int32_t)ox, (int32_t)oy);

    /* Colour-transform the diamond: pulse saturation */
    float pulse = sinf(d->t * 3.0f) * 0.3f + 0.7f;
    gfx_cx_t dia_cx = {
        .r_mul = (int16_t)(256 * pulse),
        .g_mul = (int16_t)(256 * pulse),
        .b_mul = 256,
        .r_add = 0, .g_add = 0, .b_add = 0
    };

    /* -- update scene objects */
    static const gfx_cx_t cx_id = { 256,256,256, 0,0,0 };

    gfx_obj_t *star_obj = gfx_scene_place(&d->scene, &d->star,    1, star_mat, cx_id);
    gfx_obj_t *dia_obj  = gfx_scene_place(&d->scene, &d->diamond, 2, dia_mat,  dia_cx);
    gfx_obj_t *orb_obj  = gfx_scene_place(&d->scene, &d->circle,  3, orb_mat,  cx_id);
    (void)star_obj; (void)dia_obj; (void)orb_obj;

    /* render */
    draw_background(fb, d->t);      /* layer 0: immediate-mode background */
    gfx_render(&d->scene, 0, fb);   /* bg=0 skips clear (background drawn) */
}
