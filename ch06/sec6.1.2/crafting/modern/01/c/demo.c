/**
 * demo.c
 * 
 * Demonstration of the SVG renderer capabilities
 */

#include "svg_renderer.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

/**
 * Demo 1: Basic shapes
 */
void demo_basic_shapes(void) {
    printf("Demo 1: Creating basic shapes...\n");
    
    Rasterizer* rast = rasterizer_create(500, 400, color_rgb(255, 255, 255));
    if (!rast) {
        fprintf(stderr, "Failed to create rasterizer\n");
        return;
    }
    
    /* Rectangles */
    rasterizer_draw_rectangle(rast, 20, 20, 100, 80, color_from_hex("#FF6B6B"));
    rasterizer_draw_rectangle(rast, 140, 20, 100, 80, color_from_hex("#4ECDC4"));
    
    /* Circles */
    rasterizer_draw_circle(rast, point_make(70, 180), 40, 
                          color_from_hex("#FFE66D"), 64);
    rasterizer_draw_circle(rast, point_make(190, 180), 40, 
                          color_from_hex("#95E1D3"), 64);
    
    /* Ellipses */
    rasterizer_draw_ellipse(rast, 70, 300, 50, 30, 
                           color_from_hex("#F38181"), 64);
    rasterizer_draw_ellipse(rast, 190, 300, 50, 30, 
                           color_from_hex("#AA96DA"), 64);
    
    /* Triangle using polygon */
    PointArray* triangle = point_array_create();
    point_array_add(triangle, point_make(300, 50));
    point_array_add(triangle, point_make(400, 50));
    point_array_add(triangle, point_make(350, 120));
    rasterizer_fill_polygon(rast, triangle, color_from_hex("#FCBAD3"), 
                           FILL_RULE_EVENODD);
    point_array_free(triangle);
    
    /* Star using polygon */
    PointArray* star = point_array_create();
    point_array_add(star, point_make(350, 180));
    point_array_add(star, point_make(370, 230));
    point_array_add(star, point_make(425, 230));
    point_array_add(star, point_make(380, 265));
    point_array_add(star, point_make(400, 320));
    point_array_add(star, point_make(350, 285));
    point_array_add(star, point_make(300, 320));
    point_array_add(star, point_make(320, 265));
    point_array_add(star, point_make(275, 230));
    point_array_add(star, point_make(330, 230));
    rasterizer_fill_polygon(rast, star, color_from_hex("#FFFFD2"), 
                           FILL_RULE_EVENODD);
    point_array_free(star);
    
    rasterizer_save_ppm(rast, "demo1_basic_shapes.ppm");
    rasterizer_free(rast);
    
    printf("✓ Saved to demo1_basic_shapes.ppm\n");
}

/**
 * Demo 2: Path commands with bezier curves
 */
void demo_complex_paths(void) {
    printf("\nDemo 2: Creating complex paths with curves...\n");
    
    Rasterizer* rast = rasterizer_create(500, 300, color_rgb(255, 255, 255));
    if (!rast) {
        fprintf(stderr, "Failed to create rasterizer\n");
        return;
    }
    
    /* Heart shape using cubic bezier */
    const char* heart_path = 
        "M 250,100 "
        "C 250,80 230,60 200,60 "
        "C 170,60 150,80 150,110 "
        "C 150,140 250,200 250,200 "
        "C 250,200 350,140 350,110 "
        "C 350,80 330,60 300,60 "
        "C 270,60 250,80 250,100 Z";
    
    PathCommand* heart_commands = path_parse(heart_path);
    if (heart_commands) {
        PointArray* heart_polygon = path_to_polygon(heart_commands, 0.5f);
        if (heart_polygon) {
            rasterizer_fill_polygon(rast, heart_polygon, 
                                   color_from_hex("#FF1744"), 
                                   FILL_RULE_EVENODD);
            point_array_free(heart_polygon);
        }
        path_command_free_list(heart_commands);
    }
    
    /* Wave using quadratic curves */
    const char* wave_path = 
        "M 50,250 "
        "Q 100,200 150,250 "
        "Q 200,300 250,250 "
        "Q 300,200 350,250 "
        "Q 400,300 450,250 "
        "L 450,280 L 50,280 Z";
    
    PathCommand* wave_commands = path_parse(wave_path);
    if (wave_commands) {
        PointArray* wave_polygon = path_to_polygon(wave_commands, 0.5f);
        if (wave_polygon) {
            rasterizer_fill_polygon(rast, wave_polygon, 
                                   color_from_hex("#00BCD4"), 
                                   FILL_RULE_EVENODD);
            point_array_free(wave_polygon);
        }
        path_command_free_list(wave_commands);
    }
    
    rasterizer_save_ppm(rast, "demo2_complex_paths.ppm");
    rasterizer_free(rast);
    
    printf("✓ Saved to demo2_complex_paths.ppm\n");
}

/**
 * Demo 3: Gradient-like effect
 */
void demo_gradient_effect(void) {
    printf("\nDemo 3: Creating gradient effect...\n");
    
    Rasterizer* rast = rasterizer_create(400, 400, color_rgb(240, 240, 240));
    if (!rast) {
        fprintf(stderr, "Failed to create rasterizer\n");
        return;
    }
    
    /* Create concentric circles with color transition */
    for (int i = 0; i < 20; i++) {
        float radius = 150.0f - (float)i * 7.0f;
        uint8_t r = (uint8_t)(255 - i * 10);
        uint8_t g = (uint8_t)(100 + i * 5);
        uint8_t b = (uint8_t)(150 + i * 5);
        
        rasterizer_draw_circle(rast, point_make(200, 200), radius, 
                              color_rgb(r, g, b), 64);
    }
    
    /* Add decorative rectangles */
    rasterizer_draw_rectangle(rast, 50, 50, 80, 80, color_rgb(255, 200, 0));
    rasterizer_draw_rectangle(rast, 270, 270, 80, 80, color_rgb(0, 200, 255));
    
    rasterizer_save_ppm(rast, "demo3_gradient.ppm");
    rasterizer_free(rast);
    
    printf("✓ Saved to demo3_gradient.ppm\n");
}

/**
 * Demo 4: Composite scene
 */
void demo_composite_scene(void) {
    printf("\nDemo 4: Creating a composite scene...\n");
    
    Rasterizer* rast = rasterizer_create(600, 400, color_rgb(255, 255, 255));
    if (!rast) {
        fprintf(stderr, "Failed to create rasterizer\n");
        return;
    }
    
    /* Sky */
    rasterizer_draw_rectangle(rast, 0, 0, 600, 250, 
                             color_from_hex("#87CEEB"));
    
    /* Sun */
    rasterizer_draw_circle(rast, point_make(500, 80), 40, 
                          color_from_hex("#FFD700"), 64);
    
    /* Ground */
    rasterizer_draw_rectangle(rast, 0, 250, 600, 150, 
                             color_from_hex("#90EE90"));
    
    /* House body */
    rasterizer_draw_rectangle(rast, 150, 180, 120, 100, 
                             color_from_hex("#D2691E"));
    
    /* Roof */
    PointArray* roof = point_array_create();
    point_array_add(roof, point_make(140, 180));
    point_array_add(roof, point_make(210, 130));
    point_array_add(roof, point_make(280, 180));
    rasterizer_fill_polygon(rast, roof, color_from_hex("#8B4513"), 
                           FILL_RULE_EVENODD);
    point_array_free(roof);
    
    /* Door */
    rasterizer_draw_rectangle(rast, 190, 230, 40, 50, 
                             color_from_hex("#654321"));
    
    /* Windows */
    rasterizer_draw_rectangle(rast, 165, 200, 30, 30, 
                             color_from_hex("#ADD8E6"));
    rasterizer_draw_rectangle(rast, 225, 200, 30, 30, 
                             color_from_hex("#ADD8E6"));
    
    /* Tree trunk */
    rasterizer_draw_rectangle(rast, 400, 200, 30, 80, 
                             color_from_hex("#8B4513"));
    
    /* Tree foliage */
    rasterizer_draw_circle(rast, point_make(350, 200), 40, 
                          color_from_hex("#228B22"), 64);
    rasterizer_draw_circle(rast, point_make(415, 180), 45, 
                          color_from_hex("#228B22"), 64);
    rasterizer_draw_circle(rast, point_make(450, 210), 35, 
                          color_from_hex("#228B22"), 64);
    
    /* Clouds */
    rasterizer_draw_ellipse(rast, 100, 60, 40, 25, 
                           color_rgb(255, 255, 255), 64);
    rasterizer_draw_ellipse(rast, 130, 60, 35, 20, 
                           color_rgb(255, 255, 255), 64);
    rasterizer_draw_ellipse(rast, 115, 50, 30, 20, 
                           color_rgb(255, 255, 255), 64);
    
    rasterizer_draw_ellipse(rast, 350, 80, 50, 30, 
                           color_rgb(255, 255, 255), 64);
    rasterizer_draw_ellipse(rast, 390, 80, 40, 25, 
                           color_rgb(255, 255, 255), 64);
    
    rasterizer_save_ppm(rast, "demo4_scene.ppm");
    rasterizer_free(rast);
    
    printf("✓ Saved to demo4_scene.ppm\n");
}

/**
 * Demo 5: Path parsing test
 */
void demo_path_commands(void) {
    printf("\nDemo 5: Testing path parser with various commands...\n");
    
    Rasterizer* rast = rasterizer_create(500, 400, color_rgb(255, 255, 255));
    if (!rast) {
        fprintf(stderr, "Failed to create rasterizer\n");
        return;
    }
    
    /* Test absolute commands */
    const char* path1 = "M 50 50 L 150 50 L 150 150 L 50 150 Z";
    PathCommand* cmds1 = path_parse(path1);
    if (cmds1) {
        PointArray* poly1 = path_to_polygon(cmds1, 0.5f);
        if (poly1) {
            rasterizer_fill_polygon(rast, poly1, color_from_hex("#E91E63"), 
                                   FILL_RULE_EVENODD);
            point_array_free(poly1);
        }
        path_command_free_list(cmds1);
    }
    
    /* Test relative commands */
    const char* path2 = "M 200 50 l 100 0 l 0 100 l -100 0 z";
    PathCommand* cmds2 = path_parse(path2);
    if (cmds2) {
        PointArray* poly2 = path_to_polygon(cmds2, 0.5f);
        if (poly2) {
            rasterizer_fill_polygon(rast, poly2, color_from_hex("#3F51B5"), 
                                   FILL_RULE_EVENODD);
            point_array_free(poly2);
        }
        path_command_free_list(cmds2);
    }
    
    /* Test horizontal and vertical lines */
    const char* path3 = "M 350 50 h 100 v 100 h -100 v -100";
    PathCommand* cmds3 = path_parse(path3);
    if (cmds3) {
        PointArray* poly3 = path_to_polygon(cmds3, 0.5f);
        if (poly3) {
            rasterizer_fill_polygon(rast, poly3, color_from_hex("#009688"), 
                                   FILL_RULE_EVENODD);
            point_array_free(poly3);
        }
        path_command_free_list(cmds3);
    }
    
    /* Test cubic bezier */
    const char* path4 = "M 50 200 C 50 250 150 250 150 300 L 50 300 Z";
    PathCommand* cmds4 = path_parse(path4);
    if (cmds4) {
        PointArray* poly4 = path_to_polygon(cmds4, 0.5f);
        if (poly4) {
            rasterizer_fill_polygon(rast, poly4, color_from_hex("#FF9800"), 
                                   FILL_RULE_EVENODD);
            point_array_free(poly4);
        }
        path_command_free_list(cmds4);
    }
    
    /* Test quadratic bezier */
    const char* path5 = "M 200 200 q 50 50 100 0 l 0 100 l -100 0 z";
    PathCommand* cmds5 = path_parse(path5);
    if (cmds5) {
        PointArray* poly5 = path_to_polygon(cmds5, 0.5f);
        if (poly5) {
            rasterizer_fill_polygon(rast, poly5, color_from_hex("#8BC34A"), 
                                   FILL_RULE_EVENODD);
            point_array_free(poly5);
        }
        path_command_free_list(cmds5);
    }
    
    rasterizer_save_ppm(rast, "demo5_path_commands.ppm");
    rasterizer_free(rast);
    
    printf("✓ Saved to demo5_path_commands.ppm\n");
}

/**
 * Print summary of improvements
 */
void print_summary(void) {
    printf("\n");
    printf("============================================================\n");
    printf("C SVG RENDERER - KEY FEATURES\n");
    printf("============================================================\n");
    printf("\n");
    printf("Clean Code Practices:\n");
    printf("  ✓ Proper header/implementation separation\n");
    printf("  ✓ No global variables\n");
    printf("  ✓ Consistent naming conventions\n");
    printf("  ✓ Comprehensive comments and documentation\n");
    printf("  ✓ Proper error handling\n");
    printf("  ✓ Memory management with cleanup functions\n");
    printf("\n");
    printf("Architecture:\n");
    printf("  ✓ Modular design with clear separation\n");
    printf("  ✓ Opaque pointers for encapsulation\n");
    printf("  ✓ Linked lists for dynamic structures\n");
    printf("  ✓ Dynamic arrays with capacity management\n");
    printf("\n");
    printf("Supported Features:\n");
    printf("  ✓ Path commands: M, L, H, V, C, Q, Z (absolute & relative)\n");
    printf("  ✓ Basic shapes: rect, circle, ellipse\n");
    printf("  ✓ Polygon rendering\n");
    printf("  ✓ Bezier curve subdivision\n");
    printf("  ✓ Scanline polygon fill algorithm\n");
    printf("  ✓ Color parsing (hex, named colors)\n");
    printf("  ✓ PPM output format\n");
    printf("\n");
    printf("============================================================\n");
}

/**
 * Main program
 */
int main(void) {
    printf("C SVG Renderer Demonstration\n");
    printf("============================================================\n");
    
    demo_basic_shapes();
    demo_complex_paths();
    demo_gradient_effect();
    demo_composite_scene();
    demo_path_commands();
    
    print_summary();
    
    printf("\n✨ All demos completed!\n");
    printf("Check the generated .ppm files to see the results.\n");
    
    return 0;
}
