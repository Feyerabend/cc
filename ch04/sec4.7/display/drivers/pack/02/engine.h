#ifndef GRAPHICS_ENGINE_H
#define GRAPHICS_ENGINE_H

#include <stdint.h>
#include <stdbool.h>
#include "display.h"

// Engine Configuration - Reduced for embedded constraints
#define MAX_SPRITES 16
#define MAX_TEXTURES 8
#define MAX_PARTICLE_SYSTEMS 2
#define PARTICLE_POOL_SIZE 32

// Error handling
typedef enum {
    ENGINE_OK = 0,
    ENGINE_ERROR_INIT_FAILED,
    ENGINE_ERROR_OUT_OF_MEMORY,
    ENGINE_ERROR_INVALID_PARAM,
    ENGINE_ERROR_RESOURCE_FULL,
    ENGINE_ERROR_NOT_FOUND
} engine_error_t;

// Forward declarations
typedef struct sprite_t sprite_t;
typedef struct texture_t texture_t;
typedef struct particle_system_t particle_system_t;

// Handle system - safer than direct array access
typedef uint8_t sprite_handle_t;
typedef uint8_t texture_handle_t;
typedef uint8_t particle_system_handle_t;

#define INVALID_HANDLE 0xFF

// Blend modes
typedef enum {
    BLEND_NONE = 0,
    BLEND_ALPHA,
    BLEND_ADDITIVE
} blend_mode_t;

// Texture structure - simplified
typedef struct texture_t {
    uint16_t* data;
    uint16_t width;
    uint16_t height;
    bool owned_data;  // Whether engine should free the data
    bool active;
} texture_t;

// Sprite structure - streamlined
typedef struct sprite_t {
    float x, y;                    // Position (float for smooth movement)
    float velocity_x, velocity_y;  // Velocity per frame
    uint16_t width, height;        // Dimensions
    texture_handle_t texture;      // Texture reference
    uint8_t layer;                 // Render layer (0-7)
    uint8_t alpha;                 // Transparency (0-255)
    blend_mode_t blend_mode;
    bool active;
    bool visible;
    bool collision_enabled;
} sprite_t;

// Particle structure
typedef struct {
    float x, y;
    float vel_x, vel_y;
    float acc_x, acc_y;
    uint16_t color;
    uint8_t alpha;
    uint16_t life_remaining;
    bool active;
} particle_t;

// Particle system
typedef struct particle_system_t {
    particle_t particles[PARTICLE_POOL_SIZE];
    float spawn_x, spawn_y;
    float spawn_radius;
    uint16_t base_color;
    uint16_t spawn_rate_ms;  // ms between spawns
    uint16_t particle_lifetime_ms;
    uint32_t last_spawn_time;
    uint8_t active_count;
    bool active;
} particle_system_t;

// Collision callback
typedef void (*collision_callback_t)(sprite_handle_t sprite1, sprite_handle_t sprite2);

// Statistics
typedef struct {
    uint32_t frame_time_ms;
    uint16_t fps;
    uint8_t sprite_count;
    uint8_t particle_count;
    uint32_t total_frames;
} engine_stats_t;



// Core Engine API

// Engine lifecycle
engine_error_t engine_init(void);
void engine_shutdown(void);
void engine_update(void);
void engine_render(void);
void engine_present(void);

// Statistics
const engine_stats_t* engine_get_stats(void);
void engine_reset_stats(void);

// Error handling
const char* engine_error_string(engine_error_t error);



// Texture Management

// Create texture from data (engine takes ownership if copy_data = true)
texture_handle_t texture_create(uint16_t* data, uint16_t width, uint16_t height, bool copy_data);

// Create solid color texture
texture_handle_t texture_create_solid(uint16_t color, uint16_t width, uint16_t height);

// Destroy texture
void texture_destroy(texture_handle_t handle);

// Get texture info
bool texture_get_info(texture_handle_t handle, uint16_t* width, uint16_t* height);


// Sprite Management  

// Create sprite
sprite_handle_t sprite_create(float x, float y, texture_handle_t texture);

// Destroy sprite
void sprite_destroy(sprite_handle_t handle);

// Position and movement
void sprite_set_position(sprite_handle_t handle, float x, float y);
void sprite_get_position(sprite_handle_t handle, float* x, float* y);
void sprite_set_velocity(sprite_handle_t handle, float vx, float vy);
void sprite_move(sprite_handle_t handle, float dx, float dy);

// Appearance
void sprite_set_texture(sprite_handle_t handle, texture_handle_t texture);
void sprite_set_alpha(sprite_handle_t handle, uint8_t alpha);
void sprite_set_blend_mode(sprite_handle_t handle, blend_mode_t mode);
void sprite_set_layer(sprite_handle_t handle, uint8_t layer);
void sprite_set_visibility(sprite_handle_t handle, bool visible);

// Collision
void sprite_enable_collision(sprite_handle_t handle, bool enabled);
bool sprite_check_collision(sprite_handle_t handle1, sprite_handle_t handle2);
void sprite_set_collision_callback(collision_callback_t callback);

// Utility
bool sprite_is_valid(sprite_handle_t handle);
void sprite_get_bounds(sprite_handle_t handle, float* x, float* y, float* width, float* height);



// Particle System

// Create particle system
particle_system_handle_t particles_create(float x, float y, uint16_t color);

// Destroy particle system  
void particles_destroy(particle_system_handle_t handle);

// Configuration
void particles_set_position(particle_system_handle_t handle, float x, float y);
void particles_set_spawn_rate(particle_system_handle_t handle, uint16_t rate_ms);
void particles_set_lifetime(particle_system_handle_t handle, uint16_t lifetime_ms);
void particles_set_spawn_radius(particle_system_handle_t handle, float radius);

// Emission
void particles_emit_burst(particle_system_handle_t handle, uint8_t count);
void particles_set_continuous(particle_system_handle_t handle, bool continuous);


// Camera System

void camera_set_position(float x, float y);
void camera_get_position(float* x, float* y);
void camera_move(float dx, float dy);
void camera_follow_sprite(sprite_handle_t handle, float offset_x, float offset_y);


// Rendering Primitives

void graphics_draw_line(int16_t x0, int16_t y0, int16_t x1, int16_t y1, uint16_t color);
void graphics_draw_rect(int16_t x, int16_t y, uint16_t width, uint16_t height, uint16_t color);
void graphics_draw_circle(int16_t x, int16_t y, uint8_t radius, uint16_t color);
void graphics_fill_circle(int16_t x, int16_t y, uint8_t radius, uint16_t color);


// Color Utilities

uint16_t color_rgb(uint8_t r, uint8_t g, uint8_t b);
uint16_t color_blend(uint16_t color1, uint16_t color2, uint8_t alpha);
uint16_t color_lerp(uint16_t color1, uint16_t color2, float t);

// Common colors
#define ENGINE_COLOR_BLACK     0x0000
#define ENGINE_COLOR_WHITE     0xFFFF
#define ENGINE_COLOR_RED       0xF800
#define ENGINE_COLOR_GREEN     0x07E0
#define ENGINE_COLOR_BLUE      0x001F
#define ENGINE_COLOR_YELLOW    0xFFE0
#define ENGINE_COLOR_CYAN      0x07FF
#define ENGINE_COLOR_MAGENTA   0xF81F

#endif // GRAPHICS_ENGINE_H
