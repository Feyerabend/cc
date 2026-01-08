#pragma once

#include <stdint.h>
#include <stdbool.h>

/* Display geometry */
#define GC9A01_WIDTH   240
#define GC9A01_HEIGHT  240
#define GC9A01_RADIUS  120

/* Colour format: RGB565 */
typedef uint16_t colour_t;

/* Initialisation */
void gc9a01_init(void);
void gc9a01_reset(void);

/* Display control */
void gc9a01_sleep(bool enable);
void gc9a01_invert(bool enable);
void gc9a01_set_rotation(uint8_t r);

/* Drawing primitives */
void gc9a01_clear(colour_t c);
void gc9a01_pixel(int x, int y, colour_t c);
void gc9a01_hline(int x, int y, int w, colour_t c);
void gc9a01_vline(int x, int y, int h, colour_t c);
void gc9a01_rect(int x, int y, int w, int h, colour_t c);
void gc9a01_fill_rect(int x, int y, int w, int h, colour_t c);
void gc9a01_line(int x0, int y0, int x1, int y1, colour_t c);

/* Circular helpers */
bool gc9a01_in_circle(int x, int y);
void gc9a01_circle_clip(bool enable);

/* Scrolling */
void gc9a01_scroll(int offset);

/* Low-level access (advanced use) */
void gc9a01_set_window(int x0, int y0, int x1, int y1);
void gc9a01_write_pixels(const uint16_t *data, int count);
