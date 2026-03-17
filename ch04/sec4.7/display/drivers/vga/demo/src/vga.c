/*
 * vga.c  n double-buffered VGA output, core 1
 *
 * Uses pico_scanvideo_dpi from pico-extras.
 * Core 0 renders into back_buf; core 1 streams front_buf to the display.
 *
 * Double-buffer swap is atomic: a 32-bit aligned pointer write on RP2350
 * is guaranteed to be seen atomically by the other core.
 *
 * Scanline format expected by pico_scanvideo_dpi (320 x 240 mode):
 *   composable_raw_run: pixel data in RGB565, width pixels per scanline.
 */

#include "vga.h"
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "pico/sync.h"
#include "pico/scanvideo.h"
#include "pico/scanvideo/composable_scanline.h"
#include <string.h>

/* VGA mode: 320 x 240 @ 60 Hz (640 x 480 with pixel doubling) */
/*
 * pico-extras provides vga_mode_320x240_60 in pico/scanvideo.h.
 * If your version of pico-extras uses a different symbol name, adjust here.
 */
extern const scanvideo_mode_t vga_mode_320x240_60;

/* framebuffers */
/* Two full-resolution RGB565 buffers.  ~150 KB each = 307 KB total. */
static gfx_color_t fb_a[GFX_W * GFX_H];
static gfx_color_t fb_b[GFX_W * GFX_H];

/* Volatile pointer: which buffer core 1 is currently displaying. */
static volatile gfx_color_t * volatile vga_front = fb_a;
/* The buffer core 0 writes into (whichever is NOT front). */
static volatile gfx_color_t * volatile vga_back  = fb_b;

/* Frame counter, incremented by core 1 each vertical blank. */
static volatile uint32_t vga_frames = 0;

/* Swap acknowledgement flag: core 1 sets this to vga_frames each time it */
/* begins a new frame from the newly swapped front buffer. */
static volatile uint32_t vga_swap_ack = 0;

/* API */

void vga_init(void)
{
    /* Framebuffers already zero-initialised as BSS.  Clear to black. */
    memset(fb_a, 0, sizeof(fb_a));
    memset(fb_b, 0, sizeof(fb_b));
}

gfx_color_t *vga_back_buffer(void)
{
    /* Cast away volatile for the caller (safe: core 0 is the only writer).  */
    return (gfx_color_t *)vga_back;
}

void vga_swap_buffers(void)
{
    /* Atomic pointer swap: promote back -> front, front -> back. */
    gfx_color_t *old_front = (gfx_color_t *)vga_front;
    vga_front = vga_back;     /* core 1 picks this up at next scanline start */
    vga_back  = old_front;
}

void vga_wait_vsync(void)
{
    /* Spin until core 1 acknowledges the new frame, i.e. it started reading
       from the new front buffer at least once. */
    uint32_t target = vga_frames + 1;
    while (vga_swap_ack < target) tight_loop_contents();
}

uint32_t vga_frame_count(void)
{
    return vga_frames;
}

/* core 1 VGA loop */
/*
 * Runs entirely on core 1.  Never returns.
 * Iterates scanvideo_begin_scanline_generation / end in a tight loop.
 * For each scanline it copies one row from the front framebuffer.
 */

void vga_core1_main(void)
{
    scanvideo_setup(&vga_mode_320x240_60);
    scanvideo_timing_enable(true);

    uint32_t last_frame = 0;

    while (true) {
        struct scanvideo_scanline_buffer *buf =
            scanvideo_begin_scanline_generation(true);

        int scanline = scanvideo_scanline_number(buf->scanline_id);
        int frame_num = scanvideo_frame_number(buf->scanline_id);

        /* First scanline of a new frame: snapshot the current front buffer  */
        /* pointer so the entire frame uses the same buffer.                  */
        static const gfx_color_t *cur_front = fb_a;
        if (frame_num != (int)last_frame) {
            cur_front  = (const gfx_color_t *)vga_front;
            last_frame = (uint32_t)frame_num;
            vga_frames = (uint32_t)frame_num;
            vga_swap_ack = vga_frames;
        }

        /* Build the composable scanline for pico_scanvideo_dpi.
         *
         * Format: COMPOSABLE_RAW_RUN
         *   buf->data[0] lo16 = COMPOSABLE_RAW_RUN token
         *   buf->data[0] hi16 = first pixel
         *   buf->data[1] lo16 = (width - 3)      [number of extra pixels]
         *   buf->data[1] hi16 = second pixel
         *   buf->data[2..] = remaining pixels packed lo16/hi16
         *   last pair: COMPOSABLE_EOL_ALIGN
         */
        uint32_t *words = buf->data;
        const gfx_color_t *src = cur_front + scanline * GFX_W;
        int w = GFX_W;

        words[0] = (COMPOSABLE_RAW_RUN) | ((uint32_t)src[0] << 16);
        words[1] = (uint32_t)(w - 3)   | ((uint32_t)src[1] << 16);
        for (int i = 2, j = 2; i < w; i += 2, j++) {
            words[j] = (uint32_t)src[i] | ((uint32_t)(i+1 < w ? src[i+1] : 0) << 16);
        }
        /* End-of-line token.  Must be 32-bit aligned in the buffer. */
        int end_word = 2 + (w - 2 + 1) / 2;
        words[end_word] = COMPOSABLE_EOL_ALIGN;
        buf->data_used  = end_word + 1;

        scanvideo_end_scanline_generation(buf);
    }
}
