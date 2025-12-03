#include <stdio.h>

// Convert a decimal number to BCD
void decimalToBCD(int decimal) {
    int digit;
    printf("BCD representation of %d: ", decimal);
    // Each digit from left to right
    while (decimal > 0) {
        digit = decimal % 10; // Get rightmost digit
        // Print 4-bit BCD for the digit (padded to 4 bits)
        printf("%04d ", digit); // %04d ensures 4-bit output (e.g., 0001 for 1)
        decimal /= 10; // Remove processed digit
    }
    printf("\n");
}

int main() {
    int number = 123;
    decimalToBCD(number);
    return 0;
}

