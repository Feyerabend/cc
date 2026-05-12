import json
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

class TensorFlowShakespeareRNN:
    def __init__(self, vocab_size, hidden_size=256, sequence_length=75):
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.sequence_length = sequence_length
        self.generation_model = self._build_generation_model()

    def _build_generation_model(self):
        """Build model for text generation (stateful for maintaining hidden state)"""
        generation_model = keras.Sequential([
            layers.Input(batch_shape=(1, 1, self.vocab_size)),
            layers.LSTM(self.hidden_size, return_sequences=True, stateful=True, dropout=0.0),
            layers.LSTM(self.hidden_size, return_sequences=True, stateful=True, dropout=0.0),
            layers.TimeDistributed(layers.Dense(self.vocab_size, activation='softmax'))
        ])
        return generation_model

    def generate_text(self, seed_text, char_to_idx, idx_to_char, length=200, temperature=0.8):
        """Generate text using the trained model"""
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
                x = np.zeros((1, 1, self.vocab_size))
                x[0, 0, char_to_idx[result[-1]]] = 1.0
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

class ShakespeareInferenceEngine:
    def __init__(self, model_path="shakespeare_rnn_model.keras", mappings_path="character_mappings.json"):
        """Initialize the inference engine with model and mappings"""
        # Load character mappings
        with open(mappings_path, 'r') as f:
            mappings = json.load(f)

        self.char_to_idx = mappings['char_to_idx']
        self.idx_to_char = {int(k): v for k, v in mappings['idx_to_char'].items()}
        self.vocab_size = mappings['vocab_size']
        self.sequence_length = mappings['sequence_length']
        self.hidden_size = mappings['hidden_size']

        # Initialize model
        self.rnn = TensorFlowShakespeareRNN(
            vocab_size=self.vocab_size,
            hidden_size=self.hidden_size,
            sequence_length=self.sequence_length
        )

        # Load weights
        try:
            self.rnn.generation_model.load_weights(model_path)
            print(f"Model loaded from {model_path}")
        except Exception as e:
            print(f"Error loading model weights: {e}")
            raise

    def generate(self, seed_text, length=200, temperature=0.8):
        """Generate text using the loaded model"""
        try:
            result = self.rnn.generate_text(
                seed_text=seed_text,
                char_to_idx=self.char_to_idx,
                idx_to_char=self.idx_to_char,
                length=length,
                temperature=temperature
            )
            return result
        except Exception as e:
            print(f"Error during text generation: {e}")
            return None

def main():
    # Initialize inference engine
    try:
        engine = ShakespeareInferenceEngine(
            model_path="shakespeare_rnn_model.keras",
            mappings_path="character_mappings.json"
        )
    except Exception as e:
        print(f"Failed to initialize inference engine: {e}")
        return

    # Example seed texts
    test_seeds = ["To be or not to be", "What light through yonder", "Romeo", "Fair is foul"]

    # Generate text for each seed
    for seed in test_seeds:
        print(f"\nSeed: '{seed}'")
        generated_text = engine.generate(seed, length=200, temperature=0.6)
        if generated_text:
            print(f"Generated: {generated_text}")
        print("-" * 80)

if __name__ == "__main__":
    main()