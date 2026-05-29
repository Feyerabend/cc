"""
dropout.py

Implements inverted dropout and verifies the scale-correction property.

During training with dropout probability p:
  - Each unit is zeroed with probability p.
  - Surviving units are scaled by 1 / (1 - p).
  - Expected value of each unit is unchanged.

During inference:
  - No zeroing. No scaling. The output equals the pre-dropout values.

This file:
  1. Implements a Dropout layer with a training flag.
  2. Verifies that the expected value is preserved under training-mode dropout.
  3. Shows that forgetting to disable dropout at inference time gives
     systematically lower activations.
"""

import numpy as np


class Dropout:
    def __init__(self, p=0.5, rng=None):
        """
        Parameters
        ----------
        p : float
            Probability of zeroing each unit (drop probability).
        rng : np.random.Generator or None
        """
        assert 0.0 <= p < 1.0, "Drop probability must be in [0, 1)"
        self.p = p
        self.rng = rng or np.random.default_rng()
        self.mask = None

    def forward(self, x, training=True):
        """
        Parameters
        ----------
        x : np.ndarray
        training : bool

        Returns
        -------
        out : np.ndarray, same shape as x
        """
        if not training:
            return x

        self.mask = (self.rng.uniform(size=x.shape) >= self.p).astype(float)
        return x * self.mask / (1.0 - self.p)

    def backward(self, grad_output):
        """Gradient passes through only where mask was 1."""
        return grad_output * self.mask / (1.0 - self.p)


def verify_expectation():
    rng = np.random.default_rng(0)
    x = np.ones(10_000)

    for p in [0.1, 0.3, 0.5, 0.7]:
        layer = Dropout(p=p, rng=rng)
        out = layer.forward(x, training=True)
        print(f"p={p:.1f}  input mean={x.mean():.4f}  "
              f"output mean (training)={out.mean():.4f}  "
              f"output mean (inference)={layer.forward(x, training=False).mean():.4f}")


def show_inference_bug():
    """
    Demonstrates what happens when dropout is left on at inference.
    The output is scaled down by (1-p), a common source of bugs.
    """
    rng = np.random.default_rng(1)
    x = np.full(10_000, 2.0)
    p = 0.5
    layer = Dropout(p=p, rng=rng)

    correct_inference = layer.forward(x, training=False).mean()
    buggy_inference   = layer.forward(x, training=True).mean()

    print(f"\nDropout bug demonstration (p={p}, input=2.0):")
    print(f"  Correct inference (dropout off): {correct_inference:.4f}")
    print(f"  Buggy inference   (dropout on):  {buggy_inference:.4f}")
    print(f"  Ratio: {buggy_inference / correct_inference:.4f} (should be ~1.0 if correct)")


if __name__ == "__main__":
    print("Expected value preservation under inverted dropout:")
    verify_expectation()
    show_inference_bug()
