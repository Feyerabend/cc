# aliasing demonstration
import numpy as np
import matplotlib.pyplot as plt

## --- Parameters ---
f_signal = 5        # Hz: true signal frequency
fs_good  = 100      # Hz: well above Nyquist (2 * 5 = 10 Hz)
fs_alias = 8        # Hz: below Nyquist -> aliasing

t_cont = np.linspace(0, 1, 2000)  # dense "continuous" reference
x_cont = np.sin(2 * np.pi * f_signal * t_cont)

t_good  = np.arange(0, 1, 1 / fs_good)
x_good  = np.sin(2 * np.pi * f_signal * t_good)

t_alias = np.arange(0, 1, 1 / fs_alias)
x_alias = np.sin(2 * np.pi * f_signal * t_alias)

# --- Plot ---
fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

axes[0].plot(t_cont, x_cont, 'lightgray', label='Continuous (5 Hz)')
axes[0].stem(t_good, x_good, linefmt='C0-', markerfmt='C0o', basefmt='k-', label=f'Sampled at {fs_good} Hz (good)')
axes[0].set_title('Adequate sampling--signal recovered correctly')
axes[0].legend()

axes[1].plot(t_cont, x_cont, 'lightgray', label='Continuous (5 Hz)')
axes[1].stem(t_alias, x_alias, linefmt='C1-', markerfmt='C1o', basefmt='k-', label=f'Sampled at {fs_alias} Hz (aliased)')

# Show the aliased frequency: |f_signal - fs_alias| = 3 Hz
f_alias = abs(f_signal - fs_alias)
axes[1].plot(t_cont, np.sin(2 * np.pi * f_alias * t_cont), 'C1--', alpha=0.6, label=f'Aliased component ({f_alias} Hz)')
axes[1].set_title('Under-sampling--aliasing produces phantom 3 Hz component')
axes[1].legend()

plt.xlabel('Time (s)')
plt.tight_layout()
plt.savefig('aliasing_demo.png', dpi=150)
plt.show()
