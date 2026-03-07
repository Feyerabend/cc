/*
 * main.c — Pico 2W VGTP receiver
 *
 * Core 0: preemptive RTOS
 *   net_task      (prio 3) — polls CYW43/lwIP every 10 ms
 *   protocol_task (prio 2) — parses VGTP, assembles frames into scene buffer
 *   idle_task     (prio 0) — WFI
 *
 * Core 1: display loop
 *   Renders from render_scene (double-buffered, swapped atomically by protocol_task)
 *   Shows a status overlay until the first frame arrives.
 */

#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "pico/time.h"
#include "rtos.h"
#include "display.h"
#include "net.h"
#include "scene.h"
#include "protocol.h"
#include <stdio.h>
#include <string.h>

/* ----------------------- */
/*  Core 1 — display loop  */
/* ----------------------- */

static uint16_t framebuf[DISPLAY_WIDTH * DISPLAY_HEIGHT];

/* Palette for the status overlay */
#define COL_HDR_BG  0x000Fu
#define COL_STATUS  0x2104u
#define COL_SEP     0x630Cu

static void ip_to_str(uint32_t ip, char *buf, int len)
{
    snprintf(buf, len, "%lu.%lu.%lu.%lu",
             (ip >>  0) & 0xFF, (ip >>  8) & 0xFF,
             (ip >> 16) & 0xFF, (ip >> 24) & 0xFF);
}

static void draw_status_overlay(uint16_t *fb)
{
    char buf[48];

    /* Header bar */
    fb_fill_rect(fb, 0, 0, DISPLAY_WIDTH, 14, COL_HDR_BG);
    fb_draw_string(fb, 4, 3, "VGTP", COL_SEP, COL_HDR_BG);

    if (g_wifi_connected) {
        char ip[20];
        ip_to_str(g_wifi_ip, ip, sizeof(ip));
        snprintf(buf, sizeof(buf), "%-16s rx:%-6lu f:%lu",
                 ip,
                 (unsigned long)g_udp_rx_count,
                 (unsigned long)g_frames_rendered);
    } else {
        snprintf(buf, sizeof(buf), "connecting...");
    }
    fb_draw_string(fb, 34, 3, buf, COLOR_WHITE, COL_HDR_BG);
}

static void core1_display_main(void)
{
    display_pack_init();

    while (1) {
        /* Canvas buffer is the background; scene primitives render on top */
        if (g_canvas_used)
            memcpy(framebuf, canvas_buf, sizeof(framebuf));
        else
            fb_clear(framebuf, 0x0000);

        /* Render current scene */
        const scene_buffer_t *s = (const scene_buffer_t *)render_scene;

        if (s->prim_count == 0 && !s->has_clear && !g_canvas_used) {
            /* No frame yet — show waiting message */
            fb_draw_string(framebuf, 80, 110, "waiting for VGTP frames...",
                           COLOR_WHITE, COLOR_BLACK);
        } else {
            if (s->has_clear)
                fb_fill_rect(framebuf, 0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT, s->clear_color);

            for (uint16_t i = 0; i < s->prim_count; i++) {
                const primitive_t *p = &s->prims[i];
                switch (p->type) {
                case PRIM_RECT:
                    fb_fill_rect(framebuf,
                                 p->rect.x, p->rect.y, p->rect.w, p->rect.h,
                                 p->rect.color);
                    break;
                case PRIM_TEXT:
                    fb_draw_string(framebuf,
                                   p->text.x, p->text.y, p->text.text,
                                   p->text.fg, p->text.bg);
                    break;
                case PRIM_LINE:
                    fb_draw_line_aa(framebuf,
                                    p->line.x0, p->line.y0,
                                    p->line.x1, p->line.y1,
                                    p->line.color);
                    break;
                case PRIM_BITMAP:
                    fb_blit_scaled(framebuf,
                                   p->bitmap.pixels, p->bitmap.w, p->bitmap.h,
                                   p->bitmap.x, p->bitmap.y,
                                   p->bitmap.dw, p->bitmap.dh);
                    break;
                case PRIM_CIRCLE:
                    fb_draw_circle_aa(framebuf,
                                      p->circle.cx, p->circle.cy,
                                      p->circle.r,  p->circle.color);
                    break;
                default:
                    break;
                }
            }
        }

        /* Connection-lost overlay */
        if (g_wifi_connected && g_frames_rendered > 0) {
            uint32_t now = to_ms_since_boot(get_absolute_time());
            if ((now - g_last_rx_tick) > CONNECTION_TIMEOUT_MS) {
                /* Red banner, byte-swapped for DMA: 0xF800 → 0x00F8 */
                fb_fill_rect(framebuf, 0, DISPLAY_HEIGHT / 2 - 10,
                             DISPLAY_WIDTH, 20, 0x00F8u);
                fb_draw_string(framebuf, 106, DISPLAY_HEIGHT / 2 - 4,
                               "SIGNAL LOST", 0xFFFFu, 0x00F8u);
            }
        }

        /* Status overlay always on top */
        draw_status_overlay(framebuf);

        display_blit_full(framebuf);
        display_wait_for_dma();
        sleep_ms(33);   /* ~30 fps */
    }
}

/* ------------ */
/*  RTOS tasks  */
/* ------------ */
/* net_task      — defined in net.c      */
/* protocol_task — defined in protocol.c */

static void idle_task(void *param)
{
    (void)param;
    while (1) __asm volatile("wfi");
}


int main(void) {
    stdio_init_all();
    scene_init();

    rtos_init();
    task_create(net_task, "Net", 3, NULL); /* split to handle networking */
    task_create(protocol_task, "Proto", 2, NULL); /* the other the protocol */
    task_create(idle_task, "Idle", 0, NULL); /* just waiting .. */

    multicore_launch_core1(core1_display_main);
    sleep_ms(500);

    net_wifi_init(); /* blocking: CYW43 init + WiFi connect + UDP bind */

    rtos_start();
    return 0;
}
