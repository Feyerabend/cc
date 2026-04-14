import numpy as np
import matplotlib.pyplot as plt


def convolve_1d(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    """
    1-D linear convolution using the direct (sliding-window) method.
    Output length: len(x) + len(h) - 1.
    """
    N, M = len(x), len(h)
    out_len = N + M - 1
    y = np.zeros(out_len)
    for n in range(out_len):
        for k in range(M):
            if 0 <= n - k < N:
                y[n] += h[k] * x[n - k]
    return y


# Test: convolve a pulse signal with a simple 5-tap averaging kernel
x = np.zeros(40)
x[10:20] = 1.0 # rectangular pulse

h = np.ones(5) / 5 # moving-average (low-pass) kernel

y_manual = convolve_1d(x, h)
y_numpy = np.convolve(x, h) # reference

print("Manual vs NumPy match:", np.allclose(y_manual, y_numpy))

plt.figure(figsize=(10, 4))
plt.plot(x, label='Input pulse')
plt.plot(y_numpy, label='After 5-tap average (convolved)')
plt.legend(); plt.grid(alpha=0.3)
plt.title('Convolution: rectangular pulse + moving-average kernel')
plt.tight_layout()
plt.savefig('convolution_demo.png', dpi=150)
plt.show()
