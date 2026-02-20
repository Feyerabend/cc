#include <stdio.h>

int fibonacci(int n) {
    if (n <= 1)
        return n;

    int prev2 = 0;  // fib(0)
    int prev1 = 1;  // fib(1)
    int current;

    for (int i = 2; i <= n; i++) {
        current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }

    return prev1;
}


int main() {
    int n = 10; // compute Fibonacci number
    printf("Fibonacci(%d) = %d\n", n, fibonacci(n));
    return 0;
}
