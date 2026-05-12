
## Transformer

The Transformer architecture, introduced in *Attention Is All You Need* (Vaswani et al., 2017),
replaced recurrence with self-attention as the primary mechanism for modelling sequence
dependencies. Every position in the sequence can attend directly to every other position,
eliminating the sequential bottleneck of RNNs and enabling full parallelisation during training.
This change unlocked the scale that produced modern large language models.

Two implementations are provided here:

- `transformer.py` -- a from-scratch Transformer encoder block in pure Python (no NumPy),
  implementing multi-head self-attention, positional encoding, and a feedforward sublayer.
- `sentiment.py` -- an `AdvancedTransformer` for multi-class document classification, built
  with NumPy. Includes layer normalisation, dropout, learned positional embeddings, and a
  classification head. An interactive demo is available in `sentiment.html`.


### Mathematics

*Scaled dot-product attention* computes a weighted sum of values, where weights are determined
by the compatibility of queries and keys:

```math
\text{Attention}(Q, K, V) = \text{softmax}\!\left(\frac{QK^\top}{\sqrt{d_k}}\right) V
```

The $\sqrt{d_k}$ scaling prevents dot products from growing large in high dimensions, which
would push the softmax into regions with vanishing gradients.

*Multi-head attention* runs $h$ attention heads in parallel on projected subspaces, then
concatenates and linearly projects the results:

```math
\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h)\, W^O
```
```math
\text{head}_i = \text{Attention}(Q W_i^Q,\; K W_i^K,\; V W_i^V)
```

Each Transformer layer wraps attention and a position-wise feedforward network with residual
connections and layer normalisation:

```math
x \leftarrow \text{LayerNorm}(x + \text{MultiHead}(x, x, x))
```
```math
x \leftarrow \text{LayerNorm}(x + \text{FFN}(x))
```

*Positional encoding* injects sequence order via sinusoidal functions, since self-attention
is permutation-invariant:

```math
\text{PE}_{(pos, 2i)} = \sin\!\left(\frac{pos}{10000^{2i/d}}\right), \quad
\text{PE}_{(pos, 2i+1)} = \cos\!\left(\frac{pos}{10000^{2i/d}}\right)
```


### Concepts

* *Self-Attention:* Each token attends to all others in the same sequence, producing a
  context-aware representation. Quadratic $\mathcal{O}(n^2)$ cost in sequence length is the
  main scalability constraint.
* *Multi-Head Attention:* Parallel attention heads allow the model to attend to different
  aspects of the input simultaneously -- syntax in one head, coreference in another.
* *Positional Encoding:* Because attention is order-agnostic, position information must be
  added explicitly. Sinusoidal encodings generalise to lengths unseen during training; learned
  embeddings are an alternative.
* *Layer Normalisation:* Applied after each sublayer, it stabilises training by normalising
  activations to zero mean and unit variance per token.
* *Encoder vs. Decoder:* The encoder (used here) maps the input to contextual representations.
  A decoder adds cross-attention over encoder output and a causal mask to prevent attending
  to future positions during generation.


### Samples


*Sample 1: Sentiment Classification*

* *Data:* Labelled product or movie reviews (positive / neutral / negative).
* *Scenario:* The `AdvancedTransformer` in `sentiment.py` fine-tunes on review text, learning
  which tokens and phrases are most diagnostic of sentiment. Multi-head attention allows the
  model to link negation words ("not") to the adjectives they modify across arbitrary distance.

*Sample 2: Document Topic Classification*

* *Data:* News articles from multiple topic categories (politics, sports, technology).
* *Scenario:* A classification head on top of the [CLS] token representation -- the aggregate
  of the full sequence after several transformer layers -- categorises articles into topics.
  The model generalises well because self-attention captures long-range lexical co-occurrence.

*Sample 3: Code Intention Recognition*

* *Data:* Short natural-language descriptions of programming tasks paired with intent labels.
* *Scenario:* A transformer encoder maps a user query ("sort a list in descending order") to
  an intent vector used to retrieve relevant code templates. The architecture's ability to
  weight each word against every other makes it robust to paraphrase variation.
