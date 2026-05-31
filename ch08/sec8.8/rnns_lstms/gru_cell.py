"""
gru_cell.py

Implements a Gated Recurrent Unit (GRU) cell from scratch.

The GRU was introduced in Cho et al. (2014) as a simpler alternative to the LSTM.
It merges the forget and input gates into a single update gate and removes the
separate cell state, using only the hidden state h_t to carry memory.

GRU equations:
    z_t  = sigma( W_z @ [h_{t-1}, x_t] + b_z )        update gate
    r_t  = sigma( W_r @ [h_{t-1}, x_t] + b_r )        reset gate
    h~_t = tanh(  W_h @ [r_t * h_{t-1}, x_t] + b_h )  candidate hidden state
    h_t  = (1 - z_t) * h_{t-1} + z_t * h~_t           final hidden state

Compare with LSTM:
  - No separate cell state C_t.
  - Reset gate r_t controls how much of the previous hidden state enters
    the candidate. When r_t ~ 0, the candidate ignores history.
  - Update gate z_t interpolates between old and new hidden state directly.
  - Fewer parameters: 3 weight matrices instead of 4.
"""

import numpy as np


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


class GRUCell:
    def __init__(self, input_dim, hidden_dim, rng):
        self.hidden_dim = hidden_dim
        concat_dim = hidden_dim + input_dim
        scale = np.sqrt(1.0 / hidden_dim)

        self.W_z = rng.normal(0, scale, (hidden_dim, concat_dim))
        self.b_z = np.zeros(hidden_dim)

        self.W_r = rng.normal(0, scale, (hidden_dim, concat_dim))
        self.b_r = np.zeros(hidden_dim)

        self.W_h = rng.normal(0, scale, (hidden_dim, concat_dim))
        self.b_h = np.zeros(hidden_dim)

    def step(self, x_t, h_prev):
        hx = np.concatenate([h_prev, x_t])

        z_t = sigmoid(self.W_z @ hx + self.b_z)
        r_t = sigmoid(self.W_r @ hx + self.b_r)

        h_candidate_input = np.concatenate([r_t * h_prev, x_t])
        h_tilde = np.tanh(self.W_h @ h_candidate_input + self.b_h)

        h_t = (1.0 - z_t) * h_prev + z_t * h_tilde

        gate_values = {
            "z_t": z_t,
            "r_t": r_t,
            "h_tilde": h_tilde,
            "h_t": h_t,
        }
        return h_t, gate_values


def parameter_count(cell):
    total = 0
    for name in ("W_z", "W_r", "W_h"):
        total += getattr(cell, name).size
    for name in ("b_z", "b_r", "b_h"):
        total += getattr(cell, name).size
    return total


def demo():
    from lstm_cell import LSTMCell

    rng = np.random.default_rng(1)
    input_dim = 4
    hidden_dim = 8

    gru = GRUCell(input_dim, hidden_dim, rng)
    lstm = LSTMCell(input_dim, hidden_dim, rng)

    gru_params = parameter_count(gru)
    lstm_params = sum(
        getattr(lstm, n).size
        for n in ("W_f", "W_i", "W_C", "W_o", "b_f", "b_i", "b_C", "b_o")
    )

    print(f"Parameter count comparison (input_dim={input_dim}, hidden_dim={hidden_dim})")
    print(f"  GRU:  {gru_params}")
    print(f"  LSTM: {lstm_params}")
    print(f"  Ratio: {lstm_params / gru_params:.2f}x more parameters in LSTM")
    print()

    h = np.zeros(hidden_dim)
    T = 5
    print(f"GRU forward pass for {T} steps:")
    for t in range(T):
        x_t = rng.normal(size=(input_dim,))
        h, gates = gru.step(x_t, h)
        print(f"  Step {t + 1}: update gate mean={gates['z_t'].mean():.3f}  "
              f"reset gate mean={gates['r_t'].mean():.3f}  "
              f"|h_t|={np.linalg.norm(h):.4f}")


if __name__ == "__main__":
    demo()
