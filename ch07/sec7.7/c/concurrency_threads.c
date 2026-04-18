/* concurrency_threads.c — demonstrates POSIX threads (pthreads)
 *
 * Five worker threads each simulate a slow I/O task.
 * With threads they all run concurrently; total wall time is ~2 s, not 10 s.
 *
 * Compile: gcc -o concurrency_threads concurrency_threads.c -lpthread
 * Run:     ./concurrency_threads
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pthread.h>
#include <time.h>

#define NUM_WORKERS 5
#define SLEEP_SEC   2

static pthread_mutex_t print_mutex = PTHREAD_MUTEX_INITIALIZER;

static void *worker(void *arg)
{
    int id = *(int *)arg;
    free(arg);

    pthread_mutex_lock(&print_mutex);
    printf("Worker %d starting\n", id);
    pthread_mutex_unlock(&print_mutex);

    sleep(SLEEP_SEC);   /* Simulate slow I/O (network call, disk read…) */

    pthread_mutex_lock(&print_mutex);
    printf("Worker %d done\n", id);
    pthread_mutex_unlock(&print_mutex);

    return NULL;
}

int main(void)
{
    pthread_t threads[NUM_WORKERS];

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    for (int i = 0; i < NUM_WORKERS; i++) {
        int *id = malloc(sizeof(int));
        *id = i;
        pthread_create(&threads[i], NULL, worker, id);
    }

    for (int i = 0; i < NUM_WORKERS; i++)
        pthread_join(threads[i], NULL);

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed = (t1.tv_sec - t0.tv_sec) +
                     (t1.tv_nsec - t0.tv_nsec) / 1e9;

    printf("\nAll %d workers finished in %.2f s  "
           "(would have taken %d s sequentially)\n",
           NUM_WORKERS, elapsed, NUM_WORKERS * SLEEP_SEC);
    return 0;
}
