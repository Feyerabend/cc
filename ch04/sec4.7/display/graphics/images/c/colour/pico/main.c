#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include "pico/stdlib.h"
#include "display.h"
#include "test_pattern.h"

typedef enum {
    MODE_TEST_PATTERN = 0,
    MODE_COLOR_DEMO = 1,
    MODE_RGB_BREAKDOWN = 2,
    MODE_COUNT = 3
} display_mode_t;

static display_mode_t current_mode = MODE_TEST_PATTERN;
static int current_color_index = 0;
static bool need_redraw = true;

// Button debouncing state
static bool button_was_pressed[BUTTON_COUNT] = {false};
static uint32_t last_button_time[BUTTON_COUNT] = {0};
#define DEBOUNCE_MS 200

// Helper to convert string to uppercase
void str_to_upper(char *str) {
    while (*str) {
        *str = toupper((unsigned char)*str);
        str++;
    }
}

void draw_test_pattern(void) {
    printf("Drawing test pattern..\n");
    
    // Draw the pattern efficiently - scale 5x
    for (int y = 0; y < TEST_PATTERN_HEIGHT; y++) {
        for (int x = 0; x < TEST_PATTERN_WIDTH; x++) {
            uint16_t color = test_pattern[y][x];
            display_fill_rect(x * 5, y * 5, 5, 5, color);
        }
        if (y % 8 == 0) {
            tight_loop_contents(); // Yield to system
        }
    }
    
    // Draw title bar
    display_fill_rect(0, 0, 320, 22, COLOR_BLACK);
    display_draw_string(10, 7, "TEST PATTERN - PRESS B", COLOR_WHITE, COLOR_BLACK);
    
    printf("Test pattern complete\n");
}

void draw_color_demo(void) {
    printf("Drawing color demo for color %d\n", current_color_index);
    
    display_clear(COLOR_BLACK);
    
    const color_info_t *info = &color_palette[current_color_index];
    
    // Large color swatch in center
    display_fill_rect(60, 60, 200, 120, info->color);
    
    // Draw white border around swatch
    display_fill_rect(58, 58, 204, 2, COLOR_WHITE);   // Top
    display_fill_rect(58, 180, 204, 2, COLOR_WHITE);  // Bottom
    display_fill_rect(58, 58, 2, 124, COLOR_WHITE);   // Left
    display_fill_rect(260, 58, 2, 124, COLOR_WHITE);  // Right
    
    // Title bar
    display_fill_rect(0, 0, 320, 26, 0x2104);
    display_draw_string(10, 9, "COLOR PALETTE", COLOR_WHITE, 0x2104);
    
    // Color name
    char name_buf[32];
    snprintf(name_buf, sizeof(name_buf), "COLOR: %s", info->name);
    str_to_upper(name_buf);
    display_draw_string(10, 36, name_buf, COLOR_WHITE, COLOR_BLACK);
    
    // RGB565 value
    char hex_buf[32];
    snprintf(hex_buf, sizeof(hex_buf), "RGB565: 0X%04X", info->color);
    display_draw_string(10, 192, hex_buf, COLOR_CYAN, COLOR_BLACK);
    
    // Component breakdown
    char comp_buf[40];
    snprintf(comp_buf, sizeof(comp_buf), "R:%02d G:%02d B:%02d (5:6:5 BIT)", 
             info->r_bits, info->g_bits, info->b_bits);
    display_draw_string(10, 204, comp_buf, COLOR_YELLOW, COLOR_BLACK);
    
    // Instructions
    display_draw_string(10, 222, "A:PREV X:NEXT Y:RGB B:TEST", COLOR_WHITE, COLOR_BLACK);
    
    printf("Color demo complete\n");
}

void draw_rgb_breakdown(void) {
    printf("Drawing RGB breakdown for color %d\n", current_color_index);
    
    display_clear(COLOR_BLACK);
    
    const color_info_t *info = &color_palette[current_color_index];
    
    // Title
    display_fill_rect(0, 0, 320, 26, 0x2104);
    display_draw_string(10, 9, "RGB565 BREAKDOWN", COLOR_WHITE, 0x2104);
    
    char name_buf[32];
    snprintf(name_buf, sizeof(name_buf), "%s (0X%04X)", info->name, info->color);
    str_to_upper(name_buf);
    display_draw_string(10, 36, name_buf, COLOR_WHITE, COLOR_BLACK);
    
    // Draw RGB component bars
    int bar_y = 65;
    int bar_height = 30;
    int bar_spacing = 48;
    
    // Red component (5 bits: 0-31)
    display_draw_string(10, bar_y - 14, "RED (5-BIT):", COLOR_RED, COLOR_BLACK);
    int red_width = (info->r_bits * 270) / 31;
    display_fill_rect(25, bar_y, 270, bar_height, 0x2104);
    if (red_width > 0) {
        display_fill_rect(25, bar_y, red_width, bar_height, COLOR_RED);
    }
    char val_buf[16];
    snprintf(val_buf, sizeof(val_buf), "%d/31", info->r_bits);
    display_draw_string(235, bar_y + 11, val_buf, COLOR_WHITE, COLOR_BLACK);
    
    // Green component (6 bits: 0-63)
    bar_y += bar_spacing;
    display_draw_string(10, bar_y - 14, "GREEN (6-BIT):", COLOR_GREEN, COLOR_BLACK);
    int green_width = (info->g_bits * 270) / 63;
    display_fill_rect(25, bar_y, 270, bar_height, 0x2104);
    if (green_width > 0) {
        display_fill_rect(25, bar_y, green_width, bar_height, COLOR_GREEN);
    }
    snprintf(val_buf, sizeof(val_buf), "%d/63", info->g_bits);
    display_draw_string(235, bar_y + 11, val_buf, COLOR_WHITE, COLOR_BLACK);
    
    // Blue component (5 bits: 0-31)
    bar_y += bar_spacing;
    display_draw_string(10, bar_y - 14, "BLUE (5-BIT):", COLOR_BLUE, COLOR_BLACK);
    int blue_width = (info->b_bits * 270) / 31;
    display_fill_rect(25, bar_y, 270, bar_height, 0x2104);
    if (blue_width > 0) {
        display_fill_rect(25, bar_y, blue_width, bar_height, COLOR_BLUE);
    }
    snprintf(val_buf, sizeof(val_buf), "%d/31", info->b_bits);
    display_draw_string(235, bar_y + 11, val_buf, COLOR_WHITE, COLOR_BLACK);
    
    // Instructions
    display_draw_string(10, 222, "A:PREV X:NEXT B:PATTERN", COLOR_WHITE, COLOR_BLACK);
    
    printf("RGB breakdown complete\n");
}

void redraw_display(void) {
    printf("Redrawing in mode %d\n", current_mode);
    
    display_set_backlight(true);
    
    switch (current_mode) {
        case MODE_TEST_PATTERN:
            draw_test_pattern();
            break;
        case MODE_COLOR_DEMO:
            draw_color_demo();
            break;
        case MODE_RGB_BREAKDOWN:
            draw_rgb_breakdown();
            break;
        default:
            printf("ERROR: Invalid mode %d, resetting\n", current_mode);
            current_mode = MODE_TEST_PATTERN;
            draw_test_pattern();
            break;
    }
    
    need_redraw = false;
}

// Check if button was just pressed with debouncing
bool check_button_press(button_t btn) {
    uint32_t now = to_ms_since_boot(get_absolute_time());
    
    // Check if button is currently pressed
    bool is_pressed = button_pressed(btn);
    
    // Detect rising edge (was not pressed, now is pressed)
    if (is_pressed && !button_was_pressed[btn]) {
        // Check debounce time
        if (now - last_button_time[btn] > DEBOUNCE_MS) {
            button_was_pressed[btn] = true;
            last_button_time[btn] = now;
            return true;
        }
    }
    
    // Update state when button is released
    if (!is_pressed) {
        button_was_pressed[btn] = false;
    }
    
    return false;
}

int main() {
    // Init stdio
    stdio_init_all();
    sleep_ms(1000);
    
    printf("TEST PATTERN DEMO\n");
    
    // Init display
    display_error_t result = display_pack_init();
    if (result != DISPLAY_OK) {
        printf("ERROR: DISPLAY INIT FAILED: %s\n", display_error_string(result));
        while(1) {
            sleep_ms(1000);
        }
    }
    printf("DISPLAY INITIALISED\n");
    
    // Turn on backlight
    display_set_backlight(true);
    
    // Init buttons
    result = buttons_init();
    if (result != DISPLAY_OK) {
        printf("ERROR: BUTTON INIT FAILED: %s\n", display_error_string(result));
        while(1) {
            sleep_ms(1000);
        }
    }
    printf("BUTTONS INITIALISED\n");
    printf("STARTING MAIN LOOP..\n\n");
    
    // Initial draw
    redraw_display();
    
    // Main loop - simple polling
    uint32_t last_status = 0;
    uint32_t loop_count = 0;
    
    while (1) {
        // Update button states
        buttons_update();
        
        // Check each button with proper debouncing
        if (check_button_press(BUTTON_A)) {
            printf(">>> BUTTON A PRESSED <<<\n");
            if (current_mode != MODE_TEST_PATTERN) {
                current_color_index--;
                if (current_color_index < 0) {
                    current_color_index = NUM_COLORS - 1;
                }
                printf("PREVIOUS COLOR: %d (%s)\n", 
                       current_color_index, color_palette[current_color_index].name);
                need_redraw = true;
            } else {
                printf("BUTTON A IGNORED IN TEST PATTERN MODE\n");
            }
        }
        
        if (check_button_press(BUTTON_B)) {
            printf(">>> BUTTON B PRESSED <<<\n");
            current_mode = (display_mode_t)((current_mode + 1) % MODE_COUNT);
            printf("MODE CHANGE TO: %d\n", current_mode);
            need_redraw = true;
        }
        
        if (check_button_press(BUTTON_X)) {
            printf(">>> BUTTON X PRESSED <<<\n");
            if (current_mode != MODE_TEST_PATTERN) {
                current_color_index = (current_color_index + 1) % NUM_COLORS;
                printf("NEXT COLOR: %d (%s)\n", 
                       current_color_index, color_palette[current_color_index].name);
                need_redraw = true;
            } else {
                printf("BUTTON X IGNORED IN TEST PATTERN MODE\n");
            }
        }
        
        if (check_button_press(BUTTON_Y)) {
            printf(">>> BUTTON Y PRESSED <<<\n");
            if (current_mode != MODE_RGB_BREAKDOWN) {
                current_mode = MODE_RGB_BREAKDOWN;
                printf("SWITCHING TO RGB BREAKDOWN MODE\n");
                need_redraw = true;
            } else {
                printf("ALREADY IN RGB BREAKDOWN MODE\n");
            }
        }
        
        // Redraw if needed
        if (need_redraw) {
            printf("\n-- REDRAW TRIGGERED --\n");
            redraw_display();
            printf("-- REDRAW COMPLETE --\n\n");
        }
        
        // Status update every 5 seconds
        uint32_t now = to_ms_since_boot(get_absolute_time());
        if (now - last_status > 5000) {
            printf("STATUS: MODE=%d, COLOR=%d, LOOP=%lu\n",
                   current_mode, current_color_index, loop_count);
            printf("BUTTONS RAW: A=%d B=%d X=%d Y=%d\n",
                   !gpio_get(12), !gpio_get(13), !gpio_get(14), !gpio_get(15));
            last_status = now;
        }
        
        loop_count++;
        sleep_ms(10);
    }
    
    return 0;
}
