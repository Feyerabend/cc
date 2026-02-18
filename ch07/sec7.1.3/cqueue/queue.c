#include <stdlib.h>
#include "queue.h"

struct Queue {
    int* data;
    int  front;    // index of front element
    int  rear;     // index where next element will be inserted
    int  size;     // current number of elements
    int  capacity;
};

Queue* queue_create(int capacity) {
    Queue* q = malloc(sizeof(Queue));
    if (!q) return NULL;
    q->data = malloc(sizeof(int) * capacity);
    if (!q->data) { free(q); return NULL; }
    q->front = 0;
    q->rear = 0;
    q->size = 0;
    q->capacity = capacity;
    return q;
}

void queue_destroy(Queue* q) {
    if (!q) return;
    free(q->data);
    free(q);
}

int queue_enqueue(Queue* q, int value) {
    if (q->size >= q->capacity) return 0; // full
    q->data[q->rear] = value;
    q->rear = (q->rear + 1) % q->capacity; // wrap around
    q->size++;
    return 1;
}

int queue_dequeue(Queue* q, int* out) {
    if (q->size == 0) return 0; // empty
    *out = q->data[q->front];
    q->front = (q->front + 1) % q->capacity; // wrap around
    q->size--;
    return 1;
}

int queue_front(Queue* q, int* out) {
    if (q->size == 0) return 0;
    *out = q->data[q->front];
    return 1;
}

int queue_is_empty(Queue* q) { return q->size == 0; }
int queue_is_full(Queue* q)  { return q->size >= q->capacity; }
int queue_size(Queue* q)     { return q->size; }
