
## BMP Image

### 1. XXD Conversion for `horse_bmp.h`

The `horse_bmp.h` file contains a C array (`unsigned char horse_bmp[]`) representing a BMP
image as a sequence of bytes, generated using the `xxd` command-line tool. This utility
converts binary files into C-compatible header files, embedding the data as an array for
use in embedded systems like the Raspberry Pi Pico.

#### `xxd` Command
The `horse_bmp.h` file was likely created with:
```bash
xxd -i horse.bmp > horse_bmp.h
```
- *Input*: A 320x240 24-bit BMP file (`horse.bmp`).
- *Output*: A C header file containing:
  ```c
  unsigned char horse_bmp[] = {
      0x42, 0x4d, 0x36, 0x84, 0x03, 0x00, /* ... */
  };
  unsigned int __000_bmp_len = 230454;
  unsigned int horse_bmp_size = 230454;
  ```
  - `0x42, 0x4d` are the BMP signature ("BM" in ASCII).
  - The array includes the 54-byte BMP header and 230,400 bytes of pixel data.
  - `horse_bmp_size` (230,454 bytes) matches the total file size.

#### BMP Header Analysis
The BMP header in `horse_bmp.h` provides critical information:
- *Offset 0x00*: `0x42, 0x4d` → BMP signature ("BM").
- *Offset 0x02*: `0x36, 0x84, 0x03, 0x00` → File size = 230,454 bytes.
- *Offset 0x0A*: `0x36, 0x00, 0x00, 0x00` → Pixel data offset = 54 bytes.
- *Offset 0x12*: `0x40, 0x01, 0x00, 0x00` → Width = 320 pixels.
- *Offset 0x16*: `0x10, 0xff, 0xff, 0xff` → Height = -240 (top-down rows).
- *Offset 0x1C*: `0x18, 0x00` → Bits per pixel = 24 (BGR format).
- *Offset 0x1E*: `0x00, 0x00, 0x00, 0x00` → Compression = 0 (uncompressed).
- *Pixel data size*: 320 × 240 × 3 = 230,400 bytes, plus 54-byte header = 230,454 bytes.

#### Creating `horse_bmp.h`
To recreate `horse_bmp.h`:
1. Obtain a 320x240 24-bit BMP file.
2. Run `xxd -i horse.bmp > horse_bmp.h`.
3. Optionally rename the generated length variable (e.g., `__000_bmp_len` to `horse_bmp_len`) for clarity.


### 2. Original BMP Handling in `main.c`

The original `main.c` manually parsed the BMP data and converted it to RGB565
format for display using `display_blit_full`. Here’s how it worked:

### Code Breakdown
```c
#include "display.h"
#include "horse_bmp.h"
#include "pico/stdlib.h"
#include <stdlib.h>

int main(void) {
    stdio_init_all();
    display_error_t err = display_pack_init();
    if (err != DISPLAY_OK) {
        while (true) {}
    }
    buttons_init();

    uint16_t *pixel_buffer = (uint16_t *)malloc(DISPLAY_WIDTH * DISPLAY_HEIGHT * sizeof(uint16_t));
    if (pixel_buffer == NULL) {
        display_cleanup();
        while (true) {}
    }

    uint8_t *bmp_data = horse_bmp + 54;
    for (uint16_t y = 0; y < DISPLAY_HEIGHT; y++) {
        for (uint16_t x = 0; x < DISPLAY_WIDTH; x++) {
            size_t bmp_idx = (y * DISPLAY_WIDTH + x) * 3;
            uint8_t b = bmp_data[bmp_idx + 0];
            uint8_t g = bmp_data[bmp_idx + 1];
            uint8_t r = bmp_data[bmp_idx + 2];
            uint16_t rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
            pixel_buffer[y * DISPLAY_WIDTH + x] = rgb565;
        }
    }

    err = display_blit_full(pixel_buffer);
    if (err != DISPLAY_OK) {
        // Handle error
    }

    free(pixel_buffer);
    while (true) {
        buttons_update();
        sleep_ms(10);
    }
    display_cleanup();
    return 0;
}
```

#### Key Steps
1. *Initialization*:
   - `stdio_init_all()` for debug output.
   - `display_pack_init()` initializes the ST7789V2 display (320x240, RGB565) via SPI.
   - `buttons_init()` sets up button inputs (optional).

2. *Memory Allocation*:
   - Allocates a 153,600-byte buffer (`320 × 240 × 2`) for RGB565 pixels.
   - Checks for allocation failure due to Pico’s limited SRAM (264KB).

3. *BMP Parsing and Conversion*:
   - Skips the 54-byte BMP header (`horse_bmp + 54`).
   - Reads 3 bytes per pixel (BGR order).
   - Converts to RGB565: `(r & 0xF8) << 8 | (g & 0xFC) << 3 | (b >> 3)`.
   - Stores pixels in `pixel_buffer` in row-major order.

4. *Display*:
   - `display_blit_full` sends the buffer to the display via DMA or SPI.
   - The ST7789V2 interprets RGB565 pixels (e.g., `0x0000` for black, `0xFFFF` for white).

5. *Black-and-White Handling*:
   - The BMP is 24-bit but assumed visually black-and-white (pixels are `0x000000` or `0xFFFFFF`).
   - Black converts to `0x0000`, white to `0xFFFF` in RGB565, preserving the image.


#### Limitations
- *Memory Usage*: The 153,600-byte buffer consumes most of the Pico’s SRAM.
- *Performance*: Pixel-by-pixel conversion is slow for large images.
- *Orientation*: Assumes top-down rows (correct for `horse_bmp.h`’s negative height).



### 3. New `display_draw_bmp` Function in `display.c`

To address the memory and performance issues, a new `display_draw_bmp` function was
added to `display.c`. It parses and renders the BMP directly, using a small row buffer
(640 bytes) instead of a full-frame buffer.


#### Function Code
```c
display_error_t display_draw_bmp(const uint8_t *bmp_data, uint32_t bmp_size) {
    if (!display_initialized) return DISPLAY_ERROR_NOT_INITIALIZED;
    if (!bmp_data || bmp_size < 54) return DISPLAY_ERROR_INVALID_PARAM;

    // Parse BMP header
    if (bmp_data[0] != 'B' || bmp_data[1] != 'M') return DISPLAY_ERROR_INVALID_BMP;
    uint32_t file_size = *(uint32_t *)(bmp_data + 2);
    uint32_t data_offset = *(uint32_t *)(bmp_data + 10);
    uint32_t width = *(uint32_t *)(bmp_data + 18);
    int32_t height = *(int32_t *)(bmp_data + 22);
    uint16_t bpp = *(uint16_t *)(bmp_data + 28);
    uint32_t compression = *(uint32_t *)(bmp_data + 30);

    // Validate BMP format
    if (width != DISPLAY_WIDTH || abs(height) != DISPLAY_HEIGHT || bpp != 24 || compression != 0) {
        return DISPLAY_ERROR_INVALID_BMP;
    }
    if (file_size > bmp_size || data_offset > bmp_size) {
        return DISPLAY_ERROR_INVALID_PARAM;
    }

    // Set display window
    display_error_t result = display_set_window(0, 0, DISPLAY_WIDTH - 1, DISPLAY_HEIGHT - 1);
    if (result != DISPLAY_OK) return result;

    // Prepare for pixel data transfer
    gpio_put(DISPLAY_DC_PIN, 1);
    gpio_put(DISPLAY_CS_PIN, 0);

    // Process pixels in chunks to save memory
    const uint32_t row_size = DISPLAY_WIDTH * 3; // 3 bytes per pixel (BGR)
    uint8_t *pixel_data = (uint8_t *)(bmp_data + data_offset);
    uint16_t row_buffer[DISPLAY_WIDTH]; // Buffer for one row in RGB565

    bool top_down = height < 0;
    uint32_t abs_height = abs(height);

    for (uint32_t y = 0; y < abs_height; y++) {
        // Calculate row index based on BMP orientation
        uint32_t bmp_row = top_down ? y : (abs_height - 1 - y);
        uint8_t *row_data = pixel_data + (bmp_row * row_size);

        // Convert row to RGB565
        for (uint32_t x = 0; x < DISPLAY_WIDTH; x++) {
            uint8_t b = row_data[x * 3 + 0];
            uint8_t g = row_data[x * 3 + 1];
            uint8_t r = row_data[x * 3 + 2];
            row_buffer[x] = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
        }

        // Send row to display
        result = dma_spi_write_buffer((uint8_t *)row_buffer, DISPLAY_WIDTH * 2);
        if (result != DISPLAY_OK) break;
        dma_wait_for_finish();
    }

    gpio_put(DISPLAY_CS_PIN, 1);
    return result;
}
```

#### Key Features
1. *Header Validation*:
   - Checks BMP signature (`"BM"`).
   - Verifies width (320), height (±240), bits per pixel (24), and no compression.
   - Ensures file size and data offset are valid.

2. *Memory Efficiency*:
   - Uses a 640-byte `row_buffer` (320 pixels × 2 bytes) instead of 153,600 bytes.
   - Processes one row at a time, converting BGR to RGB565 and sending via DMA.

3. *Orientation Handling*:
   - Supports top-down (negative height) and bottom-up (positive height) BMPs by
     adjusting the row index: `bmp_row = top_down ? y : (abs_height - 1 - y)`.

4. *Black-and-White Support*:
   - Handles 24-bit BGR pixels, converting black (`0x000000`) to `0x0000` and
     white (`0xFFFFFF`) to `0xFFFF` in RGB565, preserving the image’s appearance.

5. *Error Handling*:
   - Returns `DISPLAY_ERROR_INVALID_BMP` for invalid formats.
   - Integrates with existing DMA and SPI functions for reliable transfer.

#### Benefits
- *Reduced Memory*: Uses only 640 bytes vs. 153,600 bytes in the original `main.c`.
- *Simplified `main.c`*: Moves complex parsing logic to `display.c`.
- *Robustness*: Validates BMP format and handles both row orientations.



### 4. Updated `main.c` with `display_draw_bmp`

The updated `main.c` uses `display_draw_bmp` for simplicity:
```c
#include "display.h"
#include "horse_bmp.h"
#include "pico/stdlib.h"

int main(void) {
    stdio_init_all();
    display_error_t err = display_pack_init();
    if (err != DISPLAY_OK) {
        while (true) {}
    }
    buttons_init();
    err = display_draw_bmp(horse_bmp, horse_bmp_size);
    if (err != DISPLAY_OK) {
        while (true) {}
    }
    while (true) {
        buttons_update();
        sleep_ms(10);
    }
    display_cleanup();
    return 0;
}
```

- Calls `display_draw_bmp(horse_bmp, horse_bmp_size)` to render the image.
- Eliminates `malloc`, `free`, and manual pixel conversion.
- Retains button updates for potential interactivity.


### 5. Implementation Notes

#### Hardware Context
- *Display*: ST7789V2, 320x240, RGB565 format, connected via SPI.
- *Pico SRAM*: 264KB, limiting large buffers. The new `display_draw_bmp` uses minimal memory.
- *DMA*: Used for efficient pixel transfer, with fallback to blocking SPI if DMA fails.

#### Black-and-White BMP
- The BMP is 24-bit but assumed visually black-and-white (pixels are `0x000000` or `0xFFFFFF`).
- Both original and new approaches convert these to `0x0000` (black) and `0xFFFF` (white) in RGB565.

#### Alternative: Pre-Converted RGB565
To further optimize, the BMP can be pre-converted to RGB565 using a Python script:
```python
import struct
with open('horse.bmp', 'rb') as f:
    bmp = f.read()
width = struct.unpack('<I', bmp[18:22])[0]
height = abs(struct.unpack('<i', bmp[22:26])[0])
pixel_data = bmp[54:]
rgb565 = []
for y in range(height):
    for x in range(width):
        idx = (y * width + x) * 3
        b, g, r = pixel_data[idx:idx+3]
        rgb565_pixel = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        rgb565.append(rgb565_pixel)
with open('horse_rgb565.h', 'w') as f:
    f.write('unsigned short horse_rgb565[] = {\n')
    for i, pixel in enumerate(rgb565):
        f.write(f'0x{pixel:04x}, ')
        if (i + 1) % 16 == 0:
            f.write('\n')
    f.write('\n};\n')
    f.write(f'unsigned int horse_rgb565_len = {len(rgb565)};\n')
```
Then, use `display_blit_full(horse_rgb565)` in `main.c`, bypassing conversion.


### 6. CMakeLists.txt
Ensure the project builds with:
```cmake
cmake_minimum_required(VERSION 3.13)
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)
project(horse C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()
add_executable(horse
    main.c
    display.c
)
target_include_directories(horse PRIVATE ${CMAKE_CURRENT_LIST_DIR})
target_link_libraries(horse
    pico_stdlib
    hardware_spi
    hardware_dma
    hardware_gpio
    hardware_timer
)
pico_add_extra_outputs(horse)
```


### Conclusion

The `xxd` conversion embeds the BMP as a C array, suitable for the Pico. The
original `main.c` (see [drivers](./../../../drivers/)) parsed and converted
the BMP to RGB565, but used significant memory. The new `display_draw_bmp`
function in `display.c` optimizes memory usage and simplifies `main.c`,
while robustly handling 24-bit BMPs, including black-and-white images.
Pre-converting to RGB565 is an option for further performance gains.

