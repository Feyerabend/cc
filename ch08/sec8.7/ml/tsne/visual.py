"""
t-SNE Visualization using Pillow (PIL) - Fixed to read from file
Scatter plots of t-SNE embeddings with automatic clustering.
"""

from PIL import Image, ImageDraw, ImageFont
import math
import colorsys
from typing import List, Tuple, Optional, Dict, Any
import random
import csv


class KMeans:
    """Simple K-means clustering implementation for discovering clusters in t-SNE output."""
    
    def __init__(self, n_clusters: int = 4, max_iters: int = 100, random_seed: Optional[int] = None):
        self.n_clusters = n_clusters
        self.max_iters = max_iters
        if random_seed is not None:
            random.seed(random_seed)
    
    def distance(self, point1: List[float], point2: List[float]) -> float:
        """Compute Euclidean distance between two points."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(point1, point2)))
    
    def fit(self, points: List[List[float]]) -> List[int]:
        """
        Perform K-means clustering on 2D points.
        
        Args:
            points: List of 2D coordinates
            
        Returns:
            List of cluster labels for each point
        """
        if len(points) < self.n_clusters:
            # If we have fewer points than clusters, assign each point to its own cluster
            return list(range(len(points)))
        
        # Initialize centroids randomly - FIXED: ensure they're spread out
        if len(points) >= self.n_clusters:
            # Use k-means++ initialization for better spread
            centroids = []
            centroids.append(random.choice(points))
            
            for _ in range(1, self.n_clusters):
                distances = []
                for point in points:
                    min_dist = min(self.distance(point, c) for c in centroids)
                    distances.append(min_dist ** 2)
                
                # Weighted random selection
                total_dist = sum(distances)
                if total_dist > 0:
                    probs = [d / total_dist for d in distances]
                    cumulative = []
                    running_sum = 0
                    for p in probs:
                        running_sum += p
                        cumulative.append(running_sum)
                    
                    r = random.random()
                    for i, cum_prob in enumerate(cumulative):
                        if r <= cum_prob:
                            centroids.append(points[i])
                            break
                else:
                    centroids.append(random.choice(points))
        
        print(f"DEBUG: Initial centroids: {centroids[:2]}...")
        
        for iteration in range(self.max_iters):
            # Assign points to closest centroids
            labels = []
            for point in points:
                distances = [self.distance(point, centroid) for centroid in centroids]
                closest_centroid = distances.index(min(distances))
                labels.append(closest_centroid)
            
            # DEBUG: Check cluster distribution
            if iteration == 0:
                cluster_counts = {}
                for label in labels:
                    cluster_counts[label] = cluster_counts.get(label, 0) + 1
                print(f"DEBUG: Cluster distribution: {cluster_counts}")
            
            # Update centroids
            new_centroids = []
            for cluster_id in range(self.n_clusters):
                cluster_points = [points[i] for i, label in enumerate(labels) if label == cluster_id]
                
                if cluster_points:
                    # Calculate mean of cluster points
                    new_centroid = [
                        sum(point[dim] for point in cluster_points) / len(cluster_points)
                        for dim in range(len(cluster_points[0]))
                    ]
                    new_centroids.append(new_centroid)
                else:
                    # If cluster is empty, keep the old centroid
                    new_centroids.append(centroids[cluster_id])
            
            # Check for convergence
            converged = True
            for old, new in zip(centroids, new_centroids):
                if self.distance(old, new) > 1e-6:
                    converged = False
                    break
            
            centroids = new_centroids
            
            if converged:
                print(f"DEBUG: Converged after {iteration + 1} iterations")
                break
        
        # Final cluster distribution
        final_cluster_counts = {}
        for label in labels:
            final_cluster_counts[label] = final_cluster_counts.get(label, 0) + 1
        print(f"DEBUG: Final cluster distribution: {final_cluster_counts}")
        
        return labels


class TSNEVisualizer:
    """
    A class for creating visualizations of t-SNE embeddings using Pillow.
    Now includes automatic clustering discovery with debugging and file input support.
    """
    
    def __init__(self, width: int = 800, height: int = 600, margin: int = 60):
        self.width = width
        self.height = height
        self.margin = margin
        self.plot_width = width - 2 * margin
        self.plot_height = height - 2 * margin
        
        # Default styling
        self.background_color = (255, 255, 255)  # White
        self.grid_color = (240, 240, 240)  # Light gray
        self.text_color = (50, 50, 50)  # Dark gray
        self.point_size = 4
        self.alpha = 180  # Transparency for points
    
    def load_data_from_file(self, filename: str) -> Tuple[List[List[float]], List[int]]:
        """
        Load t-SNE data from a tab-separated file.
        
        Args:
            filename: Path to the data file
            
        Returns:
            Tuple of (embedding coordinates, original labels)
        """
        embedding = []
        original_labels = []
        
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                # Try to detect the delimiter
                sample = file.read(1024)
                file.seek(0)
                
                if '\t' in sample:
                    delimiter = '\t'
                elif ',' in sample:
                    delimiter = ','
                else:
                    delimiter = '\t'  # default
                
                reader = csv.DictReader(file, delimiter=delimiter)
                
                for row in reader:
                    try:
                        # Extract x, y coordinates
                        x = float(row['x'])
                        y = float(row['y'])
                        label = int(row['label'])
                        
                        embedding.append([x, y])
                        original_labels.append(label)
                        
                    except (ValueError, KeyError) as e:
                        print(f"Warning: Skipping invalid row: {row}. Error: {e}")
                        continue
            
            print(f"Successfully loaded {len(embedding)} data points from '{filename}'")
            print(f"Original labels found: {set(original_labels)}")
            
            return embedding, original_labels
            
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
            return [], []
        except Exception as e:
            print(f"Error reading file '{filename}': {e}")
            return [], []
        
    def estimate_clusters(self, embedding: List[List[float]], max_clusters: int = 10) -> int:
        """
        Estimate optimal number of clusters using elbow method.
        """
        if len(embedding) <= 2:
            return 1
        
        max_clusters = min(max_clusters, len(embedding) - 1)
        if max_clusters <= 1:
            return 1
        
        wcss_values = []  # Within-cluster sum of squares
        
        for k in range(1, max_clusters + 1):
            kmeans = KMeans(n_clusters=k, random_seed=42)
            labels = kmeans.fit(embedding)
            
            # Calculate WCSS
            wcss = 0
            for cluster_id in range(k):
                cluster_points = [embedding[i] for i, label in enumerate(labels) if label == cluster_id]
                if len(cluster_points) > 0:
                    # Calculate centroid
                    centroid = [
                        sum(point[dim] for point in cluster_points) / len(cluster_points)
                        for dim in range(2)
                    ]
                    # Sum squared distances to centroid
                    for point in cluster_points:
                        wcss += sum((point[dim] - centroid[dim]) ** 2 for dim in range(2))
            
            wcss_values.append(wcss)
        
        # Find elbow point (simple method)
        if len(wcss_values) < 3:
            return len(wcss_values)
        
        # Calculate differences
        differences = []
        for i in range(1, len(wcss_values)):
            differences.append(wcss_values[i-1] - wcss_values[i])
        
        # Find the point where the improvement starts to diminish
        max_diff = max(differences)
        threshold = max_diff * 0.1  # 10% of maximum improvement
        
        optimal_k = 1
        for i, diff in enumerate(differences):
            if diff > threshold:
                optimal_k = i + 2  # +2 because we start from k=1 and index from 0
            else:
                break
        
        return min(optimal_k, max_clusters)
    
    def generate_colors(self, n_colors: int, scheme: str = "hsv") -> List[Tuple[int, int, int]]:
        """Generate a list of distinct colors for different clusters."""
        colors = []
        
        print(f"DEBUG: Generating {n_colors} colors with scheme '{scheme}'")
        
        if scheme == "hsv":
            for i in range(n_colors):
                hue = i / n_colors
                saturation = 0.8
                value = 0.9
                rgb = colorsys.hsv_to_rgb(hue, saturation, value)
                color = tuple(int(c * 255) for c in rgb)
                colors.append(color)
                print(f"DEBUG: Color {i}: {color}")
                
        elif scheme == "rainbow":
            rainbow_colors = [
                (255, 0, 0),    # Red
                (255, 127, 0),  # Orange
                (255, 255, 0),  # Yellow
                (0, 255, 0),    # Green
                (0, 0, 255),    # Blue
                (75, 0, 130),   # Indigo
                (148, 0, 211),  # Violet
                (255, 20, 147), # Deep Pink
                (0, 191, 255),  # Deep Sky Blue
                (50, 205, 50),  # Lime Green
            ]
            colors = rainbow_colors[:n_colors]
            if n_colors > len(rainbow_colors):
                for i in range(len(rainbow_colors), n_colors):
                    hue = (i * 137.5) % 360 / 360
                    rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
                    colors.append(tuple(int(c * 255) for c in rgb))
                    
        elif scheme == "pastel":
            for i in range(n_colors):
                hue = i / n_colors
                saturation = 0.4
                value = 0.95
                rgb = colorsys.hsv_to_rgb(hue, saturation, value)
                colors.append(tuple(int(c * 255) for c in rgb))
                
        elif scheme == "bright":
            for i in range(n_colors):
                hue = i / n_colors
                saturation = 1.0
                value = 0.8
                rgb = colorsys.hsv_to_rgb(hue, saturation, value)
                colors.append(tuple(int(c * 255) for c in rgb))
        
        print(f"DEBUG: Generated colors: {colors}")
        return colors
    
    def normalize_coordinates(self, embedding: List[List[float]]) -> List[Tuple[float, float]]:
        """Normalize embedding coordinates to fit within the plot area."""
        if not embedding:
            return []
        
        x_coords = [point[0] for point in embedding]
        y_coords = [point[1] for point in embedding]
        
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # Add padding
        x_range = x_max - x_min
        y_range = y_max - y_min
        padding = 0.1
        
        x_min -= x_range * padding
        x_max += x_range * padding
        y_min -= y_range * padding
        y_max += y_range * padding
        
        x_range = x_max - x_min
        y_range = y_max - y_min
        
        # Avoid division by zero
        if x_range == 0:
            x_range = 1
        if y_range == 0:
            y_range = 1
        
        # Normalize to plot area
        normalized = []
        for point in embedding:
            x = self.margin + (point[0] - x_min) / x_range * self.plot_width
            y = self.margin + (1 - (point[1] - y_min) / y_range) * self.plot_height
            normalized.append((x, y))
        
        return normalized
    
    def draw_grid(self, draw: ImageDraw.Draw, n_lines: int = 10):
        """Draw a background grid."""
        # Vertical lines
        for i in range(n_lines + 1):
            x = self.margin + i * self.plot_width / n_lines
            draw.line([(x, self.margin), (x, self.height - self.margin)], 
                     fill=self.grid_color, width=1)
        
        # Horizontal lines
        for i in range(n_lines + 1):
            y = self.margin + i * self.plot_height / n_lines
            draw.line([(self.margin, y), (self.width - self.margin, y)], 
                     fill=self.grid_color, width=1)
    
    def draw_axes(self, draw: ImageDraw.Draw):
        """Draw coordinate axes."""
        # X-axis
        draw.line([(self.margin, self.height - self.margin), 
                  (self.width - self.margin, self.height - self.margin)], 
                 fill=self.text_color, width=2)
        
        # Y-axis
        draw.line([(self.margin, self.margin), 
                  (self.margin, self.height - self.margin)], 
                 fill=self.text_color, width=2)
    
    def draw_points(self, draw: ImageDraw.Draw, coordinates: List[Tuple[float, float]], 
                   labels: List[int], colors: List[Tuple[int, int, int]]):
        """Draw the data points with colors based on labels."""
        print(f"DEBUG: Drawing {len(coordinates)} points")
        print(f"DEBUG: Unique labels: {set(labels)}")
        print(f"DEBUG: Available colors: {colors}")
        
        # Create a mapping to ensure we use colors correctly
        unique_labels = sorted(list(set(labels)))
        label_to_color_index = {label: i for i, label in enumerate(unique_labels)}
        
        for i, ((x, y), label) in enumerate(zip(coordinates, labels)):
            color_index = label_to_color_index[label]
            color = colors[color_index % len(colors)]
            
            # Debug first few points
            if i < 5:
                print(f"DEBUG: Point {i}: label={label}, color_index={color_index}, color={color}")
            
            # Draw point as a circle
            radius = self.point_size
            bbox = [x - radius, y - radius, x + radius, y + radius]
            draw.ellipse(bbox, fill=color, outline=None)
    
    def draw_legend(self, draw: ImageDraw.Draw, colors: List[Tuple[int, int, int]], 
                   labels: List[str], font_size: int = 12):
        """Draw a legend for the clusters."""
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except (OSError, IOError):
                try:
                    font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", font_size)
                except (OSError, IOError):
                    font = ImageFont.load_default()
        
        legend_x = self.width - self.margin - 100
        legend_y = self.margin + 20
        
        # Background for legend
        legend_width = 90
        legend_height = len(labels) * 20 + 10
        draw.rectangle([legend_x - 5, legend_y - 5, 
                       legend_x + legend_width, legend_y + legend_height], 
                      fill=(255, 255, 255, 200), outline=self.text_color)
        
        for i, (color, label) in enumerate(zip(colors, labels)):
            y = legend_y + i * 20
            
            # Color square
            draw.rectangle([legend_x, y, legend_x + 15, y + 15], 
                          fill=color, outline=self.text_color)
            
            # Label text
            draw.text((legend_x + 20, y + 2), label, fill=self.text_color, font=font)
    
    def add_title(self, draw: ImageDraw.Draw, title: str, font_size: int = 16):
        """Add a title to the plot."""
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except (OSError, IOError):
                try:
                    font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", font_size)
                except (OSError, IOError):
                    font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), title, font=font)
        text_width = bbox[2] - bbox[0]
        
        x = (self.width - text_width) // 2
        y = 10
        
        draw.text((x, y), title, fill=self.text_color, font=font)
    
    def create_visualization(self, embedding: List[List[float]], 
                           labels: Optional[List[int]] = None,
                           n_clusters: Optional[int] = None,
                           title: str = "t-SNE Visualization", 
                           color_scheme: str = "hsv",
                           show_grid: bool = True,
                           show_legend: bool = True,
                           auto_cluster: bool = True,
                           use_original_labels: bool = False) -> Tuple[Image.Image, List[int]]:
        """
        Create a complete t-SNE visualization.
        
        Args:
            use_original_labels: If True, use the original labels from file instead of clustering
        """
        if not embedding:
            # Return empty image if no data
            img = Image.new('RGB', (self.width, self.height), self.background_color)
            return img, []
        
        # Determine cluster labels
        if use_original_labels and labels is not None:
            # Use original labels from the file
            print(f"Using original labels from file: {set(labels)}")
            cluster_labels = labels
        elif labels is None or auto_cluster:
            if n_clusters is None:
                n_clusters = self.estimate_clusters(embedding)
                print(f"Estimated optimal number of clusters: {n_clusters}")
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_seed=42)
            cluster_labels = kmeans.fit(embedding)
            print(f"Discovered {len(set(cluster_labels))} clusters")
        else:
            cluster_labels = labels
        
        # Create image
        img = Image.new('RGB', (self.width, self.height), self.background_color)
        draw = ImageDraw.Draw(img)
        
        # Generate colors for clusters
        unique_labels = sorted(list(set(cluster_labels)))
        n_clusters_actual = len(unique_labels)
        colors = self.generate_colors(n_clusters_actual, color_scheme)
        
        print(f"DEBUG: Unique labels found: {unique_labels}")
        print(f"DEBUG: Colors generated: {colors}")
        
        # Normalize coordinates
        coordinates = self.normalize_coordinates(embedding)
        
        # Draw components
        if show_grid:
            self.draw_grid(draw)
        
        self.draw_axes(draw)
        self.draw_points(draw, coordinates, cluster_labels, colors)
        
        if show_legend:
            if use_original_labels:
                legend_labels = [f"Class {label}" for label in unique_labels]
            else:
                legend_labels = [f"Cluster {label}" for label in unique_labels]
            legend_colors = colors[:len(unique_labels)]
            self.draw_legend(draw, legend_colors, legend_labels)
        
        # Update title based on visualization type
        if use_original_labels:
            title += f" (Original {n_clusters_actual} Classes)"
        elif auto_cluster and n_clusters_actual > 1:
            title += f" ({n_clusters_actual} Auto-Discovered Clusters)"
        
        self.add_title(draw, title)
        
        return img, cluster_labels
    
    def save_visualization_from_file(self, filename: str, 
                                   output_filename: str = "tsne_plot.png",
                                   use_original_labels: bool = True,
                                   **kwargs) -> List[int]:
        """
        Create and save a t-SNE visualization from a data file.
        
        Args:
            filename: Input data file path
            output_filename: Output image file path
            use_original_labels: Whether to use original labels or perform clustering
            
        Returns:
            The cluster labels that were used
        """
        # Load data from file
        embedding, original_labels = self.load_data_from_file(filename)
        
        if not embedding:
            print("No data loaded. Cannot create visualization.")
            return []
        
        # Create visualization
        img, used_labels = self.create_visualization(
            embedding, 
            original_labels if use_original_labels else None,
            use_original_labels=use_original_labels,
            **kwargs
        )
        
        # Save image
        img.save(output_filename, quality=95, optimize=True)
        print(f"Visualization saved to '{output_filename}'")
        return used_labels


def main():
    """
    Example usage of the TSNEVisualizer with file input.
    """
    data_file = "tsne_output.tsv"
    
    print(f"Loading t-SNE data from '{data_file}'...")

    visualizer = TSNEVisualizer(width=1200, height=900, margin=80)
    
    print("Creating visualization with original labels...")
    used_labels = visualizer.save_visualization_from_file(
        data_file,
        output_filename="tsne_original_labels.png",
        title="t-SNE Visualization from File Data",
        color_scheme="rainbow",
        show_grid=True,
        show_legend=True,
        use_original_labels=True
    )
    
    print(f"Used labels: {set(used_labels)}")

    print("\nCreating visualisation with automatic clustering...")
    auto_labels = visualizer.save_visualization_from_file(
        data_file,
        output_filename="tsne_auto_clusters.png",
        title="t-SNE Visualisation with Auto-Clustering",
        color_scheme="hsv",
        show_grid=True,
        show_legend=True,
        use_original_labels=False,
        auto_cluster=True
    )
    
    print(f"Auto-discovered labels: {set(auto_labels)}")
    print("\nDone! Check PNG files.")


if __name__ == "__main__":
    main()