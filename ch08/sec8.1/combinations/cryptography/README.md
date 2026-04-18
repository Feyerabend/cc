
## Project: From Security, Randomness, and Complexity to Cryptography

You already understand three systemic forces:
- *Security*: systems must behave predictably in the presence of adversaries.
- *Randomness*: some outcomes are unpredictable, either as a hazard or a tool.
- *Complexity*: some problems are computationally hard to solve.

In this project, you will discover that when you need to protect information
from an adversary, these three forces combine into a single inevitable structure:
- *Cryptography*.

The equation you will derive is:
```
Security + Randomness + Complexity  ->  Cryptography
```
Your task is not to start from "cryptography" as a given solution, but to
*reconstruct why it must exist* when you try to communicate securely over
a channel an adversary can observe.

This is a design discovery exercise, not a memorisation one.


### Part 1 - A Thought Experiment: The Eavesdropper

Alice wants to send a message to Bob.
The channel between them is public. Eve can read everything on it.

Alice wants Bob to receive her message. She does not want Eve to understand it.

The simplest approach: agree on a secret beforehand.
Alice shifts every letter by 3. B becomes E. C becomes F.
Bob knows the shift. He reverses it. Eve sees gibberish.

Run it:

```python
def caesar(text, shift):
    result = []
    for ch in text:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            result.append(ch)
    return ''.join(result)

message   = "meet me at midnight"
encrypted = caesar(message, 3)
decrypted = caesar(encrypted, -3)

print("Original: ", message)
print("Encrypted:", encrypted)
print("Decrypted:", decrypted)
```

Eve sees the encrypted text. Can she recover the message?


### Part 2 - Discovering the Attack

Eve does not know the shift. But there are only 25 possible shifts.
She tries them all:

```python
print("Eve tries all shifts:")
for shift in range(26):
    attempt = caesar(encrypted, -shift)
    print(f"  Shift {shift:>2}: {attempt}")
```

One line is readable English. Eve finds it immediately.

The Caesar cipher fails because its *complexity* is too low.
There are only 25 possible keys. An adversary can try all of them trivially.

Security requires that the adversary's search space be so large
that exhaustive search is computationally infeasible.


### Part 3 - Why Randomness Enters

If Alice always uses the same key, Eve can learn patterns.
If Alice uses a predictable key (her birthday, a common word), Eve can guess it.

The key must be *random*: chosen uniformly from a large space,
with no pattern Eve can exploit.

Model the key space:

```python
import random, string

def random_key(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

for length in [4, 8, 16, 32]:
    key        = random_key(length)
    space_size = (26 + 26 + 10) ** length
    print(f"Length {length:>2}: key={key!r:>34}  space={space_size:.2e}")
```

Observe: as key length grows, the space grows exponentially.
At 32 characters, exhaustive search is not feasible on any machine that exists.

But randomness alone is not enough. Eve still needs to *do work* to search.
That work must be provably hard.


### Part 4 - Why Complexity Is the Third Force

Randomness makes the key space large.
Complexity makes searching that space hard.

These are different things. A large space can sometimes be searched cleverly
(if the cipher has structure). Cryptographic security requires that no
clever algorithm exists--only brute force, and brute force is infeasible.

Model the cost of brute force:

```python
GUESSES_PER_SECOND = 1_000_000_000   # 1 billion guesses/second (fast hardware)
SECONDS_PER_YEAR   = 365 * 24 * 3600

def years_to_break(key_bits):
    space = 2 ** key_bits
    seconds = space / GUESSES_PER_SECOND
    return seconds / SECONDS_PER_YEAR

print("Key size | Years to break (brute force)")
for bits in [40, 56, 64, 128, 256]:
    years = years_to_break(bits)
    print(f"  {bits:>3} bits: {years:.2e} years")
```

At 128 bits, the universe is not old enough for brute force to succeed.

This is the role of complexity: it converts randomness (large key space)
into security (infeasible search).


### Part 5 - Your Task: Observe the Three Forces Working Together

Before building any cipher, observe what happens when one force is absent.

```python
import secrets

KEY_SPACE = 2 ** 128   # bits of randomness

def assess(has_security_goal, has_randomness, has_complexity):
    if not has_security_goal:
        return "No goal: no adversary model, nothing to protect"
    if not has_randomness:
        return "Predictable key: Eve can enumerate candidates"
    if not has_complexity:
        return "Weak cipher: structure enables shortcut attacks"
    return "All three present: cryptographic security is achievable"

configs = [
    (True,  False, True),
    (True,  True,  False),
    (True,  True,  True),
]

for s, r, c in configs:
    print(f"Security={s} Randomness={r} Complexity={c}: {assess(s, r, c)}")
```

Each missing force breaks the system in a different way.


### Part 6 - Introduce a Cipher Without Naming It

Now build the simplest structure that uses all three forces.

You will use a *one-time pad*: a key as long as the message,
chosen randomly, XORed with the message byte by byte.

You still do not call it "cryptography". You call it *masking with a secret*.

```python
import secrets

def mask(data: bytes, key: bytes) -> bytes:
    return bytes(d ^ k for d, k in zip(data, key))

message    = b"meet me at midnight"
key        = secrets.token_bytes(len(message))   # truly random

encrypted  = mask(message, key)
decrypted  = mask(encrypted, key)

print("Message:  ", message)
print("Key:      ", key.hex())
print("Encrypted:", encrypted.hex())
print("Decrypted:", decrypted)
```

Without the key, the encrypted bytes reveal nothing about the message.
Every possible plaintext is equally likely. Eve has no foothold.

You have not named what you built. You have built it from the three forces.


### Part 7 - Observe the Emergence

Now compare:

| Scheme                         | Randomness         | Complexity                      | Secure against Eve?   |
|--------------------------------|--------------------|---------------------------------|-----------------------|
| Caesar cipher                  | None (fixed shift) | None (26 options)               | No                    |
| Caesar with random shift       | Some (1 of 26)     | None (26 options)               | Barely                |
| Long random key, weak cipher   | High               | Low                             | No (shortcut attacks) |
| Random key, XOR (one-time pad) | Perfect            | Perfect (information-theoretic) | Yes                   |

This is the moment the equation becomes real:
```
Security + Randomness + Complexity  ->  Cryptography
```

Not as an algorithm to memorise. As an *inevitability*.

If you must communicate securely over a channel an adversary can read,
and the adversary is computationally bounded, and you cannot share a
secret in advance (or the secret must be small), then you are forced
to invent a structure that uses randomness to create unpredictability
and computational complexity to make search infeasible.
That structure is cryptography.


### Part 8 - The Limits of the One-Time Pad

The one-time pad is theoretically perfect. It is also practically unusable:
- The key must be as long as the message.
- The key must be truly random.
- The key must never be reused.
- The key must be shared securely in advance.

That last point is fatal: if you could share the key securely, you could
share the message securely. The problem is circular.

This forces you towards *asymmetric cryptography*: systems where you can
publish a key freely (the public key) and keep one secret (the private key),
such that encrypting with the public key requires the private key to reverse.

The security of these systems rests entirely on *computational complexity*:
the hardness of problems like integer factorisation or discrete logarithm.
If someone finds an efficient algorithm for these problems, the cipher breaks.

Randomness and complexity do not disappear. They deepen.


### Part 9 - Reflection Questions

Answer in writing:

1. Why is a large key space necessary but not sufficient for security?
2. Why must the key be random rather than merely secret?
3. What does "computationally infeasible" mean precisely? Infeasible for whom, by when?
4. Why does the one-time pad fail in practice even though it is theoretically perfect?
5. What would happen to most current cryptography if efficient algorithms for
   integer factorisation were discovered?
6. Where do you encounter cryptography in everyday computing without noticing it?

If you can answer these, you understand cryptography at a systemic level.
Not as a set of algorithms. As a necessity created by deeper forces.

Now. Rename your "masking with a secret" to a *cipher*--and your random
key generation to *key derivation*.
At that point, you are not learning what cryptography is.
You are recognising what you already built.
