/*
 * Space Invaders with Toggle-able Optimisation + Profiling
 * 
 * This is the game with mechanics:
 * - Player movement and shooting
 * - 15 invaders with formation movement
 * - Edge detection and dropping
 * - Bunkers with pixel-perfect damage
 * - Bomb spawning from invaders
 * - Collision detection (all types)
 * - Win/lose conditions
 * - Score tracking
 * - Game reset
 * 
 * Performance features:
 * - Press Y to toggle: Simple vs Spatial Grid collision
 * - On-screen FPS, collision checks, frame time
 * - Compare algorithms in real-time
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include "pico/stdlib.h"
#include "display.h"

#define MAX_BULLETS 5
#define MAX_BOMBS 15
#define MAX_INVADERS 15
#define MAX_BUNKERS 3

#define INVADER_ROWS 3
#define INVADER_COLS 5
#define INVADER_MOVE_INTERVAL 30  // frames between moves
#define BOMB_FIRE_CHANCE 3        // % chance per invader move

#define PLAYER_SPEED 3.0f
#define BULLET_SPEED 5.0f
#define BOMB_SPEED 3.0f
#define INVADER_SPEED 1.5f
#define INVADER_DROP 10.0f

#define GRID_SIZE 8  // Spatial grid: 8x8

typedef struct {
    float x, y;
    int width, height;
} player_t;

typedef struct {
    float x, y;
    bool active;
} projectile_t;

typedef enum {
    INVADER_TYPE_SMALL,
    INVADER_TYPE_LARGE
} invader_type_t;

typedef struct {
    float x, y;
    int width, height;
    invader_type_t type;
    bool alive;
} invader_t;

typedef struct {
    float x, y;
    int width, height;
    uint8_t pixels[3][5];  // 3 rows, 5 cols (1=solid, 0=destroyed)
} bunker_t;

typedef struct {
    uint16_t invader_mask;
    uint16_t bullet_mask;
    uint16_t bomb_mask;
} spatial_cell_t;


// State
static player_t player;
static projectile_t bullets[MAX_BULLETS];
static projectile_t bombs[MAX_BOMBS];
static invader_t invaders[MAX_INVADERS];
static bunker_t bunkers[MAX_BUNKERS];

static int invader_count = 0;
static int invader_direction = 1;  // 1=right, -1=left
static int move_counter = 0;
static int score = 0;
static bool game_over = false;
static bool win = false;


// Opt
typedef enum {
    COLLISION_SIMPLE,
    COLLISION_SPATIAL_GRID
} collision_mode_t;

static collision_mode_t collision_mode = COLLISION_SIMPLE;
static spatial_cell_t spatial_grid[GRID_SIZE][GRID_SIZE];
static float grid_cell_width, grid_cell_height;

// Performance tracking
typedef struct {
    uint32_t fps;
    uint32_t frame_count;
    uint32_t last_fps_time;
    
    uint32_t frame_start_us;
    uint32_t logic_start_us;
    uint32_t collision_start_us;
    uint32_t render_start_us;
    
    uint32_t frame_time_us;
    uint32_t logic_time_us;
    uint32_t collision_time_us;
    uint32_t render_time_us;
    
    uint32_t collision_checks;
    
    bool show_stats;
} perf_stats_t;

static perf_stats_t perf = {0};



bool check_collision(float x1, float y1, int w1, int h1,
                     float x2, float y2, int w2, int h2) {
    return (x1 < x2 + w2 && x1 + w1 > x2 && 
            y1 < y2 + h2 && y1 + h1 > y2);
}


// Inits
void init_player(void) {
    player.x = DISPLAY_WIDTH / 2 - 10;
    player.y = DISPLAY_HEIGHT - 30;
    player.width = 20;
    player.height = 10;
}

void init_invaders(void) {
    invader_count = 0;
    
    for (int row = 0; row < INVADER_ROWS; row++) {
        for (int col = 0; col < INVADER_COLS; col++) {
            invader_t* inv = &invaders[invader_count];
            
            inv->x = 60 + col * 40;
            inv->y = 40 + row * 30;
            inv->type = (row == 0) ? INVADER_TYPE_LARGE : INVADER_TYPE_SMALL;
            inv->width = 20;
            inv->height = 15;
            inv->alive = true;
            
            invader_count++;
        }
    }
    
    invader_direction = 1;
    move_counter = 0;
}

void init_bunkers(void) {
    // Bunker pattern: solid block with notch at bottom
    uint8_t pattern[3][5] = {
        {1, 1, 1, 1, 1},
        {1, 1, 1, 1, 1},
        {1, 0, 0, 0, 1}
    };
    
    for (int i = 0; i < MAX_BUNKERS; i++) {
        bunker_t* bunker = &bunkers[i];
        
        bunker->x = 60 + i * 100;
        bunker->y = DISPLAY_HEIGHT - 80;
        bunker->width = 30;
        bunker->height = 18;
        
        memcpy(bunker->pixels, pattern, sizeof(pattern));
    }
}

void init_game(void) {
    init_player();
    init_invaders();
    init_bunkers();
    
    memset(bullets, 0, sizeof(bullets));
    memset(bombs, 0, sizeof(bombs));
    
    score = 0;
    game_over = false;
    win = false;
    
    // Init spatial grid parameters
    grid_cell_width = (float)DISPLAY_WIDTH / GRID_SIZE;
    grid_cell_height = (float)DISPLAY_HEIGHT / GRID_SIZE;
    
    perf.last_fps_time = time_us_32();
    perf.show_stats = true;
}


void fire_bullet(void) {
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!bullets[i].active) {
            bullets[i].x = player.x + player.width / 2 - 1;
            bullets[i].y = player.y;
            bullets[i].active = true;
            return;
        }
    }
}

void fire_bomb(int invader_index) {
    if (!invaders[invader_index].alive) return;
    
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (!bombs[i].active) {
            invader_t* inv = &invaders[invader_index];
            bombs[i].x = inv->x + inv->width / 2 - 1;
            bombs[i].y = inv->y + inv->height;
            bombs[i].active = true;
            return;
        }
    }
}

void update_projectiles(void) {
    // Update bullets (move up)
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (bullets[i].active) {
            bullets[i].y -= BULLET_SPEED;
            if (bullets[i].y < -5) {
                bullets[i].active = false;
            }
        }
    }
    
    // Update bombs (move down)
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (bombs[i].active) {
            bombs[i].y += BOMB_SPEED;
            if (bombs[i].y > DISPLAY_HEIGHT + 5) {
                bombs[i].active = false;
            }
        }
    }
}


// Move
void update_invaders(void) {
    move_counter++;
    
    if (move_counter >= INVADER_MOVE_INTERVAL) {
        move_counter = 0;
        
        // Check if any invader hit screen edge
        bool hit_edge = false;
        for (int i = 0; i < invader_count; i++) {
            if (!invaders[i].alive) continue;
            
            invader_t* inv = &invaders[i];
            
            if ((invader_direction > 0 && inv->x + inv->width >= DISPLAY_WIDTH - 10) ||
                (invader_direction < 0 && inv->x <= 10)) {
                hit_edge = true;
                break;
            }
        }
        
        if (hit_edge) {
            // Reverse direction and drop down
            invader_direction *= -1;
            
            for (int i = 0; i < invader_count; i++) {
                if (invaders[i].alive) {
                    invaders[i].y += INVADER_DROP;
                    
                    // Check if reached player
                    if (invaders[i].y + invaders[i].height >= player.y) {
                        game_over = true;
                    }
                }
            }
        } else {
            // Move horizontally
            for (int i = 0; i < invader_count; i++) {
                if (invaders[i].alive) {
                    invaders[i].x += INVADER_SPEED * invader_direction;
                }
            }
        }
        
        // Random bomb dropping from alive invaders
        for (int i = 0; i < invader_count; i++) {
            if (invaders[i].alive && rand() % 100 < BOMB_FIRE_CHANCE) {
                fire_bomb(i);
            }
        }
    }
}


// Bunker
bool check_bunker_collision(float px, float py, int pw, int ph, bunker_t* bunker) {
    // Bounding box check first
    if (!check_collision(px, py, pw, ph,
                        bunker->x, bunker->y, bunker->width, bunker->height)) {
        return false;
    }
    
    // Pixel-perfect check
    float pixel_width = bunker->width / 5.0f;
    float pixel_height = bunker->height / 3.0f;
    
    int col = (int)((px + pw/2 - bunker->x) / pixel_width);
    int row = (int)((py + ph/2 - bunker->y) / pixel_height);
    
    if (row >= 0 && row < 3 && col >= 0 && col < 5) {
        return bunker->pixels[row][col] == 1;
    }
    
    return false;
}

void damage_bunker(bunker_t* bunker, float hit_x, float hit_y) {
    float pixel_width = bunker->width / 5.0f;
    float pixel_height = bunker->height / 3.0f;
    
    int col = (int)((hit_x - bunker->x) / pixel_width);
    int row = (int)((hit_y - bunker->y) / pixel_height);
    
    // Destroy 3x3 area around hit
    for (int dr = -1; dr <= 1; dr++) {
        for (int dc = -1; dc <= 1; dc++) {
            int r = row + dr;
            int c = col + dc;
            if (r >= 0 && r < 3 && c >= 0 && c < 5) {
                bunker->pixels[r][c] = 0;
            }
        }
    }
}


// Collision (N^2)
void collision_simple(void) {
    perf.collision_checks = 0;
    
    // Bullet vs Invader
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
                score += (invaders[j].type == INVADER_TYPE_LARGE) ? 20 : 10;
                break;
            }
        }
    }
    
    // Bullet vs Bunker
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!bullets[i].active) continue;
        
        for (int j = 0; j < MAX_BUNKERS; j++) {
            perf.collision_checks++;
            
            if (check_bunker_collision(bullets[i].x, bullets[i].y, 2, 4, &bunkers[j])) {
                damage_bunker(&bunkers[j], bullets[i].x, bullets[i].y);
                bullets[i].active = false;
                break;
            }
        }
    }
    
    // Bomb vs Player
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (!bombs[i].active) continue;
        
        perf.collision_checks++;
        
        if (check_collision(bombs[i].x, bombs[i].y, 2, 4,
                          player.x, player.y, player.width, player.height)) {
            game_over = true;
        }
    }
    
    // Bomb vs Bunker
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (!bombs[i].active) continue;
        
        for (int j = 0; j < MAX_BUNKERS; j++) {
            perf.collision_checks++;
            
            if (check_bunker_collision(bombs[i].x, bombs[i].y, 2, 4, &bunkers[j])) {
                damage_bunker(&bunkers[j], bombs[i].x, bombs[i].y);
                bombs[i].active = false;
                break;
            }
        }
    }
    
    // Check win condition
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


// Collision (the spatial grid opt.)
void collision_spatial_grid(void) {
    perf.collision_checks = 0;
    
    // Clear grid
    memset(spatial_grid, 0, sizeof(spatial_grid));
    
    // Populate grid with invaders
    for (int i = 0; i < invader_count; i++) {
        if (!invaders[i].alive) continue;
        
        int gx = (int)(invaders[i].x / grid_cell_width);
        int gy = (int)(invaders[i].y / grid_cell_height);
        
        if (gx >= 0 && gx < GRID_SIZE && gy >= 0 && gy < GRID_SIZE) {
            spatial_grid[gy][gx].invader_mask |= (1 << i);
        }
    }
    
    // Bullet vs Invader (using spatial grid)
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!bullets[i].active) continue;
        
        int gx = (int)(bullets[i].x / grid_cell_width);
        int gy = (int)(bullets[i].y / grid_cell_height);
        
        // Check adjacent cells (3x3 area)
        for (int dy = -1; dy <= 1; dy++) {
            for (int dx = -1; dx <= 1; dx++) {
                int cx = gx + dx;
                int cy = gy + dy;
                
                if (cx < 0 || cx >= GRID_SIZE || cy < 0 || cy >= GRID_SIZE) continue;
                
                uint16_t mask = spatial_grid[cy][cx].invader_mask;
                
                for (int j = 0; j < invader_count && mask; j++) {
                    if (!(mask & (1 << j))) continue;
                    if (!invaders[j].alive) continue;
                    
                    perf.collision_checks++;
                    
                    if (check_collision(bullets[i].x, bullets[i].y, 2, 4,
                                      invaders[j].x, invaders[j].y,
                                      invaders[j].width, invaders[j].height)) {
                        bullets[i].active = false;
                        invaders[j].alive = false;
                        score += (invaders[j].type == INVADER_TYPE_LARGE) ? 20 : 10;
                        mask &= ~(1 << j);
                        break;
                    }
                }
                if (!bullets[i].active) break;
            }
            if (!bullets[i].active) break;
        }
    }
    
    // Bullet vs Bunker (not affected by spatial grid for this simple case)
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!bullets[i].active) continue;
        
        for (int j = 0; j < MAX_BUNKERS; j++) {
            perf.collision_checks++;
            
            if (check_bunker_collision(bullets[i].x, bullets[i].y, 2, 4, &bunkers[j])) {
                damage_bunker(&bunkers[j], bullets[i].x, bullets[i].y);
                bullets[i].active = false;
                break;
            }
        }
    }
    
    // Bomb vs Player
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (!bombs[i].active) continue;
        
        perf.collision_checks++;
        
        if (check_collision(bombs[i].x, bombs[i].y, 2, 4,
                          player.x, player.y, player.width, player.height)) {
            game_over = true;
        }
    }
    
    // Bomb vs Bunker
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (!bombs[i].active) continue;
        
        for (int j = 0; j < MAX_BUNKERS; j++) {
            perf.collision_checks++;
            
            if (check_bunker_collision(bombs[i].x, bombs[i].y, 2, 4, &bunkers[j])) {
                damage_bunker(&bunkers[j], bombs[i].x, bombs[i].y);
                bombs[i].active = false;
                break;
            }
        }
    }
    
    // Check win condition
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


void update_game(void) {
    if (game_over || win) return;
    
    perf.logic_start_us = time_us_32();
    
    update_projectiles();
    update_invaders();
    
    perf.logic_time_us = time_us_32() - perf.logic_start_us;
    
    // Collision detection with selected algorithm
    perf.collision_start_us = time_us_32();
    
    if (collision_mode == COLLISION_SIMPLE) {
        collision_simple();
    } else {
        collision_spatial_grid();
    }
    
    perf.collision_time_us = time_us_32() - perf.collision_start_us;
}



void handle_input(void) {
    buttons_update();
    
    // Movement
    if (button_pressed(BUTTON_A) && player.x > 0) {
        player.x -= PLAYER_SPEED;
    }
    if (button_pressed(BUTTON_B) && player.x < DISPLAY_WIDTH - player.width) {
        player.x += PLAYER_SPEED;
    }
    
    // Fire
    if (button_just_pressed(BUTTON_X)) {
        if (!game_over && !win) {
            fire_bullet();
        } else {
            // Restart game
            init_game();
        }
    }
    
    // Toggle collision mode
    if (button_just_pressed(BUTTON_Y)) {
        collision_mode = (collision_mode == COLLISION_SIMPLE) ? 
                         COLLISION_SPATIAL_GRID : COLLISION_SIMPLE;
        printf("\n=== Switched to %s ===\n",
               (collision_mode == COLLISION_SIMPLE) ? "SIMPLE" : "SPATIAL GRID");
    }
}


// Render
void draw_invader(invader_t* inv) {
    if (!inv->alive) return;
    
    uint16_t color = (inv->type == INVADER_TYPE_LARGE) ? COLOR_RED : COLOR_GREEN;
    
    // Body
    disp_framebuffer_fill_rect(inv->x, inv->y, inv->width, inv->height, color);
    
    // Eyes
    disp_framebuffer_fill_rect(inv->x + 4, inv->y + 3, 3, 3, COLOR_WHITE);
    disp_framebuffer_fill_rect(inv->x + inv->width - 7, inv->y + 3, 3, 3, COLOR_WHITE);
}

void draw_bunker(bunker_t* bunker) {
    float pixel_width = bunker->width / 5.0f;
    float pixel_height = bunker->height / 3.0f;
    
    for (int row = 0; row < 3; row++) {
        for (int col = 0; col < 5; col++) {
            if (bunker->pixels[row][col]) {
                int px = bunker->x + col * pixel_width;
                int py = bunker->y + row * pixel_height;
                disp_framebuffer_fill_rect(px, py, pixel_width, pixel_height, COLOR_GREEN);
            }
        }
    }
}

void draw_performance_hud(void) {
    if (!perf.show_stats) return;
    
    char buf[64];
    int y = 5;
    
    // Mode indicator
    const char* mode = (collision_mode == COLLISION_SIMPLE) ? "SIMPLE" : "SPATIAL";
    snprintf(buf, sizeof(buf), "%s", mode);
    disp_framebuffer_draw_text(5, y, buf, COLOR_CYAN, COLOR_BLACK);
    y += 10;
    
    // FPS
    snprintf(buf, sizeof(buf), "FPS:%lu", perf.fps);
    uint16_t fps_color = (perf.fps >= 55) ? COLOR_GREEN :
                        (perf.fps >= 30) ? COLOR_YELLOW : COLOR_RED;
    disp_framebuffer_draw_text(5, y, buf, fps_color, COLOR_BLACK);
    y += 10;
    
    // Collision checks
    snprintf(buf, sizeof(buf), "CHK:%lu", perf.collision_checks);
    disp_framebuffer_draw_text(5, y, buf, COLOR_WHITE, COLOR_BLACK);
    y += 10;
    
    // Collision time
    snprintf(buf, sizeof(buf), "COL:%luus", perf.collision_time_us);
    disp_framebuffer_draw_text(5, y, buf, COLOR_YELLOW, COLOR_BLACK);
    
    // Score (top right)
    snprintf(buf, sizeof(buf), "Score:%d", score);
    disp_framebuffer_draw_text(DISPLAY_WIDTH - 60, 5, buf, COLOR_WHITE, COLOR_BLACK);
}

void render_game(void) {
    perf.render_start_us = time_us_32();
    
    disp_framebuffer_clear(COLOR_BLACK);
    
    // Player
    disp_framebuffer_fill_rect(player.x, player.y, player.width, player.height, COLOR_WHITE);
    
    // Invaders
    for (int i = 0; i < invader_count; i++) {
        draw_invader(&invaders[i]);
    }
    
    // Bunkers
    for (int i = 0; i < MAX_BUNKERS; i++) {
        draw_bunker(&bunkers[i]);
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
    draw_performance_hud();
    
    // Game state messages
    if (game_over) {
        disp_framebuffer_draw_text(DISPLAY_WIDTH/2 - 48, DISPLAY_HEIGHT/2,
                                   "GAME OVER", COLOR_RED, COLOR_BLACK);
        disp_framebuffer_draw_text(DISPLAY_WIDTH/2 - 36, DISPLAY_HEIGHT/2 + 15,
                                   "Press X", COLOR_WHITE, COLOR_BLACK);
    } else if (win) {
        disp_framebuffer_draw_text(DISPLAY_WIDTH/2 - 36, DISPLAY_HEIGHT/2,
                                   "YOU WIN!", COLOR_GREEN, COLOR_BLACK);
        disp_framebuffer_draw_text(DISPLAY_WIDTH/2 - 36, DISPLAY_HEIGHT/2 + 15,
                                   "Press X", COLOR_WHITE, COLOR_BLACK);
    }
    
    disp_framebuffer_flush();
    
    perf.render_time_us = time_us_32() - perf.render_start_us;
}


// Performance track
void update_fps(void) {
    perf.frame_count++;
    uint32_t now = time_us_32();
    
    if (now - perf.last_fps_time >= 1000000) {
        perf.fps = perf.frame_count;
        perf.frame_count = 0;
        perf.last_fps_time = now;
        
        // Log to serial
        printf("Mode:%s FPS:%lu Checks:%lu ColTime:%luus RenderTime:%luus\n",
               (collision_mode == COLLISION_SIMPLE) ? "SIMPLE" : "SPATIAL",
               perf.fps, perf.collision_checks,
               perf.collision_time_us, perf.render_time_us);
    }
}



int main() {
    stdio_init_all();
    
    printf("COMPLETE Space Invaders - Algorithm Comparison\n");
    printf("Controls:\n");
    printf("  A/B - Move left/right\n");
    printf("  X - Fire / Restart\n");
    printf("  Y - Toggle collision mode (Simple vs Spatial Grid)\n");
    printf("\nWatch the performance stats on screen!\n\n");
    
    // Init hardware
    disp_config_t config = disp_get_default_config();
    if (disp_init(&config) != DISP_OK) {
        printf("Display init failed!\n");
        return 1;
    }
    
    if (buttons_init() != DISP_OK) {
        printf("Button init failed!\n");
        return 1;
    }
    
    if (disp_framebuffer_alloc() != DISP_OK) {
        printf("Framebuffer allocation failed!\n");
        return 1;
    }
    
    printf("Hardware initialized successfully!\n\n");
    
    // Init game
    init_game();
    
    // Main game loop
    while (true) {
        perf.frame_start_us = time_us_32();
        
        handle_input();
        update_game();
        render_game();
        update_fps();
        
        perf.frame_time_us = time_us_32() - perf.frame_start_us;
        
        sleep_ms(16);  // ~60 FPS target
    }
    
    return 0;
}

