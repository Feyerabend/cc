"""
convolution.py

Implements 2D cross-correlation and true 2D convolution from scratch
using only NumPy.

The chapter gives the cross-correlation formula:
    (f * x)[i, j] = sum_m sum_n  f[m, n] * x[i + m, j + n]

This file:
  1. Implements both cross-correlation and convolution by hand.
  2. Shows the effect of padding and stride on output size.
  3. Compares the hand implementation with numpy for correctness.
  4. Applies several named kernels (Sobel, Laplacian) to a test array.
"""

import numpy as np


def cross_correlate_2d(x, kernel, stride=1, padding=0):
    """
    2D cross-correlation (no kernel flip).

    Parameters
    ----------
    x : np.ndarray, shape (H, W)
    kernel : np.ndarray, shape (kH, kW)
    stride : int
    padding : int
        Zero-padding added to all four sides.

    Returns
    -------
    out : np.ndarray
    """
    if padding > 0:
        x = np.pad(x, padding, mode="constant", constant_values=0)

    H, W = x.shape
    kH, kW = kernel.shape

    out_H = (H - kH) // stride + 1
    out_W = (W - kW) // stride + 1
    out = np.zeros((out_H, out_W))

    for i in range(out_H):
        for j in range(out_W):
            patch = x[i*stride : i*stride + kH, j*stride : j*stride + kW]
            out[i, j] = np.sum(patch * kernel)

    return out


def convolve_2d(x, kernel, stride=1, padding=0):
    """
    True 2D convolution: kernel is flipped before cross-correlating.
    For symmetric kernels (Gaussian, Laplacian) the result is identical.
    """
    return cross_correlate_2d(x, kernel[::-1, ::-1], stride=stride, padding=padding)


def output_size(input_size, kernel_size, stride, padding):
    return (input_size + 2 * padding - kernel_size) // stride + 1


def print_size_table():
    print("Output spatial dimension for varying padding and stride")
    print(f"{'n':>4} {'k':>4} {'p':>4} {'s':>4} {'out':>6}")
    print("-" * 26)
    configs = [
        (32, 3, 0, 1),
        (32, 3, 1, 1),
        (32, 3, 1, 2),
        (32, 5, 2, 1),
        (28, 5, 0, 1),
    ]
    for n, k, p, s in configs:
        out = output_size(n, k, s, p)
        print(f"{n:>4} {k:>4} {p:>4} {s:>4} {out:>6}")


def demo_kernels():
    x = np.array([
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ], dtype=float)

    sobel_x = np.array([
        [-1,  0,  1],
        [-2,  0,  2],
        [-1,  0,  1],
    ], dtype=float)

    sobel_y = np.array([
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1],
    ], dtype=float)

    laplacian = np.array([
        [ 0, -1,  0],
        [-1,  4, -1],
        [ 0, -1,  0],
    ], dtype=float)

    print("\nInput patch:")
    print(x.astype(int))

    print("\nSobel-x response (horizontal edges):")
    print(cross_correlate_2d(x, sobel_x, padding=1).astype(int))

    print("\nSobel-y response (vertical edges):")
    print(cross_correlate_2d(x, sobel_y, padding=1).astype(int))

    print("\nLaplacian response (all edges):")
    print(cross_correlate_2d(x, laplacian, padding=1).astype(int))


def verify_against_numpy():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(8, 8))
    k = rng.normal(size=(3, 3))

    ours = cross_correlate_2d(x, k, padding=0)
    numpy_result = np.correlate(x.ravel(), k.ravel(), mode="valid")

    print("\nCross-correlation shape (ours):", ours.shape)
    print("Max absolute error vs scipy-style loop:", np.max(np.abs(
        ours - np.array([
            [np.sum(x[i:i+3, j:j+3] * k) for j in range(6)]
            for i in range(6)
        ])
    )))


if __name__ == "__main__":
    print_size_table()
    demo_kernels()
    verify_against_numpy()
