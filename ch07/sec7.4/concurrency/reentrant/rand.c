#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>

// re-entrant random number generator
int rand_safe(unsigned long *next) {
    *next = *next * 1103515245 + 12345;
    return (unsigned int)(*next/65536) % 32768;
}

void handle_signal(int sig) {
    unsigned long local_next = 1;  // each caller maintains its own state
    printf("Signal handler called! Random num in handler: %d\n", 
           rand_safe(&local_next));
}

int main() {
    unsigned long next_main = 1;  // main thread's state

    signal(SIGUSR1, handle_signal);

    printf("Main thread random num: %d\n", rand_safe(&next_main));
    printf("Main thread random num: %d\n", rand_safe(&next_main));

    // simulate interrupt during execution
    raise(SIGUSR1);

    printf("Main thread random num: %d\n", rand_safe(&next_main));
    return 0;
}