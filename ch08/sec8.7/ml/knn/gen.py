import csv
import random
from sklearn.neighbors import KNeighborsClassifier

random.seed(42)

# Generate training data
def generate_points(label, center_x, center_y, count):
    return [(random.gauss(center_x, 10), random.gauss(center_y, 10), label) for _ in range(count)]

train_apples = generate_points("apple", 50, 50, 50)
train_oranges = generate_points("orange", 150, 150, 50)

train_data = train_apples + train_oranges
X_train = [(x, y) for x, y, _ in train_data]
y_train = [label for _, _, label in train_data]

# Generate unlabeled test points
test_data = [(random.uniform(0, 200), random.uniform(0, 200)) for _ in range(50)]

# KNN classification
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(X_train, y_train)
predictions = knn.predict(test_data)

# Save to CSV
with open("data.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["x", "y", "type"])
    for x, y, label in train_data:
        writer.writerow([x, y, label])
    for (x, y), label in zip(test_data, predictions):
        writer.writerow([x, y, f"predicted_{label}"])



