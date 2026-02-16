#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <float.h>

// Basic vector and matrix structures
typedef struct {
    float x, y, z;
} Vec3;

typedef struct {
    float m[4][4];
} Mat4;

typedef struct {
    int v1, v2, v3;  // Vertex indices for triangle face
} Face;

typedef struct {
    Vec3 *vertices;
    Face *faces;
    Vec3 *face_colors;  // Color for each face
    int vertex_count;
    int face_count;
} Model;

typedef struct {
    Vec3 position;
    Vec3 rotation;
    float fov;
    float near_plane;
    float far_plane;
    int screen_width;
    int screen_height;
} Camera;

// Framebuffer structure
typedef struct {
    unsigned char* pixels;
    int width;
    int height;
    int channels;  // 1 for grayscale, 3 for RGB
} Framebuffer;

// Triangle structure for sorting
typedef struct {
    Vec3 v1, v2, v3;  // Screen space vertices with z
    Vec3 color;       // RGB color
    float avg_z;      // Average z for sorting
} Triangle;

// Framebuffer operations
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
            // Grayscale: use luminance formula
            fb->pixels[pixel_index] = (unsigned char)(0.299f * r + 0.587f * g + 0.114f * b);
        } else if (fb->channels == 3) {
            fb->pixels[pixel_index] = r;
            fb->pixels[pixel_index + 1] = g;
            fb->pixels[pixel_index + 2] = b;
        }
    }
}

// Scanline triangle filling algorithm
void fill_triangle_scanline(Framebuffer* fb, Vec3 v1, Vec3 v2, Vec3 v3, 
                           unsigned char r, unsigned char g, unsigned char b) {
    // Sort vertices by y coordinate (v1.y <= v2.y <= v3.y)
    if (v1.y > v2.y) { Vec3 temp = v1; v1 = v2; v2 = temp; }
    if (v2.y > v3.y) { Vec3 temp = v2; v2 = v3; v3 = temp; }
    if (v1.y > v2.y) { Vec3 temp = v1; v1 = v2; v2 = temp; }

    int y1 = (int)v1.y;
    int y2 = (int)v2.y;
    int y3 = (int)v3.y;

    // Handle degenerate cases
    if (y3 == y1) return;

    // Fill the triangle using two parts: top and bottom
    for (int y = y1; y <= y3; y++) {
        if (y < 0 || y >= fb->height) continue;

        float x_left, x_right;
        
        if (y <= y2) {
            // Top part of triangle (v1 to v2)
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
            // Bottom part of triangle (v2 to v3)
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

        // Fill the scanline
        int start_x = (int)fmaxf(0, x_left);
        int end_x = (int)fminf(fb->width - 1, x_right);
        
        for (int x = start_x; x <= end_x; x++) {
            set_pixel(fb, x, y, r, g, b);
        }
    }
}

// Bresenham's line algorithm (for wireframe mode)
void draw_line_fb(Framebuffer* fb, int x0, int y0, int x1, int y1, unsigned char r, unsigned char g, unsigned char b) {
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

// PAM file output
void save_pam(Framebuffer* fb, const char* filename) {
    FILE* file = fopen(filename, "w");
    if (!file) {
        printf("Error: Cannot create file %s\n", filename);
        return;
    }

    // PAM header
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

    // Write pixel data in ASCII format
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

// Vector operations
Vec3 vec3_add(Vec3 a, Vec3 b) {
    return (Vec3){a.x + b.x, a.y + b.y, a.z + b.z};
}

Vec3 vec3_sub(Vec3 a, Vec3 b) {
    return (Vec3){a.x - b.x, a.y - b.y, a.z - b.z};
}

Vec3 vec3_scale(Vec3 v, float s) {
    return (Vec3){v.x * s, v.y * s, v.z * s};
}

float vec3_dot(Vec3 a, Vec3 b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

Vec3 vec3_cross(Vec3 a, Vec3 b) {
    return (Vec3){
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x
    };
}

float vec3_length(Vec3 v) {
    return sqrtf(v.x * v.x + v.y * v.y + v.z * v.z);
}

Vec3 vec3_normalize(Vec3 v) {
    float len = vec3_length(v);
    if (len > 0.0001f) {
        return vec3_scale(v, 1.0f / len);
    }
    return (Vec3){0, 0, 0};
}

// Matrix operations
Mat4 mat4_identity() {
    Mat4 m = {0};
    m.m[0][0] = m.m[1][1] = m.m[2][2] = m.m[3][3] = 1.0f;
    return m;
}

Mat4 mat4_multiply(Mat4 a, Mat4 b) {
    Mat4 result = {0};
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            for (int k = 0; k < 4; k++) {
                result.m[i][j] += a.m[i][k] * b.m[k][j];
            }
        }
    }
    return result;
}

Vec3 mat4_transform_vec3(Mat4 m, Vec3 v) {
    float w = m.m[3][0] * v.x + m.m[3][1] * v.y + m.m[3][2] * v.z + m.m[3][3];
    if (fabsf(w) < 0.0001f) w = 1.0f; // Avoid division by zero
    return (Vec3){
        (m.m[0][0] * v.x + m.m[0][1] * v.y + m.m[0][2] * v.z + m.m[0][3]) / w,
        (m.m[1][0] * v.x + m.m[1][1] * v.y + m.m[1][2] * v.z + m.m[1][3]) / w,
        (m.m[2][0] * v.x + m.m[2][1] * v.y + m.m[2][2] * v.z + m.m[2][3]) / w
    };
}

// Transformation matrices
Mat4 mat4_translation(float x, float y, float z) {
    Mat4 m = mat4_identity();
    m.m[0][3] = x;
    m.m[1][3] = y;
    m.m[2][3] = z;
    return m;
}

Mat4 mat4_rotation_x(float angle) {
    Mat4 m = mat4_identity();
    float c = cosf(angle);
    float s = sinf(angle);
    m.m[1][1] = c; m.m[1][2] = -s;
    m.m[2][1] = s; m.m[2][2] = c;
    return m;
}

Mat4 mat4_rotation_y(float angle) {
    Mat4 m = mat4_identity();
    float c = cosf(angle);
    float s = sinf(angle);
    m.m[0][0] = c; m.m[0][2] = s;
    m.m[2][0] = -s; m.m[2][2] = c;
    return m;
}

Mat4 mat4_rotation_z(float angle) {
    Mat4 m = mat4_identity();
    float c = cosf(angle);
    float s = sinf(angle);
    m.m[0][0] = c; m.m[0][1] = -s;
    m.m[1][0] = s; m.m[1][1] = c;
    return m;
}

Mat4 mat4_perspective(float fov, float aspect, float near, float far) {
    Mat4 m = {0};
    float f = 1.0f / tanf(fov * 0.5f);
    m.m[0][0] = f / aspect;
    m.m[1][1] = f;
    m.m[2][2] = (far + near) / (near - far);
    m.m[2][3] = (2 * far * near) / (near - far);
    m.m[3][2] = -1;
    return m;
}

// Screen space conversion
Vec3 world_to_screen(Vec3 world_pos, Camera* camera) {
    Vec3 screen;
    screen.x = (world_pos.x + 1.0f) * camera->screen_width * 0.5f;
    screen.y = (1.0f - world_pos.y) * camera->screen_height * 0.5f;
    screen.z = world_pos.z;
    return screen;
}

// Create a colored cube model
Model* create_colored_cube() {
    Model* model = malloc(sizeof(Model));
    model->vertex_count = 8;
    model->face_count = 12;
    
    // Allocate memory
    model->vertices = malloc(model->vertex_count * sizeof(Vec3));
    model->faces = malloc(model->face_count * sizeof(Face));
    model->face_colors = malloc(model->face_count * sizeof(Vec3));
    
    // Cube vertices
    model->vertices[0] = (Vec3){-1, -1, -1}; // back bottom left
    model->vertices[1] = (Vec3){ 1, -1, -1}; // back bottom right
    model->vertices[2] = (Vec3){ 1,  1, -1}; // back top right
    model->vertices[3] = (Vec3){-1,  1, -1}; // back top left
    model->vertices[4] = (Vec3){-1, -1,  1}; // front bottom left
    model->vertices[5] = (Vec3){ 1, -1,  1}; // front bottom right
    model->vertices[6] = (Vec3){ 1,  1,  1}; // front top right
    model->vertices[7] = (Vec3){-1,  1,  1}; // front top left
    
    // Cube faces (2 triangles per face) with colors
    // Back face - Red
    model->faces[0] = (Face){0, 1, 2};
    model->faces[1] = (Face){0, 2, 3};
    model->face_colors[0] = (Vec3){1.0f, 0.2f, 0.2f};
    model->face_colors[1] = (Vec3){1.0f, 0.2f, 0.2f};
    
    // Front face - Green
    model->faces[2] = (Face){4, 6, 5};
    model->faces[3] = (Face){4, 7, 6};
    model->face_colors[2] = (Vec3){0.2f, 1.0f, 0.2f};
    model->face_colors[3] = (Vec3){0.2f, 1.0f, 0.2f};
    
    // Left face - Blue
    model->faces[4] = (Face){0, 3, 7};
    model->faces[5] = (Face){0, 7, 4};
    model->face_colors[4] = (Vec3){0.2f, 0.2f, 1.0f};
    model->face_colors[5] = (Vec3){0.2f, 0.2f, 1.0f};
    
    // Right face - Yellow
    model->faces[6] = (Face){1, 5, 6};
    model->faces[7] = (Face){1, 6, 2};
    model->face_colors[6] = (Vec3){1.0f, 1.0f, 0.2f};
    model->face_colors[7] = (Vec3){1.0f, 1.0f, 0.2f};
    
    // Bottom face - Magenta
    model->faces[8] = (Face){0, 4, 5};
    model->faces[9] = (Face){0, 5, 1};
    model->face_colors[8] = (Vec3){1.0f, 0.2f, 1.0f};
    model->face_colors[9] = (Vec3){1.0f, 0.2f, 1.0f};
    
    // Top face - Cyan
    model->faces[10] = (Face){3, 2, 6};
    model->faces[11] = (Face){3, 6, 7};
    model->face_colors[10] = (Vec3){0.2f, 1.0f, 1.0f};
    model->face_colors[11] = (Vec3){0.2f, 1.0f, 1.0f};
    
    return model;
}

void free_model(Model* model) {
    if (model) {
        free(model->vertices);
        free(model->faces);
        free(model->face_colors);
        free(model);
    }
}

// Comparison function for sorting triangles by depth (painter's algorithm)
int compare_triangles(const void *a, const void *b) {
    Triangle *ta = (Triangle*)a;
    Triangle *tb = (Triangle*)b;
    
    // Sort by average z (furthest first for painter's algorithm)
    // Smaller z = closer to camera, so draw larger z first
    if (ta->avg_z < tb->avg_z) return -1;  // ta is further, draw first
    if (ta->avg_z > tb->avg_z) return 1;   // ta is closer, draw later
    return 0;
}

// Rendering functions
void render_solid(Model* model, Camera* camera, Vec3 object_position, Vec3 object_rotation, Framebuffer* fb) {
    // Create transformation matrix
    Mat4 translation = mat4_translation(object_position.x, object_position.y, object_position.z);
    Mat4 rot_x = mat4_rotation_x(object_rotation.x);
    Mat4 rot_y = mat4_rotation_y(object_rotation.y);
    Mat4 rot_z = mat4_rotation_z(object_rotation.z);
    Mat4 rotation = mat4_multiply(mat4_multiply(rot_z, rot_y), rot_x);
    Mat4 model_matrix = mat4_multiply(translation, rotation);

    // Create view matrix
    Mat4 view = mat4_translation(-camera->position.x, -camera->position.y, -camera->position.z);

    // Create projection matrix
    float aspect = (float)camera->screen_width / camera->screen_height;
    Mat4 projection = mat4_perspective(camera->fov, aspect, camera->near_plane, camera->far_plane);

    // Combined transformation matrix
    Mat4 mvp = mat4_multiply(mat4_multiply(projection, view), model_matrix);

    // Transform and project all vertices
    Vec3* projected_vertices = malloc(model->vertex_count * sizeof(Vec3));
    for (int i = 0; i < model->vertex_count; i++) {
        projected_vertices[i] = mat4_transform_vec3(mvp, model->vertices[i]);
    }

    // Create triangle array for sorting
    Triangle* triangles = malloc(model->face_count * sizeof(Triangle));
    int triangle_count = 0;

    for (int i = 0; i < model->face_count; i++) {
        Face face = model->faces[i];
        
        // Check if indices are valid
        if (face.v1 >= 0 && face.v1 < model->vertex_count &&
            face.v2 >= 0 && face.v2 < model->vertex_count &&
            face.v3 >= 0 && face.v3 < model->vertex_count) {
            
            Vec3 p1 = world_to_screen(projected_vertices[face.v1], camera);
            Vec3 p2 = world_to_screen(projected_vertices[face.v2], camera);
            Vec3 p3 = world_to_screen(projected_vertices[face.v3], camera);

            // Simple backface culling - check if triangle is facing away
            Vec3 edge1 = vec3_sub(p2, p1);
            Vec3 edge2 = vec3_sub(p3, p1);
            Vec3 normal = vec3_cross(edge1, edge2);
            
            // If z component of normal is negative, triangle is facing towards viewer
            if (normal.z > 0) {
                triangles[triangle_count].v1 = p1;
                triangles[triangle_count].v2 = p2;
                triangles[triangle_count].v3 = p3;
                triangles[triangle_count].color = model->face_colors[i];
                triangles[triangle_count].avg_z = (p1.z + p2.z + p3.z) / 3.0f;
                triangle_count++;
            }
        }
    }

    // Sort triangles by depth (painter's algorithm)
    qsort(triangles, triangle_count, sizeof(Triangle), compare_triangles);

    // Draw sorted triangles
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

void render_wireframe(Model* model, Camera* camera, Vec3 object_position, Vec3 object_rotation, Framebuffer* fb) {
    // Create transformation matrix (same as solid rendering)
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

    // Transform and project all vertices
    Vec3* projected_vertices = malloc(model->vertex_count * sizeof(Vec3));
    for (int i = 0; i < model->vertex_count; i++) {
        projected_vertices[i] = mat4_transform_vec3(mvp, model->vertices[i]);
    }

    // Draw wireframe
    for (int i = 0; i < model->face_count; i++) {
        Face face = model->faces[i];
        
        if (face.v1 >= 0 && face.v1 < model->vertex_count &&
            face.v2 >= 0 && face.v2 < model->vertex_count &&
            face.v3 >= 0 && face.v3 < model->vertex_count) {
            
            Vec3 p1 = world_to_screen(projected_vertices[face.v1], camera);
            Vec3 p2 = world_to_screen(projected_vertices[face.v2], camera);
            Vec3 p3 = world_to_screen(projected_vertices[face.v3], camera);

            // Draw triangle edges in white
            draw_line_fb(fb, (int)p1.x, (int)p1.y, (int)p2.x, (int)p2.y, 255, 255, 255);
            draw_line_fb(fb, (int)p2.x, (int)p2.y, (int)p3.x, (int)p3.y, 255, 255, 255);
            draw_line_fb(fb, (int)p3.x, (int)p3.y, (int)p1.x, (int)p1.y, 255, 255, 255);
        }
    }

    free(projected_vertices);
}

// Camera creation
Camera create_camera(int width, int height) {
    Camera camera;
    camera.position = (Vec3){0, 0, 5};
    camera.rotation = (Vec3){0, 0, 0};
    camera.fov = M_PI / 4.0f;  // 45 degrees
    camera.near_plane = 0.1f;
    camera.far_plane = 100.0f;
    camera.screen_width = width;
    camera.screen_height = height;
    return camera;
}

// Main function
int main() {
    // Create framebuffer
    int width = 800, height = 600;
    Framebuffer* framebuffer = create_framebuffer(width, height, 3);  // RGB
    
    // Initialize camera
    Camera camera = create_camera(width, height);
    camera.position = (Vec3){0, 0, 5};
    
    // Create colored cube model
    Model* cube = create_colored_cube();
    
    // Object transformation
    Vec3 object_pos = {0, 0, 0};
    Vec3 object_rot = {0.3f, 0.5f, 0.1f};  // Some rotation to see 3D effect
    
    // Render solid cube
    clear_framebuffer(framebuffer, 0);  // Black background
    render_solid(cube, &camera, object_pos, object_rot, framebuffer);
    save_pam(framebuffer, "solid_cube.pam");
    
    // Render with different rotation
    clear_framebuffer(framebuffer, 0);
    object_rot.y += 1.0f;
    render_solid(cube, &camera, object_pos, object_rot, framebuffer);
    save_pam(framebuffer, "solid_cube2.pam");
    
    // Render wireframe for comparison
    clear_framebuffer(framebuffer, 0);
    render_wireframe(cube, &camera, object_pos, object_rot, framebuffer);
    save_pam(framebuffer, "wireframe_cube.pam");
    
    // Animation sequence - rotating cube
    for (int frame = 0; frame < 16; frame++) {
        clear_framebuffer(framebuffer, 0);
        object_rot.y = frame * M_PI / 8.0f;  // Rotate 22.5 degrees per frame
        object_rot.x = 0.3f;
        render_solid(cube, &camera, object_pos, object_rot, framebuffer);
        
        char filename[64];
        sprintf(filename, "cube_frame_%02d.pam", frame);
        save_pam(framebuffer, filename);
    }
    
    // Clean up
    free_model(cube);
    free_framebuffer(framebuffer);
    
    printf("Rendering complete!\n");
    printf("Generated files: solid_cube.pam, solid_cube2.pam, wireframe_cube.pam, cube_frame_XX.pam (16 animation frames)\n");
    printf("View with pam7viewer.html\n");
    
    return 0;
}