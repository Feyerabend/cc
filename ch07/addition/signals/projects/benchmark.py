import numpy as np
import time
import matplotlib.pyplot as plt


def dft_naive(x: np.ndarray) -> np.ndarray:
    """O(N^2) DFT--vectorised with NumPy broadcasting."""
    N = len(x)
    n = np.arange(N)
    k = n.reshape((N, 1))
    return np.dot(np.exp(-2j * np.pi * k * n / N), x)


def measure(func, x, repeats=3):
    """Return the minimum wall-clock time (seconds) over several repeats."""
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        func(x)
        times.append(time.perf_counter() - t0)
    return min(times)


sizes = [8, 16, 32, 64, 128, 256, 512, 1024]   # keep small: DFT is slow

t_dft = []
t_fft = []

print(f"{'N':>6}  {'DFT (ms)':>10}  {'FFT (ms)':>10}  {'Speedup':>8}")
print("-" * 42)

for N in sizes:
    x = np.random.randn(N)
    td = measure(dft_naive, x, repeats=5) * 1000
    tf = measure(np.fft.fft,  x, repeats=5) * 1000
    t_dft.append(td)
    t_fft.append(tf)
    print(f"{N:>6}  {td:>10.3f}  {tf:>10.4f}  {td/tf:>7.0f}x")

## Theoretical curves (scaled to match measurements)
n_arr = np.array(sizes, dtype=float)
scale_dft = t_dft[-1] / (sizes[-1] * 2)
scale_fft = t_fft[-1] / (sizes[-1] * np.log2(sizes[-1]))
theory_dft = scale_dft * n_arr * 2
theory_fft = scale_fft * n_arr * np.log2(n_arr)

fig, ax = plt.subplots(figsize=(9, 5))
ax.loglog(sizes, t_dft,     'C0o-', linewidth=2, label='Naive DFT (measured)')
ax.loglog(sizes, t_fft,     'C1s-', linewidth=2, label='NumPy FFT (measured)')
ax.loglog(sizes, theory_dft,'C0--', linewidth=1, alpha=0.5, label='O(N^2) theory')
ax.loglog(sizes, theory_fft,'C1--', linewidth=1, alpha=0.5, label='O(N log N) theory')

ax.set(xlabel='Signal length N', ylabel='Time (ms)',
       title='DFT vs FFT: measured runtime vs theoretical complexity')
ax.legend(); ax.grid(True, which='both', alpha=0.3)
plt.tight_layout()
plt.savefig('fft_benchmark.png', dpi=150)
plt.show()
