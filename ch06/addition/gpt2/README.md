
## GPT-2 Math Fine-Tuning Project

GPT-2 marked a major shift in how language models were perceived by demonstrating that simply scaling up a relatively straightforward architecture could yield surprisingly powerful results. Built by OpenAI and released in 2019, GPT-2 used the transformer decoder architecture but was trained at an unprecedented scale for its time (1.5 billion parameters) on a large, diverse corpus of internet text. Its key breakthrough was the empirical finding that larger models trained on more data could exhibit qualitatively new capabilities: coherent long-form text generation, rudimentary reasoning, translation-like behavior, summarization, and question answering—all without task-specific fine-tuning.

Equally significant was GPT-2’s impact on the research community and public discourse. Its outputs were realistic enough to raise concerns about misuse (e.g., automated misinformation), leading to a staged release strategy rather than an immediate full model publication. Scientifically, GPT-2 strengthened the case for unsupervised pretraining followed by adaptation, helped popularize the idea of "emergent abilities," and accelerated the trend toward scaling laws in AI. In hindsight, GPT-2 served as a bridge between earlier NLP systems that relied heavily on supervised datasets and today’s large foundation models capable of broad, flexible language understanding and generation.

This project provides a framework for fine-tuning GPT-2 on mathematical reasoning tasks and testing the hypothesis that specialized training improves mathematical problem-solving capabilities. It demonstrates:
1. Data Synthesis: Generating custom math problem datasets
2. Model Fine-Tuning: Training GPT-2 on mathematical reasoning
3. Hypothesis Testing: Statistically validating performance improvements
4. Evaluation: Comparing baseline vs. fine-tuned model performance


### Null Hypothesis

*H₀*: Fine-tuning GPT-2 on mathematical problems does not significantly improve its accuracy on math tasks.

*H₁*: Fine-tuning GPT-2 on mathematical problems significantly improves its accuracy on math tasks.


### Prerequisites

- Python 3.8+
- 8GB RAM minimum
- 10GB free disk space
- (Optional) CUDA-compatible GPU for faster training

*Difficulty level*: Intermediate  
*Prerequisites*: Basic Python knowledge, understanding of machine learning concepts  
*Estimated time to complete*: 30 minutes - 4 hours (depending on hardware)


### Project Structure

```
gpt2/
├── README.md                         ## This file
├── requirements.txt                  ## Python dependencies
├── scripts/
│   ├── 1_generate_dataset.py         ## Synthesize math problems
│   ├── 2_prepare_data.py             ## Format data for training
│   ├── 3_finetune_model.py           ## Fine-tune GPT-2
│   ├── 4_evaluate_models.py          ## Compare baseline vs fine-tuned
│   ├── 5_test_hypothesis.py          ## Statistical hypothesis testing
│   └── utils.py                      ## Helper functions
├── data/
│   ├── math_dataset.json             ## Generated math problems
│   ├── train.json                    ## Training split
│   └── test.json                     ## Test split
├── results/
│   ├── baseline_results.json         ## Baseline model outputs
│   ├── finetuned_results.json        ## Fine-tuned model outputs
│   └── hypothesis_test.json          ## Statistical test results
└── docs/
    └── METHODOLOGY.md                ## Detailed methodology explanation
```


### Installation

#### 1. Create Virtual Environment (Recommended)

```bash
python -m venv venv

## Activate (Linux/Mac)
source venv/bin/activate

## Activate (Windows)
venv\Scripts\activate
```

#### 2. Install Dependencies

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

*Expected installation time*: 2-5 minutes

#### 3. Verify GPU Setup (Optional but Recommended)

```python
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

If CUDA is available, fine-tuning will be significantly faster. If not, training will use CPU (10-20x slower).


### Quick Run

#### Option A: Run Everything at Once (Recommended for First Time)

```bash
python run_all.py
```

This runs the complete pipeline:
1. Generates 1000 math problems
2. Splits into train/test sets
3. Fine-tunes GPT-2 (15-30 min on GPU)
4. Evaluates both models
5. Performs hypothesis testing

*Total time*: ~20-35 minutes with GPU, 2-4 hours with CPU

#### Option B: Run Step-by-Step

For more control or to inspect outputs:

```bash
## Step 1: Generate dataset
python scripts/1_generate_dataset.py

## Step 2: Prepare splits
python scripts/2_prepare_data.py

## Step 3: Fine-tune (this is the slow step)
python scripts/3_finetune_model.py

## Step 4: Evaluate
python scripts/4_evaluate_models.py

## Step 5: Test hypothesis
python scripts/5_test_hypothesis.py
```

*Expected Timeline:*
- Data generation: < 1 minute
- Data preparation: < 1 minute
- Fine-tuning: 15-30 minutes (GPU) or 2-4 hours (CPU)
- Evaluation: 5-10 minutes
- Hypothesis test: < 1 minute


### What to Expect

#### During Training (Step 3)

You'll see:
```
Training: [====>    ] 40%
Loss: 0.45 | Steps: 400/1000
```

*Note*: The first epoch is slowest due to model initialization.

#### Final Results (Step 5)

Expected output:
```
===========================================
HYPOTHESIS TEST RESULTS
===========================================

Accuracy Results:
  Baseline:     0.23 (23%)
  Fine-tuned:   0.87 (87%)
  Difference:   +0.64 (+64%)

Independent t-test:
  p-value:      0.0001

✓ REJECT NULL HYPOTHESIS
Fine-tuning SIGNIFICANTLY improves accuracy.
```


### Detailed Workflow

#### Phase 1: Data Generation

*Script*: `1_generate_dataset.py`

Generates a synthetic dataset of arithmetic problems with four operations:
- Addition (e.g., "23 + 45")
- Subtraction (e.g., "78 - 34")
- Multiplication (e.g., "12 * 8")
- Division (e.g., "96 / 8")

*Output*: `data/math_dataset.json`

#### Phase 2: Data Preparation

*Script*: `2_prepare_data.py`

Splits the dataset into:
- Training set (80%): Used for fine-tuning
- Test set (20%): Used for evaluation

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
- Accuracy: Percentage of correctly solved problems
- Exact Match: Whether the full output matches expected answer
- Per-Operation Breakdown: Accuracy by operation type

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
python scripts/1_generate_dataset.py [--num_problems N] [--max_value V]
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
- `--model_name`: Model to use (default: gpt2; e.g., gpt2-medium)

#### 4_evaluate_models.py

```bash
python scripts/4_evaluate_models.py [--model_path PATH] [--test_file FILE]
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

We want to determine if fine-tuning causes an improvement, not just correlates with it.

#### Methodology

1. Controlled Comparison: Same test set for both models
2. Statistical Rigor: Use p-values to measure significance
3. Effect Size: Quantify the magnitude of improvement

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
1. Training Logs: `logs/` - Monitor loss curves
2. Model Checkpoints: `fine_tuned_model/` - Saved model weights
3. Evaluation Results: `results/` - JSON files with metrics
4. Console Output: Real-time feedback during execution

#### Expected Improvements

Based on similar experiments:
- Baseline accuracy: 20-30% (random guessing level)
- Fine-tuned accuracy: 80-95% on simple arithmetic
- Significant p-value: < 0.001

#### Checking Results

##### View JSON Results

```bash
## Hypothesis test results
cat results/hypothesis_test.json

## Detailed evaluation
cat results/finetuned_results.json
```

##### View Training Logs (TensorBoard)

```bash
tensorboard --logdir logs/
## Open browser to http://localhost:6006
```


### Customisations and Advanced Usage

#### Change Dataset Size

```bash
## Generate 2000 problems instead of 1000
python scripts/1_generate_dataset.py --num_problems 2000
```

#### Adjust Training Parameters

```bash
## Train for more epochs
python scripts/3_finetune_model.py --epochs 5

## Use smaller batch size (for limited RAM)
python scripts/3_finetune_model.py --batch_size 4
```

#### Use Different Models

```bash
## Use GPT-2 Medium (355M parameters)
python scripts/3_finetune_model.py --model_name gpt2-medium
```

Larger models (e.g., gpt2-large, gpt2-xl) require more VRAM.

#### Custom Dataset

Replace `1_generate_dataset.py` with your own data in `data/math_dataset.json` format:
```json
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

#### Quick Command Reference

```bash
# Full pipeline with custom settings
python run_all.py --num_problems 2000 --epochs 5

# Skip already-completed steps
python run_all.py --skip_training --skip_generation

# View help for any script
python scripts/1_generate_dataset.py --help

# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"
```


### Troubleshooting

#### Out of Memory Error

*Solution*: Reduce batch size or use gradient accumulation.
```bash
python scripts/3_finetune_model.py --batch_size 4
```
Edit `3_finetune_model.py` and add: `gradient_accumulation_steps=2`

#### Import Errors

*Solution*: Reinstall dependencies
```bash
pip install --upgrade -r requirements.txt
```

#### Model Not Found After Training

*Check*: Verify the model was saved
```bash
ls -la fine_tuned_model/
# Should see: config.json, pytorch_model.bin, etc.
```

#### Poor Accuracy on Test Set

Possible causes:
1. Insufficient training: Increase epochs or data size
2. Data quality: Verify test set format matches training
3. Overfitting: Use validation set to monitor
4. Task difficulty: Start with simpler operations

### Next Steps

After your first successful run:
1. Experiment: Try different dataset sizes or operations
2. Analyze: Review sample predictions in results/
3. Optimize: Tune hyperparameters for better performance
4. Extend: Add more complex math problems (algebra, calculus)

### Notes and Best Practices

1. Always use a test set separate from training data
2. Monitor for overfitting by checking validation loss
3. Run multiple trials to ensure reproducibility
4. Document hyperparameters for each experiment
5. Version control your data and model checkpoints

### Success Checklist

After running the pipeline, you should have:
- [+] `data/math_dataset.json` - Generated problems
- [+] `data/train.json` and `data/test.json` - Splits
- [+] `fine_tuned_model/` directory - Trained model
- [+] `results/baseline_results.json` - Baseline evaluation
- [+] `results/finetuned_results.json` - Fine-tuned evaluation
- [+] `results/hypothesis_test.json` - Statistical test
- [+] `logs/` directory - Training logs

If all checkboxes are complete, congratulations! You've successfully fine-tuned GPT-2!

### Getting Help

1. Review [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for theoretical background
2. Inspect script outputs for error messages
3. Verify you're in the correct directory and environment

### Contributing / Extensions

To extend this project:
1. Add new problem types (algebra, calculus, etc.)
2. Implement additional evaluation metrics
3. Compare multiple model architectures
4. Add visualization tools for results

### References

- [Hugging Face Transformers Documentation](https://huggingface.co/docs/transformers)
- [GPT-2 Paper](https://openai.com/blog/better-language-models/)
- [Fine-tuning Best Practices](https://huggingface.co/docs/transformers/training)
- [Statistical Hypothesis Testing](https://en.wikipedia.org/wiki/Statistical_hypothesis_testing)
