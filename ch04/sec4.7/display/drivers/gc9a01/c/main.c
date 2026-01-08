#include <math.h>
#include "pico/stdlib.h"
#include "gc9a01.h"


/*  Simple 3D types  */

typedef struct {
    float x, y, z;
} vec3;

/* Cube geometry */
static vec3 cube[8] = {
    {-1,-1,-1}, { 1,-1,-1},
    { 1, 1,-1}, {-1, 1,-1},
    {-1,-1, 1}, { 1,-1, 1},
    { 1, 1, 1}, {-1, 1, 1}
};

static int edges[12][2] = {
    {0,1},{1,2},{2,3},{3,0},
    {4,5},{5,6},{6,7},{7,4},
    {0,4},{1,5},{2,6},{3,7}
};


/*  Math helpers  */

static vec3 rot_x(vec3 v, float a) {
    return (vec3){
        v.x,
        v.y * cosf(a) - v.z * sinf(a),
        v.y * sinf(a) + v.z * cosf(a)
    };
}

static vec3 rot_y(vec3 v, float a) {
    return (vec3){
        v.x * cosf(a) + v.z * sinf(a),
       -v.x * sinf(a) + v.z * cosf(a),
        v.y
    };
}

static vec3 rot_z(vec3 v, float a) {
    return (vec3){
        v.x * cosf(a) - v.y * sinf(a),
        v.x * sinf(a) + v.y * cosf(a),
        v.z
    };
}

/* Perspective projection to screen */
static void project(vec3 v, int *x, int *y) {
    float d = 120.0f;
    float z = v.z + d;
    *x = (int)(120 + (v.x * 60) / z);
    *y = (int)(120 + (v.y * 60) / z);
}


/*  Main  */

int main() {
    stdio_init_all();
    sleep_ms(100);

    gc9a01_init();
    gc9a01_circle_clip(true);

    float ax = 0.0f;
    float ay = 0.0f;
    float az = 0.0f;

    while (true) {
        gc9a01_clear(0x0000);   /* black */

        vec3 t[8];
        int px[8], py[8];

        for (int i = 0; i < 8; i++) {
            vec3 v = cube[i];
            v = rot_x(v, ax);
            v = rot_y(v, ay);
            v = rot_z(v, az);
            t[i] = v;
            project(v, &px[i], &py[i]);
        }

        for (int i = 0; i < 12; i++) {
            int a = edges[i][0];
            int b = edges[i][1];
            gc9a01_line(px[a], py[a], px[b], py[b], 0xFFFF);
        }

        ax += 0.02f;
        ay += 0.015f;
        az += 0.01f;

        sleep_ms(16);
    }
}

