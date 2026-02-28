#include <stdio.h>
#include <string.h>

int main() {
    char str[] = "Hello,World,How,Are,You";
    char *saveptr;  // each caller maintains its own context
    char *token;
    
    // first call uses the string
    token = strtok_r(str, ",", &saveptr);
    while(token != NULL) {
        printf("Main: %s\n", token);
        
        // safe even if interrupted, as state is explicitly passed
        token = strtok_r(NULL, ",", &saveptr);
    }
    
    return 0;
}
