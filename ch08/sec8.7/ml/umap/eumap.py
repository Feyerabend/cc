import numpy as np
from PIL import Image, ImageDraw
import csv
import umap

# Parameters
N_SAMPLES = 150
N_CLUSTERS = 3
N_FEATURES = 3
N_COMPONENTS = 2
N_NEIGHBORS = 15
MIN_DIST = 0.1

# Generate synthetic data (mimics C code)
np.random.seed(42)
def generate_synthetic_data():
    samples_per_cluster = N_SAMPLES // N_CLUSTERS
    X = np.zeros((N_SAMPLES, N_FEATURES))
    labels = np.zeros(N_SAMPLES, dtype=int)
    for c in range(N_CLUSTERS):
        center = np.random.uniform(-5, 5, N_FEATURES)
        for i in range(samples_per_cluster):
            idx = c * samples_per_cluster + i
            labels[idx] = c
            X[idx] = center + np.random.uniform(-1, 1, N_FEATURES)
    return X, labels

# Generate data
X, labels = generate_synthetic_data()

# Save pre-UMAP data to pre_umap_data.txt
with open("pre_umap_data.txt", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Point", "Label", "X1", "X2", "X3"])
    for i in range(N_SAMPLES):
        writer.writerow([i, labels[i], X[i][0], X[i][1], X[i][2]])

# Visualize pre-UMAP data (project X1 vs. X2)
X_vis = [X[:, 0], X[:, 1]]  # Use X1, X2 for 2D projection
X_vis[0] = [(x - min(X_vis[0])) / (max(X_vis[0]) - min(X_vis[0]) + 1e-8) * 400 for x in X_vis[0]]
X_vis[1] = [(x - min(X_vis[1])) / (max(X_vis[1]) - min(X_vis[1]) + 1e-8) * 400 for x in X_vis[1]]

img_pre = Image.new("RGB", (500, 500), "white")
draw_pre = ImageDraw.Draw(img_pre)
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue

for i in range(N_SAMPLES):
    x, y = X_vis[0][i], X_vis[1][i]
    draw_pre.ellipse([(x - 3, y - 3), (x + 3, y + 3)], fill=colors[labels[i]])

img_pre.save("pre_umap_output.png")
print("Pre-UMAP data saved to pre_umap_data.txt")
print("Pre-UMAP visualization saved as pre_umap_output.png")

# Run UMAP
umap_model = umap.UMAP(
    n_neighbors=N_NEIGHBORS,
    min_dist=MIN_DIST,
    n_components=N_COMPONENTS,
    random_state=42
)
Y = umap_model.fit_transform(X)

# Save post-UMAP results to umap_data.txt
with open("umap_data.txt", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Point", "Label", "X1", "X2", "X3", "Y1", "Y2"])
    for i in range(N_SAMPLES):
        writer.writerow([i, labels[i], X[i][0], X[i][1], X[i][2], Y[i][0], Y[i][1]])

# Visualize post-UMAP
Y = [Y[:, 0], Y[:, 1]]
Y[0] = [(y - min(Y[0])) / (max(Y[0]) - min(Y[0]) + 1e-8) * 400 for y in Y[0]]
Y[1] = [(y - min(Y[1])) / (max(Y[1]) - min(Y[1]) + 1e-8) * 400 for y in Y[1]]

img = Image.new("RGB", (500, 500), "white")
draw = ImageDraw.Draw(img)
for i in range(N_SAMPLES):
    x, y = Y[0][i], Y[1][i]
    draw.ellipse([(x - 3, y - 3), (x + 3, y + 3)], fill=colors[labels[i]])

img.save("umap_output.png")
print("Post-UMAP data saved to umap_data.txt")
print("Post-UMAP visualization saved as umap_output.png")