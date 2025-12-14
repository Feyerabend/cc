#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "pico/mutex.h"
#include "hardware/sync.h"
#include "display.h"

// Particle system configuration
#define MAX_PARTICLES 800
#define GRAVITY 0.15f
#define BOUNCE_DAMPING 0.85f
#define PARTICLE_RADIUS 2

// Display boundaries (full screen now)
#define BOUNDS_LEFT 0
#define BOUNDS_RIGHT DISPLAY_WIDTH
#define BOUNDS_TOP 30  // Leave space for status bar
#define BOUNDS_BOTTOM DISPLAY_HEIGHT

// Frame buffer for double buffering (320x240 pixels)
static uint16_t framebuffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];

// Particle structure
typedef struct {
    float x, y;           // Position
    float vx, vy;         // Velocity
    uint16_t color;       // Color
    uint8_t core_id;      // Which core last updated this particle (for visualization)
} Particle;

// Shared state between cores
static Particle particles[MAX_PARTICLES];
static int particle_count = MAX_PARTICLES;
static mutex_t particle_mutex;
static volatile bool core1_ready = false;
static volatile bool rendering_done = true;

// Performance tracking
static volatile uint32_t core0_cycles = 0;
static volatile uint32_t core1_cycles = 0;
static uint32_t last_fps_time = 0;
static int frame_count = 0;
static float current_fps = 0.0f;

// User controls
static float wind_x = 0.0f;
static float wind_y = 0.0f;

// Color palette for particles
static const uint16_t particle_colors[] = {
    COLOR_RED,
    COLOR_GREEN,
    COLOR_BLUE,
    COLOR_YELLOW,
    COLOR_CYAN,
    COLOR_MAGENTA,
    0xFD20,  // Orange
    0x07FF,  // Cyan
    0xF81F,  // Pink
    0xFFE0,  // Yellow
};

// Helper function to draw pixel to framebuffer
static inline void fb_set_pixel(int x, int y, uint16_t color) {
    if (x >= 0 && x < DISPLAY_WIDTH && y >= 0 && y < DISPLAY_HEIGHT) {
        framebuffer[y * DISPLAY_WIDTH + x] = color;
    }
}

// Helper function to fill rectangle in framebuffer
static inline void fb_fill_rect(int x, int y, int w, int h, uint16_t color) {
    for (int dy = 0; dy < h; dy++) {
        int py = y + dy;
        if (py < 0 || py >= DISPLAY_HEIGHT) continue;
        
        for (int dx = 0; dx < w; dx++) {
            int px = x + dx;
            if (px >= 0 && px < DISPLAY_WIDTH) {
                framebuffer[py * DISPLAY_WIDTH + px] = color;
            }
        }
    }
}

// Helper function to create random float between min and max
static inline float randf(float min, float max) {
    return min + (rand() / (float)RAND_MAX) * (max - min);
}

// Initialize particles
void init_particles() {
    for (int i = 0; i < MAX_PARTICLES; i++) {
        particles[i].x = randf(BOUNDS_LEFT + 10, BOUNDS_RIGHT - 10);
        particles[i].y = randf(BOUNDS_TOP + 10, BOUNDS_BOTTOM - 10);
        particles[i].vx = randf(-2.0f, 2.0f);
        particles[i].vy = randf(-2.0f, 2.0f);
        particles[i].color = particle_colors[rand() % (sizeof(particle_colors) / sizeof(particle_colors[0]))];
        particles[i].core_id = 0;
    }
}

// Update physics for a range of particles
void update_particles_range(int start, int end, uint8_t core_id) {
    for (int i = start; i < end; i++) {
        Particle *p = &particles[i];
        
        // Apply gravity and wind
        p->vy += GRAVITY;
        p->vx += wind_x * 0.1f;
        p->vy += wind_y * 0.1f;
        
        // Update position
        p->x += p->vx;
        p->y += p->vy;
        
        // Boundary collision with bounce
        if (p->x <= BOUNDS_LEFT + PARTICLE_RADIUS) {
            p->x = BOUNDS_LEFT + PARTICLE_RADIUS;
            p->vx = -p->vx * BOUNCE_DAMPING;
        }
        if (p->x >= BOUNDS_RIGHT - PARTICLE_RADIUS) {
            p->x = BOUNDS_RIGHT - PARTICLE_RADIUS;
            p->vx = -p->vx * BOUNCE_DAMPING;
        }
        if (p->y <= BOUNDS_TOP + PARTICLE_RADIUS) {
            p->y = BOUNDS_TOP + PARTICLE_RADIUS;
            p->vy = -p->vy * BOUNCE_DAMPING;
        }
        if (p->y >= BOUNDS_BOTTOM - PARTICLE_RADIUS) {
            p->y = BOUNDS_BOTTOM - PARTICLE_RADIUS;
            p->vy = -p->vy * BOUNCE_DAMPING;
            // Add friction on ground
            p->vx *= 0.95f;
        }
        
        // Mark which core updated this particle
        p->core_id = core_id;
    }
}

// Render all particles to framebuffer
void render_particles() {
    // Clear game area in framebuffer
    fb_fill_rect(0, BOUNDS_TOP, DISPLAY_WIDTH, DISPLAY_HEIGHT - BOUNDS_TOP, COLOR_BLACK);
    
    // Draw all particles
    for (int i = 0; i < particle_count; i++) {
        Particle *p = &particles[i];
        int px = (int)p->x;
        int py = (int)p->y;
        
        // Draw particle as small filled rectangle for visibility
        if (px >= 0 && px < DISPLAY_WIDTH && py >= BOUNDS_TOP && py < DISPLAY_HEIGHT) {
            // Draw 3x3 particle
            fb_set_pixel(px, py, p->color);
            fb_set_pixel(px - 1, py, p->color);
            fb_set_pixel(px + 1, py, p->color);
            fb_set_pixel(px, py - 1, p->color);
            fb_set_pixel(px, py + 1, p->color);
            fb_set_pixel(px - 1, py - 1, p->color);
            fb_set_pixel(px + 1, py - 1, p->color);
            fb_set_pixel(px - 1, py + 1, p->color);
            fb_set_pixel(px + 1, py + 1, p->color);
        }
    }
}

// Draw status bar showing performance metrics to framebuffer
void draw_status_bar() {
    char buf[50];
    
    // Clear status bar area in framebuffer
    fb_fill_rect(0, 0, DISPLAY_WIDTH, 28, COLOR_BLACK);
    
    // Draw colored bars and simple graphics to framebuffer
    // Core 0 bar (red)
    int core0_bar = (core0_cycles * 80) / 1000000; // Scale to pixels
    if (core0_bar > 80) core0_bar = 80;
    fb_fill_rect(90, 4, core0_bar, 8, COLOR_RED);
    
    // Core 1 bar (blue)
    int core1_bar = (core1_cycles * 80) / 1000000;
    if (core1_bar > 80) core1_bar = 80;
    fb_fill_rect(180, 4, core1_bar, 8, COLOR_BLUE);
    
    // Draw simple FPS indicator (colored square that changes with FPS)
    uint16_t fps_color = current_fps > 50 ? COLOR_GREEN : (current_fps > 30 ? COLOR_YELLOW : COLOR_RED);
    fb_fill_rect(5, 4, 8, 8, fps_color);
    
    // Particle count indicator
    fb_fill_rect(5, 16, 8, 8, COLOR_CYAN);
}

// Update FPS counter
void update_fps() {
    frame_count++;
    uint32_t now = to_ms_since_boot(get_absolute_time());
    
    if (now - last_fps_time >= 1000) {
        current_fps = frame_count * 1000.0f / (now - last_fps_time);
        frame_count = 0;
        last_fps_time = now;
        
        // Print FPS to console
        printf("FPS: %.1f | Particles: %d | C0: %lu us | C1: %lu us\n", 
               current_fps, particle_count, core0_cycles, core1_cycles);
    }
}

// Handle user input
void handle_input() {
    static bool prev_btn_a = false;
    static bool prev_btn_b = false;
    
    // Button A: Reset particles
    bool btn_a = button_pressed(BUTTON_A);
    if (btn_a && !prev_btn_a) {
        init_particles();
        printf("Particles reset!\n");
    }
    prev_btn_a = btn_a;
    
    // Button B: Adjust particle count
    bool btn_b = button_pressed(BUTTON_B);
    if (btn_b && !prev_btn_b) {
        particle_count += 100;
        if (particle_count > MAX_PARTICLES) particle_count = 100;
        printf("Particle count: %d\n", particle_count);
    }
    prev_btn_b = btn_b;
    
    // X and Y buttons: Control wind
    if (button_pressed(BUTTON_X)) {
        wind_x = 0.5f;  // Wind right
    } else {
        wind_x *= 0.95f;  // Decay
    }
    
    if (button_pressed(BUTTON_Y)) {
        wind_y = -0.3f;  // Wind up
    } else {
        wind_y *= 0.95f;  // Decay
    }
}

// Core 1 entry point - handles physics for second half of particles
void core1_entry() {
    printf("Core 1 started\n");
    
    while (1) {
        // Wait for core 0 to signal start of frame
        while (!core1_ready) {
            tight_loop_contents();
        }
        
        uint32_t start = time_us_32();
        
        // Update second half of particles
        int mid = particle_count / 2;
        update_particles_range(mid, particle_count, 1);
        
        core1_cycles = time_us_32() - start;
        
        // Signal completion
        core1_ready = false;
        rendering_done = true;
    }
}

int main() {
    stdio_init_all();
    
    printf("\n=== Dual-Core Particle System ===\n");
    printf("Initializing...\n");
    
    // Initialize display and buttons
    display_error_t result = display_pack_init();
    if (result != DISPLAY_OK) {
        printf("Display initialization failed: %s\n", display_error_string(result));
        return -1;
    }
    printf("Display initialized successfully\n");
    
    result = buttons_init();
    if (result != DISPLAY_OK) {
        printf("Button initialization failed: %s\n", display_error_string(result));
        return -1;
    }
    printf("Buttons initialized successfully\n");
    
    // Initialize mutex
    mutex_init(&particle_mutex);
    
    // Initialize particles
    srand(time_us_32());
    init_particles();
    
    // Clear framebuffer
    for (int i = 0; i < DISPLAY_WIDTH * DISPLAY_HEIGHT; i++) {
        framebuffer[i] = COLOR_BLACK;
    }
    
    // Clear screen
    display_clear(COLOR_BLACK);
    
    printf("\n=== System Ready ===\n");
    printf("Particles: %d\n", particle_count);
    printf("Display: 320x240 (full screen)\n");
    printf("Double buffering: ENABLED (flicker-free)\n");
    printf("\nControls:\n");
    printf("  X Button = Wind Right\n");
    printf("  Y Button = Wind Up\n");
    printf("  A Button = Reset Particles\n");
    printf("  B Button = Change Particle Count\n");
    printf("\nStarting simulation...\n\n");
    
    // Launch core 1
    multicore_launch_core1(core1_entry);
    sleep_ms(100); // Give core 1 time to start
    
    last_fps_time = to_ms_since_boot(get_absolute_time());
    
    // Core 0 main loop
    while (true) {
        buttons_update();
        handle_input();
        
        // Update first half of particles on core 0
        uint32_t start = time_us_32();
        
        int mid = particle_count / 2;
        update_particles_range(0, mid, 0);
        
        core0_cycles = time_us_32() - start;
        
        // Signal core 1 to start its work
        rendering_done = false;
        core1_ready = true;
        
        // Wait for core 1 to finish
        while (!rendering_done) {
            tight_loop_contents();
        }
        
        // Render everything to framebuffer (only core 0 does rendering)
        render_particles();
        draw_status_bar();
        
        // Blit the entire framebuffer to display in one operation - eliminates flicker!
        display_blit_full(framebuffer);
        
        update_fps();
        
        sleep_ms(16); // ~60 FPS target
    }
    
    return 0;
}