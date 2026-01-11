// DIFFIE-HELLMAN INITIATOR (C)
// Demonstrates key exchange then symmetric encryption
// Wiring: UART TX (GP4) -> Pico2 RX, UART RX (GP5) -> Pico2 TX, GND -> GND

#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/uart.h"
#include "pico/rand.h"

// UART configuration
#define UART_ID uart1
#define BAUD_RATE 115200
#define UART_TX_PIN 4
#define UART_RX_PIN 5

// Diffie-Hellman parameters
#define DH_PRIME 23
#define DH_GENERATOR 5

// Queue structures for inter-core communication
typedef enum {
    TASK_DH_COMPUTE,
    TASK_DH_SHARED,
    TASK_ENCRYPT
} TaskType;

typedef enum {
    RESULT_DH_PUBLIC,
    RESULT_DH_SHARED,
    RESULT_ENCRYPTED
} ResultType;

typedef struct {
    TaskType type;
    uint32_t g;
    uint32_t private_key;
    uint32_t other_public;
    uint32_t p;
    uint8_t data[256];
    size_t data_len;
    uint32_t key;
} Task;

typedef struct {
    ResultType type;
    uint32_t value;
    uint8_t data[256];
    size_t data_len;
    uint32_t time_ms;
} Result;

// Shared state
static volatile bool core1_ready = false;
static volatile uint32_t dh_shared_secret = 0;

// Simple modular exponentiation
uint32_t pow_mod(uint32_t base, uint32_t exp, uint32_t mod) {
    uint32_t result = 1;
    base = base % mod;
    
    while (exp > 0) {
        if (exp % 2 == 1) {
            result = (result * base) % mod;
        }
        exp = exp >> 1;
        base = (base * base) % mod;
    }
    
    return result;
}

// Simple XOR encryption (for demonstration only)
void encrypt_with_key(const uint8_t* data, size_t len, uint32_t key, uint8_t* output) {
    uint8_t key_bytes[4];
    key_bytes[0] = (key >> 24) & 0xFF;
    key_bytes[1] = (key >> 16) & 0xFF;
    key_bytes[2] = (key >> 8) & 0xFF;
    key_bytes[3] = key & 0xFF;
    
    for (size_t i = 0; i < len; i++) {
        output[i] = data[i] ^ key_bytes[i % 4];
    }
}

// Core 1 task: Crypto engine
void core1_task() {
    printf("[Core 1] Crypto engine started\n");
    core1_ready = true;
    
    while (true) {
        // Check if there's a task waiting
        if (multicore_fifo_rvalid()) {
            uint32_t task_ptr = multicore_fifo_pop_blocking();
            Task* task = (Task*)task_ptr;
            
            Result result = {0};
            uint32_t start = to_ms_since_boot(get_absolute_time());
            
            switch (task->type) {
                case TASK_DH_COMPUTE: {
                    // Compute g^private mod p
                    result.type = RESULT_DH_PUBLIC;
                    result.value = pow_mod(task->g, task->private_key, task->p);
                    result.time_ms = to_ms_since_boot(get_absolute_time()) - start;
                    printf("[Core 1] DH public computed in %lu ms\n", result.time_ms);
                    break;
                }
                
                case TASK_DH_SHARED: {
                    // Compute other_public^private mod p
                    result.type = RESULT_DH_SHARED;
                    result.value = pow_mod(task->other_public, task->private_key, task->p);
                    result.time_ms = to_ms_since_boot(get_absolute_time()) - start;
                    printf("[Core 1] DH shared secret computed in %lu ms\n", result.time_ms);
                    break;
                }
                
                case TASK_ENCRYPT: {
                    // Encrypt data
                    result.type = RESULT_ENCRYPTED;
                    encrypt_with_key(task->data, task->data_len, task->key, result.data);
                    result.data_len = task->data_len;
                    result.time_ms = to_ms_since_boot(get_absolute_time()) - start;
                    printf("[Core 1] Encrypted %zu bytes in %lu ms\n", task->data_len, result.time_ms);
                    break;
                }
            }
            
            // Send result back
            multicore_fifo_push_blocking((uint32_t)&result);
            sleep_ms(10); // Give core 0 time to copy result
        }
        
        sleep_ms(5);
    }
}

// Helper to send task and wait for result
Result send_task_and_wait(Task* task) {
    multicore_fifo_push_blocking((uint32_t)task);
    
    // Wait for result
    uint32_t result_ptr = multicore_fifo_pop_blocking();
    Result result = *(Result*)result_ptr;
    
    return result;
}

int main() {
    stdio_init_all();
    sleep_ms(2000); // Wait for USB serial
    
    printf("PICO 2 - DIFFIE-HELLMAN INITIATOR (C)\n\n");
    printf("DH Parameters:\n");
    printf("  Prime (p) = %d\n", DH_PRIME);
    printf("  Generator (g) = %d\n", DH_GENERATOR);
    printf("\nWiring:\n");
    printf("  GP%d (TX) -> Pico2 RX, GP%d (RX) -> Pico2 TX\n", UART_TX_PIN, UART_RX_PIN);
    printf("  GND -> GND\n\n");
    
    // Start Core 1
    multicore_launch_core1(core1_task);
    while (!core1_ready) {
        sleep_ms(100);
    }
    
    // Setup UART
    uart_init(UART_ID, BAUD_RATE);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
    
    printf("\n[Core 0] Ready. Starting DH key exchange..\n");
    printf("--------------------------------------------------\n");
    
    // Step 1: Generate private key
    uint32_t private_key = 2 + (get_rand_32() % (DH_PRIME - 3));
    printf("[STEP 1] Generated private key: %lu (secret!)\n", private_key);
    
    // Step 2: Compute public key
    printf("[STEP 2] Computing public key: %d^%lu mod %d\n", DH_GENERATOR, private_key, DH_PRIME);
    Task task = {
        .type = TASK_DH_COMPUTE,
        .g = DH_GENERATOR,
        .private_key = private_key,
        .p = DH_PRIME
    };
    Result result = send_task_and_wait(&task);
    uint32_t public_key = result.value;
    printf("[STEP 2] Our public key: %lu\n", public_key);
    
    // Step 3: Send public key
    printf("[STEP 3] Sending public key to Pico 2..\n");
    uint8_t pub_bytes[2] = {(public_key >> 8) & 0xFF, public_key & 0xFF};
    uart_write_blocking(UART_ID, pub_bytes, 2);
    
    // Step 4: Receive other's public key
    printf("[STEP 4] Waiting for Pico 2's public key..\n");
    uint8_t recv_buf[2];
    uint32_t timeout = to_ms_since_boot(get_absolute_time());
    int received = 0;
    
    while (received < 2) {
        if (uart_is_readable(UART_ID)) {
            recv_buf[received++] = uart_getc(UART_ID);
        }
        
        if (to_ms_since_boot(get_absolute_time()) - timeout > 10000) {
            printf("[ERROR] Timeout waiting for other public key\n");
            return 1;
        }
        sleep_ms(10);
    }
    
    uint32_t other_public_key = (recv_buf[0] << 8) | recv_buf[1];
    printf("[STEP 4] Received public key: %lu\n", other_public_key);
    
    // Step 5: Compute shared secret
    printf("[STEP 5] Computing shared secret: %lu^%lu mod %d\n", other_public_key, private_key, DH_PRIME);
    task.type = TASK_DH_SHARED;
    task.other_public = other_public_key;
    task.private_key = private_key;
    task.p = DH_PRIME;
    result = send_task_and_wait(&task);
    dh_shared_secret = result.value;
    printf("[STEP 5] ✓ Shared secret established: %lu\n", dh_shared_secret);
    
    printf("\nKEY EXCHANGE COMPLETE!\n\n");
    printf("\nNow you can send encrypted messages..\n");
    printf("--------------------------------------------------\n");
    
    // Main encryption loop
    char input_buf[128];
    while (true) {
        printf("\nEnter text to encrypt: ");
        fgets(input_buf, sizeof(input_buf), stdin);
        
        // Remove newline
        size_t len = strlen(input_buf);
        if (len > 0 && input_buf[len-1] == '\n') {
            input_buf[len-1] = '\0';
            len--;
        }
        
        if (len == 0) continue;
        
        printf("\n[INPUT] '%s' (%zu bytes)\n", input_buf, len);
        
        // Encrypt
        printf("[ENCRYPT] Using shared secret: %lu\n", dh_shared_secret);
        task.type = TASK_ENCRYPT;
        memcpy(task.data, input_buf, len);
        task.data_len = len;
        task.key = dh_shared_secret;
        result = send_task_and_wait(&task);
        
        printf("[ENCRYPTED] ");
        for (size_t i = 0; i < result.data_len; i++) {
            printf("%02x", result.data[i]);
        }
        printf("\n");
        
        // Send: length + encrypted data
        uint8_t len_bytes[2] = {(len >> 8) & 0xFF, len & 0xFF};
        uart_write_blocking(UART_ID, len_bytes, 2);
        uart_write_blocking(UART_ID, result.data, result.data_len);
        
        printf("[UART TX] Sent %zu bytes\n", result.data_len + 2);
        printf("--------------------------------------------------\n");
    }
    
    return 0;
}

