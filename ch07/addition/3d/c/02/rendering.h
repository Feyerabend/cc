#ifndef RENDERING_H
#define RENDERING_H

#include "rmath.h"
#include "model.h"

typedef struct {
    unsigned char* pixels;
    int width;
    int height;
    int channels;  // 1 for grayscale, 3 for RGB
} Framebuffer;

typedef struct {
    Vec3 v1, v2, v3;  // Screen space vertices with z
    Vec3 color;       // RGB color (after lighting)
    float avg_z;      // Average z for sorting
} Triangle;

Framebuffer* create_framebuffer(int width, int height, int channels);
void free_framebuffer(Framebuffer* fb);
void clear_framebuffer(Framebuffer* fb, unsigned char value);
void set_pixel(Framebuffer* fb, int x, int y, unsigned char r, unsigned char g, unsigned char b);
void fill_triangle_scanline(Framebuffer* fb, Vec3 v1, Vec3 v2, Vec3 v3, 
                           unsigned char r, unsigned char g, unsigned char b);
void draw_line_fb(Framebuffer* fb, int x0, int y0, int x1, int y1, 
                  unsigned char r, unsigned char g, unsigned char b);
void save_pam(Framebuffer* fb, const char* filename);
Vec3 world_to_screen(Vec3 world_pos, Camera* camera);
Vec3 calculate_lighting(Vec3 surface_normal, Vec3 base_color, Light* light);
int compare_triangles(const void *a, const void *b);
void render_solid_with_lighting(Model* model, Camera* camera, Vec3 object_position, 
                               Vec3 object_rotation, Framebuffer* fb, Light* light);

#endif