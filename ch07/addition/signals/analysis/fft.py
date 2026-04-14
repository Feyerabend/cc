import numpy as np
import matplotlib.pyplot as plt


def plot_spectrum(x, fs, title='Spectrum', xlim=None):
    """
    Plot the single-sided amplitude spectrum of signal x sampled at fs Hz.
    Returns (freqs, magnitudes).
    """
    N = len(x)
    X = np.fft.rfft(x)
    mag = np.abs(X) / N
    mag[1:-1] *= 2  # double for single-sided
    freq = np.fft.rfftfreq(N, 1 / fs)

    plt.figure(figsize=(10, 4))
    plt.plot(freq, mag)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Amplitude')
    plt.title(title)
    if xlim:
        plt.xlim(xlim)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    return freq, mag


fs = 2000
t = np.arange(0, 1, 1 / fs)

# Construct a signal with known components plus noise
x  = (1.0 * np.sin(2 * np.pi * 100 * t) +
      0.5 * np.sin(2 * np.pi * 250 * t) +
      0.3 * np.sin(2 * np.pi * 400 * t) +
      0.2 * np.random.randn(len(t))) # broadband noise

freq, mag = plot_spectrum(x, fs,
    title='Spectrum: three tones (100, 250, 400 Hz) in broadband noise',
    xlim=(0, 600))

# Identify peak frequencies programmatically
from scipy.signal import find_peaks
peaks, props = find_peaks(mag, height=0.05, distance=20)
print("Detected peaks:")
for p in peaks:
    print(f"  f = {freq[p]:.1f} Hz,  amplitude ≈ {mag[p]:.3f}")

plt.scatter(freq[peaks], mag[peaks], color='red', zorder=5, label='Detected peaks')
plt.legend()
plt.savefig('spectrum_analysis.png', dpi=150)
plt.show()
