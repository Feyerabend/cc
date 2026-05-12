import numpy as np
import re
import time
from collections import Counter, defaultdict
import os
import pickle
import argparse

class MiniNeuralLM:
    def __init__(self, 
                 vocab_size=1000, 
                 embedding_dim=32, 
                 context_size=3, 
                 hidden_dim=128, 
                 learning_rate=0.01,
                 use_two_hidden_layers=True,
                 dropout_rate=0.2,
                 momentum_beta=0.9):
        """
        Initialize the neural language model with He initialization and momentum
        
        Parameters:
        - vocab_size: Size of the vocabulary
        - embedding_dim: Dimension of word embeddings
        - context_size: Number of previous words used as context
        - hidden_dim: Dimension of hidden layers
        - learning_rate: Initial learning rate
        - use_two_hidden_layers: Whether to use two hidden layers
        - dropout_rate: Dropout probability (0 = no dropout)
        - momentum_beta: Momentum parameter (0.9 is typical)
        """
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.context_size = context_size
        self.hidden_dim = hidden_dim
        self.learning_rate = learning_rate
        self.use_two_hidden_layers = use_two_hidden_layers
        self.dropout_rate = dropout_rate
        self.momentum_beta = momentum_beta
        
        # Initialize embeddings with He initialization
        self.embeddings = np.random.randn(vocab_size, embedding_dim) * np.sqrt(2.0 / (vocab_size + embedding_dim))
        
        input_dim = context_size * embedding_dim
        
        # Initialize first hidden layer weights
        self.W1 = np.random.randn(input_dim, hidden_dim) * np.sqrt(2.0 / (input_dim + hidden_dim))
        self.b1 = np.zeros(hidden_dim)
        
        # Optional second hidden layer
        if use_two_hidden_layers:
            self.W1_5 = np.random.randn(hidden_dim, hidden_dim) * np.sqrt(2.0 / (hidden_dim + hidden_dim))
            self.b1_5 = np.zeros(hidden_dim)
            
        # Output layer weights
        self.W2 = np.random.randn(hidden_dim, vocab_size) * np.sqrt(2.0 / (hidden_dim + vocab_size))
        self.b2 = np.zeros(vocab_size)
        
        # Initialize momentum buffers
        self.momentum = {
            'W1': np.zeros_like(self.W1),
            'b1': np.zeros_like(self.b1),
            'W2': np.zeros_like(self.W2),
            'b2': np.zeros_like(self.b2),
            'embeddings': np.zeros_like(self.embeddings)
        }
        if use_two_hidden_layers:
            self.momentum['W1_5'] = np.zeros_like(self.W1_5)
            self.momentum['b1_5'] = np.zeros_like(self.b1_5)
        
        # Training tracking
        self.losses = []
    
    def forward(self, context_indices, is_training=True):
        """
        Forward pass through the network with optional dropout
        
        Parameters:
        - context_indices: Indices of context words
        - is_training: Whether in training mode (affects dropout)
        
        Returns:
        - probs: Probability distribution over vocabulary
        - cache: Intermediate values needed for backpropagation
        """
        # Embedding lookup
        embedded = [self.embeddings[idx] for idx in context_indices]
        x = np.concatenate(embedded)
        
        # First hidden layer with ReLU
        hidden_pre = np.dot(x, self.W1) + self.b1
        hidden = np.maximum(0, hidden_pre)  # ReLU activation
        
        # Apply dropout if training
        if is_training and self.dropout_rate > 0:
            dropout_mask1 = np.random.binomial(1, 1-self.dropout_rate, size=hidden.shape) / (1-self.dropout_rate)
            hidden *= dropout_mask1
        else:
            dropout_mask1 = None
        
        # Optional second hidden layer
        hidden_pre2 = None
        hidden2 = hidden
        dropout_mask2 = None
        
        if self.use_two_hidden_layers:
            hidden_pre2 = np.dot(hidden, self.W1_5) + self.b1_5
            hidden2 = np.maximum(0, hidden_pre2)  # ReLU activation
            
            if is_training and self.dropout_rate > 0:
                dropout_mask2 = np.random.binomial(1, 1-self.dropout_rate, size=hidden2.shape) / (1-self.dropout_rate)
                hidden2 *= dropout_mask2
        
        # Output layer with softmax
        scores = np.dot(hidden2, self.W2) + self.b2
        # Numerical stability trick for softmax
        exp_scores = np.exp(scores - np.max(scores))
        probs = exp_scores / np.sum(exp_scores)
        
        # Cache values for backpropagation
        cache = {
            'context_indices': context_indices,
            'x': x,
            'hidden_pre': hidden_pre,
            'hidden': hidden,
            'hidden_pre2': hidden_pre2,
            'hidden2': hidden2,
            'dropout_mask1': dropout_mask1,
            'dropout_mask2': dropout_mask2,
            'scores': scores,
            'probs': probs
        }
        
        return probs, cache
    
    def backward(self, probs, target_idx, cache):
        """
        Backward pass to compute gradients
        
        Parameters:
        - probs: Output probabilities from forward pass
        - target_idx: Index of target word
        - cache: Values cached from forward pass
        
        Returns:
        - Dictionary of gradients for all parameters
        """
        grads = {
            'W1': np.zeros_like(self.W1),
            'b1': np.zeros_like(self.b1),
            'W2': np.zeros_like(self.W2),
            'b2': np.zeros_like(self.b2),
            'embeddings': np.zeros_like(self.embeddings)
        }
        
        if self.use_two_hidden_layers:
            grads['W1_5'] = np.zeros_like(self.W1_5)
            grads['b1_5'] = np.zeros_like(self.b1_5)
        
        # Gradient of loss w.r.t. scores
        dscores = probs.copy()
        dscores[target_idx] -= 1
        
        # Gradient of output layer weights
        hidden_final = cache['hidden2']
        grads['W2'] = np.outer(hidden_final, dscores)
        grads['b2'] = dscores
        
        # Backpropagate through second hidden layer if present
        dhidden_final = np.dot(dscores, self.W2.T)
        
        if cache['dropout_mask2'] is not None:
            dhidden_final *= cache['dropout_mask2']
        
        if self.use_two_hidden_layers:
            # Gradient through ReLU
            dhidden_pre2 = dhidden_final * (cache['hidden_pre2'] > 0)
            
            # Gradient of second hidden layer weights
            grads['W1_5'] = np.outer(cache['hidden'], dhidden_pre2)
            grads['b1_5'] = dhidden_pre2
            
            # Backpropagate to first hidden layer
            dhidden = np.dot(dhidden_pre2, self.W1_5.T)
        else:
            dhidden = dhidden_final
        
        # Apply dropout mask if present
        if cache['dropout_mask1'] is not None:
            dhidden *= cache['dropout_mask1']
        
        # Gradient through ReLU
        dhidden_pre = dhidden * (cache['hidden_pre'] > 0)
        
        # Gradient of first hidden layer weights
        grads['W1'] = np.outer(cache['x'], dhidden_pre)
        grads['b1'] = dhidden_pre
        
        # Backpropagate to embeddings
        dx = np.dot(dhidden_pre, self.W1.T)
        split_size = self.embedding_dim
        dx_split = [dx[i*split_size:(i+1)*split_size] for i in range(self.context_size)]
        
        # Update embedding gradients
        for i, idx in enumerate(cache['context_indices']):
            grads['embeddings'][idx] += dx_split[i]
        
        return grads
    
    def update_params(self, grads):
        """
        Update parameters using gradient descent with momentum
        
        Parameters:
        - grads: Dictionary of gradients from backward pass
        """
        for param_name in grads:
            # Update momentum
            self.momentum[param_name] = (self.momentum_beta * self.momentum[param_name] + 
                                        (1 - self.momentum_beta) * grads[param_name])
            
            # Apply parameter update
            if param_name == 'W1':
                self.W1 -= self.learning_rate * self.momentum[param_name]
            elif param_name == 'b1':
                self.b1 -= self.learning_rate * self.momentum[param_name]
            elif param_name == 'W1_5' and self.use_two_hidden_layers:
                self.W1_5 -= self.learning_rate * self.momentum[param_name]
            elif param_name == 'b1_5' and self.use_two_hidden_layers:
                self.b1_5 -= self.learning_rate * self.momentum[param_name]
            elif param_name == 'W2':
                self.W2 -= self.learning_rate * self.momentum[param_name]
            elif param_name == 'b2':
                self.b2 -= self.learning_rate * self.momentum[param_name]
            elif param_name == 'embeddings':
                self.embeddings -= self.learning_rate * self.momentum[param_name]
    
    def train_step(self, context_indices, target_idx):
        """
        Single training step: forward pass, loss computation, backward pass, parameter update
        
        Parameters:
        - context_indices: Indices of context words
        - target_idx: Index of target word
        
        Returns:
        - loss: Computed loss for this example
        """
        probs, cache = self.forward(context_indices)
        loss = -np.log(probs[target_idx] + 1e-15)  # Cross-entropy loss
        
        grads = self.backward(probs, target_idx, cache)
        self.update_params(grads)
        
        return loss
    
    def predict(self, context_indices):
        """
        Predict the most likely next word
        
        Parameters:
        - context_indices: Indices of context words
        
        Returns:
        - Index of predicted word
        """
        probs, _ = self.forward(context_indices, is_training=False)
        return np.argmax(probs)
    
    def predict_topk(self, context_indices, k=5):
        """
        Predict top-k most likely next words
        
        Parameters:
        - context_indices: Indices of context words
        - k: Number of top predictions to return
        
        Returns:
        - Tuple of (indices, probabilities) for top-k predictions
        """
        probs, _ = self.forward(context_indices, is_training=False)
        topk_indices = np.argsort(probs)[::-1][:k]
        topk_probs = probs[topk_indices]
        return topk_indices, topk_probs


class TextPreprocessor:
    def __init__(self, vocab_size=1000, context_size=3):
        """
        Initialize text preprocessor
        
        Parameters:
        - vocab_size: Maximum vocabulary size
        - context_size: Number of context words to use
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
        Build vocabulary from text
        
        Parameters:
        - text: Input text to process
        
        Returns:
        - List of vocabulary words
        """
        words = self._tokenize(text)
        word_counts = Counter(words)
        
        # Keep most common words, reserving spots for special tokens
        common_words = [word for word, _ in word_counts.most_common(self.vocab_size - 2)]
        self.vocab = [self.pad_token, self.unk_token] + common_words
        
        self.word_to_idx = {word: idx for idx, word in enumerate(self.vocab)}
        self.idx_to_word = {idx: word for idx, word in enumerate(self.vocab)}
        
        return self.vocab
    
    def _tokenize(self, text):
        """
        Basic tokenization of text
        
        Parameters:
        - text: Input text
        
        Returns:
        - List of tokens
        """
        text = text.lower()
        
        # Add spaces around punctuation
        for punct in '.,!?;:()[]{}""\'':
            text = text.replace(punct, f' {punct} ')
        
        words = [word for word in text.split() if word]
        
        return words
    
    def text_to_indices(self, text):
        """
        Convert text to numerical indices
        
        Parameters:
        - text: Input text
        
        Returns:
        - List of word indices
        """
        words = self._tokenize(text)
        indices = [self.word_to_idx.get(word, self.word_to_idx[self.unk_token]) for word in words]
        return indices
    
    def create_training_examples(self, text):
        """
        Create training examples from text
        
        Parameters:
        - text: Input text
        
        Returns:
        - List of (context_indices, target_idx) pairs
        """
        indices = self.text_to_indices(text)
        examples = []
        
        # Pad beginning with <PAD> tokens
        padded_indices = [self.word_to_idx[self.pad_token]] * self.context_size + indices
        
        for i in range(len(indices)):
            context_indices = padded_indices[i:i+self.context_size]
            target_idx = indices[i]
            examples.append((context_indices, target_idx))
        
        return examples
    
    def indices_to_text(self, indices):
        """
        Convert indices back to text
        
        Parameters:
        - indices: List of word indices
        
        Returns:
        - String of reconstructed text
        """
        words = [self.idx_to_word.get(idx, self.unk_token) for idx in indices]
        return ' '.join(words)


def train_model(model, preprocessor, text, num_epochs=5, batch_size=32, print_every=1000):
    """
    Train the language model
    
    Parameters:
    - model: MiniNeuralLM instance
    - preprocessor: TextPreprocessor instance
    - text: Training text
    - num_epochs: Number of training epochs
    - batch_size: Size of mini-batches (currently not implemented)
    - print_every: Print progress every N examples
    
    Returns:
    - Trained model
    """
    examples = preprocessor.create_training_examples(text)
    
    print(f"Training on {len(examples)} examples for {num_epochs} epochs...")
    start_time = time.time()
    
    for epoch in range(num_epochs):
        np.random.shuffle(examples)
        
        total_loss = 0
        batch_loss = 0
        
        for i, (context_indices, target_idx) in enumerate(examples):
            loss = model.train_step(context_indices, target_idx)
            total_loss += loss
            batch_loss += loss
            
            if (i + 1) % print_every == 0:
                avg_batch_loss = batch_loss / print_every
                batch_loss = 0
                print(f"Epoch {epoch+1}/{num_epochs}, Step {i+1}/{len(examples)}, "
                      f"Loss: {avg_batch_loss:.4f}, Time: {time.time() - start_time:.2f}s")
                
        avg_epoch_loss = total_loss / len(examples)
        model.losses.append(avg_epoch_loss)
        print(f"Epoch {epoch+1} complete. Average loss: {avg_epoch_loss:.4f}")
    
    print(f"Training complete in {time.time() - start_time:.2f}s")
    return model


def generate_text(model, preprocessor, seed_text, num_words=50, temperature=1.0):
    """
    Generate text from the model
    
    Parameters:
    - model: Trained MiniNeuralLM
    - preprocessor: TextPreprocessor
    - seed_text: Starting text
    - num_words: Number of words to generate
    - temperature: Controls randomness (1.0 = normal, <1.0 = more conservative)
    
    Returns:
    - Generated text string
    """
    seed_indices = preprocessor.text_to_indices(seed_text)
    
    # Pad if seed is shorter than context window
    if len(seed_indices) < model.context_size:
        pad_idx = preprocessor.word_to_idx[preprocessor.pad_token]
        seed_indices = [pad_idx] * (model.context_size - len(seed_indices)) + seed_indices
    
    context_indices = seed_indices[-model.context_size:]
    generated_indices = []
    
    for _ in range(num_words):
        probs, _ = model.forward(context_indices, is_training=False)
        
        # Apply temperature scaling
        if temperature != 1.0:
            probs = np.power(probs, 1.0 / temperature)
            probs = probs / np.sum(probs)
        
        # Sample from distribution
        next_idx = np.random.choice(len(probs), p=probs)
        generated_indices.append(next_idx)
        
        # Update context window
        context_indices = context_indices[1:] + [next_idx]
    
    generated_text = preprocessor.indices_to_text(generated_indices)
    
    return seed_text + " " + generated_text


def load_text_from_folder(folder_path):
    """
    Load all text files from a folder
    
    Parameters:
    - folder_path: Path to folder containing text files
    
    Returns:
    - Concatenated text from all files
    """
    all_text = ""
    file_count = 0
    
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return all_text
    
    for root, _, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith(('.txt', '.md', '.text')):
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_text = f.read()
                        all_text += file_text + "\n\n"
                        file_count += 1
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    print(f"Loaded {file_count} text files from {folder_path}")
    return all_text


def save_model(model, preprocessor, filepath):
    """
    Save model and preprocessor to file
    
    Parameters:
    - model: Trained MiniNeuralLM
    - preprocessor: TextPreprocessor
    - filepath: Path to save file
    """
    data = {
        'model_params': {
            'vocab_size': model.vocab_size,
            'embedding_dim': model.embedding_dim,
            'context_size': model.context_size,
            'hidden_dim': model.hidden_dim,
            'learning_rate': model.learning_rate,
            'use_two_hidden_layers': model.use_two_hidden_layers,
            'dropout_rate': model.dropout_rate,
            'momentum_beta': model.momentum_beta
        },
        'model_weights': {
            'embeddings': model.embeddings,
            'W1': model.W1,
            'b1': model.b1,
            'W1_5': model.W1_5 if model.use_two_hidden_layers else None,
            'b1_5': model.b1_5 if model.use_two_hidden_layers else None,
            'W2': model.W2,
            'b2': model.b2
        },
        'vocab': preprocessor.vocab,
        'word_to_idx': preprocessor.word_to_idx,
        'idx_to_word': preprocessor.idx_to_word
    }
    
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)
    
    print(f"Model saved to {filepath}")


def load_model(filepath):
    """
    Load model and preprocessor from file
    
    Parameters:
    - filepath: Path to saved model file
    
    Returns:
    - Tuple of (model, preprocessor)
    """
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    
    preprocessor = TextPreprocessor(
        vocab_size=len(data['vocab']),
        context_size=data['model_params']['context_size']
    )
    preprocessor.vocab = data['vocab']
    preprocessor.word_to_idx = data['word_to_idx']
    preprocessor.idx_to_word = data['idx_to_word']
    
    model = MiniNeuralLM(
        vocab_size=data['model_params']['vocab_size'],
        embedding_dim=data['model_params']['embedding_dim'],
        context_size=data['model_params']['context_size'],
        hidden_dim=data['model_params']['hidden_dim'],
        learning_rate=data['model_params']['learning_rate'],
        use_two_hidden_layers=data['model_params']['use_two_hidden_layers'],
        dropout_rate=data['model_params']['dropout_rate'],
        momentum_beta=data['model_params']['momentum_beta']
    )
    
    model.embeddings = data['model_weights']['embeddings']
    model.W1 = data['model_weights']['W1']
    model.b1 = data['model_weights']['b1']
    if model.use_two_hidden_layers:
        model.W1_5 = data['model_weights']['W1_5']
        model.b1_5 = data['model_weights']['b1_5']
    model.W2 = data['model_weights']['W2']
    model.b2 = data['model_weights']['b2']
    
    print(f"Model loaded from {filepath}")
    return model, preprocessor


def evaluate_perplexity(model, preprocessor, text):
    """
    Evaluate perplexity of model on given text
    
    Parameters:
    - model: Trained MiniNeuralLM
    - preprocessor: TextPreprocessor
    - text: Evaluation text
    
    Returns:
    - Perplexity score (lower is better)
    """
    examples = preprocessor.create_training_examples(text)
    
    total_log_likelihood = 0
    for context_indices, target_idx in examples:
        probs, _ = model.forward(context_indices, is_training=False)
        probability = probs[target_idx]
        total_log_likelihood += np.log(probability + 1e-15)
    
    avg_neg_log_likelihood = -total_log_likelihood / len(examples)
    perplexity = np.exp(avg_neg_log_likelihood)
    
    return perplexity


def main():
    """Main entry point for command line usage"""
    parser = argparse.ArgumentParser(description='Train and use a mini neural language model')
    parser.add_argument('--data', type=str, help='Path to data folder or text file')
    parser.add_argument('--vocab_size', type=int, default=5000, help='Vocabulary size')
    parser.add_argument('--embedding_dim', type=int, default=64, help='Embedding dimension')
    parser.add_argument('--context_size', type=int, default=5, help='Context window size')
    parser.add_argument('--hidden_dim', type=int, default=256, help='Hidden layer dimension')
    parser.add_argument('--learning_rate', type=float, default=0.01, help='Learning rate')
    parser.add_argument('--epochs', type=int, default=5, help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size (currently not implemented)')
    parser.add_argument('--save', type=str, help='Path to save the model')
    parser.add_argument('--load', type=str, help='Path to load the model')
    parser.add_argument('--generate', type=str, help='Seed text for generation')
    parser.add_argument('--num_words', type=int, default=50, help='Number of words to generate')
    parser.add_argument('--temperature', type=float, default=0.8, help='Sampling temperature')
    
    args = parser.parse_args()
    
    if args.load:
        model, preprocessor = load_model(args.load)
    else:
        if not args.data:
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

        else:
            if os.path.isdir(args.data):
                sample_text = load_text_from_folder(args.data)
            else:
                try:
                    with open(args.data, 'r', encoding='utf-8') as f:
                        sample_text = f.read()
                    print(f"Loaded text from {args.data}")
                except Exception as e:
                    print(f"Error reading {args.data}: {e}")
                    return
        
        preprocessor = TextPreprocessor(vocab_size=args.vocab_size, context_size=args.context_size)
        vocab = preprocessor.build_vocab(sample_text)
        
        print(f"Vocabulary size: {len(vocab)}")
        print(f"Sample vocab: {vocab[:10]}...")
        
        model = MiniNeuralLM(
            vocab_size=len(vocab),
            embedding_dim=args.embedding_dim,
            context_size=args.context_size,
            hidden_dim=args.hidden_dim,
            learning_rate=args.learning_rate,
            use_two_hidden_layers=True,
            dropout_rate=0.2,
            momentum_beta=0.9
        )
        
        model = train_model(
            model, 
            preprocessor, 
            sample_text, 
            num_epochs=args.epochs, 
            batch_size=args.batch_size,
            print_every=100
        )
    
    if args.save:
        save_model(model, preprocessor, args.save)
    
    if args.generate:
        seed_text = args.generate
        generated = generate_text(
            model, 
            preprocessor, 
            seed_text, 
            num_words=args.num_words, 
            temperature=args.temperature
        )
        print("\nGenerated text:")
        print(generated)
    elif not args.load:
        seed_text = "The neural network"
        generated = generate_text(
            model, 
            preprocessor, 
            seed_text, 
            num_words=args.num_words, 
            temperature=args.temperature
        )
        print("\nGenerated text:")
        print(generated)
    
    if not args.load:
        print("\nTraining loss by epoch:")
        for i, loss in enumerate(model.losses):
            print(f"Epoch {i+1}: {loss:.4f}")
            
    eval_text = "The neural network learns from data. Language models predict words."
    perplexity = evaluate_perplexity(model, preprocessor, eval_text)
    print(f"\nPerplexity on sample text: {perplexity:.2f}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()