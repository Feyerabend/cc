#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>

#define MAX_HANDLERS 10
#define MAX_SIGNALS  32

// Function pointer type for handlers
typedef void (*Handler)();

// Interrupt Vector Table: array of handler lists per signal
typedef struct {
    Handler handlers[MAX_HANDLERS];
    int count;
} SignalHandlerList;

SignalHandlerList ivt[MAX_SIGNALS];

// Register a handler for a signal
void register_handler(int sig, Handler h) {
    if (sig >= MAX_SIGNALS) return;
    if (ivt[sig].count < MAX_HANDLERS) {
        ivt[sig].handlers[ivt[sig].count++] = h;
    }
}

// Dispatcher called from signal handler
void dispatch(int sig) {
    printf("[IVT] Signal %d received. Dispatching...\n", sig);
    for (int i = 0; i < ivt[sig].count; i++) {
        if (ivt[sig].handlers[i]) {
            ivt[sig].handlers[i]();
        }
    }
}

// Real signal handler installed via sigaction
void signal_handler(int sig) {
    dispatch(sig);
}

// Example handlers
void handler_A() {
    printf("Handler A responding to signal!\n");
}

void handler_B() {
    printf("Handler B taking action!\n");
}

int main() {
    printf("PID: %d\n", getpid());
    printf("Send SIGUSR1 using: kill -USR1 %d\n", getpid());

    // Register signal and handlers
    struct sigaction sa;
    sa.sa_handler = signal_handler;
    sa.sa_flags = SA_RESTART;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGUSR1, &sa, NULL);

    register_handler(SIGUSR1, handler_A);
    register_handler(SIGUSR1, handler_B);

    // Run forever
    while (1) {
        pause();  // Wait for signal
    }

    return 0;
}