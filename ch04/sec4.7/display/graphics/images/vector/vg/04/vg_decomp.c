/*
 * VGF (Vector Graphics Format) Decompressor and Renderer in C
 * For RPi Pico with Pimoroni Display Pack 2.0
 */

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// VGF file header
typedef struct {
    uint16_t width;
    uint16_t height;
    uint8_t num_colors;
    uint16_t *colors;  // RGB565 format
    uint16_t num_shapes;
} VGFHeader;

// Shape data
typedef struct {
    uint8_t type;
    uint8_t fill_idx;
    uint8_t stroke_idx;
    uint8_t stroke_width;
    uint16_t num_points;
    int16_t *points;  // x, y pairs
} VGFShape;

// Read VGF header
int vgf_read_header(FILE *f, VGFHeader *header) {
    uint8_t magic[4];
    
    // Check magic number
    if (fread(magic, 1, 4, f) != 4 || memcmp(magic, "VGF1", 4) != 0) {
        return -1;
    }
    
    // Read dimensions
    fread(&header->width, 2, 1, f);
    fread(&header->height, 2, 1, f);
    
    // Read color palette
    fread(&header->num_colors, 1, 1, f);
    header->colors = malloc(header->num_colors * sizeof(uint16_t));
    
    for (int i = 0; i < header->num_colors; i++) {
        uint8_t r, g, b;
        fread(&r, 1, 1, f);
        fread(&g, 1, 1, f);
        fread(&b, 1, 1, f);
        
        // Convert to RGB565
        header->colors[i] = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
    }
    
    // Read number of shapes
    fread(&header->num_shapes, 2, 1, f);
    
    return 0;
}

// Read next shape from file
int vgf_read_shape(FILE *f, VGFShape *shape) {
    fread(&shape->type, 1, 1, f);
    fread(&shape->fill_idx, 1, 1, f);
    fread(&shape->stroke_idx, 1, 1, f);
    fread(&shape->stroke_width, 1, 1, f);
    fread(&shape->num_points, 2, 1, f);
    
    if (shape->num_points == 0) {
        shape->points = NULL;
        return 0;
    }
    
    // Allocate points array
    shape->points = malloc(shape->num_points * 2 * sizeof(int16_t));
    
    // Read first point (absolute)
    uint16_t x, y;
    fread(&x, 2, 1, f);
    fread(&y, 2, 1, f);
    shape->points[0] = x;
    shape->points[1] = y;
    
    // Read remaining points (delta encoded)
    for (int i = 1; i < shape->num_points; i++) {
        int8_t dx;
        int16_t dy;
        
        fread(&dx, 1, 1, f);
        
        if (dx == -128) {  // Escape sequence
            int16_t full_dx, full_dy;
            fread(&full_dx, 2, 1, f);
            fread(&full_dy, 2, 1, f);
            x += full_dx;
            y += full_dy;
        } else {
            int8_t dy_byte;
            fread(&dy_byte, 1, 1, f);
            x += dx;
            y += dy_byte;
        }
        
        shape->points[i * 2] = x;
        shape->points[i * 2 + 1] = y;
    }
    
    return 0;
}

// Free shape memory
void vgf_free_shape(VGFShape *shape) {
    if (shape->points) {
        free(shape->points);
        shape->points = NULL;
    }
}

// Simple line drawing (Bresenham's algorithm)
void draw_line(uint16_t *framebuffer, int width, int height,
               int x0, int y0, int x1, int y1, uint16_t color) {
    int dx = abs(x1 - x0);
    int dy = abs(y1 - y0);
    int sx = (x0 < x1) ? 1 : -1;
    int sy = (y0 < y1) ? 1 : -1;
    int err = dx - dy;
    
    while (1) {
        if (x0 >= 0 && x0 < width && y0 >= 0 && y0 < height) {
            framebuffer[y0 * width + x0] = color;
        }
        
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

// Render shape to framebuffer
void vgf_render_shape(uint16_t *framebuffer, int width, int height,
                      VGFShape *shape, VGFHeader *header) {
    if (shape->num_points < 2) return;
    
    // Draw stroke
    if (shape->stroke_idx != 255) {
        uint16_t color = header->colors[shape->stroke_idx];
        
        for (int i = 0; i < shape->num_points - 1; i++) {
            int x1 = shape->points[i * 2];
            int y1 = shape->points[i * 2 + 1];
            int x2 = shape->points[(i + 1) * 2];
            int y2 = shape->points[(i + 1) * 2 + 1];
            
            draw_line(framebuffer, width, height, x1, y1, x2, y2, color);
        }
    }
    
    // TODO: Add fill rendering (scanline algorithm)
}

// Example main function
int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Usage: %s <input.vgf>\n", argv[0]);
        return 1;
    }
    
    FILE *f = fopen(argv[1], "rb");
    if (!f) {
        printf("Error opening file\n");
        return 1;
    }
    
    VGFHeader header;
    if (vgf_read_header(f, &header) != 0) {
        printf("Invalid VGF file\n");
        fclose(f);
        return 1;
    }
    
    printf("VGF: %dx%d, %d colors, %d shapes\n",
           header.width, header.height, header.num_colors, header.num_shapes);
    
    // Allocate framebuffer (RGB565)
    uint16_t *framebuffer = calloc(header.width * header.height, sizeof(uint16_t));
    
    // Render all shapes
    for (int i = 0; i < header.num_shapes; i++) {
        VGFShape shape;
        vgf_read_shape(f, &shape);
        vgf_render_shape(framebuffer, header.width, header.height, &shape, &header);
        vgf_free_shape(&shape);
    }
    
    // TODO: Send framebuffer to display
    // change to modified custom driver
    
    // Cleanup
    free(framebuffer);
    free(header.colors);
    fclose(f);
    
    return 0;
}
