import numpy as np
import matplotlib.pyplot as plt


def make_signal(frequencies, amplitudes, phases, fs=1000, duration=1.0):
    """
    Construct a signal by summing sinusoids.

    Parameters
    ----------
    frequencies : list of float  --component frequencies (Hz)
    amplitudes  : list of float  --component amplitudes
    phases      : list of float  --component phases (radians)
    fs          : int            --sampling rate (Hz)
    duration    : float          --signal duration (seconds)

    Returns
    -------
    t : time axis
    x : signal values
    """
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    x = np.zeros_like(t)
    for f, A, phi in zip(frequencies, amplitudes, phases):
        x += A * np.sin(2 * np.pi * f * t + phi)
    return t, x


## --- Example: harmonic series (musical-like) ---
freqs = [100, 200, 300, 400, 500]       # fundamental + 4 harmonics
amps  = [1.0, 0.7, 0.5, 0.3, 0.2]       # decaying amplitudes
phase = [0.0, 0.1, 0.3, 0.0, 0.5]

t, x = make_signal(freqs, amps, phase, fs=2000, duration=0.05)

fig, axes = plt.subplots(2, 1, figsize=(10, 7))
axes[0].plot(t * 1000, x)
axes[0].set(title='Harmonic signal (100 Hz fundamental + overtones)', xlabel='Time (ms)', ylabel='Amplitude')
axes[0].grid(alpha=0.3)

# Spectrum
X     = np.fft.rfft(x)
mag   = np.abs(X) * 2 / len(x)
f_ax  = np.fft.rfftfreq(len(x), 1 / 2000)
axes[1].stem(f_ax, mag, linefmt='C0-', markerfmt='C0o', basefmt='k-')
axes[1].set(title='Spectrum--peaks at harmonics', xlabel='Frequency (Hz)', ylabel='Amplitude', xlim=[0, 700])
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('signal_generation.png', dpi=150)
plt.show()

# --- Noise: adding Gaussian noise to a signal ---
t2, clean = make_signal([50], [1.0], [0.0], fs=1000, duration=1.0)
noisy = clean + 0.5 * np.random.randn(len(clean))

plt.figure(figsize=(10, 3))
plt.plot(t2[:200], noisy[:200], alpha=0.6, label='Noisy')
plt.plot(t2[:200], clean[:200], linewidth=2, label='Clean')
plt.legend(); plt.grid(alpha=0.3)
plt.title('Clean vs noisy signal')
plt.tight_layout()
plt.savefig('noisy_signal.png', dpi=150)
plt.show()
