/*
 * display.c - VGA output via pico_scanvideo_dpi
 *
 * Targets the Pimoroni Pico VGA Demo Base (same hardware as RPi Pico VGA Demo Board).
 * Core 1 calls display_vga_init() then display_vga_run(&active_fb_ptr).
 * Core 0 renders into a back buffer and swaps the pointer for double-buffering.
 *
 * GPIO assignments (fixed by the VGA demo board resistor DAC):
 *   GPIO  0- 4  Blue [4:0]
 *   GPIO  5-10  Green[5:0]
 *   GPIO 11-15  Red  [4:0]
 *   GPIO 16     H-Sync
 *   GPIO 17     V-Sync
 *
 * Color format: standard RGB565 — blue in bits[4:0], green in bits[10:5],
 * red in bits[15:11].  This maps directly to the GPIO pins above, so no
 * byte-swapping is needed (contrast with the old SPI/DMA approach).
 */

#include "display.h"
#include "font.h"
#include "pico/scanvideo.h"
#include "pico/scanvideo/composable_scanline.h"
#include "hardware/sync.h"
#include <string.h>

/* ==========================================================================
 * VGA initialisation and scanline loop
 * ========================================================================== */

display_error_t display_vga_init(void) {
    scanvideo_setup(&vga_mode_320x240_60);
    scanvideo_timing_enable(true);
    return DISPLAY_OK;
}

/*
 * display_vga_run - Core 1 scanline output loop (never returns).
 *
 * Reads from *active_fb_ptr each scanline so that Core 0 can swap the
 * pointer between frames without a lock (32-bit aligned pointer write/read
 * is atomic on RP2350 shared SRAM).
 *
 * Scanline buffer format for COMPOSABLE_RAW_RUN with DISPLAY_WIDTH pixels:
 *   word[0]      : COMPOSABLE_RAW_RUN (lo16) | pixel[0] (hi16)
 *   word[1]      : (DISPLAY_WIDTH-3) (lo16)  | pixel[1] (hi16)
 *   word[2..159] : pixel[2*i] (lo16) | pixel[2*i+1] (hi16)   (i=1..159)
 *   word[161]    : COMPOSABLE_EOL_ALIGN
 *   data_used    : 162
 */
void display_vga_run(uint16_t * volatile *active_fb_ptr) {
    while (true) {
        struct scanvideo_scanline_buffer *buf =
            scanvideo_begin_scanline_generation(true);

        int line = scanvideo_scanline_number(buf->scanline_id);
        const uint16_t *src = *active_fb_ptr + line * DISPLAY_WIDTH;

        uint32_t *data = buf->data;
        data[0] = COMPOSABLE_RAW_RUN | ((uint32_t)src[0] << 16u);
        data[1] = (uint32_t)(DISPLAY_WIDTH - 3) | ((uint32_t)src[1] << 16u);

        for (int i = 1; i < DISPLAY_WIDTH / 2; i++) {
            data[1 + i] = (uint32_t)src[2 * i] | ((uint32_t)src[2 * i + 1] << 16u);
        }

        data[DISPLAY_WIDTH / 2 + 1] = COMPOSABLE_EOL_ALIGN;
        buf->data_used = DISPLAY_WIDTH / 2 + 2;   /* = 162 words */

        scanvideo_end_scanline_generation(buf);
    }
}

/*
 * Framebuffer rendering helpers
 * (identical to the previous SPI-based display.c — the fb_* API is hardware-
 * independent; only the blit path changes, which is now handled by the VGA
 * scanline loop above.)
 */

static inline int clamp_i(int v, int lo, int hi) {
    return v < lo ? lo : v > hi ? hi : v;
}

static inline uint8_t cx_apply_channel(uint8_t in, int mul, int add) {
    int v = ((int)in * mul >> 8) + add;
    if (v < 0)   return 0;
    if (v > 255) return 255;
    return (uint8_t)v;
}

/* Unpack RGB565 to 8-bit channels */
static inline void unpack565(uint16_t c, uint8_t *r, uint8_t *g, uint8_t *b) {
    *r = ((c >> 11) & 0x1F) << 3;
    *g = ((c >>  5) & 0x3F) << 2;
    *b =  (c        & 0x1F) << 3;
}

/* Pack 8-bit RGB back to RGB565 */
static inline uint16_t pack565(uint8_t r, uint8_t g, uint8_t b) {
    return ((uint16_t)(r & 0xF8) << 8) |
           ((uint16_t)(g & 0xFC) << 3) |
           (b >> 3);
}

/* Blend a pixel with given fractional weight (0-255) against existing fb pixel */
static inline void wu_plot_fb(uint16_t *fb, int x, int y, uint8_t alpha, uint16_t color) {
    if ((unsigned)x >= DISPLAY_WIDTH || (unsigned)y >= DISPLAY_HEIGHT) return;
    uint16_t *dst = &fb[y * DISPLAY_WIDTH + x];

    uint8_t sr, sg, sb, dr, dg, db;
    unpack565(color, &sr, &sg, &sb);
    unpack565(*dst,  &dr, &dg, &db);

    uint8_t ia = 255 - alpha;
    uint8_t r = (uint8_t)(((uint16_t)sr * alpha + (uint16_t)dr * ia) >> 8);
    uint8_t g = (uint8_t)(((uint16_t)sg * alpha + (uint16_t)dg * ia) >> 8);
    uint8_t b = (uint8_t)(((uint16_t)sb * alpha + (uint16_t)db * ia) >> 8);
    *dst = pack565(r, g, b);
}

/* --------------------------------------------------------------------------- */
void fb_clear(uint16_t *fb, uint16_t color) {
    int total = DISPLAY_WIDTH * DISPLAY_HEIGHT;
    for (int i = 0; i < total; i++) fb[i] = color;
}

void fb_draw_pixel(uint16_t *fb, int x, int y, uint16_t color) {
    if ((unsigned)x < DISPLAY_WIDTH && (unsigned)y < DISPLAY_HEIGHT)
        fb[y * DISPLAY_WIDTH + x] = color;
}

void fb_fill_rect(uint16_t *fb, int x, int y, int w, int h, uint16_t color) {
    int x1 = clamp_i(x,     0, DISPLAY_WIDTH);
    int y1 = clamp_i(y,     0, DISPLAY_HEIGHT);
    int x2 = clamp_i(x + w, 0, DISPLAY_WIDTH);
    int y2 = clamp_i(y + h, 0, DISPLAY_HEIGHT);
    for (int row = y1; row < y2; row++)
        for (int col = x1; col < x2; col++)
            fb[row * DISPLAY_WIDTH + col] = color;
}

/*
 * fb_draw_char - draw a 5x8 glyph centred (1px left pad) inside an 8x8 cell.
 * Font bytes: data[0]=rightmost col, data[4]=leftmost col; bit 0 = top row.
 */
void fb_draw_char(uint16_t *fb, int x, int y, char c, uint16_t fg, uint16_t bg) {
    if ((unsigned)x >= DISPLAY_WIDTH || (unsigned)y >= DISPLAY_HEIGHT) return;

    uint8_t code = (unsigned char)c;

    /* Fill full 8x8 cell with bg */
    for (int col = 0; col < 8 && (x + col) < (int)DISPLAY_WIDTH; col++)
        for (int row = 0; row < 8 && (y + row) < (int)DISPLAY_HEIGHT; row++)
            fb[(y + row) * DISPLAY_WIDTH + (x + col)] = bg;

    if (code >= 128 && code <= 143) {
        /* Block character: 8x8, MSB = leftmost pixel, no left pad */
        for (int row = 0; row < 8 && (y + row) < (int)DISPLAY_HEIGHT; row++) {
            uint8_t row_bits = font_block[code - 128][row];
            for (int col = 0; col < 8 && (x + col) < (int)DISPLAY_WIDTH; col++)
                if (row_bits & (0x80 >> col))
                    fb[(y + row) * DISPLAY_WIDTH + (x + col)] = fg;
        }
        return;
    }

    int idx = code - 32;
    if (idx < 0 || idx >= (int)(sizeof(font5x8) / sizeof(font5x8[0]))) idx = 0;
    const uint8_t *char_data = font5x8[idx];

    for (int col = 0; col < 5 && (x + 1 + col) < (int)DISPLAY_WIDTH; col++) {
        uint8_t line = char_data[4 - col];
        for (int row = 0; row < 8 && (y + row) < (int)DISPLAY_HEIGHT; row++)
            if (line & (1 << row))
                fb[(y + row) * DISPLAY_WIDTH + (x + 1 + col)] = fg;
    }
}

void fb_draw_string(uint16_t *fb, int x, int y, const char *str, uint16_t fg, uint16_t bg) {
    while (*str && x < (int)DISPLAY_WIDTH) {
        fb_draw_char(fb, x, y, *str++, fg, bg);
        x += 6;
    }
}

/*
 * fb_draw_line_aa - Xiaolin Wu anti-aliased line.
 */
void fb_draw_line_aa(uint16_t *fb, float x0, float y0, float x1, float y1, uint16_t color) {
    bool steep = (y1 - y0 < 0 ? y0 - y1 : y1 - y0) >
                 (x1 - x0 < 0 ? x0 - x1 : x1 - x0);
    if (steep)   { float t; t=x0;x0=y0;y0=t; t=x1;x1=y1;y1=t; }
    if (x0 > x1) { float t; t=x0;x0=x1;x1=t; t=y0;y0=y1;y1=t; }

    float dx = x1 - x0, dy = y1 - y0;
    float grad = (dx == 0.0f) ? 1.0f : dy / dx;

    int   xe = (int)(x0 + 0.5f);
    float ye = y0 + grad * (xe - x0);
    float xg = 1.0f - (x0 + 0.5f - xe);
    int xp1 = xe, yp1 = (int)ye;
    float frac = ye - yp1;
    if (steep) {
        wu_plot_fb(fb, yp1,   xp1, (uint8_t)(255 * (1-frac) * xg), color);
        wu_plot_fb(fb, yp1+1, xp1, (uint8_t)(255 * frac     * xg), color);
    } else {
        wu_plot_fb(fb, xp1, yp1,   (uint8_t)(255 * (1-frac) * xg), color);
        wu_plot_fb(fb, xp1, yp1+1, (uint8_t)(255 * frac     * xg), color);
    }
    float intery = ye + grad;

    xe = (int)(x1 + 0.5f);
    ye = y1 + grad * (xe - x1);
    xg = x1 + 0.5f - (int)(x1 + 0.5f);
    int xp2 = xe, yp2 = (int)ye;
    frac = ye - yp2;
    if (steep) {
        wu_plot_fb(fb, yp2,   xp2, (uint8_t)(255 * (1-frac) * xg), color);
        wu_plot_fb(fb, yp2+1, xp2, (uint8_t)(255 * frac     * xg), color);
    } else {
        wu_plot_fb(fb, xp2, yp2,   (uint8_t)(255 * (1-frac) * xg), color);
        wu_plot_fb(fb, xp2, yp2+1, (uint8_t)(255 * frac     * xg), color);
    }

    for (int xi = xp1+1; xi < xp2; xi++) {
        int yi = (int)intery;
        uint8_t f = (uint8_t)(255 * (intery - yi));
        if (steep) {
            wu_plot_fb(fb, yi,   xi, 255-f, color);
            wu_plot_fb(fb, yi+1, xi, f,     color);
        } else {
            wu_plot_fb(fb, xi, yi,   255-f, color);
            wu_plot_fb(fb, xi, yi+1, f,     color);
        }
        intery += grad;
    }
}

/*
 * fb_blit_scaled - bilinear-filtered scaled blit.
 */
void fb_blit_scaled(uint16_t *fb,
                    const uint16_t *src, int sw, int sh,
                    int dx, int dy, int dw, int dh)
{
    if (!src || sw <= 0 || sh <= 0 || dw <= 0 || dh <= 0) return;

    int step_x = (sw << 16) / dw;
    int step_y = (sh << 16) / dh;

    for (int py = 0; py < dh; py++) {
        int oy = dy + py;
        if (oy < 0 || oy >= (int)DISPLAY_HEIGHT) continue;

        int sy16 = (int)(((long long)py * step_y));
        int sy   = sy16 >> 16;
        int fy   = (sy16 >> 8) & 0xFF;

        int sy0 = clamp_i(sy,   0, sh-1);
        int sy1 = clamp_i(sy+1, 0, sh-1);

        int sx16 = 0;
        for (int px = 0; px < dw; px++, sx16 += step_x) {
            int ox = dx + px;
            if (ox < 0 || ox >= (int)DISPLAY_WIDTH) continue;

            int sx  = sx16 >> 16;
            int fx  = (sx16 >> 8) & 0xFF;

            int sx0 = clamp_i(sx,   0, sw-1);
            int sx1 = clamp_i(sx+1, 0, sw-1);

            uint16_t c00 = src[sy0 * sw + sx0];
            uint16_t c10 = src[sy0 * sw + sx1];
            uint16_t c01 = src[sy1 * sw + sx0];
            uint16_t c11 = src[sy1 * sw + sx1];

            uint8_t r00,g00,b00, r10,g10,b10, r01,g01,b01, r11,g11,b11;
            unpack565(c00,&r00,&g00,&b00);
            unpack565(c10,&r10,&g10,&b10);
            unpack565(c01,&r01,&g01,&b01);
            unpack565(c11,&r11,&g11,&b11);

            int ifx = 255 - fx, ify = 255 - fy;
            int w00 = ifx * ify, w10 = fx * ify;
            int w01 = ifx * fy,  w11 = fx * fy;
            int total = w00 + w10 + w01 + w11;
            if (total == 0) total = 1;

            uint8_t r = (uint8_t)((w00*r00 + w10*r10 + w01*r01 + w11*r11) / total);
            uint8_t g = (uint8_t)((w00*g00 + w10*g10 + w01*g01 + w11*g11) / total);
            uint8_t b = (uint8_t)((w00*b00 + w10*b10 + w01*b01 + w11*b11) / total);

            fb[oy * DISPLAY_WIDTH + ox] = pack565(r, g, b);
        }
    }
}

/*
 * fb_apply_color_transform - Flash ColorTransform ported to RGB565.
 */
void fb_apply_color_transform(uint16_t *fb, const fb_color_transform_t *cx) {
    fb_apply_color_transform_rect(fb, cx, 0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT);
}

void fb_apply_color_transform_rect(uint16_t *fb, const fb_color_transform_t *cx,
                                   int x, int y, int w, int h)
{
    if (!cx) return;
    int x1 = clamp_i(x,     0, (int)DISPLAY_WIDTH);
    int y1 = clamp_i(y,     0, (int)DISPLAY_HEIGHT);
    int x2 = clamp_i(x + w, 0, (int)DISPLAY_WIDTH);
    int y2 = clamp_i(y + h, 0, (int)DISPLAY_HEIGHT);

    if (cx->r_mul == 256 && cx->r_add == 0 &&
        cx->g_mul == 256 && cx->g_add == 0 &&
        cx->b_mul == 256 && cx->b_add == 0) return;

    for (int row = y1; row < y2; row++) {
        uint16_t *line = &fb[row * DISPLAY_WIDTH + x1];
        for (int col = x1; col < x2; col++, line++) {
            uint8_t r, g, b;
            unpack565(*line, &r, &g, &b);
            r = cx_apply_channel(r, cx->r_mul, cx->r_add);
            g = cx_apply_channel(g, cx->g_mul, cx->g_add);
            b = cx_apply_channel(b, cx->b_mul, cx->b_add);
            *line = pack565(r, g, b);
        }
    }
}
