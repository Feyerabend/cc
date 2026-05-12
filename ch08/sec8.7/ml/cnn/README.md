
## Convolutional Neural Network (CNN)

A Convolutional Neural Network is a feedforward network that exploits the spatial structure
of grid-like data (images, audio spectrograms) by replacing fully connected layers with
convolutional filters. A filter is a small weight matrix that is slid across the input,
computing a dot product at each position. Shared weights drastically reduce the parameter
count compared to a dense network, and the filter learns to detect a local pattern --
an edge, a corner, a texture -- wherever it appears in the input.

The code here trains and runs a CNN on CIFAR-10, a benchmark of 60,000 colour images in
10 classes (airplane, automobile, bird, cat, deer, dog, frog, horse, ship, truck):

- `cnn_simple.py` -- builds, trains, and evaluates a three-block CNN with TensorFlow/Keras.
  Saves the trained model to `cifar10_model.h5`.
- `model_user.py` -- loads the saved model and classifies new images supplied as command-line
  arguments or drawn from a set of test images.


### Mathematics

A convolutional layer with filter $W \in \mathbb{R}^{k \times k \times C_{in}}$ produces a
feature map by computing:

```math
z_{i,j} = \sum_{u=0}^{k-1} \sum_{v=0}^{k-1} \sum_{c=1}^{C_{in}} W_{u,v,c} \cdot x_{i+u,\, j+v,\, c} + b
```

followed by a non-linear activation (ReLU: $\sigma(z) = \max(0, z)$).

*Max pooling* downsamples by taking the maximum over a $p \times p$ window, reducing spatial
dimensions by a factor of $p$ while retaining the strongest activations.

A depth-$L$ CNN alternates convolutional and pooling layers, then flattens into a dense head.
For $C$ classes the output passes through a softmax:

```math
\hat{y}_k = \frac{e^{z_k}}{\sum_{j=1}^{C} e^{z_j}}
```

Training minimises categorical cross-entropy $\mathcal{L} = -\sum_k y_k \log \hat{y}_k$
via backpropagation, where gradients flow through pooling (max-pooling passes the gradient
only to the winning position) and convolution (a transposed convolution of the upstream
gradient with the filter).


### Concepts

* *Receptive Field:* The region of the input that influences a single output unit. Deeper
  layers have larger receptive fields, allowing detection of complex, large-scale patterns.
* *Parameter Sharing:* The same filter weights are applied at every spatial position.
  This enforces translation equivariance and reduces parameters from $H \cdot W \cdot k^2$
  to $k^2$ per filter.
* *Batch Normalisation:* Normalises activations within a mini-batch to zero mean and unit
  variance, then scales and shifts with learned parameters. Stabilises and accelerates training.
* *Dropout:* Randomly zeroes activations during training, acting as an ensemble of thinned
  networks. Reduces co-adaptation between neurons and mitigates overfitting.
* *Depth vs. Width:* Deeper networks learn more abstract hierarchies; wider layers increase
  the number of detectors per level. Both increase capacity and risk overfitting on small data.


### Samples


*Sample 1: CIFAR-10 Image Classification*

* *Data:* 50,000 training + 10,000 test RGB images, 32×32 pixels, 10 classes.
* *Scenario:* The three-block CNN in `cnn_simple.py` (Conv→BN→Conv→Pool→Dropout ×3, then Dense)
  reaches ~85% test accuracy. `model_user.py` classifies arbitrary images by resizing them to
  32×32 before passing them through the saved model.

*Sample 2: Transfer Learning with Pre-trained Weights*

* *Data:* A small custom dataset of industrial defect images (scratches, dents, discolouration).
* *Scenario:* The convolutional blocks of a network pre-trained on ImageNet are frozen; only the
  dense head is retrained on the defect dataset. Pre-trained filters already detect edges and
  textures, so the head needs very few labelled examples to converge -- a common pattern when
  labelled data is scarce.

*Sample 3: Medical Image Segmentation*

* *Data:* Histopathology slides annotated at pixel level (tumour vs. healthy tissue).
* *Scenario:* A U-Net architecture -- an encoder CNN that progressively downsamples, followed by
  a decoder that upsamples with skip connections to the encoder -- produces a pixel-level mask.
  The skip connections preserve fine spatial detail that would otherwise be lost in the bottleneck.
