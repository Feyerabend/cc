
// .. impl. for display ..

void gpio_callback(uint gpio, uint32_t events) {
    // button press event handling ..
}

int main() {
    stdio_init_all();

    // GPIO 2 as input with an interrupt
    gpio_set_irq_enabled_with_callback(2,
        GPIO_IRQ_EDGE_RISE,
        true,
        &gpio_callback
    );

    // low−power mode, wait for interrupts
    while (true) {
        __wfi(); // wait for interrupt
    }
}
