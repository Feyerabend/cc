// Test 3: Complex nested control flow with optimization opportunities

int compute(int x, int y) {
    int sum = 0;
    int i = 0;
    
    // Constants that should be folded
    int a = 10 + 20;
    int b = a * 2;
    
    while (i < x) {
        if (i < y) {
            sum = sum + i;
        } else {
            sum = sum + (i * 2);
        }
        i = i + 1;
    }
    
    return sum;
}

int main() {
    int result = compute(10, 5);
    return result;
}
