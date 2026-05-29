"""
positional_encoding.py

Computes and visualises the sinusoidal positional encoding from:
    Vaswani et al., "Attention Is All You Need" (2017).

For position pos and dimension index i:
    PE[pos, 2i]   = sin( pos / 10000^(2i / d_model) )
    PE[pos, 2i+1] = cos( pos / 10000^(2i / d_model) )

Properties that make this encoding useful:
  1. Each position gets a unique encoding vector.
  2. The encoding for position pos+k is a linear function of the encoding
     for position pos, so the model can learn to attend to relative offsets.
  3. The frequencies span many scales: the first dimension oscillates fast
     (period 2pi), while the last oscillates very slowly (period ~62832).
  4. Values are bounded in [-1, 1], so they do not dominate the token
     embeddings when added.
"""

import numpy as np
import matplotlib.pyplot as plt


def positional_encoding(max_seq_len, d_model):
    """
    Returns the PE matrix of shape (max_seq_len, d_model).
    """
    PE = np.zeros((max_seq_len, d_model))
    positions = np.arange(max_seq_len)[:, np.newaxis]
    dim_indices = np.arange(0, d_model, 2)

    angles = positions / np.power(10000, dim_indices / d_model)

    PE[:, 0::2] = np.sin(angles)
    PE[:, 1::2] = np.cos(angles[:, :d_model // 2])

    return PE


def plot_encoding(PE, max_seq_len, d_model):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    im = axes[0].imshow(PE, aspect="auto", cmap="RdBu", vmin=-1, vmax=1)
    axes[0].set_xlabel("Dimension index")
    axes[0].set_ylabel("Position")
    axes[0].set_title(f"Positional Encoding Matrix ({max_seq_len} x {d_model})")
    fig.colorbar(im, ax=axes[0])

    for pos in [0, 4, 8, 16, 32]:
        if pos < max_seq_len:
            axes[1].plot(PE[pos, :], label=f"pos={pos}", linewidth=1.2)
    axes[1].set_xlabel("Dimension index")
    axes[1].set_ylabel("Encoding value")
    axes[1].set_title("Encoding vectors for selected positions")
    axes[1].legend()
    axes[1].grid(True, linewidth=0.4, alpha=0.5)

    plt.tight_layout()
    plt.savefig("positional_encoding.png", dpi=150, bbox_inches="tight")
    print("Saved positional_encoding.png")
    plt.show()


def demo_relative_encoding():
    """
    Shows that PE[pos + k] can be expressed as a linear transformation of PE[pos].
    We verify this numerically for a single dimension pair (sin, cos).
    """
    d_model = 64
    max_len = 100
    PE = positional_encoding(max_len, d_model)

    pos = 20
    k = 5
    dim = 0

    sin_pos  = PE[pos, dim]
    cos_pos  = PE[pos, dim + 1]
    sin_posk = PE[pos + k, dim]
    cos_posk = PE[pos + k, dim + 1]

    freq = 1.0 / (10000 ** (dim / d_model))
    angle_k = k * freq

    predicted_sin = sin_pos * np.cos(angle_k) + cos_pos * np.sin(angle_k)
    predicted_cos = cos_pos * np.cos(angle_k) - sin_pos * np.sin(angle_k)

    print("Relative encoding check (dimension pair 0, 1):")
    print(f"  PE[{pos}]  sin={sin_pos:.6f}  cos={cos_pos:.6f}")
    print(f"  PE[{pos+k}] sin={sin_posk:.6f}  cos={cos_posk:.6f}")
    print(f"  Predicted from linear transform: sin={predicted_sin:.6f}  cos={predicted_cos:.6f}")
    print(f"  Error: {abs(predicted_sin - sin_posk):.2e}, {abs(predicted_cos - cos_posk):.2e}")
    print("  -> PE[pos+k] is an exact linear transform of PE[pos] for each dimension pair.")


if __name__ == "__main__":
    max_seq_len = 64
    d_model = 64
    PE = positional_encoding(max_seq_len, d_model)
    plot_encoding(PE, max_seq_len, d_model)
    demo_relative_encoding()
