#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// Convert binary to Gray code
unsigned int binary_to_gray(unsigned int n) {
    return n ^ (n >> 1);
}

// Convert Gray code back to binary
unsigned int gray_to_binary(unsigned int g) {
    unsigned int n = g;
    while (g >>= 1)
        n ^= g;
    return n;
}

// Simulate a 1-bit glitch with a given probability (0.0-1.0)
unsigned int simulate_bit_glitch(unsigned int value, double glitch_chance, int bits) {
    if ((rand() / (double)RAND_MAX) < glitch_chance) {
        int bit_to_flip = rand() % bits;
        return value ^ (1 << bit_to_flip);
    }
    return value;
}

// Helper to print binary
void print_binary(unsigned int n, int width) {
    for (int i = width - 1; i >= 0; --i)
        putchar((n & (1 << i)) ? '1' : '0');
}


int main() {
    const int bits = 4;
    const double glitch_probability = 0.2; // 20% chance of glitch
    const int max_value = 1 << bits;

    srand((unsigned int)time(NULL));

    printf("Step | True Dec | Binary    | Read Bin | Error | Gray     | Read Gray | Error\n");
    printf("-------------------------------------------------------------------------------\n");

    for (int i = 0; i < max_value - 1; ++i) {
        unsigned int true_binary = i + 1;
        unsigned int true_gray = binary_to_gray(true_binary);

        // Simulate glitch in binary read
        unsigned int glitch_bin = simulate_bit_glitch(true_binary, glitch_probability, bits);
        unsigned int glitch_gray = simulate_bit_glitch(true_gray, glitch_probability, bits);

        unsigned int read_bin = glitch_bin;
        unsigned int read_gray = gray_to_binary(glitch_gray);

        printf(" %2d  |    %2u     | ", i+1, true_binary);
        print_binary(true_binary, bits);
        printf(" | ");
        print_binary(read_bin, bits);
        printf("  |  %s  | ", read_bin == true_binary ? " OK " : "FAIL");

        print_binary(true_gray, bits);
        printf(" | ");
        print_binary(glitch_gray, bits);
        printf("  |  %s\n", read_gray == true_binary ? " OK " : "FAIL");
    }

    return 0;
}

