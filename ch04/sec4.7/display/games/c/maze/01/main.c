#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "pico/stdlib.h"
#include "pico/time.h"
#include "display.h"

// Simple maze (1 = wall, 0 = empty, 2 = goal)
#define MAZE_WIDTH 10
#define MAZE_HEIGHT 10

static const uint8_t maze[MAZE_HEIGHT][MAZE_WIDTH] = {
    {1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
    {1, 0, 0, 0, 1, 0, 0, 0, 0, 1},
    {1, 0, 1, 0, 1, 0, 1, 1, 0, 1},
    {1, 0, 1, 0, 0, 0, 0, 1, 0, 1},
    {1, 0, 1, 1, 1, 1, 0, 1, 0, 1},
    {1, 0, 0, 0, 0, 0, 0, 1, 0, 1},
    {1, 1, 1, 0, 1, 1, 1, 1, 0, 1},
    {1, 0, 0, 0, 1, 0, 0, 0, 0, 1},
    {1, 0, 1, 0, 0, 0, 1, 1, 2, 1},
    {1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
};

// Player state
static float player_x = 1.5f;
static float player_y = 1.5f;
static float player_angle = 0.0f;

// Rendering constants
#define FOV 60.0f
#define RENDER_DISTANCE 10.0f
#define WALL_HEIGHT_SCALE 100.0f

// Framebuffer
static uint16_t framebuffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];

// Game state
static bool game_won = false;
static uint32_t start_time = 0;
static uint32_t end_time = 0;

// Minimap state
static bool show_minimap = false;
static uint32_t minimap_hide_time = 0;
#define MINIMAP_DISPLAY_DURATION 3000  // Show for 3 seconds

// Movement constants
#define MOVE_SPEED 0.3f
#define TURN_SPEED 0.15f

// Forward declarations
static void fb_draw_string(uint16_t x, uint16_t y, const char* str, uint16_t color, uint16_t bg_color);
static void fb_draw_char(uint16_t x, uint16_t y, char c, uint16_t color, uint16_t bg_color);

// Check if position is valid (not wall)
static bool is_valid_position(float x, float y) {
    int grid_x = (int)x;
    int grid_y = (int)y;
    
    if (grid_x < 0 || grid_x >= MAZE_WIDTH || grid_y < 0 || grid_y >= MAZE_HEIGHT) {
        return false;
    }
    
    return maze[grid_y][grid_x] != 1;
}

// Check if player reached goal
static bool check_goal(float x, float y) {
    int grid_x = (int)x;
    int grid_y = (int)y;
    
    if (grid_x < 0 || grid_x >= MAZE_WIDTH || grid_y < 0 || grid_y >= MAZE_HEIGHT) {
        return false;
    }
    
    return maze[grid_y][grid_x] == 2;
}

// Cast a single ray and return distance to wall
static float cast_ray(float start_x, float start_y, float angle, bool *hit_vertical, bool *is_north_south) {
    float ray_dx = cosf(angle);
    float ray_dy = sinf(angle);
    
    float t = 0.0f;
    float step = 0.05f;
    
    *hit_vertical = false;
    *is_north_south = false;
    
    while (t < RENDER_DISTANCE) {
        t += step;
        float test_x = start_x + ray_dx * t;
        float test_y = start_y + ray_dy * t;
        
        int grid_x = (int)test_x;
        int grid_y = (int)test_y;
        
        if (grid_x < 0 || grid_x >= MAZE_WIDTH || grid_y < 0 || grid_y >= MAZE_HEIGHT) {
            return t;
        }
        
        if (maze[grid_y][grid_x] == 1) {
            // Determine if we hit a vertical or horizontal wall
            float frac_x = test_x - grid_x;
            float frac_y = test_y - grid_y;
            
            // Check which side of the cell we hit
            if (frac_x < 0.1f || frac_x > 0.9f) {
                *hit_vertical = true;  // East/West wall
                *is_north_south = false;
            } else {
                *hit_vertical = false;  // North/South wall
                *is_north_south = true;
            }
            
            return t;
        }
    }
    
    return RENDER_DISTANCE;
}

// Clear framebuffer
static void fb_clear(uint16_t color) {
    for (int i = 0; i < DISPLAY_WIDTH * DISPLAY_HEIGHT; i++) {
        framebuffer[i] = color;
    }
}

// Render the 3D view - SIMPLE and FAST
static void render_3d_view(void) {
    float angle_step = (FOV * M_PI / 180.0f) / DISPLAY_WIDTH;
    float start_angle = player_angle - (FOV * M_PI / 180.0f) / 2.0f;
    
    // Draw entire scene column by column
    for (int x = 0; x < DISPLAY_WIDTH; x++) {
        float ray_angle = start_angle + x * angle_step;
        bool hit_vertical = false;
        bool is_north_south = false;
        float distance = cast_ray(player_x, player_y, ray_angle, &hit_vertical, &is_north_south);
        
        // Fix fisheye
        distance *= cosf(ray_angle - player_angle);
        
        // Calculate wall strip height
        int wall_height = (int)(DISPLAY_HEIGHT / distance);
        int wall_top = (DISPLAY_HEIGHT - wall_height) / 2;
        int wall_bottom = wall_top + wall_height;
        
        // Draw this column
        for (int y = 0; y < DISPLAY_HEIGHT; y++) {
            uint16_t color;
            
            if (y < wall_top) {
                // Ceiling - simple gradient
                int dist_from_center = DISPLAY_HEIGHT / 2 - y;
                uint8_t brightness = 20 + dist_from_center / 3;
                if (brightness > 60) brightness = 60;
                color = (brightness >> 3) | ((brightness >> 2) << 5) | ((brightness >> 3) << 11);
                
            } else if (y >= wall_bottom) {
                // Floor - simple gradient
                int dist_from_center = y - DISPLAY_HEIGHT / 2;
                uint8_t brightness = 40 + dist_from_center / 2;
                if (brightness > 100) brightness = 100;
                color = (brightness >> 3) | ((brightness >> 2) << 5) | ((brightness >> 3) << 11);
                
            } else {
                // Wall - gray with distance shading (never pure white)
                uint8_t brightness = 140;  // Start at medium-gray instead of 200
                if (distance > 1.0f) {
                    brightness = 140 - (uint8_t)(distance * 8);
                    if (brightness < 60) brightness = 60;
                }
                color = (brightness >> 3) | ((brightness >> 2) << 5) | ((brightness >> 3) << 11);
            }
            
            framebuffer[y * DISPLAY_WIDTH + x] = color;
        }
    }
}

// Draw minimap
static void draw_minimap(void) {
    int map_size = 10;  // Increased from 8 to 10
    int map_x_offset = 5;
    int map_y_offset = DISPLAY_HEIGHT - MAZE_HEIGHT * map_size - 5;
    
    // Draw black background for minimap
    for (int y = 0; y < MAZE_HEIGHT * map_size + 4; y++) {
        for (int x = 0; x < MAZE_WIDTH * map_size + 4; x++) {
            int px = map_x_offset - 2 + x;
            int py = map_y_offset - 2 + y;
            if (px >= 0 && px < DISPLAY_WIDTH && py >= 0 && py < DISPLAY_HEIGHT) {
                framebuffer[py * DISPLAY_WIDTH + px] = COLOR_BLACK;
            }
        }
    }
    
    // Draw maze
    for (int y = 0; y < MAZE_HEIGHT; y++) {
        for (int x = 0; x < MAZE_WIDTH; x++) {
            uint16_t color = COLOR_BLACK;
            
            if (maze[y][x] == 1) {
                color = COLOR_WHITE;
            } else if (maze[y][x] == 2) {
                color = COLOR_GREEN;
            } else {
                color = 0x4208; // Medium gray (darker than before)
            }
            
            // Draw cell with 1px border
            for (int dy = 1; dy < map_size - 1; dy++) {
                for (int dx = 1; dx < map_size - 1; dx++) {
                    int px = map_x_offset + x * map_size + dx;
                    int py = map_y_offset + y * map_size + dy;
                    if (px < DISPLAY_WIDTH && py < DISPLAY_HEIGHT) {
                        framebuffer[py * DISPLAY_WIDTH + px] = color;
                    }
                }
            }
        }
    }
    
    // Draw player position - BRIGHT BLUE and LARGER
    int player_px = map_x_offset + (int)(player_x * map_size);
    int player_py = map_y_offset + (int)(player_y * map_size);
    
    // Draw a larger bright blue circle for player (4x4 pixels for larger map)
    for (int dy = -2; dy <= 2; dy++) {
        for (int dx = -2; dx <= 2; dx++) {
            int px = player_px + dx;
            int py = player_py + dy;
            if (px >= 0 && px < DISPLAY_WIDTH && py >= 0 && py < DISPLAY_HEIGHT) {
                framebuffer[py * DISPLAY_WIDTH + px] = COLOR_CYAN;  // Bright cyan/blue
            }
        }
    }
    
    // Draw player direction arrow (longer and yellow)
    for (float t = 0.5f; t <= 3.0f; t += 0.3f) {
        int dir_x = player_px + (int)(cosf(player_angle) * map_size * t);
        int dir_y = player_py + (int)(sinf(player_angle) * map_size * t);
        
        if (dir_x >= 0 && dir_x < DISPLAY_WIDTH && dir_y >= 0 && dir_y < DISPLAY_HEIGHT) {
            framebuffer[dir_y * DISPLAY_WIDTH + dir_x] = COLOR_YELLOW;
            // Make arrow thicker
            if (dir_x + 1 < DISPLAY_WIDTH) {
                framebuffer[dir_y * DISPLAY_WIDTH + dir_x + 1] = COLOR_YELLOW;
            }
            if (dir_y + 1 < DISPLAY_HEIGHT) {
                framebuffer[(dir_y + 1) * DISPLAY_WIDTH + dir_x] = COLOR_YELLOW;
            }
        }
    }
}

// Simple 5x8 font
static const uint8_t simple_font[][5] = {
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
    {0x00, 0x41, 0x41, 0x7F, 0x00}, // [
    {0x20, 0x10, 0x08, 0x04, 0x02}, // backslash
    {0x00, 0x7F, 0x41, 0x41, 0x00}, // ]
    {0x04, 0x02, 0x01, 0x02, 0x04}, // ^
    {0x40, 0x40, 0x40, 0x40, 0x40}, // _
    {0x00, 0x04, 0x02, 0x01, 0x00}, // `
    {0x78, 0x54, 0x54, 0x54, 0x20}, // a
    {0x38, 0x44, 0x44, 0x48, 0x7F}, // b
    {0x28, 0x44, 0x44, 0x44, 0x38}, // c
    {0x7F, 0x48, 0x44, 0x44, 0x38}, // d
    {0x18, 0x54, 0x54, 0x54, 0x38}, // e
    {0x02, 0x01, 0x09, 0x7E, 0x08}, // f
    {0x4C, 0x92, 0x92, 0x92, 0x7C}, // g
    {0x78, 0x04, 0x04, 0x08, 0x7F}, // h
    {0x00, 0x44, 0x7D, 0x40, 0x00}, // i
    {0x02, 0x7D, 0x82, 0x80, 0x40}, // j
    {0x44, 0x28, 0x10, 0x08, 0x7F}, // k
    {0x00, 0x40, 0x7F, 0x41, 0x00}, // l
    {0x7C, 0x04, 0x18, 0x04, 0x7C}, // m
    {0x78, 0x04, 0x04, 0x08, 0x7C}, // n
    {0x38, 0x44, 0x44, 0x44, 0x38}, // o
    {0x18, 0x24, 0x24, 0x24, 0xFC}, // p
    {0xFC, 0x24, 0x24, 0x24, 0x18}, // q
    {0x08, 0x04, 0x04, 0x08, 0x7C}, // r
    {0x24, 0x54, 0x54, 0x54, 0x48}, // s
    {0x20, 0x40, 0x44, 0x3F, 0x04}, // t
    {0x3C, 0x40, 0x40, 0x20, 0x7C}, // u
    {0x1C, 0x20, 0x40, 0x20, 0x1C}, // v
    {0x3C, 0x40, 0x30, 0x40, 0x3C}, // w
    {0x44, 0x28, 0x10, 0x28, 0x44}, // x
    {0x7C, 0x90, 0x90, 0x90, 0x4C}, // y
    {0x44, 0x64, 0x54, 0x4C, 0x44}, // z
};

// Draw character to framebuffer
static void fb_draw_char(uint16_t x, uint16_t y, char c, uint16_t color, uint16_t bg_color) {
    if (x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return;
    
    int idx = c - 32;
    if (idx < 0 || idx >= 91) return;
    
    const uint8_t *char_data = simple_font[idx];
    
    for (int col = 0; col < 5 && (x + col) < DISPLAY_WIDTH; col++) {
        uint8_t line = char_data[4 - col];
        for (int row = 0; row < 8 && (y + row) < DISPLAY_HEIGHT; row++) {
            uint16_t pixel_color = (line & (1 << row)) ? color : bg_color;
            framebuffer[(y + row) * DISPLAY_WIDTH + (x + col)] = pixel_color;
        }
    }
}

// Draw string to framebuffer
static void fb_draw_string(uint16_t x, uint16_t y, const char* str, uint16_t color, uint16_t bg_color) {
    int offset_x = 0;
    while (*str && (x + offset_x) < DISPLAY_WIDTH) {
        fb_draw_char(x + offset_x, y, *str, color, bg_color);
        offset_x += 6;
        str++;
    }
}

// Button callbacks
static void btn_a_callback(button_t btn) {
    (void)btn;
    if (game_won) return;
    
    // Move forward
    float new_x = player_x + cosf(player_angle) * MOVE_SPEED;
    float new_y = player_y + sinf(player_angle) * MOVE_SPEED;
    
    if (is_valid_position(new_x, new_y)) {
        player_x = new_x;
        player_y = new_y;
    }
    
    // Check for goal
    if (check_goal(player_x, player_y) && !game_won) {
        game_won = true;
        end_time = to_ms_since_boot(get_absolute_time());
    }
}

static void btn_b_callback(button_t btn) {
    (void)btn;
    if (game_won) return;
    
    // Move backward
    float new_x = player_x - cosf(player_angle) * MOVE_SPEED;
    float new_y = player_y - sinf(player_angle) * MOVE_SPEED;
    
    if (is_valid_position(new_x, new_y)) {
        player_x = new_x;
        player_y = new_y;
    }
}

static void btn_x_callback(button_t btn) {
    (void)btn;
    if (game_won) return;
    
    // Check if Y is also pressed - show minimap
    if (button_pressed(BUTTON_Y)) {
        show_minimap = true;
        minimap_hide_time = to_ms_since_boot(get_absolute_time()) + MINIMAP_DISPLAY_DURATION;
        return;
    }
    
    // Turn left 90 degrees
    player_angle -= M_PI / 2;
    
    // Normalize angle
    while (player_angle < 0) player_angle += 2 * M_PI;
    while (player_angle >= 2 * M_PI) player_angle -= 2 * M_PI;
}

static void btn_y_callback(button_t btn) {
    (void)btn;
    if (game_won) {
        // Reset game
        player_x = 1.5f;
        player_y = 1.5f;
        player_angle = 0.0f;
        game_won = false;
        show_minimap = false;
        start_time = to_ms_since_boot(get_absolute_time());
    } else {
        // Check if X is also pressed - show minimap
        if (button_pressed(BUTTON_X)) {
            show_minimap = true;
            minimap_hide_time = to_ms_since_boot(get_absolute_time()) + MINIMAP_DISPLAY_DURATION;
            return;
        }
        
        // Turn right 90 degrees
        player_angle += M_PI / 2;
        
        // Normalize angle
        while (player_angle < 0) player_angle += 2 * M_PI;
        while (player_angle >= 2 * M_PI) player_angle -= 2 * M_PI;
    }
}

int main(void) {
    stdio_init_all();
    
    if (display_pack_init() != DISPLAY_OK) {
        printf("Display init failed\n");
        return 1;
    }
    
    if (buttons_init() != DISPLAY_OK) {
        printf("Buttons init failed\n");
        return 1;
    }
    
    button_set_callback(BUTTON_A, btn_a_callback);
    button_set_callback(BUTTON_B, btn_b_callback);
    button_set_callback(BUTTON_X, btn_x_callback);
    button_set_callback(BUTTON_Y, btn_y_callback);
    
    display_clear(COLOR_BLACK);
    display_set_backlight(true);
    
    start_time = to_ms_since_boot(get_absolute_time());
    
    printf("Maze Game Started\n");
    printf("Controls:\n");
    printf("  A - Move forward\n");
    printf("  B - Move backward\n");
    printf("  X - Turn left\n");
    printf("  Y - Turn right\n");
    
    while (1) {
        buttons_update();
        
        // Check if minimap should be hidden
        uint32_t current_time = to_ms_since_boot(get_absolute_time());
        if (show_minimap && current_time >= minimap_hide_time) {
            show_minimap = false;
        }
        
        // Render 3D view
        render_3d_view();
        
        // Draw minimap only if visible
        if (show_minimap) {
            draw_minimap();
        }
        
        // Draw UI
        if (game_won) {
            uint32_t elapsed = (end_time - start_time) / 1000;
            char buf[50];
            snprintf(buf, sizeof(buf), "YOU WIN! Time: %lus", elapsed);
            
            // Draw box behind text
            for (int y = 100; y < 130; y++) {
                for (int x = 40; x < 280; x++) {
                    framebuffer[y * DISPLAY_WIDTH + x] = COLOR_BLACK;
                }
            }
            
            fb_draw_string(50, 105, buf, COLOR_GREEN, COLOR_BLACK);
            fb_draw_string(50, 115, "Press Y to restart", COLOR_YELLOW, COLOR_BLACK);
        } else {
            fb_draw_string(5, 5, "X+Y:Map A:Fwd B:Back", COLOR_WHITE, COLOR_BLACK);
            
            // Show elapsed time
            uint32_t elapsed = (current_time - start_time) / 1000;
            char buf[30];
            snprintf(buf, sizeof(buf), "Time: %lus", elapsed);
            fb_draw_string(220, 5, buf, COLOR_CYAN, COLOR_BLACK);
        }
        
        // Blit framebuffer to display
        display_blit_full(framebuffer);
        
        // Small delay to prevent too rapid updates
        sleep_ms(50);
    }
    
    return 0;
}
