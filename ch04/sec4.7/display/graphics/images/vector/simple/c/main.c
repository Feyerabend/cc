#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "display.h"

static uint16_t fb[DISPLAY_WIDTH * DISPLAY_HEIGHT];

typedef struct { float x, y; } vec2;
typedef struct { float m[3][3]; } mat3;

typedef struct {
    vec2 *v;
    int n;
    uint16_t color;
} shape;

static float rot = 0.0f, scale = 1.0f;
static vec2 trans = {160, 120};
static int cur_shape = 0;
static bool auto_rot = true;

static mat3 identity(void) {
    return (mat3){{{1,0,0},{0,1,0},{0,0,1}}};
}

static mat3 translate(float x, float y) {
    mat3 m = identity(); m.m[0][2] = x; m.m[1][2] = y; return m;
}

static mat3 rotate(float a) {
    mat3 m = identity();
    float c = cosf(a), s = sinf(a);
    m.m[0][0] = c; m.m[0][1] = -s;
    m.m[1][0] = s; m.m[1][1] = c;
    return m;
}

static mat3 scale_mat(float sx, float sy) {
    mat3 m = identity(); m.m[0][0] = sx; m.m[1][1] = sy; return m;
}

static mat3 mul(mat3 a, mat3 b) {
    mat3 r = {0};
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            for (int k = 0; k < 3; k++)
                r.m[i][j] += a.m[i][k] * b.m[k][j];
    return r;
}

static vec2 transform(mat3 m, vec2 p) {
    return (vec2){
        m.m[0][0]*p.x + m.m[0][1]*p.y + m.m[0][2],
        m.m[1][0]*p.x + m.m[1][1]*p.y + m.m[1][2]
    };
}

static void line(int x0, int y0, int x1, int y1, uint16_t c) {
    int dx = abs(x1-x0), sx = x0 < x1 ? 1 : -1;
    int dy = abs(y1-y0), sy = y0 < y1 ? 1 : -1;
    int err = dx - dy;
    while (1) {
        if (x0 >= 0 && x0 < DISPLAY_WIDTH && y0 >= 0 && y0 < DISPLAY_HEIGHT)
            fb[y0 * DISPLAY_WIDTH + x0] = c;
        if (x0 == x1 && y0 == y1) break;
        int e2 = 2 * err;
        if (e2 > -dy) { err -= dy; x0 += sx; }
        if (e2 <  dx) { err += dx; y0 += sy; }
    }
}

static void draw_shape(shape *s, mat3 t) {
    for (int i = 0; i < s->n; i++) {
        vec2 a = transform(t, s->v[i]);
        vec2 b = transform(t, s->v[(i+1)%s->n]);
        line((int)a.x, (int)a.y, (int)b.x, (int)b.y, s->color);
    }
}

static void draw_text(int x, int y, const char *s, uint16_t fg, uint16_t bg) {
    while (*s && x < DISPLAY_WIDTH) {
        const uint8_t *g = display_get_font_char(*s++);
        for (int col = 0; col < 5 && x + col < DISPLAY_WIDTH; col++) {
            uint8_t l = g[4 - col];
            for (int row = 0; row < 8 && y + row < DISPLAY_HEIGHT; row++) {
                uint16_t c = (l & (1 << row)) ? fg : bg;
                fb[(y + row) * DISPLAY_WIDTH + (x + col)] = c;
            }
        }
        x += 6;
    }
}

static void draw_ui(void) {
    char buf[64];
    snprintf(buf, sizeof(buf), "SHAPE: %d/%d", cur_shape + 1, 5);
    draw_text(10, 10, buf, COLOR_WHITE, COLOR_BLACK);
    snprintf(buf, sizeof(buf), "ROT: %.1f", rot * 180 / M_PI);
    draw_text(10, 20, buf, COLOR_WHITE, COLOR_BLACK);
    snprintf(buf, sizeof(buf), "SCALE: %.2f", scale);
    draw_text(10, 30, buf, COLOR_WHITE, COLOR_BLACK);
    snprintf(buf, sizeof(buf), "AUTO: %s", auto_rot ? "ON" : "OFF");
    draw_text(10, 40, buf, COLOR_WHITE, COLOR_BLACK);
    draw_text(10, 220, "A:SHAPE B:AUTO X:+ Y:-", COLOR_YELLOW, COLOR_BLACK);
}

// Shapes
static vec2 tri[] = {{0,-30},{26,15},{-26,15}};
static vec2 sq[]  = {{-25,-25},{25,-25},{25,25},{-25,25}};
static vec2 pen[] = {{0,-30},{28,-9},{17,24},{-17,24},{-28,-9}};
static vec2 hex[] = {{0,-30},{26,-15},{26,15},{0,30},{-26,15},{-26,-15}};
static vec2 star[] = {{0,-30},{7,-10},{28,-10},{11,5},{18,25},{0,15},{-18,25},{-11,5},{-28,-10},{-7,-10}};

static shape shapes[] = {
    {tri, 3, COLOR_CYAN}, {sq, 4, COLOR_YELLOW}, {pen, 5, COLOR_MAGENTA},
    {hex, 6, COLOR_GREEN}, {star, 10, COLOR_RED}
};

// Callbacks
static void on_a(button_t) { cur_shape = (cur_shape + 1) % 5; }
static void on_b(button_t) { auto_rot = !auto_rot; }
static void on_x(button_t) { if (scale < 3.0f) scale += 0.2f; }
static void on_y(button_t) { if (scale > 0.2f) scale -= 0.2f; }

int main() {
    stdio_init_all();
    display_pack_init();
    buttons_init();
    button_set_callback(BUTTON_A, on_a);
    button_set_callback(BUTTON_B, on_b);
    button_set_callback(BUTTON_X, on_x);
    button_set_callback(BUTTON_Y, on_y);

    while (1) {
        buttons_update();

        for (int i = 0; i < DISPLAY_WIDTH * DISPLAY_HEIGHT; i++) fb[i] = COLOR_BLACK;

        if (auto_rot) {
            rot += 0.02f;
            if (rot > 2 * M_PI) rot -= 2 * M_PI;
        }

        mat3 t = mul(translate(trans.x, trans.y),
                     mul(rotate(rot), scale_mat(scale, scale)));

        draw_shape(&shapes[cur_shape], t);

        mat3 axis = translate(trans.x, trans.y);
        vec2 o = transform(axis, (vec2){0,0});
        vec2 x = transform(axis, (vec2){40,0});
        vec2 y = transform(axis, (vec2){0,40});
        line((int)o.x, (int)o.y, (int)x.x, (int)x.y, COLOR_RED);
        line((int)o.x, (int)o.y, (int)y.x, (int)y.y, COLOR_GREEN);

        draw_ui();
        display_blit_full(fb);
        sleep_ms(16);
    }
}