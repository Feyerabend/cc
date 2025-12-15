/*
 * Space Invaders - In-Game Algorithm Comparison
 * 
 * This shorter version keeps some of the game but
 * allows switching collision detection *algorithms*
 * on-the-fly to show *performance* difference.
 * 
 * It is not suppose to compare against the other
 * codes in full detail, but give a quick idea!
 * Your mission is to make a project go further
 * from this starting point.
 * 
 * Press Y to toggle: Simple vs Spatial Grid
 * 
 * The profiler here is PART OF THE GAME,
 * not a separate tool.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "display.h"

// Collision detection modes
typedef enum {
    COLLISION_SIMPLE,      // n^2 brute force
    COLLISION_SPATIAL_GRID // Spatial grid optimization
} collision_mode_t;

static collision_mode_t collision_mode = COLLISION_SIMPLE;

// Performance tracking (minimal overhead)
static struct {
    uint32_t fps;
    uint32_t frame_count;
    uint32_t last_fps_time;
    uint32_t collision_checks;
    uint32_t last_frame_time_us;
} perf;

// Game state (your full game)
#define MAX_INVADERS 15
#define MAX_BULLETS 5
#define MAX_BOMBS 15

typedef struct { float x, y; int width, height; } player_t;
typedef struct { float x, y; bool active; } projectile_t;
typedef struct { float x, y; int width, height; bool alive; uint16_t color; } invader_t;

static player_t player;
static projectile_t bullets[MAX_BULLETS];
static projectile_t bombs[MAX_BOMBS];
static invader_t invaders[MAX_INVADERS];
static int invader_count = 0;

// Spatial grid (only used when mode == COLLISION_SPATIAL_GRID)
#define GRID_SIZE 8
typedef struct {
    uint16_t invader_mask;
    uint16_t bullet_mask;
    uint16_t bomb_mask;
} spatial_cell_t;

static spatial_cell_t grid[GRID_SIZE][GRID_SIZE];

// Collision check helper
bool check_collision(float x1, float y1, int w1, int h1, 
                     float x2, float y2, int w2, int h2) {
    return (x1 < x2 + w2 && x1 + w1 > x2 && y1 < y2 + h2 && y1 + h1 > y2);
}

// SIMPLE collision detection (n^2 brute force)
void collision_simple(void) {
    perf.collision_checks = 0;
    
    // Bullet vs Invader (m * n checks)
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!bullets[i].active) continue;
        
        for (int j = 0; j < invader_count; j++) {
            if (!invaders[j].alive) continue;
            
            perf.collision_checks++;
            
            if (check_collision(bullets[i].x, bullets[i].y, 2, 4,
                              invaders[j].x, invaders[j].y, 
                              invaders[j].width, invaders[j].height)) {
                bullets[i].active = false;
                invaders[j].alive = false;
                break;
            }
        }
    }
    
    // Bomb vs Player (n checks)
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (!bombs[i].active) continue;
        
        perf.collision_checks++;
        
        if (check_collision(bombs[i].x, bombs[i].y, 2, 4,
                          player.x, player.y, player.width, player.height)) {
            // Game over logic here
        }
    }
}

// SPATIAL GRID collision detection (optimised)
void collision_spatial_grid(void) {
    perf.collision_checks = 0;
    
    // Clear grid
    memset(grid, 0, sizeof(grid));
    
    float cell_width = (float)DISPLAY_WIDTH / GRID_SIZE;
    float cell_height = (float)DISPLAY_HEIGHT / GRID_SIZE;
    
    // Populate grid with invaders
    for (int i = 0; i < invader_count; i++) {
        if (!invaders[i].alive) continue;
        
        int gx = (int)(invaders[i].x / cell_width);
        int gy = (int)(invaders[i].y / cell_height);
        
        if (gx >= 0 && gx < GRID_SIZE && gy >= 0 && gy < GRID_SIZE) {
            grid[gy][gx].invader_mask |= (1 << i);
        }
    }
    
    // Check bullets against nearby cells only
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!bullets[i].active) continue;
        
        int gx = (int)(bullets[i].x / cell_width);
        int gy = (int)(bullets[i].y / cell_height);
        
        // Check current cell and 8 neighbors
        for (int dy = -1; dy <= 1; dy++) {
            for (int dx = -1; dx <= 1; dx++) {
                int cx = gx + dx;
                int cy = gy + dy;
                
                if (cx < 0 || cx >= GRID_SIZE || cy < 0 || cy >= GRID_SIZE) continue;
                
                uint16_t mask = grid[cy][cx].invader_mask;
                
                // Only check invaders in this cell
                for (int j = 0; j < invader_count && mask; j++) {
                    if (!(mask & (1 << j))) continue;
                    if (!invaders[j].alive) continue;
                    
                    perf.collision_checks++;
                    
                    if (check_collision(bullets[i].x, bullets[i].y, 2, 4,
                                      invaders[j].x, invaders[j].y,
                                      invaders[j].width, invaders[j].height)) {
                        bullets[i].active = false;
                        invaders[j].alive = false;
                        mask &= ~(1 << j);
                        break;
                    }
                }
            }
        }
    }
    
    // Bomb vs player (simple check, not affected by grid)
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (!bombs[i].active) continue;
        
        perf.collision_checks++;
        
        if (check_collision(bombs[i].x, bombs[i].y, 2, 4,
                          player.x, player.y, player.width, player.height)) {
            // Game over logic here
        }
    }
}

// Update collision detection based on current mode
void update_collisions(void) {
    uint32_t start = time_us_32();
    
    if (collision_mode == COLLISION_SIMPLE) {
        collision_simple();
    } else {
        collision_spatial_grid();
    }
    
    perf.last_frame_time_us = time_us_32() - start;
}

// Render performance overlay
void render_performance_hud(void) {
    char buf[64];
    int y = 5;
    
    // Mode indicator
    const char* mode_name = (collision_mode == COLLISION_SIMPLE) ? "SIMPLE" : "SPATIAL GRID";
    snprintf(buf, sizeof(buf), "Mode: %s", mode_name);
    disp_framebuffer_draw_text(5, y, buf, COLOR_CYAN, COLOR_BLACK);
    y += 10;
    
    // FPS
    snprintf(buf, sizeof(buf), "FPS: %lu", perf.fps);
    uint16_t fps_color = (perf.fps >= 55) ? COLOR_GREEN : 
                        (perf.fps >= 30) ? COLOR_YELLOW : COLOR_RED;
    disp_framebuffer_draw_text(5, y, buf, fps_color, COLOR_BLACK);
    y += 10;
    
    // Collision checks this frame
    snprintf(buf, sizeof(buf), "Checks: %lu", perf.collision_checks);
    disp_framebuffer_draw_text(5, y, buf, COLOR_WHITE, COLOR_BLACK);
    y += 10;
    
    // Collision time
    snprintf(buf, sizeof(buf), "Col: %lu us", perf.last_frame_time_us);
    disp_framebuffer_draw_text(5, y, buf, COLOR_YELLOW, COLOR_BLACK);
    y += 10;
    
    // Instructions
    disp_framebuffer_draw_text(5, DISPLAY_HEIGHT - 15, 
                               "Y: Toggle Mode", COLOR_CYAN, COLOR_BLACK);
}

// Update FPS counter
void update_fps(void) {
    perf.frame_count++;
    uint32_t now = time_us_32();
    
    if (now - perf.last_fps_time >= 1000000) {
        perf.fps = perf.frame_count;
        perf.frame_count = 0;
        perf.last_fps_time = now;
        
        // Log to serial
        printf("Mode: %s, FPS: %lu, Collision checks: %lu\n",
               (collision_mode == COLLISION_SIMPLE) ? "SIMPLE" : "SPATIAL",
               perf.fps, perf.collision_checks);
    }
}

// Init game
void init_game(void) {
    player.x = DISPLAY_WIDTH / 2 - 10;
    player.y = DISPLAY_HEIGHT - 30;
    player.width = 20;
    player.height = 10;
    
    invader_count = 15;
    for (int i = 0; i < invader_count; i++) {
        invaders[i].x = 60 + (i % 5) * 40;
        invaders[i].y = 40 + (i / 5) * 30;
        invaders[i].width = 20;
        invaders[i].height = 15;
        invaders[i].alive = true;
        invaders[i].color = (i < 10) ? COLOR_GREEN : COLOR_RED;
    }
    
    memset(bullets, 0, sizeof(bullets));
    memset(bombs, 0, sizeof(bombs));
    
    perf.last_fps_time = time_us_32();
}

// Simplified game update
void update_game(void) {
    // Update bullets
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (bullets[i].active) {
            bullets[i].y -= 5;
            if (bullets[i].y < 0) bullets[i].active = false;
        }
    }
    
    // Update bombs
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (bombs[i].active) {
            bombs[i].y += 3;
            if (bombs[i].y > DISPLAY_HEIGHT) bombs[i].active = false;
        }
    }
}

// Render game
void render_game(void) {
    disp_framebuffer_clear(COLOR_BLACK);
    
    // Player
    disp_framebuffer_fill_rect(player.x, player.y, player.width, player.height, COLOR_WHITE);
    
    // Invaders
    for (int i = 0; i < invader_count; i++) {
        if (invaders[i].alive) {
            disp_framebuffer_fill_rect(invaders[i].x, invaders[i].y,
                                      invaders[i].width, invaders[i].height,
                                      invaders[i].color);
        }
    }
    
    // Bullets
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (bullets[i].active) {
            disp_framebuffer_fill_rect(bullets[i].x, bullets[i].y, 2, 4, COLOR_YELLOW);
        }
    }
    
    // Bombs
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (bombs[i].active) {
            disp_framebuffer_fill_rect(bombs[i].x, bombs[i].y, 2, 4, COLOR_RED);
        }
    }
    
    // Performance HUD
    render_performance_hud();
    
    disp_framebuffer_flush();
}

// Handle input
void handle_input(void) {
    buttons_update();
    
    if (button_pressed(BUTTON_A) && player.x > 0) {
        player.x -= 3;
    }
    if (button_pressed(BUTTON_B) && player.x < DISPLAY_WIDTH - player.width) {
        player.x += 3;
    }
    if (button_just_pressed(BUTTON_X)) {
        for (int i = 0; i < MAX_BULLETS; i++) {
            if (!bullets[i].active) {
                bullets[i].x = player.x + player.width / 2;
                bullets[i].y = player.y;
                bullets[i].active = true;
                break;
            }
        }
    }
    
    // Toggle collision mode
    if (button_just_pressed(BUTTON_Y)) {
        collision_mode = (collision_mode == COLLISION_SIMPLE) ? 
                         COLLISION_SPATIAL_GRID : COLLISION_SIMPLE;
        
        printf("\n=== Switched to %s mode ===\n",
               (collision_mode == COLLISION_SIMPLE) ? "SIMPLE" : "SPATIAL GRID");
    }
}

int main() {
    stdio_init_all();
    
    printf("Space Invaders - Algorithm Comparison\n");
    printf("Press Y to toggle: Simple vs Spatial Grid\n");
    printf("Watch FPS and collision check count!\n\n");
    
    disp_config_t config = disp_get_default_config();
    disp_init(&config);
    buttons_init();
    disp_framebuffer_alloc();
    
    init_game();
    
    while (true) {
        handle_input();
        update_game();
        update_collisions();
        render_game();
        update_fps();
        
        sleep_ms(16);
    }
    
    return 0;
}
