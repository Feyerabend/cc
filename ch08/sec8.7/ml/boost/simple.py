import math
import random

class DecisionStump:
    """A simple decision tree with one split (weak learner)"""
    
    def __init__(self):
        self.feature_idx = None
        self.threshold = None
        self.left_value = None
        self.right_value = None
    
    def fit(self, X, y, sample_weights=None):
        if sample_weights is None:
            sample_weights = [1.0] * len(y)
        
        best_error = float('inf')
        n_features = len(X[0])
        
        # Try each feature
        for feature_idx in range(n_features):
            # Get unique values for thresholds
            feature_values = sorted(set(row[feature_idx] for row in X))
            
            # Try each threshold
            for i in range(len(feature_values) - 1):
                threshold = (feature_values[i] + feature_values[i + 1]) / 2
                
                # Split data
                left_y = []
                right_y = []
                left_weights = []
                right_weights = []
                
                for j, row in enumerate(X):
                    if row[feature_idx] <= threshold:
                        left_y.append(y[j])
                        left_weights.append(sample_weights[j])
                    else:
                        right_y.append(y[j])
                        right_weights.append(sample_weights[j])
                
                if not left_y or not right_y:
                    continue
                
                # Calculate weighted means
                left_pred = sum(val * weight for val, weight in zip(left_y, left_weights)) / sum(left_weights)
                right_pred = sum(val * weight for val, weight in zip(right_y, right_weights)) / sum(right_weights)
                
                # Calculate weighted error
                error = 0
                for j, row in enumerate(X):
                    pred = left_pred if row[feature_idx] <= threshold else right_pred
                    error += sample_weights[j] * (y[j] - pred) ** 2
                
                if error < best_error:
                    best_error = error
                    self.feature_idx = feature_idx
                    self.threshold = threshold
                    self.left_value = left_pred
                    self.right_value = right_pred
    
    def predict(self, X):
        predictions = []
        for row in X:
            if self.feature_idx is not None:
                pred = self.left_value if row[self.feature_idx] <= self.threshold else self.right_value
            else:
                pred = 0  # fallback
            predictions.append(pred)
        return predictions

class SimpleGradientBoosting:
    """Simplified Gradient Boosting implementation"""
    
    def __init__(self, n_estimators=100, learning_rate=0.1, max_depth=1):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth  # Only depth 1 (stumps) supported in this simple version
        self.estimators = []
        self.initial_prediction = 0
    
    def fit(self, X, y):
        # Initialize with mean
        self.initial_prediction = sum(y) / len(y)
        
        # Initialize predictions
        current_predictions = [self.initial_prediction] * len(y)
        
        for i in range(self.n_estimators):
            # Calculate residuals (negative gradients for MSE)
            residuals = [y[j] - current_predictions[j] for j in range(len(y))]
            
            # Fit weak learner to residuals
            weak_learner = DecisionStump()
            weak_learner.fit(X, residuals)
            
            # Get predictions from weak learner
            weak_predictions = weak_learner.predict(X)
            
            # Update current predictions
            for j in range(len(current_predictions)):
                current_predictions[j] += self.learning_rate * weak_predictions[j]
            
            self.estimators.append(weak_learner)
            
            # Optional: print progress
            if (i + 1) % 20 == 0:
                mse = sum((y[j] - current_predictions[j]) ** 2 for j in range(len(y))) / len(y)
                print(f"Iteration {i + 1}, MSE: {mse:.4f}")
    
    def predict(self, X):
        predictions = [self.initial_prediction] * len(X)
        
        for estimator in self.estimators:
            weak_predictions = estimator.predict(X)
            for i in range(len(predictions)):
                predictions[i] += self.learning_rate * weak_predictions[i]
        
        return predictions

# Example usage and testing
if __name__ == "__main__":
    # Generate sample data
    random.seed(42)
    
    def generate_sample_data(n_samples=100):
        X = []
        y = []
        for _ in range(n_samples):
            x1 = random.uniform(-3, 3)
            x2 = random.uniform(-3, 3)
            # Non-linear function with noise
            target = x1**2 + x2**2 + 0.5 * x1 * x2 + random.gauss(0, 0.1)
            X.append([x1, x2])
            y.append(target)
        return X, y
    
    # Generate training data
    X_train, y_train = generate_sample_data(100)
    
    # Train the model
    print("Training Gradient Boosting model...")
    gb = SimpleGradientBoosting(n_estimators=50, learning_rate=0.1)
    gb.fit(X_train, y_train)
    
    # Make predictions
    predictions = gb.predict(X_train)
    
    # Calculate MSE
    mse = sum((y_train[i] - predictions[i]) ** 2 for i in range(len(y_train))) / len(y_train)
    print(f"\nFinal Training MSE: {mse:.4f}")
    
    # Show some predictions vs actual
    print("\nSample predictions vs actual:")
    for i in range(5):
        print(f"Predicted: {predictions[i]:.3f}, Actual: {y_train[i]:.3f}")
    
    # Test on new data
    X_test, y_test = generate_sample_data(20)
    test_predictions = gb.predict(X_test)
    test_mse = sum((y_test[i] - test_predictions[i]) ** 2 for i in range(len(y_test))) / len(y_test)
    print(f"\nTest MSE: {test_mse:.4f}")
    print("\nSample test predictions vs actual:")
    for i in range(5):
        print(f"Predicted: {test_predictions[i]:.3f}, Actual: {y_test[i]:.3f}")

