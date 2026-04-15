import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import firwin, butter, freqz, sosfilt, lfilter

fs = 1000.0
f_c = 100.0         # cutoff (Hz)
norm = f_c / (fs / 2)

# Design IIR: 4th-order Butterworth
b_iir, a_iir = butter(4, norm, btype='low')

# Design FIR: windowed sinc (Parks-McClellan / firwin), same cutoff
# Comparable sharpness to IIR order 4 requires many more taps
n_taps_list = [15, 51, 101]

w, H_iir = freqz(b_iir, a_iir, worN=2048)
freq = w * fs / (2 * np.pi)

plt.figure(figsize=(10, 5))
plt.plot(freq, 20 * np.log10(np.abs(H_iir) + 1e-12), linewidth=2, label='IIR Butterworth (order 4)')

for n in n_taps_list:
    b_fir = firwin(n, norm, window='hann')
    w2, H_fir = freqz(b_fir, 1, worN=2048)
    plt.plot(freq, 20 * np.log10(np.abs(H_fir) + 1e-12), linestyle='--', label=f'FIR Hann window ({n} taps)')

plt.axvline(f_c, color='k', linestyle=':', alpha=0.5, label=f'Cutoff {f_c} Hz')
plt.axhline(-3,  color='k', linestyle=':', alpha=0.3, label='-3 dB')
plt.xlabel('Frequency (Hz)'); plt.ylabel('Gain (dB)')
plt.title('FIR vs IIR: frequency response comparison')
plt.xlim(0, 400); plt.ylim(-80, 5)
plt.legend(fontsize=8); plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('fir_vs_iir.png', dpi=150)
plt.show()

# --- Phase comparison ---
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
_, H_iir_p = freqz(b_iir, a_iir, worN=2048)
axes[0].plot(freq, np.unwrap(np.angle(H_iir_p)) * 180 / np.pi)
axes[0].set(title='IIR Butterworth--non-linear phase', xlabel='Frequency (Hz)', ylabel='Phase (degrees)')
axes[0].grid(alpha=0.3)

b_fir51 = firwin(51, norm, window='hann')
_, H_fir_p = freqz(b_fir51, 1, worN=2048)
axes[1].plot(freq, np.unwrap(np.angle(H_fir_p)) * 180 / np.pi, color='C1')
axes[1].set(title='FIR (51 taps, Hann)--linear phase', xlabel='Frequency (Hz)', ylabel='Phase (degrees)')
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('fir_iir_phase.png', dpi=150)
plt.show()
