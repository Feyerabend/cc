
## Convolutional Neural Networks

The book part introduces the 2D convolution formula and lists the key structural
principles. This section goes deeper into the arithmetic of convolutions and
gives hands-on code that lets you see exactly what happens inside a convolutional
layer.

### Files

| File                                       | What it demonstrates                                            |
|--------------------------------------------|-----------------------------------------------------------------|
| [convolution.py](convolution.py)           | 2D cross-correlation from scratch, compared with `np.correlate` |
| [receptive_field.py](./receptive_field.py) | How the receptive field grows with depth and stride             |
| [feature_maps.py](./feature_maps.py)       | Edge-detection kernels applied to a synthetic image             |
| [convolution.c](./convolution.c)           | A single 2D convolution in C with no external libraries         |

### Key ideas extended here

*Cross-correlation vs convolution.* The book notes that most frameworks
implement cross-correlation (no kernel flip) rather than true convolution. The
difference is invisible when the kernel is learned, because the network can learn
the flipped version, but the distinction matters when reasoning about the operation
analytically. `convolution.py` implements both and shows where they differ.

*Receptive field growth.* Each neuron in a convolutional layer can only see a
small patch of the input. With deeper stacks, that patch--the receptive
field--grows. The rate of growth depends on kernel size, stride, and dilation.
`receptive_field.py` computes and prints receptive field sizes for several standard
architectures (VGG-style, ResNet-style with stride-2 layers).

*Padding and stride.* The output spatial dimension after a convolution with
input size $n$, kernel size $k$, padding $p$, and stride $s$ is:
$$\left\lfloor \frac{n + 2p - k}{s} \right\rfloor + 1$$
`convolution.py` verifies this formula for several combinations.

*Handcrafted kernels.* Before learned features, computer vision relied on
handcrafted filters: Sobel for edges, Gaussian for blur, Laplacian for sharpening.
`feature_maps.py` applies these to a synthetic image to make the analogy between
classic filters and learned CNN kernels tangible.
