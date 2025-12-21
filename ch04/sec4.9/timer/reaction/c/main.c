#include "pico/stdlib.h"
#include "display.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// LED pin (backlight can be used as indicator)
#define LED_PIN PIN_BL

// Game states
typedef enum {
    STATE_INSTRUCTIONS,  // Show instructions
    STATE_GET_READY,     // Countdown 3-2-1
    STATE_WAITING,       // Red LED - WAIT
    STATE_GO,            // Green LED - GO!
    STATE_RESULT,        // Show your time
    STATE_FALSE_START    // Pressed too early
} game_state_t;

// Game variables
static game_state_t state = STATE_INSTRUCTIONS;
static uint32_t state_start_time = 0;
static uint32_t reaction_start_time = 0;
static uint32_t last_reaction_time = 0;
static uint32_t best_time = 999999;
static uint32_t worst_time = 0;
static int attempt_count = 0;
static uint32_t total_time = 0;
static uint32_t wait_duration = 0;

// Visual
static uint16_t *fb = NULL;

// Helper: Draw centered text
static void draw_text_centered(uint16_t y, const char *text, uint16_t color) {
    int len = strlen(text);
    uint16_t x = (DISPLAY_WIDTH - len * 6) / 2;
    disp_framebuffer_draw_text(x, y, text, color, COLOR_BLACK);
}

// Helper: Draw GIANT number
static void draw_giant_number(char digit, uint16_t color) {
    // Simple style digit patterns
    // Each digit is drawn as large filled rectangles
    
    uint16_t cx = DISPLAY_WIDTH / 2;
    uint16_t cy = DISPLAY_HEIGHT / 2;
    uint16_t seg_width = 80;
    uint16_t seg_height = 20;
    uint16_t seg_spacing = 90;
    
    // Clear center area
    disp_framebuffer_fill_rect(cx - 100, cy - 110, 200, 220, COLOR_BLACK);
    
    switch(digit) {
        case '3':
            // Top horizontal
            disp_framebuffer_fill_rect(cx - seg_width/2, cy - seg_spacing, seg_width, seg_height, color);
            // Middle horizontal
            disp_framebuffer_fill_rect(cx - seg_width/2, cy - seg_height/2, seg_width, seg_height, color);
            // Bottom horizontal
            disp_framebuffer_fill_rect(cx - seg_width/2, cy + seg_spacing - seg_height, seg_width, seg_height, color);
            // Right top vertical
            disp_framebuffer_fill_rect(cx + seg_width/2 - seg_height, cy - seg_spacing, seg_height, seg_spacing, color);
            // Right bottom vertical
            disp_framebuffer_fill_rect(cx + seg_width/2 - seg_height, cy, seg_height, seg_spacing, color);
            break;
            
        case '2':
            // Top horizontal
            disp_framebuffer_fill_rect(cx - seg_width/2, cy - seg_spacing, seg_width, seg_height, color);
            // Middle horizontal
            disp_framebuffer_fill_rect(cx - seg_width/2, cy - seg_height/2, seg_width, seg_height, color);
            // Bottom horizontal
            disp_framebuffer_fill_rect(cx - seg_width/2, cy + seg_spacing - seg_height, seg_width, seg_height, color);
            // Right top vertical
            disp_framebuffer_fill_rect(cx + seg_width/2 - seg_height, cy - seg_spacing, seg_height, seg_spacing, color);
            // Left bottom vertical
            disp_framebuffer_fill_rect(cx - seg_width/2, cy, seg_height, seg_spacing, color);
            break;
            
        case '1':
            // Right top vertical
            disp_framebuffer_fill_rect(cx + seg_width/2 - seg_height, cy - seg_spacing, seg_height, seg_spacing, color);
            // Right bottom vertical
            disp_framebuffer_fill_rect(cx + seg_width/2 - seg_height, cy, seg_height, seg_spacing, color);
            break;
            
        case 'G':
            // Draw "GO!"
            disp_framebuffer_fill_rect(cx - 90, cy - 80, 180, 160, color);
            // Cut out letters in black
            draw_text_centered(cy - 20, "GO!", COLOR_BLACK);
            // Actually draw GO bigger
            for (int dy = 0; dy < 8; dy++) {
                for (int dx = 0; dx < 8; dx++) {
                    disp_framebuffer_draw_text(cx - 45 + dx*2, cy - 30 + dy*4, "GO!", COLOR_BLACK, color);
                }
            }
            break;
    }
}

// Helper: Draw progress dots (showing which attempt)
static void draw_progress_dots(void) {
    uint16_t dot_y = 10;
    uint16_t dot_size = 10;
    uint16_t spacing = 20;
    uint16_t start_x = (DISPLAY_WIDTH - (5 * spacing)) / 2;
    
    for (int i = 0; i < 5; i++) {
        uint16_t color = (i < attempt_count) ? COLOR_GREEN : COLOR_WHITE;
        disp_framebuffer_fill_rect(start_x + i * spacing, dot_y, dot_size, dot_size, color);
    }
}

// Draw instructions screen
static void draw_instructions(void) {
    disp_framebuffer_clear(COLOR_BLACK);
    
    draw_text_centered(30, "REACTION SPEED TEST", COLOR_CYAN);
    disp_framebuffer_fill_rect(40, 48, 240, 3, COLOR_CYAN);
    
    disp_framebuffer_draw_text(30, 70, "HOW TO PLAY:", COLOR_YELLOW, COLOR_BLACK);
    
    disp_framebuffer_draw_text(30, 95, "1. Screen will turn RED", COLOR_RED, COLOR_BLACK);
    disp_framebuffer_draw_text(45, 110, "= WAIT! Don't press!", COLOR_WHITE, COLOR_BLACK);
    
    disp_framebuffer_draw_text(30, 135, "2. When it turns GREEN", COLOR_GREEN, COLOR_BLACK);
    disp_framebuffer_draw_text(45, 150, "= Press A FAST!", COLOR_WHITE, COLOR_BLACK);
    
    disp_framebuffer_fill_rect(30, 175, 260, 2, COLOR_WHITE);
    
    disp_framebuffer_draw_text(30, 185, "The LED will show:", COLOR_YELLOW, COLOR_BLACK);
    disp_framebuffer_draw_text(40, 200, "OFF = Waiting for red", COLOR_WHITE, COLOR_BLACK);
    disp_framebuffer_draw_text(40, 213, "ON  = GO! Press now!", COLOR_GREEN, COLOR_BLACK);
    
    draw_text_centered(230, ">>> Press A to START <<<", COLOR_GREEN);
    
    disp_framebuffer_flush();
}

// Draw countdown screen (3...2...1...)
static void draw_countdown(uint32_t now) {
    disp_framebuffer_clear(COLOR_BLACK);
    
    uint32_t elapsed = now - state_start_time;
    uint32_t countdown_num = 3 - (elapsed / 1000);  // 3, 2, 1
    
    draw_progress_dots();
    
    if (countdown_num >= 1 && countdown_num <= 3) {
        char digit = '0' + countdown_num;
        
        // Draw GIANT countdown number
        draw_giant_number(digit, COLOR_YELLOW);
        
        draw_text_centered(200, "Get your finger ready...", COLOR_WHITE);
    }
    
    disp_framebuffer_flush();
}

// Draw waiting screen (RED - don't press yet!)
static void draw_waiting(void) {
    // Simple full-screen RED
    disp_framebuffer_clear(COLOR_RED);
    
    // Just one big message in center
    draw_text_centered(110, "WAIT...", COLOR_WHITE);
    
    disp_framebuffer_flush();
}

// Draw GO screen (GREEN - press now!)
static void draw_go(void) {
    // Simple full-screen GREEN
    disp_framebuffer_clear(COLOR_GREEN);
    
    // Just one big message
    draw_text_centered(110, "GO!", COLOR_BLACK);
    
    disp_framebuffer_flush();
}

// Draw result screen
static void draw_result(void) {
    disp_framebuffer_clear(COLOR_BLACK);
    
    draw_progress_dots();
    
    // Color code the result
    uint16_t result_color;
    const char *rating;
    
    if (last_reaction_time < 200) {
        result_color = COLOR_GREEN;
        rating = "AMAZING!";
    } else if (last_reaction_time < 250) {
        result_color = COLOR_CYAN;
        rating = "EXCELLENT!";
    } else if (last_reaction_time < 300) {
        result_color = COLOR_YELLOW;
        rating = "GREAT!";
    } else if (last_reaction_time < 400) {
        result_color = COLOR_YELLOW;
        rating = "GOOD";
    } else {
        result_color = COLOR_RED;
        rating = "SLOW - TRY AGAIN";
    }
    
    draw_text_centered(40, "YOUR TIME:", COLOR_WHITE);
    
    // Draw time clearly - just once, large but readable
    char time_str[16];
    snprintf(time_str, sizeof(time_str), "%lu ms", last_reaction_time);
    
    // Draw at 3x size by repeating horizontally and vertically  
    int len = strlen(time_str);
    uint16_t base_x = (DISPLAY_WIDTH - len * 6 * 3) / 2;
    uint16_t base_y = 75;
    
    for (int dy = 0; dy < 3; dy++) {
        for (int dx = 0; dx < 3; dx++) {
            disp_framebuffer_draw_text(base_x + dx, base_y + dy, time_str, result_color, COLOR_BLACK);
        }
    }
    
    draw_text_centered(115, rating, result_color);
    
    // Statistics
    disp_framebuffer_fill_rect(20, 145, 280, 2, COLOR_WHITE);
    
    char buf[32];
    snprintf(buf, sizeof(buf), "Best:  %lums", best_time);
    disp_framebuffer_draw_text(60, 160, buf, COLOR_GREEN, COLOR_BLACK);
    
    if (attempt_count > 1) {
        snprintf(buf, sizeof(buf), "Avg:   %lums", total_time / attempt_count);
        disp_framebuffer_draw_text(60, 175, buf, COLOR_CYAN, COLOR_BLACK);
    }
    
    if (attempt_count < 5) {
        draw_text_centered(205, "Press A - Next round", COLOR_WHITE);
        draw_text_centered(220, "Press B - Restart", COLOR_YELLOW);
    } else {
        disp_framebuffer_fill_rect(20, 195, 280, 2, COLOR_YELLOW);
        draw_text_centered(205, "TEST COMPLETE!", COLOR_YELLOW);
        draw_text_centered(220, "Press B to restart", COLOR_GREEN);
    }
    
    disp_framebuffer_flush();
}

// Draw false start screen
static void draw_false_start(void) {
    disp_framebuffer_clear(COLOR_RED);
    
    draw_progress_dots();
    
    // Big X pattern
    for (int i = 0; i < 150; i += 10) {
        disp_framebuffer_fill_rect(85 + i, 70 + i, 15, 15, COLOR_WHITE);
        disp_framebuffer_fill_rect(235 - i, 70 + i, 15, 15, COLOR_WHITE);
    }
    
    draw_text_centered(80, "FALSE START!", COLOR_YELLOW);
    draw_text_centered(180, "TOO EARLY!", COLOR_WHITE);
    draw_text_centered(200, "Wait for GREEN light!", COLOR_YELLOW);
    
    draw_text_centered(225, "Press A to try again", COLOR_WHITE);
    
    disp_framebuffer_flush();
}

// Control LED based on state
static void update_led(void) {
    switch (state) {
        case STATE_GO:
            // LED ON when it's time to press
            disp_set_backlight(true);
            break;
            
        case STATE_WAITING:
            // LED OFF during waiting (red light)
            disp_set_backlight(false);
            break;
            
        default:
            // LED ON for other states (instructions, countdown, results)
            disp_set_backlight(true);
            break;
    }
}

// Button A callback
static void button_a_pressed(button_t button) {
    uint32_t now = to_ms_since_boot(get_absolute_time());
    
    switch (state) {
        case STATE_INSTRUCTIONS:
            // Start the game
            state = STATE_GET_READY;
            state_start_time = now;
            attempt_count = 0;
            best_time = 999999;
            worst_time = 0;
            total_time = 0;
            draw_countdown(now);
            update_led();
            break;
            
        case STATE_WAITING:
            // Pressed too early!
            state = STATE_FALSE_START;
            state_start_time = now;
            draw_false_start();
            update_led();
            break;
            
        case STATE_GO:
            // Good press! Calculate reaction time
            last_reaction_time = now - reaction_start_time;
            
            // Update statistics
            attempt_count++;
            total_time += last_reaction_time;
            if (last_reaction_time < best_time) {
                best_time = last_reaction_time;
            }
            if (last_reaction_time > worst_time) {
                worst_time = last_reaction_time;
            }
            
            state = STATE_RESULT;
            state_start_time = now;
            draw_result();
            update_led();
            break;
            
        case STATE_RESULT:
            if (attempt_count < 5) {
                // Next round
                state = STATE_GET_READY;
                state_start_time = now;
                draw_countdown(now);
                update_led();
            }
            break;
            
        case STATE_FALSE_START:
            // Try again after false start
            state = STATE_GET_READY;
            state_start_time = now;
            draw_countdown(now);
            update_led();
            break;
            
        default:
            break;
    }
}

// Button B callback - reset/restart
static void button_b_pressed(button_t button) {
    state = STATE_INSTRUCTIONS;
    state_start_time = to_ms_since_boot(get_absolute_time());
    draw_instructions();
    update_led();
}

int main() {
    stdio_init_all();
    sleep_ms(1000);
    
    printf("=== Reaction Timer Game ===\n");
    
    // Initialize display
    disp_config_t config = disp_get_default_config();
    disp_error_t err = disp_init(&config);
    
    if (err != DISP_OK) {
        printf("Display init failed: %s\n", disp_error_string(err));
        return 1;
    }
    
    // Allocate framebuffer
    err = disp_framebuffer_alloc();
    if (err != DISP_OK) {
        printf("Framebuffer alloc failed\n");
        disp_deinit();
        return 1;
    }
    
    fb = disp_get_framebuffer();
    
    // Initialize buttons
    buttons_init();
    button_set_callback(BUTTON_A, button_a_pressed);
    button_set_callback(BUTTON_B, button_b_pressed);
    
    // Seed random
    srand(to_ms_since_boot(get_absolute_time()));
    
    printf("Game started\n");
    
    // Show instructions
    draw_instructions();
    update_led();
    
    uint32_t last_update = 0;
    
    while (true) {
        uint32_t now = to_ms_since_boot(get_absolute_time());
        
        // Update buttons
        buttons_update();
        
        // State machine updates
        if (now - last_update >= 16) {
            last_update = now;
            
            switch (state) {
                case STATE_GET_READY: {
                    uint32_t elapsed = now - state_start_time;
                    
                    if (elapsed >= 3000) {
                        // Countdown finished, enter waiting state
                        state = STATE_WAITING;
                        state_start_time = now;
                        // Random wait time (2-5 seconds)
                        wait_duration = (rand() % 3000) + 2000;
                        draw_waiting();
                        update_led();
                    } else {
                        // Update countdown display every second
                        static uint32_t last_second = 999;
                        uint32_t current_second = elapsed / 1000;
                        if (current_second != last_second) {
                            last_second = current_second;
                            draw_countdown(now);
                        }
                    }
                    break;
                }
                
                case STATE_WAITING: {
                    // Wait for random duration then go green
                    uint32_t elapsed = now - state_start_time;
                    
                    if (elapsed >= wait_duration) {
                        state = STATE_GO;
                        reaction_start_time = now;
                        draw_go();
                        update_led();
                    }
                    break;
                }
                
                default:
                    break;
            }
        }
        
        sleep_ms(1);
    }
    
    disp_deinit();
    return 0;
}
