
## Small Language Model

### What it does

- Learns language patterns: Analyses text to predict the next word given a sequence of previous words
- Generates text: Can produce new text continuations based on input prompts
- Understands context: Uses recent word history (context window) to make predictions

### How it works

__1. Preprocessing (`TextPreprocessor`)__
   - Builds a vocabulary from input text
   - Converts words to numerical indices
   - Creates training examples of (context window -> target word) pairs

__2. Neural Network Architecture (`MiniNeuralLM`)__
   - Embedding Layer: Converts word indices to dense vectors
   - Hidden Layers: Learns hierarchical text patterns using:
     - ReLU activation for non-linearity
     - Optional dropout for regularisation
   - Output Layer: Produces probability distribution over vocabulary

__3. Training__
   - Uses backpropagation to adjust weights
   - Implements momentum for smoother optimisation
   - Tracks loss to monitor learning progress

__4. Generation__
   - Samples from predicted probabilities
   - Uses temperature to control randomness
   - Maintains a sliding context window

### AI Components

- Deep Learning: Neural network with hidden layers
- Natural Language Processing: Word embeddings, language modelling
- Machine Learning: Gradient-based optimization, regularization

This is a simplified version of modern language models like GPT, but demonstrates core AI
concepts of learning patterns from data and generating new content through neural network
processing.


### 1. Code-Level Mechanics


#### Core Components
- `MiniNeuralLM` Class: Implements a neural network with:
  - Embedding layer: Maps words to dense vectors (e.g., `dog` → `[0.2, -0.5, 0.7]`)
  - Hidden layers: Non-linear transformations of input data
  - Output layer: Predicts probabilities for the next word
- `TextPreprocessor`: Converts raw text into numerical inputs (indices) for the model
- Training loop: Adjusts model parameters using gradient descent


#### Code Flow

1. Preprocessing:
   ```python
   # Convert text to numerical indices
   indices = preprocessor.text_to_indices("The cat sat")
   # → [4, 12, 7]
   ```

2. Forward Pass:
   ```python
   # Embed words → process through layers → get probabilities
   probs, cache = model.forward(context_indices)
   ```

3. Loss Calculation:
   ```python
   # Compare prediction (probs) to actual next word
   loss = -np.log(probs[target_idx])
   ```

4. Backward Pass:
   ```python
   # Compute gradients for all parameters
   grads = model.backward(probs, target_idx, cache)
   ```

5. Parameter Update:
   ```python
   # Adjust weights using momentum-augmented gradients
   model.update_params(grads)
   ```


### 2. Mathematical Foundations


#### Core Equations

1. Embedding Lookup:
   - For input word indices `[i₁, i₂, i₃]`:
   ```
   x = concat(embedding[i₁], embedding[i₂], embedding[i₃])
   ```

2. Hidden Layer (ReLU Activation):
   ```
   h₁ = max(0, W₁⋅x + b₁)        # First hidden layer
   h₂ = max(0, W₁₅⋅h₁ + b₁₅)     # Optional second layer
   ```

3. Output Probabilities (Softmax):
   ```
   scores = W₂⋅h₂ + b₂
   probs = exp(scores) / sum(exp(scores))
   ```

4. Loss Function (Cross-Entropy):
   ```
   Loss = -log(prob[target_word])
   ```

5. Backpropagation:
   - Uses the chain rule to compute gradients:
     - Gradient of loss w.r.t. weights: `∂Loss/∂W = ∂Loss/∂probs ⋅ ∂probs/∂h₂ ⋅ ∂h₂/∂W`
     - Propagates gradients backward through layers

6. Momentum Update:
   ```
   momentum = β⋅momentum + (1-β)⋅gradient
   W = W - learning_rate⋅momentum
   ```


### 3. ML-Specific Features


#### a. Learning Mechanism

- What's learned: 
  - Word embeddings (`embeddings` matrix)
  - Weight matrices (`W1`, `W1_5`, `W2`)
  - Biases (`b1`, `b1_5`, `b2`)
- How learning happens: 
  - Adjusts parameters to minimise prediction error (loss)
  - Uses gradient descent with momentum to avoid oscillations

#### b. Regularisation
- Dropout (code snippet):
  ```python
  hidden *= dropout_mask  # Randomly zero out neurons during training
  ```
- Mathematically: Forces the network to learn redundant representations.

#### c. Numerical Stability
- Softmax Trick (code):
  ```python
  exp_scores = np.exp(scores - np.max(scores))  # Avoid overflow
  ```
- He Initialisation (code):
  ```python
  # Initialise weights with sqrt(2/(fan_in + fan_out))
  self.W1 = np.random.randn(...) * np.sqrt(2.0 / (input_dim + hidden_dim))
  ```


### 4. Language Modelling as ML


#### ML Concepts
- Supervised Learning: Trained on (input sequence → target word) pairs
- Probabilistic Modelling: Outputs a distribution over possible next words
- Generalisation: Learns patterns from training text to predict unseen sequences

#### Limitations (vs. Modern LLMs)
- Fixed context window (vs. attention in Transformers)
- Feedforward architecture (vs. recurrent/self-attention mechanisms)
- Small scale (~1k vocabulary vs. billions of tokens)

### Summary

1. It learns from data (text) without explicit rules
2. Uses gradient-based optimization to improve predictions
3. Implements core ML components: embeddings, hidden layers, loss functions, regularization

The code implements the math of neural networks directly--matrix multiplications, activation functions, 
and gradient computations--making it an example of "ML from scratch".
