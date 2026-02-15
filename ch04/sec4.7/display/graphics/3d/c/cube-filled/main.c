#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "pico/stdlib.h"
#include "pico/time.h"
#include "display.h"

#define CENTER_X 160.0f
#define CENTER_Y 120.0f
#define CUBE_SIZE 60.0f

// Double buffer for flicker-free rendering
static uint16_t framebuffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];

// Cube vertices in 3D space (local coordinates)
static float vertices[8][3] = {
    {-1, -1, -1}, {1, -1, -1}, {1, 1, -1}, {-1, 1, -1},  // Back face
    {-1, -1,  1}, {1, -1,  1}, {1, 1,  1}, {-1, 1,  1}   // Front face
};

// Cube edges (pairs of vertex indices)
static const int edges[12][2] = {
    {0, 1}, {1, 2}, {2, 3}, {3, 0},  // Back face
    {4, 5}, {5, 6}, {6, 7}, {7, 4},  // Front face
    {0, 4}, {1, 5}, {2, 6}, {3, 7}   // Connecting edges
};

// Cube faces as triangles (two triangles per face, counter-clockwise winding when viewed from outside)
static const int faces[12][3] = {
    // Front face (+Z) - vertices 4,5,6,7
    {4, 5, 7}, {5, 6, 7},
    // Back face (-Z) - vertices 0,1,2,3 (viewed from outside/front)
    {1, 0, 2}, {0, 3, 2},
    // Right face (+X) - vertices 1,2,5,6
    {1, 5, 2}, {5, 6, 2},
    // Left face (-X) - vertices 0,3,4,7
    {4, 0, 7}, {0, 3, 7},
    // Top face (+Y) - vertices 3,2,7,6
    {3, 7, 2}, {7, 6, 2},
    // Bottom face (-Y) - vertices 0,1,4,5
    {0, 1, 4}, {1, 5, 4}
};

// Face colors
static const uint16_t face_colors[6] = {
    COLOR_RED,     // Front
    COLOR_GREEN,   // Back
    COLOR_BLUE,    // Right
    COLOR_YELLOW,  // Left
    COLOR_CYAN,    // Top
    COLOR_MAGENTA  // Bottom
};

// Rotation angles
static float angle_x = 0.3f;
static float angle_y = 0.5f;
static float angle_z = 0.0f;

// Rotation speeds
static float speed_x = 0.01f;
static float speed_y = 0.015f;
static float speed_z = 0.008f;

// Control state
static bool auto_rotate = true;
static bool solid_mode = true;  // Start in solid mode
static float zoom = 1.5f;

// Projected 2D vertices
static float projected[8][2];

// Forward declarations for framebuffer functions
static void fb_draw_string(uint16_t x, uint16_t y, const char* str, uint16_t color, uint16_t bg_color);
static void fb_draw_char(uint16_t x, uint16_t y, char c, uint16_t color, uint16_t bg_color);

/* Xiaolin Wu anti-aliased line (drawing to framebuffer) */
static void wu_plot(int x, int y, uint8_t brightness, uint16_t color) {
    if (x < 0 || x >= 320 || y < 0 || y >= 240) return;

    uint8_t r5 = (color >> 11) & 0x1F;
    uint8_t g6 = (color >>  5) & 0x3F;
    uint8_t b5 =  color        & 0x1F;

    uint8_t r = (r5 * brightness) >> 8;
    uint8_t g = (g6 * brightness) >> 8;
    uint8_t b = (b5 * brightness) >> 8;

    uint16_t blended = (r << 11) | (g << 5) | b;
    framebuffer[y * DISPLAY_WIDTH + x] = blended;
}

static void draw_line(float x0, float y0, float x1, float y1, uint16_t color) {
    bool steep = fabsf(y1 - y0) > fabsf(x1 - x0);

    if (steep) {
        float t; t = x0; x0 = y0; y0 = t; t = x1; x1 = y1; y1 = t;
    }
    if (x0 > x1) {
        float t; t = x0; x0 = x1; x1 = t; t = y0; y0 = y1; y1 = t;
    }

    float dx = x1 - x0;
    float dy = y1 - y0;
    float gradient = (dx == 0.0f) ? 1.0f : dy / dx;

    int   xend = (int)(x0 + 0.5f);
    float yend = y0 + gradient * (xend - x0);
    float xgap = 1.0f - (x0 + 0.5f - (int)(x0 + 0.5f));
    int   xpxl1 = xend;
    int   ypxl1 = (int)yend;

    if (steep) {
        wu_plot(ypxl1,     xpxl1,     (uint8_t)(255 * (1 - (yend - ypxl1)) * xgap), color);
        wu_plot(ypxl1 + 1, xpxl1,     (uint8_t)(255 * (yend - ypxl1) * xgap),       color);
    } else {
        wu_plot(xpxl1,     ypxl1,     (uint8_t)(255 * (1 - (yend - ypxl1)) * xgap), color);
        wu_plot(xpxl1,     ypxl1 + 1, (uint8_t)(255 * (yend - ypxl1) * xgap),       color);
    }
    float intery = yend + gradient;

    xend = (int)(x1 + 0.5f);
    yend = y1 + gradient * (xend - x1);
    xgap = x1 + 0.5f - (int)(x1 + 0.5f);
    int xpxl2 = xend;
    int ypxl2 = (int)yend;

    if (steep) {
        wu_plot(ypxl2,     xpxl2,     (uint8_t)(255 * (1 - (yend - ypxl2)) * xgap), color);
        wu_plot(ypxl2 + 1, xpxl2,     (uint8_t)(255 * (yend - ypxl2) * xgap),       color);
    } else {
        wu_plot(xpxl2,     ypxl2,     (uint8_t)(255 * (1 - (yend - ypxl2)) * xgap), color);
        wu_plot(xpxl2,     ypxl2 + 1, (uint8_t)(255 * (yend - ypxl2) * xgap),       color);
    }

    for (int x = xpxl1 + 1; x < xpxl2; ++x) {
        int y   = (int)intery;
        uint8_t frac = (uint8_t)(255 * (intery - y));

        if (steep) {
            wu_plot(y,     x, 255 - frac, color);
            wu_plot(y + 1, x, frac,       color);
        } else {
            wu_plot(x, y,     255 - frac, color);
            wu_plot(x, y + 1, frac,       color);
        }
        intery += gradient;
    }
}

// 3D rotation matrices
static void rotate_x(float v[3], float angle) {
    float y = v[1];
    float z = v[2];
    v[1] = y * cosf(angle) - z * sinf(angle);
    v[2] = y * sinf(angle) + z * cosf(angle);
}

static void rotate_y(float v[3], float angle) {
    float x = v[0];
    float z = v[2];
    v[0] = x * cosf(angle) + z * sinf(angle);
    v[2] = -x * sinf(angle) + z * cosf(angle);
}

static void rotate_z(float v[3], float angle) {
    float x = v[0];
    float y = v[1];
    v[0] = x * cosf(angle) - y * sinf(angle);
    v[1] = x * sinf(angle) + y * cosf(angle);
}

// Project 3D point to 2D screen
static void project(float v[3], float *x, float *y) {
    float perspective = 4.0f / (4.0f + v[2]);  // Simple perspective
    *x = CENTER_X + v[0] * CUBE_SIZE * zoom * perspective;
    *y = CENTER_Y + v[1] * CUBE_SIZE * zoom * perspective;
}

// Cross product for normal calculation
static void cross_product(float ax, float ay, float az,
                          float bx, float by, float bz,
                          float *nx, float *ny, float *nz) {
    *nx = ay * bz - az * by;
    *ny = az * bx - ax * bz;
    *nz = ax * by - ay * bx;
}

// Calculate if face is visible (backface culling using screen-space method)
static bool is_face_visible(int face_idx) {
    // Get three vertices of the triangle
    int v0 = faces[face_idx][0];
    int v1 = faces[face_idx][1];
    int v2 = faces[face_idx][2];
    
    // Use 2D projected coordinates to determine winding order
    float x0 = projected[v0][0];
    float y0 = projected[v0][1];
    float x1 = projected[v1][0];
    float y1 = projected[v1][1];
    float x2 = projected[v2][0];
    float y2 = projected[v2][1];
    
    // Calculate signed area (cross product in 2D)
    float area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0);
    
    // If area is positive, triangle is counter-clockwise (visible)
    return area > 0;
}

// Calculate face depth (average Z of vertices)
static float face_depth(int face_idx, float rotated_vertices[8][3]) {
    int v0 = faces[face_idx][0];
    int v1 = faces[face_idx][1];
    int v2 = faces[face_idx][2];
    
    return (rotated_vertices[v0][2] + rotated_vertices[v1][2] + rotated_vertices[v2][2]) / 3.0f;
}

// Calculate face lighting intensity (0-255)
static uint8_t calculate_lighting(int face_idx, float rotated_vertices[8][3]) {
    int v0 = faces[face_idx][0];
    int v1 = faces[face_idx][1];
    int v2 = faces[face_idx][2];
    
    // Calculate two edges
    float e1x = rotated_vertices[v1][0] - rotated_vertices[v0][0];
    float e1y = rotated_vertices[v1][1] - rotated_vertices[v0][1];
    float e1z = rotated_vertices[v1][2] - rotated_vertices[v0][2];
    
    float e2x = rotated_vertices[v2][0] - rotated_vertices[v0][0];
    float e2y = rotated_vertices[v2][1] - rotated_vertices[v0][1];
    float e2z = rotated_vertices[v2][2] - rotated_vertices[v0][2];
    
    // Calculate normal
    float nx, ny, nz;
    cross_product(e1x, e1y, e1z, e2x, e2y, e2z, &nx, &ny, &nz);
    
    // Normalize
    float len = sqrtf(nx * nx + ny * ny + nz * nz);
    if (len > 0.001f) {
        nx /= len;
        ny /= len;
        nz /= len;
    }
    
    // Light direction (from top-front-right)
    float lx = 0.5f, ly = -0.5f, lz = -0.7f;
    float llen = sqrtf(lx * lx + ly * ly + lz * lz);
    lx /= llen;
    ly /= llen;
    lz /= llen;
    
    // Calculate lighting intensity (Lambert diffuse)
    float dot = nx * lx + ny * ly + nz * lz;
    if (dot < 0) dot = 0;
    
    // Ambient + diffuse
    float ambient = 0.3f;
    float intensity = ambient + (1.0f - ambient) * dot;
    
    return (uint8_t)(intensity * 255.0f);
}

// Calculate depth for edge sorting
static float edge_depth(int edge_idx) {
    int v1 = edges[edge_idx][0];
    int v2 = edges[edge_idx][1];
    
    // Use average Z of both vertices
    float rotated1[3] = {vertices[v1][0], vertices[v1][1], vertices[v1][2]};
    float rotated2[3] = {vertices[v2][0], vertices[v2][1], vertices[v2][2]};
    
    rotate_x(rotated1, angle_x);
    rotate_y(rotated1, angle_y);
    rotate_z(rotated1, angle_z);
    
    rotate_x(rotated2, angle_x);
    rotate_y(rotated2, angle_y);
    rotate_z(rotated2, angle_z);
    
    return (rotated1[2] + rotated2[2]) / 2.0f;
}

// Render with simple painter's algorithm - NO backface culling
static void render_cube_painter(void) {
    // Store rotated vertices
    float rotated_vertices[8][3];
    
    // Transform all vertices
    for (int i = 0; i < 8; i++) {
        rotated_vertices[i][0] = vertices[i][0];
        rotated_vertices[i][1] = vertices[i][1];
        rotated_vertices[i][2] = vertices[i][2];
        
        rotate_x(rotated_vertices[i], angle_x);
        rotate_y(rotated_vertices[i], angle_y);
        rotate_z(rotated_vertices[i], angle_z);
        
        project(rotated_vertices[i], &projected[i][0], &projected[i][1]);
    }
    
    // Create depth-sorted list
    typedef struct {
        int index;
        float depth;
    } face_data_t;
    
    face_data_t face_list[12];
    
    // Calculate depth for each face (average Z of its vertices)
    for (int i = 0; i < 12; i++) {
        face_list[i].index = i;
        face_list[i].depth = face_depth(i, rotated_vertices);
    }
    
    // Sort by depth - furthest first (largest Z)
    for (int i = 0; i < 11; i++) {
        for (int j = 0; j < 11 - i; j++) {
            if (face_list[j].depth < face_list[j + 1].depth) {  // Changed: draw furthest first
                face_data_t temp = face_list[j];
                face_list[j] = face_list[j + 1];
                face_list[j + 1] = temp;
            }
        }
    }
    
    // Draw ALL faces in depth order (back to front)
    for (int i = 0; i < 12; i++) {
        int face_idx = face_list[i].index;
        int v0 = faces[face_idx][0];
        int v1 = faces[face_idx][1];
        int v2 = faces[face_idx][2];
        
        // Get 2D coordinates
        int x0 = (int)(projected[v0][0] + 0.5f);
        int y0 = (int)(projected[v0][1] + 0.5f);
        int x1 = (int)(projected[v1][0] + 0.5f);
        int y1 = (int)(projected[v1][1] + 0.5f);
        int x2 = (int)(projected[v2][0] + 0.5f);
        int y2 = (int)(projected[v2][1] + 0.5f);
        
        // Get face color
        uint16_t color = face_colors[face_idx / 2];
        
        // Draw filled triangle - front faces paint over back faces
        draw_filled_triangle(framebuffer, x0, y0, x1, y1, x2, y2, color);
    }
}

// Test each face individually with labels
static void render_face_debug(void) {
    // Store rotated vertices
    float rotated_vertices[8][3];
    
    // Transform all vertices
    for (int i = 0; i < 8; i++) {
        rotated_vertices[i][0] = vertices[i][0];
        rotated_vertices[i][1] = vertices[i][1];
        rotated_vertices[i][2] = vertices[i][2];
        
        rotate_x(rotated_vertices[i], angle_x);
        rotate_y(rotated_vertices[i], angle_y);
        rotate_z(rotated_vertices[i], angle_z);
        
        project(rotated_vertices[i], &projected[i][0], &projected[i][1]);
    }
    
    // Create depth-sorted list
    typedef struct {
        int index;
        float depth;
    } face_data_t;
    
    face_data_t face_list[12];
    
    for (int i = 0; i < 12; i++) {
        face_list[i].index = i;
        face_list[i].depth = face_depth(i, rotated_vertices);
    }
    
    // Sort back to front
    for (int i = 0; i < 11; i++) {
        for (int j = 0; j < 11 - i; j++) {
            if (face_list[j].depth > face_list[j + 1].depth) {
                face_data_t temp = face_list[j];
                face_list[j] = face_list[j + 1];
                face_list[j + 1] = temp;
            }
        }
    }
    
    // Draw faces WITH backface culling (FIXED)
    for (int i = 0; i < 12; i++) {
        int face_idx = face_list[i].index;
        int v0 = faces[face_idx][0];
        int v1 = faces[face_idx][1];
        int v2 = faces[face_idx][2];
        
        // Backface culling - check winding order in screen space
        float x0 = projected[v0][0];
        float y0 = projected[v0][1];
        float x1 = projected[v1][0];
        float y1 = projected[v1][1];
        float x2 = projected[v2][0];
        float y2 = projected[v2][1];
        
        float area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0);
        
        // FIXED: If area is NEGATIVE, triangle is counter-clockwise (visible)
        // This was backwards before!
        if (area >= 0) continue;  // Skip clockwise (back-facing) triangles
        
        // Get 2D coordinates
        int ix0 = (int)(x0 + 0.5f);
        int iy0 = (int)(y0 + 0.5f);
        int ix1 = (int)(x1 + 0.5f);
        int iy1 = (int)(y1 + 0.5f);
        int ix2 = (int)(x2 + 0.5f);
        int iy2 = (int)(y2 + 0.5f);
        
        // Get face color
        uint16_t color = face_colors[face_idx / 2];
        
        // Draw filled triangle
        draw_filled_triangle(framebuffer, ix0, iy0, ix1, iy1, ix2, iy2, color);
    }
    
    // Draw vertex indices for debugging
    for (int i = 0; i < 8; i++) {
        int x = (int)(projected[i][0] + 0.5f);
        int y = (int)(projected[i][1] + 0.5f);
        
        if (x >= 5 && x < 315 && y >= 5 && y < 235) {
            char buf[4];
            snprintf(buf, sizeof(buf), "%d", i);
            fb_draw_string(x + 2, y - 4, buf, COLOR_WHITE, COLOR_BLACK);
        }
    }
}

// Render just one face for debugging
static void render_one_face_test(void) {
    // Store rotated vertices
    float rotated_vertices[8][3];
    
    // Transform all vertices
    for (int i = 0; i < 8; i++) {
        rotated_vertices[i][0] = vertices[i][0];
        rotated_vertices[i][1] = vertices[i][1];
        rotated_vertices[i][2] = vertices[i][2];
        
        rotate_x(rotated_vertices[i], angle_x);
        rotate_y(rotated_vertices[i], angle_y);
        rotate_z(rotated_vertices[i], angle_z);
        
        project(rotated_vertices[i], &projected[i][0], &projected[i][1]);
    }
    
    // Draw just the front face (first triangle)
    int face_idx = 0;
    int v0 = faces[face_idx][0];
    int v1 = faces[face_idx][1];
    int v2 = faces[face_idx][2];
    
    // Get 2D coordinates
    int x0 = (int)(projected[v0][0] + 0.5f);
    int y0 = (int)(projected[v0][1] + 0.5f);
    int x1 = (int)(projected[v1][0] + 0.5f);
    int y1 = (int)(projected[v1][1] + 0.5f);
    int x2 = (int)(projected[v2][0] + 0.5f);
    int y2 = (int)(projected[v2][1] + 0.5f);
    
    // Draw filled triangle - bright red
    draw_filled_triangle(framebuffer, x0, y0, x1, y1, x2, y2, COLOR_RED);
    
    // Draw second triangle of front face
    face_idx = 1;
    v0 = faces[face_idx][0];
    v1 = faces[face_idx][1];
    v2 = faces[face_idx][2];
    
    x0 = (int)(projected[v0][0] + 0.5f);
    y0 = (int)(projected[v0][1] + 0.5f);
    x1 = (int)(projected[v1][0] + 0.5f);
    y1 = (int)(projected[v1][1] + 0.5f);
    x2 = (int)(projected[v2][0] + 0.5f);
    y2 = (int)(projected[v2][1] + 0.5f);
    
    draw_filled_triangle(framebuffer, x0, y0, x1, y1, x2, y2, COLOR_RED);
    
    // NOTE: Wireframe removed - it was making the fill look transparent!
}

// Render the cube with solid faces (simple version - no culling for testing)
static void render_cube_solid_simple(void) {
    // Store rotated vertices
    float rotated_vertices[8][3];
    
    // Transform all vertices
    for (int i = 0; i < 8; i++) {
        rotated_vertices[i][0] = vertices[i][0];
        rotated_vertices[i][1] = vertices[i][1];
        rotated_vertices[i][2] = vertices[i][2];
        
        rotate_x(rotated_vertices[i], angle_x);
        rotate_y(rotated_vertices[i], angle_y);
        rotate_z(rotated_vertices[i], angle_z);
        
        project(rotated_vertices[i], &projected[i][0], &projected[i][1]);
    }
    
    // Draw all 12 triangles
    for (int face_idx = 0; face_idx < 12; face_idx++) {
        int v0 = faces[face_idx][0];
        int v1 = faces[face_idx][1];
        int v2 = faces[face_idx][2];
        
        // Get 2D coordinates
        int x0 = (int)(projected[v0][0] + 0.5f);
        int y0 = (int)(projected[v0][1] + 0.5f);
        int x1 = (int)(projected[v1][0] + 0.5f);
        int y1 = (int)(projected[v1][1] + 0.5f);
        int x2 = (int)(projected[v2][0] + 0.5f);
        int y2 = (int)(projected[v2][1] + 0.5f);
        
        // Get face color
        uint16_t color = face_colors[face_idx / 2];
        
        // Draw filled triangle with full brightness
        draw_filled_triangle(framebuffer, x0, y0, x1, y1, x2, y2, color);
    }
}

// Render the cube with solid faces
static void render_cube_solid(void) {
    // Store rotated vertices
    float rotated_vertices[8][3];
    
    // Transform all vertices
    for (int i = 0; i < 8; i++) {
        rotated_vertices[i][0] = vertices[i][0];
        rotated_vertices[i][1] = vertices[i][1];
        rotated_vertices[i][2] = vertices[i][2];
        
        rotate_x(rotated_vertices[i], angle_x);
        rotate_y(rotated_vertices[i], angle_y);
        rotate_z(rotated_vertices[i], angle_z);
        
        project(rotated_vertices[i], &projected[i][0], &projected[i][1]);
    }
    
    // Prepare face data for sorting
    typedef struct {
        int index;
        float depth;
    } face_data_t;
    
    face_data_t face_list[12];
    
    // Calculate depth for each face
    for (int i = 0; i < 12; i++) {
        face_list[i].index = i;
        face_list[i].depth = face_depth(i, rotated_vertices);
    }
    
    // Sort faces by depth (back to front for painter's algorithm)
    for (int i = 0; i < 11; i++) {
        for (int j = 0; j < 11 - i; j++) {
            if (face_list[j].depth > face_list[j + 1].depth) {
                face_data_t temp = face_list[j];
                face_list[j] = face_list[j + 1];
                face_list[j + 1] = temp;
            }
        }
    }
    
    // Draw faces back to front (with backface culling)
    for (int i = 0; i < 12; i++) {
        int face_idx = face_list[i].index;
        
        // Check if face is visible
        if (!is_face_visible(face_idx)) continue;
        
        int v0 = faces[face_idx][0];
        int v1 = faces[face_idx][1];
        int v2 = faces[face_idx][2];
        
        // Get 2D coordinates
        int x0 = (int)(projected[v0][0] + 0.5f);
        int y0 = (int)(projected[v0][1] + 0.5f);
        int x1 = (int)(projected[v1][0] + 0.5f);
        int y1 = (int)(projected[v1][1] + 0.5f);
        int x2 = (int)(projected[v2][0] + 0.5f);
        int y2 = (int)(projected[v2][1] + 0.5f);
        
        // Get face color (each pair of triangles = one face)
        uint16_t color = face_colors[face_idx / 2];
        
        // Calculate lighting
        uint8_t intensity = calculate_lighting(face_idx, rotated_vertices);
        
        // Draw filled triangle
        draw_shaded_triangle(framebuffer, x0, y0, x1, y1, x2, y2, color, intensity);
    }
}

// Render the cube (original wireframe version)
static void render_cube(void) {
    // Transform and project all vertices
    for (int i = 0; i < 8; i++) {
        float rotated[3] = {vertices[i][0], vertices[i][1], vertices[i][2]};
        
        rotate_x(rotated, angle_x);
        rotate_y(rotated, angle_y);
        rotate_z(rotated, angle_z);
        
        project(rotated, &projected[i][0], &projected[i][1]);
    }
    
    // Sort edges by depth (painter's algorithm - back to front)
    int sorted_edges[12];
    float depths[12];
    
    for (int i = 0; i < 12; i++) {
        sorted_edges[i] = i;
        depths[i] = edge_depth(i);
    }
    
    // Simple bubble sort by depth
    for (int i = 0; i < 11; i++) {
        for (int j = 0; j < 11 - i; j++) {
            if (depths[j] > depths[j + 1]) {
                float temp_d = depths[j];
                depths[j] = depths[j + 1];
                depths[j + 1] = temp_d;
                
                int temp_e = sorted_edges[j];
                sorted_edges[j] = sorted_edges[j + 1];
                sorted_edges[j + 1] = temp_e;
            }
        }
    }
    
    // Draw edges in sorted order with depth-based color
    for (int i = 0; i < 12; i++) {
        int edge_idx = sorted_edges[i];
        int v1 = edges[edge_idx][0];
        int v2 = edges[edge_idx][1];
        
        // Color based on depth (cyan to blue gradient)
        float depth_norm = (depths[i] + 2.0f) / 4.0f;  // Normalize to 0-1
        if (depth_norm < 0.0f) depth_norm = 0.0f;
        if (depth_norm > 1.0f) depth_norm = 1.0f;
        
        uint8_t blue_intensity = (uint8_t)(31 * depth_norm);
        uint8_t green_intensity = (uint8_t)(63 * (1.0f - depth_norm * 0.5f));
        uint16_t color = (blue_intensity) | (green_intensity << 5);
        
        draw_line(projected[v1][0], projected[v1][1],
                  projected[v2][0], projected[v2][1], color);
    }
    
    // Draw vertices as small dots
    for (int i = 0; i < 8; i++) {
        int x = (int)(projected[i][0] + 0.5f);
        int y = (int)(projected[i][1] + 0.5f);
        
        if (x >= 0 && x < 320 && y >= 0 && y < 240) {
            framebuffer[y * DISPLAY_WIDTH + x] = COLOR_WHITE;
            // Make vertices slightly thicker
            if (x > 0) framebuffer[y * DISPLAY_WIDTH + (x-1)] = COLOR_WHITE;
            if (x < 319) framebuffer[y * DISPLAY_WIDTH + (x+1)] = COLOR_WHITE;
            if (y > 0) framebuffer[(y-1) * DISPLAY_WIDTH + x] = COLOR_WHITE;
            if (y < 239) framebuffer[(y+1) * DISPLAY_WIDTH + x] = COLOR_WHITE;
        }
    }
}

/* Button callbacks */
static void btn_a_callback(button_t btn) { 
    (void)btn;
    auto_rotate = !auto_rotate;
}

static void btn_b_callback(button_t btn) { 
    (void)btn;
    solid_mode = !solid_mode;  // Toggle solid/wireframe
}

static void btn_x_callback(button_t btn) { 
    (void)btn;
    // Increase rotation speed
    speed_x *= 1.5f;
    speed_y *= 1.5f;
    speed_z *= 1.5f;
    
    // Cap maximum speed
    if (speed_x > 0.1f) speed_x = 0.1f;
    if (speed_y > 0.1f) speed_y = 0.1f;
    if (speed_z > 0.1f) speed_z = 0.1f;
}

static void btn_y_callback(button_t btn) { 
    (void)btn;
    // Zoom in/out
    zoom += 0.3f;
    if (zoom > 3.0f) zoom = 0.8f;  // Cycle back
}

// Clear framebuffer
static void fb_clear(uint16_t color) {
    for (int i = 0; i < DISPLAY_WIDTH * DISPLAY_HEIGHT; i++) {
        framebuffer[i] = color;
    }
}

// Simple 5x8 font (subset for our needs)
static const uint8_t simple_font[][5] = {
    {0x00, 0x00, 0x00, 0x00, 0x00}, // Space (32)
    {0x00, 0x00, 0x5F, 0x00, 0x00}, // !
    {0x00, 0x07, 0x00, 0x07, 0x00}, // "
    {0x14, 0x7F, 0x14, 0x7F, 0x14}, // #
    {0x12, 0x2A, 0x7F, 0x2A, 0x24}, // $
    {0x62, 0x64, 0x08, 0x13, 0x23}, // %
    {0x50, 0x22, 0x55, 0x49, 0x36}, // &
    {0x00, 0x00, 0x07, 0x00, 0x00}, // '
    {0x00, 0x41, 0x22, 0x1C, 0x00}, // (
    {0x00, 0x1C, 0x22, 0x41, 0x00}, // )
    {0x14, 0x08, 0x3E, 0x08, 0x14}, // *
    {0x08, 0x08, 0x3E, 0x08, 0x08}, // +
    {0x00, 0x30, 0x50, 0x00, 0x00}, // ,
    {0x08, 0x08, 0x08, 0x08, 0x08}, // -
    {0x00, 0x60, 0x60, 0x00, 0x00}, // .
    {0x02, 0x04, 0x08, 0x10, 0x20}, // /
    {0x3E, 0x45, 0x49, 0x51, 0x3E}, // 0
    {0x00, 0x40, 0x7F, 0x42, 0x00}, // 1
    {0x46, 0x49, 0x51, 0x61, 0x42}, // 2
    {0x31, 0x4B, 0x45, 0x41, 0x21}, // 3
    {0x10, 0x7F, 0x12, 0x14, 0x18}, // 4
    {0x39, 0x49, 0x49, 0x49, 0x2F}, // 5
    {0x30, 0x49, 0x49, 0x4A, 0x3C}, // 6
    {0x07, 0x0D, 0x09, 0x71, 0x01}, // 7
    {0x36, 0x49, 0x49, 0x49, 0x36}, // 8
    {0x1E, 0x29, 0x49, 0x49, 0x0E}, // 9
    {0x00, 0x36, 0x36, 0x00, 0x00}, // :
    {0x00, 0x36, 0x76, 0x00, 0x00}, // ;
    {0x00, 0x41, 0x22, 0x14, 0x08}, // <
    {0x14, 0x14, 0x14, 0x14, 0x14}, // =
    {0x08, 0x14, 0x22, 0x41, 0x00}, // >
    {0x06, 0x09, 0x51, 0x01, 0x06}, // ?
    {0x3E, 0x41, 0x79, 0x49, 0x32}, // @
    {0x7E, 0x11, 0x11, 0x11, 0x7E}, // A (65)
    {0x36, 0x49, 0x49, 0x49, 0x7F}, // B
    {0x22, 0x41, 0x41, 0x41, 0x3E}, // C
    {0x1C, 0x22, 0x41, 0x41, 0x7F}, // D
    {0x41, 0x49, 0x49, 0x49, 0x7F}, // E
    {0x01, 0x09, 0x09, 0x09, 0x7F}, // F
    {0x7A, 0x49, 0x49, 0x41, 0x3E}, // G
    {0x7F, 0x08, 0x08, 0x08, 0x7F}, // H
    {0x00, 0x41, 0x7F, 0x41, 0x00}, // I
    {0x01, 0x3F, 0x41, 0x40, 0x20}, // J
    {0x41, 0x22, 0x14, 0x08, 0x7F}, // K
    {0x40, 0x40, 0x40, 0x40, 0x7F}, // L
    {0x7F, 0x02, 0x0C, 0x02, 0x7F}, // M
    {0x7F, 0x10, 0x0C, 0x02, 0x7F}, // N
    {0x3E, 0x41, 0x41, 0x41, 0x3E}, // O
    {0x06, 0x09, 0x09, 0x09, 0x7F}, // P
    {0x5E, 0x21, 0x51, 0x41, 0x3E}, // Q
    {0x46, 0x29, 0x19, 0x09, 0x7F}, // R
    {0x31, 0x49, 0x49, 0x49, 0x46}, // S
    {0x01, 0x01, 0x7F, 0x01, 0x01}, // T
    {0x3F, 0x40, 0x40, 0x40, 0x3F}, // U
    {0x1F, 0x20, 0x40, 0x20, 0x1F}, // V
    {0x3F, 0x40, 0x38, 0x40, 0x3F}, // W
    {0x63, 0x14, 0x08, 0x14, 0x63}, // X
    {0x07, 0x08, 0x70, 0x08, 0x07}, // Y
    {0x43, 0x45, 0x49, 0x51, 0x61}, // Z
    {0x00, 0x41, 0x41, 0x7F, 0x00}, // [
    {0x20, 0x10, 0x08, 0x04, 0x02}, // backslash
    {0x00, 0x7F, 0x41, 0x41, 0x00}, // ]
    {0x04, 0x02, 0x01, 0x02, 0x04}, // ^
    {0x40, 0x40, 0x40, 0x40, 0x40}, // _
    {0x00, 0x04, 0x02, 0x01, 0x00}, // `
    {0x78, 0x54, 0x54, 0x54, 0x20}, // a (97)
    {0x38, 0x44, 0x44, 0x48, 0x7F}, // b
    {0x28, 0x44, 0x44, 0x44, 0x38}, // c
    {0x7F, 0x48, 0x44, 0x44, 0x38}, // d
    {0x18, 0x54, 0x54, 0x54, 0x38}, // e
    {0x02, 0x01, 0x09, 0x7E, 0x08}, // f
    {0x4C, 0x92, 0x92, 0x92, 0x7C}, // g
    {0x78, 0x04, 0x04, 0x08, 0x7F}, // h
    {0x00, 0x44, 0x7D, 0x40, 0x00}, // i
    {0x02, 0x7D, 0x82, 0x80, 0x40}, // j
    {0x44, 0x28, 0x10, 0x08, 0x7F}, // k
    {0x00, 0x40, 0x7F, 0x41, 0x00}, // l
    {0x7C, 0x04, 0x18, 0x04, 0x7C}, // m
    {0x78, 0x04, 0x04, 0x08, 0x7C}, // n
    {0x38, 0x44, 0x44, 0x44, 0x38}, // o
    {0x18, 0x24, 0x24, 0x24, 0xFC}, // p
    {0xFC, 0x24, 0x24, 0x24, 0x18}, // q
    {0x08, 0x04, 0x04, 0x08, 0x7C}, // r
    {0x24, 0x54, 0x54, 0x54, 0x48}, // s
    {0x20, 0x40, 0x44, 0x3F, 0x04}, // t
    {0x3C, 0x40, 0x40, 0x20, 0x7C}, // u
    {0x1C, 0x20, 0x40, 0x20, 0x1C}, // v
    {0x3C, 0x40, 0x30, 0x40, 0x3C}, // w
    {0x44, 0x28, 0x10, 0x28, 0x44}, // x
    {0x7C, 0x90, 0x90, 0x90, 0x4C}, // y
    {0x44, 0x64, 0x54, 0x4C, 0x44}, // z
};

// Draw character to framebuffer
static void fb_draw_char(uint16_t x, uint16_t y, char c, uint16_t color, uint16_t bg_color) {
    if (x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return;
    
    // Convert to font index (supports space through 'z')
    int idx = c - 32;
    if (idx < 0 || idx >= 91) return; // Out of range
    
    const uint8_t *char_data = simple_font[idx];
    
    // Draw character bitmap
    for (int col = 0; col < 5 && (x + col) < DISPLAY_WIDTH; col++) {
        uint8_t line = char_data[4 - col]; // Reverse column order
        for (int row = 0; row < 8 && (y + row) < DISPLAY_HEIGHT; row++) {
            uint16_t pixel_color = (line & (1 << row)) ? color : bg_color;
            framebuffer[(y + row) * DISPLAY_WIDTH + (x + col)] = pixel_color;
        }
    }
}

// Draw string to framebuffer
static void fb_draw_string(uint16_t x, uint16_t y, const char* str, uint16_t color, uint16_t bg_color) {
    int offset_x = 0;
    while (*str && (x + offset_x) < DISPLAY_WIDTH) {
        fb_draw_char(x + offset_x, y, *str, color, bg_color);
        offset_x += 6; // 5 pixel font + 1 pixel spacing
        str++;
    }
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

    // Set up button callbacks
    button_set_callback(BUTTON_A, btn_a_callback);
    button_set_callback(BUTTON_B, btn_b_callback);
    button_set_callback(BUTTON_X, btn_x_callback);
    button_set_callback(BUTTON_Y, btn_y_callback);

    display_clear(COLOR_BLACK);
    display_set_backlight(true);
    
    printf("3D Cube Demo Started\n");
    printf("Controls:\n");
    printf("  A - Toggle rotation\n");
    printf("  B - Toggle solid/wireframe\n");
    printf("  X - Increase speed\n");
    printf("  Y - Cycle zoom\n");

    while (1) {
        buttons_update();
        
        // Clear framebuffer (not the display)
        fb_clear(COLOR_BLACK);
        
        // Update rotation angles if auto-rotating
        if (auto_rotate) {
            angle_x += speed_x;
            angle_y += speed_y;
            angle_z += speed_z;
            
            // Wrap angles to prevent overflow
            if (angle_x > 2 * M_PI) angle_x -= 2 * M_PI;
            if (angle_y > 2 * M_PI) angle_y -= 2 * M_PI;
            if (angle_z > 2 * M_PI) angle_z -= 2 * M_PI;
        }
        
        // Render the cube to framebuffer
        if (solid_mode) {
            render_cube_painter();  // Simple painter's algorithm, no backface culling
        } else {
            render_cube();
        }
        
        // Draw UI text to framebuffer (before blitting!)
        char buf[50];
        snprintf(buf, sizeof(buf), "A:%s B:%s X:Speed Y:Zoom", 
                 auto_rotate ? "Pause" : "Play ",
                 solid_mode ? "Wire" : "Solid");
        fb_draw_string(5, 5, buf, COLOR_GREEN, COLOR_BLACK);
        
        snprintf(buf, sizeof(buf), "Speed: %.3f  Zoom: %.1fx", 
                 speed_y, zoom);
        fb_draw_string(5, 225, buf, COLOR_CYAN, COLOR_BLACK);
        
        // Blit entire framebuffer to display in one shot (flicker-free!)
        display_blit_full(framebuffer);
        
        // Frame rate control (~30 fps)
        sleep_ms(33);
    }

    return 0;
}
