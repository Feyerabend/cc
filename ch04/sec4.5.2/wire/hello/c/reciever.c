#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"

#define UART_ID uart1
#define BAUD_RATE 9600
#define UART_TX_PIN 4
#define UART_RX_PIN 5
#define MAX_MESSAGE_LEN 100

bool read_message(char *buffer, uint32_t max_len) {
    static char temp_buffer[MAX_MESSAGE_LEN];
    static uint32_t buffer_index = 0;
    bool message_received = false;

    // Read available characters
    while (uart_is_readable(UART_ID) && buffer_index < max_len - 1) {
        char c = uart_getc(UART_ID);
        temp_buffer[buffer_index++] = c;

        // Check for complete message
        if (buffer_index >= 2 && temp_buffer[0] == '#' && temp_buffer[buffer_index - 1] == '*') {
            // Extract message (strip '#' and '*')
            if (buffer_index > 2) { // Ensure there's content between # and *
                strncpy(buffer, temp_buffer + 1, buffer_index - 2);
                buffer[buffer_index - 2] = '\0'; // Null-terminate
                message_received = true;
            }
            buffer_index = 0; // Reset buffer
            break;
        }
    }

    // Reset buffer if it overflows
    if (buffer_index >= max_len) {
        buffer_index = 0;
    }

    return message_received;
}

int main() {
    stdio_init_all(); // Initialize standard I/O (for printf)

    // Initialize UART1
    uart_init(UART_ID, BAUD_RATE);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);

    char message[MAX_MESSAGE_LEN];

    while (1) {
        if (read_message(message, MAX_MESSAGE_LEN)) {
            printf("Received: %s\n", message);
        }
        sleep_ms(100); // Delay 100ms to prevent busy waiting
    }

    return 0;
}
