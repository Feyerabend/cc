// A stand-in for display.c, so the Lisp VM and games can run on a PC.
// Drawing goes to an in-memory framebuffer that can be saved as an image,
// and button presses are set from the host program.

#include "display_host.h"
#include "../font5x8.h"
#include <stdio.h>
#include <string.h>

static uint16_t framebuffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];
static bool have_framebuffer = false;
static bool btn_down[BUTTON_COUNT];
static bool btn_was_down[BUTTON_COUNT];
static bool btn_next[BUTTON_COUNT];
static uint32_t flush_count = 0;

disp_config_t disp_get_default_config(void) {
    return (disp_config_t) { 0 };
}

disp_error_t disp_init(const disp_config_t *config) {
    (void) config;
    return DISP_OK;
}

disp_error_t disp_deinit(void) {
    return DISP_OK;
}

void disp_set_error_context(disp_error_t code, const char *function, int line, const char *message) {
    (void) code;
    (void) function;
    (void) line;
    (void) message;
}

const char *disp_error_string(disp_error_t error) {
    return error == DISP_OK ? "OK" : "Error";
}

disp_error_t disp_framebuffer_alloc(void) {
    have_framebuffer = true;
    return DISP_OK;
}

void disp_framebuffer_free(void) {
    have_framebuffer = false;
}

uint16_t *disp_get_framebuffer(void) {
    return have_framebuffer ? framebuffer : NULL;
}

disp_error_t disp_framebuffer_flush(void) {
    flush_count++;
    return DISP_OK;
}

disp_error_t disp_framebuffer_clear(uint16_t color) {
    for (size_t i = 0; i < DISPLAY_WIDTH * DISPLAY_HEIGHT; i++) {
        framebuffer[i] = color;
    }
    return DISP_OK;
}

void disp_framebuffer_set_pixel(uint16_t x, uint16_t y, uint16_t color) {
    if (x < DISPLAY_WIDTH && y < DISPLAY_HEIGHT) {
        framebuffer[y * DISPLAY_WIDTH + x] = color;
    }
}

void disp_framebuffer_fill_rect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint16_t color) {
    for (uint32_t dy = 0; dy < h; dy++) {
        for (uint32_t dx = 0; dx < w; dx++) {
            disp_framebuffer_set_pixel((uint16_t) (x + dx), (uint16_t) (y + dy), color);
        }
    }
}

void disp_framebuffer_draw_char(uint16_t x, uint16_t y, char c, uint16_t fg, uint16_t bg) {
    if ((unsigned char) c < 32 || (unsigned char) c > 127) c = ' ';
    const uint8_t *glyph = FONT_5X8[c - 32];
    for (int col = 0; col < 5; col++) {
        for (int row = 0; row < 8; row++) {
            uint16_t color = (glyph[col] & (1 << row)) ? fg : bg;
            disp_framebuffer_set_pixel((uint16_t) (x + col), (uint16_t) (y + row), color);
        }
    }
}

void disp_framebuffer_draw_text(uint16_t x, uint16_t y, const char *text, uint16_t fg, uint16_t bg) {
    while (*text && x < DISPLAY_WIDTH) {
        disp_framebuffer_draw_char(x, y, *text++, fg, bg);
        x += 6;
    }
}

disp_error_t buttons_init(void) {
    memset(btn_down, 0, sizeof(btn_down));
    memset(btn_was_down, 0, sizeof(btn_was_down));
    memset(btn_next, 0, sizeof(btn_next));
    return DISP_OK;
}

void buttons_update(void) {
    for (int i = 0; i < BUTTON_COUNT; i++) {
        btn_was_down[i] = btn_down[i];
        btn_down[i] = btn_next[i];
    }
}

bool button_pressed(button_t button) {
    return button < BUTTON_COUNT && btn_down[button];
}

bool button_just_pressed(button_t button) {
    return button < BUTTON_COUNT && btn_down[button] && !btn_was_down[button];
}

bool button_just_released(button_t button) {
    return button < BUTTON_COUNT && !btn_down[button] && btn_was_down[button];
}

void host_set_button(button_t button, bool down) {
    if (button < BUTTON_COUNT) btn_next[button] = down;
}

uint32_t host_flush_count(void) {
    return flush_count;
}

// Writes the framebuffer as a binary PPM image
bool host_save_ppm(const char *path) {
    FILE *f = fopen(path, "wb");
    if (f == NULL) return false;
    fprintf(f, "P6\n%d %d\n255\n", DISPLAY_WIDTH, DISPLAY_HEIGHT);
    for (size_t i = 0; i < DISPLAY_WIDTH * DISPLAY_HEIGHT; i++) {
        uint16_t c = framebuffer[i];
        uint8_t rgb[3] = {
            (uint8_t) (((c >> 11) & 0x1F) * 255 / 31),
            (uint8_t) (((c >> 5) & 0x3F) * 255 / 63),
            (uint8_t) ((c & 0x1F) * 255 / 31)
        };
        fwrite(rgb, 1, 3, f);
    }
    return fclose(f) == 0;
}

// A checksum of the screen, so tests can tell whether drawing changed
uint32_t host_screen_hash(void) {
    uint32_t h = 2166136261u;
    for (size_t i = 0; i < DISPLAY_WIDTH * DISPLAY_HEIGHT; i++) {
        h = (h ^ (framebuffer[i] & 0xFF)) * 16777619u;
        h = (h ^ (framebuffer[i] >> 8)) * 16777619u;
    }
    return h;
}

uint16_t host_get_pixel(int x, int y) {
    if (x < 0 || y < 0 || x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return 0;
    return framebuffer[y * DISPLAY_WIDTH + x];
}
