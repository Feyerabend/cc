// main.c - Example to display the horse BMP on the display pack

#include "display.h"
#include "horse_bmp.h"
#include "pico/stdlib.h"

#include <stdlib.h>

int main(void) {
    // Initialize stdio for any debug output (optional)
    stdio_init_all();

    // Initialize the display
    display_error_t err = display_pack_init();
    if (err != DISPLAY_OK) {
        // Handle error, e.g., loop forever or print
        while (true) {}
    }

    // Optional: Initialize buttons if you want to use them
    buttons_init();

    // Allocate buffer for RGB565 pixels (320x240x2 bytes = 153600 bytes)
    uint16_t *pixel_buffer = (uint16_t *)malloc(DISPLAY_WIDTH * DISPLAY_HEIGHT * sizeof(uint16_t));
    if (pixel_buffer == NULL) {
        // Memory allocation failed - handle error
        display_cleanup();
        while (true) {}
    }

    // Parse BMP data (assuming it's a valid 320x240 24-bit BMP with top-down rows)
    // BMP header is 54 bytes, pixel data is BGR order
    uint8_t *bmp_data = horse_bmp + 54;  // Skip header

    for (uint16_t y = 0; y < DISPLAY_HEIGHT; y++) {
        for (uint16_t x = 0; x < DISPLAY_WIDTH; x++) {
            size_t bmp_idx = (y * DISPLAY_WIDTH + x) * 3;
            uint8_t b = bmp_data[bmp_idx + 0];
            uint8_t g = bmp_data[bmp_idx + 1];
            uint8_t r = bmp_data[bmp_idx + 2];

            // Convert to RGB565: (R[7:3] << 11) | (G[7:2] << 5) | B[7:3]
            uint16_t rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
            pixel_buffer[y * DISPLAY_WIDTH + x] = rgb565;
        }
    }

    // Blit the converted pixels to the display
    err = display_blit_full(pixel_buffer);
    if (err != DISPLAY_OK) {
        // Handle error
    }

    // Free the buffer (optional, since we loop forever)
    free(pixel_buffer);

    // Main loop - update buttons and keep running
    while (true) {
        buttons_update();
        sleep_ms(10);  // Small delay to avoid busy loop
    }

    // Cleanup (unreachable in this example)
    display_cleanup();
    return 0;
}
