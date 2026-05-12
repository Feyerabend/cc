
## Random Forest

Random Forest is an ensemble learning method that operates by constructing a multitude of
[decision trees](./../dtree/) during training and outputting the mode of the classes
(classification) or mean prediction (regression) of the individual trees. It combines
bagging (bootstrap aggregating) and random feature selection to create a diverse set of
trees, reducing overfitting and improving generalisation.


### Mathematics

At each split the algorithm chooses the feature and threshold that minimise weighted impurity.
Two common criteria are Gini impurity and entropy:

```math
\text{Gini} = 1 - \sum_{k=1}^{K} p_k^2
```

```math
H = -\sum_{k=1}^{K} p_k \log_2 p_k
```

where $p_k$ is the fraction of samples at the node belonging to class $k$.

For a forest of $T$ trees the final prediction aggregates individual tree outputs. For
classification, the majority vote is taken:

```math
\hat{y} = \arg\max_{k} \sum_{t=1}^{T} \mathbf{1}[\hat{y}_t = k]
```

For regression, the mean is used:

```math
\hat{y} = \frac{1}{T} \sum_{t=1}^{T} \hat{y}_t
```

At each split only $m$ features are considered (typically $m = \sqrt{p}$ for classification
and $m = p/3$ for regression, where $p$ is the total number of features). This decorrelates
the trees and is the key difference from plain bagged trees.


### Concepts

* *Bootstrap Sampling:* Each tree is trained on a random sample drawn with replacement from
  the training set, approximately 63% of the original samples. The remaining ~37% form the
  out-of-bag set used for unbiased error estimation.
* *Feature Randomness:* Considering only a random subset of features at each split prevents
  any single dominant feature from appearing in every tree, forcing diversity in the ensemble.
* *Variance Reduction:* Individual deep trees have low bias but high variance. Averaging many
  uncorrelated trees keeps the bias low while reducing variance by a factor of roughly $1/T$.
* *Feature Importance:* A tree's contribution can be measured by how much each feature
  decreases impurity across all splits, averaged over all trees. This gives a natural ranking
  of predictors.
* *Out-of-Bag Error:* Because each tree sees only ~63% of training samples, predictions on
  the held-out 37% provide a free estimate of generalisation error without a separate
  validation set.


### Samples


*Sample 1: Wine Quality Prediction*

* *Features:* Fixed acidity, volatile acidity, citric acid, residual sugar, chlorides,
  sulphates, alcohol content (11 physicochemical measurements).
* *Target:* Quality score (3--8) mapped to Low / Medium / High.
* *Scenario:* A winery uses a random forest to predict quality ratings from lab measurements,
  enabling early feedback during fermentation before human tasters evaluate the batch.

*Sample 2: Credit Risk Assessment*

* *Features:* Income, employment tenure, debt-to-income ratio, credit utilisation, number of
  late payments.
* *Target:* Default (Yes / No).
* *Scenario:* A bank trains a random forest on historical loan outcomes. Feature importances
  reveal that credit utilisation and late-payment history are the strongest predictors,
  informing which data to collect for future applicants.

*Sample 3: Remote Sensing Land Cover*

* *Features:* Spectral bands from satellite imagery (near-infrared, red, green, SWIR).
* *Target:* Land cover class (forest, cropland, urban, water, bare soil).
* *Scenario:* Geographers classify land cover across a region from multispectral satellite
  imagery. Random forests handle the high-dimensional, non-linear spectral signatures well and
  provide per-pixel class probabilities alongside the classification map.


### Strengths and Limitations

*Strengths:* handles high-dimensional data, resistant to overfitting through ensemble averaging,
captures non-linear relationships without feature scaling, provides built-in feature importances
and out-of-bag error estimates.

*Limitations:* less interpretable than single decision trees, slower prediction than linear
models when the forest is large, can struggle with very high-cardinality categorical features
without careful encoding.
