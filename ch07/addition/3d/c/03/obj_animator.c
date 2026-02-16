#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

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

// PAM framebuffer structure
typedef struct {
    unsigned char* pixels;
    int width;
    int height;
    int channels;  // 3 for RGB
} Framebuffer;


// FRAMEBUFFER OPERATIONS

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

void clear_framebuffer(Framebuffer* fb, unsigned char r, unsigned char g, unsigned char b) {
    for (int i = 0; i < fb->width * fb->height; i++) {
        fb->pixels[i * fb->channels + 0] = r;
        fb->pixels[i * fb->channels + 1] = g;
        fb->pixels[i * fb->channels + 2] = b;
    }
}

void set_pixel(Framebuffer* fb, int x, int y, unsigned char r, unsigned char g, unsigned char b) {
    if (x >= 0 && x < fb->width && y >= 0 && y < fb->height) {
        int index = (y * fb->width + x) * fb->channels;
        fb->pixels[index] = r;
        fb->pixels[index + 1] = g;
        fb->pixels[index + 2] = b;
    }
}

// Bresenham's line algorithm with anti-aliasing
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

// PAM FILE OUTPUT (ASCII FORMAT)

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
    fprintf(file, "TUPLTYPE RGB\n");
    fprintf(file, "ENDHDR\n");

    // Write pixel data in ASCII format
    for (int i = 0; i < fb->width * fb->height * fb->channels; i++) {
        fprintf(file, "%d", fb->pixels[i]);
        
        // Add space after each value, newline every 12 values for readability
        if ((i + 1) % 12 == 0) {
            fprintf(file, "\n");
        } else {
            fprintf(file, " ");
        }
    }
    
    // Ensure file ends with newline
    if ((fb->width * fb->height * fb->channels) % 12 != 0) {
        fprintf(file, "\n");
    }
    
    fclose(file);
}

// VECTOR OPERATIONS

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
    return v;
}

// MATRIX OPERATIONS

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
    if (fabs(w) < 0.0001f) w = 1.0f;  // Prevent division by zero
    return (Vec3){
        (m.m[0][0] * v.x + m.m[0][1] * v.y + m.m[0][2] * v.z + m.m[0][3]) / w,
        (m.m[1][0] * v.x + m.m[1][1] * v.y + m.m[1][2] * v.z + m.m[1][3]) / w,
        (m.m[2][0] * v.x + m.m[2][1] * v.y + m.m[2][2] * v.z + m.m[2][3]) / w
    };
}

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
    m.m[2][3] = (2.0f * far * near) / (near - far);
    m.m[3][2] = -1.0f;
    return m;
}


// OBJ FILE LOADER

Model* load_obj(const char* filename) {
    FILE* file = fopen(filename, "r");
    if (!file) {
        printf("Error: Cannot open file %s\n", filename);
        return NULL;
    }

    Model* model = malloc(sizeof(Model));
    model->vertices = NULL;
    model->faces = NULL;
    model->vertex_count = 0;
    model->face_count = 0;

    // First pass: count vertices and faces
    char line[256];
    while (fgets(line, sizeof(line), file)) {
        if (line[0] == 'v' && line[1] == ' ') {
            model->vertex_count++;
        } else if (line[0] == 'f' && line[1] == ' ') {
            model->face_count++;
        }
    }

    if (model->vertex_count == 0) {
        printf("Error: No vertices found in OBJ file\n");
        fclose(file);
        free(model);
        return NULL;
    }

    // Allocate memory
    model->vertices = malloc(model->vertex_count * sizeof(Vec3));
    model->faces = malloc(model->face_count * sizeof(Face));

    // Second pass: load data
    rewind(file);
    int v_idx = 0, f_idx = 0;
    
    while (fgets(line, sizeof(line), file)) {
        if (line[0] == 'v' && line[1] == ' ') {
            float x, y, z;
            sscanf(line, "v %f %f %f", &x, &y, &z);
            model->vertices[v_idx++] = (Vec3){x, y, z};
        } else if (line[0] == 'f' && line[1] == ' ') {
            int v1, v2, v3;
            // Handle various OBJ face formats
            if (sscanf(line, "f %d/%*d/%*d %d/%*d/%*d %d/%*d/%*d", &v1, &v2, &v3) == 3 ||
                sscanf(line, "f %d//%*d %d//%*d %d//%*d", &v1, &v2, &v3) == 3 ||
                sscanf(line, "f %d/%*d %d/%*d %d/%*d", &v1, &v2, &v3) == 3 ||
                sscanf(line, "f %d %d %d", &v1, &v2, &v3) == 3) {
                // OBJ indices are 1-based, convert to 0-based
                model->faces[f_idx++] = (Face){v1-1, v2-1, v3-1};
            }
        }
    }

    fclose(file);
    printf("Loaded model: %d vertices, %d faces\n", model->vertex_count, model->face_count);
    return model;
}

void free_model(Model* model) {
    if (model) {
        free(model->vertices);
        free(model->faces);
        free(model);
    }
}

// RENDERING

typedef struct {
    int x, y;
} Point2D;

Point2D world_to_screen(Vec3 world_pos, Camera* camera) {
    Point2D screen;
    screen.x = (int)((world_pos.x + 1.0f) * camera->screen_width * 0.5f);
    screen.y = (int)((1.0f - world_pos.y) * camera->screen_height * 0.5f);
    return screen;
}

void render_wireframe(Framebuffer* fb, Model* model, Camera* camera, 
                     Vec3 object_position, Vec3 object_rotation,
                     unsigned char r, unsigned char g, unsigned char b) {
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

    // Draw wireframe
    for (int i = 0; i < model->face_count; i++) {
        Face face = model->faces[i];
        
        // Check if indices are valid
        if (face.v1 >= 0 && face.v1 < model->vertex_count &&
            face.v2 >= 0 && face.v2 < model->vertex_count &&
            face.v3 >= 0 && face.v3 < model->vertex_count) {
            
            Point2D p1 = world_to_screen(projected_vertices[face.v1], camera);
            Point2D p2 = world_to_screen(projected_vertices[face.v2], camera);
            Point2D p3 = world_to_screen(projected_vertices[face.v3], camera);

            // Draw triangle edges
            draw_line_fb(fb, p1.x, p1.y, p2.x, p2.y, r, g, b);
            draw_line_fb(fb, p2.x, p2.y, p3.x, p3.y, r, g, b);
            draw_line_fb(fb, p3.x, p3.y, p1.x, p1.y, r, g, b);
        }
    }

    free(projected_vertices);
}

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

// ANIMATION GENERATION

void generate_animation(const char* obj_filename, const char* output_prefix, 
                       int num_frames, int width, int height) {
    // Load model
    Model* model = load_obj(obj_filename);
    if (!model) {
        printf("Failed to load model\n");
        return;
    }

    // Create framebuffer
    Framebuffer* fb = create_framebuffer(width, height, 3);
    
    // Initialize camera
    Camera camera = create_camera(width, height);
    camera.position = (Vec3){0, 0, 5};
    
    // Animation parameters
    Vec3 object_pos = {0, 0, 0};
    Vec3 object_rot = {0.2f, 0, 0};  // Initial rotation
    
    // Generate frames
    printf("\nGenerating %d frames..\n", num_frames);
    for (int frame = 0; frame < num_frames; frame++) {
        // Clear framebuffer (dark background)
        clear_framebuffer(fb, 20, 20, 30);
        
        // Update rotation (rotate around Y axis)
        object_rot.y = (2.0f * M_PI * frame) / num_frames;
        
        // Render
        render_wireframe(fb, model, &camera, object_pos, object_rot, 
                        100, 200, 255);  // Light blue wireframe
        
        // Save frame
        char filename[256];
        sprintf(filename, "%s_%03d.pam", output_prefix, frame);
        save_pam(fb, filename);
        
        printf("  Frame %d/%d: %s\n", frame + 1, num_frames, filename);
    }
    
    printf("\nAnimation frames generated successfully!\n");
    printf("Use the Python script to merge them into a GIF:\n");
    printf("  python3 pam_to_gif.py frame_*.pam\n");
    
    // Clean up
    free_framebuffer(fb);
    free_model(model);
}



int main(int argc, char* argv[]) {
    printf("-- OBJ to PAM Animation Generator --\n\n");
    
    // Default parameters
    const char* obj_file = "model.obj";
    const char* output_prefix = "frame";
    int num_frames = 36;  // Full rotation
    int width = 800;
    int height = 600;
    
    // Parse command line arguments
    if (argc > 1) obj_file = argv[1];
    if (argc > 2) output_prefix = argv[2];
    if (argc > 3) num_frames = atoi(argv[3]);
    if (argc > 4) width = atoi(argv[4]);
    if (argc > 5) height = atoi(argv[5]);
    
    printf("Configuration:\n");
    printf("  OBJ file: %s\n", obj_file);
    printf("  Output prefix: %s\n", output_prefix);
    printf("  Number of frames: %d\n", num_frames);
    printf("  Resolution: %dx%d\n\n", width, height);
    
    // Generate animation
    generate_animation(obj_file, output_prefix, num_frames, width, height);
    
    return 0;
}
