#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/gpio.h"

// Config
#define UART_ID uart1
#define BAUD_RATE 9600
#define UART_TX_PIN 4
#define UART_RX_PIN 5

#define BUFFER_SIZE 256
#define MESSAGE_SIZE 128
#define HISTORY_SIZE 20

// Message structures
typedef struct {
    char command[MESSAGE_SIZE];
    uint32_t timestamp;
} history_entry_t;

// Global variables
static char rx_buffer[BUFFER_SIZE];
static int rx_buffer_pos = 0;
static history_entry_t command_history[HISTORY_SIZE];
static int history_count = 0;
static volatile bool running = true;

// Function prototypes
void send_command(const char* command);
void send_request(const char* request);
void check_for_messages();
void display_message(const char* message);
void interactive_mode();
void monitor_mode();
void add_to_history(const char* command);
void show_history();
void show_help();
char* format_message(const char* message, char* buffer);
char* parse_message(const char* raw_message, char* buffer);
void format_time(uint32_t timestamp, char* buffer);
char* trim_string(char* str);

void interactive_mode() {
    printf("\n=== Interactive Mode ===\n");
    show_help();
    
    char input[MESSAGE_SIZE];
    
    while (running) {
        // Check for incoming messages first
        check_for_messages();
        
        // Get user input (non-blocking check)
        printf("\nEnter command (or 'help'): ");
        fflush(stdout);
        
        if (fgets(input, sizeof(input), stdin)) {
            char* cmd = trim_string(input);
            
            // Convert to uppercase for comparison
            char upper_cmd[MESSAGE_SIZE];
            strncpy(upper_cmd, cmd, sizeof(upper_cmd) - 1);
            upper_cmd[sizeof(upper_cmd) - 1] = '\0';
            
            for (int i = 0; upper_cmd[i]; i++) {
                upper_cmd[i] = toupper(upper_cmd[i]);
            }
            
            // Process commands
            if (strcmp(upper_cmd, "QUIT") == 0 || strcmp(upper_cmd, "EXIT") == 0) {
                running = false;
                break;
            } else if (strcmp(upper_cmd, "HELP") == 0) {
                show_help();
            } else if (strcmp(upper_cmd, "HISTORY") == 0) {
                show_history();
            } else if (strcmp(upper_cmd, "CLEAR") == 0) {
                // Clear screen (works on most terminals)
                printf("\033[2J\033[H");
                show_help();
            } else if (strlen(cmd) == 0) {
                continue;
            } else if (strcmp(upper_cmd, "STATUS") == 0) {
                send_command("STATUS");
            } else if (strcmp(upper_cmd, "PING") == 0) {
                send_command("PING");
            } else if (strcmp(upper_cmd, "LED_ON") == 0) {
                send_command("LED_ON");
            } else if (strcmp(upper_cmd, "LED_OFF") == 0) {
                send_command("LED_OFF");
            } else if (strcmp(upper_cmd, "TEMP") == 0) {
                send_request("TEMP");
            } else if (strncmp(upper_cmd, "RAW:", 4) == 0) {
                // Send raw message (useful for testing)
                send_command(cmd + 4);
            } else {
                printf("Unknown command: %s (type 'help' for available commands)\n", cmd);
            }
        }
        
        // Small delay to prevent overwhelming the UART
        sleep_ms(50);
    }
}

void monitor_mode() {
    printf("\n=== Monitor Mode ===\n");
    printf("Listening for UART messages...\n");
    printf("Press Ctrl+C to exit\n\n");
    
    uint32_t last_activity = to_ms_since_boot(get_absolute_time());
    
    while (running) {
        bool had_activity = false;
        
        // Check for messages
        int old_pos = rx_buffer_pos;
        check_for_messages();
        
        if (rx_buffer_pos != old_pos || uart_is_readable(UART_ID)) {
            had_activity = true;
            last_activity = to_ms_since_boot(get_absolute_time());
        }
        
        // Show periodic status if no activity
        uint32_t now = to_ms_since_boot(get_absolute_time());
        if (!had_activity && (now - last_activity) > 30000) { // 30 seconds
            printf("[%lu] No activity for 30s - still monitoring...\n", now / 1000);
            last_activity = now;
        }
        
        sleep_ms(100);
    }
}

void send_command(const char* command) {
    char message[MESSAGE_SIZE];
    snprintf(message, sizeof(message), "CMD:%s", command);
    
    char formatted[MESSAGE_SIZE + 4];
    format_message(message, formatted);
    
    // Send the formatted message
    for (size_t i = 0; i < strlen(formatted); i++) {
        uart_putc(UART_ID, formatted[i]);
    }
    
    printf("Sent command: %s\n", command);
    add_to_history(message);
}

void send_request(const char* request) {
    char message[MESSAGE_SIZE];
    snprintf(message, sizeof(message), "REQ:%s", request);
    
    char formatted[MESSAGE_SIZE + 4];
    format_message(message, formatted);
    
    // Send the formatted message
    for (size_t i = 0; i < strlen(formatted); i++) {
        uart_putc(UART_ID, formatted[i]);
    }
    
    printf("Sent request: %s\n", request);
    add_to_history(message);
}

void check_for_messages() {
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
            printf("Warning: RX buffer overflow, data may be lost\n");
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
                display_message(parsed_msg);
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

void display_message(const char* message) {
    char time_str[16];
    uint32_t timestamp = to_ms_since_boot(get_absolute_time());
    format_time(timestamp, time_str);
    
    printf("[%s] Received: %s\n", time_str, message);
}

void add_to_history(const char* command) {
    int idx = history_count % HISTORY_SIZE;
    strncpy(command_history[idx].command, command, sizeof(command_history[idx].command) - 1);
    command_history[idx].command[sizeof(command_history[idx].command) - 1] = '\0';
    command_history[idx].timestamp = to_ms_since_boot(get_absolute_time());
    history_count++;
}

void show_history() {
    printf("\n=== Command History ===\n");
    if (history_count == 0) {
        printf("No commands in history.\n");
        return;
    }
    
    int start = (history_count > HISTORY_SIZE) ? history_count - HISTORY_SIZE : 0;
    int count = (history_count > HISTORY_SIZE) ? HISTORY_SIZE : history_count;
    
    for (int i = 0; i < count; i++) {
        int idx = (start + i) % HISTORY_SIZE;
        char time_str[16];
        format_time(command_history[idx].timestamp, time_str);
        printf("%2d. [%s] %s\n", i + 1, time_str, command_history[idx].command);
    }
}

void show_help() {
    printf("\n=== Available Commands ===\n");
    printf("Device Commands:\n");
    printf("  STATUS     - Request device status\n");
    printf("  PING       - Ping the device\n");
    printf("  LED_ON     - Turn LED on\n");
    printf("  LED_OFF    - Turn LED off\n");
    printf("  TEMP       - Request temperature reading\n");
    printf("\nController Commands:\n");
    printf("  HISTORY    - Show command history\n");
    printf("  CLEAR      - Clear screen\n");
    printf("  HELP       - Show this help\n");
    printf("  QUIT/EXIT  - Exit program\n");
    printf("\nAdvanced:\n");
    printf("  RAW:text   - Send raw message (for testing)\n");
    printf("========================\n");
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

char* trim_string(char* str) {
    char* end;
    
    // Trim leading whitespace
    while(isspace((unsigned char)*str)) str++;
    
    if(*str == 0) return str; // All spaces
    
    // Trim trailing whitespace
    end = str + strlen(str) - 1;
    while(end > str && isspace((unsigned char)*end)) end--;
    
    end[1] = '\0';
    return str;
}


int main() {
    stdio_init_all();
    
    // Initialize UART
    uart_init(UART_ID, BAUD_RATE);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
    
    // Configure UART settings for better reliability
    uart_set_hw_flow(UART_ID, false, false);
    uart_set_format(UART_ID, 8, 1, UART_PARITY_NONE);
    
    printf("\n=== UART Controller ===\n");
    printf("TX Pin: GP%d, RX Pin: GP%d\n", UART_TX_PIN, UART_RX_PIN);
    printf("Baud Rate: %d\n", BAUD_RATE);
    printf("Message Format: #MESSAGE*\n");
    
    // Choose mode
    printf("\nSelect operating mode:\n");
    printf("1. Interactive mode (send commands and receive responses)\n");
    printf("2. Monitor mode (listen only)\n");
    printf("Enter choice (1 or 2): ");
    
    char choice = getchar();
    while (getchar() != '\n'); // consume remaining characters
    
    if (choice == '1') {
        interactive_mode();
    } else if (choice == '2') {
        monitor_mode();
    } else {
        printf("Invalid choice. Exiting.\n");
        return 1;
    }
    
    printf("\nController stopped.\n");
    return 0;
}
