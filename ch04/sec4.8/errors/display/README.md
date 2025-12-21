
## Pimoroni Display Pack 2.0 Driver

A more complete, production-ready driver for the *Pimoroni Display Pack 2.0*
(ST7789 320x240 IPS LCD with 4 tactile buttons) on the *Raspberry Pi Pico 2*
using the C/C++ SDK.

Designed with *zero silent failures* in mind: every public function returns
detailed error codes, validates parameters, and gracefully degrades when
hardware resources are unavailable.

- *320x240 landscape mode* with 16-bit RGB565 color
- *High-speed DMA transfers* (~40ms full-screen updates)
- *Automatic fallback* to blocking SPI if DMA unavailable
- *Framebuffer mode* for flicker-free, double-buffered rendering
- *Bounds-checked drawing primitives* (pixels, rectangles, text)
- *Complete 5x8 bitmap font* (ASCII 32-127)
- *4-button support* with debouncing, edge detection, and callbacks
- *Rich error system* with function/line/message context
- *State protection* prevents double-init and use-after-free



## File Structure

| File | Purpose |
|------|---------|
| `display.h` | Public API, types, error codes, color constants |
| `display.c` | Full implementation (SPI, DMA, drawing, buttons) |
| `main.c` | Interactive demo showcasing bouncing ball, plasma, starfield |
| `CMakeLists.txt` | Build configuration for Pico SDK |



## Quick Start

```c
#include "display.h"
#include "pico/stdlib.h"

int main() {
    stdio_init_all();

    // Init with default config (DMA enabled, max speed)
    if (disp_init(NULL) != DISP_OK) {
        printf("Display init failed: %s\n", 
               disp_error_string(disp_get_last_error().code));
        return -1;
    }

    // Draw something
    disp_clear(COLOR_BLACK);
    disp_draw_text(50, 100, "Hello Pico!", COLOR_WHITE, COLOR_BLACK);

    // Init buttons
    buttons_init();
    
    while (1) {
        buttons_update();
        
        if (button_just_pressed(BUTTON_A)) {
            printf("Button A pressed!\n");
        }
        
        sleep_ms(10);
    }
}
```



## Core API

### Init

```c
disp_config_t disp_get_default_config(void);
disp_error_t  disp_init(const disp_config_t *cfg);
disp_error_t  disp_deinit(void);
bool          disp_is_initialized(void);
```

*Default config:*
- SPI baudrate: 62.5 MHz (maximum speed)
- DMA enabled
- Backlight on

### Direct Drawing (immediate mode)

```c
disp_error_t disp_clear(uint16_t color);
disp_error_t disp_fill_rect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint16_t color);
disp_error_t disp_draw_pixel(uint16_t x, uint16_t y, uint16_t color);
disp_error_t disp_blit(uint16_t x, uint16_t y, uint16_t w, uint16_t h, const uint16_t *pixels);
disp_error_t disp_draw_char(uint16_t x, uint16_t y, char c, uint16_t fg, uint16_t bg);
disp_error_t disp_draw_text(uint16_t x, uint16_t y, const char *txt, uint16_t fg, uint16_t bg);
```

### Framebuffer Mode (double-buffered, flicker-free)

```c
disp_error_t disp_framebuffer_alloc(void);              // Allocate 320x240x2 bytes
void         disp_framebuffer_free(void);
uint16_t*    disp_get_framebuffer(void);                // Direct pixel access
disp_error_t disp_framebuffer_clear(uint16_t color);
void         disp_framebuffer_set_pixel(uint16_t x, uint16_t y, uint16_t color);
void         disp_framebuffer_fill_rect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint16_t color);
void         disp_framebuffer_draw_char(uint16_t x, uint16_t y, char c, uint16_t fg, uint16_t bg);
void         disp_framebuffer_draw_text(uint16_t x, uint16_t y, const char *txt, uint16_t fg, uint16_t bg);
disp_error_t disp_framebuffer_flush(void);              // Send to display (DMA)
```

*Usage pattern:*
```c
disp_framebuffer_alloc();

while (game_running) {
    disp_framebuffer_clear(COLOR_BLACK);
    // Draw everything to framebuffer...
    disp_framebuffer_flush();  // Single DMA transfer
    sleep_ms(16);  // ~60 FPS
}

disp_framebuffer_free();
```

### Buttons (A, B, X, Y)

```c
disp_error_t buttons_init(void);
void         buttons_update(void);                       // Call in main loop
bool         button_pressed(button_t b);                 // Currently held?
bool         button_just_pressed(button_t b);            // Edge: just pressed
bool         button_just_released(button_t b);           // Edge: just released
disp_error_t button_set_callback(button_t b, button_callback_t cb);
```

*Button enum:* `BUTTON_A`, `BUTTON_B`, `BUTTON_X`, `BUTTON_Y`

Buttons are *debounced* (50ms) and provide clean edge detection.

### Control

```c
disp_error_t disp_set_backlight(bool on);
disp_error_t disp_wait_complete(uint32_t timeout_ms);   // Wait for DMA
```



### Error Handling

Every function returns `disp_error_t`. On failure:

```c
disp_error_t err = disp_some_function(...);
if (err != DISP_OK) {
    disp_error_context_t ctx = disp_get_last_error();
    printf("ERROR %d (%s) in %s():%d - %s\n",
           err,
           disp_error_string(err),
           ctx.function, ctx.line,
           ctx.message ? ctx.message : "no details");
}
```

*Convenience macro:*

```c
#define CHECK(call) do {                                    \
    disp_error_t e = (call);                                \
    if (e != DISP_OK) {                                     \
        disp_error_context_t ctx = disp_get_last_error();   \
        printf("FAIL %s:%d → %s (%s)\n",                    \
               ctx.function, ctx.line,                      \
               disp_error_string(e), ctx.message);          \
        return e;                                           \
    }                                                       \
} while(0)
```

*Error codes:*
- `DISP_OK` - Success
- `DISP_ERR_ALREADY_INIT` - Already initialized
- `DISP_ERR_NOT_INIT` - Not initialized
- `DISP_ERR_NULL_POINTER` - NULL pointer passed
- `DISP_ERR_INVALID_COORDS` - Coordinates out of bounds
- `DISP_ERR_DMA_NOT_AVAILABLE` - No DMA channel available
- `DISP_ERR_DMA_TIMEOUT` - DMA transfer timeout
- (see `display.h` for complete list)



### Performance

| Operation | DMA enabled | DMA disabled |
|-----------|-------------|--------------|
| Full-screen clear | ~40 ms | ~200 ms |
| 80x80 blit | ~6 ms | ~25 ms |
| Framebuffer flush (320x240) | ~40 ms | ~200 ms |
| Text character (5x8) | ~1-2 ms | unchanged |

*Tip:* Use framebuffer mode for animations and games to avoid flicker and maximize throughput.



### Demo

The `main.c` provides three interactive demos:

1. *Bouncing Ball* - Smooth physics with rainbow colors
2. *Plasma Effect* - Real-time mathematical visualization
3. *Starfield* - 3D parallax star simulation

Press *A*, *B*, or *X* to select a demo. Press any button to return to menu.

All demos use framebuffer mode for *60 FPS, flicker-free* rendering.



### Pin Configuration

Pimoroni Display Pack 2.0 standard pinout:

| Function | GPIO |
|----------|------|
| SPI CLK | 18 |
| SPI MOSI | 19 |
| CS | 17 |
| DC (Data/Command) | 16 |
| RESET | 21 |
| Backlight | 20 |
| Button A | 12 |
| Button B | 13 |
| Button X | 14 |
| Button Y | 15 |



### Color Constants

RGB565 format (5 bits red, 6 bits green, 5 bits blue):

```c
COLOR_BLACK, COLOR_WHITE, COLOR_RED, COLOR_GREEN,
COLOR_BLUE, COLOR_YELLOW, COLOR_CYAN, COLOR_MAGENTA
```

*Custom colors:*
```c
// R: 0-31, G: 0-63, B: 0-31
uint16_t color = (r << 11) | (g << 5) | b;
```




### Graceful DMA Fallback

```c
disp_config_t cfg = disp_get_default_config();
cfg.use_dma = true;

if (disp_init(&cfg) != DISP_OK) {
    printf("DMA unavailable - falling back to blocking SPI\n");
    cfg.use_dma = false;
    disp_init(&cfg);  // Should succeed
}
```

### Custom Configuration

```c
disp_config_t cfg = {
    .spi_baudrate = 40000000,   // 40 MHz (slower, more stable)
    .use_dma = false,           // Disable DMA
    .dma_timeout_ms = 500,      // Timeout (if DMA enabled)
    .enable_backlight = true    // Backlight on at init
};

disp_init(&cfg);
```

### Button Callbacks

```c
void on_button_a(button_t btn) {
    printf("Button A callback!\n");
}

buttons_init();
button_set_callback(BUTTON_A, on_button_a);

while (1) {
    buttons_update();  // Fires callback on press
    sleep_ms(10);
}
```

### Extending

When extending this driver:

- Always return `disp_error_t` from public functions
- Use `DISP_ERROR(code, "message")` macro to set context
- Validate all pointers, coordinates, and state
- Add new error codes to `disp_error_t` enum and `err_str[]` array
- Test both DMA-enabled and DMA-disabled modes

