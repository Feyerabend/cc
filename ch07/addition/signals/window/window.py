import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import get_window

fs = 1000
N = 256
t = np.arange(N) / fs

# Non-integer frequency: leakage occurs
f = 50.3  # Hz--does NOT fit exactly in N samples

x_rect = np.sin(2 * np.pi * f * t) # rectangular window (= no window)
x_hann = x_rect * np.hanning(N)
x_blac = x_rect * get_window('blackman', N)

def db_spectrum(x):
    X = np.fft.rfft(x)
    return 20 * np.log10(np.abs(X) / np.max(np.abs(X)) + 1e-12)

freq = np.fft.rfftfreq(N, 1 / fs)

plt.figure(figsize=(10, 5))
plt.plot(freq, db_spectrum(x_rect), alpha=0.8, label='Rectangular (no window)')
plt.plot(freq, db_spectrum(x_hann), alpha=0.8, label='Hann window')
plt.plot(freq, db_spectrum(x_blac), alpha=0.8, label='Blackman window')
plt.axvline(f, color='k', linestyle=':', label=f'True frequency ({f} Hz)')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude (dB, normalised)')
plt.title(f'Spectral leakage comparison--signal at {f} Hz (non-integer bin)')
plt.xlim(20, 100); plt.ylim(-80, 5)
plt.legend(); plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('windowing.png', dpi=150)
plt.show()
