#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include "rendering.h"
#include "math.h"
#include "model.h"

Framebuffer* create_framebuffer(int width, int height, int channels) {
    Framebuffer* fb = malloc(sizeof(Framebuffer));
    fb->width = width;
    fb->height = height;
    fb->channels = channels;
    fb->pixels = calloc(width * height * channels, sizeof(unsigned char));
    return fb;
}

void free_framebuffer(Framebuffer* fb) {
    if (fb) {
        free(fb->pixels);
        free(fb);
    }
}

void clear_framebuffer(Framebuffer* fb, unsigned char value) {
    memset(fb->pixels, value, fb->width * fb->height * fb->channels);
}

void set_pixel(Framebuffer* fb, int x, int y, unsigned char r, unsigned char g, unsigned char b) {
    if (x >= 0 && x < fb->width && y >= 0 && y < fb->height) {
        int pixel_index = (y * fb->width + x) * fb->channels;
        if (fb->channels == 1) {
            fb->pixels[pixel_index] = (unsigned char)(0.299f * r + 0.587f * g + 0.114f * b);
        } else if (fb->channels == 3) {
            fb->pixels[pixel_index] = r;
            fb->pixels[pixel_index + 1] = g;
            fb->pixels[pixel_index + 2] = b;
        }
    }
}

void fill_triangle_scanline(Framebuffer* fb, Vec3 v1, Vec3 v2, Vec3 v3, 
                           unsigned char r, unsigned char g, unsigned char b) {
    if (v1.y > v2.y) { Vec3 temp = v1; v1 = v2; v2 = temp; }
    if (v2.y > v3.y) { Vec3 temp = v2; v2 = v3; v3 = temp; }
    if (v1.y > v2.y) { Vec3 temp = v1; v1 = v2; v2 = temp; }

    int y1 = (int)v1.y;
    int y2 = (int)v2.y;
    int y3 = (int)v3.y;

    if (y3 == y1) return;

    for (int y = y1; y <= y3; y++) {
        if (y < 0 || y >= fb->height) continue;

        float x_left, x_right;
        
        if (y <= y2) {
            if (y2 == y1) {
                x_left = fminf(v1.x, v2.x);
                x_right = fmaxf(v1.x, v2.x);
            } else {
                float t1 = (float)(y - y1) / (y2 - y1);
                float t2 = (float)(y - y1) / (y3 - y1);
                
                float x1 = v1.x + t1 * (v2.x - v1.x);
                float x2 = v1.x + t2 * (v3.x - v1.x);
                
                x_left = fminf(x1, x2);
                x_right = fmaxf(x1, x2);
            }
        } else {
            if (y3 == y2) {
                x_left = fminf(v2.x, v3.x);
                x_right = fmaxf(v2.x, v3.x);
            } else {
                float t1 = (float)(y - y2) / (y3 - y2);
                float t2 = (float)(y - y1) / (y3 - y1);
                
                float x1 = v2.x + t1 * (v3.x - v2.x);
                float x2 = v1.x + t2 * (v3.x - v1.x);
                
                x_left = fminf(x1, x2);
                x_right = fmaxf(x1, x2);
            }
        }

        int start_x = (int)fmaxf(0, x_left);
        int end_x = (int)fminf(fb->width - 1, x_right);
        
        for (int x = start_x; x <= end_x; x++) {
            set_pixel(fb, x, y, r, g, b);
        }
    }
}

void draw_line_fb(Framebuffer* fb, int x0, int y0, int x1, int y1, 
                  unsigned char r, unsigned char g, unsigned char b) {
    int dx = abs(x1 - x0);
    int dy = abs(y1 - y0);
    int sx = x0 < x1 ? 1 : -1;
    int sy = y0 < y1 ? 1 : -1;
    int err = dx - dy;

    while (1) {
        set_pixel(fb, x0, y0, r, g, b);
        
        if (x0 == x1 && y0 == y1) break;
        
        int e2 = 2 * err;
        if (e2 > -dy) {
            err -= dy;
            x0 += sx;
        }
        if (e2 < dx) {
            err += dx;
            y0 += sy;
        }
    }
}

void save_pam(Framebuffer* fb, const char* filename) {
    FILE* file = fopen(filename, "w");
    if (!file) {
        printf("Error: Cannot create file %s\n", filename);
        return;
    }

    fprintf(file, "P7\n");
    fprintf(file, "WIDTH %d\n", fb->width);
    fprintf(file, "HEIGHT %d\n", fb->height);
    fprintf(file, "DEPTH %d\n", fb->channels);
    fprintf(file, "MAXVAL 255\n");
    
    if (fb->channels == 1) {
        fprintf(file, "TUPLTYPE GRAYSCALE\n");
    } else if (fb->channels == 3) {
        fprintf(file, "TUPLTYPE RGB\n");
    }
    
    fprintf(file, "ENDHDR\n");

    for (int i = 0; i < fb->width * fb->height * fb->channels; i++) {
        fprintf(file, "%d", fb->pixels[i]);
        
        if ((i + 1) % 12 == 0) {
            fprintf(file, "\n");
        } else {
            fprintf(file, " ");
        }
    }
    
    if ((fb->width * fb->height * fb->channels) % 12 != 0) {
        fprintf(file, "\n");
    }
    
    fclose(file);
    printf("Saved %s (%dx%d, %d channels)\n", filename, fb->width, fb->height, fb->channels);
}

Vec3 world_to_screen(Vec3 world_pos, Camera* camera) {
    Vec3 screen;
    screen.x = (world_pos.x + 1.0f) * camera->screen_width * 0.5f;
    screen.y = (1.0f - world_pos.y) * camera->screen_height * 0.5f;
    screen.z = world_pos.z;
    return screen;
}

Vec3 calculate_lighting(Vec3 surface_normal, Vec3 base_color, Light* light) {
    Vec3 normal = vec3_normalize(surface_normal);
    Vec3 ambient = vec3_multiply(base_color, vec3_scale(light->ambient_color, light->ambient_intensity));
    float diffuse_factor = fmaxf(0.0f, vec3_dot(normal, light->direction));
    Vec3 diffuse = vec3_multiply(base_color, vec3_scale(vec3_scale(light->color, light->intensity), diffuse_factor));
    Vec3 final_color = vec3_add(ambient, diffuse);
    return vec3_clamp(final_color, 0.0f, 1.0f);
}

int compare_triangles(const void *a, const void *b) {
    Triangle *ta = (Triangle*)a;
    Triangle *tb = (Triangle*)b;
    if (ta->avg_z < tb->avg_z) return -1;
    if (ta->avg_z > tb->avg_z) return 1;
    return 0;
}

void render_solid_with_lighting(Model* model, Camera* camera, Vec3 object_position, 
                               Vec3 object_rotation, Framebuffer* fb, Light* light) {
    Mat4 translation = mat4_translation(object_position.x, object_position.y, object_position.z);
    Mat4 rot_x = mat4_rotation_x(object_rotation.x);
    Mat4 rot_y = mat4_rotation_y(object_rotation.y);
    Mat4 rot_z = mat4_rotation_z(object_rotation.z);
    Mat4 rotation = mat4_multiply(mat4_multiply(rot_z, rot_y), rot_x);
    Mat4 model_matrix = mat4_multiply(translation, rotation);
    Mat4 view = mat4_translation(-camera->position.x, -camera->position.y, -camera->position.z);
    float aspect = (float)camera->screen_width / camera->screen_height;
    Mat4 projection = mat4_perspective(camera->fov, aspect, camera->near_plane, camera->far_plane);
    Mat4 mvp = mat4_multiply(mat4_multiply(projection, view), model_matrix);

    Vec3* projected_vertices = malloc(model->vertex_count * sizeof(Vec3));
    for (int i = 0; i < model->vertex_count; i++) {
        projected_vertices[i] = mat4_transform_vec3(mvp, model->vertices[i]);
    }

    Triangle* triangles = malloc(model->face_count * sizeof(Triangle));
    int triangle_count = 0;

    for (int i = 0; i < model->face_count; i++) {
        Face face = model->faces[i];
        
        if (face.v1 >= 0 && face.v1 < model->vertex_count &&
            face.v2 >= 0 && face.v2 < model->vertex_count &&
            face.v3 >= 0 && face.v3 < model->vertex_count) {
            
            Vec3 p1 = world_to_screen(projected_vertices[face.v1], camera);
            Vec3 p2 = world_to_screen(projected_vertices[face.v2], camera);
            Vec3 p3 = world_to_screen(projected_vertices[face.v3], camera);

            Vec3 edge1 = vec3_sub(p2, p1);
            Vec3 edge2 = vec3_sub(p3, p1);
            Vec3 normal = vec3_cross(edge1, edge2);
            
            if (normal.z > 0) {
                Vec3 world_normal = mat4_transform_normal(model_matrix, model->face_normals[i]);
                world_normal = vec3_normalize(world_normal);
                Vec3 lit_color = calculate_lighting(world_normal, model->face_colors[i], light);
                
                triangles[triangle_count].v1 = p1;
                triangles[triangle_count].v2 = p2;
                triangles[triangle_count].v3 = p3;
                triangles[triangle_count].color = lit_color;
                triangles[triangle_count].avg_z = (p1.z + p2.z + p3.z) / 3.0f;
                triangle_count++;
            }
        }
    }

    qsort(triangles, triangle_count, sizeof(Triangle), compare_triangles);

    for (int i = 0; i < triangle_count; i++) {
        Triangle t = triangles[i];
        unsigned char r = (unsigned char)(t.color.x * 255);
        unsigned char g = (unsigned char)(t.color.y * 255);
        unsigned char b = (unsigned char)(t.color.z * 255);
        fill_triangle_scanline(fb, t.v1, t.v2, t.v3, r, g, b);
    }

    free(projected_vertices);
    free(triangles);
}