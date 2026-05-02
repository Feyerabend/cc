
## What is Machine Learning (ML)?

The story of machine learning (ML) in AI begins as a divergence from what is often called [GOFAI](./../gofai/)
(Good Old-Fashioned Artificial Intelligence), which dominated from the 1950s through the 1980s. GOFAI relied
on symbolic reasoning, logic, and handcrafted rules to simulate intelligent behaviour. Researchers built expert
systems and used formal languages to model human reasoning. These systems worked well in constrained domains
(like theorem proving or medical diagnosis) but struggled with uncertainty, noise, and learning from data.

By the 1980s, limitations of GOFAI became clear. Systems required enormous manual effort and lacked adaptability.
At the same time, researchers in statistics and pattern recognition—fields somewhat separate from mainstream
AI--we're exploring probabilistic methods and data-driven learning. Techniques like decision trees, nearest
neighbour methods, and early neural networks were gaining traction. These methods could learn patterns from
data without needing explicit programming of rules.

The 1990s saw a growing convergence between AI and statistical learning, sometimes called the "statistical
revolution" in AI. Developments included:
- Bayesian networks (e.g., Judea Pearl’s work),
- Support Vector Machines (SVMs),
- boosting algorithms, and
- the broader framework of probabilistic inference and optimisation.

At this point, machine learning started to dominate practical AI applications—such as speech recognition,
handwriting recognition, and web search. GOFAI faded from the center of research as its systems could not
scale or adapt as well as ML-based approaches.

The major turning point came in the 2010s, with the resurgence of neural networks under the name deep
learning, thanks to increased computational power (GPUs), large datasets, and algorithmic innovations
(like better training methods and architectures). Models like AlexNet (2012) showcased the power of deep
neural networks in tasks like image recognition, kicking off an era where learning from data replaced
rule-based reasoning as the primary method of building intelligent systems.

Today, machine learning—especially deep learning—is the dominant approach in AI. However, there is a
growing recognition that symbolic reasoning and ML might need to be integrated, leading to hybrid approaches
that combine structured knowledge and statistical learning, aiming to recapture the generality and
abstraction GOFAI once sought but with the adaptability of modern ML.


### The Concepts

So, Machine Learning (ML) is a paradigm where computers learn rules or patterns directly from data rather
than being explicitly programmed with them. Instead of providing the computer with a set of rigid if/else
statements or fixed algorithms, you supply it with *data* and *examples of the desired output for that data*.
The machine then analyses these examples to discover underlying patterns, forming a "model" that can be
used to make predictions or decisions on new, unseen data.

Think of it this way:

* *Conventional Programming.* You, the programmer, define the Rules that process Data to produce Answers.
  For instance, you might write code that specifies exactly how to calculate a tax based on income brackets.  
* *Machine Learning.* You provide Data along with the Answers (or labels) for that data, and the computer's
  algorithms work to learn the Rules (which collectively form a "model"). An example is feeding an ML
  system thousands of images of cats and dogs, each labeled correctly. The system learns to identify
  features that distinguish cats from dogs without being explicitly told "a cat has pointy ears and whiskers."

For example, to classify emails as "spam" or "not spam" in ML, you would feed an algorithm thousands of
pre-labeled emails (e.g., "This email about a 'Nigerian prince' is spam," "This email from my colleague
is not spam"). The algorithm then identifies patterns (e.g., specific word frequencies like "urgent" or
"free," sender characteristics, formatting) that differentiate spam from legitimate emails. Once trained,
this learned "model" can then predict whether a *new, unseen* email is spam or not with a certain degree
of accuracy.


### ML vs. Conventional Programming: Shifting Mindsets

The biggest shift from conventional programming to ML is the fundamental change in how solutions are developed:
the transition from explicit rules to data-driven discovery of rules.

In conventional programming, you define precise, step-by-step instructions for the computer to execute:

```python
def classify_email_conventional(email_text):  
    if "nigerian prince" in email_text.lower() and "urgent" in email_text.lower():  
        return "spam"  
    elif "free lottery" in email_text.lower() or "click here" in email_text.lower():  
        return "spam"  
    else:  
        return "not spam"
```

This approach is highly effective when the rules governing a problem are clear, finite, and easily expressible
by a human. However, ML truly excels when these rules are too complex, too numerous, constantly changing, or
even impossible for a human to articulate explicitly. For instance, how would you write if/else statements to
reliably recognise a human face in an image, accounting for different angles, lighting, and expressions?

This is where the ML mindset comes into play:

* You don't tell the machine *how* to classify spam; you show it *what* spam looks like through numerous examples.
  The machine then figures out the how.  
* You don't program the formula for recognising faces; you provide many examples of faces and non-faces. The
  machine then identifies the intricate patterns that define a face.

This paradigm shift enables the solution of problems that are otherwise intractable with traditional programming,
especially  those involving complex, nuanced patterns in large datasets, such as image recognition, natural language
processing, and personalised recommendations.



## The Language of Patterns: Mathematics in ML

Machine Learning can seem almost magical in its ability to discover complex patterns and make
predictions. However, this "magic" is firmly rooted in rigorous mathematics. You don't necessarily
need to be a math expert to use ML tools, but grasping the core concepts from these fields will
provide invaluable insight into how algorithms work, why certain techniques are used, and how
to troubleshoot and improve your models.


### Linear Algebra: The Mathematics of Data

* Concept: Linear algebra is the branch of mathematics that deals with vectors, vector spaces,
  linear equations, and matrices. In Machine Learning, data is almost universally represented
  numerically and organised into structures that align perfectly with linear algebra concepts.  
  * Vectors: A single data point (e.g., the features of one house: \[size, number of bedrooms,
    age\]) is often represented as a vector.  
  * Matrices: A collection of many data points (e.g., an entire dataset of houses, where each
    row is a house and each column is a feature) is typically represented as a matrix.  
  * Tensors: In more advanced deep learning, data might be represented as tensors, which are
    generalisations of vectors and matrices to higher dimensions (e.g., an image being a 3D
    tensor: height x width x colour channels).  

* Why it's used: Linear algebra provides the essential tools for efficient manipulation,
  transformation, and processing of these numerical data structures.  
  * Feature Scaling: Operations to normalise or standardise data often involve vector/matrix
    operations.  
  * Dimensionality Reduction: Techniques like Principal Component Analysis (PCA) rely heavily
    on eigenvalue decomposition, a core linear algebra concept, to reduce the number of features
    while retaining important information.  
  * Neural Networks: The fundamental operation within a neural network layer is a matrix
    multiplication, where input features are multiplied by a matrix of weights (parameters)
    and summed to produce an output. Many ML models are fundamentally sophisticated linear
    equations or compositions of them.  
  * Data Transformation: Many data preparation steps, such as one-hot encoding or creating
    polynomial features, result in new matrices that are processed using linear algebra.  

* *Programmer's view:* If you've ever used libraries for numerical computation like NumPy in Python,
  you are already interacting with linear algebra concepts daily, even if you're not explicitly
  thinking of them in mathematical terms. Functions like `np.dot()` (dot product), `np.linalg.inv()`
  (matrix inverse), or `np.transpose()` are direct implementations of linear algebraic operations.
  Understanding these operations allows you to write more efficient and correct ML code.


### Calculus (especially Derivatives): The Engine of Optimisation

* Concept: Calculus is the mathematical study of continuous change. It's divided into differential
  calculus (dealing with rates of change and slopes) and integral calculus (dealing with accumulation).
  In the context of ML, differential calculus is paramount, primarily used for optimisation—that is,
  finding the "best" set of parameters that make our model as accurate as possible.  
    * Loss Functions in Machine Learning: In machine learning, every model has a loss function (or cost
      function), which quantifies how inaccurate the model's predictions are compared to the actual values.
      The primary objective of training a machine learning model is to minimise this loss.
      For linear regression, a commonly used loss function is the Mean Squared Error (MSE), defined as:
$\text{MSE} = \frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2$$
where:
$y_i$ is the actual value,
$\hat{y}_i$ is the predicted value,
$n$ is the total number of data points.

  * Optimisation: Calculus provides the tools to find the minimum point of a function.  

* Why it's used: Derivatives (from differential calculus) are central to the optimisation process.
  A derivative tells us the rate of change of a function with respect to one of its variables, and
  critically, the direction in which the function is increasing or decreasing most rapidly.  
  * Gradient Descent: This is the most common optimisation algorithm in ML. By calculating the partial
    derivative of our loss function with respect to each model parameter (e.g., $m$ and $b$ in linear
    regression), we can determine how much and in which direction to adjust those parameters to
    reduce the loss. Gradient Descent iteratively takes small steps "downhill" in the landscape
    defined by the loss function until a local minimum (the lowest point in that area) is reached.  
  * Backpropagation: In neural networks, the process of calculating gradients efficiently across
    multiple layers is called backpropagation, which is a sophisticated application of the chain
    rule from calculus.  

* *Programmer's view:* While you won't typically write derivative calculations from scratch when
  using modern ML frameworks (they use automatic differentiation), understanding *why* these calculations
  are performed is somewhat essential. You will regularly use optimisation algorithms (e.g., SGD for
  Stochastic Gradient Descent, Adam, RMSprop) that implement these calculus-based concepts under the
  hood to automatically update model parameters based on the calculated gradients, pushing the model
  towards better performance.


### Probability and Statistics: The Foundation of Inference and Uncertainty

* Concept:  
  * Probability: Quantifies uncertainty, allowing us to describe the likelihood of events. It provides
    a framework for reasoning about random phenomena.  
  * Statistics: Involves collecting, analysing, interpreting, presenting, and organising data to find
    patterns, make inferences, and draw conclusions. In ML, we constantly deal with data that has inherent
    variability and uncertainty.  

* Why it's used:  
  * Modelling Uncertainty: Many ML models, particularly those involved in classification, are explicitly
    built upon probabilistic principles to estimate the likelihood of different outcomes. For example,
    a spam classifier might not just say "spam" or "not spam," but "95% probability of being spam."
    Naive Bayes classifiers are a prime example of models rooted in conditional probability.  
  * Evaluating Models: How good is our model? Statistics provides rigorous framework to assess a model's
    performance. Measures like accuracy, precision, recall, F1-score, Area Under the Receiver Operating
    Characteristic Curve (AUC-ROC), and confidence intervals are all statistical metrics used to understand
    a model's strengths, weaknesses, and whether its predictions are statistically significant.  
  * Data Understanding and Preprocessing: Statistics is indispensable for exploring and understanding
    the distribution of our data. It helps identify outliers, detect correlations between different
    features, and guide effective data preparation for modelling (e.g., normalisation, imputation of
    missing values, sampling techniques). Understanding concepts like mean, median, variance, standard
    deviation, and different probability distributions (e.g., Gaussian) is fundamental.  
  * Inferential Statistics: This branch allows us to make predictions or draw conclusions about a larger
    population based on a sample of data, which is precisely what ML models aim to do: learn from training
    data and generalise to unseen data.  

* *Programmer's view:* When you split your dataset into training, validation, and testing sets (to ensure
  the model generalises well), or when you analyse your model's performance metrics after training, you
  are applying fundamental statistical concepts. Understanding statistical significance helps you interpret
  if an improvement in your model's performance is truly meaningful or just random chance. Many data
  science libraries in Python (e.g., Pandas, Matplotlib, Seaborn, SciPy) have strong statistical underpinnings.


### Conclusion

These three mathematical pillars--Linear Algebra for data representation and manipulation,
Calculus for optimisation, and Probability & Statistics for understanding uncertainty and
evaluating performance--form the bedrock of Machine Learning. While you don't need to be a
theoretical mathematician, a solid grasp of these concepts will empower you to move beyond
simply using ML libraries as black boxes, enabling you to design, understand, debug, and
innovate in the exciting field of machine learning.

*Continue learning the [core](./CORE.md) of ML ..*
