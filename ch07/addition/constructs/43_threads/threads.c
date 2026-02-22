 // POSIX threads
#include <stdio.h>
#include <pthread.h>

void* say_hello(void* arg) {
    printf("Hello from thread!\n");
    return NULL;
}

int main() {
    pthread_t t;
    pthread_create(&t, NULL, say_hello, NULL);
    pthread_join(t, NULL);
    printf("Back in main thread.\n");
    return 0;
}
