
## XGBoost

XGBoost, short for *eXtreme Gradient Boosting*, is a machine learning algorithm designed
for supervised learning tasks like classification, regression, and ranking. It builds on
the concept of gradient boosting, where weak learners, typically decision trees, are
combined sequentially to form a strong predictive model. Each weak learner corrects the
errors of its predecessors, resulting in a model that improves iteratively. XGBoost stands
out for its efficiency, scalability, and ability to handle large datasets with high-dimensional
features.

The core idea behind XGBoost is to minimise a loss function by adding decision trees that
predict the residuals or errors of prior models. Unlike traditional gradient boosting, XGBoost
incorporates regularisation to prevent overfitting, parallel processing to speed up computation,
and a sparse-aware algorithm to handle missing data efficiently. It also supports custom loss
functions, allowing flexibility for specific tasks. The algorithm optimises a combination of a
loss function, such as mean squared error for regression or log loss for classification, and
a regularisation term that penalises model complexity.

Mathematically, XGBoost aims to minimise an objective function defined as the sum of a loss
term and a regularisation term. For a dataset with $n$ samples and $m$ features, let $y_i$ be
the true label and $\hat{y}_i$ be the predicted value for the $i$-th sample. The objective
function at iteration $t$ is:

```math
\text{Obj} = \sum_{i=1}^n l(y_i, \hat{y}_i^{(t)}) + \sum_{k=1}^t \Omega(f_k)
```

Here, $l(y_i, \hat{y}_i^{(t)})$ is the loss function measuring the difference between the true
and predicted values, such as $(y_i - \hat{y}_i)^2$ for regression. The term $\Omega(f_k)$ is
the regularization penalty for the $k$-th tree, defined as:

```math
\Omega(f) = \gamma T + \frac{1}{2} \lambda \sum_{j=1}^T w_j^2
```

where $T$ is the number of leaves in the tree, $w_j$ is the weight of the $j$-th leaf, $\gamma$
controls the penalty on the number of leaves, and $\lambda$ controls the penalty on the leaf weights.
This regularisation discourages overly complex trees, improving generalisation.

XGBoost uses a second-order Taylor approximation of the loss function to optimise the objective
efficiently. For each iteration, it approximates the loss using both the gradient (first derivative)
and the Hessian (second derivative) of the loss with respect to the predictions. This allows the
algorithm to find the optimal structure and weights for each new tree by solving a quadratic
optimisation problem. The gain for splitting a node in a tree is calculated as:

```math
\text{Gain} = \frac{1}{2} \left[ \frac{(\sum_{i \in I_L} g_i)^2}{\sum_{i \in I_L} h_i + \lambda} + \frac{(\sum_{i \in I_R} g_i)^2}{\sum_{i \in I_R} h_i + \lambda} - \frac{(\sum_{i \in I} g_i)^2}{\sum_{i \in I} h_i + \lambda} \right] - \gamma
```

where $I_L$ and $I_R$ are the sets of instances in the left and right child nodes, $I$ is the parent
node, $g_i$ is the gradient, and $h_i$ is the Hessian for the $i$-th instance. This gain guides the
tree's splitting decisions, balancing predictive power and model simplicity.

To illustrate, consider a simple regression example using Python and the XGBoost library. Suppose we
have a dataset with one feature $x$ and a target $y$, and we want to predict $y$ using XGBoost.
The code below trains a model and makes predictions:

```python
import xgboost as xgb
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# Generate sample data
X = np.random.rand(100, 1) * 10
y = 3 * X.flatten() + np.random.normal(0, 1, 100)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create DMatrix for XGBoost
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

# Set parameters
params = {
    'objective': 'reg:squarederror',
    'max_depth': 3,
    'eta': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8
}

# Train model
model = xgb.train(params, dtrain, num_boost_round=100)

# Predict and evaluate
y_pred = model.predict(dtest)
mse = mean_squared_error(y_test, y_pred)
print(f"Mean Squared Error: {mse:.2f}")
```

This example demonstrates loading data into XGBoost’s DMatrix format, setting hyperparameters like
learning rate ($\eta$), tree depth, and subsampling ratios, training the model, and evaluating its
performance. The parameters control the trade-off between model complexity and accuracy, with
regularisation terms like $\lambda$ and $\gamma$ embedded in the algorithm’s optimisation process.

For a classification task, consider a binary classification problem using the Iris dataset, where
we predict whether a sample is of a specific class. The code below shows how to implement this:

```python
from sklearn.datasets import load_iris
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load Iris dataset and create binary classification problem
iris = load_iris()
X = iris.data
y = (iris.target == 0).astype(int)  # Class 0 vs. others

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create DMatrix
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

# Set parameters
params = {
    'objective': 'binary:logistic',
    'max_depth': 3,
    'eta': 0.1,
    'eval_metric': 'logloss'
}

# Train model
model = xgb.train(params, dtrain, num_boost_round=100)

# Predict and evaluate
y_pred = (model.predict(dtest) > 0.5).astype(int)
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy:.2f}")
```

This classification example uses the logistic loss function and evaluates the model with
log loss, showcasing XGBoost’s flexibility across different tasks. The algorithm’s ability
to handle both numerical and categorical features, along with its robustness to missing
values, makes it versatile for real-world datasets.

In practice, XGBoost’s performance depends on tuning hyperparameters like learning rate,
tree depth, and subsampling ratios. Techniques like cross-validation and early stopping
can further optimise the model. Its paralleled tree construction and hardware acceleration
make it computationally efficient, while features like feature importance scores provide
interpretability.
