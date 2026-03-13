/*
 * LINEAR LOGIC GAME SEMANTICS DEMONSTRATION
 *
 * 
 * This game implements linear logic concepts through game semantics on a
 * Raspberry Pi Pico with Display Pack 2.0.
 * 
 * GAME SEMANTICS INTERPRETATION:
 * ------------------------------
 * In game semantics, a formula A is interpreted as a two-player game between:
 *   - SYSTEM (∀, We, Proponent): Tries to prove A
 *   - ENVIRONMENT (∃, Opponent): Tries to refute A
 * 
 * A proof of A is a WINNING STRATEGY for System.
 * 
 * LINEAR LOGIC CONNECTIVES AS GAME RULES:
 * 
 * A ⊗ B (TENSOR):    System must defend both A AND B simultaneously
 * A ⅋ B (PAR):       Environment chooses which of A or B to attack
 * A & B (WITH):      Environment chooses which game (A or B) to play
 * A ⊕ B (PLUS):      System chooses which game to play
 * A ⊸ B (LOLLIPOP):  Environment plays A, then System must play B
 * !A (BANG):         A can be replayed infinitely (persistent resource)
 * ?A (WHYNOT):       A might be needed multiple times
 * 
 * THE GAME:
 * ---------
 * We model a RESOURCE EXCHANGE PROTOCOL using session types and linear logic.
 * 
 * Session Type: !Coin ⊸ (Item ⊕ Refund)
 * 
 * "If you give me unlimited coins, I'll give you either an item or a refund"
 * 
 * In game semantics:
 * - Environment (Opponent) provides coins
 * - System (Proponent) must respond with item or refund
 * - Coins marked with ! are reusable (classical resources)
 * - Item/Refund are linear (one-time use, must choose)
 * 
 * AFFINE TYPES:
 * We also demonstrate AFFINE logic (use-at-most-once) where resources can be
 * DISCARDED but not DUPLICATED. This is weaker than linear (exactly-once).
 * 
 * EFFECT TYPES:
 * Resources carry effects (rendering, state changes) that must be sequenced.
 * 
 * GAMEPLAY:
 * - You control the SYSTEM (proving the proposition)
 * - The environment makes demands (opponent moves)
 * - Manage resources correctly or LOSE (type error = game over)
 * - Each resource has LINEAR constraints visualized on screen
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "pico/stdlib.h"
#include "display.h"
#include "font.h"


// LINEAR LOGIC TYPE SYSTEM

typedef enum {
    MULTIPLICITY_LINEAR,   // must use exactly once (⊗, ⊸)
    MULTIPLICITY_AFFINE,   // use at most once (can discard)
    MULTIPLICITY_RELEVANT, // use at least once (can duplicate)
    MULTIPLICITY_UNLIMITED // use any number of times (!)
} multiplicity_t;

typedef enum {
    POLARITY_POSITIVE,  // System moves (⊗, ⊕, !, 1)
    POLARITY_NEGATIVE   // Environment moves (⅋, &, ?, ⊥)
} polarity_t;

typedef enum {
    RESOURCE_COIN,
    RESOURCE_ITEM,
    RESOURCE_REFUND,
    RESOURCE_PROOF,
    RESOURCE_COUNT
} resource_type_t;

typedef struct {
    resource_type_t type;
    multiplicity_t mult;
    polarity_t pol;
    int uses_remaining;  // -1 for unlimited
    bool consumed;
    uint32_t created_at; // timestamp
    uint16_t color;
    int x, y;           // screen position
} linear_resource_t;

#define MAX_RESOURCES 32
static linear_resource_t resources[MAX_RESOURCES];
static int resource_count = 0;


// GAME SEMANTICS STATE

typedef enum {
    TURN_ENVIRONMENT,  // Opponent's move
    TURN_SYSTEM,       // Proponent's move (us)
    TURN_GAME_OVER
} turn_t;

typedef struct {
    turn_t current_turn;
    int system_score;
    int environment_score;
    uint32_t move_count;
    bool type_error;
    char status_msg[64];
} game_state_t;

static game_state_t game;
static uint16_t framebuffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];


// SESSION TYPE PROTOCOL STATE MACHINE

typedef enum {
    SESSION_INIT,           // ⊢ !Coin ⊸ (Item ⊕ Refund)
    SESSION_AWAITING_COIN,  // Environment must provide !Coin
    SESSION_COIN_RECEIVED,  // System must respond with Item ⊕ Refund
    SESSION_CHOICE_ITEM,    // System chose Item (⊕-left)
    SESSION_CHOICE_REFUND,  // System chose Refund (⊕-right)
    SESSION_COMPLETE,       // Protocol finished
    SESSION_TYPE_ERROR      // Linear constraint violated
} session_state_t;

static session_state_t session = SESSION_INIT;


// RESOURCE MANAGEMENT (LINEAR LOGIC ENFORCEMENT)

const char* resource_names[] = {"Coin", "Item", "Refund", "Proof"};
const char* multiplicity_names[] = {"LINEAR", "AFFINE", "RELEVANT", "UNLIM"};

int create_resource(resource_type_t type, multiplicity_t mult, polarity_t pol) {
    if (resource_count >= MAX_RESOURCES) return -1;
    
    linear_resource_t *r = &resources[resource_count];
    r->type = type;
    r->mult = mult;
    r->pol = pol;
    r->consumed = false;
    r->created_at = to_ms_since_boot(get_absolute_time());
    
    switch (mult) {

        case MULTIPLICITY_LINEAR:
            r->uses_remaining = 1;
            r->color = COLOR_RED;
            break;

        case MULTIPLICITY_AFFINE:
            r->uses_remaining = 1;
            r->color = COLOR_YELLOW;
            break;

        case MULTIPLICITY_RELEVANT:
            r->uses_remaining = -1; // unlimited uses, but must use at least once
            r->color = COLOR_CYAN;
            break;

        case MULTIPLICITY_UNLIMITED:
            r->uses_remaining = -1;
            r->color = COLOR_GREEN;
            break;
    }
    
    // Assign screen position
    r->x = 20 + (resource_count % 4) * 70;
    r->y = 60 + (resource_count / 4) * 40;
    
    return resource_count++;
}

bool consume_resource(int idx) {
    if (idx < 0 || idx >= resource_count) return false;
    
    linear_resource_t *r = &resources[idx];
    
    if (r->consumed && r->mult == MULTIPLICITY_LINEAR) {
        // Type error! Tried to use linear resource twice
        snprintf(game.status_msg, sizeof(game.status_msg), 
                 "TYPE ERROR: %s used twice!", resource_names[r->type]);
        game.type_error = true;
        session = SESSION_TYPE_ERROR;
        return false;
    }
    
    if (r->uses_remaining == 0) {
        snprintf(game.status_msg, sizeof(game.status_msg),
                 "TYPE ERROR: %s exhausted!", resource_names[r->type]);
        game.type_error = true;
        session = SESSION_TYPE_ERROR;
        return false;
    }
    
    if (r->uses_remaining > 0) {
        r->uses_remaining--;
    }
    
    r->consumed = true;
    return true;
}

bool discard_resource(int idx) {
    if (idx < 0 || idx >= resource_count) return false;
    
    linear_resource_t *r = &resources[idx];
    
    if (r->mult == MULTIPLICITY_LINEAR) {
        // Cannot discard linear resources!
        snprintf(game.status_msg, sizeof(game.status_msg),
                 "TYPE ERROR: Cannot discard LINEAR %s!", resource_names[r->type]);
        game.type_error = true;
        session = SESSION_TYPE_ERROR;
        return false;
    }
    
    // Affine types can be discarded
    r->consumed = true;
    r->uses_remaining = 0;
    return true;
}


// GAME SEMANTICS MOVES

// OPPONENT MOVE: Environment provides a coin
void opponent_provide_coin(void) {
    if (session != SESSION_AWAITING_COIN) return;
    
    int coin_idx = create_resource(RESOURCE_COIN, MULTIPLICITY_UNLIMITED, POLARITY_NEGATIVE);
    
    if (coin_idx >= 0) {
        snprintf(game.status_msg, sizeof(game.status_msg),
                 "OPPONENT: Provides !Coin (unlimited)");
        session = SESSION_COIN_RECEIVED;
        game.current_turn = TURN_SYSTEM;
        game.environment_score += 10;
    }
}

// PROPONENT MOVE: System chooses Item (⊕-left introduction)
void system_choose_item(void) {
    if (session != SESSION_COIN_RECEIVED) return;
    
    // Find a coin to consume
    int coin_idx = -1;
    for (int i = 0; i < resource_count; i++) {
        if (resources[i].type == RESOURCE_COIN && !resources[i].consumed) {
            coin_idx = i;
            break;
        }
    }
    
    if (coin_idx < 0) {
        snprintf(game.status_msg, sizeof(game.status_msg),
                 "TYPE ERROR: No coin available!");
        game.type_error = true;
        return;
    }
    
    // Consume coin (but it's unlimited, so it's still there)
    consume_resource(coin_idx);
    
    // Create item as LINEAR resource
    int item_idx = create_resource(RESOURCE_ITEM, MULTIPLICITY_LINEAR, POLARITY_POSITIVE);
    
    if (item_idx >= 0) {
        snprintf(game.status_msg, sizeof(game.status_msg),
                 "SYSTEM: Item ⊕ _ (left choice, LINEAR)");
        session = SESSION_CHOICE_ITEM;
        game.system_score += 20;
    }
}

// PROPONENT MOVE: System chooses Refund (⊕-right introduction)
void system_choose_refund(void) {
    if (session != SESSION_COIN_RECEIVED) return;
    
    // Create refund as AFFINE resource (can be discarded)
    int refund_idx = create_resource(RESOURCE_REFUND, MULTIPLICITY_AFFINE, POLARITY_POSITIVE);
    
    if (refund_idx >= 0) {
        snprintf(game.status_msg, sizeof(game.status_msg),
                 "SYSTEM: _ ⊕ Refund (right choice, AFFINE)");
        session = SESSION_CHOICE_REFUND;
        game.system_score += 10;
    }
}


// VISUALISATION

void draw_resource(uint16_t *fb, int idx) {
    linear_resource_t *r = &resources[idx];
    
    int x = r->x;
    int y = r->y;
    
    // Draw box
    uint16_t box_color = r->consumed ? (r->color >> 2) : r->color;
    fb_fill_rect(fb, x, y, 60, 30, COLOR_BLACK);
    fb_fill_rect(fb, x+2, y+2, 56, 26, box_color);
    
    // Draw resource name
    fb_draw_string(fb, x+4, y+4, resource_names[r->type], COLOR_BLACK, box_color);
    
    // Draw multiplicity indicator
    char mult_str[16];
    if (r->uses_remaining < 0) {
        snprintf(mult_str, sizeof(mult_str), "∞");
    } else {
        snprintf(mult_str, sizeof(mult_str), "×%d", r->uses_remaining);
    }
    fb_draw_string(fb, x+4, y+16, mult_str, COLOR_BLACK, box_color);
    
    // Draw consumed marker
    if (r->consumed) {
        fb_draw_line_aa(fb, x, y, x+60, y+30, COLOR_WHITE);
    }
}

void draw_session_diagram(uint16_t *fb) {
    // Draw session type: !Coin ⊸ (Item ⊕ Refund)
    int x = 10, y = 10;
    
    fb_draw_string(fb, x, y, "Session: !Coin", COLOR_GREEN, COLOR_BLACK);
    fb_draw_char(fb, x+100, y, 140, COLOR_WHITE, COLOR_BLACK); // lollipop arrow
    fb_draw_string(fb, x+108, y, "(Item", COLOR_RED, COLOR_BLACK);
    fb_draw_char(fb, x+148, y, '+', COLOR_YELLOW, COLOR_BLACK);
    fb_draw_string(fb, x+156, y, "Refund)", COLOR_YELLOW, COLOR_BLACK);
    
    // State indicator
    const char *state_names[] = {
        "INIT", "AWAIT_COIN", "COIN_RECV", "ITEM", "REFUND", "DONE", "ERROR"
    };
    fb_draw_string(fb, x, y+12, "State:", COLOR_CYAN, COLOR_BLACK);
    fb_draw_string(fb, x+42, y+12, state_names[session], COLOR_WHITE, COLOR_BLACK);
}

void draw_turn_indicator(uint16_t *fb) {
    int x = 10, y = 30;
    
    if (game.current_turn == TURN_ENVIRONMENT) {
        fb_draw_string(fb, x, y, "OPPONENT TURN", COLOR_RED, COLOR_BLACK);
        fb_draw_string(fb, x, y+10, "(Environment ∃)", COLOR_RED, COLOR_BLACK);
    } else if (game.current_turn == TURN_SYSTEM) {
        fb_draw_string(fb, x, y, "YOUR TURN", COLOR_GREEN, COLOR_BLACK);
        fb_draw_string(fb, x, y+10, "(System ∀)", COLOR_GREEN, COLOR_BLACK);
    } else {
        fb_draw_string(fb, x, y, "GAME OVER", COLOR_MAGENTA, COLOR_BLACK);
    }
}

void draw_status(uint16_t *fb) {
    int y = DISPLAY_HEIGHT - 40;
    
    fb_fill_rect(fb, 0, y, DISPLAY_WIDTH, 40, COLOR_BLACK);
    
    char score_str[32];
    snprintf(score_str, sizeof(score_str), "Sys:%d Env:%d", 
             game.system_score, game.environment_score);
    fb_draw_string(fb, 10, y+4, score_str, COLOR_WHITE, COLOR_BLACK);
    
    fb_draw_string(fb, 10, y+16, game.status_msg, 
                   game.type_error ? COLOR_RED : COLOR_CYAN, COLOR_BLACK);
    
    // Control hints
    fb_draw_string(fb, 10, y+28, "A:Coin B:Item X:Refund Y:Next", COLOR_YELLOW, COLOR_BLACK);
}

void draw_linear_logic_explanation(uint16_t *fb) {
    int x = DISPLAY_WIDTH - 110;
    int y = 50;
    
    fb_draw_string(fb, x, y, "LINEAR:", COLOR_RED, COLOR_BLACK);
    fb_draw_string(fb, x, y+10, " use 1x", COLOR_RED, COLOR_BLACK);
    
    fb_draw_string(fb, x, y+22, "AFFINE:", COLOR_YELLOW, COLOR_BLACK);
    fb_draw_string(fb, x, y+32, " <=1x", COLOR_YELLOW, COLOR_BLACK);
    
    fb_draw_string(fb, x, y+44, "UNLIM:", COLOR_GREEN, COLOR_BLACK);
    fb_draw_string(fb, x, y+54, " !A", COLOR_GREEN, COLOR_BLACK);
}


// GAME LOOP

void init_game(void) {
    memset(&game, 0, sizeof(game));
    resource_count = 0;
    session = SESSION_INIT;
    game.current_turn = TURN_ENVIRONMENT;
    snprintf(game.status_msg, sizeof(game.status_msg), "Protocol starting..");
}

void start_protocol(void) {
    session = SESSION_AWAITING_COIN;
    snprintf(game.status_msg, sizeof(game.status_msg), "Awaiting opponent's coin..");
}

void update_game(void) {
    static uint32_t last_update = 0;
    uint32_t now = to_ms_since_boot(get_absolute_time());
    
    if (now - last_update < 1000) return;
    last_update = now;
    
    // Auto-progress certain states
    if (session == SESSION_AWAITING_COIN && game.current_turn == TURN_ENVIRONMENT) {
        opponent_provide_coin();
    }
}

void render(void) {
    fb_clear(framebuffer, COLOR_BLACK);
    
    draw_session_diagram(framebuffer);
    draw_turn_indicator(framebuffer);
    draw_linear_logic_explanation(framebuffer);
    
    // Draw all resources
    for (int i = 0; i < resource_count; i++) {
        draw_resource(framebuffer, i);
    }
    
    draw_status(framebuffer);
    
    display_blit_full(framebuffer);
}

void handle_input(void) {
    buttons_update();
    
    if (button_just_pressed(BUTTON_A)) {
        // Environment provides coin
        if (session == SESSION_AWAITING_COIN) {
            opponent_provide_coin();
        }
    }
    
    if (button_just_pressed(BUTTON_B)) {
        // System chooses Item
        if (game.current_turn == TURN_SYSTEM) {
            system_choose_item();
        }
    }
    
    if (button_just_pressed(BUTTON_X)) {
        // System chooses Refund
        if (game.current_turn == TURN_SYSTEM) {
            system_choose_refund();
        }
    }
    
    if (button_just_pressed(BUTTON_Y)) {
        // Next round / reset
        if (session == SESSION_CHOICE_ITEM || session == SESSION_CHOICE_REFUND) {
            init_game();
            start_protocol();
        }
    }
}




int main(void) {
    stdio_init_all();
    
    if (display_pack_init() != DISPLAY_OK) {
        printf("Display init failed!\n");
        return 1;
    }
    
    if (buttons_init() != DISPLAY_OK) {
        printf("Buttons init failed!\n");
        return 1;
    }
    
    display_set_backlight(true);
    
    // serial connection for debugging
    printf("\n-- LINEAR LOGIC GAME SEMANTICS --\n");
    printf("Session Type: !Coin ⊸ (Item ⊕ Refund)\n");
    printf("Game semantics interpretation:\n");
    printf("  - Opponent (∃) provides unlimited coins\n");
    printf("  - Proponent (∀) must choose Item or Refund\n");
    printf("  - Linear resources must be used exactly once\n");
    printf("  - Affine resources can be discarded\n");
    printf("----------------------\n\n");
    
    init_game();
    start_protocol();
    
    while (true) {
        handle_input();
        update_game();
        render();
        sleep_ms(16); // ~60 FPS
    }
    
    return 0;
}
