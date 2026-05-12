
## Logistic Regression

Logistic regression is a statistical method used for binary classification problems. Unlike linear
regression, which predicts a continuous outcome, logistic regression predicts the probability that
an observation belongs to one of two categories (e.g., yes/no, true/false, spam/not spam).

Imagine you're trying to predict if a customer will click on an ad or not. You might have information
like how long they spent on the website, their age, or their browsing history. You can't use a simple
straight line to predict "click" or "no click" because those are categories, not continuous numbers.
Logistic regression helps us by estimating the probability of a "click" based on these factors. If
the probability is above a certain threshold (say, 50%), we predict they will click; otherwise, we
predict they won't. It essentially draws an "S-shaped" curve that squashes the predictions between
0 and 1 (probabilities).


### Mathematics

While linear regression uses a linear equation, logistic regression uses a logistic function (also
known as the sigmoid function) to map the output of a linear combination of independent variables
to a probability between 0 and 1.

The linear combination of independent variables is similar to linear regression:

```math
z = \beta_0 + \beta_1 x_1 + \beta_2 x_2 + ... + \beta_n x_n
```

Where:
* $z$ is the linear combination of independent variables.
* $\beta_0$ is the intercept.
* $\beta_i$ are the coefficients for each independent variable $x_i$.

This $z$ value is then passed through the logistic (sigmoid) function to get the predicted probability $p$:

```math
p = \frac{1}{1 + e^{-z}}
```

or

```math
p = \frac{1}{1 + e^{-(\beta_0 + \beta_1 x_1 + ... + \beta_n x_n)}}
```

Where:
* $p$ is the predicted probability of the dependent variable belonging to a specific class (e.g.,
  probability of a customer clicking the ad).
* $e$ is Euler's number (approximately 2.71828).

The output $p$ is always between 0 and 1. We then set a threshold (commonly 0.5) to classify the
observation. If $p \geq 0.5$, we classify it as one category; otherwise, we classify it as the other.

Logistic regression fundamentally models the *log-odds* of an event. The odds of an event are defined
as $\frac{p}{1-p}$. Taking the natural logarithm of the odds gives us the log-odds:

```math
\text{log-odds} = \ln\left(\frac{p}{1-p}\right) = \beta_0 + \beta_1 x_1 + ... + \beta_n x_n
```

This shows that the log-odds are a linear combination of the independent variables.


### Concepts

* *Binary Classification:* The primary use case for logistic regression, where the dependent variable
  has only two possible outcomes.
* *Sigmoid Function (Logistic Function):* The S-shaped curve that transforms the linear combination of
  predictors into a probability. It squashes any real-valued input into a value between 0 and 1.
* *Log-Odds (Logit):* The logarithm of the odds of an event. Logistic regression models this as a linear
  function of the independent variables.
* *Decision Boundary (Threshold):* The probability value (typically 0.5) used to classify an observation
  into one of the two categories. If the predicted probability is above the threshold, it's one class;
  otherwise, it's the other.
* *Maximum Likelihood Estimation (MLE):* The method used to estimate the coefficients ($\beta$ values)
  in logistic regression. Instead of minimizing squared errors (like OLS in linear regression), MLE aims
  to find the coefficients that maximize the likelihood of observing the actual data.
* *Odds Ratio:* For a one-unit increase in an independent variable, the odds of the event occurring are
  multiplied by $e^{\beta_i}$. This provides an interpretable measure of the impact of each independent
  variable on the odds of the outcome.


### Samples


*Sample 1: Predicting Customer Churn*

* *Dependent Variable:* Churn (Yes/No - did the customer cancel their subscription?)
* *Independent Variables:* Monthly usage, customer service calls, contract type, average bill.
* *Scenario:* A telecommunications company wants to predict which customers are likely to churn.
  Logistic regression can be used to model the probability of churn based on customer behavior and
  service history. The output probability helps them identify at-risk customers and implement
  retention strategies.

*Sample 2: Medical Diagnosis*

* *Dependent Variable:* Disease presence (Yes/No - does the patient have the disease?)
* *Independent Variables:* Age, blood pressure, cholesterol levels, specific symptoms.
* *Scenario:* Doctors can use logistic regression to estimate the probability of a patient having
  a particular disease based on their medical readings and symptoms. If the probability exceeds a
  certain threshold, further diagnostic tests might be recommended.

*Sample 3: Spam Email Detection*

* *Dependent Variable:* Spam (Yes/No - is the email spam?)
* *Independent Variables:* Presence of certain keywords, sender's reputation, number of exclamation
  marks, email length.
* *Scenario:* Email providers use logistic regression to filter out spam. The model can calculate
  the probability that an incoming email is spam based on its characteristics. If the probability
  is high, the email is flagged and moved to the spam folder.


