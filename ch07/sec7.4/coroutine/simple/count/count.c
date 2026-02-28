#include <stdio.h>
#include <setjmp.h>

jmp_buf main_env;   // Environment for main function
jmp_buf count_env;  // Environment for count function
int count = 0;      // Move count to global scope
int limit = 0;      // Global limit

// Coroutine function that counts from 1 to limit
void count_up_to() {
    // Save coroutine starting point
    if (setjmp(count_env) == 0) {
        // First time setup
        count = 1;
        // Jump back to main immediately after setup
        longjmp(main_env, 1);
    }
    
    // Resume point for the coroutine
    while (count <= limit) {
        printf("%d\n", count);
        count++;
        
        // Yield execution back to main
        if (count <= limit) {
            longjmp(main_env, 1);
        }
    }
    
    // End of coroutine
    printf("Counting complete!\n");
    longjmp(main_env, 2); // Use 2 to signal completion
}

int main() {
    limit = 5;  // Set the limit
    
    // Save the main function state
    int status = setjmp(main_env);
    
    if (status == 0) {
        // First time setup - start the coroutine
        count_up_to();
    } 
    else if (status == 1) {
        // Coroutine yielded, we can do work here
        printf("Back in main, count is now %d\n", count);
        
        // Resume the coroutine
        longjmp(count_env, 1);
    }
    // If status == 2, coroutine is complete
    
    return 0;
}
