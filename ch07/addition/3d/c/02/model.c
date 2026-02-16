#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "model.h"
#include "rmath.h"

int load_pam_texture(const char* filename, unsigned char** texture, int* width, int* height) {
    FILE* file = fopen(filename, "r");
    if (!file) {
        printf("Error: Cannot open PAM file %s\n", filename);
        return 0;
    }

    char line[256];
    int depth = 0, maxval = 0;
    *width = 0;
    *height = 0;
    
    // Read header
    if (!fgets(line, sizeof(line), file) || strncmp(line, "P7", 2) != 0) {
        printf("Error: Not a P7 PAM file\n");
        fclose(file);
        return 0;
    }

    while (fgets(line, sizeof(line), file)) {
        if (line[0] == '#') continue;
        if (strncmp(line, "WIDTH", 5) == 0) {
            sscanf(line, "WIDTH %d", width);
        }
        else if (strncmp(line, "HEIGHT", 6) == 0) {
            sscanf(line, "HEIGHT %d", height);
        }
        else if (strncmp(line, "DEPTH", 5) == 0) {
            sscanf(line, "DEPTH %d", &depth);
        }
        else if (strncmp(line, "MAXVAL", 6) == 0) {
            sscanf(line, "MAXVAL %d", &maxval);
        }
        else if (strncmp(line, "TUPLTYPE", 8) == 0) {
            if (strstr(line, "RGB") == NULL && strstr(line, "GRAYSCALE") == NULL) {
                printf("Error: Only RGB and GRAYSCALE TUPLTYPE supported\n");
                fclose(file);
                return 0;
            }
        }
        else if (strncmp(line, "ENDHDR", 6) == 0) {
            break;
        }
    }

    // Validate header values
    if (*width <= 0 || *height <= 0) {
        printf("Error: Invalid dimensions (%dx%d)\n", *width, *height);
        fclose(file);
        return 0;
    }
    
    if (depth != 1 && depth != 3) {
        printf("Error: Only depth 1 (grayscale) or 3 (RGB) supported (got %d)\n", depth);
        fclose(file);
        return 0;
    }
    
    if (maxval != 255) {
        printf("Error: Only MAXVAL 255 supported (got %d)\n", maxval);
        fclose(file);
        return 0;
    }

    // Allocate texture memory (always RGB)
    *texture = malloc((*width) * (*height) * 3 * sizeof(unsigned char));
    if (!*texture) {
        printf("Error: Memory allocation failed for texture\n");
        fclose(file);
        return 0;
    }

    // Read pixel data
    int pixel_count = (*width) * (*height);
    for (int i = 0; i < pixel_count; i++) {
        if (depth == 3) {
            // RGB
            int r, g, b;
            if (fscanf(file, "%d %d %d", &r, &g, &b) != 3) {
                printf("Error: Failed to read RGB pixel data at pixel %d\n", i);
                free(*texture);
                fclose(file);
                return 0;
            }
            (*texture)[i * 3] = (unsigned char)r;
            (*texture)[i * 3 + 1] = (unsigned char)g;
            (*texture)[i * 3 + 2] = (unsigned char)b;
        } else {
            // Grayscale - convert to RGB
            int gray;
            if (fscanf(file, "%d", &gray) != 1) {
                printf("Error: Failed to read grayscale pixel data at pixel %d\n", i);
                free(*texture);
                fclose(file);
                return 0;
            }
            (*texture)[i * 3] = (unsigned char)gray;
            (*texture)[i * 3 + 1] = (unsigned char)gray;
            (*texture)[i * 3 + 2] = (unsigned char)gray;
        }
    }

    fclose(file);
    printf("Successfully loaded texture: %dx%d, depth=%d\n", *width, *height, depth);
    return 1;
}

Model* create_colored_cube(const char* pam_filename) {
    Model* model = malloc(sizeof(Model));
    model->vertex_count = 8;
    model->face_count = 12;
    
    model->vertices = malloc(model->vertex_count * sizeof(Vec3));
    model->normals = malloc(model->vertex_count * sizeof(Vec3));
    model->faces = malloc(model->face_count * sizeof(Face));
    model->face_colors = malloc(model->face_count * sizeof(Vec3));
    model->face_normals = malloc(model->face_count * sizeof(Vec3));
    
    // Allocate 3 texture coordinates per face (one for each triangle vertex)
    model->tex_coords = malloc(model->face_count * 3 * sizeof(TexCoord));
    
    // Vertex positions
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
    
    // Face definitions with FIXED texture coordinates per triangle
    // Back face - Red (triangles 0, 1)
    model->faces[0] = (Face){0, 1, 2};
    model->faces[1] = (Face){0, 2, 3};
    model->face_colors[0] = (Vec3){0.8f, 0.2f, 0.2f};
    model->face_colors[1] = (Vec3){0.8f, 0.2f, 0.2f};
    model->face_normals[0] = (Vec3){0, 0, -1};
    model->face_normals[1] = (Vec3){0, 0, -1};
    // Triangle 0: v0, v1, v2
    model->tex_coords[0] = (TexCoord){0, 1}; // bottom-left
    model->tex_coords[1] = (TexCoord){1, 1}; // bottom-right
    model->tex_coords[2] = (TexCoord){1, 0}; // top-right
    // Triangle 1: v0, v2, v3
    model->tex_coords[3] = (TexCoord){0, 1}; // bottom-left
    model->tex_coords[4] = (TexCoord){1, 0}; // top-right
    model->tex_coords[5] = (TexCoord){0, 0}; // top-left
    
    // Front face - Green (triangles 2, 3)
    model->faces[2] = (Face){4, 6, 5};
    model->faces[3] = (Face){4, 7, 6};
    model->face_colors[2] = (Vec3){0.2f, 0.8f, 0.2f};
    model->face_colors[3] = (Vec3){0.2f, 0.8f, 0.2f};
    model->face_normals[2] = (Vec3){0, 0, 1};
    model->face_normals[3] = (Vec3){0, 0, 1};
    // Triangle 2: v4, v6, v5
    model->tex_coords[6] = (TexCoord){0, 1};  // bottom-left
    model->tex_coords[7] = (TexCoord){1, 0};  // top-right
    model->tex_coords[8] = (TexCoord){1, 1};  // bottom-right
    // Triangle 3: v4, v7, v6
    model->tex_coords[9] = (TexCoord){0, 1};   // bottom-left
    model->tex_coords[10] = (TexCoord){0, 0};  // top-left
    model->tex_coords[11] = (TexCoord){1, 0};  // top-right
    
    // Left face - Blue (triangles 4, 5)
    model->faces[4] = (Face){0, 3, 7};
    model->faces[5] = (Face){0, 7, 4};
    model->face_colors[4] = (Vec3){0.2f, 0.2f, 0.8f};
    model->face_colors[5] = (Vec3){0.2f, 0.2f, 0.8f};
    model->face_normals[4] = (Vec3){-1, 0, 0};
    model->face_normals[5] = (Vec3){-1, 0, 0};
    // Triangle 4: v0, v3, v7
    model->tex_coords[12] = (TexCoord){0, 1}; // bottom-left
    model->tex_coords[13] = (TexCoord){1, 1}; // bottom-right
    model->tex_coords[14] = (TexCoord){1, 0}; // top-right
    // Triangle 5: v0, v7, v4
    model->tex_coords[15] = (TexCoord){0, 1}; // bottom-left
    model->tex_coords[16] = (TexCoord){1, 0}; // top-right
    model->tex_coords[17] = (TexCoord){0, 0}; // top-left
    
    // Right face - Yellow (triangles 6, 7)
    model->faces[6] = (Face){1, 5, 6};
    model->faces[7] = (Face){1, 6, 2};
    model->face_colors[6] = (Vec3){0.8f, 0.8f, 0.2f};
    model->face_colors[7] = (Vec3){0.8f, 0.8f, 0.2f};
    model->face_normals[6] = (Vec3){1, 0, 0};
    model->face_normals[7] = (Vec3){1, 0, 0};
    // Triangle 6: v1, v5, v6
    model->tex_coords[18] = (TexCoord){0, 1}; // bottom-left
    model->tex_coords[19] = (TexCoord){1, 1}; // bottom-right
    model->tex_coords[20] = (TexCoord){1, 0}; // top-right
    // Triangle 7: v1, v6, v2
    model->tex_coords[21] = (TexCoord){0, 1}; // bottom-left
    model->tex_coords[22] = (TexCoord){1, 0}; // top-right
    model->tex_coords[23] = (TexCoord){0, 0}; // top-left
    
    // Bottom face - Magenta (triangles 8, 9)
    model->faces[8] = (Face){0, 4, 5};
    model->faces[9] = (Face){0, 5, 1};
    model->face_colors[8] = (Vec3){0.8f, 0.2f, 0.8f};
    model->face_colors[9] = (Vec3){0.8f, 0.2f, 0.8f};
    model->face_normals[8] = (Vec3){0, -1, 0};
    model->face_normals[9] = (Vec3){0, -1, 0};
    // Triangle 8: v0, v4, v5
    model->tex_coords[24] = (TexCoord){0, 0}; // top-left
    model->tex_coords[25] = (TexCoord){0, 1}; // bottom-left
    model->tex_coords[26] = (TexCoord){1, 1}; // bottom-right
    // Triangle 9: v0, v5, v1
    model->tex_coords[27] = (TexCoord){0, 0}; // top-left
    model->tex_coords[28] = (TexCoord){1, 1}; // bottom-right
    model->tex_coords[29] = (TexCoord){1, 0}; // top-right
    
    // Top face - Cyan (triangles 10, 11)
    model->faces[10] = (Face){3, 2, 6};
    model->faces[11] = (Face){3, 6, 7};
    model->face_colors[10] = (Vec3){0.2f, 0.8f, 0.8f};
    model->face_colors[11] = (Vec3){0.2f, 0.8f, 0.8f};
    model->face_normals[10] = (Vec3){0, 1, 0};
    model->face_normals[11] = (Vec3){0, 1, 0};
    // Triangle 10: v3, v2, v6
    model->tex_coords[30] = (TexCoord){0, 0}; // top-left
    model->tex_coords[31] = (TexCoord){1, 0}; // top-right
    model->tex_coords[32] = (TexCoord){1, 1}; // bottom-right
    // Triangle 11: v3, v6, v7
    model->tex_coords[33] = (TexCoord){0, 0}; // top-left
    model->tex_coords[34] = (TexCoord){1, 1}; // bottom-right
    model->tex_coords[35] = (TexCoord){0, 1}; // bottom-left
    
    // Load PAM texture
    if (!load_pam_texture(pam_filename, &model->texture, &model->tex_width, &model->tex_height)) {
        printf("Error: Failed to load texture from %s, using fallback checkerboard\n", pam_filename);
        model->tex_width = 8;
        model->tex_height = 8;
        model->texture = malloc(model->tex_width * model->tex_height * 3 * sizeof(unsigned char));
        
        // Create a simple checkerboard pattern for debugging
        for (int y = 0; y < model->tex_height; y++) {
            for (int x = 0; x < model->tex_width; x++) {
                int index = (y * model->tex_width + x) * 3;
                int checker = ((x / 2) + (y / 2)) % 2;
                if (checker) {
                    model->texture[index] = 255;     // White
                    model->texture[index + 1] = 255;
                    model->texture[index + 2] = 255;
                } else {
                    model->texture[index] = 128;     // Gray
                    model->texture[index + 1] = 128;
                    model->texture[index + 2] = 128;
                }
            }
        }
    }
    
    return model;
}

void free_model(Model* model) {
    if (model) {
        free(model->vertices);
        free(model->normals);
        free(model->faces);
        free(model->face_colors);
        free(model->face_normals);
        free(model->tex_coords);
        free(model->texture);
        free(model);
    }
}

Light create_default_light() {
    Light light;
    light.direction = vec3_normalize((Vec3){0.3f, -0.7f, 0.2f});
    light.color = (Vec3){1.0f, 1.0f, 1.0f}; // Pure white for better visibility
    light.intensity = 1.2f; // Increased intensity
    light.ambient_color = (Vec3){1.0f, 1.0f, 1.0f}; // Pure white ambient
    light.ambient_intensity = 0.5f; // Increased ambient for better visibility
    return light;
}