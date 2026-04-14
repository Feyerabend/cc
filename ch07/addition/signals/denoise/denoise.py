import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import butter, sosfilt


def load_audio(path: str):
    """Load a WAV file. Returns (sample_rate, mono_float_array)."""
    sr, data = wavfile.read(path)
    # Convert to float in [-1, 1]
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float32) / 2147483648.0
    # Mix to mono if stereo
    if data.ndim == 2:
        data = data.mean(axis=1)
    return sr, data


def bandpass_audio(signal, sr, f_low=300, f_high=3400, order=5):
    """Telephone-band bandpass: 300 Hz - 3.4 kHz."""
    sos = butter(order, [f_low / (sr / 2), f_high / (sr / 2)], btype='band', output='sos')
    return sosfilt(sos, signal)


def spectral_subtract(signal, sr, noise_start=0.0, noise_end=0.3, frame_ms=25, hop_ms=10, alpha=2.0):
    """
    Simple spectral subtraction denoiser.

    noise_start / noise_end : time range (seconds) assumed to be noise-only.
                      alpha : over-subtraction factor (>1 more aggressive).
    """
    frame_len = int(frame_ms * sr / 1000)
    hop_len = int(hop_ms * sr / 1000)
    window = np.hanning(frame_len)

    # Estimate noise spectrum from the noise-only segment
    n0 = int(noise_start * sr)
    n1 = int(noise_end * sr)
    noise_seg = signal[n0:n1]
    noise_frames = []
    for start in range(0, len(noise_seg) - frame_len, hop_len):
        frame  = noise_seg[start:start + frame_len] * window
        noise_frames.append(np.abs(np.fft.rfft(frame)))
    noise_psd = np.mean(noise_frames, axis=0) * 2   ## average power spectrum

    # Process entire signal frame by frame
    output = np.zeros(len(signal))
    counts = np.zeros(len(signal))

    for start in range(0, len(signal) - frame_len, hop_len):
        frame = signal[start:start + frame_len] * window
        X = np.fft.rfft(frame)
        mag = np.abs(X)
        phase = np.angle(X)
        # Subtract noise
        mag_clean = np.maximum(mag * 2 - alpha * noise_psd, 0) * 0.5
        X_clean = mag_clean * np.exp(1j * phase)
        y_frame = np.fft.irfft(X_clean) * window
        output[start:start + frame_len] += y_frame
        counts[start:start + frame_len] += window

    # Normalise by overlap-add counts
    counts = np.where(counts < 1e-8, 1.0, counts)
    return output / counts


# ---- Usage example (requires an audio file) ----
# The Birth of the Telephone by Thomas Augustus Watson
# Public Domain (ca 1 min part): https://www.gutenberg.org/ebooks/10254
sr, audio = load_audio('noisy.wav') 
clean = spectral_subtract(audio, sr)
wavfile.write('clean.wav', sr, (clean * 32767).astype(np.int16))

# ---- Synthetic demo (no file needed) ----
sr = 16000
t = np.arange(0, 2.0, 1 / sr)
# "Speech": 200 Hz tone, starts at 0.3 s
speech = np.zeros_like(t)
speech[int(0.3 * sr):] = 0.8 * np.sin(2 * np.pi * 200 * t[:int(1.7 * sr)])
# Noise: broadband Gaussian
noise = 0.15 * np.random.randn(len(t))
noisy = speech + noise

denoised = spectral_subtract(noisy, sr, noise_start=0.0, noise_end=0.28)

fig, axes = plt.subplots(3, 1, figsize=(12, 7), sharex=True)
axes[0].plot(t, noisy, alpha=0.7); axes[0].set_title('Noisy signal')
axes[1].plot(t, speech, alpha=0.9); axes[1].set_title('Clean reference')
axes[2].plot(t, denoised, alpha=0.9, color='C2')
axes[2].set_title('After spectral subtraction')
plt.xlabel('Time (s)')
plt.tight_layout()
plt.savefig('audio_denoising.png', dpi=150)
plt.show()
