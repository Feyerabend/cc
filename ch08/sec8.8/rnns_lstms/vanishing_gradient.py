"""
vanishing_gradient.py

Demonstrates the vanishing gradient problem in a plain RNN.

A simple RNN has the recurrence:
    h_t = tanh(W_hh @ h_{t-1} + W_xh @ x_t + b)

The gradient of the loss w.r.t. h_0 passes through T Jacobians of the
form d(h_t)/d(h_{t-1}). Each Jacobian includes the factor W_hh^T scaled
by the tanh derivative. If the spectral radius of W_hh is below 1, the
product of these Jacobians shrinks exponentially.

This script:
  1. Initialises W_hh with spectral radius < 1 and measures gradient decay.
  2. Repeats with spectral radius > 1 to show gradient explosion.
  3. Plots gradient norm vs sequence length for both cases.
"""

import numpy as np
import matplotlib.pyplot as plt


def tanh_derivative(z):
    return 1.0 - np.tanh(z) ** 2


def rnn_gradient_norms(T, W_hh, h_dim, rng):
    """
    Propagates a gradient backward through T time steps of a plain RNN.
    Returns the norm of the gradient at each step.

    We set x_t = 0 so only the recurrent path matters.
    The hidden state is updated as:  h_t = tanh(W_hh @ h_{t-1})
    """
    h = rng.normal(size=(h_dim,)) * 0.1
    states = [h.copy()]

    for _ in range(T):
        z = W_hh @ states[-1]
        h = np.tanh(z)
        states.append(h.copy())

    grad = np.ones(h_dim)
    norms = [np.linalg.norm(grad)]

    for t in range(T, 0, -1):
        z = W_hh @ states[t - 1]
        diag_dtanh = tanh_derivative(z)
        grad = (W_hh.T @ (diag_dtanh * grad))
        norms.append(np.linalg.norm(grad))

    return list(reversed(norms))


def make_W_with_spectral_radius(h_dim, target_radius, rng):
    W = rng.normal(size=(h_dim, h_dim))
    eigenvalues = np.linalg.eigvals(W)
    current_radius = np.max(np.abs(eigenvalues))
    return W * (target_radius / current_radius)


def main():
    rng = np.random.default_rng(42)
    h_dim = 16
    T = 50

    W_small = make_W_with_spectral_radius(h_dim, target_radius=0.8, rng=rng)
    W_large = make_W_with_spectral_radius(h_dim, target_radius=1.2, rng=rng)

    norms_vanish = rnn_gradient_norms(T, W_small, h_dim, rng)
    norms_explode = rnn_gradient_norms(T, W_large, h_dim, rng)

    steps = list(range(T + 1))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    ax1.plot(steps, norms_vanish, linewidth=1.8, color="tab:blue")
    ax1.set_xlabel("Time step from output")
    ax1.set_ylabel("Gradient norm")
    ax1.set_title("Vanishing gradients (spectral radius = 0.8)")
    ax1.set_yscale("log")
    ax1.grid(True, linewidth=0.4, alpha=0.5)

    ax2.plot(steps, norms_explode, linewidth=1.8, color="tab:red")
    ax2.set_xlabel("Time step from output")
    ax2.set_ylabel("Gradient norm")
    ax2.set_title("Exploding gradients (spectral radius = 1.2)")
    ax2.set_yscale("log")
    ax2.grid(True, linewidth=0.4, alpha=0.5)

    plt.tight_layout()
    plt.savefig("vanishing_gradient.png", dpi=150, bbox_inches="tight")
    print("Saved vanishing_gradient.png")
    plt.show()


if __name__ == "__main__":
    main()
