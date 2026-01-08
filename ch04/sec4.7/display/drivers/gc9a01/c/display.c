#include "gc9a01.h"
#include "pico/stdlib.h"
#include "hardware/spi.h"


/*  Pin configuration (adjust if needed)  */

#define PIN_SCK   18
#define PIN_MOSI  19
#define PIN_CS    17
#define PIN_DC    16
#define PIN_RST   20

#define SPI_PORT  spi0
#define SPI_BAUD  62500000


/*  GC9A01 commands  */

#define CMD_SWRESET   0x01
#define CMD_SLPIN     0x10
#define CMD_SLPOUT    0x11
#define CMD_INVOFF    0x20
#define CMD_INVON     0x21
#define CMD_DISPON    0x29
#define CMD_CASET     0x2A
#define CMD_RASET     0x2B
#define CMD_RAMWR     0x2C
#define CMD_MADCTL    0x36
#define CMD_COLMOD    0x3A
#define CMD_VSCRDEF   0x33
#define CMD_VSCRSADD  0x37

static bool circle_clip = true;


/*  Low-level SPI helpers  */

static inline void cs(bool v)  { gpio_put(PIN_CS, v); }
static inline void dc(bool v)  { gpio_put(PIN_DC, v); }

static void write_cmd(uint8_t c) {
    dc(0); cs(0);
    spi_write_blocking(SPI_PORT, &c, 1);
    cs(1);
}

static void write_data(const uint8_t *d, int len) {
    dc(1); cs(0);
    spi_write_blocking(SPI_PORT, d, len);
    cs(1);
}

static void write_u16(uint16_t v) {
    uint8_t b[2] = { v >> 8, v & 0xFF };
    write_data(b, 2);
}


/*  Init  */

void gc9a01_reset(void) {
    gpio_put(PIN_RST, 0);
    sleep_ms(20);
    gpio_put(PIN_RST, 1);
    sleep_ms(150);
}

void gc9a01_init(void) {
    spi_init(SPI_PORT, SPI_BAUD);
    gpio_set_function(PIN_SCK,  GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);

    gpio_init(PIN_CS);  gpio_set_dir(PIN_CS,  GPIO_OUT);
    gpio_init(PIN_DC);  gpio_set_dir(PIN_DC,  GPIO_OUT);
    gpio_init(PIN_RST); gpio_set_dir(PIN_RST, GPIO_OUT);

    cs(1); dc(1);

    gc9a01_reset();

    write_cmd(CMD_SWRESET);
    sleep_ms(150);

    write_cmd(CMD_COLMOD);
    uint8_t fmt = 0x55;   /* RGB565 */
    write_data(&fmt, 1);

    write_cmd(CMD_MADCTL);
    uint8_t mad = 0x00;
    write_data(&mad, 1);

    write_cmd(CMD_SLPOUT);
    sleep_ms(120);

    write_cmd(CMD_DISPON);
    sleep_ms(20);
}


/*  Addressing  */

void gc9a01_set_window(int x0, int y0, int x1, int y1) {
    write_cmd(CMD_CASET);
    write_u16(x0);
    write_u16(x1);

    write_cmd(CMD_RASET);
    write_u16(y0);
    write_u16(y1);

    write_cmd(CMD_RAMWR);
}


/*  Pixel I/O  */

void gc9a01_write_pixels(const uint16_t *data, int count) {
    dc(1); cs(0);
    spi_write_blocking(SPI_PORT, (const uint8_t *)data, count * 2);
    cs(1);
}


/*  Drawing  */

bool gc9a01_in_circle(int x, int y) {
    int dx = x - GC9A01_RADIUS;
    int dy = y - GC9A01_RADIUS;
    return (dx*dx + dy*dy) <= (GC9A01_RADIUS * GC9A01_RADIUS);
}

void gc9a01_circle_clip(bool enable) {
    circle_clip = enable;
}

void gc9a01_pixel(int x, int y, colour_t c) {
    if (x < 0 || y < 0 || x >= 240 || y >= 240) return;
    if (circle_clip && !gc9a01_in_circle(x, y)) return;

    gc9a01_set_window(x, y, x, y);
    write_u16(c);
}

void gc9a01_hline(int x, int y, int w, colour_t c) {
    for (int i = 0; i < w; i++)
        gc9a01_pixel(x + i, y, c);
}

void gc9a01_vline(int x, int y, int h, colour_t c) {
    for (int i = 0; i < h; i++)
        gc9a01_pixel(x, y + i, c);
}

void gc9a01_rect(int x, int y, int w, int h, colour_t c) {
    gc9a01_hline(x, y, w, c);
    gc9a01_hline(x, y + h - 1, w, c);
    gc9a01_vline(x, y, h, c);
    gc9a01_vline(x + w - 1, y, h, c);
}

void gc9a01_fill_rect(int x, int y, int w, int h, colour_t c) {
    for (int i = 0; i < h; i++)
        gc9a01_hline(x, y + i, w, c);
}

/* Bresenham's */
void gc9a01_line(int x0, int y0, int x1, int y1, colour_t c) {
    int dx = abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
    int dy = -abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
    int err = dx + dy;

    while (1) {
        gc9a01_pixel(x0, y0, c);
        if (x0 == x1 && y0 == y1) break;
        int e2 = 2 * err;
        if (e2 >= dy) { err += dy; x0 += sx; }
        if (e2 <= dx) { err += dx; y0 += sy; }
    }
}

void gc9a01_clear(colour_t c) {
    gc9a01_set_window(0, 0, 239, 239);
    for (int i = 0; i < 240 * 240; i++)
        write_u16(c);
}


/*  Display features  */

void gc9a01_sleep(bool enable) {
    write_cmd(enable ? CMD_SLPIN : CMD_SLPOUT);
    sleep_ms(120);
}

void gc9a01_invert(bool enable) {
    write_cmd(enable ? CMD_INVON : CMD_INVOFF);
}

void gc9a01_scroll(int offset) {
    write_cmd(CMD_VSCRSADD);
    write_u16(offset);
}

