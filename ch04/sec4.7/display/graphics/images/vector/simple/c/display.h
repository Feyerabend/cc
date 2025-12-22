#ifndef DISPLAY_H
#define DISPLAY_H

#include <stdint.h>
#include <stdbool.h>
#include "pico/stdlib.h"

#define DISPLAY_WIDTH  320
#define DISPLAY_HEIGHT 240

#define COLOR_BLACK   0x0000
#define COLOR_WHITE   0xFFFF
#define COLOR_RED     0xF800
#define COLOR_GREEN   0x07E0
#define COLOR_BLUE    0x001F
#define COLOR_YELLOW  0xFFE0
#define COLOR_CYAN    0x07FF
#define COLOR_MAGENTA 0xF81F

typedef enum {
    BUTTON_A, BUTTON_B, BUTTON_X, BUTTON_Y, BUTTON_COUNT
} button_t;

typedef void (*button_callback_t)(button_t button);

typedef enum {
    DISPLAY_OK,
    DISPLAY_ERROR_INIT_FAILED,
    DISPLAY_ERROR_DMA_FAILED,
    DISPLAY_ERROR_INVALID_PARAM,
    DISPLAY_ERROR_NOT_INITIALIZED
} display_error_t;

// Display
display_error_t display_pack_init(void);
display_error_t display_clear(uint16_t color);
display_error_t display_fill_rect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint16_t color);
display_error_t display_draw_pixel(uint16_t x, uint16_t y, uint16_t color);
display_error_t display_blit_full(const uint16_t *pixels);
display_error_t display_draw_char(uint16_t x, uint16_t y, char c, uint16_t color, uint16_t bg);
display_error_t display_draw_string(uint16_t x, uint16_t y, const char *str, uint16_t color, uint16_t bg);
display_error_t display_set_backlight(bool on);

// Buttons
display_error_t buttons_init(void);
void buttons_update(void);
bool button_pressed(button_t btn);
bool button_just_pressed(button_t btn);
bool button_just_released(button_t btn);
display_error_t button_set_callback(button_t btn, button_callback_t cb);

// Utility
bool display_is_initialized(void);
bool display_dma_busy(void);
void display_wait_for_dma(void);
void display_cleanup(void);
const char* display_error_string(display_error_t err);

// Font
const uint8_t* display_get_font_char(char c);

#endif
