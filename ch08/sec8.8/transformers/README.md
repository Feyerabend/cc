
## Transformers

The book presents the self-attention formula and lists the components of a
Transformer encoder layer. This section works through the arithmetic step by step
and implements scaled dot-product attention and positional encoding from scratch.

### Files

| File                     | What it demonstrates                                      |
|--------------------------|-----------------------------------------------------------|
| `attention.py`           | Scaled dot-product attention and multi-head attention     |
| `positional_encoding.py` | Sinusoidal positional encoding - values and visualisation |
| `attention.c`            | Single-head attention in C for a short sequence           |


### Key ideas extended here

*Why scaling by sqrt(d_k)?* Without the scaling factor, the dot products
$QK^\top$ grow in magnitude with $d_k$. Large magnitudes push the softmax into
regions where its gradient is near zero, slowing training. Dividing by
$\sqrt{d_k}$ keeps the variance of the dot products roughly constant regardless
of dimension. `attention.py` shows this effect numerically.

*Multi-head attention.* Rather than computing a single attention function,
the Transformer projects queries, keys, and values into $h$ lower-dimensional
subspaces, computes attention in each, then concatenates and projects the results.
This lets the model attend to information from different representation subspaces
simultaneously. The total parameter count is the same as single-head attention
with the same total dimension.

*Positional encoding.* Self-attention is permutation-invariant: if you shuffle
the input tokens, the attention weights reshuffle accordingly but the operation
cannot distinguish positions. Positional encodings inject absolute or relative
position information by adding a fixed (or learned) vector to each token embedding.
The sinusoidal encoding from the original Transformer paper uses frequencies at
different scales so that the model can learn to attend to relative positions.
`positional_encoding.py` visualises the encoding matrix as a heatmap.

*Quadratic complexity.* Self-attention computes pairwise similarity between all
$n$ tokens, resulting in an $n \times n$ attention matrix. Memory and computation
scale as $O(n^2)$, which becomes prohibitive for very long sequences. This has
motivated a large body of research into linear-complexity approximations such as
Linformer, Performer, and FlashAttention.
