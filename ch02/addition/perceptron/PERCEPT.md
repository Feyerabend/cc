
## The Perceptron

The perceptron is one of the earliest machine learning models, originally introduced
by Frank Rosenblatt in 1958. It was designed as a simplified model of how neurons in
the brain process information. The perceptron is a type of binary classifier, meaning
it decides between two categories by applying a weighted sum to inputs and passing the
result through an activation function (usually a step function).

While the original perceptron could only solve linearly separable problems, it laid
the foundation for modern neural networks. The introduction of the multi-layer perceptron
(MLP) and backpropagation in the 1980s allowed for more complex decision boundaries,
leading to deep learning as we know it today.


### Overview

The program 'percept.py' program builds a simple multi-class perceptron to classify
shapes (circles, squares, and lines) from 8×8 pixel images.

The code is split into three main parts:
1. Image Generation: Creates synthetic training images of circles, squares, and lines.
2. Perceptron Model: Implements a multi-class perceptron with weight updates.
3. Training and Testing: Loads image data, trains the perceptron, and evaluates accuracy.



__1. Perceptron Model__

This is the heart of the program. The perceptron model is responsible for learning and
predicting shapes based on the pixel data.

```python
class Perceptron:
    def __init__(self, input_size, num_classes, l2_lambda=0.01):
        self.num_classes = num_classes
        self.input_size = input_size
        self.weights = [[random.uniform(-1, 1) for _ in range(input_size)] for _ in range(num_classes)]
        self.bias = [random.uniform(-1, 1) for _ in range(num_classes)]
        self.learning_rate = 0.1
        self.l2_lambda = l2_lambda  # regularisation strength
```
- input_size: Number of pixels in the input image (8×8 = 64).
- num_classes: Number of shapes (circle, square, line → 3 classes).
- self.weights: A list of weight vectors for each class, initialised randomly.
- self.bias: A separate bias term for each class.
- self.l2_lambda: L2 regularisation strength to prevent overfitting.


__2. Activation Function & Prediction__

The perceptron uses a step activation function to determine class labels.

```python
def activation(self, x):
    return 1 if x >= 0 else 0
```

This function returns 1 for positive values and 0 otherwise.

```python
def predict(self, inputs):
    scores = [sum(w * i for w, i in zip(self.weights[c], inputs)) + self.bias[c] for c in range(self.num_classes)]
    return scores.index(max(scores))
```
- Computes the score for each class using the weighted sum of inputs plus bias.
- Returns the class with the highest score (argmax).


__3. Training Algorithm__

```python
def train(self, training_data, labels, epochs):
    for _ in range(epochs):
        for inputs, label in zip(training_data, labels):
            prediction = self.predict(inputs)
            if prediction != label:
                # update weights with L2 regularisation
                for i in range(len(self.weights[label])):
                    self.weights[label][i] += self.learning_rate * (inputs[i] - self.l2_lambda * self.weights[label][i])
                    self.weights[prediction][i] -= self.learning_rate * (inputs[i] + self.l2_lambda * self.weights[prediction][i])
                # update biases
                self.bias[label] += self.learning_rate
                self.bias[prediction] -= self.learning_rate
```
1. Iterates through the dataset for multiple epochs to refine weights.
2. Makes a prediction and compares it to the correct label.
3. If wrong, updates weights:
- Increases weights of the correct class.
- Decreases weights of the wrongly predicted class.
- Uses L2 regularisation to prevent excessive weight growth.[^L2]
4. Bias updates work the same way to shift decision boundaries.

[^L2]: The effect of L2 regularization is that it discourages overly complex models by shrinking
the weights toward smaller values, making the model more robust and less sensitive to variations
in the training data. This helps improve generalization and prevents the model from memorising
training examples instead of learning meaningful patterns.

__4. Image Generation (Synthetic Training Data)__

The dataset consists of binary 8×8 images representing three shapes: circle, square, and line.


#### Generating a Circle

```python
def generate_circle_image(size=8, noise_level=0.1):
    image = [[0] * size for _ in range(size)]
    cx, cy = random.randint(size // 4, 3 * size // 4), random.randint(size // 4, 3 * size // 4)
    radius = random.randint(size // 4, size // 3)

    for x in range(size):
        for y in range(size):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                image[x][y] = 1

    add_noise(image, noise_level)
    return image
```
- Creates a blank grid (0s for black pixels).
- Picks a random center (cx, cy) and random radius.
- Fills pixels inside the circle using the equation of a circle:
    - Calls add_noise() to introduce random noise.


#### Generating a Square

```python
def generate_square_image(size=8, noise_level=0.1):
    image = [[0] * size for _ in range(size)]
    start_x, start_y = random.randint(1, size // 3), random.randint(1, size // 3)
    end_x, end_y = random.randint(2 * size // 3, size - 1), random.randint(2 * size // 3, size - 1)

    for x in range(start_x, end_x):
        for y in range(start_y, end_y):
            image[x][y] = 1

    add_noise(image, noise_level)
    return image
```
- Picks random start and end points for the square.
- Fills the bounding box with 1s to create the square.


#### Generating a Line

```python
def generate_line_image(size=8, noise_level=0.1):
    image = [[0] * size for _ in range(size)]
    slope = random.uniform(-1, 1)
    intercept = random.randint(0, size - 1)

    for x in range(size):
        y = int(slope * x + intercept)
        if 0 <= y < size:
            image[x][y] = 1

    add_noise(image, noise_level)
    return image
```
- Generates a random slope and intercept for a line equation:
    - Rounds y to the nearest pixel and sets it to 1.


#### Adding Noise

```python
def add_noise(image, noise_level=0.1):
    size = len(image)
    num_pixels = int(size * size * noise_level)

    for _ in range(num_pixels):
        x, y = random.randint(0, size - 1), random.randint(0, size - 1)
        image[x][y] = 1 if image[x][y] == 0 else 0
```
- Randomly flips a percentage of pixels to simulate noise.


__5. Training and Evaluating the Perceptron__

```python
generate_and_save_data()

input_size = 64  # 8x8 image
perceptron = Perceptron(input_size, num_classes=3)
train_data, train_labels, test_data, test_labels = load_all_data()
perceptron.train(train_data, train_labels, epochs=10)

correct_predictions = sum(1 for inputs, label in zip(test_data, test_labels) if perceptron.predict(inputs) == label)
accuracy = correct_predictions / len(test_labels) * 100
print(f"Accuracy: {accuracy:.2f}%")
```
- Generates training/testing data.
- Loads and flattens images into feature vectors.
- Trains the perceptron for 10 epochs.
- Evaluates accuracy on test data.

