/*
 * demo.h  animated 2D demo scene
 *
 * Three layers illustrate the gfx API:
 *   Layer 0: tiled sine-wave background (immediate-mode horizontal spans)
 *   Layer 1: rotating star (5-point polygon, radial gradient fill)
 *   Layer 2: bouncing diamond (quadratic bezier sides, solid fill)
 *   Layer 3: orbiting circle (approximated with 16 bezier segments)
 */

#pragma once
#include "gfx.h"

typedef struct {
    float    t;          /* global time in seconds */
    float    star_angle; /* rotation of the star */
    float    diamond_x;
    float    diamond_y;
    float    diamond_vx;
    float    diamond_vy;
    float    orbit_angle;

    /* pre-built shapes (allocated once, reused each frame) */
    gfx_shape_t star;
    gfx_shape_t diamond;
    gfx_shape_t circle;

    gfx_scene_t scene;
} demo_state_t;

/* Initialise shapes and scene.  Call once before the render loop. */
void demo_init(demo_state_t *d);

/* Advance physics / animation by dt seconds, then render the scene into fb. */
void demo_update(demo_state_t *d, float dt, gfx_color_t *fb);
