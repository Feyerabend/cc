
## Project: From Noise, Errors, and Fault Tolerance to Error Correction

You already understand three systemic forces:
- *Noise*: uncontrolled variation in physical systems that corrupts signals and data.
- *Errors*: outcomes that diverge from expectation--wrong bits, wrong results, wrong state.
- *Fault Tolerance*: the requirement that a system continues operating correctly despite failures.

In this project, you will discover that when these three forces act together,
they leave only one structural response:
- *Error Correction*.

The equation you will derive is:
```
Noise + Errors + Fault Tolerance  ->  Error Correction
```
Your task is not to start from "error correction" as a given solution, but to
*reconstruct why adding deliberate redundancy to data is the only rational
response* when physical reality corrupts information and the system must
still produce correct results.

This is a design discovery exercise, not a memorisation one.


### Part 1 - A Thought Experiment: The Unreliable Channel

Alice sends a message to Bob over a wire.
The wire is long. It passes through electromagnetic interference.
With some small probability, each bit flips: a 0 becomes a 1, or vice versa.

Alice sends: `01101001`
Bob receives: `01001001`

One bit flipped. Bob does not know which one. He does not even know
that anything went wrong. He processes the corrupted data as if it were correct.

This is not a hypothetical. Every real channel--copper wire, optical fibre,
radio, RAM, disk--flips bits. The rate varies, but it is never zero.

Model it:

```python
import random

def noisy_channel(bits: list[int], error_rate: float) -> list[int]:
    return [b ^ 1 if random.random() < error_rate else b for b in bits]

message = [0, 1, 1, 0, 1, 0, 0, 1]
received = noisy_channel(message, error_rate=0.05)

errors = sum(a != b for a, b in zip(message, received))
print(f"Sent:     {message}")
print(f"Received: {received}")
print(f"Errors:   {errors} bit(s)")
```

Run it many times. Sometimes zero errors. Sometimes one. Occasionally two.
Bob cannot tell which run was clean.


### Part 2 - Discovering the Blindness Problem

The devastating property of noise is not that it corrupts data.
It is that it corrupts data *silently*.

Without any additional structure, Bob cannot distinguish a clean transmission
from a corrupted one. He receives bits. He has no basis for doubt.

Fault tolerance requires that the system detect and recover from faults.
But here, the system cannot even *detect* that a fault occurred.

Fault tolerance without detection is impossible.

Simulate the blindness:

```python
def interpret(bits):
    value = int(''.join(str(b) for b in bits), 2)
    return value

original = [0, 1, 1, 0, 1, 0, 0, 1]
corrupted = noisy_channel(original, error_rate=0.1)

print(f"Original value:  {interpret(original)}")
print(f"Received value:  {interpret(corrupted)}")
print(f"Same?            {interpret(original) == interpret(corrupted)}")
```

When they match by accident (corruption cancelled out), you cannot even
measure the problem. When they differ, Bob still does not know *what*
the original was. He only knows what he received.

Something must be added. But what?


### Part 3 - The Insight: Information About Information

The key observation: to detect or correct an error, you need *information
about the information*. Something in the transmission must allow the receiver
to check whether the data is consistent with itself.

That something cannot come from the channel--the channel is the problem.
It must come from the sender, who knows the original data.

The sender must add *extra bits* whose values are determined by the
original bits. When the receiver gets the message, they can check whether
the extra bits still correctly describe the data bits. If not, something
was corrupted.

This extra information is not part of the message. It exists only to verify
or restore the message. It is, in a precise sense, *deliberate redundancy*.


### Part 4 - Your Task: Invent the Simplest Possible Check

Before reading about any error correction scheme, try to invent one.

Here is the simplest imaginable: add one extra bit to the message such that
the total number of 1-bits in the transmission is always even.

```python
def add_parity(bits):
    parity = sum(bits) % 2
    return bits + [parity]

def check_parity(bits_with_parity):
    return sum(bits_with_parity) % 2 == 0

message    = [0, 1, 1, 0, 1, 0, 0, 1]
with_parity = add_parity(message)
print(f"Message with parity: {with_parity}")

for _ in range(5):
    received = noisy_channel(with_parity, error_rate=0.05)
    ok       = check_parity(received)
    print(f"  Received: {received}  |  Parity check: {'OK' if ok else 'ERROR DETECTED'}")
```

Run it. When is the error detected? When is it missed?

The parity bit detects *odd* numbers of errors. Two flips can cancel each other out--
the parity looks correct even though two bits are wrong.

You have invented detection. You have not yet invented *correction*.


### Part 5 - Simulate the Limits of Detection Alone

Detection without correction is useful but incomplete. If you detect an error,
what do you do?

Option 1: ask for retransmission. Fine for networks. Impossible for memory.
Option 2: discard the data. Safe but lossy.
Option 3: *correct* the error without retransmission.

For option 3, you need more redundancy--enough to not only know *that* an
error occurred, but *where* it occurred.

Model retransmission vs. correction:

```python
def transmit_with_retry(message, channel_error_rate, max_retries=5):
    for attempt in range(max_retries):
        received = noisy_channel(add_parity(message), channel_error_rate)
        if check_parity(received):
            return received[:-1], attempt + 1
    return None, max_retries

message = [0, 1, 1, 0, 1, 0, 0, 1]
data, attempts = transmit_with_retry(message, 0.1)
print(f"Received after {attempts} attempt(s): {data}")
```

Retransmission works when:
- The channel allows two-way communication.
- Latency of retransmission is acceptable.
- Errors are rare enough that retransmission is not constant.

When these conditions do not hold--as in RAM, disk storage, or deep-space
communication where round-trip time is hours--you need correction, not retransmission.


### Part 6 - Introduce Correction Without Naming It

Now build the simplest structure that can *correct* a single-bit error.

You will send the message three times. The receiver takes a majority vote
on each bit position.

You still do not call this "error correction". You call it *voting*.

```python
def triple_redundancy_encode(bits):
    return [b for b in bits for _ in range(3)]

def triple_redundancy_decode(bits):
    result = []
    for i in range(0, len(bits), 3):
        group = bits[i:i+3]
        result.append(1 if sum(group) >= 2 else 0)
    return result

message  = [0, 1, 1, 0, 1, 0, 0, 1]
encoded  = triple_redundancy_encode(message)
received = noisy_channel(encoded, error_rate=0.05)
decoded  = triple_redundancy_decode(received)

errors_in    = sum(a != b for a, b in zip(encoded, received))
errors_out   = sum(a != b for a, b in zip(message, decoded))
print(f"Bit errors in transmission: {errors_in}")
print(f"Bit errors after decoding:  {errors_out}")
print(f"Original: {message}")
print(f"Decoded:  {decoded}")
```

Run it many times. How often does the voting fail to correct the error?
Under what conditions does it fail?


### Part 7 - Observe the Emergence

Compare the three strategies:

| Strategy          | Extra bits      | Detects errors? | Corrects errors? | Cost          |
|-------------------|-----------------|-----------------|------------------|---------------|
| None              | 0               | No              | No               | None          |
| Parity            | 1 per 8 bits    | Some            | No               | ~12% overhead |
| Triple redundancy | 2x message size | Yes             | Single-bit       | 200% overhead |

The overhead of triple redundancy is extreme. Real error correction codes
(Hamming, Reed-Solomon, LDPC) achieve correction with far less overhead--
but the principle is the same: add structured redundancy so the receiver
can locate and fix the corruption.

This is the moment the equation becomes real:
```
Noise + Errors + Fault Tolerance  ->  Error Correction
```

Not as a technique. As an *inevitability*.

When physical reality corrupts information (noise), and corrupted information
produces wrong results (errors), and the system must continue to produce
correct results despite this (fault tolerance)--you are forced to add
structured redundancy that carries information about the information.
That structure is error correction.


### Part 8 - Where Error Correction Lives

Error correction is not one mechanism. It is a principle that appears at every layer:

- *Memory (ECC RAM)*: adds extra bits per memory word to correct single-bit errors.
- *Storage (RAID)*: distributes data across disks so that losing one disk loses nothing.
- *Networks (TCP)*: checksums detect corruption; retransmission corrects it.
- *Wireless (4G/5G)*: turbo codes and LDPC correct errors in radio transmission.
- *Deep space (Voyager)*: convolutional codes correct errors across billions of kilometres.
- *QR codes*: Reed-Solomon allows up to 30% of the code to be damaged and still readable.

Each is the same insight, applied at a different layer with different cost constraints.


### Part 9 - Reflection Questions

Answer in writing:

1. Why is *silent* corruption more dangerous than *detected* corruption?
2. Why does detecting an error require redundancy?
3. What is the difference between *detection* and *correction*?
   What does correction require that detection does not?
4. Why can triple redundancy fail even when it seems like it should succeed?
5. Why does error correction overhead vary so much across different schemes?
   What determines the minimum overhead needed?
6. Where in your own computing environment does error correction operate
   without you being aware of it?

If you can answer these, you understand error correction at a systemic level.
Not as a trick. As a necessity created by deeper forces.

Now. Rename your "voting" to *majority decoding*--the simplest instance of
a *forward error correction code*.
At that point, you are not learning what error correction is.
You are recognising what you already built.
