

### Activation Function

*Explanation:* A function that determines the output of a neuron or node in a neural network. It introduces
non-linearity into the network, allowing it to learn complex patterns. Common activation functions include
ReLU, sigmoid, and tanh.

*Example:* In a hidden layer, after computing the weighted sum of inputs ($z = \sum w_i x_i + b$), an activation
function $a(z)$ is applied to produce the neuron's output. For instance, if using ReLU, $a(z) = \max(0, z)$.

*Reference:* Neural network architectures, deep learning fundamentals.


### Autoencoder

*Explanation:* An unsupervised neural network that aims to learn a compressed, low-dimensional representation
(encoding) of its input data. It consists of an encoder that maps the input to the latent space, and a decoder
that reconstructs the input from this latent representation.

*Example:* An autoencoder can be used for dimensionality reduction by training it to reconstruct images. The
bottleneck layer (latent space) will contain a compressed representation of the original image.

*Reference:* Unsupervised learning, dimensionality reduction.


### Backpropagation

*Explanation:* An algorithm used to train artificial neural networks by calculating the gradient of the loss
function with respect to the weights and biases. It propagates the error backward through the network, allowing
for iterative adjustment of parameters.

*Example:* During training, after a forward pass computes the network's output and the loss, backpropagation
calculates how much each weight and bias contributed to the error. This information is then used by an optimisation
algorithm (like gradient descent) to update the parameters.

*Reference:* Neural network training, gradient descent.


### Batch Normalization

*Explanation:* A technique that normalises the inputs of each layer in a neural network, usually before the activation
function. It aims to stabilise and accelerate the training process by reducing internal covariate shift and allowing
for higher learning rates.

*Example:* After a linear transformation $y = Wx + b$, batch normalisation would transform $y$ to $\hat{y}$ by
subtracting the mini-batch mean and dividing by the mini-batch standard deviation, scaled by learned parameters
$\gamma$ and $\beta$.

*Reference:* Deep learning optimisation, neural network regularisation.


### Bias (Machine Learning)

*Explanation:* In machine learning, bias refers to the simplifying assumptions made by a model to make the target
function easier to learn. High bias can lead to underfitting, where the model is too simple to capture the ground
truth.

*Example:* A linear regression model applied to non-linear data will exhibit high bias because it assumes a linear
relationship, leading to poor performance.

*Reference:* Bias-variance trade-off, model complexity.


### Convolutional Neural Network (CNN)

*Explanation:* A type of neural network specifically designed for processing structured grid-like data, such as images.
CNNs employ convolutional layers that apply filters to input data, pooling layers for dimensionality reduction, and
fully connected layers for classification.

*Example:* In image recognition, a CNN might use a convolutional layer to detect edges, followed by another to detect
textures, and then a pooling layer to reduce the spatial dimensions of the feature maps before passing them to a fully
connected layer for object classification.

*Reference:* Computer vision, deep learning architectures.


### Cross-Entropy Loss

*Explanation:* A commonly used loss function in classification tasks, particularly with models that output probabilities
(like neural networks with a softmax activation in the output layer). It measures the dissimilarity between the predicted
probability distribution and the true distribution.

*Example:* For a binary classification problem, if the true label is 1 and the model predicts a probability of 0.8, the
binary cross-entropy loss would be calculated as $-[1 \cdot \log(0.8) + (1-1) \log(1-0.8)] = -\log(0.8)$.

*Reference:* Loss functions, classification tasks.


### Dataset

*Explanation:* A collection of related data, typically organised in a structured format, used for training, validating,
and testing machine learning models. Datasets can consist of various data types, including images, text, audio, and
numerical data.

*Example:* The MNIST dataset consists of thousands of grayscale images of handwritten digits, along with their corresponding
labels, used for training digit recognition models.

*Reference:* Machine learning fundamentals, data science.


### Deep Learning

*Explanation:* A subfield of machine learning that uses artificial neural networks with multiple layers (deep neural networks)
to learn complex patterns from data. It has achieved significant success in areas like image recognition, natural language
processing, and speech recognition.

*Example:* Training a neural network with 10 hidden layers to classify images is an example of deep learning.

*Reference:* Artificial intelligence, neural networks.


### Epoch

*Explanation:* One complete pass through the entire training dataset during the training of a machine learning model. During
an epoch, the model processes all training examples, performs forward and backward passes, and updates its parameters.

*Example:* If a training dataset has 1000 examples and the batch size is 100, one epoch would consist of 10 updates (1000 / 100).

*Reference:* Neural network training, optimisation.


### Feature Engineering

*Explanation:* The process of selecting, transforming, and creating new features (variables) from raw data to improve the
performance of a machine learning model. It often involves domain expertise and creativity to extract meaningful information.

*Example:* From a dataset of timestamps, creating new features like "day of the week," "hour of the day," or "is_weekend" can
be a form of feature engineering for a time-series prediction model.

*Reference:* Data preprocessing, machine learning workflows.


### Feedforward Neural Network (FNN)

*Explanation:* The simplest type of artificial neural network where connections between nodes do not form a cycle. Information
flows only in one direction, from the input layer, through any hidden layers, to the output layer.

*Example:* A multi-layer perceptron (MLP) used for classification where information moves from input pixels to hidden layers
and finally to an output layer representing class probabilities is a feedforward network.

*Reference:* Neural network architectures, supervised learning.


### Gradient Descent

*Explanation:* An iterative optimisation algorithm used to minimise a function (e.g., a loss function) by iteratively moving
in the direction of the steepest descent of the function. It's a fundamental algorithm for training many machine learning models.

*Example:* To train a linear regression model, gradient descent would iteratively adjust the slope and intercept parameters by
taking small steps in the direction opposite to the gradient of the mean squared error.

*Reference:* Optimisation algorithms, machine learning training.


### Hyperparameters

*Explanation:* Parameters whose values are set before the training process of a machine learning model begins. They are not
learned from the data during training and often control the learning process itself.

*Example:* The learning rate, the number of hidden layers, the number of neurons in each layer, and the batch size are all
examples of hyperparameters in a neural network.

*Reference:* Model tuning, machine learning best practices.


### Hyperplane

*Explanation:* In a machine learning context, particularly for classification problems, a hyperplane serves as a decision
boundary. Its purpose is to divide the space where your data points exist, separating them into different categories or
classes. If your data can be visualised in two dimensions (like a scatter plot), the hyperplane is a simple line. For data
in three dimensions, it becomes a flat plane. In situations with more than three dimensions (which are common in real-world
datasets but hard for us to visualise), it remains a "hyperplane"--a flat, high-dimensional boundary that effectively splits
the data into distinct regions for classification.

*Example:* Imagine you have data points representing whether a customer will buy a product (one class) or not (another class),
based on two features like their age and income. If you plot these customers on a graph, a machine learning model might discover
a line (the hyperplane) that best separates the "will buy" customers from the "will not buy" customers. When a new customer's
age and income are entered, their position relative to this line determines the prediction of whether they will buy or not.

*Reference:* Classification, decision boundary, feature space, linear models.


### K-Means Clustering

*Explanation:* An unsupervised learning algorithm used for partitioning a dataset into $K$ distinct, non-overlapping clusters.
It iteratively assigns data points to the nearest centroid and then updates the centroids to be the mean of the points
assigned to that cluster.

*Example:* Grouping customer data into $K$ segments based on their purchasing behaviour could be achieved using K-Means clustering.

*Reference:* Unsupervised learning, clustering algorithms.


### L1 Regularisation (Lasso)

*Explanation:* A regularisation technique that adds a penalty to the loss function proportional to the absolute value of the
model's coefficients. It encourages sparsity in the model by driving some coefficients exactly to zero, effectively performing
feature selection.

*Example:* In linear regression, adding an L1 penalty to the mean squared error can lead to a model where some features are
completely ignored because their corresponding weights become zero.

*Reference:* Regularisation techniques, model complexity.


### L2 Regularisation (Ridge)

*Explanation:* A regularisation technique that adds a penalty to the loss function proportional to the square of the magnitude
of the model's coefficients. It discourages large weights, preventing overfitting and leading to smoother models.

*Example:* In linear regression, adding an L2 penalty to the mean squared error will shrink the coefficients towards zero,
reducing the impact of individual features.

*Reference:* Regularisation techniques, overfitting.


### Latent Space

*Explanation:* A lower-dimensional, abstract representation of data that captures its essential characteristics. In machine
learning, especially with generative models like autoencoders or GANs, the model learns to map high-dimensional data into
this compressed space.

*Example:* In a variational autoencoder (VAE), the latent space represents a compressed, continuous distribution from which
new data points can be sampled and decoded to generate novel outputs similar to the training data.

*Reference:* Dimensionality reduction, generative models.


### Learning Rate

*Explanation:* A hyperparameter in optimisation algorithms that determines the step size at each iteration while moving
towards the minimum of a loss function. A small learning rate can lead to slow convergence, while a large learning rate
can cause the algorithm to overshoot the minimum.

*Example:* If the gradient of the loss function with respect to a weight is 0.1 and the learning rate is 0.01, the weight
will be updated by $-0.01 \times 0.1 = -0.001$.

*Reference:* Optimisation algorithms, neural network training.


### Long Short-Term Memory (LSTM)

*Explanation:* A type of recurrent neural network (RNN) specifically designed to overcome the vanishing gradient problem
and learn long-term dependencies in sequential data. LSTMs use "gates" (input, forget, output) to control the flow of
information into and out of their memory cells.

*Example:* An LSTM network can be used for predicting the next word in a sentence, where the context of words seen much
earlier in the sentence needs to be remembered.

*Reference:* Recurrent neural networks, sequence modelling.


### Loss Function (Cost Function)

*Explanation:* A function that quantifies the discrepancy between the predicted output of a machine learning model and
the true target values. The goal of training is to minimise this loss function.

*Example:* Mean Squared Error (MSE) is a common loss function for regression tasks, calculated as the average of the
squared differences between predicted and actual values.

*Reference:* Model evaluation, optimisation.


### Machine Learning

*Explanation:* A subfield of artificial intelligence that enables systems to learn from data without being explicitly
programmed. It involves developing algorithms that can identify patterns, make predictions, and adapt their behaviour
based on experience.

*Example:* Training a spam filter to classify emails as "spam" or "not spam" based on a dataset of labeled emails is
a classic example of machine learning.

*Reference:* Artificial intelligence, data science.


### Mean Squared Error (MSE)

*Explanation:* A common metric and loss function used in regression problems. It calculates the average of the squared
differences between predicted values and actual values.

*Example:* If a model predicts temperatures of [20, 22] and the actual temperatures are [19, 21], the MSE would be
$((20-19)^2 + (22-21)^2) / 2 = (1^2 + 1^2) / 2 = 1$.

*Reference:* Regression analysis, loss functions.


### Model (Machine Learning)

*Explanation:* A representation of a system that has learned patterns and relationships from data. It can be used to
make predictions or decisions on new, unseen data.

*Example:* A trained neural network that can classify images of cats and dogs is a machine learning model.

*Reference:* Machine learning fundamentals, predictive modelling.


### Natural Language Processing (NLP)

*Explanation:* A subfield of artificial intelligence that focuses on the interaction between computers and human
language. NLP aims to enable computers to understand, interpret, and generate human language.

*Example:* Sentiment analysis, where a model determines the emotional tone of a piece of text, is a common application of NLP.

*Reference:* Artificial intelligence, computational linguistics.


### Neural Network

*Explanation:* A computational model inspired by the structure and function of biological neural networks. It consists
of interconnected nodes (neurons) organised in layers, that process information and learn from data.

*Example:* A neural network can be trained to recognise handwritten digits by learning the patterns in pixel data.

*Reference:* Deep learning, artificial intelligence.


### Overfitting

*Explanation:* A phenomenon where a machine learning model learns the training data too well, including its noise and outliers,
leading to poor generalisation performance on unseen data. The model essentially memorises the training data rather than
learning underlying patterns.

*Example:* A decision tree that is allowed to grow to its full depth on a training set might perfectly classify all training
examples but perform poorly on new data due to overfitting.

*Reference:* Model generalisation, regularisation.


### Optimisation Algorithm

*Explanation:* An algorithm used to minimise or maximise an objective function (e.g., a loss function) by iteratively adjusting
the parameters of a model. Examples include Gradient Descent, Adam, and RMSprop.

*Example:* Adam optimiser is commonly used in deep learning to efficiently update the weights of a neural network by combining
the benefits of AdaGrad and RMSprop.

*Reference:* Machine learning training, calculus.


### Parameter (Model Parameter)

*Explanation:* Internal variables of a machine learning model whose values are learned from the training data. These parameters
define the model's behaviour and enable it to make predictions.

*Example:* In a linear regression model $y = mx + b$, $m$ (slope) and $b$ (intercept) are the parameters that the model learns
during training.

*Reference:* Model training, machine learning fundamentals.


### Perceptron

*Explanation:* The simplest form of an artificial neural network, consisting of a single neuron. It's a linear classifier that
takes multiple binary inputs and produces a single binary output.

*Example:* A perceptron can be trained to classify emails as "spam" or "not spam" based on a set of binary features like
"contains_links" or "has_suspicious_keywords".

*Reference:* Neural network history, linear classification.


### Pooling Layer

*Explanation:* A layer in a convolutional neural network (CNN) that reduces the spatial dimensions (width and height) of the
input feature maps. It helps to reduce the number of parameters and computations, and provides translational invariance. Common
types include max pooling and average pooling.

*Example:* A max pooling layer with a $2 \times 2$ filter and stride 2 would take the maximum value from each $2 \times 2$ region
of the input feature map, effectively halving its width and height.

*Reference:* Convolutional neural networks, dimensionality reduction.


### Precision

*Explanation:* In classification, precision is the ratio of correctly predicted positive observations to the total predicted
positive observations. It answers the question: "Of all the instances I predicted as positive, how many were actually positive?"

*Example:* If a model predicts 10 emails as spam, and only 7 of them are actually spam, the precision is $7/10 = 0.7$.

*Reference:* Classification metrics, model evaluation.


### Recurrent Neural Network (RNN)

*Explanation:* A type of neural network designed to process sequential data by maintaining an internal "memory" that allows
information to persist across steps. RNNs are suitable for tasks like natural language processing and time series prediction.

*Example:* An RNN can be used to generate text, where the model considers the sequence of previously generated words to predict
the next word.

*Reference:* Sequence modelling, deep learning architectures.


### Regression

*Explanation:* A type of supervised learning task that aims to predict a continuous numerical output value based on input features.

*Example:* Predicting the price of a house based on its size, number of bedrooms, and location is a regression problem.

*Reference:* Supervised learning, statistical modelling.


### Regularisation

*Explanation:* Techniques used to prevent overfitting in machine learning models by adding a penalty to the loss function or
by constraining the model's complexity.

*Example:* Dropout is a regularisation technique where randomly selected neurons are ignored during training, forcing the
network to learn more robust features.

*Reference:* Overfitting, model generalisation.


### ReLU (Rectified Linear Unit)

*Explanation:* An activation function commonly used in neural networks. It outputs the input directly if it is positive,
and zero otherwise. It helps to overcome the vanishing gradient problem and speeds up training.

*Example:* If the input to a ReLU function is -2, the output is 0. If the input is 5, the output is 5.

*Reference:* Activation functions, deep learning.


### Reinforcement Learning

*Explanation:* A type of machine learning where an agent learns to make decisions by interacting with an environment.
The agent receives rewards for desirable actions and penalties for undesirable ones, aiming to maximise cumulative reward.

*Example:* Training an AI to play chess by rewarding it for winning games and penalising it for losing is an example of
reinforcement learning.

*Reference:* Artificial intelligence, control theory.


### Root Mean Squared Error (RMSE)

*Explanation:* The square root of the Mean Squared Error (MSE). It is a common metric used in regression problems and
represents the standard deviation of the residuals (prediction errors).

*Example:* If the MSE of a regression model is 9, the RMSE would be $\sqrt{9} = 3$. This means, on average, the predictions
are 3 units away from the actual values.

*Reference:* Regression analysis, loss functions.


### Sigmoid Function

*Explanation:* An activation function that squashes input values into a range between 0 and 1. It is often used in the
output layer of binary classification neural networks to produce probabilities.

*Example:* Given an input $x$, the sigmoid function is $f(x) = 1 / (1 + e^{-x})$. If $x=0$, $f(x)=0.5$. As $x$ approaches
infinity, $f(x)$ approaches 1, and as $x$ approaches negative infinity, $f(x)$ approaches 0.

*Reference:* Activation functions, neural networks.


### Softmax Function

*Explanation:* An activation function typically used in the output layer of a multi-class classification neural network.
It converts a vector of arbitrary real values into a probability distribution, where each value is between 0 and 1 and
the sum of all values is 1.

*Example:* If a neural network outputs scores [2.0, 1.0, 0.1] for three classes, the softmax function would convert these
scores into probabilities like [0.7, 0.2, 0.1] respectively, summing to 1.

*Reference:* Activation functions, multi-class classification.


### Stochastic Gradient Descent (SGD)

*Explanation:* A variant of the gradient descent optimisation algorithm where the model's parameters are updated for each
training example (or a small mini-batch) rather than after calculating the gradient over the entire dataset. This introduces
more noise but can lead to faster convergence.

*Example:* Instead of calculating the average gradient across all 10,000 training images, SGD might update the weights after
processing each individual image (or a batch of 32 images).

*Reference:* Optimisation algorithms, neural network training.


### Supervised Learning

*Explanation:* A type of machine learning where the model learns from a labeled dataset, meaning each input example is paired
with its corresponding correct output. The goal is to learn a mapping from inputs to outputs to make predictions on new, unseen data.

*Example:* Training a model to classify images of animals (cats, dogs, birds) by providing it with images and their correct
labels is an example of supervised learning.

*Reference:* Machine learning paradigms, classification and regression.


### Support Vector Machine (SVM)

*Explanation:* A supervised learning algorithm used for classification and regression tasks. SVMs work by finding an optimal
hyperplane that best separates data points into different classes with the largest possible margin.

*Example:* An SVM can be used to classify emails as "spam" or "not spam" by finding the optimal hyperplane that separates the
spam emails from the legitimate ones in a high-dimensional feature space.

*Reference:* Classification algorithms, machine learning.


### Tensor

*Explanation:* A multi-dimensional array, a generalisation of vectors and matrices. In machine learning, particularly deep
learning, data is typically represented as tensors.

*Example:* A grayscale image can be represented as a 2D tensor (matrix), a color image as a 3D tensor
(height x width x color channels), and a batch of color images as a 4D tensor (batch size x height x width x color channels).

*Reference:* Deep learning frameworks, linear algebra.


### Tensor Processing Unit (TPU)

*Explanation:* An application-specific integrated circuit (ASIC) developed by Google specifically for accelerating machine
learning workloads, particularly for neural network training and inference.

*Example:* Training a large-scale deep learning model on Google Cloud Platform might leverage TPUs for significantly faster
computation compared to traditional CPUs or GPUs.

*Reference:* Deep learning hardware, cloud computing.


### Training Data

*Explanation:* The portion of a dataset used to train a machine learning model. The model learns patterns and relationships
from this data to build its internal representation.

*Example:* In a sentiment analysis task, a large collection of movie reviews, each labeled as "positive" or "negative," would
serve as the training data.

*Reference:* Machine learning workflow, data splitting.


### Transfer Learning

*Explanation:* A machine learning technique where a model trained on one task is re-purposed or fine-tuned for a second,
related task. It leverages pre-trained models to reduce training time and improve performance, especially with limited data.

*Example:* Taking a pre-trained CNN model that was trained on a vast image dataset (like ImageNet) and fine-tuning its last
layers for a specific task like classifying medical images.

*Reference:* Deep learning techniques, model reusability.


### Underfitting

*Explanation:* A phenomenon where a machine learning model is too simple to capture the underlying patterns in the training
data, leading to poor performance on both training and unseen data. It often results from high bias.

*Example:* Trying to fit a linear regression model to data that clearly shows a quadratic relationship would result in underfitting.

*Reference:* Bias-variance trade-off, model complexity.


### Unsupervised Learning

*Explanation:* A type of machine learning where the model learns from unlabeled data, without explicit output guidance. The
goal is to discover hidden patterns, structures, or relationships within the data.

*Example:* Using clustering algorithms like K-Means to group similar documents in a large text corpus without any prior labels
is an example of unsupervised learning.

*Reference:* Machine learning paradigms, data exploration.


### Validation Data

*Explanation:* The portion of a dataset used to evaluate the performance of a machine learning model during the training phase
and to tune hyperparameters. It helps to monitor for overfitting and provides an unbiased estimate of the model's performance
on unseen data.

*Example:* After each epoch of training, the model's accuracy on the validation data is checked to determine if training should
continue or if hyperparameters need adjustment.

*Reference:* Machine learning workflow, model evaluation.


### Vanishing Gradient Problem

*Explanation:* A challenge in training deep neural networks, particularly recurrent neural networks, where the gradients of the
loss function with respect to the weights in earlier layers become extremely small during backpropagation. This makes it difficult
for the network to learn long-term dependencies.

*Example:* In a deep RNN processing a long sentence, the influence of words at the beginning of the sentence might be "forgotten"
by the time the gradient signal propagates back to the initial layers due to vanishing gradients.

*Reference:* Deep learning challenges, recurrent neural networks.


### Variance (Machine Learning)

*Explanation:* In machine learning, variance refers to the model's sensitivity to small fluctuations or noise in the training data.
High variance can lead to overfitting, where the model performs well on training data but poorly on unseen data.

*Example:* A very complex decision tree with many branches might have high variance, as it can learn the noise in the training
data, making it less generalisable.

*Reference:* Bias-variance trade-off, model complexity.


### Word Embedding

*Explanation:* A dense vector representation of words in a continuous vector space. Words with similar meanings or contexts are
mapped to similar vector representations, capturing semantic relationships.

*Example:* The word embeddings for "king" and "queen" would be closer in the vector space than "king" and "apple," reflecting their
semantic similarity. Word2Vec and GloVe are popular word embedding techniques.

*Reference:* Natural language processing, distributed representations.


## References

- Burkov, A. (2019[2019]). *The hundred-page machine learning book*. [Quebec City, Canada]: Andriy Burkov.

- Goodfellow, I., Bengio, Y. and Courville, A., 2016. *Deep Learning*. MIT Press.
