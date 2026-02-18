#include <stdio.h>
#include "queue.h"

typedef struct {
    int task_id;
    int priority;  // not used in FIFO, but could extend to priority queue
} Task;

void simulate_task_scheduler() {
    printf("-- Task Scheduler Simulation (FIFO Queue) --\n\n");
    
    Queue* ready_queue = queue_create(10);
    
    // Enqueue tasks as they arrive
    printf("Tasks arriving:\n");
    for (int i = 1; i <= 5; i++) {
        queue_enqueue(ready_queue, i * 100);
        printf("  Task T%d added to queue\n", i * 100);
    }
    
    printf("\nProcessing tasks (FIFO order):\n");
    int task_id;
    while (queue_dequeue(ready_queue, &task_id)) {
        printf("  Executing Task T%d\n", task_id);
    }
    
    printf("\nQueue is now %s\n", 
           queue_is_empty(ready_queue) ? "empty" : "not empty");
    
    queue_destroy(ready_queue);
}

int main(void) {
    simulate_task_scheduler();
    return 0;
}
