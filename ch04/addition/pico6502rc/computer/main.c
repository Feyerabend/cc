
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "display.h"
#include "fake6502.h"
#include "font.h"

// Include the ROM data
#include "rom.h"

// Memory layout (C64-inspired)
#define SCREEN_RAM_START  0x0400
#define SCREEN_RAM_END    0x07AF
#define SCREEN_CHARS      1200
#define SCREEN_COLS       40
#define SCREEN_ROWS       30

#define COLOR_RAM_START   0xD800
#define COLOR_RAM_END     0xDBAF

#define VIC_BASE          0xD000
#define VIC_BORDER_COLOR  0xD000
#define VIC_BG_COLOR      0xD001

// GFX registers ($D010–$D017) — within the VIC range
#define GFX_X_LO   0xD010   // pixel / line X1 low byte
#define GFX_X_HI   0xD011   // pixel / line X1 high byte
#define GFX_Y      0xD012   // pixel / line Y1 (0–239)
#define GFX_COLOR  0xD013   // color index 0–15
#define GFX_CMD    0xD014   // 1=PLOT 2=CLRGFX 3=LINE 4=RECT (triggers action)
#define GFX_X2_LO  0xD015   // line X2 / rect width  low
#define GFX_X2_HI  0xD016   // line X2 / rect width  high
#define GFX_Y2     0xD017   // line Y2 / rect height

#define CIA_BUTTONS       0xDC00  // Button state register

#define ROM_START         0x8000
#define VECTOR_RESET      0xFFFC

// Memory: only lower 32 KB (0x0000–0x7FFF) lives in RAM.
// ROM (0x8000+) is read directly from rom_data[] in flash.
// Color RAM (0xD800–0xDBAF) lives in its own compact buffer.
static uint8_t memory[0x8000];           // 32 KB user RAM
static uint8_t color_ram[SCREEN_CHARS];  // 1200 bytes for color cells

// VIC registers (volatile: written by Core 0, read by Core 1)
static volatile uint8_t vic_border_color = 0x06;  // Blue
static volatile uint8_t vic_bg_color = 0x0E;      // Light blue

// C64 color palette (RGB565)
static const uint16_t c64_colors[16] = {
    0x0000,  // 0: Black
    0xFFFF,  // 1: White
    0xF800,  // 2: Red
    0x07FF,  // 3: Cyan
    0xF81F,  // 4: Purple
    0x07E0,  // 5: Green
    0x001F,  // 6: Blue
    0xFFE0,  // 7: Yellow
    0xFD20,  // 8: Orange
    0x8410,  // 9: Brown
    0xFC10,  // A: Light red
    0x4208,  // B: Dark grey
    0x8410,  // C: Grey
    0x87F0,  // D: Light green
    0x841F,  // E: Light blue
    0xC618,  // F: Light grey
};

// Copied and adapted font from display.c
// (5x8 font, will pad to 8x8 in rendering)
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

// Pixel layer: nibble-packed, 2 pixels per byte.
// Even pixel i: low nibble  of pixel_layer[i>>1]
// Odd  pixel i: high nibble of pixel_layer[i>>1]
// 0 = transparent, 1–15 = C64 colour index.
// Persistent — only cleared by GFX_CMD=2 (CLRGFX).
#define PIXEL_LAYER_BYTES ((DISPLAY_WIDTH * DISPLAY_HEIGHT + 1) / 2)
static uint8_t pixel_layer[PIXEL_LAYER_BYTES];

// Shadow of GFX registers $D010–$D017 (index = address - $D010)
static uint8_t gfx_regs[8];

// Framebuffer for off-screen rendering
static uint16_t framebuffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];

// ---------------------------------------------------------------------------
// GFX helper functions
// ---------------------------------------------------------------------------

static void gfx_plot(int x, int y, uint8_t color) {
    if (x < 0 || x >= DISPLAY_WIDTH || y < 0 || y >= DISPLAY_HEIGHT) return;
    int i = y * DISPLAY_WIDTH + x;
    color &= 0x0F;
    if (i & 1)
        pixel_layer[i >> 1] = (pixel_layer[i >> 1] & 0x0F) | (color << 4);
    else
        pixel_layer[i >> 1] = (pixel_layer[i >> 1] & 0xF0) | color;
}

static void gfx_line(int x0, int y0, int x1, int y1, uint8_t color) {
    int dx = abs(x1 - x0);
    int dy = abs(y1 - y0);
    int sx = (x0 < x1) ? 1 : -1;
    int sy = (y0 < y1) ? 1 : -1;
    int err = dx - dy;
    while (1) {
        gfx_plot(x0, y0, color);
        if (x0 == x1 && y0 == y1) break;
        int e2 = 2 * err;
        if (e2 > -dy) { err -= dy; x0 += sx; }
        if (e2 <  dx) { err += dx; y0 += sy; }
    }
}

static void gfx_rect(int x, int y, int w, int h, uint8_t color) {
    for (int row = 0; row < h; row++)
        for (int col = 0; col < w; col++)
            gfx_plot(x + col, y + row, color);
}

static void handle_gfx_cmd(uint8_t cmd) {
    int     x     = gfx_regs[0] | (gfx_regs[1] << 8);
    int     y     = gfx_regs[2];
    uint8_t color = gfx_regs[3] & 0x0F;
    int     x2    = gfx_regs[5] | (gfx_regs[6] << 8);
    int     y2    = gfx_regs[7];
    switch (cmd) {
        case 1: gfx_plot(x, y, color); break;
        case 2: memset(pixel_layer, 0, sizeof(pixel_layer)); break;
        case 3: gfx_line(x, y, x2, y2, color); break;
        case 4: gfx_rect(x, y, x2, y2, color); break; // x2=width, y2=height
    }
}

// Button cooldown: once a button fires, it won't re-fire for this many ms.
// Prevents the 6502 tight loop from triggering the same action hundreds of
// times per frame while a button is held.
#define BUTTON_COOLDOWN_MS 200
static uint32_t btn_cooldown_until[4] = {0, 0, 0, 0};

// 6502 memory interface
uint8_t read6502(uint16_t address) {
    // Lower 32 KB lives in RAM
    if (address < 0x8000)
        return memory[address];

    // ROM (0x8000–0x8000+ROM_DATA_SIZE-1): read directly from flash
    if (address < ROM_START + ROM_DATA_SIZE)
        return rom_data[address - ROM_START];

    // CIA buttons at $DC00 — check BEFORE color RAM: $DC00 falls inside
    // the color RAM window $D800–$DCAF and would be misread otherwise.
    // Cooldown: a button that has fired won't re-fire for BUTTON_COOLDOWN_MS.
    // This prevents the 2MHz 6502 loop from triggering hundreds of times
    // while a button is physically held.
    if (address == CIA_BUTTONS) {
        uint8_t buttons = 0xFF;
        uint32_t now = to_ms_since_boot(get_absolute_time());
        for (int i = 0; i < 4; i++) {
            bool pressed = button_pressed((button_t)i);
            if (!pressed) {
                btn_cooldown_until[i] = 0;  // reset cooldown on release
            } else if (now >= btn_cooldown_until[i]) {
                buttons &= ~(1u << i);      // report as pressed
                btn_cooldown_until[i] = now + BUTTON_COOLDOWN_MS;
            }
            // else: still in cooldown — report as not pressed (0xFF bit stays)
        }
        return buttons;
    }

    // Color RAM (0xD800–0xDCAF)
    if (address >= COLOR_RAM_START && address < COLOR_RAM_START + SCREEN_CHARS)
        return color_ram[address - COLOR_RAM_START];

    // Reset vector: always point to ROM_START
    if (address == VECTOR_RESET)     return (uint8_t)(ROM_START & 0xFF);
    if (address == VECTOR_RESET + 1) return (uint8_t)(ROM_START >> 8);

    return 0;
}

void write6502(uint16_t address, uint8_t value) {
    // VIC and GFX registers (0xD000–0xD01F)
    if (address >= VIC_BASE && address < VIC_BASE + 0x20) {
        switch (address) {
            case VIC_BORDER_COLOR:
                vic_border_color = value & 0x0F;
                break;
            case VIC_BG_COLOR:
                vic_bg_color = value & 0x0F;
                break;
            // GFX registers
            case GFX_X_LO: case GFX_X_HI: case GFX_Y:    case GFX_COLOR:
            case GFX_CMD:  case GFX_X2_LO: case GFX_X2_HI: case GFX_Y2:
                gfx_regs[address - GFX_X_LO] = value;
                if (address == GFX_CMD) handle_gfx_cmd(value);
                break;
        }
        // VIC/GFX registers are above 0x8000; don't touch memory[]
        return;
    }

    // Color RAM (0xD800–0xDCAF), but not the CIA buttons register at $DC00
    if (address >= COLOR_RAM_START && address < COLOR_RAM_START + SCREEN_CHARS
            && address != CIA_BUTTONS) {
        color_ram[address - COLOR_RAM_START] = value;
        return;
    }

    // ROM and all other high addresses are read-only / unmapped
    if (address >= 0x8000) return;

    memory[address] = value;
}

// Render the character screen to framebuffer, then blit
void render_screen(void) {
    static uint32_t last_render = 0;
    uint32_t now = to_ms_since_boot(get_absolute_time());
    
    // Limit to ~30 FPS to avoid over-rendering
    if (now - last_render < 33) return;
    last_render = now;
    
    // Clear framebuffer to background color
    uint16_t bg_color = c64_colors[vic_bg_color];
    for (int i = 0; i < DISPLAY_WIDTH * DISPLAY_HEIGHT; i++) {
        framebuffer[i] = bg_color;
    }
    
    // Composite pixel layer (behind characters, on top of background)
    // Pixel layer is nibble-packed: even index = low nibble, odd = high nibble
    for (int i = 0; i < DISPLAY_WIDTH * DISPLAY_HEIGHT; i++) {
        uint8_t nibble = (i & 1) ? (pixel_layer[i >> 1] >> 4)
                                  : (pixel_layer[i >> 1] & 0x0F);
        if (nibble != 0) framebuffer[i] = c64_colors[nibble];
    }

    // Character size (8x8)
    const int char_w = 8;
    const int char_h = 8;

    // Render characters
    for (int row = 0; row < SCREEN_ROWS; row++) {
        for (int col = 0; col < SCREEN_COLS; col++) {
            int idx = row * SCREEN_COLS + col;
            uint8_t ch = memory[SCREEN_RAM_START + idx];
            uint8_t color_byte = color_ram[idx];
            uint16_t fg_color = c64_colors[color_byte & 0x0F];

            // Screen position (with border offset)
            int base_x = 8 + col * char_w;
            int base_y = 8 + row * char_h;

            if (ch >= 32 && ch <= 90) {
                // Text character: 5×8 font with 1px left pad
                const uint8_t *char_data = font5x8[ch - 32];
                for (int px = 0; px < 5; px++) {
                    uint8_t line = char_data[4 - px];  // reverse as in original
                    for (int py = 0; py < 8; py++) {
                        if (line & (1 << py)) {
                            int draw_x = base_x + px + 1;  // left pad 1
                            int draw_y = base_y + py;
                            if (draw_x >= 0 && draw_x < DISPLAY_WIDTH &&
                                draw_y >= 0 && draw_y < DISPLAY_HEIGHT) {
                                framebuffer[draw_y * DISPLAY_WIDTH + draw_x] = fg_color;
                            }
                        }
                    }
                }
            } else if (ch >= 128 && ch <= 143) {
                // Block character: 8×8, no padding, MSB = leftmost pixel
                for (int py = 0; py < 8; py++) {
                    uint8_t row_bits = font_block[ch - 128][py];
                    for (int px = 0; px < 8; px++) {
                        if (row_bits & (0x80 >> px)) {
                            int draw_x = base_x + px;
                            int draw_y = base_y + py;
                            if (draw_x >= 0 && draw_x < DISPLAY_WIDTH &&
                                draw_y >= 0 && draw_y < DISPLAY_HEIGHT) {
                                framebuffer[draw_y * DISPLAY_WIDTH + draw_x] = fg_color;
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Render border last so it always appears on top of characters and pixels.
    // This prevents block chars near the edge from visually overflowing.
    uint16_t border_color = c64_colors[vic_border_color];
    for (int x = 0; x < DISPLAY_WIDTH; x++) {
        for (int y = 0; y < 8; y++)
            framebuffer[y * DISPLAY_WIDTH + x] = border_color;
        for (int y = DISPLAY_HEIGHT - 8; y < DISPLAY_HEIGHT; y++)
            framebuffer[y * DISPLAY_WIDTH + x] = border_color;
    }
    for (int y = 8; y < DISPLAY_HEIGHT - 8; y++) {
        for (int x = 0; x < 8; x++)
            framebuffer[y * DISPLAY_WIDTH + x] = border_color;
        for (int x = DISPLAY_WIDTH - 8; x < DISPLAY_WIDTH; x++)
            framebuffer[y * DISPLAY_WIDTH + x] = border_color;
    }

    // Blit the framebuffer to display
    display_blit_full(framebuffer);
}


// Core 1: handles display rendering and button polling
void core1_entry(void) {
    while (1) {
        buttons_update();
        render_screen();
    }
}

int main() {
    // Init stdio
    stdio_init_all();
    sleep_ms(1000);  // Wait for USB serial
    
    printf("\n=== 6502 Emulator - C64 Style ===\n");
    
    // Init display
    display_error_t err = display_pack_init();
    if (err != DISPLAY_OK) {
        printf("Display init failed: %s\n", display_error_string(err));
        while(1) tight_loop_contents();
    }
    
    // Init buttons
    err = buttons_init();
    if (err != DISPLAY_OK) {
        printf("Button init failed: %s\n", display_error_string(err));
    }
    
    printf("Display initialized: %dx%d\n", DISPLAY_WIDTH, DISPLAY_HEIGHT);
    
    // Init memory (lower 32 KB)
    memset(memory, 0, sizeof(memory));
    memset(color_ram, 0x0E, sizeof(color_ram));  // Light blue for all cells

    // ROM lives in flash (rom_data[]); no copy needed.
    // Reset vector is returned by read6502 directly.
    printf("ROM at $%04X, %d bytes (in flash)\n", ROM_START, ROM_DATA_SIZE);

    // Init screen RAM with spaces
    for (int i = 0; i < SCREEN_CHARS; i++) {
        memory[SCREEN_RAM_START + i] = ' ';
    }
    
    // Welcome message
    const char *msg = "6502 EMULATOR - C64 STYLE";
    int msg_len = strlen(msg);
    int start_pos = (SCREEN_COLS - msg_len) / 2 + SCREEN_COLS * (SCREEN_ROWS / 2);  // Center vertically too
    for (int i = 0; i < msg_len; i++) {
        memory[SCREEN_RAM_START + start_pos + i] = msg[i];
        color_ram[start_pos + i] = 0x01;  // White
    }
    
    // Reset 6502
    reset6502();
    printf("6502 reset. PC=$%04X\n", PC);
    
    uint32_t cycle_count = 0;
    uint32_t last_fps_print = to_ms_since_boot(get_absolute_time());
    
    printf("Starting emulation...\n");

    // Launch Core 1 to handle display rendering and button polling
    multicore_launch_core1(core1_entry);

    // Main loop - Core 0 runs the 6502 at ~1MHz using time-based pacing
    // This ensures ROM software delay loops and timing-dependent code behave correctly.
    // Core 1 handles display independently, so pacing here doesn't affect frame rate.
    while (1) {
        uint32_t batch_start = time_us_32();

        // Run 2000 cycles per ms = ~2MHz
        for (int i = 0; i < 2000; i++) {
            step6502();
            cycle_count++;
        }

        // Busy-wait out the remainder of 1ms
        while (time_us_32() - batch_start < 1000) {
            tight_loop_contents();
        }

        // Print stats every 5 seconds
        uint32_t now = to_ms_since_boot(get_absolute_time());
        if (now - last_fps_print > 5000) {
            printf("Cycles: %lu, PC=$%04X, A=$%02X, X=$%02X, Y=$%02X\n",
                   cycle_count, PC, A, X, Y);
            last_fps_print = now;
        }
    }
    
    return 0;
}
