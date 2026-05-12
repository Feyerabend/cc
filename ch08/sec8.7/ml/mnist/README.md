
## MNIST

MNIST (Modified National Institute of Standards and Technology) was developed in 1998 by Yann LeCun,
Léon Bottou, Yoshua Bengio, and Patrick Haffner as an improved and standardised version of the original
NIST dataset. It consists of 60,000 training images and 10,000 test images of 28×28 grayscale handwritten
digits (0--9), drawn from American high school students and Census Bureau employees. Despite its simplicity,
MNIST became the de facto benchmark for testing and comparing machine learning models for over two decades.


### Dataset and Task

Each image is a 28×28 array of pixel intensities in [0, 255], typically normalised to [0, 1]. Labels are
integers 0--9. The standard task is 10-class classification.

Common baseline results on the MNIST test set:
- k-nearest neighbours (k=3): ~97%
- Single-layer neural network (784 → 10): ~92%
- Convolutional neural network (LeNet-5): ~99.05%
- Modern deep residual networks: >99.7%

The scripts in this folder implement two approaches:
- `mnist.py` -- a plain feedforward neural network (no convolutions) built from scratch using only NumPy.
- `cnn.py` -- a convolutional neural network using Keras/TensorFlow.


### Mathematics

A feedforward network for MNIST maps a flattened 784-dimensional input $x$ through one or more hidden
layers to a 10-dimensional output. A hidden layer computes:

```math
h = \sigma(Wx + b)
```

where $W$ is a weight matrix, $b$ a bias vector, and $\sigma$ an activation function (sigmoid, ReLU, etc.).
The output layer uses softmax to produce a probability distribution over the 10 classes:

```math
\hat{y}_k = \frac{e^{z_k}}{\sum_{j=0}^{9} e^{z_j}}
```

Training minimises the cross-entropy loss:

```math
\mathcal{L} = -\sum_{k=0}^{9} y_k \log \hat{y}_k
```

where $y$ is the one-hot label vector. Weights are updated via backpropagation and gradient descent.


### Influence

### Precursor to Handwriting Recognition

MNIST's techniques were extended to postal address recognition, bank check processing, and form
digitisation. The original NIST dataset had already been used by the U.S. Postal Service and financial
institutions for exactly these tasks; MNIST standardised the benchmark for academic research.

### Benchmarking for Deep Learning

Techniques developed and validated on MNIST often generalised to harder datasets such as ImageNet.
LeNet-5, the convolutional network first tested on MNIST, established the template for the convolutional
architectures now used in autonomous driving, medical imaging, and security.

### Embedded Systems and Edge AI

MNIST has been used to test lightweight neural network implementations for embedded devices. Digit
recognition on low-power hardware for IoT applications traces directly to training and evaluation
pipelines developed on MNIST.


### Evolution to MNIST

Despite its practical use, the original NIST dataset had inconsistencies in image formatting and
preprocessing. To address this, Yann LeCun and colleagues created MNIST in 1998, which rescaled
all images to 28×28 pixels, standardised grayscale values, and balanced the dataset. Modern real-world
OCR systems use larger, more diverse datasets, but MNIST remains the canonical entry point for
learning about image classification.
