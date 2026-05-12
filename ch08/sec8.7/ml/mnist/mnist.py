import struct
import math
import random

# read MNIST dataset
def load_mnist_images(filename):
    with open(filename, 'rb') as f:
        magic, num_images, rows, cols = struct.unpack(">IIII", f.read(16))
        assert magic == 2051, "Invalid magic number in MNIST image file!"
        data = f.read()
        return [[pixel / 255.0 for pixel in data[i * rows * cols:(i + 1) * rows * cols]] for i in range(num_images)]

def load_mnist_labels(filename):
    with open(filename, 'rb') as f:
        magic, num_labels = struct.unpack(">II", f.read(8))
        assert magic == 2049, "Invalid magic number in MNIST label file!"
        return list(f.read(num_labels))

# load dataset
train_images = load_mnist_images("train-images.idx3-ubyte")
train_labels = load_mnist_labels("train-labels.idx1-ubyte")
test_images = load_mnist_images("t10k-images.idx3-ubyte")
test_labels = load_mnist_labels("t10k-labels.idx1-ubyte")

# Neural Network parameters
INPUT_SIZE = 28 * 28
HIDDEN_SIZE = 64
OUTPUT_SIZE = 10
LEARNING_RATE = 0.1
EPOCHS = 5

# init weights and biases
def init_weights(rows, cols):
    return [[random.uniform(-0.1, 0.1) for _ in range(cols)] for _ in range(rows)]

weights_input_hidden = init_weights(INPUT_SIZE, HIDDEN_SIZE)
weights_hidden_output = init_weights(HIDDEN_SIZE, OUTPUT_SIZE)
bias_hidden = [0.0] * HIDDEN_SIZE
bias_output = [0.0] * OUTPUT_SIZE

# activation
def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def softmax(vector):
    exp_values = [math.exp(v) for v in vector]
    total = sum(exp_values)
    return [v / total for v in exp_values]

# forward pass
def forward(image):
    hidden_input = [sum(image[i] * weights_input_hidden[i][j] for i in range(INPUT_SIZE)) + bias_hidden[j] for j in range(HIDDEN_SIZE)]
    hidden_output = [sigmoid(x) for x in hidden_input]
    
    final_input = [sum(hidden_output[i] * weights_hidden_output[i][j] for i in range(HIDDEN_SIZE)) + bias_output[j] for j in range(OUTPUT_SIZE)]
    final_output = softmax(final_input)
    return hidden_output, final_output

def backprop(image, label):
    global weights_input_hidden, weights_hidden_output, bias_hidden, bias_output
    hidden_output, final_output = forward(image)
    
    # one-hot encode label
    target = [1.0 if i == label else 0.0 for i in range(OUTPUT_SIZE)]
    
    # output layer error
    output_error = [final_output[i] - target[i] for i in range(OUTPUT_SIZE)]
    
    # hidden layer error
    hidden_error = [
        sum(weights_hidden_output[i][j] * output_error[j] for j in range(OUTPUT_SIZE)) * hidden_output[i] * (1 - hidden_output[i])
        for i in range(HIDDEN_SIZE)
    ]
    
    # update weights and biases (gradient descent)
    for i in range(HIDDEN_SIZE):
        for j in range(OUTPUT_SIZE):
            weights_hidden_output[i][j] -= LEARNING_RATE * output_error[j] * hidden_output[i]
    for j in range(OUTPUT_SIZE):
        bias_output[j] -= LEARNING_RATE * output_error[j]
    
    for i in range(INPUT_SIZE):
        for j in range(HIDDEN_SIZE):
            weights_input_hidden[i][j] -= LEARNING_RATE * hidden_error[j] * image[i]
    for j in range(HIDDEN_SIZE):
        bias_hidden[j] -= LEARNING_RATE * hidden_error[j]

# training
print("Training...")
for epoch in range(EPOCHS):
    for img, lbl in zip(train_images, train_labels):
        backprop(img, lbl)
    print(f"Epoch {epoch + 1}/{EPOCHS} completed.")

# testing
print("Testing...")
correct = sum(1 for img, lbl in zip(test_images, test_labels) if lbl == forward(img)[1].index(max(forward(img)[1])))
accuracy = correct / len(test_labels) * 100
print(f"Accuracy: {accuracy:.2f}%")
