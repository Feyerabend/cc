
## Simple Text Editor

A minimalist text editor running on the Raspberry Pi Pico with Pimoroni Display
Pack 2.0, featuring keyboard input via USB serial, visual cursor, real-time editing,
and hardware button controls.


- *Live Text Editing* - Type and edit text in real-time
- *Visual Cursor* - Blinking cursor shows current position
- *USB Keyboard Input* - Full keyboard support via USB serial
- *Hardware Button Controls* - Quick access debug and clear functions
- *Multi-line Support* - Automatic line wrapping with newline handling
- *Status Bar* - Real-time display of cursor position and buffer stats
- *Error Recovery* - Automatic display health checks and recovery
- *Compact Memory* - Only 512 bytes text buffer, minimal RAM usage


- Raspberry Pi Pico (or compatible RP2040 board)
- Pimoroni Display Pack 2.0 (320×240 LCD with buttons)
- USB connection to computer (for keyboard input)
- Pico SDK installed and configured


### Editor Controls

Keyboard (via USB Serial):
| Key | Function |
|-----|----------|
| *Any printable character* | Insert at cursor position |
| *Backspace / Delete* | Delete character before cursor |
| *Enter / Return* | Insert newline |
| *Left Arrow* | Move cursor left |
| *Right Arrow* | Move cursor right |

Hardware Buttons:
| Button | Function |
|--------|----------|
| *Button A* | Show debug information (position, length, errors) |
| *Button B* | Clear all text (reset editor) |


Display Layout:
```
┌────────────────────────────────────┐
│ EDITOR                             │  ← Title bar (red)
├────────────────────────────────────┤
│                                    │
│  Your text appears here...         │  ← Text area
│  Multiple lines supported          │    (29 lines × 53 chars)
│  Cursor shows position: █          │
│                                    │
├────────────────────────────────────┤
│ P:42 L:156 E:0                     │  ← Status bar (blue)
├────────────────────────────────────┤
│ A:DEBUG B:CLEAR - TYPE TEXT ABOVE  │  ← Help text (green)
└────────────────────────────────────┘
```

*Status Bar Fields:*
- `P:` - Cursor position in buffer
- `L:` - Total text length (characters)
- `E:` - Error count (display failures)


### Installation

__1. Copy Files__
Add these files to your Pico project:
- `display.h` - Display library header
- `display.c` - Display library implementation  
- `main.c` - Text editor code

__2. CMakeLists.txt Configuration__
```cmake
cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(text_editor C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(text_editor
    main.c
    display.c
)

target_link_libraries(text_editor
    pico_stdlib
    hardware_spi
    hardware_dma
    hardware_gpio
    hardware_irq
    hardware_timer
)

# IMPORTANT: Enable USB stdio for keyboard input
pico_enable_stdio_usb(text_editor 1)
pico_enable_stdio_uart(text_editor 0)

pico_add_extra_outputs(text_editor)
```

__3. Build and Flash__
```bash
mkdir build
cd build
cmake ..
make
# Copy text_editor.uf2 to your Pico in BOOTSEL mode
```

__4. Connect Serial Terminal__
After flashing, connect with a serial terminal program:

*Linux/Mac:*
```bash
screen /dev/ttyACM0 115200
# or
minicom -D /dev/ttyACM0 -b 115200
```

*Windows:*
- Use PuTTY, TeraTerm, or Windows Terminal
- Connect to the Pico's COM port at 115200 baud

*Exit screen:* Press `Ctrl-A` then `K` then `Y`


### Usage

1. *Connect* - Plug Pico into computer via USB
2. *Open Terminal* - Connect serial terminal at 115200 baud
3. *Start Typing* - Characters appear on both screen and display
4. *Navigate* - Use arrow keys to move cursor
5. *Edit* - Backspace to delete, Enter for new lines
6. *Debug* - Press Button A on display to see buffer stats
7. *Clear* - Press Button B to start fresh


### Code Architecture


The editor uses static buffers for maximum stability:

```c
static char text_buffer[TEXT_BUFFER_SIZE];       // 512 bytes - main text
static char display_line[SCREEN_CHARS_WIDTH + 1]; // 54 bytes - temp line buffer
static uint16_t text_length;                      // Current text length
static uint16_t cursor_pos;                       // Cursor position (0 to length)
```

Total text capacity: *512 characters* (approximately 8-10 lines of text)


__Text Buffer Management__

*Insertion Algorithm:*
```c
void insert_char(char c) {
    // Shift text right from cursor position
    for (uint16_t i = text_length; i > cursor_pos; i--) {
        text_buffer[i] = text_buffer[i - 1];
    }
    text_buffer[cursor_pos] = c;  // Insert new character
    cursor_pos++;                  // Advance cursor
    text_length++;                 // Update length
}
```

*Deletion Algorithm:*
```c
void delete_char(void) {
    cursor_pos--;  // Move cursor back
    // Shift text left from cursor position
    for (uint16_t i = cursor_pos; i < text_length - 1; i++) {
        text_buffer[i] = text_buffer[i + 1];
    }
    text_length--;  // Update length
}
```

### Rendering System

The editor uses *direct character rendering* rather than frame buffers:

1. *Clear screen* - Fill entire display with black
2. *Draw title* - Static "EDITOR" text in red
3. *Draw text* - Character-by-character from buffer
4. *Draw cursor* - White rectangle at cursor position
5. *Draw status* - Blue bar with position info
6. *Draw help* - Green instruction text

Each frame takes approximately 50-100ms due to character-by-character drawing.


### Character Mapping

The display font only supports uppercase letters.
Lowercase input is automatically converted:

```c
char display_char = (c >= 'a' && c <= 'z') ? (c - 32) : c;
```

*Supported characters:* Space (32) through 'Z' (90)


### Cursor Blinking

Cursor toggles visibility every 1000ms (1 second):

```c
if (now - last_blink > CURSOR_BLINK_MS) {
    cursor_visible = !cursor_visible;
    last_blink = now;
    needs_redraw = true;
}
```


### Display Health Monitoring

The editor includes automatic display health checks and recovery:

```c
// Check every 5 seconds
if (!display_is_initialized()) {
    display_pack_init();  // Attempt recovery
}

// After 10 consecutive errors, full reset
if (error_count > 10) {
    display_cleanup();
    display_pack_init();
    error_count = 0;
}
```

### Customisation

__Buffer Size__
Increase text capacity by modifying `TEXT_BUFFER_SIZE`:

```c
#define TEXT_BUFFER_SIZE 1024  // Double capacity to 1KB
```

*Warning:* Larger buffers increase memory usage and may slow down rendering.

__Cursor Blink Speed__
Change blink interval in milliseconds:

```c
#define CURSOR_BLINK_MS 500   // Faster blink (0.5 seconds)
#define CURSOR_BLINK_MS 2000  // Slower blink (2 seconds)
```

__Display Layout__
Adjust the text area size:

```c
#define TEXT_LINES (SCREEN_LINES - 3)  // Lines for text
// Decrease to -4 for more status space
// Increase to -2 for more text space
```

__Loop Speed__
Change the main loop delay:

```c
sleep_ms(50);   // Default: 50ms (20 updates/sec)
sleep_ms(20);   // Faster: 20ms (50 updates/sec)
sleep_ms(100);  // Slower: 100ms (10 updates/sec)
```


### Performance Characteristics

Rendering Speed:
- *Clear screen:* ~10ms
- *Character drawing:* ~1ms per character
- *Full redraw:* 50-100ms (depends on text length)
- *Update frequency:* ~20 times per second

Memory Usage:
- *Text buffer:* 512 bytes
- *Display line buffer:* 54 bytes
- *Stack/heap:* <100 bytes
- *Total:* ~700 bytes (0.3% of Pico's 264KB RAM)

Input Latency:
- *Keyboard to buffer:* <1ms
- *Buffer to display:* 50-100ms (next render cycle)
- *Total perceived latency:* 50-150ms


### Extend

Add Syntax Highlighting:
```c
typedef enum {
    COLOR_NORMAL = COLOR_WHITE,
    COLOR_KEYWORD = COLOR_CYAN,
    COLOR_NUMBER = COLOR_YELLOW,
    COLOR_COMMENT = COLOR_GREEN
} syntax_color_t;

syntax_color_t get_char_color(char c, uint16_t pos) {
    // Implement simple syntax detection
    if (c >= '0' && c <= '9') return COLOR_NUMBER;
    // Add keyword detection, etc.
    return COLOR_NORMAL;
}
```

Add File Operations:
Using Pico's flash memory:

```c
#include "hardware/flash.h"

#define FLASH_TARGET_OFFSET (256 * 1024)

void save_to_flash(void) {
    uint32_t ints = save_and_disable_interrupts();
    flash_range_erase(FLASH_TARGET_OFFSET, FLASH_SECTOR_SIZE);
    flash_range_program(FLASH_TARGET_OFFSET, text_buffer, TEXT_BUFFER_SIZE);
    restore_interrupts(ints);
}

void load_from_flash(void) {
    const uint8_t *flash_data = (const uint8_t *)(XIP_BASE + FLASH_TARGET_OFFSET);
    memcpy(text_buffer, flash_data, TEXT_BUFFER_SIZE);
}
```

Add Search Function:
```c
uint16_t search_text(const char *query) {
    size_t query_len = strlen(query);
    for (uint16_t i = 0; i <= text_length - query_len; i++) {
        if (strncmp(&text_buffer[i], query, query_len) == 0) {
            return i;  // Found at position i
        }
    }
    return 0xFFFF;  // Not found
}
```

Add Copy/Paste Buffer:
```c
static char clipboard[128];
static uint16_t clipboard_len = 0;
static uint16_t selection_start = 0;
static uint16_t selection_end = 0;

void copy_selection(void) {
    clipboard_len = selection_end - selection_start;
    memcpy(clipboard, &text_buffer[selection_start], clipboard_len);
}

void paste_clipboard(void) {
    // Insert clipboard contents at cursor
    for (uint16_t i = 0; i < clipboard_len; i++) {
        insert_char(clipboard[i]);
    }
}
```


### Troubleshooting

*No text appears on display:*
- Check USB serial connection is working (you should see debug output)
- Verify display initialization succeeded (check serial output)
- Press Button A to see debug info including error count
- Try Button B to clear and reset

*Characters not appearing:*
- Ensure terminal is sending at 115200 baud
- Check that characters are printable (32-126 ASCII range)
- Verify buffer isn't full (max 512 characters)
- Look for "Display OK" message in serial output

*Cursor doesn't move:*
- Arrow keys require ANSI escape sequence support
- Some terminals may need configuration to send these sequences
- Try typing characters first to verify basic functionality works

*Display freezes or shows garbage:*
- Check `E:` count in status bar (error counter)
- High error counts indicate display problems
- Editor will attempt automatic recovery after 10 errors
- Try power cycling the Pico if recovery fails

*Button A/B don't work:*
- Verify "Buttons OK" message appears in serial output
- Check physical connections to GPIO pins 12-15
- Buttons require `buttons_update()` to be called regularly

*Text corrupted after editing:*
- Buffer overflow - stay under 512 character limit
- Check debug output with Button A to see buffer state
- Use Button B to clear and start fresh


### Limitations

- *Maximum text:* 512 characters (~8-10 lines)
- *Font:* Uppercase only, ASCII 32-90
- *No undo/redo:* Changes are permanent
- *No file persistence:* Text lost on reset (unless you add flash storage)
- *Single screen:* No scrolling, text wraps to visible area
- *Basic navigation:* Only left/right cursor movement (no up/down)
- *Slow rendering:* Character-by-character drawing (50-100ms full redraw)


### Improvements / Projects

Potential enhancements for advanced users:

1. *Scrolling* - View text beyond visible area
2. *Multiple buffers* - Switch between different text documents
3. *Line numbers* - Show line numbers in margin
4. *Word wrap* - Intelligent wrapping at word boundaries
5. *Command mode* - Vi-like command interface using Button Y
6. *File browser* - Navigate and load files from flash
7. *Clipboard history* - Remember multiple copy operations
8. *Syntax templates* - Quick insertion of common code patterns


### Technical Details

__Input Processing__
The editor uses non-blocking keyboard input:

```c
int c = getchar_timeout_us(0);  // Returns immediately
if (c == PICO_ERROR_TIMEOUT) return;  // No character available
```

__ANSI Escape Sequences__
Arrow keys send escape sequences:
- *Left:* `ESC [ D` (0x1B 0x5B 0x44)
- *Right:* `ESC [ C` (0x1B 0x5B 0x43)

The editor parses these three-character sequences to detect navigation keys.

__Display Protocol__
Each character requires multiple SPI transactions:
1. Set cursor position (window command)
2. Draw character pixels (5×8 bitmap, 40 pixels)

For a full screen of text (~500 characters):
- 500 chars × 41 pixels each = 20,500 pixel operations
- At 31.25 MHz SPI = ~50ms total


![Text Editor](./../../../../../assets/image/display/editor_dp2.png)

