// Test 1: Factorial function with dead code and constant folding opportunities

int factorial(int n) {
    int result = 1;
    int dead_var = 5 + 3;  // Dead code - never used
    int x = 2 * 3;         // Constant folding opportunity
    
    while (n > 1) {
        result = result * n;
        n = n - 1;
    }
    
    return result;
}

int main() {
    int x = factorial(5);
    return x;
}
