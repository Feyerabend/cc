
## K-Nearest Neighbours

K-Nearest Neighbours (KNN) is one of the simplest and most intuitive machine learning algorithms.
To classify a new data point, it looks at the K training examples that are closest to it in feature
space and assigns the majority class among those neighbours. No explicit training step is required --
the model simply stores all training data and defers all computation to prediction time.

The algorithm rests on a straightforward assumption: similar inputs tend to belong to the same class.
"Similarity" is measured by distance, most commonly Euclidean distance in continuous feature spaces.
The choice of K controls the bias-variance trade-off: a small K (e.g. K=1) gives a flexible but
noisy decision boundary, while a large K smooths the boundary but may underfit.

The visualisation here is built with D3.js and loads a CSV file produced by `gen.py`. Training
points (apples and oranges, drawn from two Gaussian clusters) and KNN-predicted test points are
plotted together, illustrating how the decision boundary separates the two classes.


### Mathematics

Given a query point $x$ and a set of labelled training points $\{(x_i, y_i)\}$, KNN assigns the
class by majority vote over the K closest neighbours:

```math
\hat{y} = \arg\max_{c} \sum_{i \in \mathcal{N}_K(x)} \mathbf{1}[y_i = c]
```

where $\mathcal{N}_K(x)$ is the set of indices of the K nearest training points. Distance is
typically Euclidean:

```math
d(x, x_i) = \sqrt{\sum_{j=1}^{p} (x_j - x_{ij})^2}
```

For regression, the prediction is the mean of the K neighbours' values:

```math
\hat{y} = \frac{1}{K} \sum_{i \in \mathcal{N}_K(x)} y_i
```

Prediction time is $\mathcal{O}(n \cdot p)$ per query for a brute-force search over $n$ training
points with $p$ features. Spatial index structures such as KD-trees reduce this to
$\mathcal{O}(p \log n)$ in low dimensions.


### Concepts

* *K (Number of Neighbours):* The key hyperparameter. Small K overfits; large K underfits. A
  common heuristic starting point is $K = \sqrt{n}$.
* *Distance Metric:* Euclidean distance is standard. Manhattan distance is used when features
  have very different scales or when the data lies in a high-dimensional sparse space. Features
  should be normalised before computing distances.
* *Lazy Learning:* KNN stores the entire training set and does all computation at prediction time.
  There is no explicit model fitting phase, but prediction can be slow on large datasets.
* *Decision Boundary:* KNN produces a locally adaptive, non-linear decision boundary. With K=1
  the boundary is a Voronoi tessellation of the training points.
* *Curse of Dimensionality:* In high-dimensional feature spaces, all points become approximately
  equidistant, making nearest-neighbour search less meaningful. Feature selection or dimensionality
  reduction is important when using KNN on high-dimensional data.


### Samples


*Sample 1: Image Digit Classification*

* *Features:* Pixel intensities of 28×28 greyscale images (784 dimensions).
* *Target:* Digit class (0--9).
* *Scenario:* On the MNIST dataset, KNN with K=3 and L2 distance achieves ~97% test accuracy.
  It requires no training and serves as a strong non-parametric baseline against which neural
  networks are compared.

*Sample 2: Product Recommendation*

* *Features:* User--item rating vectors (collaborative filtering).
* *Target:* Predicted rating for unseen items.
* *Scenario:* A streaming service finds the K users most similar to a target user by cosine
  distance in rating space, then recommends items highly rated by those neighbours but not yet
  seen by the target user.

*Sample 3: Anomaly Detection in Network Traffic*

* *Features:* Packet size, inter-arrival time, protocol flags, connection duration.
* *Target:* Normal / Anomalous.
* *Scenario:* A security monitor flags network connections whose K nearest neighbours in
  feature space are predominantly labelled as attacks. Because KNN adapts locally, it can
  detect novel attack patterns that fall near known attack examples even without retraining.
