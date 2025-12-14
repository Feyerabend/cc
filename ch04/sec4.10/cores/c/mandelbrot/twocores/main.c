#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "pico/sync.h"
#include "display.h"

// Mandelbrot calculation parameters
#define MAX_ITERATIONS 64
#define ZOOM_FACTOR 1.5

typedef struct {
    double center_x;
    double center_y;
    double zoom;
} view_t;

typedef struct {
    uint16_t *framebuffer;
    view_t view;
    volatile bool render_requested;
    volatile bool core1_done;
    mutex_t render_mutex;
} render_state_t;

static render_state_t render_state = {
    .framebuffer = NULL,
    .view = {
        .center_x = -0.5,
        .center_y = 0.0,
        .zoom = 1.0
    },
    .render_requested = false,
    .core1_done = false
};

static volatile bool needs_redraw = false;

// Colour palette for Mandelbrot set
static uint16_t get_mandelbrot_color(int iterations) {
    if (iterations == MAX_ITERATIONS) {
        return COLOR_BLACK; // Inside set
    }
    
    // Create a smooth colour gradient
    float t = (float)iterations / MAX_ITERATIONS;
    
    // Generate RGB values with smooth transitions
    int r = (int)(9 * (1 - t) * t * t * t * 255);
    int g = (int)(15 * (1 - t) * (1 - t) * t * t * 255);
    int b = (int)(8.5 * (1 - t) * (1 - t) * (1 - t) * t * 255);
    
    // Clamp values
    r = r > 255 ? 255 : r;
    g = g > 255 ? 255 : g;
    b = b > 255 ? 255 : b;
    
    // Convert to RGB565
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3);
}

// Calculate Mandelbrot iterations for a given point
static int mandelbrot_iterations(double cx, double cy) {
    double x = 0.0, y = 0.0;
    int iteration = 0;
    
    while (x * x + y * y <= 4.0 && iteration < MAX_ITERATIONS) {
        double xtemp = x * x - y * y + cx;
        y = 2.0 * x * y + cy;
        x = xtemp;
        iteration++;
    }
    
    return iteration;
}

// Render a portion of the Mandelbrot set (for multi-core rendering)
static void render_mandelbrot_section(uint16_t *framebuffer, view_t *v, 
                                     int start_line, int end_line, int core_id) {
    // Calculate the complex plane bounds
    double aspect = (double)DISPLAY_WIDTH / (double)DISPLAY_HEIGHT;
    double range_y = 2.5 / v->zoom;
    double range_x = range_y * aspect;
    
    double min_x = v->center_x - range_x / 2.0;
    double max_x = v->center_x + range_x / 2.0;
    double min_y = v->center_y - range_y / 2.0;
    double max_y = v->center_y + range_y / 2.0;
    
    // Calculate step sizes
    double step_x = (max_x - min_x) / DISPLAY_WIDTH;
    double step_y = (max_y - min_y) / DISPLAY_HEIGHT;
    
    // Render assigned lines
    for (int py = start_line; py < end_line; py++) {
        double cy = min_y + py * step_y;
        
        for (int px = 0; px < DISPLAY_WIDTH; px++) {
            double cx = min_x + px * step_x;
            
            int iterations = mandelbrot_iterations(cx, cy);
            uint16_t color = get_mandelbrot_color(iterations);
            
            framebuffer[py * DISPLAY_WIDTH + px] = color;
        }
        
        // Progress indicator
        if (core_id == 0 && py % 20 == 0) {
            printf("Core %d: line %d/%d\n", core_id, py, end_line);
        }
    }
}

// Core 1 entry point - renders bottom half of screen
void core1_entry() {
    printf("Core 1 started!\n");
    
    while (true) {
        // Wait for render request
        while (!render_state.render_requested) {
            sleep_ms(1);
        }
        
        // Render bottom half (lines 120-239)
        render_mandelbrot_section(render_state.framebuffer, 
                                 &render_state.view,
                                 DISPLAY_HEIGHT / 2, 
                                 DISPLAY_HEIGHT,
                                 1);
        
        // Signal completion
        render_state.core1_done = true;
        
        // Wait for core 0 to clear the request
        while (render_state.render_requested) {
            sleep_ms(1);
        }
    }
}

// Render the full Mandelbrot set using both cores
static void render_mandelbrot_parallel(uint16_t *framebuffer, view_t *v) {
    printf("Rendering Mandelbrot (parallel): zoom=%.2f, center=(%.4f, %.4f)\n", 
           v->zoom, v->center_x, v->center_y);
    
    uint32_t start_time = to_ms_since_boot(get_absolute_time());
    
    // Update shared state
    render_state.framebuffer = framebuffer;
    render_state.view = *v;
    render_state.core1_done = false;
    
    // Signal core 1 to start
    render_state.render_requested = true;
    
    // Core 0 renders top half (lines 0-119)
    render_mandelbrot_section(framebuffer, v, 0, DISPLAY_HEIGHT / 2, 0);
    
    printf("Core 0 done, waiting for Core 1..\n");
    
    // Wait for core 1 to finish
    while (!render_state.core1_done) {
        tight_loop_contents();
    }
    
    // Clear the render request
    render_state.render_requested = false;
    
    uint32_t end_time = to_ms_since_boot(get_absolute_time());
    printf("Render complete. Time: %lu ms\n", end_time - start_time);
}

// Button callbacks
static void button_a_callback(button_t button) {
    // Zoom in
    render_state.view.zoom *= ZOOM_FACTOR;
    needs_redraw = true;
    printf("Zoom in: %.2f\n", render_state.view.zoom);
}

static void button_b_callback(button_t button) {
    // Zoom out
    render_state.view.zoom /= ZOOM_FACTOR;
    if (render_state.view.zoom < 0.1) render_state.view.zoom = 0.1;
    needs_redraw = true;
    printf("Zoom out: %.2f\n", render_state.view.zoom);
}

static void button_x_callback(button_t button) {
    // Pan up
    double range_y = 2.5 / render_state.view.zoom;
    render_state.view.center_y -= range_y * 0.2;
    needs_redraw = true;
    printf("Pan up\n");
}

static void button_y_callback(button_t button) {
    // Pan down
    double range_y = 2.5 / render_state.view.zoom;
    render_state.view.center_y += range_y * 0.2;
    needs_redraw = true;
    printf("Pan down\n");
}

int main() {
    // Init stdio for USB serial output
    stdio_init_all();
    sleep_ms(2000); // Wait for USB connection
    
    printf("\n-- Dual-Core Mandelbrot Set Renderer --\n");
    printf("Display: %dx%d pixels\n", DISPLAY_WIDTH, DISPLAY_HEIGHT);
    printf("Max iterations: %d\n", MAX_ITERATIONS);
    printf("Using both CPU cores for parallel rendering!\n\n");
    
    // Initialize mutex
    mutex_init(&render_state.render_mutex);
    
    // Initialize display
    printf("Init display..\n");
    display_error_t err = display_pack_init();
    if (err != DISPLAY_OK) {
        printf("Display init failed: %s\n", display_error_string(err));
        return 1;
    }
    printf("Display init successfully!\n");
    
    // Initialize buttons
    printf("Init buttons..\n");
    err = buttons_init();
    if (err != DISPLAY_OK) {
        printf("Button init failed: %s\n", display_error_string(err));
        return 1;
    }
    
    // Set up button callbacks
    button_set_callback(BUTTON_A, button_a_callback);
    button_set_callback(BUTTON_B, button_b_callback);
    button_set_callback(BUTTON_X, button_x_callback);
    button_set_callback(BUTTON_Y, button_y_callback);
    printf("Buttons initiated\n\n");
    
    // Allocate framebuffer
    printf("Allocating framebuffer (%d bytes)..\n", 
           DISPLAY_WIDTH * DISPLAY_HEIGHT * 2);
    render_state.framebuffer = (uint16_t *)malloc(DISPLAY_WIDTH * DISPLAY_HEIGHT * sizeof(uint16_t));
    if (!render_state.framebuffer) {
        printf("Failed to allocate framebuffer.\n");
        return 1;
    }
    printf("Framebuffer allocated.\n\n");
    
    // Launch core 1
    printf("Launching Core 1..\n");
    multicore_launch_core1(core1_entry);
    sleep_ms(100); // Give core 1 time to start
    
    // Show initial instructions
    display_clear(COLOR_BLACK);
    display_draw_string(10, 30, "DUAL-CORE MANDELBROT", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(10, 50, "RENDERING..", COLOR_CYAN, COLOR_BLACK);
    display_draw_string(10, 90, "CONTROLS:", COLOR_YELLOW, COLOR_BLACK);
    display_draw_string(10, 110, "A: ZOOM IN", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(10, 125, "B: ZOOM OUT", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(10, 140, "X: PAN UP", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(10, 155, "Y: PAN DOWN", COLOR_WHITE, COLOR_BLACK);
    sleep_ms(2000);
    
    // Initial render
    printf("\n-- Initial Render --\n");
    render_mandelbrot_parallel(render_state.framebuffer, &render_state.view);
    display_blit_full(render_state.framebuffer);
    
    printf("\n-- Ready! Use buttons to navigate --\n");
    printf("A=Zoom In, B=Zoom Out, X=Pan Up, Y=Pan Down\n\n");
    
    // Main loop
    uint32_t frame_count = 0;
    while (true) {
        // Update button states
        buttons_update();
        
        // Check if we need to redraw
        if (needs_redraw) {
            needs_redraw = false;
            
            printf("\n-- Redrawing Frame %lu --\n", frame_count++);
            render_mandelbrot_parallel(render_state.framebuffer, &render_state.view);
            display_blit_full(render_state.framebuffer);
        }
        
        sleep_ms(10);
    }
    
    // Cleanup (unreachable but good practice)
    free(render_state.framebuffer);
    display_cleanup();
    
    return 0;
}
