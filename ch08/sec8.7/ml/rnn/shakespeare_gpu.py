import random
import os
import sys
import glob
import time

# Try to import CuPy for GPU acceleration, fallback to NumPy
try:
    import cupy as cp
    import numpy as np
    GPU_AVAILABLE = True
    print("GPU acceleration available with CuPy!")
except ImportError:
    import numpy as np
    cp = np  # Use NumPy as fallback
    GPU_AVAILABLE = False
    print("CuPy not found. Install with: pip install cupy-cuda11x")
    print("Falling back to CPU with NumPy")

class GPUShakespeareRNN:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.001, use_gpu=True):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        self.use_gpu = use_gpu and GPU_AVAILABLE
        
        # Choose array library based on GPU availability
        self.xp = cp if self.use_gpu else np
        
        if self.use_gpu:
            print(f"Using GPU: {cp.cuda.Device().name}")
            print(f"GPU Memory: {cp.cuda.Device().mem_info[1] / 1e9:.1f} GB total")
        else:
            print("Using CPU computation")
        
        # Initialize weights with Xavier/He initialization
        self.Wxh = self.xp.random.randn(hidden_size, input_size).astype(self.xp.float32) * self.xp.sqrt(2.0 / input_size)
        self.Whh = self.xp.random.randn(hidden_size, hidden_size).astype(self.xp.float32) * self.xp.sqrt(2.0 / hidden_size)
        self.Why = self.xp.random.randn(output_size, hidden_size).astype(self.xp.float32) * self.xp.sqrt(2.0 / hidden_size)
        
        # Biases
        self.bh = self.xp.zeros((hidden_size, 1), dtype=self.xp.float32)
        self.by = self.xp.zeros((output_size, 1), dtype=self.xp.float32)
        
        # Gradient clipping
        self.max_grad_norm = 5.0
        
        # Adam optimizer parameters
        self.beta1, self.beta2 = 0.9, 0.999
        self.eps = 1e-8
        self.t = 0
        
        # Adam momentum terms (on GPU if available)
        self.mWxh = self.xp.zeros_like(self.Wxh)
        self.mWhh = self.xp.zeros_like(self.Whh)
        self.mWhy = self.xp.zeros_like(self.Why)
        self.mbh = self.xp.zeros_like(self.bh)
        self.mby = self.xp.zeros_like(self.by)
        
        self.vWxh = self.xp.zeros_like(self.Wxh)
        self.vWhh = self.xp.zeros_like(self.Whh)
        self.vWhy = self.xp.zeros_like(self.Why)
        self.vbh = self.xp.zeros_like(self.bh)
        self.vby = self.xp.zeros_like(self.by)
        
        # Pre-allocate workspace arrays for better GPU memory management
        self._workspace_h = self.xp.zeros((hidden_size, 100), dtype=self.xp.float32)  # For sequences up to 100
        self._workspace_y = self.xp.zeros((output_size, 100), dtype=self.xp.float32)
        self._workspace_p = self.xp.zeros((output_size, 100), dtype=self.xp.float32)
    
    def to_gpu_array(self, data):
        """Convert input data to GPU array if GPU is available"""
        if isinstance(data, list):
            if isinstance(data[0], list):
                # 2D list - convert to 2D array
                arr = self.xp.array(data, dtype=self.xp.float32)
            else:
                # 1D list - convert to column vector
                arr = self.xp.array(data, dtype=self.xp.float32).reshape(-1, 1)
        else:
            arr = self.xp.asarray(data, dtype=self.xp.float32)
        return arr
    
    def softmax_stable(self, x):
        """GPU-optimized numerically stable softmax"""
        # Subtract max for numerical stability
        x_max = self.xp.max(x, axis=0, keepdims=True)
        exp_x = self.xp.exp(x - x_max)
        return exp_x / self.xp.sum(exp_x, axis=0, keepdims=True)
    
    def forward_gpu(self, inputs):
        """
        GPU-accelerated forward pass with memory optimization
        """
        seq_len = len(inputs)
        
        # Convert inputs to GPU tensor efficiently
        X = self.xp.column_stack([self.to_gpu_array(inp).flatten() for inp in inputs])
        
        # Use pre-allocated workspace or create new arrays
        if seq_len <= self._workspace_h.shape[1]:
            H = self._workspace_h[:, :seq_len+1]
            Y = self._workspace_y[:, :seq_len]
            P = self._workspace_p[:, :seq_len]
            H.fill(0)  # Clear previous values
        else:
            H = self.xp.zeros((self.hidden_size, seq_len + 1), dtype=self.xp.float32)
            Y = self.xp.zeros((self.output_size, seq_len), dtype=self.xp.float32)
            P = self.xp.zeros((self.output_size, seq_len), dtype=self.xp.float32)
        
        # GPU-optimized forward pass
        for t in range(seq_len):
            # Vectorized operations on GPU
            wxh_term = self.Wxh @ X[:, t:t+1]
            whh_term = self.Whh @ H[:, t:t+1]
            
            # Hidden state with fused operations
            H[:, t+1:t+2] = self.xp.tanh(wxh_term + whh_term + self.bh)
            
            # Output computation
            Y[:, t:t+1] = self.Why @ H[:, t+1:t+2] + self.by
            P[:, t:t+1] = self.softmax_stable(Y[:, t:t+1])
        
        return H[:, :seq_len+1].copy(), Y.copy(), P.copy()
    
    def backward_gpu(self, inputs, targets, H, Y, P):
        """
        GPU-accelerated backward pass with optimized memory access
        """
        seq_len = len(inputs)
        
        # Convert to GPU tensors
        X = self.xp.column_stack([self.to_gpu_array(inp).flatten() for inp in inputs])
        T = self.xp.column_stack([self.to_gpu_array(tgt).flatten() for tgt in targets])
        
        # Initialize gradients on GPU
        dWxh = self.xp.zeros_like(self.Wxh)
        dWhh = self.xp.zeros_like(self.Whh)
        dWhy = self.xp.zeros_like(self.Why)
        dbh = self.xp.zeros_like(self.bh)
        dby = self.xp.zeros_like(self.by)
        
        # Output gradients (vectorized)
        dY = P - T
        
        # Efficient gradient computation using GPU BLAS
        dWhy = dY @ H[:, 1:].T
        dby = self.xp.sum(dY, axis=1, keepdims=True)
        
        # Backpropagate through time (GPU accelerated)
        dH = self.xp.zeros_like(H)
        
        # Vectorized BPTT
        for t in range(seq_len - 1, -1, -1):
            # Gradient from output layer
            dH[:, t+1:t+2] += self.Why.T @ dY[:, t:t+1]
            
            # Tanh derivative (element-wise GPU operation)
            dH_raw = dH[:, t+1:t+2] * (1 - H[:, t+1:t+2] ** 2)
            
            # Accumulate gradients using GPU matrix operations
            dWxh += dH_raw @ X[:, t:t+1].T
            dWhh += dH_raw @ H[:, t:t+1].T
            dbh += dH_raw
            
            # Propagate to previous timestep
            dH[:, t:t+1] = self.Whh.T @ dH_raw
        
        grads = [dWxh, dWhh, dWhy, dbh, dby]
        self.clip_gradients_gpu(grads)
        
        return grads
    
    def clip_gradients_gpu(self, grads):
        """GPU-accelerated gradient clipping"""
        # Compute total norm using GPU operations
        grad_norms_sq = [self.xp.sum(g**2) for g in grads]
        total_norm = self.xp.sqrt(sum(grad_norms_sq))
        
        if total_norm > self.max_grad_norm:
            clip_coef = self.max_grad_norm / total_norm
            # Apply clipping on GPU
            for g in grads:
                g *= clip_coef
    
    def update_weights_adam_gpu(self, grads):
        """GPU-accelerated Adam optimizer"""
        dWxh, dWhh, dWhy, dbh, dby = grads
        self.t += 1
        
        # All operations performed on GPU
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
        bias_correction1 = 1 - self.beta1 ** self.t
        bias_correction2 = 1 - self.beta2 ** self.t
        
        # Update weights (all GPU operations)
        step_size = self.learning_rate / bias_correction1
        
        self.Wxh -= step_size * self.mWxh / (self.xp.sqrt(self.vWxh / bias_correction2) + self.eps)
        self.Whh -= step_size * self.mWhh / (self.xp.sqrt(self.vWhh / bias_correction2) + self.eps)
        self.Why -= step_size * self.mWhy / (self.xp.sqrt(self.vWhy / bias_correction2) + self.eps)
        self.bh -= step_size * self.mbh / (self.xp.sqrt(self.vbh / bias_correction2) + self.eps)
        self.by -= step_size * self.mby / (self.xp.sqrt(self.vby / bias_correction2) + self.eps)
    
    def train_step_gpu(self, inputs, targets):
        """GPU-accelerated training step"""
        # Forward pass
        H, Y, P = self.forward_gpu(inputs)
        
        # Calculate loss
        targets_tensor = self.xp.column_stack([self.to_gpu_array(tgt).flatten() for tgt in targets])
        loss = -self.xp.sum(targets_tensor * self.xp.log(P + 1e-8)) / len(inputs)
        
        # Backward pass
        grads = self.backward_gpu(inputs, targets, H, Y, P)
        
        # Update weights
        self.update_weights_adam_gpu(grads)
        
        # Return loss as Python float and last hidden state
        if self.use_gpu:
            return float(loss.get()), H[:, -1].get()  # Transfer to CPU
        else:
            return float(loss), H[:, -1]
    
    def get_memory_usage(self):
        """Get current GPU memory usage"""
        if self.use_gpu:
            mempool = cp.get_default_memory_pool()
            used_bytes = mempool.used_bytes()
            total_bytes = cp.cuda.Device().mem_info[1]
            return used_bytes / 1e6, total_bytes / 1e6  # Convert to MB
        return 0, 0

class GPUDataLoader:
    def __init__(self, shakespeare_folder="Shakespeare"):
        self.shakespeare_folder = shakespeare_folder
        self.ensure_folder_exists()
        
    def ensure_folder_exists(self):
        if not os.path.exists(self.shakespeare_folder):
            os.makedirs(self.shakespeare_folder)
            print(f"Created '{self.shakespeare_folder}' folder.")
            print("Please add Shakespeare text files (.txt) to this folder.")
            print("Download from: https://www.gutenberg.org/ebooks/author/65")
    
    def get_available_files(self):
        pattern = os.path.join(self.shakespeare_folder, "*.txt")
        files = glob.glob(pattern)
        return [os.path.basename(f) for f in files]
    
    def load_texts(self, num_files=1):
        available_files = self.get_available_files()
        
        if not available_files:
            print(f"No .txt files found in '{self.shakespeare_folder}' folder!")
            return ""
        
        files_to_load = available_files[:min(num_files, len(available_files))]
        print(f"Loading {len(files_to_load)} file(s): {files_to_load}")
        
        combined_text = ""
        for filename in files_to_load:
            filepath = os.path.join(self.shakespeare_folder, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                    combined_text += text + "\n\n"
                    print(f"Loaded {filename}: {len(text):,} characters")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        
        return combined_text

def preprocess_text(text):
    """Optimized text preprocessing"""
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?;:-\'"()\n')
    cleaned_text = ''.join(c for c in text if c in allowed_chars)
    lines = cleaned_text.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip() and not line.isupper()]
    return ' '.join(cleaned_lines)

def create_char_dataset(text):
    chars = sorted(set(text))
    char_to_idx = {ch: i for i, ch in enumerate(chars)}
    idx_to_char = {i: ch for i, ch in enumerate(chars)}
    return chars, char_to_idx, idx_to_char

def char_to_onehot(char, char_to_idx, vocab_size):
    vector = [0.0] * vocab_size
    idx = char_to_idx.get(char)
    if idx is not None:
        vector[idx] = 1.0
    return vector

def create_training_data(text, char_to_idx, vocab_size, sequence_length):
    sequences, targets = [], []
    step_size = sequence_length // 2
    text_len = len(text)
    
    print("Creating training sequences...")
    
    for i in range(0, text_len - sequence_length, step_size):
        seq_chars = text[i:i+sequence_length]
        target_chars = text[i+1:i+sequence_length+1]
        
        seq_vectors = [char_to_onehot(c, char_to_idx, vocab_size) for c in seq_chars]
        target_vectors = [char_to_onehot(c, char_to_idx, vocab_size) for c in target_chars]
        
        sequences.append(seq_vectors)
        targets.append(target_vectors)
        
        if len(sequences) % 1000 == 0:
            print(f"Created {len(sequences):,} sequences...")
    
    return sequences, targets

def generate_text_gpu(rnn, seed_text, char_to_idx, idx_to_char, length=200, temperature=0.8):
    """GPU-accelerated text generation"""
    vocab_size = len(char_to_idx)
    h = rnn.xp.zeros((rnn.hidden_size, 1), dtype=rnn.xp.float32)
    result = seed_text
    
    # Process seed text
    for char in seed_text:
        if char in char_to_idx:
            x = rnn.to_gpu_array(char_to_onehot(char, char_to_idx, vocab_size))
            h = rnn.xp.tanh(rnn.Wxh @ x + rnn.Whh @ h + rnn.bh)
    
    # Generate new characters
    for _ in range(length):
        if result:
            last_char = result[-1]
            if last_char in char_to_idx:
                x = rnn.to_gpu_array(char_to_onehot(last_char, char_to_idx, vocab_size))
                
                # Forward pass on GPU
                h = rnn.xp.tanh(rnn.Wxh @ x + rnn.Whh @ h + rnn.bh)
                y = rnn.Why @ h + rnn.by
                p = rnn.softmax_stable(y)
                
                # Temperature sampling
                if temperature > 0:
                    p = p.flatten()
                    if rnn.use_gpu:
                        p_cpu = p.get()  # Transfer to CPU for sampling
                    else:
                        p_cpu = p
                    
                    p_cpu = np.exp(np.log(p_cpu + 1e-8) / temperature)
                    p_cpu = p_cpu / np.sum(p_cpu)
                    next_idx = np.random.choice(len(p_cpu), p=p_cpu)
                else:
                    if rnn.use_gpu:
                        next_idx = int(rnn.xp.argmax(p).get())
                    else:
                        next_idx = int(rnn.xp.argmax(p))
                
                next_char = idx_to_char[next_idx]
                result += next_char
            else:
                break
        else:
            break
    
    return result

def main():
    global GPU_AVAILABLE  # Declare as global to modify it
    
    print("GPU-Accelerated Shakespeare RNN")
    print("=" * 60)
    
    # Check GPU availability
    if GPU_AVAILABLE:
        try:
            cp.cuda.Device(0).use()
            print(f"GPU Device: {cp.cuda.Device().name}")
            mem_info = cp.cuda.Device().mem_info
            print(f"GPU Memory: {mem_info[1]/1e9:.1f} GB total, {mem_info[0]/1e9:.1f} GB free")
        except Exception as e:
            print(f"GPU initialization failed: {e}")
            GPU_AVAILABLE = False
    
    # Parse arguments
    num_files = 1
    if len(sys.argv) > 1:
        try:
            num_files = int(sys.argv[1])
        except ValueError:
            print("Usage: python gpu_shakespeare_rnn.py [num_files]")
            return
    
    # Load and preprocess data
    loader = GPUDataLoader()
    text = loader.load_texts(num_files)
    if not text:
        return
    
    print("Preprocessing text...")
    text = preprocess_text(text)
    print(f"Text length: {len(text):,} characters")
    
    # Create character mappings
    chars, char_to_idx, idx_to_char = create_char_dataset(text)
    vocab_size = len(chars)
    print(f"Vocabulary size: {vocab_size}")
    
    # Model parameters
    hidden_size = 256  # Larger for GPU
    sequence_length = 75  # Longer sequences for GPU
    learning_rate = 0.001
    
    # Create GPU model
    rnn = GPUShakespeareRNN(
        input_size=vocab_size,
        hidden_size=hidden_size,
        output_size=vocab_size,
        learning_rate=learning_rate,
        use_gpu=GPU_AVAILABLE
    )
    
    # Create training data
    sequences, targets = create_training_data(text, char_to_idx, vocab_size, sequence_length)
    print(f"Training sequences: {len(sequences):,}")
    
    # Training loop
    print("\nStarting GPU training...")
    print("=" * 60)
    
    epochs = 50
    print_every = 5
    start_time = time.time()
    
    for epoch in range(epochs):
        epoch_start = time.time()
        total_loss = 0.0
        
        # Shuffle training data
        combined = list(zip(sequences, targets))
        random.shuffle(combined)
        sequences_shuffled, targets_shuffled = zip(*combined)
        
        # Training step
        for i, (seq, target) in enumerate(zip(sequences_shuffled, targets_shuffled)):
            loss, _ = rnn.train_step_gpu(seq, target)
            total_loss += loss
            
            # Memory management for GPU
            if rnn.use_gpu and i % 100 == 0:
                cp.get_default_memory_pool().free_all_blocks()
        
        epoch_time = time.time() - epoch_start
        
        if epoch % print_every == 0:
            avg_loss = total_loss / len(sequences)
            
            # GPU memory usage
            if rnn.use_gpu:
                used_mem, total_mem = rnn.get_memory_usage()
                mem_str = f", GPU: {used_mem:.0f}/{total_mem:.0f} MB"
            else:
                mem_str = ""
            
            print(f"Epoch {epoch:3d}, Loss: {avg_loss:.4f}, Time: {epoch_time:.2f}s{mem_str}")
            
            # Generate sample
            seed = random.choice(["To be", "What is", "Romeo", "My lord"])
            sample = generate_text_gpu(rnn, seed, char_to_idx, idx_to_char, 100, 0.7)
            print(f"Sample: '{sample[:80]}...'")
            print()
    
    total_time = time.time() - start_time
    print(f"Training completed in {total_time:.2f} seconds!")
    
    # Performance summary
    sequences_per_sec = len(sequences) * epochs / total_time
    print(f"Performance: {sequences_per_sec:.0f} sequences/second")
    print("=" * 60)
    
    # Final generation
    print("\nFinal Shakespeare generation:")
    test_seeds = ["To be or not to be", "What light through yonder", "Romeo", "Fair is foul"]
    
    for seed in test_seeds:
        print(f"\nSeed: '{seed}'")
        result = generate_text_gpu(rnn, seed, char_to_idx, idx_to_char, 200, 0.6)
        print(f"Generated: {result}")
        print("-" * 80)
    
    # Clean up GPU memory
    if GPU_AVAILABLE:
        cp.get_default_memory_pool().free_all_blocks()
        print("GPU memory cleaned up")

if __name__ == "__main__":
    main()

