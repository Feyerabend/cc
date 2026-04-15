import numpy as np
from scipy.ndimage import convolve, gaussian_filter
from scipy.datasets import ascent
import matplotlib.pyplot as plt


# Kernel Library

KERNELS = {
    "box_blur_3":      np.ones((3, 3)) / 9,
    "box_blur_5":      np.ones((5, 5)) / 25,

    "sharpen":         np.array([[ 0, -1,  0],
                                 [-1,  5, -1],
                                 [ 0, -1,  0]], dtype=float),

    "edge_laplacian":  np.array([[ 0,  1,  0],
                                 [ 1, -4,  1],
                                 [ 0,  1,  0]], dtype=float),

    "edge_laplacian8": np.array([[ 1,  1,  1],
                                 [ 1, -8,  1],
                                 [ 1,  1,  1]], dtype=float),

    "emboss":          np.array([[-2, -1,  0],
                                 [-1,  1,  1],
                                 [ 0,  1,  2]], dtype=float),

    "sobel_x":         np.array([[-1,  0,  1],
                                 [-2,  0,  2],
                                 [-1,  0,  1]], dtype=float),

    "sobel_y":         np.array([[-1, -2, -1],
                                 [ 0,  0,  0],
                                 [ 1,  2,  1]], dtype=float),
}


# Filter Functions

def apply_kernel(image: np.ndarray, kernel_name: str) -> np.ndarray:
    """Apply a named kernel from the KERNELS dict to a greyscale image."""
    if kernel_name not in KERNELS:
        raise ValueError(f"Unknown kernel '{kernel_name}'. " f"Available: {list(KERNELS)}")
    return convolve(image.astype(float), KERNELS[kernel_name])


def apply_gaussian(image: np.ndarray, sigma: float = 2.0) -> np.ndarray:
    return gaussian_filter(image.astype(float), sigma=sigma)


def edge_magnitude(image: np.ndarray) -> np.ndarray:
    """Sobel edge magnitude = sqrt(Gx^2 + Gy^2)."""
    gx = apply_kernel(image, "sobel_x")
    gy = apply_kernel(image, "sobel_y")
    return np.hypot(gx, gy)


def normalise_u8(img: np.ndarray) -> np.ndarray:
    lo, hi = img.min(), img.max()
    if hi == lo:
        return np.zeros_like(img, dtype=np.uint8)
    return ((img - lo) / (hi - lo) * 255).astype(np.uint8)


# Demo

def toolkit_demo():
    image = ascent().astype(float)

    ops = [
        ("Original",           image),
        ("Gaussian sigma=2",   apply_gaussian(image, 2.0)),
        ("Gaussian sigma=5",   apply_gaussian(image, 5.0)),
        ("Sharpen",            apply_kernel(image, "sharpen")),
        ("Edge (Laplacian)",   apply_kernel(image, "edge_laplacian")),
        ("Edge (Laplacian 8)", apply_kernel(image, "edge_laplacian8")),
        ("Edge magnitude",     edge_magnitude(image)),
        ("Emboss",             apply_kernel(image, "emboss")),
    ]

    cols = 4
    rows = (len(ops) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(16, rows * 4))

    for ax, (title, img) in zip(axes.flat, ops):
        ax.imshow(normalise_u8(img), cmap='gray', interpolation='nearest')
        ax.set_title(title, fontsize=10)
        ax.axis('off')

    for ax in axes.flat[len(ops):]:
        ax.axis('off')

    plt.suptitle('Image Filter Toolkit', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('image_filter_toolkit.png', dpi=150)
    plt.show()


toolkit_demo()
