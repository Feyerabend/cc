#include <stdio.h>
#include "pico/stdlib.h"
#include "display.h"

int main() {
    // Initialize standard I/O for debugging
    stdio_init_all();
    printf("Starting simple display test...\n");

    // Initialize display
    if (display_pack_init() != DISPLAY_OK) {
        printf("Display initialization failed: %s\n", display_error_string(display_pack_init()));
        return 1;
    }
    printf("Display initialized\n");

    // Initialize buttons
    if (buttons_init() != DISPLAY_OK) {
        printf("Buttons initialization failed: %s\n", display_error_string(buttons_init()));
        return 1;
    }
    printf("Buttons initialized\n");

    // Turn on backlight
    if (display_set_backlight(true) != DISPLAY_OK) {
        printf("Failed to set backlight\n");
        return 1;
    }
    printf("Backlight enabled\n");

    // Array of colors to cycle through
    uint16_t colors[] = {COLOR_YELLOW, COLOR_RED, COLOR_GREEN, COLOR_BLUE};
    int color_index = 0;
    int num_colors = sizeof(colors) / sizeof(colors[0]);

    // Initial display fill
    if (display_clear(colors[color_index]) != DISPLAY_OK) {
        printf("Failed to clear display with color 0x%04X\n", colors[color_index]);
        return 1;
    }
    printf("Display filled with color 0x%04X\n", colors[color_index]);

    while (true) {
        buttons_update();

        // Cycle colors on BUTTON_Y press
        if (button_just_pressed(BUTTON_Y)) {
            color_index = (color_index + 1) % num_colors;
            if (display_clear(colors[color_index]) != DISPLAY_OK) {
                printf("Failed to clear display with color 0x%04X\n", colors[color_index]);
            } else {
                printf("Display filled with color 0x%04X\n", colors[color_index]);
            }
        }

        // Frame rate control (~60 FPS)
        sleep_ms(16);
    }

    // Cleanup (unreachable, but for completeness)
    display_cleanup();
    return 0;
}
