import random
import math
from collections import Counter

class DecisionTree:
    def __init__(self, max_depth=10, min_samples_split=2):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.tree = None
    
    def fit(self, X, y):
        self.tree = self._build_tree(X, y, depth=0)
    
    def _build_tree(self, X, y, depth):
        n_samples, n_features = len(X), len(X[0])
        
        # Stopping criteria
        if (depth >= self.max_depth or 
            n_samples < self.min_samples_split or 
            len(set(y)) == 1):
            return Counter(y).most_common(1)[0][0]
        
        # Find best split
        best_feature, best_threshold = self._find_best_split(X, y)
        
        if best_feature is None:
            return Counter(y).most_common(1)[0][0]
        
        # Split data
        left_indices, right_indices = self._split_data(X, best_feature, best_threshold)
        
        left_X = [X[i] for i in left_indices]
        left_y = [y[i] for i in left_indices]
        right_X = [X[i] for i in right_indices]
        right_y = [y[i] for i in right_indices]
        
        # Recursively build subtrees
        left_child = self._build_tree(left_X, left_y, depth + 1)
        right_child = self._build_tree(right_X, right_y, depth + 1)
        
        return {
            'feature': best_feature,
            'threshold': best_threshold,
            'left': left_child,
            'right': right_child
        }
    
    def _find_best_split(self, X, y):
        n_features = len(X[0])
        best_gini = float('inf')
        best_feature = None
        best_threshold = None
        
        # Random feature selection for random forest
        feature_indices = random.sample(range(n_features), 
                                      min(int(math.sqrt(n_features)), n_features))
        
        for feature_idx in feature_indices:
            values = [row[feature_idx] for row in X]
            thresholds = set(values)
            
            for threshold in thresholds:
                left_indices, right_indices = self._split_data(X, feature_idx, threshold)
                
                if len(left_indices) == 0 or len(right_indices) == 0:
                    continue
                
                left_y = [y[i] for i in left_indices]
                right_y = [y[i] for i in right_indices]
                
                gini = self._weighted_gini(left_y, right_y)
                
                if gini < best_gini:
                    best_gini = gini
                    best_feature = feature_idx
                    best_threshold = threshold
        
        return best_feature, best_threshold
    
    def _split_data(self, X, feature_idx, threshold):
        left_indices = []
        right_indices = []
        
        for i, row in enumerate(X):
            if row[feature_idx] <= threshold:
                left_indices.append(i)
            else:
                right_indices.append(i)
        
        return left_indices, right_indices
    
    def _gini_impurity(self, y):
        if len(y) == 0:
            return 0
        
        counter = Counter(y)
        impurity = 1.0
        
        for count in counter.values():
            prob = count / len(y)
            impurity -= prob ** 2
        
        return impurity
    
    def _weighted_gini(self, left_y, right_y):
        n_left, n_right = len(left_y), len(right_y)
        n_total = n_left + n_right
        
        weighted_gini = (n_left / n_total) * self._gini_impurity(left_y)
        weighted_gini += (n_right / n_total) * self._gini_impurity(right_y)
        
        return weighted_gini
    
    def predict_single(self, x):
        return self._traverse_tree(x, self.tree)
    
    def _traverse_tree(self, x, node):
        if not isinstance(node, dict):
            return node
        
        if x[node['feature']] <= node['threshold']:
            return self._traverse_tree(x, node['left'])
        else:
            return self._traverse_tree(x, node['right'])
    
    def predict(self, X):
        return [self.predict_single(x) for x in X]


class RandomForest:
    def __init__(self, n_trees=10, max_depth=10, min_samples_split=2, 
                 sample_ratio=0.8):
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.sample_ratio = sample_ratio
        self.trees = []
    
    def fit(self, X, y):
        self.trees = []
        n_samples = len(X)
        
        for _ in range(self.n_trees):
            # Bootstrap sampling
            sample_size = int(n_samples * self.sample_ratio)
            indices = random.choices(range(n_samples), k=sample_size)
            
            X_sample = [X[i] for i in indices]
            y_sample = [y[i] for i in indices]
            
            # Train tree
            tree = DecisionTree(self.max_depth, self.min_samples_split)
            tree.fit(X_sample, y_sample)
            self.trees.append(tree)
    
    def predict(self, X):
        predictions = []
        
        for x in X:
            tree_predictions = [tree.predict_single(x) for tree in self.trees]
            # Majority vote
            prediction = Counter(tree_predictions).most_common(1)[0][0]
            predictions.append(prediction)
        
        return predictions
    
    def predict_proba(self, X):
        probabilities = []
        
        for x in X:
            tree_predictions = [tree.predict_single(x) for tree in self.trees]
            counter = Counter(tree_predictions)
            total = len(tree_predictions)
            
            prob_dict = {label: count/total for label, count in counter.items()}
            probabilities.append(prob_dict)
        
        return probabilities


# Example usage
if __name__ == "__main__":
    # Create sample data (XOR problem)
    X = [
        [0, 0], [0, 1], [1, 0], [1, 1],
        [0.1, 0.1], [0.1, 0.9], [0.9, 0.1], [0.9, 0.9],
        [0.2, 0.2], [0.2, 0.8], [0.8, 0.2], [0.8, 0.8]
    ]
    y = [0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0]
    
    # Train random forest
    rf = RandomForest(n_trees=5, max_depth=5)
    rf.fit(X, y)
    
    # Make predictions
    test_X = [[0.1, 0.1], [0.1, 0.9], [0.9, 0.1], [0.9, 0.9]]
    predictions = rf.predict(test_X)
    probabilities = rf.predict_proba(test_X)
    
    print("Predictions:", predictions)
    print("Probabilities:", probabilities)
    
    # Test accuracy on training data
    train_predictions = rf.predict(X)
    accuracy = sum(1 for i in range(len(y)) if y[i] == train_predictions[i]) / len(y)
    print(f"Training accuracy: {accuracy:.2f}")

# This code implements a simple Decision Tree and Random Forest classifier in Python.
# It includes methods for fitting the model, making predictions, and calculating probabilities.
# The example usage demonstrates training on a small dataset and making predictions.
# The implementation uses Gini impurity for splitting and bootstrap sampling for the random forest.

