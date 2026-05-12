# this script takes time to run, so be patient, even if it use GPU acceleration
import random
import os
import sys
import glob
import time
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# Configure TensorFlow for optimal GPU usage
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(f"GPU acceleration available! Found {len(gpus)} GPU(s)")
        print(f"GPU(s): {[gpu.name for gpu in gpus]}")
    except RuntimeError as e:
        print(f"GPU setup error: {e}")
else:
    print("No GPU found, using CPU")

class TensorFlowShakespeareRNN:
    def __init__(self, vocab_size, hidden_size=256, sequence_length=75, learning_rate=0.001):
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.sequence_length = sequence_length
        self.learning_rate = learning_rate
        
        # Build the model
        self.model = self._build_model()
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        print(f"Model built with {self.model.count_params():,} parameters")
        
        # For text generation
        self.generation_model = self._build_generation_model()
    
    def _build_model(self):
        """Build the training model"""
        model = keras.Sequential([
            # Input layer
            layers.Input(shape=(self.sequence_length, self.vocab_size)),
            
            # LSTM layers with dropout for regularization
            layers.LSTM(self.hidden_size, return_sequences=True, dropout=0.2, recurrent_dropout=0.2),
            layers.LSTM(self.hidden_size, return_sequences=True, dropout=0.2, recurrent_dropout=0.2),
            
            # Dense output layer with softmax
            layers.TimeDistributed(layers.Dense(self.vocab_size, activation='softmax'))
        ])
        
        return model
    
    def _build_generation_model(self):
        """Build model for text generation (stateful for maintaining hidden state)"""
        generation_model = keras.Sequential([
            layers.Input(batch_shape=(1, 1, self.vocab_size)),
            layers.LSTM(self.hidden_size, return_sequences=True, stateful=True, dropout=0.0),
            layers.LSTM(self.hidden_size, return_sequences=True, stateful=True, dropout=0.0),
            layers.TimeDistributed(layers.Dense(self.vocab_size, activation='softmax'))
        ])
        
        return generation_model
    
    def train_step(self, X_batch, y_batch):
        """Custom training step with gradient clipping"""
        with tf.GradientTape() as tape:
            predictions = self.model(X_batch, training=True)
            loss = tf.keras.losses.categorical_crossentropy(y_batch, predictions)
            loss = tf.reduce_mean(loss)
        
        # Compute gradients
        gradients = tape.gradient(loss, self.model.trainable_variables)
        
        # Clip gradients
        clipped_gradients, _ = tf.clip_by_global_norm(gradients, 5.0)
        
        # Apply gradients
        self.model.optimizer.apply_gradients(zip(clipped_gradients, self.model.trainable_variables))
        
        return loss
    
    def transfer_weights_to_generation_model(self):
        """Transfer weights from training model to generation model"""
        # Get weights from training model
        weights = self.model.get_weights()
        
        # Set weights to generation model (same architecture, different batch size)
        self.generation_model.set_weights(weights)
    
    def generate_text(self, seed_text, char_to_idx, idx_to_char, length=200, temperature=0.8):
        """Generate text using the trained model"""
        # Transfer weights to generation model
        self.transfer_weights_to_generation_model()
        
        # Reset state for all LSTM layers
        for layer in self.generation_model.layers:
            if hasattr(layer, 'reset_states'):
                layer.reset_states()
        
        result = seed_text
        
        # Process seed text to warm up the model
        for char in seed_text:
            if char in char_to_idx:
                x = np.zeros((1, 1, self.vocab_size))
                x[0, 0, char_to_idx[char]] = 1.0
                self.generation_model.predict(x, verbose=0)
        
        # Generate new characters
        for _ in range(length):
            if result and result[-1] in char_to_idx:
                # Prepare input
                x = np.zeros((1, 1, self.vocab_size))
                x[0, 0, char_to_idx[result[-1]]] = 1.0
                
                # Get prediction
                predictions = self.generation_model.predict(x, verbose=0)[0, 0, :]
                
                # Apply temperature sampling
                if temperature > 0:
                    predictions = np.log(predictions + 1e-8) / temperature
                    predictions = np.exp(predictions)
                    predictions = predictions / np.sum(predictions)
                    next_idx = np.random.choice(len(predictions), p=predictions)
                else:
                    next_idx = np.argmax(predictions)
                
                next_char = idx_to_char[next_idx]
                result += next_char
            else:
                break
        
        return result
    
    def get_gpu_memory_info(self):
        """Get GPU memory information"""
        try:
            if tf.config.list_physical_devices('GPU'):
                # For TensorFlow 2.x, memory info is handled differently
                # Return approximate info based on model size
                return 0, 0  # Memory info not easily accessible in TF 2.x
        except:
            pass
        return 0, 0

class TensorFlowDataLoader:
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

def create_training_data_tf(text, char_to_idx, vocab_size, sequence_length, step_size=None):
    """Create training data optimized for TensorFlow"""
    if step_size is None:
        step_size = sequence_length // 2
    
    text_len = len(text)
    sequences = []
    targets = []
    
    print("Creating training sequences...")
    
    for i in range(0, text_len - sequence_length, step_size):
        seq_chars = text[i:i+sequence_length]
        target_chars = text[i+1:i+sequence_length+1]
        
        # Convert to indices
        seq_indices = [char_to_idx.get(c, 0) for c in seq_chars]
        target_indices = [char_to_idx.get(c, 0) for c in target_chars]
        
        sequences.append(seq_indices)
        targets.append(target_indices)
        
        if len(sequences) % 1000 == 0:
            print(f"Created {len(sequences):,} sequences...")
    
    # Convert to numpy arrays
    X = np.array(sequences)
    y = np.array(targets)
    
    # Convert to one-hot encoding
    print("Converting to one-hot encoding...")
    X_onehot = tf.keras.utils.to_categorical(X, num_classes=vocab_size)
    y_onehot = tf.keras.utils.to_categorical(y, num_classes=vocab_size)
    
    return X_onehot, y_onehot

def create_tf_dataset(X, y, batch_size=32, buffer_size=10000):
    """Create TensorFlow dataset with batching and shuffling"""
    dataset = tf.data.Dataset.from_tensor_slices((X, y))
    dataset = dataset.shuffle(buffer_size)
    dataset = dataset.batch(batch_size, drop_remainder=True)
    dataset = dataset.prefetch(tf.data.AUTOTUNE)
    return dataset

class TrainingCallback(keras.callbacks.Callback):
    """Custom callback for monitoring training and generating samples"""
    def __init__(self, rnn_model, char_to_idx, idx_to_char, generate_every=5):
        self.rnn_model = rnn_model
        self.char_to_idx = char_to_idx
        self.idx_to_char = idx_to_char
        self.generate_every = generate_every
        self.seeds = ["To be", "What is", "Romeo", "My lord"]
    
    def on_epoch_end(self, epoch, logs=None):
        if epoch % self.generate_every == 0:
            print(f"\nEpoch {epoch} - Loss: {logs.get('loss', 0):.4f}, Accuracy: {logs.get('accuracy', 0):.4f}")
            
            # Generate sample text
            try:
                seed = random.choice(self.seeds)
                sample = self.rnn_model.generate_text(seed, self.char_to_idx, self.idx_to_char, 80, 0.7)
                print(f"Sample: '{sample}'")
            except Exception as e:
                print(f"Text generation error: {e}")
                print("Sample generation skipped")
            
            # GPU memory info
            current_mem, peak_mem = self.rnn_model.get_gpu_memory_info()
            if current_mem > 0:
                print(f"GPU Memory: {current_mem:.0f} MB current, {peak_mem:.0f} MB peak")
            print("-" * 80)

def main():
    print("TensorFlow Shakespeare RNN")
    print("=" * 60)
    
    # Display TensorFlow and GPU info
    print(f"TensorFlow version: {tf.__version__}")
    print(f"GPU available: {tf.config.list_physical_devices('GPU')}")
    print(f"Built with CUDA: {tf.test.is_built_with_cuda()}")
    
    # Parse arguments
    num_files = 1
    if len(sys.argv) > 1:
        try:
            num_files = int(sys.argv[1])
        except ValueError:
            print("Usage: python tf_shakespeare_rnn.py [num_files]")
            return
    
    # Load and preprocess data
    loader = TensorFlowDataLoader()
    text = loader.load_texts(num_files)
    if not text:
        return
    
    print("\nPreprocessing text...")
    text = preprocess_text(text)
    print(f"Text length: {len(text):,} characters")
    
    # Create character mappings
    chars, char_to_idx, idx_to_char = create_char_dataset(text)
    vocab_size = len(chars)
    print(f"Vocabulary size: {vocab_size}")
    print(f"Characters: {''.join(chars[:50])}{'...' if len(chars) > 50 else ''}")
    
    # Model parameters
    hidden_size = 256
    sequence_length = 75
    learning_rate = 0.001
    batch_size = 64
    epochs = 50
    
    # Create model
    print(f"\nBuilding TensorFlow model...")
    rnn = TensorFlowShakespeareRNN(
        vocab_size=vocab_size,
        hidden_size=hidden_size,
        sequence_length=sequence_length,
        learning_rate=learning_rate
    )
    
    # Create training data
    print(f"\nCreating training data...")
    X, y = create_training_data_tf(text, char_to_idx, vocab_size, sequence_length)
    print(f"Training data shape: X={X.shape}, y={y.shape}")
    
    # Create TensorFlow dataset
    train_dataset = create_tf_dataset(X, y, batch_size)
    
    # Setup callbacks
    callbacks = [
        TrainingCallback(rnn, char_to_idx, idx_to_char, generate_every=5),
        keras.callbacks.ReduceLROnPlateau(monitor='loss', factor=0.5, patience=3, min_lr=1e-6),
        keras.callbacks.EarlyStopping(monitor='loss', patience=10, restore_best_weights=True)
    ]
    
    # Training
    print(f"\nStarting training...")
    print("=" * 60)
    
    start_time = time.time()
    
    history = rnn.model.fit(
        train_dataset,
        epochs=epochs,
        callbacks=callbacks,
        verbose=1
    )
    
    total_time = time.time() - start_time
    print(f"\nTraining completed in {total_time:.2f} seconds!")
    
    # Performance summary
    total_samples = len(X) * epochs
    samples_per_sec = total_samples / total_time
    print(f"Performance: {samples_per_sec:.0f} samples/second")
    print("=" * 60)
    
    # Final generation
    print("\nFinal Shakespeare generation:")
    test_seeds = ["To be or not to be", "What light through yonder", "Romeo", "Fair is foul"]
    
    for seed in test_seeds:
        print(f"\nSeed: '{seed}'")
        try:
            result = rnn.generate_text(seed, char_to_idx, idx_to_char, 200, 0.6)
            print(f"Generated: {result}")
        except Exception as e:
            print(f"Generation error: {e}")
        print("-" * 80)
    
    # Save model
    model_path = "shakespeare_rnn_model.keras"
    rnn.model.save(model_path)
    print(f"\nModel saved to {model_path}")
    
    # Save character mappings
    import json
    mappings = {
        'char_to_idx': char_to_idx,
        'idx_to_char': idx_to_char,
        'vocab_size': vocab_size,
        'sequence_length': sequence_length,
        'hidden_size': hidden_size
    }
    
    with open('character_mappings.json', 'w') as f:
        json.dump(mappings, f)
    print("Character mappings saved to character_mappings.json")

def load_model_and_generate(model_path="shakespeare_rnn_model.keras", 
                          mappings_path="character_mappings.json"):
    """Load saved model and generate text"""
    import json
    
    # Load mappings
    with open(mappings_path, 'r') as f:
        mappings = json.load(f)
    
    char_to_idx = mappings['char_to_idx']
    idx_to_char = {int(k): v for k, v in mappings['idx_to_char'].items()}
    
    # Recreate model
    rnn = TensorFlowShakespeareRNN(
        vocab_size=mappings['vocab_size'],
        hidden_size=mappings['hidden_size'],
        sequence_length=mappings['sequence_length']
    )
    
    # Load weights
    rnn.model.load_weights(model_path)
    
    return rnn, char_to_idx, idx_to_char

if __name__ == "__main__":
    main()