// Demo: Shows compiler optimizations in action
// This program has intentional inefficiencies that get optimized away

int demo(int n) {
    // Constant folding examples
    int a = 10 + 20;           // Folded to: 30
    int b = a * 2;             // Could be folded to: 60 (not implemented yet)
    int c = 5 * 6;             // Folded to: 30
    
    // Dead code that never gets used
    int unused1 = 100 + 200;   // Will be eliminated
    int unused2 = 50 * 4;      // Will be eliminated
    
    // Actually used variables
    int result = 0;
    int i = 0;
    
    // Loop with some computation
    while (i < n) {
        if (i < 5) {
            result = result + c;    // c is 30
        } else {
            result = result + i;
        }
        i = i + 1;
    }
    
    return result;
}

int main() {
    int value = demo(10);
    return value;
}
