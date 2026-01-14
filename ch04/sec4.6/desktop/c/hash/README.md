
## Cryptographic Hash Functions Demo

A comprehensive educational demonstration of cryptographic hash functions
and their properties, implemented in C using the FNV-1a hash algorithm.


### Overview

This program demonstrates the fundamental concepts and properties of cryptographic
hash functions through practical examples. While it uses FNV-1a for educational
purposes, it illustrates principles used in production cryptographic systems.


### Features

#### 1. Basic Integrity Checking
Demonstrates how hash functions verify data hasn't been corrupted or tampered
with during transmission or storage.

```
Original Data: IntegrityCheck
Hash: 0x6e8c8e4d
```

#### 2. Avalanche Effect Demonstration
Shows how a single character change produces a completely different
hash value--a critical property for security.

```
Original:  "The quick brown fox"
Modified:  "The quick brown foz"  (one letter changed)
Result: Completely different hash values
```

#### 3. Collision Resistance
Demonstrates that even similar inputs produce vastly different hash outputs,
making it difficult to find two inputs with the same hash.

#### 4. Message Authentication (MAC)
Implements a keyed hash function that verifies both data integrity AND
authenticity using a secret key, similar to HMAC used in real systems.

### Hash Algorithm: FNV-1a

The program uses FNV-1a (Fowler-Noll-Vo hash function, version 1a) which provides:

- *Better distribution* than simple summation methods
- *Fast computation* suitable for demonstrations
- *Good avalanche properties* for educational purposes
- *Industry recognition* as a reliable non-cryptographic hash

#### FNV-1a Parameters
- *Offset basis*: 2166136261
- *Prime*: 16777619
- *Output*: 32-bit hash value

### Key Properties of Cryptographic Hashes

#### 1. Deterministic
Same input always produces the same hash output. Essential for verification.

#### 2. Fast Computation
Hash functions must compute quickly to be practical for large-scale use.

#### 3. Avalanche Effect
Small changes in input cause large, unpredictable changes in output.
Even flipping one bit should change approximately 50% of the hash bits.

#### 4. One-Way Function
Cannot reverse a hash to recover the original data. This is fundamental
to password storage and data protection.

#### 5. Collision Resistant
Computationally infeasible to find two different inputs that produce the same hash value.


### Compilation and Usage

#### Compile
```bash
gcc hash_demo.c -o hash_demo
```

#### Run
```bash
./hash_demo
```

#### Expected Output
The program will display:
- Basic integrity verification examples
- Avalanche effect demonstration
- Collision resistance examples
- Message authentication code (MAC) verification
- Summary of cryptographic hash properties


### Real-World Applications

#### Data Integrity
- File verification (checksums)
- Download verification (comparing hashes)
- Database integrity checks
- Blockchain transaction verification

#### Authentication
- Password storage (hash passwords, never store plaintext)
- Message authentication codes (HMAC)
- Digital signatures
- API request signing

#### Security
- Certificate fingerprints
- Git commit IDs
- Blockchain proof-of-work
- Deduplication in storage systems


### Important Security Note

*For Production Use*: This implementation is educational.
For real-world cryptographic applications, always use
established libraries and algorithms:

- *OpenSSL*: Industry-standard cryptographic library
- *Recommended algorithms*: SHA-256, SHA-3, BLAKE2, BLAKE3
- *For MACs*: Use HMAC-SHA256 or newer authenticated encryption

Never implement your own cryptographic primitives for production security systems.


### Code Structure

```
hash_demo.c
├── fnv1a_hash()                         // Core hash function
├── keyed_hash()                         // Message authentication
├── demonstrate_avalanche_effect()       // Shows sensitivity to changes
├── demonstrate_collision_resistance()   // Shows hash distribution
├── demonstrate_message_authentication() // Shows MAC verification
└── main()                               // Orchestrates demonstrations
```


### Educational Value

This demo is designed to teach:

- How hash functions maintain data integrity
- Why cryptographic properties matter
- The difference between integrity and authenticity
- How keyed hashes prevent tampering
- Practical applications of hash functions


### Further Learning & Projects

To deepen your understanding of cryptographic hash functions:

1. Study production algorithms: SHA-256, SHA-3, BLAKE2
2. Learn about HMAC (Hash-based Message Authentication Code)
3. Explore digital signatures and public key cryptography
4. Understand rainbow tables and why salting is important
5. Research collision attacks (MD5, SHA-1 vulnerabilities)

This code prioritises clarity and educational value over performance.
The FNV-1a implementation is suitable for understanding concepts but
should __not__ be used for security-critical applications.


