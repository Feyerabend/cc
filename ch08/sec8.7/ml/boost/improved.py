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

class EnhancedGradientBoosting:    
    def __init__(self, n_estimators=100, learning_rate=0.1, subsample=0.8, 
                 colsample=0.8, early_stopping_rounds=10, min_samples_leaf=5):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.subsample = subsample  # Row sampling
        self.colsample = colsample  # Column sampling
        self.early_stopping_rounds = early_stopping_rounds
        self.min_samples_leaf = min_samples_leaf
        self.estimators = []
        self.feature_subsets = []  # Store which features each estimator uses
        self.initial_prediction = 0
        self.train_errors = []
        self.val_errors = []
    
    def _calculate_mse(self, y_true, y_pred):
        return sum((y_true[i] - y_pred[i]) ** 2 for i in range(len(y_true))) / len(y_true)
    
    def _train_val_split(self, X, y, val_size=0.2):
        """Simple train/validation split"""
        n_val = int(len(X) * val_size)
        indices = list(range(len(X)))
        random.shuffle(indices)
        
        val_indices = indices[:n_val]
        train_indices = indices[n_val:]
        
        X_train = [X[i] for i in train_indices]
        y_train = [y[i] for i in train_indices]
        X_val = [X[i] for i in val_indices]
        y_val = [y[i] for i in val_indices]
        
        return X_train, y_train, X_val, y_val
    
    def _subsample_data(self, X, y):
        n_samples = int(len(X) * self.subsample)
        indices = random.sample(range(len(X)), n_samples)
        
        X_sub = [X[i] for i in indices]
        y_sub = [y[i] for i in indices]
        
        return X_sub, y_sub
    
    def _subsample_features(self, n_features):
        n_features_use = max(1, int(n_features * self.colsample))
        return random.sample(range(n_features), n_features_use)
    
    def fit(self, X, y):
        # Train/validation split for early stopping
        X_train, y_train, X_val, y_val = self._train_val_split(X, y)
        
        # Initialize with mean
        self.initial_prediction = sum(y_train) / len(y_train)
        
        # Initialize predictions
        train_predictions = [self.initial_prediction] * len(y_train)
        val_predictions = [self.initial_prediction] * len(y_val)
        
        best_val_error = float('inf')
        no_improvement_count = 0
        
        for i in range(self.n_estimators):
            # Calculate residuals
            residuals = [y_train[j] - train_predictions[j] for j in range(len(y_train))]
            
            # Subsample data
            X_sub, residuals_sub = self._subsample_data(X_train, residuals)
            
            # Subsample features
            feature_subset = self._subsample_features(len(X[0]))
            
            # Create feature-subsampled data
            X_sub_features = []
            for row in X_sub:
                X_sub_features.append([row[idx] for idx in feature_subset])
            
            # Fit weak learner to subsampled residuals
            weak_learner = DecisionStump()
            weak_learner.fit(X_sub_features, residuals_sub)
            
            # Store estimator and its feature subset
            self.estimators.append(weak_learner)
            self.feature_subsets.append(feature_subset)
            
            # Get predictions for full training set
            X_train_subset = []
            for row in X_train:
                X_train_subset.append([row[idx] for idx in feature_subset])
            weak_train_preds = weak_learner.predict(X_train_subset)
            
            # Get predictions for validation set
            X_val_subset = []
            for row in X_val:
                X_val_subset.append([row[idx] for idx in feature_subset])
            weak_val_preds = weak_learner.predict(X_val_subset)
            
            # Update predictions with learning rate
            for j in range(len(train_predictions)):
                train_predictions[j] += self.learning_rate * weak_train_preds[j]
            
            for j in range(len(val_predictions)):
                val_predictions[j] += self.learning_rate * weak_val_preds[j]
            
            # Calculate errors
            train_error = self._calculate_mse(y_train, train_predictions)
            val_error = self._calculate_mse(y_val, val_predictions)
            
            self.train_errors.append(train_error)
            self.val_errors.append(val_error)
            
            # Early stopping check
            if val_error < best_val_error:
                best_val_error = val_error
                no_improvement_count = 0
            else:
                no_improvement_count += 1
            
            if (i + 1) % 20 == 0:
                print(f"Iteration {i + 1}, Train MSE: {train_error:.4f}, Val MSE: {val_error:.4f}")
            
            # Early stopping
            if no_improvement_count >= self.early_stopping_rounds:
                print(f"Early stopping at iteration {i + 1}")
                break
    
    def predict(self, X):
        predictions = [self.initial_prediction] * len(X)
        
        for estimator, feature_subset in zip(self.estimators, self.feature_subsets):
            # Create feature-subsampled data
            X_subset = []
            for row in X:
                X_subset.append([row[idx] for idx in feature_subset])
            
            weak_predictions = estimator.predict(X_subset)
            for i in range(len(predictions)):
                predictions[i] += self.learning_rate * weak_predictions[i]
        
        return predictions

# Enhanced experiment with comparison
if __name__ == "__main__":
    random.seed(42)
    
    def generate_sample_data(n_samples=100):
        X = []
        y = []
        for _ in range(n_samples):
            x1 = random.uniform(-3, 3)
            x2 = random.uniform(-3, 3)
            x3 = random.uniform(-2, 2)  # Add a third feature
            # More complex non-linear function with noise
            target = x1**2 + x2**2 + 0.5 * x1 * x2 + 0.3 * x3**3 + random.gauss(0, 0.15)
            X.append([x1, x2, x3])
            y.append(target)
        return X, y
    
    # Generate larger dataset
    X_train, y_train = generate_sample_data(200)
    X_test, y_test = generate_sample_data(50)
    
    print("=== COMPARISON EXPERIMENT ===\n")
    
    # Test original model
    print("1. Original Gradient Boosting:")
    from copy import deepcopy
    
    class SimpleGradientBoosting:
        def __init__(self, n_estimators=100, learning_rate=0.1):
            self.n_estimators = n_estimators
            self.learning_rate = learning_rate
            self.estimators = []
            self.initial_prediction = 0
        
        def fit(self, X, y):
            self.initial_prediction = sum(y) / len(y)
            current_predictions = [self.initial_prediction] * len(y)
            
            for i in range(self.n_estimators):
                residuals = [y[j] - current_predictions[j] for j in range(len(y))]
                weak_learner = DecisionStump()
                weak_learner.fit(X, residuals)
                weak_predictions = weak_learner.predict(X)
                
                for j in range(len(current_predictions)):
                    current_predictions[j] += self.learning_rate * weak_predictions[j]
                
                self.estimators.append(weak_learner)
        
        def predict(self, X):
            predictions = [self.initial_prediction] * len(X)
            for estimator in self.estimators:
                weak_predictions = estimator.predict(X)
                for i in range(len(predictions)):
                    predictions[i] += self.learning_rate * weak_predictions[i]
            return predictions
    
    simple_gb = SimpleGradientBoosting(n_estimators=80, learning_rate=0.1)
    simple_gb.fit(X_train, y_train)
    
    simple_train_preds = simple_gb.predict(X_train)
    simple_test_preds = simple_gb.predict(X_test)
    
    simple_train_mse = sum((y_train[i] - simple_train_preds[i]) ** 2 for i in range(len(y_train))) / len(y_train)
    simple_test_mse = sum((y_test[i] - simple_test_preds[i]) ** 2 for i in range(len(y_test))) / len(y_test)
    
    print(f"Train MSE: {simple_train_mse:.4f}")
    print(f"Test MSE: {simple_test_mse:.4f}")
    print(f"Overfitting: {simple_test_mse - simple_train_mse:.4f}\n")
    
    # Test enhanced model
    print("2. Enhanced Gradient Boosting:")
    enhanced_gb = EnhancedGradientBoosting(
        n_estimators=100, 
        learning_rate=0.1, 
        subsample=0.8,
        colsample=0.8,
        early_stopping_rounds=15
    )
    enhanced_gb.fit(X_train, y_train)
    
    enhanced_train_preds = enhanced_gb.predict(X_train)
    enhanced_test_preds = enhanced_gb.predict(X_test)
    
    enhanced_train_mse = sum((y_train[i] - enhanced_train_preds[i]) ** 2 for i in range(len(y_train))) / len(y_train)
    enhanced_test_mse = sum((y_test[i] - enhanced_test_preds[i]) ** 2 for i in range(len(y_test))) / len(y_test)
    
    print(f"Train MSE: {enhanced_train_mse:.4f}")
    print(f"Test MSE: {enhanced_test_mse:.4f}")
    print(f"Overfitting: {enhanced_test_mse - enhanced_train_mse:.4f}")
    print(f"Number of estimators used: {len(enhanced_gb.estimators)}")
    
    print(f"\n=== IMPROVEMENTS ===")
    print(f"Test MSE improvement: {simple_test_mse - enhanced_test_mse:.4f}")
    print(f"Overfitting reduction: {(simple_test_mse - simple_train_mse) - (enhanced_test_mse - enhanced_train_mse):.4f}")
    
    # Show some sample predictions
    print(f"\n=== SAMPLE PREDICTIONS ===")
    print("Enhanced model predictions vs actual (test set):")
    for i in range(5):
        print(f"Predicted: {enhanced_test_preds[i]:.3f}, Actual: {y_test[i]:.3f}, Error: {abs(enhanced_test_preds[i] - y_test[i]):.3f}")

