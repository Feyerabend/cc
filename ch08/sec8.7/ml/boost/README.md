
## Gradient Boosting

Gradient Boosting is a machine learning technique for supervised learning tasks like regression,
classification, and ranking, where the goal is to build a strong predictive model by combining
multiple weak learners, typically decision trees. The core concept is to iteratively train weak
models that correct the errors of their predecessors, optimising a loss function through gradient
descent. Each weak learner focuses on the residuals or errors of the previous ensemble, gradually
improving predictions. This sequential approach makes gradient boosting powerful for capturing
complex patterns in data, often outperforming simpler models like linear regression or single
decision trees.

The mathematical foundation of gradient boosting lies in minimising a loss function over a dataset.
For a dataset with $n$ samples and $m$ features, let $y_i$ be the true label and $\hat{y}_i$ the
predicted value for the $i$-th sample. The objective is to find a function $F(x)$ that minimises
the loss:

```math
L = \sum_{i=1}^n l(y_i, \hat{y}_i)
```

where $l(y_i, \hat{y}_i)$ is a differentiable loss function, such as mean squared error
$(y_i - \hat{y}_i)^2$ for regression or logistic loss for classification. Gradient boosting
constructs $F(x)$ as an additive model:

```math
F(x) = \sum_{m=1}^M f_m(x)
```

where $f_m(x)$ is the $m$-th weak learner (usually a decision tree), and $M$ is the number of
iterations. At each iteration, a new tree is added to minimise the loss by following the negative
gradient of the loss function with respect to the current predictions:

```math
g_i = -\frac{\partial l(y_i, \hat{y}_i)}{\partial \hat{y}_i}
```

The new tree $f_m(x)$ is fitted to predict these gradients (or pseudo-residuals), and its
contribution is scaled by a learning rate $\eta$, typically small (e.g., 0.1), to ensure gradual
improvement and avoid overfitting. The update rule is:

```math
\hat{y}_i^{(m)} = \hat{y}_i^{(m-1)} + \eta f_m(x_i)
```

This process continues until a specified number of trees is reached or the loss converges. The
learning rate and number of trees are key hyperparameters, balancing model complexity and predictive
accuracy.

To illustrate, consider a regression example using Python and scikit-learn’s GradientBoostingRegressor.
Suppose we have a dataset with one feature $x$ and target $y$:

```python
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# Generate sample data
X = np.random.rand(100, 1) * 10
y = 3 * X.flatten() + np.random.normal(0, 1, 100)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
model.fit(X_train, y_train)

# Predict and evaluate
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"Mean Squared Error: {mse:.2f}")
```

This code trains a gradient boosting model with 100 trees, a learning rate of 0.1, and a
maximum tree depth of 3, then evaluates its performance on a test set. The model learns to
predict $y$ by iteratively fitting trees to the residuals of prior predictions.

For a classification example, consider a binary classification task using the Iris dataset:

```python
from sklearn.datasets import load_iris
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load Iris dataset and create binary classification problem
iris = load_iris()
X = iris.data
y = (iris.target == 0).astype(int)  # Class 0 vs. others

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
model.fit(X_train, y_train)

# Predict and evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy:.2f}")
```

This example uses logistic loss for binary classification, demonstrating gradient boosting’s
versatility across different problem types. The model iteratively builds trees to minimise
classification errors, with hyperparameters controlling the trade-off between accuracy and
overfitting.

In real-world applications, gradient boosting excels in scenarios requiring high predictive
accuracy on structured data. For instance, in finance, it is used for credit risk modelling,
predicting loan defaults by learning from features like credit scores and income. In e-commerce,
it powers recommendation systems by ranking products based on user behaviour. In healthcare, it
predicts patient outcomes from medical records, capturing complex interactions between variables.
Its ability to handle numerical and categorical features, along with robustness to noisy data,
makes it widely applicable.

Compared to other machine learning algorithms, gradient boosting often outperforms simpler models
like logistic regression or single decision trees due to its ensemble nature. However, it can be
slower to train than random forests, which build trees independently rather than sequentially.
Unlike neural networks, gradient boosting requires less data preprocessing and is more interpretable
through feature importance scores, but it may struggle with unstructured data like images or text,
where deep learning excels. Its sequential training process also makes it computationally intensive,
though optimisations in modern implementations mitigate this.

Two popular implementations of gradient boosting are [XGBoost](./xgboost/) and [LightGBM](./lightgbm/).
XGBoost enhances gradient boosting with regularisation to prevent overfitting, parallel tree construction,
and sparse data handling, making it highly efficient and scalable. LightGBM further optimises performance
by using histogram-based splitting and leaf-wise tree growth, which reduces memory usage and speeds
up training on large datasets. Both extend the core gradient boosting framework, offering improved speed,
scalability, and flexibility for real-world applications.


### Samples


*Sample 1: House Price Prediction*

* *Features:* Square footage, number of bedrooms, neighbourhood, age of property, proximity to amenities.
* *Target:* Sale price (continuous).
* *Scenario:* A real estate platform trains a gradient boosting regressor on historical sales data.
  Because the relationship between features and price is highly non-linear and interaction-heavy,
  boosted trees outperform linear regression significantly.

*Sample 2: Fraud Detection*

* *Features:* Transaction amount, merchant category, time since last transaction, geographic distance
  from previous transaction, device fingerprint.
* *Target:* Fraudulent (Yes / No).
* *Scenario:* A payment processor applies gradient boosting to flag suspicious transactions in real
  time. The sequential residual-fitting approach captures rare but systematic patterns in fraud
  behaviour that simpler models miss.

*Sample 3: Web Search Ranking*

* *Features:* Query--document relevance signals, user click history, page freshness, authority score.
* *Target:* Relevance ranking score.
* *Scenario:* A search engine uses gradient boosting with a ranking loss function (LambdaMART) to
  order search results. Feature importances reveal which signals most strongly predict user
  satisfaction, informing future feature engineering.

