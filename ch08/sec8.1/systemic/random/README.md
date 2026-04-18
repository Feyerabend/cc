
## The Evolution of Randomness in Computing and Cryptography: From Ancient Dice to Quantum Generators

The relationship between randomness and mathematics has ancient roots. For thousands of years,
humans used physical processes to generate randomness--casting lots, throwing bones, spinning
wheels--both for entertainment and divination. Ancient civilisations like the Babylonians,
Egyptians, and Chinese employed various randomisation devices for games and decision-making.
The Chinese I Ching dating back to approximately 1000 BCE utilised coin tosses to generate
one of 64 hexagrams for divination purposes.[^ching]

[^ching]: https://en.wikipedia.org/wiki/I_Ching_divination

Mathematical interest in randomness only began to formalise with the development of probability
theory in the 17th century, when Blaise Pascal and Pierre de Fermat analysed gambling problems
in their famous correspondence of 1654. Their work was later expanded by mathematicians like
Christiaan Huygens, Jacob Bernoulli, and Pierre-Simon Laplace. This led to a formal understanding
of random events, distributions, and expectation, but the randomness here was always tied to
physical uncertainty, not computational methods.[^points]

[^points]: See e.g. https://en.wikipedia.org/wiki/Problem_of_points

The quest for randomness in computing emerged with the dawn of electronic computation in the
mid-20th century. John von Neumann, a pioneer of computer science, confronted the problem of
generating random numbers for [Monte Carlo](./data/monte/) simulations used in nuclear
research during the 1940s. He recognised the inherent paradox in this task, famously quipping:
"Anyone who attempts to generate random numbers by deterministic means is, of course,
living in a state of sin." Nevertheless, he proposed the *middle-square method* (1946),
one of the first algorithmic attempts: take a number, square it, and extract the middle
digits as the next "random" number. Unfortunately, this method often degenerated into short,
repeating cycles, making it unreliable for serious applications.

By the 1950s, *Linear Congruential Generators (LCGs)* became popular due to their simplicity.
These work by iterating the formula:

```math
 X_{n+1} = (aX_n + c) \mod m 
```

where \(a\), \(c\), and \(m\) are carefully chosen constants. While fast and easy to implement,
LCGs were soon found to exhibit predictable patterns, especially when used in cryptography.
An extremly simple implementation in C:
```c
#include <stdio.h>
#include <time.h>
x = time(0);
// or a more fixed number  unsigned x = 42;
// (but will not change the pseudo-random principle)
unsigned rnd() {
    x = x * 1664525 + 1013904223;
    return x;
}
int main() {
    for (int i = 0; i < 10; i++)
        printf("%u\n", rnd());
}
```

A famous example is IBM's *RANDU* generator from the 1960s, which produced numbers that,
when plotted in 3D space, revealed hyperplanes--a clear sign of non-randomness.

The need for better methods led to more sophisticated algorithms. The *Mersenne Twister*
(1997) improved statistical properties, making it suitable for simulations (though still
not cryptographically secure). Meanwhile, cryptography demanded *unpredictable* randomness,
leading to *Cryptographically Secure Pseudorandom Number Generators (CSPRNGs)* like
*Blum Blum Shub* (1986), based on number theory, and later *Fortuna* and *ChaCha20*.


### True Randomness vs. Pseudorandomness

Understanding randomness in computing requires distinguishing between two fundamental concepts:

*Pseudorandomness* is generated algorithmically. Given the same initial *seed*, a pseudorandom
number generator (PRNG) will always produce the same sequence. This determinism is useful in
simulations (e.g., video games, scientific modelling) but potentially disastrous in cryptography
if the seed is guessable.

*True randomness*, in contrast, comes from physical processes--thermal noise in circuits, radioactive
decay, or even atmospheric static. The *LavaRand* project by Cloudflare famously uses lava lamps as
a chaotic entropy source. Hardware Random Number Generators (HRNGs), like Intel's *RDRAND* instruction,
exploit microscopic fluctuations in silicon to generate unpredictable values.

However, true randomness generators are often *slow* and can suffer from bias (e.g., a physical coin
toss might favour heads 51% of the time). Thus, in practice, most systems use *hybrid approaches*:
a hardware entropy source seeds a CSPRNG, which then generates randomness efficiently.

The following table helps compare the conceptual differences between random number generation approaches:

| Type                                    | Source                               | Predictability                | Typical Use Case            |
|-----------------------------------------|--------------------------------------|-------------------------------|-----------------------------|
| TRNG (True RNG)                         | Physical process (quantum, thermal)  | Unpredictable                 | Key generation, lotteries   |
| PRNG (Pseudo RNG)                       | Algorithmic, seeded                  | Predictable if seed known     | Simulations, games          |
| CSPRNG (Cryptographically Secure PRNG)  | Algorithmic + cryptographic hardness | Computationally unpredictable | Cryptography, secure tokens |


### Mathematical Underpinnings

Randomness is rigorously tested using statistical methods such as Diehard and NIST STS test suites
to detect patterns, alongside theoretical measures like Kolmogorov complexity, which defines a truly
random sequence as one that cannot be compressed.

For pseudorandomness, security hinges on *computational hardness*--e.g., assuming factoring large
primes is intractable (as in *Blum Blum Shub*).

In complexity theory, a sequence is pseudorandom if no polynomial-time algorithm can tell it apart
from a truly random sequence with significant advantage. The modern theory of pseudorandomness is
deeply linked to computational hardness assumptions--such as the hardness of factoring large integers,
discrete logarithms, or solving lattice problems. These hardness assumptions are also foundational
to cryptography.

It's worth noting that randomness is also studied in pure mathematics under the umbrella of measure
theory, ergodic theory, and Kolmogorov complexity. The latter deals with the idea that a string is
random if it has no shorter description than itself--in other words, it's incompressible. This
theoretical notion of randomness aligns with intuition: if there's no pattern, the data is random.
However, Kolmogorov complexity is uncomputable in general, which places limits on our ability to
even detect randomness with certainty.


### The Critical Role of Randomness in Cryptography

Cryptography relies fundamentally on randomness for:
- Generating encryption keys (if predictable, the system breaks)
- Creating *nonces* (numbers used once to prevent replay attacks)
- Salting passwords (to thwart rainbow tables)

Secure encryption schemes, like those used in HTTPS, VPNs, and messaging apps, rely on keys that
are either randomly generated or derived from secure pseudorandom processes. If randomness is
predictable, an attacker might reconstruct the key and decrypt the message.

Failures in random number generation have led to catastrophic breaches. In 1995, Netscape's SSL
implementation used the system time (predictable!) as a seed, allowing hackers to decrypt traffic.
Similarly, the *Dual_EC_DRBG* scandal (2006) revealed a suspected NSA backdoor in a NIST-standardised
PRNG, undermining trust in "approved" algorithms.

Modern systems avoid such pitfalls by using cryptographically secure PRNGs (e.g., `/dev/urandom` on Linux),
ensuring sufficient entropy from hardware sources, and regularly reseeding generators to prevent state recovery.


### Hardware Randomness: Implementation and Challenges

Hardware random number generators attempt to derive randomness from physical processes. Quantum mechanics
gives us real unpredictability, so some TRNGs use radioactive decay, photon emission timing, or thermal
noise. For example, Intel's processors have included hardware random number generators (Intel Secure Key,
formerly known as RdRand) that sample thermal noise from transistor junctions. Similarly, VIA Technologies
introduced the Padlock Security Engine with a hardware random number generator in their processors as
early as 2003.

These provide entropy, which is then "stretched" into longer pseudorandom sequences using cryptographic
functions like SHA-256. The result is hybrid: true randomness seeds the process, but fast generation
uses PRNGs. This is common in operating systems: Linux's `/dev/random` and `/dev/urandom` work in such a way.

Yet, hardware randomness isn't perfect. Raw entropy sources often exhibit bias, where a thermal sensor
may favour certain values. Additionally, there's manipulation risk, as a compromised HRNG could feed
predictable data to downstream systems.

Thus, *post-processing* (e.g., whitening via hash functions) is critical to ensure the quality and security
of the generated random numbers.


### Modern Applications and Future Directions

Today's applications of randomness in computing extend far beyond basic simulation and cryptography.
Random algorithms play crucial roles in machine learning through random initialisation and stochastic
gradient descent techniques. They're integral to load balancing in distributed systems, ensuring no
single node becomes a bottleneck. In privacy research, randomness powers differential privacy techniques
that protect individual data while allowing aggregate analysis. Meanwhile, quantum computing represents
a paradigm where randomness isn't just a tool but intrinsic to the computation model itself.

Another fascinating application is in randomised algorithms, which often provide elegant solutions to
problems that deterministic approaches struggle with. For example, the Miller-Rabin primality test uses
random sampling to determine if a number is probably prime with remarkable efficiency. Similarly,
randomised quicksort achieves expected O(n log n) performance by randomly selecting pivot elements,
avoiding worst-case scenarios of deterministic approaches.

As computing continues to evolve, so do our approaches to randomness. Quantum random number generators
promise "true" randomness based on quantum mechanical principles. Meanwhile, post-quantum cryptography
is developing new algoritms that remain secure even against quantum computers, often requiring new
approaches to randomness.

From von Neumann's flawed middle-square method to quantum RNGs, the pursuit of randomness mirrors
computing's evolution. Today, cryptography leans on *hybrid systems*: hardware entropy feeding robust
algorithms. Yet, the battle continues--against entropy starvation in virtual machines, algorithmic
biases, and covert backdoors.

The challenge remains: use enough unpredictability to ensure security and correctness, but generate
it efficiently and safely within fundamentally deterministic machines.


### References

1. Knuth, D. E. (1997). *The Art of Computer Programming, Volume 2: Seminumerical Algorithms*. Addison-Wesley Professional.

2. Goldreich, O. (2001). *Foundations of Cryptography: Basic Tools*. Cambridge University Press.

3. Ferguson, N., Schneier, B., & Kohno, T. (2010). *Cryptography Engineering: Design Principles and Practical Applications*. Wiley.

4. Menezes, A. J., van Oorschot, P. C., & Vanstone, S. A. (1996). *Handbook of Applied Cryptography*. CRC Press.

5. L'Ecuyer, P. (2017). "History of Uniform Random Number Generation." *Proceedings of the 2017 Winter Simulation Conference*.

6. Eastlake, D., Schiller, J., & Crocker, S. (2005). *RFC 4086: Randomness Requirements for Security*. Internet Engineering Task Force.

7. Barker, E., & Kelsey, J. (2015). *NIST Special Publication 800-90A Revision 1: Recommendation for Random Number Generation Using Deterministic Random Bit Generators*. National Institute of Standards and Technology.

8. Marsaglia, G. (1996). "DIEHARD: A Battery of Tests of Randomness." Florida State University.

9. Salmon, J. K., Moraes, M. A., Dror, R. O., & Shaw, D. E. (2011). "Parallel Random Numbers: As Easy as 1, 2, 3." *Proceedings of 2011 International Conference for High Performance Computing, Networking, Storage and Analysis*.

10. Bernstein, D. J. (2008). "The Salsa20 Family of Stream Ciphers." *New Stream Cipher Designs*. Springer.
