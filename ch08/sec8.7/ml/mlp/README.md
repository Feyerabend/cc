
## Multilayer Perceptron

A Multilayer Perceptron (MLP) is the foundational deep learning architecture: a directed acyclic graph
of layers where each layer applies a linear transformation followed by a non-linear activation function.
Unlike a single-layer perceptron, which can only learn linearly separable functions, an MLP with one
hidden layer can approximate any continuous function (Universal Approximation Theorem).

The example here compares an MLP against linear regression for temperature prediction, using the Uppsala
temperature series 1722--2022 -- one of the longest continuous meteorological records in the world. The
central lesson is that complexity is not always better: on this dataset, where seasonal cycles dominate,
linear regression with engineered features often matches the MLP's accuracy at a fraction of the cost.

See the [Uppsala dataset folder](./uppsala_tm_1722-2022/) for the full implementation, plots, and analysis.


### Mathematics

A single hidden layer transforms input $x \in \mathbb{R}^p$ as:

```math
h = \sigma(W_1 x + b_1), \quad \hat{y} = W_2 h + b_2
```

where $\sigma$ is a non-linear activation (ReLU, sigmoid, tanh). Stacking $L$ such layers gives a
depth-$L$ MLP. Training minimises a loss $\mathcal{L}$ via backpropagation: the chain rule propagates
gradients from the output back through each layer, and an optimiser (SGD, Adam) updates the weights.

For regression the loss is mean squared error:

```math
\mathcal{L} = \frac{1}{n} \sum_{i=1}^n (y_i - \hat{y}_i)^2
```

ReLU activation, $\sigma(z) = \max(0, z)$, is preferred in hidden layers because it avoids the
vanishing-gradient problem that sigmoid and tanh suffer in deep networks.


### Concepts

* *Depth vs. Width:* Deeper networks learn more abstract representations; wider layers increase
  capacity within a layer. Both increase parameter count.
* *Backpropagation:* Computes gradients of the loss with respect to all weights in one backward
  pass using the chain rule.
* *Overfitting:* MLPs can memorise training data. Dropout (randomly zeroing activations during
  training), weight decay, and early stopping all reduce overfitting.
* *Vanishing Gradients:* Gradients can shrink exponentially through layers. ReLU activations and
  He initialisation mitigate this in practice.
* *Feature Engineering:* For time-series data, encoding seasonality as sine/cosine features
  ($\sin(2\pi t/T)$, $\cos(2\pi t/T)$) can make a linear model competitive with an MLP.


### Samples


*Sample 1: Temperature Prediction (Uppsala Series)*

* *Features:* Year, month, day encoded as sine/cosine components to capture annual and daily cycles.
* *Target:* Mean daily temperature (°C).
* *Scenario:* Comparing an MLP (3 hidden layers: 64, 32, 16 neurons) with linear regression reveals
  that the linear model captures most variance once seasonal features are properly encoded, illustrating
  that model complexity should be justified by the data's actual non-linearity.

*Sample 2: Handwritten Digit Classification*

* *Features:* Flattened 784-pixel grayscale values from MNIST images.
* *Target:* Digit class (0--9).
* *Scenario:* A two-hidden-layer MLP (784 → 256 → 128 → 10) achieves ~98% test accuracy on MNIST,
  demonstrating that MLPs can solve image classification without convolutions on small datasets.

*Sample 3: Tabular Credit Risk*

* *Features:* Income, debt ratio, credit history, employment tenure (structured tabular data).
* *Target:* Default probability.
* *Scenario:* An MLP with dropout and batch normalisation outperforms logistic regression on
  non-linear credit-risk patterns. Gradient boosting often outperforms both -- the best architecture
  depends on the data structure, not on which model is most complex.
