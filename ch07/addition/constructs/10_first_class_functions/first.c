#include <stdio.h>

int square(int x) {
    return x * x;
}

int apply_function(int (*func)(int), int value) {
    return func(value);
}

int main() {
    int result = apply_function(square, 5);
    printf("%d\n", result);
    return 0;
}
