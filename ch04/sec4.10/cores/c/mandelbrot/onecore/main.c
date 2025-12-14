#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include "pico/stdlib.h"
#include "display.h"

// Mandelbrot calculation parameters
#define MAX_ITERATIONS 64
#define ZOOM_FACTOR 1.5

typedef struct {
    double center_x;
    double center_y;
    double zoom;
} view_t;

static view_t view = {
    .center_x = -0.5,
    .center_y = 0.0,
    .zoom = 1.0
};

// colour palette for Mandelbrot set
static uint16_t get_mandelbrot_color(int iterations) {
    if (iterations == MAX_ITERATIONS) {
        return COLOR_BLACK; // Inside set
    }
    
    // Create smooth colour gradient
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

// Render the Mandelbrot set to a buffer
static void render_mandelbrot(uint16_t *framebuffer, view_t *v) {
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
    
    printf("Rendering Mandelbrot: zoom=%.2f, center=(%.4f, %.4f)\n", 
           v->zoom, v->center_x, v->center_y);
    
    // Render each pixel
    for (int py = 0; py < DISPLAY_HEIGHT; py++) {
        double cy = min_y + py * step_y;
        
        for (int px = 0; px < DISPLAY_WIDTH; px++) {
            double cx = min_x + px * step_x;
            
            int iterations = mandelbrot_iterations(cx, cy);
            uint16_t color = get_mandelbrot_color(iterations);
            
            framebuffer[py * DISPLAY_WIDTH + px] = color;
        }
        
        // Progress indicator every 10 lines
        if (py % 10 == 0) {
            printf(".");
            fflush(stdout);
        }
    }
    printf("\nRender complete!\n");
}

// Button callbacks
static uint16_t *framebuffer = NULL;
static bool needs_redraw = false;

static void button_a_callback(button_t button) {
    // Zoom in
    view.zoom *= ZOOM_FACTOR;
    needs_redraw = true;
    printf("Zoom in: %.2f\n", view.zoom);
}

static void button_b_callback(button_t button) {
    // Zoom out
    view.zoom /= ZOOM_FACTOR;
    if (view.zoom < 0.1) view.zoom = 0.1; // Minimum zoom
    needs_redraw = true;
    printf("Zoom out: %.2f\n", view.zoom);
}

static void button_x_callback(button_t button) {
    // Pan up
    double range_y = 2.5 / view.zoom;
    view.center_y -= range_y * 0.2;
    needs_redraw = true;
    printf("Pan up\n");
}

static void button_y_callback(button_t button) {
    // Pan down
    double range_y = 2.5 / view.zoom;
    view.center_y += range_y * 0.2;
    needs_redraw = true;
    printf("Pan down\n");
}

int main() {
    // Init stdio for USB serial output
    stdio_init_all();
    sleep_ms(2000); // Wait for USB connection
    
    printf("\n-- Mandelbrot Set Renderer --\n");
    printf("Display: %dx%d pixels\n", DISPLAY_WIDTH, DISPLAY_HEIGHT);
    printf("Max iterations: %d\n\n", MAX_ITERATIONS);
    
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
    printf("Buttons inited!\n\n");
    
    // Allocate framebuffer
    printf("Allocating framebuffer (%d bytes)..\n", 
           DISPLAY_WIDTH * DISPLAY_HEIGHT * 2);
    framebuffer = (uint16_t *)malloc(DISPLAY_WIDTH * DISPLAY_HEIGHT * sizeof(uint16_t));
    if (!framebuffer) {
        printf("Failed to allocate framebuffer!\n");
        return 1;
    }
    printf("Framebuffer allocated!\n\n");
    
    // Show initial instructions
    display_clear(COLOR_BLACK);
    display_draw_string(10, 40, "MANDELBROT SET", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(10, 60, "RENDERING..", COLOR_CYAN, COLOR_BLACK);
    display_draw_string(10, 100, "CONTROLS:", COLOR_YELLOW, COLOR_BLACK);
    display_draw_string(10, 120, "A: ZOOM IN", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(10, 135, "B: ZOOM OUT", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(10, 150, "X: PAN UP", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(10, 165, "Y: PAN DOWN", COLOR_WHITE, COLOR_BLACK);
    sleep_ms(2000);
    
    // Initial render
    printf("-- Initial Render --\n");
    render_mandelbrot(framebuffer, &view);
    display_blit_full(framebuffer);
    
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
            render_mandelbrot(framebuffer, &view);
            display_blit_full(framebuffer);
        }
        
        sleep_ms(10); // Small delay to reduce CPU usage
    }
    
    // Cleanup (unreachable but good practice)
    free(framebuffer);
    display_cleanup();
    
    return 0;
}
