/*
 * main.c – PICO 6502 Retro Computer Emulator
 *
 * Uses the improved display.h framebuffer API throughout:
 *   - fb_clear / fb_fill_rect  for screen layout
 *   - fb_draw_string / fb_draw_char  for text (full ASCII, extended font)
 *   - fb_apply_color_transform_rect  for the animated colour-bar effect
 *   - display_blit_full  for a single tear-free DMA push each frame
 *
 * No local font tables or pixel-writing loops – everything goes through
 * display.h so there is one canonical implementation.
 */

#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "display.h"
#include "fake6502.h"
#include "rom.h"

// ---------------------------------------------------------------------------
// Memory map (C64-inspired)
// ---------------------------------------------------------------------------
#define SCREEN_RAM_START  0x0400
#define SCREEN_COLS       40
#define SCREEN_ROWS       30
#define SCREEN_CHARS      (SCREEN_COLS * SCREEN_ROWS)   // 1200

#define COLOR_RAM_START   0xD800

#define VIC_BASE          0xD000
#define VIC_BORDER_COLOR  0xD000   // $D000 – border colour index (nibble)
#define VIC_BG_COLOR      0xD001   // $D001 – background colour index (nibble)

#define CIA_BUTTONS       0xDC00   // Button state (bit clear = pressed)

#define ROM_START         0x8000
#define VECTOR_RESET      0xFFFC

// ---------------------------------------------------------------------------
// C64 colour palette (RGB565).  Index 0-15 matches the standard C64 palette.
// ---------------------------------------------------------------------------
static const uint16_t c64_colors[16] = {
    0x0000,  // 0  Black
    0xFFFF,  // 1  White
    0xF800,  // 2  Red
    0x07FF,  // 3  Cyan
    0xF81F,  // 4  Purple
    0x07E0,  // 5  Green
    0x001F,  // 6  Blue
    0xFFE0,  // 7  Yellow
    0xFD20,  // 8  Orange
    0x8410,  // 9  Brown
    0xFC10,  // A  Light red
    0x4208,  // B  Dark grey
    0x8410,  // C  Grey
    0x87F0,  // D  Light green
    0x841F,  // E  Light blue
    0xC618,  // F  Light grey
};

// ---------------------------------------------------------------------------
// Global state
// ---------------------------------------------------------------------------
static uint8_t  memory[65536];
static uint16_t framebuffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];

// VIC shadow registers (written by 6502 ROM)
static uint8_t vic_border_color = 0x06;   // Blue
static uint8_t vic_bg_color     = 0x0E;   // Light blue

// Standard C64-style layout: 40 cols × 30 rows, 8px border.
// The border is purely visual — text starts at pixel (BORDER, BORDER).
// Col 38/39 and row 28/29 extend past the display edge but the ROM never
// writes content there, so nothing is lost.
#define CHAR_W      8
#define CHAR_H      8
#define BORDER      8
#define SCREEN_COLS 40
#define SCREEN_ROWS 30

// ---------------------------------------------------------------------------
// 6502 memory interface
// ---------------------------------------------------------------------------
uint8_t read6502(uint16_t address) {
    if (address == CIA_BUTTONS) {
        uint8_t b = 0xFF;
        if (button_pressed(BUTTON_A)) b &= ~0x01;
        if (button_pressed(BUTTON_B)) b &= ~0x02;
        if (button_pressed(BUTTON_X)) b &= ~0x04;
        if (button_pressed(BUTTON_Y)) b &= ~0x08;
        return b;
    }
    return memory[address];
}

void write6502(uint16_t address, uint8_t value) {
    // VIC registers
    if (address >= VIC_BASE && address < VIC_BASE + 0x40) {
        switch (address) {
            case VIC_BORDER_COLOR: vic_border_color = value & 0x0F; break;
            case VIC_BG_COLOR:     vic_bg_color     = value & 0x0F; break;
        }
        memory[address] = value;
        return;
    }
    // ROM is read-only
    if (address >= ROM_START && address < (uint16_t)(ROM_START + ROM_DATA_SIZE))
        return;

    memory[address] = value;
}

// ---------------------------------------------------------------------------
// render_screen()
//
// Called once per frame.  Builds the entire scene into `framebuffer` then
// does a single display_blit_full() DMA push.
//
// Layout used by the ROM:
//   $0400–$07E7  screen RAM  (40×30 = 1200 chars, PETSCII)
//   $D800–$DBAF  colour RAM  (one nibble per cell, C64 palette index)
//   $D000        border colour
//   $D001        background colour
//   $05E0        animated colour-bar row   (char code, written each frame)
//   $D9E0        colour-bar colour index
// ---------------------------------------------------------------------------
static void render_screen(void) {
    uint16_t bg  = c64_colors[vic_bg_color];
    uint16_t brd = c64_colors[vic_border_color];

    // 1. Border colour fills everything, then bg overwrites the inner text area.
    fb_clear(framebuffer, brd);
    fb_fill_rect(framebuffer,
                 BORDER, BORDER,
                 DISPLAY_WIDTH  - 2 * BORDER,
                 DISPLAY_HEIGHT - 2 * BORDER,
                 bg);

    // 2. Characters – full 40×30 ROM layout, offset by BORDER pixels.
    //    Cols 38/39 draw past the right edge and are clipped by fb_draw_char.
    //    Row 29 draws past the bottom edge and is clipped similarly.
    //    The ROM never writes content there so nothing visible is lost.
    for (int row = 0; row < SCREEN_ROWS; row++) {
        for (int col = 0; col < SCREEN_COLS; col++) {
            int     idx = row * SCREEN_COLS + col;
            uint8_t ch  = memory[SCREEN_RAM_START + idx];
            uint8_t ci  = memory[COLOR_RAM_START  + idx] & 0x0F;
            if (ch > 0x20 && ch <= 0x7A)
                fb_draw_char(framebuffer,
                             BORDER + col * CHAR_W,
                             BORDER + row * CHAR_H,
                             (char)ch, c64_colors[ci], bg);
        }
    }

    // 3. Status bar – sits in the bottom border strip (y = DISPLAY_HEIGHT-CHAR_H).
    //    Drawn directly into the framebuffer, always navy/white regardless of
    //    the current border or background colour.
    {
        char status[41];
        snprintf(status, sizeof(status),
                 "PC:%04X A:%02X X:%02X Y:%02X SP:%02X P:%02X",
                 PC, A, X, Y, SP, getP());

        int sy = DISPLAY_HEIGHT - CHAR_H;          // y = 232
        fb_fill_rect(framebuffer, 0, sy, DISPLAY_WIDTH, CHAR_H, 0x000F);
        for (int i = 0; status[i] && i < 40; i++) {
            char c = status[i];
            if (c > 0x20 && c <= 0x7A)
                fb_draw_char(framebuffer, i * CHAR_W, sy, c, COLOR_WHITE, 0x000F);
        }
    }

    // 4. Single DMA blit – no tearing.
    display_blit_full(framebuffer);
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------
int main(void) {
    stdio_init_all();
    sleep_ms(500);

    printf("\n=== PICO 6502 Retro Computer ===\n");

    // Init display
    if (display_pack_init() != DISPLAY_OK) {
        printf("Display init failed\n");
        while (1) tight_loop_contents();
    }
    display_set_backlight(true);

    // Init buttons
    if (buttons_init() != DISPLAY_OK)
        printf("Warning: buttons init failed\n");

    printf("Display OK  %dx%d\n", DISPLAY_WIDTH, DISPLAY_HEIGHT);

    // ---- Memory setup --------------------------------------------------------
    memset(memory, 0, sizeof(memory));

    // Load ROM at $8000
    memcpy(memory + ROM_START, rom_data, ROM_DATA_SIZE);
    printf("ROM: %d bytes at $%04X\n", ROM_DATA_SIZE, ROM_START);

    // Reset vector → ROM start
    memory[VECTOR_RESET]     = ROM_START & 0xFF;
    memory[VECTOR_RESET + 1] = ROM_START >> 8;

    // Pre-fill screen RAM with spaces, colour RAM with light-blue
    memset(memory + SCREEN_RAM_START, 0x20, SCREEN_CHARS);
    memset(memory + COLOR_RAM_START,  0x0E, SCREEN_CHARS);

    // ---- Reset CPU -----------------------------------------------------------
    reset6502();
    printf("6502 reset.  PC=$%04X\n", PC);

    // Splash onto the character screen so there's something visible before the
    // ROM's init loop finishes.  fb_draw_string writes to the framebuffer; for
    // the character RAM we write PETSCII directly.
    {
        const char *title = "** PICO 6502 RETRO COMPUTER **";
        int tlen  = (int)strlen(title);
        int tstart = (SCREEN_COLS - tlen) / 2;
        for (int i = 0; i < tlen && (tstart + i) < SCREEN_COLS; i++) {
            memory[SCREEN_RAM_START + SCREEN_COLS * 0 + tstart + i] = (uint8_t)title[i];
            memory[COLOR_RAM_START  + SCREEN_COLS * 0 + tstart + i] = 0x01; // white
        }
    }

    // ---- Main loop -----------------------------------------------------------
    uint32_t cycle_count   = 0;
    uint32_t last_stat     = to_ms_since_boot(get_absolute_time());

    printf("Emulation started.\n");

    while (1) {
        buttons_update();

        // Run approximately 1 MHz worth of cycles per 16 ms frame (~16 666 cy)
        for (int i = 0; i < 16666; i++) {
            step6502();
            cycle_count++;
        }

        // Render and blit
        render_screen();

        // Periodic stats to UART
        uint32_t now = to_ms_since_boot(get_absolute_time());
        if (now - last_stat > 5000) {
            printf("cycles=%lu  PC=$%04X  A=$%02X  X=$%02X  Y=$%02X  SP=$%02X\n",
                   cycle_count, PC, A, X, Y, SP);
            last_stat = now;
        }

        sleep_ms(16);
    }

    return 0;
}

