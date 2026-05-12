import math
import random
import os
import sys
import glob

class ShakespeareRNN:
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
        
    def random_matrix(self, rows, cols, scale=0.01):
        """Initialize matrix with small random values"""
        return [[random.gauss(0, scale) for _ in range(cols)] for _ in range(rows)]
    
    def tanh(self, x):
        """Activation function for hidden layer"""
        return math.tanh(max(-20, min(20, x)))  # clip to prevent overflow
    
    def tanh_derivative(self, x):
        """Derivative of tanh for backpropagation"""
        return 1 - x * x
    
    def softmax(self, x):
        """Softmax activation for output layer"""
        max_x = max(x)
        exp_x = [math.exp(val - max_x) for val in x]
        sum_exp = sum(exp_x)
        return [val / (sum_exp + 1e-8) for val in exp_x]
    
    def clip_gradients(self, grads):
        """Clip gradients to prevent exploding gradients"""
        total_norm = 0
        for grad_matrix in grads:
            if isinstance(grad_matrix[0], list):  # 2D matrix
                for row in grad_matrix:
                    for val in row:
                        total_norm += val * val
            else:  # 1D vector
                for val in grad_matrix:
                    total_norm += val * val
        
        total_norm = math.sqrt(total_norm)
        
        if total_norm > self.max_grad_norm:
            scale = self.max_grad_norm / total_norm
            for grad_matrix in grads:
                if isinstance(grad_matrix[0], list):  # 2D matrix
                    for i, row in enumerate(grad_matrix):
                        for j in range(len(row)):
                            grad_matrix[i][j] *= scale
                else:  # 1D vector
                    for i in range(len(grad_matrix)):
                        grad_matrix[i] *= scale
    
    def forward(self, inputs, h_prev):
        """Forward pass through the RNN"""
        outputs = []
        hidden_states = [h_prev[:]]  # copy previous hidden state
        
        for x in inputs:
            # Calculate hidden state: h = tanh(Wxh @ x + Whh @ h_prev + bh)
            h = []
            for i in range(self.hidden_size):
                activation = self.bh[i]
                # Input to hidden
                for j in range(self.input_size):
                    activation += self.Wxh[i][j] * x[j]
                # Hidden to hidden
                for j in range(self.hidden_size):
                    activation += self.Whh[i][j] * h_prev[j]
                h.append(self.tanh(activation))
            
            # Calculate output: y = softmax(Why @ h + by)
            y = []
            for i in range(self.output_size):
                activation = self.by[i]
                for j in range(self.hidden_size):
                    activation += self.Why[i][j] * h[j]
                y.append(activation)
            
            y = self.softmax(y)
            outputs.append(y)
            hidden_states.append(h[:])  # copy hidden state
            h_prev = h
            
        return outputs, hidden_states
    
    def backward(self, inputs, targets, outputs, hidden_states):
        """Backward pass with gradient clipping"""
        # Initialize gradients
        dWxh = [[0.0] * self.input_size for _ in range(self.hidden_size)]
        dWhh = [[0.0] * self.hidden_size for _ in range(self.hidden_size)]
        dWhy = [[0.0] * self.hidden_size for _ in range(self.output_size)]
        dbh = [0.0] * self.hidden_size
        dby = [0.0] * self.output_size
        
        dh_next = [0.0] * self.hidden_size
        
        # Backpropagate through time
        for t in reversed(range(len(inputs))):
            # Output layer gradients
            dy = outputs[t][:]
            for i in range(len(targets[t])):
                dy[i] -= targets[t][i]
            
            # Update output weights and biases
            for i in range(self.output_size):
                dby[i] += dy[i]
                for j in range(self.hidden_size):
                    dWhy[i][j] += dy[i] * hidden_states[t+1][j]
            
            # Hidden layer gradients
            dh = [0.0] * self.hidden_size
            for i in range(self.hidden_size):
                # Gradient from output layer
                for j in range(self.output_size):
                    dh[i] += self.Why[j][i] * dy[j]
                # Gradient from next time step
                dh[i] += dh_next[i]
                # Apply tanh derivative
                dh[i] *= self.tanh_derivative(hidden_states[t+1][i])
            
            # Update hidden weights and biases
            for i in range(self.hidden_size):
                dbh[i] += dh[i]
                # Input to hidden weights
                for j in range(self.input_size):
                    dWxh[i][j] += dh[i] * inputs[t][j]
                # Hidden to hidden weights
                for j in range(self.hidden_size):
                    dWhh[i][j] += dh[i] * hidden_states[t][j]
            
            dh_next = dh
        
        # Clip gradients
        self.clip_gradients([dWxh, dWhh, dWhy, dbh, dby])
        
        # Update weights using gradients
        for i in range(self.hidden_size):
            for j in range(self.input_size):
                self.Wxh[i][j] -= self.learning_rate * dWxh[i][j]
            for j in range(self.hidden_size):
                self.Whh[i][j] -= self.learning_rate * dWhh[i][j]
            self.bh[i] -= self.learning_rate * dbh[i]
        
        for i in range(self.output_size):
            for j in range(self.hidden_size):
                self.Why[i][j] -= self.learning_rate * dWhy[i][j]
            self.by[i] -= self.learning_rate * dby[i]
    
    def train_step(self, inputs, targets, h_prev):
        """Single training step"""
        outputs, hidden_states = self.forward(inputs, h_prev)
        self.backward(inputs, targets, outputs, hidden_states)
        
        # Calculate loss (cross-entropy)
        loss = 0.0
        for t in range(len(targets)):
            for i in range(len(targets[t])):
                if targets[t][i] > 0:
                    loss -= math.log(max(outputs[t][i], 1e-8))
        
        return loss, hidden_states[-1]

class ShakespeareDataLoader:
    def __init__(self, shakespeare_folder="shakespeare"):
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
    """Clean and preprocess the text"""
    # Keep only printable ASCII characters and common punctuation
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?;:-\'"()\n')
    cleaned_text = ''.join(c for c in text if c in allowed_chars)
    
    # Remove excessive whitespace
    lines = cleaned_text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.isupper():  # Skip all-caps headers
            cleaned_lines.append(line)
    
    return ' '.join(cleaned_lines)

def create_char_dataset(text):
    """Convert text to character-level dataset"""
    chars = sorted(list(set(text)))
    char_to_idx = {ch: i for i, ch in enumerate(chars)}
    idx_to_char = {i: ch for i, ch in enumerate(chars)}
    
    return chars, char_to_idx, idx_to_char

def char_to_onehot(char, char_to_idx, vocab_size):
    """Convert character to one-hot vector"""
    vector = [0.0] * vocab_size
    if char in char_to_idx:
        vector[char_to_idx[char]] = 1.0
    return vector

def generate_text(rnn, seed_text, char_to_idx, idx_to_char, length=200, temperature=0.8):
    """Generate text using trained RNN with temperature sampling"""
    vocab_size = len(char_to_idx)
    h = [0.0] * rnn.hidden_size
    result = seed_text
    
    # Process seed text
    for char in seed_text:
        if char in char_to_idx:
            x = char_to_onehot(char, char_to_idx, vocab_size)
            outputs, hidden_states = rnn.forward([x], h)
            h = hidden_states[-1]
    
    # Generate new characters
    for _ in range(length):
        if result:
            last_char = result[-1]
            if last_char in char_to_idx:
                x = char_to_onehot(last_char, char_to_idx, vocab_size)
                outputs, hidden_states = rnn.forward([x], h)
                h = hidden_states[-1]
                
                # Temperature sampling
                probs = outputs[0]
                if temperature > 0:
                    # Apply temperature
                    probs = [p ** (1.0/temperature) for p in probs]
                    prob_sum = sum(probs)
                    probs = [p/prob_sum for p in probs]
                    
                    # Sample from distribution
                    r = random.random()
                    cumsum = 0
                    for i, p in enumerate(probs):
                        cumsum += p
                        if r < cumsum:
                            next_idx = i
                            break
                    else:
                        next_idx = len(probs) - 1
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
            print("Usage: python shakespeare_rnn.py [num_files]")
            print("num_files: number of text files to load (default: 1)")
            return
    
    print(f"Shakespeare RNN - Loading {num_files} text file(s)")
    print("=" * 50)
    
    # Load Shakespeare texts
    loader = ShakespeareDataLoader()
    text = loader.load_texts(num_files)
    
    if not text:
        return
    
    # Preprocess text
    text = preprocess_text(text)
    print(f"\nPreprocessed text length: {len(text)} characters")
    
    if len(text) < 1000:
        print("Warning: Text is quite short. Consider adding more files for better results.")
    
    # Prepare data
    chars, char_to_idx, idx_to_char = create_char_dataset(text)
    vocab_size = len(chars)
    
    print(f"Vocabulary size: {vocab_size}")
    print(f"Characters: {''.join(chars[:50])}{'...' if len(chars) > 50 else ''}")
    
    # Create RNN with better hyperparameters for Shakespeare
    hidden_size = 128
    sequence_length = 50
    learning_rate = 0.005
    
    rnn = ShakespeareRNN(
        input_size=vocab_size, 
        hidden_size=hidden_size, 
        output_size=vocab_size, 
        learning_rate=learning_rate
    )
    
    # Prepare training sequences
    sequences = []
    targets = []
    
    step_size = sequence_length // 2  # overlap sequences for more training data
    for i in range(0, len(text) - sequence_length, step_size):
        seq = text[i:i+sequence_length]
        target = text[i+1:i+sequence_length+1]
        
        seq_vectors = [char_to_onehot(c, char_to_idx, vocab_size) for c in seq]
        target_vectors = [char_to_onehot(c, char_to_idx, vocab_size) for c in target]
        
        sequences.append(seq_vectors)
        targets.append(target_vectors)
    
    print(f"Created {len(sequences)} training sequences")
    
    # Training loop
    print("\nStarting training...")
    print("=" * 50)
    
    epochs = 200
    print_every = 20
    
    for epoch in range(epochs):
        total_loss = 0.0
        h = [0.0] * hidden_size
        
        # Shuffle sequences for better training
        combined = list(zip(sequences, targets))
        random.shuffle(combined)
        sequences_shuffled, targets_shuffled = zip(*combined)
        
        for i, (seq, target) in enumerate(zip(sequences_shuffled, targets_shuffled)):
            loss, h = rnn.train_step(seq, target, h)
            total_loss += loss
            
            # Reset hidden state occasionally to prevent vanishing gradients
            if i % 100 == 0:
                h = [0.0] * hidden_size
        
        if epoch % print_every == 0:
            avg_loss = total_loss / len(sequences)
            print(f"Epoch {epoch:3d}, Loss: {avg_loss:.4f}")
            
            # Generate sample text
            seed_phrases = ["To be", "What is", "The king", "My lord"]
            seed = random.choice(seed_phrases)
            sample = generate_text(rnn, seed, char_to_idx, idx_to_char, 100, temperature=0.7)
            print(f"Sample: '{sample[:80]}...'")
            print()
    
    print("Training completed!")
    print("=" * 50)
    
    # Final text generation
    print("\nFinal text generation:")
    test_seeds = ["To be or not to be", "What light", "Romeo", "Shall I compare"]
    
    for seed in test_seeds:
        print(f"\nSeed: '{seed}'")
        result = generate_text(rnn, seed, char_to_idx, idx_to_char, 150, temperature=0.6)
        print(f"Generated: {result}")
        print("-" * 80)

if __name__ == "__main__":
    main()