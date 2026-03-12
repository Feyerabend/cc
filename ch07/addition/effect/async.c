
#include <stdio.h>
#include <stdlib.h>

#include "effect.h"


// ASYNC: Cooperative multitasking

typedef struct Task {
    Effect computation;
    int task_id;
    int resumed;
    struct Task* next;
} Task;

typedef struct {
    Task* head;
    Task* tail;
    int next_id;
} TaskQueue;

void enqueue_task(TaskQueue* q, Effect eff) {
    Task* t = malloc(sizeof(Task));
    t->computation = eff;
    t->task_id = q->next_id++;
    t->resumed = 0;
    t->next = NULL;
    
    if (q->tail) {
        q->tail->next = t;
        q->tail = t;
    } else {
        q->head = q->tail = t;
    }
}

Task* dequeue_task(TaskQueue* q) {
    if (!q->head) return NULL;
    Task* t = q->head;
    q->head = t->next;
    if (!q->head) q->tail = NULL;
    return t;
}

void run_async(TaskQueue* queue) {
    printf("-- Async Runtime Starting --\n");
    
    while (queue->head) {
        Task* task = dequeue_task(queue);
        printf("[Task %d] Running...\n", task->task_id);
        
        Effect current = task->computation;
        
        if (current.tag == EFF_RETURN) {
            printf("[Task %d] Completed\n", task->task_id);
            free(task);
            continue;
        }
        
        if (current.tag == EFF_ASYNC) {
            printf("[Task %d] Yielding (async operation)..\n", task->task_id);
            // Simulate async work completing later
            task->computation = current.continuation->resume(
                current.continuation, 
                NULL
            );
            task->resumed++;
            enqueue_task(queue, task->computation); // Re-queue
            free(task);
            continue;
        }
        
        // Handle other effects..
        free(task);
    }
    
    printf("-- All Tasks Done --\n");
}
