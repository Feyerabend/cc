#ifndef QUEUE_H
#define QUEUE_H

typedef struct Queue Queue;

// Constructor/Destructor
Queue* queue_create(int capacity);
void   queue_destroy(Queue* q);

// Operations
int queue_enqueue(Queue* q, int value);  // Add to rear, returns 1 on success
int queue_dequeue(Queue* q, int* out);   // Remove from front, returns 1 on success
int queue_front(Queue* q, int* out);     // Peek at front without removing
int queue_is_empty(Queue* q);
int queue_is_full(Queue* q);
int queue_size(Queue* q);

#endif // QUEUE_H
