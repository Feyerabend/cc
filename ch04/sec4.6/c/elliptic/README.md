
## Elliptic Curve Cryptography

Elliptic Curve Cryptography (ECC) is a form of public-key cryptography
based on the algebraic structure of elliptic curves over finite fields.
It's widely used in modern security systems (like HTTPS, Bitcoin, and
secure messaging) because it provides strong security with smaller key
sizes compared to older methods like RSA. This means faster computations
and less resource usage, making it ideal for devices with limited power,
such as smartphones or IoT gadgets.


#### What It Is

An elliptic curve is defined by an equation like \( y^2 = x^3 + ax + b \)
(in this case, \( a = 1 \), \( b = 6 \)) over a finite field (here, modulo
a prime \( p = 17 \)). Points on the curve are pairs \( (x, y) \) that
satisfy the equation, plus a special "point at infinity" which acts like
a neutral element (similar to zero in addition).

The key idea is that these points form a finite group under a specific
"addition" operation. You can add points together or multiply a point by
a scalar (an integer), creating a cyclic group where operations are easy
to compute but hard to reverse— this is the foundation of cryptographic
security. For example, knowing a base point \( G \) and a multiple
\( Q = kG \), it's computationally infeasible to find \( k \) (the discrete
logarithm problem) if the curve is large enough.

#### How It Works
- *Point Addition*: To add two distinct points \( P \) and \( Q \), draw
  a line through them; it intersects the curve at a third point \( R' \),
  and \( R \) is the reflection of \( R' \) over the x-axis. If \( P = Q \),
  it's "doubling": use the tangent line instead.
- *Handling Infinity*: Adding a point to its "negative" (reflection over
  x-axis) gives infinity.
- *Scalar Multiplication*: Repeated addition (e.g., \( kG = G + G +
  \dots + G \), \( k \) times), optimized via "double-and-add" for efficiency.
- *Modular Arithmetic*: All operations are done modulo \( p \) to keep numbers
  finite and ensure the group is cyclic. Modular inverses (via extended Euclidean
  algorithm) are crucial for slopes in addition/doubling.

In practice, real ECC uses much larger primes (e.g., 256-bit) for security,
but this demo uses a tiny field to illustrate concepts manually.

#### Why It's Used
ECC leverages the elliptic curve discrete logarithm problem (ECDLP), which
is harder to solve than factoring large numbers (RSA's basis). This allows
equivalent security with shorter keys: a 256-bit ECC key matches a 3072-bit
RSA key in strength. It's efficient for key exchange (e.g., ECDH), digital 
ignatures (e.g., ECDSA), and encryption. The "why" here is educational:
this setup shows how points cycle through a small group (order 20 in this
curve), demonstrating closure, identity, inverses, and
associativity--properties essential for crypto protocols.

### About the Code
This is an educational C program implementing basic ECC operations
on the curve \( y^2 = x^3 + x + 6 \mod 17 \). It defines a `Point`
struct with x, y, and an infinity flag. Key functions include:
- `is_on_curve`: Verifies if a point satisfies the equation.
- `mod_inverse`: Computes modular inverses using the extended Euclidean
   algorithm.
- `point_double` and `point_add`: Implement doubling and addition,
   handling special cases like infinity or vertical lines.
- `scalar_mult`: Uses double-and-add for efficient \( kG \).
- In `main`, it starts with base point \( G = (2, 4) \), prints multiples
  up to the cycle (reaches infinity at 20G, showing group order 20),
  and demos scalar multiplication (e.g., 7G).

The code is simple and non-optimised for clarity, focusing on math over
performance or security. It's great for learning but not production-ready
(real libs like OpenSSL handle big integers and secure curves).


