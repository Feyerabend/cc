from PIL import Image, ImageDraw
import numpy as np

def normalize(X):
    """Normalize features to [0, 1] range."""
    X = np.array(X)
    X_min = X.min(axis=0)
    X_max = X.max(axis=0)
    # Avoid division by zero
    X_range = X_max - X_min
    X_range[X_range == 0] = 1
    return (X - X_min) / X_range

class SVM:
    def __init__(self, learning_rate=0.01, lambda_param=0.01, n_iters=1000, tolerance=1e-6):
        self.lr = learning_rate
        self.lambda_param = lambda_param
        self.n_iters = n_iters
        self.tolerance = tolerance
        self.w = None
        self.b = None
        self.cost_history = []
        
    def _compute_cost(self, X, y):
        """Compute the SVM cost function."""
        n_samples = X.shape[0]
        distances = 1 - y * (X.dot(self.w) + self.b)
        distances[distances < 0] = 0  # max(0, distance)
        hinge_loss = self.lambda_param * (distances ** 2).sum()
        regularization = 0.5 * np.dot(self.w, self.w)
        return (regularization + hinge_loss) / n_samples
    
    def fit(self, X, y):
        """Train the SVM using gradient descent."""
        X = np.array(X)
        y = np.array(y)
        n_samples, n_features = X.shape
        
        # Initialize weights and bias
        self.w = np.random.normal(0, 0.01, n_features)
        self.b = 0.0
        self.cost_history = []
        
        prev_cost = float('inf')
        
        for iteration in range(self.n_iters):
            # Shuffle data for stochastic gradient descent
            indices = np.random.permutation(n_samples)
            
            for idx in indices:
                x_i = X[idx]
                y_i = y[idx]
                
                # Check if point is correctly classified with margin
                condition = y_i * (np.dot(x_i, self.w) + self.b) >= 1
                
                if condition:
                    # Correct classification - only regularization gradient
                    self.w -= self.lr * self.lambda_param * self.w
                else:
                    # Misclassified or within margin - hinge loss gradient
                    self.w -= self.lr * (self.lambda_param * self.w - y_i * x_i)
                    self.b -= self.lr * (-y_i)
            
            # Track cost every 10 iterations for efficiency
            if iteration % 10 == 0:
                current_cost = self._compute_cost(X, y)
                self.cost_history.append(current_cost)
                
                # Early stopping
                if abs(prev_cost - current_cost) < self.tolerance:
                    print(f"Converged at iteration {iteration}")
                    break
                prev_cost = current_cost
                
    def _decision_function(self, X):
        """Compute the decision function."""
        return np.dot(X, self.w) + self.b
    
    def predict(self, X):
        """Make predictions."""
        X = np.array(X)
        return np.sign(self._decision_function(X)).astype(int)
    
    def predict_proba(self, X):
        """Return decision function values (distance from hyperplane)."""
        return self._decision_function(X)
    
    def score(self, X, y):
        """Calculate accuracy."""
        predictions = self.predict(X)
        return np.mean(predictions == y)

def visualize_svm(X, y, svm_model, width=500, height=500, filename=None):
    """Visualize SVM decision boundary and data points."""
    # Normalize data for visualization
    X_normalized = normalize(X)
    
    # Create image
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Create mesh grid for decision boundary
    x_min, x_max = 0, 1
    y_min, y_max = 0, 1
    h = 0.01  # Step size
    
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                         np.arange(y_min, y_max, h))
    
    # Transform mesh grid back to original scale for prediction
    mesh_points = np.c_[xx.ravel(), yy.ravel()]
    
    # Transform back to original scale
    X_min = X.min(axis=0)
    X_max = X.max(axis=0)
    X_range = X_max - X_min
    X_range[X_range == 0] = 1
    mesh_original = mesh_points * X_range + X_min
    
    # Get predictions
    Z = svm_model.predict_proba(mesh_original)
    Z = Z.reshape(xx.shape)
    
    # Draw decision regions
    for i in range(0, Z.shape[0], 2):  # Sample every 2nd point for efficiency
        for j in range(0, Z.shape[1], 2):
            x_coord = int(j * width / Z.shape[1])
            y_coord = int(i * height / Z.shape[0])
            
            # Color based on decision function value
            if Z[i, j] > 0:
                intensity = min(255, int(200 + abs(Z[i, j]) * 20))
                color = (200, 200, intensity)  # Light blue gradient
            else:
                intensity = min(255, int(200 + abs(Z[i, j]) * 20))
                color = (intensity, 200, 200)  # Light red gradient
            
            # Draw small rectangle for efficiency
            draw.rectangle([x_coord, y_coord, x_coord+2, y_coord+2], fill=color)
    
    # Draw decision boundary (where decision function ≈ 0)
    contour_levels = [-1, 0, 1]  # Margin boundaries and decision boundary
    colors = [(100, 100, 100), (0, 0, 0), (100, 100, 100)]  # Gray, Black, Gray
    
    for level, color in zip(contour_levels, colors):
        for i in range(Z.shape[0]-1):
            for j in range(Z.shape[1]-1):
                # Simple contour detection
                if ((Z[i, j] <= level <= Z[i+1, j]) or 
                    (Z[i, j] >= level >= Z[i+1, j]) or
                    (Z[i, j] <= level <= Z[i, j+1]) or 
                    (Z[i, j] >= level >= Z[i, j+1])):
                    x_coord = int(j * width / Z.shape[1])
                    y_coord = int(i * height / Z.shape[0])
                    draw.point((x_coord, y_coord), fill=color)
    
    # Plot data points
    for point, label in zip(X_normalized, y):
        x_coord = int(point[0] * width)
        y_coord = int(point[1] * height)
        radius = 8
        
        if label == 1:
            # Blue circle for positive class
            draw.ellipse((x_coord-radius, y_coord-radius, 
                         x_coord+radius, y_coord+radius), 
                        fill=(0, 100, 255), outline=(0, 0, 0), width=2)
        else:
            # Red square for negative class
            draw.rectangle((x_coord-radius, y_coord-radius, 
                           x_coord+radius, y_coord+radius), 
                          fill=(255, 50, 50), outline=(0, 0, 0), width=2)
    
    # Add title
    draw.text((10, 10), f"SVM Decision Boundary (Accuracy: {svm_model.score(X, y):.2f})", 
              fill=(0, 0, 0))
    
    if filename:
        image.save(filename)
    
    return image

# Example usage
if __name__ == "__main__":
    # Test different challenging scenarios
    test_scenarios = [
        "clean_separable",
        "noisy_data", 
        "outliers",
        "overlapping_classes",
        "random_chaos"
    ]
    
    for scenario in test_scenarios:
        print(f"\n{'='*50}")
        print(f"Testing scenario: {scenario.upper()}")
        print('='*50)
        
        np.random.seed(42)  # For reproducibility
        
        if scenario == "clean_separable":
            # Well-separated Gaussian clusters
            X_pos = np.random.normal([3, 3], 0.4, (12, 2))
            X_neg = np.random.normal([1, 1], 0.4, (12, 2))
            X = np.vstack([X_pos, X_neg])
            y = np.hstack([np.ones(12), -np.ones(12)])
            
        elif scenario == "noisy_data":
            # Add significant noise to the features
            X_pos = np.random.normal([3, 3], 0.8, (15, 2))
            X_neg = np.random.normal([1, 1], 0.8, (15, 2))
            X = np.vstack([X_pos, X_neg])
            y = np.hstack([np.ones(15), -np.ones(15)])
            # Add random noise to all points
            X += np.random.normal(0, 0.3, X.shape)
            
        elif scenario == "outliers":
            # Normal clusters + extreme outliers
            X_pos = np.random.normal([2.5, 2.5], 0.3, (10, 2))
            X_neg = np.random.normal([1.5, 1.5], 0.3, (10, 2))
            X = np.vstack([X_pos, X_neg])
            y = np.hstack([np.ones(10), -np.ones(10)])
            
            # Add extreme outliers
            outliers_pos = np.array([[6, 0], [0, 6], [5, 5]])
            outliers_neg = np.array([[-1, 3], [3, -1], [0, 0]])
            X = np.vstack([X, outliers_pos, outliers_neg])
            y = np.hstack([y, [1, 1, 1], [-1, -1, -1]])
            
        elif scenario == "overlapping_classes":
            # Heavily overlapping distributions
            X_pos = np.random.normal([2, 2], 0.9, (20, 2))
            X_neg = np.random.normal([2.2, 2.2], 0.9, (20, 2))
            X = np.vstack([X_pos, X_neg])
            y = np.hstack([np.ones(20), -np.ones(20)])
            
        elif scenario == "random_chaos":
            # Completely random data points
            X = np.random.uniform(-2, 6, (30, 2))
            # Random labels with slight bias toward position
            y = np.where((X[:, 0] + X[:, 1]) > 4, 1, -1)
            # Add some completely random label flips
            flip_indices = np.random.choice(len(y), size=int(0.3 * len(y)), replace=False)
            y[flip_indices] *= -1
        
        print(f"Dataset shape: {X.shape}")
        print(f"Classes: {np.unique(y, return_counts=True)}")
        print(f"Data range: X1=[{X[:, 0].min():.2f}, {X[:, 0].max():.2f}], "
              f"X2=[{X[:, 1].min():.2f}, {X[:, 1].max():.2f}]")
        
        # Test different hyperparameters for challenging scenarios
        if scenario in ["overlapping_classes", "random_chaos"]:
            # More regularization for difficult cases
            svm = SVM(learning_rate=0.01, lambda_param=0.5, n_iters=2000, tolerance=1e-8)
        elif scenario == "outliers":
            # Less regularization but more iterations for outliers
            svm = SVM(learning_rate=0.005, lambda_param=0.05, n_iters=1500)
        else:
            # Standard parameters
            svm = SVM(learning_rate=0.001, lambda_param=0.1, n_iters=1000)
        
        # Train SVM
        print("Training SVM...")
        svm.fit(X, y)
        
        # Print results
        accuracy = svm.score(X, y)
        print(f"Training accuracy: {accuracy:.3f}")
        print(f"Final weights: [{svm.w[0]:.3f}, {svm.w[1]:.3f}]")
        print(f"Final bias: {svm.b:.3f}")
        print(f"Converged after {len(svm.cost_history) * 10} iterations")
        
        # Evaluate model robustness
        if accuracy > 0.8:
            print("Model handles this scenario well!")
        elif accuracy > 0.6:
            print("Model struggles but finds reasonable solution")
        else:
            print("Model has difficulty with this scenario")
            
        # Test on some new random points
        test_points = np.random.uniform(X.min(), X.max(), (5, 2))
        predictions = svm.predict(test_points)
        confidence = svm.predict_proba(test_points)
        
        print(f"Sample predictions on new points:")
        for i, (point, pred, conf) in enumerate(zip(test_points, predictions, confidence)):
            print(f"  Point [{point[0]:.2f}, {point[1]:.2f}] -> "
                  f"Class {pred:2d} (confidence: {abs(conf):.2f})")
        
        # Visualize this scenario
        print(f"Generating visualization for {scenario}...")
        image = visualize_svm(X, y, svm, filename=f"svm_{scenario}.png")
        
        # Only show the first scenario to avoid too many windows
        if scenario == "clean_separable":
            image.show()
        
        print(f"Visualization saved as: svm_{scenario}.png")
    
    print(f"\n{'='*50}")
    print("ROBUSTNESS TEST SUMMARY")
    print('='*50)
    print("The SVM was tested on 5 challenging scenarios:")
    print("1. Clean separable data (baseline)")
    print("2. Noisy features")  
    print("3. Extreme outliers")
    print("4. Overlapping class distributions")
    print("5. Random chaotic labeling")
    print("\nCheck the generated images to see how well it handled each case!")
    print("The SVM should show different behaviors:")
    print("- Tight boundaries for clean data")
    print("- Wider margins for noisy data")
    print("- Robust boundaries despite outliers")
    print("- Best-effort separation for overlapping classes")