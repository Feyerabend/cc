
## Neural Language Models

A neural language model assigns a probability to sequences of words. Given a context of $k$ previous
words, it predicts the probability distribution over the next word. This is the simplest framing of
language modelling and the foundation of all modern large language models.

Two implementations are provided here, both trained on Homer's *Iliad* (Project Gutenberg):

- `mini_lm.py` -- a minimal feedforward language model. See [MINI.md](./MINI.md) for implementation notes.
- `small_lm.py` -- an extended version with two hidden layers, dropout, momentum, and a CLI. See [SMALL.md](./SMALL.md).


### Mathematics

A feedforward language model with context window $k$ and vocabulary size $V$:

1. Each context word $w_{t-i}$ is mapped to an embedding vector $e_i \in \mathbb{R}^d$.
2. The $k$ embeddings are concatenated: $x = [e_1; e_2; \ldots; e_k] \in \mathbb{R}^{kd}$.
3. One or more hidden layers apply $h = \text{ReLU}(Wx + b)$.
4. A linear output layer produces logits $z \in \mathbb{R}^V$; softmax gives the predicted distribution:

```math
P(w_t \mid w_{t-k}, \ldots, w_{t-1}) = \frac{e^{z_{w_t}}}{\sum_{w} e^{z_w}}
```

Training minimises cross-entropy loss (equivalently, maximises log-likelihood):

```math
\mathcal{L} = -\frac{1}{N} \sum_{t} \log P(w_t \mid w_{t-k}, \ldots, w_{t-1})
```

*Perplexity* is the standard evaluation metric: $\text{PP} = e^{\mathcal{L}}$. Lower is better.
A model with perplexity 100 is roughly as uncertain as choosing uniformly from 100 words.


### Concepts

* *Context Window:* The number of preceding words used as input. Larger windows capture longer
  dependencies but increase input dimensionality linearly.
* *Word Embeddings:* Dense vector representations of words learned jointly with the model. Words
  with similar meaning end up with similar vectors.
* *Vocabulary and OOV:* Words not seen during training are mapped to a special `<UNK>` token.
  A larger vocabulary reduces unknowns but increases the softmax cost.
* *Laplace / Label Smoothing:* Avoids zero probabilities for unseen n-grams.
* *Temperature Sampling:* During generation, dividing logits by a temperature $T$ before softmax
  controls diversity. $T < 1$ makes outputs more peaked (conservative); $T > 1$ increases randomness.
* *Limitations of Feedforward LMs:* The fixed context window cannot model long-range dependencies.
  Recurrent networks (RNN/LSTM) and transformers address this at greater computational cost.


### Samples


*Sample 1: Trained on the Iliad*

* *Data:* Homer's *Iliad* (Project Gutenberg plain text, ~140,000 words).
* *Scenario:* The mini model trains on the Iliad in a few minutes on a laptop CPU and generates
  Homeric-sounding continuations. Perplexity is high because the vocabulary is archaic and the
  context window (3 words) misses most long-range structure -- but it illustrates the core mechanics.

*Sample 2: News Headline Generation*

* *Data:* A corpus of newspaper headlines.
* *Scenario:* A small feedforward LM learns the compressed, noun-heavy style of headlines. Given
  a prompt like "Scientists discover", it samples plausible completions from the learned distribution.

*Sample 3: Code Completion Baseline*

* *Data:* Python source files from a small library.
* *Scenario:* Token-level (rather than word-level) language modelling on Python code. A simple
  feedforward model learns basic syntactic patterns (indentation after `:`, common keywords).
  This illustrates why modern code models use transformers -- the fixed context window cannot
  capture the scope rules that make code meaningful.
