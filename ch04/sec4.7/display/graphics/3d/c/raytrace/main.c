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
#define MAX_SPHERES 3  // Ground + 2 spheres
#define MAX_DEPTH 2
#define EPSILON 0.001f

// Render at half resolution for speed
#define RENDER_WIDTH (DISPLAY_WIDTH / 2)
#define RENDER_HEIGHT (DISPLAY_HEIGHT / 2)

// Camera settings
#define CAMERA_FOV 60.0f
#define ASPECT_RATIO ((float)RENDER_WIDTH / (float)RENDER_HEIGHT)

// Vector 3D
typedef struct {
    float x, y, z;
} vec3;

// Ray
typedef struct {
    vec3 origin;
    vec3 direction;
} ray;

// Material
typedef struct {
    vec3 color;
    float specular;     // 0-1, shininess
    float reflective;   // 0-1, reflection amount
    float diffuse;      // 0-1, diffuse lighting
} material;

// Sphere
typedef struct {
    vec3 center;
    float radius;
    material mat;
} sphere;

// Light
typedef struct {
    vec3 position;
    float intensity;
} light;

// Scene
static sphere spheres[MAX_SPHERES];
static int num_spheres = 0;
static light lights[3];
static int num_lights = 0;

// Framebuffer
static uint16_t framebuffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];

// Animation time
static float anim_time = 0.0f;

// Multicore synchronization
static volatile bool core1_ready = false;
static volatile bool core1_done = false;
static volatile bool render_frame = false;

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

static inline vec3 vec3_mul_v(vec3 a, vec3 b) {
    return vec3_new(a.x * b.x, a.y * b.y, a.z * b.z);
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

static inline vec3 vec3_reflect(vec3 v, vec3 n) {
    return vec3_sub(v, vec3_mul(n, 2.0f * vec3_dot(v, n)));
}

// Ray-sphere intersection
static bool intersect_sphere(ray r, sphere s, float *t) {
    vec3 oc = vec3_sub(r.origin, s.center);
    float a = vec3_dot(r.direction, r.direction);
    float b = 2.0f * vec3_dot(oc, r.direction);
    float c = vec3_dot(oc, oc) - s.radius * s.radius;
    float discriminant = b * b - 4 * a * c;
    
    if (discriminant < 0) {
        return false;
    }
    
    float t1 = (-b - sqrtf(discriminant)) / (2.0f * a);
    float t2 = (-b + sqrtf(discriminant)) / (2.0f * a);
    
    if (t1 > EPSILON) {
        *t = t1;
        return true;
    }
    if (t2 > EPSILON) {
        *t = t2;
        return true;
    }
    
    return false;
}

// Find closest intersection
static bool find_closest_intersection(ray r, float t_min, float t_max, 
                                       int *hit_sphere, float *t_hit) {
    *t_hit = t_max;
    *hit_sphere = -1;
    
    for (int i = 0; i < num_spheres; i++) {
        float t;
        if (intersect_sphere(r, spheres[i], &t)) {
            if (t >= t_min && t < *t_hit) {
                *t_hit = t;
                *hit_sphere = i;
            }
        }
    }
    
    return *hit_sphere != -1;
}

// Calculate lighting at a point (simplified for speed)
static float compute_lighting(vec3 point, vec3 normal, vec3 view, float specular) {
    float intensity = 0.1f; // Lower ambient for darker scene
    
    for (int i = 0; i < num_lights; i++) {
        vec3 light_dir = vec3_sub(lights[i].position, point);
        
        // Check if point is in shadow
        ray shadow_ray;
        shadow_ray.origin = point;
        shadow_ray.direction = vec3_normalize(light_dir);
        
        int hit_sphere;
        float t_hit;
        float max_t = vec3_length(light_dir);
        
        if (find_closest_intersection(shadow_ray, EPSILON, max_t, &hit_sphere, &t_hit)) {
            continue; // In shadow
        }
        
        // Diffuse lighting only (no specular for speed)
        light_dir = vec3_normalize(light_dir);
        float n_dot_l = vec3_dot(normal, light_dir);
        if (n_dot_l > 0) {
            intensity += lights[i].intensity * n_dot_l;
        }
    }
    
    return intensity;
}

// Trace a ray through the scene
static vec3 trace_ray(ray r, float t_min, float t_max, int depth) {
    if (depth <= 0) {
        return vec3_new(0, 0, 0); // Black background
    }
    
    int hit_sphere;
    float t_hit;
    
    if (!find_closest_intersection(r, t_min, t_max, &hit_sphere, &t_hit)) {
        // Dark sky - simple gradient
        float t = 0.5f * (r.direction.y + 1.0f);
        vec3 sky_top = vec3_new(0.05f, 0.05f, 0.1f);     // Very dark blue
        vec3 sky_bottom = vec3_new(0.02f, 0.02f, 0.02f); // Almost black
        return vec3_add(vec3_mul(sky_bottom, 1.0f - t), vec3_mul(sky_top, t));
    }
    
    // Hit point and normal
    vec3 hit_point = vec3_add(r.origin, vec3_mul(r.direction, t_hit));
    vec3 normal = vec3_normalize(vec3_sub(hit_point, spheres[hit_sphere].center));
    vec3 view = vec3_mul(r.direction, -1.0f);
    
    // Calculate local color with lighting
    material mat = spheres[hit_sphere].mat;
    float light_intensity = compute_lighting(hit_point, normal, view, mat.specular);
    vec3 local_color = vec3_mul(mat.color, light_intensity * mat.diffuse);
    
    // Reflection
    if (mat.reflective > EPSILON && depth > 1) {
        vec3 reflect_dir = vec3_reflect(vec3_mul(r.direction, -1.0f), normal);
        ray reflect_ray;
        reflect_ray.origin = hit_point;
        reflect_ray.direction = reflect_dir;
        
        vec3 reflected_color = trace_ray(reflect_ray, EPSILON, INFINITY, depth - 1);
        
        // Mix local color with reflection
        local_color = vec3_add(
            vec3_mul(local_color, 1.0f - mat.reflective),
            vec3_mul(reflected_color, mat.reflective)
        );
    }
    
    return local_color;
}

// Convert float color (0-1) to RGB565 with dithering
static uint16_t vec3_to_rgb565(vec3 color) {
    // Clamp
    if (color.x < 0) color.x = 0;
    if (color.x > 1) color.x = 1;
    if (color.y < 0) color.y = 0;
    if (color.y > 1) color.y = 1;
    if (color.z < 0) color.z = 0;
    if (color.z > 1) color.z = 1;
    
    // Convert to RGB565 range
    float r_float = color.x * 31.0f;
    float g_float = color.y * 63.0f;
    float b_float = color.z * 31.0f;
    
    // Simple dithering - add small random noise to reduce banding
    // Use fractional part as dither threshold
    float r_frac = r_float - (int)r_float;
    float g_frac = g_float - (int)g_float;
    float b_frac = b_float - (int)b_float;
    
    uint8_t r = (uint8_t)r_float + (r_frac > 0.5f ? 1 : 0);
    uint8_t g = (uint8_t)g_float + (g_frac > 0.5f ? 1 : 0);
    uint8_t b = (uint8_t)b_float + (b_frac > 0.5f ? 1 : 0);
    
    // Clamp after rounding
    if (r > 31) r = 31;
    if (g > 63) g = 63;
    if (b > 31) b = 31;
    
    return (r << 11) | (g << 5) | b;
}

// Setup the scene (minimal - 2 spheres with distinct colors)
static void setup_scene(void) {
    num_spheres = 0;
    num_lights = 0;
    
    // Ground sphere (darker for contrast)
    spheres[num_spheres++] = (sphere){
        .center = {0, -5001, 0},
        .radius = 5000,
        .mat = {
            .color = {0.2f, 0.2f, 0.2f},  // Very dark gray
            .specular = 0.0f,
            .reflective = 0.15f,  // Less reflective ground
            .diffuse = 1.0f
        }
    };
    
    // Left sphere - PURE RED (mostly matte)
    spheres[num_spheres++] = (sphere){
        .center = {-1.8f, 0.3f, -4.0f},  // Start position
        .radius = 1.0f,
        .mat = {
            .color = {1.0f, 0.0f, 0.0f},  // Pure red
            .specular = 0.0f,
            .reflective = 0.2f,  // Only 20% reflective - mostly opaque
            .diffuse = 1.0f
        }
    };
    
    // Right sphere - PURE YELLOW (mostly matte)
    spheres[num_spheres++] = (sphere){
        .center = {1.8f, 0.3f, -4.0f},  // Start position
        .radius = 1.0f,
        .mat = {
            .color = {1.0f, 1.0f, 0.0f},  // Pure yellow
            .specular = 0.0f,
            .reflective = 0.2f,  // Only 20% reflective - mostly opaque
            .diffuse = 1.0f
        }
    };
    
    // Single main light
    lights[num_lights++] = (light){
        .position = {0, 8, -2},  // Higher and slightly forward
        .intensity = 1.0f
    };
}

// Animate the scene (simplified for 2 spheres)
static void animate_scene(void) {
    // Keep spheres above ground (Y should stay >= 0)
    // Move them up and down gently
    spheres[1].center.y = 0.3f + sinf(anim_time) * 0.2f;  // Red: 0.1 to 0.5
    spheres[2].center.y = 0.3f + sinf(anim_time + 3.14159f) * 0.2f;  // Yellow: 0.1 to 0.5
    
    // Rotate around center more slowly
    float angle = anim_time * 0.3f;  // Slower rotation
    float radius = 1.8f;  // Slightly more spread out
    
    spheres[1].center.x = cosf(angle) * radius;
    spheres[1].center.z = -4.0f + sinf(angle) * 0.3f;
    
    spheres[2].center.x = cosf(angle + 3.14159f) * radius;
    spheres[2].center.z = -4.0f + sinf(angle + 3.14159f) * 0.3f;
}

// Render a range of scanlines (for multicore)
static void render_scanlines(int start_y, int end_y) {
    vec3 camera_pos = vec3_new(0, 0, 0);
    float viewport_height = 2.0f * tanf((CAMERA_FOV * 3.14159f / 180.0f) / 2.0f);
    float viewport_width = viewport_height * ASPECT_RATIO;
    
    for (int y = start_y; y < end_y; y++) {
        for (int x = 0; x < RENDER_WIDTH; x++) {
            // Anti-aliasing: sample 4 sub-pixels and average
            vec3 color_sum = vec3_new(0, 0, 0);
            
            // 2x2 supersampling
            for (int sy = 0; sy < 2; sy++) {
                for (int sx = 0; sx < 2; sx++) {
                    // Offset within pixel
                    float offset_x = (sx + 0.5f) / 2.0f;
                    float offset_y = (sy + 0.5f) / 2.0f;
                    
                    // Convert to viewport coordinates
                    float u = (2.0f * (x + offset_x) / RENDER_WIDTH - 1.0f) * viewport_width / 2.0f;
                    float v = (1.0f - 2.0f * (y + offset_y) / RENDER_HEIGHT) * viewport_height / 2.0f;
                    
                    // Create ray
                    ray r;
                    r.origin = camera_pos;
                    r.direction = vec3_normalize(vec3_new(u, v, -1.0f));
                    
                    // Trace ray and accumulate color
                    vec3 sample_color = trace_ray(r, 1.0f, INFINITY, MAX_DEPTH);
                    color_sum = vec3_add(color_sum, sample_color);
                }
            }
            
            // Average the 4 samples
            vec3 color = vec3_mul(color_sum, 0.25f);
            
            // Convert to RGB565
            uint16_t pixel = vec3_to_rgb565(color);
            
            // Write 2x2 block to framebuffer (simple upscaling)
            int fx = x * 2;
            int fy = y * 2;
            framebuffer[fy * DISPLAY_WIDTH + fx] = pixel;
            framebuffer[fy * DISPLAY_WIDTH + fx + 1] = pixel;
            framebuffer[(fy + 1) * DISPLAY_WIDTH + fx] = pixel;
            framebuffer[(fy + 1) * DISPLAY_WIDTH + fx + 1] = pixel;
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
    
    printf("Raytracer Demo Started (Dual-Core)\n");
    printf("Controls:\n");
    printf("  A - Pause/Play animation\n");
    printf("  B - Reset animation\n");
    
    // Launch core 1
    multicore_launch_core1(core1_entry);
    
    // Wait for core 1 to be ready
    while (!core1_ready) {
        tight_loop_contents();
    }
    
    printf("Core 1 ready!\n");
    
    setup_scene();
    
    while (1) {
        buttons_update();
        
        // Update animation
        if (!paused) {
            animate_scene();
            anim_time += 0.05f;
        }
        
        // Render scene with both cores
        uint32_t start_time = to_ms_since_boot(get_absolute_time());
        render_scene();
        uint32_t render_time = to_ms_since_boot(get_absolute_time()) - start_time;
        
        printf("Frame rendered in %ld ms (%.1f fps)\n", 
               render_time, 1000.0f / render_time);
        
        // Limit frame rate
        if (render_time < 100) {
            sleep_ms(100 - render_time);
        }
    }
    
    return 0;
}