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

// Colors (RGB565) - using display.h colors plus custom ones
#define DARK_GREEN  0x0320  // Darker green for off-road areas

// Game constants
#define SCREEN_SIZE 240
#define MAP_SCALE 40
#define OFFSET_X 10
#define OFFSET_Y 30
#define GAME_AREA_WIDTH  240
#define GAME_AREA_HEIGHT 200

// Fixed-point arithmetic (16.16 format)
#define FIXED_SHIFT 16
#define FIXED_ONE (1 << FIXED_SHIFT)  // 65536
#define INT_TO_FIXED(x) ((x) << FIXED_SHIFT)
#define FIXED_TO_INT(x) ((x) >> FIXED_SHIFT)
#define FLOAT_TO_FIXED(x) ((int32_t)((x) * FIXED_ONE))
#define FIXED_MUL(a, b) (((int64_t)(a) * (b)) >> FIXED_SHIFT)
#define FIXED_DIV(a, b) (((int64_t)(a) << FIXED_SHIFT) / (b))

// Game state using fixed-point
int theta = 0;
int32_t x = INT_TO_FIXED(70);     // 70.0 in fixed-point
int32_t y = INT_TO_FIXED(70);     // 70.0 in fixed-point
int32_t speed_x = 0;              // 0.0 in fixed-point
int32_t speed_y = 0;              // 0.0 in fixed-point

// Previous car position for dirty region tracking
int prev_car_x = 70;
int prev_car_y = 70;
int prev_theta = 0;

// Track dirty flag
bool track_dirty = true;
bool full_screen_clear_needed = true;

// Map data
int map[5][6] = {
    {2,1,2,5,5,1},
    {6,6,6,2,1,6},
    {6,6,6,6,3,4},
    {6,3,4,3,5,1},
    {3,5,5,5,5,4}
};

// Sin/Cos lookup tables for performance
int sin_table[256];
int cos_table[256];

// Button states
bool prev_btn_a = false; // For reset detection

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

// Fixed-point square root approximation
int32_t fixed_sqrt(int32_t x) {
    if (x <= 0) return 0;
    
    int32_t result = x;
    int32_t temp;
    
    // Newton's method for square root (a few iterations)
    for (int i = 0; i < 8; i++) {
        temp = FIXED_DIV(x, result);
        result = (result + temp) >> 1;
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

// Helper function to draw a line using individual pixels
void draw_line(int x0, int y0, int x1, int y1, uint16_t color) {
    int dx = abs(x1 - x0);
    int dy = abs(y1 - y0);
    int sx = x0 < x1 ? 1 : -1;
    int sy = y0 < y1 ? 1 : -1;
    int err = dx - dy;
    
    while (true) {
        display_draw_pixel(x0, y0, color);
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

// Game functions
void reset_game() {
    x = INT_TO_FIXED(70);
    y = INT_TO_FIXED(70);
    theta = 0;
    speed_x = 0;
    speed_y = 0;
    track_dirty = true;
    full_screen_clear_needed = true;
    
    set_led(0, 0, 0); // Turn off LED
}

void update_led() {
    int total_speed = abs(speed_x) + abs(speed_y);
    
    if (button_pressed(BUTTON_X) && button_pressed(BUTTON_Y)) { // Accelerating (both X and Y pressed)
        int intensity = (total_speed > 255) ? 255 : total_speed;
        set_led(0, intensity, 0); // Green with intensity based on speed
    } else if (!button_pressed(BUTTON_X) && !button_pressed(BUTTON_Y)) { // Decelerating (no buttons pressed)
        int intensity = (total_speed > 255) ? 255 : total_speed;
        set_led(intensity, 0, 0); // Red with intensity based on speed
    } else {
        // Gradually fade based on current speed (when turning)
        int intensity = (total_speed > 255) ? 255 : total_speed;
        intensity = intensity / 4; // Dimmer when coasting
        set_led(0, intensity / 2, 0); // Dim green when coasting
    }
}

void apply_friction() {
    // Much more gradual deceleration - like sliding on a smooth surface
    // 0.98 in fixed-point is approximately 64225 (retains 98% of speed each frame)
    int32_t friction_factor = 64225; // 0.98 * 65536 - very gradual friction
    
    speed_x = FIXED_MUL(speed_x, friction_factor);
    speed_y = FIXED_MUL(speed_y, friction_factor);
    
    // Only stop extremely small movements to avoid infinite sliding
    int32_t min_speed = FLOAT_TO_FIXED(0.005f); // Much smaller threshold
    if (speed_x < min_speed && speed_x > -min_speed) speed_x = 0;
    if (speed_y < min_speed && speed_y > -min_speed) speed_y = 0;
}

void collide_corner(int x1, int y1) {
    // Calculate distance to corner point using fixed-point
    int32_t dx = x - INT_TO_FIXED(x1);
    int32_t dy = y - INT_TO_FIXED(y1);
    int32_t dist_sq = FIXED_MUL(dx, dx) + FIXED_MUL(dy, dy);
    
    int32_t inner_radius_sq = INT_TO_FIXED(64);  // 8*8 = 64
    int32_t outer_radius_sq = INT_TO_FIXED(1024); // 32*32 = 1024
    
    // If too close to corner (inside inner radius)
    if (dist_sq < inner_radius_sq) {
        if (dist_sq > 0) { // Avoid division by zero
            int32_t dist = fixed_sqrt(dist_sq);
            int32_t min_dist = INT_TO_FIXED(10);
            // Push car away from corner to minimum distance
            x = INT_TO_FIXED(x1) + FIXED_DIV(FIXED_MUL(dx, min_dist), dist);
            y = INT_TO_FIXED(y1) + FIXED_DIV(FIXED_MUL(dy, min_dist), dist);
            // Reduce speed smoothly
            speed_x = speed_x >> 1; // Divide by 2
            speed_y = speed_y >> 1;
        }
    }
    // If too far from corner (outside outer radius) 
    else if (dist_sq > outer_radius_sq) {
        int32_t dist = fixed_sqrt(dist_sq);
        int32_t max_dist = INT_TO_FIXED(30);
        // Pull car towards corner to maximum distance
        x = INT_TO_FIXED(x1) + FIXED_DIV(FIXED_MUL(dx, max_dist), dist);
        y = INT_TO_FIXED(y1) + FIXED_DIV(FIXED_MUL(dy, max_dist), dist);
        // Reduce speed smoothly
        speed_x = speed_x >> 1; // Divide by 2
        speed_y = speed_y >> 1;
    }
}

void collide_vert(int x1, int y1, int s) {
    // Check collision with vertical walls (left and right edges)
    int32_t left_wall = INT_TO_FIXED(x1 + 10);
    int32_t right_wall = INT_TO_FIXED(x1 + s - 10);
    
    if (x < left_wall) {
        x = left_wall;
        if (speed_x < 0) {
            speed_x = -speed_x;
            speed_x = FIXED_MUL(speed_x, FLOAT_TO_FIXED(0.3f)); // Reduce speed
        }
    }
    if (x > right_wall) {
        x = right_wall;
        if (speed_x > 0) {
            speed_x = -speed_x;
            speed_x = FIXED_MUL(speed_x, FLOAT_TO_FIXED(0.3f)); // Reduce speed
        }
    }
}

void collide_horiz(int x1, int y1, int s) {
    // Check collision with horizontal walls (top and bottom edges)
    int32_t top_wall = INT_TO_FIXED(y1 + 10);
    int32_t bottom_wall = INT_TO_FIXED(y1 + s - 10);
    
    if (y < top_wall) {
        y = top_wall;
        if (speed_y < 0) {
            speed_y = -speed_y;
            speed_y = FIXED_MUL(speed_y, FLOAT_TO_FIXED(0.3f)); // Reduce speed
        }
    }
    if (y > bottom_wall) {
        y = bottom_wall;
        if (speed_y > 0) {
            speed_y = -speed_y;
            speed_y = FIXED_MUL(speed_y, FLOAT_TO_FIXED(0.3f)); // Reduce speed
        }
    }
}

void draw_horiz(int px, int py, int s) {
    draw_line(px, py + 4, px + s, py + 4, COLOR_GREEN);
    draw_line(px, py + s - 4, px + s, py + s - 4, COLOR_GREEN);
}

void draw_vert(int px, int py, int s) {
    draw_line(px + s - 4, py, px + s - 4, py + s, COLOR_GREEN);
    draw_line(px + 4, py, px + 4, py + s, COLOR_GREEN);
}

void draw_curve(int px, int py, int r, int quadrant) {
    int cx = px, cy = py;
    
    if (quadrant == 1) cy += r;
    if (quadrant == 2) { cx += r; cy += r; }
    if (quadrant == 3) cx += r;
    
    // Draw curve approximation with lines
    int start_angle = -quadrant * 64;
    int end_angle = (1 - quadrant) * 64;
    
    for (int a = start_angle; a < end_angle; a += 2) {
        int x1 = cx + ((r - 4) * my_cos(a)) / 127;
        int y1 = cy + ((r - 4) * my_sin(a)) / 127;
        int x2 = cx + ((r - 4) * my_cos(a + 2)) / 127;
        int y2 = cy + ((r - 4) * my_sin(a + 2)) / 127;
        draw_line(x1, y1, x2, y2, COLOR_GREEN);
        
        x1 = cx + (4 * my_cos(a)) / 127;
        y1 = cy + (4 * my_sin(a)) / 127;
        x2 = cx + (4 * my_cos(a + 2)) / 127;
        y2 = cy + (4 * my_sin(a + 2)) / 127;
        draw_line(x1, y1, x2, y2, COLOR_GREEN);
    }
}

void draw_car() {
    // Clear previous car position and redraw any background underneath
    if (!track_dirty) {
        int prev_costheta = my_cos(prev_theta) / 20;
        int prev_sintheta = my_sin(prev_theta) / 20;
        int prev_halfcos = prev_costheta / 2;
        int prev_halfsin = prev_sintheta / 2;
        
        int prev_car_px = prev_car_x + OFFSET_X;
        int prev_car_py = prev_car_y + OFFSET_Y;
        
        int px1 = prev_car_px + prev_halfcos + prev_halfsin;
        int py1 = prev_car_py + prev_halfsin - prev_halfcos;
        int px2 = prev_car_px - prev_costheta + prev_halfsin;
        int py2 = prev_car_py - prev_sintheta - prev_halfcos;
        int px3 = prev_car_px - prev_costheta - prev_halfsin;
        int py3 = prev_car_py - prev_sintheta + prev_halfcos;
        int px4 = prev_car_px + prev_halfcos - prev_halfsin;
        int py4 = prev_car_py + prev_halfsin + prev_halfcos;
        
        // Draw over previous car with dark green (off-road color)
        draw_line(px1, py1, px2, py2, DARK_GREEN);
        draw_line(px2, py2, px3, py3, DARK_GREEN);
        draw_line(px3, py3, px4, py4, DARK_GREEN);
        draw_line(px4, py4, px1, py1, DARK_GREEN);
        
        // Redraw road elements that might be under the previous car position
        // Check which map cells the previous car was overlapping
        int prev_grid_x = (prev_car_x) / MAP_SCALE;
        int prev_grid_y = (prev_car_y) / MAP_SCALE;
        
        // Redraw the current cell and adjacent cells to handle car spanning multiple cells
        for (int dy = -1; dy <= 1; dy++) {
            for (int dx = -1; dx <= 1; dx++) {
                int grid_x = prev_grid_x + dx;
                int grid_y = prev_grid_y + dy;
                
                if (grid_x >= 0 && grid_x < 6 && grid_y >= 0 && grid_y < 5) {
                    int map_value = map[grid_y][grid_x];
                    if (map_value < 5) {
                        draw_curve(OFFSET_X + grid_x * MAP_SCALE, OFFSET_Y + grid_y * MAP_SCALE, MAP_SCALE, map_value);
                    } else if (map_value == 5) {
                        draw_horiz(OFFSET_X + grid_x * MAP_SCALE, OFFSET_Y + grid_y * MAP_SCALE, MAP_SCALE);
                    } else if (map_value == 6) {
                        draw_vert(OFFSET_X + grid_x * MAP_SCALE, OFFSET_Y + grid_y * MAP_SCALE, MAP_SCALE);
                    }
                }
            }
        }
    }
    
    // Draw current car
    int costheta = my_cos(theta) / 20;
    int sintheta = my_sin(theta) / 20;
    int halfcos = costheta / 2;
    int halfsin = sintheta / 2;
    
    int car_x = FIXED_TO_INT(x) + OFFSET_X;
    int car_y = FIXED_TO_INT(y) + OFFSET_Y;
    
    int x1 = car_x + halfcos + halfsin;
    int y1 = car_y + halfsin - halfcos;
    int x2 = car_x - costheta + halfsin;
    int y2 = car_y - sintheta - halfcos;
    int x3 = car_x - costheta - halfsin;
    int y3 = car_y - sintheta + halfcos;
    int x4 = car_x + halfcos - halfsin;
    int y4 = car_y + halfsin + halfcos;
    
    draw_line(x1, y1, x2, y2, COLOR_WHITE);  // Changed to white for better visibility
    draw_line(x2, y2, x3, y3, COLOR_WHITE);
    draw_line(x3, y3, x4, y4, COLOR_WHITE);
    draw_line(x4, y4, x1, y1, COLOR_WHITE);
    
    // Store current position for next frame
    prev_car_x = FIXED_TO_INT(x);
    prev_car_y = FIXED_TO_INT(y);
    prev_theta = theta;
}

void draw_track() {
    // First fill the entire game area with dark green (off-road)
    display_fill_rect(OFFSET_X, OFFSET_Y, GAME_AREA_WIDTH, GAME_AREA_HEIGHT, DARK_GREEN);
    
    // Then draw the track elements over it
    for (int j = 0; j < 5; j++) {
        for (int i = 0; i < 6; i++) {
            // Draw track elements
            if (map[j][i] < 5) {
                draw_curve(OFFSET_X + i * MAP_SCALE, OFFSET_Y + j * MAP_SCALE, MAP_SCALE, map[j][i]);
            } else if (map[j][i] == 5) {
                draw_horiz(OFFSET_X + i * MAP_SCALE, OFFSET_Y + j * MAP_SCALE, MAP_SCALE);
            } else if (map[j][i] == 6) {
                draw_vert(OFFSET_X + i * MAP_SCALE, OFFSET_Y + j * MAP_SCALE, MAP_SCALE);
            }
        }
    }
}

void game_loop() {
    // Handle reset button (A button)
    bool btn_a = button_pressed(BUTTON_A);
    if (btn_a && !prev_btn_a) {
        reset_game();
    }
    prev_btn_a = btn_a;
    
    // Clear screen only when needed
    if (full_screen_clear_needed) {
        // Clear the entire screen to black
        display_clear(COLOR_BLACK);
        full_screen_clear_needed = false;
        track_dirty = true;  // Force track redraw after full clear
    }
    
    if (track_dirty) {
        // Also ensure the game area background is properly drawn
        draw_track();
        track_dirty = false;
    }
    
    // Get current button states
    bool btn_x = button_pressed(BUTTON_X);
    bool btn_y = button_pressed(BUTTON_Y);
    
    // Update player rotation - Y=left, X=right (works anytime, not just when accelerating)
    if (btn_y && !btn_x) {
        theta = (theta - 2 + 256) % 256;
    } else if (btn_x && !btn_y) {
        theta = (theta + 2) % 256;
    }
    
    // Acceleration - both X and Y pressed
    if (btn_x && btn_y) {
        // Much more realistic acceleration using fixed-point
        int32_t cos_val = INT_TO_FIXED(my_cos(theta)) / 127;  // Normalize to fixed-point
        int32_t sin_val = INT_TO_FIXED(my_sin(theta)) / 127;
        
        int32_t accel = FLOAT_TO_FIXED(0.08f);  // Much more gradual acceleration (was 0.3f)
        speed_x += FIXED_MUL(cos_val, accel);
        speed_y += FIXED_MUL(sin_val, accel);
        
        // Limit maximum speed to be more reasonable
        int32_t max_speed = INT_TO_FIXED(4);  // Reduced from 8 for more realistic speed
        int32_t speed_sq = FIXED_MUL(speed_x, speed_x) + FIXED_MUL(speed_y, speed_y);
        int32_t current_speed = fixed_sqrt(speed_sq);
        
        if (current_speed > max_speed) {
            speed_x = FIXED_DIV(FIXED_MUL(speed_x, max_speed), current_speed);
            speed_y = FIXED_DIV(FIXED_MUL(speed_y, max_speed), current_speed);
        }
    }
    
    // Automatic deceleration when no buttons are pressed (but steering still works!)
    if (!btn_x && !btn_y) {
        apply_friction();
    }
    // When only one button is pressed (steering while coasting), apply light friction
    else if (btn_x != btn_y) { // XOR - only one button pressed
        // Light friction when steering while coasting (but not as much as full braking)
        int32_t light_friction_factor = 65208; // 0.996 * 65536 - very light friction
        speed_x = FIXED_MUL(speed_x, light_friction_factor);
        speed_y = FIXED_MUL(speed_y, light_friction_factor);
    }
    
    // Update position with smooth movement
    int32_t new_x = x + speed_x;
    int32_t new_y = y + speed_y;
    
    // Keep car within game boundaries
    int32_t min_x = 0;
    int32_t max_x = INT_TO_FIXED(GAME_AREA_WIDTH - OFFSET_X);
    int32_t min_y = 0;
    int32_t max_y = INT_TO_FIXED(GAME_AREA_HEIGHT - OFFSET_Y);
    
    if (new_x < min_x) {
        new_x = min_x;
        speed_x = 0;
    } else if (new_x > max_x) {
        new_x = max_x;
        speed_x = 0;
    }
    
    if (new_y < min_y) {
        new_y = min_y;
        speed_y = 0;
    } else if (new_y > max_y) {
        new_y = max_y;
        speed_y = 0;
    }
    
    x = new_x;
    y = new_y;
    
    // Collision detection
    int int_x = FIXED_TO_INT(x);
    int int_y = FIXED_TO_INT(y);
    
    for (int j = 0; j < 5; j++) {
        for (int i = 0; i < 6; i++) {
            if (int_x >= i * MAP_SCALE && int_y >= j * MAP_SCALE && 
                int_x < (i + 1) * MAP_SCALE && int_y < (j + 1) * MAP_SCALE) {
                
                switch (map[j][i]) {
                    case 1: collide_corner(i * MAP_SCALE, (j + 1) * MAP_SCALE); break;
                    case 2: collide_corner((i + 1) * MAP_SCALE, (j + 1) * MAP_SCALE); break;
                    case 3: collide_corner((i + 1) * MAP_SCALE, j * MAP_SCALE); break;
                    case 4: collide_corner(i * MAP_SCALE, j * MAP_SCALE); break;
                    case 5: collide_horiz(i * MAP_SCALE, j * MAP_SCALE, MAP_SCALE); break;
                    case 6: collide_vert(i * MAP_SCALE, j * MAP_SCALE, MAP_SCALE); break;
                }
            }
        }
    }
    
    // Update LED based on current state
    update_led();
    
    // Draw car (with dirty region optimization)
    draw_car();
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
    
    // Initialize lookup tables and LED
    init_trig_tables();
    init_led();
    
    printf("Racing game started!\n");
    printf("Controls: Y=Left, X=Right, Y+X=Accelerate, Release=Brake, A=Reset\n");
    
    while (true) {
        buttons_update(); // Update button states
        game_loop();
        sleep_ms(16); // ~60 FPS
    }
    
    return 0;
}
