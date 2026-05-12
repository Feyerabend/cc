
### Diagrams

The code generates six visualisations in the `plots/` (this) directory, each serving a specific pedagogical purpose:

1. *Training Loss Plot (`training_loss.png`)*:
   - *Type*: Line plot
   - *Purpose*: Shows the MLP's training loss (MSE) over epochs, illustrating how the model converges during training.
     It helps you understand the training process and the effect of early stopping.
   - *Pedagogical Value*: Teaches students (you) to monitor training progress and detect convergence or overfitting
     by comparing training and validation loss (if available).

2. *MLP Predictions vs. Actual Scatter Plot (`mlp_predictions.png`)*:
   - *Type*: Scatter plot
   - *Purpose*: Plots predicted temperatures (MLP) against actual temperatures for the test set, with a diagonal line
     indicating perfect predictions. The R² score is included in the title.
   - *Pedagogical Value*: Visualise prediction accuracy and identify patterns in errors (e.g., systematic biases
     or outliers).

3. *Linear Regression Predictions vs. Actual Scatter Plot (`lr_predictions.png`)*:
   - *Type*: Scatter plot
   - *Purpose*: Similar to the MLP scatter plot, but for Linear Regression predictions, allowing direct comparison with the MLP.
   - *Pedagogical Value*: Enables students to compare the predictive performance of a simple linear model versus a complex neural network, highlighting differences in fit.

4. *Residuals Histogram (`residuals_histogram.png`)*:
   - *Type*: Histogram
   - *Purpose*: Shows the distribution of MLP residuals (actual - predicted temperatures), indicating whether errors are normally distributed or skewed.
   - *Pedagogical Value*: Teaches students to analyze model errors, assess model fit, and identify potential biases or areas where the model struggles.

5. *Model Comparison - R² Scores (`r2_comparison.png`)*:
   - *Type*: Bar chart
   - *Purpose*: Compares the R² scores of MLP and Linear Regression, showing which model explains more variance in the test data.
   - *Pedagogical Value*: Helps students understand the goodness-of-fit metric (R²) and compare model effectiveness visually.

6. *Model Comparison - MAE Scores (`mae_comparison.png`)*:
   - *Type*: Bar chart
   - *Purpose*: Compares the Mean Absolute Error (MAE) of MLP and Linear Regression, showing which model has lower average prediction errors.
   - *Pedagogical Value*: Teaches students to interpret MAE as a measure of prediction accuracy and compare models based on error magnitude.

