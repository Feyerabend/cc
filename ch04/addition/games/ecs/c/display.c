#include "display.h"
#include "hardware/spi.h"
#include "hardware/sync.h"
#include "hardware/gpio.h"
#include "hardware/dma.h"
#include "hardware/irq.h"
#include "pico/time.h"
#include "hardware/timer.h"

#include <string.h>

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

// Fixed 5x8 font (same as before but with bounds checking)
static const uint8_t font5x8[][5] = {
    {0x00, 0x00, 0x00, 0x00, 0x00}, // Space
    {0x00, 0x00, 0x5F, 0x00, 0x00}, // !
    {0x00, 0x07, 0x00, 0x07, 0x00}, // "
    {0x14, 0x7F, 0x14, 0x7F, 0x14}, // #
    {0x12, 0x2A, 0x7F, 0x2A, 0x24}, // $
    {0x62, 0x64, 0x08, 0x13, 0x23}, // %
    {0x50, 0x22, 0x55, 0x49, 0x36}, // &
    {0x00, 0x00, 0x07, 0x00, 0x00}, // '
    {0x00, 0x41, 0x22, 0x1C, 0x00}, // (
    {0x00, 0x1C, 0x22, 0x41, 0x00}, // )
    {0x14, 0x08, 0x3E, 0x08, 0x14}, // *
    {0x08, 0x08, 0x3E, 0x08, 0x08}, // +
    {0x00, 0x30, 0x50, 0x00, 0x00}, // ,
    {0x08, 0x08, 0x08, 0x08, 0x08}, // -
    {0x00, 0x60, 0x60, 0x00, 0x00}, // .
    {0x02, 0x04, 0x08, 0x10, 0x20}, // /
    {0x3E, 0x45, 0x49, 0x51, 0x3E}, // 0
    {0x00, 0x40, 0x7F, 0x42, 0x00}, // 1
    {0x46, 0x49, 0x51, 0x61, 0x42}, // 2
    {0x31, 0x4B, 0x45, 0x41, 0x21}, // 3
    {0x10, 0x7F, 0x12, 0x14, 0x18}, // 4
    {0x39, 0x49, 0x49, 0x49, 0x2F}, // 5
    {0x30, 0x49, 0x49, 0x4A, 0x3C}, // 6
    {0x07, 0x0D, 0x09, 0x71, 0x01}, // 7
    {0x36, 0x49, 0x49, 0x49, 0x36}, // 8
    {0x1E, 0x29, 0x49, 0x49, 0x0E}, // 9
    {0x00, 0x36, 0x36, 0x00, 0x00}, // :
    {0x00, 0x36, 0x76, 0x00, 0x00}, // ;
    {0x00, 0x41, 0x22, 0x14, 0x08}, // <
    {0x14, 0x14, 0x14, 0x14, 0x14}, // =
    {0x08, 0x14, 0x22, 0x41, 0x00}, // >
    {0x06, 0x09, 0x51, 0x01, 0x06}, // ?
    {0x3E, 0x41, 0x79, 0x49, 0x32}, // @
    {0x7E, 0x11, 0x11, 0x11, 0x7E}, // A
    {0x36, 0x49, 0x49, 0x49, 0x7F}, // B
    {0x22, 0x41, 0x41, 0x41, 0x3E}, // C
    {0x1C, 0x22, 0x41, 0x41, 0x7F}, // D
    {0x41, 0x49, 0x49, 0x49, 0x7F}, // E
    {0x01, 0x09, 0x09, 0x09, 0x7F}, // F
    {0x7A, 0x49, 0x49, 0x41, 0x3E}, // G
    {0x7F, 0x08, 0x08, 0x08, 0x7F}, // H
    {0x00, 0x41, 0x7F, 0x41, 0x00}, // I
    {0x01, 0x3F, 0x41, 0x40, 0x20}, // J
    {0x41, 0x22, 0x14, 0x08, 0x7F}, // K
    {0x40, 0x40, 0x40, 0x40, 0x7F}, // L
    {0x7F, 0x02, 0x0C, 0x02, 0x7F}, // M
    {0x7F, 0x10, 0x0C, 0x02, 0x7F}, // N
    {0x3E, 0x41, 0x41, 0x41, 0x3E}, // O
    {0x06, 0x09, 0x09, 0x09, 0x7F}, // P
    {0x5E, 0x21, 0x51, 0x41, 0x3E}, // Q
    {0x46, 0x29, 0x19, 0x09, 0x7F}, // R
    {0x31, 0x49, 0x49, 0x49, 0x46}, // S
    {0x01, 0x01, 0x7F, 0x01, 0x01}, // T
    {0x3F, 0x40, 0x40, 0x40, 0x3F}, // U
    {0x1F, 0x20, 0x40, 0x20, 0x1F}, // V
    {0x3F, 0x40, 0x38, 0x40, 0x3F}, // W
    {0x63, 0x14, 0x08, 0x14, 0x63}, // X
    {0x07, 0x08, 0x70, 0x08, 0x07}, // Y
    {0x43, 0x45, 0x49, 0x51, 0x61}, // Z
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

// DMA interrupt handler with safety checks
void __isr dma_handler() {
    // Check if this is our channel and clear the interrupt
    if (dma_channel >= 0 && (dma_hw->ints0 & (1u << dma_channel))) {
        dma_hw->ints0 = 1u << dma_channel;
        dma_busy = false;
    }
}

// Initialize DMA with error checking
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

// Safe DMA wait
static void dma_wait_for_finish(void) {
    if (!dma_wait_for_finish_timeout(1000)) { // 1 second timeout
        // Force stop the DMA channel if timeout occurs
        if (dma_channel >= 0) {
            dma_channel_abort(dma_channel);
            dma_hw->ints0 = 1u << dma_channel; // Clear pending interrupt to prevent ghost IRQs
        }
        dma_busy = false;
    }
}

// DMA-based SPI write for buffer data with error checking
static display_error_t dma_spi_write_buffer(uint8_t* data, size_t len) {
    if (!data || len == 0) return DISPLAY_ERROR_INVALID_PARAM;
    
    if (!dma_initialized && dma_init() != DISPLAY_OK) {
        // Fallback to regular SPI if DMA init fails
        spi_write_blocking(spi0, data, len);
        return DISPLAY_OK;
    }
    
    dma_wait_for_finish();
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
        false
    );
    
    // Start the transfer
    dma_channel_start(dma_channel);
    return DISPLAY_OK;
}

// Display low-level functions with error checking
static display_error_t display_write_command(uint8_t cmd) {
    if (!display_initialized) return DISPLAY_ERROR_NOT_INITIALIZED;
    
    dma_wait_for_finish();
    gpio_put(DISPLAY_DC_PIN, 0);
    gpio_put(DISPLAY_CS_PIN, 0);
    spi_write_blocking(spi0, &cmd, 1);
    gpio_put(DISPLAY_CS_PIN, 1);
    return DISPLAY_OK;
}

static display_error_t display_write_data(uint8_t data) {
    if (!display_initialized) return DISPLAY_ERROR_NOT_INITIALIZED;
    
    dma_wait_for_finish();
    gpio_put(DISPLAY_DC_PIN, 1);
    gpio_put(DISPLAY_CS_PIN, 0);
    spi_write_blocking(spi0, &data, 1);
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
        dma_wait_for_finish();
    } else {
        spi_write_blocking(spi0, data, len);
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
    
    uint32_t pixel_count = width * height;
    
    display_error_t result = display_set_window(x, y, x + width - 1, y + height - 1);
    if (result != DISPLAY_OK) return result;
    
    // Prepare color data
    uint8_t color_bytes[2] = {color >> 8, color & 0xFF};
    dma_single_pixel[0] = color_bytes[0];
    dma_single_pixel[1] = color_bytes[1];
    
    gpio_put(DISPLAY_DC_PIN, 1);
    gpio_put(DISPLAY_CS_PIN, 0);
    
    if (pixel_count > 32 && dma_initialized) {
        // Use DMA for large fills
        size_t buffer_pixels = sizeof(dma_fill_buffer) / 2;
        for (size_t i = 0; i < buffer_pixels; i++) {
            dma_fill_buffer[i * 2] = color_bytes[0];
            dma_fill_buffer[i * 2 + 1] = color_bytes[1];
        }
        
        // Send full buffer chunks
        uint32_t full_chunks = pixel_count / buffer_pixels;
        for (uint32_t i = 0; i < full_chunks; i++) {
            result = dma_spi_write_buffer(dma_fill_buffer, sizeof(dma_fill_buffer));
            if (result != DISPLAY_OK) break;
            dma_wait_for_finish();
        }
        
        // Send remaining pixels
        if (result == DISPLAY_OK) {
            uint32_t remaining = pixel_count % buffer_pixels;
            if (remaining > 0) {
                result = dma_spi_write_buffer(dma_fill_buffer, remaining * 2);
                dma_wait_for_finish();
            }
        }
    } else {
        // Use blocking SPI for small fills
        for (uint32_t i = 0; i < pixel_count; i++) {
            spi_write_blocking(spi0, color_bytes, 2);
        }
    }
    
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
    dma_wait_for_finish();

    gpio_put(DISPLAY_CS_PIN, 1);
    return result;
}

display_error_t display_draw_char(uint16_t x, uint16_t y, char c, uint16_t color, uint16_t bg_color) {
    if (!display_initialized) return DISPLAY_ERROR_NOT_INITIALIZED;
    if (x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return DISPLAY_ERROR_INVALID_PARAM;
    
    if (c < 32 || c > 90) c = 32; // Space for unsupported chars
    
    const uint8_t *char_data = font5x8[c - 32];
    
    // Draw character bitmap with bounds checking
    for (int col = 0; col < 5 && (x + col) < DISPLAY_WIDTH; col++) {
        uint8_t line = char_data[4 - col]; // Reverse column order
        for (int row = 0; row < 8 && (y + row) < DISPLAY_HEIGHT; row++) {
            uint16_t pixel_color = (line & (1 << row)) ? color : bg_color;
            display_error_t result = display_draw_pixel(x + col, y + row, pixel_color);
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

