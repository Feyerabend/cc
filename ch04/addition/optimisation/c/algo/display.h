#ifndef DISPLAY_H
#define DISPLAY_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

// 320×240 landscape
#define DISPLAY_WIDTH  320
#define DISPLAY_HEIGHT 240

// RGB565 colors
#define COLOR_BLACK   0x0000
#define COLOR_WHITE   0xFFFF
#define COLOR_RED     0xF800
#define COLOR_GREEN   0x07E0
#define COLOR_BLUE    0x001F
#define COLOR_YELLOW  0xFFE0
#define COLOR_CYAN    0x07FF
#define COLOR_MAGENTA 0xF81F

// Buttons
typedef enum {
    BUTTON_A = 0,
    BUTTON_B = 1,
    BUTTON_X = 2,
    BUTTON_Y = 3,
    BUTTON_COUNT = 4
} button_t;

typedef void (*button_callback_t)(button_t button);

// Error codes
typedef enum {
    DISP_OK = 0,
    DISP_ERR_ALREADY_INIT,
    DISP_ERR_NOT_INIT,
    DISP_ERR_SPI_INIT_FAILED,
    DISP_ERR_GPIO_INIT_FAILED,
    DISP_ERR_RESET_FAILED,
    DISP_ERR_CONFIG_FAILED,
    DISP_ERR_NULL_POINTER,
    DISP_ERR_INVALID_COORDS,
    DISP_ERR_INVALID_DIMENSIONS,
    DISP_ERR_DMA_NOT_AVAILABLE,
    DISP_ERR_DMA_CONFIG_FAILED,
    DISP_ERR_DMA_TIMEOUT,
    DISP_ERR_CMD_FAILED,
    DISP_ERR_DATA_FAILED,
    DISP_ERR_UNKNOWN
} disp_error_t;

typedef struct {
    disp_error_t code;
    const char *function;
    int line;
    const char *message;
} disp_error_context_t;

typedef struct {
    uint32_t spi_baudrate;
    bool use_dma;
    uint32_t dma_timeout_ms;
    bool enable_backlight;
} disp_config_t;

// Default config
disp_config_t disp_get_default_config(void);

// Core
disp_error_t disp_init(const disp_config_t *config);
disp_error_t disp_deinit(void);
bool disp_is_initialized(void);

// Drawing (direct to display)
disp_error_t disp_clear(uint16_t color);
disp_error_t disp_fill_rect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint16_t color);
disp_error_t disp_draw_pixel(uint16_t x, uint16_t y, uint16_t color);
disp_error_t disp_blit(uint16_t x, uint16_t y, uint16_t w, uint16_t h, const uint16_t *pixels);

// Text (direct to display - full ASCII 32-127)
disp_error_t disp_draw_char(uint16_t x, uint16_t y, char c, uint16_t fg, uint16_t bg);
disp_error_t disp_draw_text(uint16_t x, uint16_t y, const char *text, uint16_t fg, uint16_t bg);

// Control
disp_error_t disp_set_backlight(bool enabled);
disp_error_t disp_wait_complete(uint32_t timeout_ms);

// Framebuffer mode (for smooth, flicker-free updates)
disp_error_t disp_framebuffer_alloc(void);
void disp_framebuffer_free(void);
uint16_t* disp_get_framebuffer(void);
disp_error_t disp_framebuffer_flush(void);
disp_error_t disp_framebuffer_clear(uint16_t color);
void disp_framebuffer_set_pixel(uint16_t x, uint16_t y, uint16_t color);

// Framebuffer drawing functions (draw to framebuffer instead of display)
void disp_framebuffer_fill_rect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint16_t color);
void disp_framebuffer_draw_char(uint16_t x, uint16_t y, char c, uint16_t fg, uint16_t bg);
void disp_framebuffer_draw_text(uint16_t x, uint16_t y, const char *text, uint16_t fg, uint16_t bg);

// Buttons
disp_error_t buttons_init(void);
void buttons_update(void);
bool button_pressed(button_t button);
bool button_just_pressed(button_t button);
bool button_just_released(button_t button);
disp_error_t button_set_callback(button_t button, button_callback_t callback);

// Error handling
const char* disp_error_string(disp_error_t error);
disp_error_context_t disp_get_last_error(void);
void disp_clear_error(void);

// Helper macro - returns error code
#define DISP_ERROR(code, msg) \
    (disp_set_error_context((code), __func__, __LINE__, (msg)), (code))

#endif // DISPLAY_H
