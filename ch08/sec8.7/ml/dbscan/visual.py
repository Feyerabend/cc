import math
import random
from PIL import Image, ImageDraw

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
        """Run DBSCAN clustering algorithm"""
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

def visualize_clusters(points, labels, filename="dbscan_result.png", width=800, height=800):
    """Create a visual representation of the clustering results"""
    
    # Find data bounds
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    
    # Add padding
    padding = 0.1 * max(max_x - min_x, max_y - min_y)
    min_x -= padding
    max_x += padding
    min_y -= padding
    max_y += padding
    
    # Create image
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Define colors for clusters (bright, distinct colors)
    colors = [
        '#FF6B6B',  # Red
        '#4ECDC4',  # Teal
        '#45B7D1',  # Blue
        '#96CEB4',  # Green
        '#FFEAA7',  # Yellow
        '#DDA0DD',  # Plum
        '#98D8C8',  # Mint
        '#F7DC6F',  # Light yellow
        '#BB8FCE',  # Light purple
        '#85C1E9'   # Light blue
    ]
    
    # Color for noise points
    noise_color = '#2C3E50'  # Dark gray
    
    def map_to_canvas(x, y):
        canvas_x = int((x - min_x) / (max_x - min_x) * (width - 40) + 20)
        canvas_y = int((max_y - y) / (max_y - min_y) * (height - 40) + 20)  # Flip Y
        return canvas_x, canvas_y

    # Draw points
    point_radius = 8
    for i, (point, label) in enumerate(zip(points, labels)):
        x, y = map_to_canvas(point[0], point[1])

        if label == -1:  # Noise point
            color = noise_color
            # Draw X for noise points
            draw.line([x-point_radius, y-point_radius, x+point_radius, y+point_radius], 
                     fill=color, width=3)
            draw.line([x-point_radius, y+point_radius, x+point_radius, y-point_radius], 
                     fill=color, width=3)
        else:  # Cluster point
            color = colors[label % len(colors)]
            # Draw filled circle
            draw.ellipse([x-point_radius, y-point_radius, x+point_radius, y+point_radius],
                        fill=color, outline='black', width=2)
    
    # Add legend
    legend_x = 20
    legend_y = height - 150
    
    # Count clusters
    unique_labels = set(labels)
    cluster_labels = [l for l in unique_labels if l != -1]
    has_noise = -1 in unique_labels
    
    draw.rectangle([legend_x-10, legend_y-10, legend_x+200, legend_y+len(cluster_labels)*25+40], 
                  outline='black', fill='white')
    
    draw.text((legend_x, legend_y), "Legend:", fill='black')
    legend_y += 20
    
    for cluster_id in sorted(cluster_labels):
        color = colors[cluster_id % len(colors)]
        count = labels.count(cluster_id)
        
        # Draw sample circle
        draw.ellipse([legend_x, legend_y, legend_x+12, legend_y+12], 
                    fill=color, outline='black')
        draw.text((legend_x+20, legend_y-2), f"Cluster {cluster_id} ({count} points)", fill='black')
        legend_y += 20
    
    if has_noise:
        noise_count = labels.count(-1)
        draw.line([legend_x+2, legend_y+2, legend_x+10, legend_y+10], fill=noise_color, width=2)
        draw.line([legend_x+2, legend_y+10, legend_x+10, legend_y+2], fill=noise_color, width=2)
        draw.text((legend_x+20, legend_y-2), f"Noise ({noise_count} points)", fill='black')
    
    # Save image
    img.save(filename)
    print(f"Visualisation saved as '{filename}'")
    return img

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
    
    print("\nCreating visualisation ..")
    visualize_clusters(points, labels)


