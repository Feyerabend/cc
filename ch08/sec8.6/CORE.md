
## Core Machine Learning Concepts and Algorithms

ML algorithms can be broadly categorised into:

* *Supervised Learning*: Algorithms that learn from labeled data, where the desired output
  is known for each input. The goal is to predict an output based on given input features.
* *Unsupervised Learning*: Algorithms that work with unlabelled data to find patterns or
  structures within the data without prior knowledge of the output.
* *Reinforcement Learning*: Algorithms where an agent learns to make decisions by interacting
  with an environment to maximise a cumulative reward signal.


### Table of Algorithms: Use Cases and Properties

| *Algorithm*                                                                                | *Type*        | *Typical Use Cases*                 | *Key Properties*                                                |
|--------------------------------------------------------------------------------------------|---------------|-------------------------------------|-----------------------------------------------------------------|
| [Linear Regression](./linear/)                                                             | Supervised    | Predicting continuous values        | Simple, interpretable, assumes linearity                        |
| [Logistic Regression](./logistic/)                                                         | Supervised    | Binary classification               | Probabilistic outputs, interpretable, linear decision boundary  |
| [Decision Trees](./dtree/)                                                                 | Supervised    | Classification and regression       | Interpretable, handles non-linear data, prone to overfitting    |
| [Random Forest](./forest/)                                                                 | Supervised    | General-purpose                     | Ensemble of trees, reduces overfitting, less interpretable      |
| [Support Vector Machine](./svm/)                                                           | Supervised    | High-dimensional classification     | Margin maximisation, kernel trick for non-linearity             |
| [K-Nearest Neighbours](./knn/) (KNN)                                                       | Supervised    | Classification, regression          | Instance-based, simple, no training phase                       |
| [Naive Bayes](./bayes/)                                                                    | Supervised    | Text classification, spam filtering | Probabilistic, strong independence assumptions                  |
| [Gradient Boosting](./boost/) ([XGBoost](./boost/xgboost/), [LightGBM](./boost/lightgbm/)) | Supervised    | Structured data                     | High accuracy, can overfit, less interpretable                  |
| [K-Means](./kmeans/)                                                                       | Unsupervised  | Clustering, segmentation            | Simple, assumes spherical clusters, sensitive to initialisation |
| [DBSCAN](./dbscan/)                                                                        | Unsupervised  | Clustering with noise               | Handles arbitrary shapes, density-based                         |
| [PCA](./pca/) (Principal Component Analysis)                                               | Unsupervised  | Dimensionality reduction            | Linear transformation, unsupervised, captures variance          |
| [t-SNE](./tsne/) / [UMAP](./umap/)                                                         | Unsupervised  | Visualisation, clustering           | Non-linear, preserves local structure, non-parametric           |
| [Apriori](./apriori/) / [FP-Growth](./apriori/)                                            | Unsupervised  | Market basket analysis              | Association rule mining                                         |
| [Reinforcement Learning](./rl/)                                                            | Reinforcement | Game AI, robotics, control          | Trial-and-error learning, reward signal                         |



### Supervised Learning

Supervised learning algorithms learn from data where the correct output is already known.

#### Linear Regression

* *Principles*: Linear Regression is a fundamental statistical method used to find the
  best-fitting straight line (or hyperplane in higher dimensions) that describes the
  relationship between a dependent variable and one or more independent variables. It
  relies on minimising the sum of squared errors (least squares).
* *Use Cases*: Predicting continuous outcomes, such as house prices based on size and
  location, sales forecasting based on advertising spend, or student performance based
  on study hours.
* *Statistical Relation*: It is a core statistical method focused on finding linear
  relationships in data by minimising the sum of squared errors. ML frameworks allow
  for efficient computation on large datasets and handling of multiple features.

#### Logistic Regression

* *Principles*: Developed by statistician David Cox in 1958, Logistic Regression emerged
  as a powerful statistical model for binary classification, specifically designed to model
  the probability of a binary outcome. It is based on maximum likelihood estimation.
* *Use Cases*: Binary classification problems like predicting whether a customer will churn,
  classifying an email as spam, or diagnosing the presence or absence of a disease.
* *Statistical Relation*: It is a statistical model, specifically a generalised linear model,
  that uses the logistic function to model binary outcomes based on maximum likelihood
  estimation. ML provides tools for scaling, regularisation, and integration into production
  systems.

#### Other Supervised Algorithms

* *Decision Trees*: Can be seen as a non-parametric statistical method that partitions the
  feature space into a set of rectangular regions. The splits are determined by statistical
  measures like Gini impurity or information gain (entropy). They are interpretable and can
  handle non-linear relationships but are prone to overfitting.
* *Support Vector Machine (SVM)*: A discriminative classifier that finds an optimal hyperplane
  that maximally separates data points of different classes. It has strong theoretical
  foundations in statistical learning theory (VC). The "kernel trick" allows it to implicitly
  map data into higher-dimensional spaces, enabling non-linear separation.
* *K-Nearest Neighbours (KNN)*: A non-parametric, instance-based method. Its statistical
  foundation lies in the idea that similar data points are likely to belong to the same class
  or have similar values. It relies on distance metrics (e.g., Euclidean distance).
* *Naive Bayes*: Based on Bayes' theorem of conditional probability, assuming strong (naive)
  independence between features given the class. This is a probabilistic statistical model.
  It is very efficient and performs well even with limited data due to its strong assumptions.
* *Random Forest*: An ensemble method built upon decision trees. It uses bootstrapping (sampling
  with replacement) and random feature selection, both core statistical sampling techniques,
  to create multiple trees. The final prediction is often an average (regression) or majority
  vote (classification), reducing variance.
* *Gradient Boosting (XGBoost, LightGBM)*: An ensemble technique that builds trees sequentially,
  with each new tree trying to correct the errors of the previous ones. It leverages the concept
  of gradient descent, a core optimisation algorithm in statistics and mathematics, to minimise
  a loss function.


### Unsupervised Learning

Unsupervised learning algorithms aim to find patterns or structures in unlabelled data.

#### Algorithms

* *K-Means*: A centroid-based clustering algorithm. It aims to partition data into K clusters such
  that each data point belongs to the cluster with the nearest mean. It relies on minimising
  within--cluster variance (sum of squared distances), a statistical measure of spread.
* *DBSCAN*: A density-based clustering algorithm. It identifies clusters as high-density regions
  separated by low-density regions. It doesn't assume spherical clusters and can find arbitrarily
  shaped clusters, and can identify outliers. It uses the statistical concept of local density.
* *PCA (Principal Component Analysis)*: A linear dimensionality reduction technique. It finds
  orthogonal principal components that capture the maximum variance in the data. This involves
  eigenvalue decomposition of the covariance matrix, a core concept in multivariate statistics.
* *t-SNE / UMAP*: Non-linear dimensionality reduction techniques that focus on preserving local
  and global structures in the data, respectively. Their underlying principles still relate to
  manifold learning and preserving relationships (distances or similarities) between data points
  in a lower-dimensional space.
* *Apriori / FP-Growth*: Algorithms for discovering association rules in transactional datasets.
  They identify frequently occurring itemsets and then generate rules based on statistical measures
  like support, confidence, and lift.


### Reinforcement Learning

* *Overview and Applications*: Reinforcement Learning (RL) involves an agent learning to make
  decisions by interacting with an environment to maximise a cumulative reward signal. While
  distinct from supervised/unsupervised learning, it's deeply rooted in statistical decision
  theory, Markov Decision Processes (MDPs), and dynamic programming. The agent estimates
  state-action values or policies based on observed rewards, a statistical estimation problem.
* *Applications*: Game AI, robotics, and control systems. Examples include AlphaGo and
  self-driving cars.


### Why Classification and Clustering are Fundamental

When you first begin learning about machine learning, the scope of the field can appear quite
limited. At first glance, tasks like classification and clustering may seem "simple," but their
perceived simplicity lies not in a lack of complexity, but in their foundational role. They enable
machines to categorise and organise vast amounts of information with a speed and scale that
far surpass human capability. The simplicity of their task definitions masks the sophisticated
statistical and computational techniques required to solve them effectively, especially when
applied to complex, real-world data.

1. *Fundamental Building Blocks*: Classification and clustering are often the *entry points*
   into machine learning because they represent core cognitive tasks that humans perform instinctively.
    * *Classification:* "Is this X or Y?" "What category does this belong to?" This is how we
      organise and understand the world.
    * *Clustering:* "What groups exist within this data?" "Are there natural segments?" This is
      how we identify patterns and structures without prior labels.
2. *Ubiquitous Problems*: Despite seeming simple in a way, these tasks are incredibly common
   and valuable across almost every industry:
    * *Business:* Customer segmentation (clustering), fraud detection (classification), lead
      scoring (classification), product recommendation (can involve both).
    * *Healthcare:* Disease diagnosis (classification), patient subgrouping (clustering).
    * *Science:* Classifying celestial objects, identifying gene expression patterns, grouping species.
    * *Everyday Life:* Spam filtering, facial recognition, news categorisation.
3. *Data Availability and Definition*:
    * *Classification:* Requires *labeled data*, meaning you need examples where the correct
      category is already known. This kind of data is relatively common (e.g., historical records
      of transactions, medical diagnoses).
    * *Clustering:* Is *unsupervised*, meaning it doesn't require pre-labeled data. This makes
      it powerful for exploratory data analysis when you don't know what patterns to look for.
4. *Stepping Stones to Complexity*: While the *tasks* themselves might appear simple, the *data*
   they operate on is often incredibly complex, high-dimensional, and noisy.
    * For example, classifying an image as a "cat" or "dog" is a simple human task, but for a
      computer, it involves processing millions of pixels and learning intricate features.
    * Clustering millions of customer transactions to find meaningful segments is by no means simple.
5. *Benchmarking and Interpretability*:
    * Simple classification and clustering tasks often serve as excellent benchmarks for new
      algorithms.
    * Many of the simpler algorithms (Linear Regression, Logistic Regression, Decision Trees,
      K-Means, KNN) are also highly *interpretable*. This is crucial in many real-world applications
      where you need to understand *why* a decision was made (e.g., credit scoring, medical diagnosis).
6. *Foundation for Advanced Tasks*: Classification and clustering are often components of much
   more complex systems.
    * Object detection (where an image contains multiple objects to be identified and localised)
      involves repeated classification of regions within an image.
    * Natural Language Processing often relies on classifying words or sentences.
    * Recommendation systems use clustering to group similar users or items, and then
      classification/regression to predict preferences.

*Continue [deep learning](./DEEP.md) ..*
