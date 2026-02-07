/**
 * svg_renderer.c
 * 
 * Implementation of SVG parser and renderer
 */

#include "svg_renderer.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ctype.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ============================================================================
 * Utility Functions
 * ============================================================================ */

static inline int min_int(int a, int b) {
    return (a < b) ? a : b;
}

static inline int max_int(int a, int b) {
    return (a > b) ? a : b;
}

/* ============================================================================
 * Color Functions Implementation
 * ============================================================================ */

Color color_rgb(uint8_t r, uint8_t g, uint8_t b) {
    Color c = {r, g, b, 1.0f};
    return c;
}

Color color_rgba(uint8_t r, uint8_t g, uint8_t b, float a) {
    Color c = {r, g, b, a};
    return c;
}

Color color_from_hex(const char* hex) {
    if (!hex) {
        return color_rgb(0, 0, 0);
    }
    
    /* Skip '#' if present */
    if (hex[0] == '#') {
        hex++;
    }
    
    size_t len = strlen(hex);
    uint8_t r = 0, g = 0, b = 0;
    
    if (len == 3) {
        /* Short form: #RGB */
        int r_val = (hex[0] >= 'a' ? hex[0] - 'a' + 10 : hex[0] - '0');
        int g_val = (hex[1] >= 'a' ? hex[1] - 'a' + 10 : hex[1] - '0');
        int b_val = (hex[2] >= 'a' ? hex[2] - 'a' + 10 : hex[2] - '0');
        r = (uint8_t)(r_val * 17);
        g = (uint8_t)(g_val * 17);
        b = (uint8_t)(b_val * 17);
    } else if (len >= 6) {
        /* Long form: #RRGGBB */
        char buf[3] = {0};
        
        buf[0] = hex[0]; buf[1] = hex[1];
        r = (uint8_t)strtol(buf, NULL, 16);
        
        buf[0] = hex[2]; buf[1] = hex[3];
        g = (uint8_t)strtol(buf, NULL, 16);
        
        buf[0] = hex[4]; buf[1] = hex[5];
        b = (uint8_t)strtol(buf, NULL, 16);
    }
    
    return color_rgb(r, g, b);
}

Color color_parse(const char* color_str) {
    if (!color_str) {
        return color_rgb(0, 0, 0);
    }
    
    /* Trim whitespace */
    while (isspace(*color_str)) color_str++;
    
    if (color_str[0] == '#') {
        return color_from_hex(color_str);
    }
    
    /* Named colors */
    if (strcmp(color_str, "black") == 0) return color_rgb(0, 0, 0);
    if (strcmp(color_str, "white") == 0) return color_rgb(255, 255, 255);
    if (strcmp(color_str, "red") == 0) return color_rgb(255, 0, 0);
    if (strcmp(color_str, "green") == 0) return color_rgb(0, 255, 0);
    if (strcmp(color_str, "blue") == 0) return color_rgb(0, 0, 255);
    if (strcmp(color_str, "yellow") == 0) return color_rgb(255, 255, 0);
    if (strcmp(color_str, "cyan") == 0) return color_rgb(0, 255, 255);
    if (strcmp(color_str, "magenta") == 0) return color_rgb(255, 0, 255);
    if (strcmp(color_str, "gray") == 0) return color_rgb(128, 128, 128);
    
    /* Default to black */
    return color_rgb(0, 0, 0);
}

Color color_blend(Color c1, Color c2, float t) {
    uint8_t r = (uint8_t)(c1.r + (c2.r - c1.r) * t);
    uint8_t g = (uint8_t)(c1.g + (c2.g - c1.g) * t);
    uint8_t b = (uint8_t)(c1.b + (c2.b - c1.b) * t);
    float a = c1.a + (c2.a - c1.a) * t;
    return color_rgba(r, g, b, a);
}

/* ============================================================================
 * Point Functions Implementation
 * ============================================================================ */

Point point_make(float x, float y) {
    Point p = {x, y};
    return p;
}

Point point_add(Point p1, Point p2) {
    return point_make(p1.x + p2.x, p1.y + p2.y);
}

Point point_sub(Point p1, Point p2) {
    return point_make(p1.x - p2.x, p1.y - p2.y);
}

Point point_mul(Point p, float scalar) {
    return point_make(p.x * scalar, p.y * scalar);
}

float point_distance(Point p1, Point p2) {
    float dx = p2.x - p1.x;
    float dy = p2.y - p1.y;
    return sqrtf(dx * dx + dy * dy);
}

/* ============================================================================
 * Point Array Implementation
 * ============================================================================ */

PointArray* point_array_create(void) {
    PointArray* arr = (PointArray*)malloc(sizeof(PointArray));
    if (!arr) return NULL;
    
    arr->capacity = 16;
    arr->count = 0;
    arr->points = (Point*)malloc(arr->capacity * sizeof(Point));
    
    if (!arr->points) {
        free(arr);
        return NULL;
    }
    
    return arr;
}

void point_array_add(PointArray* arr, Point p) {
    if (!arr) return;
    
    if (arr->count >= arr->capacity) {
        arr->capacity *= 2;
        Point* new_points = (Point*)realloc(arr->points, 
                                            arr->capacity * sizeof(Point));
        if (!new_points) return;
        arr->points = new_points;
    }
    
    arr->points[arr->count++] = p;
}

void point_array_free(PointArray* arr) {
    if (!arr) return;
    free(arr->points);
    free(arr);
}

/* ============================================================================
 * Path Command Implementation
 * ============================================================================ */

PathCommand* path_command_move(Point point) {
    PathCommand* cmd = (PathCommand*)malloc(sizeof(PathCommand));
    if (!cmd) return NULL;
    
    cmd->type = CMD_MOVE_TO;
    cmd->data.point = point;
    cmd->next = NULL;
    return cmd;
}

PathCommand* path_command_line(Point point) {
    PathCommand* cmd = (PathCommand*)malloc(sizeof(PathCommand));
    if (!cmd) return NULL;
    
    cmd->type = CMD_LINE_TO;
    cmd->data.point = point;
    cmd->next = NULL;
    return cmd;
}

PathCommand* path_command_cubic(Point cp1, Point cp2, Point end) {
    PathCommand* cmd = (PathCommand*)malloc(sizeof(PathCommand));
    if (!cmd) return NULL;
    
    cmd->type = CMD_CUBIC_BEZIER;
    cmd->data.cubic.cp1 = cp1;
    cmd->data.cubic.cp2 = cp2;
    cmd->data.cubic.end = end;
    cmd->next = NULL;
    return cmd;
}

PathCommand* path_command_quadratic(Point cp, Point end) {
    PathCommand* cmd = (PathCommand*)malloc(sizeof(PathCommand));
    if (!cmd) return NULL;
    
    cmd->type = CMD_QUADRATIC_BEZIER;
    cmd->data.quadratic.cp = cp;
    cmd->data.quadratic.end = end;
    cmd->next = NULL;
    return cmd;
}

PathCommand* path_command_close(void) {
    PathCommand* cmd = (PathCommand*)malloc(sizeof(PathCommand));
    if (!cmd) return NULL;
    
    cmd->type = CMD_CLOSE_PATH;
    cmd->next = NULL;
    return cmd;
}

void path_command_free_list(PathCommand* cmd) {
    while (cmd) {
        PathCommand* next = cmd->next;
        free(cmd);
        cmd = next;
    }
}

/* ============================================================================
 * Path Parser Implementation
 * ============================================================================ */

/* Helper to skip whitespace */
static const char* skip_whitespace(const char* str) {
    while (*str && (isspace(*str) || *str == ',')) {
        str++;
    }
    return str;
}

/* Helper to parse float */
static const char* parse_float(const char* str, float* value) {
    char* end;
    *value = strtof(str, &end);
    return end;
}

PathCommand* path_parse(const char* path_data) {
    if (!path_data) return NULL;
    
    PathCommand* first = NULL;
    PathCommand* last = NULL;
    Point current = point_make(0, 0);
    Point start = point_make(0, 0);
    
    const char* p = path_data;
    
    while (*p) {
        p = skip_whitespace(p);
        if (!*p) break;
        
        char cmd = *p;
        if (!isalpha(cmd)) {
            p++;
            continue;
        }
        p++;
        
        bool relative = islower(cmd);
        cmd = (char)toupper((unsigned char)cmd);
        
        switch (cmd) {
            case 'M': /* Move to */ {
                float x, y;
                p = skip_whitespace(p);
                p = parse_float(p, &x);
                p = skip_whitespace(p);
                p = parse_float(p, &y);
                
                Point point = relative ? point_add(current, point_make(x, y)) 
                                      : point_make(x, y);
                
                PathCommand* new_cmd = path_command_move(point);
                if (!new_cmd) break;
                
                if (!first) {
                    first = last = new_cmd;
                } else {
                    last->next = new_cmd;
                    last = new_cmd;
                }
                
                current = point;
                start = point;
                break;
            }
            
            case 'L': /* Line to */ {
                float x, y;
                p = skip_whitespace(p);
                p = parse_float(p, &x);
                p = skip_whitespace(p);
                p = parse_float(p, &y);
                
                Point point = relative ? point_add(current, point_make(x, y)) 
                                      : point_make(x, y);
                
                PathCommand* new_cmd = path_command_line(point);
                if (!new_cmd) break;
                
                if (!first) {
                    first = last = new_cmd;
                } else {
                    last->next = new_cmd;
                    last = new_cmd;
                }
                
                current = point;
                break;
            }
            
            case 'H': /* Horizontal line */ {
                float x;
                p = skip_whitespace(p);
                p = parse_float(p, &x);
                
                x = relative ? current.x + x : x;
                Point point = point_make(x, current.y);
                
                PathCommand* new_cmd = path_command_line(point);
                if (!new_cmd) break;
                
                if (!first) {
                    first = last = new_cmd;
                } else {
                    last->next = new_cmd;
                    last = new_cmd;
                }
                
                current = point;
                break;
            }
            
            case 'V': /* Vertical line */ {
                float y;
                p = skip_whitespace(p);
                p = parse_float(p, &y);
                
                y = relative ? current.y + y : y;
                Point point = point_make(current.x, y);
                
                PathCommand* new_cmd = path_command_line(point);
                if (!new_cmd) break;
                
                if (!first) {
                    first = last = new_cmd;
                } else {
                    last->next = new_cmd;
                    last = new_cmd;
                }
                
                current = point;
                break;
            }
            
            case 'C': /* Cubic Bezier */ {
                float x1, y1, x2, y2, x, y;
                p = skip_whitespace(p);
                p = parse_float(p, &x1);
                p = skip_whitespace(p);
                p = parse_float(p, &y1);
                p = skip_whitespace(p);
                p = parse_float(p, &x2);
                p = skip_whitespace(p);
                p = parse_float(p, &y2);
                p = skip_whitespace(p);
                p = parse_float(p, &x);
                p = skip_whitespace(p);
                p = parse_float(p, &y);
                
                Point cp1 = relative ? point_add(current, point_make(x1, y1)) 
                                    : point_make(x1, y1);
                Point cp2 = relative ? point_add(current, point_make(x2, y2)) 
                                    : point_make(x2, y2);
                Point end = relative ? point_add(current, point_make(x, y)) 
                                    : point_make(x, y);
                
                PathCommand* new_cmd = path_command_cubic(cp1, cp2, end);
                if (!new_cmd) break;
                
                if (!first) {
                    first = last = new_cmd;
                } else {
                    last->next = new_cmd;
                    last = new_cmd;
                }
                
                current = end;
                break;
            }
            
            case 'Q': /* Quadratic Bezier */ {
                float x1, y1, x, y;
                p = skip_whitespace(p);
                p = parse_float(p, &x1);
                p = skip_whitespace(p);
                p = parse_float(p, &y1);
                p = skip_whitespace(p);
                p = parse_float(p, &x);
                p = skip_whitespace(p);
                p = parse_float(p, &y);
                
                Point cp = relative ? point_add(current, point_make(x1, y1)) 
                                   : point_make(x1, y1);
                Point end = relative ? point_add(current, point_make(x, y)) 
                                    : point_make(x, y);
                
                PathCommand* new_cmd = path_command_quadratic(cp, end);
                if (!new_cmd) break;
                
                if (!first) {
                    first = last = new_cmd;
                } else {
                    last->next = new_cmd;
                    last = new_cmd;
                }
                
                current = end;
                break;
            }
            
            case 'Z': /* Close path */ {
                PathCommand* new_cmd = path_command_close();
                if (!new_cmd) break;
                
                if (!first) {
                    first = last = new_cmd;
                } else {
                    last->next = new_cmd;
                    last = new_cmd;
                }
                
                current = start;
                break;
            }
            
            default:
                break;
        }
    }
    
    return first;
}

/* ============================================================================
 * Bezier Subdivision
 * ============================================================================ */

static void subdivide_cubic_bezier(Point p0, Point p1, Point p2, Point p3, 
                                   float tolerance, PointArray* result) {
    /* De Casteljau's algorithm */
    Point mid1 = point_mul(point_add(p0, p1), 0.5f);
    Point mid2 = point_mul(point_add(p1, p2), 0.5f);
    Point mid3 = point_mul(point_add(p2, p3), 0.5f);
    Point mid4 = point_mul(point_add(mid1, mid2), 0.5f);
    Point mid5 = point_mul(point_add(mid2, mid3), 0.5f);
    Point midpoint = point_mul(point_add(mid4, mid5), 0.5f);
    
    /* Check flatness */
    float chord_length = point_distance(p0, p3);
    if (chord_length < tolerance) {
        point_array_add(result, p3);
        return;
    }
    
    Point chord_mid = point_mul(point_add(p0, p3), 0.5f);
    float deviation = point_distance(mid4, chord_mid);
    
    if (deviation < tolerance) {
        point_array_add(result, p3);
    } else {
        /* Subdivide recursively */
        subdivide_cubic_bezier(p0, mid1, mid4, midpoint, tolerance, result);
        subdivide_cubic_bezier(midpoint, mid5, mid3, p3, tolerance, result);
    }
}

PointArray* path_to_polygon(PathCommand* commands, float tolerance) {
    PointArray* polygon = point_array_create();
    if (!polygon) return NULL;
    
    Point current = point_make(0, 0);
    
    for (PathCommand* cmd = commands; cmd; cmd = cmd->next) {
        switch (cmd->type) {
            case CMD_MOVE_TO:
                current = cmd->data.point;
                point_array_add(polygon, current);
                break;
                
            case CMD_LINE_TO:
                current = cmd->data.point;
                point_array_add(polygon, current);
                break;
                
            case CMD_CUBIC_BEZIER: {
                Point cp1 = cmd->data.cubic.cp1;
                Point cp2 = cmd->data.cubic.cp2;
                Point end = cmd->data.cubic.end;
                subdivide_cubic_bezier(current, cp1, cp2, end, tolerance, polygon);
                current = end;
                break;
            }
            
            case CMD_QUADRATIC_BEZIER: {
                /* Convert quadratic to cubic */
                Point cp = cmd->data.quadratic.cp;
                Point end = cmd->data.quadratic.end;
                
                Point cp1 = point_add(current, 
                                     point_mul(point_sub(cp, current), 2.0f/3.0f));
                Point cp2 = point_add(end, 
                                     point_mul(point_sub(cp, end), 2.0f/3.0f));
                
                subdivide_cubic_bezier(current, cp1, cp2, end, tolerance, polygon);
                current = end;
                break;
            }
            
            case CMD_CLOSE_PATH:
                /* Polygon automatically closes */
                break;
                
            default:
                break;
        }
    }
    
    return polygon;
}

/* ============================================================================
 * Rasterizer Implementation
 * ============================================================================ */

Rasterizer* rasterizer_create(int width, int height, Color background) {
    Rasterizer* rast = (Rasterizer*)malloc(sizeof(Rasterizer));
    if (!rast) return NULL;
    
    rast->width = width;
    rast->height = height;
    rast->background = background;
    
    size_t pixel_count = (size_t)width * (size_t)height;
    rast->pixels = (Color*)malloc(pixel_count * sizeof(Color));
    
    if (!rast->pixels) {
        free(rast);
        return NULL;
    }
    
    /* Initialize with background color */
    for (size_t i = 0; i < pixel_count; i++) {
        rast->pixels[i] = background;
    }
    
    return rast;
}

void rasterizer_free(Rasterizer* rast) {
    if (!rast) return;
    free(rast->pixels);
    free(rast);
}

/* Edge for scanline algorithm */
typedef struct {
    float y_min;
    float y_max;
    float x_at_y_min;
    float slope;
} Edge;

static int compare_edges(const void* a, const void* b) {
    const Edge* e1 = (const Edge*)a;
    const Edge* e2 = (const Edge*)b;
    return (e1->y_min < e2->y_min) ? -1 : 1;
}

static int compare_floats(const void* a, const void* b) {
    float f1 = *(const float*)a;
    float f2 = *(const float*)b;
    return (f1 < f2) ? -1 : (f1 > f2) ? 1 : 0;
}

void rasterizer_fill_polygon(Rasterizer* rast, PointArray* points, 
                             Color color, FillRule fill_rule) {
    if (!rast || !points || points->count < 3) return;
    
    /* Build edge table */
    size_t max_edges = points->count;
    Edge* edges = (Edge*)malloc(max_edges * sizeof(Edge));
    if (!edges) return;
    
    size_t edge_count = 0;
    
    for (size_t i = 0; i < points->count; i++) {
        Point p1 = points->points[i];
        Point p2 = points->points[(i + 1) % points->count];
        
        if (fabsf(p1.y - p2.y) < 0.01f) continue; /* Skip horizontal edges */
        
        Edge edge;
        if (p1.y < p2.y) {
            edge.y_min = p1.y;
            edge.y_max = p2.y;
            edge.x_at_y_min = p1.x;
        } else {
            edge.y_min = p2.y;
            edge.y_max = p1.y;
            edge.x_at_y_min = p2.x;
        }
        edge.slope = (p2.x - p1.x) / (p2.y - p1.y);
        
        edges[edge_count++] = edge;
    }
    
    if (edge_count == 0) {
        free(edges);
        return;
    }
    
    /* Sort edges by y_min */
    qsort(edges, edge_count, sizeof(Edge), compare_edges);
    
    /* Find y bounds */
    int min_y = max_int(0, (int)edges[0].y_min);
    int max_y = min_int(rast->height - 1, (int)edges[edge_count - 1].y_max);
    
    /* Scanline fill */
    float* intersections = (float*)malloc(edge_count * sizeof(float));
    if (!intersections) {
        free(edges);
        return;
    }
    
    for (int y = min_y; y <= max_y; y++) {
        size_t intersection_count = 0;
        
        /* Find active edges and calculate intersections */
        for (size_t i = 0; i < edge_count; i++) {
            if (edges[i].y_min <= y && y < edges[i].y_max) {
                float x = edges[i].x_at_y_min + ((float)y - edges[i].y_min) * edges[i].slope;
                intersections[intersection_count++] = x;
            }
        }
        
        if (intersection_count < 2) continue;
        
        /* Sort intersections */
        qsort(intersections, intersection_count, sizeof(float), compare_floats);
        
        /* Fill using even-odd rule */
        if (fill_rule == FILL_RULE_EVENODD) {
            for (size_t i = 0; i + 1 < intersection_count; i += 2) {
                int x_start = max_int(0, (int)intersections[i]);
                int x_end = min_int(rast->width - 1, (int)intersections[i + 1]);
                
                for (int x = x_start; x <= x_end; x++) {
                    rast->pixels[y * rast->width + x] = color;
                }
            }
        }
    }
    
    free(intersections);
    free(edges);
}

void rasterizer_draw_circle(Rasterizer* rast, Point center, float radius, 
                            Color color, int segments) {
    if (!rast || segments < 3) return;
    
    PointArray* points = point_array_create();
    if (!points) return;
    
    for (int i = 0; i < segments; i++) {
        float angle = (float)(2.0 * M_PI * i) / (float)segments;
        float x = center.x + radius * cosf(angle);
        float y = center.y + radius * sinf(angle);
        point_array_add(points, point_make(x, y));
    }
    
    rasterizer_fill_polygon(rast, points, color, FILL_RULE_EVENODD);
    point_array_free(points);
}

void rasterizer_draw_rectangle(Rasterizer* rast, float x, float y, 
                               float width, float height, Color color) {
    if (!rast) return;
    
    PointArray* points = point_array_create();
    if (!points) return;
    
    point_array_add(points, point_make(x, y));
    point_array_add(points, point_make(x + width, y));
    point_array_add(points, point_make(x + width, y + height));
    point_array_add(points, point_make(x, y + height));
    
    rasterizer_fill_polygon(rast, points, color, FILL_RULE_EVENODD);
    point_array_free(points);
}

void rasterizer_draw_ellipse(Rasterizer* rast, float cx, float cy, 
                             float rx, float ry, Color color, int segments) {
    if (!rast || segments < 3) return;
    
    PointArray* points = point_array_create();
    if (!points) return;
    
    for (int i = 0; i < segments; i++) {
        float angle = (float)(2.0 * M_PI * i) / (float)segments;
        float x = cx + rx * cosf(angle);
        float y = cy + ry * sinf(angle);
        point_array_add(points, point_make(x, y));
    }
    
    rasterizer_fill_polygon(rast, points, color, FILL_RULE_EVENODD);
    point_array_free(points);
}

bool rasterizer_save_ppm(Rasterizer* rast, const char* filename) {
    if (!rast || !filename) return false;
    
    FILE* f = fopen(filename, "w");
    if (!f) return false;
    
    fprintf(f, "P3\n%d %d\n255\n", rast->width, rast->height);
    
    for (int y = 0; y < rast->height; y++) {
        for (int x = 0; x < rast->width; x++) {
            Color c = rast->pixels[y * rast->width + x];
            fprintf(f, "%d %d %d ", c.r, c.g, c.b);
        }
        fprintf(f, "\n");
    }
    
    fclose(f);
    return true;
}

/* ============================================================================
 * SVG Parser Implementation (Simplified)
 * ============================================================================ */

SVGElement* svg_parse_string(const char* svg_data) {
    /* This is a simplified parser for demonstration */
    /* A full implementation would use a proper XML parser */
    if (!svg_data) return NULL;
    
    /* For now, return NULL - would need XML parsing library */
    /* In production, use libxml2 or similar */
    return NULL;
}

SVGElement* svg_parse_file(const char* filename) {
    if (!filename) return NULL;
    
    FILE* f = fopen(filename, "r");
    if (!f) return NULL;
    
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    if (size < 0) {
        fclose(f);
        return NULL;
    }
    
    char* content = (char*)malloc((size_t)size + 1);
    if (!content) {
        fclose(f);
        return NULL;
    }
    
    size_t bytes_read = fread(content, 1, (size_t)size, f);
    content[bytes_read] = '\0';
    fclose(f);
    
    SVGElement* elements = svg_parse_string(content);
    free(content);
    
    return elements;
}

void svg_element_free_list(SVGElement* elem) {
    while (elem) {
        SVGElement* next = elem->next;
        
        if (elem->type == ELEM_PATH && elem->data.path.path_data) {
            free(elem->data.path.path_data);
        } else if (elem->type == ELEM_POLYGON) {
            point_array_free(&elem->data.polygon.points);
        }
        
        free(elem);
        elem = next;
    }
}

void svg_render(Rasterizer* rast, SVGElement* elements) {
    if (!rast || !elements) return;
    
    for (SVGElement* elem = elements; elem; elem = elem->next) {
        if (!elem->has_fill) continue;
        
        switch (elem->type) {
            case ELEM_PATH: {
                PathCommand* commands = path_parse(elem->data.path.path_data);
                if (commands) {
                    PointArray* polygon = path_to_polygon(commands, 0.5f);
                    if (polygon) {
                        rasterizer_fill_polygon(rast, polygon, elem->fill, 
                                              FILL_RULE_EVENODD);
                        point_array_free(polygon);
                    }
                    path_command_free_list(commands);
                }
                break;
            }
            
            case ELEM_RECT:
                rasterizer_draw_rectangle(rast, elem->data.rect.x, elem->data.rect.y,
                                        elem->data.rect.width, elem->data.rect.height,
                                        elem->fill);
                break;
                
            case ELEM_CIRCLE:
                rasterizer_draw_circle(rast, point_make(elem->data.circle.cx, 
                                                       elem->data.circle.cy),
                                     elem->data.circle.r, elem->fill, 64);
                break;
                
            case ELEM_ELLIPSE:
                rasterizer_draw_ellipse(rast, elem->data.ellipse.cx, 
                                      elem->data.ellipse.cy,
                                      elem->data.ellipse.rx, elem->data.ellipse.ry,
                                      elem->fill, 64);
                break;
                
            case ELEM_POLYGON:
                rasterizer_fill_polygon(rast, &elem->data.polygon.points, 
                                      elem->fill, FILL_RULE_EVENODD);
                break;
                
            default:
                break;
        }
    }
}

bool svg_render_file(const char* svg_file, const char* output_file, 
                     int width, int height) {
    SVGElement* elements = svg_parse_file(svg_file);
    if (!elements) return false;
    
    Rasterizer* rast = rasterizer_create(width, height, color_rgb(255, 255, 255));
    if (!rast) {
        svg_element_free_list(elements);
        return false;
    }
    
    svg_render(rast, elements);
    bool success = rasterizer_save_ppm(rast, output_file);
    
    rasterizer_free(rast);
    svg_element_free_list(elements);
    
    return success;
}
