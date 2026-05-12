
## PCA

Principal Component Analysis (PCA) is a linear dimensionality reduction technique. It finds
the directions of maximum variance in the data and projects the data onto a lower-dimensional
subspace spanned by those directions. The result is a compact representation that retains as
much information as possible while discarding directions that contribute little to the overall
variance.

The code here uses PCA as a preprocessing step before KNN classification. Five-dimensional
synthetic data (apple vs. orange clusters) is standardised, reduced to two principal components,
and then classified. Visualising the 2D projection makes the decision boundary interpretable.

- `pca.py` -- generates 5D data, applies `sklearn` PCA, runs KNN classification, and renders
  a 2D scatter plot to PNG.
- `visual.py` -- standalone visualisation of a PCA projection.


### Mathematics

Given $n$ centred observations $x_1, \ldots, x_n \in \mathbb{R}^p$ (zero mean), PCA computes
the sample covariance matrix:

```math
\Sigma = \frac{1}{n-1} \sum_{i=1}^{n} x_i x_i^\top
```

The principal components are the eigenvectors of $\Sigma$, ordered by decreasing eigenvalue.
Equivalently, PCA is the truncated SVD of the data matrix $X \in \mathbb{R}^{n \times p}$:

```math
X = U \Sigma V^\top
```

The first $k$ columns of $V$ (right singular vectors) are the top $k$ principal components.
Projecting onto them gives the reduced representation:

```math
Z = X V_k \in \mathbb{R}^{n \times k}
```

The fraction of variance explained by the first $k$ components is:

```math
\text{explained variance} = \frac{\sum_{i=1}^{k} \lambda_i}{\sum_{i=1}^{p} \lambda_i}
```

where $\lambda_i$ are the eigenvalues of $\Sigma$.


### Concepts

* *Standardisation:* PCA is sensitive to scale. Features with large numeric ranges dominate
  the covariance matrix. Standardising to zero mean and unit variance before PCA ensures
  all features contribute equally.
* *Explained Variance Ratio:* The key diagnostic for choosing $k$. A scree plot of cumulative
  explained variance against $k$ typically shows an elbow where additional components add
  diminishing information.
* *Linear Assumption:* PCA finds linear subspaces. Non-linear structure (spirals, manifolds)
  requires kernel PCA or manifold methods such as t-SNE or UMAP.
* *Reconstruction Error:* Projecting back from the reduced space to the original gives a
  reconstruction; the mean squared error measures information lost by the reduction.
* *PCA vs. t-SNE/UMAP:* PCA is fast, deterministic, and invertible. t-SNE and UMAP preserve
  local topology better for visualisation but are not invertible and do not scale linearly.


### Samples


*Sample 1: Apple vs. Orange Classification (5D → 2D)*

* *Data:* Synthetic 5-dimensional clusters representing two fruit classes.
* *Scenario:* PCA reduces the feature space from 5 to 2 dimensions before KNN classification.
  The 2D projection is plotted, showing how much of the class separation is captured in the
  first two components and where the decision boundary lies.

*Sample 2: Face Recognition Preprocessing*

* *Data:* A dataset of grayscale face images (e.g., AT&T Faces, 400 images × 10304 pixels).
* *Scenario:* PCA compresses each image from 10304 dimensions to 150 *eigenfaces* -- the
  principal components of the image covariance matrix. KNN in the 150-dimensional space
  achieves competitive recognition accuracy at a fraction of the computational cost.

*Sample 3: Genomics Feature Reduction*

* *Data:* Gene expression profiles: thousands of patients × tens of thousands of genes.
* *Scenario:* PCA reduces the gene space to the top 50 components that explain most
  expression variance. Downstream clustering and classification operate on these 50 features,
  avoiding the curse of dimensionality and reducing noise from genes that vary randomly.
