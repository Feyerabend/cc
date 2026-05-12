
## Linear Regression

Linear regression is a fundamental statistical method used to model the relationship between a dependent
variable and one or more independent variables. It's a cornerstone of predictive analytics and machine
learning, allowing us to understand trends, make forecasts, and identify the strength of relationships
between variables.

Imagine you're tracking the number of hours students study for an exam and their corresponding test scores.
You might notice a general trend: the more hours a student studies, the higher their score tends to be.
Linear regression helps us draw a straight line through these data points that best represents this trend.
This line can then be used to predict a student's score based on how many hours they study. In essence,
it tries to find a simple, straight-line relationship between two things.


### Mathematics

At its core, linear regression seeks to fit a linear equation to observed data. For a simple linear
regression (with one independent variable), the model is represented as:

```math
y = \beta_0 + \beta_1 x + \epsilon
```

Where:
* $y$ is the dependent variable (what we are trying to predict, e.g., test score).
* $x$ is the independent variable (what we are using to predict, e.g., hours studied).
* $\beta_0$ (beta-naught) is the y-intercept, representing the expected value of $y$ when $x$ is 0.
* $\beta_1$ (beta-one) is the slope of the line, representing the change in $y$ for a one-unit change in $x$.
* $\epsilon$ (epsilon) is the error term, representing the difference between the observed value of $y$ and
  the value predicted by the model. It accounts for variability not explained by the independent variable.

The goal of linear regression is to find the values of $\beta_0$ and $\beta_1$ that minimise the sum of
the squared differences between the actual $y$ values and the $y$ values predicted by our line. This
method is called the "Ordinary Least Squares" (OLS) method.


### Concepts

* *Dependent Variable (Response Variable):* The variable we are trying to predict or explain.
* *Independent Variable (Predictor Variable, Explanatory Variable):* The variable(s) used to predict or
  explain the dependent variable.
* *Regression Line:* The straight line that best fits the data, representing the estimated relationship
  between the variables.
* *Slope* ($\beta_1$): Indicates the direction and strength of the linear relationship between the
  independent and dependent variables. A positive slope means $y$ increases as $x$ increases, while
  a negative slope means $y$ decreases as $x$ increases.
* *Intercept* ($\beta_0$): The point where the regression line crosses the y-axis. It's the predicted
  value of the dependent variable when the independent variable is zero.
* *Residuals (Errors):* The vertical distances between the actual data points and the regression line.
  Linear regression aims to minimize these errors.
* *Coefficient of Determination* ($R^2$): A statistical measure that represents the proportion of the
  variance in the dependent variable that can be explained by the independent variable(s). It ranges
  from 0 to 1, with higher values indicating a better fit.


### Samples


*Sample 1: Predicting House Prices*

* *Dependent Variable:* House price
* *Independent Variable:* Square footage of the house
* *Scenario:* You collect data on various houses, noting their size and selling price. Linear regression
  can be used to build a model that predicts the price of a house based on its square footage. The slope
  would tell you how much the price is expected to increase for every additional square foot.


*Sample 2: Marketing Campaign Effectiveness*

* *Dependent Variable:* Sales revenue
* *Independent Variable:* Advertising expenditure
* *Scenario:* A company wants to understand if increasing their advertising budget leads to higher sales.
  By running a linear regression, they can determine if there's a significant positive relationship between
  ad spending and revenue. The model could help them predict potential sales for different advertising budgets.


*Sample 3: Agricultural Yield*

* *Dependent Variable:* Crop yield (e.g., bushels per acre)
* *Independent Variable:* Amount of fertilizer used
* *Scenario:* A farmer wants to optimize fertilizer usage. They can experiment with different fertilizer amounts
  on various plots and then use linear regression to model the relationship between fertilizer applied and crop
  yield. This helps them determine the optimal fertilizer amount to maximize yield.


