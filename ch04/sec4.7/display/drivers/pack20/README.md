
## Three Projects

These projects presupposes a larger memory as you can find in *Raspberry Pi Pico 2 W*.
We also use the larger *Pimironi Display Pack 2.0*.


### Project 1: Enhancing the Display Driver API for Buffered Rendering Efficiency

Start by refactoring the existing display driver in `display.c` and `display.h`
to emphasise a more robust API focused on buffered rendering. The current implementation
already has a `display_blit_full` function in the updated version, but extend it
to support *partial blits* and *double-buffering* to reduce flicker and improve
performance for dynamic content.

Key changes:
- Add new API functions like
  `display_blit_partial(uint16_t x, uint16_t y, uint16_t width, uint16_t height, const uint16_t *pixels)`.
  for targeted updates, which would calculate the window offsets internally and
  use DMA only for the affected region.
- Introduce a double-buffer system: Maintain two frame buffers in memory, with API
  calls like `display_get_active_buffer()` and `display_swap_buffers()` to allow
  drawing to one while blitting the other.
- Optimise the DMA handling by adding error recovery in `dma_spi_write_buffer` to
  retry on timeouts, and expose a `display_get_dma_status()` in the API for
  applications to query busy states without blocking.

This project would differ by focusing on memory efficiency and real-time rendering,
testing it with a simple animation loop in `main.c` (e.g., moving a sprite across
the screen) instead of a full game. Measure performance improvements using
`get_time_ms()` to log frame rates, ensuring the driver remains hardware-agnostic
while hiding SPI/DMA complexities behind the API.


### Project 2: Expanding the Button Driver API for Advanced Input Handling

For this one, build on the button handling in `display.c` and `display.h`, treating
it as a standalone input driver with an enhanced API that supports more complex
interactions like long presses, combinations, and event queuing. The current setup
is very basic with callbacks, so make it more versatile for applications beyond
simple presses.

Key changes:
- Extend the API with functions like
  `button_register_long_press(button_t button, uint32_t duration_ms, button_callback_t callback)`
  to detect holds, using internal timers based on `get_time_ms()`.
- Add support for button combinations via a new
  `button_set_combo_callback(uint8_t button_mask, button_callback_t callback)`, where
  `button_mask` is a bitfield (e.g., BUTTON_A | BUTTON_B).
- Implement an event queue: Introduce `button_event_t` struct and functions like
  `button_poll_event(button_event_t *event)` for non-callback polling, useful
  in main loops to avoid interrupt-heavy designs.

This approach would differ by prioritising input modularity, decoupling it further from the display
driver (perhaps splitting into a separate `buttons.h/c` file). Test it by modifying `main.c` to
create a menu system where buttons navigate options and combos trigger actions, like toggling
backlight or resetting the display, emphasising API usability for embedded UI development.


### Project 3: Integrating Graphics Primitives into the Display API for High-Level Drawing

Evolve the display API in `display.h` and `display.c` into a graphics library layer on top of the
low-level driver, adding primitive drawing functions to make it easier for applications to create
complex visuals without manual pixel manipulation. The existing font and rect functions are a
start, but standardise them and please add more.

Key changes:
- Add API primitives like
  `display_draw_line(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2, uint16_t color)` using
  Bresenham's algorithm, and
  `display_draw_circle(uint16_t x, uint16_t y, uint16_t radius, uint16_t color, bool filled)`
  with midpoint circle algorithm, all with bounds checking.
- Enhance text rendering: Introduce `display_set_font_size(uint8_t size)` for scaled fonts
  (e.g., 1x or 2x via pixel doubling) and
  `display_measure_string(const char* str, uint16_t *width, uint16_t *height)` for layout planning.
- Integrate with the frame buffer: Make all primitives optionally target a user-provided buffer
  via `display_set_target_buffer(uint16_t *buffer)`, allowing off-screen rendering before blitting.

This project would stand out by focusing on abstraction for graphics acceleration, using the Breakout
game in the updated `main.c` as a testbed--replacing buffer_fill_rect and buffer_draw_string with the
new API calls for cleaner code. Benchmark against the original to ensure no performance loss,
positioning the driver as a foundation for more advanced projects like simple GUIs or data visualisations.

