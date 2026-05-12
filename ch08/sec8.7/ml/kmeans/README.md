
## K-means

K-means clustering is an algorithm that groups data points into a specified number of clusters
by finding the best positions for cluster centers. The basic idea is to minimise the total
distance between each data point and its nearest cluster center.

The algorithm starts by randomly placing K cluster centers (centroids) in your data space.
Then it repeatedly performs two main steps until the centroids stop moving significantly.
First, it assigns each data point to whichever centroid is closest to it, creating K groups.
Second, it recalculates each centroid's position by moving it to the average location of all
points assigned to that cluster.

This process continues iteratively because moving the centroids changes which points should
be assigned to which clusters, and reassigning points changes where the centroids should be
positioned. Eventually, the system reaches a stable state where the centroids don't move much
between iterations, meaning the algorithm has converged on a solution.

The "means" in K-means refers to this averaging process where centroids are positioned at the
mean (average) location of their assigned points. The algorithm is trying to find cluster
centers that minimise the sum of squared distances from each point to its assigned centroid,
which makes the clusters as compact as possible.

One important thing to understand is that K-means will always find K clusters, even if the data
doesn't naturally form that many groups. It's also sensitive to the initial placement of
centroids, which is why the algorithm is often run multiple times with different starting
positions to find the best solution.


### Mathematics

K-means minimises the within-cluster sum of squares (WCSS), also called inertia:

```math
J = \sum_{k=1}^{K} \sum_{x_i \in C_k} \|x_i - \mu_k\|^2
```

Where:
* $K$ is the number of clusters.
* $C_k$ is the set of points assigned to cluster $k$.
* $\mu_k$ is the centroid of cluster $k$.
* $\|x_i - \mu_k\|^2$ is the squared Euclidean distance from point $x_i$ to its centroid.

The centroid $\mu_k$ is updated each iteration as the mean of all assigned points:

```math
\mu_k = \frac{1}{|C_k|} \sum_{x_i \in C_k} x_i
```

The assignment step sets each point's cluster to the nearest centroid:

```math
c_i = \arg\min_{k} \|x_i - \mu_k\|^2
```

These two steps are alternated until the assignments stop changing, which is guaranteed because
each step either decreases $J$ or leaves it unchanged, and the number of possible assignments
is finite.


### Concepts

* *K (Number of Clusters):* The single hyperparameter the user must supply. There is no automatic
  way to choose K -- common heuristics include the elbow method (plotting WCSS against K and
  looking for a bend) and the silhouette score.
* *Centroid:* The mean position of all points in a cluster. It acts as the cluster's
  representative and may not coincide with any actual data point.
* *Convergence:* The algorithm has converged when no point changes its cluster assignment between
  iterations. In practice a small tolerance or a maximum iteration count is also used.
* *Sensitivity to Initialisation:* Different starting positions for the centroids can lead to
  different final clusters. Running the algorithm multiple times with different random seeds and
  keeping the run with the lowest WCSS is a common remedy.
* *K-means++:* An improved initialisation strategy that spreads the initial centroids apart by
  choosing each successive centroid with probability proportional to its squared distance from the
  nearest already-chosen centroid. This reduces the chance of poor convergence.
* *Euclidean Distance:* The standard distance metric used in K-means. Because it measures
  straight-line distance, K-means tends to produce spherical, roughly equal-sized clusters.


### Samples


*Sample 1: Customer Segmentation*

* *Data:* Customers described by average order value and number of purchases per year.
* *K:* 3 -- low-value infrequent buyers, mid-value regulars, high-value frequent buyers.
* *Scenario:* A retailer runs K-means to segment its customer base. The resulting cluster
  centroids define three personas that inform different marketing campaigns and loyalty programmes.

*Sample 2: Image Colour Quantisation*

* *Data:* The RGB pixel values of a photograph.
* *K:* 16 -- the desired palette size.
* *Scenario:* Each pixel is a point in 3-D colour space. K-means finds 16 representative
  colours and replaces every pixel with its nearest centroid colour, compressing the image
  while preserving broad colour structure.

*Sample 3: Document Clustering*

* *Data:* News articles represented as TF-IDF vectors.
* *K:* 10 -- one intended cluster per topic category.
* *Scenario:* A news aggregator clusters articles so that stories about the same event or
  topic land in the same group. The centroid of each cluster -- the average TF-IDF vector --
  highlights the keywords that define that topic.

