/**
 * svg_renderer.h
 * 
 * Advanced SVG Parser and Renderer in C
 * Clean, modular implementation with proper memory management
 */

#ifndef SVG_RENDERER_H
#define SVG_RENDERER_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* ============================================================================
 * Core Data Structures
 * ============================================================================ */

/**
 * RGB Color with alpha channel
 */
typedef struct {
    uint8_t r;
    uint8_t g;
    uint8_t b;
    float a;
} Color;

/**
 * 2D Point
 */
typedef struct {
    float x;
    float y;
} Point;

/**
 * Fill rule enumeration
 */
typedef enum {
    FILL_RULE_EVENODD,
    FILL_RULE_NONZERO
} FillRule;

/**
 * Path command types
 */
typedef enum {
    CMD_MOVE_TO,
    CMD_LINE_TO,
    CMD_CUBIC_BEZIER,
    CMD_QUADRATIC_BEZIER,
    CMD_ARC,
    CMD_CLOSE_PATH
} CommandType;

/**
 * Generic path command structure
 */
typedef struct PathCommand {
    CommandType type;
    union {
        Point point;                           /* MoveTo, LineTo */
        struct {                               /* CubicBezier */
            Point cp1;
            Point cp2;
            Point end;
        } cubic;
        struct {                               /* QuadraticBezier */
            Point cp;
            Point end;
        } quadratic;
        struct {                               /* Arc */
            float rx;
            float ry;
            float rotation;
            bool large_arc;
            bool sweep;
            Point end;
        } arc;
    } data;
    struct PathCommand* next;                  /* Linked list */
} PathCommand;

/**
 * Dynamic array of points (polygon)
 */
typedef struct {
    Point* points;
    size_t count;
    size_t capacity;
} PointArray;

/**
 * Rasterizer canvas
 */
typedef struct {
    int width;
    int height;
    Color* pixels;                             /* width * height array */
    Color background;
} Rasterizer;

/**
 * SVG Element types
 */
typedef enum {
    ELEM_PATH,
    ELEM_RECT,
    ELEM_CIRCLE,
    ELEM_ELLIPSE,
    ELEM_POLYGON
} ElementType;

/**
 * Generic SVG element
 */
typedef struct SVGElement {
    ElementType type;
    Color fill;
    bool has_fill;
    union {
        struct {
            char* path_data;
        } path;
        struct {
            float x;
            float y;
            float width;
            float height;
            float rx;
            float ry;
        } rect;
        struct {
            float cx;
            float cy;
            float r;
        } circle;
        struct {
            float cx;
            float cy;
            float rx;
            float ry;
        } ellipse;
        struct {
            PointArray points;
        } polygon;
    } data;
    struct SVGElement* next;                   /* Linked list */
} SVGElement;

/* ============================================================================
 * Color Functions
 * ============================================================================ */

/**
 * Create color from RGB values
 */
Color color_rgb(uint8_t r, uint8_t g, uint8_t b);

/**
 * Create color from RGBA values
 */
Color color_rgba(uint8_t r, uint8_t g, uint8_t b, float a);

/**
 * Parse hex color (#RGB or #RRGGBB)
 */
Color color_from_hex(const char* hex);

/**
 * Parse any color format
 */
Color color_parse(const char* color_str);

/**
 * Blend two colors
 */
Color color_blend(Color c1, Color c2, float t);

/* ============================================================================
 * Point Functions
 * ============================================================================ */

/**
 * Create point
 */
Point point_make(float x, float y);

/**
 * Add two points
 */
Point point_add(Point p1, Point p2);

/**
 * Subtract two points
 */
Point point_sub(Point p1, Point p2);

/**
 * Multiply point by scalar
 */
Point point_mul(Point p, float scalar);

/**
 * Calculate distance between points
 */
float point_distance(Point p1, Point p2);

/* ============================================================================
 * Point Array Functions
 * ============================================================================ */

/**
 * Create point array
 */
PointArray* point_array_create(void);

/**
 * Add point to array
 */
void point_array_add(PointArray* arr, Point p);

/**
 * Free point array
 */
void point_array_free(PointArray* arr);

/* ============================================================================
 * Path Command Functions
 * ============================================================================ */

/**
 * Create move command
 */
PathCommand* path_command_move(Point point);

/**
 * Create line command
 */
PathCommand* path_command_line(Point point);

/**
 * Create cubic bezier command
 */
PathCommand* path_command_cubic(Point cp1, Point cp2, Point end);

/**
 * Create quadratic bezier command
 */
PathCommand* path_command_quadratic(Point cp, Point end);

/**
 * Create close path command
 */
PathCommand* path_command_close(void);

/**
 * Free command list
 */
void path_command_free_list(PathCommand* cmd);

/* ============================================================================
 * Path Parser
 * ============================================================================ */

/**
 * Parse SVG path data into command list
 */
PathCommand* path_parse(const char* path_data);

/**
 * Convert path commands to polygon
 */
PointArray* path_to_polygon(PathCommand* commands, float tolerance);

/* ============================================================================
 * Rasterizer Functions
 * ============================================================================ */

/**
 * Create rasterizer
 */
Rasterizer* rasterizer_create(int width, int height, Color background);

/**
 * Free rasterizer
 */
void rasterizer_free(Rasterizer* rast);

/**
 * Fill polygon
 */
void rasterizer_fill_polygon(Rasterizer* rast, PointArray* points, 
                             Color color, FillRule fill_rule);

/**
 * Draw circle
 */
void rasterizer_draw_circle(Rasterizer* rast, Point center, float radius, 
                            Color color, int segments);

/**
 * Draw rectangle
 */
void rasterizer_draw_rectangle(Rasterizer* rast, float x, float y, 
                               float width, float height, Color color);

/**
 * Draw ellipse
 */
void rasterizer_draw_ellipse(Rasterizer* rast, float cx, float cy, 
                             float rx, float ry, Color color, int segments);

/**
 * Save as PPM file
 */
bool rasterizer_save_ppm(Rasterizer* rast, const char* filename);

/* ============================================================================
 * SVG Parser Functions
 * ============================================================================ */

/**
 * Parse SVG file
 */
SVGElement* svg_parse_file(const char* filename);

/**
 * Parse SVG string
 */
SVGElement* svg_parse_string(const char* svg_data);

/**
 * Free element list
 */
void svg_element_free_list(SVGElement* elem);

/* ============================================================================
 * SVG Renderer Functions
 * ============================================================================ */

/**
 * Render SVG elements to rasterizer
 */
void svg_render(Rasterizer* rast, SVGElement* elements);

/**
 * High-level render SVG file to output
 */
bool svg_render_file(const char* svg_file, const char* output_file, 
                     int width, int height);

#endif /* SVG_RENDERER_H */
