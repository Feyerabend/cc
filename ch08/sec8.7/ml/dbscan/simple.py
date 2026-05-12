import math
import random

class DBSCAN:
    def __init__(self, eps=0.5, min_samples=5):
        self.eps = eps
        self.min_samples = min_samples
        self.labels = None
        
    def euclidean_distance(self, p1, p2):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))
    
    def get_neighbors(self, points, point_idx):
        neighbors = []
        for i, point in enumerate(points):
            if self.euclidean_distance(points[point_idx], point) <= self.eps:
                neighbors.append(i)
        return neighbors
    
    def fit(self, points):
        n_points = len(points)
        self.labels = [-1] * n_points  # -1 means unclassified
        cluster_id = 0
        
        for i in range(n_points):
            # Skip if point already processed
            if self.labels[i] != -1:
                continue
                
            # Find neighbors
            neighbors = self.get_neighbors(points, i)
            
            # Check if core point
            if len(neighbors) < self.min_samples:
                self.labels[i] = -1  # Mark as noise
                continue
            
            # Start new cluster
            self.labels[i] = cluster_id
            
            # Expand cluster
            seed_set = neighbors[:]
            j = 0
            while j < len(seed_set):
                neighbor_idx = seed_set[j]
                
                # Change noise to border point
                if self.labels[neighbor_idx] == -1:
                    self.labels[neighbor_idx] = cluster_id
                
                # Skip if already processed
                elif self.labels[neighbor_idx] != -1:
                    j += 1
                    continue
                
                # Add to cluster
                self.labels[neighbor_idx] = cluster_id

                # If neighbor is core point, add its neighbors
                neighbor_neighbors = self.get_neighbors(points, neighbor_idx)
                if len(neighbor_neighbors) >= self.min_samples:
                    seed_set.extend(neighbor_neighbors)

                j += 1

            cluster_id += 1

        return self.labels

def generate_sample_data():
    random.seed(42)
    points = []

    # Cluster 1: around (2, 2)
    for _ in range(20):
        x = random.gauss(2, 0.5)
        y = random.gauss(2, 0.5)
        points.append([x, y])

    # Cluster 2: around (8, 8)
    for _ in range(15):
        x = random.gauss(8, 0.7)
        y = random.gauss(8, 0.7)
        points.append([x, y])

    # Noise points
    for _ in range(5):
        x = random.uniform(0, 10)
        y = random.uniform(0, 10)
        points.append([x, y])

    return points

def print_results(points, labels):
    clusters = {}
    noise_points = []

    for i, label in enumerate(labels):
        if label == -1:
            noise_points.append(i)
        else:
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(i)

    print(f"Found {len(clusters)} clusters and {len(noise_points)} noise points")
    print()

    for cluster_id in sorted(clusters.keys()):
        print(f"Cluster {cluster_id}: {len(clusters[cluster_id])} points")
        for point_idx in clusters[cluster_id][:5]:  # Show first 5 points
            x, y = points[point_idx]
            print(f"  Point {point_idx}: ({x:.2f}, {y:.2f})")
        if len(clusters[cluster_id]) > 5:
            print(f"  .. and {len(clusters[cluster_id]) - 5} more points")
        print()

    if noise_points:
        print(f"Noise points: {len(noise_points)}")
        for point_idx in noise_points[:3]:  # Show first 3 noise points
            x, y = points[point_idx]
            print(f"  Point {point_idx}: ({x:.2f}, {y:.2f})")
        if len(noise_points) > 3:
            print(f"  .. and {len(noise_points) - 3} more noise points")

if __name__ == "__main__":
    points = generate_sample_data()
    print(f"Generated {len(points)} sample points")
    print()
    
    # Run DBSCAN
    dbscan = DBSCAN(eps=1.5, min_samples=3)
    labels = dbscan.fit(points)
    
    print_results(points, labels)

