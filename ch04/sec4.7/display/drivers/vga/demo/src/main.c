/*
 * main.c  entry point for the Pico 2 VGA graphics demo
 *
 * Core assignment:
 *   Core 0: animation logic + rasterisation (this file, demo.c, gfx.c, raster.c)
 *   Core 1: VGA scanline generation (vga_core1_main, never returns)
 *
 * Render loop:
 *   1. Get back buffer pointer (the one core 1 is NOT currently displaying).
 *   2. Run demo_update()   renders into back buffer.
 *   3. Swap front / back   new frame becomes visible at next scanline.
 *   4. Optionally wait for vsync to avoid tearing.
 *
 * Timing:
 *   pico_get_absolute_time() gives microseconds.  We compute dt from that so
 *   the animation runs at the correct real-time speed regardless of render load.
 */

#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "pico/time.h"
#include "vga.h"
#include "gfx.h"
#include "demo.h"

/* global demo state (static so it lives in BSS, not on the stack) */
static demo_state_t g_demo;

/* core 1 trampoline  */
/* multicore_launch_core1 needs a function pointer with no args / no return. */
static void core1_entry(void) {
    vga_core1_main();  /* never returns */
}

/* main  */
int main(void) {
    /* Pico SDK boilerplate */
    stdio_init_all();

    /* 1. Initialise VGA hardware (sets up scanvideo clocks, pin muxing). */
    vga_init();

    /* 2. Launch VGA loop on core 1 before anything else accesses the GPU PIO.*/
    multicore_launch_core1(core1_entry);

    /* 3. Give core 1 a moment to start the scanvideo state machine. */
    sleep_ms(10);

    /* 4. Initialise the demo scene (builds shapes, places objects). */
    demo_init(&g_demo);

    /* 5. Render loop on core 0. */
    absolute_time_t prev = get_absolute_time();

    while (true) {
        /* Compute elapsed time since last frame */
        absolute_time_t now = get_absolute_time();
        int64_t us = absolute_time_diff_us(prev, now);
        prev = now;
        float dt = (float)us * 1e-6f;
        /* Clamp dt to avoid spiral-of-death on first frame or after pauses  */
        if (dt > 0.05f) dt = 0.05f;
        if (dt < 0.0f)  dt = 0.0f;

        /* Get the framebuffer core 0 may write into (not the one displayed). */
        gfx_color_t *fb = vga_back_buffer();

        /* Advance animation + rasterise into fb. */
        demo_update(&g_demo, dt, fb);

        /* Swap: make this frame visible from the next scanline forward. */
        vga_swap_buffers();

        /* Wait for core 1 to acknowledge the swap (eliminates tearing).
         * Remove this call if your render loop is slower than 60 Hz then
         * you never catch up anyway. */
        vga_wait_vsync();
    }

    return 0;  /* unreachable */
}
