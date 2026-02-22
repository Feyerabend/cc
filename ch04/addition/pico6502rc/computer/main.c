
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "display.h"
#include "fake6502.h"

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

#define CIA_BUTTONS       0xDC00  // Button state register

#define ROM_START         0x8000
#define VECTOR_RESET      0xFFFC

// Memory
static uint8_t memory[65536];

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

// Framebuffer for off-screen rendering
static uint16_t framebuffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];

// 6502 memory interface
uint8_t read6502(uint16_t address) {
    // Handle special reads
    if (address == CIA_BUTTONS) {
        // Return button state (inverted - pressed = 0)
        uint8_t buttons = 0xFF;
        if (button_pressed(BUTTON_A)) buttons &= ~0x01;
        if (button_pressed(BUTTON_B)) buttons &= ~0x02;
        if (button_pressed(BUTTON_X)) buttons &= ~0x04;
        if (button_pressed(BUTTON_Y)) buttons &= ~0x08;
        return buttons;
    }
    
    return memory[address];
}

void write6502(uint16_t address, uint8_t value) {
    // Handle VIC registers
    if (address >= VIC_BASE && address < VIC_BASE + 0x20) {
        switch (address) {
            case VIC_BORDER_COLOR:
                vic_border_color = value & 0x0F;
                break;
            case VIC_BG_COLOR:
                vic_bg_color = value & 0x0F;
                break;
            // Add more VIC registers as needed
        }
        memory[address] = value;
        return;
    }
    
    // ROM is read-only
    if (address >= ROM_START && address < ROM_START + ROM_DATA_SIZE) {
        return;  // Ignore writes to ROM
    }
    
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
    
    // Render border (simple 8-pixel border)
    uint16_t border_color = c64_colors[vic_border_color];
    
    // Top border
    for (int y = 0; y < 8; y++) {
        for (int x = 0; x < DISPLAY_WIDTH; x++) {
            framebuffer[y * DISPLAY_WIDTH + x] = border_color;
        }
    }
    
    // Bottom border
    for (int y = DISPLAY_HEIGHT - 8; y < DISPLAY_HEIGHT; y++) {
        for (int x = 0; x < DISPLAY_WIDTH; x++) {
            framebuffer[y * DISPLAY_WIDTH + x] = border_color;
        }
    }
    
    // Left border
    for (int x = 0; x < 8; x++) {
        for (int y = 0; y < DISPLAY_HEIGHT; y++) {
            framebuffer[y * DISPLAY_WIDTH + x] = border_color;
        }
    }
    
    // Right border
    for (int x = DISPLAY_WIDTH - 8; x < DISPLAY_WIDTH; x++) {
        for (int y = 0; y < DISPLAY_HEIGHT; y++) {
            framebuffer[y * DISPLAY_WIDTH + x] = border_color;
        }
    }
    
    // Character size (8x8)
    const int char_w = 8;
    const int char_h = 8;
    
    // Render characters (with font padding: left 1, right 2)
    for (int row = 0; row < SCREEN_ROWS; row++) {
        for (int col = 0; col < SCREEN_COLS; col++) {
            int idx = row * SCREEN_COLS + col;
            uint8_t ch = memory[SCREEN_RAM_START + idx];
            uint8_t color_byte = memory[COLOR_RAM_START + idx];
            uint16_t fg_color = c64_colors[color_byte & 0x0F];
            
            // Screen position (with border offset)
            int base_x = 8 + col * char_w;
            int base_y = 8 + row * char_h;
            
            // Skip invalid chars
            if (ch < 32 || ch > 90) continue;
            
            const uint8_t *char_data = font5x8[ch - 32];
            
            // Draw character (5 columns, padded)
            for (int px = 0; px < 5; px++) {
                uint8_t line = char_data[4 - px];  // Reverse as in original
                for (int py = 0; py < 8; py++) {
                    if (line & (1 << py)) {
                        int draw_x = base_x + px + 1;  // Left pad 1
                        int draw_y = base_y + py;
                        // Bounds check
                        if (draw_x >= 0 && draw_x < DISPLAY_WIDTH && draw_y >= 0 && draw_y < DISPLAY_HEIGHT) {
                            framebuffer[draw_y * DISPLAY_WIDTH + draw_x] = fg_color;
                        }
                    }
                }
            }
        }
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
    
    // Init memory
    memset(memory, 0, sizeof(memory));
    
    // Load ROM
    memcpy(memory + ROM_START, rom_data, ROM_DATA_SIZE);
    printf("Loaded %d bytes to ROM at $%04X\n", ROM_DATA_SIZE, ROM_START);
    
    // Set reset vector to point to ROM start
    memory[VECTOR_RESET] = ROM_START & 0xFF;
    memory[VECTOR_RESET + 1] = ROM_START >> 8;
    
    // Init screen RAM with spaces
    for (int i = 0; i < SCREEN_CHARS; i++) {
        memory[SCREEN_RAM_START + i] = ' ';
        memory[COLOR_RAM_START + i] = 0x0E;  // Light blue
    }
    
    // Welcome message
    const char *msg = "6502 EMULATOR - C64 STYLE";
    int msg_len = strlen(msg);
    int start_pos = (SCREEN_COLS - msg_len) / 2 + SCREEN_COLS * (SCREEN_ROWS / 2);  // Center vertically too
    for (int i = 0; i < msg_len; i++) {
        memory[SCREEN_RAM_START + start_pos + i] = msg[i];
        memory[COLOR_RAM_START + start_pos + i] = 0x01;  // White
    }
    
    // Reset 6502
    reset6502();
    printf("6502 reset. PC=$%04X\n", PC);
    
    uint32_t cycle_count = 0;
    uint32_t last_fps_print = to_ms_since_boot(get_absolute_time());
    
    printf("Starting emulation...\n");

    // Launch Core 1 to handle display rendering and button polling
    multicore_launch_core1(core1_entry);

    // Main loop - Core 0 runs the 6502 flat out
    while (1) {
        step6502();
        cycle_count++;

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
