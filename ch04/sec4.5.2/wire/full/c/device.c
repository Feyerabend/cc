#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/gpio.h"
#include "hardware/adc.h"

// Config
#define UART_ID uart1
#define BAUD_RATE 9600
#define UART_TX_PIN 4
#define UART_RX_PIN 5
#define LED_PIN 25

#define BUFFER_SIZE 256
#define MESSAGE_SIZE 128

// Global variables
static char rx_buffer[BUFFER_SIZE];
static int rx_buffer_pos = 0;
static volatile uint32_t message_counter = 0;
static volatile bool led_state = false;
static uint32_t last_heartbeat = 0;
static uint32_t last_temp_reading = 0;

void process_messages();
void process_command(const char* command);
void process_request(const char* request);
void send_message(const char* message);
void send_heartbeat();
void send_periodic_data();
float read_temperature();
void blink_led(uint32_t duration_ms);
void set_led(bool state);
char* format_message(const char* message, char* buffer);
char* parse_message(const char* raw_message, char* buffer);
void format_time(uint32_t timestamp, char* buffer);


void process_messages() {
    // Read all available characters
    while (uart_is_readable(UART_ID)) {
        char c = uart_getc(UART_ID);
        
        // Add to buffer if there's space
        if (rx_buffer_pos < BUFFER_SIZE - 1) {
            rx_buffer[rx_buffer_pos++] = c;
            rx_buffer[rx_buffer_pos] = '\0';
        } else {
            // Buffer overflow - shift left and continue
            memmove(rx_buffer, rx_buffer + BUFFER_SIZE/2, BUFFER_SIZE/2);
            rx_buffer_pos = BUFFER_SIZE/2;
            rx_buffer[rx_buffer_pos++] = c;
            rx_buffer[rx_buffer_pos] = '\0';
            printf("Warning: RX buffer overflow\n");
        }
    }
    
    // Look for complete messages in buffer
    char* search_start = rx_buffer;
    while (search_start < rx_buffer + rx_buffer_pos) {
        char* msg_start = strchr(search_start, '#');
        if (!msg_start) break;
        
        char* msg_end = strchr(msg_start, '*');
        if (!msg_end) break;
        
        // Extract and parse the message
        size_t msg_len = msg_end - msg_start + 1;
        char raw_msg[MESSAGE_SIZE];
        if (msg_len < MESSAGE_SIZE) {
            strncpy(raw_msg, msg_start, msg_len);
            raw_msg[msg_len] = '\0';
            
            char parsed_msg[MESSAGE_SIZE];
            if (parse_message(raw_msg, parsed_msg)) {
                char time_str[16];
                format_time(to_ms_since_boot(get_absolute_time()), time_str);
                printf("[%s] Received: %s\n", time_str, parsed_msg);
                
                // Process the message based on type
                if (strncmp(parsed_msg, "CMD:", 4) == 0) {
                    process_command(parsed_msg + 4);
                } else if (strncmp(parsed_msg, "REQ:", 4) == 0) {
                    process_request(parsed_msg + 4);
                } else {
                    printf("Unknown message format: %s\n", parsed_msg);
                    send_message("ERROR:UNKNOWN_FORMAT");
                }
            }
        }
        
        // Move search position past this message
        search_start = msg_end + 1;
    }
    
    // Clean up processed messages from buffer
    if (search_start > rx_buffer) {
        size_t remaining = rx_buffer + rx_buffer_pos - search_start;
        if (remaining > 0) {
            memmove(rx_buffer, search_start, remaining);
        }
        rx_buffer_pos = remaining;
        rx_buffer[rx_buffer_pos] = '\0';
    }
}

void process_command(const char* command) {
    printf("Processing command: %s\n", command);
    
    if (strcmp(command, "STATUS") == 0) {
        float temp_c = read_temperature();
        char status_msg[MESSAGE_SIZE];
        snprintf(status_msg, sizeof(status_msg), 
                "STATUS:TEMP=%.1fC,LED=%s,COUNT=%lu,UPTIME=%lu", 
                temp_c, led_state ? "ON" : "OFF", message_counter, 
                to_ms_since_boot(get_absolute_time()) / 1000);
        send_message(status_msg);
        blink_led(100);
    }
    else if (strcmp(command, "PING") == 0) {
        send_message("PONG");
        blink_led(100);
    }
    else if (strcmp(command, "LED_ON") == 0) {
        set_led(true);
        send_message("ACK:LED_ON");
        printf("LED turned ON\n");
    }
    else if (strcmp(command, "LED_OFF") == 0) {
        set_led(false);
        send_message("ACK:LED_OFF");
        printf("LED turned OFF\n");
    }
    else if (strcmp(command, "RESET") == 0) {
        send_message("ACK:RESET");
        printf("Reset command received - restarting in 2 seconds...\n");
        sleep_ms(2000);
        // In a real application, you might reset the watchdog or restart
        message_counter = 0;
        send_message("DEVICE:RESTARTED");
    }
    else {
        printf("Unknown command: %s\n", command);
        char error_msg[MESSAGE_SIZE];
        snprintf(error_msg, sizeof(error_msg), "ERROR:UNKNOWN_CMD:%s", command);
        send_message(error_msg);
    }
}

void process_request(const char* request) {
    printf("Processing request: %s\n", request);
    
    if (strcmp(request, "TEMP") == 0) {
        float temp_c = read_temperature();
        float temp_f = (temp_c * 9.0f / 5.0f) + 32.0f;
        char temp_msg[MESSAGE_SIZE];
        snprintf(temp_msg, sizeof(temp_msg), "TEMP:%.1fC,%.1fF", temp_c, temp_f);
        send_message(temp_msg);
        blink_led(100);
    }
    else if (strcmp(request, "STATUS") == 0) {
        // Same as CMD:STATUS but indicate it was a request
        float temp_c = read_temperature();
        char status_msg[MESSAGE_SIZE];
        snprintf(status_msg, sizeof(status_msg), 
                "STATUS_RESP:TEMP=%.1fC,LED=%s,COUNT=%lu,UPTIME=%lu", 
                temp_c, led_state ? "ON" : "OFF", message_counter, 
                to_ms_since_boot(get_absolute_time()) / 1000);
        send_message(status_msg);
        blink_led(100);
    }
    else if (strcmp(request, "TIME") == 0) {
        uint32_t uptime = to_ms_since_boot(get_absolute_time());
        char time_msg[MESSAGE_SIZE];
        snprintf(time_msg, sizeof(time_msg), "TIME:UPTIME=%lu", uptime);
        send_message(time_msg);
    }
    else {
        printf("Unknown request: %s\n", request);
        char error_msg[MESSAGE_SIZE];
        snprintf(error_msg, sizeof(error_msg), "ERROR:UNKNOWN_REQ:%s", request);
        send_message(error_msg);
    }
}

void send_message(const char* message) {
    char formatted[MESSAGE_SIZE + 4];
    format_message(message, formatted);
    
    // Send the formatted message
    for (size_t i = 0; i < strlen(formatted); i++) {
        uart_putc(UART_ID, formatted[i]);
    }
    
    message_counter++;
    
    char time_str[16];
    format_time(to_ms_since_boot(get_absolute_time()), time_str);
    printf("[%s] Sent: %s\n", time_str, message);
}

void send_heartbeat() {
    char heartbeat_msg[MESSAGE_SIZE];
    uint32_t uptime = to_ms_since_boot(get_absolute_time()) / 1000;
    snprintf(heartbeat_msg, sizeof(heartbeat_msg), 
            "HEARTBEAT:UPTIME=%lu,COUNT=%lu", uptime, message_counter);
    send_message(heartbeat_msg);
}

void send_periodic_data() {
    float temp_c = read_temperature();
    float temp_f = (temp_c * 9.0f / 5.0f) + 32.0f;
    
    char temp_msg[MESSAGE_SIZE];
    snprintf(temp_msg, sizeof(temp_msg), 
            "PERIODIC:TEMP=%.1fC/%.1fF,LED=%s", 
            temp_c, temp_f, led_state ? "ON" : "OFF");
    send_message(temp_msg);
}

float read_temperature() {
    // Read internal temp sensor
    uint16_t raw = adc_read();
    const float conversion_factor = 3.3f / (1 << 12);
    float voltage = raw * conversion_factor;
    
    // Convert to temperature using RP2040 datasheet formula
    float temperature = 27.0f - (voltage - 0.706f) / 0.001721f;
    
    return temperature;
}

void blink_led(uint32_t duration_ms) {
    bool original_state = led_state;
    gpio_put(LED_PIN, 1);
    sleep_ms(duration_ms);
    gpio_put(LED_PIN, original_state ? 1 : 0);
}

void set_led(bool state) {
    led_state = state;
    gpio_put(LED_PIN, state ? 1 : 0);
}

char* format_message(const char* message, char* buffer) {
    snprintf(buffer, MESSAGE_SIZE + 4, "#%s*", message);
    return buffer;
}

char* parse_message(const char* raw_message, char* buffer) {
    size_t len = strlen(raw_message);
    if (len >= 3 && raw_message[0] == '#' && raw_message[len-1] == '*') {
        strncpy(buffer, raw_message + 1, len - 2);
        buffer[len - 2] = '\0';
        return buffer;
    }
    return NULL;
}

void format_time(uint32_t timestamp, char* buffer) {
    uint32_t seconds = timestamp / 1000;
    uint32_t hours = (seconds / 3600) % 24;
    uint32_t minutes = (seconds / 60) % 60;
    uint32_t secs = seconds % 60;
    snprintf(buffer, 16, "%02lu:%02lu:%02lu", hours, minutes, secs);
}


int main() {
    stdio_init_all();
    
    // Init UART
    uart_init(UART_ID, BAUD_RATE);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
    
    // Config UART settings
    uart_set_hw_flow(UART_ID, false, false);
    uart_set_format(UART_ID, 8, 1, UART_PARITY_NONE);
    
    // Init LED
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    gpio_put(LED_PIN, 0);
    
    // Init ADC for temp sensor
    adc_init();
    adc_gpio_init(26 + 4); // Internal temperature sensor is on ADC channel 4
    adc_select_input(4);   // Select temperature sensor
    
    printf("\n=== UART Device Simulator ===\n");
    printf("TX Pin: GP%d, RX Pin: GP%d\n", UART_TX_PIN, UART_RX_PIN);
    printf("LED Pin: GP%d\n", LED_PIN);
    printf("Baud Rate: %d\n", BAUD_RATE);
    printf("Message Format: #MESSAGE*\n");
    
    // Send startup message
    send_message("DEVICE:STARTED");
    blink_led(500); // Startup blink
    
    printf("\nDevice ready. Supported commands:\n");
    printf("- CMD:STATUS, CMD:PING, CMD:LED_ON, CMD:LED_OFF\n");
    printf("- REQ:TEMP\n");
    printf("Sending periodic heartbeat and temperature data...\n\n");
    
    // Main loop
    while (true) {
        uint32_t now = to_ms_since_boot(get_absolute_time());
        
        // Process incoming messages
        process_messages();
        
        // Send periodic heartbeat (every 10 seconds)
        if (now - last_heartbeat >= 10000) {
            send_heartbeat();
            last_heartbeat = now;
        }
        
        // Send periodic temperature data (every 5 seconds)
        if (now - last_temp_reading >= 5000) {
            send_periodic_data();
            last_temp_reading = now;
        }
        
        // Small delay
        sleep_ms(50);
    }
    
    return 0;
}
