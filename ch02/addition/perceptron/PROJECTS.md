
## Projects

There are several interesting projects you could explore. Here are a few that focus
on improving representation, classification accuracy, and extending the functionality.

You have to remember or keep in mind that this perceptron only distinguishes between
three types of generated images. They might not even resemble what we perceive as
circles, squares, or lines.

Threre is plently of room for improvement ..


__1. Improving Image Representations__

The current representations of circles, squares, and lines are rough and noisy, making
it difficult to determine whether they truly resemble their intended shapes. This issue
stems partly from how the figures are represented, with low resolution and other constraints
making both generation and interpretation challenging. Their clarity could be significantly
improved using the following techniques.

Project 1: Better Shape Generation
- Use anti-aliasing to make shapes smoother.
- Implement thicker lines for the line class to make them more distinct.
- Add rotated squares and ellipses to increase variation in shape generation.
- Ensure a more consistent size of objects within the 8×8 grid to prevent excessive
  variation.

Project 2: Increase Resolution
- Currently, images are only 8×8. Try generating 16×16 or 32×32 grids and downsampling
  before classification.
- Use edge detection to enhance features before flattening.
- Convert to grayscale intensity values (0-255) instead of binary pixels (0 or 1).
- Use better format for saving the images: JPEG, PNG, etc.


__2. Enhancing Classification Accuracy__

The perceptron model struggles with certain classifications.

Project 3: Feature Engineering
- Instead of raw pixels, extract features like:
- Symmetry (e.g., circles should be highly symmetric).
- Line segments (use a basic Hough Transform to detect them).
- Edge count (squares should have 4 dominant edges).

Project 4: Use a Multi-Layer Perceptron (MLP)
- The perceptron is a linear classifier, which means it struggles with overlapping classes.
- Implement a small neural network with a hidden layer and activation functions (ReLU, Sigmoid).
- Train using backpropagation instead of simple perceptron updates.

Project 5: Add More Classes
- Introduce triangles, crosses, or hollow circles to make the dataset more interesting.
- Use hierarchical classification (first classify into "curved" vs "angular" shapes
  before classifying the exact shape).


__3. Expanding the Application__

Your current project is a simple classifier, but it can be extended in several ways.

Project 6: Shape Recognition in Hand-Drawn Images
- Allow users to draw shapes (on a canvas or using ASCII input).
- Preprocess the drawing to fit into an 8×8 or 16×16 grid.
- Train the perceptron to classify hand-drawn circles, squares, and lines.

Project 7: Convert to an Embedded System
- Implement this classifier in an Raspberry Pi Pico, Arduino or ESP32, using a small
  OLED display to show predictions.
- Use a camera module to classify real-world shapes.

Project 8: Evolutionary Perceptron
- Instead of using a manually tuned perceptron, use genetic algorithms to evolve the best weights.
- Train multiple perceptrons in parallel and select the best performers for crossover and mutation.
