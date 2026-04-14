
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
(x, y) location. A seismic survey maps reflected sound energy across a field of sensors buried in the ground.

*Continuous signals* are defined at every instant, with no gaps. Mathematically we write x(t) to
mean the signal value at time t, where t is a real number. Physical signals--sound, light,
temperature--are continuous.

*Discrete signals* are defined only at specific, regularly spaced instants. We write x[n] to mean
the value at sample index n, where n is an integer. Every digital system works with discrete signals:
computers cannot store a value for every real-numbered instant, only for a countably infinite
(or finite) sequence of moments.

*Examples across domains:*

| Domain     | Signal                   | Independent variable |
|------------|--------------------------|----------------------|
| Audio      | Pressure wave / voltage  | Time                 |
| Image      | Pixel intensity          | Space (x, y)         |
| Radar      | Reflected pulse envelope | Time / range         |
| Finance    | Stock price              | Time                 |
| Biology    | Neuron firing rate       | Time                 |
| Geophysics | Seismic wave             | Space and time       |

The central task of signal processing is to extract useful information from these varying
quantities--removing noise, detecting patterns, compressing data, or transforming representations
so that downstream algorithms can work more easily.



#### 1.2 Why Signal Processing Matters

Signal processing underpins a surprisingly wide range of technologies.
Here are four areas where a working knowledge makes a real difference.

*Audio processing.* Every phone call, music stream, and voice assistant relies on signal processing.
Noise cancellation in headphones uses adaptive filters to subtract an estimate of background noise
from the microphone signal in real time. MP3 and AAC compression apply psychoacoustic models that
discard frequency content the human ear cannot perceive, achieving 10:1 compression with minimal
audible loss. Speech recognition first converts audio to a spectrogram--a time-frequency map--before
feeding it to a neural network.

*Communications.* Amplitude modulation (AM), frequency modulation (FM), and modern schemes like OFDM
(used in Wi-Fi, 4G, and 5G) all work by shifting information-bearing signals to carrier frequencies
suitable for transmission. At the receiver, a matched filter recovers the original signal from noise.
Channel equalisation corrects for the distortion introduced by the medium.

*Machine learning.* Raw signals are rarely fed directly to a classifier. A common pre-processing pipeline
converts a time-series into a frequency representation (spectrogram or mel-frequency cepstral coefficients),
applies normalisation, and possibly applies a learned filter bank. Convolutional neural networks are
themselves a form of adaptive signal processing: their learnable kernels are filters optimised for a particular task.

*Embedded systems.* Microcontrollers in industrial sensors, medical devices, and consumer electronics
all perform signal processing under tight constraints of memory and compute budget. A digital filter that
smooths a noisy ADC reading, a PID controller that cancels vibration, an encoder that detects a zero
crossing--these are signal processing tasks executed in real time, often without an operating system,
in a few kilobytes of RAM.


### 2. Mathematical Foundations

#### 2.1 Continuous vs Discrete Signals

A continuous signal x(t) assigns a real (or complex) number to every real-valued time t.
This is the natural model for physical phenomena. We can differentiate it, integrate it,
and reason about its behaviour at any instant.

A discrete signal $x[n]$ assigns a value only at integer indices $n ∈ ℤ$. It arises whenever
we *sample* a continuous signal--measuring its value at regular intervals.

*Notation summary:*

- Continuous signal:  $x(t)$,   $t ∈ ℝ$
- Discrete signal:    $x[n]$,   $n ∈ ℤ$
- Sampling period:    $T$  (seconds between samples)
- Sampling rate:      $f_s = 1 / T$  (samples per second, Hz)


The relationship between the two is:

```math
x[n] = x(n · T) = x(n / f_s)
```

Each discrete sample is simply the continuous signal evaluated at time t = nT.

*Why discrete signals are necessary.* Storing a continuous signal requires infinite
precision and infinite storage--both impossible. Discrete sampling reduces the representation
to a finite (or countably infinite) sequence of numbers, which computers can store,
transmit, and process. The key question--addressed in the next section--is how fast
we must sample to avoid losing information.



#### 2.2 Sampling and the Nyquist-Shannon Theorem

The *Nyquist-Shannon sampling theorem* gives the minimum sampling rate required
to perfectly reconstruct a band-limited continuous signal from its discrete samples.

> A continuous signal whose highest frequency component is f_max can be perfectly
> reconstructed from discrete samples taken at a rate f_s, provided:
>
> $*f_s ≥ 2 · f_max*$

The frequency $f_s / 2$ is called the *Nyquist frequency* (or folding frequency).
It is the highest frequency representable at a given sampling rate.

*Aliasing.* If the signal contains components above the Nyquist frequency and we
sample below $2 · f_max$, those high-frequency components are *folded* back into
the representable range and appear as phantom low-frequency components. This
phenomenon is called aliasing, and it is irreversible--once aliased, the original
high-frequency content cannot be recovered.

A classic visual example: a wheel spinning at 24 revolutions per second filmed at
24 frames per second appears stationary. The sampling rate (24 fps) equals the signal
frequency (24 Hz), which is exactly at the Nyquist limit for 12 Hz content--here th
rotation frequency exceeds it, causing the aliased "stationary" appearance.
(Think of a spinning wheel in a movie, or even observation with your own eyes.)

*Anti-aliasing filters.* In practice, a low-pass filter is applied to the continuous
signal *before* sampling to remove any content above $f_s / 2$. This is called an
anti-aliasing filter, and it is present in every ADC (analogue-to-digital converter)
front end.

Formula:
```math
f_s >= 2 * f_max
```

*See the [sampling](./sampling/) folder.*


#### 2.3 Fourier Transform

The central insight of Fourier analysis is that *any* periodic signal--and,
with suitable extension, any signal with finite energy--can be expressed as
a sum of sinusoids of different frequencies, amplitudes, and phases. This is
not just a mathematical curiosity; it reveals which frequencies are present
in a signal and in what proportion, turning a time-domain waveform into a
*frequency-domain spectrum*.

*Intuition.* Imagine a chord played on a piano. The pressure waveform at your
ear is a messy, oscillating curve. Yet your auditory system immediately resolves
it into individual notes--A, C, E--each at its own frequency and loudness.
Fourier analysis is the mathematical version of that decomposition: it asks,
"for each possible frequency f, how much of that frequency is present in the signal?"

*The Fourier Transform* of a continuous signal x(t) is defined as:

```math
X(f) = ∫_{-∞}^{+∞}  x(t) · e^{-i 2π f t}  dt
```

$X(f)$ is a complex-valued function of frequency. Its magnitude $|X(f)|$ is
the *amplitude spectrum* (how strong each frequency is), and its argument $∠X(f)$
is the *phase spectrum* (the phase offset of each sinusoidal component).

The *inverse Fourier Transform* recovers the time-domain signal:

```math
x(t) = ∫_{-∞}^{+∞}  X(f) · e^{+i 2π f t}  df
```

These two transforms form a perfect pair: going to the frequency domain loses no
information, and coming back gives back the original signal exactly.

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

For a finite sequence of $N$ samples $x[0], x[1]$, ..., x[N-1]$, the
*Discrete Fourier Transform* computes $N$ complex frequency coefficients:

```math
X[k] = sigma_{n=0}^{N-1}  x[n] · e^{-i 2π k n / N}     k = 0, 1, ..., N-1
```

Each $X[k]$ corresponds to the frequency $f_k = k · f_s / N$. The magnitude
$|X[k]|$ tells you how strongly that frequency is present in the signal.

*Computational cost.* Evaluating the sum naively requires $O(N^2)$ operations:
for each of the $N$ output bins $k$, we sum $N$ terms. For $N = 10 000$ this
is $10⁸$ multiply-add operations--feasible but slow. The FFT, introduced next,
reduces this to $O(N log N)$.


*See the [DFT](./dft/) folder on discrete Fourier transforms.*

