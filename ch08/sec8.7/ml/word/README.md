
## Word Embeddings

Word embeddings represent words as dense numerical vectors in a continuous space, where words that
appear in similar contexts end up with similar vectors. This simple idea -- that meaning emerges from
context -- underlies most modern NLP systems. Two implementations are provided here:

- `simple_w2v.py` -- a minimal Skip-gram Word2Vec from scratch using NumPy.
- `w2v.py` -- a more complete version with additional features.

Both train on Homer's *Iliad* (Project Gutenberg). See [WORD2VEC.md](./WORD2VEC.md) for a
conceptual overview of the models.


### Mathematics

Word2Vec trains a shallow two-layer network. For the Skip-gram model, given a centre word $w_c$,
the goal is to predict context words $w_o$ within a window of size $m$:

```math
\mathcal{L} = -\frac{1}{T} \sum_{t=1}^{T} \sum_{\substack{-m \leq j \leq m \\ j \neq 0}} \log P(w_{t+j} \mid w_t)
```

Computing the exact softmax over the vocabulary is expensive. *Negative sampling* approximates it
by training a binary classifier: given a (centre, context) pair, is it a real pair or a noise pair?

```math
\mathcal{L}_{\text{NS}} = \log \sigma(v_{w_o}^{\top} v_{w_c}) + \sum_{k=1}^{K} \mathbb{E}_{w_k \sim P_n} [\log \sigma(-v_{w_k}^{\top} v_{w_c})]
```

where $\sigma$ is the sigmoid function, $v_w$ is the embedding of word $w$, and $K$ negative samples
are drawn from the noise distribution $P_n$ (typically the unigram distribution raised to the 3/4 power).


### Concepts

* *Distributional Hypothesis:* Words that occur in similar contexts have similar meanings (Harris, 1954).
  Word2Vec operationalises this by training on context prediction.
* *Skip-gram vs. CBOW:* Skip-gram predicts context given centre word; CBOW predicts centre word given
  context. Skip-gram works better for rare words; CBOW is faster to train.
* *Embedding Dimension:* Typical values are 50--300. Higher dimensions capture more nuance but require
  more data and memory.
* *Analogy Arithmetic:* Learned embeddings support relational reasoning: $v(\text{king}) - v(\text{man})
  + v(\text{woman}) \approx v(\text{queen})$.
* *Cosine Similarity:* The standard metric for comparing word vectors. Vectors are typically
  L2-normalised after training so cosine similarity equals the dot product.


### Samples


*Sample 1: Iliad Vocabulary*

* *Data:* Homer's Iliad (~140,000 words after tokenisation).
* *Scenario:* After training, `most_similar("achilles")` returns words like "hector", "warrior",
  "greek", demonstrating that the model learns semantic relationships even from a single book.

*Sample 2: Sentiment Lexicon Seed Expansion*

* *Data:* A large product review corpus.
* *Scenario:* Starting from a small seed set of positive words ("excellent", "great", "good"), a
  retailer uses word embedding similarity to expand the lexicon automatically, improving a downstream
  sentiment classifier.

*Sample 3: Cross-lingual Transfer*

* *Data:* Parallel corpora in two languages.
* *Scenario:* Word embeddings trained separately in two languages are aligned using a small bilingual
  dictionary. After alignment, translation equivalents end up near each other in the shared space,
  enabling zero-shot cross-lingual classification.
