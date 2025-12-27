#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/adc.h"

int main() {
    // init standard I/O (e.g., for printf over USB/UART)
    stdio_init_all();

    // init ADC
    adc_init();
    
    // Select ADC input 4 (onboard temperature sensor)
    // The Raspberry Pi Pico has an onboard temperature sensor connected to ADC input 4.
    // This sensor is not enabled by default, so we need to enable it.
    adc_set_temp_sensor_enabled(true);
    adc_select_input(4);

    // The ADC on the Raspberry Pi Pico has a 12-bit resolution, so it can read values from 0 to 4095. 
    // The Pico SDK uses a 12-bit ADC (0-4095 range) by default, unlike MicroPython's 16-bit read_u16()
    // (0-65535). Thus, the conversion factor is adjusted to 3.3 / 4095.
    const float conversion_factor = 3.3f / 4095;

    while (true) {
        // Read raw temperature sensor value (12-bit, 0-4095)
        uint16_t reading = adc_read();

        // Convert raw value to voltage
        float voltage = reading * conversion_factor;

        // Convert voltage to Celsius based on onboard sensor
        float celsius = 27.0f - (voltage - 0.706f) / 0.001721f;

        // Convert Celsius to Fahrenheit
        float fahrenheit = celsius * 9.0f / 5.0f + 32.0f;

        // Print temperature in both Celsius and Fahrenheit
        printf("Temperature: %.2f C / %.2f F\n", celsius, fahrenheit);

        // Wait 2 seconds before reading again
        // sleep_ms(2000) is used instead of MicroPython's utime.sleep(2) to introduce a 2-second delay.
        sleep_ms(2000);
    }

    return 0;
}
