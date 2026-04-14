import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import convolve
from scipy.datasets import ascent   # built-in greyscale test image


def normalise(img: np.ndarray) -> np.ndarray:
    """Scale image to [0, 255] for display."""
    lo, hi = img.min(), img.max()
    return ((img - lo) / (hi - lo) * 255).astype(np.uint8)


# Load test image
image = ascent().astype(np.float32)     # 512 x 512 greyscale

# --- Kernels ---

# 1. Gaussian blur (5x5)
sigma = 1.0
ax    = np.arange(-2, 3)
gauss = np.exp(-ax * 2 / (2 * sigma * 2))
K_blur = np.outer(gauss, gauss)
K_blur /= K_blur.sum()

# 2. Unsharp masking kernel (sharpening = original + (original - blur))
K_sharpen = -K_blur.copy()
K_sharpen[2, 2] += 2.0                  # add 2x original at centre

# 3. Sobel edge detector (horizontal gradient)
K_sobel_x = np.array([[-1, 0, 1],
                      [-2, 0, 2],
                      [-1, 0, 1]], dtype=np.float32)

K_sobel_y = K_sobel_x.T

# --- Apply ---
blurred   = convolve(image, K_blur)
sharpened = convolve(image, K_sharpen)
grad_x    = convolve(image, K_sobel_x)
grad_y    = convolve(image, K_sobel_y)
edges     = np.hypot(grad_x, grad_y)    # gradient magnitude

# --- Display ---
fig, axes = plt.subplots(2, 3, figsize=(14, 9))
titles  = ['Original', 'Gaussian blur', 'Sharpened',
           'Sobel X', 'Sobel Y', 'Edge magnitude']
images  = [image, blurred, sharpened, grad_x, grad_y, edges]

for ax, img, title in zip(axes.flat, images, titles):
    ax.imshow(normalise(img), cmap='gray', interpolation='nearest')
    ax.set_title(title)
    ax.axis('off')

plt.suptitle('2-D Image Filtering with Convolution Kernels', fontsize=14)
plt.tight_layout()
plt.savefig('image_processing.png', dpi=150)
plt.show()
