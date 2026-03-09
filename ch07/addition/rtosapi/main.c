/*
 * main.c - Pico 2W RTOS visual demo
 *
 * Core 0: preemptive RTOS - LED toggle (prio 2), counter (prio 1), idle (prio 0)
 * Core 1: display - live task-state cards + scrolling scheduler timeline
 *
 * Layout (320x240):
 *   y=  0..15  header bar
 *   y= 18..127 three task cards (96x110 each)
 *   y=132..239 scheduler timeline (3 rows, one per task)
 */

#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "rtos.h"
#include "display.h"
#include <stdio.h>
#include "rtos_queue.h"
#include "rtos_shell.h"

/* -------------------------------------------- */
/*  Shared state (core 0 writes, core 1 reads)  */
/* -------------------------------------------- */
volatile uint32_t g_count  = 0;
volatile bool     g_led_on = false;

/* ----------------- */
/*  Display palette  */
/* ----------------- */
#define COL_HDR_BG   0x000Fu   /* dark navy header           */
#define COL_CARD_BG  0x2104u   /* charcoal card background   */
#define COL_TL_BG    0x1082u   /* darker timeline slot bg    */
#define COL_DOT_OFF  0x4208u   /* unfilled priority dot      */
#define COL_SEP      0x630Cu   /* separator / label color    */
#define COL_ORANGE   0xFD20u   /* BLOCKED badge + wake text  */

/*
 * One accent color per task.
 * NOTE: display_blit_full uses 8-bit DMA (little-endian byte order), so
 * the ST7789V2 sees bytes swapped vs what we write.  Each value here is
 * the byte-swapped form of the intended on-screen color:
 *   0x07FF -> on-screen 0xFF07 = orange/amber  (LED)
 *   0xF81F -> on-screen 0x1FF8 = bright teal   (Counter)
 *   0x00F8 -> on-screen 0xF800 = bright red    (Idle)
 * (Change this palette to your liking, but keep the byte-swapped values here!)
 */
static const uint16_t TC[3] = {
    0x07FF,   /* -> orange/amber on-screen - LED     */
    0xF81F,   /* -> bright teal  on-screen - COUNTER */
    0x00F8,   /* -> bright red   on-screen - IDLE    */
};

/* Short labels used in the timeline section */
static const char * const TL_LABEL[3] = { "LED", "CTR", "IDL" };

/* State badge text and colors */
static const char     * const STXT[4] = { "  READY  ", ">>RUNNING<<", " BLOCKED ", " SUSPEND " };
static const uint16_t         SBG[4]  = { COLOR_YELLOW, COLOR_GREEN, COL_ORANGE, COL_SEP  };
static const uint16_t         SFG[4]  = { COLOR_BLACK,  COLOR_BLACK, COLOR_BLACK, COLOR_WHITE };

/* ------------------ */
/*  Layout constants  */
/* ------------------ */
#define HDR_H       16
#define CARD_Y      18
#define CARD_W      96
#define CARD_H     110
static const int CX[3] = { 4, 108, 212 };   /* card x positions */

#define TL_Y       132   /* timeline section y start               */
#define TL_X        40   /* bar x start (after row label)          */
#define TL_W       RTOS_TIMELINE_LEN   /* 280px × 4ms/px = 1120ms  */
#define TL_ROW_H    18
#define TL_ROW_GAP   4

/* Scan the stack canary from the base upward to find the high-watermark.
 * Core 1 calls this; Core 0 writes to the stack from the top downward.
 * 32-bit aligned reads on shared SRAM are atomic on RP2350, so a slightly
 * stale watermark on the display is acceptable.                          */
static uint16_t stack_peak_words(int ci)
{
    const uint32_t *stack = tasks[ci].stack;
    uint16_t free = 0;
    while (free < TASK_STACK_SIZE && stack[free] == RTOS_STACK_CANARY)
        free++;
    return TASK_STACK_SIZE - free;
}

/* -------------------------------------------- */
/*  draw_card() - one 96x110 task status card   */
/* -------------------------------------------- */
static void draw_card(uint16_t *fb, int ci) {
    const int x  = CX[ci];
    const int y  = CARD_Y;
    task_state_t st = tasks[ci].state;
    uint16_t tc = TC[ci];
    char buf[20];

    /* Card background */
    fb_fill_rect(fb, x, y, CARD_W, CARD_H, COL_CARD_BG);

    /* Bright border when RUNNING */
    if (st == TASK_RUNNING) {
        fb_fill_rect(fb, x,           y,         1, CARD_H,  COLOR_WHITE);
        fb_fill_rect(fb, x+CARD_W-1,  y,         1, CARD_H,  COLOR_WHITE);
        fb_fill_rect(fb, x,           y+CARD_H-1,CARD_W, 1,  COLOR_WHITE);
    }

    /* -- Name bar -- */
    fb_fill_rect(fb, x, y, CARD_W, 14, tc);
    fb_draw_string(fb, x+4, y+3, tasks[ci].name, COLOR_BLACK, tc);

    /* -- Priority: label + filled dots -- */
    fb_draw_string(fb, x+4, y+18, "prio:", COLOR_WHITE, COL_CARD_BG);
    for (int p = 0; p < 3; p++) {
        uint16_t dot = (p < (int)tasks[ci].priority) ? tc : COL_DOT_OFF;
        fb_fill_rect(fb, x+40+p*12, y+18, 9, 8, dot);
    }

    /* -- State badge -- */
    fb_fill_rect(fb, x+4, y+30, CARD_W-8, 13, SBG[st]);
    fb_draw_string(fb, x+6, y+32, STXT[st], SFG[st], SBG[st]);

    /* -- Task-specific info -- */
    if (ci == 0) {
        fb_draw_string(fb, x+4, y+48,
                       g_led_on ? "led: ON " : "led: OFF",
                       COLOR_WHITE, COL_CARD_BG);
    } else if (ci == 1) {
        snprintf(buf, sizeof(buf), "n=%lu", (unsigned long)g_count);
        fb_draw_string(fb, x+4, y+48, buf, COLOR_WHITE, COL_CARD_BG);
    } else {
        fb_draw_string(fb, x+4, y+48, "wfi", COL_SEP, COL_CARD_BG);
    }

    /* Wake countdown when BLOCKED */
    if (st == TASK_BLOCKED) {
        uint32_t rem = (tick_count < tasks[ci].wake_time)
                       ? tasks[ci].wake_time - tick_count : 0;
        snprintf(buf, sizeof(buf), "wake:%4lums", (unsigned long)rem);
        fb_draw_string(fb, x+4, y+59, buf, COL_ORANGE, COL_CARD_BG);
    }

    /* -- Mini activity bar (last ~350 ms) -- */
    const int bx = x+4, bw = CARD_W-8, by = y+72, bh = 14;
    fb_fill_rect(fb, bx, by, bw, bh, COL_TL_BG);
    {
        uint16_t head = rtos_timeline_pos;
        for (int px = 0; px < bw; px++) {
            uint16_t pos = head - (uint16_t)(bw - px);
            if (rtos_timeline[pos % RTOS_TIMELINE_LEN] == (uint8_t)ci) {
                for (int py = by+2; py < by+bh-2; py++)
                    fb[py * DISPLAY_WIDTH + bx + px] = tc;
            }
        }
    }

    /* -- CPU% and stack high-watermark -- */
    {
        uint8_t cpu_pct = tick_count
            ? (uint8_t)((uint64_t)tasks[ci].run_ticks * 100u / tick_count)
            : 0u;
        uint16_t stk = stack_peak_words(ci);
        snprintf(buf, sizeof(buf), "cpu:%3u%%", cpu_pct);
        fb_draw_string(fb, x+4, y+88, buf, COL_SEP, COL_CARD_BG);
        snprintf(buf, sizeof(buf), "stk:%3u/256", stk);
        fb_draw_string(fb, x+4, y+98, buf, COL_SEP, COL_CARD_BG);
    }
}

/* ----------------------------------------------------- */
/*  draw_timeline() - scrolling 280ms scheduler history  */
/* ----------------------------------------------------- */
static void draw_timeline(uint16_t *fb) {
    fb_draw_string(fb, 4, TL_Y+2, "SCHEDULER", COL_SEP, COLOR_BLACK);

    uint16_t head = rtos_timeline_pos;   /* snapshot for consistent frame */

    for (int ci = 0; ci < 3; ci++) {
        int ry = TL_Y + 14 + ci * (TL_ROW_H + TL_ROW_GAP);
        uint16_t tc = TC[ci];

        fb_draw_string(fb, 4, ry+5, TL_LABEL[ci], tc, COLOR_BLACK);
        fb_fill_rect(fb, TL_X, ry, TL_W, TL_ROW_H, COL_TL_BG);

        for (int px = 0; px < TL_W; px++) {
            uint16_t pos = head - (uint16_t)(TL_W - px);
            if (rtos_timeline[pos % RTOS_TIMELINE_LEN] == (uint8_t)ci) {
                for (int py = ry+3; py < ry+TL_ROW_H-3; py++)
                    fb[py * DISPLAY_WIDTH + TL_X + px] = tc;
            }
        }
    }
}

/* ----------------------- */
/*  Core 1 - display loop  */
/* ----------------------- */
// Frame buffer for the whole display.  Core 1 owns this and the SPI/DMA,
// so no synchronisation needed for core 0 to write to it indirectly via
// the display_pack library.  (If core 0 were to write directly to this
// buffer, we'd need to disable interrupts around those writes to avoid
// tearing artifacts on the display.)
static uint16_t framebuf[DISPLAY_WIDTH * DISPLAY_HEIGHT];

static void core1_display_main(void) {
    display_pack_init();

    while (1) {
        char buf[24];

        fb_clear(framebuf, COLOR_BLACK);

        /* -- Header -- */
        fb_fill_rect(framebuf, 0, 0, DISPLAY_WIDTH, HDR_H, COL_HDR_BG);
        fb_draw_string(framebuf, 4,   4, "PICO 2W  RTOS", COLOR_BLACK, COL_HDR_BG);
        snprintf(buf, sizeof(buf), "tick:%06lu", (unsigned long)tick_count);
        fb_draw_string(framebuf, 196, 4, buf,           COLOR_WHITE, COL_HDR_BG);
        fb_fill_rect(framebuf, 0, HDR_H, DISPLAY_WIDTH, 1, COL_SEP);

        /* -- Task cards -- */
        for (int ci = 0; ci < 3; ci++)
            draw_card(framebuf, ci);

        /* -- Scheduler timeline -- */
        draw_timeline(framebuf);

        display_blit_full(framebuf);
        display_wait_for_dma();
        sleep_ms(50);
    }
}

/* ------------------- */
/*  Core 0 RTOS tasks  */
/* ------------------- */
/*
 * active_ms - keep the calling task READY/RUNNING for ~ms milliseconds
 * without actually blocking.  Higher-priority tasks still preempt us
 * on each yield, which is the whole point: it shows in the timeline
 * exactly which task owns the CPU and when it gets preempted.
 */
static void active_ms(uint32_t ms) {
    uint32_t end = tick_count + ms;
    while ((int32_t)(end - tick_count) > 0)
        task_yield();
}

/*
 * LED task - priority 2 (HIGHEST)
 *
 * Cycle (period = 700 ms total):
 *   g_led_on = true  -> active_ms(200)  200 ms active,  LED on
 *                    -> task_delay(200) 200 ms blocked,  LED on
 *   g_led_on = false -> active_ms(200)  200 ms active,  LED off
 *                    -> task_delay(100) 100 ms blocked,  LED off
 *
 * During the two active windows this task starves Counter entirely -
 * the solid LED-coloured block on the timeline makes this visible.
 */
void led_task(void *param) {
    (void)param;
    while (1) {
        g_led_on = true;
        active_ms(200);        /* 200 ms: highest-prio, owns CPU completely */
        task_delay(200);       /* 200 ms: BLOCKED, Counter runs             */
        g_led_on = false;
        active_ms(200);        /* another 200 ms active window              */
        task_delay(100);       /* short rest before next ON cycle           */
    }
}

/*
 * Counter task - priority 1 (MEDIUM)
 *
 * Active for 80 ms (preemptable by LED), sleeps 20 ms.
 * Period: 100 ms.  Inside LED's blocked window the counter fills in
 * with its own magenta blocks; when LED wakes it is immediately
 * pushed off the CPU (priority preemption visible in the timeline).
 */
void counter_task(void *param) {
    (void)param;
    while (1) {
        g_count++;
        active_ms(80);         /* 80 ms: medium-prio, preempted by LED     */
        task_delay(20);        /* 20 ms: BLOCKED, Idle gets a turn         */
    }
}

/*
 * Idle task - priority 0 (LOWEST)
 *
 * Runs WFI whenever both higher-priority tasks are sleeping.
 * Fills the gray gaps on the timeline between LED and Counter work.
 */
void idle_task(void *param) {
    (void)param;
    while (1) __asm volatile("wfi");
}

/*
 * Shell task - priority 1 (same level as Counter, round-robin).
 *
 * Waits 1500 ms for the USB CDC connection to stabilise before printing
 * the welcome banner, then calls shell_tick() every 10 ms.  Between ticks
 * the task blocks, so it consumes negligible CPU while idle.
 */
void shell_task(void *param) {
    (void)param;
    task_delay(1500);                /* wait for USB CDC to enumerate */
    printf("\r\n=== Pico 2W RTOS Shell ===\r\n");
    printf("Type 'help' for a list of commands.\r\n> ");
    while (1) {
        shell_tick();
        task_delay(10);
    }
}

/* ------------------------------------------------------------------ */
int main(void) {
    stdio_init_all();

    /* Create tasks first so core 1 sees valid names/states immediately */
    rtos_init();
    task_create(led_task,     "LED",     2, NULL);
    task_create(counter_task, "Counter", 1, NULL);
    task_create(idle_task,    "Idle",    0, NULL);
    task_create(shell_task,   "Shell",   1, NULL);

    shell_init();

    /* Launch display on core 1 - it owns all SPI/DMA */
    multicore_launch_core1(core1_display_main);
    sleep_ms(500);   /* wait for display_pack_init on core 1 */

    rtos_start();
    return 0;
}
