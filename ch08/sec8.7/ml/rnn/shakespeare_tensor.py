import numpy as np
import random
import os
import sys
import glob
import time

class TensorShakespeareRNN:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.01):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        
        # Initialize weights with Xavier/He initialization for better convergence
        self.Wxh = np.random.randn(hidden_size, input_size) * np.sqrt(2.0 / input_size)
        self.Whh = np.random.randn(hidden_size, hidden_size) * np.sqrt(2.0 / hidden_size)
        self.Why = np.random.randn(output_size, hidden_size) * np.sqrt(2.0 / hidden_size)
        
        # Biases
        self.bh = np.zeros((hidden_size, 1))
        self.by = np.zeros((output_size, 1))
        
        # For gradient clipping
        self.max_grad_norm = 5.0
        
        # Adam optimizer parameters
        self.beta1, self.beta2 = 0.9, 0.999
        self.eps = 1e-8
        self.t = 0  # Time step for Adam
        
        # Adam momentum terms
        self.mWxh = np.zeros_like(self.Wxh)
        self.mWhh = np.zeros_like(self.Whh)
        self.mWhy = np.zeros_like(self.Why)
        self.mbh = np.zeros_like(self.bh)
        self.mby = np.zeros_like(self.by)
        
        self.vWxh = np.zeros_like(self.Wxh)
        self.vWhh = np.zeros_like(self.Whh)
        self.vWhy = np.zeros_like(self.Why)
        self.vbh = np.zeros_like(self.bh)
        self.vby = np.zeros_like(self.by)
    
    def tanh_fast(self, x):
        """Optimized tanh using NumPy"""
        return np.tanh(x)
    
    def softmax(self, x):
        """Numerically stable softmax"""
        # Subtract max for numerical stability
        exp_x = np.exp(x - np.max(x, axis=0, keepdims=True))
        return exp_x / np.sum(exp_x, axis=0, keepdims=True)
    
    def forward(self, inputs):
        """
        Vectorized forward pass
        inputs: list of one-hot vectors (seq_len, vocab_size)
        """
        seq_len = len(inputs)
        
        # Convert inputs to tensor (vocab_size, seq_len)
        X = np.column_stack(inputs)
        
        # Initialize hidden states
        H = np.zeros((self.hidden_size, seq_len + 1))
        Y = np.zeros((self.output_size, seq_len))
        P = np.zeros((self.output_size, seq_len))
        
        # Forward pass through sequence
        for t in range(seq_len):
            # Hidden state: h_t = tanh(Wxh @ x_t + Whh @ h_{t-1} + bh)
            H[:, t+1:t+2] = self.tanh_fast(
                self.Wxh @ X[:, t:t+1] + 
                self.Whh @ H[:, t:t+1] + 
                self.bh
            )
            
            # Output: y_t = Why @ h_t + by
            Y[:, t:t+1] = self.Why @ H[:, t+1:t+2] + self.by
            
            # Probabilities: p_t = softmax(y_t)
            P[:, t:t+1] = self.softmax(Y[:, t:t+1])
        
        return H, Y, P
    
    def backward(self, inputs, targets, H, Y, P):
        """
        Vectorized backward pass using BPTT
        """
        seq_len = len(inputs)
        
        # Convert to tensors
        X = np.column_stack(inputs)
        T = np.column_stack(targets)
        
        # Initialize gradients
        dWxh = np.zeros_like(self.Wxh)
        dWhh = np.zeros_like(self.Whh)
        dWhy = np.zeros_like(self.Why)
        dbh = np.zeros_like(self.bh)
        dby = np.zeros_like(self.by)
        
        # Output layer gradients
        dY = P - T  # (output_size, seq_len)
        
        # Gradient for Why and by
        dWhy = dY @ H[:, 1:].T
        dby = np.sum(dY, axis=1, keepdims=True)
        
        # Backpropagate through time
        dH = np.zeros((self.hidden_size, seq_len + 1))
        
        for t in range(seq_len - 1, -1, -1):
            # Gradient from output layer
            dH[:, t+1:t+2] += self.Why.T @ dY[:, t:t+1]
            
            # Gradient through tanh
            dH_raw = dH[:, t+1:t+2] * (1 - H[:, t+1:t+2] ** 2)
            
            # Accumulate gradients
            dWxh += dH_raw @ X[:, t:t+1].T
            dWhh += dH_raw @ H[:, t:t+1].T
            dbh += dH_raw
            
            # Propagate to previous time step
            dH[:, t:t+1] = self.Whh.T @ dH_raw
        
        # Clip gradients
        grads = [dWxh, dWhh, dWhy, dbh, dby]
        self.clip_gradients(grads)
        
        return grads
    
    def clip_gradients(self, grads):
        """Gradient clipping using L2 norm"""
        total_norm = np.sqrt(sum(np.sum(g**2) for g in grads))
        
        if total_norm > self.max_grad_norm:
            clip_coef = self.max_grad_norm / total_norm
            for g in grads:
                g *= clip_coef
    
    def update_weights_adam(self, grads):
        """Adam optimizer update"""
        dWxh, dWhh, dWhy, dbh, dby = grads
        self.t += 1
        
        # Update biased first moment estimates
        self.mWxh = self.beta1 * self.mWxh + (1 - self.beta1) * dWxh
        self.mWhh = self.beta1 * self.mWhh + (1 - self.beta1) * dWhh
        self.mWhy = self.beta1 * self.mWhy + (1 - self.beta1) * dWhy
        self.mbh = self.beta1 * self.mbh + (1 - self.beta1) * dbh
        self.mby = self.beta1 * self.mby + (1 - self.beta1) * dby
        
        # Update biased second moment estimates
        self.vWxh = self.beta2 * self.vWxh + (1 - self.beta2) * (dWxh ** 2)
        self.vWhh = self.beta2 * self.vWhh + (1 - self.beta2) * (dWhh ** 2)
        self.vWhy = self.beta2 * self.vWhy + (1 - self.beta2) * (dWhy ** 2)
        self.vbh = self.beta2 * self.vbh + (1 - self.beta2) * (dbh ** 2)
        self.vby = self.beta2 * self.vby + (1 - self.beta2) * (dby ** 2)
        
        # Bias correction
        m_hat_Wxh = self.mWxh / (1 - self.beta1 ** self.t)
        m_hat_Whh = self.mWhh / (1 - self.beta1 ** self.t)
        m_hat_Why = self.mWhy / (1 - self.beta1 ** self.t)
        m_hat_bh = self.mbh / (1 - self.beta1 ** self.t)
        m_hat_by = self.mby / (1 - self.beta1 ** self.t)
        
        v_hat_Wxh = self.vWxh / (1 - self.beta2 ** self.t)
        v_hat_Whh = self.vWhh / (1 - self.beta2 ** self.t)
        v_hat_Why = self.vWhy / (1 - self.beta2 ** self.t)
        v_hat_bh = self.vbh / (1 - self.beta2 ** self.t)
        v_hat_by = self.vby / (1 - self.beta2 ** self.t)
        
        # Update weights
        self.Wxh -= self.learning_rate * m_hat_Wxh / (np.sqrt(v_hat_Wxh) + self.eps)
        self.Whh -= self.learning_rate * m_hat_Whh / (np.sqrt(v_hat_Whh) + self.eps)
        self.Why -= self.learning_rate * m_hat_Why / (np.sqrt(v_hat_Why) + self.eps)
        self.bh -= self.learning_rate * m_hat_bh / (np.sqrt(v_hat_bh) + self.eps)
        self.by -= self.learning_rate * m_hat_by / (np.sqrt(v_hat_by) + self.eps)
    
    def train_step(self, inputs, targets):
        """Single training step"""
        # Forward pass
        H, Y, P = self.forward(inputs)
        
        # Calculate loss (cross-entropy)
        targets_tensor = np.column_stack(targets)
        loss = -np.sum(targets_tensor * np.log(P + 1e-8)) / len(inputs)
        
        # Backward pass
        grads = self.backward(inputs, targets, H, Y, P)
        
        # Update weights
        self.update_weights_adam(grads)
        
        return loss, H[:, -1]

class TensorDataLoader:
    def __init__(self, shakespeare_folder="Shakespeare"):
        self.shakespeare_folder = shakespeare_folder
        self.ensure_folder_exists()
        
    def ensure_folder_exists(self):
        """Create Shakespeare folder if it doesn't exist"""
        if not os.path.exists(self.shakespeare_folder):
            os.makedirs(self.shakespeare_folder)
            print(f"Created '{self.shakespeare_folder}' folder.")
            print("Please add Shakespeare text files (.txt) to this folder.")
            print("You can download them from: https://www.gutenberg.org/ebooks/author/65")
    
    def get_available_files(self):
        """Get list of available Shakespeare text files"""
        pattern = os.path.join(self.shakespeare_folder, "*.txt")
        files = glob.glob(pattern)
        return [os.path.basename(f) for f in files]
    
    def load_texts(self, num_files=1):
        """Load specified number of Shakespeare text files"""
        available_files = self.get_available_files()
        
        if not available_files:
            print(f"No .txt files found in '{self.shakespeare_folder}' folder!")
            print("Please add Shakespeare text files to continue.")
            return ""
        
        print(f"Available files: {available_files}")
        
        # Select files to load
        files_to_load = available_files[:min(num_files, len(available_files))]
        print(f"Loading {len(files_to_load)} file(s): {files_to_load}")
        
        combined_text = ""
        for filename in files_to_load:
            filepath = os.path.join(self.shakespeare_folder, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                    combined_text += text + "\n\n"
                    print(f"Loaded {filename}: {len(text)} characters")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        
        return combined_text

def preprocess_text(text):
    """Clean and preprocess text"""
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?;:-\'"()\n')
    
    # Filter characters
    cleaned_text = ''.join(c for c in text if c in allowed_chars)
    
    # Process lines
    lines = cleaned_text.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip() and not line.isupper()]
    
    return ' '.join(cleaned_lines)

def create_char_dataset(text):
    """Create character mappings"""
    chars = sorted(set(text))
    char_to_idx = {ch: i for i, ch in enumerate(chars)}
    idx_to_char = {i: ch for i, ch in enumerate(chars)}
    
    return chars, char_to_idx, idx_to_char

def char_to_onehot(char, char_to_idx, vocab_size):
    """Convert character to one-hot vector"""
    vector = np.zeros(vocab_size)
    idx = char_to_idx.get(char)
    if idx is not None:
        vector[idx] = 1.0
    return vector

def create_training_batches(text, char_to_idx, vocab_size, sequence_length, batch_size=32):
    """Create batched training data for faster processing"""
    sequences = []
    targets = []
    
    step_size = sequence_length // 2
    text_len = len(text)
    
    print("Creating training batches...")
    
    for i in range(0, text_len - sequence_length, step_size):
        seq_chars = text[i:i+sequence_length]
        target_chars = text[i+1:i+sequence_length+1]
        
        seq_vectors = [char_to_onehot(c, char_to_idx, vocab_size) for c in seq_chars]
        target_vectors = [char_to_onehot(c, char_to_idx, vocab_size) for c in target_chars]
        
        sequences.append(seq_vectors)
        targets.append(target_vectors)
        
        if len(sequences) % 1000 == 0:
            print(f"Created {len(sequences)} sequences...")
    
    # Create batches
    batches = []
    for i in range(0, len(sequences), batch_size):
        batch_seq = sequences[i:i+batch_size]
        batch_target = targets[i:i+batch_size]
        batches.append((batch_seq, batch_target))
    
    return batches

def generate_text(rnn, seed_text, char_to_idx, idx_to_char, length=200, temperature=0.8):
    """Generate text using the trained model"""
    vocab_size = len(char_to_idx)
    h = np.zeros((rnn.hidden_size, 1))
    result = seed_text
    
    # Process seed text
    for char in seed_text:
        if char in char_to_idx:
            x = char_to_onehot(char, char_to_idx, vocab_size)
            # Single character forward pass
            h = np.tanh(rnn.Wxh @ x.reshape(-1, 1) + rnn.Whh @ h + rnn.bh)
    
    # Generate new characters
    for _ in range(length):
        if result:
            last_char = result[-1]
            if last_char in char_to_idx:
                x = char_to_onehot(last_char, char_to_idx, vocab_size)
                
                # Forward pass
                h = np.tanh(rnn.Wxh @ x.reshape(-1, 1) + rnn.Whh @ h + rnn.bh)
                y = rnn.Why @ h + rnn.by
                p = rnn.softmax(y)
                
                # Temperature sampling
                if temperature > 0:
                    p = p.flatten()
                    p = np.exp(np.log(p + 1e-8) / temperature)
                    p = p / np.sum(p)
                    
                    # Sample from distribution
                    next_idx = np.random.choice(len(p), p=p)
                else:
                    next_idx = np.argmax(p)
                
                next_char = idx_to_char[next_idx]
                result += next_char
            else:
                break
        else:
            break
    
    return result

def main():
    print("Tensor-Based Shakespeare RNN with NumPy")
    print("=" * 50)
    
    # Parse command line arguments
    num_files = 1
    if len(sys.argv) > 1:
        try:
            num_files = int(sys.argv[1])
        except ValueError:
            print("Usage: python tensor_shakespeare_rnn.py [num_files]")
            print("num_files: number of text files to load (default: 1)")
            return
    
    # Load data
    loader = TensorDataLoader()
    text = loader.load_texts(num_files)
    
    if not text:
        return
    
    # Preprocess
    print("Preprocessing text...")
    text = preprocess_text(text)
    print(f"Preprocessed text length: {len(text)} characters")
    
    # Create character mappings
    chars, char_to_idx, idx_to_char = create_char_dataset(text)
    vocab_size = len(chars)
    print(f"Vocabulary size: {vocab_size}")
    
    # Model parameters
    hidden_size = 128
    sequence_length = 50
    learning_rate = 0.001  # Lower for Adam optimizer
    batch_size = 1  # Process one sequence at a time for RNN
    
    # Create model
    rnn = TensorShakespeareRNN(
        input_size=vocab_size,
        hidden_size=hidden_size,
        output_size=vocab_size,
        learning_rate=learning_rate
    )
    
    # Create training data
    batches = create_training_batches(text, char_to_idx, vocab_size, sequence_length, batch_size)
    print(f"Created {len(batches)} training batches")
    
    # Training loop
    print("\nStarting tensor-based training...")
    print("=" * 50)
    
    epochs = 50
    print_every = 5
    
    start_time = time.time()
    
    for epoch in range(epochs):
        total_loss = 0.0
        epoch_start = time.time()
        
        # Shuffle batches
        random.shuffle(batches)
        
        for batch_idx, (sequences, targets) in enumerate(batches):
            for seq, target in zip(sequences, targets):
                loss, _ = rnn.train_step(seq, target)
                total_loss += loss
        
        epoch_time = time.time() - epoch_start
        
        if epoch % print_every == 0:
            avg_loss = total_loss / len(batches)
            print(f"Epoch {epoch:3d}, Loss: {avg_loss:.4f}, Time: {epoch_time:.2f}s")
            
            # Generate sample
            seed_phrases = ["To be", "What is", "The king", "My lord"]
            seed = random.choice(seed_phrases)
            sample = generate_text(rnn, seed, char_to_idx, idx_to_char, 100, temperature=0.7)
            print(f"Sample: '{sample[:80]}...'")
            print()
    
    total_time = time.time() - start_time
    print(f"Training completed in {total_time:.2f} seconds!")
    print("=" * 50)
    
    # Final generation
    print("\nFinal text generation:")
    test_seeds = ["To be or not to be", "What light", "Romeo", "Shall I compare"]
    
    for seed in test_seeds:
        print(f"\nSeed: '{seed}'")
        result = generate_text(rnn, seed, char_to_idx, idx_to_char, 150, temperature=0.6)
        print(f"Generated: {result}")
        print("-" * 80)

if __name__ == "__main__":
    main()