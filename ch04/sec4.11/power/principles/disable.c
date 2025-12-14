#include "hardware/clocks.h"

int main() {
    stdio_init_all();

    // disable UART0 clock to save power
    clock_stop(clk_peri);

    while (true) {
        // loop without using UART ..
    }
}
