#include <stdio.h>
#include "pico/stdlib.h"
#include "display.h"


// Game constants
#define PADDLE_WIDTH 40
#define PADDLE_HEIGHT 5
#define PADDLE_Y (DISPLAY_HEIGHT - PADDLE_HEIGHT - 4)
#define PADDLE_SPEED 8
#define BALL_SIZE 4
#define BALL_INITIAL_SPEED 2
#define BRICK_ROWS 8
#define BRICK_COLS (DISPLAY_WIDTH / BRICK_WIDTH)
#define BRICK_WIDTH 16
#define BRICK_HEIGHT 6
#define BRICK_START_Y 30
#define INITIAL_LIVES 5
#define COLOR_ORANGE 0xFEA0  // RGB565 orange

// Fixed 5x8 font copied from display.c ~ fix API changes!
static const uint8_t font5x8[][5] = {
    {0x00, 0x00, 0x00, 0x00, 0x00}, // Space
    {0x00, 0x00, 0x5F, 0x00, 0x00}, // !
    {0x00, 0x07, 0x00, 0x07, 0x00}, // "
    {0x14, 0x7F, 0x14, 0x7F, 0x14}, // #
    {0x12, 0x2A, 0x7F, 0x2A, 0x24}, // $
    {0x62, 0x64, 0x08, 0x13, 0x23}, // %
    {0x50, 0x22, 0x55, 0x49, 0x36}, // &
    {0x00, 0x00, 0x07, 0x00, 0x00}, // '
    {0x00, 0x41, 0x22, 0x1C, 0x00}, // (
    {0x00, 0x1C, 0x22, 0x41, 0x00}, // )
    {0x14, 0x08, 0x3E, 0x08, 0x14}, // *
    {0x08, 0x08, 0x3E, 0x08, 0x08}, // +
    {0x00, 0x30, 0x50, 0x00, 0x00}, // ,
    {0x08, 0x08, 0x08, 0x08, 0x08}, // -
    {0x00, 0x60, 0x60, 0x00, 0x00}, // .
    {0x02, 0x04, 0x08, 0x10, 0x20}, // /
    {0x3E, 0x45, 0x49, 0x51, 0x3E}, // 0
    {0x00, 0x40, 0x7F, 0x42, 0x00}, // 1
    {0x46, 0x49, 0x51, 0x61, 0x42}, // 2
    {0x31, 0x4B, 0x45, 0x41, 0x21}, // 3
    {0x10, 0x7F, 0x12, 0x14, 0x18}, // 4
    {0x39, 0x49, 0x49, 0x49, 0x2F}, // 5
    {0x30, 0x49, 0x49, 0x4A, 0x3C}, // 6
    {0x07, 0x0D, 0x09, 0x71, 0x01}, // 7
    {0x36, 0x49, 0x49, 0x49, 0x36}, // 8
    {0x1E, 0x29, 0x49, 0x49, 0x0E}, // 9
    {0x00, 0x36, 0x36, 0x00, 0x00}, // :
    {0x00, 0x36, 0x76, 0x00, 0x00}, // ;
    {0x00, 0x41, 0x22, 0x14, 0x08}, // <
    {0x14, 0x14, 0x14, 0x14, 0x14}, // =
    {0x08, 0x14, 0x22, 0x41, 0x00}, // >
    {0x06, 0x09, 0x51, 0x01, 0x06}, // ?
    {0x3E, 0x41, 0x79, 0x49, 0x32}, // @
    {0x7E, 0x11, 0x11, 0x11, 0x7E}, // A
    {0x36, 0x49, 0x49, 0x49, 0x7F}, // B
    {0x22, 0x41, 0x41, 0x41, 0x3E}, // C
    {0x1C, 0x22, 0x41, 0x41, 0x7F}, // D
    {0x41, 0x49, 0x49, 0x49, 0x7F}, // E
    {0x01, 0x09, 0x09, 0x09, 0x7F}, // F
    {0x7A, 0x49, 0x49, 0x41, 0x3E}, // G
    {0x7F, 0x08, 0x08, 0x08, 0x7F}, // H
    {0x00, 0x41, 0x7F, 0x41, 0x00}, // I
    {0x01, 0x3F, 0x41, 0x40, 0x20}, // J
    {0x41, 0x22, 0x14, 0x08, 0x7F}, // K
    {0x40, 0x40, 0x40, 0x40, 0x7F}, // L
    {0x7F, 0x02, 0x0C, 0x02, 0x7F}, // M
    {0x7F, 0x10, 0x0C, 0x02, 0x7F}, // N
    {0x3E, 0x41, 0x41, 0x41, 0x3E}, // O
    {0x06, 0x09, 0x09, 0x09, 0x7F}, // P
    {0x5E, 0x21, 0x51, 0x41, 0x3E}, // Q
    {0x46, 0x29, 0x19, 0x09, 0x7F}, // R
    {0x31, 0x49, 0x49, 0x49, 0x46}, // S
    {0x01, 0x01, 0x7F, 0x01, 0x01}, // T
    {0x3F, 0x40, 0x40, 0x40, 0x3F}, // U
    {0x1F, 0x20, 0x40, 0x20, 0x1F}, // V
    {0x3F, 0x40, 0x38, 0x40, 0x3F}, // W
    {0x63, 0x14, 0x08, 0x14, 0x63}, // X
    {0x07, 0x08, 0x70, 0x08, 0x07}, // Y
    {0x43, 0x45, 0x49, 0x51, 0x61}, // Z
};

// Frame buffer
static uint16_t frame_buffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];

// Buffer drawing functions
static void buffer_fill_rect(uint16_t x, uint16_t y, uint16_t width, uint16_t height, uint16_t color) {
    if (x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT || width == 0 || height == 0) return;
    if (x + width > DISPLAY_WIDTH) width = DISPLAY_WIDTH - x;
    if (y + height > DISPLAY_HEIGHT) height = DISPLAY_HEIGHT - y;

    for (uint16_t yy = y; yy < y + height; yy++) {
        for (uint16_t xx = x; xx < x + width; xx++) {
            frame_buffer[yy * DISPLAY_WIDTH + xx] = color;
        }
    }
}

static void buffer_draw_char(uint16_t x, uint16_t y, char c, uint16_t color, uint16_t bg_color) {
    if (x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return;
    if (c < 32 || c > 90) c = 32;

    const uint8_t *char_data = font5x8[c - 32];

    for (int col = 0; col < 5 && (x + col) < DISPLAY_WIDTH; col++) {
        uint8_t line = char_data[4 - col];
        for (int row = 0; row < 8 && (y + row) < DISPLAY_HEIGHT; row++) {
            uint16_t pixel_color = (line & (1 << row)) ? color : bg_color;
            frame_buffer[(y + row) * DISPLAY_WIDTH + (x + col)] = pixel_color;
        }
    }
}

static void buffer_draw_string(uint16_t x, uint16_t y, const char* str, uint16_t color, uint16_t bg_color) {
    if (!str || x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return;

    int offset_x = 0;
    while (*str && (x + offset_x) < DISPLAY_WIDTH) {
        buffer_draw_char(x + offset_x, y, *str, color, bg_color);
        offset_x += 6;
        str++;
    }
}

// Brick structure
typedef struct {
    bool active;
    uint16_t color;
    int score;
} brick_t;

// Game state
static int paddle_x = (DISPLAY_WIDTH - PADDLE_WIDTH) / 2;
static int ball_x = DISPLAY_WIDTH / 2;
static int ball_y = PADDLE_Y - BALL_SIZE;
static int ball_vx = 0;
static int ball_vy = 0;
static int current_speed = BALL_INITIAL_SPEED;
static int brick_hits = 0;
static bool ball_launched = false;
static brick_t bricks[BRICK_ROWS][BRICK_COLS];
static int score = 0;
static int lives = INITIAL_LIVES;
static bool game_over = false;

// Brick colors and scores (top to bottom, row 0 is top)
static const uint16_t row_colors[BRICK_ROWS] = {
    COLOR_RED, COLOR_RED,
    COLOR_ORANGE, COLOR_ORANGE,
    COLOR_GREEN, COLOR_GREEN,
    COLOR_YELLOW, COLOR_YELLOW
};
static const int row_scores[BRICK_ROWS] = {
    7, 7, 5, 5, 3, 3, 1, 1
};

// Init bricks
static void init_bricks(void) {
    for (int row = 0; row < BRICK_ROWS; row++) {
        for (int col = 0; col < BRICK_COLS; col++) {
            bricks[row][col].active = true;
            bricks[row][col].color = row_colors[row];
            bricks[row][col].score = row_scores[row];
        }
    }
}

// Draw game to buffer
static void draw_game_to_buffer(void) {
    // Clear buffer
    buffer_fill_rect(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT, COLOR_BLACK);

    // Draw bricks
    for (int row = 0; row < BRICK_ROWS; row++) {
        for (int col = 0; col < BRICK_COLS; col++) {
            if (bricks[row][col].active) {
                uint16_t brick_x = col * BRICK_WIDTH;
                uint16_t brick_y = BRICK_START_Y + row * BRICK_HEIGHT;
                buffer_fill_rect(brick_x, brick_y, BRICK_WIDTH - 1, BRICK_HEIGHT - 1, bricks[row][col].color);  // -1 for spacing
            }
        }
    }

    // Draw paddle
    buffer_fill_rect(paddle_x, PADDLE_Y, PADDLE_WIDTH, PADDLE_HEIGHT, COLOR_WHITE);

    // Draw ball
    buffer_fill_rect(ball_x, ball_y, BALL_SIZE, BALL_SIZE, COLOR_WHITE);

    // Draw score
    char score_str[32];
    sprintf(score_str, "SCORE: %d", score);
    buffer_draw_string(10, 10, score_str, COLOR_WHITE, COLOR_BLACK);

    // Draw lives
    char lives_str[32];
    sprintf(lives_str, "LIVES: %d", lives);
    buffer_draw_string(DISPLAY_WIDTH - 80, 10, lives_str, COLOR_WHITE, COLOR_BLACK);

    // Draw messages
    if (game_over) {
        buffer_draw_string(100, 100, "GAME OVER", COLOR_RED, COLOR_BLACK);
        buffer_draw_string(60, 115, "PRESS X TO RESTART", COLOR_WHITE, COLOR_BLACK);
    } else if (!ball_launched) {
        buffer_draw_string(60, 100, "PRESS X TO LAUNCH", COLOR_WHITE, COLOR_BLACK);
    }
}

// Update game logic
static void update_game(void) {
    if (game_over) {
        if (button_just_pressed(BUTTON_X)) {
            init_bricks();
            score = 0;
            lives = INITIAL_LIVES;
            paddle_x = (DISPLAY_WIDTH - PADDLE_WIDTH) / 2;
            ball_x = paddle_x + PADDLE_WIDTH / 2 - BALL_SIZE / 2;
            ball_y = PADDLE_Y - BALL_SIZE;
            ball_vx = 0;
            ball_vy = 0;
            ball_launched = false;
            game_over = false;
            brick_hits = 0;
            current_speed = BALL_INITIAL_SPEED;
        }
        return;
    }

    // Paddle movement (B left, Y right)
    if (button_pressed(BUTTON_B) && paddle_x > 0) {
        paddle_x -= PADDLE_SPEED;
        if (paddle_x < 0) paddle_x = 0;
    }
    if (button_pressed(BUTTON_Y) && paddle_x + PADDLE_WIDTH < DISPLAY_WIDTH) {
        paddle_x += PADDLE_SPEED;
        if (paddle_x + PADDLE_WIDTH > DISPLAY_WIDTH) paddle_x = DISPLAY_WIDTH - PADDLE_WIDTH;
    }

    // Launch ball with X
    if (!ball_launched) {
        ball_x = paddle_x + PADDLE_WIDTH / 2 - BALL_SIZE / 2;
        ball_y = PADDLE_Y - BALL_SIZE;
        if (button_just_pressed(BUTTON_X)) {
            ball_launched = true;
            ball_vx = 0;
            ball_vy = -current_speed;
        }
        return;
    }

    // Update ball position
    ball_x += ball_vx;
    ball_y += ball_vy;

    // Wall collisions
    if (ball_x < 0 || ball_x + BALL_SIZE > DISPLAY_WIDTH) {
        ball_vx = -ball_vx;
        ball_x = (ball_x < 0) ? 0 : DISPLAY_WIDTH - BALL_SIZE;
    }
    if (ball_y < 0) {
        ball_vy = -ball_vy;
        ball_y = 0;
    }

    // Bottom collision (lose life)
    if (ball_y + BALL_SIZE > DISPLAY_HEIGHT) {
        lives--;
        if (lives <= 0) {
            game_over = true;
        } else {
            ball_launched = false;
            ball_vx = 0;
            ball_vy = 0;
        }
        return;
    }

    // Paddle collision
    if (ball_y + BALL_SIZE >= PADDLE_Y &&
        ball_y <= PADDLE_Y + PADDLE_HEIGHT &&
        ball_x + BALL_SIZE >= paddle_x &&
        ball_x <= paddle_x + PADDLE_WIDTH) {
        ball_vy = -current_speed;
        float hit_pos = (ball_x + BALL_SIZE / 2.0f) - paddle_x;
        float normalized = (hit_pos / PADDLE_WIDTH) * 2.0f - 1.0f;  // -1 to 1
        ball_vx = (int)(normalized * current_speed);
        if (ball_vx == 0 && normalized != 0) ball_vx = (normalized > 0) ? 1 : -1;
        ball_y = PADDLE_Y - BALL_SIZE;
    }

    // Brick collisions
    for (int row = 0; row < BRICK_ROWS; row++) {
        for (int col = 0; col < BRICK_COLS; col++) {
            if (bricks[row][col].active) {
                uint16_t brick_x = col * BRICK_WIDTH;
                uint16_t brick_y = BRICK_START_Y + row * BRICK_HEIGHT;
                if (ball_x + BALL_SIZE > brick_x &&
                    ball_x < brick_x + BRICK_WIDTH &&
                    ball_y + BALL_SIZE > brick_y &&
                    ball_y < brick_y + BRICK_HEIGHT) {
                    bricks[row][col].active = false;
                    score += bricks[row][col].score;
                    brick_hits++;
                    ball_vy = -ball_vy;

                    // Speed up logic
                    if (row <= 1) {  // Hit top row (red)
                        current_speed = 5;
                    } else {
                        if (brick_hits == 4) current_speed = 3;
                        else if (brick_hits == 12) current_speed = 4;
                    }
                    ball_vy = (ball_vy > 0) ? current_speed : -current_speed;

                    return;  // One brick per frame
                }
            }
        }
    }
}

// Backlight toggle callback on A
static void on_button_a(button_t button) {
    static bool backlight_on = true;
    backlight_on = !backlight_on;
    display_error_t result = display_set_backlight(backlight_on);
    if (result != DISPLAY_OK) {
        printf("Error toggling backlight: %s\n", display_error_string(result));
    }
}

int main() {
    stdio_init_all();

    printf("-- Breakout Game (Updated) --\n");

    // Initialize display
    display_error_t result;
    if ((result = display_pack_init()) != DISPLAY_OK) {
        printf("Failed to initialise display: %s\n", display_error_string(result));
        return 1;
    }

    // Initialize buttons
    if ((result = buttons_init()) != DISPLAY_OK) {
        printf("Failed to initialise buttons: %s\n", display_error_string(result));
        return 1;
    }

    // Set callback for A button (backlight toggle)
    if ((result = button_set_callback(BUTTON_A, on_button_a)) != DISPLAY_OK) {
        printf("Failed to set callback for A: %s\n", display_error_string(result));
    }

    // Init game
    init_bricks();

    while (true) {
        buttons_update();

        update_game();
        draw_game_to_buffer();
        result = display_blit_full(frame_buffer);
        if (result != DISPLAY_OK) {
            printf("Error blitting frame: %s\n", display_error_string(result));
        }

        // Wait for DMA if busy
        if (display_dma_busy()) {
            display_wait_for_dma();
        }

        sleep_ms(16);  // ~60 FPS target
    }

    // Cleanup (unreachable)
    display_cleanup();
    return 0;
}


