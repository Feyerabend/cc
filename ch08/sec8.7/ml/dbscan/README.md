
## DBSCAN

DBSCAN (Density-Based Spatial Clustering of Applications with Noise) groups points that
are closely packed together and marks points in low-density regions as outliers. Unlike
K-means, it requires no prior specification of the number of clusters and can discover
clusters of arbitrary shape. Noise points -- those that do not belong to any dense region --
are labelled explicitly rather than forced into the nearest cluster.

Two files are provided:

- `simple.py` -- a from-scratch DBSCAN implementation in pure Python.
- `visual.py` -- the same algorithm extended to render a PNG image of the clustering result
  using Pillow.


### Mathematics

Two parameters govern the algorithm: $\varepsilon$ (neighbourhood radius) and $\text{MinPts}$
(minimum points to form a dense region).

A point $p$ is a *core point* if at least $\text{MinPts}$ points lie within distance
$\varepsilon$:

```math
|N_\varepsilon(p)| \geq \text{MinPts}, \quad N_\varepsilon(p) = \{q : d(p, q) \leq \varepsilon\}
```

A point $q$ is *density-reachable* from $p$ if there exists a chain of core points
$p = p_1, p_2, \ldots, p_n = q$ where each $p_{i+1} \in N_\varepsilon(p_i)$.

A cluster is a maximal set of mutually density-connected points. Any point that is not
density-reachable from any core point is labelled *noise* ($-1$).

Time complexity is $\mathcal{O}(n^2)$ for the naive implementation here (each point scans
all others to find neighbours). A spatial index (k-d tree, ball tree) reduces this to
$\mathcal{O}(n \log n)$ on average.


### Concepts

* *Core, Border, Noise:* Core points anchor clusters; border points are density-reachable from
  a core point but are not core points themselves; noise points belong to no cluster.
* *$\varepsilon$ and MinPts:* The two parameters interact. Small $\varepsilon$ or large MinPts
  produces more noise; large $\varepsilon$ or small MinPts merges distinct clusters. A k-distance
  plot (sorted distance to the $k$-th nearest neighbour) helps select $\varepsilon$.
* *Arbitrary Shape:* Because cluster membership is defined by reachability rather than distance
  to a centroid, DBSCAN naturally finds elongated, crescent, or ring-shaped clusters that
  K-means cannot separate.
* *Sensitivity to Density Variation:* DBSCAN struggles when clusters have very different
  densities, because a single $\varepsilon$ cannot simultaneously capture both sparse and
  dense regions. HDBSCAN generalises to variable density.
* *Determinism:* Border points may be assigned to different clusters depending on traversal
  order; core-point assignments are deterministic.


### Samples


*Sample 1: Geospatial Hotspot Detection*

* *Data:* GPS coordinates of reported incidents in a city.
* *Scenario:* DBSCAN identifies crime hotspots as dense spatial clusters without requiring a
  pre-specified count. Isolated incidents in quiet areas are naturally labelled as noise,
  reducing false positives in hotspot maps.

*Sample 2: Anomaly Detection in Network Traffic*

* *Data:* Per-connection features (packet size, duration, port numbers) from a network monitor.
* *Scenario:* Normal traffic forms several dense clusters; malicious or unusual connections
  appear as sparse outliers. DBSCAN's noise label directly flags candidates for review without
  a separate anomaly-scoring step.

*Sample 3: Customer Behaviour Segmentation*

* *Data:* Purchase frequency and average basket size per customer.
* *Scenario:* DBSCAN discovers non-spherical purchasing-behaviour clusters (e.g., a crescent
  of customers who buy frequently but in small amounts versus a compact cluster of bulk buyers),
  which K-means would split or merge incorrectly.
