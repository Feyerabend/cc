/*
 * scene.h — Scene buffer and primitive definitions
 *
 * Core 0 (protocol_task) writes into build_scene.
 * Core 1 (display loop) reads from render_scene.
 *
 * Swap is done by protocol_task after FRAME_END with a DMB to ensure
 * all primitive writes are visible before the pointer flip.
 */

#ifndef SCENE_H
#define SCENE_H

#include <stdint.h>
#include <stdbool.h>
#include "display.h"

#define MAX_PRIMS          64
#define PRIM_TEXT_MAX      47    /* max chars in a TEXT primitive */
#define BITMAP_MAX_PIXELS  115   /* max pixels in a BITMAP primitive (PKT_MAX_SIZE budget, 11-byte hdr) */

typedef enum {
    PRIM_RECT   = 0x01,
    PRIM_TEXT   = 0x02,
    PRIM_LINE   = 0x03,
    PRIM_BITMAP = 0x04,
    PRIM_CIRCLE = 0x05,
} prim_type_t;

typedef struct {
    prim_type_t type;
    union {
        struct {
            int16_t  x, y;
            uint16_t w, h;
            uint16_t color;
        } rect;
        struct {
            int16_t  x, y;
            uint16_t fg, bg;
            char     text[PRIM_TEXT_MAX + 1];
        } text;
        struct {
            int16_t  x0, y0, x1, y1;
            uint16_t color;
        } line;
        struct {
            int16_t  x, y;
            uint8_t  w, h;
            uint16_t dw, dh;
            uint16_t pixels[BITMAP_MAX_PIXELS];
        } bitmap;
        struct {
            int16_t  cx, cy;
            uint16_t r;
            uint16_t color;
        } circle;
    };
} primitive_t;

typedef struct {
    uint16_t    frame_id;
    bool        has_clear;
    uint16_t    clear_color;
    uint16_t    prim_count;
    primitive_t prims[MAX_PRIMS];
} scene_buffer_t;

/*
 * Double-buffer pointers.
 * Core 0 writes build_scene, then atomically swaps the pointers.
 * Core 1 reads render_scene (never writes).
 * Both are volatile so the compiler doesn't cache the pointer value.
 */
extern volatile scene_buffer_t *render_scene;
extern volatile scene_buffer_t *build_scene;

/* Number of frames that have been swapped (Core 1 can use to detect new frame) */
extern volatile uint32_t g_frames_rendered;

/*
 * Persistent canvas buffer — 320×240 RGB565 pixels (~150 KB BSS).
 * Core 0 (protocol_task) writes tiles via VGTP_TYPE_CANVAS packets.
 * Core 1 (display loop) copies this as the background each frame when
 * g_canvas_used is true.  Rendered scene primitives appear on top.
 */
extern uint16_t canvas_buf[DISPLAY_WIDTH * DISPLAY_HEIGHT];
extern volatile bool g_canvas_used;   /* false until first CANVAS packet arrives */

/* Fill canvas_buf with color_fb (already byte-swapped for DMA) and set g_canvas_used */
void canvas_clear(uint16_t color_fb);

void scene_init(void);

/* Swap build↔render with a memory barrier. Call after FRAME_END. */
void scene_swap(void);

#endif /* SCENE_H */
