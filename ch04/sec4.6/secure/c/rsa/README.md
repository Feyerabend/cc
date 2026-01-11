
## RSA Encryption and Decryption

RSA (Rivest-Shamir-Adleman) is a cornerstone of asymmetric cryptography, enabling secure data
transmission by using two distinct keys: a public key for encryption and a private key for
decryption. This algorithm leverages the mathematical difficulty of factoring large prime
numbers to ensure security. Below, we explore the key generation, encryption, and decryption
processes, followed by practical implementations in C, enhanced with detailed explanations and
considerations for real-world applications.


### Key Generation

The RSA algorithm begins with generating a pair of keys:

- *Select Prime Numbers*: Choose two large, distinct prime numbers, $p$ and $q$. For example,
  $p = 61$ and $q = 53$ are used in this educational example for simplicity.
- *Compute Modulus*: Calculate $n = p \times q$. The modulus $n$ (e.g., $61 \times 53 = 3233$)
  is a component of both the public and private keys.
- *Calculate Euler's Totient*: Compute $\phi(n) = (p - 1) \times (q - 1)$ (e.g.,
  $(61 - 1) \times (53 - 1) = 60 \times 52 = 3120$).
- *Choose Public Exponent*: Select a public exponent $e$ such that $1 < e < \phi(n)$
  and $\gcd(e, \phi(n)) = 1$. A common choice is $e = 17$, which satisfies these conditions for
  $\phi(n) = 3120$.
- *Compute Private Exponent*: Calculate the private exponent $d$, the modular inverse of
  $e \mod \phi(n)$, such that $(e \times d) \mod \phi(n) = 1$. For $e = 17$, $d = 2753$ in this example.

The public key is the pair $(e, n)$, and the private key is $(d, n)$.


### Encryption

To encrypt a plaintext message:

- *Convert Message*: Represent the plaintext message $m$ as an integer where $0 \leq m < n$. For example, $m = 65$.
- *Compute Ciphertext*: Use the public key $(e, n)$ to calculate the ciphertext $c$ using the formula:
```math
  c \equiv m^e \mod n
```
  For $m = 65$, $e = 17$, and $n = 3233$, compute $c = 65^{17} \mod 3233$, resulting in $c = 2790$.


### Decryption

To decrypt the ciphertext:

- *Recover Message*: Use the private key $(d, n)$ to compute the original message $m$ using:
  \[
  m \equiv c^d \mod n
  \]
  For $c = 2790$, $d = 2753$, and $n = 3233$, compute $m = 2790^{2753} \mod 3233$, yielding $m = 65$.


### Example

Below are two C programs demonstrating RSA encryption and decryption, using small prime numbers for clarity.
In practice, much larger primes (e.g., 2048-bit) are used to ensure security today.


#### Encrypting Program

This program generates the keys, encrypts a message, and outputs the public key and ciphertext.

```c
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
```


#### Decrypting Program

This program uses the public key, private key, and ciphertext to decrypt the message.

```c
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
```


#### Compilation and Execution

To compile the programs:

```bash
gcc encrypt.c -o encrypt
gcc decrypt.c -o decrypt
```

To run the encryption program:

```bash
./encrypt
```

*Expected Output*:
```
Public Key: (e: 17, n: 3233)
Private Key: (d: 2753)
Original Message: 65
Encrypted Message: 2790
```

To run the decryption program (ensure `ciphertext`, `e`, `n`, and `d` match the encryption output):

```bash
./decrypt
```

*Expected Output*:
```
Public Key: (e: 17, n: 3233)
Private Key: (d: 2753)
Encrypted Message: 2790
Decrypted Message: 65
```


### Key Considerations

- *Small Primes*: This example uses small primes ($p = 61$, $q = 53$) for simplicity.
  Real-world RSA requires primes with hundreds of digits to resist factorization attacks.
- *Message Conversion*: The example assumes the message is an integer ($m = 65$). Practical
  implementations convert text to integers (e.g., using ASCII or padding schemes like PKCS#1).
- *Error Handling*: The provided code lacks robust error handling (e.g., checking if a modular
  inverse exists). Production systems should include comprehensive checks.
- *Security*: For secure RSA, use large primes, secure random number generation, and standardised
  padding schemes to prevent attacks like chosen-ciphertext attacks.

This implementation demonstrates the core principles of RSA in a simplified form, suitable for
educational purposes. For real-world applications, use established cryptographic libraries
like OpenSSL or Crypto++ to handle complexities and ensure security.

