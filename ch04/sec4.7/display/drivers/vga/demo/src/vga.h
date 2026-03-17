/*
 * vga.h  double-buffered VGA output driver for Pico 2
 *
 * Uses pico_scanvideo_dpi (pico-extras) on core 1.
 * Core 0 renders into the back buffer; swap via vga_swap_buffers().
 *
 * Pin mapping (Pimoroni Pico VGA Demo Base / compatible wiring):
 *   GPIO  0-  4 : Blue  [4:0]
 *   GPIO  5- 10 : Green [5:0]
 *   GPIO 11- 15 : Red   [4:0]
 *   GPIO 16    : H-sync
 *   GPIO 17    : V-sync
 *
 * Resolution: 320 x 240, RGB565, 60 Hz
 */

#pragma once
#include <stdint.h>
#include <stdbool.h>
#include "gfx.h"      /* for GFX_W, GFX_H, gfx_color_t */

/* Frame-buffer size in pixels / bytes */
#define VGA_FB_PIXELS (GFX_W * GFX_H)
#define VGA_FB_BYTES  (VGA_FB_PIXELS * sizeof(gfx_color_t))


/* API */

/* Initialise VGA hardware.  Must be called from core 0 before launching
   core 1.  Sets up pico_scanvideo_dpi, allocates framebuffers. */
void vga_init(void);

/* Entry point for core 1.  Call via multicore_launch_core1(vga_core1_main).
   Never returns. */
void vga_core1_main(void);

/* Return a pointer to the back framebuffer (the one core 0 may write to).
   Always 320 x 240 RGB565, row-major. */
gfx_color_t *vga_back_buffer(void);

/* Atomically publish the current back buffer as the new front and flip.
   Core 1 will start reading the new front on the next vsync opportunity. */
void vga_swap_buffers(void);

/* Optional: spin until core 1 acknowledges the last swap (avoids tearing
   if your render loop is faster than the display refresh). */
void vga_wait_vsync(void);

/* Returns the total number of frames displayed since init (for timing). */
uint32_t vga_frame_count(void);
