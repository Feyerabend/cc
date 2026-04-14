import numpy as np
import matplotlib.pyplot as plt
import time


def dft_slow(x: np.ndarray) -> np.ndarray:
    N = len(x)
    n = np.arange(N)
    k = n.reshape((N, 1))
    return np.dot(np.exp(-2j * np.pi * k * n / N), x)


def benchmark(sizes):
    print(f"{'N':>8}  {'DFT (ms)':>10}  {'FFT (ms)':>10}  {'Speedup':>8}")
    print("-" * 44)
    for N in sizes:
        x = np.random.randn(N)

        t0 = time.perf_counter()
        dft_slow(x)
        t_dft = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        np.fft.fft(x)
        t_fft = (time.perf_counter() - t0) * 1000

        speedup = t_dft / t_fft if t_fft > 0 else float('inf')
        print(f"{N:>8}  {t_dft:>10.2f}  {t_fft:>10.3f}  {speedup:>7.0f}x")


benchmark([64, 256, 512, 1024])

# -- Practical FFT usage --
fs = 1000                   ## Hz
duration = 1.0              ## seconds
t  = np.linspace(0, duration, int(fs * duration), endpoint=False)

# Signal with two components at 50 Hz and 150 Hz
x = (1.0 * np.sin(2 * np.pi *  50 * t) +
     0.4 * np.sin(2 * np.pi * 150 * t))

X   = np.fft.rfft(x)       ## rfft: only positive frequencies for real input
mag = np.abs(X) / len(x)
mag[1:-1] *= 2              ## double for single-sided spectrum (except DC)
freqs = np.fft.rfftfreq(len(x), d=1 / fs)

plt.figure(figsize=(10, 4))
plt.plot(freqs, mag)
plt.xlabel('Frequency (Hz)')
plt.ylabel('Amplitude')
plt.title('FFT Spectrum--peaks at 50 Hz (amp=1.0) and 150 Hz (amp=0.4)')
plt.xlim(0, 300)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('fft_spectrum.png', dpi=150)
plt.show()
