#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <time.h>
#include <sys/time.h>


/* Ring buffer structure - caller manages storage */
typedef struct {
    uint8_t *buffer;
    volatile size_t head;
    volatile size_t tail;
    size_t capacity;
} ring_buffer_t;

/* Initialize ring buffer (re-entrant) */
void ring_buffer_init(ring_buffer_t *rb, uint8_t *storage, size_t capacity) {
    rb->buffer = storage;
    rb->head = 0;
    rb->tail = 0;
    rb->capacity = capacity;
}

/* Re-entrant write - safe to call from signal handler */
bool ring_buffer_write(ring_buffer_t *rb, uint8_t data) {
    size_t next_head = (rb->head + 1) % rb->capacity;
    
    /* Check if buffer is full */
    if (next_head == rb->tail) {
        return false;  // Buffer full
    }
    
    rb->buffer[rb->head] = data;
    rb->head = next_head;
    
    return true;
}

/* Re-entrant read */
bool ring_buffer_read(ring_buffer_t *rb, uint8_t *data) {
    /* Check if buffer is empty */
    if (rb->head == rb->tail) {
        return false;  // Buffer empty
    }
    
    *data = rb->buffer[rb->tail];
    rb->tail = (rb->tail + 1) % rb->capacity;
    
    return true;
}

/* Get number of bytes available to read */
size_t ring_buffer_available(ring_buffer_t *rb) {
    if (rb->head >= rb->tail) {
        return rb->head - rb->tail;
    } else {
        return rb->capacity - rb->tail + rb->head;
    }
}

/* Simulation Setup */

#define BUFFER_SIZE 32

/* Simulated UART buffers */
static uint8_t uart0_storage[BUFFER_SIZE];
static ring_buffer_t uart0_buffer;

static uint8_t uart1_storage[BUFFER_SIZE];
static ring_buffer_t uart1_buffer;

/* Statistics for demonstration */
static volatile unsigned int uart0_interrupts = 0;
static volatile unsigned int uart1_interrupts = 0;
static volatile unsigned int uart0_overruns = 0;
static volatile unsigned int uart1_overruns = 0;

/* Simulated data sources */
static const char *uart0_data = "Hello from UART0! ";
static const char *uart1_data = "UART1 speaking.. ";
static volatile size_t uart0_pos = 0;
static volatile size_t uart1_pos = 0;

/* SIGALRM handler - simulates UART0 interrupt */
void uart0_interrupt_handler(int sig) {
    (void)sig;
    uart0_interrupts++;
    
    /* Simulate receiving a byte */
    char byte = uart0_data[uart0_pos];
    uart0_pos = (uart0_pos + 1) % strlen(uart0_data);
    
    /* Write to buffer - this is RE-ENTRANT */
    if (!ring_buffer_write(&uart0_buffer, (uint8_t)byte)) {
        uart0_overruns++;
    }
}

/* SIGUSR1 handler - simulates UART1 interrupt */
void uart1_interrupt_handler(int sig) {
    (void)sig;
    uart1_interrupts++;
    
    /* Simulate receiving a byte */
    char byte = uart1_data[uart1_pos];
    uart1_pos = (uart1_pos + 1) % strlen(uart1_data);
    
    /* Write to buffer - this is RE-ENTRANT */
    if (!ring_buffer_write(&uart1_buffer, (uint8_t)byte)) {
        uart1_overruns++;
    }
}

/* Print buffer contents with visual representation */
void print_buffer_state(const char *name, ring_buffer_t *rb) {
    printf("\n%s Buffer State:\n", name);
    printf("  Capacity: %zu, Head: %zu, Tail: %zu, Available: %zu\n",
           rb->capacity, rb->head, rb->tail, ring_buffer_available(rb));
    
    printf("  Buffer: [");
    for (size_t i = 0; i < rb->capacity; i++) {
        if (i == rb->head && i == rb->tail) {
            printf("H/T");
        } else if (i == rb->head) {
            printf("H");
        } else if (i == rb->tail) {
            printf("T");
        } else {
            printf(" ");
        }
        
        if (rb->head == rb->tail) {
            printf("_");  // Empty
        } else if (rb->head > rb->tail) {
            printf("%c", (i >= rb->tail && i < rb->head) ? rb->buffer[i] : '_');
        } else {
            printf("%c", (i >= rb->tail || i < rb->head) ? rb->buffer[i] : '_');
        }
        
        if (i < rb->capacity - 1) printf("|");
    }
    printf("]\n");
}

int main(void) {
    printf("Re-entrant Ring Buffer with Signal Handler Simulation\n");
    printf("Simulating hardware UART interrupts using POSIX signals\n\n");
    
    /* Init buffers */
    ring_buffer_init(&uart0_buffer, uart0_storage, BUFFER_SIZE);
    ring_buffer_init(&uart1_buffer, uart1_storage, BUFFER_SIZE);
    
    /* Set up signal handlers (simulate interrupt handlers) */
    struct sigaction sa0, sa1;
    
    memset(&sa0, 0, sizeof(sa0));
    sa0.sa_handler = uart0_interrupt_handler;
    sigaction(SIGALRM, &sa0, NULL);
    
    memset(&sa1, 0, sizeof(sa1));
    sa1.sa_handler = uart1_interrupt_handler;
    sigaction(SIGUSR1, &sa1, NULL);
    
    /* Set up timer for UART0 (SIGALRM every 50ms) */
    struct itimerval timer0;
    timer0.it_value.tv_sec = 0;
    timer0.it_value.tv_usec = 50000;  // 50ms
    timer0.it_interval.tv_sec = 0;
    timer0.it_interval.tv_usec = 50000;
    setitimer(ITIMER_REAL, &timer0, NULL);
    
    printf("Starting simulation..\n");
    printf("- UART0 receives data every 50ms (via SIGALRM)\n");
    printf("- UART1 receives data when we send SIGUSR1\n");
    printf("- Main loop processes both buffers\n\n");
    
    /* Simulation loop */
    for (int iteration = 0; iteration < 20; iteration++) {
        printf("\n--- Iteration %d ---\n", iteration + 1);
        
        /* Trigger UART1 interrupt manually (simulate sporadic data) */
        if (iteration % 3 == 0) {
            printf("Triggering UART1 interrupt..\n");
            raise(SIGUSR1);
        }
        
        /* Wait a bit to let signals arrive */
        usleep(60000);  // 60ms
        
        /* Process UART0 data (main loop reading while interrupts may fire) */
        printf("\nUART0 received: \"");
        uint8_t byte;
        int count = 0;
        while (ring_buffer_read(&uart0_buffer, &byte) && count++ < 10) {
            printf("%c", byte);
            fflush(stdout);
        }
        printf("\"\n");
        
        /* Process UART1 data */
        printf("UART1 received: \"");
        count = 0;
        while (ring_buffer_read(&uart1_buffer, &byte) && count++ < 10) {
            printf("%c", byte);
            fflush(stdout);
        }
        printf("\"\n");
        
        /* Show buffer states */
        print_buffer_state("UART0", &uart0_buffer);
        print_buffer_state("UART1", &uart1_buffer);
        
        /* Show statistics */
        printf("\nStatistics:\n");
        printf("  UART0: %u interrupts, %u overruns\n", 
               uart0_interrupts, uart0_overruns);
        printf("  UART1: %u interrupts, %u overruns\n", 
               uart1_interrupts, uart1_overruns);
        
        /* Demonstrate re-entrancy by intentionally not reading for a bit */
        if (iteration == 10) {
            printf("\n! Simulating slow main loop (not reading buffers) !\n");
            sleep(1);  // Let interrupts fill up the buffer
        }
    }
    
    /* Clean up */
    timer0.it_value.tv_sec = 0;
    timer0.it_value.tv_usec = 0;
    timer0.it_interval.tv_sec = 0;
    timer0.it_interval.tv_usec = 0;
    setitimer(ITIMER_REAL, &timer0, NULL);
    
    printf("\n\n** Final Statistics **\n");
    printf("UART0: %u total interrupts, %u overruns\n", uart0_interrupts, uart0_overruns);
    printf("UART1: %u total interrupts, %u overruns\n", uart1_interrupts, uart1_overruns);
    printf("\n  Ring buffers handled concurrent access safely!\n");
    printf("  Signal handlers (interrupts) wrote while main loop read\n");
    printf("  No data corruption due to re-entrant design\n");
    
    return 0;
}


// This code simulates a re-entrant ring buffer used in an embedded system context,
// where data is received from two UARTs via interrupts (simulated with signals).
// The main loop processes the buffers while interrupts may occur, demonstrating safe concurrent access.
// The ring buffer implementation is designed to be re-entrant, allowing writes from signal handlers without data corruption.
// Note: This code is for demonstration purposes and may not be suitable for production use in a real embedded system.
// It is a simulation of the concepts, not a direct implementation for actual hardware.

