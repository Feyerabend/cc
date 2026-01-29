// Comprehensive test showing SSA optimizations

int factorial(int n) {
    int result;
    result = 1;
    
    while (n > 1) {
        result = result * n;
        n = n - 1;
    }
    
    return result;
}

int max(int a, int b) {
    int result;
    
    if (a > b) {
        result = a;
    } else {
        result = b;
    }
    
    return result;
}

int constant_example() {
    int a;
    int b;
    int c;
    int d;
    
    a = 5;
    b = 10;
    c = a + b;
    d = c * 2;
    
    return d;
}

int main() {
    int x;
    int y;
    
    x = factorial(5);
    y = constant_example();
    
    return max(x, y);
}
