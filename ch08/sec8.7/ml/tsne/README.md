
## t-SNE

t-SNE (t-Distributed Stochastic Neighbor Embedding) is a dimensionality reduction technique designed
specifically for visualisation. It maps high-dimensional data to 2D (or 3D) while preserving local
structure: points that are close in the original space are placed close in the embedding, so natural
clusters become visible to the human eye.

Unlike PCA, which preserves global variance, t-SNE focuses on local neighbourhood relationships. It
does not cluster the data -- the cluster structure you see in a t-SNE plot is a consequence of proximity
in the original space, not a labelling decision made by the algorithm. Explicit clustering (e.g. K-means)
must be applied as a separate step if discrete labels are needed.

The two files here work in a pipeline: `tsne.py` implements the algorithm and writes a 2D embedding to
`tsne_output.tsv`; `visual.py` reads that file, optionally runs K-means on the 2D coordinates, and
renders a scatter plot.


### Mathematics

t-SNE converts pairwise distances to probabilities. In high-dimensional space, the affinity between
points $i$ and $j$ is modelled as a Gaussian:

```math
p_{j|i} = \frac{\exp(-\|x_i - x_j\|^2 / 2\sigma_i^2)}{\sum_{k \neq i} \exp(-\|x_i - x_k\|^2 / 2\sigma_i^2)}
```

The bandwidth $\sigma_i$ is set per-point to match a target *perplexity* (a measure of the effective
number of neighbours). The joint probability is symmetrised: $p_{ij} = (p_{j|i} + p_{i|j}) / 2n$.

In the 2D embedding, affinities use a Student-t distribution with one degree of freedom (a Cauchy):

```math
q_{ij} = \frac{(1 + \|y_i - y_j\|^2)^{-1}}{\sum_{k \neq l}(1 + \|y_k - y_l\|^2)^{-1}}
```

The heavy tail of the Student-t distribution allows dissimilar points to be placed far apart, resolving
the crowding problem that occurs when using a Gaussian in both spaces.

The embedding is found by minimising the Kullback-Leibler divergence between the two distributions:

```math
\mathcal{L} = \text{KL}(P \| Q) = \sum_{ij} p_{ij} \log \frac{p_{ij}}{q_{ij}}
```

Gradient descent with momentum optimises $\mathcal{L}$ over the 2D coordinates $y_i$. An early
exaggeration phase (multiplying $p_{ij}$ by a factor ~12 for the first iterations) helps separate
clusters before fine-grained refinement.


### Concepts

* *Perplexity:* Controls the effective number of neighbours. Typical values: 5--50. Lower values
  focus on very local structure; higher values consider broader neighbourhoods.
* *Local vs. Global:* t-SNE preserves local distances well but distorts global structure. Cluster
  separations and inter-cluster distances in a t-SNE plot are not directly interpretable.
* *Non-determinism:* Results depend on the random initialisation. Run multiple times with different
  seeds if you suspect artefacts.
* *Complexity:* $\mathcal{O}(n^2)$ in time and space. Barnes-Hut approximations reduce this to
  $\mathcal{O}(n \log n)$ for large datasets.
* *Not for Downstream Use:* t-SNE embeddings are for visualisation only. Do not use the 2D
  coordinates as features for machine learning models.


### Samples


*Sample 1: MNIST Digit Visualisation*

* *Data:* 10,000 MNIST digit images (784 dimensions each).
* *Scenario:* A t-SNE plot of MNIST shows 10 clearly separated clusters corresponding to the 10
  digit classes, even though no label information is used during embedding. This classic demonstration
  validated t-SNE when it was introduced in 2008.

*Sample 2: Single-Cell RNA Sequencing*

* *Data:* Gene expression profiles of individual cells (thousands of genes per cell).
* *Scenario:* Biologists use t-SNE to map thousands of cells to 2D, revealing distinct cell types
  as separate clusters. t-SNE has become standard in single-cell genomics for exploratory analysis.

*Sample 3: Embedding Space of a Language Model*

* *Data:* Word or sentence embeddings from a trained language model (e.g., 512-dimensional vectors).
* *Scenario:* A t-SNE plot of word embeddings shows that semantically related words cluster together:
  animal names near each other, country names forming a separate cluster, verbs of motion grouping
  together. This visualises what the model has learned without looking at the raw weight matrices.
