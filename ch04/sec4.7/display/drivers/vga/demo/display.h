#ifndef DISPLAY_H
#define DISPLAY_H

#include <stdint.h>
#include <stdbool.h>
#include "pico/stdlib.h"

/*
 * VGA output via Pimoroni Pico VGA Demo Base (same as RPi Pico VGA Demo Board).
 *
 * Hardware: pico_scanvideo_dpi library, PIO-driven resistor DAC.
 * Resolution: 320x240 @ 60 Hz (640x480 timing, pixel-doubled).
 *
 * GPIO pin mapping (fixed by the VGA demo board hardware):
 *   GPIO  0- 4 : Blue  [4:0]   (5-bit)
 *   GPIO  5-10 : Green [5:0]   (6-bit)
 *   GPIO 11-15 : Red   [4:0]   (5-bit)
 *   GPIO 16    : H-Sync (active low)
 *   GPIO 17    : V-Sync (active low)
 *
 * Color format: standard RGB565, no byte-swapping needed (unlike SPI/DMA approach).
 */

/* Display resolution */
#define DISPLAY_WIDTH  320
#define DISPLAY_HEIGHT 240

/* Standard RGB565 color constants */
#define COLOR_BLACK     0x0000u
#define COLOR_WHITE     0xFFFFu
#define COLOR_RED       0xF800u
#define COLOR_GREEN     0x07E0u
#define COLOR_BLUE      0x001Fu
#define COLOR_YELLOW    0xFFE0u
#define COLOR_CYAN      0x07FFu
#define COLOR_MAGENTA   0xF81Fu

/* Error codes (kept for source compatibility) */
typedef enum {
    DISPLAY_OK = 0,
    DISPLAY_ERROR_INIT_FAILED,
    DISPLAY_ERROR_DMA_FAILED,
    DISPLAY_ERROR_INVALID_PARAM,
    DISPLAY_ERROR_NOT_INITIALIZED
} display_error_t;

/*
 * VGA initialisation and main loop.
 *
 * Call display_vga_init() from Core 1 before entering the scanline loop.
 * Call display_vga_run() from Core 1 to start the scanline output loop;
 * it never returns.  Pass a pointer to the volatile framebuffer pointer
 * so Core 0 can swap buffers without a lock.
 */
display_error_t display_vga_init(void);
void            display_vga_run(uint16_t * volatile *active_fb_ptr);

/* Kept for any callers that still use the old name */
static inline display_error_t display_pack_init(void) { return display_vga_init(); }

/*
 * Framebuffer rendering API.
 *
 * All functions operate on a caller-supplied uint16_t array of size
 * DISPLAY_WIDTH * DISPLAY_HEIGHT.  Render into it then hand the pointer
 * to display_vga_run() via the active_fb_ptr mechanism.
 */

/* Pack 8-bit RGB into RGB565 */
static inline uint16_t fb_rgb(uint8_t r, uint8_t g, uint8_t b) {
    return ((uint16_t)(r & 0xF8) << 8) |
           ((uint16_t)(g & 0xFC) << 3) |
           (b >> 3);
}

/* Unpack RGB565 to raw channel fields (5/6/5 bits, NOT 8-bit values) */
static inline void fb_unpack(uint16_t c, uint8_t *r, uint8_t *g, uint8_t *b) {
    *r = (c >> 11) & 0x1F;
    *g = (c >>  5) & 0x3F;
    *b =  c        & 0x1F;
}

/* Primitives */
void fb_clear(uint16_t *fb, uint16_t color);
void fb_draw_pixel(uint16_t *fb, int x, int y, uint16_t color);
void fb_fill_rect(uint16_t *fb, int x, int y, int w, int h, uint16_t color);
void fb_draw_char(uint16_t *fb, int x, int y, char c, uint16_t fg, uint16_t bg);
void fb_draw_string(uint16_t *fb, int x, int y, const char *str, uint16_t fg, uint16_t bg);

/* Xiaolin Wu anti-aliased line */
void fb_draw_line_aa(uint16_t *fb, float x0, float y0, float x1, float y1, uint16_t color);

/* Bilinear-filtered blit — scales src (sw×sh, RGB565) into dst region */
void fb_blit_scaled(uint16_t *fb,
                    const uint16_t *src, int sw, int sh,
                    int dx, int dy, int dw, int dh);

/*
 * Color transform — ported from Flash ColorTransform.
 *   result_channel = clamp(src_channel * mul/256 + add)
 * Use mul=256, add=0 for identity. mul=0..255 dims, add>0 tints.
 */
typedef struct {
    int r_mul, r_add;
    int g_mul, g_add;
    int b_mul, b_add;
} fb_color_transform_t;

void fb_apply_color_transform(uint16_t *fb, const fb_color_transform_t *cx);
void fb_apply_color_transform_rect(uint16_t *fb, const fb_color_transform_t *cx,
                                   int x, int y, int w, int h);

static inline fb_color_transform_t fb_cx_identity(void) {
    return (fb_color_transform_t){256,0, 256,0, 256,0};
}
static inline fb_color_transform_t fb_cx_dim(uint8_t level) {
    return (fb_color_transform_t){level,0, level,0, level,0};
}
static inline fb_color_transform_t fb_cx_tint(uint8_t r, uint8_t g, uint8_t b) {
    return (fb_color_transform_t){256,r, 256,g, 256,b};
}

#endif /* DISPLAY_H */
