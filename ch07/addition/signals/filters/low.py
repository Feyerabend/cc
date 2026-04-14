import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfilt, freqz

## --- Design a 4th-order Butterworth low-pass filter ---
fs     = 1000.0    ## sampling rate (Hz)
f_cut  = 50.0      ## cutoff frequency (Hz)
order  = 4

## Normalised cutoff: f_cut / (fs/2)
sos = butter(order, f_cut / (fs / 2), btype='low', output='sos')

## --- Frequency response ---
w, h = freqz(butter(order, f_cut / (fs / 2), btype='low', output='ba')[1],
             butter(order, f_cut / (fs / 2), btype='low', output='ba')[0],
             worN=2048)
freq_hz = w * (fs / 2) / np.pi

## --- Test signal: 20 Hz tone + 200 Hz noise ---
t = np.arange(0, 1, 1 / fs)
x = np.sin(2 * np.pi * 20 * t) + 0.8 * np.sin(2 * np.pi * 200 * t)
y = sosfilt(sos, x)

fig, axes = plt.subplots(2, 1, figsize=(10, 7))

axes[0].plot(t[:200], x[:200], alpha=0.7, label='Input (20 Hz + 200 Hz)')
axes[0].plot(t[:200], y[:200], linewidth=2,  label='Low-pass output (50 Hz cutoff)')
axes[0].set(title='Low-Pass Filter--Time Domain', xlabel='Time (s)')
axes[0].legend(); axes[0].grid(alpha=0.3)

axes[1].semilogx(freq_hz, 20 * np.log10(np.abs(h) + 1e-12))
axes[1].axvline(f_cut, color='r', linestyle='--', label=f'Cutoff = {f_cut} Hz')
axes[1].set(title='Frequency Response', xlabel='Frequency (Hz)',
            ylabel='Gain (dB)', xlim=[1, fs / 2], ylim=[-80, 5])
axes[1].legend(); axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('lpf_demo.png', dpi=150)
plt.show()
