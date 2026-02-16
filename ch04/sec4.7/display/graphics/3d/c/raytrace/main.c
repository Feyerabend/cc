#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

#include "pico/stdlib.h"
#include "pico/time.h"
#include "pico/multicore.h"
#include "display.h"

// Scene configuration
#define MAX_DEPTH 2
#define EPSILON 0.01f

// Render at half resolution for speed
#define RENDER_WIDTH (DISPLAY_WIDTH / 2)
#define RENDER_HEIGHT (DISPLAY_HEIGHT / 2)

// Camera settings
#define CAMERA_FOV 90.0f
#define ASPECT_RATIO ((float)RENDER_WIDTH / (float)RENDER_HEIGHT)

// Animation settings
#define COLOR_CYCLE_TIME 10.0f  // 10 seconds for full color cycle
#define BOUNCE_CYCLE_TIME 2.0f  // 2 seconds for bounce cycle
#define BOUNCE_HEIGHT 1.0f
#define BASE_Y -0.5f
#define SPHERE_RADIUS 1.0f
#define PLANE_Y -1.5f

// Vector 3D
typedef struct {
    float x, y, z;
} vec3;

// Ray
typedef struct {
    vec3 origin;
    vec3 direction;
} ray;

// Framebuffer
static uint16_t framebuffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];

// Animation time
static float anim_time = 0.0f;

// Multicore synchronization
static volatile bool core1_ready = false;
static volatile bool core1_done = false;
static volatile bool render_frame = false;

// Current sphere position and color (shared between cores)
static volatile vec3 sphere_center;
static volatile vec3 sphere_color;

// Dirty rectangle tracking (only render where sphere can be)
static volatile int dirty_x_min, dirty_x_max;
static volatile int dirty_y_min, dirty_y_max;
static bool first_frame = true;

// Vector operations
static inline vec3 vec3_new(float x, float y, float z) {
    vec3 v = {x, y, z};
    return v;
}

static inline vec3 vec3_add(vec3 a, vec3 b) {
    return vec3_new(a.x + b.x, a.y + b.y, a.z + b.z);
}

static inline vec3 vec3_sub(vec3 a, vec3 b) {
    return vec3_new(a.x - b.x, a.y - b.y, a.z - b.z);
}

static inline vec3 vec3_mul(vec3 v, float s) {
    return vec3_new(v.x * s, v.y * s, v.z * s);
}

static inline float vec3_dot(vec3 a, vec3 b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

static inline float vec3_length(vec3 v) {
    return sqrtf(vec3_dot(v, v));
}

static inline vec3 vec3_normalize(vec3 v) {
    float len = vec3_length(v);
    if (len > EPSILON) {
        return vec3_mul(v, 1.0f / len);
    }
    return v;
}

// Clamp float to 0-1 range
static inline float clamp(float x, float min, float max) {
    if (x < min) return min;
    if (x > max) return max;
    return x;
}

// Procedural checkerboard texture
static vec3 checkerboard_texture(vec3 point, vec3 base_color1, vec3 base_color2, float scale) {
    // Use floor to create checker pattern
    int check_x = (int)floorf(point.x * scale);
    int check_y = (int)floorf(point.y * scale);
    int check_z = (int)floorf(point.z * scale);
    
    // XOR to create alternating pattern
    bool is_even = ((check_x + check_y + check_z) & 1) == 0;
    
    return is_even ? base_color1 : base_color2;
}

// Helper function for HSL to RGB conversion
static float hue2rgb(float p, float q, float t) {
    if (t < 0.0f) t += 1.0f;
    if (t > 1.0f) t -= 1.0f;
    if (t < 1.0f/6.0f) return p + (q - p) * 6.0f * t;
    if (t < 1.0f/2.0f) return q;
    if (t < 2.0f/3.0f) return p + (q - p) * (2.0f/3.0f - t) * 6.0f;
    return p;
}

// HSL to RGB conversion for color cycling
static vec3 hsl_to_rgb(float h, float s, float l) {
    float r, g, b;
    
    if (s == 0.0f) {
        r = g = b = l;
    } else {
        float q = l < 0.5f ? l * (1.0f + s) : l + s - l * s;
        float p = 2.0f * l - q;
        r = hue2rgb(p, q, h + 1.0f/3.0f);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1.0f/3.0f);
    }
    
    return vec3_new(r, g, b);
}

// Ray-sphere intersection
static bool intersect_sphere(ray r, vec3 center, float radius, float *t) {
    vec3 oc = vec3_sub(r.origin, center);
    float a = vec3_dot(r.direction, r.direction);
    float b = 2.0f * vec3_dot(oc, r.direction);
    float c = vec3_dot(oc, oc) - radius * radius;
    float discriminant = b * b - 4.0f * a * c;
    
    if (discriminant < 0) {
        return false;
    }
    
    float sqrt_disc = sqrtf(discriminant);
    float t0 = (-b - sqrt_disc) / (2.0f * a);
    float t1 = (-b + sqrt_disc) / (2.0f * a);
    
    if (t0 > EPSILON) {
        *t = t0;
        return true;
    }
    if (t1 > EPSILON) {
        *t = t1;
        return true;
    }
    
    return false;
}

// Ray-plane intersection
static bool intersect_plane(ray r, float plane_y, float *t) {
    // Plane with normal (0, 1, 0) at y = plane_y
    if (fabsf(r.direction.y) < EPSILON) {
        return false; // Ray parallel to plane
    }
    
    *t = (plane_y - r.origin.y) / r.direction.y;
    return *t > EPSILON;
}

// Trace a ray through the scene
static vec3 trace_ray(ray r) {
    vec3 camera_pos = vec3_new(0, 0, 0);  // Camera at origin like original!
    vec3 light_pos = vec3_new(2, 3, 4);
    float ambient_light = 0.2f;
    float specular_power = 20.0f;
    
    // Background color
    vec3 background = vec3_new(0.078f, 0.078f, 0.078f); // RGB(20, 20, 20)
    
    // Initialize t values
    float t_sphere = 1e10f;  // Large value instead of INFINITY
    float t_plane = 1e10f;
    
    // Get current sphere state with memory barrier
    __dmb();
    vec3 s_center = {sphere_center.x, sphere_center.y, sphere_center.z};
    vec3 s_color = {sphere_color.x, sphere_color.y, sphere_color.z};
    __dmb();
    
    // Check sphere intersection
    bool hit_sphere = intersect_sphere(r, s_center, SPHERE_RADIUS, &t_sphere);
    
    // Check plane intersection
    bool hit_plane = intersect_plane(r, PLANE_Y, &t_plane);
    
    // Determine what was hit first (need to check both hit AND t value)
    if (hit_sphere && (!hit_plane || t_sphere < t_plane)) {
        // Hit sphere first (or only sphere)
        vec3 hit_point = vec3_add(r.origin, vec3_mul(r.direction, t_sphere));
        vec3 normal = vec3_normalize(vec3_sub(hit_point, s_center));
        vec3 light_dir = vec3_normalize(vec3_sub(light_pos, hit_point));
        vec3 view_dir = vec3_mul(r.direction, -1.0f);
        vec3 half_dir = vec3_normalize(vec3_add(light_dir, view_dir));
        
        // Apply black and white checkerboard texture to sphere
        // Use spherical coordinates for proper UV mapping
        float u = 0.5f + atan2f(normal.z, normal.x) / (2.0f * 3.14159f);
        float v = 0.5f - asinf(normal.y) / 3.14159f;
        
        // Create checker pattern in UV space
        int check_u = (int)floorf(u * 8.0f);  // 8 checks around
        int check_v = (int)floorf(v * 8.0f);  // 8 checks vertically
        bool is_white = ((check_u + check_v) & 1) == 0;
        
        // Simple black and white texture
        vec3 texture_color = is_white ? vec3_new(1.0f, 1.0f, 1.0f) : vec3_new(0.0f, 0.0f, 0.0f);
        
        // Diffuse lighting
        float diffuse = fmaxf(0.0f, vec3_dot(normal, light_dir));
        
        // Specular lighting (stronger on white squares)
        float specular = is_white ? powf(fmaxf(0.0f, vec3_dot(normal, half_dir)), specular_power) : 0.0f;
        
        // Combine lighting with texture
        float intensity = diffuse + ambient_light;
        vec3 color = vec3_new(
            clamp(texture_color.x * intensity + specular, 0.0f, 1.0f),
            clamp(texture_color.y * intensity + specular, 0.0f, 1.0f),
            clamp(texture_color.z * intensity + specular, 0.0f, 1.0f)
        );
        
        return color;
        
    } else if (hit_plane) {
        // Hit plane
        vec3 plane_hit = vec3_add(r.origin, vec3_mul(r.direction, t_plane));
        vec3 plane_normal = vec3_new(0, 1, 0);
        
        // Apply black and white checkerboard texture to plane
        vec3 white = vec3_new(0.8f, 0.8f, 0.8f);  // Light gray for white squares
        vec3 black = vec3_new(0.2f, 0.2f, 0.2f);  // Dark gray for black squares
        vec3 textured_plane_color = checkerboard_texture(plane_hit, white, black, 2.0f);
        
        // Vector to light
        vec3 to_light = vec3_sub(light_pos, plane_hit);
        float light_dist = vec3_length(to_light);
        vec3 light_dir = vec3_normalize(to_light);
        
        // Check if in shadow (cast shadow ray to sphere)
        ray shadow_ray;
        shadow_ray.origin = vec3_add(plane_hit, vec3_mul(light_dir, EPSILON));
        shadow_ray.direction = light_dir;
        
        float t_shadow;
        bool in_shadow = intersect_sphere(shadow_ray, s_center, SPHERE_RADIUS, &t_shadow) && 
                         t_shadow < light_dist;
        
        if (in_shadow) {
            // In shadow - darker
            float intensity = ambient_light * 0.3f;
            return vec3_mul(textured_plane_color, intensity);
        } else {
            // Lit plane
            float diffuse = fmaxf(0.0f, vec3_dot(plane_normal, light_dir));
            float intensity = diffuse + ambient_light;
            return vec3_mul(textured_plane_color, intensity);
        }
    }
    
    // Hit nothing - return background
    return background;
}

// Convert float color (0-1) to RGB565
static uint16_t vec3_to_rgb565(vec3 color) {
    // Clamp to valid range
    float r = clamp(color.x, 0.0f, 1.0f);
    float g = clamp(color.y, 0.0f, 1.0f);
    float b = clamp(color.z, 0.0f, 1.0f);
    
    // Convert to RGB565 with proper rounding
    uint8_t r5 = (uint8_t)(r * 31.0f + 0.5f);
    uint8_t g6 = (uint8_t)(g * 63.0f + 0.5f);
    uint8_t b5 = (uint8_t)(b * 31.0f + 0.5f);
    
    // Ensure within range
    if (r5 > 31) r5 = 31;
    if (g6 > 63) g6 = 63;
    if (b5 > 31) b5 = 31;
    
    return (r5 << 11) | (g6 << 5) | b5;
}

// Update animation state
static void update_animation(void) {
    // Bounce animation
    float bounce_phase = fmodf(anim_time, BOUNCE_CYCLE_TIME) / BOUNCE_CYCLE_TIME;
    float bounce_y = BASE_Y + fabsf(sinf(bounce_phase * 2.0f * 3.14159f)) * BOUNCE_HEIGHT;
    
    // Color cycling
    float hue = fmodf(anim_time, COLOR_CYCLE_TIME) / COLOR_CYCLE_TIME;
    vec3 color = hsl_to_rgb(hue, 0.8f, 0.5f);
    
    // Update sphere position and color atomically
    // Sphere should be IN FRONT of camera (negative Z since camera is at origin)
    __dmb(); // Data memory barrier before write
    sphere_center.x = 0;
    sphere_center.y = bounce_y;
    sphere_center.z = -4.0f;  // IN FRONT of camera (negative Z)
    sphere_color.x = color.x;
    sphere_color.y = color.y;
    sphere_color.z = color.z;
    __dmb(); // Data memory barrier after write
    
    // Calculate dirty region (bounding box of sphere + shadow area)
    // Project sphere to screen space
    float fov_rad = CAMERA_FOV * 3.14159f / 180.0f;
    float viewport_height = 2.0f * tanf(fov_rad / 2.0f);
    float viewport_width = viewport_height * ASPECT_RATIO;
    
    // Sphere bounds in world space (with some margin for shadow)
    float world_x_min = sphere_center.x - SPHERE_RADIUS - 0.5f;
    float world_x_max = sphere_center.x + SPHERE_RADIUS + 0.5f;
    float world_y_min = sphere_center.y - SPHERE_RADIUS - 0.5f;
    float world_y_max = sphere_center.y + SPHERE_RADIUS + 2.0f;  // Extra for shadow
    
    // Project to normalized device coordinates (-1 to 1)
    float z_dist = fabsf(sphere_center.z);
    float ndc_x_min = world_x_min / (z_dist * viewport_width / 2.0f);
    float ndc_x_max = world_x_max / (z_dist * viewport_width / 2.0f);
    float ndc_y_min = world_y_min / (z_dist * viewport_height / 2.0f);
    float ndc_y_max = world_y_max / (z_dist * viewport_height / 2.0f);
    
    // Convert to screen space
    int screen_x_min = (int)((ndc_x_min + 1.0f) * 0.5f * RENDER_WIDTH) - 2;
    int screen_x_max = (int)((ndc_x_max + 1.0f) * 0.5f * RENDER_WIDTH) + 2;
    int screen_y_min = (int)((1.0f - ndc_y_max) * 0.5f * RENDER_HEIGHT) - 2;
    int screen_y_max = (int)((1.0f - ndc_y_min) * 0.5f * RENDER_HEIGHT) + 2;
    
    // Clamp to screen bounds
    dirty_x_min = screen_x_min < 0 ? 0 : screen_x_min;
    dirty_x_max = screen_x_max >= RENDER_WIDTH ? RENDER_WIDTH - 1 : screen_x_max;
    dirty_y_min = screen_y_min < 0 ? 0 : screen_y_min;
    dirty_y_max = screen_y_max >= RENDER_HEIGHT ? RENDER_HEIGHT - 1 : screen_y_max;
}

// Render a range of scanlines (for multicore)
static void render_scanlines(int start_y, int end_y) {
    vec3 camera_pos = vec3_new(0, 0, 0);  // Camera at origin!
    float viewport_height = 2.0f * tanf((CAMERA_FOV * 3.14159f / 180.0f) / 2.0f);
    float viewport_width = viewport_height * ASPECT_RATIO;
    
    // Get dirty region bounds
    int dx_min = dirty_x_min;
    int dx_max = dirty_x_max;
    int dy_min = dirty_y_min;
    int dy_max = dirty_y_max;
    
    for (int y = start_y; y < end_y; y++) {
        // Skip rows outside dirty region (unless first frame)
        if (!first_frame && (y < dy_min || y > dy_max)) {
            continue;
        }
        
        for (int x = 0; x < RENDER_WIDTH; x++) {
            // Skip pixels outside dirty region (unless first frame)
            if (!first_frame && (x < dx_min || x > dx_max)) {
                continue;
            }
            
            // Single sample - fast!
            float u = (2.0f * (x + 0.5f) / RENDER_WIDTH - 1.0f) * viewport_width / 2.0f;
            float v = (1.0f - 2.0f * (y + 0.5f) / RENDER_HEIGHT) * viewport_height / 2.0f;
            
            ray r;
            r.origin = camera_pos;
            r.direction = vec3_normalize(vec3_new(u, v, -1.0f));
            
            vec3 color = trace_ray(r);
            
            // Convert to RGB565
            uint16_t pixel = vec3_to_rgb565(color);
            
            // Write 2x2 block to framebuffer (simple upscaling)
            int fx = x * 2;
            int fy = y * 2;
            
            // Bounds check
            if (fx + 1 < DISPLAY_WIDTH && fy + 1 < DISPLAY_HEIGHT) {
                framebuffer[fy * DISPLAY_WIDTH + fx] = pixel;
                framebuffer[fy * DISPLAY_WIDTH + fx + 1] = pixel;
                framebuffer[(fy + 1) * DISPLAY_WIDTH + fx] = pixel;
                framebuffer[(fy + 1) * DISPLAY_WIDTH + fx + 1] = pixel;
            }
        }
    }
}

// Core 1 entry point - renders bottom half of screen
static void core1_entry(void) {
    core1_ready = true;
    
    while (1) {
        // Wait for signal to render
        while (!render_frame) {
            tight_loop_contents();
        }
        
        // Render bottom half
        render_scanlines(RENDER_HEIGHT / 2, RENDER_HEIGHT);
        
        // Signal completion
        core1_done = true;
        render_frame = false;
    }
}

// Render the scene using both cores
static void render_scene(void) {
    // Signal core 1 to start rendering bottom half
    core1_done = false;
    render_frame = true;
    
    // Core 0 renders top half
    render_scanlines(0, RENDER_HEIGHT / 2);
    
    // Wait for core 1 to finish bottom half
    while (!core1_done) {
        tight_loop_contents();
    }
    
    // Display the complete frame
    display_blit_full(framebuffer);
}

// Button callbacks
static bool paused = false;

static void btn_a_callback(button_t btn) {
    (void)btn;
    paused = !paused;
}

static void btn_b_callback(button_t btn) {
    (void)btn;
    anim_time = 0.0f; // Reset animation
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
    
    display_clear(COLOR_BLACK);
    display_set_backlight(true);
    
    printf("Bouncing Sphere Raytracer Started (Dual-Core)\n");
    printf("Rendering: Dirty region optimization (fast!)\n");
    printf("Controls:\n");
    printf("  A - Pause/Play animation\n");
    printf("  B - Reset animation\n");
    
    // Initialize sphere position and color BEFORE launching core 1
    sphere_center.x = 0;
    sphere_center.y = BASE_Y;
    sphere_center.z = -4.0f;  // IN FRONT of camera (negative Z)
    sphere_color.x = 1.0f;
    sphere_color.y = 0.0f;
    sphere_color.z = 0.0f;
    
    // Initialize framebuffer to black
    for (int i = 0; i < DISPLAY_WIDTH * DISPLAY_HEIGHT; i++) {
        framebuffer[i] = COLOR_BLACK;
    }
    
    // Launch core 1
    multicore_launch_core1(core1_entry);
    
    // Wait for core 1 to be ready
    while (!core1_ready) {
        tight_loop_contents();
    }
    
    printf("Core 1 ready!\n");
    
    // Do initial animation update before first frame
    update_animation();
    
    printf("Initial sphere state:\n");
    printf("  Position: (%f, %f, %f)\n", sphere_center.x, sphere_center.y, sphere_center.z);
    printf("  Color: (%f, %f, %f)\n", sphere_color.x, sphere_color.y, sphere_color.z);
    printf("  Radius: %f\n", SPHERE_RADIUS);
    printf("  Camera at: (0, 0, 3)\n");
    printf("  Plane Y: %f\n", PLANE_Y);
    
    while (1) {
        buttons_update();
        
        // Update animation with smoother timestep
        if (!paused) {
            update_animation();
            anim_time += 0.05f;  // Back to original speed since we removed AA
        }
        
        // Render scene with both cores (now with dirty region optimization!)
        uint32_t start_time = to_ms_since_boot(get_absolute_time());
        render_scene();
        uint32_t render_time = to_ms_since_boot(get_absolute_time()) - start_time;
        
        // After first frame, enable dirty region optimization
        if (first_frame) {
            first_frame = false;
            printf("First frame complete, dirty region optimization enabled\n");
            printf("Dirty region: x[%d,%d] y[%d,%d]\n", 
                   dirty_x_min, dirty_x_max, dirty_y_min, dirty_y_max);
        }
        
        printf("Frame rendered in %ld ms (%.1f fps)\n", 
               render_time, 1000.0f / render_time);
        
        // Target 15 FPS for smooth animation
        if (render_time < 67) {
            sleep_ms(67 - render_time);
        }
    }
    
    return 0;
}

