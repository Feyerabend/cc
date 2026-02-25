/*
 * Miller-Rabin Primality Test
 * 
 * Determines whether n is prime. Instead of trial division up to sqrt(n),
 * it picks random "witnesses" and checks a number-theoretic property that
 * all primes satisfy but most composites violate.
 *
 * Core idea:
 *   If n is prime, then for ANY base a: a^(n-1) ≡ 1 (mod n)  [Fermat]
 *   More strongly: write n-1 = 2^r * d (d odd).
 *   Then either a^d ≡ 1, or a^(2^i * d) ≡ -1 for some i in [0, r-1].
 *   A composite that passes this test for base a is called a strong
 *   pseudoprime to base a. For a random a, this happens with probability
 *   at most 1/4. So k independent rounds give a false-positive rate
 *   of at most (1/4)^k.
 *
 * Two flavors of randomised algorithm:
 *   Las Vegas   -- always correct, random in *speed*    (e.g. quicksort)
 *   Monte Carlo -- always fast, random in *correctness* (this algorithm)
 *
 * With k=20 rounds the error probability is < 10^-12, good enough for
 * cryptographic key generation in practice.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <unistd.h>

/* Modular exponentiation: (base^exp) mod m, using 128-bit to avoid overflow. */
static uint64_t powmod(uint64_t base, uint64_t exp, uint64_t m) {
    uint64_t result = 1;
    base %= m;
    while (exp > 0) {
        if (exp & 1)
            result = (unsigned __int128)result * base % m;
        base = (unsigned __int128)base * base % m;
        exp >>= 1;
    }
    return result;
}

/* One Miller-Rabin round with witness a. Returns 0 if n is definitely composite. */
static int witness_pass(uint64_t n, uint64_t a, uint64_t d, int r) {
    uint64_t x = powmod(a, d, n);
    int i;

    if (x == 1 || x == n - 1)
        return 1;

    for (i = 0; i < r - 1; i++) {
        x = (unsigned __int128)x * x % n;
        if (x == n - 1)
            return 1;
    }
    return 0;
}

/* Returns 1 if n is probably prime, 0 if definitely composite.
 * Error probability <= (1/4)^rounds. */
int miller_rabin(uint64_t n, int rounds) {
    uint64_t d = n - 1;
    int r = 0, i;

    if (n < 2)  return 0;
    if (n == 2) return 1;
    if (n % 2 == 0) return 0;

    /* Factor out powers of 2: n-1 = 2^r * d */
    while (d % 2 == 0) { d /= 2; r++; }

    for (i = 0; i < rounds; i++) {
        uint64_t a = 2 + (uint64_t)rand() % (n - 3);
        if (!witness_pass(n, a, d, r))
            return 0;
    }
    return 1;
}

int main(void) {
    uint64_t candidates[] = {
        7, 100, 104729, 1000003, 15487469,
        /* A Mersenne prime: 2^31 - 1 */
        2147483647ULL,
        /* A large composite */
        2147483646ULL,
        /* A large semiprime (two primes multiplied) */
        6700417ULL * 641ULL
    };
    int n = sizeof(candidates) / sizeof(candidates[0]);
    int rounds = 20;
    int i;

    srand((unsigned int)time(NULL) ^ (unsigned int)getpid());

    printf("%-20s  %s  (%d rounds, error < 1/4^%d)\n",
           "n", "result   ", rounds, rounds);
    printf("%-20s  %s\n", "-------------------", "---------");

    for (i = 0; i < n; i++) {
        printf("%-20llu  %s\n",
               (unsigned long long)candidates[i],
               miller_rabin(candidates[i], rounds) ? "PRIME" : "composite");
    }

    return 0;
}
