import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, tf2zpk


def plot_pole_zero(b, a, title='Pole-Zero Plot'):
    z, p, k = tf2zpk(b, a)
    theta = np.linspace(0, 2 * np.pi, 300)

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(np.cos(theta), np.sin(theta), 'k--', linewidth=0.8, label='Unit circle')
    ax.axhline(0, color='k', linewidth=0.5)
    ax.axvline(0, color='k', linewidth=0.5)

    ax.scatter(z.real, z.imag, s=80, marker='o', facecolors='none', edgecolors='C0', linewidths=2, label='Zeros')
    ax.scatter(p.real, p.imag, s=80, marker='x', color='C1', linewidths=2, label='Poles')

    max_r = max(1.1, np.max(np.abs(np.concatenate([z, p]))) * 1.1)
    ax.set(xlim=[-max_r, max_r], ylim=[-max_r, max_r], xlabel='Re(z)', ylabel='Im(z)', title=title, aspect='equal')
    ax.legend(loc='upper right'); ax.grid(alpha=0.3)
    plt.tight_layout()


# 4th-order Butterworth low-pass at 200 Hz / 1000 Hz
b, a = butter(4, 200 / 500, btype='low')
plot_pole_zero(b, a, title='4th-order Butterworth LPF--all poles inside unit circle')
plt.savefig('pole_zero.png', dpi=150)
plt.show()

# Stability check
z_all, p_all, _ = tf2zpk(b, a)
stable = np.all(np.abs(p_all) < 1.0)
print(f"Filter stable: {stable}  (max pole magnitude: {np.max(np.abs(p_all)):.4f})")
