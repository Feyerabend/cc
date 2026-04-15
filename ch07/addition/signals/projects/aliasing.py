import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def alias_frequency(f_signal: float, fs: float) -> float:
    """
    Compute the aliased frequency that appears when sampling f_signal at fs.
    Uses the formula: f_alias = |f_signal - round(f_signal/fs) * fs|
    """
    k = round(f_signal / fs)
    return abs(f_signal - k * fs)


def demo_aliasing(f_sig=17.0, rates=(100, 25, 14), duration=0.5):
    t_dense = np.linspace(0, duration, 5000)
    x_cont  = np.sin(2 * np.pi * f_sig * t_dense)

    fig = plt.figure(figsize=(14, 9))
    fig.suptitle(f'Aliasing Demonstration--Signal frequency: {f_sig} Hz', fontsize=14, fontweight='bold')
    gs = GridSpec(len(rates), 2, figure=fig, width_ratios=[2, 1])

    for row, fs in enumerate(rates):
        t_s  = np.arange(0, duration, 1 / fs)
        x_s  = np.sin(2 * np.pi * f_sig * t_s)
        nyq  = fs / 2
        ok   = f_sig <= nyq
        f_al = alias_frequency(f_sig, fs) if not ok else None

        ax_t = fig.add_subplot(gs[row, 0])
        ax_f = fig.add_subplot(gs[row, 1])

        colour = '#2196F3' if ok else '#F44336'

        ax_t.plot(t_dense, x_cont, color='#ccc', linewidth=0.8, label=f'{f_sig} Hz (true)')
        sc = ax_t.stem(t_s, x_s, linefmt=colour, markerfmt='o', basefmt='k-')
        sc.markerline.set_color(colour)

        if not ok and f_al is not None:
            t_alias = np.linspace(0, duration, 2000)
            ax_t.plot(t_alias, np.sin(2 * np.pi * f_al * t_alias), '--', color=colour, alpha=0.6, label=f'Alias {f_al:.1f} Hz')

        status = 'OK' if ok else f'ALIASED -> {f_al:.1f} Hz'
        ax_t.set_title(f'fs = {fs} Hz (Nyquist = {nyq} Hz) -- {status}', color=colour)
        ax_t.legend(fontsize=8); ax_t.grid(alpha=0.2)
        ax_t.set_xlabel('Time (s)'); ax_t.set_ylabel('Amplitude')

        ## Frequency content of sampled signal
        N    = len(x_s)
        X    = np.abs(np.fft.rfft(x_s)) * 2 / N
        f_ax = np.fft.rfftfreq(N, 1 / fs)
        sc2 = ax_f.stem(f_ax, X, linefmt=colour, markerfmt='o', basefmt='k-')
        sc2.markerline.set_color(colour)
        ax_f.set(title='Spectrum', xlabel='Hz', ylabel='Amp', xlim=[0, nyq + 2])
        ax_f.grid(alpha=0.2)

    plt.tight_layout()
    plt.savefig('aliasing_full_demo.png', dpi=150)
    plt.show()

    print("\nAlias frequency table:")
    print(f"{'f_signal':>10}  {'fs':>8}  {'Nyquist':>8}  {'f_alias':>10}  {'Status':>8}")
    for fs in rates:
        f_al = alias_frequency(f_sig, fs)
        ok   = f_sig <= fs / 2
        print(f"{f_sig:>10.1f}  {fs:>8}  {fs/2:>8.1f}  {f_al:>10.1f}  "
              f"{'OK' if ok else 'ALIASED':>8}")


demo_aliasing()
