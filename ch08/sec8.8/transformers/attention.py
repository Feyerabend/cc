"""
attention.py

Implements scaled dot-product attention and multi-head attention from scratch
using NumPy, matching the formula in the book:

    Attention(Q, K, V) = softmax( Q K^T / sqrt(d_k) ) V

Also demonstrates the scaling effect: without 1/sqrt(d_k), large d_k causes
the softmax to saturate, producing near-one-hot distributions that ignore
most of the sequence.
"""

import numpy as np


def softmax(x, axis=-1):
    x = x - np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


def scaled_dot_product_attention(Q, K, V, mask=None):
    """
    Parameters
    ----------
    Q : np.ndarray, shape (..., n, d_k)
    K : np.ndarray, shape (..., n, d_k)
    V : np.ndarray, shape (..., n, d_v)
    mask : np.ndarray or None
        Additive mask (e.g. -1e9 at positions to suppress).

    Returns
    -------
    output : np.ndarray, shape (..., n, d_v)
    weights : np.ndarray, shape (..., n, n)
    """
    d_k = Q.shape[-1]
    scores = Q @ K.swapaxes(-2, -1) / np.sqrt(d_k)

    if mask is not None:
        scores = scores + mask

    weights = softmax(scores, axis=-1)
    output = weights @ V
    return output, weights


class MultiHeadAttention:
    """
    Multi-head attention with h heads, each of dimension d_model // h.
    """

    def __init__(self, d_model, h, rng):
        assert d_model % h == 0, "d_model must be divisible by h"
        self.h = h
        self.d_k = d_model // h
        self.d_model = d_model

        scale = np.sqrt(1.0 / d_model)
        self.W_Q = rng.normal(0, scale, (d_model, d_model))
        self.W_K = rng.normal(0, scale, (d_model, d_model))
        self.W_V = rng.normal(0, scale, (d_model, d_model))
        self.W_O = rng.normal(0, scale, (d_model, d_model))

    def split_heads(self, x):
        """Reshape (n, d_model) -> (h, n, d_k)"""
        n = x.shape[0]
        x = x.reshape(n, self.h, self.d_k)
        return x.transpose(1, 0, 2)

    def forward(self, X, mask=None):
        """
        Parameters
        ----------
        X : np.ndarray, shape (n, d_model)
        mask : np.ndarray or None

        Returns
        -------
        out : np.ndarray, shape (n, d_model)
        weights : np.ndarray, shape (h, n, n)
        """
        Q = X @ self.W_Q
        K = X @ self.W_K
        V = X @ self.W_V

        Q = self.split_heads(Q)
        K = self.split_heads(K)
        V = self.split_heads(V)

        attn_out, weights = scaled_dot_product_attention(Q, K, V, mask)

        n = X.shape[0]
        attn_out = attn_out.transpose(1, 0, 2).reshape(n, self.d_model)
        out = attn_out @ self.W_O

        return out, weights


def demo_scaling_effect():
    """
    Shows that without scaling, large d_k causes softmax saturation.
    """
    rng = np.random.default_rng(0)
    n = 8

    print("Effect of scaling on attention weight entropy")
    print(f"{'d_k':>6}  {'unscaled entropy':>18}  {'scaled entropy':>16}")
    print("  " + "-" * 44)

    for d_k in [4, 16, 64, 256, 1024]:
        Q = rng.normal(size=(n, d_k))
        K = rng.normal(size=(n, d_k))
        V = rng.normal(size=(n, d_k))

        scores_unscaled = Q @ K.T
        scores_scaled   = Q @ K.T / np.sqrt(d_k)

        w_unscaled = softmax(scores_unscaled)
        w_scaled   = softmax(scores_scaled)

        def entropy(w):
            eps = 1e-9
            return -np.mean(np.sum(w * np.log(w + eps), axis=-1))

        print(f"  {d_k:>4}   {entropy(w_unscaled):>16.4f}   {entropy(w_scaled):>14.4f}")

    print()
    print("Higher entropy means more distributed attention (better for learning).")
    print("Without scaling, large d_k collapses to near-one-hot attention.")


def demo_multi_head():
    rng = np.random.default_rng(1)
    n, d_model, h = 6, 16, 4

    mha = MultiHeadAttention(d_model, h, rng)
    X = rng.normal(size=(n, d_model))

    out, weights = mha.forward(X)

    print(f"\nMulti-head attention: n={n}, d_model={d_model}, h={h}, d_k={d_model // h}")
    print(f"Input shape:  {X.shape}")
    print(f"Output shape: {out.shape}")
    print(f"Weights shape (h, n, n): {weights.shape}")
    print(f"Each head's weights sum to 1 per row: {np.allclose(weights.sum(-1), 1.0)}")


if __name__ == "__main__":
    demo_scaling_effect()
    demo_multi_head()
