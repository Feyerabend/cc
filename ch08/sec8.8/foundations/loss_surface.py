"""
loss_surface.py

Visualises the loss landscape of a toy regression problem with two
free parameters: weight w and bias b for a single linear neuron.

The model is simply:  y_hat = sigmoid(w * x + b)
The loss is binary cross-entropy averaged over a small dataset.

Plotting the surface over a grid of (w, b) values shows:
  - The overall bowl shape of the landscape
  - Contour lines that gradient descent follows
  - A saddle-point region that appears when the dataset is linearly
    separable and the model is over-parameterised for the task

The gradient at a random starting point is overlaid as an arrow to
illustrate the direction of steepest descent.
"""

import numpy as np
import matplotlib.pyplot as plt


X = np.array([0.2, 0.5, 0.8, -0.3, -0.7])
Y = np.array([1.0, 1.0,  1.0,  0.0,  0.0])


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def bce_loss(w, b):
    z = w * X + b
    y_hat = sigmoid(z)
    eps = 1e-9
    return -np.mean(Y * np.log(y_hat + eps) + (1 - Y) * np.log(1 - y_hat + eps))


def compute_surface(w_range, b_range):
    W, B = np.meshgrid(w_range, b_range)
    L = np.vectorize(bce_loss)(W, B)
    return W, B, L


def numerical_gradient(w, b, h=1e-4):
    dw = (bce_loss(w + h, b) - bce_loss(w - h, b)) / (2 * h)
    db = (bce_loss(w, b + h) - bce_loss(w, b - h)) / (2 * h)
    return dw, db


def main():
    w_range = np.linspace(-4, 8, 200)
    b_range = np.linspace(-6, 4, 200)
    W, B, L = compute_surface(w_range, b_range)

    w0, b0 = 0.0, -2.0
    dw, db = numerical_gradient(w0, b0)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax3d = fig.add_subplot(121, projection="3d")
    ax3d.plot_surface(W, B, L, cmap="viridis", alpha=0.85, linewidth=0)
    ax3d.set_xlabel("w")
    ax3d.set_ylabel("b")
    ax3d.set_zlabel("Loss")
    ax3d.set_title("Loss Surface (3D)")

    ax2d = axes[1]
    cp = ax2d.contourf(W, B, L, levels=40, cmap="viridis")
    fig.colorbar(cp, ax=ax2d, label="Loss")
    ax2d.contour(W, B, L, levels=40, colors="white", linewidths=0.4, alpha=0.4)

    scale = 0.3
    ax2d.annotate(
        "",
        xy=(w0 - scale * dw, b0 - scale * db),
        xytext=(w0, b0),
        arrowprops=dict(arrowstyle="->", color="red", lw=2.0),
    )
    ax2d.plot(w0, b0, "ro", markersize=6, label="start")
    ax2d.set_xlabel("w")
    ax2d.set_ylabel("b")
    ax2d.set_title("Loss Contours + Gradient Direction")
    ax2d.legend()

    plt.tight_layout()
    plt.savefig("loss_surface.png", dpi=150, bbox_inches="tight")
    print("Saved loss_surface.png")
    plt.show()


if __name__ == "__main__":
    main()
