#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <pthread.h>

#define QUEUE_SIZE 10
#define MAX_SIGNALS 32

typedef struct {
    int queue[QUEUE_SIZE];
    int head, tail, count;
    pthread_mutex_t mutex;
    pthread_cond_t cond;
} SignalQueue;

SignalQueue queues[MAX_SIGNALS];

void enqueue(SignalQueue *q, int value) {
    pthread_mutex_lock(&q->mutex);
    if (q->count < QUEUE_SIZE) {
        q->queue[q->tail] = value;
        q->tail = (q->tail + 1) % QUEUE_SIZE;
        q->count++;
        pthread_cond_signal(&q->cond);
    }
    pthread_mutex_unlock(&q->mutex);
}

void* signal_worker(void *arg) {
    int sig = *(int*)arg;
    SignalQueue *q = &queues[sig];
    while (1) {
        pthread_mutex_lock(&q->mutex);
        while (q->count == 0) {
            pthread_cond_wait(&q->cond, &q->mutex);
        }
        int val = q->queue[q->head];
        q->head = (q->head + 1) % QUEUE_SIZE;
        q->count--;
        pthread_mutex_unlock(&q->mutex);
        printf("Handled signal %d from queue\n", val);
    }
    return NULL;
}

void signal_handler(int sig) {
    enqueue(&queues[sig], sig);
}

void setup(int sig) {
    struct sigaction sa;
    sa.sa_handler = signal_handler;
    sa.sa_flags = SA_RESTART;
    sigemptyset(&sa.sa_mask);
    sigaction(sig, &sa, NULL);
}

int main() {
    printf("PID: %d\n", getpid());

    for (int i = 0; i < MAX_SIGNALS; i++) {
        pthread_mutex_init(&queues[i].mutex, NULL);
        pthread_cond_init(&queues[i].cond, NULL);
        queues[i].head = queues[i].tail = queues[i].count = 0;
    }

    // two signal handlers
    int sigs[] = {SIGUSR1, SIGUSR2};
    for (int i = 0; i < 2; i++) {
        setup(sigs[i]);
        pthread_t tid;
        pthread_create(&tid, NULL, signal_worker, &sigs[i]);
        pthread_detach(tid);
    }

    // main thread sleeps
    while (1) pause();
}
