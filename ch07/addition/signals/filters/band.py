import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfilt

fs     = 1000.0
f_low  = 20.0 # Hz--lower cutoff
f_high = 80.0 # Hz--upper cutoff
order  = 4

sos = butter(order, [f_low / (fs / 2), f_high / (fs / 2)], btype='band', output='sos')

# Signal: 10 Hz (below band) + 50 Hz (in band) + 150 Hz (above band)
t = np.arange(0, 1, 1 / fs)
x = (np.sin(2 * np.pi *  10 * t) +
     np.sin(2 * np.pi *  50 * t) +
     np.sin(2 * np.pi * 150 * t))
y = sosfilt(sos, x)

fig, axes = plt.subplots(2, 1, figsize=(10, 6))
axes[0].plot(t[:300], x[:300], label='Input: 10 + 50 + 150 Hz')
axes[0].plot(t[:300], y[:300], linewidth=2, label=f'Band-pass [{f_low}-{f_high} Hz] -> 50 Hz only')
axes[0].legend(); axes[0].grid(alpha=0.3)
axes[0].set_title('Band-Pass Filter')

# Show spectra
def spectrum(sig, fs):
    X = np.fft.rfft(sig)
    m = np.abs(X) * 2 / len(sig)
    f = np.fft.rfftfreq(len(sig), 1 / fs)
    return f, m

fx, mx = spectrum(x, fs)
fy, my = spectrum(y, fs)
axes[1].plot(fx, mx, alpha=0.5, label='Input spectrum')
axes[1].plot(fy, my, linewidth=2, label='Filtered spectrum')
axes[1].axvspan(f_low, f_high, alpha=0.1, color='green', label='Pass band')
axes[1].set(xlim=[0, 200], xlabel='Frequency (Hz)', ylabel='Amplitude')
axes[1].legend(); axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('bpf_demo.png', dpi=150)
plt.show()