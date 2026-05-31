"""
lstm_cell.py

Implements a single LSTM time step exactly as derived in the book.

The six equations are reproduced verbatim (using the same variable
names) so this file can be read side-by-side with the text.

Gate equations (all using concatenated [h_{t-1}, x_t]):
    f_t = sigma( W_f @ [h_{t-1}, x_t] + b_f )   forget gate
    i_t = sigma( W_i @ [h_{t-1}, x_t] + b_i )   input gate
    C~_t = tanh( W_C @ [h_{t-1}, x_t] + b_C )   cell candidate
    C_t = f_t * C_{t-1} + i_t * C~_t            cell state update
    o_t = sigma( W_o @ [h_{t-1}, x_t] + b_o )   output gate
    h_t = o_t * tanh(C_t)                       hidden state
"""

import numpy as np


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


class LSTMCell:
    """
    A single LSTM cell.

    Parameters
    ----------
    input_dim : int
        Dimensionality of x_t.
    hidden_dim : int
        Dimensionality of h_t and C_t.
    rng : np.random.Generator
    """

    def __init__(self, input_dim, hidden_dim, rng):
        self.hidden_dim = hidden_dim
        concat_dim = hidden_dim + input_dim

        scale = np.sqrt(1.0 / hidden_dim)

        self.W_f = rng.normal(0, scale, (hidden_dim, concat_dim))
        self.b_f = np.zeros(hidden_dim)

        self.W_i = rng.normal(0, scale, (hidden_dim, concat_dim))
        self.b_i = np.zeros(hidden_dim)

        self.W_C = rng.normal(0, scale, (hidden_dim, concat_dim))
        self.b_C = np.zeros(hidden_dim)

        self.W_o = rng.normal(0, scale, (hidden_dim, concat_dim))
        self.b_o = np.zeros(hidden_dim)

    def step(self, x_t, h_prev, C_prev):
        """
        Run one LSTM time step.

        Parameters
        ----------
        x_t    : np.ndarray, shape (input_dim,)
        h_prev : np.ndarray, shape (hidden_dim,)
        C_prev : np.ndarray, shape (hidden_dim,)

        Returns
        -------
        h_t : np.ndarray, shape (hidden_dim,)
        C_t : np.ndarray, shape (hidden_dim,)
        gate_values : dict
            Intermediate gate activations for inspection.
        """
        hx = np.concatenate([h_prev, x_t])

        f_t = sigmoid(self.W_f @ hx + self.b_f)
        i_t = sigmoid(self.W_i @ hx + self.b_i)
        C_tilde = np.tanh(self.W_C @ hx + self.b_C)
        C_t = f_t * C_prev + i_t * C_tilde
        o_t = sigmoid(self.W_o @ hx + self.b_o)
        h_t = o_t * np.tanh(C_t)

        gate_values = {
            "f_t": f_t,
            "i_t": i_t,
            "C_tilde": C_tilde,
            "C_t": C_t,
            "o_t": o_t,
            "h_t": h_t,
        }
        return h_t, C_t, gate_values


def demo():
    rng = np.random.default_rng(0)
    input_dim = 4
    hidden_dim = 8

    cell = LSTMCell(input_dim, hidden_dim, rng)

    h = np.zeros(hidden_dim)
    C = np.zeros(hidden_dim)

    T = 5
    print(f"Running LSTM cell for {T} steps (input_dim={input_dim}, hidden_dim={hidden_dim})")
    print()

    for t in range(T):
        x_t = rng.normal(size=(input_dim,))
        h, C, gates = cell.step(x_t, h, C)

        print(f"Step {t + 1}")
        print(f"  forget gate mean:  {gates['f_t'].mean():.4f}  (near 1 = remember, near 0 = forget)")
        print(f"  input  gate mean:  {gates['i_t'].mean():.4f}  (controls new info added)")
        print(f"  output gate mean:  {gates['o_t'].mean():.4f}  (controls what is exposed)")
        print(f"  cell state norm:   {np.linalg.norm(C):.4f}")
        print(f"  hidden state norm: {np.linalg.norm(h):.4f}")
        print()


if __name__ == "__main__":
    demo()
