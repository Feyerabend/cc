import numpy as np
import random
import os
import sys
import glob
import time

class TensorShakespeareLSTM:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.01):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        
        # Initialize LSTM weights with Xavier/He initialization
        # Input gate weights
        self.Wxi = np.random.randn(hidden_size, input_size) * np.sqrt(2.0 / input_size)
        self.Whi = np.random.randn(hidden_size, hidden_size) * np.sqrt(2.0 / hidden_size)
        self.bi = np.zeros((hidden_size, 1))
        
        # Forget gate weights
        self.Wxf = np.random.randn(hidden_size, input_size) * np.sqrt(2.0 / input_size)
        self.Whf = np.random.randn(hidden_size, hidden_size) * np.sqrt(2.0 / hidden_size)
        self.bf = np.ones((hidden_size, 1))  # Initialize forget gate bias to 1
        
        # Candidate values weights
        self.Wxc = np.random.randn(hidden_size, input_size) * np.sqrt(2.0 / input_size)
        self.Whc = np.random.randn(hidden_size, hidden_size) * np.sqrt(2.0 / hidden_size)
        self.bc = np.zeros((hidden_size, 1))
        
        # Output gate weights
        self.Wxo = np.random.randn(hidden_size, input_size) * np.sqrt(2.0 / input_size)
        self.Who = np.random.randn(hidden_size, hidden_size) * np.sqrt(2.0 / hidden_size)
        self.bo = np.zeros((hidden_size, 1))
        
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
        self.mWxi = np.zeros_like(self.Wxi)
        self.mWhi = np.zeros_like(self.Whi)
        self.mbi = np.zeros_like(self.bi)
        self.mWxf = np.zeros_like(self.Wxf)
        self.mWhf = np.zeros_like(self.Whf)
        self.mbf = np.zeros_like(self.bf)
        self.mWxc = np.zeros_like(self.Wxc)
        self.mWhc = np.zeros_like(self.Whc)
        self.mbc = np.zeros_like(self.bc)
        self.mWxo = np.zeros_like(self.Wxo)
        self.mWho = np.zeros_like(self.Who)
        self.mbo = np.zeros_like(self.bo)
        self.mWhy = np.zeros_like(self.Why)
        self.mby = np.zeros_like(self.by)
        
        # Second moment
        self.vWxi = np.zeros_like(self.Wxi)
        self.vWhi = np.zeros_like(self.Whi)
        self.vbi = np.zeros_like(self.bi)
        self.vWxf = np.zeros_like(self.Wxf)
        self.vWhf = np.zeros_like(self.Whf)
        self.vbf = np.zeros_like(self.bf)
        self.vWxc = np.zeros_like(self.Wxc)
        self.vWhc = np.zeros_like(self.Whc)
        self.vbc = np.zeros_like(self.bc)
        self.vWxo = np.zeros_like(self.Wxo)
        self.vWho = np.zeros_like(self.Who)
        self.vbo = np.zeros_like(self.bo)
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
        LSTM forward pass
        inputs: list of one-hot vectors (seq_len, vocab_size)
        """
        seq_len = len(inputs)
        
        # Convert inputs to tensor (vocab_size, seq_len)
        X = np.column_stack(inputs)
        
        # Initialize states
        H = np.zeros((self.hidden_size, seq_len + 1))
        C = np.zeros((self.hidden_size, seq_len + 1))
        
        # Gates and intermediate values
        I = np.zeros((self.hidden_size, seq_len))  # Input gate
        F = np.zeros((self.hidden_size, seq_len))  # Forget gate
        G = np.zeros((self.hidden_size, seq_len))  # Candidate values
        O = np.zeros((self.hidden_size, seq_len))  # Output gate
        
        Y = np.zeros((self.output_size, seq_len))
        P = np.zeros((self.output_size, seq_len))
        
        # Forward pass through sequence
        for t in range(seq_len):
            # Input gate
            i_gate = self.sigmoid(
                self.Wxi @ X[:, t:t+1] + 
                self.Whi @ H[:, t:t+1] + 
                self.bi
            )
            I[:, t:t+1] = i_gate
            
            # Forget gate
            f_gate = self.sigmoid(
                self.Wxf @ X[:, t:t+1] + 
                self.Whf @ H[:, t:t+1] + 
                self.bf
            )
            F[:, t:t+1] = f_gate
            
            # Candidate values
            g_gate = self.tanh_fast(
                self.Wxc @ X[:, t:t+1] + 
                self.Whc @ H[:, t:t+1] + 
                self.bc
            )
            G[:, t:t+1] = g_gate
            
            # Output gate
            o_gate = self.sigmoid(
                self.Wxo @ X[:, t:t+1] + 
                self.Who @ H[:, t:t+1] + 
                self.bo
            )
            O[:, t:t+1] = o_gate
            
            # Cell state
            C[:, t+1:t+2] = F[:, t:t+1] * C[:, t:t+1] + I[:, t:t+1] * G[:, t:t+1]
            
            # Hidden state
            H[:, t+1:t+2] = O[:, t:t+1] * self.tanh_fast(C[:, t+1:t+2])
            
            # Output
            Y[:, t:t+1] = self.Why @ H[:, t+1:t+2] + self.by
            P[:, t:t+1] = self.softmax(Y[:, t:t+1])
        
        return H, C, I, F, G, O, Y, P
    
    def backward(self, inputs, targets, H, C, I, F, G, O, Y, P):
        """
        LSTM backward pass using BPTT
        """
        seq_len = len(inputs)
        
        # Convert to tensors
        X = np.column_stack(inputs)
        T = np.column_stack(targets)
        
        # Initialize gradients
        dWxi = np.zeros_like(self.Wxi)
        dWhi = np.zeros_like(self.Whi)
        dbi = np.zeros_like(self.bi)
        dWxf = np.zeros_like(self.Wxf)
        dWhf = np.zeros_like(self.Whf)
        dbf = np.zeros_like(self.bf)
        dWxc = np.zeros_like(self.Wxc)
        dWhc = np.zeros_like(self.Whc)
        dbc = np.zeros_like(self.bc)
        dWxo = np.zeros_like(self.Wxo)
        dWho = np.zeros_like(self.Who)
        dbo = np.zeros_like(self.bo)
        dWhy = np.zeros_like(self.Why)
        dby = np.zeros_like(self.by)
        
        # Output layer gradients
        dY = P - T  # (output_size, seq_len)
        
        # Gradient for Why and by
        dWhy = dY @ H[:, 1:].T
        dby = np.sum(dY, axis=1, keepdims=True)
        
        # Initialize gradients for states
        dH = np.zeros((self.hidden_size, seq_len + 1))
        dC = np.zeros((self.hidden_size, seq_len + 1))
        
        # Backpropagate through time
        for t in range(seq_len - 1, -1, -1):
            # Gradient from output layer
            dH[:, t+1:t+2] += self.Why.T @ dY[:, t:t+1]
            
            # Output gate gradients
            dO = dH[:, t+1:t+2] * self.tanh_fast(C[:, t+1:t+2])
            dO_input = dO * O[:, t:t+1].reshape(-1, 1) * (1 - O[:, t:t+1].reshape(-1, 1))
            
            dWxo += dO_input @ X[:, t:t+1].T
            dWho += dO_input @ H[:, t:t+1].T
            dbo += dO_input
            
            # Cell state gradients
            dC[:, t+1:t+2] += dH[:, t+1:t+2] * O[:, t:t+1].reshape(-1, 1) * (1 - self.tanh_fast(C[:, t+1:t+2]) ** 2)
            
            # Forget gate gradients
            dF = dC[:, t+1:t+2] * C[:, t:t+1]
            dF_input = dF * F[:, t:t+1].reshape(-1, 1) * (1 - F[:, t:t+1].reshape(-1, 1))
            
            dWxf += dF_input @ X[:, t:t+1].T
            dWhf += dF_input @ H[:, t:t+1].T
            dbf += dF_input
            
            # Input gate gradients
            dI = dC[:, t+1:t+2] * G[:, t:t+1].reshape(-1, 1)
            dI_input = dI * I[:, t:t+1].reshape(-1, 1) * (1 - I[:, t:t+1].reshape(-1, 1))
            
            dWxi += dI_input @ X[:, t:t+1].T
            dWhi += dI_input @ H[:, t:t+1].T
            dbi += dI_input
            
            # Candidate gradients
            dG = dC[:, t+1:t+2] * I[:, t:t+1].reshape(-1, 1)
            dG_input = dG * (1 - G[:, t:t+1].reshape(-1, 1) ** 2)
            
            dWxc += dG_input @ X[:, t:t+1].T
            dWhc += dG_input @ H[:, t:t+1].T
            dbc += dG_input
            
            # Propagate gradients to previous time step
            dH[:, t:t+1] = (
                self.Whi.T @ dI_input +
                self.Whf.T @ dF_input +
                self.Whc.T @ dG_input +
                self.Who.T @ dO_input
            )
            
            dC[:, t:t+1] = dC[:, t+1:t+2] * F[:, t:t+1].reshape(-1, 1)
        
        # Collect all gradients
        grads = [dWxi, dWhi, dbi, dWxf, dWhf, dbf, dWxc, dWhc, dbc, 
                dWxo, dWho, dbo, dWhy, dby]
        
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
        """Adam optimizer update for all LSTM weights"""
        (dWxi, dWhi, dbi, dWxf, dWhf, dbf, dWxc, dWhc, dbc, 
         dWxo, dWho, dbo, dWhy, dby) = grads
        
        self.t += 1
        
        # Update first moment estimates
        self.mWxi = self.beta1 * self.mWxi + (1 - self.beta1) * dWxi
        self.mWhi = self.beta1 * self.mWhi + (1 - self.beta1) * dWhi
        self.mbi = self.beta1 * self.mbi + (1 - self.beta1) * dbi
        self.mWxf = self.beta1 * self.mWxf + (1 - self.beta1) * dWxf
        self.mWhf = self.beta1 * self.mWhf + (1 - self.beta1) * dWhf
        self.mbf = self.beta1 * self.mbf + (1 - self.beta1) * dbf
        self.mWxc = self.beta1 * self.mWxc + (1 - self.beta1) * dWxc
        self.mWhc = self.beta1 * self.mWhc + (1 - self.beta1) * dWhc
        self.mbc = self.beta1 * self.mbc + (1 - self.beta1) * dbc
        self.mWxo = self.beta1 * self.mWxo + (1 - self.beta1) * dWxo
        self.mWho = self.beta1 * self.mWho + (1 - self.beta1) * dWho
        self.mbo = self.beta1 * self.mbo + (1 - self.beta1) * dbo
        self.mWhy = self.beta1 * self.mWhy + (1 - self.beta1) * dWhy
        self.mby = self.beta1 * self.mby + (1 - self.beta1) * dby
        
        # Update second moment estimates
        self.vWxi = self.beta2 * self.vWxi + (1 - self.beta2) * (dWxi ** 2)
        self.vWhi = self.beta2 * self.vWhi + (1 - self.beta2) * (dWhi ** 2)
        self.vbi = self.beta2 * self.vbi + (1 - self.beta2) * (dbi ** 2)
        self.vWxf = self.beta2 * self.vWxf + (1 - self.beta2) * (dWxf ** 2)
        self.vWhf = self.beta2 * self.vWhf + (1 - self.beta2) * (dWhf ** 2)
        self.vbf = self.beta2 * self.vbf + (1 - self.beta2) * (dbf ** 2)
        self.vWxc = self.beta2 * self.vWxc + (1 - self.beta2) * (dWxc ** 2)
        self.vWhc = self.beta2 * self.vWhc + (1 - self.beta2) * (dWhc ** 2)
        self.vbc = self.beta2 * self.vbc + (1 - self.beta2) * (dbc ** 2)
        self.vWxo = self.beta2 * self.vWxo + (1 - self.beta2) * (dWxo ** 2)
        self.vWho = self.beta2 * self.vWho + (1 - self.beta2) * (dWho ** 2)
        self.vbo = self.beta2 * self.vbo + (1 - self.beta2) * (dbo ** 2)
        self.vWhy = self.beta2 * self.vWhy + (1 - self.beta2) * (dWhy ** 2)
        self.vby = self.beta2 * self.vby + (1 - self.beta2) * (dby ** 2)
        
        # Bias correction
        bias_correction1 = 1 - self.beta1 ** self.t
        bias_correction2 = 1 - self.beta2 ** self.t
        
        # Update weights
        self.Wxi -= self.learning_rate * (self.mWxi / bias_correction1) / (np.sqrt(self.vWxi / bias_correction2) + self.eps)
        self.Whi -= self.learning_rate * (self.mWhi / bias_correction1) / (np.sqrt(self.vWhi / bias_correction2) + self.eps)
        self.bi -= self.learning_rate * (self.mbi / bias_correction1) / (np.sqrt(self.vbi / bias_correction2) + self.eps)
        self.Wxf -= self.learning_rate * (self.mWxf / bias_correction1) / (np.sqrt(self.vWxf / bias_correction2) + self.eps)
        self.Whf -= self.learning_rate * (self.mWhf / bias_correction1) / (np.sqrt(self.vWhf / bias_correction2) + self.eps)
        self.bf -= self.learning_rate * (self.mbf / bias_correction1) / (np.sqrt(self.vbf / bias_correction2) + self.eps)
        self.Wxc -= self.learning_rate * (self.mWxc / bias_correction1) / (np.sqrt(self.vWxc / bias_correction2) + self.eps)
        self.Whc -= self.learning_rate * (self.mWhc / bias_correction1) / (np.sqrt(self.vWhc / bias_correction2) + self.eps)
        self.bc -= self.learning_rate * (self.mbc / bias_correction1) / (np.sqrt(self.vbc / bias_correction2) + self.eps)
        self.Wxo -= self.learning_rate * (self.mWxo / bias_correction1) / (np.sqrt(self.vWxo / bias_correction2) + self.eps)
        self.Who -= self.learning_rate * (self.mWho / bias_correction1) / (np.sqrt(self.vWho / bias_correction2) + self.eps)
        self.bo -= self.learning_rate * (self.mbo / bias_correction1) / (np.sqrt(self.vbo / bias_correction2) + self.eps)
        self.Why -= self.learning_rate * (self.mWhy / bias_correction1) / (np.sqrt(self.vWhy / bias_correction2) + self.eps)
        self.by -= self.learning_rate * (self.mby / bias_correction1) / (np.sqrt(self.vby / bias_correction2) + self.eps)
    
    def train_step(self, inputs, targets):
        """Single training step"""
        # Forward pass
        H, C, I, F, G, O, Y, P = self.forward(inputs)
        
        # Calculate loss (cross-entropy)
        targets_tensor = np.column_stack(targets)
        loss = -np.sum(targets_tensor * np.log(P + 1e-8)) / len(inputs)
        
        # Backward pass
        grads = self.backward(inputs, targets, H, C, I, F, G, O, Y, P)
        
        # Update weights
        self.update_weights_adam(grads)
        
        return loss, H[:, -1], C[:, -1]

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

def generate_text(lstm, seed_text, char_to_idx, idx_to_char, length=200, temperature=0.8):
    """Generate text using the trained LSTM model"""
    vocab_size = len(char_to_idx)
    h = np.zeros((lstm.hidden_size, 1))
    c = np.zeros((lstm.hidden_size, 1))
    result = seed_text
    
    # Process seed text
    for char in seed_text:
        if char in char_to_idx:
            x = char_to_onehot(char, char_to_idx, vocab_size)
            
            # LSTM forward pass for single character
            # Input gate
            i_gate = lstm.sigmoid(lstm.Wxi @ x.reshape(-1, 1) + lstm.Whi @ h + lstm.bi)
            # Forget gate
            f_gate = lstm.sigmoid(lstm.Wxf @ x.reshape(-1, 1) + lstm.Whf @ h + lstm.bf)
            # Candidate values
            g_gate = lstm.tanh_fast(lstm.Wxc @ x.reshape(-1, 1) + lstm.Whc @ h + lstm.bc)
            # Output gate
            o_gate = lstm.sigmoid(lstm.Wxo @ x.reshape(-1, 1) + lstm.Who @ h + lstm.bo)
            
            # Update cell and hidden states
            c = f_gate * c + i_gate * g_gate
            h = o_gate * lstm.tanh_fast(c)
    
    # Generate new characters
    for _ in range(length):
        if result:
            last_char = result[-1]
            if last_char in char_to_idx:
                x = char_to_onehot(last_char, char_to_idx, vocab_size)
                
                # LSTM forward pass
                i_gate = lstm.sigmoid(lstm.Wxi @ x.reshape(-1, 1) + lstm.Whi @ h + lstm.bi)
                f_gate = lstm.sigmoid(lstm.Wxf @ x.reshape(-1, 1) + lstm.Whf @ h + lstm.bf)
                g_gate = lstm.tanh_fast(lstm.Wxc @ x.reshape(-1, 1) + lstm.Whc @ h + lstm.bc)
                o_gate = lstm.sigmoid(lstm.Wxo @ x.reshape(-1, 1) + lstm.Who @ h + lstm.bo)
                
                c = f_gate * c + i_gate * g_gate
                h = o_gate * lstm.tanh_fast(c)
                
                # Output
                y = lstm.Why @ h + lstm.by
                p = lstm.softmax(y)
                
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
    print("Tensor-Based Shakespeare LSTM with NumPy")
    print("=" * 50)
    
    # Parse command line arguments
    num_files = 1
    if len(sys.argv) > 1:
        try:
            num_files = int(sys.argv[1])
        except ValueError:
            print("Usage: python tensor_shakespeare_lstm.py [num_files]")
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
    lstm = TensorShakespeareLSTM(vocab_size, hidden_size, vocab_size, learning_rate)
    print("LSTM model initialized")
    
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
                loss, _, _ = lstm.train_step(seq_inputs, seq_targets)
                batch_loss += loss
                epoch_loss += loss
                total_sequences += 1
            
            # Average loss for this batch (for display purposes)
            batch_loss_avg = batch_loss / batch_size_actual
            
            # Print progress every 50 batches
            if (batch_idx + 1) % 50 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Batch {batch_idx+1}/{len(batches)}, "
                      f"Batch Loss: {batch_loss_avg:.4f}")
        
        # Average loss for epoch (total loss / total sequences)
        epoch_loss_avg = epoch_loss / total_sequences
        epoch_time = time.time() - epoch_start
        
        print(f"Epoch {epoch+1}/{epochs} completed in {epoch_time:.2f}s")
        print(f"Average Loss: {epoch_loss_avg:.4f} (over {total_sequences} sequences)")
        
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
                    generated = generate_text(lstm, seed, char_to_idx, idx_to_char, 
                                            length=100, temperature=0.8)
                    print(f"Seed '{seed}': {generated}")
                    break
            
            print("-" * 30)
        
        print()

    print("Training completed!")
    print(f"Final loss: {epoch_loss:.4f}")
    
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
                generated = generate_text(lstm, seed, char_to_idx, idx_to_char, 
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