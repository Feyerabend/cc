"""
feature_maps.py

Applies several handcrafted convolutional kernels to a synthetic image
and visualises the resulting feature maps.

Before deep learning, computer vision relied on filters like these.
A CNN's first layer learns filters that often resemble them: the network
discovers by gradient descent what engineers once designed by hand.

Kernels demonstrated:
  - Identity:       passes the image through unchanged
  - Sobel-x:        detects vertical edges (horizontal intensity gradient)
  - Sobel-y:        detects horizontal edges (vertical intensity gradient)
  - Gradient mag.:  sqrt(Sobel-x^2 + Sobel-y^2), all edges regardless of direction
  - Gaussian blur:  smooths the image, suppresses high-frequency noise
  - Laplacian:      second-order derivative, sharpens and detects all edges
  - Emboss:         gives a 3-D relief effect, directional edge + shading
"""

import numpy as np
import matplotlib.pyplot as plt


def cross_correlate_2d(x, kernel, padding=1):
    kH, kW = kernel.shape
    if padding > 0:
        x = np.pad(x, padding, mode="constant", constant_values=0)
    H, W = x.shape
    out_H = H - kH + 1
    out_W = W - kW + 1
    out = np.zeros((out_H, out_W))
    for i in range(out_H):
        for j in range(out_W):
            out[i, j] = np.sum(x[i : i + kH, j : j + kW] * kernel)
    return out


def make_synthetic_image(size=64):
    """
    Builds a 64x64 synthetic image with:
      - A bright rectangle in the upper-left quadrant
      - A circle in the lower-right quadrant
      - A diagonal stripe across the centre
    """
    img = np.zeros((size, size))

    img[8:28, 8:28] = 0.8

    cx, cy, r = 46, 46, 12
    ys, xs = np.ogrid[:size, :size]
    circle_mask = (xs - cx) ** 2 + (ys - cy) ** 2 <= r ** 2
    img[circle_mask] = 0.9

    for k in range(size):
        if 0 <= size // 2 - k < size and 0 <= k < size:
            img[size // 2 - k, k] = 0.6
            if k + 1 < size:
                img[size // 2 - k, k + 1] = 0.5

    img = np.clip(img + np.random.default_rng(7).normal(0, 0.04, img.shape), 0, 1)
    return img


def gaussian_kernel(size=5, sigma=1.0):
    ax = np.arange(-(size // 2), size // 2 + 1)
    xx, yy = np.meshgrid(ax, ax)
    k = np.exp(-(xx ** 2 + yy ** 2) / (2 * sigma ** 2))
    return k / k.sum()


def main():
    img = make_synthetic_image(64)

    identity = np.array([
        [0,  0, 0],
        [0,  1, 0],
        [0,  0, 0],
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

    emboss = np.array([
        [-2, -1,  0],
        [-1,  1,  1],
        [ 0,  1,  2],
    ], dtype=float)

    gauss = gaussian_kernel(size=5, sigma=1.0)

    fm_grad_mag  = np.sqrt(fm_sobel_x ** 2 + fm_sobel_y ** 2)
    fm_identity  = cross_correlate_2d(img, identity,   padding=1)
    fm_sobel_x   = cross_correlate_2d(img, sobel_x,    padding=1)
    fm_sobel_y   = cross_correlate_2d(img, sobel_y,    padding=1)
    fm_gauss     = cross_correlate_2d(img, gauss,      padding=2)
    fm_laplacian = cross_correlate_2d(img, laplacian,  padding=1)
    fm_emboss    = cross_correlate_2d(img, emboss,     padding=1)

    maps = [
        (img,          "Input image",                     "gray"),
        (fm_identity,  "Identity",                        "gray"),
        (fm_sobel_x,   "Sobel-x\n(vertical edges)",       "RdBu"),
        (fm_sobel_y,   "Sobel-y\n(horizontal edges)",     "RdBu"),
        (fm_grad_mag,  "Gradient magnitude\n(all edges)", "hot"),
        (fm_gauss,     "Gaussian blur\n(σ=1.0)",          "gray"),
        (fm_laplacian, "Laplacian\n(edge sharpening)",    "RdBu"),
        (fm_emboss,    "Emboss",                          "gray"),
    ]

    fig, axes = plt.subplots(2, 4, figsize=(14, 7))
    fig.suptitle("Feature Maps: Handcrafted Kernels Applied to a Synthetic Image",
                 fontsize=13)

    for ax, (fm, title, cmap) in zip(axes.flat, maps):
        vmax = np.percentile(np.abs(fm), 99)
        vmin = -vmax if cmap == "RdBu" else 0
        ax.imshow(fm, cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest")
        ax.set_title(title, fontsize=9)
        ax.axis("off")

    plt.tight_layout()
    plt.savefig("feature_maps.png", dpi=150, bbox_inches="tight")
    print("Saved feature_maps.png")
    plt.show()


if __name__ == "__main__":
    main()
