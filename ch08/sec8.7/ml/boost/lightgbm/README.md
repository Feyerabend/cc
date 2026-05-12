## LightGBM

LightGBM (Light Gradient Boosting Machine) is a powerful machine learning algorithm
developed by Microsoft, belonging to the family of gradient boosting methods. It combines
many simple decision-making rules into one highly accurate predictor, similar to assembling
a team of specialists to make a highly accurate collective decision on a loan application.
Each expert (or decision tree in LightGBM's case) learns from the mistakes of previous
experts, gradually building a more accurate model.



### The Real-World Problem: Credit Approval

Banks and financial institutions process thousands of loan applications daily, each
decision carrying significant risk. Approving a good applicant leads to customer
satisfaction and interest income, while denying one means lost revenue. Conversely,
approving a risky applicant risks potential default and financial loss, whereas denying
them avoids risk and ensures sound business practice. The cost of incorrect decisions
is substantial; for example, a single bad $50,000 loan might require 50 good loans to
offset the loss. This is where machine learning can be invaluable.


#### Traditional vs. ML Approach

Traditionally, loan officers manually review applications, relying on experience and
basic rules. This often leads to *inconsistent decisions, human bias, slow processing,
and limited ability to process complex patterns*. In contrast, a machine learning
approach analyses thousands of historical applications to discover complex patterns
human reviewers might miss. It can process applications in milliseconds, handling
multiple factors simultaneously.

However, it's crucial to state this more carefully: While ML models offer consistency
and can process vast amounts of data, they are not inherently "unbiased." *Machine
learning can introduce new forms of bias or amplify existing ones if not properly
managed.* If the historical data used for training contains biases from past human
decisions, the ML model will learn and perpetuate these, potentially leading to unfair
judgments. Therefore, simply introducing ML or AI is not a straight solution to
eliminating bias; rather, it shifts the challenge to *identifying and mitigating
algorithmic and data-driven biases.*


### What The Code Example Does

Our example uses the renowned American Credit Approval dataset, comprising 690 real
credit applications, each with 15 anonymised features (e.g., A2, A3 likely represent
age and income; A8, A9 possibly employment history and loan purpose; A14, A15 credit
history and existing financial obligations). Each application has a known outcome:
approved (+) or denied (-).


#### Step-by-Step Process Walkthrough

1. *Data Loading and Exploration*: The model learns from 690 real credit decisions,
   with the dataset shape being (690, 15) and target classes as \['+', '-'\]. The
   algorithm first examines historical data to understand the problem scope.

2. *Data Preprocessing*: Real-world data is often messy. Our code addresses missing
   values, mixed data types, and inconsistent formats, transforming raw, messy data
   into clean, numerical data ready for machine learning. This is akin to standardising
   all loan applications into a uniform format before review.

3. *Model Training*: During training, the algorithm iteratively builds decision trees.
   For instance, the first tree might achieve 60% accuracy, and subsequent trees focus
   on the cases the previous ones got wrong. This continues for a set number of
   iterations (e.g., 30 in our example) until *early stopping* occurs, meaning additional
   trees no longer improve accuracy. This process is analogous to 30 loan experts, each
   becoming more specialized in handling difficult cases that previous experts struggled
   with.

4. *Performance Evaluation*: The Credit Approval Model achieved an *Accuracy of 0.8188*.
   The classification report further breaks down performance:
    * *82% overall accuracy*: The model makes the correct decision 82 out of 100 times.
    * *87% precision for approvals*: When the model predicts "approve," it's correct 87% of the time.
    * *85% recall for denials*: The model identifies 85% of risky applications that should be denied.

5. *Feature Importance*: This step identifies the most critical factors for credit approval.
   For example, A3 (likely income) might be the most important, followed by A14 (possibly
   credit history), and then A2 (perhaps age or employment length). This insight helps
   businesses focus data collection efforts, streamline application processes, and better
   understand risk factors.

6. *Real-Time Prediction Example*: For a new application, the model provides a prediction
   with a confidence score. For instance, if an actual approved application was predicted
   as approved with 96.2% confidence, it demonstrates the model's reliability for real-world
   use.



#### For Financial Institutions

LightGBM offers significant *operational benefits*, including processing applications in
seconds (speed), and potentially achieving greater consistency and scalability compared
to manual processes. It can aid in *risk management* by providing better default prediction
and quantifying decision certainty. However, it's vital to acknowledge that while ML provides
an audit trail of decisions, ensuring that these decisions are truly *unbiased and fair*
requires proactive efforts to address algorithmic and data biases.

#### For Loan Applicants

Applicants *can* experience *improved experiences* through faster decisions and potentially
more consistent evaluation criteria. However, the promise of "fair treatment" and "reduced bias"
is not automatically guaranteed. Decisions are based on data, but if that data is biased,
the system can perpetuate or even exacerbate unfair outcomes. *Ensuring truly fair treatment
and reduced bias requires careful attention to data quality, algorithm design, and continuous
monitoring for disparate impact across different applicant groups.*

#### Regulatory Compliance

Modern banking regulations demand *explainable decisions* and *fair lending practices*, meaning
no discrimination based on protected characteristics. They also require *risk documentation*.
While LightGBM provides clear feature importance and can help in understanding *what* factors
influenced a decision, the *why* (in terms of fairness) still requires significant effort.
Financial institutions must actively work to ensure their ML models satisfy fair lending
requirements and can demonstrate non-discriminatory outcomes, which goes beyond just model
accuracy.


### Why LightGBM Specifically?

Compared to traditional rules-based systems, LightGBM automatically discovers
complex patterns, adapts to changing market conditions, and handles multiple
variables simultaneously. Against Deep Learning, it offers much faster training
and prediction, requires less data, provides more interpretable results, and has
lower computational requirements. When compared to other gradient boosting algorithms
like XGBoost and CatBoost, LightGBM stands out for its faster training, lower memory
usage (efficient for large datasets), better accuracy (often winning machine learning
competitions), and ease of use (sensible defaults, less hyperparameter tuning).

LightGBM incorporates several key optimisations, including *leaf-wise tree growth*
(more efficient than traditional level-wise growth), *Exclusive Feature Bundling*
(reduces memory usage and training time), and *Gradient-based One-Side Sampling*
(focuses on more informative data points).

Consider a mid-size bank processing 10,000 loan applications annually. Without machine
learning, manual review (2 hours per application) costs $1,000,000 annually in labor
and potentially $1,500,000 in losses from bad loans (70% human accuracy). With LightGBM,
automated screening takes seconds per application. An implementation cost of $100,000
(one-time) can lead to reduced bad loans (18% × $5M = $900,000 potential losses) due
to 82% ML accuracy. This results in annual savings of $600,000 in reduced losses plus
$800,000 in labor costs, totaling *$1,400,000*.


This LightGBM example demonstrates how modern machine learning *can* transform traditional
business processes. By learning from historical data, the algorithm *can* create a fast,
accurate, and consistent decision-making system that benefits both financial institutions
and their customers. The 82% accuracy achieved on real credit data represents a significant
improvement over purely manual processes. However, achieving truly *fair and unbiased outcomes*,
and ensuring compliance with complex regulatory requirements, demands a proactive and
continuous effort to address potential *algorithmic and data biases*. It is a powerful tool,
but its responsible application requires careful attention to its limitations and ethical
implications.

