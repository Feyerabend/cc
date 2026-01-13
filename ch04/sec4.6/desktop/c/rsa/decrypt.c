#include <stdio.h>

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
    // Public key components
    int e = 17; // Public exponent
    int n = 3233; // Modulus (p * q)

    // Private key component
    int d = 2753; // Private exponent

    // Ciphertext
    int ciphertext = 2790; // From encryption program

    printf("Public Key: (e: %d, n: %d)\n", e, n);
    printf("Private Key: (d: %d)\n", d);
    printf("Encrypted Message: %d\n", ciphertext);

    // Decryption
    int decrypted_message = mod_exp(ciphertext, d, n);
    printf("Decrypted Message: %d\n", decrypted_message);

    return 0;
}
