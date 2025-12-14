#include "pico/stdlib.h"
#include "hardware/clocks.h"

int main() {
    stdio_init_all();

    // GPIO 2 as the wakeup pin
    gpio_set_dir(2, GPIO_IN);
    gpio_pull_up(2);

    // dormant mode and wait for a GPIO event
    clock_dormant_until_gpio(2);

    // resumes after GPIO event
    while (true) {
        printf("Woke up from dormant mode\n");
    }
}
