#include "display.h"
#include "pico/stdlib.h"
#include <stdio.h>
#include <string.h>

// State
typedef struct {
    uint32_t counter;
    uint32_t ms_counter;
    uint32_t lap_time;
    bool running;
    bool show_lap;
    uint32_t last_update_ms;
    bool needs_full_redraw;
} timer_state_t;

static timer_state_t state = {0};
static uint16_t *fb = NULL;

// Draw large digit (3x scale) to framebuffer
// Esp. for this demo
void draw_large_digit(uint16_t x, uint16_t y, char c, uint16_t fg, uint16_t bg) {
    if (c < '0' || c > '9') c = '0';
    
    const uint8_t digits[10][7] = {
        {0x0E,0x11,0x11,0x11,0x11,0x11,0x0E}, // 0
        {0x04,0x0C,0x04,0x04,0x04,0x04,0x0E}, // 1
        {0x0E,0x11,0x01,0x0E,0x10,0x10,0x1F}, // 2
        {0x0E,0x11,0x01,0x0E,0x01,0x11,0x0E}, // 3
        {0x11,0x11,0x11,0x1F,0x01,0x01,0x01}, // 4
        {0x1F,0x10,0x10,0x0E,0x01,0x11,0x0E}, // 5
        {0x0E,0x10,0x10,0x1E,0x11,0x11,0x0E}, // 6
        {0x1F,0x01,0x02,0x04,0x08,0x08,0x08}, // 7
        {0x0E,0x11,0x11,0x0E,0x11,0x11,0x0E}, // 8
        {0x0E,0x11,0x11,0x0F,0x01,0x01,0x0E}, // 9
    };
    
    const uint8_t *pattern = digits[c - '0'];
    
    for (int row = 0; row < 7; row++) {
        for (int col = 0; col < 5; col++) {
            uint16_t color = (pattern[row] & (1 << (4 - col))) ? fg : bg;
            disp_framebuffer_fill_rect(x + col*3, y + row*3, 3, 3, color);
        }
    }
}

// Draw time in large format
void draw_large_time(uint16_t x, uint16_t y, uint32_t total_ms, uint16_t color) {
    uint32_t minutes = (total_ms / 60000) % 100;
    uint32_t seconds = (total_ms / 1000) % 60;
    uint32_t millis = total_ms % 1000;
    
    char time_str[16];
    sprintf(time_str, "%02lu:%02lu.%03lu", minutes, seconds, millis);
    
    uint16_t cx = x;
    for (int i = 0; time_str[i]; i++) {
        if (time_str[i] >= '0' && time_str[i] <= '9') {
            draw_large_digit(cx, y, time_str[i], color, COLOR_BLACK);
            cx += 18;
        } else if (time_str[i] == ':') {
            disp_framebuffer_fill_rect(cx + 2, y + 6, 3, 3, color);
            disp_framebuffer_fill_rect(cx + 2, y + 15, 3, 3, color);
            cx += 10;
        } else if (time_str[i] == '.') {
            disp_framebuffer_fill_rect(cx + 2, y + 18, 3, 3, color);
            cx += 10;
        }
    }
}

// Draw progress bar
void draw_progress_bar(uint16_t x, uint16_t y, uint16_t w, uint16_t h, 
                       uint32_t value, uint32_t max, uint16_t color) {
    disp_framebuffer_fill_rect(x, y, w, h, COLOR_WHITE);
    disp_framebuffer_fill_rect(x+2, y+2, w-4, h-4, COLOR_BLACK);
    
    if (max > 0) {
        uint16_t fill_w = ((w-4) * value) / max;
        if (fill_w > 0) {
            disp_framebuffer_fill_rect(x+2, y+2, fill_w, h-4, color);
        }
    }
}

// Draw static UI
void draw_static_ui(void) {
    disp_framebuffer_draw_text(10, 5, "PRECISION STOPWATCH", COLOR_CYAN, COLOR_BLACK);
    disp_framebuffer_fill_rect(0, 140, DISPLAY_WIDTH, 1, COLOR_WHITE);
    disp_framebuffer_draw_text(10, 150, "A: Start/Stop", COLOR_CYAN, COLOR_BLACK);
    disp_framebuffer_draw_text(10, 165, "B: Reset", COLOR_CYAN, COLOR_BLACK);
    disp_framebuffer_draw_text(10, 180, "X: Lap/Split", COLOR_CYAN, COLOR_BLACK);
    disp_framebuffer_draw_text(10, 195, "Y: Toggle Lap", COLOR_CYAN, COLOR_BLACK);
}

// Update dynamic content
void update_display_dynamic(void) {
    // Clear dynamic areas
    disp_framebuffer_fill_rect(20, 35, 280, 25, COLOR_BLACK);
    disp_framebuffer_fill_rect(20, 70, 280, 20, COLOR_BLACK);
    disp_framebuffer_fill_rect(20, 100, 280, 12, COLOR_BLACK);
    disp_framebuffer_fill_rect(10, 120, 200, 12, COLOR_BLACK);
    disp_framebuffer_fill_rect(180, 150, 140, 12, COLOR_BLACK);
    
    // Main timer
    uint32_t display_ms = state.running ? state.ms_counter : state.counter * 1000;
    draw_large_time(20, 35, display_ms, state.running ? COLOR_GREEN : COLOR_YELLOW);
    
    // Progress bar
    uint32_t sec_progress = (display_ms / 1000) % 60;
    draw_progress_bar(20, 70, 280, 20, sec_progress, 60, COLOR_BLUE);
    
    // Lap time
    if (state.show_lap && state.lap_time > 0) {
        disp_framebuffer_draw_text(20, 100, "LAP:", COLOR_MAGENTA, COLOR_BLACK);
        char lap_str[32];
        sprintf(lap_str, "%02lu:%02lu.%03lu", 
                (state.lap_time / 60000) % 100,
                (state.lap_time / 1000) % 60,
                state.lap_time % 1000);
        disp_framebuffer_draw_text(70, 100, lap_str, COLOR_WHITE, COLOR_BLACK);
    }
    
    // MS ticker
    if (state.running) {
        char ms_str[8];
        sprintf(ms_str, "%03lu", display_ms % 1000);
        disp_framebuffer_draw_text(260, 100, ms_str, COLOR_YELLOW, COLOR_BLACK);
    }
    
    // Status
    disp_framebuffer_draw_text(10, 120, 
        state.running ? "STATUS: RUNNING" : "STATUS: STOPPED", 
        state.running ? COLOR_GREEN : COLOR_RED, COLOR_BLACK);
    
    // Counter
    char info[32];
    sprintf(info, "Count: %lu", state.counter);
    disp_framebuffer_draw_text(180, 150, info, COLOR_WHITE, COLOR_BLACK);
}

// Full screen update
void update_display_full(void) {
    disp_framebuffer_clear(COLOR_BLACK);
    draw_static_ui();
    update_display_dynamic();
    state.needs_full_redraw = false;
}

// Button callbacks
void on_button_a(button_t btn) {
    state.running = !state.running;
    if (state.running) {
        state.last_update_ms = to_ms_since_boot(get_absolute_time());
    }
    state.needs_full_redraw = true;
}

void on_button_b(button_t btn) {
    state.counter = 0;
    state.ms_counter = 0;
    state.lap_time = 0;
    state.running = false;
    state.show_lap = false;
    state.needs_full_redraw = true;
}

void on_button_x(button_t btn) {
    if (state.running) {
        state.lap_time = state.ms_counter;
        state.show_lap = true;
        state.needs_full_redraw = true;
    }
}

void on_button_y(button_t btn) {
    state.show_lap = !state.show_lap;
    state.needs_full_redraw = true;
}

int main() {
    stdio_init_all();
    sleep_ms(1000);
    
    printf("-- Precision Stopwatch --n");
    
    // Initialize display
    disp_config_t config = disp_get_default_config();
    disp_error_t err = disp_init(&config);
    
    if (err != DISP_OK) {
        printf("Display init failed: %s\n", disp_error_string(err));
        return -1;
    }
    
    // Allocate framebuffer
    err = disp_framebuffer_alloc();
    if (err != DISP_OK) {
        printf("Framebuffer alloc failed: %s\n", disp_error_string(err));
        disp_deinit();
        return -1;
    }
    
    fb = disp_get_framebuffer();
    
    // Initialize buttons
    buttons_init();
    button_set_callback(BUTTON_A, on_button_a);
    button_set_callback(BUTTON_B, on_button_b);
    button_set_callback(BUTTON_X, on_button_x);
    button_set_callback(BUTTON_Y, on_button_y);
    
    // Initial draw
    state.last_update_ms = to_ms_since_boot(get_absolute_time());
    state.needs_full_redraw = true;
    update_display_full();
    disp_framebuffer_flush();
    
    printf("Running..\n");
    
    uint32_t last_display_update = 0;
    
    while (true) {
        uint32_t now = to_ms_since_boot(get_absolute_time());
        
        buttons_update();
        
        if (state.running) {
            uint32_t elapsed = now - state.last_update_ms;
            state.ms_counter += elapsed;
            state.last_update_ms = now;
            state.counter = state.ms_counter / 1000;
        }
        
        uint32_t update_interval = state.running ? 33 : 100;
        if (now - last_display_update >= update_interval) {
            if (state.needs_full_redraw) {
                update_display_full();
            } else {
                update_display_dynamic();
            }
            
            disp_framebuffer_flush();
            last_display_update = now;
        }
        
        sleep_ms(1);
    }
    
    return 0;
}
