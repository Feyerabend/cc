#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <pthread.h>

#define MAX_HANDLERS 10
#define MAX_SIGNALS  32

typedef void (*Handler)();

typedef struct {
    Handler handlers[MAX_HANDLERS];
    int count;
} SignalHandlerList;

SignalHandlerList ivt[MAX_SIGNALS];

// register a handler for a signal
void register_handler(int sig, Handler h) {
    if (sig >= MAX_SIGNALS) return;
    if (ivt[sig].count < MAX_HANDLERS) {
        ivt[sig].handlers[ivt[sig].count++] = h;
    }
}

// thread wrapper for handler call
void* thread_wrapper(void* arg) {
    Handler h = (Handler)arg;
    h();
    return NULL;
}

// dispatcher called from signal handler
void dispatch(int sig) {
    printf("[IVT] Signal %d received. Dispatching in threads...\n", sig);

    for (int i = 0; i < ivt[sig].count; i++) {
        pthread_t tid;
        if (pthread_create(&tid, NULL, thread_wrapper, (void*)ivt[sig].handlers[i]) == 0) {
            pthread_detach(tid);  // don't wait for the thread
        }
    }
}

// real signal handler installed via sigaction
void signal_handler(int sig) {
    dispatch(sig);
}

// example handlers
void handler_A() {
    printf("Handler A (thread %p) reacting!\n", (void*)pthread_self());
}

void handler_B() {
    printf("Handler B (thread %p) doing work!\n", (void*)pthread_self());
}

int main() {
    printf("PID: %d\n", getpid());
    printf("Send SIGUSR1 using: kill -USR1 %d\n", getpid());

    // register signal and handlers
    struct sigaction sa;
    sa.sa_handler = signal_handler;
    sa.sa_flags = SA_RESTART;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGUSR1, &sa, NULL);

    register_handler(SIGUSR1, handler_A);
    register_handler(SIGUSR1, handler_B);

    // wait for signals
    while (1) {
        pause();  // sleep until signal received
    }

    return 0;
}