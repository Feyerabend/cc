/* state_game.c – State machine game for Pimoroni DisplayPack 2.0 */
#include "pico/stdlib.h"
#include "display.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define MAX_ENTITIES   4
#define CELL_SIZE      8
#define FLASH_FRAMES   15

/*  Entity structure  */
typedef struct {
    int16_t x, y;        // Cell position
    int16_t dx, dy;      // Movement delta
    bool is_player;
    bool is_ai;
    bool flashing;
    uint8_t flash_timer;
} Entity;

/*  Game states  */
typedef enum {
    STATE_MENU,
    STATE_PLAYING,
    STATE_GAME_OVER,
    STATE_PAUSED
} GameState;

/*  Global game data  */
static struct {
    GameState state;
    GameState prev_state;
    Entity entities[MAX_ENTITIES];
    Entity prev_entities[MAX_ENTITIES];  // Previous positions for clearing
    uint32_t score;
    uint32_t frame_count;
    int16_t field_width;   // In cells
    int16_t field_height;  // In cells
    bool needs_render;     // Flag to force render
    bool first_render;     // First render flag
} game;

/*  State machine functions  */

// Init game field
static void init_game_field(void) {
    game.field_width = DISPLAY_WIDTH / CELL_SIZE;
    game.field_height = DISPLAY_HEIGHT / CELL_SIZE;
}

// Init entities
static void init_entities(void) {
    // Player (entity 0)
    game.entities[0].x = game.field_width / 2;
    game.entities[0].y = game.field_height / 2;
    game.entities[0].dx = 0;
    game.entities[0].dy = 0;
    game.entities[0].is_player = true;
    game.entities[0].is_ai = false;
    game.entities[0].flashing = false;
    game.entities[0].flash_timer = 0;
    
    // AI entities (1, 2, 3)
    for (int i = 1; i < MAX_ENTITIES; i++) {
        game.entities[i].x = rand() % game.field_width;
        game.entities[i].y = rand() % game.field_height;
        game.entities[i].dx = (rand() % 3) - 1;
        game.entities[i].dy = (rand() % 3) - 1;
        game.entities[i].is_player = false;
        game.entities[i].is_ai = true;
        game.entities[i].flashing = false;
        game.entities[i].flash_timer = 0;
    }
}

// Check collision between two entities
static bool check_collision(Entity *a, Entity *b) {
    return (a->x == b->x && a->y == b->y);
}

/*  State: MENU  */
static void state_menu_enter(void) {
    game.score = 0;
    game.frame_count = 0;
    game.needs_render = true;
}

static void state_menu_update(void) {
    if (button_just_pressed(BUTTON_Y)) {
        game.state = STATE_PLAYING;
    }
}

static void state_menu_render(void) {
    display_clear(COLOR_BLACK);
    display_draw_string(80, 100, "PRESS Y TO START", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(80, 120, "X/Y/A/B = MOVE", COLOR_GREEN, COLOR_BLACK);
}

/*  State: PLAYING  */
static void state_playing_enter(void) {
    init_entities();
    game.needs_render = true;
    game.first_render = true;  // Force full clear on first render
    // Copy initial positions
    memcpy(game.prev_entities, game.entities, sizeof(game.entities));
}

static void state_playing_update(void) {
    Entity *player = &game.entities[0];
    
    // Handle input - set player direction
    if (button_pressed(BUTTON_Y)) {
        player->dx = 0;
        player->dy = -1;
    } else if (button_pressed(BUTTON_A)) {
        player->dx = 0;
        player->dy = 1;
    } else if (button_pressed(BUTTON_X)) {
        player->dx = -1;
        player->dy = 0;
    } else if (button_pressed(BUTTON_B)) {
        player->dx = 1;
        player->dy = 0;
    }
    
    // Update AI behavior
    for (int i = 1; i < MAX_ENTITIES; i++) {
        Entity *ai = &game.entities[i];
        if (rand() % 5 == 0) {
            ai->dx = (rand() % 3) - 1;
            ai->dy = (rand() % 3) - 1;
        }
    }
    
    // Update flash timers
    for (int i = 1; i < MAX_ENTITIES; i++) {
        Entity *ai = &game.entities[i];
        if (ai->flashing) {
            ai->flash_timer--;
            if (ai->flash_timer == 0) {
                ai->flashing = false;
            }
        }
    }
    
    // Move all entities
    for (int i = 0; i < MAX_ENTITIES; i++) {
        Entity *e = &game.entities[i];
        
        // Only move if there's actual movement
        if (e->dx != 0 || e->dy != 0) {
            e->x += e->dx;
            e->y += e->dy;
            
            // Clamp to field
            if (e->x < 0) e->x = 0;
            if (e->x >= game.field_width) e->x = game.field_width - 1;
            if (e->y < 0) e->y = 0;
            if (e->y >= game.field_height) e->y = game.field_height - 1;
        }
    }
    
    // Check collisions
    for (int i = 1; i < MAX_ENTITIES; i++) {
        Entity *ai = &game.entities[i];
        if (check_collision(player, ai)) {
            ai->flashing = true;
            ai->flash_timer = FLASH_FRAMES;
            game.score += 10;
        }
    }
    
    game.frame_count++;
}

// Helper to save entity positions (called AFTER rendering)
static void save_entity_positions(void) {
    memcpy(game.prev_entities, game.entities, sizeof(game.entities));
    // Clear first_render flag AFTER we've saved the initial positions
    if (game.first_render) {
        game.first_render = false;
    }
}

static void state_playing_render(void) {
    // Clear the whole screen
    display_clear(COLOR_BLACK);
    
    // Wait for any DMA operations to complete before drawing
    display_wait_for_dma();
    
    // Draw all entities at current positions
    for (int i = 0; i < MAX_ENTITIES; i++) {
        Entity *e = &game.entities[i];
        
        uint16_t px = e->x * CELL_SIZE;
        uint16_t py = e->y * CELL_SIZE;
        
        uint16_t color;
        if (e->is_player) {
            color = COLOR_GREEN;
        } else if (e->flashing) {
            color = COLOR_YELLOW;
        } else {
            color = COLOR_RED;
        }
        
        display_fill_rect(px, py, CELL_SIZE, CELL_SIZE, color);
    }
    
    // Draw score
    char score_str[32];
    snprintf(score_str, sizeof(score_str), "SCORE:%lu", game.score);
    display_draw_string(5, 5, score_str, COLOR_WHITE, COLOR_BLACK);
    
    // Wait for all drawing to complete
    display_wait_for_dma();
}

/*  State: GAME_OVER  */
static void state_gameover_enter(void) {
    game.needs_render = true;
}

static void state_gameover_update(void) {
    if (button_just_pressed(BUTTON_Y)) {
        game.state = STATE_MENU;
    }
}

static void state_gameover_render(void) {
    display_clear(COLOR_BLACK);
    display_draw_string(90, 100, "GAME OVER", COLOR_RED, COLOR_BLACK);
    
    char score_str[32];
    snprintf(score_str, sizeof(score_str), "SCORE: %lu", game.score);
    display_draw_string(90, 120, score_str, COLOR_WHITE, COLOR_BLACK);
    
    display_draw_string(60, 150, "PRESS Y FOR MENU", COLOR_GREEN, COLOR_BLACK);
}

/*  State: PAUSED  */
static void state_paused_enter(void) {
    game.needs_render = true;
}

static void state_paused_update(void) {
    if (button_just_pressed(BUTTON_Y)) {
        game.state = STATE_PLAYING;
    }
}

static void state_paused_render(void) {
    // Render playing state in background
    state_playing_render();
    // Overlay pause message
    display_fill_rect(100, 100, 120, 30, COLOR_BLACK);
    display_draw_string(120, 110, "PAUSED", COLOR_CYAN, COLOR_BLACK);
}

/*  State machine dispatcher  */
static void state_machine_update(void) {
    // Check for state change
    if (game.state != game.prev_state) {
        // State entry
        switch (game.state) {
            case STATE_MENU:
                state_menu_enter();
                break;
            case STATE_PLAYING:
                state_playing_enter();
                break;
            case STATE_GAME_OVER:
                state_gameover_enter();
                break;
            case STATE_PAUSED:
                state_paused_enter();
                break;
        }
        game.prev_state = game.state;
    }
    
    // State update
    switch (game.state) {
        case STATE_MENU:
            state_menu_update();
            break;
        case STATE_PLAYING:
            state_playing_update();
            break;
        case STATE_GAME_OVER:
            state_gameover_update();
            break;
        case STATE_PAUSED:
            state_paused_update();
            break;
    }
    
    // State render - ALWAYS render playing state every frame
    if (game.state == STATE_PLAYING) {
        state_playing_render();
    } else if (game.needs_render) {
        // Other states only render when needed
        switch (game.state) {
            case STATE_MENU:
                state_menu_render();
                break;
            case STATE_GAME_OVER:
                state_gameover_render();
                break;
            case STATE_PAUSED:
                state_paused_render();
                break;
            default:
                break;
        }
        game.needs_render = false;
    }
}

/*  Main  */
int main(void) {
    // Init Pico SDK
    stdio_init_all();
    
    // Seed random
    srand(time_us_32());
    
    // Initialize hardware
    if (display_pack_init() != DISPLAY_OK) {
        return -1;
    }
    if (buttons_init() != DISPLAY_OK) {
        return -1;
    }
    
    // Init game
    memset(&game, 0, sizeof(game));
    init_game_field();
    game.state = STATE_MENU;
    game.prev_state = STATE_GAME_OVER; // Force entry
    game.needs_render = true;
    game.first_render = true;
    
    // Main loop
    while (1) {
        buttons_update();
        state_machine_update();
        sleep_ms(50); // ~20 FPS
    }
    
    return 0;
}