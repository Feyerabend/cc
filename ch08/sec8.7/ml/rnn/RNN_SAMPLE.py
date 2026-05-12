import math
import random

class SimpleRNN:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.1):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        
        # Initialize weights randomly
        self.Wxh = self.random_matrix(hidden_size, input_size)  # input to hidden
        self.Whh = self.random_matrix(hidden_size, hidden_size)  # hidden to hidden
        self.Why = self.random_matrix(output_size, hidden_size)  # hidden to output
        
        # Biases
        self.bh = [0.0] * hidden_size  # hidden bias
        self.by = [0.0] * output_size  # output bias
        
    def random_matrix(self, rows, cols):
        """Initialize matrix with small random values"""
        return [[random.uniform(-0.1, 0.1) for _ in range(cols)] for _ in range(rows)]
    
    def tanh(self, x):
        """Activation function for hidden layer"""
        return math.tanh(x)
    
    def tanh_derivative(self, x):
        """Derivative of tanh for backpropagation"""
        return 1 - x * x
    
    def softmax(self, x):
        """Softmax activation for output layer"""
        exp_x = [math.exp(val - max(x)) for val in x]  # numerical stability
        sum_exp = sum(exp_x)
        return [val / sum_exp for val in exp_x]
    
    def forward(self, inputs, h_prev):
        """
        Forward pass through the RNN
        inputs: list of one-hot vectors (sequence)
        h_prev: previous hidden state
        Returns: outputs, hidden_states
        """
        outputs = []
        hidden_states = [h_prev]
        
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
            hidden_states.append(h)
            h_prev = h
            
        return outputs, hidden_states
    
    def backward(self, inputs, targets, outputs, hidden_states):
        """
        Backward pass - compute gradients
        """
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
                dy[i] -= targets[t][i]  # derivative of cross-entropy loss
            
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
                if targets[t][i] > 0:  # only for the correct class
                    loss -= math.log(outputs[t][i] + 1e-8)  # avoid log(0)
        
        return loss, hidden_states[-1]

# Example usage: Character-level language model
def create_char_dataset(text):
    """Convert text to character-level dataset"""
    chars = list(set(text))
    char_to_idx = {ch: i for i, ch in enumerate(chars)}
    idx_to_char = {i: ch for i, ch in enumerate(chars)}
    
    return chars, char_to_idx, idx_to_char

def char_to_onehot(char, char_to_idx, vocab_size):
    """Convert character to one-hot vector"""
    vector = [0.0] * vocab_size
    vector[char_to_idx[char]] = 1.0
    return vector

def predict_next_char(rnn, seed_text, char_to_idx, idx_to_char, length=50):
    """Generate text using trained RNN"""
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
                
                # Sample from output distribution
                probs = outputs[0]
                # Simple sampling: pick character with highest probability
                next_idx = probs.index(max(probs))
                next_char = idx_to_char[next_idx]
                result += next_char
            else:
                break
        else:
            break
    
    return result

# Demo
if __name__ == "__main__":
    # Sample text
    text = "hello world this is a simple example of character level rnn training"
    
    # Prepare data
    chars, char_to_idx, idx_to_char = create_char_dataset(text)
    vocab_size = len(chars)
    
    print(f"Vocabulary: {chars}")
    print(f"Vocabulary size: {vocab_size}")
    
    # Create RNN
    rnn = SimpleRNN(input_size=vocab_size, hidden_size=50, output_size=vocab_size, learning_rate=0.1)
    
    # Training data preparation
    sequence_length = 10
    sequences = []
    targets = []
    
    for i in range(len(text) - sequence_length):
        seq = text[i:i+sequence_length]
        target = text[i+1:i+sequence_length+1]
        
        seq_vectors = [char_to_onehot(c, char_to_idx, vocab_size) for c in seq]
        target_vectors = [char_to_onehot(c, char_to_idx, vocab_size) for c in target]
        
        sequences.append(seq_vectors)
        targets.append(target_vectors)
    
    # Training loop
    print("\nStarting training...")
    h = [0.0] * rnn.hidden_size
    
    for epoch in range(100):
        total_loss = 0.0
        h = [0.0] * rnn.hidden_size  # reset hidden state
        
        for seq, target in zip(sequences, targets):
            loss, h = rnn.train_step(seq, target, h)
            total_loss += loss
        
        if epoch % 20 == 0:
            avg_loss = total_loss / len(sequences)
            print(f"Epoch {epoch}, Average Loss: {avg_loss:.4f}")
            
            # Generate sample text
            sample = predict_next_char(rnn, "hello", char_to_idx, idx_to_char, 20)
            print(f"Sample generation: '{sample}'")
    
    print("\nFinal text generation:")
    result = predict_next_char(rnn, "this", char_to_idx, idx_to_char, 30)
    print(f"Generated: '{result}'")