#include <stdio.h>

// Compute GCD
int gcd(int a, int b) {
    if (b == 0) {
        return a;
    }
    return gcd(b, a % b);
}

// Calculate modular inverse
int mod_inverse(int e, int phi) {
    for (int d = 1; d < phi; d++) {
        if ((e * d) % phi == 1) {
            return d;
        }
    }
    return -1; // No modular inverse found
}

// Perform modular exponentiation
int mod_exp(int base, int exp, int mod) {
    int result = 1;
    while (exp > 0) {
        if (exp % 2 == 1) { // If exponent is odd
            result = (result * base) % mod;
        }
        base = (base * base) % mod; // Square the base
        exp /= 2; // Divide exponent by 2
    }
    return result;
}

int main() {
    // Define small prime numbers
    int p = 61; // Prime number 1
    int q = 53; // Prime number 2
    int n = p * q; // n = 61 * 53 = 3233
    int phi = (p - 1) * (q - 1); // phi(n) = 60 * 52 = 3120

    // Choose public exponent
    int e = 17; // Satisfies 1 < e < phi and gcd(e, phi) = 1
    // Calculate private exponent
    int d = mod_inverse(e, phi);

    printf("Public Key: (e: %d, n: %d)\n", e, n);
    printf("Private Key: (d: %d)\n", d);

    // Original message
    int message = 65;
    printf("Original Message: %d\n", message);

    // Encryption
    int ciphertext = mod_exp(message, e, n);
    printf("Encrypted Message: %d\n", ciphertext);

    return 0;
}
