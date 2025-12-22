#include <stdio.h>
#include <ctype.h>
#include <string.h>
#include "pico/stdlib.h"
#include "display.h"

// Ultra-minimal settings
#define TEXT_BUFFER_SIZE 512   // Even smaller buffer
#define MAX_LINE_LENGTH 32     // Limit line length
#define FONT_WIDTH 6
#define FONT_HEIGHT 8
#define SCREEN_CHARS_WIDTH (DISPLAY_WIDTH / FONT_WIDTH)
#define SCREEN_LINES (DISPLAY_HEIGHT / FONT_HEIGHT)
#define TEXT_LINES (SCREEN_LINES - 3)  // More space for status
#define CURSOR_BLINK_MS 1000           // Slower blink

// Simple static buffers - no complex structures
static char text_buffer[TEXT_BUFFER_SIZE];
static char display_line[SCREEN_CHARS_WIDTH + 1];
static uint16_t text_length = 0;
static uint16_t cursor_pos = 0;
static bool cursor_visible = true;
static bool needs_redraw = true;
static uint32_t last_blink = 0;
static uint32_t last_display_check = 0;
static bool display_ok = false;
static uint32_t error_count = 0;

// Get current time in milliseconds
static inline uint32_t get_time_ms(void) {
    return to_ms_since_boot(get_absolute_time());
}

// Init everything
static bool editor_init(void) {
    printf("Editor init starting..\n");
    
    // Clear all buffers
    memset(text_buffer, 0, sizeof(text_buffer));
    memset(display_line, 0, sizeof(display_line));
    
    text_length = 0;
    cursor_pos = 0;
    cursor_visible = true;
    needs_redraw = true;
    last_blink = get_time_ms();
    last_display_check = get_time_ms();
    error_count = 0;
    
    printf("Editor init complete\n");
    return true;
}

// Check display health
static bool check_display(void) {
    uint32_t now = get_time_ms();
    if (now - last_display_check < 5000) return display_ok; // Check every 5 seconds
    
    last_display_check = now;
    
    if (!display_is_initialized()) {
        printf("Display not init, attempting reinit..\n");
        display_error_t err = display_pack_init();
        display_ok = (err == DISPLAY_OK);
        if (!display_ok) {
            printf("Display reinit failed: %d\n", err);
            error_count++;
        }
    } else {
        display_ok = true;
    }
    
    return display_ok;
}

// Safe character insertion
static void insert_char(char c) {
    if (text_length >= TEXT_BUFFER_SIZE - 2) {
        return;
    }
    
    if (cursor_pos > text_length) {
        cursor_pos = text_length;
    }
    
    // Shift text right
    for (uint16_t i = text_length; i > cursor_pos; i--) {
        text_buffer[i] = text_buffer[i - 1];
    }
    
    text_buffer[cursor_pos] = c;
    cursor_pos++;
    text_length++;
    text_buffer[text_length] = '\0';
    needs_redraw = true;
}

// Safe character deletion
static void delete_char(void) {
    if (cursor_pos == 0 || text_length == 0) return;
    
    cursor_pos--;
    
    // Shift text left
    for (uint16_t i = cursor_pos; i < text_length - 1; i++) {
        text_buffer[i] = text_buffer[i + 1];
    }
    
    text_length--;
    text_buffer[text_length] = '\0';
    needs_redraw = true;
}

// Move cursor safely
static void move_cursor_left(void) {
    if (cursor_pos > 0) {
        cursor_pos--;
        needs_redraw = true;
    }
}

static void move_cursor_right(void) {
    if (cursor_pos < text_length) {
        cursor_pos++;
        needs_redraw = true;
    }
}

// Simple render - just one line at a time to avoid complexity
static bool render_simple(void) {
    if (!check_display()) {
        return false;
    }
    
    // Clear screen first
    display_error_t err = display_clear(COLOR_BLACK);
    if (err != DISPLAY_OK) {
        display_ok = false;
        return false;
    }
    
    // Draw text - simple approach, just show what we can
    uint8_t screen_x = 0;
    uint8_t screen_y = 0;
    
    // DEBUG: Draw some test text first to see if character drawing works
    display_draw_string(0, 0, "EDITOR", COLOR_RED, COLOR_BLACK);
    
    // Start drawing actual text from line 1
    screen_y = 1;
    screen_x = 0;
    
    for (uint16_t i = 0; i < text_length && screen_y < TEXT_LINES; i++) {
        char c = text_buffer[i];
        
        if (c == '\n') {
            screen_y++;
            screen_x = 0;
        } else if (c >= 32 && c < 127 && screen_x < SCREEN_CHARS_WIDTH) {
            char display_char = (c >= 'a' && c <= 'z') ? (c - 32) : c;
            err = display_draw_char(screen_x * FONT_WIDTH, screen_y * FONT_HEIGHT, 
                                   display_char, COLOR_WHITE, COLOR_BLACK);
            if (err != DISPLAY_OK) {
                display_ok = false;
                return false;
            }
            screen_x++;
        }
    }
    
    // Calculate cursor screen position (adjust for test line)
    uint8_t cursor_screen_x = 0;
    uint8_t cursor_screen_y = 1; // Start from line 1 because of TEST
    
    for (uint16_t i = 0; i < cursor_pos && i < text_length; i++) {
        if (text_buffer[i] == '\n') {
            cursor_screen_y++;
            cursor_screen_x = 0;
        } else {
            cursor_screen_x++;
        }
    }
    
    // If no text, cursor should be at start of line 1
    if (text_length == 0) {
        cursor_screen_x = 0;
        cursor_screen_y = 1;
    }
    
    // Draw cursor
    if (cursor_visible && cursor_screen_y < TEXT_LINES && cursor_screen_x < SCREEN_CHARS_WIDTH) {
        err = display_fill_rect(cursor_screen_x * FONT_WIDTH, cursor_screen_y * FONT_HEIGHT,
                               3, FONT_HEIGHT, COLOR_WHITE);
        if (err != DISPLAY_OK) {
            display_ok = false;
            return false;
        }
    }
    
    // Draw status bar
    uint16_t status_y = TEXT_LINES * FONT_HEIGHT;
    err = display_fill_rect(0, status_y, DISPLAY_WIDTH, FONT_HEIGHT, COLOR_BLUE);
    if (err != DISPLAY_OK) {
        display_ok = false;
        return false;
    }
    
    // Status text
    memset(display_line, 0, sizeof(display_line));
    snprintf(display_line, sizeof(display_line) - 1, "P:%d L:%d E:%d", 
             cursor_pos, text_length, error_count);
    
    err = display_draw_string(0, status_y, display_line, COLOR_WHITE, COLOR_BLUE);
    if (err != DISPLAY_OK) {
        display_ok = false;
        return false;
    }
    
    // Help line
    err = display_draw_string(0, status_y + FONT_HEIGHT, "A:DEBUG B:CLEAR - TYPE TEXT ABOVE", 
                             COLOR_GREEN, COLOR_BLACK);
    if (err != DISPLAY_OK) {
        display_ok = false;
        return false;
    }
    
    return true;
}

// Handle input
static void handle_input(void) {
    int c = getchar_timeout_us(0);
    if (c == PICO_ERROR_TIMEOUT) return;
    
    // Handle escape sequences
    if (c == 0x1B) {
        int next1 = getchar_timeout_us(1000);
        if (next1 == '[') {
            int next2 = getchar_timeout_us(1000);
            switch (next2) {
                case 'C': move_cursor_right(); break;
                case 'D': move_cursor_left(); break;
            }
        }
        return;
    }
    
    // Handle keys
    switch (c) {
        case 0x7F:
        case 0x08:
            delete_char();
            break;
        case '\r':
        case '\n':
            insert_char('\n');
            break;
        default:
            if (c >= 32 && c < 127) {
                insert_char((char)c);
            }
            break;
    }
}

// Button handlers
static void handle_button_a(button_t button) {
    // Show debug info instead of clearing
    printf("\n--- DEBUG INFO ---\n");
    printf("Text length: %d\n", text_length);
    printf("Cursor pos: %d\n", cursor_pos);
    printf("Display OK: %d\n", display_ok);
    printf("Error count: %d\n", error_count);
    printf("Buffer content: '");
    for (int i = 0; i < text_length && i < 50; i++) {
        if (text_buffer[i] >= 32 && text_buffer[i] < 127) {
            printf("%c", text_buffer[i]);
        } else {
            printf("[%d]", text_buffer[i]);
        }
    }
    printf("'\n");
    printf("---------------------\n\n");
    
    // Force a redraw to test
    needs_redraw = true;
}


// Add button B for clearing
static void handle_button_b(button_t button) {
    memset(text_buffer, 0, sizeof(text_buffer));
    text_length = 0;
    cursor_pos = 0;
    needs_redraw = true;
}

// Main function
int main() {
    stdio_init_all();
    printf("- SIMPLE TEXT EDITOR STARTING -\n");
    
    // Initialize display with retries
    display_error_t disp_err = DISPLAY_ERROR_INIT_FAILED;
    for (int retry = 0; retry < 3; retry++) {
        printf("Display init attempt %d..\n", retry + 1);
        disp_err = display_pack_init();
        if (disp_err == DISPLAY_OK) {
            display_ok = true;
            break;
        }
        printf("Display init failed: %d, retrying...\n", disp_err);
        sleep_ms(1000);
    }
    
    if (disp_err != DISPLAY_OK) {
        printf("FATAL: Cannot initialize display after 3 attempts\n");
        while (1) {
            sleep_ms(1000);
            printf("Display failed\n");
        }
    }
    
    printf("Display OK\n");
    
    // Init buttons
    display_error_t btn_err = buttons_init();
    if (btn_err == DISPLAY_OK) {
        button_set_callback(BUTTON_A, handle_button_a);
        button_set_callback(BUTTON_B, handle_button_b);
        printf("Buttons OK\n");
    } else {
        printf("Buttons failed: %d\n", btn_err);
    }
    
    // Init editor
    if (!editor_init()) {
        printf("Editor init failed\n");
        return 1;
    }
    
    printf("-- EDITOR READY --\n");
    printf("Type characters, use backspace, arrow keys\n");
    printf("Button A clears text\n");
    
    // Initial render
    if (!render_simple()) {
        printf("Initial render failed\n");
    }
    needs_redraw = false;
    
    // Main loop
    uint32_t loop_count = 0;
    uint32_t last_health_check = 0;
    
    while (1) {
        loop_count++;
        uint32_t now = get_time_ms();
        
        // Health check every 30 seconds
        if (now - last_health_check > 30000) {
            last_health_check = now;
            
            // Force display check
            check_display();
        }
        
        // Update buttons
        if (btn_err == DISPLAY_OK) {
            buttons_update();
        }
        
        // Handle input
        handle_input();
        
        // Handle cursor blink
        if (now - last_blink > CURSOR_BLINK_MS) {
            cursor_visible = !cursor_visible;
            last_blink = now;
            needs_redraw = true;
        }
        
        // Render if needed
        if (needs_redraw) {
            if (render_simple()) {
                needs_redraw = false;
            } else {
                error_count++;
                
                // If too many errors, try display reinit
                if (error_count > 10) {
                    printf("Display recovery attempt..\n");
                    display_cleanup();
                    sleep_ms(500);
                    disp_err = display_pack_init();
                    if (disp_err == DISPLAY_OK) {
                        display_ok = true;
                        error_count = 0;
                    }
                }
            }
        }
        
        // Wait for display
        if (display_dma_busy()) {
            display_wait_for_dma();
        }
        
        sleep_ms(50); // Slow loop for stability
    }
    
    return 0;
}
