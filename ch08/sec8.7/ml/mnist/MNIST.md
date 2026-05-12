
## Neural Networks

This script implements a basic neural network to classify images from the MNIST dataset of handwritten digits (0-9).

### Missing Data

> [!IMPORTANT] 
> The program/script will not work without data!
> If you want automatic download of MNIST data, try the torch [version](./tta/),
> which can be used also in this example. But it requires a virtual environment
> and obviously installation of torch.

Otherwise, search for the following files online:
- `train-images.idx3-ubyte`
- `train-labels.idx1-ubyte`
- `t10k-images.idx3-ubyte`
- `t10k-labels.idx1-ubyte`

At the time of writing: https://github.com/mbornet-hl/MNIST/tree/master/MNIST.
Change the names of the files.

### Explanation

1. *MNIST Dataset*:
   - The MNIST dataset contains 28x28 grayscale images of digits with corresponding labels (0-9).
   - `load_mnist_images` reads the image files and scales pixel values to the range [0, 1].
   - `load_mnist_labels` reads the labels.

2. *Neural Network Structure*:
   - *Input Layer*: Each image has 28×28 = 784 pixels, flattened into a 784-element vector.
   - *Hidden Layer*: Contains 64 neurons. This layer processes the input features using weights and biases, then applies a sigmoid activation function to introduce non-linearity.
   - *Output Layer*: Contains 10 neurons (one for each digit). The network produces a probability distribution over the 10 classes using the softmax function.

3. *Initialisation*:
   - Random weights and biases are assigned to both layers and updated during training.

4. *Training Process*:
   - *Feedforward*: Data flows from the input to the output, computing intermediate values for the hidden and output layers.
   - *Backpropagation*: The network computes the error (difference between predicted and true labels) and adjusts weights and biases using gradient descent to minimise this error.

5. *Prediction*:
   - After training, the network is tested on unseen data to evaluate accuracy.


### Mathematical Explanations

#### Feedforward Process

##### 1. Input Layer
Each input image $\`\mathbf{x} \in \mathbb{R}^{784}\`$ represents the pixel intensities scaled to $\`[0, 1]\`$.

##### 2. Hidden Layer
For each hidden neuron $\`j\`$, the input and output are computed as:

```math
h_j = \sigma\left(\sum_{i=1}^{784} x_i w_{ij} + b_j\right),
```

where:
- $\` w_{ij} \`$ is the weight connecting input $\` i \`$ to hidden neuron $\` j \`$,
- $\` b_j \`$ is the bias for hidden neuron $\` j \`$,
- $\` \sigma(x) = \frac{1}{1 + e^{-x}} \`$ is the sigmoid activation function.

The hidden layer output is:

```math
\mathbf{h} \in \mathbb{R}^{64}, \quad \text{where } h_j = \sigma(\text{weighted sum of inputs to neuron } j).
```

##### 3. Output Layer
For each output neuron $\` k \`$, compute the input:

```math
o_k = \sum_{j=1}^{64} h_j w_{jk} + b_k,
```

where:
- $\` w_{jk} \`$ is the weight connecting hidden neuron $\` j \`$ to output neuron $\` k \`$,
- $\` b_k \`$ is the bias for output neuron $\` k \`$.

The final output probabilities are computed using the *softmax function*:

```math
p_k = \frac{e^{o_k}}{\sum_{l=1}^{10} e^{o_l}},
```

where the output vector $\` \mathbf{p} \in \mathbb{R}^{10} \`$ represents the probabilities for each of the 10 classes.


### Error and Backpropagation

##### 1. Output Error
The target (true label) is one-hot encoded: $\` \mathbf{t} \in \{0, 1\}^{10} \`$.  
The error for each output neuron $\` k \`$ is given by:

```math
\delta_k = p_k - t_k.
```

##### 2. Hidden Layer Error
Backpropagate the error to the hidden layer:

```math
\delta_j = \left( \sum_{k=1}^{10} \delta_k w_{jk} \right) \cdot h_j \cdot (1 - h_j),
```

where the term $\` h_j \cdot (1 - h_j) \`$ comes from the derivative of the sigmoid activation function.

##### 3. Gradient Updates
The weights and biases are updated using gradient descent as follows:

- Update weights and biases for the output layer:

```math
w_{jk} \gets w_{jk} - \eta \cdot \delta_k \cdot h_j,

b_k \gets b_k - \eta \cdot \delta_k,
```

where $\` \eta \`$ is the learning rate.
    
- Update weights and biases for the hidden layer:

```math
w_{ij} \gets w_{ij} - \eta \cdot \delta_j \cdot x_i,
```

```math
b_j \gets b_j - \eta \cdot \delta_j.
```



### Accuracy

After training, the model's performance is evaluated on unseen data by comparing the predicted labels with the true labels. The accuracy is given by:

```math
\text{Accuracy} = \frac{\text{Number of Correct Predictions}}{\text{Total Number of Predictions}} \times 100.
```
