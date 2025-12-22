
### Creating APIs for Low-Level Drivers: A General Guide

APIs (Application Programming Interfaces) for drivers provide a clean, user-friendly
layer atop the raw hardware interactions. They turn complex, error-prone low-level code
(like register pokes or SPI transactions) into simple, intuitive functions. This is
especially useful in embedded systems like the Raspberry Pi Pico, where you want to
reuse driver code across projects without exposing every hardware quirk.

In general, good APIs follow principles like
*simplicity* (easy to learn/use),
*abstraction* (hide implementation details),
*extensibility* (easy to add features), and
*performance* (minimal overhead).
They can be synchronous (blocking calls) or asynchronous (event-driven, e.g.,
via callbacks or interrupts). For drivers, APIs often include initialisation,
configuration, core operations (read/write), and cleanup.


#### Why Create APIs for Low-Level Drivers?
- *Usability*: Developers can focus on app logic (e.g., "draw a button")
  instead of "send SPI command 0x2C".
- *Maintainability*: Centralise bug fixes or optimisations in one place.
- *Portability*: Abstract platform differences (e.g., Pico vs. Arduino)
  behind the same interface.
- *Safety*: Enforce bounds-checking or error handling to prevent crashes.
- *Testing*: Easier to mock or unit-test high-level functions.

For the Pico + Pimoroni Display Pack example, a low-level driver handles
ST7789 registers directly, but an API might add methods like `drawPixel(x, y, color)`
or `fillRect(x1, y1, x2, y2, color)` for graphics primitives.


#### General Steps to Design and Implement Driver APIs

Here's a structured approach, applicable to any platform (e.g., C/C++ for Pico,
Python for MicroPython, or even Rust).

1. *Define the Interface (What the User Sees)*:
   - Identify core operations from the hardware's perspective (init, config, I/O, shutdown).
   - Use descriptive names and group related functions (e.g., in a struct or class).
   - Consider parameters: Keep them intuitive (e.g., `color` as RGB565 int, not raw bytes).
   - Handle errors gracefully (return codes, enums, or exceptions).

   Example Interface Sketch (in C for Pico):
   ```c
   typedef struct {
       void (*init)(void);              // Init hardware
       void (*deinit)(void);            // Cleanup
       void (*clear)(uint16_t color);   // Fill screen with colour
       void (*drawPixel)(int x, int y, uint16_t color);  // Set single pixel
       void (*drawLine)(int x0, int y0, int x1, int y1, uint16_t color);  // Bresenham or similar
       void (*text)(const char* str, int x, int y, uint16_t fg, uint16_t bg);  // Render text
   } DisplayAPI;
   ```

2. *Implement the Backend (Tie to Low-Level Driver)*:
   - Wrap your low-level functions (from the previous example) inside the API.
   - Add state management (e.g., track screen bounds to clip draws).
   - Optimise where needed (e.g., buffer pixels before flushing to SPI).

3. *Add Utilities and Extensions*:
   - Built-in primitives: Rectangles, circles (using algorithms like Midpoint Circle).
   - Fonts/Bitmaps: Embed simple fonts or load images.
   - Events: For input devices, add polling or interrupt-based reads.

4. *Test and Document*:
   - Unit tests: Verify edge cases (e.g., draw off-screen).
   - Docs: Use Doxygen-style comments or README with examples.
   - Versioning: Use semantic versioning for changes.

5. *Deployment*:
   - Package as a library (e.g., CMake for C, pip for Python).
   - Make it modular: Users can swap backends (e.g., ST7789 vs. ILI9341).


#### Example: Building an API for the Pimoroni Display Pack (ST7789 on Pico)

Let's extend the low-level ST7789 driver from before into a full API in C/C++.
This assumes the Pico SDK setup.

*Step 1: Define the API Structure*
```c
// display_api.h
#ifndef DISPLAY_API_H
#define DISPLAY_API_H

#include "pico/stdlib.h"
#include "hardware/spi.h"

#define SCREEN_WIDTH  240
#define SCREEN_HEIGHT 135
#define COLOR_RGB565(r, g, b) (((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3))  // Convert to 16-bit

typedef enum {
    DISPLAY_OK = 0,
    DISPLAY_ERR_INIT,
    DISPLAY_ERR_BOUNDS
} DisplayError;

typedef struct {
    uint8_t cs_pin, dc_pin, rst_pin;
    spi_inst_t *spi_port;
    bool initialized;
} DisplayHandle;

typedef struct {
    DisplayError (*init)(DisplayHandle *handle);           // Setup
    DisplayError (*deinit)(DisplayHandle *handle);         // Teardown
    DisplayError (*clear)(DisplayHandle *handle, uint16_t color);  // Fill screen
    DisplayError (*drawPixel)(DisplayHandle *handle, int x, int y, uint16_t color);  // Pixel
    DisplayError (*fillRect)(DisplayHandle *handle, int x, int y, int w, int h, uint16_t color);  // Rectangle
    DisplayError (*drawText)(DisplayHandle *handle, const char *text, int x, int y, uint16_t fg, uint16_t bg);  // Simple text (8x8 font)
} DisplayAPI;

// Global instance (or pass handle for multi-display support)
extern DisplayAPI display;

#endif
```

*Step 2: Implement the API (display_api.c)*
This builds on the low-level functions. For brevity, I'll show key parts—full
text rendering would need a font array.

```c
// display_api.c
#include "display_api.h"

// Low-level functions (from previous example)
extern void st7789_command(uint8_t cmd);
extern void st7789_data(const uint8_t *data, size_t len);
extern void st7789_set_window(int x0, int y0, int x1, int y1);  // Helper to set draw area (using 0x2A/0x2B)

// Simple 8x8 font (subset for demo; in reality, use a full bitmap array)
static const uint8_t font8x8[128][8] = {
    // .. (e.g., for 'A': {0x00, 0x18, 0x24, 0x42, 0x7E, 0x42, 0x42, 0x00}, etc.)
    // Omitted for space; generate from tools like fontconvert
};

DisplayAPI display = {0};  // Init to zero

// Low-level init wrapper
static DisplayError st7789_ll_init(DisplayHandle *handle) {
    // Pin setup (hardcoded for Pimoroni)
    handle->cs_pin = 17; handle->dc_pin = 20; handle->rst_pin = 21;
    handle->spi_port = spi0;

    // GPIO init
    gpio_init(handle->cs_pin); gpio_set_dir(handle->cs_pin, GPIO_OUT); gpio_put(handle->cs_pin, 1);
    gpio_init(handle->dc_pin); gpio_set_dir(handle->dc_pin, GPIO_OUT);
    gpio_init(handle->rst_pin); gpio_set_dir(handle->rst_pin, GPIO_OUT);

    // SPI init
    spi_init(handle->spi_port, 10000000);  // 10 MHz
    gpio_set_function(16, GPIO_FUNC_SPI);  // MISO
    gpio_set_function(18, GPIO_FUNC_SPI);  // SCK
    gpio_set_function(19, GPIO_FUNC_SPI);  // MOSI

    // Run ST7789 init sequence
    gpio_put(handle->rst_pin, 0); sleep_ms(10);
    gpio_put(handle->rst_pin, 1); sleep_ms(120);
    st7789_command(0x01); sleep_ms(150);  // Reset
    st7789_command(0x11); sleep_ms(120);  // Sleep out
    st7789_command(0x3A); uint8_t colmod = 0x05; st7789_data(&colmod, 1);  // 16-bit color
    st7789_command(0x36); uint8_t madctl = 0x00; st7789_data(&madctl, 1);  // Orientation
    st7789_command(0x29);  // Display on

    handle->initialized = true;
    return DISPLAY_OK;
}

// API Implementation
DisplayError display_init(DisplayHandle *handle) {
    if (handle->initialized) return DISPLAY_OK;
    return st7789_ll_init(handle);
}

DisplayError display_deinit(DisplayHandle *handle) {
    if (!handle->initialized) return DISPLAY_OK;
    st7789_command(0x28);  // Display off
    spi_deinit(handle->spi_port);
    handle->initialized = false;
    return DISPLAY_OK;
}

DisplayError display_clear(DisplayHandle *handle, uint16_t color) {
    if (!handle->initialized) return DISPLAY_ERR_INIT;
    st7789_set_window(0, 0, SCREEN_WIDTH-1, SCREEN_HEIGHT-1);
    st7789_command(0x2C);  // Memory write
    uint8_t color_bytes[2] = {color >> 8, color & 0xFF};
    for (int i = 0; i < SCREEN_WIDTH * SCREEN_HEIGHT; i++) {
        st7789_data(color_bytes, 2);  // Naive loop; optimise with DMA for speed
    }
    return DISPLAY_OK;
}

DisplayError display_drawPixel(DisplayHandle *handle, int x, int y, uint16_t color) {
    if (!handle->initialized || x < 0 || x >= SCREEN_WIDTH || y < 0 || y >= SCREEN_HEIGHT) {
        return DISPLAY_ERR_BOUNDS;
    }
    st7789_set_window(x, y, x, y);
    st7789_command(0x2C);
    uint8_t color_bytes[2] = {color >> 8, color & 0xFF};
    st7789_data(color_bytes, 2);
    return DISPLAY_OK;
}

DisplayError display_fillRect(DisplayHandle *handle, int x, int y, int w, int h, uint16_t color) {
    if (!handle->initialized || x < 0 || y < 0 || x+w > SCREEN_WIDTH || y+h > SCREEN_HEIGHT) {
        return DISPLAY_ERR_BOUNDS;
    }
    st7789_set_window(x, y, x+w-1, y+h-1);
    st7789_command(0x2C);
    uint8_t color_bytes[2] = {color >> 8, color & 0xFF};
    int pixels = w * h;
    for (int i = 0; i < pixels; i++) {
        st7789_data(color_bytes, 2);
    }
    return DISPLAY_OK;
}

// Simple text: Render char-by-char using font
DisplayError display_drawText(DisplayHandle *handle, const char *text, int x, int y, uint16_t fg, uint16_t bg) {
    if (!handle->initialized) return DISPLAY_ERR_INIT;
    int cx = x;
    while (*text) {
        if (*text >= 32 && *text < 128) {  // Printable ASCII
            const uint8_t *glyph = font8x8[(int)*text];
            for (int gy = 0; gy < 8; gy++) {
                for (int gx = 0; gx < 8; gx++) {
                    uint16_t col = (glyph[gy] & (1 << (7 - gx))) ? fg : bg;
                    display_drawPixel(handle, cx + gx, y + gy, col);
                }
            }
            cx += 8;  // Advance X
        }
        text++;
    }
    return DISPLAY_OK;
}
```

*Step 3: Usage Example (in main.c)*
```c
#include "display_api.h"

DisplayHandle my_display = {0};

int main() {
    stdio_init_all();
    display_init(&my_display);
    
    display_clear(&my_display, COLOR_RGB565(0, 0, 0));  // Black screen
    display_drawText(&my_display, "Hello Pico!", 10, 10, COLOR_RGB565(255, 255, 255), COLOR_RGB565(0, 0, 0));
    display_fillRect(&my_display, 50, 50, 100, 20, COLOR_RGB565(255, 0, 0));  // Red rect
    
    while (true) {
        tight_loop_contents();
    }
    return 0;
}
```

#### Tips for General API Design Across Languages/Platforms
| Aspect | C/C++ (Pico/Embedded) | Python (MicroPython) | Considerations |
|--------|-----------------------|----------------------|----------------|
| *State Management* | Use structs/handles for instances. | Classes with `__init__`. | Avoid globals for thread-safety. |
| *Error Handling* | Return enums/codes. | Raise exceptions. | Log errors for debugging. |
| *Performance* | Inline critical funcs; use DMA. | Avoid loops in hot paths. | Profile with tools like perf or uPy's micropython-meminfo. |
| *Extensibility* | Function pointers in structs. | Inheritance/mixins. | Design for swapping backends (e.g., SPI vs. I2C). |
| *Documentation* | Doxygen comments. | Docstrings + Sphinx. | Include examples and param types. |


#### When to Build APIs vs. Stick to Low-Level
- *Build When*: Reusing code across projects, team collaboration, or adding features like animation/touch support.
- *Skip When*: One-off prototypes or ultra-constrained environments (e.g., <1KB RAM).
- *Evolution*: Start low-level, then layer APIs as complexity grows. Open-source it on GitHub for feedback.

This approach scales to other drivers (e.g., sensors via I2C or motors via PWM).
