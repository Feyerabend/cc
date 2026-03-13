#include "display.h"
#include "font.h"
#include "hardware/spi.h"
#include "hardware/sync.h"
#include "hardware/gpio.h"
#include "hardware/dma.h"
#include "hardware/irq.h"
#include "pico/time.h"
#include "hardware/timer.h"

#include <string.h>
#include <math.h>

// Display Pack pin defs
#define DISPLAY_CS_PIN 17
#define DISPLAY_CLK_PIN 18
#define DISPLAY_MOSI_PIN 19
#define DISPLAY_DC_PIN 16
#define DISPLAY_RESET_PIN 21
#define DISPLAY_BL_PIN 20

// Button pins
#define BUTTON_A_PIN 12
#define BUTTON_B_PIN 13
#define BUTTON_X_PIN 14
#define BUTTON_Y_PIN 15

// DMA configuration
static int dma_channel = -1;
static bool dma_initialized = false;
static volatile bool dma_busy = false;
static bool display_initialized = false;

// Internal state with proper bounds checking
static button_callback_t button_callbacks[BUTTON_COUNT] = {NULL};
static volatile bool button_state[BUTTON_COUNT] = {false};
static volatile bool button_last_state[BUTTON_COUNT] = {false};
static volatile uint32_t last_button_check = 0;
static bool buttons_initialized = false;

// DMA buffer for repeated pixel data (for solid fills)
static uint8_t dma_fill_buffer[512]; // Buffer for repeated color data
static uint8_t dma_single_pixel[2];  // Single pixel buffer for DMA

// Button pin mapping
static const uint8_t button_pins[BUTTON_COUNT] = {
    BUTTON_A_PIN, BUTTON_B_PIN, BUTTON_X_PIN, BUTTON_Y_PIN
};

// Error message strings
static const char* error_strings[] = {
    "OK",
    "Init failed",
    "DMA operation failed",
    "Invalid parameter",
    "Display not initialised"
};

// Get current time in milliseconds
static inline uint32_t get_time_ms(void) {
    return to_ms_since_boot(get_absolute_time());
}

// Wait for SPI to finish transmitting (FIFO drain)
static inline void spi_wait_idle(void) {
    // Wait for TX FIFO to empty and SPI to become idle
    while (spi_is_busy(spi0)) {
        tight_loop_contents();
    }
    // Small delay to ensure last byte is fully clocked out
    sleep_us(1);
}

// DMA interrupt handler with safety checks
void __isr dma_handler() {
    // Check if this is our channel and clear the interrupt
    if (dma_channel >= 0 && (dma_hw->ints0 & (1u << dma_channel))) {
        dma_hw->ints0 = 1u << dma_channel;
        dma_busy = false;
    }
}

// Init DMA with error checking
static display_error_t dma_init(void) {
    if (dma_initialized) return DISPLAY_OK;
    
    // Get a free DMA channel
    dma_channel = dma_claim_unused_channel(false);
    if (dma_channel < 0) return DISPLAY_ERROR_DMA_FAILED;
    
    // Set up the DMA interrupt
    dma_channel_set_irq0_enabled(dma_channel, true);
    irq_set_exclusive_handler(DMA_IRQ_0, dma_handler);
    irq_set_enabled(DMA_IRQ_0, true);
    
    dma_initialized = true;
    return DISPLAY_OK;
}

static bool dma_wait_for_finish_timeout(uint32_t timeout_ms) {
    uint32_t start = get_time_ms();
    while (dma_busy) {
        if (get_time_ms() - start > timeout_ms) {
            return false; // Timeout
        }
        tight_loop_contents();
    }
    return true;
}

// DMA wait with SPI sync
static void dma_wait_for_finish(void) {
    if (!dma_wait_for_finish_timeout(1000)) { // 1 second timeout
        // Force stop the DMA channel if timeout occurs
        if (dma_channel >= 0) {
            dma_channel_abort(dma_channel);
            dma_hw->ints0 = 1u << dma_channel; // Clear pending interrupt to prevent ghost IRQs
        }
        dma_busy = false;
    }
    // Wait for SPI FIFO to drain after DMA completes
    spi_wait_idle();
}

// Fixed DMA SPI write with proper sync
static display_error_t dma_spi_write_buffer(uint8_t* data, size_t len) {
    if (!data || len == 0) return DISPLAY_ERROR_INVALID_PARAM;
    
    if (!dma_initialized && dma_init() != DISPLAY_OK) {
        // Fallback to regular SPI if DMA init fails
        spi_write_blocking(spi0, data, len);
        spi_wait_idle();
        return DISPLAY_OK;
    }
    
    // Ensure previous transfer is completely done
    dma_wait_for_finish();
    
    // Set busy flag before configuring to prevent race condition
    dma_busy = true;
    
    // Configure DMA channel
    dma_channel_config c = dma_channel_get_default_config(dma_channel);
    channel_config_set_transfer_data_size(&c, DMA_SIZE_8);
    channel_config_set_dreq(&c, spi_get_dreq(spi0, true));
    channel_config_set_read_increment(&c, true);
    channel_config_set_write_increment(&c, false);
    
    // Set up the transfer
    dma_channel_configure(
        dma_channel,
        &c,
        &spi_get_hw(spi0)->dr,
        data,
        len,
        true  // Start immediately
    );
    
    return DISPLAY_OK;
}

// Display low-level functions with error checking
static display_error_t display_write_command(uint8_t cmd) {
    if (!display_initialized) return DISPLAY_ERROR_NOT_INITIALIZED;
    
    dma_wait_for_finish();
    gpio_put(DISPLAY_DC_PIN, 0);
    gpio_put(DISPLAY_CS_PIN, 0);
    spi_write_blocking(spi0, &cmd, 1);
    spi_wait_idle();
    gpio_put(DISPLAY_CS_PIN, 1);
    return DISPLAY_OK;
}

static display_error_t display_write_data(uint8_t data) {
    if (!display_initialized) return DISPLAY_ERROR_NOT_INITIALIZED;
    
    dma_wait_for_finish();
    gpio_put(DISPLAY_DC_PIN, 1);
    gpio_put(DISPLAY_CS_PIN, 0);
    spi_write_blocking(spi0, &data, 1);
    spi_wait_idle();
    gpio_put(DISPLAY_CS_PIN, 1);
    return DISPLAY_OK;
}

static display_error_t display_write_data_buf(uint8_t *data, size_t len) {
    if (!display_initialized) return DISPLAY_ERROR_NOT_INITIALIZED;
    if (!data || len == 0) return DISPLAY_ERROR_INVALID_PARAM;
    
    dma_wait_for_finish();
    gpio_put(DISPLAY_DC_PIN, 1);
    gpio_put(DISPLAY_CS_PIN, 0);
    
    display_error_t result = DISPLAY_OK;
    if (len > 64) { // Use DMA for larger transfers
        result = dma_spi_write_buffer(data, len);
        // Must wait for DMA to complete before raising CS
        dma_wait_for_finish();
    } else {
        spi_write_blocking(spi0, data, len);
        spi_wait_idle();
    }
    
    gpio_put(DISPLAY_CS_PIN, 1);
    return result;
}

static display_error_t display_set_window(uint16_t x0, uint16_t y0, uint16_t x1, uint16_t y1) {
    display_error_t result;
    
    if ((result = display_write_command(0x2A)) != DISPLAY_OK) return result; // CASET
    if ((result = display_write_data(x0 >> 8)) != DISPLAY_OK) return result;
    if ((result = display_write_data(x0 & 0xFF)) != DISPLAY_OK) return result;
    if ((result = display_write_data(x1 >> 8)) != DISPLAY_OK) return result;
    if ((result = display_write_data(x1 & 0xFF)) != DISPLAY_OK) return result;

    if ((result = display_write_command(0x2B)) != DISPLAY_OK) return result; // RASET
    if ((result = display_write_data(y0 >> 8)) != DISPLAY_OK) return result;
    if ((result = display_write_data(y0 & 0xFF)) != DISPLAY_OK) return result;
    if ((result = display_write_data(y1 >> 8)) != DISPLAY_OK) return result;
    if ((result = display_write_data(y1 & 0xFF)) != DISPLAY_OK) return result;
    
    if ((result = display_write_command(0x2C)) != DISPLAY_OK) return result; // RAMWR
    
    return DISPLAY_OK;
}

// Public display functions with robust error handling
display_error_t display_pack_init(void) {
    if (display_initialized) return DISPLAY_OK;
    
    // Init SPI (reduced speed for stability)
    if (spi_init(spi0, 31250000) == 0) return DISPLAY_ERROR_INIT_FAILED;
    gpio_set_function(DISPLAY_CLK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(DISPLAY_MOSI_PIN, GPIO_FUNC_SPI);
    
    // Init control pins
    gpio_init(DISPLAY_CS_PIN);
    gpio_init(DISPLAY_DC_PIN);
    gpio_init(DISPLAY_RESET_PIN);
    gpio_init(DISPLAY_BL_PIN);
    
    gpio_set_dir(DISPLAY_CS_PIN, GPIO_OUT);
    gpio_set_dir(DISPLAY_DC_PIN, GPIO_OUT);
    gpio_set_dir(DISPLAY_RESET_PIN, GPIO_OUT);
    gpio_set_dir(DISPLAY_BL_PIN, GPIO_OUT);
    
    // Start with everything in known state
    gpio_put(DISPLAY_CS_PIN, 1);
    gpio_put(DISPLAY_DC_PIN, 1);
    gpio_put(DISPLAY_BL_PIN, 0);
    
    // Hardware reset
    gpio_put(DISPLAY_RESET_PIN, 1);
    sleep_ms(10);
    gpio_put(DISPLAY_RESET_PIN, 0);
    sleep_ms(10);
    gpio_put(DISPLAY_RESET_PIN, 1);
    sleep_ms(120);
    
    display_initialized = true; // Set before using display commands
    
    // Init DMA
    if (dma_init() != DISPLAY_OK) {
        // Continue without DMA - not critical
    }
    
    // ST7789V2 init sequence
    display_error_t result;
    if ((result = display_write_command(0x01)) != DISPLAY_OK) goto init_error; // SWRESET
    sleep_ms(150);
    
    if ((result = display_write_command(0x11)) != DISPLAY_OK) goto init_error; // SLPOUT
    sleep_ms(120);
    
    if ((result = display_write_command(0x3A)) != DISPLAY_OK) goto init_error; // COLMOD
    if ((result = display_write_data(0x55)) != DISPLAY_OK) goto init_error;    // 16-bit RGB565
    
    if ((result = display_write_command(0x36)) != DISPLAY_OK) goto init_error; // MADCTL
    if ((result = display_write_data(0x70)) != DISPLAY_OK) goto init_error;    // Row/Column exchange, RGB order
    
    // Set display area to full 320x240
    if ((result = display_write_command(0x2A)) != DISPLAY_OK) goto init_error; // CASET
    if ((result = display_write_data(0x00)) != DISPLAY_OK) goto init_error;
    if ((result = display_write_data(0x00)) != DISPLAY_OK) goto init_error;
    if ((result = display_write_data(0x01)) != DISPLAY_OK) goto init_error;
    if ((result = display_write_data(0x3F)) != DISPLAY_OK) goto init_error;

    if ((result = display_write_command(0x2B)) != DISPLAY_OK) goto init_error; // RASET
    if ((result = display_write_data(0x00)) != DISPLAY_OK) goto init_error;
    if ((result = display_write_data(0x00)) != DISPLAY_OK) goto init_error;
    if ((result = display_write_data(0x00)) != DISPLAY_OK) goto init_error;
    if ((result = display_write_data(0xEF)) != DISPLAY_OK) goto init_error;
    
    // Additional settings (continue even if some fail)
    display_write_command(0xB2); // PORCTRL
    display_write_data(0x0C);
    display_write_data(0x0C);
    display_write_data(0x00);
    display_write_data(0x33);
    display_write_data(0x33);
    
    display_write_command(0xB7); // GCTRL
    display_write_data(0x35);
    
    display_write_command(0xBB); // VCOMS
    display_write_data(0x19);
    
    display_write_command(0xC0); // LCMCTRL
    display_write_data(0x2C);
    
    display_write_command(0xC2); // VDVVRHEN
    display_write_data(0x01);
    
    display_write_command(0xC3); // VRHS
    display_write_data(0x12);
    
    display_write_command(0xC4); // VDVS
    display_write_data(0x20);
    
    display_write_command(0xC6); // FRCTRL2
    display_write_data(0x0F);
    
    display_write_command(0xD0); // PWCTRL1
    display_write_data(0xA4);
    display_write_data(0xA1);
    
    // Gamma correction (continue even if fails)
    display_write_command(0xE0);
    display_write_data(0xD0); display_write_data(0x04); display_write_data(0x0D);
    display_write_data(0x11); display_write_data(0x13); display_write_data(0x2B);
    display_write_data(0x3F); display_write_data(0x54); display_write_data(0x4C);
    display_write_data(0x18); display_write_data(0x0D); display_write_data(0x0B);
    display_write_data(0x1F); display_write_data(0x23);
    
    display_write_command(0xE1);
    display_write_data(0xD0); display_write_data(0x04); display_write_data(0x0C);
    display_write_data(0x11); display_write_data(0x13); display_write_data(0x2C);
    display_write_data(0x3F); display_write_data(0x44); display_write_data(0x51);
    display_write_data(0x2F); display_write_data(0x1F); display_write_data(0x1F);
    display_write_data(0x20); display_write_data(0x23);
    
    display_write_command(0x21); // INVON
    display_write_command(0x13); // NORON
    sleep_ms(10);
    display_write_command(0x29); // DISPON
    sleep_ms(100);
    
    // Turn on backlight
    gpio_put(DISPLAY_BL_PIN, 1);
    
    return DISPLAY_OK;

init_error:
    display_initialized = false;
    return result;
}

display_error_t display_clear(uint16_t color) {
    return display_fill_rect(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT, color);
}

display_error_t display_fill_rect(uint16_t x, uint16_t y, uint16_t width, uint16_t height, uint16_t color) {
    if (!display_initialized) return DISPLAY_ERROR_NOT_INITIALIZED;
    if (x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return DISPLAY_ERROR_INVALID_PARAM;
    
    // Clamp dimensions to display bounds
    if (x + width > DISPLAY_WIDTH) width = DISPLAY_WIDTH - x;
    if (y + height > DISPLAY_HEIGHT) height = DISPLAY_HEIGHT - y;
    if (width == 0 || height == 0) return DISPLAY_OK;
    
    uint32_t pixel_count = (uint32_t)width * (uint32_t)height;
    
    // Set window with inclusive end coordinates
    display_error_t result = display_set_window(x, y, x + width - 1, y + height - 1);
    if (result != DISPLAY_OK) return result;
    
    // Prepare color data
    uint8_t color_bytes[2] = {color >> 8, color & 0xFF};
    
    gpio_put(DISPLAY_DC_PIN, 1);
    gpio_put(DISPLAY_CS_PIN, 0);
    
    if (pixel_count > 32 && dma_initialized) {
        // Use DMA for large fills
        size_t buffer_pixels = sizeof(dma_fill_buffer) / 2;
        
        // Fill the entire buffer with the color
        for (size_t i = 0; i < buffer_pixels; i++) {
            dma_fill_buffer[i * 2] = color_bytes[0];
            dma_fill_buffer[i * 2 + 1] = color_bytes[1];
        }
        
        // Send full buffer chunks
        uint32_t full_chunks = pixel_count / buffer_pixels;
        for (uint32_t i = 0; i < full_chunks; i++) {
            result = dma_spi_write_buffer(dma_fill_buffer, sizeof(dma_fill_buffer));
            if (result != DISPLAY_OK) break;
            // Wait for each chunk to complete before starting next
            dma_wait_for_finish();
        }
        
        // Send remaining pixels
        if (result == DISPLAY_OK) {
            uint32_t remaining = pixel_count % buffer_pixels;
            if (remaining > 0) {
                result = dma_spi_write_buffer(dma_fill_buffer, remaining * 2);
                // Wait for final chunk to complete
                dma_wait_for_finish();
            }
        }
    } else {
        // Use blocking SPI for small fills
        for (uint32_t i = 0; i < pixel_count; i++) {
            spi_write_blocking(spi0, color_bytes, 2);
        }
        // Ensure SPI is idle after blocking writes
        spi_wait_idle();
    }
    
    // Ensure all data is sent before raising CS
    dma_wait_for_finish();
    gpio_put(DISPLAY_CS_PIN, 1);
    
    return result;
}

display_error_t display_draw_pixel(uint16_t x, uint16_t y, uint16_t color) {
    if (x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return DISPLAY_ERROR_INVALID_PARAM;
    return display_fill_rect(x, y, 1, 1, color);
}

display_error_t display_blit_full(const uint16_t *pixels) {
    if (!display_initialized) return DISPLAY_ERROR_NOT_INITIALIZED;
    if (!pixels) return DISPLAY_ERROR_INVALID_PARAM;

    display_error_t result = display_set_window(0, 0, DISPLAY_WIDTH - 1, DISPLAY_HEIGHT - 1);
    if (result != DISPLAY_OK) return result;

    dma_wait_for_finish();
    gpio_put(DISPLAY_DC_PIN, 1);
    gpio_put(DISPLAY_CS_PIN, 0);

    result = dma_spi_write_buffer((uint8_t *)pixels, DISPLAY_WIDTH * DISPLAY_HEIGHT * 2);
    
    // Must wait for DMA to complete before raising CS
    dma_wait_for_finish();

    gpio_put(DISPLAY_CS_PIN, 1);
    return result;
}

display_error_t display_draw_char(uint16_t x, uint16_t y, char c, uint16_t color, uint16_t bg_color) {
    if (!display_initialized) return DISPLAY_ERROR_NOT_INITIALIZED;
    if (x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return DISPLAY_ERROR_INVALID_PARAM;

    uint8_t code = (unsigned char)c;

    if (code >= 128 && code <= 143) {
        // Block character: 8×8, MSB = leftmost pixel, no left pad
        for (int py = 0; py < 8 && (y + py) < DISPLAY_HEIGHT; py++) {
            uint8_t row_bits = font_block[code - 128][py];
            for (int px = 0; px < 8 && (x + px) < DISPLAY_WIDTH; px++) {
                uint16_t pixel_color = (row_bits & (0x80 >> px)) ? color : bg_color;
                display_error_t result = display_draw_pixel(x + px, y + py, pixel_color);
                if (result != DISPLAY_OK) return result;
            }
        }
        return DISPLAY_OK;
    }

    int idx = code - 32;
    if (idx < 0 || idx >= (int)(sizeof(font5x8)/sizeof(font5x8[0]))) idx = 0; // default to space

    const uint8_t *char_data = font5x8[idx];

    // Draw 5px glyph with 1px left pad; data[4-col] = left-to-right column order
    for (int col = 0; col < 5 && (x + 1 + col) < DISPLAY_WIDTH; col++) {
        uint8_t line = char_data[4 - col];
        for (int row = 0; row < 8 && (y + row) < DISPLAY_HEIGHT; row++) {
            uint16_t pixel_color = (line & (1 << row)) ? color : bg_color;
            display_error_t result = display_draw_pixel(x + 1 + col, y + row, pixel_color);
            if (result != DISPLAY_OK) return result;
        }
    }
    return DISPLAY_OK;
}

display_error_t display_draw_string(uint16_t x, uint16_t y, const char* str, uint16_t color, uint16_t bg_color) {
    if (!display_initialized) return DISPLAY_ERROR_NOT_INITIALIZED;
    if (!str) return DISPLAY_ERROR_INVALID_PARAM;
    if (x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return DISPLAY_ERROR_INVALID_PARAM;
    
    int offset_x = 0;
    while (*str && (x + offset_x) < DISPLAY_WIDTH) {
        display_error_t result = display_draw_char(x + offset_x, y, *str, color, bg_color);
        if (result != DISPLAY_OK) return result;
        offset_x += 6; // 5 pixel font + 1 pixel spacing
        str++;
    }
    return DISPLAY_OK;
}

display_error_t display_set_backlight(bool on) {
    if (!display_initialized) return DISPLAY_ERROR_NOT_INITIALIZED;
    gpio_put(DISPLAY_BL_PIN, on ? 1 : 0);
    return DISPLAY_OK;
}

// Button functions with robust error handling
display_error_t buttons_init(void) {
    if (buttons_initialized) return DISPLAY_OK;
    
    for (int i = 0; i < BUTTON_COUNT; i++) {
        gpio_init(button_pins[i]);
        gpio_set_dir(button_pins[i], GPIO_IN);
        gpio_pull_up(button_pins[i]);
        button_state[i] = true; // Pulled up initially
        button_last_state[i] = true;
        button_callbacks[i] = NULL;
    }
    
    buttons_initialized = true;
    return DISPLAY_OK;
}

void buttons_update(void) {
    if (!buttons_initialized) return;
    
    uint32_t now = get_time_ms();
    
    // Debounce - only check buttons every 50ms
    if (now - last_button_check < 50) return;
    last_button_check = now;
    
    for (int i = 0; i < BUTTON_COUNT; i++) {
        button_last_state[i] = button_state[i];
        button_state[i] = gpio_get(button_pins[i]);
        
        // Call callback if button was just pressed and callback exists
        if (button_last_state[i] && !button_state[i] && button_callbacks[i]) {
            // Extra safety: check callback is still valid before calling
            if (button_callbacks[i] != NULL) {
                button_callbacks[i]((button_t)i);
            }
        }
    }
}

bool button_pressed(button_t button) {
    if (!buttons_initialized || button >= BUTTON_COUNT) return false;
    return !button_state[button]; // Inverted because of pull-up
}

bool button_just_pressed(button_t button) {
    if (!buttons_initialized || button >= BUTTON_COUNT) return false;
    return button_last_state[button] && !button_state[button];
}

bool button_just_released(button_t button) {
    if (!buttons_initialized || button >= BUTTON_COUNT) return false;
    return !button_last_state[button] && button_state[button];
}

display_error_t button_set_callback(button_t button, button_callback_t callback) {
    if (!buttons_initialized) return DISPLAY_ERROR_NOT_INITIALIZED;
    if (button >= BUTTON_COUNT) return DISPLAY_ERROR_INVALID_PARAM;
    
    // Disable interrupts briefly to ensure atomic update
    uint32_t interrupts = save_and_disable_interrupts();
    button_callbacks[button] = callback;
    restore_interrupts(interrupts);
    
    return DISPLAY_OK;
}

// Utility functions
bool display_is_initialized(void) {
    return display_initialized;
}

bool display_dma_busy(void) {
    return dma_busy;
}

void display_wait_for_dma(void) {
    dma_wait_for_finish();
}

const char* display_error_string(display_error_t error) {
    if (error < 0 || error >= (sizeof(error_strings) / sizeof(error_strings[0]))) {
        return "Unknown error";
    }
    return error_strings[error];
}

// Function to deinit DMA safely
static void display_dma_deinit(void) {
    if (dma_initialized) {
        // Wait for any pending operations
        dma_wait_for_finish();
        
        // Disable interrupt and unclaim channel
        if (dma_channel >= 0) {
            dma_channel_set_irq0_enabled(dma_channel, false);
            dma_channel_unclaim(dma_channel);
        }
        
        irq_set_enabled(DMA_IRQ_0, false);
        dma_initialized = false;
        dma_channel = -1;
    }
}

// Cleanup function to be called at program end
void display_cleanup(void) {
    // Wait for any pending DMA operations
    display_wait_for_dma();
    
    // Clean up DMA
    display_dma_deinit();
    
    // Clean up SPI
    if (display_initialized) {
        spi_deinit(spi0);
        gpio_put(DISPLAY_BL_PIN, 0); // Turn off backlight
    }
    
    // Reset init flags
    display_initialized = false;
    buttons_initialized = false;
    
    // Clear button callbacks
    for (int i = 0; i < BUTTON_COUNT; i++) {
        button_callbacks[i] = NULL;
    }
}

// =============================================================================
// Framebuffer rendering helpers
// Inspired by the Flash renderer (Bitmap / ColorTransform / REdge)
// adapted for RGB565 and the Pico's memory layout.
// =============================================================================

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

static inline int clamp_i(int v, int lo, int hi) {
    return v < lo ? lo : v > hi ? hi : v;
}

// Apply a single Flash-style channel transform: out = clamp(in * mul/256 + add)
static inline uint8_t cx_apply_channel(uint8_t in, int mul, int add) {
    int v = ((int)in * mul >> 8) + add;
    if (v < 0) return 0;
    if (v > 255) return 255;
    return (uint8_t)v;
}

// Unpack RGB565 to 8-bit channels (r5→r8, g6→g8, b5→b8)
static inline void unpack565(uint16_t c, uint8_t *r, uint8_t *g, uint8_t *b) {
    *r = ((c >> 11) & 0x1F) << 3;
    *g = ((c >>  5) & 0x3F) << 2;
    *b =  (c        & 0x1F) << 3;
}

// Pack 8-bit RGB back to RGB565
static inline uint16_t pack565(uint8_t r, uint8_t g, uint8_t b) {
    return ((uint16_t)(r & 0xF8) << 8) |
           ((uint16_t)(g & 0xFC) << 3) |
           (b >> 3);
}

// Blend a pixel with given fractional weight (0–255) against the existing fb pixel
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

// ---------------------------------------------------------------------------
// fb_clear
// ---------------------------------------------------------------------------
void fb_clear(uint16_t *fb, uint16_t color) {
    int total = DISPLAY_WIDTH * DISPLAY_HEIGHT;
    for (int i = 0; i < total; i++) fb[i] = color;
}

// ---------------------------------------------------------------------------
// fb_draw_pixel
// ---------------------------------------------------------------------------
void fb_draw_pixel(uint16_t *fb, int x, int y, uint16_t color) {
    if ((unsigned)x < DISPLAY_WIDTH && (unsigned)y < DISPLAY_HEIGHT)
        fb[y * DISPLAY_WIDTH + x] = color;
}

// ---------------------------------------------------------------------------
// fb_fill_rect
// ---------------------------------------------------------------------------
void fb_fill_rect(uint16_t *fb, int x, int y, int w, int h, uint16_t color) {
    int x1 = clamp_i(x,     0, DISPLAY_WIDTH  - 1);
    int y1 = clamp_i(y,     0, DISPLAY_HEIGHT - 1);
    int x2 = clamp_i(x + w, 0, DISPLAY_WIDTH);
    int y2 = clamp_i(y + h, 0, DISPLAY_HEIGHT);
    for (int row = y1; row < y2; row++)
        for (int col = x1; col < x2; col++)
            fb[row * DISPLAY_WIDTH + col] = color;
}

// ---------------------------------------------------------------------------
// fb_draw_char
// Draws a 5×8 glyph centred (1px left pad) inside an 8×8 cell.
// Font bytes are stored right-column-first: data[0]=rightmost col, data[4]=leftmost col.
// Reading as data[4-col] gives left-to-right rendering.
// bit 0 of each byte = topmost pixel row.
// ---------------------------------------------------------------------------
void fb_draw_char(uint16_t *fb, int x, int y, char c, uint16_t fg, uint16_t bg) {
    if ((unsigned)x >= DISPLAY_WIDTH || (unsigned)y >= DISPLAY_HEIGHT) return;

    uint8_t code = (unsigned char)c;

    // Fill full 8×8 cell with bg
    for (int col = 0; col < 8 && (x + col) < (int)DISPLAY_WIDTH; col++)
        for (int row = 0; row < 8 && (y + row) < (int)DISPLAY_HEIGHT; row++)
            fb[(y + row) * DISPLAY_WIDTH + (x + col)] = bg;

    if (code >= 128 && code <= 143) {
        // Block character: 8×8, MSB = leftmost pixel, no left pad
        for (int row = 0; row < 8 && (y + row) < (int)DISPLAY_HEIGHT; row++) {
            uint8_t row_bits = font_block[code - 128][row];
            for (int col = 0; col < 8 && (x + col) < (int)DISPLAY_WIDTH; col++)
                if (row_bits & (0x80 >> col))
                    fb[(y + row) * DISPLAY_WIDTH + (x + col)] = fg;
        }
        return;
    }

    int idx = code - 32;
    if (idx < 0 || idx >= (int)(sizeof(font5x8)/sizeof(font5x8[0]))) idx = 0;
    const uint8_t *char_data = font5x8[idx];
    // Draw 5px glyph at columns 1..5 (1px left pad), data[4-col] = left-to-right
    for (int col = 0; col < 5 && (x + 1 + col) < (int)DISPLAY_WIDTH; col++) {
        uint8_t line = char_data[4 - col];
        for (int row = 0; row < 8 && (y + row) < (int)DISPLAY_HEIGHT; row++)
            if (line & (1 << row))
                fb[(y + row) * DISPLAY_WIDTH + (x + 1 + col)] = fg;
    }
}

// ---------------------------------------------------------------------------
// fb_draw_string
// ---------------------------------------------------------------------------
void fb_draw_string(uint16_t *fb, int x, int y, const char *str, uint16_t fg, uint16_t bg) {
    while (*str && x < (int)DISPLAY_WIDTH) {
        fb_draw_char(fb, x, y, *str++, fg, bg);
        x += 6;
    }
}

// ---------------------------------------------------------------------------
// fb_draw_line_aa  – Xiaolin Wu anti-aliased line
// Ported from the Flash REdge scanline walker concept: fractional pixel
// coverage is accumulated and blended rather than snapped to integer coords.
// ---------------------------------------------------------------------------
void fb_draw_line_aa(uint16_t *fb, float x0, float y0, float x1, float y1, uint16_t color) {
    bool steep = (y1 - y0 < 0 ? y0 - y1 : y1 - y0) >
                 (x1 - x0 < 0 ? x0 - x1 : x1 - x0);
    if (steep)   { float t; t=x0;x0=y0;y0=t; t=x1;x1=y1;y1=t; }
    if (x0 > x1) { float t; t=x0;x0=x1;x1=t; t=y0;y0=y1;y1=t; }

    float dx = x1 - x0, dy = y1 - y0;
    float grad = (dx == 0.0f) ? 1.0f : dy / dx;

    // First endpoint
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

    // Last endpoint
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

    // Interior pixels
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

// ---------------------------------------------------------------------------
// fb_draw_circle_aa – Xiaolin Wu anti-aliased circle
//
// Iterates x from 1 to r/√2; at each x computes y = sqrt(r²-x²).
// The fractional part of y drives alpha for the two adjacent pixels.
// 8-fold symmetry fills all octants from one pass.
// ---------------------------------------------------------------------------
void fb_draw_circle_aa(uint16_t *fb, int cx, int cy, int r, uint16_t color)
{
    if (r <= 0) return;

    /* Cardinal points (full opacity) */
    wu_plot_fb(fb, cx + r, cy,     255, color);
    wu_plot_fb(fb, cx - r, cy,     255, color);
    wu_plot_fb(fb, cx,     cy + r, 255, color);
    wu_plot_fb(fb, cx,     cy - r, 255, color);

    int r2 = r * r;
    for (int x = 1; ; x++) {
        float y = sqrtf((float)(r2 - x * x));
        if (y < (float)x) break;   /* past 45 °, done */

        int     yi = (int)y;
        uint8_t a  = (uint8_t)((y - yi) * 255.0f);
        uint8_t na = (uint8_t)(255 - a);

        /* +x quadrants */
        wu_plot_fb(fb, cx + x, cy + yi,     na, color);
        wu_plot_fb(fb, cx + x, cy + yi + 1, a,  color);
        wu_plot_fb(fb, cx + x, cy - yi,     na, color);
        wu_plot_fb(fb, cx + x, cy - yi - 1, a,  color);
        /* −x quadrants */
        wu_plot_fb(fb, cx - x, cy + yi,     na, color);
        wu_plot_fb(fb, cx - x, cy + yi + 1, a,  color);
        wu_plot_fb(fb, cx - x, cy - yi,     na, color);
        wu_plot_fb(fb, cx - x, cy - yi - 1, a,  color);
        /* swapped axes (fills complementary octants) */
        wu_plot_fb(fb, cx + yi,     cy + x, na, color);
        wu_plot_fb(fb, cx + yi + 1, cy + x, a,  color);
        wu_plot_fb(fb, cx - yi,     cy + x, na, color);
        wu_plot_fb(fb, cx - yi - 1, cy + x, a,  color);
        wu_plot_fb(fb, cx + yi,     cy - x, na, color);
        wu_plot_fb(fb, cx + yi + 1, cy - x, a,  color);
        wu_plot_fb(fb, cx - yi,     cy - x, na, color);
        wu_plot_fb(fb, cx - yi - 1, cy - x, a,  color);
    }
}

// ---------------------------------------------------------------------------
// fb_blit_scaled – bilinear scaled blit
//
// Ported from Flash Bitmap.GetSSRGBPixel() / Bitmap.Blt32to32().
// That code uses 16.16 fixed-point; we do the same for the Pico to keep
// it integer-friendly and fast.
//
// For each destination pixel (dx+px, dy+py) we find the corresponding source
// pixel in fixed-point, then bilinearly interpolate the 2×2 neighbourhood.
// ---------------------------------------------------------------------------
void fb_blit_scaled(uint16_t *fb,
                    const uint16_t *src, int sw, int sh,
                    int dx, int dy, int dw, int dh)
{
    if (!src || sw <= 0 || sh <= 0 || dw <= 0 || dh <= 0) return;

    // Step size in source image per destination pixel (16.16 fixed)
    int step_x = (sw << 16) / dw;
    int step_y = (sh << 16) / dh;

    for (int py = 0; py < dh; py++) {
        int oy = dy + py;
        if (oy < 0 || oy >= (int)DISPLAY_HEIGHT) continue;

        // Source Y in 16.16
        int sy16 = (int)(((long long)py * step_y));
        int sy   = sy16 >> 16;
        int fy   = (sy16 >> 8) & 0xFF; // fractional part (0–255)

        // Clamp row indices
        int sy0 = clamp_i(sy,   0, sh-1);
        int sy1 = clamp_i(sy+1, 0, sh-1);

        int sx16 = 0;
        for (int px = 0; px < dw; px++, sx16 += step_x) {
            int ox = dx + px;
            if (ox < 0 || ox >= (int)DISPLAY_WIDTH) continue;

            int sx  = sx16 >> 16;
            int fx  = (sx16 >> 8) & 0xFF; // fractional part (0–255)

            // Clamp column indices
            int sx0 = clamp_i(sx,   0, sw-1);
            int sx1 = clamp_i(sx+1, 0, sw-1);

            // Fetch the 2×2 neighbourhood
            uint16_t c00 = src[sy0 * sw + sx0];
            uint16_t c10 = src[sy0 * sw + sx1];
            uint16_t c01 = src[sy1 * sw + sx0];
            uint16_t c11 = src[sy1 * sw + sx1];

            // Unpack all four to 8-bit
            uint8_t r00,g00,b00, r10,g10,b10, r01,g01,b01, r11,g11,b11;
            unpack565(c00,&r00,&g00,&b00);
            unpack565(c10,&r10,&g10,&b10);
            unpack565(c01,&r01,&g01,&b01);
            unpack565(c11,&r11,&g11,&b11);

            // Bilinear blend using Flash-style fixed-point weights
            // w00=(255-fx)*(255-fy), etc., each 0–65025; divide by 255^2
            int ifx = 255 - fx, ify = 255 - fy;
            int w00 = ifx * ify, w10 = fx * ify;
            int w01 = ifx * fy,  w11 = fx * fy;
            int total = w00 + w10 + w01 + w11; // = 255*255 always
            if (total == 0) total = 1;

            uint8_t r = (uint8_t)((w00*r00 + w10*r10 + w01*r01 + w11*r11) / total);
            uint8_t g = (uint8_t)((w00*g00 + w10*g10 + w01*g01 + w11*g11) / total);
            uint8_t b = (uint8_t)((w00*b00 + w10*b10 + w01*b01 + w11*b11) / total);

            fb[oy * DISPLAY_WIDTH + ox] = pack565(r, g, b);
        }
    }
}

// ---------------------------------------------------------------------------
// fb_apply_color_transform – Flash ColorTransform ported to RGB565 framebuffer
//
// Each channel: out = clamp(in * mul/256 + add, 0, 255)
// This is exactly what Flash's ColorTransform.ApplyChannel() does.
// ---------------------------------------------------------------------------
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

    // Fast path: identity transform
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

