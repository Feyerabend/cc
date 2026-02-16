#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

#include "pico/stdlib.h"
#include "pico/time.h"
#include "display.h"

// Map configuration
#define MAP_SIZE 16
#define TILE_SIZE 64

// Rendering settings
#define FOV (3.14159f / 3.0f)  // 60 degrees
#define NUM_RAYS DISPLAY_WIDTH
#define MAX_DEPTH 800.0f
#define WALL_HEIGHT_SCALE 8000.0f

// Player movement
#define MOVE_SPEED 3.0f
#define TURN_SPEED 0.08f
#define COLLISION_RADIUS 20.0f

// Target and shooting settings
#define MAX_TARGETS 10
#define TARGET_RADIUS 15.0f
#define PROJECTILE_SPEED 8.0f
#define PROJECTILE_LIFETIME 60  // frames
#define SHOOT_COOLDOWN 15       // frames

// Map: 0 = empty, 1 = wall, 2 = pillar
static const uint8_t map[MAP_SIZE][MAP_SIZE] = {
    {1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1},
    {1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1},
    {1,0,0,0,0,0,2,0,0,0,0,0,0,0,0,1},
    {1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1},
    {1,0,0,0,0,0,0,0,0,2,0,0,0,0,0,1},
    {1,0,2,0,0,0,0,0,0,0,0,0,0,0,0,1},
    {1,0,0,0,0,1,1,1,0,0,0,0,0,0,0,1},
    {1,0,0,0,0,1,0,1,0,0,0,0,0,2,0,1},
    {1,0,0,0,0,1,0,1,0,0,0,0,0,0,0,1},
    {1,0,2,0,0,0,0,0,0,0,1,1,1,0,0,1},
    {1,0,0,0,0,0,0,0,0,0,1,0,1,0,0,1},
    {1,0,0,0,0,0,2,0,0,0,1,0,1,0,0,1},
    {1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1},
    {1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1},
    {1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1},
    {1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1}
};

// Player state
static struct {
    float x;
    float y;
    float angle;
} player;

// Target structure - simplified
typedef struct {
    float x;
    float y;
    bool active;
} target_t;

// Projectile structure
typedef struct {
    float x;
    float y;
    float vx;
    float vy;
    int lifetime;
    bool active;
} projectile_t;

// Game state
static target_t targets[MAX_TARGETS];
static projectile_t projectile;
static int shoot_cooldown = 0;
static int score = 0;
static int total_targets = 0;

// Framebuffer
static uint16_t framebuffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];

// Button state tracking
static bool btn_state[4] = {false, false, false, false};

// Fast sine/cosine approximation using lookup table
#define TRIG_TABLE_SIZE 360
static float sin_table[TRIG_TABLE_SIZE];
static float cos_table[TRIG_TABLE_SIZE];

static void init_trig_tables(void) {
    for (int i = 0; i < TRIG_TABLE_SIZE; i++) {
        float angle = (i * 2.0f * 3.14159f) / TRIG_TABLE_SIZE;
        sin_table[i] = sinf(angle);
        cos_table[i] = cosf(angle);
    }
}

static inline float fast_sin(float angle) {
    // Normalize angle to 0-2π
    while (angle < 0) angle += 2.0f * 3.14159f;
    while (angle >= 2.0f * 3.14159f) angle -= 2.0f * 3.14159f;
    
    int index = (int)((angle * TRIG_TABLE_SIZE) / (2.0f * 3.14159f)) % TRIG_TABLE_SIZE;
    return sin_table[index];
}

static inline float fast_cos(float angle) {
    while (angle < 0) angle += 2.0f * 3.14159f;
    while (angle >= 2.0f * 3.14159f) angle -= 2.0f * 3.14159f;
    
    int index = (int)((angle * TRIG_TABLE_SIZE) / (2.0f * 3.14159f)) % TRIG_TABLE_SIZE;
    return cos_table[index];
}

// Initialize targets at random positions
static void init_targets(void) {
    total_targets = 0;
    score = 0;
    
    // Predefined target positions in WIDE OPEN areas
    const struct { int x; int y; } positions[] = {
        {3, 3},   // Top left open area
        {7, 3},   // Top middle
        {12, 3},  // Top right open area
        {3, 7},   // Left middle
        {12, 7},  // Right middle  
        {7, 9},   // Center area
        {3, 12},  // Bottom left
        {7, 13},  // Bottom middle
        {12, 12}, // Bottom right
        {10, 10}  // Another center spot
    };
    
    for (int i = 0; i < MAX_TARGETS; i++) {
        targets[i].x = positions[i].x * TILE_SIZE + TILE_SIZE / 2;
        targets[i].y = positions[i].y * TILE_SIZE + TILE_SIZE / 2;
        targets[i].active = true;
        total_targets++;
        
        printf("Target %d at map (%d,%d) = world (%.1f,%.1f)\n", 
               i, positions[i].x, positions[i].y, targets[i].x, targets[i].y);
    }
    
    // Initialize projectile as inactive
    projectile.active = false;
}

// Check collision with map
static bool is_colliding(float x, float y) {
    int mapX = (int)(x / TILE_SIZE);
    int mapY = (int)(y / TILE_SIZE);
    
    // Check surrounding tiles
    for (int dy = -1; dy <= 1; dy++) {
        for (int dx = -1; dx <= 1; dx++) {
            int checkX = mapX + dx;
            int checkY = mapY + dy;
            
            // Bounds check
            if (checkX < 0 || checkX >= MAP_SIZE || checkY < 0 || checkY >= MAP_SIZE) {
                return true;
            }
            
            if (map[checkY][checkX] != 0) {
                // Calculate distance to tile center
                float tileCenterX = (checkX + 0.5f) * TILE_SIZE;
                float tileCenterY = (checkY + 0.5f) * TILE_SIZE;
                float dx_dist = x - tileCenterX;
                float dy_dist = y - tileCenterY;
                float dist = sqrtf(dx_dist * dx_dist + dy_dist * dy_dist);
                
                if (dist < TILE_SIZE / 2.0f + COLLISION_RADIUS) {
                    return true;
                }
            }
        }
    }
    return false;
}

// Update player position based on button input
static void update_player(void) {
    // Get current button states
    bool left = button_pressed(BUTTON_B);   // Turn left
    bool right = button_pressed(BUTTON_Y);  // Turn right
    bool forward = button_pressed(BUTTON_A); // Move forward
    bool shoot = button_just_pressed(BUTTON_X); // Shoot
    
    // Shooting
    if (shoot && shoot_cooldown == 0 && !projectile.active) {
        projectile.x = player.x;
        projectile.y = player.y;
        projectile.vx = fast_cos(player.angle) * PROJECTILE_SPEED;
        projectile.vy = fast_sin(player.angle) * PROJECTILE_SPEED;
        projectile.lifetime = PROJECTILE_LIFETIME;
        projectile.active = true;
        shoot_cooldown = SHOOT_COOLDOWN;
    }
    
    // Cooldown
    if (shoot_cooldown > 0) shoot_cooldown--;
    
    // Rotation
    if (left) {
        player.angle -= TURN_SPEED;
    }
    if (right) {
        player.angle += TURN_SPEED;
    }
    
    // Normalize angle
    while (player.angle < 0) player.angle += 2.0f * 3.14159f;
    while (player.angle >= 2.0f * 3.14159f) player.angle -= 2.0f * 3.14159f;
    
    // Movement
    float moveX = 0;
    float moveY = 0;
    
    if (forward) {
        moveX = fast_cos(player.angle) * MOVE_SPEED;
        moveY = fast_sin(player.angle) * MOVE_SPEED;
    }
    
    // Apply movement with collision detection
    float newX = player.x + moveX;
    float newY = player.y + moveY;
    
    // Check if we can move to the new position (both axes together)
    if (!is_colliding(newX, newY)) {
        // Clear path - move normally
        player.x = newX;
        player.y = newY;
    } else {
        // Blocked - try sliding along walls
        // Try X only (slide along Y-axis walls)
        if (!is_colliding(newX, player.y)) {
            player.x = newX;
        }
        // Try Y only (slide along X-axis walls)
        if (!is_colliding(player.x, newY)) {
            player.y = newY;
        }
        // If both fail, don't move (stuck in corner)
    }
}

// Update projectile physics and collision
static void update_projectile(void) {
    if (!projectile.active) return;
    
    projectile.lifetime--;
    if (projectile.lifetime <= 0) {
        projectile.active = false;
        return;
    }
    
    // Move projectile
    projectile.x += projectile.vx;
    projectile.y += projectile.vy;
    
    // Check wall collision
    int mapX = (int)(projectile.x / TILE_SIZE);
    int mapY = (int)(projectile.y / TILE_SIZE);
    
    if (mapX < 0 || mapX >= MAP_SIZE || mapY < 0 || mapY >= MAP_SIZE || map[mapY][mapX] != 0) {
        projectile.active = false;
        return;
    }
    
    // Check target collision
    for (int i = 0; i < MAX_TARGETS; i++) {
        if (!targets[i].active) continue;
        
        float dx = projectile.x - targets[i].x;
        float dy = projectile.y - targets[i].y;
        float dist = sqrtf(dx * dx + dy * dy);
        
        if (dist < TARGET_RADIUS) {
            targets[i].active = false;
            projectile.active = false;
            score++;
            printf("HIT! Score: %d/%d\n", score, total_targets);
            return;
        }
    }
}

// Cast a single ray
typedef struct {
    float distance;
    uint8_t hit_type;
} ray_result_t;

static ray_result_t cast_ray(float angle) {
    float sin_a = fast_sin(angle);
    float cos_a = fast_cos(angle);
    
    float distance = 0;
    bool hit_wall = false;
    uint8_t hit_type = 0;
    
    // Step along ray
    while (!hit_wall && distance < MAX_DEPTH) {
        distance += 1.0f;  // Step size
        
        float testX = player.x + cos_a * distance;
        float testY = player.y + sin_a * distance;
        
        int mapX = (int)(testX / TILE_SIZE);
        int mapY = (int)(testY / TILE_SIZE);
        
        // Boundary check
        if (mapX < 0 || mapX >= MAP_SIZE || mapY < 0 || mapY >= MAP_SIZE) {
            hit_wall = true;
            distance = MAX_DEPTH;
        } else if (map[mapY][mapX] != 0) {
            hit_wall = true;
            hit_type = map[mapY][mapX];
        }
    }
    
    ray_result_t result = {distance, hit_type};
    return result;
}

// Convert RGB to RGB565
static inline uint16_t rgb_to_rgb565(uint8_t r, uint8_t g, uint8_t b) {
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3);
}

// Target rendering - simple structure to hold sprite data
typedef struct {
    float distance;
    int screenX;
    int screenY;
    int size;
    uint16_t color;
} sprite_render_t;

// Render the 3D view
static void render_3d_view(void) {
    // Clear framebuffer - ceiling and floor
    uint16_t ceiling_color = rgb_to_rgb565(51, 51, 51);   // Dark gray ceiling
    uint16_t floor_color = rgb_to_rgb565(102, 102, 102);  // Lighter gray floor
    
    int half_height = DISPLAY_HEIGHT / 2;
    
    // Fill ceiling
    for (int y = 0; y < half_height; y++) {
        for (int x = 0; x < DISPLAY_WIDTH; x++) {
            framebuffer[y * DISPLAY_WIDTH + x] = ceiling_color;
        }
    }
    
    // Fill floor
    for (int y = half_height; y < DISPLAY_HEIGHT; y++) {
        for (int x = 0; x < DISPLAY_WIDTH; x++) {
            framebuffer[y * DISPLAY_WIDTH + x] = floor_color;
        }
    }
    
    // Z-buffer for proper rendering order
    float zbuffer[NUM_RAYS];
    for (int i = 0; i < NUM_RAYS; i++) zbuffer[i] = MAX_DEPTH;
    
    // Cast rays for each column (walls)
    for (int x = 0; x < NUM_RAYS; x++) {
        float rayAngle = player.angle - FOV / 2.0f + (x / (float)NUM_RAYS) * FOV;
        ray_result_t ray = cast_ray(rayAngle);
        
        // Fix fish-eye effect
        float distance = ray.distance * fast_cos(rayAngle - player.angle);
        zbuffer[x] = distance;
        
        // Prevent division by zero
        if (distance < 0.1f) distance = 0.1f;
        
        // Calculate wall height
        int wallHeight = (int)(WALL_HEIGHT_SCALE / distance);
        if (wallHeight > DISPLAY_HEIGHT * 2) wallHeight = DISPLAY_HEIGHT * 2;
        
        // Calculate brightness based on distance
        float brightness = 1.0f - (distance / MAX_DEPTH);
        if (brightness < 0) brightness = 0;
        if (brightness > 1.0f) brightness = 1.0f;
        
        uint8_t bright_val = (uint8_t)(brightness * 255);
        
        // Different colors for different wall types
        uint16_t wall_color;
        if (ray.hit_type == 1) {
            // Regular walls - reddish
            wall_color = rgb_to_rgb565(bright_val, bright_val / 2, bright_val / 2);
        } else if (ray.hit_type == 2) {
            // Pillars - blueish
            wall_color = rgb_to_rgb565(bright_val / 2, (bright_val * 4) / 5, bright_val);
        } else {
            wall_color = rgb_to_rgb565(bright_val, bright_val, bright_val);
        }
        
        // Calculate wall drawing bounds
        int wallTop = (DISPLAY_HEIGHT - wallHeight) / 2;
        int wallBottom = (DISPLAY_HEIGHT + wallHeight) / 2;
        
        // Clamp to screen bounds
        if (wallTop < 0) wallTop = 0;
        if (wallBottom >= DISPLAY_HEIGHT) wallBottom = DISPLAY_HEIGHT - 1;
        
        // Draw vertical line (wall slice)
        for (int y = wallTop; y <= wallBottom; y++) {
            framebuffer[y * DISPLAY_WIDTH + x] = wall_color;
        }
    }
    
    // Render targets as DIAMOND SHAPES (easier to see and aim at!)
    int targets_in_range = 0;
    int targets_in_fov = 0;
    int targets_rendered = 0;
    
    for (int i = 0; i < MAX_TARGETS; i++) {
        if (!targets[i].active) continue;
        
        float dx = targets[i].x - player.x;
        float dy = targets[i].y - player.y;
        float distance = sqrtf(dx * dx + dy * dy);
        
        if (distance < 1.0f || distance > MAX_DEPTH) continue;
        targets_in_range++;
        
        // Calculate angle to target
        float angle_to_target = atan2f(dy, dx);
        float angle_diff = angle_to_target - player.angle;
        
        // Normalize angle difference
        while (angle_diff > 3.14159f) angle_diff -= 2.0f * 3.14159f;
        while (angle_diff < -3.14159f) angle_diff += 2.0f * 3.14159f;
        
        // Check if target is in FOV
        if (angle_diff < -FOV / 2.0f || angle_diff > FOV / 2.0f) continue;
        targets_in_fov++;
        
        // Calculate which screen column this target appears in
        int screenX = (int)(DISPLAY_WIDTH / 2 + (angle_diff / FOV) * DISPLAY_WIDTH);
        if (screenX < 0 || screenX >= DISPLAY_WIDTH) continue;
        
        // Check z-buffer - only draw if target is closer than wall at this position
        if (distance >= zbuffer[screenX]) {
            // Target is behind a wall, skip it
            continue;
        }
        
        targets_rendered++;
        
        // Calculate target size based on distance
        int targetSize = (int)(WALL_HEIGHT_SCALE / distance);
        if (targetSize < 10) targetSize = 10;
        if (targetSize > DISPLAY_HEIGHT) targetSize = DISPLAY_HEIGHT;
        
        // BRIGHT YELLOW with ORANGE outline for visibility
        uint16_t target_fill = rgb_to_rgb565(255, 255, 0);   // Yellow
        uint16_t target_edge = rgb_to_rgb565(255, 128, 0);   // Orange
        
        int centerY = DISPLAY_HEIGHT / 2;
        int halfSize = targetSize / 2;
        
        // Draw diamond shape:
        // Top half (point at top, widening downward)
        for (int y = 0; y <= halfSize; y++) {
            int width = y; // Width increases as we go down
            for (int x = -width; x <= width; x++) {
                int px = screenX + x;
                int py = centerY - halfSize + y;
                
                if (px >= 0 && px < DISPLAY_WIDTH && py >= 0 && py < DISPLAY_HEIGHT) {
                    // Orange edge on outline
                    if (x == -width || x == width || y == 0) {
                        framebuffer[py * DISPLAY_WIDTH + px] = target_edge;
                    } else {
                        framebuffer[py * DISPLAY_WIDTH + px] = target_fill;
                    }
                }
            }
        }
        
        // Bottom half (widest at middle, narrowing to point)
        for (int y = 0; y <= halfSize; y++) {
            int width = halfSize - y; // Width decreases as we go down
            for (int x = -width; x <= width; x++) {
                int px = screenX + x;
                int py = centerY + y;
                
                if (px >= 0 && px < DISPLAY_WIDTH && py >= 0 && py < DISPLAY_HEIGHT) {
                    // Orange edge on outline
                    if (x == -width || x == width || y == halfSize) {
                        framebuffer[py * DISPLAY_WIDTH + px] = target_edge;
                    } else {
                        framebuffer[py * DISPLAY_WIDTH + px] = target_fill;
                    }
                }
            }
        }
        
        // Add a small red center dot for aiming
        int dot_size = targetSize / 10;
        if (dot_size < 1) dot_size = 1;
        if (dot_size > 3) dot_size = 3;
        
        for (int dy = -dot_size; dy <= dot_size; dy++) {
            for (int dx = -dot_size; dx <= dot_size; dx++) {
                int px = screenX + dx;
                int py = centerY + dy;
                if (px >= 0 && px < DISPLAY_WIDTH && py >= 0 && py < DISPLAY_HEIGHT) {
                    framebuffer[py * DISPLAY_WIDTH + px] = rgb_to_rgb565(255, 0, 0);
                }
            }
        }
    }
    
    // Render projectile with PROPER distance scaling
    if (projectile.active) {
        float dx = projectile.x - player.x;
        float dy = projectile.y - player.y;
        float distance = sqrtf(dx * dx + dy * dy);
        
        if (distance > 1.0f && distance < MAX_DEPTH) {
            float angle_to_proj = atan2f(dy, dx);
            float angle_diff = angle_to_proj - player.angle;
            
            while (angle_diff > 3.14159f) angle_diff -= 2.0f * 3.14159f;
            while (angle_diff < -3.14159f) angle_diff += 2.0f * 3.14159f;
            
            if (angle_diff >= -FOV / 2.0f && angle_diff <= FOV / 2.0f) {
                int screenX = (int)(DISPLAY_WIDTH / 2 + (angle_diff / FOV) * DISPLAY_WIDTH);
                
                if (screenX >= 0 && screenX < DISPLAY_WIDTH) {
                    // FIX: Much stronger distance scaling - should shrink dramatically with distance
                    // Using same formula as walls for consistency
                    int projSize = (int)(WALL_HEIGHT_SCALE / distance * 0.15f);
                    if (projSize < 3) projSize = 3;
                    if (projSize > 40) projSize = 40;
                    
                    int projScreenY = DISPLAY_HEIGHT / 2;
                    
                    // Bright red projectile for contrast
                    uint16_t proj_color = rgb_to_rgb565(255, 0, 0); // Bright red
                    uint16_t proj_glow = rgb_to_rgb565(255, 255, 0); // Yellow center
                    
                    // Draw projectile as circle with glow
                    int proj_radius = projSize / 2;
                    for (int dy = -proj_radius; dy <= proj_radius; dy++) {
                        for (int dx = -proj_radius; dx <= proj_radius; dx++) {
                            int distSq = dx*dx + dy*dy;
                            if (distSq > proj_radius*proj_radius) continue;
                            
                            int px = screenX + dx;
                            int py = projScreenY + dy;
                            
                            if (px >= 0 && px < DISPLAY_WIDTH && py >= 0 && py < DISPLAY_HEIGHT) {
                                // Yellow glow in center
                                if (distSq < (proj_radius/2)*(proj_radius/2)) {
                                    framebuffer[py * DISPLAY_WIDTH + px] = proj_glow;
                                } else {
                                    framebuffer[py * DISPLAY_WIDTH + px] = proj_color;
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Draw HUD directly to framebuffer - score and targets remaining  
    // (We'll use simple pixel drawing instead of display_draw_string)
    
    // Draw mini-map in top-right corner
    int map_start_x = DISPLAY_WIDTH - 85;
    int map_start_y = 5;
    int map_scale = 5;
    
    // Draw map background
    for (int y = 0; y < MAP_SIZE * map_scale; y++) {
        for (int x = 0; x < MAP_SIZE * map_scale; x++) {
            int px = map_start_x + x;
            int py = map_start_y + y;
            if (px >= 0 && px < DISPLAY_WIDTH && py >= 0 && py < DISPLAY_HEIGHT) {
                int mapX = x / map_scale;
                int mapY = y / map_scale;
                uint16_t color;
                if (map[mapY][mapX] != 0) {
                    color = rgb_to_rgb565(100, 100, 100); // Gray walls
                } else {
                    color = rgb_to_rgb565(20, 20, 20); // Dark floor
                }
                framebuffer[py * DISPLAY_WIDTH + px] = color;
            }
        }
    }
    
    // Draw targets on mini-map
    for (int i = 0; i < MAX_TARGETS; i++) {
        if (!targets[i].active) continue;
        
        int tx = map_start_x + (int)((targets[i].x / TILE_SIZE) * map_scale);
        int ty = map_start_y + (int)((targets[i].y / TILE_SIZE) * map_scale);
        
        // Draw target as cyan dot
        for (int dy = -1; dy <= 1; dy++) {
            for (int dx = -1; dx <= 1; dx++) {
                int px = tx + dx;
                int py = ty + dy;
                if (px >= 0 && px < DISPLAY_WIDTH && py >= 0 && py < DISPLAY_HEIGHT) {
                    framebuffer[py * DISPLAY_WIDTH + px] = rgb_to_rgb565(0, 255, 255);
                }
            }
        }
    }
    
    // Draw player on mini-map as RED dot
    int px_player = map_start_x + (int)((player.x / TILE_SIZE) * map_scale);
    int py_player = map_start_y + (int)((player.y / TILE_SIZE) * map_scale);
    
    // Draw player as bright red dot (2x2 for visibility)
    for (int dy = -1; dy <= 1; dy++) {
        for (int dx = -1; dx <= 1; dx++) {
            int px = px_player + dx;
            int py = py_player + dy;
            if (px >= 0 && px < DISPLAY_WIDTH && py >= 0 && py < DISPLAY_HEIGHT) {
                framebuffer[py * DISPLAY_WIDTH + px] = rgb_to_rgb565(255, 0, 0);
            }
        }
    }
    
    // DEBUG WINDOW - show target rendering stats
    // Draw background box for debug info
    int debug_x = 5;
    int debug_y = DISPLAY_HEIGHT - 40;
    for (int y = debug_y - 2; y < debug_y + 30; y++) {
        for (int x = debug_x - 2; x < debug_x + 110; x++) {
            if (x >= 0 && x < DISPLAY_WIDTH && y >= 0 && y < DISPLAY_HEIGHT) {
                framebuffer[y * DISPLAY_WIDTH + x] = rgb_to_rgb565(20, 20, 40);
            }
        }
    }
    
    // Debug text
    char debug_buf[32];
    snprintf(debug_buf, sizeof(debug_buf), "TGTS RANGE:%d", targets_in_range);
    draw_string_to_fb(framebuffer, debug_x, debug_y, debug_buf, COLOR_WHITE);
    
    snprintf(debug_buf, sizeof(debug_buf), "     FOV:%d", targets_in_fov);
    draw_string_to_fb(framebuffer, debug_x, debug_y + 8, debug_buf, COLOR_WHITE);
    
    snprintf(debug_buf, sizeof(debug_buf), "     DRAW:%d", targets_rendered);
    draw_string_to_fb(framebuffer, debug_x, debug_y + 16, debug_buf, COLOR_YELLOW);
    
    snprintf(debug_buf, sizeof(debug_buf), "POS:%.0f.%.0f", player.x, player.y);
    draw_string_to_fb(framebuffer, debug_x, debug_y + 24, debug_buf, COLOR_CYAN);
    
    // Draw score text DIRECTLY to framebuffer (before blit!)
    char hud_text[32];
    snprintf(hud_text, sizeof(hud_text), "SCORE:%d/%d", score, total_targets);
    draw_string_to_fb(framebuffer, 5, 5, hud_text, COLOR_WHITE);
    
    if (score >= total_targets) {
        draw_string_to_fb(framebuffer, DISPLAY_WIDTH/2 - 20, DISPLAY_HEIGHT/2 - 3, "YOU WIN!", COLOR_GREEN);
    }
    
    // NOW blit everything to display at once - this includes the text!
    display_blit_full(framebuffer);
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
    
    display_clear(COLOR_BLACK);
    display_set_backlight(true);
    
    
    // Init trig tables for speed
    init_trig_tables();
    
    // Init player position
    player.x = TILE_SIZE * 2;
    player.y = TILE_SIZE * 2;
    player.angle = 0;
    
    // Init targets
    init_targets();
    
    printf("Player starting at (%.1f, %.1f)\n", player.x, player.y);
    printf("Targets: %d\n", total_targets);
    printf("Controls: A=Forward, B=Left, Y=Right, X=Shoot\n");
    printf("Starting render loop..\n");
    
    uint32_t frame_count = 0;
    
    while (1) {
        buttons_update();
        
        // Update player
        uint32_t update_start = to_ms_since_boot(get_absolute_time());
        update_player();
        update_projectile();
        uint32_t update_time = to_ms_since_boot(get_absolute_time()) - update_start;
        
        // Render
        uint32_t render_start = to_ms_since_boot(get_absolute_time());
        render_3d_view();
        uint32_t render_time = to_ms_since_boot(get_absolute_time()) - render_start;
        
        frame_count++;
        
        if (frame_count % 30 == 0) {
            int active_count = 0;
            for (int i = 0; i < MAX_TARGETS; i++) {
                if (targets[i].active) active_count++;
            }
            printf("Frame %lu: Update=%lums Render=%lums (%.1f fps) Pos=(%.1f, %.1f) Angle=%.2f Targets:%d\n",
                   frame_count, update_time, render_time, 
                   1000.0f / (update_time + render_time),
                   player.x, player.y, player.angle, active_count);
        }
        
        // Small delay for stability
        sleep_ms(10);
    }
    
    return 0;
}

