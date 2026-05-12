
> [!IMPORTANT]  
> Requires recommended virtual environment and torch.
> Installment of MNIST data is done through the script.

## Test-Time Adaptation on MNIST

TTA directly addresses *distribution shift*: the gap between the distribution a model was trained
on and the distribution it encounters at deployment. Causes include sensor noise, lighting changes,
domain differences, and temporal drift. When such shifts occur, model accuracy can degrade sharply
even though the weights are otherwise well-trained.

`mnist.py` demonstrates TTA with a `SimpleNet` classifier trained on clean MNIST digits. At test
time, Gaussian noise is applied to the inputs and BatchNorm statistics are adapted per-batch via
entropy minimisation before making predictions.

Another example of TTA applied to a [language model](./../../tta/).


### Mathematics

*BatchNorm TTA* replaces the frozen training statistics $(\mu_\text{train}, \sigma^2_\text{train})$
with statistics recomputed on each test batch:

```math
\hat{x}_i = \frac{x_i - \mu_\text{test}}{\sqrt{\sigma^2_\text{test} + \varepsilon}},
\quad \mu_\text{test} = \frac{1}{m}\sum_{i=1}^m x_i,
\quad \sigma^2_\text{test} = \frac{1}{m}\sum_{i=1}^m (x_i - \mu_\text{test})^2
```

The core weights are untouched; only normalisation re-centres the activations to match the
current batch's distribution.

*Entropy minimisation (Tent)* fine-tunes the BatchNorm affine parameters $(\gamma, \beta)$ by
minimising prediction entropy on the test batch -- an unsupervised loss requiring no labels:

```math
\mathcal{L}_\text{ent} = -\sum_k p_k \log p_k
```

A few gradient steps with this loss on the test batch before prediction allow the model to
sharpen its output distribution for the new input statistics.


### Concepts

* *Distribution Shift:* Can be covariate shift (different inputs, same label function), label shift
  (different class frequencies), or concept drift (the input-label relationship itself changes).
* *Adaptation Scope:* Updating only BatchNorm statistics (TTT-BN) is the lightest variant.
  Updating affine parameters $(\gamma, \beta)$ adds a gradient step. Updating all parameters
  risks catastrophic forgetting of the original domain.
* *Tent / Entropy Minimisation:* Confident models have low-entropy predictions. Minimising entropy
  on the test batch -- without labels -- encourages the model to produce sharp predictions on the
  shifted distribution.
* *Online vs. Episodic:* Online TTA accumulates updates across the stream; episodic TTA resets to
  the original weights for each new test sample or batch.
* *Batch Size Dependence:* Small batches yield noisy batch statistics, potentially destabilising
  adaptation. A minimum batch size (~32) is needed for reliable BN-based TTA.


### Samples


*Sample 1: MNIST with Gaussian Noise*

* *Model:* SimpleNet (fully connected layers with BatchNorm), trained for 2 epochs on clean MNIST.
* *Corruption:* Gaussian noise $\mathcal{N}(0, 0.3)$ added per pixel at test time.
* *Results:*
  - Clean test accuracy: 97.58%
  - Noisy test accuracy (no TTA): 60.72%
  - Noisy test accuracy (after TTA): 90.18% -- a recovery of 29.46 percentage points.

*Sample 2: CIFAR-10-C Corruption Benchmarks*

* *Data:* The standard CIFAR-10-C benchmark applies 19 corruptions at 5 severity levels
  (fog, blur, noise, contrast, JPEG artefacts).
* *Scenario:* Tent-style entropy minimisation of BatchNorm parameters during test time reduces
  the mean corruption error by 18--25% on ResNet-26, with no access to labels and only one
  gradient step per batch.

*Sample 3: Medical Imaging Domain Shift*

* *Data:* X-ray classifier trained on hospital A deployed on hospital B (different scanner make,
  exposure settings, patient demographics).
* *Scenario:* BatchNorm TTA adapts running statistics to hospital B's image distribution at
  inference time. Much of the accuracy lost from the domain shift is recovered without any
  labelled images from hospital B.
