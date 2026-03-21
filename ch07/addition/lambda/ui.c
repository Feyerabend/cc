/*
 * ui.c — status display for pico-lambda using Pimoroni Display Pack 2.0
 *
 * Layout (320 × 240, 5×8 font, 10px line pitch):
 *
 *  ┌──────────────────────────────────────────────────────────────┐
 *  │  pico-lambda                          10.0.x.x              │  header (blue)
 *  ├──────────────────────────────────────────────────────────────┤
 *  │  Requests: 0          Uptime: 00:00:00                       │
 *  ├──────────────────────────────────────────────────────────────┤
 *  │  Expression                                                  │  label (dark)
 *  │  ...truncated to 52 chars...                                 │
 *  │                                                              │
 *  │  Result                                                      │
 *  │  ...up to 4 lines...                                         │
 *  │                                                              │
 *  └──────────────────────────────────────────────────────────────┘
 *
 * All drawing goes into a static framebuffer; display_blit_full()
 * pushes it to the ST7789 over DMA-SPI.
 */

#include "ui.h"
#include "display.h"
#include "pico/stdlib.h"
#include <stdio.h>
#include <string.h>

/* ------------------------------------------------------------------ */
/*  Layout constants                                                   */
/* ------------------------------------------------------------------ */
#define LINE_H      10      /* pixels per text row (8px char + 2px gap) */
#define COL_W        6      /* pixels per char (5px glyph + 1px gap)    */
#define MARGIN       6      /* left/right margin in pixels               */
#define CHARS_PER_ROW  ((DISPLAY_WIDTH - 2 * MARGIN) / COL_W)   /* 51  */

/* Row Y positions */
#define Y_HEADER     4
#define Y_STATS     22
#define Y_DIV1      34
#define Y_EXPR_LBL  38
#define Y_EXPR_VAL  50
#define Y_DIV2     114
#define Y_RESP_LBL 118
#define Y_RESP_VAL 130

/* Header bar height */
#define HEADER_H    18

/* Expression area: 6 rows × LINE_H  (50 .. 110) */
#define EXPR_ROWS    6
/* Response area:  6 rows × LINE_H  (130 .. 190) */
#define RESP_ROWS    6

/* Accent colors */
#define C_BG        COLOR_BLACK
#define C_HEADER    fb_rgb(0,  50, 120)   /* dark blue                 */
#define C_DIV       fb_rgb(40, 40,  40)   /* dim grey                  */
#define C_TITLE     COLOR_WHITE
#define C_IP        COLOR_WHITE
#define C_LABEL     COLOR_WHITE
#define C_VALUE     COLOR_WHITE
#define C_OK        COLOR_GREEN
#define C_ERR       fb_rgb(255, 80, 80)
#define C_DIM       fb_rgb(80, 80, 80)

/* ------------------------------------------------------------------ */
/*  Module state                                                       */
/* ------------------------------------------------------------------ */
static uint16_t fb[DISPLAY_WIDTH * DISPLAY_HEIGHT];
static char     stored_ip[24];
static uint32_t req_count = 0;

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */
static void draw_divider(int y)
{
    fb_fill_rect(fb, 0, y, DISPLAY_WIDTH, 1, C_DIV);
}

/* Draw a string clipped to CHARS_PER_ROW; pads remainder with bg.  */
static void draw_row(int x, int y, const char *s, uint16_t fg, uint16_t bg)
{
    int col = 0;
    while (*s && col < CHARS_PER_ROW) {
        fb_draw_char(fb, x + col * COL_W, y, *s++, fg, bg);
        col++;
    }
    /* Erase any leftover from a previous longer string */
    while (col < CHARS_PER_ROW) {
        fb_draw_char(fb, x + col * COL_W, y, ' ', fg, bg);
        col++;
    }
}

/* Wrap src into up to max_rows rows of CHARS_PER_ROW each,
 * clearing any rows below the content.                              */
static void draw_wrapped(int x, int y, const char *src,
                         int max_rows, uint16_t fg, uint16_t bg)
{
    char line[CHARS_PER_ROW + 1];
    int  row = 0;
    while (*src && row < max_rows) {
        int n = 0;
        while (*src && *src != '\n' && n < CHARS_PER_ROW)
            line[n++] = *src++;
        line[n] = '\0';
        if (*src == '\n') src++;
        draw_row(x, y + row * LINE_H, line, fg, bg);
        row++;
    }
    while (row < max_rows) {
        draw_row(x, y + row * LINE_H, "", fg, bg);
        row++;
    }
}

/* ------------------------------------------------------------------ */
/*  Static layout (drawn once in ui_init)                             */
/* ------------------------------------------------------------------ */
static void draw_static_layout(void)
{
    fb_clear(fb, C_BG);

    /* Header bar */
    fb_fill_rect(fb, 0, 0, DISPLAY_WIDTH, HEADER_H, C_HEADER);
    fb_draw_string(fb, MARGIN, Y_HEADER, "pico-lambda", C_TITLE, C_HEADER);
    /* IP right-aligned in header */
    int ip_x = DISPLAY_WIDTH - MARGIN - (int)strlen(stored_ip) * COL_W;
    fb_draw_string(fb, ip_x, Y_HEADER, stored_ip, C_IP, C_HEADER);

    draw_divider(Y_DIV1);

    /* Section labels */
    fb_draw_string(fb, MARGIN, Y_EXPR_LBL, "Expression", C_LABEL, C_BG);
    fb_draw_string(fb, MARGIN, Y_RESP_LBL, "Result",     C_LABEL, C_BG);

    draw_divider(Y_DIV2);
}

/* ------------------------------------------------------------------ */
/*  Public API                                                         */
/* ------------------------------------------------------------------ */
void ui_init(const char *ip)
{
    if (display_pack_init() != DISPLAY_OK) return;
    display_set_backlight(true);

    strncpy(stored_ip, ip ? ip : "?.?.?.?", sizeof(stored_ip) - 1);
    stored_ip[sizeof(stored_ip) - 1] = '\0';

    draw_static_layout();

    /* Initial stats row */
    fb_draw_string(fb, MARGIN, Y_STATS, "Requests: 0       Uptime: 00:00:00",
                   C_VALUE, C_BG);

    display_wait_for_dma();
    display_blit_full(fb);
}

void ui_tick(void)
{
    uint32_t t  = to_ms_since_boot(get_absolute_time()) / 1000;
    uint32_t h  = t / 3600;
    uint32_t m  = (t % 3600) / 60;
    uint32_t s  = t % 60;

    char stats[CHARS_PER_ROW + 1];
    snprintf(stats, sizeof(stats),
             "Requests: %-6lu  Uptime: %02lu:%02lu:%02lu",
             (unsigned long)req_count, (unsigned long)h,
             (unsigned long)m, (unsigned long)s);

    draw_row(MARGIN, Y_STATS, stats, C_VALUE, C_BG);

    display_wait_for_dma();
    display_blit_full(fb);
}

void ui_on_request(const char *src, const dispatch_result_t *result)
{
    req_count++;

    /* Expression — strip leading/trailing whitespace for display   */
    draw_wrapped(MARGIN, Y_EXPR_VAL, src ? src : "",
                 EXPR_ROWS, C_DIM, C_BG);

    /* Result */
    uint16_t res_color = (result && result->ok) ? C_OK : C_ERR;
    draw_wrapped(MARGIN, Y_RESP_VAL,
                 (result && result->len > 0) ? result->buf : "(no output)",
                 RESP_ROWS, res_color, C_BG);

    display_wait_for_dma();
    display_blit_full(fb);
}
