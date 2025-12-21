#include "display.h"
#include "pico/stdlib.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

// Helper: Draw filled circle in framebuffer
void fb_draw_circle(uint16_t cx, uint16_t cy, uint16_t r, uint16_t color) {
    uint16_t *fb = disp_get_framebuffer();
    if (!fb) return;
    
    int r_sq = r * r;
    for (int y = -r; y <= r; y++) {
        int y_sq = y * y;
        for (int x = -r; x <= r; x++) {
            if (x*x + y_sq <= r_sq) { 
                int px = cx + x;
                int py = cy + y;
                if (px >= 0 && px < DISPLAY_WIDTH && py >= 0 && py < DISPLAY_HEIGHT) {
                    fb[py * DISPLAY_WIDTH + px] = color;
                }
            }
        }
    }
}

// Demo 1: Smooth bouncing ball
void demo_bouncing_ball(void) {
    printf("\n-- Smooth Bouncing Ball Demo --\n");
    
    // Allocate framebuffer
    if (disp_framebuffer_alloc() != DISP_OK) {
        printf("Failed to allocate framebuffer!\n");
        return;
    }
    
    float x = 160, y = 120;
    float vx = 3.5, vy = 2.8;
    uint16_t radius = 15;
    uint32_t frame = 0;
    
    uint32_t last_time = to_ms_since_boot(get_absolute_time());
    uint32_t last_fps_print = last_time;
    
    printf("Running.. any button to exit\n");
    
    // Wait for button release first
    while (button_pressed(BUTTON_A) || button_pressed(BUTTON_B) || 
           button_pressed(BUTTON_X) || button_pressed(BUTTON_Y)) {
        buttons_update();
        sleep_ms(10);
    }
    
    sleep_ms(200);  // Small delay to ensure clean state
    
    while (1) {
        buttons_update();
        
        // Check for ANY button press to exit
        if (button_just_pressed(BUTTON_A) || button_just_pressed(BUTTON_B) || 
            button_just_pressed(BUTTON_X) || button_just_pressed(BUTTON_Y)) {
            printf("Exiting bouncing ball\n");
            break;
        }
        
        // Clear framebuffer
        disp_framebuffer_clear(COLOR_BLACK);
        
        // Update physics
        x += vx;
        y += vy;
        
        if (x - radius < 0) {
            x = radius;
            vx = -vx;
        }
        if (x + radius >= DISPLAY_WIDTH) {
            x = DISPLAY_WIDTH - radius - 1;
            vx = -vx;
        }
        if (y - radius < 0) {
            y = radius;
            vy = -vy;
        }
        if (y + radius >= DISPLAY_HEIGHT) {
            y = DISPLAY_HEIGHT - radius - 1;
            vy = -vy;
        }
        
        // Draw ball with rainbow color
        uint16_t color = ((frame * 8) & 0x1F) << 11 | 
                        ((frame * 4) & 0x3F) << 5 | 
                        ((frame * 16) & 0x1F);
        fb_draw_circle((uint16_t)x, (uint16_t)y, radius, color);
        
        // Draw "trail" effect
        if (frame > 0) {
            fb_draw_circle((uint16_t)(x - vx), (uint16_t)(y - vy), radius/2, color >> 2);
        }
        
        // Flush to display (single DMA transfer!)
        disp_framebuffer_flush();
        
        frame++;
        
        // Calculate FPS every second
        uint32_t now = to_ms_since_boot(get_absolute_time());
        if (now - last_fps_print >= 1000) {
            float fps = frame * 1000.0f / (now - last_time);
            printf("FPS: %.1f\n", fps);
            last_fps_print = now;
        }
        
        sleep_ms(16);  // ~60 FPS target
    }
    
    disp_framebuffer_free();
}

// Demo 2: Plasma effect
void demo_plasma(void) {
    printf("\n-- Smooth Plasma Effect --\n");
    
    if (disp_framebuffer_alloc() != DISP_OK) {
        printf("Failed to allocate framebuffer!\n");
        return;
    }
    
    uint16_t *fb = disp_get_framebuffer();
    uint32_t frame = 0;
    uint32_t last_fps_print = to_ms_since_boot(get_absolute_time());
    
    printf("Running.. any button to exit\n");
    
    // Wait for button release first
    while (button_pressed(BUTTON_A) || button_pressed(BUTTON_B) || 
           button_pressed(BUTTON_X) || button_pressed(BUTTON_Y)) {
        buttons_update();
        sleep_ms(10);
    }
    
    sleep_ms(200);  // Small delay to ensure clean state
    
    while (1) {
        buttons_update();
        
        // Check for ANY button press to exit
        if (button_just_pressed(BUTTON_A) || button_just_pressed(BUTTON_B) || 
            button_just_pressed(BUTTON_X) || button_just_pressed(BUTTON_Y)) {
            printf("Exiting plasma\n");
            break;
        }
        
        float time = frame * 0.05f;
        
        // Generate plasma pattern
        for (int y = 0; y < DISPLAY_HEIGHT; y++) {
            for (int x = 0; x < DISPLAY_WIDTH; x++) {
                float fx = x / 40.0f;
                float fy = y / 40.0f;
                
                float v = sinf(fx + time) + 
                         sinf(fy + time) + 
                         sinf((fx + fy + time) * 0.5f) + 
                         sinf(sqrtf(fx*fx + fy*fy) + time);
                
                v = (v + 4.0f) / 8.0f;  // Normalize to 0-1
                
                uint8_t r = (uint8_t)(sinf(v * 6.28f) * 127 + 128);
                uint8_t g = (uint8_t)(sinf(v * 6.28f + 2.09f) * 127 + 128);
                uint8_t b = (uint8_t)(sinf(v * 6.28f + 4.18f) * 127 + 128);
                
                // Convert to RGB565
                uint16_t color = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3);
                fb[y * DISPLAY_WIDTH + x] = color;
            }
        }
        
        disp_framebuffer_flush();
        frame++;
        
        uint32_t now = to_ms_since_boot(get_absolute_time());
        if (now - last_fps_print >= 1000) {
            printf("Frame %lu\n", (unsigned long)frame);
            last_fps_print = now;
        }
    }
    
    disp_framebuffer_free();
}

// Demo 3: Starfield
void demo_starfield(void) {
    printf("\n-- Smooth Starfield Demo --\n");
    
    if (disp_framebuffer_alloc() != DISP_OK) {
        printf("Failed to allocate framebuffer!\n");
        return;
    }
    
    #define NUM_STARS 150
    struct {
        float x, y, z;
    } stars[NUM_STARS];
    
    // Init stars
    for (int i = 0; i < NUM_STARS; i++) {
        stars[i].x = (rand() % 2000) - 1000;
        stars[i].y = (rand() % 2000) - 1000;
        stars[i].z = rand() % 1000 + 1;
    }
    
    uint16_t *fb = disp_get_framebuffer();
    uint32_t frame = 0;
    uint32_t last_fps_print = to_ms_since_boot(get_absolute_time());
    
    printf("Running.. any button to exit\n");
    
    // Wait for button release first
    while (button_pressed(BUTTON_A) || button_pressed(BUTTON_B) || 
           button_pressed(BUTTON_X) || button_pressed(BUTTON_Y)) {
        buttons_update();
        sleep_ms(10);
    }
    
    sleep_ms(200);  // Small delay to ensure clean state
    
    while (1) {
        buttons_update();
        
        // Check for ANY button press to exit
        if (button_just_pressed(BUTTON_A) || button_just_pressed(BUTTON_B) || 
            button_just_pressed(BUTTON_X) || button_just_pressed(BUTTON_Y)) {
            printf("Exiting starfield\n");
            break;
        }
        
        disp_framebuffer_clear(0x0000);  // Black
        
        // Update and draw stars
        for (int i = 0; i < NUM_STARS; i++) {
            stars[i].z -= 8;
            if (stars[i].z <= 0) {
                stars[i].x = (rand() % 2000) - 1000;
                stars[i].y = (rand() % 2000) - 1000;
                stars[i].z = 1000;
            }
            
            // Project to screen
            float k = 128.0f / stars[i].z;
            int sx = (int)(stars[i].x * k) + DISPLAY_WIDTH / 2;
            int sy = (int)(stars[i].y * k) + DISPLAY_HEIGHT / 2;
            
            if (sx >= 0 && sx < DISPLAY_WIDTH && sy >= 0 && sy < DISPLAY_HEIGHT) {
                // Brightness based on distance
                uint8_t brightness = (uint8_t)(255 * (1.0f - stars[i].z / 1000.0f));
                uint16_t color = ((brightness >> 3) << 11) | 
                               ((brightness >> 2) << 5) | 
                               (brightness >> 3);
                
                // Draw star with size based on distance
                int size = 1 + (1000 - (int)stars[i].z) / 400;
                for (int dy = 0; dy < size; dy++) {
                    for (int dx = 0; dx < size; dx++) {
                        int px = sx + dx;
                        int py = sy + dy;
                        if (px < DISPLAY_WIDTH && py < DISPLAY_HEIGHT) {
                            fb[py * DISPLAY_WIDTH + px] = color;
                        }
                    }
                }
            }
        }
        
        disp_framebuffer_flush();
        frame++;
        
        uint32_t now = to_ms_since_boot(get_absolute_time());
        if (now - last_fps_print >= 1000) {
            printf("Frame %lu\n", (unsigned long)frame);
            last_fps_print = now;
        }
        
        sleep_ms(16);  // ~60 FPS
    }
    
    disp_framebuffer_free();
}

int main() {
    stdio_init_all();
    sleep_ms(2000);
    
    printf("  SMOOTH RENDERING DEMO\n");
    printf("  Using DMA + Framebuffer\n\n");
    
    // Init with DMA enabled
    disp_config_t cfg = disp_get_default_config();
    cfg.use_dma = true;
    cfg.spi_baudrate = 62500000;  // Maximum speed
    
    disp_error_t err = disp_init(&cfg);
    if (err != DISP_OK) {
        printf("Init failed: %s\n", disp_error_string(err));
        return 1;
    }
    
    buttons_init();
    
    // Show intro
    disp_clear(COLOR_BLACK);
    disp_draw_text(60, 100, "RENDERING DEMOS", COLOR_WHITE, COLOR_BLACK);
    disp_draw_text(60, 120, "Press any button", COLOR_CYAN, COLOR_BLACK);
    sleep_ms(2000);
    
    while (1) {
        disp_clear(COLOR_BLACK);
        disp_draw_text(80, 30,  "DEMO MENU", COLOR_WHITE, COLOR_BLACK);
        disp_draw_text(20, 70,  "A: Bouncing Ball", COLOR_GREEN, COLOR_BLACK);
        disp_draw_text(20, 90,  "B: Plasma Effect", COLOR_YELLOW, COLOR_BLACK);
        disp_draw_text(20, 110, "X: Starfield", COLOR_CYAN, COLOR_BLACK);
        disp_draw_text(20, 150, "Press a button to start!", COLOR_WHITE, COLOR_BLACK);
        
        printf("\n--- MENU: Press A/B/X to select demo ---\n");
        
        // Wait for ALL buttons to be released
        printf("Waiting for button release..\n");
        while (button_pressed(BUTTON_A) || button_pressed(BUTTON_B) || 
               button_pressed(BUTTON_X) || button_pressed(BUTTON_Y)) {
            buttons_update();
            sleep_ms(10);
        }
        
        // Small delay to ensure clean state
        sleep_ms(200);
        printf("Ready for input\n");
        
        // Now wait for a button press
        bool demo_selected = false;
        while (!demo_selected) {
            buttons_update();
            
            if (button_just_pressed(BUTTON_A)) {
                printf("\n>>> Starting bouncing ball demo <<<\n");
                sleep_ms(200);
                demo_bouncing_ball();
                demo_selected = true;
            }
            else if (button_just_pressed(BUTTON_B)) {
                printf("\n>>> Starting plasma demo <<<\n");
                sleep_ms(200);
                demo_plasma();
                demo_selected = true;
            }
            else if (button_just_pressed(BUTTON_X)) {
                printf("\n>>> Starting starfield demo <<<\n");
                sleep_ms(200);
                demo_starfield();
                demo_selected = true;
            }
            
            sleep_ms(10);
        }
        
        // Small delay after demo before returning to menu
        sleep_ms(300);
    }
    
    return 0;
}
