import os
import random
import numpy as np

def generate_circle_image(size=12, noise_level=0.05):
    """Generate a more distinct circle with better positioning"""
    image = np.zeros((size, size))
    cx, cy = size // 2, size // 2
    radius = random.uniform(size * 0.25, size * 0.35)
    
    for x in range(size):
        for y in range(size):
            distance = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            if distance <= radius:
                image[x, y] = 1
            # Add anti-aliasing for smoother edges
            elif distance <= radius + 1:
                image[x, y] = max(0, 1 - (distance - radius))
    
    add_noise(image, noise_level)
    return image

def generate_square_image(size=12, noise_level=0.05):
    """Generate a more distinct square with better positioning"""
    image = np.zeros((size, size))
    side_length = random.randint(int(size * 0.5), int(size * 0.7))
    start_x = (size - side_length) // 2
    start_y = (size - side_length) // 2
    
    image[start_x:start_x + side_length, start_y:start_y + side_length] = 1
    
    add_noise(image, noise_level)
    return image

def generate_line_image(size=12, noise_level=0.05):
    """Generate a more distinct line with better thickness"""
    image = np.zeros((size, size))
    
    # Random orientation: horizontal, vertical, or diagonal
    orientation = random.choice(['horizontal', 'vertical', 'diagonal_lr', 'diagonal_rl'])
    thickness = 2  # Make lines thicker for better detection
    
    if orientation == 'horizontal':
        y_pos = size // 2
        for t in range(-thickness//2, thickness//2 + 1):
            if 0 <= y_pos + t < size:
                image[:, y_pos + t] = 1
    elif orientation == 'vertical':
        x_pos = size // 2
        for t in range(-thickness//2, thickness//2 + 1):
            if 0 <= x_pos + t < size:
                image[x_pos + t, :] = 1
    elif orientation == 'diagonal_lr':
        for x in range(size):
            for t in range(-thickness//2, thickness//2 + 1):
                y = x + t
                if 0 <= y < size:
                    image[x, y] = 1
    else:  # diagonal_rl
        for x in range(size):
            for t in range(-thickness//2, thickness//2 + 1):
                y = (size - 1 - x) + t
                if 0 <= y < size:
                    image[x, y] = 1
    
    add_noise(image, noise_level)
    return image

def add_noise(image, noise_level=0.05):
    """Add noise to image"""
    size = image.shape[0]
    num_pixels = int(size * size * noise_level)
    
    for _ in range(num_pixels):
        x, y = random.randint(0, size - 1), random.randint(0, size - 1)
        image[x, y] = 1 - image[x, y]  # Flip pixel

def save_image_ppm(image, filename):
    """Save image in PPM format"""
    with open(filename, 'w') as f:
        size = image.shape[0]
        f.write(f'P3\n{size} {size}\n255\n')
        for row in image:
            for pixel in row:
                value = int(pixel * 255)
                f.write(f'{value} {value} {value} ')
            f.write('\n')

def generate_and_save_data(num_samples=200, size=12):
    """Generate training and test datasets"""
    for folder in ["train/circle", "train/square", "train/line", 
                   "test/circle", "test/square", "test/line"]:
        os.makedirs(folder, exist_ok=True)

    # 80-20 train-test split
    train_samples = int(num_samples * 0.8)
    test_samples = num_samples - train_samples
    
    shapes = ["circle", "square", "line"]
    
    for i in range(train_samples):
        for shape in shapes:
            image = globals()[f'generate_{shape}_image'](size)
            save_image_ppm(image, f"train/{shape}/{shape}_{i}.ppm")
    
    for i in range(test_samples):
        for shape in shapes:
            image = globals()[f'generate_{shape}_image'](size)
            save_image_ppm(image, f"test/{shape}/{shape}_{i}.ppm")
    
    print(f"Generated {train_samples} training and {test_samples} test samples per class")


class Perceptron:
    def __init__(self, input_size, num_classes, learning_rate=0.01, l2_lambda=0.001):
        self.num_classes = num_classes
        self.input_size = input_size
        # Xavier initialization for better convergence
        limit = np.sqrt(6 / (input_size + num_classes))
        self.weights = np.random.uniform(-limit, limit, (num_classes, input_size))
        self.bias = np.zeros(num_classes)
        self.learning_rate = learning_rate
        self.l2_lambda = l2_lambda

    def predict(self, inputs):
        """Predict class for given inputs"""
        scores = np.dot(self.weights, inputs) + self.bias
        return np.argmax(scores)

    def train(self, training_data, labels, epochs, verbose=True):
        """Train the perceptron with optional progress reporting"""
        training_data = np.array(training_data)
        labels = np.array(labels)
        
        for epoch in range(epochs):
            # Shuffle data each epoch
            indices = np.random.permutation(len(training_data))
            shuffled_data = training_data[indices]
            shuffled_labels = labels[indices]
            
            correct = 0
            for inputs, label in zip(shuffled_data, shuffled_labels):
                prediction = self.predict(inputs)
                
                if prediction == label:
                    correct += 1
                else:
                    # Update weights with L2 regularization
                    self.weights[label] += self.learning_rate * (inputs - self.l2_lambda * self.weights[label])
                    self.weights[prediction] -= self.learning_rate * (inputs + self.l2_lambda * self.weights[prediction])
                    
                    # Update biases
                    self.bias[label] += self.learning_rate
                    self.bias[prediction] -= self.learning_rate
            
            if verbose and (epoch + 1) % 2 == 0:
                accuracy = correct / len(training_data) * 100
                print(f"Epoch {epoch + 1}/{epochs} - Training Accuracy: {accuracy:.2f}%")

def load_images_from_directory(directory, label):
    """Load all PPM images from a directory"""
    images, labels = [], []
    files = sorted([f for f in os.listdir(directory) if f.endswith(".ppm")])
    
    for filename in files:
        with open(os.path.join(directory, filename), 'r') as f:
            lines = f.readlines()[3:]  # skip header
            pixels = [float(val) / 255.0 for val in ' '.join(lines).split() if val.strip()]
            # Take only grayscale values (every 3rd value since it's RGB)
            pixels = pixels[::3]
            images.append(pixels)
            labels.append(label)
    
    return images, labels

def load_all_data():
    """Load all training and test data"""
    train_images, train_labels, test_images, test_labels = [], [], [], []
    
    shapes = ["circle", "square", "line"]
    for shape, label in zip(shapes, [0, 1, 2]):
        img, lbl = load_images_from_directory(f"train/{shape}", label)
        train_images.extend(img)
        train_labels.extend(lbl)
        
        img, lbl = load_images_from_directory(f"test/{shape}", label)
        test_images.extend(img)
        test_labels.extend(lbl)
    
    return train_images, train_labels, test_images, test_labels

def print_confusion_matrix(confusion_matrix, class_labels):
    """Print a formatted confusion matrix"""
    print("\n" + "="*60)
    print("CONFUSION MATRIX")
    print("="*60)
    
    # Print header
    print("\n" + " " * 12 + " ".join(f"{label:^12}" for label in class_labels))
    print(" " * 12 + "-" * (12 * len(class_labels)))
    
    # Print matrix rows
    for i, row in enumerate(confusion_matrix):
        actual_label = f"{class_labels[i]:<10}"
        row_values = " ".join(f"{value:^12}" for value in row)
        print(f"{actual_label} | {row_values}")
    
    print("\n" + "="*60)
    
    # Calculate per-class metrics
    print("\nPER-CLASS METRICS:")
    print("-" * 60)
    for i, label in enumerate(class_labels):
        true_positives = confusion_matrix[i][i]
        false_positives = sum(confusion_matrix[j][i] for j in range(len(class_labels)) if j != i)
        false_negatives = sum(confusion_matrix[i][j] for j in range(len(class_labels)) if j != i)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        print(f"{label:8} - Precision: {precision:.2%} | Recall: {recall:.2%} | F1: {f1:.2%}")
    
    print("="*60)


if __name__ == "__main__":
    print("Generating dataset...")
    generate_and_save_data(num_samples=200, size=12)
    
    print("\nLoading data...")
    input_size = 144  # 12x12 image
    train_data, train_labels, test_data, test_labels = load_all_data()
    
    print(f"Training samples: {len(train_data)}")
    print(f"Test samples: {len(test_data)}")
    
    print("\nTraining perceptron...")
    perceptron = Perceptron(input_size, num_classes=3, learning_rate=0.01, l2_lambda=0.001)
    perceptron.train(train_data, train_labels, epochs=20, verbose=True)
    
    print("\n" + "="*60)
    print("EVALUATING ON TEST SET")
    print("="*60)
    
    # Calculate accuracy
    correct_predictions = sum(1 for inputs, label in zip(test_data, test_labels) 
                            if perceptron.predict(inputs) == label)
    accuracy = correct_predictions / len(test_labels) * 100
    print(f"\nTest Accuracy: {accuracy:.2f}%")
    
    # Build confusion matrix
    num_classes = 3
    confusion_matrix = [[0] * num_classes for _ in range(num_classes)]
    
    for inputs, true_label in zip(test_data, test_labels):
        predicted_label = perceptron.predict(inputs)
        confusion_matrix[true_label][predicted_label] += 1
    
    # Print detailed results
    class_labels = ["Circle", "Square", "Line"]
    print_confusion_matrix(confusion_matrix, class_labels)
