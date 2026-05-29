"""
batch_norm.py

Implements Batch Normalisation (Ioffe and Szegedy, 2015) from scratch.

Given a mini-batch of activations x of shape (batch_size, d):
  1. Compute batch mean and variance:
       mu    = mean(x, axis=0)
       sigma = var(x, axis=0) + eps
  2. Normalise:
       x_hat = (x - mu) / sqrt(sigma)
  3. Rescale with learned parameters gamma and beta:
       y = gamma * x_hat + beta

During training, accumulate running statistics:
   running_mean = momentum * running_mean + (1 - momentum) * mu
   running_var  = momentum * running_var  + (1 - momentum) * var

During inference, use running statistics instead of batch statistics.
"""

import numpy as np


class BatchNorm:
    def __init__(self, d, momentum=0.9, eps=1e-5):
        """
        Parameters
        ----------
        d : int
            Feature dimension (number of units to normalise over batch).
        momentum : float
            Smoothing factor for running statistics.
        eps : float
            Numerical stability constant.
        """
        self.gamma = np.ones(d)
        self.beta = np.zeros(d)
        self.momentum = momentum
        self.eps = eps

        self.running_mean = np.zeros(d)
        self.running_var = np.ones(d)

        self.cache = None

    def forward(self, x, training=True):
        """
        Parameters
        ----------
        x : np.ndarray, shape (batch_size, d)
        training : bool

        Returns
        -------
        y : np.ndarray, shape (batch_size, d)
        """
        if training:
            mu = x.mean(axis=0)
            var = x.var(axis=0)

            self.running_mean = self.momentum * self.running_mean + (1 - self.momentum) * mu
            self.running_var  = self.momentum * self.running_var  + (1 - self.momentum) * var

            x_hat = (x - mu) / np.sqrt(var + self.eps)
            self.cache = (x, x_hat, mu, var)
        else:
            x_hat = (x - self.running_mean) / np.sqrt(self.running_var + self.eps)

        return self.gamma * x_hat + self.beta

    def backward(self, grad_output):
        """
        Backpropagates through batch norm to compute:
          - d_gamma, d_beta (parameter gradients)
          - d_x (input gradient, needed for chaining with previous layers)
        """
        x, x_hat, mu, var = self.cache
        batch_size = x.shape[0]

        d_gamma = np.sum(grad_output * x_hat, axis=0)
        d_beta = np.sum(grad_output, axis=0)

        d_x_hat = grad_output * self.gamma
        d_var = np.sum(d_x_hat * (x - mu) * -0.5 * (var + self.eps) ** -1.5, axis=0)
        d_mu = (np.sum(d_x_hat * -1.0 / np.sqrt(var + self.eps), axis=0)
                + d_var * np.mean(-2.0 * (x - mu), axis=0))
        d_x = (d_x_hat / np.sqrt(var + self.eps)
               + d_var * 2.0 * (x - mu) / batch_size
               + d_mu / batch_size)

        return d_x, d_gamma, d_beta


def demo():
    rng = np.random.default_rng(42)
    batch_size = 32
    d = 8

    bn = BatchNorm(d=d)
    x = rng.normal(loc=5.0, scale=3.0, size=(batch_size, d))

    y_train = bn.forward(x, training=True)
    print("After batch norm (training):")
    print(f"  Input  mean: {x.mean(axis=0).round(3)}")
    print(f"  Input  std:  {x.std(axis=0).round(3)}")
    print(f"  Output mean: {y_train.mean(axis=0).round(3)}")
    print(f"  Output std:  {y_train.std(axis=0).round(3)}")

    for _ in range(100):
        x_batch = rng.normal(loc=5.0, scale=3.0, size=(batch_size, d))
        bn.forward(x_batch, training=True)

    x_test = rng.normal(loc=5.0, scale=3.0, size=(batch_size, d))
    y_inference = bn.forward(x_test, training=False)
    print("\nRunning statistics after 100 training batches:")
    print(f"  Running mean (should be ~5.0): {bn.running_mean.round(3)}")
    print(f"  Running var  (should be ~9.0): {bn.running_var.round(3)}")
    print(f"\nInference output mean (should be ~0): {y_inference.mean(axis=0).round(3)}")


if __name__ == "__main__":
    demo()
