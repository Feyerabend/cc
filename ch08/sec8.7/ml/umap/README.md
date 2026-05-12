
## UMAP

UMAP (Uniform Manifold Approximation and Projection) is a non-linear dimensionality reduction
algorithm that maps high-dimensional data to a low-dimensional embedding while preserving both
local and, to a greater extent than t-SNE, global structure. It is faster than t-SNE on large
datasets and can be applied to new points after training, making it usable as a preprocessing
step in machine learning pipelines.

`eumap.py` generates 150 synthetic 3D points in 3 clusters, saves a raw X1/X2 projection for
comparison, then applies UMAP to produce a 2D embedding. Both the pre- and post-UMAP scatter
plots are saved as PNG images using Pillow.


### Mathematics

UMAP constructs a weighted graph in the high-dimensional space. For each point $x_i$, it fits
a local metric using the distance to its $k$-th nearest neighbour $\rho_i$ as a normalisation:

```math
w_{ij} = \exp\!\left(-\frac{d(x_i, x_j) - \rho_i}{\sigma_i}\right)
```

where $\sigma_i$ is chosen so that the fuzzy set membership sums to $\log_2 k$. The graph is
made symmetric: $\bar{w}_{ij} = w_{ij} + w_{ji} - w_{ij} w_{ji}$.

The low-dimensional layout minimises the cross-entropy between the high-dimensional membership
strengths $\bar{w}_{ij}$ and the low-dimensional counterparts $v_{ij}$:

```math
\mathcal{L} = \sum_{ij} \left[ \bar{w}_{ij} \log \frac{\bar{w}_{ij}}{v_{ij}}
  + (1 - \bar{w}_{ij}) \log \frac{1 - \bar{w}_{ij}}{1 - v_{ij}} \right]
```

where the low-dimensional affinity uses a differentiable approximation to the Student-t
distribution with parameters $a$ and $b$ fit from `min_dist`:

```math
v_{ij} = \left(1 + a\, \|y_i - y_j\|^{2b}\right)^{-1}
```

Optimisation proceeds with stochastic gradient descent and negative sampling.


### Concepts

* *n_neighbors:* Controls the balance between local and global structure. Small values focus
  on fine-grained local topology; large values preserve more global relationships. Typical
  range: 5--50.
* *min_dist:* The minimum distance between points in the embedding. Smaller values produce
  tighter, more detailed clusters; larger values spread the embedding out. Range: 0.0--1.0.
* *UMAP vs. t-SNE:* UMAP is faster ($\mathcal{O}(n \log n)$ vs. $\mathcal{O}(n^2)$ for vanilla
  t-SNE), preserves more global structure, and supports out-of-sample projection. t-SNE is
  still standard for its visual cluster separation on many benchmark datasets.
* *Out-of-Sample Extension:* After fitting, `umap_model.transform(X_new)` maps new points into
  the learned embedding. This is not supported by standard t-SNE.
* *Metric:* UMAP accepts any distance metric (Euclidean, cosine, Manhattan, precomputed).
  Cosine distance is preferred for high-dimensional text and embedding vectors.


### Samples


*Sample 1: Synthetic 3D Cluster Visualisation*

* *Data:* 150 synthetic points in 3 clusters, 3 features.
* *Scenario:* `eumap.py` compares the raw X1/X2 projection against the UMAP 2D embedding.
  The raw projection may show overlapping clusters; UMAP separates them by leveraging the
  third feature and the manifold structure across all three dimensions.

*Sample 2: Single-Cell RNA Sequencing*

* *Data:* Gene expression profiles of individual cells (~20,000 genes per cell).
* *Scenario:* UMAP has become the standard visualisation tool in single-cell genomics, largely
  replacing t-SNE. It runs faster on datasets of hundreds of thousands of cells and its global
  layout is more consistent across runs with the same random seed.

*Sample 3: Sentence Embedding Exploration*

* *Data:* 10,000 sentences encoded as 768-dimensional vectors by a pre-trained language model.
* *Scenario:* UMAP reduces the embeddings to 2D for exploration. Topics cluster spatially and
  the out-of-sample transform allows new sentences to be placed in the same map without
  rerunning the full embedding.
