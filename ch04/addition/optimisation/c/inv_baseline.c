/*
 * Space Invaders - Baseline Implementation
 * 
 * This is the CLEAN, SIMPLE version with *NO* optimisations.
 * Use this as the reference to compare against optimised versions.
 * 
 * Features:
 * - Clear, readable code
 * - No premature optimisations
 * - Well-commented
 * - Easy to understand and modify
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include "pico/stdlib.h"
#include "display.h"

// Game constants
#define MAX_BULLETS 5
#define MAX_BOMBS 15
#define MAX_INVADERS 15
#define MAX_BUNKERS 3

#define INVADER_ROWS 3
#define INVADER_COLS 5
#define INVADER_SPACING_X 40
#define INVADER_SPACING_Y 30
#define INVADER_START_X 60
#define INVADER_START_Y 40

#define PLAYER_SPEED 3.0f
#define BULLET_SPEED 5.0f
#define BOMB_SPEED 3.0f
#define INVADER_SPEED 1.0f
#define INVADER_DROP 10.0f
#define INVADER_MOVE_INTERVAL 30  // frames between moves

// Invader type
typedef enum {
    INVADER_SMALL,
    INVADER_LARGE
} invader_type_t;

// Player
typedef struct {
    float x, y;
    int width, height;
} player_t;

// Projectile (bullet or bomb)
typedef struct {
    float x, y;
    bool active;
} projectile_t;

// Invader
typedef struct {
    float x, y;
    int width, height;
    invader_type_t type;
    bool alive;
} invader_t;

// Bunker
typedef struct {
    float x, y;
    int width, height;
    uint8_t pixels[3][5];  // 3 rows, 5 columns (1=solid, 0=destroyed)
} bunker_t;

// Game state
typedef struct {
    player_t player;
    projectile_t bullets[MAX_BULLETS];
    projectile_t bombs[MAX_BOMBS];
    invader_t invaders[MAX_INVADERS];
    bunker_t bunkers[MAX_BUNKERS];
    
    int invader_count;
    int invader_direction;  // 1=right, -1=left
    int move_counter;
    
    bool game_over;
    bool win;
    
    uint32_t frame_count;
    uint32_t fps;
    uint32_t last_fps_time;
} game_state_t;

static game_state_t game;

// Function prototypes
void init_game(void);
void update_game(void);
void render_game(void);
void handle_input(void);

void init_player(void);
void init_invaders(void);
void init_bunkers(void);

void update_projectiles(void);
void update_invaders(void);
void check_collisions(void);

void fire_bullet(void);
void fire_bomb(void);

void draw_player(void);
void draw_invader(invader_t* inv);
void draw_bunker(bunker_t* bunker);
void draw_projectiles(void);
void draw_ui(void);

bool check_collision(float x1, float y1, int w1, int h1, 
                     float x2, float y2, int w2, int h2);
bool check_bunker_collision(float px, float py, int pw, int ph, bunker_t* bunker);
void damage_bunker(bunker_t* bunker, float hit_x, float hit_y);

// Initialize player
void init_player(void) {
    game.player.x = DISPLAY_WIDTH / 2 - 10;
    game.player.y = DISPLAY_HEIGHT - 30;
    game.player.width = 20;
    game.player.height = 10;
}

// Initialize invaders
void init_invaders(void) {
    game.invader_count = 0;
    
    for (int row = 0; row < INVADER_ROWS; row++) {
        for (int col = 0; col < INVADER_COLS; col++) {
            invader_t* inv = &game.invaders[game.invader_count];
            
            inv->x = INVADER_START_X + col * INVADER_SPACING_X;
            inv->y = INVADER_START_Y + row * INVADER_SPACING_Y;
            inv->type = (row == 0) ? INVADER_LARGE : INVADER_SMALL;
            inv->width = 20;
            inv->height = 15;
            inv->alive = true;
            
            game.invader_count++;
        }
    }
    
    game.invader_direction = 1;
    game.move_counter = 0;
}

// Initialize bunkers
void init_bunkers(void) {
    // Simple bunker pattern (solid with notch at bottom)
    uint8_t pattern[3][5] = {
        {1, 1, 1, 1, 1},
        {1, 1, 1, 1, 1},
        {1, 0, 0, 0, 1}
    };
    
    for (int i = 0; i < MAX_BUNKERS; i++) {
        bunker_t* bunker = &game.bunkers[i];
        
        // Space bunkers evenly
        bunker->x = 60 + i * 100;
        bunker->y = DISPLAY_HEIGHT - 80;
        bunker->width = 30;
        bunker->height = 18;
        
        // Copy pattern
        memcpy(bunker->pixels, pattern, sizeof(pattern));
    }
}

// Initialize game
void init_game(void) {
    memset(&game, 0, sizeof(game_state_t));
    
    init_player();
    init_invaders();
    init_bunkers();
    
    game.game_over = false;
    game.win = false;
    game.frame_count = 0;
    game.last_fps_time = time_us_32();
}

// Fire bullet
void fire_bullet(void) {
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!game.bullets[i].active) {
            game.bullets[i].x = game.player.x + game.player.width / 2 - 1;
            game.bullets[i].y = game.player.y;
            game.bullets[i].active = true;
            return;
        }
    }
}

// Fire bomb from random alive invader
void fire_bomb(void) {
    // Count alive invaders
    int alive_indices[MAX_INVADERS];
    int alive_count = 0;
    
    for (int i = 0; i < game.invader_count; i++) {
        if (game.invaders[i].alive) {
            alive_indices[alive_count++] = i;
        }
    }
    
    if (alive_count == 0) return;
    
    // Pick random alive invader
    int idx = alive_indices[rand() % alive_count];
    invader_t* inv = &game.invaders[idx];
    
    // Find free bomb slot
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (!game.bombs[i].active) {
            game.bombs[i].x = inv->x + inv->width / 2 - 1;
            game.bombs[i].y = inv->y + inv->height;
            game.bombs[i].active = true;
            return;
        }
    }
}

// Check rectangle collision
bool check_collision(float x1, float y1, int w1, int h1, 
                     float x2, float y2, int w2, int h2) {
    return (x1 < x2 + w2 && x1 + w1 > x2 && 
            y1 < y2 + h2 && y1 + h1 > y2);
}

// Check collision with bunker (pixel-perfect)
bool check_bunker_collision(float px, float py, int pw, int ph, bunker_t* bunker) {
    // First check bounding box
    if (!check_collision(px, py, pw, ph, 
                        bunker->x, bunker->y, bunker->width, bunker->height)) {
        return false;
    }
    
    // Check which pixel cell was hit
    float pixel_width = bunker->width / 5.0f;
    float pixel_height = bunker->height / 3.0f;
    
    int col = (int)((px + pw/2 - bunker->x) / pixel_width);
    int row = (int)((py + ph/2 - bunker->y) / pixel_height);
    
    // Check if pixel is solid
    if (row >= 0 && row < 3 && col >= 0 && col < 5) {
        return bunker->pixels[row][col] == 1;
    }
    
    return false;
}

// Damage bunker at hit location
void damage_bunker(bunker_t* bunker, float hit_x, float hit_y) {
    float pixel_width = bunker->width / 5.0f;
    float pixel_height = bunker->height / 3.0f;
    
    int col = (int)((hit_x - bunker->x) / pixel_width);
    int row = (int)((hit_y - bunker->y) / pixel_height);
    
    // Destroy hit pixel and adjacent pixels (3x3 area)
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

// Update projectiles
void update_projectiles(void) {
    // Update bullets (move up)
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (game.bullets[i].active) {
            game.bullets[i].y -= BULLET_SPEED;
            
            // Remove if off screen
            if (game.bullets[i].y < 0) {
                game.bullets[i].active = false;
            }
        }
    }
    
    // Update bombs (move down)
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (game.bombs[i].active) {
            game.bombs[i].y += BOMB_SPEED;
            
            // Remove if off screen
            if (game.bombs[i].y > DISPLAY_HEIGHT) {
                game.bombs[i].active = false;
            }
        }
    }
}

// Update invaders
void update_invaders(void) {
    game.move_counter++;
    
    if (game.move_counter >= INVADER_MOVE_INTERVAL) {
        game.move_counter = 0;
        
        // Check if any invader hit screen edge
        bool hit_edge = false;
        for (int i = 0; i < game.invader_count; i++) {
            if (!game.invaders[i].alive) continue;
            
            invader_t* inv = &game.invaders[i];
            
            if ((game.invader_direction > 0 && inv->x + inv->width >= DISPLAY_WIDTH - 10) ||
                (game.invader_direction < 0 && inv->x <= 10)) {
                hit_edge = true;
                break;
            }
        }
        
        if (hit_edge) {
            // Reverse direction and drop down
            game.invader_direction *= -1;
            
            for (int i = 0; i < game.invader_count; i++) {
                if (game.invaders[i].alive) {
                    game.invaders[i].y += INVADER_DROP;
                    
                    // Check if reached player
                    if (game.invaders[i].y + game.invaders[i].height >= game.player.y) {
                        game.game_over = true;
                    }
                }
            }
        } else {
            // Move horizontally
            for (int i = 0; i < game.invader_count; i++) {
                if (game.invaders[i].alive) {
                    game.invaders[i].x += INVADER_SPEED * game.invader_direction;
                }
            }
        }
        
        // Random bomb dropping (20% chance)
        if (rand() % 100 < 20) {
            fire_bomb();
        }
    }
}

// Check all collisions
void check_collisions(void) {
    // Bullet vs Invader
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!game.bullets[i].active) continue;
        
        for (int j = 0; j < game.invader_count; j++) {
            if (!game.invaders[j].alive) continue;
            
            if (check_collision(game.bullets[i].x, game.bullets[i].y, 2, 4,
                              game.invaders[j].x, game.invaders[j].y,
                              game.invaders[j].width, game.invaders[j].height)) {
                game.bullets[i].active = false;
                game.invaders[j].alive = false;
                break;
            }
        }
    }
    
    // Bullet vs Bunker
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!game.bullets[i].active) continue;
        
        for (int j = 0; j < MAX_BUNKERS; j++) {
            if (check_bunker_collision(game.bullets[i].x, game.bullets[i].y, 2, 4,
                                      &game.bunkers[j])) {
                damage_bunker(&game.bunkers[j], game.bullets[i].x, game.bullets[i].y);
                game.bullets[i].active = false;
                break;
            }
        }
    }
    
    // Bomb vs Player
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (!game.bombs[i].active) continue;
        
        if (check_collision(game.bombs[i].x, game.bombs[i].y, 2, 4,
                          game.player.x, game.player.y,
                          game.player.width, game.player.height)) {
            game.game_over = true;
        }
    }
    
    // Bomb vs Bunker
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (!game.bombs[i].active) continue;
        
        for (int j = 0; j < MAX_BUNKERS; j++) {
            if (check_bunker_collision(game.bombs[i].x, game.bombs[i].y, 2, 4,
                                      &game.bunkers[j])) {
                damage_bunker(&game.bunkers[j], game.bombs[i].x, game.bombs[i].y);
                game.bombs[i].active = false;
                break;
            }
        }
    }
    
    // Check win condition
    bool any_alive = false;
    for (int i = 0; i < game.invader_count; i++) {
        if (game.invaders[i].alive) {
            any_alive = true;
            break;
        }
    }
    if (!any_alive) {
        game.win = true;
    }
}

// Handle input
void handle_input(void) {
    // Move left
    if (button_pressed(BUTTON_A)) {
        if (game.player.x > 0) {
            game.player.x -= PLAYER_SPEED;
        }
    }
    
    // Move right
    if (button_pressed(BUTTON_B)) {
        if (game.player.x < DISPLAY_WIDTH - game.player.width) {
            game.player.x += PLAYER_SPEED;
        }
    }
    
    // Fire bullet
    if (button_just_pressed(BUTTON_X)) {
        fire_bullet();
    }
    
    // Restart game
    if ((game.game_over || game.win) && button_just_pressed(BUTTON_X)) {
        init_game();
    }
}

// Draw player
void draw_player(void) {
    disp_framebuffer_fill_rect(game.player.x, game.player.y, 
                               game.player.width, game.player.height, 
                               COLOR_WHITE);
}

// Draw invader
void draw_invader(invader_t* inv) {
    if (!inv->alive) return;
    
    uint16_t color = (inv->type == INVADER_LARGE) ? COLOR_RED : COLOR_GREEN;
    
    // Body
    disp_framebuffer_fill_rect(inv->x, inv->y, inv->width, inv->height, color);
    
    // Eyes (simple white rectangles)
    disp_framebuffer_fill_rect(inv->x + 4, inv->y + 3, 3, 3, COLOR_WHITE);
    disp_framebuffer_fill_rect(inv->x + inv->width - 7, inv->y + 3, 3, 3, COLOR_WHITE);
}

// Draw bunker
void draw_bunker(bunker_t* bunker) {
    float pixel_width = bunker->width / 5.0f;
    float pixel_height = bunker->height / 3.0f;
    
    for (int row = 0; row < 3; row++) {
        for (int col = 0; col < 5; col++) {
            if (bunker->pixels[row][col]) {
                int px = bunker->x + col * pixel_width;
                int py = bunker->y + row * pixel_height;
                
                disp_framebuffer_fill_rect(px, py, pixel_width, pixel_height, 
                                          COLOR_GREEN);
            }
        }
    }
}

// Draw projectiles
void draw_projectiles(void) {
    // Draw bullets
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (game.bullets[i].active) {
            disp_framebuffer_fill_rect(game.bullets[i].x, game.bullets[i].y, 
                                      2, 4, COLOR_YELLOW);
        }
    }
    
    // Draw bombs
    for (int i = 0; i < MAX_BOMBS; i++) {
        if (game.bombs[i].active) {
            disp_framebuffer_fill_rect(game.bombs[i].x, game.bombs[i].y, 
                                      2, 4, COLOR_RED);
        }
    }
}

// Draw UI
void draw_ui(void) {
    char buffer[32];
    
    // FPS counter
    snprintf(buffer, sizeof(buffer), "FPS: %lu", game.fps);
    disp_framebuffer_draw_text(5, 5, buffer, COLOR_CYAN, COLOR_BLACK);
    
    // Game over / win messages
    if (game.game_over) {
        disp_framebuffer_draw_text(DISPLAY_WIDTH/2 - 48, DISPLAY_HEIGHT/2, 
                                  "GAME OVER", COLOR_RED, COLOR_BLACK);
        disp_framebuffer_draw_text(DISPLAY_WIDTH/2 - 60, DISPLAY_HEIGHT/2 + 15, 
                                  "Press X to restart", COLOR_WHITE, COLOR_BLACK);
    } else if (game.win) {
        disp_framebuffer_draw_text(DISPLAY_WIDTH/2 - 36, DISPLAY_HEIGHT/2, 
                                  "YOU WIN!", COLOR_GREEN, COLOR_BLACK);
        disp_framebuffer_draw_text(DISPLAY_WIDTH/2 - 60, DISPLAY_HEIGHT/2 + 15, 
                                  "Press X to restart", COLOR_WHITE, COLOR_BLACK);
    }
}

// Update game logic
void update_game(void) {
    if (game.game_over || game.win) return;
    
    update_projectiles();
    update_invaders();
    check_collisions();
}

// Render game
void render_game(void) {
    // Clear framebuffer
    disp_framebuffer_clear(COLOR_BLACK);
    
    // Draw game objects
    draw_player();
    
    for (int i = 0; i < game.invader_count; i++) {
        draw_invader(&game.invaders[i]);
    }
    
    for (int i = 0; i < MAX_BUNKERS; i++) {
        draw_bunker(&game.bunkers[i]);
    }
    
    draw_projectiles();
    draw_ui();
    
    // Flush to display
    disp_framebuffer_flush();
}

// Main
int main() {
    stdio_init_all();
    
    printf("Space Invaders - Baseline Version\n\n");
    printf("This is the clean reference implementation.\n");
    printf("Controls:\n");
    printf("  A - Move left\n");
    printf("  B - Move right\n");
    printf("  X - Fire / Restart\n");
    printf("\n");
    
    // Initialize display
    disp_config_t config = disp_get_default_config();
    if (disp_init(&config) != DISP_OK) {
        printf("ERROR: Display init failed!\n");
        return 1;
    }
    
    // Initialize buttons
    if (buttons_init() != DISP_OK) {
        printf("ERROR: Button init failed!\n");
        return 1;
    }
    
    // Allocate framebuffer
    if (disp_framebuffer_alloc() != DISP_OK) {
        printf("ERROR: Framebuffer allocation failed!\n");
        return 1;
    }
    
    printf("Init complete!\n\n");
    
    // Initialize game
    init_game();
    
    // Main game loop
    while (true) {
        // Update buttons
        buttons_update();
        
        // Handle input
        handle_input();
        
        // Update game logic
        update_game();
        
        // Render
        render_game();
        
        // FPS calculation
        game.frame_count++;
        uint32_t now = time_us_32();
        if (now - game.last_fps_time >= 1000000) {
            game.fps = game.frame_count;
            game.frame_count = 0;
            game.last_fps_time = now;
            
            printf("FPS: %lu\n", game.fps);
        }
        
        // Frame limiter (~60 FPS)
        sleep_ms(16);
    }
    
    return 0;
}
