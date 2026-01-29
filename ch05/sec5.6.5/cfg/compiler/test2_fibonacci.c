// Test 2: Fibonacci with if/else branches

int fib(int n) {
    if (n <= 1) {
        return n;
    } else {
        int a = fib(n - 1);
        int b = fib(n - 2);
        return a + b;
    }
}

int main() {
    int result = fib(10);
    return result;
}
