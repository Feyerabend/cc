#ifndef MODEL_H
#define MODEL_H

#include "rmath.h"

typedef struct {
    int v1, v2, v3;  // Vertex indices for triangle face
} Face;

typedef struct {
    Vec3 *vertices;
    Vec3 *normals;      // Normal vectors for each vertex
    Face *faces;
    Vec3 *face_colors;  // Base color for each face
    Vec3 *face_normals; // Normal for each face
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

typedef struct {
    Vec3 direction;     // Light direction (normalized)
    Vec3 color;         // Light color (RGB 0-1)
    float intensity;    // Light intensity
    Vec3 ambient_color; // Ambient light color
    float ambient_intensity; // Ambient light intensity
} Light;

Model* create_colored_cube();
//Model* create_floor();
void free_model(Model* model);
Light create_default_light();

#endif