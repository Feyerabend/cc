import numpy as np
import random
import os
import sys
import glob
import time

class TensorShakespeareGRU:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.01):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        
        # Initialize GRU weights with Xavier/He initialization
        # Reset gate weights
        self.Wxr = np.random.randn(hidden_size, input_size) * np.sqrt(2.0 / input_size)
        self.Whr = np.random.randn(hidden_size, hidden_size) * np.sqrt(2.0 / hidden_size)
        self.br = np.zeros((hidden_size, 1))
        
        # Update gate weights
        self.Wxz = np.random.randn(hidden_size, input_size) * np.sqrt(2.0 / input_size)
        self.Whz = np.random.randn(hidden_size, hidden_size) * np.sqrt(2.0 / hidden_size)
        self.bz = np.zeros((hidden_size, 1))
        
        # New gate weights (candidate hidden state)
        self.Wxh = np.random.randn(hidden_size, input_size) * np.sqrt(2.0 / input_size)
        self.Whh = np.random.randn(hidden_size, hidden_size) * np.sqrt(2.0 / hidden_size)
        self.bh = np.zeros((hidden_size, 1))
        
        # Output layer weights
        self.Why = np.random.randn(output_size, hidden_size) * np.sqrt(2.0 / hidden_size)
        self.by = np.zeros((output_size, 1))
        
        # For gradient clipping
        self.max_grad_norm = 5.0
        
        # Adam optimizer parameters
        self.beta1, self.beta2 = 0.9, 0.999
        self.eps = 1e-8
        self.t = 0  # Time step for Adam
        
        # Initialize Adam momentum terms for all weights
        self.init_adam_params()
    
    def init_adam_params(self):
        """Initialize Adam optimizer momentum terms"""
        # First moment
        self.mWxr = np.zeros_like(self.Wxr)
        self.mWhr = np.zeros_like(self.Whr)
        self.mbr = np.zeros_like(self.br)
        self.mWxz = np.zeros_like(self.Wxz)
        self.mWhz = np.zeros_like(self.Whz)
        self.mbz = np.zeros_like(self.bz)
        self.mWxh = np.zeros_like(self.Wxh)
        self.mWhh = np.zeros_like(self.Whh)
        self.mbh = np.zeros_like(self.bh)
        self.mWhy = np.zeros_like(self.Why)
        self.mby = np.zeros_like(self.by)
        
        # Second moment
        self.vWxr = np.zeros_like(self.Wxr)
        self.vWhr = np.zeros_like(self.Whr)
        self.vbr = np.zeros_like(self.br)
        self.vWxz = np.zeros_like(self.Wxz)
        self.vWhz = np.zeros_like(self.Whz)
        self.vbz = np.zeros_like(self.bz)
        self.vWxh = np.zeros_like(self.Wxh)
        self.vWhh = np.zeros_like(self.Whh)
        self.vbh = np.zeros_like(self.bh)
        self.vWhy = np.zeros_like(self.Why)
        self.vby = np.zeros_like(self.by)
    
    def sigmoid(self, x):
        """Numerically stable sigmoid"""
        return np.where(x >= 0, 
                       1 / (1 + np.exp(-np.clip(x, -500, 500))),
                       np.exp(np.clip(x, -500, 500)) / (1 + np.exp(np.clip(x, -500, 500))))
    
    def tanh_fast(self, x):
        """Optimized tanh using NumPy"""
        return np.tanh(np.clip(x, -500, 500))
    
    def softmax(self, x):
        """Numerically stable softmax"""
        exp_x = np.exp(x - np.max(x, axis=0, keepdims=True))
        return exp_x / np.sum(exp_x, axis=0, keepdims=True)
    
    def forward(self, inputs):
        """
        GRU forward pass
        inputs: list of one-hot vectors (seq_len, vocab_size)
        """
        seq_len = len(inputs)
        
        # Convert inputs to tensor (vocab_size, seq_len)
        X = np.column_stack(inputs)
        
        # Initialize hidden states
        H = np.zeros((self.hidden_size, seq_len + 1))
        
        # Gates and intermediate values
        R = np.zeros((self.hidden_size, seq_len))  # Reset gate
        Z = np.zeros((self.hidden_size, seq_len))  # Update gate
        H_tilde = np.zeros((self.hidden_size, seq_len))  # Candidate hidden state
        
        Y = np.zeros((self.output_size, seq_len))
        P = np.zeros((self.output_size, seq_len))
        
        # Forward pass through sequence
        for t in range(seq_len):
            # Reset gate
            r_gate = self.sigmoid(
                self.Wxr @ X[:, t:t+1] + 
                self.Whr @ H[:, t:t+1] + 
                self.br
            )
            R[:, t:t+1] = r_gate
            
            # Update gate
            z_gate = self.sigmoid(
                self.Wxz @ X[:, t:t+1] + 
                self.Whz @ H[:, t:t+1] + 
                self.bz
            )
            Z[:, t:t+1] = z_gate
            
            # Candidate hidden state
            h_tilde = self.tanh_fast(
                self.Wxh @ X[:, t:t+1] + 
                self.Whh @ (R[:, t:t+1] * H[:, t:t+1]) + 
                self.bh
            )
            H_tilde[:, t:t+1] = h_tilde
            
            # New hidden state
            H[:, t+1:t+2] = (1 - Z[:, t:t+1]) * H[:, t:t+1] + Z[:, t:t+1] * H_tilde[:, t:t+1]
            
            # Output
            Y[:, t:t+1] = self.Why @ H[:, t+1:t+2] + self.by
            P[:, t:t+1] = self.softmax(Y[:, t:t+1])
        
        return H, R, Z, H_tilde, Y, P
    
    def backward(self, inputs, targets, H, R, Z, H_tilde, Y, P):
        """
        GRU backward pass using BPTT
        """
        seq_len = len(inputs)
        
        # Convert to tensors
        X = np.column_stack(inputs)
        T = np.column_stack(targets)
        
        # Initialize gradients
        dWxr = np.zeros_like(self.Wxr)
        dWhr = np.zeros_like(self.Whr)
        dbr = np.zeros_like(self.br)
        dWxz = np.zeros_like(self.Wxz)
        dWhz = np.zeros_like(self.Whz)
        dbz = np.zeros_like(self.bz)
        dWxh = np.zeros_like(self.Wxh)
        dWhh = np.zeros_like(self.Whh)
        dbh = np.zeros_like(self.bh)
        dWhy = np.zeros_like(self.Why)
        dby = np.zeros_like(self.by)
        
        # Output layer gradients
        dY = P - T  # (output_size, seq_len)
        
        # Gradient for Why and by
        dWhy = dY @ H[:, 1:].T
        dby = np.sum(dY, axis=1, keepdims=True)
        
        # Initialize gradient for hidden state
        dH = np.zeros((self.hidden_size, seq_len + 1))
        
        # Backpropagate through time
        for t in range(seq_len - 1, -1, -1):
            # Gradient from output layer
            dH[:, t+1:t+2] += self.Why.T @ dY[:, t:t+1]
            
            # GRU gate gradients
            # Gradient w.r.t candidate hidden state
            dH_tilde = dH[:, t+1:t+2] * Z[:, t:t+1].reshape(-1, 1)
            dH_tilde_input = dH_tilde * (1 - H_tilde[:, t:t+1].reshape(-1, 1) ** 2)
            
            # Gradients for candidate hidden state weights
            dWxh += dH_tilde_input @ X[:, t:t+1].T
            dWhh += dH_tilde_input @ (R[:, t:t+1].reshape(-1, 1) * H[:, t:t+1]).T
            dbh += dH_tilde_input
            
            # Gradient w.r.t reset gate
            dR = dH_tilde_input * (self.Whh @ H[:, t:t+1])
            dR_input = dR * R[:, t:t+1].reshape(-1, 1) * (1 - R[:, t:t+1].reshape(-1, 1))
            
            # Gradients for reset gate weights
            dWxr += dR_input @ X[:, t:t+1].T
            dWhr += dR_input @ H[:, t:t+1].T
            dbr += dR_input
            
            # Gradient w.r.t update gate
            dZ = dH[:, t+1:t+2] * (H_tilde[:, t:t+1].reshape(-1, 1) - H[:, t:t+1])
            dZ_input = dZ * Z[:, t:t+1].reshape(-1, 1) * (1 - Z[:, t:t+1].reshape(-1, 1))
            
            # Gradients for update gate weights
            dWxz += dZ_input @ X[:, t:t+1].T
            dWhz += dZ_input @ H[:, t:t+1].T
            dbz += dZ_input
            
            # Propagate gradients to previous time step
            dH[:, t:t+1] = (
                dH[:, t+1:t+2] * (1 - Z[:, t:t+1].reshape(-1, 1)) +
                self.Whr.T @ dR_input +
                self.Whz.T @ dZ_input +
                self.Whh.T @ dH_tilde_input * R[:, t:t+1].reshape(-1, 1)
            )
        
        # Collect all gradients
        grads = [dWxr, dWhr, dbr, dWxz, dWhz, dbz, dWxh, dWhh, dbh, dWhy, dby]
        
        # Clip gradients
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
        """Adam optimizer update for all GRU weights"""
        (dWxr, dWhr, dbr, dWxz, dWhz, dbz, dWxh, dWhh, dbh, dWhy, dby) = grads
        
        self.t += 1
        
        # Update first moment estimates
        self.mWxr = self.beta1 * self.mWxr + (1 - self.beta1) * dWxr
        self.mWhr = self.beta1 * self.mWhr + (1 - self.beta1) * dWhr
        self.mbr = self.beta1 * self.mbr + (1 - self.beta1) * dbr
        self.mWxz = self.beta1 * self.mWxz + (1 - self.beta1) * dWxz
        self.mWhz = self.beta1 * self.mWhz + (1 - self.beta1) * dWhz
        self.mbz = self.beta1 * self.mbz + (1 - self.beta1) * dbz
        self.mWxh = self.beta1 * self.mWxh + (1 - self.beta1) * dWxh
        self.mWhh = self.beta1 * self.mWhh + (1 - self.beta1) * dWhh
        self.mbh = self.beta1 * self.mbh + (1 - self.beta1) * dbh
        self.mWhy = self.beta1 * self.mWhy + (1 - self.beta1) * dWhy
        self.mby = self.beta1 * self.mby + (1 - self.beta1) * dby
        
        # Update second moment estimates
        self.vWxr = self.beta2 * self.vWxr + (1 - self.beta2) * (dWxr ** 2)
        self.vWhr = self.beta2 * self.vWhr + (1 - self.beta2) * (dWhr ** 2)
        self.vbr = self.beta2 * self.vbr + (1 - self.beta2) * (dbr ** 2)
        self.vWxz = self.beta2 * self.vWxz + (1 - self.beta2) * (dWxz ** 2)
        self.vWhz = self.beta2 * self.vWhz + (1 - self.beta2) * (dWhz ** 2)
        self.vbz = self.beta2 * self.vbz + (1 - self.beta2) * (dbz ** 2)
        self.vWxh = self.beta2 * self.vWxh + (1 - self.beta2) * (dWxh ** 2)
        self.vWhh = self.beta2 * self.vWhh + (1 - self.beta2) * (dWhh ** 2)
        self.vbh = self.beta2 * self.vbh + (1 - self.beta2) * (dbh ** 2)
        self.vWhy = self.beta2 * self.vWhy + (1 - self.beta2) * (dWhy ** 2)
        self.vby = self.beta2 * self.vby + (1 - self.beta2) * (dby ** 2)
        
        # Bias correction
        bias_correction1 = 1 - self.beta1 ** self.t
        bias_correction2 = 1 - self.beta2 ** self.t
        
        # Update weights
        self.Wxr -= self.learning_rate * (self.mWxr / bias_correction1) / (np.sqrt(self.vWxr / bias_correction2) + self.eps)
        self.Whr -= self.learning_rate * (self.mWhr / bias_correction1) / (np.sqrt(self.vWhr / bias_correction2) + self.eps)
        self.br -= self.learning_rate * (self.mbr / bias_correction1) / (np.sqrt(self.vbr / bias_correction2) + self.eps)
        self.Wxz -= self.learning_rate * (self.mWxz / bias_correction1) / (np.sqrt(self.vWxz / bias_correction2) + self.eps)
        self.Whz -= self.learning_rate * (self.mWhz / bias_correction1) / (np.sqrt(self.vWhz / bias_correction2) + self.eps)
        self.bz -= self.learning_rate * (self.mbz / bias_correction1) / (np.sqrt(self.vbz / bias_correction2) + self.eps)
        self.Wxh -= self.learning_rate * (self.mWxh / bias_correction1) / (np.sqrt(self.vWxh / bias_correction2) + self.eps)
        self.Whh -= self.learning_rate * (self.mWhh / bias_correction1) / (np.sqrt(self.vWhh / bias_correction2) + self.eps)
        self.bh -= self.learning_rate * (self.mbh / bias_correction1) / (np.sqrt(self.vbh / bias_correction2) + self.eps)
        self.Why -= self.learning_rate * (self.mWhy / bias_correction1) / (np.sqrt(self.vWhy / bias_correction2) + self.eps)
        self.by -= self.learning_rate * (self.mby / bias_correction1) / (np.sqrt(self.vby / bias_correction2) + self.eps)
    
    def train_step(self, inputs, targets):
        """Single training step"""
        # Forward pass
        H, R, Z, H_tilde, Y, P = self.forward(inputs)
        
        # Calculate loss (cross-entropy)
        targets_tensor = np.column_stack(targets)
        loss = -np.sum(targets_tensor * np.log(P + 1e-8)) / len(inputs)
        
        # Backward pass
        grads = self.backward(inputs, targets, H, R, Z, H_tilde, Y, P)
        
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

def generate_text(gru, seed_text, char_to_idx, idx_to_char, length=200, temperature=0.8):
    """Generate text using the trained GRU model"""
    vocab_size = len(char_to_idx)
    h = np.zeros((gru.hidden_size, 1))
    result = seed_text
    
    # Process seed text
    for char in seed_text:
        if char in char_to_idx:
            x = char_to_onehot(char, char_to_idx, vocab_size)
            
            # GRU forward pass for single character
            # Reset gate
            r_gate = gru.sigmoid(gru.Wxr @ x.reshape(-1, 1) + gru.Whr @ h + gru.br)
            # Update gate
            z_gate = gru.sigmoid(gru.Wxz @ x.reshape(-1, 1) + gru.Whz @ h + gru.bz)
            # Candidate hidden state
            h_tilde = gru.tanh_fast(gru.Wxh @ x.reshape(-1, 1) + gru.Whh @ (r_gate * h) + gru.bh)
            
            # Update hidden state
            h = (1 - z_gate) * h + z_gate * h_tilde
    
    # Generate new characters
    for _ in range(length):
        if result:
            last_char = result[-1]
            if last_char in char_to_idx:
                x = char_to_onehot(last_char, char_to_idx, vocab_size)
                
                # GRU forward pass
                r_gate = gru.sigmoid(gru.Wxr @ x.reshape(-1, 1) + gru.Whr @ h + gru.br)
                z_gate = gru.sigmoid(gru.Wxz @ x.reshape(-1, 1) + gru.Whz @ h + gru.bz)
                h_tilde = gru.tanh_fast(gru.Wxh @ x.reshape(-1, 1) + gru.Whh @ (r_gate * h) + gru.bh)
                
                h = (1 - z_gate) * h + z_gate * h_tilde
                
                # Output
                y = gru.Why @ h + gru.by
                p = gru.softmax(y)
                
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
    print("Tensor-Based Shakespeare GRU with NumPy")
    print("=" * 50)
    
    # Parse command line arguments
    num_files = 1
    if len(sys.argv) > 1:
        try:
            num_files = int(sys.argv[1])
        except ValueError:
            print("Usage: python shakespeare_gru.py [num_files]")
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
    
    if len(text) < 1000:
        print("Text too short for meaningful training!")
        return
    
    # Create character mappings
    chars, char_to_idx, idx_to_char = create_char_dataset(text)
    vocab_size = len(chars)
    print(f"Vocabulary size: {vocab_size}")
    print(f"Characters: {''.join(chars[:20])}{'...' if len(chars) > 20 else ''}")
    
    # Training parameters
    sequence_length = 25
    hidden_size = 128
    batch_size = 32
    epochs = 10
    learning_rate = 0.001
    
    print(f"\nTraining parameters:")
    print(f"Sequence length: {sequence_length}")
    print(f"Hidden size: {hidden_size}")
    print(f"Batch size: {batch_size}")
    print(f"Learning rate: {learning_rate}")
    print(f"Epochs: {epochs}")
    
    # Create training batches
    batches = create_training_batches(text, char_to_idx, vocab_size, sequence_length, batch_size)
    print(f"Created {len(batches)} training batches")
    
    # Initialize model
    gru = TensorShakespeareGRU(vocab_size, hidden_size, vocab_size, learning_rate)
    print("GRU model initialized")
    
    # Training loop
    print("\nStarting training...")
    print("=" * 50)
    
    best_loss = float('inf')
    
    for epoch in range(epochs):
        epoch_loss = 0.0
        total_sequences = 0
        epoch_start = time.time()
        
        # Shuffle batches
        random.shuffle(batches)
        
        for batch_idx, (batch_sequences, batch_targets) in enumerate(batches):
            batch_loss = 0.0
            batch_size_actual = len(batch_sequences)
            
            # Train on each sequence in the batch
            for seq_inputs, seq_targets in zip(batch_sequences, batch_targets):
                loss, _ = gru.train_step(seq_inputs, seq_targets)  # This is already averaged per sequence
                batch_loss += loss  # Sum of averaged losses
                epoch_loss += loss  # Sum of averaged losses
                total_sequences += 1

            # Average loss for this batch
            batch_loss_avg = batch_loss / batch_size_actual  # Average of the averaged losses

            # At end of epoch:
            epoch_loss_avg = epoch_loss / total_sequences  # Average of all sequence losses
            
            # Print progress every 50 batches
            if (batch_idx + 1) % 50 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Batch {batch_idx+1}/{len(batches)}, "
                      f"Batch Loss: {batch_loss_avg:.4f}")
        
        # Average loss for epoch (total loss / total sequences)
        epoch_loss_avg = epoch_loss / total_sequences
        epoch_time = time.time() - epoch_start
        
        print(f"Epoch {epoch+1}/{epochs} completed in {epoch_time:.2f}s")
        print(f"Average Loss: {epoch_loss_avg:.4f} (over {total_sequences} sequences)") # !!!!!?????
        
        # Save best model (in practice, you'd save to disk)
        if epoch_loss_avg < best_loss:
            best_loss = epoch_loss_avg
            print(f"New best loss: {best_loss:.4f}")
        
        # Generate sample text every few epochs
        if (epoch + 1) % 2 == 0 or epoch == 0:
            print("\nGenerating sample text:")
            print("-" * 30)
            
            # Try different seed texts
            seed_texts = ["To be", "What is", "The king", "My lord"]
            for seed in seed_texts:
                if all(c in char_to_idx for c in seed):
                    generated = generate_text(gru, seed, char_to_idx, idx_to_char, 
                                            length=100, temperature=0.8)
                    print(f"Seed '{seed}': {generated}")
                    break
            
            print("-" * 30)
        
        print()

    print("Training completed!")
    print(f"Final best loss: {best_loss:.4f}")
    
    # Interactive text generation
    print("\n" + "=" * 50)
    print("Interactive Text Generation")
    print("Enter a seed text (or 'quit' to exit):")
    
    while True:
        try:
            seed = input("\nSeed text: ").strip()
            
            if seed.lower() == 'quit':
                break
            
            if not seed:
                seed = "The "
            
            # Check if all characters in seed are in vocabulary
            if not all(c in char_to_idx for c in seed):
                print("Warning: Some characters in seed text are not in vocabulary.")
                # Filter to valid characters
                seed = ''.join(c for c in seed if c in char_to_idx)
                if not seed:
                    seed = "The "
                print(f"Using filtered seed: '{seed}'")
            
            # Generate with different temperatures
            temperatures = [0.5, 0.8, 1.0]
            
            for temp in temperatures:
                generated = generate_text(gru, seed, char_to_idx, idx_to_char, 
                                        length=200, temperature=temp)
                print(f"\nTemperature {temp}:")
                print(generated)
                print("-" * 40)
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Goodbye!")

if __name__ == "__main__":
    main()