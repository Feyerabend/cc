"""
t-SNE (t-Distributed Stochastic Neighbor Embedding)
Pure Python - Fixed version with improved numerical stability and realistic data generation
"""

import math
import random
from typing import List, Tuple, Optional
import time


class TSNEConfig:
    """Configuration class for t-SNE parameters."""
    
    def __init__(
        self,
        dims: int = 2,
        perplexity: float = 30.0,
        iterations: int = 1000,
        learning_rate: float = 200.0,
        early_exaggeration: float = 12.0,
        early_exaggeration_iter: int = 250,
        min_gain: float = 0.01,
        momentum: float = 0.9,
        tolerance: float = 1e-5,
        verbose: bool = True
    ):
        self.dims = dims
        self.perplexity = perplexity
        self.iterations = iterations
        self.learning_rate = learning_rate
        self.early_exaggeration = early_exaggeration
        self.early_exaggeration_iter = early_exaggeration_iter
        self.min_gain = min_gain
        self.momentum = momentum
        self.tolerance = tolerance
        self.verbose = verbose


class TSNE:
    """
    t-SNE implementation with improved performance and features.
    
    Features:
    - Early exaggeration for better global structure
    - Adaptive gains for faster convergence
    - Progress tracking and convergence monitoring
    - Better numerical stability
    - Configurable parameters
    """
    
    def __init__(self, config: Optional[TSNEConfig] = None):
        self.config = config or TSNEConfig()
        self.cost_history = []
        
    def euclidean_squared(self, a: List[float], b: List[float]) -> float:
        """Compute squared Euclidean distance between two points."""
        return sum((x - y) ** 2 for x, y in zip(a, b))
    
    def pairwise_distances(self, X: List[List[float]]) -> List[List[float]]:
        """Compute pairwise squared distances matrix."""
        N = len(X)
        D = [[0.0] * N for _ in range(N)]
        
        for i in range(N):
            for j in range(i + 1, N):
                d = self.euclidean_squared(X[i], X[j])
                D[i][j] = d
                D[j][i] = d
                
        return D
    
    def compute_entropy_and_prob(self, distances: List[float], beta: float) -> Tuple[float, List[float]]:
        """
        Compute Shannon entropy and probabilities given distances and precision (beta).
        Improved numerical stability to prevent overflow.
        
        Returns:
            Tuple of (entropy, probabilities)
        """
        if not distances:
            return 0.0, []
        
        # Find minimum distance for numerical stability
        min_dist = min(distances)
        
        # Compute log probabilities to avoid overflow
        log_P = [-beta * (d - min_dist) for d in distances]
        
        # Find maximum log probability for log-sum-exp trick
        max_log_P = max(log_P)
        
        # Compute probabilities using log-sum-exp trick
        exp_vals = []
        for log_p in log_P:
            exp_val = log_p - max_log_P
            # Cap the exponent to prevent overflow/underflow
            if exp_val < -700:  # exp(-700) is approximately 0
                exp_vals.append(0.0)
            else:
                exp_vals.append(math.exp(exp_val))
        
        sum_exp = sum(exp_vals)
        
        if sum_exp == 0:
            # Handle numerical issues - uniform distribution
            P = [1.0 / len(distances) for _ in distances]
            H = math.log(len(distances))
        else:
            # Normalize probabilities
            P = [exp_val / sum_exp for exp_val in exp_vals]
            
            # Compute entropy: H = log(sum_P) + beta * E[distance]
            log_sum_P = max_log_P + math.log(sum_exp)
            expected_dist = sum(d * p for d, p in zip(distances, P))
            H = log_sum_P + beta * (expected_dist - min_dist)
        
        return H, P
    
    def binary_search_precision(self, distances: List[float], target_perplexity: float) -> List[float]:
        """
        Binary search to find the precision (beta) that gives the target perplexity.
        Improved bounds and convergence criteria.
        
        Returns:
            Probability distribution for the given distances
        """
        if not distances:
            return []
        
        # Initialize beta with reasonable bounds
        beta = 1.0
        beta_min, beta_max = 1e-20, 1e20  # Set reasonable bounds
        log_target = math.log(target_perplexity)
        
        # Store best result in case we don't converge perfectly
        best_P = None
        best_error = float('inf')
        
        for iteration in range(50):  # Maximum iterations
            H, P = self.compute_entropy_and_prob(distances, beta)
            error = abs(H - log_target)
            
            # Track best result
            if error < best_error:
                best_error = error
                best_P = P[:]
            
            # Check convergence
            if error < self.config.tolerance:
                return P
            
            # Update beta bounds
            if H > log_target:
                beta_min = beta
                if beta_max == 1e20:
                    beta *= 2.0
                else:
                    beta = (beta + beta_max) / 2.0
            else:
                beta_max = beta
                if beta_min == 1e-20:
                    beta /= 2.0
                else:
                    beta = (beta + beta_min) / 2.0
            
            # Prevent beta from becoming too extreme
            beta = max(min(beta, 1e15), 1e-15)
        
        # Return best result if we didn't converge perfectly
        return best_P if best_P is not None else [1.0 / len(distances) for _ in distances]
    
    def compute_affinities(self, X: List[List[float]]) -> List[List[float]]:
        """
        Compute the high-dimensional affinities P_ij.
        
        Returns:
            Symmetric probability matrix P
        """
        N = len(X)
        D = self.pairwise_distances(X)
        P = [[0.0] * N for _ in range(N)]
        
        if self.config.verbose:
            print("Computing pairwise affinities...")
        
        for i in range(N):
            # Get distances to all other points (excluding self)
            distances = [D[i][j] for j in range(N) if j != i]
            
            if not distances:  # Single point case
                continue
            
            # Find probabilities that give target perplexity
            prob_dist = self.binary_search_precision(distances, self.config.perplexity)
            
            # Fill in the probability matrix
            prob_idx = 0
            for j in range(N):
                if i != j:
                    P[i][j] = prob_dist[prob_idx] if prob_idx < len(prob_dist) else 1e-12
                    prob_idx += 1
        
        # Make P symmetric and normalize
        for i in range(N):
            for j in range(N):
                if i != j:
                    P[i][j] = (P[i][j] + P[j][i]) / (2.0 * N)
                    P[i][j] = max(P[i][j], 1e-12)  # Numerical stability
        
        return P
    
    def compute_low_dim_affinities(self, Y: List[List[float]]) -> Tuple[List[List[float]], List[List[float]]]:
        """
        Compute low-dimensional affinities Q_ij using Student-t distribution.
        
        Returns:
            Tuple of (Q matrix, numerator matrix for gradient computation)
        """
        N = len(Y)
        num = [[0.0] * N for _ in range(N)]
        Q = [[0.0] * N for _ in range(N)]
        
        # Compute numerators
        sum_num = 0.0
        for i in range(N):
            for j in range(i + 1, N):
                dist = self.euclidean_squared(Y[i], Y[j])
                num_ij = 1.0 / (1.0 + dist)
                num[i][j] = num[j][i] = num_ij
                sum_num += 2.0 * num_ij
        
        # Normalize to get Q (avoid division by zero)
        sum_num = max(sum_num, 1e-12)
        for i in range(N):
            for j in range(N):
                Q[i][j] = max(num[i][j] / sum_num, 1e-12) if i != j else 0.0
        
        return Q, num
    
    def compute_gradient(self, P: List[List[float]], Q: List[List[float]], 
                        Y: List[List[float]], num: List[List[float]]) -> List[List[float]]:
        """Compute the gradient of the cost function."""
        N = len(Y)
        dims = len(Y[0])
        dY = [[0.0] * dims for _ in range(N)]
        
        for i in range(N):
            for d in range(dims):
                grad = 0.0
                for j in range(N):
                    if i != j:
                        diff = Y[i][d] - Y[j][d]
                        grad += 4.0 * (P[i][j] - Q[i][j]) * num[i][j] * diff
                dY[i][d] = grad
        
        return dY
    
    def compute_cost(self, P: List[List[float]], Q: List[List[float]]) -> float:
        """Compute KL divergence cost."""
        cost = 0.0
        N = len(P)
        
        for i in range(N):
            for j in range(N):
                if i != j and P[i][j] > 1e-12 and Q[i][j] > 1e-12:
                    cost += P[i][j] * math.log(P[i][j] / Q[i][j])
        
        return cost
    
    def center_embedding(self, Y: List[List[float]]) -> List[List[float]]:
        """Center the embedding around the origin."""
        N = len(Y)
        dims = len(Y[0])
        
        # Compute means
        means = [sum(Y[i][d] for i in range(N)) / N for d in range(dims)]
        
        # Center the data
        for i in range(N):
            for d in range(dims):
                Y[i][d] -= means[d]
        
        return Y
    
    def fit_transform(self, X: List[List[float]]) -> List[List[float]]:
        """
        Fit t-SNE on X and return the embedding.
        
        Args:
            X: High-dimensional data points
            
        Returns:
            Low-dimensional embedding
        """
        if not X or not X[0]:
            return []
        
        if self.config.verbose:
            print(f"Running t-SNE with {len(X)} samples, {len(X[0])} dimensions")
            print(f"Target dimensions: {self.config.dims}")
            print(f"Perplexity: {self.config.perplexity}")
            print(f"Iterations: {self.config.iterations}")
            print(f"Learning rate: {self.config.learning_rate}")
        
        start_time = time.time()
        N = len(X)
        
        # Compute high-dimensional affinities
        P = self.compute_affinities(X)
        
        # Initialize low-dimensional embedding
        Y = [[random.gauss(0, 1e-4) for _ in range(self.config.dims)] for _ in range(N)]
        
        # Initialize optimization variables
        dY = [[0.0] * self.config.dims for _ in range(N)]
        iY = [[0.0] * self.config.dims for _ in range(N)]  # Momentum term
        gains = [[1.0] * self.config.dims for _ in range(N)]
        
        if self.config.verbose:
            print("\nStarting optimization...")
        
        # Main optimization loop
        for iteration in range(self.config.iterations):
            # Apply early exaggeration
            if iteration < self.config.early_exaggeration_iter:
                P_effective = [[P[i][j] * self.config.early_exaggeration for j in range(N)] for i in range(N)]
            else:
                P_effective = P
            
            # Compute low-dimensional affinities
            Q, num = self.compute_low_dim_affinities(Y)
            
            # Compute gradient
            dY = self.compute_gradient(P_effective, Q, Y, num)
            
            # Update gains (adaptive learning rates)
            for i in range(N):
                for d in range(self.config.dims):
                    # Check for sign changes in gradient
                    sign_change = (dY[i][d] > 0) != (iY[i][d] > 0)
                    gains[i][d] = (gains[i][d] + 0.2) if sign_change else (gains[i][d] * 0.8)
                    gains[i][d] = max(gains[i][d], self.config.min_gain)
            
            # Update embedding using momentum
            for i in range(N):
                for d in range(self.config.dims):
                    iY[i][d] = (self.config.momentum * iY[i][d] - 
                               self.config.learning_rate * gains[i][d] * dY[i][d])
                    Y[i][d] += iY[i][d]
            
            # Center the embedding
            Y = self.center_embedding(Y)
            
            # Track progress
            if (iteration + 1) % 50 == 0 or iteration == 0:
                cost = self.compute_cost(P_effective, Q)
                self.cost_history.append(cost)
                
                if self.config.verbose:
                    elapsed = time.time() - start_time
                    print(f"Iteration {iteration + 1:4d}: Cost = {cost:.6f}, "
                          f"Time = {elapsed:.2f}s")
        
        if self.config.verbose:
            total_time = time.time() - start_time
            print(f"\nt-SNE completed in {total_time:.2f} seconds")
        
        return Y


def normalize_data(X: List[List[float]]) -> List[List[float]]:
    """
    Normalize data to zero mean and unit variance per feature.
    
    Args:
        X: Input data matrix
        
    Returns:
        Normalized data matrix
    """
    if not X or not X[0]:
        return X
    
    n_features = len(X[0])
    n_samples = len(X)
    
    # Create a copy to avoid modifying original data
    X_normalized = [row[:] for row in X]
    
    for feature_idx in range(n_features):
        # Extract feature column
        feature_values = [X_normalized[i][feature_idx] for i in range(n_samples)]
        
        # Compute mean and standard deviation
        mean = sum(feature_values) / n_samples
        variance = sum((x - mean) ** 2 for x in feature_values) / n_samples
        std = math.sqrt(variance) if variance > 0 else 1.0
        
        # Normalize feature
        for sample_idx in range(n_samples):
            X_normalized[sample_idx][feature_idx] = (X_normalized[sample_idx][feature_idx] - mean) / std
    
    return X_normalized


def generate_realistic_data(dimensions: int = 15, total_samples: int = 300) -> Tuple[List[List[float]], List[int]]:
    """
    Generate realistic, varied data that mimics real-world scenarios.
    Creates clusters with different shapes, sizes, densities, and outliers.
    
    Args:
        dimensions: Number of dimensions for the data
        total_samples: Total number of samples to generate
    
    Returns:
        Tuple of (data, labels)
    """
    data = []
    labels = []
    current_label = 0
    
    # Cluster 1: Dense, spherical cluster (e.g., well-defined group)
    n_samples_1 = int(total_samples * 0.25)
    center_1 = [random.uniform(-2, 2) for _ in range(dimensions)]
    for _ in range(n_samples_1):
        point = []
        for d in range(dimensions):
            if d < 5:  # First few dimensions have tight clustering
                point.append(center_1[d] + random.gauss(0, 0.3))
            else:  # Other dimensions have more spread
                point.append(center_1[d] + random.gauss(0, 0.8))
        data.append(point)
        labels.append(current_label)
    current_label += 1
    
    # Cluster 2: Elongated cluster (e.g., data following a trend)
    n_samples_2 = int(total_samples * 0.2)
    base_point = [random.uniform(-1, 1) for _ in range(dimensions)]
    direction = [random.gauss(0, 1) for _ in range(dimensions)]
    # Normalize direction vector
    magnitude = math.sqrt(sum(x**2 for x in direction))
    direction = [x / magnitude for x in direction]
    
    for _ in range(n_samples_2):
        # Generate points along the direction with some perpendicular spread
        t = random.uniform(-3, 3)  # Parameter along the main direction
        perpendicular_noise = [random.gauss(0, 0.4) for _ in range(dimensions)]
        
        point = []
        for d in range(dimensions):
            main_component = base_point[d] + t * direction[d]
            point.append(main_component + perpendicular_noise[d])
        
        data.append(point)
        labels.append(current_label)
    current_label += 1
    
    # Cluster 3: Loose, irregular cluster (e.g., heterogeneous group)
    n_samples_3 = int(total_samples * 0.25)
    # Multiple sub-centers within this cluster
    sub_centers = []
    for _ in range(3):
        sub_center = [random.uniform(1, 4) for _ in range(dimensions)]
        sub_centers.append(sub_center)
    
    for i in range(n_samples_3):
        # Choose a sub-center randomly
        center = random.choice(sub_centers)
        point = []
        for d in range(dimensions):
            # Vary the spread by dimension
            if d % 3 == 0:  # Some dimensions have tight clustering
                spread = 0.5
            elif d % 3 == 1:  # Some have medium spread
                spread = 1.2
            else:  # Others have loose spread
                spread = 2.0
            
            point.append(center[d] + random.gauss(0, spread))
        
        data.append(point)
        labels.append(current_label)
    current_label += 1
    
    # Cluster 4: Ring/Donut shaped cluster (non-spherical)
    n_samples_4 = int(total_samples * 0.15)
    ring_center = [random.uniform(-3, -1) for _ in range(dimensions)]
    ring_radius = 2.0
    
    for _ in range(n_samples_4):
        # Generate point on a ring in first two dimensions, noise in others
        angle = random.uniform(0, 2 * math.pi)
        radius = ring_radius + random.gauss(0, 0.3)  # Add some width to the ring
        
        point = ring_center[:]
        point[0] += radius * math.cos(angle)
        point[1] += radius * math.sin(angle)
        
        # Add noise to other dimensions
        for d in range(2, dimensions):
            point[d] += random.gauss(0, 0.6)
        
        data.append(point)
        labels.append(current_label)
    current_label += 1
    
    # Add outliers (scattered individual points)
    n_outliers = total_samples - len(data)
    for _ in range(n_outliers):
        # Scattered outliers in random locations
        point = [random.uniform(-6, 6) for _ in range(dimensions)]
        data.append(point)
        labels.append(current_label)  # Each outlier gets its own label
        current_label += 1
    
    # Add some correlated noise across dimensions to make it more realistic
    correlation_strength = 0.3
    for i in range(len(data)):
        base_noise = random.gauss(0, 1)
        for d in range(dimensions):
            # Add correlated noise to some dimensions
            if d < dimensions // 2:
                data[i][d] += correlation_strength * base_noise
    
    return data, labels


def generate_mixed_density_clusters(dimensions: int = 12, total_samples: int = 250) -> Tuple[List[List[float]], List[int]]:
    """
    Generate clusters with very different densities and sizes - more like real data.
    
    Args:
        dimensions: Number of dimensions
        total_samples: Total number of samples
    
    Returns:
        Tuple of (data, labels)
    """
    data = []
    labels = []
    
    # Large, sparse cluster (like a broad category)
    n_large = int(total_samples * 0.4)
    center_large = [0] * dimensions
    for _ in range(n_large):
        point = []
        for d in range(dimensions):
            # Some dimensions cluster tightly, others spread widely
            if d < 3:
                spread = 0.8
            elif d < 7:
                spread = 2.5
            else:
                spread = 1.8
            point.append(center_large[d] + random.gauss(0, spread))
        data.append(point)
        labels.append(0)
    
    # Small, dense cluster (like a specialized subgroup)
    n_small_dense = int(total_samples * 0.15)
    center_dense = [random.uniform(3, 5) for _ in range(dimensions)]
    for _ in range(n_small_dense):
        point = []
        for d in range(dimensions):
            point.append(center_dense[d] + random.gauss(0, 0.2))
        data.append(point)
        labels.append(1)
    
    # Medium cluster with internal structure
    n_medium = int(total_samples * 0.25)
    for i in range(n_medium):
        # Create two sub-clusters within this group
        if i < n_medium // 2:
            center = [-2, -2] + [random.uniform(-1, 1) for _ in range(dimensions - 2)]
        else:
            center = [-1, -3] + [random.uniform(-1, 1) for _ in range(dimensions - 2)]
        
        point = []
        for d in range(dimensions):
            spread = random.uniform(0.4, 1.2)  # Variable spread per point
            point.append(center[d] + random.gauss(0, spread))
        data.append(point)
        labels.append(2)
    
    # Bridge cluster (connects other clusters)
    n_bridge = total_samples - len(data)
    for _ in range(n_bridge):
        # Points scattered between main clusters
        if random.random() < 0.5:
            # Between cluster 0 and 2
            t = random.uniform(0, 1)
            base = [t * (-1) + (1-t) * 0, t * (-2.5) + (1-t) * 0]
        else:
            # Between cluster 1 and 2
            t = random.uniform(0, 1)
            base = [t * 4 + (1-t) * (-1.5), t * 4 + (1-t) * (-2.5)]
        
        point = base + [random.gauss(0, 1.5) for _ in range(dimensions - 2)]
        data.append(point)
        labels.append(3)
    
    return data, labels


def save_embedding(embedding: List[List[float]], labels: List[int], filename: str = "tsne_output.tsv"):
    """
    Save t-SNE embedding to a TSV file.
    
    Args:
        embedding: 2D embedding coordinates
        labels: Cluster labels
        filename: Output filename
    """
    with open(filename, "w") as f:
        f.write("x\ty\tlabel\n")  # Header
        for point, label in zip(embedding, labels):
            f.write(f"{point[0]:.6f}\t{point[1]:.6f}\t{label}\n")
    
    print(f"Embedding saved to '{filename}'")


if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)
    
    # Choose between different data generation methods
    print("Choose data generation method:")
    print("1. Realistic varied clusters (default)")
    print("2. Mixed density clusters")
    
    choice = input("Enter choice (1 or 2, or press Enter for 1): ").strip()
    
    if choice == "2":
        print("Generating mixed density cluster data...")
        data, labels = generate_mixed_density_clusters(dimensions=15, total_samples=300)
    else:
        print("Generating realistic varied cluster data...")
        data, labels = generate_realistic_data(dimensions=18, total_samples=350)
    
    print(f"Generated {len(data)} samples with {len(data[0])} dimensions")
    print(f"Number of unique clusters: {len(set(labels))}")
    
    # Show cluster sizes
    from collections import Counter
    cluster_counts = Counter(labels)
    print("Cluster sizes:", dict(cluster_counts))
    
    # Normalize the data
    data = normalize_data(data)
    
    # Configure t-SNE
    config = TSNEConfig(
        dims=2,
        perplexity=25.0,  # Slightly lower for more varied data
        iterations=1000,
        learning_rate=200.0,
        early_exaggeration=12.0,
        verbose=True
    )
    
    # Run t-SNE
    tsne = TSNE(config)
    embedding = tsne.fit_transform(data)
    
    # Save results
    save_embedding(embedding, labels)
    
    # Print some statistics
    if tsne.cost_history:
        print(f"\nFinal cost: {tsne.cost_history[-1]:.6f}")
        if len(tsne.cost_history) > 1:
            print(f"Cost reduction: {tsne.cost_history[0] - tsne.cost_history[-1]:.6f}")
    else:
        print("No cost history available.")
    
    # Print final embedding statistics
    print(f"Final embedding shape: {len(embedding)} points, {len(embedding[0])} dimensions")
    
    print("\nTo visualize the results, you can plot the tsne_output.tsv file")
    print("The file contains x, y coordinates and cluster labels for each point")