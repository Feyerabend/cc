import numpy as np
import re
import time
from collections import Counter, defaultdict

class MiniNeuralLM:
    """
    A simple feedforward neural network language model.
    Predicts the next word given a context window of previous words.
    """
    
    def __init__(self, 
                 vocab_size=1000, 
                 embedding_dim=32, 
                 context_size=3, 
                 hidden_dim=128, 
                 learning_rate=0.01):
        """
        Initialize the model parameters.
        
        Args:
            vocab_size: Size of vocabulary (number of unique words)
            embedding_dim: Dimension of word embeddings
            context_size: Number of previous words to use as context
            hidden_dim: Size of the hidden layer
            learning_rate: Learning rate for SGD
        """
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.context_size = context_size
        self.hidden_dim = hidden_dim
        self.learning_rate = learning_rate
        
        # Initialize embeddings (vocab_size x embedding_dim)
        # Use Xavier/Glorot initialization for better gradient flow
        self.embeddings = np.random.randn(vocab_size, embedding_dim) * np.sqrt(2.0 / (vocab_size + embedding_dim))
        
        # Concatenated embeddings input size
        input_dim = context_size * embedding_dim
        
        # Hidden layer weights and biases
        self.W1 = np.random.randn(input_dim, hidden_dim) * np.sqrt(2.0 / (input_dim + hidden_dim))
        self.b1 = np.zeros(hidden_dim)
        
        # Output layer weights and biases
        self.W2 = np.random.randn(hidden_dim, vocab_size) * np.sqrt(2.0 / (hidden_dim + vocab_size))
        self.b2 = np.zeros(vocab_size)
        
        # For tracking progress
        self.losses = []
        
    def forward(self, context_indices):
        """
        Forward pass of the neural network.
        
        Args:
            context_indices: List of word indices in the context window
            
        Returns:
            probs: Probability distribution over next words
            cache: Cached values for backward pass
        """
        # Lookup embeddings for each word in context
        embedded = [self.embeddings[idx] for idx in context_indices]
        
        # Concatenate embeddings
        x = np.concatenate(embedded)
        
        # Hidden layer with ReLU activation
        hidden_pre = np.dot(x, self.W1) + self.b1
        hidden = np.maximum(0, hidden_pre)  # ReLU activation
        
        # Output layer with softmax
        scores = np.dot(hidden, self.W2) + self.b2
        exp_scores = np.exp(scores - np.max(scores))  # Subtract max for numerical stability
        probs = exp_scores / np.sum(exp_scores)
        
        # Cache values for backward pass
        cache = {
            'context_indices': context_indices,
            'x': x,
            'hidden_pre': hidden_pre,
            'hidden': hidden,
            'scores': scores,
            'probs': probs
        }
        
        return probs, cache
    
    def backward(self, probs, target_idx, cache):
        """
        Backward pass to compute gradients.
        
        Args:
            probs: Output probabilities from forward pass
            target_idx: Index of the actual next word
            cache: Cached values from forward pass
            
        Returns:
            gradients: Dictionary of gradients for all parameters
        """
        # Initialize gradient dictionary
        grads = {
            'W1': np.zeros_like(self.W1),
            'b1': np.zeros_like(self.b1),
            'W2': np.zeros_like(self.W2),
            'b2': np.zeros_like(self.b2),
            'embeddings': np.zeros_like(self.embeddings)
        }
        
        # Gradient for output layer
        dscores = probs.copy()
        dscores[target_idx] -= 1
        
        # Gradients for W2 and b2
        grads['W2'] = np.outer(cache['hidden'], dscores)
        grads['b2'] = dscores
        
        # Gradient for hidden layer
        dhidden = np.dot(dscores, self.W2.T)
        
        # ReLU gradient: dhidden_pre = dhidden * (hidden_pre > 0)
        dhidden_pre = dhidden * (cache['hidden_pre'] > 0)
        
        # Gradients for W1 and b1
        grads['W1'] = np.outer(cache['x'], dhidden_pre)
        grads['b1'] = dhidden_pre
        
        # Gradient for embeddings
        dx = np.dot(dhidden_pre, self.W1.T)
        
        # Split the gradient to each embedding
        split_size = self.embedding_dim
        dx_split = [dx[i*split_size:(i+1)*split_size] for i in range(self.context_size)]
        
        # Update embedding gradients for each context word
        for i, idx in enumerate(cache['context_indices']):
            grads['embeddings'][idx] += dx_split[i]
        
        return grads
    
    def update_params(self, grads):
        """
        Update parameters using calculated gradients.
        
        Args:
            grads: Dictionary of gradients
        """
        # Simple SGD update
        self.W1 -= self.learning_rate * grads['W1']
        self.b1 -= self.learning_rate * grads['b1']
        self.W2 -= self.learning_rate * grads['W2']
        self.b2 -= self.learning_rate * grads['b2']
        self.embeddings -= self.learning_rate * grads['embeddings']
    
    def train_step(self, context_indices, target_idx):
        """
        Perform one training step (forward and backward pass).
        
        Args:
            context_indices: Indices of context words
            target_idx: Index of target word
            
        Returns:
            loss: Cross-entropy loss for this example
        """
        # Forward pass
        probs, cache = self.forward(context_indices)
        
        # Compute loss (cross entropy)
        loss = -np.log(probs[target_idx] + 1e-15)  # Add small epsilon to avoid log(0)
        
        # Backward pass
        grads = self.backward(probs, target_idx, cache)
        
        # Update parameters
        self.update_params(grads)
        
        return loss
    
    def predict(self, context_indices):
        """
        Predict the next word given context.
        
        Args:
            context_indices: Indices of context words
            
        Returns:
            next_word_idx: Index of predicted next word
        """
        probs, _ = self.forward(context_indices)
        return np.argmax(probs)
    
    def predict_topk(self, context_indices, k=5):
        """
        Predict the top k most likely next words.
        
        Args:
            context_indices: Indices of context words
            k: Number of top predictions to return
            
        Returns:
            topk_indices: Indices of top k predicted words
            topk_probs: Probabilities of top k predicted words
        """
        probs, _ = self.forward(context_indices)
        topk_indices = np.argsort(probs)[::-1][:k]
        topk_probs = probs[topk_indices]
        return topk_indices, topk_probs

    def calculate_perplexity(self, examples):
        """
        Calculate perplexity on given examples.
        
        Args:
            examples: List of (context_indices, target_idx) pairs
            
        Returns:
            perplexity: Calculated perplexity
        """
        total_loss = 0
        count = 0
        
        for context_indices, target_idx in examples:
            # Forward pass
            probs, _ = self.forward(context_indices)
            
            # Compute loss (cross entropy)
            loss = -np.log(probs[target_idx] + 1e-15)  # Add small epsilon to avoid log(0)
            total_loss += loss
            count += 1
        
        avg_loss = total_loss / count
        perplexity = np.exp(avg_loss)
        return perplexity

class TextPreprocessor:
    """Helper class to preprocess text and create training data."""
    
    def __init__(self, vocab_size=1000, context_size=3):
        """
        Initialize the text preprocessor.
        
        Args:
            vocab_size: Maximum vocabulary size
            context_size: Size of context window
        """
        self.vocab_size = vocab_size
        self.context_size = context_size
        self.word_to_idx = {}
        self.idx_to_word = {}
        self.vocab = []
        self.unk_token = "<UNK>"
        self.pad_token = "<PAD>"
    
    def build_vocab(self, text):
        """
        Build vocabulary from text.
        
        Args:
            text: Raw text string
            
        Returns:
            vocab: List of words in vocabulary
        """
        # Clean and tokenize text
        words = self._tokenize(text)
        
        # Count word frequencies
        word_counts = Counter(words)
        
        # Use most common words plus special tokens
        common_words = [word for word, _ in word_counts.most_common(self.vocab_size - 2)]
        self.vocab = [self.pad_token, self.unk_token] + common_words
        
        # Build mappings
        self.word_to_idx = {word: idx for idx, word in enumerate(self.vocab)}
        self.idx_to_word = {idx: word for idx, word in enumerate(self.vocab)}
        
        return self.vocab
    
    def _tokenize(self, text):
        """
        Simple tokenization by splitting on whitespace and punctuation.
        
        Args:
            text: Raw text string
            
        Returns:
            words: List of words
        """
        # Convert to lowercase
        text = text.lower()
        
        # Replace punctuation with space + punctuation + space for better tokenization
        for punct in '.,!?;:()[]{}""\'':
            text = text.replace(punct, f' {punct} ')
        
        # Split on whitespace and filter empty strings
        words = [word for word in text.split() if word]
        
        return words
    
    def text_to_indices(self, text):
        """
        Convert text to word indices.
        
        Args:
            text: Raw text string
            
        Returns:
            indices: List of word indices
        """
        words = self._tokenize(text)
        indices = [self.word_to_idx.get(word, self.word_to_idx[self.unk_token]) for word in words]
        return indices
    
    def create_training_examples(self, text):
        """
        Create context-target pairs for training.
        
        Args:
            text: Raw text string
            
        Returns:
            examples: List of (context_indices, target_idx) pairs
        """
        indices = self.text_to_indices(text)
        examples = []
        
        # Pad the beginning with pad_token
        padded_indices = [self.word_to_idx[self.pad_token]] * self.context_size + indices
        
        # Create context-target pairs
        for i in range(len(indices)):
            context_indices = padded_indices[i:i+self.context_size]
            target_idx = indices[i]
            examples.append((context_indices, target_idx))
        
        return examples
    
    def indices_to_text(self, indices):
        """
        Convert word indices back to text.
        
        Args:
            indices: List of word indices
            
        Returns:
            text: Space-joined words
        """
        words = [self.idx_to_word.get(idx, self.unk_token) for idx in indices]
        return ' '.join(words)


def train_model(model, preprocessor, text, num_epochs=5, batch_size=32, print_every=1000):
    # Create training examples
    examples = preprocessor.create_training_examples(text)
    
    # Split into train and validation sets (80/20 split)
    split_idx = int(0.8 * len(examples))
    train_examples = examples[:split_idx]
    val_examples = examples[split_idx:]
    
    print(f"Training on {len(train_examples)} examples, validating on {len(val_examples)} examples for {num_epochs} epochs...")
    
    for epoch in range(num_epochs):
        # Shuffle training examples for each epoch
        np.random.shuffle(train_examples)
        
        total_loss = 0
        batch_loss = 0
        
        for i, (context_indices, target_idx) in enumerate(train_examples):
            # Train on one example
            loss = model.train_step(context_indices, target_idx)
            total_loss += loss
            batch_loss += loss
            
            # Print progress
            if (i + 1) % print_every == 0:
                avg_batch_loss = batch_loss / print_every
                batch_loss = 0
                # Calculate validation perplexity
                val_perplexity = model.calculate_perplexity(val_examples)
                print(f"Epoch {epoch+1}/{num_epochs}, Step {i+1}/{len(train_examples)}, "
                      f"Loss: {avg_batch_loss:.4f}, Val Perplexity: {val_perplexity:.2f}")
                
        # Print epoch stats
        avg_epoch_loss = total_loss / len(train_examples)
        train_perplexity = np.exp(avg_epoch_loss)
        val_perplexity = model.calculate_perplexity(val_examples)
        model.losses.append(avg_epoch_loss)
        print(f"Epoch {epoch+1} complete. "
              f"Train Loss: {avg_epoch_loss:.4f}, "
              f"Train PPL: {train_perplexity:.2f}, "
              f"Val PPL: {val_perplexity:.2f}")
    
    return model

def generate_text(model, preprocessor, seed_text, num_words=50, temperature=1.0):
    """
    Generate text by sampling from the model.
    
    Args:
        model: Trained MiniNeuralLM instance
        preprocessor: TextPreprocessor instance
        seed_text: Text to start generation with
        num_words: Number of words to generate
        temperature: Sampling temperature (higher = more diverse)
        
    Returns:
        generated_text: Generated text string
    """
    # Convert seed text to indices
    seed_indices = preprocessor.text_to_indices(seed_text)
    
    # Make sure we have enough context
    if len(seed_indices) < model.context_size:
        # Pad with padding token
        pad_idx = preprocessor.word_to_idx[preprocessor.pad_token]
        seed_indices = [pad_idx] * (model.context_size - len(seed_indices)) + seed_indices
    
    # Take the last context_size words as initial context
    context_indices = seed_indices[-model.context_size:]
    generated_indices = []
    
    for _ in range(num_words):
        # Get probability distribution for next word
        probs, _ = model.forward(context_indices)
        
        # Apply temperature
        if temperature != 1.0:
            # Adjust probabilities by temperature
            probs = np.power(probs, 1.0 / temperature)
            probs = probs / np.sum(probs)
        
        # Sample next word index
        next_idx = np.random.choice(len(probs), p=probs)
        generated_indices.append(next_idx)
        
        # Update context
        context_indices = context_indices[1:] + [next_idx]
    
    # Convert generated indices to text
    generated_text = preprocessor.indices_to_text(generated_indices)
    
    return seed_text + " " + generated_text


def main():
    """Example usage of the mini neural language model."""
    
    # Sample text for demonstration
    # In a real application, you would load a larger text corpus
    sample_text = """
    The quick brown fox jumps over the lazy dog. A neural network is a 
    computational model inspired by the structure and function of the human brain.
    Deep learning models use multiple layers of neural networks. The embeddings
    transform words into vectors in a continuous space. Language models predict
    the probability of the next word given previous words. Training requires 
    optimizing the parameters to minimize the loss function. Gradient descent
    updates the weights based on the gradient of the loss. Backpropagation
    calculates the gradients efficiently. The hidden layer captures intermediate
    representations. The output layer produces the final predictions.
    """
    
    # Create preprocessor and build vocabulary
    preprocessor = TextPreprocessor(vocab_size=100, context_size=3)
    vocab = preprocessor.build_vocab(sample_text)
    
    # Print vocabulary summary
    print(f"Vocabulary size: {len(vocab)}")
    print(f"Sample vocab: {vocab[:10]}...")
    
    # Create model
    model = MiniNeuralLM(
        vocab_size=len(vocab),
        embedding_dim=32,
        context_size=3,
        hidden_dim=64,
        learning_rate=0.01
    )
    
    # Train model
    model = train_model(
        model, 
        preprocessor, 
        sample_text, 
        num_epochs=10, 
        batch_size=1,  # Online learning (batch_size=1)
        print_every=50
    )
    
    # Generate text
    seed_text = "The neural network"
    generated = generate_text(model, preprocessor, seed_text, num_words=20, temperature=0.8)
    print("\nGenerated text:")
    print(generated)
    
    # Show model performance over time
    print("\nTraining loss by epoch:")
    for i, loss in enumerate(model.losses):
        print(f"Epoch {i+1}: {loss:.4f}")


if __name__ == "__main__":
    main()
