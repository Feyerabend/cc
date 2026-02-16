#include <stdlib.h>
#include "model.h"
#include "rmath.h"

Model* create_colored_cube() {
    Model* model = malloc(sizeof(Model));
    model->vertex_count = 8;
    model->face_count = 12;
    
    model->vertices = malloc(model->vertex_count * sizeof(Vec3));
    model->normals = malloc(model->vertex_count * sizeof(Vec3));
    model->faces = malloc(model->face_count * sizeof(Face));
    model->face_colors = malloc(model->face_count * sizeof(Vec3));
    model->face_normals = malloc(model->face_count * sizeof(Vec3));
    
    model->vertices[0] = (Vec3){-1, -1, -1}; // back bottom left
    model->vertices[1] = (Vec3){ 1, -1, -1}; // back bottom right
    model->vertices[2] = (Vec3){ 1,  1, -1}; // back top right
    model->vertices[3] = (Vec3){-1,  1, -1}; // back top left
    model->vertices[4] = (Vec3){-1, -1,  1}; // front bottom left
    model->vertices[5] = (Vec3){ 1, -1,  1}; // front bottom right
    model->vertices[6] = (Vec3){ 1,  1,  1}; // front top right
    model->vertices[7] = (Vec3){-1,  1,  1}; // front top left
    
    for (int i = 0; i < model->vertex_count; i++) {
        model->normals[i] = (Vec3){0, 0, 0};
    }
    
    // Back face - Red
    model->faces[0] = (Face){0, 1, 2};
    model->faces[1] = (Face){0, 2, 3};
    model->face_colors[0] = (Vec3){0.8f, 0.2f, 0.2f};
    model->face_colors[1] = (Vec3){0.8f, 0.2f, 0.2f};
    model->face_normals[0] = (Vec3){0, 0, -1};
    model->face_normals[1] = (Vec3){0, 0, -1};
    
    // Front face - Green
    model->faces[2] = (Face){4, 6, 5};
    model->faces[3] = (Face){4, 7, 6};
    model->face_colors[2] = (Vec3){0.2f, 0.8f, 0.2f};
    model->face_colors[3] = (Vec3){0.2f, 0.8f, 0.2f};
    model->face_normals[2] = (Vec3){0, 0, 1};
    model->face_normals[3] = (Vec3){0, 0, 1};
    
    // Left face - Blue
    model->faces[4] = (Face){0, 3, 7};
    model->faces[5] = (Face){0, 7, 4};
    model->face_colors[4] = (Vec3){0.2f, 0.2f, 0.8f};
    model->face_colors[5] = (Vec3){0.2f, 0.2f, 0.8f};
    model->face_normals[4] = (Vec3){-1, 0, 0};
    model->face_normals[5] = (Vec3){-1, 0, 0};
    
    // Right face - Yellow
    model->faces[6] = (Face){1, 5, 6};
    model->faces[7] = (Face){1, 6, 2};
    model->face_colors[6] = (Vec3){0.8f, 0.8f, 0.2f};
    model->face_colors[7] = (Vec3){0.8f, 0.8f, 0.2f};
    model->face_normals[6] = (Vec3){1, 0, 0};
    model->face_normals[7] = (Vec3){1, 0, 0};
    
    // Bottom face - Magenta
    model->faces[8] = (Face){0, 4, 5};
    model->faces[9] = (Face){0, 5, 1};
    model->face_colors[8] = (Vec3){0.8f, 0.2f, 0.8f};
    model->face_colors[9] = (Vec3){0.8f, 0.2f, 0.8f};
    model->face_normals[8] = (Vec3){0, -1, 0};
    model->face_normals[9] = (Vec3){0, -1, 0};
    
    // Top face - Cyan
    model->faces[10] = (Face){3, 2, 6};
    model->faces[11] = (Face){3, 6, 7};
    model->face_colors[10] = (Vec3){0.2f, 0.8f, 0.8f};
    model->face_colors[11] = (Vec3){0.2f, 0.8f, 0.8f};
    model->face_normals[10] = (Vec3){0, 1, 0};
    model->face_normals[11] = (Vec3){0, 1, 0};
    
    return model;
}

/*
Model* create_floor() {
    Model* model = malloc(sizeof(Model));
    model->vertex_count = 4;
    model->face_count = 2;
    
    model->vertices = malloc(model->vertex_count * sizeof(Vec3));
    model->normals = malloc(model->vertex_count * sizeof(Vec3));
    model->faces = malloc(model->face_count * sizeof(Face));
    model->face_colors = malloc(model->face_count * sizeof(Vec3));
    model->face_normals = malloc(model->face_count * sizeof(Vec3));
    
    float size = 8.0f;
    model->vertices[0] = (Vec3){-size, -3, -size}; // bottom left
    model->vertices[1] = (Vec3){ size, -3, -size}; // bottom right
    model->vertices[2] = (Vec3){ size, -3,  size}; // top right
    model->vertices[3] = (Vec3){-size, -3,  size}; // top left
    
    for (int i = 0; i < 4; i++) {
        model->normals[i] = (Vec3){0, 1, 0};
    }
    
    model->faces[0] = (Face){0, 1, 2};
    model->faces[1] = (Face){0, 2, 3};
    
    model->face_colors[0] = (Vec3){0.4f, 0.4f, 0.4f};
    model->face_colors[1] = (Vec3){0.4f, 0.4f, 0.4f};
    
    model->face_normals[0] = (Vec3){0, 1, 0};
    model->face_normals[1] = (Vec3){0, 1, 0};
    
    return model;
}*/

void free_model(Model* model) {
    if (model) {
        free(model->vertices);
        free(model->normals);
        free(model->faces);
        free(model->face_colors);
        free(model->face_normals);
        free(model);
    }
}

Light create_default_light() {
    Light light;
    light.direction = vec3_normalize((Vec3){0.3f, -0.7f, 0.2f});
    light.color = (Vec3){1.0f, 1.0f, 0.9f}; // Slightly warm white
    light.intensity = 0.8f;
    light.ambient_color = (Vec3){0.8f, 0.9f, 1.0f}; // Slightly cool ambient
    light.ambient_intensity = 0.3f;
    return light;
}