
#include <stdio.h>
#include <stdlib.h>

#include "effect.h"


// Cooperative multitasking
// This is a very basic cooperative multitasking
// runtime that can run multiple tasks that yield on async effects.

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

// Init a new task queue
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

// Dequeue a task from the queue
Task* dequeue_task(TaskQueue* q) {
    if (!q->head) return NULL;
    Task* t = q->head;
    q->head = t->next;
    if (!q->head) q->tail = NULL;
    return t;
}

void run_async(TaskQueue* queue) {
    printf("-- Async Runtime Starting --\n\n");

    while (queue->head) {
        Task* task = dequeue_task(queue);
        Effect current = task->computation;

        if (current.tag == EFF_RETURN) {
            printf("[Task %d] Completed\n", task->task_id);
            free(task);
            continue;
        }

        if (current.tag == EFF_ASYNC) {
            printf("[Task %d] Yielding -- re-queuing behind others\n", task->task_id);
            // Advance the computation past the yield point, then re-queue it.
            // Other tasks already in the queue run before this one is picked up again.
            Effect next = current.continuation->resume(current.continuation, NULL);
            enqueue_task(queue, next);
            free(task);
            continue;
        }

        // Unhandled effect
        printf("[Task %d] Unhandled effect %d\n", task->task_id, current.tag);
        free(task);
    }

    printf("\n-- All Tasks Done --\n");
}


/* A simple two-step task: print a message, yield, then print again. */

typedef struct {
    int step;
    int id;
} WorkCtx;

Effect work_resume(Continuation* k, void* value) {
    WorkCtx* ctx = k->context;

    switch (ctx->step) {
        case 0:
            printf("[Work %d] Starting\n", ctx->id);
            ctx->step = 1;
            return eff_async(NULL, NULL, k);

        case 1:
            printf("[Work %d] Resumed after yield\n", ctx->id);
            return eff_return(NULL);

        default:
            return eff_return(NULL);
    }
}


int main() {
    TaskQueue queue = {NULL, NULL, 0};

    // Spawn three tasks; each will yield once before completing.
    for (int i = 0; i < 3; i++) {
        WorkCtx* ctx = malloc(sizeof(WorkCtx));
        ctx->step = 0;
        ctx->id   = i;

        Continuation* k = malloc(sizeof(Continuation));
        k->resume  = work_resume;
        k->context = ctx;
        k->parent  = NULL;

        Effect eff = k->resume(k, NULL);
        enqueue_task(&queue, eff);
    }

    run_async(&queue);
    return 0;
}
