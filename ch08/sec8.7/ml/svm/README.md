
## Support Vector Machines

Support Vector Machines (SVMs) are powerful supervised learning algorithms, primarily
used for classification and regression tasks. Developed by Vladimir Vapnik and his
colleagues in the 1990s, SVMs became one of the most popular machine learning methods
due to their strong theoretical foundations and excellent performance on many real-world
problems.

The core idea is to find an optimal hyperplane that best separates data points belonging
to different classes in a high-dimensional feature space. Given two classes of points that
are linearly separable, there are infinitely many separating lines. The SVM finds the *best*
one: the hyperplane that maximises the margin between the closest data points of each class.
These closest points are called *support vectors*.


### Mathematics

Given $n$ training samples $(x_1, y_1), \ldots, (x_n, y_n)$ with $x_i \in \mathbb{R}^d$ and
$y_i \in \{-1, 1\}$, the hard-margin SVM finds the hyperplane $w \cdot x + b = 0$ that
maximises the margin $2 / \|w\|$:

```math
\min_{w,b} \frac{1}{2} \|w\|^2 \quad \text{subject to} \quad y_i(w \cdot x_i + b) \ge 1
```

For non-separable data the *soft-margin* SVM introduces slack variables $\xi_i \ge 0$ and a
regularisation parameter $C$:

```math
\min_{w,b,\xi} \frac{1}{2} \|w\|^2 + C \sum_{i=1}^n \xi_i \quad \text{subject to} \quad y_i(w \cdot x_i + b) \ge 1 - \xi_i
```

The *kernel trick* replaces every dot product $x_i \cdot x_j$ in the dual formulation with a
kernel function $K(x_i, x_j) = \phi(x_i) \cdot \phi(x_j)$, implicitly mapping data into a
higher-dimensional space without computing $\phi$ explicitly. Common kernels:

* *Linear:* $K(x_i, x_j) = x_i \cdot x_j$
* *Polynomial:* $K(x_i, x_j) = (x_i \cdot x_j + c)^d$
* *RBF / Gaussian:* $K(x_i, x_j) = \exp(-\gamma \|x_i - x_j\|^2)$
* *Sigmoid:* $K(x_i, x_j) = \tanh(\alpha\, x_i \cdot x_j + c)$


### Concepts

* *Support Vectors:* Only the training points that lie on or inside the margin boundaries
  determine the hyperplane. All other points can be removed without changing the solution.
  This makes SVMs memory-efficient at inference time.
* *Margin:* The distance $2 / \|w\|$ between the two margin hyperplanes. Maximising it
  reduces the VC dimension and improves generalisation.
* *C (Regularisation):* Controls the bias-variance trade-off. Small $C$ allows more margin
  violations (wider margin, higher bias); large $C$ penalises them heavily (narrower margin,
  lower bias).
* *Duality:* The primal problem is equivalent to a dual quadratic program whose solution
  naturally yields the support vectors and enables the kernel trick.
* *Multi-class:* SVMs are inherently binary. Multi-class problems are handled with
  One-vs-Rest (K classifiers) or One-vs-One ($K(K-1)/2$ classifiers).
* *SVR:* Support Vector Regression finds a function that deviates from observed values by
  at most $\epsilon$, while being as flat as possible.


### Samples


*Sample 1: Text Classification*

* *Features:* TF-IDF vectors of email body text (high-dimensional, sparse).
* *Target:* Spam / Not spam.
* *Scenario:* A linear-kernel SVM is well-suited to this task because text data is typically
  linearly separable in TF-IDF space. The sparsity of support vectors means the trained model
  is compact even when trained on millions of documents.

*Sample 2: Handwritten Digit Recognition*

* *Features:* Pixel intensities of 8×8 greyscale digit images (64 features).
* *Target:* Digit class (0--9).
* *Scenario:* An RBF-kernel SVM on the UCI digits dataset achieves ~99% test accuracy. The
  kernel implicitly maps pixel intensities into a space where digit classes become linearly
  separable without engineering explicit features.

*Sample 3: Protein Function Prediction*

* *Features:* Amino acid composition, physico-chemical properties, sequence motifs.
* *Target:* Functional class (enzyme, receptor, structural protein, etc.).
* *Scenario:* SVMs with specialised string kernels defined directly on amino acid sequences
  have historically achieved state-of-the-art results in bioinformatics, exploiting the kernel
  trick to operate in sequence space without a fixed-length feature vector.
