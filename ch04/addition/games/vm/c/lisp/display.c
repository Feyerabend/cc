#include "display.h"
#include "hardware/spi.h"
#include "hardware/gpio.h"
#include "hardware/dma.h"
#include "hardware/irq.h"
#include "hardware/sync.h"
#include "pico/time.h"
#include <string.h>
#include <stdio.h>  // For debug prints
#include <stdlib.h>


// Pins (Pimoroni Display Pack 2.0)
#define PIN_CS    17
#define PIN_CLK   18
#define PIN_MOSI  19
#define PIN_DC    16
#define PIN_RST   21
#define PIN_BL    20


#define BTN_A 12
#define BTN_B 13
#define BTN_X 14
#define BTN_Y 15

static const uint8_t button_pins[BUTTON_COUNT] = { BTN_A, BTN_B, BTN_X, BTN_Y };

// State
static struct {
    bool initialized;
    bool dma_enabled;
    int dma_channel;
    volatile bool dma_busy;
    disp_error_context_t last_error;
    disp_config_t config;
    uint16_t *framebuffer;  // Optional framebuffer for smooth rendering
} g = {0};


static button_callback_t button_cb[BUTTON_COUNT] = {0};
static volatile bool btn_current[BUTTON_COUNT] = {0};      // Current debounced state
static volatile bool btn_last[BUTTON_COUNT] = {0};         // Previous debounced state
static volatile bool btn_pressed[BUTTON_COUNT] = {0};      // Edge: just pressed
static volatile bool btn_released[BUTTON_COUNT] = {0};     // Edge: just released
static volatile uint32_t btn_last_change[BUTTON_COUNT] = {0};  // Time of last change
static bool buttons_ready = false;

#define DEBOUNCE_MS 50  // 50ms debounce time

// Full 5Ã—8 font (ASCII 32-127)
static const uint8_t FONT_5X8[][5] = {
    {0x00,0x00,0x00,0x00,0x00},{0x00,0x00,0x5F,0x00,0x00},{0x00,0x07,0x00,0x07,0x00},{0x14,0x7F,0x14,0x7F,0x14},
    {0x24,0x2A,0x7F,0x2A,0x12},{0x23,0x13,0x08,0x64,0x62},{0x36,0x49,0x55,0x22,0x50},{0x00,0x05,0x03,0x00,0x00},
    {0x00,0x1C,0x22,0x41,0x00},{0x00,0x41,0x22,0x1C,0x00},{0x08,0x2A,0x1C,0x2A,0x08},{0x08,0x08,0x3E,0x08,0x08},
    {0x00,0x50,0x30,0x00,0x00},{0x08,0x08,0x08,0x08,0x08},{0x00,0x60,0x60,0x00,0x00},{0x20,0x10,0x08,0x04,0x02},
    {0x3E,0x51,0x49,0x45,0x3E},{0x00,0x42,0x7F,0x40,0x00},{0x42,0x61,0x51,0x49,0x46},{0x21,0x41,0x45,0x4B,0x31},
    {0x18,0x14,0x12,0x7F,0x10},{0x27,0x45,0x45,0x45,0x39},{0x3C,0x4A,0x49,0x49,0x30},{0x01,0x71,0x09,0x05,0x03},
    {0x36,0x49,0x49,0x49,0x36},{0x06,0x49,0x49,0x29,0x1E},{0x00,0x36,0x36,0x00,0x00},{0x00,0x56,0x36,0x00,0x00},
    {0x00,0x08,0x14,0x22,0x41},{0x14,0x14,0x14,0x14,0x14},{0x41,0x22,0x14,0x08,0x00},{0x02,0x01,0x51,0x09,0x06},
    {0x32,0x49,0x79,0x41,0x3E},{0x7E,0x11,0x11,0x11,0x7E},{0x7F,0x49,0x49,0x49,0x36},{0x3E,0x41,0x41,0x41,0x22},
    {0x7F,0x41,0x41,0x22,0x1C},{0x7F,0x49,0x49,0x49,0x41},{0x7F,0x09,0x09,0x01,0x01},{0x3E,0x41,0x41,0x51,0x32},
    {0x7F,0x08,0x08,0x08,0x7F},{0x00,0x41,0x7F,0x41,0x00},{0x20,0x40,0x41,0x3F,0x01},{0x7F,0x08,0x14,0x22,0x41},
    {0x7F,0x40,0x40,0x40,0x40},{0x7F,0x02,0x04,0x02,0x7F},{0x7F,0x04,0x08,0x10,0x7F},{0x3E,0x41,0x41,0x41,0x3E},
    {0x7F,0x09,0x09,0x09,0x06},{0x3E,0x41,0x51,0x21,0x5E},{0x7F,0x09,0x19,0x29,0x46},{0x46,0x49,0x49,0x49,0x31},
    {0x01,0x01,0x7F,0x01,0x01},{0x3F,0x40,0x40,0x40,0x3F},{0x1F,0x20,0x40,0x20,0x1F},{0x7F,0x20,0x18,0x20,0x7F},
    {0x63,0x14,0x08,0x14,0x63},{0x03,0x04,0x78,0x04,0x03},{0x61,0x51,0x49,0x45,0x43},{0x00,0x00,0x7F,0x41,0x41},
    {0x02,0x04,0x08,0x10,0x20},{0x41,0x41,0x7F,0x00,0x00},{0x04,0x02,0x01,0x02,0x04},{0x40,0x40,0x40,0x40,0x40},
    {0x00,0x01,0x02,0x04,0x00},{0x20,0x54,0x54,0x54,0x78},{0x7F,0x48,0x44,0x44,0x38},{0x38,0x44,0x44,0x44,0x20},
    {0x38,0x44,0x44,0x48,0x7F},{0x38,0x54,0x54,0x54,0x18},{0x08,0x7E,0x09,0x01,0x02},{0x08,0x14,0x54,0x54,0x3C},
    {0x7F,0x08,0x04,0x04,0x78},{0x00,0x44,0x7D,0x40,0x00},{0x20,0x40,0x44,0x3D,0x00},{0x00,0x7F,0x10,0x28,0x44},
    {0x00,0x41,0x7F,0x40,0x00},{0x7C,0x04,0x18,0x04,0x78},{0x7C,0x08,0x04,0x04,0x78},{0x38,0x44,0x44,0x44,0x38},
    {0x7C,0x14,0x14,0x14,0x08},{0x08,0x14,0x14,0x18,0x7C},{0x7C,0x08,0x04,0x04,0x08},{0x48,0x54,0x54,0x54,0x20},
    {0x04,0x3F,0x44,0x40,0x20},{0x3C,0x40,0x40,0x20,0x7C},{0x1C,0x20,0x40,0x20,0x1C},{0x3C,0x40,0x30,0x40,0x3C},
    {0x44,0x28,0x10,0x28,0x44},{0x0C,0x50,0x50,0x50,0x3C},{0x44,0x64,0x54,0x4C,0x44},{0x00,0x08,0x36,0x41,0x00},
    {0x00,0x00,0x7F,0x00,0x00},{0x00,0x41,0x36,0x08,0x00},{0x08,0x08,0x2A,0x1C,0x08},{0x08,0x1C,0x2A,0x08,0x08}
};

static const char* err_str[] = {
    "OK","Already init","Not init","SPI fail","GPIO fail","Reset fail","Config fail",
    "NULL ptr","Bad coords","Bad dims","DMA unavailable","DMA config","DMA timeout",
    "Cmd failed","Data failed","Unknown"
};

void disp_set_error_context(disp_error_t code, const char *f, int l, const char *m) {
    g.last_error.code = code; g.last_error.function = f;
    g.last_error.line = l; g.last_error.message = m;
}

const char* disp_error_string(disp_error_t e) {
    if (e >= sizeof(err_str)/sizeof(err_str[0])) return "???";
    return err_str[e];
}

disp_error_context_t disp_get_last_error(void) { return g.last_error; }
void disp_clear_error(void) { g.last_error.code = DISP_OK; }

static void __isr dma_irq(void) {
    if (g.dma_channel >= 0 && (dma_hw->ints0 & (1u << g.dma_channel))) {
        dma_hw->ints0 = 1u << g.dma_channel;
        g.dma_busy = false;
    }
}

static disp_error_t dma_init(void) {
    if (g.dma_enabled) return DISP_OK;
    g.dma_channel = dma_claim_unused_channel(false);
    if (g.dma_channel < 0) {
        printf("DEBUG: No DMA channel available\n");
        return DISP_ERROR(DISP_ERR_DMA_NOT_AVAILABLE, "no channel");
    }
    dma_channel_set_irq0_enabled(g.dma_channel, true);
    irq_set_exclusive_handler(DMA_IRQ_0, dma_irq);
    irq_set_enabled(DMA_IRQ_0, true);
    g.dma_enabled = true;
    printf("DEBUG: DMA channel %d initialized\n", g.dma_channel);
    return DISP_OK;
}

static void dma_deinit(void) {
    if (g.dma_enabled) {
        if (g.dma_channel >= 0) {
            dma_channel_set_irq0_enabled(g.dma_channel, false);
            dma_channel_unclaim(g.dma_channel);
        }
        irq_set_enabled(DMA_IRQ_0, false);
        g.dma_enabled = false; g.dma_channel = -1;
    }
}

static disp_error_t wait_dma(uint32_t ms) {
    uint32_t start = to_ms_since_boot(get_absolute_time());
    while (g.dma_busy) {
        if (to_ms_since_boot(get_absolute_time()) - start > ms) {
            dma_channel_abort(g.dma_channel);
            g.dma_busy = false;
            return DISP_ERROR(DISP_ERR_DMA_TIMEOUT, "timeout");
        }
        tight_loop_contents();
    }
    return DISP_OK;
}

static disp_error_t write_cmd(uint8_t cmd) {
    wait_dma(1000);
    gpio_put(PIN_DC, 0); 
    gpio_put(PIN_CS, 0);
    spi_write_blocking(spi0, &cmd, 1);
    gpio_put(PIN_CS, 1);
    return DISP_OK;
}

static disp_error_t write_data(const uint8_t *data, size_t len) {
    if (!data || len == 0) return DISP_ERROR(DISP_ERR_NULL_POINTER, "bad data");
    wait_dma(1000);
    gpio_put(PIN_DC, 1); 
    gpio_put(PIN_CS, 0);
    
    if (g.dma_enabled && len > 64) {
        g.dma_busy = true;
        dma_channel_config c = dma_channel_get_default_config(g.dma_channel);
        channel_config_set_transfer_data_size(&c, DMA_SIZE_8);
        channel_config_set_dreq(&c, spi_get_dreq(spi0, true));
        channel_config_set_read_increment(&c, true);
        channel_config_set_write_increment(&c, false);
        dma_channel_configure(g.dma_channel, &c, &spi_get_hw(spi0)->dr, data, len, true);
        wait_dma(1000);
    } else {
        spi_write_blocking(spi0, data, len);
    }
    gpio_put(PIN_CS, 1);
    return DISP_OK;
}

static disp_error_t set_window(uint16_t x0, uint16_t y0, uint16_t x1, uint16_t y1) {
    uint8_t buf[4];
    write_cmd(0x2A); // CASET
    buf[0] = x0 >> 8; buf[1] = x0 & 0xFF; buf[2] = x1 >> 8; buf[3] = x1 & 0xFF;
    write_data(buf, 4);
    write_cmd(0x2B); // RASET
    buf[0] = y0 >> 8; buf[1] = y0 & 0xFF; buf[2] = y1 >> 8; buf[3] = y1 & 0xFF;
    write_data(buf, 4);
    return write_cmd(0x2C); // RAMWR
}

static disp_error_t lcd_init_sequence(void) {
    disp_error_t e;
    printf("DEBUG: Starting LCD init sequence\n");
    
    if ((e = write_cmd(0x01)) != DISP_OK) return e; 
    sleep_ms(150); 
    printf("DEBUG: Software reset done\n");
    
    if ((e = write_cmd(0x11)) != DISP_OK) return e; 
    sleep_ms(255);  // Increased delay - some displays need this
    printf("DEBUG: Sleep out done\n");
    
    // Pixel format - 16-bit RGB565
    if ((e = write_cmd(0x3A)) != DISP_OK) return e;
    if ((e = write_data((uint8_t[]){0x55}, 1)) != DISP_OK) return e;
    printf("DEBUG: Pixel format set\n");
    
    // Memory access control - try different rotation values
    if ((e = write_cmd(0x36)) != DISP_OK) return e;
    if ((e = write_data((uint8_t[]){0x70}, 1)) != DISP_OK) return e;  // Try 0x70 instead of 0x60
    printf("DEBUG: MADCTL set\n");
    
    if ((e = write_cmd(0x21)) != DISP_OK) return e; 
    printf("DEBUG: Inversion on\n");
    
    if ((e = write_cmd(0x13)) != DISP_OK) return e; 
    printf("DEBUG: Normal display mode\n");
    
    if ((e = write_cmd(0x29)) != DISP_OK) return e; 
    sleep_ms(100);
    printf("DEBUG: Display on\n");
    
    return DISP_OK;
}

disp_config_t disp_get_default_config(void) {
    return (disp_config_t){
        .spi_baudrate = 62500000,  // Max speed for smooth updates
        .use_dma = true,           // Enable DMA for performance
        .dma_timeout_ms = 1000,
        .enable_backlight = true
    };
}

disp_error_t disp_init(const disp_config_t *cfg) {
    if (g.initialized) return DISP_ERROR(DISP_ERR_ALREADY_INIT, "already init");
    g.config = cfg ? *cfg : disp_get_default_config();

    printf("DEBUG: Init SPI at %lu Hz\n", (unsigned long)g.config.spi_baudrate);
    spi_init(spi0, g.config.spi_baudrate);
    
    // Set SPI format - Mode 0 (CPOL=0, CPHA=0)
    spi_set_format(spi0, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    
    gpio_set_function(PIN_CLK, GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);

    gpio_init(PIN_CS); gpio_set_dir(PIN_CS, GPIO_OUT); gpio_put(PIN_CS, 1);
    gpio_init(PIN_DC); gpio_set_dir(PIN_DC, GPIO_OUT);
    gpio_init(PIN_RST); gpio_set_dir(PIN_RST, GPIO_OUT); gpio_put(PIN_RST, 1);
    gpio_init(PIN_BL); gpio_set_dir(PIN_BL, GPIO_OUT); gpio_put(PIN_BL, 0);  // Start off

    printf("DEBUG: Hardware reset\n");
    gpio_put(PIN_RST, 0); 
    sleep_ms(20);  // Increased delay
    gpio_put(PIN_RST, 1); 
    sleep_ms(150);  // Increased delay

    disp_error_t e = lcd_init_sequence();
    if (e != DISP_OK) {
        printf("DEBUG: LCD init sequence failed: %s\n", disp_error_string(e));
        return e;
    }

    if (g.config.use_dma) {
        if (dma_init() != DISP_OK) {
            printf("DEBUG: DMA init failed, continuing without DMA\n");
            g.config.use_dma = false;
        }
    }
    
    if (g.config.enable_backlight) {
        printf("DEBUG: Enabling backlight\n");
        gpio_put(PIN_BL, 1);
    }

    g.initialized = true;
    printf("DEBUG: Display init successfully\n");
    return DISP_OK;
}

disp_error_t disp_deinit(void) {
    if (!g.initialized) return DISP_ERROR(DISP_ERR_NOT_INIT, "not init");
    gpio_put(PIN_BL, 0);
    disp_framebuffer_free();  // Clean up framebuffer if allocated
    dma_deinit();
    spi_deinit(spi0);
    g.initialized = false;
    return DISP_OK;
}

bool disp_is_initialized(void) { return g.initialized; }

disp_error_t disp_clear(uint16_t color) {
    printf("DEBUG: Clearing screen to color 0x%04X\n", color);
    return disp_fill_rect(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT, color);
}

disp_error_t disp_fill_rect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint16_t color) {
    if (!g.initialized) return DISP_ERROR(DISP_ERR_NOT_INIT, "not init");
    if (x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return DISP_ERROR(DISP_ERR_INVALID_COORDS, "bad pos");
    if (x + w > DISPLAY_WIDTH)  w = DISPLAY_WIDTH  - x;
    if (y + h > DISPLAY_HEIGHT) h = DISPLAY_HEIGHT - y;
    if (w == 0 || h == 0) return DISP_OK;

    set_window(x, y, x + w - 1, y + h - 1);
    uint8_t buf[2] = {color >> 8, color & 0xFF};
    uint32_t pixels = (uint32_t)w * h;

    gpio_put(PIN_DC, 1); 
    gpio_put(PIN_CS, 0);
    
    if (g.dma_enabled && pixels > 32) {
        // Build a 512-byte block (256 pixels) for efficient DMA
        static uint8_t block[512];
        for (int i = 0; i < 256; i++) {
            block[i*2] = buf[0];
            block[i*2+1] = buf[1];
        }
        
        // Send 256-pixel chunks via DMA
        while (pixels >= 256) {
            g.dma_busy = true;
            dma_channel_config c = dma_channel_get_default_config(g.dma_channel);
            channel_config_set_transfer_data_size(&c, DMA_SIZE_8);
            channel_config_set_dreq(&c, spi_get_dreq(spi0, true));
            channel_config_set_read_increment(&c, true);
            channel_config_set_write_increment(&c, false);
            dma_channel_configure(g.dma_channel, &c, &spi_get_hw(spi0)->dr, block, 512, true);
            wait_dma(1000);
            pixels -= 256;
        }
        
        // Handle remainder with blocking write
        if (pixels > 0) {
            spi_write_blocking(spi0, block, pixels * 2);
        }
    } else {
        // Small fills - use blocking
        for (uint32_t i = 0; i < pixels; i++) {
            spi_write_blocking(spi0, buf, 2);
        }
    }
    
    gpio_put(PIN_CS, 1);
    return DISP_OK;
}

disp_error_t disp_draw_pixel(uint16_t x, uint16_t y, uint16_t color) {
    return disp_fill_rect(x, y, 1, 1, color);
}

disp_error_t disp_blit(uint16_t x, uint16_t y, uint16_t w, uint16_t h, const uint16_t *pixels) {
    if (!g.initialized) return DISP_ERROR(DISP_ERR_NOT_INIT, "not init");
    if (!pixels) return DISP_ERROR(DISP_ERR_NULL_POINTER, "null");
    if (x + w > DISPLAY_WIDTH || y + h > DISPLAY_HEIGHT) return DISP_ERROR(DISP_ERR_INVALID_COORDS, "bad size");
    set_window(x, y, x + w - 1, y + h - 1);
    return write_data((const uint8_t*)pixels, w * h * 2);
}

disp_error_t disp_draw_char(uint16_t x, uint16_t y, char c, uint16_t fg, uint16_t bg) {
    if (c < 32 || c > 127) c = ' ';
    const uint8_t *glyph = FONT_5X8[c - 32];
    for (int col = 0; col < 5 && x + col < DISPLAY_WIDTH; col++) {
        uint8_t line = glyph[col];
        for (int row = 0; row < 8 && y + row < DISPLAY_HEIGHT; row++) {
            uint16_t colr = (line & (1 << row)) ? fg : bg;
            disp_draw_pixel(x + col, y + row, colr);
        }
    }
    return DISP_OK;
}

disp_error_t disp_draw_text(uint16_t x, uint16_t y, const char *txt, uint16_t fg, uint16_t bg) {
    while (*txt && x < DISPLAY_WIDTH) {
        disp_draw_char(x, y, *txt++, fg, bg);
        x += 6;
    }
    return DISP_OK;
}

disp_error_t disp_set_backlight(bool on) {
    gpio_put(PIN_BL, on);
    return DISP_OK;
}

disp_error_t disp_wait_complete(uint32_t ms) { return wait_dma(ms); }


// Allocate a full-screen framebuffer for double-buffered rendering
// Here Pico 2 or Pico 2W should be enough
disp_error_t disp_framebuffer_alloc(void) {
    if (g.framebuffer) return DISP_OK;  // Already allocated
    
    size_t size = DISPLAY_WIDTH * DISPLAY_HEIGHT * sizeof(uint16_t);
    g.framebuffer = (uint16_t*)malloc(size);
    
    if (!g.framebuffer) {
        printf("DEBUG: Failed to allocate framebuffer (%zu bytes)\n", size);
        return DISP_ERROR(DISP_ERR_NULL_POINTER, "framebuffer alloc failed");
    }
    
    printf("DEBUG: Framebuffer allocated (%zu bytes)\n", size);
    memset(g.framebuffer, 0, size);
    return DISP_OK;
}

void disp_framebuffer_free(void) {
    if (g.framebuffer) {
        free(g.framebuffer);
        g.framebuffer = NULL;
        printf("DEBUG: Framebuffer freed\n");
    }
}

uint16_t* disp_get_framebuffer(void) {
    return g.framebuffer;
}

disp_error_t disp_framebuffer_clear(uint16_t color) {
    if (!g.framebuffer) return DISP_ERROR(DISP_ERR_NULL_POINTER, "no framebuffer");
    
    uint32_t pixels = DISPLAY_WIDTH * DISPLAY_HEIGHT;
    for (uint32_t i = 0; i < pixels; i++) {
        g.framebuffer[i] = color;
    }
    return DISP_OK;
}

void disp_framebuffer_set_pixel(uint16_t x, uint16_t y, uint16_t color) {
    if (!g.framebuffer || x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return;
    g.framebuffer[y * DISPLAY_WIDTH + x] = color;
}

disp_error_t disp_framebuffer_flush(void) {
    if (!g.initialized) return DISP_ERROR(DISP_ERR_NOT_INIT, "not init");
    if (!g.framebuffer) return DISP_ERROR(DISP_ERR_NULL_POINTER, "no framebuffer");
    
    // Send entire framebuffer to display in one operation
    set_window(0, 0, DISPLAY_WIDTH - 1, DISPLAY_HEIGHT - 1);
    
    // Convert to big-endian bytes for display
    size_t total_bytes = DISPLAY_WIDTH * DISPLAY_HEIGHT * 2;
    
    gpio_put(PIN_DC, 1);
    gpio_put(PIN_CS, 0);
    
    if (g.dma_enabled) {
        // Use DMA for maximum speed
        g.dma_busy = true;
        dma_channel_config c = dma_channel_get_default_config(g.dma_channel);
        channel_config_set_transfer_data_size(&c, DMA_SIZE_8);
        channel_config_set_dreq(&c, spi_get_dreq(spi0, true));
        channel_config_set_read_increment(&c, true);
        channel_config_set_write_increment(&c, false);
        dma_channel_configure(g.dma_channel, &c, &spi_get_hw(spi0)->dr, 
                            (uint8_t*)g.framebuffer, total_bytes, true);
        wait_dma(1000);
    } else {
        spi_write_blocking(spi0, (uint8_t*)g.framebuffer, total_bytes);
    }
    
    gpio_put(PIN_CS, 1);
    return DISP_OK;
}

// Framebuffer drawing functions
void disp_framebuffer_fill_rect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint16_t color) {
    if (!g.framebuffer) return;
    
    // Clip to screen bounds
    if (x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return;
    if (x + w > DISPLAY_WIDTH) w = DISPLAY_WIDTH - x;
    if (y + h > DISPLAY_HEIGHT) h = DISPLAY_HEIGHT - y;
    
    for (uint16_t dy = 0; dy < h; dy++) {
        for (uint16_t dx = 0; dx < w; dx++) {
            g.framebuffer[(y + dy) * DISPLAY_WIDTH + (x + dx)] = color;
        }
    }
}

void disp_framebuffer_draw_char(uint16_t x, uint16_t y, char c, uint16_t fg, uint16_t bg) {
    if (!g.framebuffer) return;
    if (c < 32 || c > 127) c = ' ';
    
    const uint8_t *glyph = FONT_5X8[c - 32];
    for (int col = 0; col < 5 && x + col < DISPLAY_WIDTH; col++) {
        uint8_t line = glyph[col];
        for (int row = 0; row < 8 && y + row < DISPLAY_HEIGHT; row++) {
            uint16_t color = (line & (1 << row)) ? fg : bg;
            g.framebuffer[(y + row) * DISPLAY_WIDTH + (x + col)] = color;
        }
    }
}

void disp_framebuffer_draw_text(uint16_t x, uint16_t y, const char *txt, uint16_t fg, uint16_t bg) {
    if (!g.framebuffer || !txt) return;
    
    while (*txt && x < DISPLAY_WIDTH) {
        disp_framebuffer_draw_char(x, y, *txt++, fg, bg);
        x += 6;
    }
}

// Buttons
disp_error_t buttons_init(void) {
    if (buttons_ready) return DISP_OK;

    uint32_t now = to_ms_since_boot(get_absolute_time());
    
    for (int i = 0; i < BUTTON_COUNT; i++) {
        gpio_init(button_pins[i]);
        gpio_set_dir(button_pins[i], GPIO_IN);
        gpio_pull_up(button_pins[i]);
        
        // Read initial state (active low, so invert)
        bool state = !gpio_get(button_pins[i]);
        
        btn_current[i] = state;
        btn_last[i] = state;
        btn_pressed[i] = false;
        btn_released[i] = false;
        btn_last_change[i] = now;
    }
    
    buttons_ready = true;
    printf("DEBUG: Buttons initialised\n");
    return DISP_OK;
}

void buttons_update(void) {
    if (!buttons_ready) return;

    uint32_t now = to_ms_since_boot(get_absolute_time());

    for (int i = 0; i < BUTTON_COUNT; i++) {
        // Read current hardware state (active low)
        bool hw_state = !gpio_get(button_pins[i]);
        
        // Clear edge flags from previous update
        btn_pressed[i] = false;
        btn_released[i] = false;
        
        // Check if hardware state differs from current debounced state
        if (hw_state != btn_current[i]) {
            // Check if enough time has passed since last change
            if (now - btn_last_change[i] >= DEBOUNCE_MS) {
                // Update state
                btn_last[i] = btn_current[i];
                btn_current[i] = hw_state;
                btn_last_change[i] = now;
                
                // Detect edges
                if (btn_current[i] && !btn_last[i]) {
                    // Just pressed
                    btn_pressed[i] = true;
                    printf("DEBUG: Button %d pressed\n", i);
                    
                    // Fire callback
                    if (button_cb[i]) {
                        button_cb[i]((button_t)i);
                    }
                }
                else if (!btn_current[i] && btn_last[i]) {
                    // Just released
                    btn_released[i] = true;
                    printf("DEBUG: Button %d released\n", i);
                }
            }
        } else {
            // State matches - reset debounce timer
            btn_last_change[i] = now;
        }
    }
}

bool button_pressed(button_t b) {
    // Returns true if button is currently held down
    return (b < BUTTON_COUNT) ? btn_current[b] : false;
}

bool button_just_pressed(button_t b) {
    // Returns true for ONE update cycle after press
    return (b < BUTTON_COUNT) ? btn_pressed[b] : false;
}

bool button_just_released(button_t b) {
    // Returns true for ONE update cycle after release
    return (b < BUTTON_COUNT) ? btn_released[b] : false;
}

disp_error_t button_set_callback(button_t b, button_callback_t cb) {
    if (b >= BUTTON_COUNT) return DISP_ERROR(DISP_ERR_INVALID_DIMENSIONS, "invalid button");
    button_cb[b] = cb;
    return DISP_OK;
}
