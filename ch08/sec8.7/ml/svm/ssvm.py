import numpy as np

# normalize dataset
def normalize(X):
    X = np.array(X)
    ranges = X.max(axis=0) - X.min(axis=0)
    ranges[ranges == 0] = 1  # Avoid division by zero!
    return (X - X.min(axis=0)) / ranges

class SVM:
    def __init__(self, learning_rate=0.01, lambda_param=0.01, n_iters=1000):
        self.lr = learning_rate
        self.lambda_param = lambda_param
        self.n_iters = n_iters
        self.w = None
        self.b = None

    def fit(self, X, y):
        X = np.array(X)
        y = np.array(y)
        n_samples, n_features = X.shape

        # Ensure labels are +1 or -1
        y_ = np.where(y <= 0, -1, 1)

        # Initialize weights and bias
        self.w = np.zeros(n_features)
        self.b = 0.0

        for _ in range(self.n_iters):
            for idx in range(n_samples):
                x_i = X[idx]
                y_i = y_[idx]
                # Check if the point is within the margin or misclassified
                if y_i * (np.dot(self.w, x_i) + self.b) < 1:
                    # Update weights and bias for hinge loss + regularization
                    self.w += self.lr * (y_i * x_i - 2 * self.lambda_param * self.w)
                    self.b += self.lr * y_i
                else:
                    # Update weights with only regularization
                    self.w -= self.lr * 2 * self.lambda_param * self.w

    def predict(self, X):
        X = np.array(X)
        # Return +1 or -1 based on the sign of w^T x + b
        return np.sign(np.dot(X, self.w) + self.b)

# Sample data points (more separable)
X = np.array([[3.1, 2.5], [1.5, 2.2], [2.3, 3.3], [5.1, 1.6], [4.0, 2.0], [0.5, 0.8]])
y = np.array([1, 1, 1, -1, -1, -1])

# Normalize the feature matrix
X_normalized = normalize(X)

# Train the SVM
model = SVM(learning_rate=0.01, lambda_param=0.01, n_iters=1000)
model.fit(X_normalized, y)
predictions = model.predict(X_normalized)

print("SVM Predictions:", predictions)