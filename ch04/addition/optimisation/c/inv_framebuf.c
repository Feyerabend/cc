/*
 * Space Invaders - Framebuffer Optimisation Demonstration
 * 
 * This demonstrates the REAL performance difference between:
 * - Drawing directly to display (slow, causes tearing)
 * - Using a framebuffer (fast, smooth)
 * 
 * Press Y to toggle between modes and see the difference!
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "display.h"

// Game constants
#define MAX_BULLETS 5
#define MAX_BOMBS 15
#define MAX_INVADERS 15
#define INVADER_ROWS 3
#define INVADER_COLS 5

// Rendering mode
typedef enum {
    RENDER_DIRECT,      // Draw directly to display (slow)
    RENDER_FRAMEBUFFER  // Use framebuffer (fast)
} render_mode_t;

static render_mode_t current_mode = RENDER_FRAMEBUFFER;
static uint32_t frame_count = 0;
static uint32_t fps = 0;
static uint32_t last_fps_time = 0;
static uint32_t frame_time_us = 0;

// Player
typedef struct {
    float x, y;
    int width, height;
    float speed;
} Player;

// Projectile
typedef struct {
    float x, y;
    bool active;
} Projectile;

// Invader
typedef struct {
    float x, y;
    int width, height;
    bool alive;
    uint16_t color;
} Invader;

// Game state
static Player player;
static Projectile bullets[MAX_BULLETS];
static Projectile bombs[MAX_BOMBS];
static Invader invaders[MAX_INVADERS];
static int invader_count = 0;
static float invader_speed = 1.0f;
static int invader_direction = 1;
static int move_counter = 0;
static bool game_over = false;
static bool win = false;

// Function prototypes
void init_game(void);
void update_game(void);
void render_direct(void);
void render_framebuffer(void);
void draw_invader_direct(Invader* inv);
void draw_invader_fb(Invader* inv);
bool check_collision(float x1, float y1, int w1, int h1, float x2, float y2, int w2, int h2);
void fire_bullet(void);
void fire_bomb(void);

// Initialize game
void init_game(void) {
    // Player setup
    player.x = DISPLAY_WIDTH / 2 - 10;
    player.y = DISPLAY_HEIGHT - 30;
    player.width = 20;
    player.height = 10;
    player.speed = 3.0f;
    
    // Clear projectiles
    memset(bullets, 0, sizeof(bullets));
    memset(bombs, 0, sizeof(bombs));
    
    // Create invaders
    invader_count = 0;
    for (int row = 0; row < INVADER_ROWS; row++) {
        for (int col = 0; col < INVADER_COLS; col++) {
            invaders[invader_count].x = 60 + col * 40;
            invaders[invader_count].y = 40 + row * 30;
            invaders[invader_count].width = 20;
            invaders[invader_count].height = 15;
            invaders[invader_count].alive = true;
            invaders[invader_count].color = (row == 0) ? COLOR_RED : COLOR_GREEN;
            invader_count++;
        }
    }
    
    game_over = false;
    win = false;
    move_counter = 0;
}

// Fire bullet
void fire_bullet(void) {
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!bullets[i].active) {
            bullets[i].x = player.x + player.width / 2;
            bullets[i].y = player.y;
            bullets[i].active = true;
            break;
        }
    }
}

// Fire bomb
void fire_bomb(void) {
    // Find a random alive invader
    int alive_indices[MAX_INVADERS];
    int alive_count = 0;
    
    for (int i = 0; i < invader_count; i++) {
        if (invaders[i].alive) {
            alive_indices[alive_count++] = i;
        }
    }
    
    if (alive_count == 0) return;
    
    int idx = alive_indices[rand() % alive_count];
    
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (!bombs[i].active) {
            bombs[i].x = invaders[idx].x + invaders[idx].width / 2;
            bombs[i].y = invaders[idx].y + invaders[idx].height;
            bombs[i].active = true;
            break;
        }
    }
}

// Collision check
bool check_collision(float x1, float y1, int w1, int h1, float x2, float y2, int w2, int h2) {
    return (x1 < x2 + w2 && x1 + w1 > x2 && y1 < y2 + h2 && y1 + h1 > y2);
}

// Update game logic
void update_game(void) {
    if (game_over || win) return;
    
    // Update bullets
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (bullets[i].active) {
            bullets[i].y -= 5.0f;
            if (bullets[i].y < 0) {
                bullets[i].active = false;
            }
        }
    }
    
    // Update bombs
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (bombs[i].active) {
            bombs[i].y += 3.0f;
            if (bombs[i].y > DISPLAY_HEIGHT) {
                bombs[i].active = false;
            }
        }
    }
    
    // Move invaders
    move_counter++;
    if (move_counter >= 30) {
        move_counter = 0;
        
        bool should_drop = false;
        
        // Check edge collision
        for (int i = 0; i < invader_count; i++) {
            if (invaders[i].alive) {
                if ((invader_direction > 0 && invaders[i].x + invaders[i].width >= DISPLAY_WIDTH - 10) ||
                    (invader_direction < 0 && invaders[i].x <= 10)) {
                    should_drop = true;
                    break;
                }
            }
        }
        
        if (should_drop) {
            invader_direction *= -1;
            for (int i = 0; i < invader_count; i++) {
                if (invaders[i].alive) {
                    invaders[i].y += 10;
                    if (invaders[i].y + invaders[i].height >= player.y) {
                        game_over = true;
                    }
                }
            }
        } else {
            for (int i = 0; i < invader_count; i++) {
                if (invaders[i].alive) {
                    invaders[i].x += invader_speed * invader_direction;
                }
            }
        }
        
        // Random bomb
        if (rand() % 100 < 20) {
            fire_bomb();
        }
    }
    
    // Bullet-invader collision
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!bullets[i].active) continue;
        
        for (int j = 0; j < invader_count; j++) {
            if (!invaders[j].alive) continue;
            
            if (check_collision(bullets[i].x, bullets[i].y, 2, 4,
                              invaders[j].x, invaders[j].y, 
                              invaders[j].width, invaders[j].height)) {
                bullets[i].active = false;
                invaders[j].alive = false;
                break;
            }
        }
    }
    
    // Bomb-player collision
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (bombs[i].active) {
            if (check_collision(bombs[i].x, bombs[i].y, 2, 4,
                              player.x, player.y, player.width, player.height)) {
                game_over = true;
            }
        }
    }
    
    // Check win
    bool any_alive = false;
    for (int i = 0; i < invader_count; i++) {
        if (invaders[i].alive) {
            any_alive = true;
            break;
        }
    }
    if (!any_alive) {
        win = true;
    }
}

// Draw invader - DIRECT mode
void draw_invader_direct(Invader* inv) {
    if (!inv->alive) return;
    
    // Simple rectangle representation
    disp_fill_rect(inv->x, inv->y, inv->width, inv->height, inv->color);
    
    // Draw "eyes"
    disp_fill_rect(inv->x + 4, inv->y + 3, 3, 3, COLOR_WHITE);
    disp_fill_rect(inv->x + inv->width - 7, inv->y + 3, 3, 3, COLOR_WHITE);
}

// Draw invader - FRAMEBUFFER mode
void draw_invader_fb(Invader* inv) {
    if (!inv->alive) return;
    
    // Simple rectangle representation
    disp_framebuffer_fill_rect(inv->x, inv->y, inv->width, inv->height, inv->color);
    
    // Draw "eyes"
    disp_framebuffer_fill_rect(inv->x + 4, inv->y + 3, 3, 3, COLOR_WHITE);
    disp_framebuffer_fill_rect(inv->x + inv->width - 7, inv->y + 3, 3, 3, COLOR_WHITE);
}

// Render using DIRECT mode (slow)
void render_direct(void) {
    uint32_t start = time_us_32();
    
    // Clear screen - this alone is slow!
    disp_clear(COLOR_BLACK);
    
    // Draw player
    disp_fill_rect(player.x, player.y, player.width, player.height, COLOR_WHITE);
    
    // Draw invaders
    for (int i = 0; i < invader_count; i++) {
        draw_invader_direct(&invaders[i]);
    }
    
    // Draw bullets
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (bullets[i].active) {
            disp_fill_rect(bullets[i].x, bullets[i].y, 2, 4, COLOR_YELLOW);
        }
    }
    
    // Draw bombs
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (bombs[i].active) {
            disp_fill_rect(bombs[i].x, bombs[i].y, 2, 4, COLOR_RED);
        }
    }
    
    // Draw UI
    char buf[64];
    snprintf(buf, sizeof(buf), "DIRECT MODE - %lu FPS", fps);
    disp_draw_text(5, 5, buf, COLOR_YELLOW, COLOR_BLACK);
    
    snprintf(buf, sizeof(buf), "Frame: %lu us", frame_time_us);
    disp_draw_text(5, 15, buf, COLOR_YELLOW, COLOR_BLACK);
    
    disp_draw_text(5, 225, "Press Y to toggle mode", COLOR_CYAN, COLOR_BLACK);
    
    if (game_over) {
        disp_draw_text(DISPLAY_WIDTH/2 - 30, DISPLAY_HEIGHT/2, "GAME OVER", COLOR_RED, COLOR_BLACK);
    } else if (win) {
        disp_draw_text(DISPLAY_WIDTH/2 - 24, DISPLAY_HEIGHT/2, "YOU WIN!", COLOR_GREEN, COLOR_BLACK);
    }
    
    frame_time_us = time_us_32() - start;
}

// Render using FRAMEBUFFER mode (fast)
void render_framebuffer(void) {
    uint32_t start = time_us_32();
    
    // Clear framebuffer - fast in-memory operation
    disp_framebuffer_clear(COLOR_BLACK);
    
    // Draw player
    disp_framebuffer_fill_rect(player.x, player.y, player.width, player.height, COLOR_WHITE);
    
    // Draw invaders
    for (int i = 0; i < invader_count; i++) {
        draw_invader_fb(&invaders[i]);
    }
    
    // Draw bullets
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (bullets[i].active) {
            disp_framebuffer_fill_rect(bullets[i].x, bullets[i].y, 2, 4, COLOR_YELLOW);
        }
    }
    
    // Draw bombs
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (bombs[i].active) {
            disp_framebuffer_fill_rect(bombs[i].x, bombs[i].y, 2, 4, COLOR_RED);
        }
    }
    
    // Draw UI
    char buf[64];
    snprintf(buf, sizeof(buf), "FRAMEBUFFER - %lu FPS", fps);
    disp_framebuffer_draw_text(5, 5, buf, COLOR_YELLOW, COLOR_BLACK);
    
    snprintf(buf, sizeof(buf), "Frame: %lu us", frame_time_us);
    disp_framebuffer_draw_text(5, 15, buf, COLOR_YELLOW, COLOR_BLACK);
    
    disp_framebuffer_draw_text(5, 225, "Press Y to toggle mode", COLOR_CYAN, COLOR_BLACK);
    
    if (game_over) {
        disp_framebuffer_draw_text(DISPLAY_WIDTH/2 - 30, DISPLAY_HEIGHT/2, "GAME OVER", COLOR_RED, COLOR_BLACK);
    } else if (win) {
        disp_framebuffer_draw_text(DISPLAY_WIDTH/2 - 24, DISPLAY_HEIGHT/2, "YOU WIN!", COLOR_GREEN, COLOR_BLACK);
    }
    
    // Flush to display - ONE fast DMA transfer
    disp_framebuffer_flush();
    
    frame_time_us = time_us_32() - start;
}

// Main
int main() {
    stdio_init_all();
    
    // Initialize display with default config (DMA enabled)
    disp_config_t config = disp_get_default_config();
    if (disp_init(&config) != DISP_OK) {
        printf("Display init failed!\n");
        return 1;
    }
    
    // Initialize buttons
    buttons_init();
    
    // Allocate framebuffer
    if (disp_framebuffer_alloc() != DISP_OK) {
        printf("Framebuffer allocation failed!\n");
        return 1;
    }
    
    init_game();
    
    printf("Space Invaders - Framebuffer Demo\n");
    printf("Controls:\n");
    printf("  A/B - Move left/right\n");
    printf("  X - Fire\n");
    printf("  Y - Toggle render mode\n");
    
    last_fps_time = time_us_32();
    
    while (true) {
        // Update buttons
        buttons_update();
        
        // Handle input
        if (button_pressed(BUTTON_A) && player.x > 0) {
            player.x -= player.speed;
        }
        if (button_pressed(BUTTON_B) && player.x < DISPLAY_WIDTH - player.width) {
            player.x += player.speed;
        }
        if (button_just_pressed(BUTTON_X)) {
            fire_bullet();
        }
        if (button_just_pressed(BUTTON_Y)) {
            // Toggle mode
            current_mode = (current_mode == RENDER_DIRECT) ? RENDER_FRAMEBUFFER : RENDER_DIRECT;
            printf("Switched to %s mode\n", 
                   current_mode == RENDER_DIRECT ? "DIRECT" : "FRAMEBUFFER");
        }
        
        // Reset game
        if ((game_over || win) && button_just_pressed(BUTTON_X)) {
            init_game();
        }
        
        // Update game logic
        update_game();
        
        // Render based on current mode
        if (current_mode == RENDER_DIRECT) {
            render_direct();
        } else {
            render_framebuffer();
        }
        
        // FPS calculation
        frame_count++;
        uint32_t now = time_us_32();
        if (now - last_fps_time >= 1000000) {
            fps = frame_count;
            frame_count = 0;
            last_fps_time = now;
            
            printf("FPS: %lu, Frame time: %lu us, Mode: %s\n", 
                   fps, frame_time_us,
                   current_mode == RENDER_DIRECT ? "DIRECT" : "FRAMEBUFFER");
        }
        
        sleep_ms(16); // ~60 FPS target
    }
    
    return 0;
}
