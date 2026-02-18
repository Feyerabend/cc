

## Quick Start Guide

Get up and running with GPT-2 math fine-tuning in 5 minutes!

### Prerequisites

- Python 3.8+
- 8GB RAM minimum
- 10GB free disk space
- (Optional) CUDA-compatible GPU for faster training

### Installation

#### 1. Set Up Environment

```bash
## Create virtual environment
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

*Expected installation time*: 2-5 minutes

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

If you want more control or to inspect outputs between steps:

```bash
# Step 1: Generate dataset
python scripts/1_generate_dataset.py

# Step 2: Prepare splits
python scripts/2_prepare_data.py

# Step 3: Fine-tune (this is the slow step)
python scripts/3_finetune_model.py

# Step 4: Evaluate
python scripts/4_evaluate_models.py

# Step 5: Test hypothesis
python scripts/5_test_hypothesis.py
```

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

### Checking Results

#### View JSON Results

```bash
# Hypothesis test results
cat results/hypothesis_test.json

# Detailed evaluation
cat results/finetuned_results.json
```

#### View Training Logs (TensorBoard)

```bash
tensorboard --logdir logs/
# Open browser to http://localhost:6006
```

### Common Customizations

#### Change Dataset Size

```bash
# Generate 2000 problems instead of 1000
python scripts/1_generate_dataset.py --num_problems 2000
```

#### Adjust Training Parameters

```bash
# Train for more epochs
python scripts/3_finetune_model.py --epochs 5

# Use smaller batch size (for limited RAM)
python scripts/3_finetune_model.py --batch_size 4
```

#### Use Different Models

```bash
# Use GPT-2 Medium (355M parameters)
python scripts/3_finetune_model.py --model_name gpt2-medium
```

### Troubleshooting

#### Out of Memory Error

*Solution*: Reduce batch size
```bash
python scripts/3_finetune_model.py --batch_size 4
```

#### CUDA Not Available

*Impact*: Training will use CPU (10-20x slower)
*Solution*: This is fine for learning! Just expect longer training time.

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

### Next Steps

After your first successful run:

1. *Experiment*: Try different dataset sizes or operations
2. *Analyze*: Review sample predictions in results/
3. *Optimize*: Tune hyperparameters for better performance
4. *Extend*: Add more complex math problems (algebra, calculus)

### Quick Command Reference

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

### Getting Help

1. Check the main [README.md](README.md) for detailed documentation
2. Review [docs/methodology.md](docs/METHODOLOGY.md) for theoretical background
3. Inspect script outputs for error messages
4. Verify you're in the correct directory and environment

### Success Checklist

After running the pipeline, you should have:

- [x] `data/math_dataset.json` - Generated problems
- [x] `data/train.json` and `data/test.json` - Splits
- [x] `fine_tuned_model/` directory - Trained model
- [x] `results/baseline_results.json` - Baseline evaluation
- [x] `results/finetuned_results.json` - Fine-tuned evaluation
- [x] `results/hypothesis_test.json` - Statistical test
- [x] `logs/` directory - Training logs

If all checkboxes are complete, congratulations! You've successfully fine-tuned GPT-2!


*Estimated time to complete*: 30 minutes - 4 hours (depending on hardware)
*Difficulty level*: Intermediate
*Prerequisites*: Basic Python knowledge, understanding of machine learning concepts
