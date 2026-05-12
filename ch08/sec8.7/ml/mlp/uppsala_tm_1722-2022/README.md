
## MLP and Linear Regression

The provided Python code implements a machine learning pipeline for predicting temperature using
a *Multilayer Perceptron* (MLP) and *Linear Regression*, applied to a temperature dataset (in
this case real). The pedagogical value lies in its comprehensive demonstration of key machine
learning concepts, data preprocessing, model evaluation, and visualisation techniques. 
(Also see [linear regression](./../../linear/).)

The temperature data used in this project comes from the official long-term temperature series
for Uppsala, Sweden, maintained by the Swedish Meteorological and Hydrological Institute (SMHI):
https://www.smhi.se/data/temperatur-och-vind/temperatur/uppsalas-temperaturserie

Additional historical background, including commentary on the data’s continuity and adjustments
over time, is available here: http://celsius.met.uu.se/default.aspx?pageid=31.

You may recognise the name Celsius as the unit of temperature measurement. Anders Celsius, the
Swedish astronomer and physicist who proposed the Celsius scale, was also actively involved in
early temperature measurements in Uppsala, where he lived and worked.
> *The temperature series from Uppsala is one of the longest continuous records in the world
> and has been used in numerous studies of historical climate trends.*

The main lesson from this code: You will likely discover that the MLP performs similarly to
linear regression on this data. This teaches that the crucial ML lesson: complexity isn't
always better. You might therefore see when and why to choose simpler models, which is more
valuable than just throwing complex models at everything.


### Multilayer Perceptron (MLP)

- *Definition*: An MLP is a type of artificial neural network consisting of multiple layers of
  interconnected nodes (neurons). It includes an input layer, one or more hidden layers with
  non-linear activation functions (e.g., ReLU), and an output layer. MLPs are used for both
  regression and classification tasks.

- *How It Works*:
  - *Input Layer*: Takes the feature vector (e.g., year, month, day_of_year, etc.).
  - *Hidden Layers*: Apply weighted transformations and non-linear activations to capture
    complex patterns in the data.
  - *Output Layer*: Produces a single value for regression (e.g., predicted temperature).
  - *Training*: Uses backpropagation and an optimiser (e.g., Adam) to minimize a loss function
    (e.g., MSE) by adjusting weights.

- *Key Features*:
  - Can model non-linear relationships, making it suitable for complex datasets.
  - Requires careful tuning of hyperparameters (e.g., number of layers, neurons, learning rate).
  - Prone to overfitting, mitigated by techniques like dropout and early stopping.

- *In the Code*: The MLP is implemented with three hidden layers (64, 32, 16 neurons), ReLU activation,
  dropout for regularisation, and early stopping to prevent overfitting. It’s trained on scaled features
  to predict temperature.


### Linear Regression

- *Definition*: Linear Regression is a statistical model that predicts a continuous output variable
  as a linear combination of input features. It assumes a linear relationship between features and the target.

- *How It Works*:
  - Fits a line (or hyperplane in higher dimensions) to the data by minimising the sum of squared errors.
  - Model equation: $y = w_0 + w_1x_1 + w_2x_2 + \dots + w_nx_n$, where $w_i$ are weights, $x_i$ are features,
    and $y$ is the predicted value.
  - Coefficients ($w_i$) indicate feature importance.

- *Key Features*:
  - Simple, interpretable, and computationally efficient.
  - Limited to linear relationships, so it may underfit complex data.
  - Less prone to overfitting compared to MLPs.

- *In the Code*: Linear Regression is used as a baseline model, trained on the same scaled features as the
  MLP. Its coefficients are analysed to identify the most important features (e.g., seasonal or temporal features).


### Comparison in the Code

- *Purpose*: The code compares MLP and Linear Regression to determine if the MLP's complexity improves temperature
  prediction over the simpler Linear Regression model.

- *Findings*:
  - *Performance*: The R² and MAE bar charts (`r2_comparison.png`, `mae_comparison.png`) show whether the MLP
    outperforms Linear Regression. If the MLP’s metrics are only marginally better, it suggests overengineering (or
    the choice was too advanced), as the simpler model may suffice.
  - *Feature Importance*: The Linear Regression model provides interpretable coefficients, showing which features
    (e.g., `month_sin`, `day_cos`) drive predictions, while the MLP’s complexity makes feature importance harder
    to interpret.
  - *Overfitting*: The code compares training and test metrics for both models. A large gap between training and
    test performance for the MLP indicates overfitting, while Linear Regression is less likely to overfit due to
    its simplicity.

- *Pedagogical Insight*: This comparison teaches students of these implementations the importance of balancing
  model complexity with performance, using a simple baseline to evaluate whether complex models are really necessary.


### Specific Insights from the Code

- *MLP vs. Linear Regression*: The code suggests that the MLP may capture non-linear patterns (e.g., complex
  seasonal interactions), but if the data is largely explained by linear trends (e.g., seasonal cycles or warming
  trends), Linear Regression may perform comparably with less computational cost.

- *Overengineering*: The MLP’s architecture (three hidden layers, dropout, early stopping) is relatively complex
  for a temperature prediction task, which may be adequately modeled by Linear Regression, especially if seasonal
  features (`month_sin`, `day_cos`) capture most of the variance.

- *Visualisations*: The scatter plots and histograms allow students to visually assess whether the MLP’s predictions
  are more accurate or if residuals show patterns that Linear Regression misses.

- *Experimentation*: The code encourages experimenting with MLP architecture or feature sets, teaching students to
  test hypotheses about model design and feature importance.

There is also a parser which is used for inspecting the data. Running the parser will give you a diagram
to different properties of the data.


### Conclusion

The code teaches you to:
- Prepare and engineer features for temporal data.
- Implement and compare simple (Linear Regression) and complex (MLP) models.
- Evaluate models using standard metrics and visualisations.
- Critically assess whether complex models are justified or if simpler models suffice.

The visualisations (scatter plots, histograms, bar charts) provide intuitive insights into model
performance, error distributions, and training dynamics, making abstract concepts tangible. The
comparison between MLP and Linear Regression highlights the trade-offs between model complexity
and performance, addressing interest in evaluating overengineering in machine learning.
