import math
import random
import os
import sys
import glob

class FastShakespeareRNN:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.01):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        
        # Initialize weights randomly (smaller values for stability)
        self.Wxh = self.random_matrix(hidden_size, input_size, scale=0.01)
        self.Whh = self.random_matrix(hidden_size, hidden_size, scale=0.01)
        self.Why = self.random_matrix(output_size, hidden_size, scale=0.01)
        
        # Biases
        self.bh = [0.0] * hidden_size
        self.by = [0.0] * output_size
        
        # For gradient clipping
        self.max_grad_norm = 5.0
        
        # Pre-allocate arrays to avoid repeated memory allocation
        self._temp_hidden = [0.0] * hidden_size
        self._temp_output = [0.0] * output_size
        self._temp_probs = [0.0] * output_size
        
    def random_matrix(self, rows, cols, scale=0.01):
        """Initialize matrix with small random values"""
        return [[random.gauss(0, scale) for _ in range(cols)] for _ in range(rows)]
    
    def tanh_fast(self, x):
        """Faster tanh approximation"""
        if x > 20: return 1.0
        if x < -20: return -1.0
        # Fast tanh approximation: tanh(x) ≈ x / (1 + |x|) for |x| < 1
        # For larger values, use the exact computation
        if abs(x) < 1:
            return x / (1 + abs(x)) if x >= 0 else x / (1 - x)
        return math.tanh(x)
    
    def tanh_derivative(self, x):
        """Derivative of tanh for backpropagation"""
        return 1 - x * x
    
    def softmax_fast(self, x, result):
        """In-place softmax to avoid memory allocation"""
        max_x = max(x)
        sum_exp = 0.0
        
        # First pass: compute exp and sum
        for i in range(len(x)):
            result[i] = math.exp(x[i] - max_x)
            sum_exp += result[i]
        
        # Second pass: normalize
        inv_sum = 1.0 / (sum_exp + 1e-8)
        for i in range(len(result)):
            result[i] *= inv_sum
    
    def matrix_vector_multiply(self, matrix, vector, result):
        """Optimized matrix-vector multiplication with result reuse"""
        for i in range(len(matrix)):
            result[i] = 0.0
            for j in range(len(vector)):
                result[i] += matrix[i][j] * vector[j]
    
    def forward_optimized(self, inputs, h_prev):
        """Optimized forward pass with minimal memory allocation"""
        outputs = []
        h_current = h_prev[:]
        hidden_states = [h_prev[:]]
        
        for x in inputs:
            # Reuse temporary arrays
            h_new = self._temp_hidden
            y_raw = self._temp_output
            
            # Calculate hidden state efficiently
            # h = tanh(Wxh @ x + Whh @ h_prev + bh)
            for i in range(self.hidden_size):
                activation = self.bh[i]
                # Vectorized operations replaced with optimized loops
                wxh_row = self.Wxh[i]
                whh_row = self.Whh[i]
                
                for j in range(self.input_size):
                    activation += wxh_row[j] * x[j]
                for j in range(self.hidden_size):
                    activation += whh_row[j] * h_current[j]
                    
                h_new[i] = self.tanh_fast(activation)
            
            # Calculate output: y = softmax(Why @ h + by)
            for i in range(self.output_size):
                activation = self.by[i]
                why_row = self.Why[i]
                for j in range(self.hidden_size):
                    activation += why_row[j] * h_new[j]
                y_raw[i] = activation
            
            # Apply softmax in-place
            y_probs = self._temp_probs[:]
            self.softmax_fast(y_raw, y_probs)
            
            outputs.append(y_probs[:])  # Make a copy for output
            h_current[:] = h_new[:]     # Copy hidden state
            hidden_states.append(h_current[:])
            
        return outputs, hidden_states
    
    def clip_gradients(self, grads):
        """Optimized gradient clipping"""
        total_norm_sq = 0.0
        
        # Calculate total norm squared more efficiently
        for grad_matrix in grads:
            if isinstance(grad_matrix[0], list):  # 2D matrix
                for row in grad_matrix:
                    for val in row:
                        total_norm_sq += val * val
            else:  # 1D vector
                for val in grad_matrix:
                    total_norm_sq += val * val
        
        total_norm = math.sqrt(total_norm_sq)
        
        if total_norm > self.max_grad_norm:
            scale = self.max_grad_norm / total_norm
            # Apply scaling
            for grad_matrix in grads:
                if isinstance(grad_matrix[0], list):  # 2D matrix
                    for row in grad_matrix:
                        for j in range(len(row)):
                            row[j] *= scale
                else:  # 1D vector
                    for i in range(len(grad_matrix)):
                        grad_matrix[i] *= scale
    
    def backward_optimized(self, inputs, targets, outputs, hidden_states):
        """Optimized backward pass"""
        seq_len = len(inputs)
        
        # Pre-allocate gradient matrices
        dWxh = [[0.0] * self.input_size for _ in range(self.hidden_size)]
        dWhh = [[0.0] * self.hidden_size for _ in range(self.hidden_size)]
        dWhy = [[0.0] * self.hidden_size for _ in range(self.output_size)]
        dbh = [0.0] * self.hidden_size
        dby = [0.0] * self.output_size
        
        dh_next = [0.0] * self.hidden_size
        
        # Backpropagate through time
        for t in range(seq_len - 1, -1, -1):
            # Output layer gradients (reuse memory)
            dy = outputs[t][:]
            target_t = targets[t]
            
            for i in range(len(target_t)):
                dy[i] -= target_t[i]
            
            # Update output weights and biases
            h_t = hidden_states[t+1]
            for i in range(self.output_size):
                dby[i] += dy[i]
                why_row = dWhy[i]
                dy_i = dy[i]
                for j in range(self.hidden_size):
                    why_row[j] += dy_i * h_t[j]
            
            # Hidden layer gradients
            dh = [0.0] * self.hidden_size
            
            # More efficient gradient computation
            for i in range(self.hidden_size):
                # Gradient from output layer
                grad_sum = 0.0
                for j in range(self.output_size):
                    grad_sum += self.Why[j][i] * dy[j]
                
                # Add gradient from next time step
                dh[i] = (grad_sum + dh_next[i]) * self.tanh_derivative(h_t[i])
            
            # Update hidden weights and biases
            input_t = inputs[t]
            h_prev = hidden_states[t]
            
            for i in range(self.hidden_size):
                dh_i = dh[i]
                dbh[i] += dh_i
                
                # Input to hidden weights
                dWxh_row = dWxh[i]
                for j in range(self.input_size):
                    dWxh_row[j] += dh_i * input_t[j]
                
                # Hidden to hidden weights  
                dWhh_row = dWhh[i]
                for j in range(self.hidden_size):
                    dWhh_row[j] += dh_i * h_prev[j]
            
            dh_next[:] = dh[:]
        
        # Clip gradients
        self.clip_gradients([dWxh, dWhh, dWhy, dbh, dby])
        
        # Apply gradients with optimized loops
        lr = self.learning_rate
        
        for i in range(self.hidden_size):
            # Update Wxh and Whh
            wxh_row = self.Wxh[i]
            whh_row = self.Whh[i]
            dWxh_row = dWxh[i]
            dWhh_row = dWhh[i]
            
            for j in range(self.input_size):
                wxh_row[j] -= lr * dWxh_row[j]
            for j in range(self.hidden_size):
                whh_row[j] -= lr * dWhh_row[j]
            
            self.bh[i] -= lr * dbh[i]
        
        for i in range(self.output_size):
            why_row = self.Why[i]
            dWhy_row = dWhy[i]
            for j in range(self.hidden_size):
                why_row[j] -= lr * dWhy_row[j]
            self.by[i] -= lr * dby[i]
    
    def train_step_fast(self, inputs, targets, h_prev):
        """Optimized training step"""
        outputs, hidden_states = self.forward_optimized(inputs, h_prev)
        self.backward_optimized(inputs, targets, outputs, hidden_states)
        
        # Calculate loss more efficiently
        loss = 0.0
        for t in range(len(targets)):
            target_t = targets[t]
            output_t = outputs[t]
            for i in range(len(target_t)):
                if target_t[i] > 0:
                    loss -= math.log(max(output_t[i], 1e-8))
        
        return loss, hidden_states[-1]

class OptimizedShakespeareDataLoader:
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

def preprocess_text_fast(text):
    """Optimized text preprocessing"""
    # Pre-compile allowed characters set
    allowed_chars = frozenset('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?;:-\'"()\n')
    
    # Filter characters more efficiently
    cleaned_chars = [c for c in text if c in allowed_chars]
    cleaned_text = ''.join(cleaned_chars)
    
    # Process lines more efficiently
    lines = cleaned_text.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip() and not line.isupper()]
    
    return ' '.join(cleaned_lines)

def create_char_dataset_fast(text):
    """Optimized character dataset creation"""
    # Use set for faster character collection
    char_set = set(text)
    chars = sorted(char_set)
    
    # Create mappings more efficiently
    char_to_idx = {ch: i for i, ch in enumerate(chars)}
    idx_to_char = chars  # Direct list access is faster than dict for idx->char
    
    return chars, char_to_idx, idx_to_char

def char_to_onehot_fast(char, char_to_idx, vocab_size):
    """Optimized one-hot encoding"""
    vector = [0.0] * vocab_size
    idx = char_to_idx.get(char)
    if idx is not None:
        vector[idx] = 1.0
    return vector

def create_training_data_fast(text, char_to_idx, vocab_size, sequence_length):
    """Pre-compute all training sequences for faster training"""
    sequences = []
    targets = []
    
    step_size = sequence_length // 2
    text_len = len(text)
    
    print("Pre-computing training sequences...")
    
    for i in range(0, text_len - sequence_length, step_size):
        seq_chars = text[i:i+sequence_length]
        target_chars = text[i+1:i+sequence_length+1]
        
        # Convert to one-hot more efficiently
        seq_vectors = []
        target_vectors = []
        
        for c in seq_chars:
            seq_vectors.append(char_to_onehot_fast(c, char_to_idx, vocab_size))
        
        for c in target_chars:
            target_vectors.append(char_to_onehot_fast(c, char_to_idx, vocab_size))
        
        sequences.append(seq_vectors)
        targets.append(target_vectors)
        
        if len(sequences) % 1000 == 0:
            print(f"Created {len(sequences)} sequences...")
    
    return sequences, targets

def generate_text_fast(rnn, seed_text, char_to_idx, idx_to_char, length=200, temperature=0.8):
    """Optimized text generation"""
    vocab_size = len(char_to_idx)
    h = [0.0] * rnn.hidden_size
    result = seed_text
    
    # Process seed text
    for char in seed_text:
        if char in char_to_idx:
            x = char_to_onehot_fast(char, char_to_idx, vocab_size)
            outputs, hidden_states = rnn.forward_optimized([x], h)
            h = hidden_states[-1]
    
    # Generate new characters
    for _ in range(length):
        if result:
            last_char = result[-1]
            if last_char in char_to_idx:
                x = char_to_onehot_fast(last_char, char_to_idx, vocab_size)
                outputs, hidden_states = rnn.forward_optimized([x], h)
                h = hidden_states[-1]
                
                # Temperature sampling
                probs = outputs[0]
                if temperature > 0:
                    # Apply temperature more efficiently
                    inv_temp = 1.0 / temperature
                    max_prob = max(probs)
                    
                    # Compute softmax with temperature
                    exp_sum = 0.0
                    temp_probs = []
                    for p in probs:
                        exp_val = math.exp((math.log(p + 1e-8) - math.log(max_prob + 1e-8)) * inv_temp)
                        temp_probs.append(exp_val)
                        exp_sum += exp_val
                    
                    # Normalize
                    temp_probs = [p / exp_sum for p in temp_probs]
                    
                    # Sample from distribution
                    r = random.random()
                    cumsum = 0.0
                    next_idx = len(temp_probs) - 1
                    for i, p in enumerate(temp_probs):
                        cumsum += p
                        if r < cumsum:
                            next_idx = i
                            break
                else:
                    # Greedy sampling
                    next_idx = probs.index(max(probs))
                
                next_char = idx_to_char[next_idx]
                result += next_char
            else:
                break
        else:
            break
    
    return result

def main():
    # Parse command line arguments
    num_files = 1
    if len(sys.argv) > 1:
        try:
            num_files = int(sys.argv[1])
        except ValueError:
            print("Usage: python optimized_shakespeare_rnn.py [num_files]")
            print("num_files: number of text files to load (default: 1)")
            return
    
    print(f"Optimized Shakespeare RNN - Loading {num_files} text file(s)")
    print("=" * 50)
    
    # Load Shakespeare texts
    loader = OptimizedShakespeareDataLoader()
    text = loader.load_texts(num_files)
    
    if not text:
        return
    
    # Preprocess text
    print("Preprocessing text...")
    text = preprocess_text_fast(text)
    print(f"Preprocessed text length: {len(text)} characters")
    
    if len(text) < 1000:
        print("Warning: Text is quite short. Consider adding more files for better results.")
    
    # Prepare data
    print("Creating character dataset...")
    chars, char_to_idx, idx_to_char = create_char_dataset_fast(text)
    vocab_size = len(chars)
    
    print(f"Vocabulary size: {vocab_size}")
    print(f"Characters: {''.join(chars[:50])}{'...' if len(chars) > 50 else ''}")
    
    # Create RNN with optimized parameters
    hidden_size = 128
    sequence_length = 50
    learning_rate = 0.01  # Slightly higher for faster convergence
    
    rnn = FastShakespeareRNN(
        input_size=vocab_size, 
        hidden_size=hidden_size, 
        output_size=vocab_size, 
        learning_rate=learning_rate
    )
    
    # Pre-compute training data
    sequences, targets = create_training_data_fast(text, char_to_idx, vocab_size, sequence_length)
    print(f"Created {len(sequences)} training sequences")
    
    # Training loop
    print("\nStarting optimized training...")
    print("=" * 50)
    
    epochs = 100  # Reduced epochs due to faster convergence
    print_every = 10
    
    for epoch in range(epochs):
        total_loss = 0.0
        h = [0.0] * hidden_size
        
        # Shuffle sequences for better training
        combined = list(zip(sequences, targets))
        random.shuffle(combined)
        sequences_shuffled, targets_shuffled = zip(*combined)
        
        for i, (seq, target) in enumerate(zip(sequences_shuffled, targets_shuffled)):
            loss, h = rnn.train_step_fast(seq, target, h)
            total_loss += loss
            
            # Reset hidden state occasionally
            if i % 50 == 0:  # More frequent resets
                h = [0.0] * hidden_size
        
        if epoch % print_every == 0:
            avg_loss = total_loss / len(sequences)
            print(f"Epoch {epoch:3d}, Loss: {avg_loss:.4f}")
            
            # Generate sample text
            seed_phrases = ["To be", "What is", "The king", "My lord"]
            seed = random.choice(seed_phrases)
            sample = generate_text_fast(rnn, seed, char_to_idx, idx_to_char, 100, temperature=0.7)
            print(f"Sample: '{sample[:80]}...'")
            print()
    
    print("Training completed!")
    print("=" * 50)
    
    # Final text generation
    print("\nFinal text generation:")
    test_seeds = ["To be or not to be", "What light", "Romeo", "Shall I compare"]
    
    for seed in test_seeds:
        print(f"\nSeed: '{seed}'")
        result = generate_text_fast(rnn, seed, char_to_idx, idx_to_char, 150, temperature=0.6)
        print(f"Generated: {result}")
        print("-" * 80)

if __name__ == "__main__":
    main()