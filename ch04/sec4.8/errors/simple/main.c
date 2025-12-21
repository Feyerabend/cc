#include "display.h"
#include "pico/stdlib.h"
#include <stdio.h>
#include <stdlib.h>

// Simple menu system
typedef enum {
    TEST_COLORS,
    TEST_RECTANGLES,
    TEST_PIXELS,
    TEST_TEXT,
    TEST_BLIT,
    TEST_FRAMEBUFFER,
    TEST_BACKLIGHT,
    TEST_COUNT
} test_mode_t;

const char* test_names[] = {
    "Color Fill",
    "Rectangles",
    "Random Pixels",
    "Text Drawing",
    "Image Blit",
    "Framebuffer",
    "Backlight Toggle"
};

uint16_t current_test = 0;
bool test_running = false;
bool menu_changed = false;

// Display menu
void show_menu(void) {
    disp_clear(COLOR_BLACK);
    disp_draw_text(60, 20, "API TESTER", COLOR_WHITE, COLOR_BLACK);
    
    for (int i = 0; i < TEST_COUNT; i++) {
        uint16_t color = (i == current_test) ? COLOR_YELLOW : COLOR_CYAN;
        char line[40];
        snprintf(line, sizeof(line), "%c %s", (i == current_test) ? '>' : ' ', test_names[i]);
        disp_draw_text(20, 50 + i * 20, line, color, COLOR_BLACK);
    }
    
    disp_draw_text(20, 200, "A:Select X:Up Y:Down", COLOR_GREEN, COLOR_BLACK);
}

// Test 1: Basic color fills
void test_colors(void) {
    printf("\nTest: Color Fills\n");
    
    uint16_t colors[] = {
        COLOR_RED, COLOR_GREEN, COLOR_BLUE,
        COLOR_YELLOW, COLOR_CYAN, COLOR_MAGENTA,
        COLOR_WHITE, COLOR_BLACK
    };
    const char* color_names[] = {
        "RED",
        "GREEN",
        "BLUE",
        "YELLOW",
        "CYAN",
        "MAGENTA",
        "WHITE",
        "BLACK"
    };
    
    for (int i = 0; i < 8; i++) {
        printf("Filling screen with %s\n", color_names[i]);
        disp_clear(colors[i]);
        
        // Draw label
        uint16_t fg = (i == 7) ? COLOR_WHITE : COLOR_BLACK;
        uint16_t bg = colors[i];
        disp_draw_text(100, 110, color_names[i], fg, bg);
        
        sleep_ms(800);
        
        // Check for exit
        buttons_update();
        if (button_pressed(BUTTON_B)) {
            printf("Test cancelled\n");
            return;
        }
    }
    
    printf("Color test complete!\n");
}

// Test 2: Draw rectangles
void test_rectangles(void) {
    printf("\nTest: Rectangles\n");
    
    disp_clear(COLOR_BLACK);
    
    // Nested rectangles
    for (int i = 0; i < 10; i++) {
        uint16_t x = i * 16;
        uint16_t y = i * 12;
        uint16_t w = DISPLAY_WIDTH - x * 2;
        uint16_t h = DISPLAY_HEIGHT - y * 2;
        uint16_t color = (i * 7) << 11 | (i * 5) << 5 | (i * 3);
        
        printf("Drawing rect %d: (%d,%d) %dx%d\n", i, x, y, w, h);
        disp_fill_rect(x, y, w, h, color);
        sleep_ms(200);
        
        buttons_update();
        if (button_pressed(BUTTON_B)) return;
    }
    
    sleep_ms(1000);
    
    // Random rectangles
    disp_clear(COLOR_BLACK);
    disp_draw_text(60, 10, "Random Rectangles", COLOR_WHITE, COLOR_BLACK);
    
    for (int i = 0; i < 30; i++) {
        uint16_t x = rand() % DISPLAY_WIDTH;
        uint16_t y = rand() % DISPLAY_HEIGHT;
        uint16_t w = 20 + rand() % 60;
        uint16_t h = 20 + rand() % 60;
        uint16_t color = rand() & 0xFFFF;
        
        disp_fill_rect(x, y, w, h, color);
        sleep_ms(150);
        
        buttons_update();
        if (button_pressed(BUTTON_B)) return;
    }
    
    printf("Rectangle test complete!\n");
}

// Test 3: Random pixels
void test_pixels(void) {
    printf("\nTest: Random Pixels\n");
    
    disp_clear(COLOR_BLACK);
    disp_draw_text(80, 10, "Drawing Pixels", COLOR_WHITE, COLOR_BLACK);
    
    uint32_t start = to_ms_since_boot(get_absolute_time());
    
    for (int i = 0; i < 5000; i++) {
        uint16_t x = rand() % DISPLAY_WIDTH;
        uint16_t y = 30 + rand() % (DISPLAY_HEIGHT - 30);
        uint16_t color = rand() & 0xFFFF;
        
        disp_draw_pixel(x, y, color);
        
        if (i % 500 == 0) {
            buttons_update();
            if (button_pressed(BUTTON_B)) return;
        }
    }
    
    uint32_t elapsed = to_ms_since_boot(get_absolute_time()) - start;
    printf("Drew 5000 pixels in %lu ms (%.1f pixels/sec)\n", 
           (unsigned long)elapsed, 5000000.0f / elapsed);
    
    sleep_ms(2000);
}

// Test 4: Text rendering
void test_text(void) {
    printf("\nTest: Text Drawing\n");
    
    disp_clear(COLOR_BLACK);
    
    // Title
    disp_draw_text(80, 10, "TEXT RENDERING", COLOR_WHITE, COLOR_BLACK);
    
    // Different colors
    disp_draw_text(10, 40, "Red text", COLOR_RED, COLOR_BLACK);
    disp_draw_text(10, 55, "Green text", COLOR_GREEN, COLOR_BLACK);
    disp_draw_text(10, 70, "Blue text", COLOR_BLUE, COLOR_BLACK);
    disp_draw_text(10, 85, "Yellow text", COLOR_YELLOW, COLOR_BLACK);
    disp_draw_text(10, 100, "Cyan text", COLOR_CYAN, COLOR_BLACK);
    disp_draw_text(10, 115, "Magenta text", COLOR_MAGENTA, COLOR_BLACK);
    
    // ASCII range test
    disp_draw_text(10, 140, "ASCII 32-127:", COLOR_WHITE, COLOR_BLACK);
    disp_draw_text(10, 155, "!\"#$%&'()*+,-./01234", COLOR_CYAN, COLOR_BLACK);
    disp_draw_text(10, 170, "56789:;<=>?@ABCDEFGH", COLOR_CYAN, COLOR_BLACK);
    disp_draw_text(10, 185, "IJKLMNOPQRSTUVWXYZ[", COLOR_CYAN, COLOR_BLACK);
    disp_draw_text(10, 200, "\\]^_`abcdefghijklmno", COLOR_CYAN, COLOR_BLACK);
    disp_draw_text(10, 215, "pqrstuvwxyz{|}~", COLOR_CYAN, COLOR_BLACK);
    
    printf("Text test complete\n");
    sleep_ms(3000);
}

// Test 5: Image blit
void test_blit(void) {
    printf("\nTest: Image Blit\n");
    
    disp_clear(COLOR_BLACK);
    disp_draw_text(90, 10, "IMAGE BLIT", COLOR_WHITE, COLOR_BLACK);
    
    // Create a gradient image
    const int img_w = 100, img_h = 80;
    uint16_t *img = malloc(img_w * img_h * sizeof(uint16_t));
    
    if (!img) {
        printf("Failed to allocate image buffer\n");
        disp_draw_text(40, 100, "Memory allocation failed!", COLOR_RED, COLOR_BLACK);
        sleep_ms(2000);
        return;
    }
    
    // Generate gradient
    for (int y = 0; y < img_h; y++) {
        for (int x = 0; x < img_w; x++) {
            uint8_t r = (x * 31) / img_w;
            uint8_t g = (y * 63) / img_h;
            uint8_t b = ((x + y) * 31) / (img_w + img_h);
            img[y * img_w + x] = (r << 11) | (g << 5) | b;
        }
    }
    
    // Blit to different positions
    int positions[][2] = {
        {10, 40},
        {110, 40},
        {210, 40},
        {10, 130},
        {110, 130},
        {210, 130}
    };
    
    for (int i = 0; i < 6; i++) {
        printf("Blitting image to position %d: (%d, %d)\n", i, positions[i][0], positions[i][1]);
        disp_blit(positions[i][0], positions[i][1], img_w, img_h, img);
        sleep_ms(400);
        
        buttons_update();
        if (button_pressed(BUTTON_B)) {
            free(img);
            return;
        }
    }
    
    free(img);
    printf("Blit test complete\n");
    sleep_ms(2000);
}

// Test 6: Framebuffer performance
void test_framebuffer(void) {
    printf("\nTest: Framebuffer Mode\n");
    
    if (disp_framebuffer_alloc() != DISP_OK) {
        printf("Failed to allocate framebuffer\n");
        disp_clear(COLOR_BLACK);
        disp_draw_text(40, 100, "Framebuffer alloc failed!", COLOR_RED, COLOR_BLACK);
        sleep_ms(2000);
        return;
    }
    
    uint16_t *fb = disp_get_framebuffer();
    
    // Animated gradient
    for (int frame = 0; frame < 100; frame++) {
        for (int y = 0; y < DISPLAY_HEIGHT; y++) {
            for (int x = 0; x < DISPLAY_WIDTH; x++) {
                uint8_t r = ((x + frame) * 31) / DISPLAY_WIDTH;
                uint8_t g = ((y + frame) * 63) / DISPLAY_HEIGHT;
                uint8_t b = (((x + y + frame * 2) % 256) * 31) / 256;
                fb[y * DISPLAY_WIDTH + x] = (r << 11) | (g << 5) | b;
            }
        }
        
        // Add text overlay
        disp_draw_text(60, 110, "FRAMEBUFFER MODE", COLOR_WHITE, COLOR_BLACK);
        
        uint32_t start = to_ms_since_boot(get_absolute_time());
        disp_framebuffer_flush();
        uint32_t elapsed = to_ms_since_boot(get_absolute_time()) - start;
        
        if (frame % 10 == 0) {
            printf("Frame %d flushed in %lu ms\n", frame, (unsigned long)elapsed);
        }
        
        buttons_update();
        if (button_pressed(BUTTON_B)) break;
    }
    
    disp_framebuffer_free();
    printf("Framebuffer test complete\n");
}

// Test 7: Backlight toggle
void test_backlight(void) {
    printf("\nTest: Backlight Toggle\n");
    
    disp_clear(COLOR_WHITE);
    disp_draw_text(60, 100, "Watch the backlight", COLOR_BLACK, COLOR_WHITE);
    disp_draw_text(80, 120, "toggle on/off", COLOR_BLACK, COLOR_WHITE);
    sleep_ms(1000);
    
    for (int i = 0; i < 5; i++) {
        printf("Backlight OFF\n");
        disp_set_backlight(false);
        sleep_ms(500);
        
        printf("Backlight ON\n");
        disp_set_backlight(true);
        sleep_ms(500);
        
        buttons_update();
        if (button_pressed(BUTTON_B)) {
            disp_set_backlight(true);
            return;
        }
    }
    
    printf("Backlight test complete\n");
}

// Button callbacks
void on_button_a(button_t b) {
    if (!test_running) {
        test_running = true;
        printf("\nStarting test: %s\n", test_names[current_test]);
    }
}

void on_button_x(button_t b) {
    if (!test_running) {
        if (current_test > 0) {
            current_test--;
            menu_changed = true;
            printf("Selected: %s\n", test_names[current_test]);
        }
    }
}

void on_button_y(button_t b) {
    if (!test_running) {
        if (current_test < TEST_COUNT - 1) {
            current_test++;
            menu_changed = true;
            printf("Selected: %s\n", test_names[current_test]);
        }
    }
}

int main() {
    stdio_init_all();
    sleep_ms(2000);
    
    printf("\n    DISPLAY API TESTER\n\n");
    
    // Init display
    disp_config_t cfg = disp_get_default_config();
    cfg.use_dma = true;
    cfg.spi_baudrate = 62500000;
    
    disp_error_t err = disp_init(&cfg);
    if (err != DISP_OK) {
        printf("Display init failed: %s\n", disp_error_string(err));
        return 1;
    }
    printf("Display initialized: 320x240 @ %lu Hz\n", (unsigned long)cfg.spi_baudrate);
    
    // Init buttons
    buttons_init();
    button_set_callback(BUTTON_A, on_button_a);
    button_set_callback(BUTTON_X, on_button_x);
    button_set_callback(BUTTON_Y, on_button_y);
    
    // Show splash
    disp_clear(COLOR_BLUE);
    disp_draw_text(70, 100, "API TESTER", COLOR_WHITE, COLOR_BLUE);
    disp_draw_text(85, 120, "Loading ..", COLOR_YELLOW, COLOR_BLUE);
    sleep_ms(1500);
    
    srand(12345);
    
    // Main loop
    while (1) {
        if (!test_running) {
            show_menu();
            menu_changed = false;
            
            // Wait for button press or menu change
            while (!test_running && !menu_changed) {
                buttons_update();
                sleep_ms(10);
            }
            
            // If menu changed (X/Y pressed), redraw and continue waiting
            if (menu_changed) {
                continue;
            }
            
            // A was pressed - wait for button release
            while (button_pressed(BUTTON_A)) {
                buttons_update();
                sleep_ms(10);
            }
            
            // Run selected test
            switch (current_test) {
                case TEST_COLORS:      test_colors(); break;
                case TEST_RECTANGLES:  test_rectangles(); break;
                case TEST_PIXELS:      test_pixels(); break;
                case TEST_TEXT:        test_text(); break;
                case TEST_BLIT:        test_blit(); break;
                case TEST_FRAMEBUFFER: test_framebuffer(); break;
                case TEST_BACKLIGHT:   test_backlight(); break;
            }
            
            // Wait for button release before returning to menu
            while (button_pressed(BUTTON_B)) {
                buttons_update();
                sleep_ms(10);
            }
            
            test_running = false;
            printf("\nReturning to menu ..\n");
            sleep_ms(500);
        }
    }
    
    return 0;
}
