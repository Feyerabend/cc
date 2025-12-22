#ifndef DISPLAY_H
#define DISPLAY_H

#include <stdint.h>
#include <stdbool.h>
#include "pico/stdlib.h"

// Display Pack 2.0 specifications: 320x240 pixels
#define DISPLAY_WIDTH 320
#define DISPLAY_HEIGHT 240

// Colors (RGB565 format)
#define COLOR_BLACK     0x0000
#define COLOR_WHITE     0xFFFF
#define COLOR_RED       0xF800
#define COLOR_GREEN     0x07E0
#define COLOR_BLUE      0x001F
#define COLOR_YELLOW    0xFFE0
#define COLOR_CYAN      0x07FF
#define COLOR_MAGENTA   0xF81F

// Button definitions
typedef enum {
    BUTTON_A = 0,
    BUTTON_B = 1,
    BUTTON_X = 2,
    BUTTON_Y = 3,
    BUTTON_COUNT = 4  // Added for bounds checking ..
} button_t;

// Button callback function type
typedef void (*button_callback_t)(button_t button);

// Error codes
typedef enum {
    DISPLAY_OK = 0,
    DISPLAY_ERROR_INIT_FAILED,
    DISPLAY_ERROR_DMA_FAILED,
    DISPLAY_ERROR_INVALID_PARAM,
    DISPLAY_ERROR_NOT_INITIALIZED
} display_error_t;

// Display functions
display_error_t display_pack_init(void);
display_error_t display_clear(uint16_t color);
display_error_t display_fill_rect(uint16_t x, uint16_t y, uint16_t width, uint16_t height, uint16_t color);
display_error_t display_draw_pixel(uint16_t x, uint16_t y, uint16_t color);
display_error_t display_draw_char(uint16_t x, uint16_t y, char c, uint16_t color, uint16_t bg_color);
display_error_t display_draw_string(uint16_t x, uint16_t y, const char* str, uint16_t color, uint16_t bg_color);
display_error_t display_set_backlight(bool on);

// Button functions
display_error_t buttons_init(void);
void buttons_update(void);
bool button_pressed(button_t button);
bool button_just_pressed(button_t button);
bool button_just_released(button_t button);
display_error_t button_set_callback(button_t button, button_callback_t callback);

// Utility functions
bool display_is_initialized(void);
bool display_dma_busy(void);
void display_wait_for_dma(void);
void display_cleanup(void);
const char* display_error_string(display_error_t error);

#endif // DISPLAY_H
