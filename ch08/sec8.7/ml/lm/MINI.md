
## Mini Language Model

#### 1. Class: MiniNeuralLM

This is the core model.
- What it does: It predicts the next word given a few previous words (context).
- Structure: Simple feedforward neural network:
- Embeddings: Each word is turned into a small vector.
- Hidden Layer: Nonlinear transformation (ReLU).
- Output Layer: Predicts a probability distribution over all words in the vocabulary using softmax.

Important points:
- Context size = how many previous words you look at (like a sliding window).
- Embedding dimension = how big the word-vectors are.
- Hidden size = how large the internal memory (hidden layer) is.
- Learning rate = how fast the model updates during training.
- Loss = Cross-entropy loss between predicted probability and true next word.


#### 2. Class: TextPreprocessor

This prepares the text.
- Build vocabulary: Picks most common words. Maps them to indices.
- Tokenisation: Splits text into lowercase words, handles punctuation simply.
- Training examples: Builds (context, target) pairs: [previous words] ➔ [next word].
- Unknown words: Any word not in the vocabulary becomes <UNK>.
- Padding: If not enough context, adds special <PAD> token.


#### 3. Function: train_model

Training loop.
- Takes training examples and updates the model parameters using gradient descent.
- Measures and prints loss (average per batch and per epoch).
- Shuffles training data every epoch for better learning.
- Tracks how loss drops over time.


#### 4. Function: generate_text

Text generation.
- Takes a seed (few starting words).
- Predicts one word at a time, using the model’s softmax output.
- Can apply temperature (controls randomness):
- High temperature (e.g., 1.5) = more random.
- Low temperature (e.g., 0.5) = more deterministic.
- Repeats prediction to generate multiple words.


#### What is the loss here?

Loss = Cross-entropy between the predicted probability distribution and the real target word.

Meaning:
- If the model gives very low probability to the correct next word, loss is high.
- If it gives high probability to the correct word, loss is low.

Technically:
- Loss = -log(probability assigned to correct next word)
- Lower loss = better model.



#### What is perplexity here?

Perplexity is a standard way to measure a language model’s quality.

It is calculated as:

Perplexity = exp(average loss)

Interpretation:
- Perplexity ≈ “How many choices the model is confused between at each prediction.”
- Lower perplexity = model is more confident and accurate.
- Example: Perplexity 2 = about 2 choices; perplexity 100 = about 100 choices.

Why it matters:
- Random guessing among 1000 words → perplexity near 1000.
- Good model → perplexity drops toward 10, 5, 2, etc.


| Part  | Purpose   | Outcome   |
|---|---|---|
| MiniNeuralLM (class)    | Defines the neural language model                           | Predicts the next word from a fixed-size context window                                   |
| __init__                | Initialises model parameters                                | Randomised embeddings, weights, and biases for training                                  |
| forward                 | Forward pass through the network                            | Outputs probabilities for next word prediction                                           |
| backward                | Computes gradients                                           | Prepares parameter updates via backpropagation                                            |
| update_params           | Updates model parameters                                    | Applies gradient descent updates                                                         |
| train_step              | One training step (forward + backward + update)              | Trains the model a little more                                                            |
| predict                 | Predicts the most likely next word                          | Returns the word index with highest probability                                           |
| predict_topk            | Predicts top-k most likely next words                       | Returns k best word predictions with their probabilities                                 |
| TextPreprocessor (class)| Preprocesses and tokenises raw text                          | Prepares text: tokenises, builds vocabulary, creates training examples                   |
| build_vocab             | Builds vocabulary from raw text                             | Maps words to integer indices and vice versa                                              |
| create_training_examples| Creates (context, target) training pairs                    | Provides training samples to the model                                                   |
| train_model (function)  | Orchestrates model training                                  | Trains the model over multiple epochs, prints loss                                        |
| generate_text (function)| Samples words to generate new text                          | Produces generated text by repeatedly predicting and sampling next word                  |
| Perplexity (in train_model)   | Related to loss                                              | Lower loss → lower perplexity → better model |



### Example

#### Vocabulary

| Word    | Index |
|---------|-------|
| `<PAD>` | 0     |
| `the`   | 1     |
| `cat`   | 2     |
| `sat`   | 3     |
| `on`    | 4     |
| `mat`   | 5     |
| `.`     | 6     |

- Vocabulary size: *7*
- Embedding dimension: *2*
- Hidden size: *4*


#### Embedding Table

| Word    | Embedding (2D vector) |
|---------|-----------------------|
| `<PAD>` | [0.0, 0.0]            |
| `the`   | [1.0, 0.5]            |
| `cat`   | [0.5, 1.0]            |
| `sat`   | [1.0, 1.0]            |
| `on`    | [0.5, 0.5]            |
| `mat`   | [1.0, 0.0]            |
| `.`     | [0.0, 1.0]            |


#### Hidden Layer Weights `W1` (input 6 × hidden 4)

| Input Feature | Hidden 1 | Hidden 2 | Hidden 3 | Hidden 4 |
|---------------|----------|----------|----------|----------|
| 0             | 0.1      | 0.2      | 0.1      | 0.0      |
| 1             | 0.0      | 0.1      | 0.3      | 0.2      |
| 2             | 0.2      | 0.0      | 0.1      | 0.1      |
| 3             | 0.3      | 0.1      | 0.0      | 0.0      |
| 4             | 0.2      | 0.3      | 0.1      | 0.2      |
| 5             | 0.1      | 0.2      | 0.2      | 0.1      |


#### Hidden Layer Bias `b1` (size 4)

| Hidden Node | Bias |
|-------------|------|
| 1           | 0.1  |
| 2           | 0.1  |
| 3           | 0.1  |
| 4           | 0.1  |


#### Output Layer Weights `W2` (hidden 4 × vocab 7)

| Hidden Node | `<PAD>` | `the` | `cat` | `sat` | `on` | `mat` | `.` |
|-------------|---------|-------|-------|-------|------|-------|-----|
| 1           | 0.2     | 0.1   | 0.0   | 0.2   | 0.1  | 0.3   | 0.1 |
| 2           | 0.1     | 0.2   | 0.1   | 0.0   | 0.2  | 0.1   | 0.3 |
| 3           | 0.0     | 0.1   | 0.3   | 0.2   | 0.1  | 0.0   | 0.2 |
| 4           | 0.1     | 0.3   | 0.2   | 0.1   | 0.2  | 0.1   | 0.0 |


#### Output Layer Bias `b2` (size 7)

| Word    | Bias |
|---------|------|
| `<PAD>` | 0.1  |
| `the`   | 0.1  |
| `cat`   | 0.1  |
| `sat`   | 0.1  |
| `on`    | 0.1  |
| `mat`   | 0.1  |
| `.`     | 0.1  |


### Example: Step-by-step through "the cat"

#### Input

Two words: `the`, `cat`

Look up embeddings:

- `the` → [1.0, 0.5]
- `cat` → [0.5, 1.0]

Concatenate embeddings:

```text
[1.0, 0.5, 0.5, 1.0] 
```

Pad to match 6 inputs (add two zeros):

```text
[1.0, 0.5, 0.5, 1.0, 0.0, 0.0]
```


#### Compute Hidden Layer Activation

Apply linear transformation:

```text
h = W1 * input + b1
```

Step through manually:

For each hidden node:

```
h1 = (1.0 * 0.1) + (0.5 * 0.0) + (0.5 * 0.2) + (1.0 * 0.3) + (0.0 * 0.2) + (0.0 * 0.1) + 0.1
h2 = (1.0 * 0.2) + (0.5 * 0.1) + (0.5 * 0.0) + (1.0 * 0.1) + (0.0 * 0.3) + (0.0 * 0.2) + 0.1
h3 = (1.0 * 0.1) + (0.5 * 0.3) + (0.5 * 0.1) + (1.0 * 0.0) + (0.0 * 0.1) + (0.0 * 0.2) + 0.1
h4 = (1.0 * 0.0) + (0.5 * 0.2) + (0.5 * 0.1) + (1.0 * 0.0) + (0.0 * 0.2) + (0.0 * 0.1) + 0.1
```

Calculate each term manually if you want exact numeric values.


#### Activation Function

Apply ReLU:

```text
relu(x) = max(0, x)
```

All negative outputs replaced with 0.


#### Compute Output Scores

Apply second linear layer:

```text
output = W2 * h + b2
```

One score per vocabulary word (`<PAD>`, `the`, `cat`, `sat`, `on`, `mat`, `.`).


Apply Softmax: Normalise scores into probabilities.

Prediction: Choose word with highest probability.


### Summary

- Embedding lookup
- Linear layer 1 (W1, b1) + ReLU
- Linear layer 2 (W2, b2)
- Softmax
- Pick most probable word

