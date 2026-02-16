#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "model.h"
#include "rendering.h"

int main() {
    printf("Starting 3D Renderer...\n");

    Camera camera = {
        .position = {0, 0, 4}, // Move camera closer
        .rotation = {0, 0, 0},
        .fov = 60.0f * M_PI / 180.0f, // Wider field of view
        .near_plane = 0.1f,
        .far_plane = 100.0f,
        .screen_width = 800,
        .screen_height = 600
    };

    Light light = create_default_light();
    Model* cube = create_colored_cube("texture.pam");
    Framebuffer* fb = create_framebuffer(camera.screen_width, camera.screen_height, 3);

    int num_frames = 60;
    float animation_speed = 2.0f;

    for (int frame = 0; frame < num_frames; frame++) {
        printf("Rendering frame %d/%d\n", frame + 1, num_frames);
        clear_framebuffer(fb, 40); // Slightly lighter background

        float t = (float)frame / (num_frames - 1) * animation_speed * M_PI;

        Vec3 cube_rotation = {
            sinf(t * 0.7f) * 0.5f, // Rotate around x
            t * 1.2f,              // Rotate around y
            cosf(t * 0.5f) * 0.3f  // Rotate around z
        };

        Vec3 cube_position = {
            0.0f, // Centered
            0.0f, // Centered
            0.0f  // At origin
        };

        light.direction = vec3_normalize((Vec3){
            sinf(t * 0.4f) * 0.5f,
            -0.7f,
            cosf(t * 0.4f) * 0.5f + 0.5f
        });

        render_solid_with_lighting(cube, &camera, cube_position, cube_rotation, fb, &light);

        char filename[256];
        snprintf(filename, sizeof(filename), "frame_%03d.pam", frame);
        save_pam(fb, filename);
    }

    free_model(cube);
    free_framebuffer(fb);

    printf("Rendering complete!\n");
    printf("Generated %d animation frames\n", num_frames);
    printf("Use an image viewer or convert to another format to view the .pam files\n");
    printf("Example: convert frame_000.pam frame_000.png\n");

    return 0;
}