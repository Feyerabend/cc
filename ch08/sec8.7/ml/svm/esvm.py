import random
import numpy as np
from itertools import combinations
from collections import defaultdict
import math

def normalize(X):
    X = np.array(X)
    return (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0))

def standardize(X):
    X = np.array(X)
    return (X - X.mean(axis=0)) / X.std(axis=0)

class Kernel:
    @staticmethod
    def linear(x1, x2):
        return np.dot(x1, x2)
    
    @staticmethod
    def rbf(x1, x2, gamma=1.0):
        return np.exp(-gamma * np.linalg.norm(x1 - x2) ** 2)
    
    @staticmethod
    def polynomial(x1, x2, degree=3, coef0=1.0):
        return (np.dot(x1, x2) + coef0) ** degree
    
    @staticmethod
    def sigmoid(x1, x2, gamma=1.0, coef0=1.0):
        return np.tanh(gamma * np.dot(x1, x2) + coef0)

class SMOOptimizer:
    def __init__(self, C=1.0, tol=1e-3, max_passes=5):
        self.C = C
        self.tol = tol
        self.max_passes = max_passes
    
    def optimize(self, X, y, kernel_func, alpha=None):
        n_samples = X.shape[0]
        if alpha is None:
            alpha = np.zeros(n_samples)
        
        b = 0.0
        passes = 0
        
        while passes < self.max_passes:
            num_changed_alphas = 0
            
            for i in range(n_samples):
                # Calculate prediction error
                E_i = self._calculate_error(X, y, alpha, b, i, kernel_func)
                
                # Check KKT conditions
                if ((y[i] * E_i < -self.tol and alpha[i] < self.C) or 
                    (y[i] * E_i > self.tol and alpha[i] > 0)):
                    
                    # Select second alpha randomly
                    j = self._select_second_alpha(i, n_samples)
                    E_j = self._calculate_error(X, y, alpha, b, j, kernel_func)
                    
                    # Save old alphas
                    alpha_i_old = alpha[i]
                    alpha_j_old = alpha[j]
                    
                    # Compute bounds
                    if y[i] != y[j]:
                        L = max(0, alpha[j] - alpha[i])
                        H = min(self.C, self.C + alpha[j] - alpha[i])
                    else:
                        L = max(0, alpha[i] + alpha[j] - self.C)
                        H = min(self.C, alpha[i] + alpha[j])
                    
                    if L == H:
                        continue
                    
                    # Compute eta
                    eta = (2 * kernel_func(X[i], X[j]) - 
                          kernel_func(X[i], X[i]) - kernel_func(X[j], X[j]))
                    
                    if eta >= 0:
                        continue
                    
                    # Update alpha[j]
                    alpha[j] = alpha[j] - (y[j] * (E_i - E_j)) / eta
                    alpha[j] = max(L, min(H, alpha[j]))
                    
                    if abs(alpha[j] - alpha_j_old) < 1e-5:
                        continue
                    
                    # Update alpha[i]
                    alpha[i] = alpha[i] + y[i] * y[j] * (alpha_j_old - alpha[j])
                    
                    # Update bias
                    b1 = (b - E_i - y[i] * (alpha[i] - alpha_i_old) * kernel_func(X[i], X[i]) -
                          y[j] * (alpha[j] - alpha_j_old) * kernel_func(X[i], X[j]))
                    
                    b2 = (b - E_j - y[i] * (alpha[i] - alpha_i_old) * kernel_func(X[i], X[j]) -
                          y[j] * (alpha[j] - alpha_j_old) * kernel_func(X[j], X[j]))
                    
                    if 0 < alpha[i] < self.C:
                        b = b1
                    elif 0 < alpha[j] < self.C:
                        b = b2
                    else:
                        b = (b1 + b2) / 2
                    
                    num_changed_alphas += 1
            
            if num_changed_alphas == 0:
                passes += 1
            else:
                passes = 0
        
        return alpha, b
    
    def _calculate_error(self, X, y, alpha, b, i, kernel_func):
        prediction = 0
        for j in range(len(alpha)):
            if alpha[j] > 0:
                prediction += alpha[j] * y[j] * kernel_func(X[j], X[i])
        prediction += b
        return prediction - y[i]
    
    def _select_second_alpha(self, i, n_samples):
        j = i
        while j == i:
            j = random.randint(0, n_samples - 1)
        return j

class KernelSVM:
    def __init__(self, kernel='rbf', C=1.0, gamma=1.0, degree=3, coef0=1.0, 
                 tol=1e-3, max_iter=1000):
        self.kernel = kernel
        self.C = C
        self.gamma = gamma
        self.degree = degree
        self.coef0 = coef0
        self.tol = tol
        self.max_iter = max_iter
        
        # Kernel function mapping
        self.kernel_funcs = {
            'linear': Kernel.linear,
            'rbf': lambda x1, x2: Kernel.rbf(x1, x2, self.gamma),
            'poly': lambda x1, x2: Kernel.polynomial(x1, x2, self.degree, self.coef0),
            'sigmoid': lambda x1, x2: Kernel.sigmoid(x1, x2, self.gamma, self.coef0)
        }
        
        self.optimizer = SMOOptimizer(C=C, tol=tol, max_passes=max_iter//100)
        
    def fit(self, X, y):
        self.X_train = np.array(X)
        self.y_train = np.array(y)
        
        # Get kernel function
        kernel_func = self.kernel_funcs[self.kernel]
        
        # Optimize using SMO
        self.alpha, self.b = self.optimizer.optimize(
            self.X_train, self.y_train, kernel_func
        )
        
        # Store support vectors
        self.support_vector_indices = np.where(self.alpha > self.tol)[0]
        self.support_vectors = self.X_train[self.support_vector_indices]
        self.support_vector_labels = self.y_train[self.support_vector_indices]
        self.support_vector_alphas = self.alpha[self.support_vector_indices]
        
        return self
    
    def decision_function(self, X):
        X = np.array(X)
        kernel_func = self.kernel_funcs[self.kernel]
        
        decisions = []
        for x in X:
            decision = 0
            for i, sv_idx in enumerate(self.support_vector_indices):
                decision += (self.alpha[sv_idx] * self.y_train[sv_idx] * 
                           kernel_func(self.X_train[sv_idx], x))
            decision += self.b
            decisions.append(decision)
        
        return np.array(decisions)
    
    def predict(self, X):
        decisions = self.decision_function(X)
        return np.sign(decisions).astype(int)
    
    def predict_proba(self, X):
        decisions = self.decision_function(X)
        # Simple sigmoid transformation (Platt scaling would require additional fitting)
        probabilities = 1 / (1 + np.exp(-decisions))
        return np.column_stack([1 - probabilities, probabilities])

class MultiClassSVM:
    def __init__(self, strategy='ovo', **svm_params):
        self.strategy = strategy  # 'ovo' or 'ova'
        self.svm_params = svm_params
        self.classifiers = {}
        self.classes = None
        
    def fit(self, X, y):
        X = np.array(X)
        y = np.array(y)
        self.classes = np.unique(y)
        
        if len(self.classes) == 2:
            # Binary classification
            self.classifiers[(self.classes[0], self.classes[1])] = KernelSVM(**self.svm_params)
            self.classifiers[(self.classes[0], self.classes[1])].fit(X, y)
        elif self.strategy == 'ovo':
            # One-vs-One
            for class_pair in combinations(self.classes, 2):
                # Get samples for this pair
                mask = (y == class_pair[0]) | (y == class_pair[1])
                X_pair = X[mask]
                y_pair = y[mask]
                
                # Convert labels to -1, 1
                y_binary = np.where(y_pair == class_pair[0], -1, 1)
                
                # Train classifier
                clf = KernelSVM(**self.svm_params)
                clf.fit(X_pair, y_binary)
                self.classifiers[class_pair] = clf
                
        elif self.strategy == 'ova':
            # One-vs-All
            for class_label in self.classes:
                y_binary = np.where(y == class_label, 1, -1)
                clf = KernelSVM(**self.svm_params)
                clf.fit(X, y_binary)
                self.classifiers[class_label] = clf
        
        return self
    
    def predict(self, X):
        X = np.array(X)
        
        if len(self.classes) == 2:
            # Binary classification
            clf = list(self.classifiers.values())[0]
            predictions = clf.predict(X)
            return np.where(predictions == -1, self.classes[0], self.classes[1])
        
        elif self.strategy == 'ovo':
            # One-vs-One voting
            votes = np.zeros((len(X), len(self.classes)))
            class_to_idx = {cls: i for i, cls in enumerate(self.classes)}
            
            for class_pair, clf in self.classifiers.items():
                predictions = clf.predict(X)
                for i, pred in enumerate(predictions):
                    if pred == -1:
                        votes[i, class_to_idx[class_pair[0]]] += 1
                    else:
                        votes[i, class_to_idx[class_pair[1]]] += 1
            
            return self.classes[np.argmax(votes, axis=1)]
        
        elif self.strategy == 'ova':
            # One-vs-All with highest decision function
            decisions = np.zeros((len(X), len(self.classes)))
            
            for i, class_label in enumerate(self.classes):
                clf = self.classifiers[class_label]
                decisions[:, i] = clf.decision_function(X)
            
            return self.classes[np.argmax(decisions, axis=1)]

class CrossValidator:
    def __init__(self, k_folds=5):
        self.k_folds = k_folds
    
    def split(self, X, y):
        n_samples = len(X)
        indices = list(range(n_samples))
        random.shuffle(indices)
        
        fold_size = n_samples // self.k_folds
        folds = []
        
        for i in range(self.k_folds):
            start = i * fold_size
            end = start + fold_size if i < self.k_folds - 1 else n_samples
            test_indices = indices[start:end]
            train_indices = indices[:start] + indices[end:]
            folds.append((train_indices, test_indices))
        
        return folds
    
    def cross_validate(self, X, y, param_grid, svm_class=KernelSVM):
        X = np.array(X)
        y = np.array(y)
        
        best_params = None
        best_score = -np.inf
        results = []
        
        # Generate parameter combinations
        param_combinations = self._generate_param_combinations(param_grid)
        
        for params in param_combinations:
            scores = []
            
            # K-fold cross-validation
            for train_idx, test_idx in self.split(X, y):
                X_train, X_test = X[train_idx], X[test_idx]
                y_train, y_test = y[train_idx], y[test_idx]
                
                # Train model
                model = svm_class(**params)
                model.fit(X_train, y_train)
                
                # Evaluate
                predictions = model.predict(X_test)
                accuracy = np.mean(predictions == y_test)
                scores.append(accuracy)
            
            avg_score = np.mean(scores)
            std_score = np.std(scores)
            
            results.append({
                'params': params,
                'mean_score': avg_score,
                'std_score': std_score,
                'scores': scores
            })
            
            if avg_score > best_score:
                best_score = avg_score
                best_params = params
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'results': results
        }
    
    def _generate_param_combinations(self, param_grid):
        if not param_grid:
            return [{}]
        
        combinations = []
        keys = list(param_grid.keys())
        
        def generate_recursive(current_params, key_index):
            if key_index == len(keys):
                combinations.append(current_params.copy())
                return
            
            key = keys[key_index]
            for value in param_grid[key]:
                current_params[key] = value
                generate_recursive(current_params, key_index + 1)
                del current_params[key]
        
        generate_recursive({}, 0)
        return combinations


if __name__ == "__main__":
    # Sample data - expanded for better demonstration
    X = [
        [3.1, 2.5], [1.5, 2.2], [2.3, 3.3], [5.1, 1.6], [4.0, 2.0], [0.5, 0.8],
        [6.2, 1.9], [1.8, 3.8], [2.9, 1.4], [4.7, 3.2], [0.9, 1.1], [5.8, 2.8],
        [3.5, 4.1], [1.2, 0.9], [4.8, 1.2], [2.6, 3.9], [5.3, 3.5], [1.7, 2.8]
    ]
    y = [1, 1, -1, -1, 1, -1, -1, -1, 1, -1, 1, -1, -1, 1, -1, -1, -1, 1]
    
    # Multi-class data
    X_multi = X + [[7.1, 4.5], [6.8, 3.9], [7.5, 4.2], [6.9, 4.8]]
    y_multi = y + [2, 2, 2, 2]  # Adding a third class
    
    # Normalize data
    X_norm = normalize(X)
    X_multi_norm = normalize(X_multi)
    
    print("=== Enhanced SVM ===\n")
    
    # 1. Basic kernel SVM
    print("1. Kernel SVM with RBF kernel:")
    svm_rbf = KernelSVM(kernel='rbf', C=1.0, gamma=0.5)
    svm_rbf.fit(X_norm, y)
    predictions_rbf = svm_rbf.predict(X_norm)
    accuracy_rbf = np.mean(predictions_rbf == y)
    print(f"   RBF Kernel Accuracy: {accuracy_rbf:.3f}")
    print(f"   Support Vectors: {len(svm_rbf.support_vectors)}")
    print(f"   Predictions: {predictions_rbf}")
    
    # 2. Different kernels comparison
    print("\n2. Kernel Comparison:")
    kernels = ['linear', 'rbf', 'poly', 'sigmoid']
    for kernel in kernels:
        svm_k = KernelSVM(kernel=kernel, C=1.0, gamma=0.5)
        svm_k.fit(X_norm, y)
        pred_k = svm_k.predict(X_norm)
        acc_k = np.mean(pred_k == y)
        print(f"   {kernel.upper()} kernel accuracy: {acc_k:.3f}")
    
    # 3. Multi-class classification
    print("\n3. Multi-class Classification:")
    multi_svm_ovo = MultiClassSVM(strategy='ovo', kernel='rbf', C=1.0, gamma=0.5)
    multi_svm_ovo.fit(X_multi_norm, y_multi)
    pred_multi_ovo = multi_svm_ovo.predict(X_multi_norm)
    acc_multi_ovo = np.mean(pred_multi_ovo == y_multi)
    print(f"   One-vs-One accuracy: {acc_multi_ovo:.3f}")
    print(f"   Predictions: {pred_multi_ovo}")
    
    multi_svm_ova = MultiClassSVM(strategy='ova', kernel='rbf', C=1.0, gamma=0.5)
    multi_svm_ova.fit(X_multi_norm, y_multi)
    pred_multi_ova = multi_svm_ova.predict(X_multi_norm)
    acc_multi_ova = np.mean(pred_multi_ova == y_multi)
    print(f"   One-vs-All accuracy: {acc_multi_ova:.3f}")
    
    # 4. Cross-validation and hyperparameter tuning
    print("\n4. Cross-validation and Hyperparameter Tuning:")
    cv = CrossValidator(k_folds=3)  # Using 3 folds due to small dataset
    
    param_grid = {
        'kernel': ['rbf', 'poly'],
        'C': [0.1, 1.0, 10.0],
        'gamma': [0.1, 0.5, 1.0]
    }
    
    cv_results = cv.cross_validate(X_norm, y, param_grid)
    print(f"   Best parameters: {cv_results['best_params']}")
    print(f"   Best cross-validation score: {cv_results['best_score']:.3f}")
    
    # 5. Probability estimates
    print("\n5. Probability Estimates:")
    svm_prob = KernelSVM(**cv_results['best_params'])
    svm_prob.fit(X_norm, y)
    probabilities = svm_prob.predict_proba(X_norm[:5])  # First 5 samples
    print("   Sample probabilities (first 5 samples):")
    for i, prob in enumerate(probabilities):
        print(f"   Sample {i+1}: Class -1: {prob[0]:.3f}, Class 1: {prob[1]:.3f}")
    
    # 6. Decision function values
    print("\n6. Decision Function Values:")
    decisions = svm_prob.decision_function(X_norm[:5])
    print("   Decision values (first 5 samples):")
    for i, decision in enumerate(decisions):
        print(f"   Sample {i+1}: {decision:.3f}")
    
    print("\n=== Performance Summary ===")
    print(f"Training samples: {len(X)}")
    print(f"Features: {len(X[0])}")
    print(f"Classes: {len(np.unique(y))}")
    print(f"Best model accuracy: {cv_results['best_score']:.3f}")
    print(f"Support vectors in best model: {len(svm_prob.support_vectors)}")

