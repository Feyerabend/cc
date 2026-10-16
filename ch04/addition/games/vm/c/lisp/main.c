#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "display.h"
#include "lisp_vm.h"
#include "lisp_game.h"

// GAME_SCRIPT holds the game's Lisp source. CMake generates this header
// from a .lisp file in examples/ (see CMakeLists.txt).
#include "game_script.h"

#define FRAME_US 16667  // About 60 frames per second

// The interpreter is recursive, and core 0's stack is only 4 KB on the
// RP2350 (it lives in the SCRATCH_Y memory bank). The game therefore runs
// on core 1, with a stack of its own. LISP_STACK_SIZE and LISP_MAX_DEPTH
// are set together in CMakeLists.txt.
static uint32_t lisp_stack[LISP_STACK_SIZE / sizeof(uint32_t)];

// The VM is far too big for any stack
static lisp_vm_t vm;

static void show_message(const char *title, uint16_t color, const char *text) {
    printf("%s %s\n", title, text);

    disp_framebuffer_clear(COLOR_BLACK);
    disp_framebuffer_draw_text(10, 10, title, color, COLOR_BLACK);

    // Wrap the text at 50 characters, which fits 320 pixels
    char line[51];
    int y = 30;
    const char *p = text;
    while (*p && y + 8 <= DISPLAY_HEIGHT) {
        size_t n = strlen(p);
        if (n > 50) n = 50;
        memcpy(line, p, n);
        line[n] = '\0';
        disp_framebuffer_draw_text(10, (uint16_t) y, line, COLOR_WHITE, COLOR_BLACK);
        p += n;
        y += 12;
    }
    disp_framebuffer_flush();
}

static bool init_hardware(void) {
    disp_config_t config = disp_get_default_config();
    disp_error_t err = disp_init(&config);
    if (err == DISP_OK) err = disp_framebuffer_alloc();
    if (err == DISP_OK) err = buttons_init();
    if (err != DISP_OK) {
        printf("Hardware init failed: %s\n", disp_error_string(err));
        return false;
    }
    return true;
}

static void run_game(void) {
    disp_framebuffer_clear(COLOR_BLACK);
    disp_framebuffer_draw_text(100, 116, "Loading game...", COLOR_GREEN, COLOR_BLACK);
    disp_framebuffer_flush();

    lisp_init(&vm);
    lisp_game_init(&vm);
    srand(time_us_32());

    if (lisp_run(&vm, GAME_SCRIPT) == NULL) {
        show_message("Error while loading:", COLOR_RED, lisp_error(&vm));
        return;
    }
    printf("Game loaded, %u of %d cells in use\n", (unsigned) vm.cells_used, LISP_HEAP_SIZE);
    if (!vm.running) {
        show_message("The game never called (start)", COLOR_YELLOW, "");
        return;
    }

    absolute_time_t next_frame = get_absolute_time();
    uint32_t frames = 0;
    uint64_t last_report = time_us_64();

    while (vm.running) {
        if (!lisp_game_frame(&vm)) {
            show_message("Error:", COLOR_RED, lisp_error(&vm));
            return;
        }
        frames++;

        // Report frames per second and memory use every 5 seconds
        uint64_t now = time_us_64();
        if (now - last_report >= 5000000) {
            printf("%lu fps, %u cells in use, %lu collections\n",
                   (unsigned long) (frames / 5), (unsigned) vm.cells_used,
                   (unsigned long) vm.gc_count);
            frames = 0;
            last_report = now;
        }

        // Wait for the next frame. If a frame took too long, start
        // counting again from now rather than trying to catch up.
        next_frame = delayed_by_us(next_frame, FRAME_US);
        if (time_reached(next_frame)) {
            next_frame = get_absolute_time();
        } else {
            sleep_until(next_frame);
        }
    }

    show_message("Game stopped", COLOR_YELLOW, "");
}

static void core1_main(void) {
    if (init_hardware()) {
        run_game();
    }
    while (true) {
        tight_loop_contents();
    }
}

int main(void) {
    stdio_init_all();
    sleep_ms(2000);  // Time to open the USB serial console
    printf("\nPicoLisp game system\n");

    multicore_launch_core1_with_stack(core1_main, lisp_stack, sizeof(lisp_stack));

    // Core 0 has nothing else to do; USB serial is served by interrupts
    while (true) {
        sleep_ms(1000);
    }
}
