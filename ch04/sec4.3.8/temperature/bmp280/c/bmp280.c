#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"

// BMP280 SPI setup
#define SPI_PORT  spi1
#define PIN_CS    8   // GPIO 8  (Physical Pin 11)
#define PIN_SCK   10  // GPIO 10 (Physical Pin 14)
#define PIN_MOSI  11  // GPIO 11 (Physical Pin 15)
#define PIN_MISO  12  // GPIO 12 (Physical Pin 16)

// BMP280 register addresses
#define REG_DIG_T1     0x88
#define REG_CTRL_MEAS  0xF4
#define REG_TEMP       0xFA

static uint16_t dig_T1;
static int16_t dig_T2;
static int16_t dig_T3;

// SPI read/write functions
static void read_reg(uint8_t reg, uint8_t *buf, size_t len) {
    uint8_t addr = reg | 0x80;  // Read mode (MSB=1)
    gpio_put(PIN_CS, 0);        // Select chip
    spi_write_blocking(SPI_PORT, &addr, 1);
    spi_read_blocking(SPI_PORT, 0, buf, len);
    gpio_put(PIN_CS, 1);        // Deselect chip
}

static void write_reg(uint8_t reg, uint8_t data) {
    uint8_t buf[2] = { reg & 0x7F, data };  // Write mode (MSB=0)
    gpio_put(PIN_CS, 0);
    spi_write_blocking(SPI_PORT, buf, 2);
    gpio_put(PIN_CS, 1);
}

// Read an unsigned short (little endian)
static uint16_t read_u16(uint8_t reg) {
    uint8_t d[2];
    read_reg(reg, d, 2);
    return (uint16_t) (d[0] | (d[1] << 8));
}

// Read a signed short
static int16_t read_s16(uint8_t reg) {
    return (int16_t) read_u16(reg);
}

static float read_temperature(void) {
    uint8_t data[3];
    read_reg(REG_TEMP, data, 3);
    int32_t raw = ((int32_t) data[0] << 12) | ((int32_t) data[1] << 4) | (data[2] >> 4);

    // Compensation formula from datasheet
    int32_t var1 = (((raw >> 3) - ((int32_t) dig_T1 << 1)) * (int32_t) dig_T2) >> 11;
    int32_t var2 = (((((raw >> 4) - (int32_t) dig_T1) *
                      ((raw >> 4) - (int32_t) dig_T1)) >> 12) *
                    (int32_t) dig_T3) >> 14;
    int32_t t_fine = var1 + var2;
    int32_t T = (t_fine * 5 + 128) >> 8;
    return T / 100.0f;
}

int main() {
    stdio_init_all();

    // SPI mode 0, 1 MHz
    spi_init(SPI_PORT, 1000 * 1000);
    spi_set_format(SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(PIN_SCK, GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);
    gpio_set_function(PIN_MISO, GPIO_FUNC_SPI);

    gpio_init(PIN_CS);
    gpio_set_dir(PIN_CS, GPIO_OUT);
    gpio_put(PIN_CS, 1);

    // Get calibration data for temperature
    dig_T1 = read_u16(REG_DIG_T1);
    dig_T2 = read_s16(REG_DIG_T1 + 2);
    dig_T3 = read_s16(REG_DIG_T1 + 4);

    // Configure sensor: oversampling x1, normal mode
    write_reg(REG_CTRL_MEAS, 0x27);

    while (true) {
        printf("Temperature: %.2f C\n", read_temperature());
        sleep_ms(1000);
    }
}
