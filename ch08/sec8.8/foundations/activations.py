"""
activations.py

Plots and compares the activation functions discussed in the chapter:
ReLU, Leaky ReLU, Sigmoid, and Tanh.

For each function the script plots:
  - The function itself
  - Its derivative (which is what flows back during backpropagation)

The saturation regions of sigmoid and tanh, where the derivative
approaches zero, are shaded to make vanishing gradients visible.
"""

import numpy as np
import matplotlib.pyplot as plt


def relu(z):
    return np.maximum(0.0, z)

def relu_grad(z):
    return (z > 0).astype(float)


def leaky_relu(z, alpha=0.01):
    return np.where(z >= 0, z, alpha * z)

def leaky_relu_grad(z, alpha=0.01):
    return np.where(z >= 0, 1.0, alpha)


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))

def sigmoid_grad(z):
    s = sigmoid(z)
    return s * (1.0 - s)


def tanh_fn(z):
    return np.tanh(z)

def tanh_grad(z):
    return 1.0 - np.tanh(z) ** 2


SATURATION_THRESHOLD = 0.05


def plot_activation(ax_fn, ax_grad, z, fn, grad_fn, name, shade_saturation=False):
    y = fn(z)
    dy = grad_fn(z)

    ax_fn.plot(z, y, linewidth=1.8)
    ax_fn.axhline(0, color="black", linewidth=0.5)
    ax_fn.axvline(0, color="black", linewidth=0.5)
    ax_fn.set_title(name, fontsize=11)
    ax_fn.set_ylabel("f(z)")
    ax_fn.grid(True, linewidth=0.4, alpha=0.5)

    ax_grad.plot(z, dy, linewidth=1.8, color="tab:orange")
    ax_grad.axhline(0, color="black", linewidth=0.5)
    ax_grad.axvline(0, color="black", linewidth=0.5)
    ax_grad.set_ylabel("f'(z)")
    ax_grad.set_xlabel("z")
    ax_grad.grid(True, linewidth=0.4, alpha=0.5)

    if shade_saturation:
        sat_mask = dy < SATURATION_THRESHOLD
        ax_grad.fill_between(
            z, 0, dy,
            where=sat_mask,
            alpha=0.25,
            color="red",
            label=f"f'(z) < {SATURATION_THRESHOLD} (saturation)"
        )
        ax_grad.legend(fontsize=8)


def main():
    z = np.linspace(-5, 5, 500)

    fig, axes = plt.subplots(4, 2, figsize=(10, 12))
    fig.suptitle("Activation Functions and Their Derivatives", fontsize=14, y=1.01)

    specs = [
        (relu,        relu_grad,        "ReLU",        False),
        (leaky_relu,  leaky_relu_grad,  "Leaky ReLU (α=0.01)", False),
        (sigmoid,     sigmoid_grad,     "Sigmoid",     True),
        (tanh_fn,     tanh_grad,        "Tanh",        True),
    ]

    for row, (fn, grad_fn, name, shade) in enumerate(specs):
        plot_activation(axes[row, 0], axes[row, 1], z, fn, grad_fn, name, shade)

    plt.tight_layout()
    plt.savefig("activations.png", dpi=150, bbox_inches="tight")
    print("Saved activations.png")
    plt.show()


if __name__ == "__main__":
    main()
