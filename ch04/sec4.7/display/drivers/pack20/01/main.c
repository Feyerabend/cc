#include <stdio.h>
#include "pico/stdlib.h"
#include "display.h"


static volatile bool callback_in_progress = false;
static volatile uint32_t last_callback_time = 0;


static void safe_callback_wrapper(void (*callback_func)(button_t), button_t button) {
    uint32_t now = to_ms_since_boot(get_absolute_time());
    

    if (now - last_callback_time < 200) return;
    

    if (callback_in_progress) return;
    
    callback_in_progress = true;
    last_callback_time = now;
    

    if (callback_func) {
        callback_func(button);
    }
    
    callback_in_progress = false;
}


void on_button_a(button_t button) {
    printf("Button A pressed!\n");
    display_error_t result;
    
    if ((result = display_clear(COLOR_RED)) != DISPLAY_OK) {
        printf("Error clearing display: %s\n", display_error_string(result));
        return;
    }
    
    if ((result = display_draw_string(10, 60, "BUTTON A PRESSED", COLOR_WHITE, COLOR_RED)) != DISPLAY_OK) {
        printf("Error drawing string: %s\n", display_error_string(result));
    }
}

void on_button_b(button_t button) {
    printf("Button B pressed!\n");
    display_error_t result;
    
    if ((result = display_clear(COLOR_GREEN)) != DISPLAY_OK) {
        printf("Error clearing display: %s\n", display_error_string(result));
        return;
    }
    
    if ((result = display_draw_string(10, 60, "BUTTON B PRESSED", COLOR_WHITE, COLOR_GREEN)) != DISPLAY_OK) {
        printf("Error drawing string: %s\n", display_error_string(result));
    }
}

void on_button_x(button_t button) {
    printf("Button X pressed!\n");
    display_error_t result;
    
    if ((result = display_clear(COLOR_BLUE)) != DISPLAY_OK) {
        printf("Error clearing display: %s\n", display_error_string(result));
        return;
    }
    
    if ((result = display_draw_string(10, 60, "BUTTON X PRESSED", COLOR_WHITE, COLOR_BLUE)) != DISPLAY_OK) {
        printf("Error drawing string: %s\n", display_error_string(result));
    }
}

void on_button_y(button_t button) {
    printf("Button Y pressed!\n");
    display_error_t result;
    
    if ((result = display_clear(COLOR_YELLOW)) != DISPLAY_OK) {
        printf("Error clearing display: %s\n", display_error_string(result));
        return;
    }
    
    if ((result = display_draw_string(10, 60, "BUTTON Y PRESSED", COLOR_BLACK, COLOR_YELLOW)) != DISPLAY_OK) {
        printf("Error drawing string: %s\n", display_error_string(result));
    }
}


void safe_on_button_a(button_t button) { safe_callback_wrapper(on_button_a, button); }
void safe_on_button_b(button_t button) { safe_callback_wrapper(on_button_b, button); }
void safe_on_button_x(button_t button) { safe_callback_wrapper(on_button_x, button); }
void safe_on_button_y(button_t button) { safe_callback_wrapper(on_button_y, button); }


static bool draw_initial_screen(void) {
    display_error_t result;
    
    // Clear screen
    if ((result = display_clear(COLOR_BLACK)) != DISPLAY_OK) {
        printf("Failed to clear display: %s\n", display_error_string(result));
        return false;
    }
    
    // Draw title
    if ((result = display_draw_string(10, 10, "ROBUST DISPLAY LIBRARY", COLOR_WHITE, COLOR_BLACK)) != DISPLAY_OK) {
        printf("Failed to draw title: %s\n", display_error_string(result));
        return false;
    }
    
    // Draw test strings with bounds checking
    const char* test_lines[] = {
        "TEXT SHOULD NOT BE MIRRORED?",
        "01234567890123456789012345678901234567890123456789", // ? works
        "PRESS ANY BUTTON TO TEST",
        "A=RED B=GREEN X=BLUE Y=YELLOW"
    };
    
    uint16_t y_positions[] = {25, 40, 55, 70};
    uint16_t colors[] = {COLOR_CYAN, COLOR_CYAN, COLOR_YELLOW, COLOR_WHITE};
    
    for (int i = 0; i < 4; i++) {
        if ((result = display_draw_string(10, y_positions[i], test_lines[i], colors[i], COLOR_BLACK)) != DISPLAY_OK) {
            printf("Failed to draw line %d: %s\n", i, display_error_string(result));
            // Continue with other lines even if one fails
        }
    }
    
    // Draw a test rectangle with bounds checking
    if ((result = display_fill_rect(10, 90, 50, 20, COLOR_MAGENTA)) != DISPLAY_OK) {
        printf("Failed to draw rectangle: %s\n", display_error_string(result));
    } else {
        if ((result = display_draw_string(15, 95, "RECT", COLOR_WHITE, COLOR_MAGENTA)) != DISPLAY_OK) {
            printf("Failed to draw rectangle text: %s\n", display_error_string(result));
        }
    }
    
    // Draw individual pixels with bounds checking
    for (int i = 0; i < 20; i++) {
        uint16_t x_pos = 70 + i;
        uint16_t y_pos = 90 + i/2;
        
        // Check bounds before drawing
        if (x_pos < DISPLAY_WIDTH - 40 && y_pos < DISPLAY_HEIGHT - 10) {
            display_draw_pixel(x_pos, y_pos, COLOR_RED);
            display_draw_pixel(x_pos + 20, y_pos, COLOR_GREEN);
            display_draw_pixel(x_pos + 40, y_pos, COLOR_BLUE);
        }
    }
    
    return true;
}

// Function to safely initialise everything
static bool initialize_system(void) {
    display_error_t result;
    
    printf("Init system..\n");
    
    // Init display with error checking
    if ((result = display_pack_init()) != DISPLAY_OK) {
        printf("Failed to initialise display: %s\n", display_error_string(result));
        return false;
    }
    printf("Display initialised successfully\n");
    
    // Initialize buttons with error checking
    if ((result = buttons_init()) != DISPLAY_OK) {
        printf("Failed to initialise buttons: %s\n", display_error_string(result));
        return false;
    }
    printf("Buttons initialised successfully\n");
    
    // Set up button callbacks with error checking
    struct {
        button_t button;
        button_callback_t callback;
        const char* name;
    } button_configs[] = {
        {BUTTON_A, safe_on_button_a, "A"},
        {BUTTON_B, safe_on_button_b, "B"},
        {BUTTON_X, safe_on_button_x, "X"},
        {BUTTON_Y, safe_on_button_y, "Y"}
    };
    
    for (int i = 0; i < 4; i++) {
        if ((result = button_set_callback(button_configs[i].button, button_configs[i].callback)) != DISPLAY_OK) {
            printf("Failed to set callback for button %s: %s\n", 
                   button_configs[i].name, display_error_string(result));
            return false;
        }
        printf("Button %s callback set successfully\n", button_configs[i].name);
    }
    
    return true;
}

int main() {
    stdio_init_all();
    
    printf("-- Display Pack Library Example --\n");
    
    // Init system with comprehensive error checking
    if (!initialize_system()) {
        printf("System init failed! Exiting..\n");
        return 1;
    }
    
    // Draw initial screen
    if (!draw_initial_screen()) {
        printf("Failed to draw initial screen, but continuing..\n");
    }
    
    printf("Example Started!\n");
    printf("Press buttons A, B, X, or Y to test functionality\n");
    printf("Hold A+B together to toggle backlight\n");
    
    // Main loop with error recovery
    uint32_t last_status_print = 0;
    uint32_t backlight_toggle_time = 0;
    bool backlight_on = true;
    bool both_buttons_pressed = false;
    
    while (true) {
        // Update button states (this handles debouncing and callbacks)
        buttons_update();
        
        // Check for special key combination (A+B for backlight toggle)
        bool a_pressed = button_pressed(BUTTON_A);
        bool b_pressed = button_pressed(BUTTON_B);
        
        if (a_pressed && b_pressed && !both_buttons_pressed) {
            uint32_t now = to_ms_since_boot(get_absolute_time());
            if (now - backlight_toggle_time > 1000) { // Prevent rapid toggling
                backlight_on = !backlight_on;
                display_error_t result = display_set_backlight(backlight_on);
                if (result == DISPLAY_OK) {
                    printf("Toggled backlight: %s\n", backlight_on ? "ON" : "OFF");
                } else {
                    printf("Failed to toggle backlight: %s\n", display_error_string(result));
                }
                backlight_toggle_time = now;
            }
            both_buttons_pressed = true;
        } else if (!a_pressed || !b_pressed) {
            both_buttons_pressed = false;
        }
        
        // Periodic status update (every 30 seconds)
        uint32_t now = to_ms_since_boot(get_absolute_time());
        if (now - last_status_print > 30000) {
            printf("System status: Display=%s, Buttons=%s, DMA=%s\n",
                   display_is_initialized() ? "OK" : "ERROR",
                   "OK", // buttons don't have a direct status check
                   display_dma_busy() ? "BUSY" : "IDLE");
            last_status_print = now;
        }
        
        // Wait for any pending display operations before continuing
        if (display_dma_busy()) {
            display_wait_for_dma();
        }
        
        sleep_ms(10); // Small delay to prevent excessive CPU usage
    }
    
    // Cleanup (this code should never be reached in normal operation)
    printf("Cleaning up..\n");
    display_cleanup();
    
    return 0;
}
