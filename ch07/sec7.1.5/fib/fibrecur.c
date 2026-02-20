#include <stdio.h>

// own recursive stack implementation to compute Fibonacci numbers iteratively
#define MAX 100
int fibMemo[MAX];


int fibonacci(int n) {
    int stack[MAX];
    int top = -1;

    stack[++top] = n;

    while (top >= 0) {
        int k = stack[top];

        if (k <= 1) {
            fibMemo[k] = k;
            top--;
        }
        else if (fibMemo[k] != -1) {
            top--;
        }
        else if (fibMemo[k - 1] == -1) {
            stack[++top] = k - 1;
        }
        else if (fibMemo[k - 2] == -1) {
            stack[++top] = k - 2;
        }
        else {
            fibMemo[k] = fibMemo[k - 1] + fibMemo[k - 2];
            top--;
        }
    }

    return fibMemo[n];
}


int main() {
    int n = 10; // compute Fibonacci number
    printf("Fibonacci(%d) = %d\n", n, fibonacci(n));
    return 0;
}
