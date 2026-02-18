#include <stdio.h>

#define MAX 100

int fibMemo[MAX];

int fibonacci(int n) {
    if (n <= 1) 
        return n;
    if (fibMemo[n] != -1) 
        return fibMemo[n];
    
    fibMemo[n] = fibonacci(n - 1) + fibonacci(n - 2);
    return fibMemo[n];
}

int main() {
    int n = 10; // compute Fibonacci number
    for (int i = 0; i < MAX; i++)
        fibMemo[i] = -1; // init memoization array with -1
    
    printf("Fibonacci(%d) = %d\n", n, fibonacci(n));
    return 0;
}
