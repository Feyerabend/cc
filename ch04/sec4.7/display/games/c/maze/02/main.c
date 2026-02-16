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
    bool back = button_pressed(BUTTON_X);    // Move backward
    
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
    if (back) {
        moveX = -fast_cos(player.angle) * MOVE_SPEED;
        moveY = -fast_sin(player.angle) * MOVE_SPEED;
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
    
    // Cast rays for each column
    for (int x = 0; x < NUM_RAYS; x++) {
        float rayAngle = player.angle - FOV / 2.0f + (x / (float)NUM_RAYS) * FOV;
        ray_result_t ray = cast_ray(rayAngle);
        
        // Fix fish-eye effect
        float distance = ray.distance * fast_cos(rayAngle - player.angle);
        
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
    
    // Blit to display
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
    
    printf("Player starting at (%.1f, %.1f)\n", player.x, player.y);
    printf("Starting render loop..\n");
    
    uint32_t frame_count = 0;
    
    while (1) {
        buttons_update();
        
        // Update player
        uint32_t update_start = to_ms_since_boot(get_absolute_time());
        update_player();
        uint32_t update_time = to_ms_since_boot(get_absolute_time()) - update_start;
        
        // Render
        uint32_t render_start = to_ms_since_boot(get_absolute_time());
        render_3d_view();
        uint32_t render_time = to_ms_since_boot(get_absolute_time()) - render_start;
        
        frame_count++;
        
        if (frame_count % 30 == 0) {
            printf("Frame %lu: Update=%lums Render=%lums (%.1f fps) Pos=(%.1f, %.1f) Angle=%.2f\n",
                   frame_count, update_time, render_time, 
                   1000.0f / (update_time + render_time),
                   player.x, player.y, player.angle);
        }
        
        // Small delay for stability
        sleep_ms(10);
    }
    
    return 0;
}

