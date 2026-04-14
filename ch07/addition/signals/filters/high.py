import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfilt

fs = 1000.0
f_cut = 30.0
order = 4

sos = butter(order, f_cut / (fs / 2), btype='high', output='sos')

# Test signal: slow drift (5 Hz) + sharp event
t = np.arange(0, 2, 1 / fs)
drift  = np.sin(2 * np.pi * 2 * t) # 2 Hz baseline drift
event  = np.zeros_like(t)
event[600:620] = 1.0  # short transient event
x = drift + event + 0.05 * np.random.randn(len(t))

y = sosfilt(sos, x)

plt.figure(figsize=(10, 5))
plt.subplot(2, 1, 1)
plt.plot(t, x, label='Input (drift + event + noise)')
plt.legend(); plt.grid(alpha=0.3)

plt.subplot(2, 1, 2)
plt.plot(t, y, color='C1', label='High-pass output--drift removed, event preserved')
plt.legend(); plt.grid(alpha=0.3)
plt.xlabel('Time (s)')
plt.tight_layout()
plt.savefig('hpf_demo.png', dpi=150)
plt.show()

# --- 1-D edge detection kernel (discrete derivative) ---
x_step = np.zeros(50)
x_step[20:] = 1.0 # step edge
h_edge = np.array([-1, 0, 1]) # first-difference kernel
edge_response = np.convolve(x_step, h_edge, mode='same')

plt.figure(figsize=(8, 3))
plt.plot(x_step, label='Step signal')
plt.plot(edge_response, label='Edge response (HPF kernel [-1,0,1])')
plt.legend(); plt.grid(alpha=0.3)
plt.title('High-pass filtering as edge detection')
plt.tight_layout()
plt.savefig('edge_detection.png', dpi=150)
plt.show()
