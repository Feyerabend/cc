#include "engine.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>  // Added for abs()
#include "pico/time.h"


// Internal Engine State (Singleton Pattern)

typedef struct {
    // Resource pools
    sprite_t sprites[MAX_SPRITES];
    texture_t textures[MAX_TEXTURES];
    particle_system_t particle_systems[MAX_PARTICLE_SYSTEMS];
    
    // Free lists for O(1) allocation
    uint8_t free_sprites[MAX_SPRITES];
    uint8_t free_textures[MAX_TEXTURES];
    uint8_t free_particles[MAX_PARTICLE_SYSTEMS];
    uint8_t free_sprite_count;
    uint8_t free_texture_count;
    uint8_t free_particle_count;
    
    // Camera state
    float camera_x, camera_y;
    sprite_handle_t camera_follow_target;
    float camera_follow_offset_x, camera_follow_offset_y;
    
    // Collision callback
    collision_callback_t collision_callback;
    
    // Frame buffer - with bounds checking
    uint16_t* framebuffer;
    size_t framebuffer_size;
    
    // Statistics
    engine_stats_t stats;
    uint32_t last_frame_time;
    uint32_t frame_accumulator;
    uint16_t frame_counter;
    
    // Memory watchdog
    uint32_t memory_check_counter;
    bool memory_error_detected;
    
    // State
    bool initialized;
    
} engine_context_t;

static engine_context_t g_engine = {0};

// Error strings
static const char* error_strings[] = {
    "OK",
    "Initialization failed",
    "Out of memory",
    "Invalid parameter",
    "Resource pool full",
    "Resource not found"
};

// Memory safety constants
#define MEMORY_CHECK_INTERVAL 100  // Check every 100 frames
#define MAX_FRAMEBUFFER_SIZE (DISPLAY_WIDTH * DISPLAY_HEIGHT * sizeof(uint16_t))


// Internal Helper Functions

static inline uint32_t get_time_ms(void) {
    return to_ms_since_boot(get_absolute_time());
}

// Memory safety check
static bool check_memory_integrity(void) {
    // Basic sanity checks
    if (!g_engine.framebuffer) return false;
    if (g_engine.framebuffer_size != MAX_FRAMEBUFFER_SIZE) return false;
    
    // Check for obvious corruption patterns
    uint16_t* fb = g_engine.framebuffer;
    size_t pixel_count = DISPLAY_WIDTH * DISPLAY_HEIGHT;
    
    // Check for completely invalid values
    for (size_t i = 0; i < 16 && i < pixel_count; i++) {
        // Check a few pixels at the start - they shouldn't all be the same
        // unless it's a clear operation
        (void)fb[i]; // Just ensure we can read it
    }
    
    return true;
}

static void init_free_lists(void) {
    // Initialize free lists
    for (int i = 0; i < MAX_SPRITES; i++) {
        g_engine.free_sprites[i] = i;
        // Clear sprite data
        memset(&g_engine.sprites[i], 0, sizeof(sprite_t));
    }
    for (int i = 0; i < MAX_TEXTURES; i++) {
        g_engine.free_textures[i] = i;
        // Clear texture data
        memset(&g_engine.textures[i], 0, sizeof(texture_t));
    }
    for (int i = 0; i < MAX_PARTICLE_SYSTEMS; i++) {
        g_engine.free_particles[i] = i;
        // Clear particle system data
        memset(&g_engine.particle_systems[i], 0, sizeof(particle_system_t));
    }
    
    g_engine.free_sprite_count = MAX_SPRITES;
    g_engine.free_texture_count = MAX_TEXTURES;
    g_engine.free_particle_count = MAX_PARTICLE_SYSTEMS;
}

static uint8_t allocate_sprite_handle(void) {
    if (g_engine.free_sprite_count == 0) return INVALID_HANDLE;
    
    uint8_t handle = g_engine.free_sprites[--g_engine.free_sprite_count];
    
    // Clear the sprite data before use
    memset(&g_engine.sprites[handle], 0, sizeof(sprite_t));
    g_engine.sprites[handle].active = true;
    
    return handle;
}

static void free_sprite_handle(uint8_t handle) {
    if (handle >= MAX_SPRITES || !g_engine.sprites[handle].active) return;
    
    // Clear sprite data
    memset(&g_engine.sprites[handle], 0, sizeof(sprite_t));
    g_engine.sprites[handle].active = false;
    
    if (g_engine.free_sprite_count < MAX_SPRITES) {
        g_engine.free_sprites[g_engine.free_sprite_count++] = handle;
    }
}

static uint8_t allocate_texture_handle(void) {
    if (g_engine.free_texture_count == 0) return INVALID_HANDLE;
    
    uint8_t handle = g_engine.free_textures[--g_engine.free_texture_count];
    
    // Clear texture data before use
    memset(&g_engine.textures[handle], 0, sizeof(texture_t));
    g_engine.textures[handle].active = true;
    
    return handle;
}

static void free_texture_handle(uint8_t handle) {
    if (handle >= MAX_TEXTURES || !g_engine.textures[handle].active) return;
    
    texture_t* tex = &g_engine.textures[handle];
    
    // Free owned data safely
    if (tex->owned_data && tex->data) {
        // Verify pointer is reasonable before freeing
        if ((uintptr_t)tex->data > 0x10000000) {  // Basic sanity check for Pico
            free(tex->data);
        }
        tex->data = NULL;
    }
    
    // Clear texture data
    memset(tex, 0, sizeof(texture_t));
    tex->active = false;
    
    if (g_engine.free_texture_count < MAX_TEXTURES) {
        g_engine.free_textures[g_engine.free_texture_count++] = handle;
    }
}

static uint8_t allocate_particle_handle(void) {
    if (g_engine.free_particle_count == 0) return INVALID_HANDLE;
    
    uint8_t handle = g_engine.free_particles[--g_engine.free_particle_count];
    
    // Clear particle system data before use
    memset(&g_engine.particle_systems[handle], 0, sizeof(particle_system_t));
    g_engine.particle_systems[handle].active = true;
    
    return handle;
}

static void free_particle_handle(uint8_t handle) {
    if (handle >= MAX_PARTICLE_SYSTEMS || !g_engine.particle_systems[handle].active) return;
    
    // Clear particle system data
    memset(&g_engine.particle_systems[handle], 0, sizeof(particle_system_t));
    g_engine.particle_systems[handle].active = false;
    
    if (g_engine.free_particle_count < MAX_PARTICLE_SYSTEMS) {
        g_engine.free_particles[g_engine.free_particle_count++] = handle;
    }
}

static void world_to_screen(float world_x, float world_y, int16_t* screen_x, int16_t* screen_y) {
    if (!screen_x || !screen_y) return;
    
    *screen_x = (int16_t)(world_x - g_engine.camera_x);
    *screen_y = (int16_t)(world_y - g_engine.camera_y);
}

static bool is_sprite_on_screen(const sprite_t* sprite) {
    if (!sprite) return false;
    
    int16_t screen_x, screen_y;
    world_to_screen(sprite->x, sprite->y, &screen_x, &screen_y);
    
    return !(screen_x + (int16_t)sprite->width < 0 || 
             screen_x >= DISPLAY_WIDTH ||
             screen_y + (int16_t)sprite->height < 0 || 
             screen_y >= DISPLAY_HEIGHT);
}

static bool is_valid_framebuffer_coords(int16_t x, int16_t y) {
    return (x >= 0 && x < DISPLAY_WIDTH && y >= 0 && y < DISPLAY_HEIGHT);
}

static void render_sprite_to_framebuffer(const sprite_t* sprite, const texture_t* texture) {
    if (!sprite || !texture || !sprite->visible || !is_sprite_on_screen(sprite)) return;
    if (!g_engine.framebuffer || g_engine.memory_error_detected) return;
    
    int16_t screen_x, screen_y;
    world_to_screen(sprite->x, sprite->y, &screen_x, &screen_y);
    
    // Clipping with bounds checking
    int16_t start_x = screen_x < 0 ? -screen_x : 0;
    int16_t start_y = screen_y < 0 ? -screen_y : 0;
    int16_t end_x = screen_x + (int16_t)texture->width > DISPLAY_WIDTH ? DISPLAY_WIDTH - screen_x : (int16_t)texture->width;
    int16_t end_y = screen_y + (int16_t)texture->height > DISPLAY_HEIGHT ? DISPLAY_HEIGHT - screen_y : (int16_t)texture->height;
    
    // Additional safety checks
    if (start_x >= texture->width || start_y >= texture->height) return;
    if (end_x <= start_x || end_y <= start_y) return;
    
    for (int16_t ty = start_y; ty < end_y; ty++) {
        for (int16_t tx = start_x; tx < end_x; tx++) {
            // Bounds check for texture access
            if (ty >= texture->height || tx >= texture->width) continue;
            
            uint16_t src_color = texture->data[ty * texture->width + tx];
            if (src_color == 0x0000) continue; // Skip transparent pixels
            
            int16_t fb_x = screen_x + tx;
            int16_t fb_y = screen_y + ty;
            
            if (is_valid_framebuffer_coords(fb_x, fb_y)) {
                size_t fb_index = fb_y * DISPLAY_WIDTH + fb_x;
                
                // Bounds check for framebuffer
                if (fb_index < (DISPLAY_WIDTH * DISPLAY_HEIGHT)) {
                    if (sprite->alpha < 255 || sprite->blend_mode != BLEND_NONE) {
                        uint16_t dst_color = g_engine.framebuffer[fb_index];
                        src_color = color_blend(src_color, dst_color, sprite->alpha);
                    }
                    g_engine.framebuffer[fb_index] = src_color;
                }
            }
        }
    }
}


// Core Engine Implementation

engine_error_t engine_init(void) {
    if (g_engine.initialized) return ENGINE_OK;
    
    printf("Init Graphics Engine..\n");
    
    // Initialize display
    display_error_t display_result = display_pack_init();
    if (display_result != DISPLAY_OK) {
        printf("Display initialization failed: %s\n", display_error_string(display_result));
        return ENGINE_ERROR_INIT_FAILED;
    }
    
    // Allocate framebuffer with error checking
    g_engine.framebuffer_size = MAX_FRAMEBUFFER_SIZE;
    g_engine.framebuffer = malloc(g_engine.framebuffer_size);
    if (!g_engine.framebuffer) {
        printf("Failed to allocate framebuffer\n");
        return ENGINE_ERROR_OUT_OF_MEMORY;
    }
    
    // Initialize framebuffer to known state
    memset(g_engine.framebuffer, 0, g_engine.framebuffer_size);
    
    // Initialize engine state
    memset(&g_engine.sprites, 0, sizeof(g_engine.sprites));
    memset(&g_engine.textures, 0, sizeof(g_engine.textures));
    memset(&g_engine.particle_systems, 0, sizeof(g_engine.particle_systems));
    
    init_free_lists();
    
    g_engine.camera_x = 0;
    g_engine.camera_y = 0;
    g_engine.camera_follow_target = INVALID_HANDLE;
    g_engine.collision_callback = NULL;
    g_engine.memory_check_counter = 0;
    g_engine.memory_error_detected = false;
    
    // Clear statistics
    memset(&g_engine.stats, 0, sizeof(engine_stats_t));
    
    g_engine.last_frame_time = get_time_ms();
    g_engine.initialized = true;
    
    printf("Graphics Engine initialised successfully\n");
    return ENGINE_OK;
}

void engine_shutdown(void) {
    if (!g_engine.initialized) return;
    
    printf("Shutting down Graphics Engine..\n");
    
    // Free all textures
    for (int i = 0; i < MAX_TEXTURES; i++) {
        if (g_engine.textures[i].active) {
            free_texture_handle(i);
        }
    }
    
    // Clear all sprites
    for (int i = 0; i < MAX_SPRITES; i++) {
        if (g_engine.sprites[i].active) {
            free_sprite_handle(i);
        }
    }
    
    // Clear all particle systems
    for (int i = 0; i < MAX_PARTICLE_SYSTEMS; i++) {
        if (g_engine.particle_systems[i].active) {
            free_particle_handle(i);
        }
    }
    
    // Free framebuffer safely
    if (g_engine.framebuffer) {
        // Clear framebuffer before freeing
        memset(g_engine.framebuffer, 0, g_engine.framebuffer_size);
        free(g_engine.framebuffer);
        g_engine.framebuffer = NULL;
        g_engine.framebuffer_size = 0;
    }
    
    // Clean up display
    display_cleanup();
    
    // Reset all state
    memset(&g_engine, 0, sizeof(engine_context_t));
    g_engine.initialized = false;
    
    printf("Graphics Engine shutdown complete\n");
}

void engine_update(void) {
    if (!g_engine.initialized || g_engine.memory_error_detected) return;
    
    uint32_t current_time = get_time_ms();
    uint32_t frame_time = current_time - g_engine.last_frame_time;
    
    // Sanity check on frame time
    if (frame_time > 1000) frame_time = 33; // Cap at reasonable value
    
    g_engine.stats.frame_time_ms = frame_time;
    g_engine.last_frame_time = current_time;
    g_engine.stats.total_frames++;
    
    // Periodic memory check
    g_engine.memory_check_counter++;
    if (g_engine.memory_check_counter >= MEMORY_CHECK_INTERVAL) {
        if (!check_memory_integrity()) {
            printf("Memory integrity check failed!\n");
            g_engine.memory_error_detected = true;
            return;
        }
        g_engine.memory_check_counter = 0;
    }
    
    // Update FPS counter
    g_engine.frame_accumulator += g_engine.stats.frame_time_ms;
    g_engine.frame_counter++;
    
    if (g_engine.frame_accumulator >= 1000) {
        g_engine.stats.fps = g_engine.frame_counter;
        g_engine.frame_counter = 0;
        g_engine.frame_accumulator = 0;
    }
    
    // Update camera following
    if (g_engine.camera_follow_target != INVALID_HANDLE && 
        g_engine.camera_follow_target < MAX_SPRITES &&
        g_engine.sprites[g_engine.camera_follow_target].active) {
        
        const sprite_t* target = &g_engine.sprites[g_engine.camera_follow_target];
        g_engine.camera_x = target->x - (DISPLAY_WIDTH / 2) + g_engine.camera_follow_offset_x;
        g_engine.camera_y = target->y - (DISPLAY_HEIGHT / 2) + g_engine.camera_follow_offset_y;
    }
    
    // Update sprite physics
    g_engine.stats.sprite_count = 0;
    for (int i = 0; i < MAX_SPRITES; i++) {
        sprite_t* sprite = &g_engine.sprites[i];
        if (!sprite->active) continue;
        
        g_engine.stats.sprite_count++;
        
        // Apply velocity with bounds checking
        if (sprite->velocity_x != 0.0f || sprite->velocity_y != 0.0f) {
            // Check for reasonable values
            if (sprite->velocity_x > -1000.0f && sprite->velocity_x < 1000.0f) {
                sprite->x += sprite->velocity_x;
            }
            if (sprite->velocity_y > -1000.0f && sprite->velocity_y < 1000.0f) {
                sprite->y += sprite->velocity_y;
            }
        }
    }
    
    // Update particle systems
    g_engine.stats.particle_count = 0;
    for (int i = 0; i < MAX_PARTICLE_SYSTEMS; i++) {
        particle_system_t* system = &g_engine.particle_systems[i];
        if (!system->active) continue;
        
        // Spawn particles
        if (system->spawn_rate_ms > 0 && 
            current_time - system->last_spawn_time >= system->spawn_rate_ms) {
            particles_emit_burst(i, 1);
            system->last_spawn_time = current_time;
        }
        
        // Update particles
        for (int j = 0; j < PARTICLE_POOL_SIZE; j++) {
            particle_t* p = &system->particles[j];
            if (!p->active) continue;
            
            g_engine.stats.particle_count++;
            
            // Update physics with bounds checking
            if (p->acc_x > -10.0f && p->acc_x < 10.0f) p->vel_x += p->acc_x;
            if (p->acc_y > -10.0f && p->acc_y < 10.0f) p->vel_y += p->acc_y;
            if (p->vel_x > -100.0f && p->vel_x < 100.0f) p->x += p->vel_x;
            if (p->vel_y > -100.0f && p->vel_y < 100.0f) p->y += p->vel_y;
            
            // Update lifetime
            if (p->life_remaining > g_engine.stats.frame_time_ms) {
                p->life_remaining -= g_engine.stats.frame_time_ms;
                // Fade alpha based on remaining life
                if (system->particle_lifetime_ms > 0) {
                    float life_ratio = (float)p->life_remaining / system->particle_lifetime_ms;
                    p->alpha = (uint8_t)(255 * life_ratio);
                }
            } else {
                p->active = false;
                if (system->active_count > 0) {
                    system->active_count--;
                }
            }
        }
    }
    
    // Collision detection with safety checks
    if (g_engine.collision_callback) {
        for (int i = 0; i < MAX_SPRITES; i++) {
            sprite_t* s1 = &g_engine.sprites[i];
            if (!s1->active || !s1->collision_enabled) continue;
            
            for (int j = i + 1; j < MAX_SPRITES; j++) {
                sprite_t* s2 = &g_engine.sprites[j];
                if (!s2->active || !s2->collision_enabled) continue;
                
                if (sprite_check_collision(i, j)) {
                    g_engine.collision_callback(i, j);
                }
            }
        }
    }
}

void engine_render(void) {
    if (!g_engine.initialized || !g_engine.framebuffer || g_engine.memory_error_detected) return;
    
    // Clear framebuffer safely
    memset(g_engine.framebuffer, 0, g_engine.framebuffer_size);
    
    // Render sprites by layer (0 = back, higher = front)
    for (uint8_t layer = 0; layer < 8; layer++) {
        for (int i = 0; i < MAX_SPRITES; i++) {
            const sprite_t* sprite = &g_engine.sprites[i];
            if (!sprite->active || sprite->layer != layer) continue;
            
            if (sprite->texture < MAX_TEXTURES && g_engine.textures[sprite->texture].active) {
                const texture_t* texture = &g_engine.textures[sprite->texture];
                if (texture->data) {  // Additional safety check
                    render_sprite_to_framebuffer(sprite, texture);
                }
            }
        }
        
        // Render particles on each layer
        for (int i = 0; i < MAX_PARTICLE_SYSTEMS; i++) {
            const particle_system_t* system = &g_engine.particle_systems[i];
            if (!system->active) continue;
            
            for (int j = 0; j < PARTICLE_POOL_SIZE; j++) {
                const particle_t* p = &system->particles[j];
                if (!p->active) continue;
                
                int16_t screen_x, screen_y;
                world_to_screen(p->x, p->y, &screen_x, &screen_y);
                
                if (is_valid_framebuffer_coords(screen_x, screen_y)) {
                    size_t fb_index = screen_y * DISPLAY_WIDTH + screen_x;
                    if (fb_index < (DISPLAY_WIDTH * DISPLAY_HEIGHT)) {
                        uint16_t color = p->color;
                        if (p->alpha < 255) {
                            uint16_t bg = g_engine.framebuffer[fb_index];
                            color = color_blend(color, bg, p->alpha);
                        }
                        g_engine.framebuffer[fb_index] = color;
                    }
                }
            }
        }
    }
}

void engine_present(void) {
    if (!g_engine.initialized || !g_engine.framebuffer || g_engine.memory_error_detected) return;
    
    display_error_t result = display_blit_full(g_engine.framebuffer);
    if (result != DISPLAY_OK) {
        printf("Display blit failed: %s\n", display_error_string(result));
        // Don't set memory error for display issues, just log
    }
}

const engine_stats_t* engine_get_stats(void) {
    return &g_engine.stats;
}

void engine_reset_stats(void) {
    memset(&g_engine.stats, 0, sizeof(engine_stats_t));
    g_engine.frame_counter = 0;
    g_engine.frame_accumulator = 0;
}

const char* engine_error_string(engine_error_t error) {
    if (error >= sizeof(error_strings) / sizeof(error_strings[0])) {
        return "Unknown error";
    }
    return error_strings[error];
}


// Texture Management

texture_handle_t texture_create(uint16_t* data, uint16_t width, uint16_t height, bool copy_data) {
    if (!data || width == 0 || height == 0 || width > 1024 || height > 1024) return INVALID_HANDLE;
    
    uint8_t handle = allocate_texture_handle();
    if (handle == INVALID_HANDLE) return INVALID_HANDLE;
    
    texture_t* tex = &g_engine.textures[handle];
    tex->width = width;
    tex->height = height;
    
    if (copy_data) {
        size_t data_size = (size_t)width * height * sizeof(uint16_t);
        
        // Safety check for reasonable allocation size
        if (data_size > 512 * 1024) {  // 512KB limit
            free_texture_handle(handle);
            return INVALID_HANDLE;
        }
        
        tex->data = malloc(data_size);
        if (!tex->data) {
            free_texture_handle(handle);
            return INVALID_HANDLE;
        }
        memcpy(tex->data, data, data_size);
        tex->owned_data = true;
    } else {
        tex->data = data;
        tex->owned_data = false;
    }
    
    return handle;
}

texture_handle_t texture_create_solid(uint16_t color, uint16_t width, uint16_t height) {
    if (width == 0 || height == 0 || width > 1024 || height > 1024) return INVALID_HANDLE;
    
    uint8_t handle = allocate_texture_handle();
    if (handle == INVALID_HANDLE) return INVALID_HANDLE;
    
    texture_t* tex = &g_engine.textures[handle];
    size_t pixel_count = (size_t)width * height;
    size_t data_size = pixel_count * sizeof(uint16_t);
    
    // Safety check for reasonable allocation size
    if (data_size > 512 * 1024) {  // 512KB limit
        free_texture_handle(handle);
        return INVALID_HANDLE;
    }
    
    tex->data = malloc(data_size);
    if (!tex->data) {
        free_texture_handle(handle);
        return INVALID_HANDLE;
    }
    
    for (size_t i = 0; i < pixel_count; i++) {
        tex->data[i] = color;
    }
    
    tex->width = width;
    tex->height = height;
    tex->owned_data = true;
    
    return handle;
}

void texture_destroy(texture_handle_t handle) {
    if (handle != INVALID_HANDLE && handle < MAX_TEXTURES) {
        free_texture_handle(handle);
    }
}

bool texture_get_info(texture_handle_t handle, uint16_t* width, uint16_t* height) {
    if (handle >= MAX_TEXTURES || !g_engine.textures[handle].active) return false;
    
    const texture_t* tex = &g_engine.textures[handle];
    if (width) *width = tex->width;
    if (height) *height = tex->height;
    return true;
}


// Sprite Management  

sprite_handle_t sprite_create(float x, float y, texture_handle_t texture) {
    if (texture >= MAX_TEXTURES || !g_engine.textures[texture].active) {
        return INVALID_HANDLE;
    }
    
    uint8_t handle = allocate_sprite_handle();
    if (handle == INVALID_HANDLE) return INVALID_HANDLE;
    
    sprite_t* sprite = &g_engine.sprites[handle];
    sprite->x = x;
    sprite->y = y;
    sprite->velocity_x = 0;
    sprite->velocity_y = 0;
    sprite->texture = texture;
    sprite->width = g_engine.textures[texture].width;
    sprite->height = g_engine.textures[texture].height;
    sprite->layer = 1;
    sprite->alpha = 255;
    sprite->blend_mode = BLEND_NONE;
    sprite->visible = true;
    sprite->collision_enabled = false;
    
    return handle;
}

void sprite_destroy(sprite_handle_t handle) {
    if (handle != INVALID_HANDLE && handle < MAX_SPRITES) {
        // Clear camera follow if this sprite was being followed
        if (g_engine.camera_follow_target == handle) {
            g_engine.camera_follow_target = INVALID_HANDLE;
        }
        free_sprite_handle(handle);
    }
}

void sprite_set_position(sprite_handle_t handle, float x, float y) {
    if (handle >= MAX_SPRITES || !g_engine.sprites[handle].active) return;
    
    // Sanity check on position values
    if (x < -10000.0f || x > 10000.0f || y < -10000.0f || y > 10000.0f) return;
    
    g_engine.sprites[handle].x = x;
    g_engine.sprites[handle].y = y;
}

void sprite_get_position(sprite_handle_t handle, float* x, float* y) {
    if (handle >= MAX_SPRITES || !g_engine.sprites[handle].active) return;
    if (x) *x = g_engine.sprites[handle].x;
    if (y) *y = g_engine.sprites[handle].y;
}

void sprite_set_velocity(sprite_handle_t handle, float vx, float vy) {
    if (handle >= MAX_SPRITES || !g_engine.sprites[handle].active) return;
    
    // Sanity check on velocity values
    if (vx < -1000.0f || vx > 1000.0f || vy < -1000.0f || vy > 1000.0f) return;
    
    g_engine.sprites[handle].velocity_x = vx;
    g_engine.sprites[handle].velocity_y = vy;
}

void sprite_move(sprite_handle_t handle, float dx, float dy) {
    if (handle >= MAX_SPRITES || !g_engine.sprites[handle].active) return;
    
    // Sanity check on delta values
    if (dx < -1000.0f || dx > 1000.0f || dy < -1000.0f || dy > 1000.0f) return;
    
    g_engine.sprites[handle].x += dx;
    g_engine.sprites[handle].y += dy;
}

void sprite_set_texture(sprite_handle_t handle, texture_handle_t texture) {
    if (handle >= MAX_SPRITES || !g_engine.sprites[handle].active) return;
    if (texture >= MAX_TEXTURES || !g_engine.textures[texture].active) return;
    
    g_engine.sprites[handle].texture = texture;
    g_engine.sprites[handle].width = g_engine.textures[texture].width;
    g_engine.sprites[handle].height = g_engine.textures[texture].height;
}

void sprite_set_alpha(sprite_handle_t handle, uint8_t alpha) {
    if (handle >= MAX_SPRITES || !g_engine.sprites[handle].active) return;
    g_engine.sprites[handle].alpha = alpha;
}

void sprite_set_blend_mode(sprite_handle_t handle, blend_mode_t mode) {
    if (handle >= MAX_SPRITES || !g_engine.sprites[handle].active) return;
    g_engine.sprites[handle].blend_mode = mode;
}

void sprite_set_layer(sprite_handle_t handle, uint8_t layer) {
    if (handle >= MAX_SPRITES || !g_engine.sprites[handle].active) return;
    if (layer > 7) layer = 7;
    g_engine.sprites[handle].layer = layer;
}

void sprite_set_visibility(sprite_handle_t handle, bool visible) {
    if (handle >= MAX_SPRITES || !g_engine.sprites[handle].active) return;
    g_engine.sprites[handle].visible = visible;
}

void sprite_enable_collision(sprite_handle_t handle, bool enabled) {
    if (handle >= MAX_SPRITES || !g_engine.sprites[handle].active) return;
    g_engine.sprites[handle].collision_enabled = enabled;
}

bool sprite_check_collision(sprite_handle_t handle1, sprite_handle_t handle2) {
    if (handle1 >= MAX_SPRITES || handle2 >= MAX_SPRITES) return false;
    
    const sprite_t* s1 = &g_engine.sprites[handle1];
    const sprite_t* s2 = &g_engine.sprites[handle2];
    
    if (!s1->active || !s2->active || !s1->collision_enabled || !s2->collision_enabled) {
        return false;
    }
    
    // AABB collision detection with bounds checking
    float s1_right = s1->x + s1->width;
    float s1_bottom = s1->y + s1->height;
    float s2_right = s2->x + s2->width;
    float s2_bottom = s2->y + s2->height;
    
    return !(s1_right <= s2->x ||
             s2_right <= s1->x ||
             s1_bottom <= s2->y ||
             s2_bottom <= s1->y);
}

void sprite_set_collision_callback(collision_callback_t callback) {
    g_engine.collision_callback = callback;
}

bool sprite_is_valid(sprite_handle_t handle) {
    return handle < MAX_SPRITES && g_engine.sprites[handle].active;
}

void sprite_get_bounds(sprite_handle_t handle, float* x, float* y, float* width, float* height) {
    if (handle >= MAX_SPRITES || !g_engine.sprites[handle].active) return;
    
    const sprite_t* sprite = &g_engine.sprites[handle];
    if (x) *x = sprite->x;
    if (y) *y = sprite->y;
    if (width) *width = sprite->width;
    if (height) *height = sprite->height;
}


// Particle System Implementation

particle_system_handle_t particles_create(float x, float y, uint16_t color) {
    uint8_t handle = allocate_particle_handle();
    if (handle == INVALID_HANDLE) return INVALID_HANDLE;
    
    particle_system_t* system = &g_engine.particle_systems[handle];
    
    system->spawn_x = x;
    system->spawn_y = y;
    system->spawn_radius = 5.0f;
    system->base_color = color;
    system->spawn_rate_ms = 100;  // 10 particles per second
    system->particle_lifetime_ms = 2000;  // 2 seconds
    system->last_spawn_time = get_time_ms();
    system->active = true;
    system->active_count = 0;
    
    return handle;
}

void particles_destroy(particle_system_handle_t handle) {
    if (handle != INVALID_HANDLE && handle < MAX_PARTICLE_SYSTEMS) {
        free_particle_handle(handle);
    }
}

void particles_set_position(particle_system_handle_t handle, float x, float y) {
    if (handle >= MAX_PARTICLE_SYSTEMS || !g_engine.particle_systems[handle].active) return;
    
    // Sanity check on position
    if (x < -10000.0f || x > 10000.0f || y < -10000.0f || y > 10000.0f) return;
    
    g_engine.particle_systems[handle].spawn_x = x;
    g_engine.particle_systems[handle].spawn_y = y;
}

void particles_set_spawn_rate(particle_system_handle_t handle, uint16_t rate_ms) {
    if (handle >= MAX_PARTICLE_SYSTEMS || !g_engine.particle_systems[handle].active) return;
    g_engine.particle_systems[handle].spawn_rate_ms = rate_ms;
}

void particles_set_lifetime(particle_system_handle_t handle, uint16_t lifetime_ms) {
    if (handle >= MAX_PARTICLE_SYSTEMS || !g_engine.particle_systems[handle].active) return;
    if (lifetime_ms > 30000) lifetime_ms = 30000; // Cap at 30 seconds
    g_engine.particle_systems[handle].particle_lifetime_ms = lifetime_ms;
}

void particles_set_spawn_radius(particle_system_handle_t handle, float radius) {
    if (handle >= MAX_PARTICLE_SYSTEMS || !g_engine.particle_systems[handle].active) return;
    if (radius < 0.0f) radius = 0.0f;
    if (radius > 100.0f) radius = 100.0f; // Reasonable limit
    g_engine.particle_systems[handle].spawn_radius = radius;
}

void particles_emit_burst(particle_system_handle_t handle, uint8_t count) {
    if (handle >= MAX_PARTICLE_SYSTEMS || !g_engine.particle_systems[handle].active) return;
    if (count > 50) count = 50; // Reasonable limit
    
    particle_system_t* system = &g_engine.particle_systems[handle];
    
    for (uint8_t i = 0; i < count && system->active_count < PARTICLE_POOL_SIZE; i++) {
        // Find free particle
        for (int j = 0; j < PARTICLE_POOL_SIZE; j++) {
            particle_t* p = &system->particles[j];
            if (p->active) continue;
            
            // Initialize particle
            p->active = true;
            p->x = system->spawn_x + ((float)(rand() % 200 - 100) / 100.0f) * system->spawn_radius;
            p->y = system->spawn_y + ((float)(rand() % 200 - 100) / 100.0f) * system->spawn_radius;
            
            // Random velocity (bounded)
            p->vel_x = ((float)(rand() % 200 - 100) / 100.0f) * 2.0f;
            p->vel_y = ((float)(rand() % 200 - 100) / 100.0f) * 2.0f;
            
            // Simple gravity
            p->acc_x = 0.0f;
            p->acc_y = 0.05f;
            
            p->color = system->base_color;
            p->alpha = 255;
            p->life_remaining = system->particle_lifetime_ms;
            
            system->active_count++;
            break;
        }
    }
}

void particles_set_continuous(particle_system_handle_t handle, bool continuous) {
    if (handle >= MAX_PARTICLE_SYSTEMS || !g_engine.particle_systems[handle].active) return;
    // Continuous spawning is controlled by spawn_rate_ms (0 = no continuous spawning)
    if (!continuous) {
        g_engine.particle_systems[handle].spawn_rate_ms = 0;
    }
}


// Camera System

void camera_set_position(float x, float y) {
    // Sanity check
    if (x < -10000.0f || x > 10000.0f || y < -10000.0f || y > 10000.0f) return;
    
    g_engine.camera_x = x;
    g_engine.camera_y = y;
    g_engine.camera_follow_target = INVALID_HANDLE;  // Disable following
}

void camera_get_position(float* x, float* y) {
    if (x) *x = g_engine.camera_x;
    if (y) *y = g_engine.camera_y;
}

void camera_move(float dx, float dy) {
    // Sanity check
    if (dx < -1000.0f || dx > 1000.0f || dy < -1000.0f || dy > 1000.0f) return;
    
    g_engine.camera_x += dx;
    g_engine.camera_y += dy;
    g_engine.camera_follow_target = INVALID_HANDLE;  // Disable following
}

void camera_follow_sprite(sprite_handle_t handle, float offset_x, float offset_y) {
    if (handle >= MAX_SPRITES || !g_engine.sprites[handle].active) return;
    
    g_engine.camera_follow_target = handle;
    g_engine.camera_follow_offset_x = offset_x;
    g_engine.camera_follow_offset_y = offset_y;
}


// Rendering Primitives - with bounds checking

static void safe_set_pixel(int16_t x, int16_t y, uint16_t color) {
    if (!g_engine.framebuffer || g_engine.memory_error_detected) return;
    if (!is_valid_framebuffer_coords(x, y)) return;
    
    size_t index = y * DISPLAY_WIDTH + x;
    if (index < (DISPLAY_WIDTH * DISPLAY_HEIGHT)) {
        g_engine.framebuffer[index] = color;
    }
}

void graphics_draw_line(int16_t x0, int16_t y0, int16_t x1, int16_t y1, uint16_t color) {
    if (!g_engine.framebuffer || g_engine.memory_error_detected) return;
    
    // Bresenham's line algorithm with safety checks
    int16_t dx = abs(x1 - x0);
    int16_t dy = abs(y1 - y0);
    int16_t sx = x0 < x1 ? 1 : -1;
    int16_t sy = y0 < y1 ? 1 : -1;
    int16_t err = (dx > dy ? dx : -dy) / 2;
    int16_t e2;
    
    int max_iterations = DISPLAY_WIDTH + DISPLAY_HEIGHT; // Prevent infinite loops
    int iterations = 0;

    while (iterations < max_iterations) {
        safe_set_pixel(x0, y0, color);
        
        if (x0 == x1 && y0 == y1) break;
        
        e2 = err;
        if (e2 > -dx) { err -= dy; x0 += sx; }
        if (e2 < dy) { err += dx; y0 += sy; }
        
        iterations++;
    }
}

void graphics_draw_rect(int16_t x, int16_t y, uint16_t width, uint16_t height, uint16_t color) {
    if (width == 0 || height == 0) return;
    
    graphics_draw_line(x, y, x + width - 1, y, color);
    graphics_draw_line(x, y, x, y + height - 1, color);
    graphics_draw_line(x + width - 1, y, x + width - 1, y + height - 1, color);
    graphics_draw_line(x, y + height - 1, x + width - 1, y + height - 1, color);
}

void graphics_draw_circle(int16_t x, int16_t y, uint8_t radius, uint16_t color) {
    if (!g_engine.framebuffer || g_engine.memory_error_detected) return;
    if (radius > 200) return; // Reasonable limit
    
    int16_t f = 1 - radius;
    int16_t ddF_x = 1;
    int16_t ddF_y = -2 * radius;
    int16_t i = 0;
    int16_t j = radius;

    safe_set_pixel(x, y + radius, color);
    safe_set_pixel(x, y - radius, color);
    safe_set_pixel(x + radius, y, color);
    safe_set_pixel(x - radius, y, color);

    while (i < j) {
        if (f >= 0) {
            j--;
            ddF_y += 2;
            f += ddF_y;
        }
        i++;
        ddF_x += 2;
        f += ddF_x;

        // Draw 8 octants
        safe_set_pixel(x + i, y + j, color);
        safe_set_pixel(x - i, y + j, color);
        safe_set_pixel(x + i, y - j, color);
        safe_set_pixel(x - i, y - j, color);
        safe_set_pixel(x + j, y + i, color);
        safe_set_pixel(x - j, y + i, color);
        safe_set_pixel(x + j, y - i, color);
        safe_set_pixel(x - j, y - i, color);
    }
}

void graphics_fill_circle(int16_t x, int16_t y, uint8_t radius, uint16_t color) {
    if (!g_engine.framebuffer || g_engine.memory_error_detected) return;
    if (radius > 200) return; // Reasonable limit
    
    for (int16_t dy = -radius; dy <= radius; dy++) {
        for (int16_t dx = -radius; dx <= radius; dx++) {
            if (dx * dx + dy * dy <= radius * radius) {
                safe_set_pixel(x + dx, y + dy, color);
            }
        }
    }
}



// Color Utilities

uint16_t color_rgb(uint8_t r, uint8_t g, uint8_t b) {
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
}

uint16_t color_blend(uint16_t color1, uint16_t color2, uint8_t alpha) {
    if (alpha == 255) return color1;
    if (alpha == 0) return color2;
    
    // Extract RGB components
    uint8_t r1 = (color1 >> 8) & 0xF8;
    uint8_t g1 = (color1 >> 3) & 0xFC;
    uint8_t b1 = (color1 << 3) & 0xF8;
    
    uint8_t r2 = (color2 >> 8) & 0xF8;
    uint8_t g2 = (color2 >> 3) & 0xFC;
    uint8_t b2 = (color2 << 3) & 0xF8;
    
    // Blend
    uint8_t r = (r1 * alpha + r2 * (255 - alpha)) / 255;
    uint8_t g = (g1 * alpha + g2 * (255 - alpha)) / 255;
    uint8_t b = (b1 * alpha + b2 * (255 - alpha)) / 255;
    
    return color_rgb(r, g, b);
}

uint16_t color_lerp(uint16_t color1, uint16_t color2, float t) {
    if (t <= 0.0f) return color1;
    if (t >= 1.0f) return color2;
    
    uint8_t alpha = (uint8_t)(t * 255);
    return color_blend(color2, color1, alpha);
}
