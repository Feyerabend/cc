#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"

#define UART_ID uart1
#define BAUD_RATE 9600
#define UART_TX_PIN 4
#define UART_RX_PIN 5

void send_message(const char *message) {
    char start_char = '#';
    char end_char = '*';
    uart_putc(UART_ID, start_char); // Send start character
    uart_puts(UART_ID, message);    // Send message
    uart_putc(UART_ID, end_char);   // Send end character
}

int main() {
    stdio_init_all(); // Initialize standard I/O (for printf)

    // Initialize UART1
    uart_init(UART_ID, BAUD_RATE);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);

    const char *message = "Hello, World!";

    while (1) {
        send_message(message);
        printf("Sent: %s\n", message);
        sleep_ms(2000); // Delay 2 seconds
    }

    return 0;
}