
## GPT-2 Math Fine-Tuning Project

To get a sense of what LLMs are, but also to show the Null hypothesis:
A framework for fine-tuning GPT-2 on mathematical reasoning tasks and testing
the hypothesis that specialised training improves mathematical
problem-solving capabilities.

This project demonstrates:
1. *Data Synthesis*: Generating custom math problem datasets
2. *Model Fine-Tuning*: Training GPT-2 on mathematical reasoning
3. *Hypothesis Testing*: Statistically validating performance improvements
4. *Evaluation*: Comparing baseline vs. fine-tuned model performance

#### Null Hypothesis

*H₀*: Fine-tuning GPT-2 on mathematical problems does not significantly improve its accuracy on math tasks.

*H₁*: Fine-tuning GPT-2 on mathematical problems significantly improves its accuracy on math tasks.


### Project Structure

```
gpt2/
├── README.md                         # This file
├── requirements.txt                  # Python dependencies
├── scripts/
│   ├── 1_generate_dataset.py         # Synthesize math problems
│   ├── 2_prepare_data.py             # Format data for training
│   ├── 3_finetune_model.py           # Fine-tune GPT-2
│   ├── 4_evaluate_models.py          # Compare baseline vs fine-tuned
│   ├── 5_test_hypothesis.py          # Statistical hypothesis testing
│   └── utils.py                      # Helper functions
├── data/
│   ├── math_dataset.json             # Generated math problems
│   ├── train.json                    # Training split
│   └── test.json                     # Test split
├── results/
│   ├── baseline_results.json         # Baseline model outputs
│   ├── finetuned_results.json        # Fine-tuned model outputs
│   └── hypothesis_test.json          # Statistical test results
└── docs/
    └── METHODOLOGY.md                # Detailed methodology explanation
```

#### Step 1: Read the QUICKSTART

Here: [QUICKSTART](QUICKSTART.md)
(Almost the same instructions.)

#### Step 2: Create Virtual Environment (Recommended)

```bash
python -m venv venv

## Activate on Linux/Mac
source venv/bin/activate

## Activate on Windows
venv\Scripts\activate
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

*What gets installed:*
- `transformers` - Hugging Face library for GPT-2
- `torch` - PyTorch deep learning framework
- `datasets` - Dataset handling utilities
- `numpy` - Numerical computing
- `scipy` - Statistical tests
- `tqdm` - Progress bars

#### Step 4: Verify GPU Setup (Optional but Recommended)

```python
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

If CUDA is available, fine-tuning will be significantly faster.

### Run

Run the entire pipeline with these commands:

```bash
## 1. Generate synthetic math dataset (1000 problems)
python scripts/1_generate_dataset.py

## 2. Prepare training and test splits
python scripts/2_prepare_data.py

## 3. Fine-tune GPT-2 (this takes the longest - 15-30 minutes on GPU)
python scripts/3_finetune_model.py

## 4. Evaluate both models
python scripts/4_evaluate_models.py

## 5. Run hypothesis test
python scripts/5_test_hypothesis.py
```

*Expected Timeline:*
- Data generation: < 1 minute
- Data preparation: < 1 minute
- Fine-tuning: 15-30 minutes (GPU) or 2-4 hours (CPU)
- Evaluation: 5-10 minutes
- Hypothesis test: < 1 minute

### Detailed Workflow

#### Phase 1: Data Generation

*Script*: `1_generate_dataset.py`

Generates a synthetic dataset of arithmetic problems with four operations:
- Addition (e.g., "23 + 45")
- Subtraction (e.g., "78 - 34")
- Multiplication (e.g., "12 * 8")
- Division (e.g., "96 / 8")

*Output*: `data/math_dataset.json`

*Customization:*
```python
## Edit the script to change dataset size
python scripts/1_generate_dataset.py --num_problems 2000
```

#### Phase 2: Data Preparation

*Script*: `2_prepare_data.py`

Splits the dataset into:
- *Training set* (80%): Used for fine-tuning
- *Test set* (20%): Used for evaluation

Formats data into the structure expected by the Trainer API.

*Output*: 
- `data/train.json`
- `data/test.json`

#### Phase 3: Model Fine-Tuning

*Script*: `3_finetune_model.py`

Fine-tunes GPT-2 on the mathematical dataset using Hugging Face's Trainer API.

*Key Parameters:*
- Model: `gpt2` (124M parameters)
- Epochs: 3
- Batch size: 8
- Learning rate: 5e-5
- Warmup steps: 500

*Output*: 
- `./fine_tuned_model/` directory with model checkpoints
- Training logs in `./logs/`

*Monitor Training:*
```bash
## Watch training progress
tail -f logs/*/training_log.txt
```

#### Phase 4: Model Evaluation

*Script*: `4_evaluate_models.py`

Evaluates both baseline and fine-tuned models on the test set.

*Metrics Calculated:*
- *Accuracy*: Percentage of correctly solved problems
- *Exact Match*: Whether the full output matches expected answer
- *Per-Operation Breakdown*: Accuracy by operation type

*Output*: 
- `results/baseline_results.json`
- `results/finetuned_results.json`

#### Phase 5: Hypothesis Testing

*Script*: `5_test_hypothesis.py`

Performs statistical analysis to determine if the improvement is significant.

*Statistical Tests:*
- Independent t-test
- Bootstrap confidence intervals (optional)
- Effect size calculation (Cohen's d)

*Output*: 
- `results/hypothesis_test.json`
- Console output with test results

### Scripts Documentation

#### 1_generate_dataset.py

```bash
python scripts/1_generate_dataset.py [--num_problems N]
```

*Options:*
- `--num_problems`: Number of problems to generate (default: 1000)
- `--max_value`: Maximum operand value (default: 100)

#### 2_prepare_data.py

```bash
python scripts/2_prepare_data.py [--train_split RATIO]
```

*Options:*
- `--train_split`: Training set ratio (default: 0.8)

#### 3_finetune_model.py

```bash
python scripts/3_finetune_model.py [OPTIONS]
```

*Options:*
- `--epochs`: Number of training epochs (default: 3)
- `--batch_size`: Training batch size (default: 8)
- `--learning_rate`: Learning rate (default: 5e-5)
- `--output_dir`: Model save directory (default: ./fine_tuned_model)

#### 4_evaluate_models.py

```bash
python scripts/4_evaluate_models.py [--model_path PATH]
```

*Options:*
- `--model_path`: Path to fine-tuned model (default: ./fine_tuned_model)
- `--test_file`: Test data file (default: data/test.json)

#### 5_test_hypothesis.py

```bash
python scripts/5_test_hypothesis.py [--alpha THRESHOLD]
```

*Options:*
- `--alpha`: Significance level (default: 0.05)


### Understanding the Hypothesis Test

#### What We're Testing

We want to determine if fine-tuning *causes* an improvement,
not just correlates with it.

#### Methodology

1. *Controlled Comparison*: Same test set for both models
2. *Statistical Rigor*: Use p-values to measure significance
3. *Effect Size*: Quantify the magnitude of improvement

#### Interpreting Results

*If p-value < 0.05:*
- Reject null hypothesis
- Fine-tuning has a statistically significant effect
- The improvement is unlikely due to chance

*If p-value ≥ 0.05:*
- Fail to reject null hypothesis
- No significant evidence of improvement
- Differences might be due to random variation

#### Example Output

```
=== Hypothesis Test Results ===
Baseline Accuracy: 0.23 (23%)
Fine-tuned Accuracy: 0.87 (87%)
Difference: 0.64 (64 percentage points)

Statistical Test: Independent t-test
P-value: 0.0001
Significance level: 0.05

REJECT NULL HYPOTHESIS
Fine-tuning significantly improves performance (p < 0.05)
Effect size (Cohen's d): 2.43 (large effect)
```

### Results and Evaluation

After running the pipeline, check:

1. *Training Logs*: `logs/` - Monitor loss curves
2. *Model Checkpoints*: `fine_tuned_model/` - Saved model weights
3. *Evaluation Results*: `results/` - JSON files with metrics
4. *Console Output*: Real-time feedback during execution

#### Expected Improvements

Based on similar experiments:
- Baseline accuracy: 20-30% (random guessing level)
- Fine-tuned accuracy: 80-95% on simple arithmetic
- Significant p-value: < 0.001


### Advanced Usage

#### Custom Dataset

Replace `1_generate_dataset.py` with your own data:

```python
# data/math_dataset.json format
[
    {
        "problem": "What is 5 + 3?",
        "solution": "8"
    },
    ...
]
```

#### Hyperparameter Tuning

Modify `3_finetune_model.py`:

```python
training_args = TrainingArguments(
    num_train_epochs=5,              # More epochs
    per_device_train_batch_size=16,  # Larger batches
    learning_rate=3e-5,              # Lower learning rate
    warmup_steps=1000,               # More warmup
)
```

#### Using Larger Models

Replace `gpt2` with:
- `gpt2-medium` (355M parameters)
- `gpt2-large` (774M parameters)
- `gpt2-xl` (1.5B parameters)

Larger models require significantly more VRAM.


### Troubleshooting

#### Out of Memory (OOM) Error

```bash
# Reduce batch size
python scripts/3_finetune_model.py --batch_size 4

# Or use gradient accumulation
# Edit 3_finetune_model.py and add:
# gradient_accumulation_steps=2
```

#### CUDA Not Available

If you don't have a GPU:
```python
# Training will automatically use CPU
# Expect 10-20x slower training
```

#### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

#### Model Not Found

```bash
# Verify model was saved
ls -la fine_tuned_model/

# Check for pytorch_model.bin
```

#### Poor Accuracy on Test Set

Possible causes:
1. *Insufficient training*: Increase epochs or data size
2. *Data quality*: Verify test set format matches training
3. *Overfitting*: Use validation set to monitor
4. *Task difficulty*: Start with simpler operations

### Notes and Best Practices

1. *Always use a test set* separate from training data
2. *Monitor for overfitting* by checking validation loss
3. *Run multiple trials* to ensure reproducibility
4. *Document hyperparameters* for each experiment
5. *Version control your data* and model checkpoints

### Contributing / Projects

To extend this project:
1. Add new problem types (algebra, calculus, etc.)
2. Implement additional evaluation metrics
3. Compare multiple model architectures
4. Add visualization tools for results


### Reference

- [Hugging Face Transformers Documentation](https://huggingface.co/docs/transformers)
- [GPT-2 Paper](https://openai.com/blog/better-language-models/)
- [Fine-tuning Best Practices](https://huggingface.co/docs/transformers/training)
- [Statistical Hypothesis Testing](https://en.wikipedia.org/wiki/Statistical_hypothesis_testing)

