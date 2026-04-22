
## Information Theory: Reflections, Parallels, and Implementations

### The Moment Communication Became a Science

In 1948, Claude Shannon published *A Mathematical Theory of Communication*
in the Bell System Technical Journal. The title is almost comically understated.
The paper did not improve communication--it *defined* what communication is.
Before Shannon, engineers built better radios and telephone lines by intuition
and experiment. After Shannon, there was a rigorous mathematical object called 
*information*, a precise quantity called *entropy*, a hard limit called
*channel capacity*, and theorems that told you exactly how close to that
limit you could get.

The key conceptual move was to separate *meaning* from *information*. Shannon
was not interested in what a message means to its recipient. He was interested
in how much *uncertainty* it resolves. This is counterintuitive but powerful.
By bracketing semantics entirely, Shannon could apply probability theory and
make exact statements that apply to every message over every channel.



### Information as Surprise

The fundamental quantity is the *self-information* of an event.
If event *x* has probability P(x), the information gained by observing it is:

```math
I(x) = -log₂ P(x)
```

The unit (when the base is 2) is the *bit*--not the binary digit,
but the unit of information. One bit is the amount of information
in a fair coin flip.

The formula is forced by a few natural requirements:
- Certain events (P = 1) carry no information: I = 0.
- Rare events carry more information than common ones: I is decreasing in P.
- Independent events' information adds: I(xy) = I(x) + I(y), which requires a logarithm.

So `-log₂ P(x)` is not an arbitrary choice--it is the unique function satisfying these
three constraints. A fair die showing a 4 carries 2.58 bits. A message that a particular 
patient tested positive for a 1-in-a-million disease carries about 20 bits.



### Entropy — Average Surprise

A single event's information depends on which event occurred. A more useful quantity
averages over all possible outcomes, weighted by probability. This is *Shannon entropy*:

```math
H(X) = -Σ P(x) log₂ P(x)
```

Entropy measures the *average amount of information* produced by a source, or equivalently,
the average number of bits needed to describe one outcome.

Two extremes illuminate the concept:

- *Minimum entropy (H = 0)*: one outcome has probability 1. The source is deterministic;
  you always know what it will say next. Zero uncertainty, zero information.
- *Maximum entropy*: all outcomes are equally probable. This is the most uncertain source
  possible. For a source with *n* equally likely symbols, H = log₂ n bits--exactly the
  number of binary questions needed to identify which symbol occurred.

Entropy is always non-negative, always bounded above by log₂ n,
and achieves that bound only at the uniform distribution.



### The Thermodynamic Echo

Shannon's entropy formula is identical in structure to
*Boltzmann's entropy* from statistical mechanics:

```math
S = -k Σ pᵢ ln pᵢ
```

where *k* is Boltzmann's constant. Shannon replaced the constant and
switched the logarithm base; the mathematical object is the same.

This is not coincidence. Shannon was aware of the analogy. The story
goes that John von Neumann advised him to call the quantity "entropy"
because it would give him an advantage in debates--nobody
really understands entropy. But the connection runs deeper than naming.

*Maxwell's Demon* (1867): James Clerk Maxwell imagined a tiny demon
controlling a gate between two chambers of gas. By selectively opening
and closing the gate for fast and slow molecules, the demon could decrease
entropy without doing work--apparently violating the second law of thermodynamics.

*Szilard's engine* (1929): Leó Szilárd showed that the demon must
*measure* the molecules, and that measurement acquires information.
He calculated that one bit of information corresponds to exactly
*k*T ln 2 of free energy--connecting information to thermodynamics quantitatively.

*Landauer's principle* (1961): Rolf Landauer proved that *erasing*
one bit of information necessarily dissipates at least kT ln 2 joules of heat.
Erasure is the thermodynamically irreversible act. Computation itself need
not dissipate energy; only erasure of information does.

This means information is not merely a mathematical abstraction.
It has a physical unit price. Every time you delete a file, you
are increasing the entropy of the universe by a minimum measurable amount.
The universe keeps accounts.



### Channel Capacity and the Noisy Channel Coding Theorem

Once information is quantified, the next question is:
how much of it can reliably traverse a noisy channel?

Shannon modelled a communication system as: Source -> Encoder -> Channel -> Decoder -> Sink.
The channel corrupts symbols with some probability.
The question is whether the corruption can be overcome
by clever encoding.

*Mutual information* *I(X; Y)* measures how much knowing the channel
output *Y* reduces uncertainty about the input *X*:

```math
I(X; Y) = H(X) - H(X|Y)
```

It is the overlap between the information in *X* and
the information in *Y*--the shared content that survives the channel.

*Channel capacity* is the maximum mutual information
over all possible input distributions:

```math
C = max_{P(x)} I(X; Y)
```

Shannon's *Noisy Channel Coding Theorem* then states:

> For any rate R < C, there exists an encoding scheme that achieves arbitrarily
> small error probability. For any rate R > C, reliable communication is impossible
> regardless of the encoding scheme.

This is one of the most striking existence proofs in
all of mathematics. Shannon proved that good codes
*must exist* without constructing any specific code.
He showed the theoretical boundary is achievable and
gave no recipe for achieving it.

Finding practical codes that approach this limit took
decades. Turbo codes (1993) came within a fraction of
a dB of the Shannon limit. LDPC codes (rediscovered in the 1990s)
achieved similar performance. Modern 5G communications
operate within about 1% of the theoretical maximum.
Every wireless device in existence is, in part,
an application of Shannon's 1948 theorem.



### Source Coding: Compression and the Entropy Bound

The noisy channel theorem deals with reliable *transmission*.
A separate set of theorems deals with efficient
*representation*--*source coding* or, in practice, data compression.

*Shannon's Source Coding Theorem* states: the minimum average number of bits per symbol
required to represent a source without loss is its entropy H. You cannot compress below
the entropy limit. You can always compress down to it (in the limit of long messages).

This is the fundamental theorem of lossless compression. Every compressor--gzip, zstd,
bzip2, the PNG codec, the DEFLATE algorithm inside ZIP files--is an engineering approximation
of this theorem.

#### Huffman Coding

Huffman coding (1952) is the simplest scheme that achieves within one bit per symbol of
the entropy bound. The idea is direct: assign shorter codewords to more frequent symbols.
Build a binary tree greedily from the bottom up, combining the two least frequent
symbols at each step.

For a source with probabilities P(a) = 0.5, P(b) = 0.33, P(c) = 0.17:

```
Entropy = 1.459 bits/symbol

Huffman:
  a --> 0        (1 bit)
  b --> 11       (2 bits)
  c --> 10       (2 bits)

Avg code length = 0.5×1 + 0.33×2 + 0.17×2 = 1.50 bits/symbol
Gap from entropy = 0.041 bits/symbol
```

The gap is always less than 1 bit per symbol. Arithmetic coding closes this gap further--it
represents an entire message as a single real number in [0,1), achieving arbitrarily close
to the entropy limit at the cost of more complex arithmetic.

Real-world compressors go beyond per-symbol codes. *LZ77* (the basis of gzip and PNG)
exploits *sequential* structure: it encodes repeated substrings as back-references.
This implicitly captures higher-order statistics--not just symbol frequencies but patterns.
*bzip2* uses Burrows-Wheeler transform plus Huffman. *zstd* uses ANS (asymmetric numeral systems),
a modern generalisation of arithmetic coding that is both near-optimal and fast.

All of them are racing toward the same theoretical limit that Shannon established in 1948.



### KL Divergence and Cross-Entropy

Information theory also provides tools for comparing probability
distributions--essential in statistics and machine learning.

*Kullback-Leibler divergence*:

```math
D_KL(P ‖ Q) = Σ P(x) log₂ [P(x) / Q(x)]
```

This measures the extra bits needed to encode events from *P* using
a code optimised for *Q*. It is always non-negative (zero only when
$P = Q$), and asymmetric — $D_KL(P‖Q) ≠ D_KL(Q‖P)$ in general.
It is not a distance metric, but it is a measure of how wrong
*Q* is as a model for *P*.

*Cross-entropy*:

```math
H(P, Q) = -Σ P(x) log₂ Q(x) = H(P) + D_KL(P ‖ Q)
```

Cross-entropy is what you minimise in neural network classification.
The model produces a distribution *Q* (its predictions); the true
labels define *P*. Minimising cross-entropy is equivalent to minimising
KL divergence from *P* to *Q*, which means making the model's
distribution match reality as closely as possible.

The loss function printed out during deep learning training is
Shannon's 1948 concept, running on GPU clusters in 2024.



### Kolmogorov Complexity — Information Meets Turing

Shannon's entropy is a property of a *source*--a probability distribution.
But what about the information content of a *single* string,
independent of any assumed distribution?

*Kolmogorov complexity* K(s) of a string *s* is the length (in bits) of
the shortest program on a universal Turing machine that outputs *s* and
then halts. It is the ultimate compression of *s*--the minimum description
length, independent of any probabilistic model.

This bridges information theory and the Turing machine from the previous section.

Key facts:

- *K(s) is uncomputable.* Determining the shortest program for an arbitrary
  string is equivalent to solving the Halting Problem. You can upper-bound K(s)
  for any specific string, but you can never prove you have found the minimum.
  The optimal compressor cannot be constructed.

- *Most strings are incompressible.* For any length *n*, there are 2ⁿ strings
  but only 2^(n-1) + 1 programs shorter than *n* bits. By the pigeonhole principle,
  at least half of all *n*-bit strings have K(s) ≥ n — they cannot be compressed at all.
  "Random" strings, in the Kolmogorov sense, are maximally incompressible.

- **K connects to Shannon entropy.** For strings generated by a source with entropy H,
the expected Kolmogorov complexity is approximately H(X) per symbol. The connection
is approximate and requires care, but the two theories are shadow images of each other:
Shannon measures average behaviour over a distribution; Kolmogorov measures the
worst-case complexity of individual strings.

The incomputability of K(s) means the "ideal" compressor--the one that achieves the
Kolmogorov limit--cannot be built. Every real compressor is an approximation, using
heuristics and models to extract as much structure as it can find. The limit is real;
reaching it is forbidden by the same argument that forbids the halting oracle.



### Abstract vs. Concrete

Shannon's theorems are, like Turing's, existence results about abstract objects.
The noisy channel theorem guarantees codes exist; it does not exhibit them.
The source coding theorem guarantees compression to entropy is possible;
Huffman coding comes close but not all the way.

The same abstract/concrete gap that separates Turing machines from physical
computers separates Shannon's channel capacity from real communication systems:

| Concept      | Shannon's Model                 | Engineering Reality              |
|--------------|---------------------------------|----------------------------------|
| Channel      | Memoryless, stationary noise    | Burst errors, fading, multipath  |
| Encoder      | Arbitrary, unbounded complexity | Finite latency, hardware budget  |
| Block length | Infinite (for vanishing error)  | Milliseconds of data per packet  |
| Capacity     | Exact real number               | Approximation from measurements  |
| Compression  | Arbitrary-order model           | Sliding window, fixed dictionary |

Real engineers work in the gap. The gap has been closing for 75 years--5G is near Shannon
capacity, zstd is near entropy for many sources--but it has not vanished and never will,
because the theorems about what the limit is do not tell you how to reach it with bounded resources.



### Huffman Coding in Python

A full implementation: entropy calculation, tree construction,
encoding, and decoding with round-trip verification.

```python
import math
import heapq
from collections import Counter


def entropy(text: str) -> float:
    n = len(text)
    counts = Counter(text)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


class HuffNode:
    __slots__ = ('sym', 'freq', 'left', 'right')

    def __init__(self, sym, freq, left=None, right=None):
        self.sym   = sym
        self.freq  = freq
        self.left  = left
        self.right = right

    def __lt__(self, other):
        return self.freq < other.freq


def build_tree(text: str) -> HuffNode:
    counts = Counter(text)
    heap = [HuffNode(sym, freq) for sym, freq in counts.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        heapq.heappush(heap, HuffNode(None, a.freq + b.freq, a, b))
    return heap[0]


def _collect_codes(node, prefix, table):
    if node.sym is not None:
        table[node.sym] = prefix or '0'
    else:
        _collect_codes(node.left,  prefix + '0', table)
        _collect_codes(node.right, prefix + '1', table)


def encode(text: str) -> tuple[str, HuffNode, dict]:
    root  = build_tree(text)
    table = {}
    _collect_codes(root, '', table)
    return ''.join(table[c] for c in text), root, table


def decode(bits: str, root: HuffNode) -> str:
    if root.sym is not None:         # single unique symbol
        return root.sym * len(bits)
    result, node = [], root
    for bit in bits:
        node = node.left if bit == '0' else node.right
        if node.sym is not None:
            result.append(node.sym)
            node = root
    return ''.join(result)
```

Sample output for a few inputs:

```
Text:          'aaabbc'
  Entropy:     1.4591 bits/symbol  (theoretical minimum)
  Avg code:    1.5000 bits/symbol  (Huffman actual)
  Gap:         0.0409 bits/symbol
  Original:    48 bits (8-bit ASCII)
  Compressed:  9 bits
  Ratio:       18.8%
  Codes:       'a'=0  'b'=11  'c'=10

Text:          'abcdefgh'
  Entropy:     3.0000 bits/symbol  (theoretical minimum)
  Avg code:    3.0000 bits/symbol  (Huffman actual)
  Gap:         0.0000 bits/symbol
  Original:    64 bits (8-bit ASCII)
  Compressed:  24 bits
  Ratio:       37.5%
  Codes:       'a'=100  'b'=110  'c'=001  'd'=010  ...

Text:          'aaaaaa'
  Entropy:     0.0000 bits/symbol  (theoretical minimum)
  Avg code:    1.0000 bits/symbol  (Huffman actual)
  Gap:         1.0000 bits/symbol
```

The uniform case (`abcdefgh`) achieves zero gap--Huffman is optimal when the
probabilities are exact negative powers of 2. The degenerate case (`aaaaaa`)
shows Huffman's floor: it cannot go below 1 bit per symbol even when entropy
is 0. This is where run-length encoding or arithmetic coding outperforms it.

The complete runnable file is [`info.py`](info.py).



### Huffman Coding in C

The same algorithm in C, using a min-heap over a static node pool.
The transition from `heapq` to an explicit heap is the main structural
difference; the logic is identical.

```c
typedef struct {
    int   sym;         /* ASCII value, -1 for internal nodes */
    long  freq;
    int   left, right;
} Node;

static Node pool[MAX_NODES];
static int  heap[MAX_NODES];

/* Min-heap push and pop, keyed by pool[idx].freq */
static void heap_push(int idx) { /* ... standard sift-up ... */ }
static int  heap_pop(void)     { /* ... standard sift-down ... */ }

/* Build Huffman tree from frequency table */
for (int i = 0; i < MAX_SYMS; i++)
    if (freq[i]) heap_push(node_new(i, freq[i], -1, -1));

while (heap_sz > 1) {
    int a = heap_pop(), b = heap_pop();
    heap_push(node_new(-1, pool[a].freq + pool[b].freq, a, b));
}
```

The key insight expressed in C is that the Huffman algorithm is entirely
defined by the priority queue: always merge the two cheapest (least frequent)
subtrees. The resulting tree is provably optimal--no other prefix-free code
has a smaller average length.

The complete runnable file is [`info.c`](info.c). Compile with:

```sh
gcc -Wall -Wextra -o info info.c -lm && ./info
```



### What the Output Shows

The numbers reveal several important facts:

*Entropy is an asymptote, not a target.* Huffman coding always produces an average code
length between H and H+1. For the pangram (43 chars, 26 distinct), the gap is 0.08 bits/symbol--tight.
For short strings with few symbols and non-power-of-2 probabilities, the gap can approach 1.

*The compressibility of a source is fully determined by its entropy.* `aaabbc` compresses
to 18.8% of its ASCII representation; `abcdefgh` compresses to 37.5%. The difference is
entropy--1.46 vs. 3.00 bits/symbol. A source with higher entropy is harder to compress
not because of any implementation detail but because it *contains more information*.

*Real text has low entropy.* English text has an entropy of roughly 1.0–1.5 bits per
character when long-range correlations are included (Shannon estimated this in 1951
using human subjects as predictors). Huffman over individual characters achieves 4–5 bits/character
because it ignores all sequential structure. The gap between these figures is what LZ-based
compressors exploit--they model context, not just symbol frequencies.



### The Deeper Structure

Shannon's theory is, like Turing's and Gödel's, a theory of limits.
- Gödel: there are truths no proof system can reach.
- Turing: there are questions no algorithm can answer.
- Shannon: there are rates no encoder can exceed, and compressions no scheme can surpass.

All three limits arise from a version of the same argument: the space of possible objects
(proofs, computations, codes) is not large enough to cover everything we might want it to cover.
Diagonalisation, incompressibility, and the pigeonhole principle are the same move in different languages.

The connection between Shannon and Turing runs through Kolmogorov complexity--the information
content of a single string measured in Turing machine terms. K(s) is Shannon entropy applied to
individual strings, and it is uncomputable for exactly the same reason the Halting Problem is
undecidable. The optimal compressor and the halting oracle are the same impossibility wearing
different clothes.

What Shannon added that Turing did not is the *quantitative* language. Turing said certain
things cannot be computed. Shannon said *how much* information a source contains, *how much*
noise a channel introduces, and *how far* a given code is from the optimum.
The limits are not just walls--they are calibrated. You can measure how close you are to them.

That measurability is what turned a theoretical framework into an engineering discipline.
Every compression codec, every error-correcting code in your phone, every neural network
loss function, and every Wi-Fi protocol you have ever used is a point in the space that
Shannon mapped in 1948.

