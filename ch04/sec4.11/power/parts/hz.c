
#include "hardware/clocks.h"

int main() {

    // system clock at 48 MHz (default 125 MHz)
    set_sys_clock_khz(48000, true);

    while (true) {
        // tasks at lower frequency to save power
    }
}

