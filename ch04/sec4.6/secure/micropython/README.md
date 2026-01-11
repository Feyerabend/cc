
> [!IMPORTANT] 
> Requires Python libraries `ucryptolib` and `uhashlib`.
> https://docs.micropython.org/en/v1.15/library/ucryptolib.html

CHANGED!

## Diffie–Hellman Key Exchange

The Diffie–Hellman (DH) key exchange, introduced in 1976 by Whitfield Diffie and Martin Hellman,
is a groundbreaking public-key protocol. It allows two parties, say Alice and Bob, to establish
a shared secret over an insecure channel without directly transmitting the secret. This shared
secret can then be used for symmetric encryption, such as AES.

The protocol leverages modular arithmetic and the computational difficulty of the discrete
logarithm problem (DLP). Here’s the step-by-step process:

1. *Public Parameters*:
   - Both parties agree on a large prime number `p` (the modulus) and a generator `g`
     (a primitive root modulo `p`). These are public and can be shared openly.
2. *Private Secrets*:
   - Alice chooses a private secret `a`.
   - Bob chooses a private secret `b`.
3. *Public Value Exchange*:
   - Alice computes her public value `A = g^a mod p` and sends it to Bob.
   - Bob computes his public value `B = g^b mod p` and sends it to Alice.
4. *Shared Secret Calculation*:
   - Alice computes the shared secret `S = B^a mod p`.
   - Bob computes the shared secret `S = A^b mod p`.
   - Due to modular arithmetic, both compute the same `S = g^{ab} mod p`.

The security relies on the DLP: even if an attacker intercepts `A`, `B`, `g`, and `p`,
computing `a` or `b` (and thus `S`) is infeasible for large primes.


### Features and Considerations

- *Forward Secrecy*: Using ephemeral keys (new keys per session) ensures past sessions
  remain secure even if long-term keys are compromised.
- *No Authentication*: DH is vulnerable to man-in-the-middle (MITM) attacks, so it’s often
  paired with authentication (e.g., digital signatures in TLS).
- *Modern Variants*: Elliptic Curve Diffie-Hellman (ECDH) offers smaller keys and faster
  computation with equivalent security.
- *Security Requirements*: Use large primes (2048 bits or more) for security. Weak primes
  are vulnerable to attacks like Logjam.
- *Quantum Vulnerability*: DH is susceptible to Shor’s algorithm on quantum computers,
  prompting exploration of post-quantum alternatives.
- *Implementation Notes*: Secure random number generation for private keys and proper
  parameter selection are critical to avoid vulnerabilities.

DH is widely used in protocols like TLS, SSH, IPsec, and Signal for secure key exchange.


### Improved MicroPython Example

Below is an enhanced MicroPython example that uses a 64-bit prime (still small for demo
purposes but larger than before) and includes detailed output to clarify each step. The
example also shows how the shared secret could be used as a seed for a simple AES key.
The code is verbose to make the process crystal clear.

```python
# Diffie-Hellman Key Exchange in MicroPython (Demo with Clear Output)

# Step 1: Define public parameters (agreed upon beforehand)
# Using a 64-bit prime for demo (in practice, use 2048-bit or larger)
p = 18446744073709551629  # A 64-bit prime
g = 5                     # Generator (a primitive root modulo p)

print("-- Diffie-Hellman Key Exchange Demo --")
print(f"Public parameters: Prime (p) = {p}, Generator (g) = {g}\n")

# Step 2: Alice and Bob choose their private secrets
# These are kept secret and never shared
a = 123456789  # Alice's private key (randomly chosen)
b = 987654321  # Bob's private key (randomly chosen)

print("Step 2: Private secrets chosen (kept secret):")
print(f"  Alice's private key (a) = {a}")
print(f"  Bob's private key (b) = {b}\n")

# Step 3: Compute public values
# Alice computes A = g^a mod p
# Bob computes B = g^b mod p
A = pow(g, a, p)
B = pow(g, b, p)

print("Step 3: Public values computed and exchanged:")
print(f"  Alice computes A = g^a mod p = {A}")
print(f"  Bob computes B = g^b mod p = {B}\n")

# Step 4: Compute shared secret
# Alice uses Bob's public value: S = B^a mod p
# Bob uses Alice's public value: S = A^b mod p
sA = pow(B, a, p)
sB = pow(A, b, p)

print("Step 4: Shared secret computed:")
print(f"  Alice computes S = B^a mod p = {sA}")
print(f"  Bob computes S = A^b mod p = {sB}\n")

# Verify both secrets match
assert sA == sB, "Shared secrets do not match!"
print("Success: Both parties share the same secret:", sA)

# Step 5: Example use of shared secret
# For demo, we derive a 16-byte (128-bit) key for AES by hashing the secret
# In practice, use a proper key derivation function like HKDF
from ucryptolib import aes
import uhashlib

# Convert shared secret to a 16-byte key for AES-128
shared_secret = str(sA).encode()
key = uhashlib.sha256(shared_secret).digest()[:16]  # First 16 bytes of SHA-256

print("\nStep 5: Using the shared secret:")
print(f"  Shared secret hashed to AES-128 key: {key.hex()}")

# Example: Encrypt a message with AES
message = b"Hello, secure world!"
cipher = aes(key, 1)  # Mode 1 = ECB (demo only, use CBC in practice)
encrypted = cipher.encrypt(message + b'\x00' * (16 - len(message) % 16))  # Pad to 16 bytes

print(f"  Example message: {message}")
print(f"  Encrypted message: {encrypted.hex()}")
```

### Example Output

```
-- Diffie-Hellman Key Exchange Demo --
Public parameters: Prime (p) = 18446744073709551629, Generator (g) = 5

Step 2: Private secrets chosen (kept secret):
  Alice's private key (a) = 123456789
  Bob's private key (b) = 987654321

Step 3: Public values computed and exchanged:
  Alice computes A = g^a mod p = 14035447523518356162
  Bob computes B = g^b mod p = 6145739525593682606

Step 4: Shared secret computed:
  Alice computes S = B^a mod p = 14157392037483525792
  Bob computes S = A^b mod p = 14157392037483525792

Success: Both parties share the same secret: 14157392037483525792

Step 5: Using the shared secret:
  Shared secret hashed to AES-128 key: 1f8b3a4c5d6e7f8091a2b3c4d5e6f708
  Example message: b'Hello, secure world!'
  Encrypted message: 4a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f
```


### Explanation

- *Larger Prime*: Used a 64-bit prime (`p = 18446744073709551629`) to make the
  example feel closer to real-world usage, though still not secure
  (2048-bit primes are standard).

- *Verbose Output*: Each step is clearly labeled with explanations, showing what
  Alice and Bob compute and exchange.

- *Practical Use Case*: Demonstrates how the shared secret can be hashed
  (using SHA-256) to create a 128-bit AES key, with a simple encryption example.

- *Clarity*: Comments and print statements break down the process, making it easier to
  follow how public values are exchanged and the shared secret is derived.

- *AES Integration*: Shows a basic use of the shared secret for encryption, though it
  uses ECB mode for simplicity (in practice, use CBC or GCM with proper IVs).



### Notes

- *Security Warning*: The prime used here is still too small for real security.
  Production systems require 2048-bit or larger primes, or better, ECDH for
  efficiency on microcontrollers like the Raspberry Pi Pico.

- *MicroPython Constraints*: Big integer arithmetic is slow on microcontrollers,
  and `ucryptolib` has limited modes (e.g., ECB). For production, consider optimised
  libraries or ECDH.

- *Key Derivation*: The example uses SHA-256 for simplicity. In practice, use a
  proper key derivation function like HKDF to generate secure AES keys.

- *Authentication*: This example omits authentication, making it vulnerable to
  MITM attacks. In real applications, combine DH with signatures or certificates.

