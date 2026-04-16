
## Signal Processing

> *About this additional section:* This section fills a gap in the main text by introducing
  the fundamentals of signal processing: what signals are, how they are sampled and represented
  digitally, how to analyse them in the frequency domain, and how to filter them.
  Each concept is paired with working code in Python, C, and (where applicable) JavaScript
  so you can experiment immediately.


### 1. Introduction

#### 1.1 What is a Signal?

A *signal* is any quantity that varies and carries information. The variation can be over time,
space, or any other independent variable; what matters is that a receiver can extract meaning
from the variation.

*Time-domain signals* change with time. A microphone converts air pressure variations into
a voltage that fluctuates thousands of times per second--that voltage waveform is a time-domain
signal. An electrocardiogram records the heart's electrical activity as a function of time.
A gyroscope in a phone reports angular velocity moment by moment.

*Spatial signals* vary across position rather than (or in addition to) time. A digital photograph
is a two-dimensional spatial signal: each pixel encodes light intensity (and colour) at a particular
$(x, y)$ location. A seismic survey maps reflected sound energy across a field of sensors buried
in the ground.

*Continuous signals* are defined at every instant, with no gaps. Mathematically we write $x(t)$
to mean the signal value at time $t$, where $t$ is a real number. Physical signals--sound, light,
temperature--are continuous.

*Discrete signals* are defined only at specific, regularly spaced instants. We write $x[n]$
to mean the value at sample index $n$, where $n$ is an integer. Every digital system works
with discrete signals: computers cannot store a value for every real-numbered instant,
only for a countably infinite (or finite) sequence of moments.

*Examples across domains:*

| Domain     | Signal                   | Independent variable |
|------------|--------------------------|----------------------|
| Audio      | Pressure wave / voltage  | Time                 |
| Image      | Pixel intensity          | Space `(x, y)`       |
| Radar      | Reflected pulse envelope | Time / range         |
| Finance    | Stock price              | Time                 |
| Biology    | Neuron firing rate       | Time                 |
| Geophysics | Seismic wave             | Space and time       |

The central task of signal processing is to extract useful information from these
varying quantities--removing noise, detecting patterns, compressing data, or
transforming representations so that downstream algorithms can work more easily.



#### 1.2 Why Signal Processing Matters

Signal processing underpins a surprisingly wide range of technologies.
Here are four areas where a working knowledge makes a real difference.

*Audio processing.* Every phone call, music stream, and voice assistant relies
on signal processing. Noise cancellation in headphones uses adaptive filters to
subtract an estimate of background noise from the microphone signal in real time.
MP3 and AAC compression apply psychoacoustic models that discard frequency content
the human ear cannot perceive, achieving 10:1 compression with minimal audible
loss. Speech recognition first converts audio to a spectrogram--a time-frequency
map--before feeding it to a neural network.

*Communications.* Amplitude modulation (AM), frequency modulation (FM), and modern
schemes like OFDM (used in Wi-Fi, 4G, and 5G) all work by shifting information-bearing
signals to carrier frequencies suitable for transmission. At the receiver, a matched
filter recovers the original signal from noise. Channel equalisation corrects for
the distortion introduced by the medium.

*Machine learning.* Raw signals are rarely fed directly to a classifier. A common
pre-processing pipeline converts a time-series into a frequency representation
(spectrogram or mel-frequency cepstral coefficients), applies normalisation, and
possibly applies a learned filter bank. Convolutional neural networks are themselves
a form of adaptive signal processing: their learnable kernels are filters optimised
for a particular task.

*Embedded systems.* Microcontrollers in industrial sensors, medical devices, and
consumer electronics all perform signal processing under tight constraints of memory
and compute budget. A digital filter that smooths a noisy ADC reading, a PID controller
that cancels vibration, an encoder that detects a zero crossing--these are signal
processing tasks executed in real time, often without an operating system,
in a few kilobytes of RAM.


### 2. Mathematical Foundations

#### 2.1 Continuous vs Discrete Signals

A continuous signal $x(t)$ assigns a real (or complex) number to every real-valued
time $t$. This is the natural model for physical phenomena. We can differentiate it,
integrate it, and reason about its behaviour at any instant.

A discrete signal $x[n]$ assigns a value only at integer indices $n ∈ ℤ$.
It arises whenever we *sample* a continuous signal--measuring its value
at regular intervals.

*Notation summary:*
- Continuous signal:  $x(t)$,   $t ∈ ℝ$
- Discrete signal:    $x[n]$,   $n ∈ ℤ$
- Sampling period:    $T$  (seconds between samples)
- Sampling rate:      $f_s = 1 / T$  (samples per second, Hz)


The relationship between the two is:
```math
x[n] = x(n · T) = x(n / f_s)
```

Each discrete sample is simply the continuous signal evaluated at time $t = nT$.

*Why discrete signals are necessary.* Storing a continuous signal requires infinite
precision and infinite storage--both impossible. Discrete sampling reduces the
representation to a finite (or countably infinite) sequence of numbers, which
computers can store, transmit, and process. The key question--addressed in the
next section--is how fast we must sample to avoid losing information.



#### 2.2 Sampling and the Nyquist-Shannon Theorem

The *Nyquist-Shannon sampling theorem* gives the minimum sampling rate required
to perfectly reconstruct a band-limited continuous signal from its discrete samples.

> A continuous signal whose highest frequency component is $$f_m$$ can be perfectly
> reconstructed from discrete samples taken at a rate $$f_s$$, provided: $f_s ≥ 2 · f_m$

The frequency $f_s / 2$ is called the *Nyquist frequency* (or folding frequency).
It is the highest frequency representable at a given sampling rate.

*Aliasing.* If the signal contains components above the Nyquist frequency and we
sample below $2 · f_m$, those high-frequency components are *folded* back into
the representable range and appear as phantom low-frequency components. This
phenomenon is called aliasing, and it is irreversible--once aliased, the original
high-frequency content cannot be recovered.

A classic visual example: a wheel spinning at 24 revolutions per second filmed at
24 frames per second appears stationary. The sampling rate (24 fps) equals the signal
frequency (24 Hz), which is exactly at the Nyquist limit for 12 Hz content--here the
rotation frequency exceeds it, causing the aliased "stationary" appearance.

*Anti-aliasing filters.* In practice, a low-pass filter is applied to the continuous
signal *before* sampling to remove any content above $f_s / 2$. This is called an
anti-aliasing filter, and it is present in every ADC (analogue-to-digital converter)
front end.

Formula:
```math
f_s >= 2 · f_m
```

*See the [sampling](./sampling/) folder.*


#### 2.3 Fourier Transform

The central insight of Fourier analysis is that *any* periodic signal--and,
with suitable extension, any signal with finite energy--can be expressed as
a sum of sinusoids[^sinusoids] of different frequencies, amplitudes, and
phases. This is not just a mathematical curiosity; it reveals which frequencies
are present in a signal and in what proportion, turning a time-domain waveform
into a *frequency-domain spectrum*.

[^sinusoids]: A sinusoid is a mathematical curve—specifically the sine $\sin$
or cosine $\cos$ function--that describes a continuous, smooth oscillation.
In signal processing, sinusoids are the fundamental "building blocks" of all
complex signals.

*Intuition.* Imagine a chord played on a piano. The pressure waveform at your
ear is a messy, oscillating curve. Yet your auditory system immediately resolves
it into individual notes--A, C, E--each at its own frequency and loudness.
Fourier analysis is the mathematical version of that decomposition: it asks,
"for each possible frequency $f$, how much of that frequency is present in
the signal?"

*The Fourier Transform* of a continuous signal $x(t)$ is defined as:

```math
X(f) = ∫_{-∞}^{+∞}  x(t) · e^{-i 2π f t}  dt
```

$X(f)$ is a complex-valued function of frequency. Its magnitude $|X(f)|$
is the *amplitude spectrum* (how strong each frequency is), and its argument
$∠X(f)$ is the *phase spectrum* (the phase offset of each sinusoidal component).

The *inverse Fourier Transform* recovers the time-domain signal:
```math
x(t) = ∫_{-∞}^{+∞}  X(f) · e^{+i 2π f t}  df
```

These two transforms form a perfect pair: going to the frequency domain
loses no information, and coming back gives back the original signal exactly.

*Key properties to know:*

| Property            | Statement                                                |
|---------------------|----------------------------------------------------------|
| Linearity           | $FT{a·x + b·y} = a·X + b·Y$                              |
| Time shift          | Shifting $x(t)$ by $τ$ multiplies $X(f)$ by $e^{-i2πfτ}$ |
| Convolution theorem | Convolution in time <--> multiplication in frequency     |
| Parseval's theorem  | Energy is preserved: $∫\|x\|² dt = ∫\|X\|² df$           |

The *convolution theorem* is particularly important for filtering: applying a filter
$h$ to a signal $x$ by convolution in the time domain is *equivalent* to multiplying
their Fourier transforms $H(f) · X(f)$ in the frequency domain.
This is why frequency-domain filtering is often computationally cheaper.


#### 2.4 Discrete Fourier Transform (DFT)

For a finite sequence of $N$ samples $x[0], x[1], ..., x[N-1]$, the
*Discrete Fourier Transform* computes $N$ complex frequency coefficients:

```math
X[k] = \sigma_{n=0}^{N-1}  x[n] · e^{-i 2π k n / N}     k = 0, 1, ..., N-1
```

Each $X[k]$ corresponds to the frequency $f_k = k · f_s / N$. The magnitude
$|X[k]|$ tells you how strongly that frequency is present in the signal.

*Computational cost.* Evaluating the sum naively requires $O(N^2)$ operations:
for each of the $N$ output bins $k$, we sum $N$ terms. For $N = 10 000$ this
is $10⁸$ multiply-add operations--feasible but slow. The FFT, introduced next,
reduces this to $O(N log N)$.


*See the [DFT](./dft/) folder on discrete Fourier transforms.*



#### 2.5 Fast Fourier Transform (FFT)

The FFT is not a different transform--it is an efficient *algorithm* for
computing the DFT. The standard Cooley-Tukey radix-2 FFT exploits the fact
that a DFT of size N can be recursively split into two DFTs of size $N/2$:

```math
X[k]      = E[k] + W^k · O[k]
X[k + N/2] = E[k] - W^k · O[k]
```
where $W = e^{-i 2π / N}$   (the "twiddle factor")
- $E[k] = DFT$ of even-indexed samples
- $O[k] = DFT$ of odd-indexed samples

Applying this split recursively (for $N = 2^m$) reduces the total operation
count from $O(N^2)$ to $*O(N log₂ N)*$. For $N = 1 048 576 (2²⁰)$,
the speedup is roughly $52 000×$.

*Complexity comparison:*

| N      | DFT (N²)  | FFT (N log₂ N) | Speedup |
|--------|-----------|----------------|---------|
| 64     | 4 096     | 384            | 10.7×   |
| 1 024  | 1 048 576 | 10 240         | 102×    |
| 65 536 | 4.3 × 10⁹ | 1 048 576      | 4 096×  |

This dramatic improvement is what makes real-time frequency analysis practical.

*See folder on [FFT](./fft/).*


### 3. Convolution and Filtering

#### 3.1 Convolution

Convolution is the mathematical operation that describes how a filter
transforms a signal. Intuitively, it is a *weighted, sliding average*:
the filter kernel $h$ slides across the signal $x$, at each position
computing a dot product of the kernel with the local signal values.

The discrete convolution of $x$ and $h$ is:

```math
(x * h)[n] = \sigma_{k=-∞}^{+∞}  x[k] · h[n - k]
```

For a finite-length kernel of length $M$, this becomes:

```math
y[n] = \sigma_{k=0}^{M-1}  h[k] · x[n - k]
```

Read this as: "to compute the output at position $n$, take the last
$M$ input samples, weight each one by the corresponding filter
coefficient, and sum the results."

*Why convolution matters for filtering:*

- A low-pass filter has a kernel whose coefficients are all positive
  and roughly equal--it computes a *running average*, smoothing out
  rapid fluctuations.

- A high-pass filter has a kernel with positive and negative coefficients
  that sum to zero--it subtracts a smoothed version of the signal from
  itself, emphasising edges and rapid changes.

- The Convolution Theorem tells us that convolution in the time
  domain equals multiplication in the frequency domain, so filter
  design is often done in the frequency domain and converted back
  via the inverse Fourier Transform.


*See the folder [convolution](./conv/).*


#### 3.2 Filters

A filter is a system that selectively attenuates (reduces) certain frequencies
while passing others. The three fundamental types are defined by which part of
the frequency spectrum they pass.


##### 3.2.1 Low-Pass Filter

A low-pass filter (LPF) passes frequencies *below* a cutoff frequency $f_c$ and
attenuates frequencies above it. The result in the time domain is a smoothing
effect: rapid, high-frequency oscillations are suppressed while slow, low-frequency
trends are preserved.

*Typical applications:* noise smoothing in sensor data, removing hiss from audio,
anti-aliasing before downsampling, blurring in image processing.


##### 3.2.2 High-Pass Filter

A high-pass filter (HPF) passes frequencies *above* $f_c$ and attenuates those
below it. It removes slow-varying trends and baseline drift, leaving only rapid
changes. Mathematically, a high-pass filter is the complement of a low-pass:
$HPF = 1 - LPF$.

*Typical applications:* removing DC offset from audio or sensor data, detecting
edges in images (where edges correspond to high spatial frequencies), removing
low-frequency hum (50/60 Hz mains interference) from biomedical signals.


##### 3.2.3 Band-Pass Filter

A band-pass filter (BPF) passes only the frequencies *within* a specified range
`[f_low, f_high]`, attenuating both lower and higher content. It can be constructed
by cascading a high-pass and a low-pass filter, or designed directly.

*Typical applications:* radio tuning (selecting one station's frequency band),
isolating a physiological rhythm in biosignals (e.g. the alpha band 8-12 Hz in EEG),
equaliser bands in audio processing, extracting a specific harmonic from a vibrating structure.

*See folder on [filters](./filters/).*





### 4. Practical Examples

#### 4.1 Signal Generation

Understanding how to construct synthetic signals with known properties is core
both for testing algorithms and for building intuition about the frequency domain.

A pure sinusoid at frequency $f$ with amplitude $A$ and phase $φ$ is:

```math
x(t) = A · sin(2π f t + φ)
```

Real signals are almost always *multi-frequency*: a musical note contains a
fundamental frequency and its harmonics; a speech vowel has formant peaks;
a machine vibration spectrum reveals bearing defects.

*See folder [generate](./generate/) on generating and combining signals.*


#### 4.2 Frequency Analysis

Reading an FFT spectrum is a skill. Here is what to look for.

- *Peaks* indicate dominant frequency components. The height of a peak
  (after normalisation) gives the amplitude; its position on the frequency
  axis gives the frequency.

- *DC component* (`bin k = 0`) represents the signal mean. A non-zero
  DC bin means the signal has a constant offset.

- *Noise floor*--if the spectrum has many small bins rather than a few
  clear peaks, the signal is noisy in a spectrally broad sense.

- *Harmonics* appear as evenly spaced peaks at integer multiples of a
  fundamental. They indicate non-linear distortion, clipping, or a
  naturally harmonic source like a plucked string.

- *The symmetric half*--for a real-valued signal, the FFT output above
  N/2 is the conjugate mirror of the lower half. Use `np.fft.rfft`
  to work with just the unique positive-frequency half.


*Interpreting FFT output in folder [analysis](./analysis/).*


#### 4.3 Audio Processing

Audio signals are time-varying pressure waves, digitised at rates typically
between 8 kHz (telephone quality) and 48 kHz (professional audio).
Signal processing techniques are central to nearly every stage of
an audio pipeline.

*A common task: removing broadband noise from a recording.*

The simplest approach is *spectral subtraction*: estimate the noise spectrum
from a segment where only noise is present (no speech or music), then subtract
that estimate from every frame of the recording. More sophisticated methods
include Wiener filtering and deep neural network denoisers,
but spectral subtraction is a good introduction to the idea.

*See more on loading, filtering, and denoising audio in folder [denoise](./denoise/).*



#### 4.4 Image Processing (2D Signals)

An image is a two-dimensional discrete signal: the value at position `(x, y)` is the
pixel intensity (or a colour triplet). All the concepts developed for 1-D signals
extend naturally to 2-D.

The 2-D convolution of an image $I$ with a kernel $K$ is:

```math
(I * K)[m, n] = \sigma_i \sigma_j  I[m - i, n - j] · K[i, j]
```

Different kernels produce different effects. Three important ones:

| Kernel                             | Effect               | Use                   |
|------------------------------------|----------------------|-----------------------|
| All-positive, sums to 1            | Blurring / smoothing | Noise reduction       |
| Positive centre, negative surround | Sharpening           | Enhancing fine detail |
| Asymmetric gradients               | Edge detection       | Feature extraction    |

*Blur, sharpen, and edge detection on an image in folder [process](./process/).*



### 5. Advanced Topics

#### 5.1 Windowing and Spectral Leakage

When we compute the DFT of a finite block of N samples, we are implicitly assuming the
signal is periodic with period N. If the signal is not exactly periodic within the
block--which is almost always the case for real data--the discontinuity at the block
boundaries causes energy to *leak* from the true frequency bins into neighbouring bins.
This is called *spectral leakage*.

*Illustration.* Take a 1-second sine wave at exactly 50 Hz sampled at 1000 Hz: the FFT
produces a single clean spike. Now take the same wave at 50.3 Hz: the signal no longer
completes an integer number of cycles in 1 second, and the FFT shows a smeared blob
rather than a sharp spike--energy has leaked into adjacent bins.

*Window functions* reduce leakage by tapering the signal to zero at both ends of the block.
This eliminates the artificial discontinuity at the cost of slightly widening the spectral
peak (reduced frequency resolution). The choice of window is a trade-off between:

- *Main-lobe width*--how narrow/sharp the spectral peak is (frequency resolution)
- *Side-lobe level*--how much energy leaks into distant bins (leakage suppression)

*Common windows:*

| Window       | Main-lobe                   | Peak side-lobe        | Best for ..                             |
|--------------|-----------------------------|-----------------------|-----------------------------------------|
| Rectangular  | Narrowest                   | -13 dB (high leakage) | Signals with exact-bin frequencies      |
| Hann         | Wider                       | -31 dB                | General-purpose audio/vibration         |
| Hamming      | Slightly narrower than Hann | -41 dB                | Speech processing                       |
| Blackman     | Widest                      | -57 dB                | Detecting weak signals near strong ones |
| Flat-top     | Widest                      | -93 dB                | Precise amplitude measurement           |

*Leakage and window comparison in folder [window](./window/).*

*Rule of thumb:* use a Hann window as the default for audio and vibration analysis.
Use a flat-top window when you need to measure amplitudes precisely. Use rectangular
only when you know the signal frequency aligns exactly with a DFT bin.



#### 5.2 The Z-Transform

The Z-Transform is a generalisation of the Discrete-Time Fourier Transform (DTFT)
to the complex plane. Where the DTFT evaluates on the unit circle $|z| = 1$, the
Z-Transform evaluates everywhere in the z-plane. This makes it the principal tool
for analysing and designing digital filters.

*Definition:*
```math
X(z) = \sigma_{n=-∞}^{+∞}  x[n] · z^{-n}       z ∈ ℂ
```

Evaluating on the unit circle $z = e^{i2πf/fs}$ recovers the DTFT.

*Why the z-plane matters:*

The *poles* and *zeros* of a filter's transfer function H(z) completely determine its behaviour:
- A *zero* at $z = z₀$ means the filter completely cancels that frequency.
- A *pole* at $z = p₀$ means the filter amplifies frequencies near the angle of $p₀$.
- For a stable filter, all poles must lie *strictly inside* the unit circle.

*Transfer function H(z) and difference equation.*

A causal linear filter is described by a rational transfer function:

```math
H(z) = B(z) / A(z) = (b₀ + b₁z⁻¹ + ... + bₘz⁻ᴹ) / (1 + a₁z⁻¹ + ... + aₙz⁻ᴺ)
```

This corresponds directly to the difference equation:

```math
y[n] = b₀x[n] + b₁x[n-1] + ... - a₁y[n-1] - a₂y[n-2] - ...
```

*Pole-zero plot and filter stability in folder [z](./z/).*



#### 5.3 FIR vs IIR Filters

Digital filters fall into two fundamental families.

*FIR (Finite Impulse Response)* filters have only feedforward paths--the output
depends only on current and past *inputs*, never on past outputs. Their impulse
response is finite (it dies out in exactly M steps for an M-tap filter).

```math
y[n] = \sigma_{k=0}^{M-1}  b_k · x[n - k]
```

*IIR (Infinite Impulse Response)* filters have feedback paths--the output depends on
past *outputs* as well as past inputs. Their impulse response is theoretically infinite,
though it decays exponentially for a stable filter.

```math
y[n] = \sigma_{k=0}^{M} b_k · x[n-k]  -  \sigma_{k=1}^{N} a_k · y[n-k]
```

*Comparison:*

| Property              | FIR                             | IIR                                               |
|-----------------------|---------------------------------|---------------------------------------------------|
| Stability             | Always stable (no feedback)     | Possible instability if poles outside unit circle |
| Phase response        | Exactly linear phase achievable | Non-linear phase (introduces distortion)          |
| Computational cost    | Higher (needs many taps)        | Lower (fewer coefficients for same sharpness)     |
| Frequency selectivity | Moderate per tap                | High (matches analogue filter prototypes)         |
| Typical design method | Windowed sinc, Parks-McClellan  | Butterworth, Chebyshev, Elliptic                  |
| Suited for            | Audio (phase-critical), sensors | Communications, real-time systems                 |

*Comparing FIR and IIR for the same specification in folder [firiir](./firiir/).*

*When to choose FIR:* audio processing, biomedical signal analysis,
any application where phase linearity matters (phase distortion can
cause waveform dispersion or ear-fatiguing artefacts in audio).

*When to choose IIR:* real-time systems with tight computational budgets,
communications receivers, control loops--anywhere the non-linear phase
is acceptable and efficiency is paramount.


### 6. Projects

#### 6.1 Real-Time Spectrum Analyser

This project uses the Web Audio API to capture microphone input in the browser,
run the browser's built-in FFT, and display a live frequency spectrum.
No external libraries needed.

File: [spectrum.html](./projects/spectrum.html)




#### 6.2 Aliasing Demonstration

This self-contained script generates a publication-quality figure showing
the effect of aliasing at three sampling rates, and computes the alias
frequency analytically.

File [alias.py](./projects/alias.py)




#### 6.3 Image Filter Toolkit

A reusable toolkit for applying common 2-D signal processing kernels to greyscale images.

File: [toolkit.py](./projects/toolkit.py)




#### 6.4 FFT Benchmark: Naive DFT vs FFT

This project benchmarks the naive $O(N^2)$ DFT against `numpy.fft`
(which uses a compiled FFT library) and plots the measured times
alongside the theoretical complexity curves.

File: [benchmark.py](./projects/benchmark.py)




### Conclusion

This section introduced signal processing from first principles
through to practical implementation:

1. *Signals* are information-carrying quantities that vary over time,
   space, or any other independent variable. Digital systems work with
   *discrete* samples of underlying *continuous* physical signals.

2. *Sampling* converts a continuous signal to a discrete one. The
   Nyquist-Shannon theorem sets the minimum sampling rate at twice
   the highest frequency component. Violating this limit causes
   *aliasing*--an irreversible corruption where high-frequency
   content appears as phantom low-frequency artefacts.

3. *The Fourier Transform* decomposes a signal into its constituent
   sinusoids, revealing the frequency content invisible in the time
   domain. The DFT is the discrete version; the FFT computes it in
   $O(N log N)$ time, making real-time frequency analysis practical.

4. *Convolution* is the operation underlying all linear filtering.
   Choosing different kernels produces smoothing (low-pass), sharpening
   (high-pass), edge detection, and more. The convolution theorem
   makes frequency-domain filtering efficient.

5. *FIR filters* are unconditionally stable and can achieve exact
   linear phase. *IIR filters* are more efficient but introduce phase
   distortion and require care to ensure stability--checked via pole
   location in the z-plane.

6. *Windowing* reduces spectral leakage when analysing finite-length
signals, at the cost of slightly reduced frequency resolution.

The projects in Section 6 tie these ideas together into runnable programs:
a live spectrum analyser in the browser, an aliasing visualiser, an image
filter toolkit, and a complexity benchmark. Each can be extended--add
a waterfall spectrogram to the spectrum analyser, experiment with
non-uniform sampling, or implement a Cooley-Tukey FFT from scratch to
see exactly how the $O(N log N)$ recursion works.

