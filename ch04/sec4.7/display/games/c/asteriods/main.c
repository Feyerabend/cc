#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "display.h"

// RGB LED pins
#define LED_R       6
#define LED_G       7
#define LED_B       8

// Game constants - use full display
#define SCREEN_WIDTH 320
#define SCREEN_HEIGHT 240
#define GAME_AREA_X 0
#define GAME_AREA_Y 20
#define GAME_AREA_WIDTH 320
#define GAME_AREA_HEIGHT 220

// Fixed-point arithmetic (16.16 format)
#define FIXED_SHIFT 16
#define FIXED_ONE (1 << FIXED_SHIFT)
#define INT_TO_FIXED(x) ((x) << FIXED_SHIFT)
#define FIXED_TO_INT(x) ((x) >> FIXED_SHIFT)
#define FLOAT_TO_FIXED(x) ((int32_t)((x) * FIXED_ONE))
#define FIXED_MUL(a, b) (((int64_t)(a) * (b)) >> FIXED_SHIFT)
#define FIXED_DIV(a, b) (((int64_t)(a) << FIXED_SHIFT) / (b))

// Ship constants
#define SHIP_SIZE 10
#define THRUST_POWER FLOAT_TO_FIXED(0.25f)
#define TURN_SPEED 5
#define MAX_SPEED FLOAT_TO_FIXED(6.0f)
#define FRICTION_FACTOR 64880  // 0.99 in fixed point

// Bullet constants
#define MAX_BULLETS 8
#define BULLET_SPEED FLOAT_TO_FIXED(10.0f)
#define BULLET_LIFETIME 45  // Reduced from 60 for higher difficulty

// Asteroid constants
#define MAX_ASTEROIDS 10
#define ASTEROID_MIN_SIZE 12
#define ASTEROID_MAX_SIZE 25
#define INITIAL_ASTEROIDS 6  // Increased from 4 for higher difficulty

#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))

// Bounding rect
typedef struct {
    int min_x, min_y, max_x, max_y;
} BoundingRect;

// Game objects
typedef struct {
    int32_t x, y;           // Position (fixed-point)
    int32_t dx, dy;         // Velocity (fixed-point)
    int angle;              // Angle (0-255)
    bool thrusting;
    int32_t radius;         // Collision radius (fixed-point)
    BoundingRect prev_rect;
    bool was_drawn;
} Ship;

typedef struct {
    int32_t x, y;           // Position (fixed-point)
    int32_t dx, dy;         // Velocity (fixed-point)
    int lifetime;
    bool active;
    BoundingRect prev_rect;
    bool was_active;
} Bullet;

typedef struct {
    int32_t x, y;           // Position (fixed-point)
    int32_t dx, dy;         // Velocity (fixed-point)
    int32_t size;           // Size (fixed-point)
    int32_t radius;         // Collision radius (fixed-point)
    int angle;              // Rotation angle
    int vertices[6][2];     // 6 vertices for performance
    bool active;
    BoundingRect prev_rect;
    bool was_active;
} Asteroid;

// Game state
Ship ship;
Bullet bullets[MAX_BULLETS];
Asteroid asteroids[MAX_ASTEROIDS];
int score = 0;
int lives = 3;
bool game_over = false;
int shoot_cooldown = 0;
int respawn_timer = 0;
bool ship_visible = true;

// Redraw control
int clear_counter = 0;
int prev_score = -1;
int prev_lives = -1;
bool need_full_clear = true;

// Previous button states for edge detection
bool prev_btn_x = false;

// Lookup tables
int sin_table[256];
int cos_table[256];

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

// Math functions - optimized
int32_t fast_sqrt(int32_t x) {
    if (x <= 0) return 0;
    if (x < FIXED_ONE) return x;
    
    // Simple approximation for performance
    uint32_t result = x >> 1;
    for (int i = 0; i < 4; i++) {
        result = (result + x / result) >> 1;
    }
    return result;
}

int my_sin(int angle) {
    return sin_table[angle & 0xFF];
}

int my_cos(int angle) {
    return cos_table[angle & 0xFF];
}

void init_trig_tables() {
    for (int i = 0; i < 256; i++) {
        sin_table[i] = (int)(sin(2.0 * M_PI * i / 256.0) * 127.0);
        cos_table[i] = (int)(cos(2.0 * M_PI * i / 256.0) * 127.0);
    }
}

// Fast line drawing with clipping
void draw_line_clipped(int x0, int y0, int x1, int y1, uint16_t color) {
    // Simple bounds check - skip if completely outside
    if ((x0 < 0 && x1 < 0) || (x0 >= DISPLAY_WIDTH && x1 >= DISPLAY_WIDTH) ||
        (y0 < 0 && y1 < 0) || (y0 >= DISPLAY_HEIGHT && y1 >= DISPLAY_HEIGHT)) {
        return;
    }
    
    int dx = abs(x1 - x0);
    int dy = abs(y1 - y0);
    int sx = x0 < x1 ? 1 : -1;
    int sy = y0 < y1 ? 1 : -1;
    int err = dx - dy;
    
    while (true) {
        if (x0 >= 0 && x0 < DISPLAY_WIDTH && y0 >= 0 && y0 < DISPLAY_HEIGHT) {
            display_draw_pixel(x0, y0, color);
        }
        if (x0 == x1 && y0 == y1) break;
        
        int e2 = 2 * err;
        if (e2 > -dy) {
            err -= dy;
            x0 += sx;
        }
        if (e2 < dx) {
            err += dx;
            y0 += sy;
        }
    }
}

// Wrap coordinates to screen, keeping ship out of UI area
void wrap_position(int32_t *x, int32_t *y) {
    int screen_x = FIXED_TO_INT(*x);
    int screen_y = FIXED_TO_INT(*y);
    
    if (screen_x < -20) *x = INT_TO_FIXED(GAME_AREA_WIDTH + 10);
    else if (screen_x > GAME_AREA_WIDTH + 20) *x = INT_TO_FIXED(-10);
    
    // Keep objects at least 20 pixels below UI area
    if (screen_y < GAME_AREA_Y) *y = INT_TO_FIXED(GAME_AREA_HEIGHT + GAME_AREA_Y + 10);
    else if (screen_y > GAME_AREA_HEIGHT + GAME_AREA_Y + 20) *y = INT_TO_FIXED(GAME_AREA_Y + 20);
}

// Clipped clear rect
void clear_object_rect(BoundingRect *rect) {
    int minx = max(rect->min_x, GAME_AREA_X);
    int maxx = min(rect->max_x, GAME_AREA_X + GAME_AREA_WIDTH - 1);
    int miny = max(rect->min_y, GAME_AREA_Y);
    int maxy = min(rect->max_y, GAME_AREA_Y + GAME_AREA_HEIGHT - 1);
    if (minx > maxx || miny > maxy) return;
    display_fill_rect(minx, miny, maxx - minx + 1, maxy - miny + 1, COLOR_BLACK);
}

// Ship functions
BoundingRect get_ship_bounds() {
    int sx = FIXED_TO_INT(ship.x);
    int sy = FIXED_TO_INT(ship.y);
    
    int cos_val = my_cos(ship.angle);
    int sin_val = my_sin(ship.angle);
    
    // Ship nose
    int nose_x = sx + (SHIP_SIZE * cos_val) / 127;
    int nose_y = sy - (SHIP_SIZE * sin_val) / 127;
    
    // Ship back corners
    int back_cos = my_cos(ship.angle + 128);
    int back_sin = my_sin(ship.angle + 128);
    
    int left_x = sx + (SHIP_SIZE * back_cos) / 127 + (SHIP_SIZE * sin_val) / 255;
    int left_y = sy - (SHIP_SIZE * back_sin) / 127 + (SHIP_SIZE * cos_val) / 255;
    
    int right_x = sx + (SHIP_SIZE * back_cos) / 127 - (SHIP_SIZE * sin_val) / 255;
    int right_y = sy - (SHIP_SIZE * back_sin) / 127 - (SHIP_SIZE * cos_val) / 255;
    
    int minx = min(nose_x, min(left_x, right_x));
    int maxx = max(nose_x, max(left_x, right_x));
    int miny = min(nose_y, min(left_y, right_y));
    int maxy = max(nose_y, max(left_y, right_y));
    
    if (ship.thrusting) {
        int flame_x = sx + (SHIP_SIZE * 3 * back_cos) / (2 * 127);
        int flame_y = sy - (SHIP_SIZE * 3 * back_sin) / (2 * 127);
        minx = min(minx, flame_x);
        maxx = max(maxx, flame_x);
        miny = min(miny, flame_y);
        maxy = max(maxy, flame_y);
    }
    
    // Add margin for line drawing
    return (BoundingRect){minx - 1, miny - 1, maxx + 1, maxy + 1};
}

void init_ship() {
    ship.x = INT_TO_FIXED(GAME_AREA_WIDTH / 2);
    ship.y = INT_TO_FIXED(GAME_AREA_HEIGHT / 2 + GAME_AREA_Y);
    ship.dx = 0;
    ship.dy = 0;
    ship.angle = 0;
    ship.thrusting = false;
    ship.radius = INT_TO_FIXED(SHIP_SIZE);
    ship.was_drawn = false;
    respawn_timer = 60;
}

void update_ship() {
    if (respawn_timer > 0) {
        respawn_timer--;
        ship_visible = (respawn_timer / 3) % 2;
    } else {
        ship_visible = true;
    }
    
    // Controls: B=Left, Y=Right, A=Thrust, X=Shoot
    if (button_pressed(BUTTON_B)) {
        ship.angle = (ship.angle - TURN_SPEED + 256) & 0xFF;
    }
    if (button_pressed(BUTTON_Y)) {
        ship.angle = (ship.angle + TURN_SPEED) & 0xFF;
    }
    
    // Thrust with A button
    ship.thrusting = button_pressed(BUTTON_A);
    if (ship.thrusting) {
        int32_t cos_val = INT_TO_FIXED(my_cos(ship.angle)) / 127;
        int32_t sin_val = INT_TO_FIXED(my_sin(ship.angle)) / 127;
        
        ship.dx += FIXED_MUL(cos_val, THRUST_POWER);
        ship.dy -= FIXED_MUL(sin_val, THRUST_POWER);
    }
    
    // Apply friction when not thrusting
    if (!ship.thrusting) {
        ship.dx = FIXED_MUL(ship.dx, FRICTION_FACTOR);
        ship.dy = FIXED_MUL(ship.dy, FRICTION_FACTOR);
    }
    
    // Limit speed
    int32_t speed_sq = FIXED_MUL(ship.dx, ship.dx) + FIXED_MUL(ship.dy, ship.dy);
    if (speed_sq > FIXED_MUL(MAX_SPEED, MAX_SPEED)) {
        int32_t speed = fast_sqrt(speed_sq);
        ship.dx = FIXED_DIV(FIXED_MUL(ship.dx, MAX_SPEED), speed);
        ship.dy = FIXED_DIV(FIXED_MUL(ship.dy, MAX_SPEED), speed);
    }
    
    // Update position
    ship.x += ship.dx;
    ship.y += ship.dy;
    
    wrap_position(&ship.x, &ship.y);
}

void draw_ship() {
    if (!ship_visible) return;
    
    int sx = FIXED_TO_INT(ship.x);
    int sy = FIXED_TO_INT(ship.y);
    
    if (sx < 15 || sx > DISPLAY_WIDTH - 15 || sy < GAME_AREA_Y + 15 || sy > DISPLAY_HEIGHT - 15) return;
    
    int cos_val = my_cos(ship.angle);
    int sin_val = my_sin(ship.angle);
    
    // Ship nose
    int nose_x = sx + (SHIP_SIZE * cos_val) / 127;
    int nose_y = sy - (SHIP_SIZE * sin_val) / 127;
    
    // Ship back corners
    int back_cos = my_cos(ship.angle + 128);
    int back_sin = my_sin(ship.angle + 128);
    
    int left_x = sx + (SHIP_SIZE * back_cos) / 127 + (SHIP_SIZE * sin_val) / 255;
    int left_y = sy - (SHIP_SIZE * back_sin) / 127 + (SHIP_SIZE * cos_val) / 255;
    
    int right_x = sx + (SHIP_SIZE * back_cos) / 127 - (SHIP_SIZE * sin_val) / 255;
    int right_y = sy - (SHIP_SIZE * back_sin) / 127 - (SHIP_SIZE * cos_val) / 255;
    
    // Draw ship triangle
    draw_line_clipped(nose_x, nose_y, left_x, left_y, COLOR_WHITE);
    draw_line_clipped(left_x, left_y, right_x, right_y, COLOR_WHITE);
    draw_line_clipped(right_x, right_y, nose_x, nose_y, COLOR_WHITE);
    
    // Draw thrust flame
    if (ship.thrusting) {
        int flame_x = sx + (SHIP_SIZE * 3 * back_cos) / (2 * 127);
        int flame_y = sy - (SHIP_SIZE * 3 * back_sin) / (2 * 127);
        draw_line_clipped(left_x, left_y, flame_x, flame_y, COLOR_YELLOW);
        draw_line_clipped(right_x, right_y, flame_x, flame_y, COLOR_YELLOW);
    }
}

// Bullet functions
BoundingRect get_bullet_bounds(Bullet *b) {
    int bx = FIXED_TO_INT(b->x);
    int by = FIXED_TO_INT(b->y);
    return (BoundingRect){bx - 1, by - 1, bx + 2, by + 2};  // Margin
}

void shoot_bullet() {
    if (shoot_cooldown > 0) return;
    
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!bullets[i].active) {
            bullets[i].active = true;
            bullets[i].was_active = false;
            bullets[i].x = ship.x;
            bullets[i].y = ship.y;
            
            int32_t cos_val = INT_TO_FIXED(my_cos(ship.angle)) / 127;
            int32_t sin_val = INT_TO_FIXED(my_sin(ship.angle)) / 127;
            
            bullets[i].dx = ship.dx + FIXED_MUL(cos_val, BULLET_SPEED);
            bullets[i].dy = ship.dy - FIXED_MUL(sin_val, BULLET_SPEED);
            bullets[i].lifetime = BULLET_LIFETIME;
            
            shoot_cooldown = 6;
            break;
        }
    }
}

void update_bullets() {
    if (shoot_cooldown > 0) shoot_cooldown--;
    
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!bullets[i].active) continue;
        
        bullets[i].x += bullets[i].dx;
        bullets[i].y += bullets[i].dy;
        bullets[i].lifetime--;
        
        wrap_position(&bullets[i].x, &bullets[i].y);
        
        if (bullets[i].lifetime <= 0) {
            bullets[i].active = false;
        }
    }
}

void draw_bullets() {
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!bullets[i].active) continue;
        
        int bx = FIXED_TO_INT(bullets[i].x);
        int by = FIXED_TO_INT(bullets[i].y);
        
        if (bx >= 0 && bx < DISPLAY_WIDTH-2 && by >= 0 && by < DISPLAY_HEIGHT-2) {
            display_draw_pixel(bx, by, COLOR_WHITE);
            display_draw_pixel(bx + 1, by, COLOR_WHITE);
            display_draw_pixel(bx, by + 1, COLOR_WHITE);
            display_draw_pixel(bx + 1, by + 1, COLOR_WHITE);
        }
    }
}

// Asteroid functions
BoundingRect get_asteroid_bounds(Asteroid *a) {
    int ax = FIXED_TO_INT(a->x);
    int ay = FIXED_TO_INT(a->y);
    int minx = 9999, miny = 9999, maxx = -9999, maxy = -9999;
    for (int j = 0; j < 6; j++) {
        int x = ax + a->vertices[j][0];
        int y = ay + a->vertices[j][1];
        minx = min(minx, x);
        maxx = max(maxx, x);
        miny = min(miny, y);
        maxy = max(maxy, y);
    }
    // Add margin
    return (BoundingRect){minx - 1, miny - 1, maxx + 1, maxy + 1};
}

void create_asteroid(int32_t x, int32_t y, int32_t size) {
    for (int i = 0; i < MAX_ASTEROIDS; i++) {
        if (!asteroids[i].active) {
            asteroids[i].active = true;
            asteroids[i].was_active = false;
            asteroids[i].x = x;
            asteroids[i].y = y;
            asteroids[i].size = size;
            asteroids[i].radius = size;
            asteroids[i].angle = rand() % 256;
            
            // Random velocity, increased for difficulty
            int32_t speed = FLOAT_TO_FIXED(0.5f + (rand() % 50) / 100.0f); // 0.5 to 1.0
            int angle = rand() % 256;
            asteroids[i].dx = FIXED_MUL(speed, INT_TO_FIXED(my_cos(angle)) / 127);
            asteroids[i].dy = FIXED_MUL(speed, INT_TO_FIXED(my_sin(angle)) / 127);
            
            // Generate shape - 6 vertices
            int base_radius = FIXED_TO_INT(size);
            for (int j = 0; j < 6; j++) {
                int variation = base_radius / 3;
                int radius = base_radius - variation/2 + (rand() % variation);
                
                int vertex_angle = (j * 256) / 6;
                asteroids[i].vertices[j][0] = (radius * my_cos(vertex_angle)) / 127;
                asteroids[i].vertices[j][1] = (radius * my_sin(vertex_angle)) / 127;
            }
            break;
        }
    }
}

void init_asteroids() {
    for (int i = 0; i < MAX_ASTEROIDS; i++) {
        asteroids[i].active = false;
        asteroids[i].was_active = false;
    }
    
    for (int i = 0; i < INITIAL_ASTEROIDS; i++) {
        int32_t x, y;
        do {
            x = INT_TO_FIXED(50 + rand() % (GAME_AREA_WIDTH - 100));
            y = INT_TO_FIXED(GAME_AREA_Y + 50 + rand() % (GAME_AREA_HEIGHT - 100));
        } while (abs(FIXED_TO_INT(x - ship.x)) < 60 && abs(FIXED_TO_INT(y - ship.y)) < 60);
        
        int32_t size = INT_TO_FIXED(ASTEROID_MIN_SIZE + rand() % (ASTEROID_MAX_SIZE - ASTEROID_MIN_SIZE));
        create_asteroid(x, y, size);
    }
}

void update_asteroids() {
    for (int i = 0; i < MAX_ASTEROIDS; i++) {
        if (!asteroids[i].active) continue;
        
        asteroids[i].x += asteroids[i].dx;
        asteroids[i].y += asteroids[i].dy;
        asteroids[i].angle = (asteroids[i].angle + 1) & 0xFF;
        
        wrap_position(&asteroids[i].x, &asteroids[i].y);
    }
}

void draw_asteroids() {
    for (int i = 0; i < MAX_ASTEROIDS; i++) {
        if (!asteroids[i].active) continue;
        
        int ax = FIXED_TO_INT(asteroids[i].x);
        int ay = FIXED_TO_INT(asteroids[i].y);
        int size = FIXED_TO_INT(asteroids[i].size);
        
        if (ax < size || ax > DISPLAY_WIDTH - size || ay < size || ay > DISPLAY_HEIGHT - size) continue;
        
        // Draw asteroid as 6-sided polygon
        for (int j = 0; j < 6; j++) {
            int next = (j + 1) % 6;
            
            int x1 = ax + asteroids[i].vertices[j][0];
            int y1 = ay + asteroids[i].vertices[j][1];
            int x2 = ax + asteroids[i].vertices[next][0];
            int y2 = ay + asteroids[i].vertices[next][1];
            
            draw_line_clipped(x1, y1, x2, y2, COLOR_WHITE);
        }
    }
}

// Collision detection - simplified
bool check_collision(int32_t x1, int32_t y1, int32_t r1, int32_t x2, int32_t y2, int32_t r2) {
    int dx = FIXED_TO_INT(x1 - x2);
    int dy = FIXED_TO_INT(y1 - y2);
    int min_dist = FIXED_TO_INT(r1 + r2);
    
    // Simple distance check
    return (dx * dx + dy * dy) < (min_dist * min_dist);
}

void check_collisions() {
    // Bullet-asteroid collisions
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (!bullets[i].active) continue;
        
        for (int j = 0; j < MAX_ASTEROIDS; j++) {
            if (!asteroids[j].active) continue;
            
            if (check_collision(bullets[i].x, bullets[i].y, INT_TO_FIXED(4),
                               asteroids[j].x, asteroids[j].y, asteroids[j].radius)) {
                
                bullets[i].active = false;
                asteroids[j].active = false;
                score += 100;
                
                // Split asteroid if large enough, increased threshold for difficulty
                if (asteroids[j].size > INT_TO_FIXED(ASTEROID_MIN_SIZE + 6)) {
                    int32_t new_size = asteroids[j].size * 2 / 3;
                    create_asteroid(asteroids[j].x + INT_TO_FIXED(8), asteroids[j].y, new_size);
                    create_asteroid(asteroids[j].x - INT_TO_FIXED(8), asteroids[j].y, new_size);
                }
                break;
            }
        }
    }
    
    // Ship-asteroid collisions
    if (respawn_timer <= 0) {
        for (int j = 0; j < MAX_ASTEROIDS; j++) {
            if (!asteroids[j].active) continue;
            
            if (check_collision(ship.x, ship.y, ship.radius,
                               asteroids[j].x, asteroids[j].y, asteroids[j].radius)) {
                lives--;
                if (lives > 0) {
                    init_ship();
                } else {
                    game_over = true;
                }
                break;
            }
        }
    }
}

// LED updates
void update_led() {
    if (game_over) {
        set_led(255, 0, 0);
    } else if (ship.thrusting) {
        set_led(0, 0, 255);
    } else if (shoot_cooldown > 0) {
        set_led(255, 255, 0);
    } else {
        set_led(0, 100, 0);
    }
}

// Game state functions
void reset_game() {
    score = 0;
    lives = 3;
    game_over = false;
    shoot_cooldown = 0;
    clear_counter = 0;
    prev_score = -1;
    prev_lives = -1;
    need_full_clear = true;
    
    for (int i = 0; i < MAX_BULLETS; i++) {
        bullets[i].active = false;
        bullets[i].was_active = false;
    }
    
    init_ship();
    init_asteroids();
    set_led(0, 0, 0);
}

void draw_ui() {
    // Only draw UI when score/lives change, on full clear, or during game over
    if (score != prev_score || lives != prev_lives || need_full_clear || game_over) {
        // Clear UI area
        display_fill_rect(0, 0, DISPLAY_WIDTH, GAME_AREA_Y, COLOR_BLACK);
        
        if (!game_over) {
            char score_text[32];
            char lives_text[16];
            
            snprintf(score_text, sizeof(score_text), "SCORE: %d", score);
            snprintf(lives_text, sizeof(lives_text), "LIVES: %d", lives);
            
            display_draw_string(5, 2, score_text, COLOR_WHITE, COLOR_BLACK);
            display_draw_string(200, 2, lives_text, COLOR_WHITE, COLOR_BLACK);
        }
        
        if (game_over) {
            display_draw_string(110, 120, "GAME OVER", COLOR_RED, COLOR_BLACK);
            display_draw_string(100, 140, "X TO RESTART", COLOR_WHITE, COLOR_BLACK);
        }
        
        prev_score = score;
        prev_lives = lives;
    }
}

bool all_asteroids_destroyed() {
    for (int i = 0; i < MAX_ASTEROIDS; i++) {
        if (asteroids[i].active) return false;
    }
    return true;
}

void game_loop() {
    clear_counter++;
    
    // Handle input - X button shoots/restarts
    bool btn_x = button_pressed(BUTTON_X);
    if (btn_x && !prev_btn_x) {
        if (game_over) {
            reset_game();
        } else {
            shoot_bullet();
        }
    }
    prev_btn_x = btn_x;
    
    if (!game_over) {
        update_ship();
        update_bullets();
        update_asteroids();
        check_collisions();
        
        // Spawn new wave if all asteroids destroyed
        if (all_asteroids_destroyed()) {
            init_asteroids();
        }
    }
    
    update_led();
    
    // Periodic full clear every 60 frames (~1.2s at 50 FPS)
    if (need_full_clear || (clear_counter % 60 == 0)) {
        // Clear entire screen (UI + game area)
        display_fill_rect(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT, COLOR_BLACK);
        need_full_clear = false;
    } else {
        // Clear old object positions
        if (ship.was_drawn) {
            clear_object_rect(&ship.prev_rect);
        }
        for (int i = 0; i < MAX_BULLETS; i++) {
            if (bullets[i].was_active) {
                clear_object_rect(&bullets[i].prev_rect);
            }
        }
        for (int i = 0; i < MAX_ASTEROIDS; i++) {
            if (asteroids[i].was_active) {
                clear_object_rect(&asteroids[i].prev_rect);
            }
        }
    }
    
    // Draw everything
    draw_ship();
    draw_bullets();
    draw_asteroids();
    draw_ui();
    
    // Update previous states
    if (ship_visible) {
        ship.prev_rect = get_ship_bounds();
    }
    ship.was_drawn = ship_visible;
    
    for (int i = 0; i < MAX_BULLETS; i++) {
        if (bullets[i].active) {
            bullets[i].prev_rect = get_bullet_bounds(&bullets[i]);
        }
        bullets[i].was_active = bullets[i].active;
    }
    
    for (int i = 0; i < MAX_ASTEROIDS; i++) {
        if (asteroids[i].active) {
            asteroids[i].prev_rect = get_asteroid_bounds(&asteroids[i]);
        }
        asteroids[i].was_active = asteroids[i].active;
    }
}

int main() {
    stdio_init_all();
    
    // Initialize display pack and buttons
    display_error_t result = display_pack_init();
    if (result != DISPLAY_OK) {
        printf("Display initialization failed: %s\n", display_error_string(result));
        return -1;
    }
    
    result = buttons_init();
    if (result != DISPLAY_OK) {
        printf("Button initialization failed: %s\n", display_error_string(result));
        return -1;
    }
    
    // Initialize game systems
    init_trig_tables();
    init_led();
    reset_game();
    
    printf("Vector space combat game started!\n");
    printf("Controls: B=Turn Left, Y=Turn Right, A=Thrust, X=Shoot/Restart\n");
    
    while (true) {
        buttons_update();
        game_loop();
        sleep_ms(20); // ~50 FPS
    }
    
    return 0;
}
