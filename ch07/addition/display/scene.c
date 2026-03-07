/*
 * scene.c — Double-buffered scene storage
 */

#include "scene.h"
#include "hardware/sync.h"   /* __dmb() */
#include <string.h>

static scene_buffer_t scene_a;
static scene_buffer_t scene_b;

volatile scene_buffer_t *render_scene = &scene_a;
volatile scene_buffer_t *build_scene  = &scene_b;

volatile uint32_t g_frames_rendered = 0;

/* Canvas buffer — persistent background, ~150 KB in BSS */
uint16_t canvas_buf[DISPLAY_WIDTH * DISPLAY_HEIGHT];
volatile bool g_canvas_used = false;

void canvas_clear(uint16_t color_fb)
{
    uint32_t npix = DISPLAY_WIDTH * DISPLAY_HEIGHT;
    for (uint32_t i = 0; i < npix; i++)
        canvas_buf[i] = color_fb;
    g_canvas_used = true;
}

void scene_init(void)
{
    memset(&scene_a, 0, sizeof(scene_a));
    memset(&scene_b, 0, sizeof(scene_b));
    memset(canvas_buf, 0, sizeof(canvas_buf));
}

void scene_swap(void)
{
    __dmb();   /* ensure all writes to build_scene are visible to Core 1 */
    volatile scene_buffer_t *tmp = render_scene;
    render_scene = build_scene;
    build_scene  = tmp;
    g_frames_rendered++;
}
