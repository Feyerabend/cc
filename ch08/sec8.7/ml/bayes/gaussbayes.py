import math
from collections import defaultdict

class GaussianNB:
    def __init__(self):
        self.class_feature_stats = defaultdict(list)
        self.class_counts = defaultdict(int)
        self.total_samples = 0

    def train(self, X, y):
        # X: list of feature vectors, y: list of class labels
        self.total_samples = len(y)
        num_features = len(X[0])
        stats = defaultdict(lambda: [ [] for _ in range(num_features) ])

        for features, label in zip(X, y):
            self.class_counts[label] += 1
            for i, value in enumerate(features):
                stats[label][i].append(value)

        # mean and variance per feature per class
        for cls, feature_lists in stats.items():
            self.class_feature_stats[cls] = [
                (sum(f)/len(f), self._variance(f)) for f in feature_lists
            ]

    def _variance(self, values):
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    def _gaussian_pdf(self, x, mean, var):
        if var == 0: return 1.0 if x == mean else 0.0
        coeff = 1 / math.sqrt(2 * math.pi * var)
        exponent = math.exp(-((x - mean) ** 2) / (2 * var))
        return coeff * exponent

    def predict(self, x):
        scores = {}
        for cls in self.class_counts:
            log_prob = math.log(self.class_counts[cls] / self.total_samples)
            for i, value in enumerate(x):
                mean, var = self.class_feature_stats[cls][i]
                prob = self._gaussian_pdf(value, mean, var)
                log_prob += math.log(prob + 1e-9)  # epsilon to avoid log(0)
            scores[cls] = log_prob
        return max(scores, key=scores.get)

# Example usage
if __name__ == "__main__":
    # Sample data
    X = [
        [1.0, 2.0],
        [1.5, 1.8],
        [5.0, 8.0],
        [6.0, 9.0],
        [1.0, 0.6],
        [9.0, 11.0]
    ]
    y = ['A', 'A', 'B', 'B', 'A', 'B']

    model = GaussianNB()
    model.train(X, y)

    test_data = [[1.2, 1.5], [5.5, 8.5]]
    for data in test_data:
        print(f"Predicted class for {data}: {model.predict(data)}")

# This code implements a Gaussian Naive Bayes classifier.
# It calculates the mean and variance of each feature for each class
# during training and uses these statistics to compute the probability
# of a new sample belonging to each class during prediction.

# The example usage at the end demonstrates how to train the model
# with sample data and make predictions on new data points.
# The model is simple and efficient for binary and multi-class classification tasks.
# Note: This implementation assumes that the features are continuous and normally distributed.
# PROJECTS: The GaussianNB class can be extended or modified for more complex scenarios,
# such as handling missing values, categorical features, or different distributions.
