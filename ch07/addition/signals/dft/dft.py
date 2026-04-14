import numpy as np
import matplotlib.pyplot as plt


def dft(x: np.ndarray) -> np.ndarray:
    """Compute the DFT of a 1-D sequence using the naive O(N^2) algorithm."""
    N = len(x)
    X = np.zeros(N, dtype=complex)
    for k in range(N):
        for n in range(N):
            X[k] += x[n] * np.exp(-2j * np.pi * k * n / N)
    return X


# Generate a test signal: 3 Hz + 7 Hz at fs = 50 Hz, 1 second
fs = 50
N = fs      # 1 second -> 50 samples
t = np.arange(N) / fs
x = np.sin(2 * np.pi * 3 * t) + 0.5 * np.sin(2 * np.pi * 7 * t)

X   = dft(x)
mag = np.abs(X) / N  # normalise by N

# Only the first N//2 bins are meaningful (positive frequencies)
freqs = np.arange(N // 2) * fs / N

fig, axes = plt.subplots(2, 1, figsize=(10, 6))
axes[0].plot(t, x)
axes[0].set(title='Time domain', xlabel='Time (s)', ylabel='Amplitude')

axes[1].stem(freqs, 2 * mag[:N // 2],     # x2 for single-sided spectrum
             linefmt='C0-', markerfmt='C0o', basefmt='k-')
axes[1].set(title='Frequency domain (DFT)', xlabel='Frequency (Hz)', ylabel='Amplitude', xlim=[0, fs / 2])

plt.tight_layout()
plt.savefig('dft_demo.png', dpi=150)
plt.show()
