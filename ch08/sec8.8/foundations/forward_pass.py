"""
forward_pass.py

Implements a minimal feedforward neural network using only NumPy.
The network has a fixed architecture: 2 -> 4 -> 4 -> 1.

The chapter describes the layer computation as:
    z^(l) = W^(l) h^(l-1) + b^(l)
    h^(l) = sigma(z^(l))

This file makes each of those steps explicit and prints intermediate
values so you can follow the data through the network by hand.
"""

import numpy as np


def relu(z):
    return np.maximum(0.0, z)


def relu_derivative(z):
    return (z > 0).astype(float)


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def softmax(z):
    shifted = z - np.max(z)
    exp_z = np.exp(shifted)
    return exp_z / np.sum(exp_z)


def initialise_parameters(layer_dims, rng):
    """
    Xavier (Glorot) initialisation: scale weights by 1/sqrt(fan_in).
    Biases are initialised to zero.

    Parameters
    ----------
    layer_dims : list of int
        Number of units in each layer, including the input layer.
    rng : np.random.Generator

    Returns
    -------
    params : list of (W, b) tuples, one per layer transition.
    """
    params = []
    for i in range(1, len(layer_dims)):
        fan_in = layer_dims[i - 1]
        fan_out = layer_dims[i]
        scale = np.sqrt(1.0 / fan_in)
        W = rng.normal(0.0, scale, size=(fan_out, fan_in))
        b = np.zeros((fan_out, 1))
        params.append((W, b))
    return params


def forward_pass(x, params, activation=relu, output_activation=sigmoid):
    """
    Runs a full forward pass through the network.

    Parameters
    ----------
    x : np.ndarray, shape (d, 1)
        Input column vector.
    params : list of (W, b) tuples
    activation : callable
        Hidden layer activation function.
    output_activation : callable
        Output layer activation function.

    Returns
    -------
    activations : list of np.ndarray
        The activation h^(l) at every layer, including the input (l=0).
    pre_activations : list of np.ndarray
        The pre-activation z^(l) at every layer (excluding the input).
    """
    h = x
    activations = [h]
    pre_activations = []

    for layer_idx, (W, b) in enumerate(params):
        z = W @ h + b
        pre_activations.append(z)

        is_last_layer = (layer_idx == len(params) - 1)
        if is_last_layer:
            h = output_activation(z)
        else:
            h = activation(z)

        activations.append(h)

    return activations, pre_activations


def binary_cross_entropy(y_hat, y):
    eps = 1e-9
    return -(y * np.log(y_hat + eps) + (1 - y) * np.log(1 - y_hat + eps))


def print_pass(x, y, params):
    print("Input x:")
    print(x.T)

    activations, pre_activations = forward_pass(x, params)

    for l, (z, h) in enumerate(zip(pre_activations, activations[1:]), start=1):
        print(f"\nLayer {l}")
        print(f"  pre-activation z^({l}):  {z.T}")
        print(f"  activation    h^({l}):  {h.T}")

    y_hat = activations[-1]
    loss = binary_cross_entropy(y_hat, y)
    print(f"\nTarget y       : {y}")
    print(f"Prediction y_hat: {float(y_hat.flat[0]):.6f}")
    print(f"Binary cross-entropy loss: {float(loss.flat[0]):.6f}")


if __name__ == "__main__":
    rng = np.random.default_rng(seed=42)

    layer_dims = [2, 4, 4, 1]
    params = initialise_parameters(layer_dims, rng)

    x = np.array([[0.5], [-0.3]])
    y = 1.0

    print_pass(x, y, params)
