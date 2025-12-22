#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <stdio.h>
#include <time.h>

#include "pico/stdlib.h"
#include "pico/time.h"
#include "display.h"

#define CENTER_X 160.0f
#define CENTER_Y 120.0f
#define RADIUS   100.0f

/* Hand “memory” – where the tip of the previous hand was drawn -- one way of avoiding flicker */
static float last_sec_x = 0, last_sec_y = 0;
static float last_min_x = 0, last_min_y = 0;
static float last_hour_x = 0, last_hour_y = 0;

/* Lap hand (static while stopwatch runs) */
static float lap_sec_x = 0, lap_sec_y = 0;
static float lap_min_x = 0, lap_min_y = 0;
static float lap_hour_x = 0, lap_hour_y = 0;
static bool  lap_active = false;

/* Stopwatch state */
static bool   stopwatch_running = false;
static absolute_time_t stopwatch_start;
static int64_t stopwatch_elapsed_ms = 0;   // when stopped

/* Last drawn values (to avoid unnecessary redraws) */
static int last_sec = -1, last_min = -1, last_hour = -1;

/* Button callbacks */
static void btn_a_callback(button_t btn) { (void)btn;
    if (stopwatch_running) {                     // STOP
        stopwatch_running = false;
        stopwatch_elapsed_ms = absolute_time_diff_us(stopwatch_start,
                                                    get_absolute_time()) / 1000;
    } else {                                     // START / RESUME
        stopwatch_running = true;
        stopwatch_start = get_absolute_time();
        if (stopwatch_elapsed_ms > 0)            // resume from pause
            stopwatch_start = delayed_by_us(stopwatch_start,
                                            -stopwatch_elapsed_ms * 1000);
    }
}

static void btn_b_callback(button_t btn) { (void)btn;
    /* RESET */
    stopwatch_running = false;
    stopwatch_elapsed_ms = 0;
    lap_active = false;
    last_sec = last_min = last_hour = -1;        // force full redraw
    display_clear(COLOR_BLACK); // ok?
}

static void btn_y_callback(button_t btn) { (void)btn;
    /* LAP – freeze current hands, keep drawing live hands on top */
    if (!stopwatch_running) return;              // only while running

    lap_active = true;
    /* copy current tip positions */
    lap_sec_x = last_sec_x;   lap_sec_y = last_sec_y;
    lap_min_x = last_min_x;   lap_min_y = last_min_y;
    lap_hour_x = last_hour_x; lap_hour_y = last_hour_y;
}

/* Bresenham line – "standard" */
void draw_line2(float x0f, float y0f, float x1f, float y1f, uint16_t color) {
    int ix0 = (int)(x0f + 0.5f), iy0 = (int)(y0f + 0.5f);
    int ix1 = (int)(x1f + 0.5f), iy1 = (int)(y1f + 0.5f);

    int dx = abs(ix1 - ix0), sx = ix0 < ix1 ? 1 : -1;
    int dy = -abs(iy1 - iy0), sy = iy0 < iy1 ? 1 : -1;
    int err = dx + dy;

    while (1) {
        if (ix0 >= 0 && ix0 < 320 && iy0 >= 0 && iy0 < 240)
            display_draw_pixel(ix0, iy0, color);
        if (ix0 == ix1 && iy0 == iy1) break;
        int e2 = 2 * err;
        if (e2 >= dy) { err += dy; ix0 += sx; }
        if (e2 <= dx) { err += dx; iy0 += sy; }
    }
}

/*  Xiaolin Wu anti-aliased line */
static void wu_plot(int x, int y, uint8_t brightness, uint16_t color) {
    if (x < 0 || x >= 320 || y < 0 || y >= 240) return;

    /* Extract 5-6-5 components */
    uint8_t r5 = (color >> 11) & 0x1F;
    uint8_t g6 = (color >>  5) & 0x3F;
    uint8_t b5 =  color        & 0x1F;

    /* Scale by brightness (0-255) */
    uint8_t r = (r5 * brightness) >> 8;
    uint8_t g = (g6 * brightness) >> 8;
    uint8_t b = (b5 * brightness) >> 8;

    uint16_t blended = (r << 11) | (g << 5) | b;
    display_draw_pixel(x, y, blended);
}

void draw_line(float x0, float y0, float x1, float y1, uint16_t color) {
    bool steep = fabsf(y1 - y0) > fabsf(x1 - x0);

    /* Make the line always go left to right */
    if (steep) {
        float t; t = x0; x0 = y0; y0 = t; t = x1; x1 = y1; y1 = t;
    }
    if (x0 > x1) {
        float t; t = x0; x0 = x1; x1 = t; t = y0; y0 = y1; y1 = t;
    }

    float dx = x1 - x0;
    float dy = y1 - y0;
    float gradient = (dx == 0.0f) ? 1.0f : dy / dx;

    /* ---- first end point ---- */
    int   xend = (int)(x0 + 0.5f);
    float yend = y0 + gradient * (xend - x0);
    float xgap = 1.0f - (x0 + 0.5f - (int)(x0 + 0.5f));
    int   xpxl1 = xend;
    int   ypxl1 = (int)yend;

    if (steep) {
        wu_plot(ypxl1,     xpxl1,     (uint8_t)(255 * (1 - (yend - ypxl1)) * xgap), color);
        wu_plot(ypxl1 + 1, xpxl1,     (uint8_t)(255 * (yend - ypxl1) * xgap),       color);
    } else {
        wu_plot(xpxl1,     ypxl1,     (uint8_t)(255 * (1 - (yend - ypxl1)) * xgap), color);
        wu_plot(xpxl1,     ypxl1 + 1, (uint8_t)(255 * (yend - ypxl1) * xgap),       color);
    }
    float intery = yend + gradient;

    /* ---- second end point ---- */
    xend = (int)(x1 + 0.5f);
    yend = y1 + gradient * (xend - x1);
    xgap = x1 + 0.5f - (int)(x1 + 0.5f);
    int xpxl2 = xend;
    int ypxl2 = (int)yend;

    if (steep) {
        wu_plot(ypxl2,     xpxl2,     (uint8_t)(255 * (1 - (yend - ypxl2)) * xgap), color);
        wu_plot(ypxl2 + 1, xpxl2,     (uint8_t)(255 * (yend - ypxl2) * xgap),       color);
    } else {
        wu_plot(xpxl2,     ypxl2,     (uint8_t)(255 * (1 - (yend - ypxl2)) * xgap), color);
        wu_plot(xpxl2,     ypxl2 + 1, (uint8_t)(255 * (yend - ypxl2) * xgap),       color);
    }

    /* ---- main loop ---- */
    for (int x = xpxl1 + 1; x < xpxl2; ++x) {
        int y   = (int)intery;
        uint8_t frac = (uint8_t)(255 * (intery - y));

        if (steep) {
            wu_plot(y,     x, 255 - frac, color);
            wu_plot(y + 1, x, frac,       color);
        } else {
            wu_plot(x, y,     255 - frac, color);
            wu_plot(x, y + 1, frac,       color);
        }
        intery += gradient;
    }
}

/* Draw the static clock face (ticks) */
void draw_face(void) {
    for (int i = 0; i < 12; ++i) {
        float angle = i * 30.0f * (float)M_PI / 180.0f;
        float innerX = CENTER_X + (RADIUS - 15) * cosf(angle);
        float innerY = CENTER_Y + (RADIUS - 15) * sinf(angle);
        float outerX = CENTER_X + RADIUS * cosf(angle);
        float outerY = CENTER_Y + RADIUS * sinf(angle);
        draw_line(innerX, innerY, outerX, outerY, COLOR_WHITE);
    }
}

/* Generic hand drawer – erases previous position if any */
void draw_hand(float length, float angle_deg, uint16_t color,
               float *store_x, float *store_y) {
    float rad = angle_deg * (float)M_PI / 180.0f;
    float x = CENTER_X + length * cosf(rad);
    float y = CENTER_Y + length * sinf(rad);

    /* erase old hand */
    if (*store_x != 0.0f || *store_y != 0.0f)
        draw_line(CENTER_X, CENTER_Y, *store_x, *store_y, COLOR_BLACK);

    draw_line(CENTER_X, CENTER_Y, x, y, color);
    *store_x = x; *store_y = y;
}


int main(void) {
    stdio_init_all();
    if (display_pack_init() != DISPLAY_OK) return 1;
    if (buttons_init() != DISPLAY_OK) return 1;

    button_set_callback(BUTTON_A, btn_a_callback);
    button_set_callback(BUTTON_B, btn_b_callback);
    button_set_callback(BUTTON_Y, btn_y_callback);   // <-- lap

    display_clear(COLOR_BLACK);
    display_set_backlight(true);
    draw_face();
    display_draw_pixel((int)CENTER_X, (int)CENTER_Y, COLOR_WHITE);
    last_sec = last_min = last_hour = -1;

    while (1) {
        buttons_update();

        int h = 0, m = 0, s = 0, ms = 0;

        // * 1. STOPWATCH MODE
        if (stopwatch_running) {
            int64_t elapsed = absolute_time_diff_us(stopwatch_start,
                                                    get_absolute_time()) / 1000;
            s  = (elapsed / 1000) % 60;
            m  = (elapsed / 60000) % 60;
            h  = (elapsed / 3600000) % 12;
            ms = elapsed % 1000;

        } else if (stopwatch_elapsed_ms > 0) {
            /* show frozen stopwatch time */
            s  = (stopwatch_elapsed_ms / 1000) % 60;
            m  = (stopwatch_elapsed_ms / 60000) % 60;
            h  = (stopwatch_elapsed_ms / 3600000) % 12;
            ms = stopwatch_elapsed_ms % 1000;

        } else {

            // * 2. CLOCK MODE
            time_t epoch = time(NULL); // POSIX seconds
            struct tm *lt = localtime(&epoch);
            h = lt->tm_hour % 12;
            m = lt->tm_min;
            s = lt->tm_sec;
            /* sub-second from Pico high-res timer */
            uint64_t us = to_us_since_boot(get_absolute_time()) % 1000000ULL;
            ms = us / 1000;
        }

        /* 3. SECOND HAND – always updated (fastest) */
        float sec_angle = s * 6.0f + ms * 0.006f;
        draw_hand(90, sec_angle, COLOR_RED, &last_sec_x, &last_sec_y);
        draw_face(); // always erased otherwise


        /* 4. MINUTE HAND – update only when second changes */
        if (s != last_sec) {
            float min_angle = m * 6.0f + s * 0.1f;
            draw_hand(80, min_angle, COLOR_WHITE, &last_min_x, &last_min_y);
            last_sec = s;
            last_min = m;  // also
        }

        /* 5. HOUR HAND – update only when minute changes */
        if (h != last_hour || m != last_min) {
            float hour_angle = h * 30.0f + m * 0.5f;
            draw_hand(60, hour_angle, COLOR_CYAN, &last_hour_x, &last_hour_y);
            last_hour = h;
            last_min = m;  // also update last_min here to stay in sync
        }
        /* 6. LAP HAND (static while active) */
        if (lap_active) {
            /* draw once – no erase, just overlay */
            if (lap_sec_x != 0.0f || lap_sec_y != 0.0f)
                draw_line(CENTER_X, CENTER_Y, lap_sec_x, lap_sec_y, COLOR_YELLOW);
            if (lap_min_x != 0.0f || lap_min_y != 0.0f)
                draw_line(CENTER_X, CENTER_Y, lap_min_x, lap_min_y, COLOR_YELLOW);
            if (lap_hour_x != 0.0f || lap_hour_y != 0.0f)
                draw_line(CENTER_X, CENTER_Y, lap_hour_x, lap_hour_y, COLOR_YELLOW);
        }

        /* 7. MODE TEXT */
        const char *mode;
        if (stopwatch_running)
            mode = "STOPWATCH RUNNING  (A=STOP  C=LAP)    ";
        else if (stopwatch_elapsed_ms > 0)
            mode = "STOPWATCH STOPPED  (A=START B=RESET)  ";
        else
            mode = "CLOCK MODE         (A=START STOPWATCH)";

        display_draw_string(10, 220, mode, COLOR_GREEN, COLOR_BLACK);

        sleep_ms(50);          // ~20 fps – smooth enough for hands
    }
}
