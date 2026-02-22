#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "pico/stdlib.h"
#include "pico/time.h"
#include "display.h"

#define CENTER_X 160.0f
#define CENTER_Y 120.0f
#define CUBE_SIZE 60.0f

// Single framebuffer – rendered into each frame, then blasted to the display
// with display_blit_full() for tear-free output.
static uint16_t framebuffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];

// Cube geometry
static float vertices[8][3] = {
    {-1, -1, -1}, { 1, -1, -1}, { 1,  1, -1}, {-1,  1, -1},  // back face
    {-1, -1,  1}, { 1, -1,  1}, { 1,  1,  1}, {-1,  1,  1}   // front face
};

static const int edges[12][2] = {
    {0,1},{1,2},{2,3},{3,0},
    {4,5},{5,6},{6,7},{7,4},
    {0,4},{1,5},{2,6},{3,7}
};

// Rotation state
static float angle_x = 0.3f, angle_y = 0.5f, angle_z = 0.0f;
static float speed_x = 0.01f, speed_y = 0.015f, speed_z = 0.008f;
static bool  auto_rotate = true;
static float zoom = 1.5f;

// Projected 2D vertices
static float projected[8][2];

// Fade effect driven by B button
static float fade_level = 1.0f;
static bool  fading_in  = false;
static bool  fading_out = false;

// ---------------------------------------------------------------------------
// 3D helpers
// ---------------------------------------------------------------------------
static void rotate_x(float v[3], float a) {
    float y=v[1],z=v[2]; v[1]=y*cosf(a)-z*sinf(a); v[2]=y*sinf(a)+z*cosf(a);
}
static void rotate_y(float v[3], float a) {
    float x=v[0],z=v[2]; v[0]=x*cosf(a)+z*sinf(a); v[2]=-x*sinf(a)+z*cosf(a);
}
static void rotate_z(float v[3], float a) {
    float x=v[0],y=v[1]; v[0]=x*cosf(a)-y*sinf(a); v[1]=x*sinf(a)+y*cosf(a);
}
static void project(float v[3], float *sx, float *sy) {
    float p=4.0f/(4.0f+v[2]);
    *sx=CENTER_X+v[0]*CUBE_SIZE*zoom*p;
    *sy=CENTER_Y+v[1]*CUBE_SIZE*zoom*p;
}
static float edge_depth(int ei) {
    float r1[3]={vertices[edges[ei][0]][0],vertices[edges[ei][0]][1],vertices[edges[ei][0]][2]};
    float r2[3]={vertices[edges[ei][1]][0],vertices[edges[ei][1]][1],vertices[edges[ei][1]][2]};
    rotate_x(r1,angle_x); rotate_y(r1,angle_y); rotate_z(r1,angle_z);
    rotate_x(r2,angle_x); rotate_y(r2,angle_y); rotate_z(r2,angle_z);
    return (r1[2]+r2[2])*0.5f;
}

// ---------------------------------------------------------------------------
// Cube renderer — uses display.h framebuffer helpers exclusively
// ---------------------------------------------------------------------------
static void render_cube(void) {
    for (int i=0;i<8;i++) {
        float r[3]={vertices[i][0],vertices[i][1],vertices[i][2]};
        rotate_x(r,angle_x); rotate_y(r,angle_y); rotate_z(r,angle_z);
        project(r,&projected[i][0],&projected[i][1]);
    }

    int sorted[12]; float depths[12];
    for (int i=0;i<12;i++){sorted[i]=i;depths[i]=edge_depth(i);}
    for (int i=0;i<11;i++)
        for (int j=0;j<11-i;j++)
            if (depths[j]>depths[j+1]){
                float td=depths[j];depths[j]=depths[j+1];depths[j+1]=td;
                int   te=sorted[j];sorted[j]=sorted[j+1];sorted[j+1]=te;
            }

    for (int i=0;i<12;i++) {
        int ei=sorted[i], v1=edges[ei][0], v2=edges[ei][1];
        float dn=(depths[i]+2.0f)/4.0f;
        if(dn<0)dn=0; if(dn>1)dn=1;
        uint16_t color=((uint16_t)(uint8_t)(31*dn)) |
                       ((uint16_t)(uint8_t)(63*(1.0f-dn*0.5f))<<5);
        // fb_draw_line_aa lives in display.c – no local duplicate
        fb_draw_line_aa(framebuffer,
                        projected[v1][0],projected[v1][1],
                        projected[v2][0],projected[v2][1], color);
    }

    for (int i=0;i<8;i++) {
        int x=(int)(projected[i][0]+0.5f), y=(int)(projected[i][1]+0.5f);
        fb_draw_pixel(framebuffer,x,  y,  COLOR_WHITE);
        fb_draw_pixel(framebuffer,x-1,y,  COLOR_WHITE);
        fb_draw_pixel(framebuffer,x+1,y,  COLOR_WHITE);
        fb_draw_pixel(framebuffer,x,  y-1,COLOR_WHITE);
        fb_draw_pixel(framebuffer,x,  y+1,COLOR_WHITE);
    }
}

// ---------------------------------------------------------------------------
// Button callbacks
// ---------------------------------------------------------------------------
static void btn_a_cb(button_t b){(void)b; auto_rotate=!auto_rotate;}

static void btn_b_cb(button_t b){
    (void)b;
    angle_x=0.3f; angle_y=0.5f; angle_z=0.0f; zoom=1.5f;
    fading_out=true; fading_in=false;          // trigger fade reset effect
}

static void btn_x_cb(button_t b){
    (void)b;
    speed_x*=1.5f; speed_y*=1.5f; speed_z*=1.5f;
    if(speed_x>0.1f)speed_x=0.1f;
    if(speed_y>0.1f)speed_y=0.1f;
    if(speed_z>0.1f)speed_z=0.1f;
}

static void btn_y_cb(button_t b){
    (void)b; zoom+=0.3f; if(zoom>3.0f)zoom=0.8f;
}

// ---------------------------------------------------------------------------
// Main loop
// ---------------------------------------------------------------------------
int main(void) {
    stdio_init_all();

    if (display_pack_init() != DISPLAY_OK) { printf("Display init failed\n"); return 1; }
    if (buttons_init()      != DISPLAY_OK) { printf("Buttons init failed\n"); return 1; }

    button_set_callback(BUTTON_A, btn_a_cb);
    button_set_callback(BUTTON_B, btn_b_cb);
    button_set_callback(BUTTON_X, btn_x_cb);
    button_set_callback(BUTTON_Y, btn_y_cb);

    display_clear(COLOR_BLACK);
    display_set_backlight(true);

    printf("3D Cube  A=Pause  B=Fade+Reset  X=Speed  Y=Zoom\n");

    while (1) {
        buttons_update();

        // Clear framebuffer via display.h helper
        fb_clear(framebuffer, COLOR_BLACK);

        // Update rotation
        if (auto_rotate) {
            angle_x+=speed_x; angle_y+=speed_y; angle_z+=speed_z;
            if(angle_x>2*M_PI)angle_x-=2*M_PI;
            if(angle_y>2*M_PI)angle_y-=2*M_PI;
            if(angle_z>2*M_PI)angle_z-=2*M_PI;
        }

        render_cube();

        // HUD – fb_draw_string now handles lowercase via display.h extended font
        char buf[64];
        snprintf(buf,sizeof(buf),"A:%s  X:spd  Y:zoom  B:reset",
                 auto_rotate?"pause":"play ");
        fb_draw_string(framebuffer, 5,   5, buf, COLOR_GREEN, COLOR_BLACK);

        snprintf(buf,sizeof(buf),"spd:%.3f  zoom:%.1fx", (double)speed_y,(double)zoom);
        fb_draw_string(framebuffer, 5, 225, buf, COLOR_CYAN,  COLOR_BLACK);

        // Fade effect: Flash-style ColorTransform dim (ported in display.c)
        if (fading_out) {
            fade_level -= 0.08f;
            if (fade_level<=0.0f){fade_level=0.0f; fading_out=false; fading_in=true;}
        } else if (fading_in) {
            fade_level += 0.08f;
            if (fade_level>=1.0f){fade_level=1.0f; fading_in=false;}
        }

        if (fade_level < 1.0f) {
            // fb_cx_dim() and fb_apply_color_transform() live in display.c
            fb_color_transform_t cx = fb_cx_dim((uint8_t)(fade_level*255.0f));
            fb_apply_color_transform(framebuffer, &cx);
        }

        // Single DMA blit — no tearing
        display_blit_full(framebuffer);

        sleep_ms(33);
    }

    return 0;
}
