/*
 * main.c - Pico 2W RTOS + GFX client
 *
 * Core 0: preemptive RTOS
 *   - led_task     (prio 2): LED toggle demo
 *   - counter_task (prio 1): counter demo
 *   - net_task     (prio 1): polls Mac GFX server, fills g_gfx_buf
 *   - idle_task    (prio 0): WFI
 *
 * Core 1: display
 *   - If g_gfx_ready: render GFX commands from g_gfx_buf
 *   - Else:           render RTOS scheduler visualisation
 */

#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/sync.h"
#include "rtos.h"
#include "display.h"
#include "net.h"
#include "config.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/*  Shared RTOS state (core 0 - core 1) */
volatile uint32_t g_count  = 0;
volatile bool     g_led_on = false;

/*  Network debug status (core 0 net_task - core 1 display) */
volatile uint8_t  g_net_state  = 0;   /* 0=init 1=wifi 2=connecting 3=conn 4=err */
volatile uint32_t g_net_frames = 0;   /* total frames received */
volatile int      g_ring_avail = 0;   /* last ring buffer bytes available */
volatile uint32_t g_recv_cb_count = 0; /* incremented in recv_cb */
volatile uint32_t g_poll_count    = 0; /* incremented each cyw43_arch_poll call */
volatile uint32_t g_total_bytes   = 0; /* total bytes written to ring */

/*  Shared GFX double-buffer (core 0 net_task - core 1 display) -
 * net_task writes into buf[write_idx] and then atomically flips write_idx.
 * core 1 always reads from buf[1 - write_idx] (the last fully written slot).
 * No flag needed: core 1 just grabs the latest available frame each tick.
 *  */
#define GFX_BUF_SIZE 8192
static char              g_gfx_buf[2][GFX_BUF_SIZE];
static volatile int      g_gfx_write_idx = 0;   /* slot net_task just finished */
static volatile bool     g_gfx_active    = false; /* true once first frame rcvd */

/* 
 *  CORE 1  display
 */

/*  GFX command renderer */

/*
 * Parse a 6-char uppercase hex RGB888 string (e.g. "FF8000")
 * and return the byte-swapped RGB565 value for the DMA framebuffer.
 *
 * The SPI DMA sends bytes in memory order (little-endian), so a uint16_t
 * stored in the framebuffer is received by the ST7789V2 byte-swapped.
 * We pre-swap here so the on-screen color matches the server's RGB888.
 *
 * If colors look wrong (inverted), remove the __builtin_bswap16() call.
 */
static uint16_t parse_color(const char *hex6) {
    char tmp[7];
    memcpy(tmp, hex6, 6);
    tmp[6] = '\0';
    unsigned long rgb = strtoul(tmp, NULL, 16);
    uint8_t  r  = (rgb >> 16) & 0xFF;
    uint8_t  g  = (rgb >>  8) & 0xFF;
    uint8_t  b  =  rgb        & 0xFF;
    uint16_t c  = fb_rgb(r, g, b);
    return __builtin_bswap16(c);
}

/*
 * Render one frame of GFX commands into the framebuffer.
 * Commands are newline-separated ASCII (see server/server.py for protocol).
 */
static uint16_t s_bg_color = 0x0000;   /* tracks last CLEAR color for TEXT bg */

static void render_gfx(uint16_t *fb, const char *cmds) {
    const char *p = cmds;

    while (*p) {
        /* Extract one line */
        const char *nl  = strchr(p, '\n');
        size_t      len = nl ? (size_t)(nl - p) : strlen(p);
        if (len == 0) { p = nl ? nl + 1 : p + strlen(p); continue; }

        char line[128];
        if (len >= sizeof(line)) len = sizeof(line) - 1;
        memcpy(line, p, len);
        line[len] = '\0';
        p = nl ? nl + 1 : p + strlen(p);

        /* CLEAR RRGGBB */
        if (strncmp(line, "CLEAR ", 6) == 0 && len >= 12) {
            s_bg_color = parse_color(line + 6);
            fb_clear(fb, s_bg_color);

        /* RECT x y w h RRGGBB */
        } else if (strncmp(line, "RECT ", 5) == 0) {
            int  x, y, w, h;
            char col[8];
            if (sscanf(line + 5, "%d %d %d %d %6s", &x, &y, &w, &h, col) == 5) {
                fb_fill_rect(fb, x, y, w, h, parse_color(col));
            }

        /* TEXT x y RRGGBB message */
        } else if (strncmp(line, "TEXT ", 5) == 0) {
            int  x, y;
            char col[8], msg[80];
            if (sscanf(line + 5, "%d %d %6s %79[^\n]", &x, &y, col, msg) >= 3) {
                fb_draw_string(fb, x, y, msg, parse_color(col), s_bg_color);
            }

        /* NOP — nothing */
        }
    }
}

/*  RTOS visualiser (shown when no GFX data available)  */

#define COL_HDR_BG   0x000Fu
#define COL_CARD_BG  0x2104u
#define COL_TL_BG    0x1082u
#define COL_DOT_OFF  0x4208u
#define COL_SEP      0x630Cu
#define COL_ORANGE   0xFD20u

static const uint16_t TC[4] = {
    0x07FF,   /* LED     → orange/amber */
    0xF81F,   /* Counter → bright teal  */
    0x00F8,   /* Idle    → bright red   */
    0xE01F,   /* NET     → yellow       */
};
static const char * const TL_LABEL[4] = { "LED", "CTR", "IDL", "NET" };
static const char     * const STXT[4] = { "  READY  ", ">>RUNNING<<", " BLOCKED ", " SUSPEND " };
static const uint16_t         SBG[4]  = { COLOR_YELLOW, COLOR_GREEN, COL_ORANGE, COL_SEP };
static const uint16_t         SFG[4]  = { COLOR_BLACK,  COLOR_BLACK, COLOR_BLACK, COLOR_WHITE };

#define HDR_H      16
#define CARD_Y     18
#define CARD_W     74
#define CARD_H    110
static const int CX[4] = { 2, 82, 162, 242 };

#define TL_Y      132
#define TL_X       40
#define TL_W      RTOS_TIMELINE_LEN
#define TL_ROW_H   14
#define TL_ROW_GAP  3

static void draw_card(uint16_t *fb, int ci) {
    const int x = CX[ci], y = CARD_Y;
    task_state_t st = tasks[ci].state;
    uint16_t tc = TC[ci];
    char buf[20];

    fb_fill_rect(fb, x, y, CARD_W, CARD_H, COL_CARD_BG);

    if (st == TASK_RUNNING) {
        fb_fill_rect(fb, x,          y,          1, CARD_H, COLOR_WHITE);
        fb_fill_rect(fb, x+CARD_W-1, y,          1, CARD_H, COLOR_WHITE);
        fb_fill_rect(fb, x,          y+CARD_H-1, CARD_W, 1, COLOR_WHITE);
    }

    fb_fill_rect(fb, x, y, CARD_W, 14, tc);
    fb_draw_string(fb, x+2, y+3, tasks[ci].name, COLOR_BLACK, tc);

    for (int p = 0; p < 3; p++) {
        uint16_t dot = (p < (int)tasks[ci].priority) ? tc : COL_DOT_OFF;
        fb_fill_rect(fb, x+2+p*12, y+18, 9, 8, dot);
    }

    fb_fill_rect(fb, x+2, y+30, CARD_W-4, 13, SBG[st]);
    fb_draw_string(fb, x+3, y+32, STXT[st], SFG[st], SBG[st]);

    if (ci == 0) {
        fb_draw_string(fb, x+2, y+48, g_led_on ? "led:ON " : "led:OFF",
                       COLOR_WHITE, COL_CARD_BG);
    } else if (ci == 1) {
        snprintf(buf, sizeof(buf), "n=%lu", (unsigned long)g_count);
        fb_draw_string(fb, x+2, y+48, buf, COLOR_WHITE, COL_CARD_BG);
    } else if (ci == 2) {
        fb_draw_string(fb, x+2, y+48, "wfi", COL_SEP, COL_CARD_BG);
    } else {
        fb_draw_string(fb, x+2, y+48, "http", TC[3], COL_CARD_BG);
    }

    if (st == TASK_BLOCKED) {
        uint32_t rem = (tick_count < tasks[ci].wake_time)
                       ? tasks[ci].wake_time - tick_count : 0;
        snprintf(buf, sizeof(buf), "w:%4lums", (unsigned long)rem);
        fb_draw_string(fb, x+2, y+59, buf, COL_ORANGE, COL_CARD_BG);
    }

    /* Mini activity bar */
    const int bx = x+2, bw = CARD_W-4, by = y+72, bh = 14;
    fb_fill_rect(fb, bx, by, bw, bh, COL_TL_BG);
    uint16_t head = rtos_timeline_pos;
    for (int px = 0; px < bw; px++) {
        uint16_t pos = head - (uint16_t)(bw - px);
        if (rtos_timeline[pos % RTOS_TIMELINE_LEN] == (uint8_t)ci) {
            for (int py = by+2; py < by+bh-2; py++)
                fb[py * DISPLAY_WIDTH + bx + px] = tc;
        }
    }
}

static void draw_timeline(uint16_t *fb, int num_tasks_shown) {
    fb_draw_string(fb, 4, TL_Y+2, "SCHED", COL_SEP, COLOR_BLACK);
    uint16_t head = rtos_timeline_pos;
    for (int ci = 0; ci < num_tasks_shown; ci++) {
        int ry = TL_Y + 14 + ci * (TL_ROW_H + TL_ROW_GAP);
        fb_draw_string(fb, 4, ry+3, TL_LABEL[ci], TC[ci], COLOR_BLACK);
        fb_fill_rect(fb, TL_X, ry, TL_W, TL_ROW_H, COL_TL_BG);
        for (int px = 0; px < TL_W; px++) {
            uint16_t pos = head - (uint16_t)(TL_W - px);
            if (rtos_timeline[pos % RTOS_TIMELINE_LEN] == (uint8_t)ci) {
                for (int py = ry+2; py < ry+TL_ROW_H-2; py++)
                    fb[py * DISPLAY_WIDTH + TL_X + px] = TC[ci];
            }
        }
    }
}

/*  Core 1 main  */

static uint16_t framebuf[DISPLAY_WIDTH * DISPLAY_HEIGHT];

static void core1_display_main(void) {
    display_pack_init();

    int last_rendered_idx = -1;   /* which slot we last rendered */

    while (1) {
        char buf[24];

        int latest = g_gfx_write_idx;   /* snapshot - net_task updates this */

        if (g_gfx_active && latest != last_rendered_idx) {
            /*  New GFX frame available: render it  */
            __dmb();
            render_gfx(framebuf, g_gfx_buf[latest]);
            last_rendered_idx = latest;
        } else if (!g_gfx_active) {
            /*  No GFX data yet: show RTOS visualiser  */
            fb_clear(framebuf, COLOR_BLACK);
            fb_fill_rect(framebuf, 0, 0, DISPLAY_WIDTH, HDR_H, COL_HDR_BG);
            fb_draw_string(framebuf, 4, 4, "PICO 2W  RTOS", COLOR_BLACK, COL_HDR_BG);
            snprintf(buf, sizeof(buf), "tick:%06lu", (unsigned long)tick_count);
            fb_draw_string(framebuf, 180, 4, buf, COLOR_WHITE, COL_HDR_BG);
            fb_fill_rect(framebuf, 0, HDR_H, DISPLAY_WIDTH, 1, COL_SEP);


            for (int ci = 0; ci < 4; ci++)
                draw_card(framebuf, ci);
            draw_timeline(framebuf, 4);
        }
        /* else: GFX active, same frame as last tick — blit unchanged */

        display_blit_full(framebuf);
        display_wait_for_dma();
    }
}

/* 
 *  CORE 0  RTOS tasks
 */

static void active_ms(uint32_t ms) {
    uint32_t end = tick_count + ms;
    while ((int32_t)(end - tick_count) > 0)
        task_yield();
}

void led_task(void *param) {
    (void)param;
    while (1) {
        g_led_on = true;
        active_ms(200);
        task_delay(200);
        g_led_on = false;
        active_ms(200);
        task_delay(100);
    }
}

void counter_task(void *param) {
    (void)param;
    while (1) {
        g_count++;
        active_ms(80);
        task_delay(20);
    }
}

/*  net_task: persistent stream, double-buffer frames for core 1 - */
void net_task(void *param) {
    (void)param;

    g_net_state = 1;   /* wifi up, connecting TCP */
    while (!net_stream_connect()) {
        g_net_state = 4;   /* connect failed */
        task_delay(2000);
        g_net_state = 2;
    }
    g_net_state = 3;   /* connected */

    while (1) {
        int write_slot = 1 - g_gfx_write_idx;
        g_ring_avail = (int)net_ring_available();
        int len = net_stream_poll(g_gfx_buf[write_slot], GFX_BUF_SIZE);

        if (len > 0) {
            __dmb();
            g_gfx_write_idx = write_slot;
            g_gfx_active    = true;
            g_net_frames++;
        } else if (len < 0) {
            g_net_state = 4;   /* disconnected */
            task_delay(500);
            g_net_state = 2;
            while (!net_stream_connect()) {
                g_net_state = 4;
                task_delay(2000);
                g_net_state = 2;
            }
            g_net_state = 3;
        }

        task_delay(1);   /* yield 1 ms so lower-priority tasks can run */
    }
}

void idle_task(void *param) {
    (void)param;
    while (1) __asm volatile("wfi");
}

/*  main ─ */
int main(void) {
    stdio_init_all();

    /*
     * Initialise WiFi before the RTOS starts.
     * If the AP is absent the connect will time out after 10 s and
     * net_task will keep retrying in the background.
     */
    if (net_init()) g_net_state = 1;   /* wifi connected */

    rtos_init();
    task_create(net_task,     "NET",  3, NULL);   /* highest: must poll lwIP */
    task_create(led_task,     "LED",  2, NULL);
    task_create(counter_task, "CTR",  1, NULL);
    task_create(idle_task,    "Idle", 0, NULL);

    multicore_launch_core1(core1_display_main);
    sleep_ms(500);

    rtos_start();
    return 0;
}
