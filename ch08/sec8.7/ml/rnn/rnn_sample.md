
## Simple RNN

* `SimpleRNN` Class: This is the main class that defines the RNN architecture and its operations.

    * `__init__`:
        * Purpose: Initializes the RNN model.
        * How to use: When creating an `RNN` object, you specify the `input_size` (size of one-hot
          encoded input), `hidden_size` (number of neurons in the hidden layer), `output_size`
          (size of one-hot encoded output), and an optional `learning_rate`. For example,
          `rnn = SimpleRNN(input_size=vocab_size, hidden_size=50, output_size=vocab_size, learning_rate=0.1)`.
        * What to expect: This sets up the initial weights (`Wxh`, `Whh`, `Why`) and biases
          (`bh`, `by`) randomly. These weights and biases are the parameters the model will
          learn during training.

    * `random_matrix`:
        * Purpose: A helper function to initialize weight matrices with small random values.
        * How to use: Called internally by `__init__`. Students generally won't call this directly.
        * What to expect: Creates a 2D list (matrix) filled with random numbers between -0.1 and 0.1.
          This helps break symmetry and allows the model to learn different features.

    * `tanh`:
        * Purpose: The activation function for the hidden layer. It squashes values between -1 and 1.
        * How to use: Called internally during the forward pass.
        * What to expect: Given an input `x`, it returns `math.tanh(x)`. Non-linearity introduced
          by `tanh` allows the RNN to learn complex patterns.

    * `tanh_derivative`:
        * Purpose: The derivative of the `tanh` function, used during backpropagation.
        * How to use: Called internally during the backward pass.
        * What to expect: Given an output `x` from the `tanh` function, it returns `1 - x * x`.
          This derivative is crucial for calculating gradients.

    * `softmax`:
        * Purpose: The activation function for the output layer. It converts a vector of numbers
          into a probability distribution, where all values are between 0 and 1 and sum up to 1.
        * How to use: Called internally during the forward pass to get the model's output probabilities.
        * What to expect: Given a list of activations, it returns a list of probabilities. The
          highest probability corresponds to the character the RNN predicts as the next in the sequence.

    * `forward`:
        * Purpose: Performs the forward pass through the RNN for a given sequence of inputs. It
          calculates the hidden states and outputs for each time step.
        * How to use: `outputs, hidden_states = rnn.forward(inputs, h_prev)`. `inputs` are a sequence
          of one-hot vectors, and `h_prev` is the hidden state from the previous sequence or an initial
          zero vector.
        * What to expect: Returns two lists: `outputs` (the predicted probability distributions for
          each time step) and `hidden_states` (the hidden state at each time step).

    * `backward`:
        * Purpose: Implements the backpropagation through time (BPTT) algorithm to compute gradients
          of the loss with respect to the weights and biases.
        * How to use: Called internally by `train_step`. Students won't call this directly.
        * What to expect: Updates the internal gradients (`dWxh`, `dWhh`, `dWhy`, `dbh`, `dby`) based
          on the difference between predicted outputs and actual targets. After computing, it applies
          these gradients to update the model's weights and biases.

    * `train_step`:
        * Purpose: Performs a single training step: forward pass, backward pass (gradient calculation
          and weight update), and loss calculation.
        * How to use: `loss, h = rnn.train_step(seq, target, h)`. You provide a sequence of inputs,
          their corresponding target outputs, and the previous hidden state.
        * What to expect: Returns the calculated `loss` for the given sequence and the `final hidden state`
          after processing the sequence. This hidden state is then passed to the next `train_step` for
          sequential training.

* Helper Functions for Character-level Model:

    * `create_char_dataset`:
        * Purpose: Processes raw text to create a vocabulary of unique characters and mappings between
          characters and their numerical indices.
        * How to use: `chars, char_to_idx, idx_to_char = create_char_dataset(text)`. Pass your training
          text to it.
        * What to expect: Returns a list of unique `chars`, a dictionary `char_to_idx` (mapping character
          to its integer index), and `idx_to_char` (mapping integer index back to character). These are
          essential for converting text to numerical representations and vice-versa.

    * `char_to_onehot`:
        * Purpose: Converts a single character into a one-hot encoded vector. This is the numerical input
          format for the RNN.
        * How to use: `vector = char_to_onehot(char, char_to_idx, vocab_size)`. Provide the character,
          the character-to-index mapping, and the total vocabulary size.
        * What to expect: Returns a list of floats where only one element is 1.0 (at the index corresponding
          to the character) and others are 0.0.

    * `predict_next_char`:
        * Purpose: Uses the trained RNN to generate new text based on a seed text.
        * How to use: `sample = predict_next_char(rnn, "seed_text", char_to_idx, idx_to_char, length=50)`.
          Provide the trained RNN model, a starting string, the character mappings, and the desired length
          of the generated text.
        * What to expect: Returns a string of generated text. The quality of the generated text depends on
          the training data size, epochs, and model complexity.

* Example Usage (`if __name__ == "__main__":`):
    * Purpose: This block demonstrates how to set up, train, and use the `SimpleRNN` for a character-level
      language modeling task.
    * What to expect: It will print the vocabulary, vocabulary size, training progress (epoch and loss),
      and sample text generations at different epochs. It showcases the end-to-end process of training and
      inference with this custom RNN.
