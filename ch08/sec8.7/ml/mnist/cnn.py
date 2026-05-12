import struct
import math
import random

def load_mnist_images(filename):
    with open(filename, 'rb') as f:
        magic, num_images, rows, cols = struct.unpack(">IIII", f.read(16))
        assert magic == 2051, "Invalid magic number in MNIST image file!"
        data = list(f.read())

        # reshape each image into a 28 x 28 matrix
        images = [[
            [pixel / 255.0 for pixel in data[i * rows * cols + j * cols:(i * rows * cols) + (j + 1) * cols]]
            for j in range(rows)
        ] for i in range(num_images)]

        return images, rows, cols

def load_mnist_labels(filename):
    with open(filename, 'rb') as f:
        magic, num_labels = struct.unpack(">II", f.read(8))
        assert magic == 2049, "Invalid magic number in MNIST label file!"
        return list(f.read(num_labels))

# load dataset
train_images, IMG_ROWS, IMG_COLS = load_mnist_images("train-images.idx3-ubyte")
train_labels = load_mnist_labels("train-labels.idx1-ubyte")
test_images, _, _ = load_mnist_images("t10k-images.idx3-ubyte")
test_labels = load_mnist_labels("t10k-labels.idx1-ubyte")

# CNN parameters ~ hyperparameters you can tune!
FILTER_SIZE = 3
NUM_FILTERS = 8
POOL_SIZE = 2
HIDDEN_SIZE = 64
OUTPUT_SIZE = 10
LEARNING_RATE = 0.1
EPOCHS = 5

# init random filters
filters = [[[random.uniform(-0.1, 0.1) for _ in range(FILTER_SIZE)] for _ in range(FILTER_SIZE)] for _ in range(NUM_FILTERS)]

# fully connected layer weights
weights_hidden_output = [[random.uniform(-0.1, 0.1) for _ in range(OUTPUT_SIZE)] for _ in range(HIDDEN_SIZE)]
bias_output = [0.0] * OUTPUT_SIZE

# activation functions and softmax
def relu(x):
    return max(0, x)

def softmax(vector):
    exp_values = [math.exp(v) for v in vector]
    total = sum(exp_values)
    return [v / total for v in exp_values]

# convolution operation
def convolve(image, filter):
    img_size = len(image)
    output_size = img_size - FILTER_SIZE + 1
    output = [[0] * output_size for _ in range(output_size)]
    
    for i in range(output_size):
        for j in range(output_size):
            output[i][j] = sum(image[i+x][j+y] * filter[x][y] for x in range(FILTER_SIZE) for y in range(FILTER_SIZE))
    
    return output

def max_pool(image):
    img_size = len(image)
    output_size = img_size // POOL_SIZE
    output = [[0] * output_size for _ in range(output_size)]
    for i in range(output_size):
        for j in range(output_size):
            output[i][j] = max(image[i * POOL_SIZE + x][j * POOL_SIZE + y] for x in range(POOL_SIZE) for y in range(POOL_SIZE))
    return output

def forward(image):
    # ensure image is correctly shaped  (28x28)
    if len(image) != IMG_ROWS or len(image[0]) != IMG_COLS:
        raise ValueError(f"Image shape mismatch: Expected {IMG_ROWS}x{IMG_COLS}, got {len(image)}x{len(image[0])}")

    # convolution, ReLU, and Pooling layers
    conv_outputs = [convolve(image, f) for f in filters]
    relu_outputs = [[list(map(relu, row)) for row in conv] for conv in conv_outputs]
    pooled_outputs = [max_pool(conv) for conv in relu_outputs]

    # flatten to fully connected layer input
    flattened = [val for pool in pooled_outputs for row in pool for val in row]

    # fully connected layer and softmax
    final_input = [sum(flattened[i] * weights_hidden_output[i][j] for i in range(HIDDEN_SIZE)) + bias_output[j] for j in range(OUTPUT_SIZE)]
    final_output = softmax(final_input)
    return flattened, final_output

# training with backprop
def backprop(image, label):
    global weights_hidden_output, bias_output, filters

    flattened, final_output = forward(image)

    # one-hot encode label for target output
    target = [1.0 if i == label else 0.0 for i in range(OUTPUT_SIZE)]
    
    # output layer error (cross-entropy loss)
    output_error = [final_output[i] - target[i] for i in range(OUTPUT_SIZE)]
    
    # update weights and biases
    for i in range(HIDDEN_SIZE):
        for j in range(OUTPUT_SIZE):
            weights_hidden_output[i][j] -= LEARNING_RATE * output_error[j] * flattened[i]
    for j in range(OUTPUT_SIZE):
        bias_output[j] -= LEARNING_RATE * output_error[j]


print("Training CNN ..")
for epoch in range(EPOCHS):
    for img, lbl in zip(train_images, train_labels):
        try:
            backprop(img, lbl)
        except Exception as e:
            print(f"Error processing image with label {lbl}: {e}")
    print(f"Epoch {epoch + 1}/{EPOCHS} completed.")

# init matrix
confusion_matrix = [[0] * OUTPUT_SIZE for _ in range(OUTPUT_SIZE)]


print("Testing CNN ..")
correct = 0
total = len(test_labels)

for img, lbl in zip(test_images, test_labels):
    predicted_label = forward(img)[1].index(max(forward(img)[1]))
    confusion_matrix[lbl][predicted_label] += 1  # increment for confusion matrix
    if lbl == predicted_label:
        correct += 1

accuracy = correct / total * 100
print(f"Accuracy: {accuracy:.2f}%")


print("\nConfusion Matrix:")
header = "   " + " ".join(f"{i:5}" for i in range(OUTPUT_SIZE))
print(header)
for i in range(OUTPUT_SIZE):
    row = f"{i:2}: " + " ".join(f"{confusion_matrix[i][j]:5}" for j in range(OUTPUT_SIZE))
    print(row)

# ASCII bar chart
max_value = max(max(row) for row in confusion_matrix)
bar_char = "█"
max_bar_length = 50  # adjust for wider/narrower bars

# normalise function
def scale_bar(value, max_v, max_len):
    return int((value / max_v) * max_len)

print("\nConfusion Matrix as Bar Chart:\n")
for i, row in enumerate(confusion_matrix):
    total = sum(row)
    bar_length = scale_bar(total, max_value, max_bar_length)
    print(f"{i}: {bar_char * bar_length:<{max_bar_length}}  {total}")
