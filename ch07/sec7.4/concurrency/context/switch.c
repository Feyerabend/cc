#include <stdio.h>
#include <setjmp.h>

// Global jump buffers for each task and the main scheduler
jmp_buf ctx_main, ctx_a, ctx_b;

// Task states to track completion
int a_done = 0, b_done = 0;
// Track the last task that ran (0 = none, 1 = A, 2 = B)
int last_task = 0;

void taskA() {
    static int i = 0;  // Static to persist state across calls
    while (i < 3) {
        printf("Task A: %d\n", i);
        i++;
        if (setjmp(ctx_a) == 0) {  // Save context, yield to main
            longjmp(ctx_main, 1);   // 1 means "yield"
        }
        return;  // Return to main after resuming to allow switch
    }
    printf("Task A: Completed\n");
    a_done = 1;
    longjmp(ctx_main, 2);  // 2 means "done"
}

void taskB() {
    static int i = 0;  // Static to persist state across calls
    while (i < 3) {
        printf("Task B: %d\n", i);
        i++;
        if (setjmp(ctx_b) == 0) {  // Save context, yield to main
            longjmp(ctx_main, 1);   // 1 means "yield"
        }
        return;  // Return to main after resuming to allow switch
    }
    printf("Task B: Completed\n");
    b_done = 1;
    longjmp(ctx_main, 2);  // 2 means "done"
}

int main() {
    int val;  // To store return value from setjmp

    // Initial setup: start Task A
    if (setjmp(ctx_main) == 0) {
        last_task = 1;  // Mark Task A as running
        taskA();
    }

    // Main scheduler loop
    while (!a_done || !b_done) {
        val = setjmp(ctx_main);  // Save main context
        if (val == 0) {          // Initial call: decide which task to run
            if (last_task == 0 || last_task == 2) {
                if (!a_done) {
                    last_task = 1;  // Mark Task A as running
                    taskA();
                }
            } else if (last_task == 1) {
                if (!b_done) {
                    last_task = 2;  // Mark Task B as running
                    taskB();
                }
            }
        } else if (val == 1) {   // Task yielded
            // Switch to the other task based on last_task
            if (last_task == 1 && !b_done) {
                last_task = 2;  // Switch to Task B
                taskB();
            } else if (last_task == 2 && !a_done) {
                last_task = 1;  // Switch to Task A
                taskA();
            }
        } else if (val == 2) {   // Task finished
            // Continue to check completion and switch
            if (last_task == 1 && !a_done) {
                last_task = 1;
                taskA();
            } else if (last_task == 2 && !b_done) {
                last_task = 2;
                taskB();
            }
        } else {
            fprintf(stderr, "Error: Unexpected value %d\n", val);
            return 1;
        }
    }

    printf("All done\n");
    return 0;
}