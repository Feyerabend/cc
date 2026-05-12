import csv
import random
import numpy as np
from PIL import Image, ImageDraw
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from collections import Counter

random.seed(42)
np.random.seed(42)

# Generate higher-dimensional training data for PCA
def generate_points_nd(label, center, count, dimensions=5):
    """Generate n-dimensional points around a center"""
    points = []
    for _ in range(count):
        point = [random.gauss(center[i], 2) for i in range(dimensions)]
        points.append(point + [label])
    return points

# Better test data generation with improved spread
def generate_comprehensive_test_data(apple_center, orange_center, n_samples=40):
    """Generate test data with better coverage of the feature space"""
    test_data = []
    
    # 1. Points near apple cluster (should predict apple)
    for _ in range(n_samples // 4):
        point = [random.gauss(apple_center[i], 3) for i in range(5)]
        test_data.append(point)
    
    # 2. Points near orange cluster (should predict orange)  
    for _ in range(n_samples // 4):
        point = [random.gauss(orange_center[i], 3) for i in range(5)]
        test_data.append(point)
        
    # 3. Points in between clusters (decision boundary region)
    for _ in range(n_samples // 4):
        # Interpolate between centers with some noise
        alpha = random.uniform(0.3, 0.7)  # Blend factor
        point = [alpha * apple_center[i] + (1-alpha) * orange_center[i] + random.gauss(0, 2) 
                for i in range(5)]
        test_data.append(point)
    
    # 4. Points outside both clusters (extrapolation test)
    for _ in range(n_samples - 3*(n_samples//4)):
        # Generate points beyond the training distribution
        point = []
        for i in range(5):
            if random.random() < 0.5:
                # Below apple cluster
                point.append(random.uniform(apple_center[i] - 10, apple_center[i] - 5))
            else:
                # Beyond orange cluster  
                point.append(random.uniform(orange_center[i] + 5, orange_center[i] + 10))
        test_data.append(point)
    
    return np.array(test_data)

# Create 5D data centers
apple_center = [10, 20, 30, 15, 25]
orange_center = [50, 40, 60, 45, 55]

train_apples = generate_points_nd("apple", apple_center, 50, 5)
train_oranges = generate_points_nd("orange", orange_center, 50, 5)

train_data = train_apples + train_oranges

# Separate features and labels
X_original = np.array([row[:-1] for row in train_data])  # All columns except last
y_labels = [row[-1] for row in train_data]  # Last column

print(f"Original data shape: {X_original.shape}")
print(f"Labels: {set(y_labels)}")

# Split for validation
X_train_split, X_val, y_train_split, y_val = train_test_split(X_original, y_labels, test_size=0.2, random_state=42)

# Train KNN on original high-dimensional data
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(X_train_split, y_train_split)

# Validate
val_predictions = knn.predict(X_val)
validation_accuracy = accuracy_score(y_val, val_predictions)
print(f"Validation accuracy (5D): {validation_accuracy:.3f}")

# Apply PCA to reduce to 2D
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_original)

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

print(f"PCA explained variance ratio: {pca.explained_variance_ratio_}")
print(f"Total variance explained: {sum(pca.explained_variance_ratio_):.3f}")

# Generate improved test data in original 5D space
test_data_5d = generate_comprehensive_test_data(apple_center, orange_center, 40)

# Predict labels for test data using original 5D model
knn_final = KNeighborsClassifier(n_neighbors=5)
knn_final.fit(X_original, y_labels)
test_predictions = knn_final.predict(test_data_5d)

# Transform test data to PCA space
test_data_scaled = scaler.transform(test_data_5d)
test_data_pca = pca.transform(test_data_scaled)

# Add diagnostic analysis
print(f"\nTest prediction distribution: {Counter(test_predictions)}")

# Calculate distances to help interpret results
apple_distances = [np.linalg.norm(point - apple_center) for point in test_data_5d]
orange_distances = [np.linalg.norm(point - orange_center) for point in test_data_5d]

print("\nTest point analysis (showing first 10):")
for i, (pred, apple_dist, orange_dist) in enumerate(zip(test_predictions[:10], apple_distances[:10], orange_distances[:10])):
    closest = "apple" if apple_dist < orange_dist else "orange"
    agreement = "✓" if pred == closest else "✗"
    print(f"Point {i:2d}: predicted={pred:6s}, closest={closest:6s} {agreement}, apple_dist={apple_dist:.2f}, orange_dist={orange_dist:.2f}")

def normalize_coords(data, width, height, margin=50):
    """Normalize coordinates to fit in image with margin"""
    min_x, max_x = data[:, 0].min(), data[:, 0].max()
    min_y, max_y = data[:, 1].min(), data[:, 1].max()
    
    # Scale to fit in image with margin
    scale_x = (width - 2 * margin) / (max_x - min_x) if max_x != min_x else 1
    scale_y = (height - 2 * margin) / (max_y - min_y) if max_y != min_y else 1
    scale = min(scale_x, scale_y)
    
    # Center and scale
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    normalized = np.zeros_like(data)
    normalized[:, 0] = (data[:, 0] - center_x) * scale + width // 2
    normalized[:, 1] = (data[:, 1] - center_y) * scale + height // 2
    
    return normalized.astype(int)

# Save results to CSV with additional analysis
with open("pca_results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["pc1", "pc2", "type", "original_label", "apple_distance", "orange_distance", "closest_center"])
    
    # Training data
    for i, (pc1, pc2) in enumerate(X_pca):
        apple_dist = np.linalg.norm(X_original[i] - apple_center)
        orange_dist = np.linalg.norm(X_original[i] - orange_center)
        closest = "apple" if apple_dist < orange_dist else "orange"
        writer.writerow([pc1, pc2, "training", y_labels[i], apple_dist, orange_dist, closest])
    
    # Test data
    for i, (pc1, pc2) in enumerate(test_data_pca):
        apple_dist = apple_distances[i]
        orange_dist = orange_distances[i]
        closest = "apple" if apple_dist < orange_dist else "orange"
        writer.writerow([pc1, pc2, "predicted", test_predictions[i], apple_dist, orange_dist, closest])

print("\nResults saved to pca_results.csv")
print(f"Test predictions: {list(test_predictions)}")

# Calculate prediction accuracy based on nearest center
correct_predictions = sum(1 for pred, apple_dist, orange_dist in 
                         zip(test_predictions, apple_distances, orange_distances)
                         if (pred == "apple" and apple_dist < orange_dist) or 
                            (pred == "orange" and orange_dist < apple_dist))

print(f"Test accuracy (based on nearest center): {correct_predictions/len(test_predictions):.3f}")
