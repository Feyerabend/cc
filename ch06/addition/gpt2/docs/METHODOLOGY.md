
## Methodology Documentation

This document provides an explanation of the methodology
used in this GPT-2 math fine-tuning project, including the theoretical
foundation, experimental design, and statistical approach.


### Table of Contents

1. [Research Question](#research-question)
2. [Hypothesis Framework](#hypothesis-framework)
3. [Experimental Design](#experimental-design)
4. [Data Generation](#data-generation)
5. [Model Training](#model-training)
6. [Evaluation Methodology](#evaluation-methodology)
7. [Statistical Testing](#statistical-testing)
8. [Interpretation Guidelines](#interpretation-guidelines)

### Research Question

*Primary Question*: Does fine-tuning GPT-2 on mathematical problems
improve its ability to solve arithmetic tasks?

This question is important because:
- It tests whether language models can learn specialized skills through fine-tuning
- It provides insights into transfer learning for numerical reasoning
- It demonstrates a systematic approach to evaluating model improvements


### Hypothesis Framework

#### Null Hypothesis (H₀)

*Statement*: Fine-tuning GPT-2 on mathematical problems does
not significantly improve its accuracy on arithmetic tasks.

*Formal Notation*: μ_finetuned - μ_baseline = 0

Where:
- μ_baseline = mean accuracy of baseline GPT-2
- μ_finetuned = mean accuracy of fine-tuned GPT-2

#### Alternative Hypothesis (H₁)

*Statement*: Fine-tuning GPT-2 on mathematical problems
significantly improves its accuracy on arithmetic tasks.

*Formal Notation*: μ_finetuned - μ_baseline > 0

#### Why This Matters

Testing the null hypothesis prevents us from making false
claims about model improvements. Without statistical testing,
we might attribute random fluctuations to genuine learning effects.


### Experimental Design

#### Control Variables

To ensure a fair comparison, we control:
1. *Model Architecture*: Both models use identical GPT-2 architecture (124M parameters)
2. *Test Set*: Both models are evaluated on the same held-out test problems
3. *Evaluation Procedure*: Identical generation parameters and answer extraction
4. *Random Seeds*: Fixed for reproducibility

#### Treatment

The *treatment* is fine-tuning on a mathematical dataset consisting of:
- Arithmetic problems (addition, subtraction, multiplication, division)
- Formatted as question-answer pairs
- Presented in a consistent format: "Q: {problem} A: {answer}"

#### Measurements

*Primary Metric*: Accuracy (proportion of correctly solved problems)

*Secondary Metrics*:
- Accuracy by operation type
- Effect size (Cohen's d)
- Confidence intervals


### Data Generation

#### Synthetic Dataset Rationale

We use a *synthetic dataset* for several reasons:
1. *Control*: We know the ground truth with certainty
2. *Scale*: Easy to generate thousands of examples
3. *Balance*: Can ensure even distribution across operations
4. *Reproducibility*: Anyone can regenerate the exact dataset

#### Generation Process

```python
For each problem:
1. Select operation: {+, -, *, /}
2. Generate operands: random integers in [1, 100]
3. Special handling for division (ensure integer results)
4. Calculate ground truth solution
5. Format as: "Q: a op b A: solution"
```

#### Dataset Split

- *Training Set*: 80% (used for fine-tuning)
- *Test Set*: 20% (held out for evaluation)

*Critical*: Test set must be completely separate to measure generalization.


### Model Training

#### Fine-Tuning Parameters

```
Model: GPT-2 (124M parameters)
Epochs: 3
Batch Size: 8
Learning Rate: 5e-5
Optimizer: AdamW
Warmup Steps: 500
Max Sequence Length: 128
```

#### Why These Parameters?

- *Small learning rate*: Prevents catastrophic forgetting of pre-trained knowledge
- *Few epochs*: Avoids overfitting on small dataset
- *Warmup*: Stabilizes training in early steps

#### Training Objective

*Causal Language Modeling*: Predict next token given previous tokens

The model learns to generate:
```
Q: 5 + 3 A: 8
```

By minimising cross-entropy loss between predicted and actual tokens.


### Evaluation Methodology

#### Generation Process

For each test problem:
1. Provide question: "Q: 5 + 3"
2. Generate continuation with model
3. Extract numeric answer from generated text
4. Compare to ground truth

#### Answer Extraction

We use regex to extract numbers from generated text:
- Look for first numeric value after "A:"
- Handle decimals and negative numbers
- Mark as incorrect if no number found

#### Accuracy Calculation

```
Accuracy = (Number of Correct Answers) / (Total Test Problems)
```

A prediction is "correct" if:
- Exact match for integers
- Within 0.01 for floating-point (handles rounding errors)


### Statistical Testing

#### Why Statistical Testing?

Observed accuracy differences could be due to:
1. *True effect*: Fine-tuning actually helps
2. *Random chance*: Natural variation in model outputs
3. *Test set bias*: Easier/harder problems by chance

Statistical testing helps us distinguish (1) from (2) and (3).

#### Tests Performed

##### 1. Independent t-test

*Purpose*: Compare mean accuracy between two independent samples

*Assumptions*:
- Independent samples (different model predictions)
- Approximately normal distribution (Central Limit Theorem applies)

*Interpretation*:
- *p-value < 0.05*: Reject H₀ (significant difference)
- *p-value ≥ 0.05*: Fail to reject H₀ (no significant evidence)

##### 2. Mann-Whitney U Test

*Purpose*: Non-parametric alternative to t-test

*Advantage*: Doesn't assume normal distribution

*Use*: Confirms t-test results with fewer assumptions

##### 3. Effect Size (Cohen's d)

*Purpose*: Measure the magnitude of the difference

*Formula*:
```
Cohen's d = (μ₁ - μ₂) / pooled_standard_deviation
```

*Interpretation*:
- |d| < 0.2: Negligible effect
- 0.2 ≤ |d| < 0.5: Small effect
- 0.5 ≤ |d| < 0.8: Medium effect
- |d| ≥ 0.8: Large effect

*Importance*: A statistically significant result with small
effect size may not be practically meaningful.

##### 4. Bootstrap Confidence Intervals

*Purpose*: Estimate uncertainty in accuracy difference

*Method*:
1. Resample results with replacement (10,000 times)
2. Calculate mean difference for each sample
3. Compute 95% confidence interval

*Interpretation*: If CI excludes 0, we can be 95% confident the improvement is real.

#### Significance Level (α)

We use *α = 0.05* (5% significance level)

*Meaning*:
- We accept a 5% chance of false positive (Type I error)
- If p < 0.05, improvement is significant at 95% confidence

#### Multiple Testing Considerations

We perform multiple statistical tests (t-test, Mann-Whitney, etc.) but:
- They test the same hypothesis in different ways
- We don't need Bonferroni correction
- Primary conclusion comes from t-test; others are confirmatory


### Interpretation Guidelines

#### Scenario 1: Significant Improvement

*Results*:
- p-value < 0.05
- Large effect size (d > 0.8)
- 95% CI excludes 0

*Conclusion*: 
Fine-tuning significantly improves mathematical reasoning
The improvement is both statistically significant and practically meaningful
Results are unlikely due to chance

#### Scenario 2: No Significant Improvement

*Results*:
- p-value ≥ 0.05
- Small effect size (d < 0.2)
- 95% CI includes 0

*Conclusion*:
✗ No evidence that fine-tuning improves performance
✗ Observed differences could be due to random variation
✗ Need larger sample size or different approach

#### Scenario 3: Significant but Small Effect

*Results*:
- p-value < 0.05
- Small effect size (d ~ 0.3)
- 95% CI barely excludes 0

*Conclusion*:
⚠ Fine-tuning has a statistically significant but small effect
⚠ May not be practically meaningful
⚠ Consider whether the improvement justifies the computational cost


### Limitations

#### Acknowledged Limitations

1. *Task Simplicity*: Arithmetic is relatively simple;
   results may not generalize to complex math

2. *Synthetic Data*: Real-world math problems may be more varied

3. *Small Model*: GPT-2 (124M) is small by modern standards;
   larger models might show different patterns

4. *Limited Training*: Only 3 epochs with 800 examples;
   more data might help

5. *Single Trial*: Ideally, we'd run multiple trials
   with different random seeds

#### Addressing Limitations

To strengthen conclusions:
- Run multiple trials with different random seeds
- Test on larger, more diverse datasets
- Compare multiple model sizes
- Include more complex mathematical operations


### Best Practices

#### For Reproducibility

1. Fix random seeds
2. Document all hyperparameters
3. Save model checkpoints
4. Version control data and code
5. Provide clear instructions

#### For Valid Inference

1. Use held-out test set
2. Avoid data leakage
3. Report all metrics
4. Use appropriate statistical tests
5. Acknowledge limitations

#### For Practical Application

1. Consider computational costs
2. Measure effect size, not just p-values
3. Test on diverse problems
4. Compare to relevant baselines
5. Validate on real-world tasks


### Reference

##### Statistical Methods

- *t-tests*: Student (1908). "The Probable Error of a Mean"
- *Effect Sizes*: Cohen (1988). "Statistical Power Analysis for the Behavioral Sciences"
- *Bootstrap Methods*: Efron (1979). "Bootstrap Methods: Another Look at the Jackknife"

##### Machine Learning

- *GPT-2 Paper*: Radford et al. (2019). "Language Models are Unsupervised Multitask Learners"
- *Transfer Learning*: Pan & Yang (2010). "A Survey on Transfer Learning"
- *Fine-tuning*: Howard & Ruder (2018). "Universal Language Model Fine-tuning for Text Classification"

##### Experimental Design

- *Null Hypothesis Testing*: Fisher (1925). "Statistical Methods for Research Workers"
- *Reproducibility*: Peng (2011). "Reproducible Research in Computational Science"


### Conclusion

This methodology combines:
- *Rigorous experimental design* (controlled comparison)
- *Statistical hypothesis testing* (p-values, effect sizes)
- *Reproducible procedures* (documented parameters, fixed seeds)

