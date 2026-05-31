
## RNNs and LSTMs

The book derives the LSTM equations and explains the gating
mechanism. This section implements the LSTM cell from scratch and
demonstrates the vanishing gradient problem that motivated it.

### Files

| File                    | What it demonstrates                                        |
|-------------------------|-------------------------------------------------------------|
| `vanishing_gradient.py` | Gradient norm decay with depth in a plain RNN               |
| `lstm_cell.py`          | Single LSTM step, matching the equations from the chapter   |
| `lstm_sequence.py`      | Running an LSTM over a full sequence (sine wave prediction) |
| `gru_cell.py`           | Gated Recurrent Unit: a simpler alternative to the LSTM     |


### Key ideas extended here

*Why gradients vanish.* A plain RNN propagates gradients through repeated
matrix multiplications. If the spectral radius of the recurrent weight matrix
$W_{hh}$ is less than one, the gradient norm decays exponentially with the
number of time steps. `vanishing_gradient.py` shows this collapse experimentally
and plots gradient norm as a function of sequence length.

*The GRU.* The LSTM is not the only solution to vanishing gradients. The Gated
Recurrent Unit (GRU), introduced in 2014, achieves similar performance with fewer
parameters by merging the forget and input gates into a single *update gate* and
eliminating the separate cell state. `gru_cell.py` implements the GRU alongside
the LSTM so the two architectures can be compared directly.

*Backpropagation through time (BPTT).* Training an RNN on a sequence of length
$T$ is equivalent to unrolling the recurrence into a feedforward network with $T$
layers and backpropagating through all of them. The gradient of the loss with
respect to the initial hidden state passes through every time step, making the
vanishing and exploding gradient problems particularly acute.
