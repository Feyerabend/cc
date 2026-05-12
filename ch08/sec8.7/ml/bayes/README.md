
## Naive Bayes

Naive Bayes classifiers stem from Bayes’ Theorem, formulated by *Thomas Bayes* in the 18th century.
However, the "naive" assumption—treating features as conditionally independent—emerged much later.
The model became practically relevant in the 1950s and 1960s with the development of early machine
learning algorithms. Despite its simplicity, it gained popularity in *text classification*,
*spam filtering*, and other probabilistic inference tasks, especially in the 1990s with the growth
of digital text processing.

Naive Bayes is a *probabilistic classifier* based on Bayes’ Theorem:

```math
P(C \mid X) = \frac{P(X \mid C) \cdot P(C)}{P(X)}
```

Where:
- `C` is a class label.
- `X = (x₁, x₂, ..., xₙ)` is the feature vector.
- `P(C | X)` is the posterior probability of class `C` given the features.
- `P(X | C)` is the likelihood.
- `P(C)` is the prior probability of class `C`.
- `P(X)` is the evidence (a normalization constant).

The "naive" part comes from assuming that all features `xᵢ`
are *conditionally independent* given the class `C`:

```math
P(X \mid C) = \prod_{i=1}^{n} P(x_i \mid C)
```

This simplification allows efficient learning and prediction.

### Training and Prediction

1. *Training* involves estimating:
   - Class priors `P(C)`.
   - Feature likelihoods `P(xᵢ | C)`, using frequency counts or
     distributions (e.g. Gaussian for continuous features).

2. *Prediction*:
   - For a new input `X`, compute the posterior for each class
     and choose the one with the highest score.

### Common Variants

- *Multinomial Naive Bayes*: Suitable for discrete features like word counts in documents.
- *Bernoulli Naive Bayes*: Assumes binary features (word present or not).
- *Gaussian Naive Bayes*: Assumes features are continuous and normally distributed.

### Use Cases

- *Spam detection*: Classify emails as spam/ham.
- *Text classification*: News categorisation, sentiment analysis.
- *Medical diagnosis*: Predict disease likelihood from symptoms.
- *Document classification*: Fast, scalable method even with large vocabularies.

Naive Bayes is particularly effective when:
- The independence assumption roughly holds.
- There is a large number of features but relatively few training samples.

The code often uses *Laplace smoothing*: E.g. in the case of spam Laplace smoothing adds 1 to
all word counts to avoid zero probabilities for unseen words during prediction.  
This ensures that every word has a non-zero chance of occurring, stabilising the model
especially for small datasets.

### Naive Bayes Variants

| Variant             | Input Type         | Feature Model                        | Common Use Case                |
|---------------------|--------------------|--------------------------------------|--------------------------------|
| *Multinomial NB*  | Discrete counts     | Frequencies of features (e.g. word counts) | Text classification, spam filtering |
| *Bernoulli NB*    | Binary features     | Presence/absence of features         | Binary text features, document classification |
| *Gaussian NB*     | Continuous values   | Assumes features follow a Gaussian distribution | Sensor data, medical measurements, numerical features |

- *Multinomial* is best when feature frequency matters (e.g., "cheap" appearing 3 times).
- *Bernoulli* is suitable when only presence or absence is relevant (e.g., "contains the word 'buy'?").
- *Gaussian* fits continuous domains where values follow roughly normal distributions.


### Bayesian Networks: Definition and Function

Bayesian networks, also known as belief networks or probabilistic directed acyclic graphs (DAGs),
are graphical models that represent a set of variables and their probabilistic dependencies.
They combine graph theory, probability theory, and statistics to enable reasoning under uncertainty.

A Bayesian network consists of:
1. Nodes: Representing random variables.
2. Directed Edges: Indicating conditional dependencies, with the graph being acyclic (no loops).
3. Conditional Probability Distributions (CPDs): Associated with each node, quantifying the effect
   of parent nodes.

The key idea is to leverage conditional independence to simplify complex probability calculations.
For instance, in a medical diagnosis system, nodes might represent symptoms, diseases, and test
results, with edges showing how a disease influences symptoms. Given observed symptoms, the network
can compute the probability of specific diseases, as exemplified in diagnostic applications like
determining malaria likelihood based on fever and travel history.

Judea Pearl formalised Bayesian networks in his 1988 book, *Probabilistic Reasoning in Intelligent Systems*.
Also see: Brockman, J. (red.) (2019). *Possible minds: twenty-five ways of looking at AI*. New York: Penguin Press.


### Samples


*Sample 1: Spam Filtering*

* *Features:* Word presence/frequency in email body and subject (Multinomial or Bernoulli NB).
* *Target:* Spam / Ham.
* *Scenario:* An email provider trains a Multinomial NB on a labelled corpus using Laplace
  smoothing to handle unseen words. Despite the independence assumption, the classifier achieves
  high precision and is fast enough to score millions of incoming messages per second.

*Sample 2: Medical Diagnosis from Symptoms*

* *Features:* Presence of symptoms (fever, cough, fatigue, rash) -- binary features.
* *Target:* Disease class (flu, cold, COVID, allergy).
* *Scenario:* A triage system uses Bernoulli NB to estimate the probability of each disease
  given reported symptoms. Because class priors reflect real-world base rates, the posterior
  probabilities are well-calibrated and help clinicians prioritise further testing.

*Sample 3: Temperature Prediction from Climate Data*

* *Features:* Month, geographic region, elevation, humidity (continuous).
* *Target:* Temperature range category (Cold / Mild / Hot).
* *Scenario:* A Gaussian NB models the conditional distribution of each feature per class
  as a univariate Gaussian. The resulting classifier is lightweight, interpretable, and
  suitable for deployment on resource-constrained weather sensors.
