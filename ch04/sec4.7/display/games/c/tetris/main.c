#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/pwm.h"
#include "display.h"

// Button pins (handled by display.h, but for reference)
#define BTN_A       12
#define BTN_B       13
#define BTN_X       14
#define BTN_Y       15

// RGB LED pins
#define LED_R       6
#define LED_G       7
#define LED_B       8

// Game constants
#define BOARD_WIDTH     10
#define BOARD_HEIGHT    20
#define BLOCK_SIZE      11
#define BOARD_OFFSET_X  50
#define BOARD_OFFSET_Y  10

// Buffer constants
#define GAME_AREA_WIDTH  (BOARD_WIDTH * BLOCK_SIZE + 4)
#define GAME_AREA_HEIGHT (BOARD_HEIGHT * BLOCK_SIZE + 4)

// Colours ~ basic colors move to display.h later
#define BLACK       COLOR_BLACK
#define WHITE       COLOR_WHITE
#define RED         COLOR_RED
#define GREEN       COLOR_GREEN
#define BLUE        COLOR_BLUE
#define YELLOW      COLOR_YELLOW
#define CYAN        COLOR_CYAN
#define MAGENTA     COLOR_MAGENTA
#define ORANGE      0xFD20
#define GRAY        0x8410

// Tetris piece colors
uint16_t piece_colors[7] = { CYAN, BLUE, ORANGE, YELLOW, GREEN, MAGENTA, RED };

// Game board
uint8_t board[BOARD_HEIGHT][BOARD_WIDTH];
uint8_t prev_board[BOARD_HEIGHT][BOARD_WIDTH];

// Current piece state
typedef struct {
    int x, y;
    int type;
    int rotation;
} Piece;

Piece current_piece;
Piece prev_piece;
Piece next_piece;

// Game state
int score = 0;
int level = 1;
int lines_cleared = 0;
int drop_timer = 0;
int drop_speed = 48;
bool game_over = false;
bool need_new_piece = true;
bool force_full_redraw = false;

// Button states
bool btn_a = false, btn_b = false, btn_x = false, btn_y = false;
bool prev_btn_a = false, prev_btn_b = false, prev_btn_x = false, prev_btn_y = false;

// Tetris piece definitions
const uint8_t tetris_pieces[7][4][4][4] = {
    // I piece
    {
        {{0,0,0,0},{1,1,1,1},{0,0,0,0},{0,0,0,0}},
        {{0,0,1,0},{0,0,1,0},{0,0,1,0},{0,0,1,0}},
        {{0,0,0,0},{0,0,0,0},{1,1,1,1},{0,0,0,0}},
        {{0,1,0,0},{0,1,0,0},{0,1,0,0},{0,1,0,0}}
    },
    // O piece
    {
        {{0,1,1,0},{0,1,1,0},{0,0,0,0},{0,0,0,0}},
        {{0,1,1,0},{0,1,1,0},{0,0,0,0},{0,0,0,0}},
        {{0,1,1,0},{0,1,1,0},{0,0,0,0},{0,0,0,0}},
        {{0,1,1,0},{0,1,1,0},{0,0,0,0},{0,0,0,0}}
    },
    // T piece
    {
        {{0,1,0,0},{1,1,1,0},{0,0,0,0},{0,0,0,0}},
        {{0,1,0,0},{0,1,1,0},{0,1,0,0},{0,0,0,0}},
        {{0,0,0,0},{1,1,1,0},{0,1,0,0},{0,0,0,0}},
        {{0,1,0,0},{1,1,0,0},{0,1,0,0},{0,0,0,0}}
    },
    // S piece
    {
        {{0,1,1,0},{1,1,0,0},{0,0,0,0},{0,0,0,0}},
        {{0,1,0,0},{0,1,1,0},{0,0,1,0},{0,0,0,0}},
        {{0,0,0,0},{0,1,1,0},{1,1,0,0},{0,0,0,0}},
        {{1,0,0,0},{1,1,0,0},{0,1,0,0},{0,0,0,0}}
    },
    // Z piece
    {
        {{1,1,0,0},{0,1,1,0},{0,0,0,0},{0,0,0,0}},
        {{0,0,1,0},{0,1,1,0},{0,1,0,0},{0,0,0,0}},
        {{0,0,0,0},{1,1,0,0},{0,1,1,0},{0,0,0,0}},
        {{0,1,0,0},{1,1,0,0},{1,0,0,0},{0,0,0,0}}
    },
    // J piece
    {
        {{1,0,0,0},{1,1,1,0},{0,0,0,0},{0,0,0,0}},
        {{0,1,1,0},{0,1,0,0},{0,1,0,0},{0,0,0,0}},
        {{0,0,0,0},{1,1,1,0},{0,0,1,0},{0,0,0,0}},
        {{0,1,0,0},{0,1,0,0},{1,1,0,0},{0,0,0,0}}
    },
    // L piece
    {
        {{0,0,1,0},{1,1,1,0},{0,0,0,0},{0,0,0,0}},
        {{0,1,0,0},{0,1,0,0},{0,1,1,0},{0,0,0,0}},
        {{0,0,0,0},{1,1,1,0},{1,0,0,0},{0,0,0,0}},
        {{1,1,0,0},{0,1,0,0},{0,1,0,0},{0,0,0,0}}
    }
};

// Game rendering functions
void draw_board() {

    // Clear game area
    display_fill_rect(BOARD_OFFSET_X, BOARD_OFFSET_Y, GAME_AREA_WIDTH, GAME_AREA_HEIGHT, BLACK);

    // Draw border
    display_fill_rect(BOARD_OFFSET_X, BOARD_OFFSET_Y, GAME_AREA_WIDTH, 2, WHITE);
    display_fill_rect(BOARD_OFFSET_X, BOARD_OFFSET_Y + GAME_AREA_HEIGHT - 2, GAME_AREA_WIDTH, 2, WHITE);
    display_fill_rect(BOARD_OFFSET_X, BOARD_OFFSET_Y, 2, GAME_AREA_HEIGHT, WHITE);
    display_fill_rect(BOARD_OFFSET_X + GAME_AREA_WIDTH - 2, BOARD_OFFSET_Y, 2, GAME_AREA_HEIGHT, WHITE);

    // Draw placed pieces
    for (int y = 0; y < BOARD_HEIGHT; y++) {
        for (int x = 0; x < BOARD_WIDTH; x++) {
            if (board[y][x] != 0) {
                int screen_x = BOARD_OFFSET_X + 2 + x * BLOCK_SIZE;
                int screen_y = BOARD_OFFSET_Y + 2 + y * BLOCK_SIZE;
                display_fill_rect(screen_x, screen_y, BLOCK_SIZE - 1, BLOCK_SIZE - 1, piece_colors[board[y][x] - 1]);
            }
        }
    }
}

void draw_piece(Piece *piece, uint16_t color) {
    for (int y = 0; y < 4; y++) {
        for (int x = 0; x < 4; x++) {
            if (tetris_pieces[piece->type][piece->rotation][y][x]) {
                int board_x = piece->x + x;
                int board_y = piece->y + y;
                if (board_x >= 0 && board_x < BOARD_WIDTH && board_y >= 0 && board_y < BOARD_HEIGHT) {
                    int screen_x = BOARD_OFFSET_X + 2 + board_x * BLOCK_SIZE;
                    int screen_y = BOARD_OFFSET_Y + 2 + board_y * BLOCK_SIZE;
                    display_fill_rect(screen_x, screen_y, BLOCK_SIZE - 1, BLOCK_SIZE - 1, color);
                }
            }
        }
    }
}

bool has_board_changed() {
    return memcmp(board, prev_board, sizeof(board)) != 0;
}

bool has_piece_changed() {
    return memcmp(&current_piece, &prev_piece, sizeof(Piece)) != 0;
}

void update_display() {
    bool board_changed = has_board_changed();
    bool piece_changed = has_piece_changed();

    if (force_full_redraw || board_changed || piece_changed) {
        // Erase old piece position
        if (piece_changed && !need_new_piece) {
            draw_piece(&prev_piece, BLACK);
        }

        // Redraw board if changed
        if (board_changed || force_full_redraw) {
            draw_board();
        }

        // Draw new piece
        draw_piece(&current_piece, piece_colors[current_piece.type]);

        // Update previous states
        memcpy(prev_board, board, sizeof(board));
        memcpy(&prev_piece, &current_piece, sizeof(Piece));
        force_full_redraw = false;
    }
}

static bool ui_initialized = false;

void draw_static_ui() {
    static int last_score = -1;
    static int last_level = -1;
    static int last_lines = -1;
    static int last_next_piece = -1;

    // Init UI area once
    if (!ui_initialized) {

        // Clear entire right side, extended to cover all potential artifacts?
        display_fill_rect(BOARD_OFFSET_X + GAME_AREA_WIDTH + 5, BOARD_OFFSET_Y,
                          DISPLAY_WIDTH - (BOARD_OFFSET_X + GAME_AREA_WIDTH + 5),
                          DISPLAY_HEIGHT - BOARD_OFFSET_Y, BLACK);
        ui_initialized = true;
        last_next_piece = -999;
        last_score = -999;
        last_level = -999;
        last_lines = -999;
    }

    // Update next piece display
    if (next_piece.type != last_next_piece) {
        int preview_x = BOARD_OFFSET_X + GAME_AREA_WIDTH + 20;
        int preview_y = BOARD_OFFSET_Y + 20;

        // Clear preview area
        display_fill_rect(preview_x, preview_y, 60, 60, BLACK);

        // Draw gray border
        display_fill_rect(preview_x, preview_y, 60, 1, GRAY);
        display_fill_rect(preview_x, preview_y + 59, 60, 1, GRAY);
        display_fill_rect(preview_x, preview_y, 1, 60, GRAY);
        display_fill_rect(preview_x + 59, preview_y, 1, 60, GRAY);

        // Draw next piece
        if (next_piece.type >= 0 && next_piece.type < 7) {
            for (int y = 0; y < 4; y++) {
                for (int x = 0; x < 4; x++) {
                    if (tetris_pieces[next_piece.type][0][y][x]) {
                        int px = 15 + x * 10;
                        int py = 15 + y * 10;
                        display_fill_rect(preview_x + px, preview_y + py, 8, 8, piece_colors[next_piece.type]);
                    }
                }
            }
        }

        last_next_piece = next_piece.type;
    }

    // Update score display and instructions
    if (score != last_score || level != last_level || lines_cleared != last_lines) {
        int info_x = BOARD_OFFSET_X + GAME_AREA_WIDTH + 20;
        int info_y = BOARD_OFFSET_Y + 150; // Moved down to avoid overlap with instructions

        // Draw instructions below preview box
        int text_x = info_x;
        int text_y = BOARD_OFFSET_Y + 90; // Shifted down from 80
        display_draw_string(text_x, text_y, "B: LEFT", WHITE, BLACK);
        display_draw_string(text_x, text_y + 10, "Y: RIGHT", WHITE, BLACK);
        display_draw_string(text_x, text_y + 20, "B+Y: ROTATE", WHITE, BLACK);
        display_draw_string(text_x, text_y + 30, "A: HARD DROP", WHITE, BLACK);
        display_draw_string(text_x, text_y + 40, "X: SOFT DROP", WHITE, BLACK);

        last_score = score;
        last_level = level;
        last_lines = lines_cleared;
    }
}

// LED Control Functions
void init_led() {
    gpio_set_function(LED_R, GPIO_FUNC_PWM);
    gpio_set_function(LED_G, GPIO_FUNC_PWM);
    gpio_set_function(LED_B, GPIO_FUNC_PWM);

    uint slice_r = pwm_gpio_to_slice_num(LED_R);
    uint slice_g = pwm_gpio_to_slice_num(LED_G);
    uint slice_b = pwm_gpio_to_slice_num(LED_B);

    pwm_set_wrap(slice_r, 255);
    pwm_set_wrap(slice_g, 255);
    pwm_set_wrap(slice_b, 255);

    pwm_set_enabled(slice_r, true);
    pwm_set_enabled(slice_g, true);
    pwm_set_enabled(slice_b, true);
}

void set_led(uint8_t r, uint8_t g, uint8_t b) {
    uint slice_r = pwm_gpio_to_slice_num(LED_R);
    uint slice_g = pwm_gpio_to_slice_num(LED_G);
    uint slice_b = pwm_gpio_to_slice_num(LED_B);

    pwm_set_chan_level(slice_r, pwm_gpio_to_channel(LED_R), 255 - r);
    pwm_set_chan_level(slice_g, pwm_gpio_to_channel(LED_G), 255 - g);
    pwm_set_chan_level(slice_b, pwm_gpio_to_channel(LED_B), 255 - b);
}

// Game Functions
void read_buttons() {
    btn_a = button_pressed(BUTTON_A);
    btn_b = button_pressed(BUTTON_B);
    btn_x = button_pressed(BUTTON_X);
    btn_y = button_pressed(BUTTON_Y);
}

void init_game() {
    memset(board, 0, sizeof(board));
    memset(prev_board, 255, sizeof(prev_board));

    current_piece.x = -1;
    current_piece.y = -1;
    current_piece.type = -1;
    current_piece.rotation = -1;
    prev_piece = current_piece;

    score = 0;
    level = 1;
    lines_cleared = 0;
    drop_timer = 0;
    drop_speed = 48;
    game_over = false;
    need_new_piece = true;
    force_full_redraw = true;
    ui_initialized = false;

    display_clear(BLACK);

    set_led(0, 255, 0);
}

bool is_valid_position(Piece *piece) {
    for (int y = 0; y < 4; y++) {
        for (int x = 0; x < 4; x++) {
            if (tetris_pieces[piece->type][piece->rotation][y][x]) {
                int board_x = piece->x + x;
                int board_y = piece->y + y;

                if (board_x < 0 || board_x >= BOARD_WIDTH || board_y >= BOARD_HEIGHT) {
                    return false;
                }

                if (board_y >= 0 && board[board_y][board_x] != 0) {
                    return false;
                }
            }
        }
    }
    return true;
}

void place_piece(Piece *piece) {
    for (int y = 0; y < 4; y++) {
        for (int x = 0; x < 4; x++) {
            if (tetris_pieces[piece->type][piece->rotation][y][x]) {
                int board_x = piece->x + x;
                int board_y = piece->y + y;

                if (board_y >= 0 && board_y < BOARD_HEIGHT &&
                    board_x >= 0 && board_x < BOARD_WIDTH) {
                    board[board_y][board_x] = piece->type + 1;
                }
            }
        }
    }
}

void generate_piece(Piece *piece) {
    piece->x = BOARD_WIDTH / 2 - 2;
    piece->y = 0;
    piece->type = rand() % 7;
    piece->rotation = 0;
}

int clear_full_lines() {
    int cleared_lines = 0;

    for (int y = BOARD_HEIGHT - 1; y >= 0; y--) {
        bool full_line = true;
        for (int x = 0; x < BOARD_WIDTH; x++) {
            if (board[y][x] == 0) {
                full_line = false;
                break;
            }
        }

        if (full_line) {
            for (int move_y = y; move_y > 0; move_y--) {
                memcpy(board[move_y], board[move_y - 1], BOARD_WIDTH);
            }
            memset(board[0], 0, BOARD_WIDTH);
            cleared_lines++;
            y++;
        }
    }

    return cleared_lines;
}

void update_score(int lines) {
    if (lines > 0) {
        int points[] = {0, 100, 300, 500, 800};
        score += points[lines] * level;
        lines_cleared += lines;

        level = 1 + lines_cleared / 10;
        drop_speed = 48 - (level - 1) * 3;
        if (drop_speed < 3) drop_speed = 3;

        set_led(0, 0, 255);
    }
}

void game_loop() {
    buttons_update();
    read_buttons();

    if (game_over) {
        if (btn_a && !prev_btn_a) {
            init_game();
        }
        set_led(255, 0, 0);
        prev_btn_a = btn_a;
        prev_btn_b = btn_b;
        prev_btn_x = btn_x;
        prev_btn_y = btn_y;
        return;
    }

    if (need_new_piece) {
        current_piece = next_piece;
        generate_piece(&next_piece);

        if (!is_valid_position(&current_piece)) {
            game_over = true;
            return;
        }
        prev_piece = current_piece;
        need_new_piece = false;
    }

    Piece test_piece = current_piece;

    // Move left (B button)
    if (btn_b && !prev_btn_b && !(btn_b && btn_y)) {
        test_piece.x--;
        if (is_valid_position(&test_piece)) {
            current_piece = test_piece;
        }
    }

    // Move right (Y button)
    if (btn_y && !prev_btn_y && !(btn_b && btn_y)) {
        test_piece.x++;
        if (is_valid_position(&test_piece)) {
            current_piece = test_piece;
        }
    }

    // Rotate (B + Y buttons)
    if (btn_b && btn_y && (!prev_btn_b || !prev_btn_y)) {
        test_piece.rotation = (test_piece.rotation + 1) % 4;
        if (is_valid_position(&test_piece)) {
            current_piece = test_piece;
        }
    }

    // Soft drop (X button) ~doesn't work very well
    bool soft_drop = btn_x;

    // Hard drop (A button)
    if (btn_a && !prev_btn_a) {
        while (true) {
            test_piece = current_piece;
            test_piece.y++;
            if (is_valid_position(&test_piece)) {
                current_piece = test_piece;
                score += 2;
            } else {
                break;
            }
        }
        drop_timer = drop_speed;
    }

    // Handle piece dropping
    drop_timer++;
    if (drop_timer >= drop_speed || soft_drop) {
        test_piece = current_piece;
        test_piece.y++;

        if (is_valid_position(&test_piece)) {
            current_piece = test_piece;
            if (soft_drop) score += 1;
        } else {
            place_piece(&current_piece);
            int cleared = clear_full_lines();
            update_score(cleared);
            need_new_piece = true;
        }
        drop_timer = 0;
    }

    prev_btn_a = btn_a;
    prev_btn_b = btn_b;
    prev_btn_x = btn_x;
    prev_btn_y = btn_y;

    if (!game_over) {
        uint16_t piece_color = piece_colors[current_piece.type];
        uint8_t r = (piece_color >> 11) << 3;
        uint8_t g = ((piece_color >> 5) & 0x3F) << 2;
        uint8_t b = (piece_color & 0x1F) << 3;
        set_led(r/4, g/4, b/4);
    }
}

int main() {
    stdio_init_all();

    display_pack_init();
    buttons_init();
    init_led();

    srand(time(NULL));

    generate_piece(&next_piece);
    init_game();

    printf("Tetris game started!\n");
    printf("Controls: B=Left, Y=Right, B+Y=Rotate, A=Hard Drop, X=Soft Drop\n");
    printf("Game Over: A=Restart\n");

    while (true) {
        game_loop();
        update_display();
        draw_static_ui();
        sleep_ms(16);
    }

    display_cleanup();
    return 0;
}
