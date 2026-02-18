#!/usr/bin/env python3
"""
Master Script: Run Complete GPT-2 Math Fine-Tuning Pipeline

This script runs all steps of the pipeline in sequence:
1. Generate dataset
2. Prepare data
3. Fine-tune model
4. Evaluate models
5. Test hypothesis

Usage:
    python run_all.py [--num_problems N] [--epochs E]
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """
    Run a command and handle errors.
    
    Args:
        cmd (list): Command and arguments
        description (str): Step description
    """
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print('='*60)
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True, text=True)
        print(f"\n✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} failed with error code {e.returncode}")
        return False
    except KeyboardInterrupt:
        print(f"\n⚠ Pipeline interrupted by user")
        sys.exit(1)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Run complete GPT-2 math fine-tuning pipeline'
    )
    parser.add_argument(
        '--num_problems',
        type=int,
        default=1000,
        help='Number of problems to generate (default: 1000)'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=3,
        help='Number of training epochs (default: 3)'
    )
    parser.add_argument(
        '--batch_size',
        type=int,
        default=8,
        help='Training batch size (default: 8)'
    )
    parser.add_argument(
        '--skip_generation',
        action='store_true',
        help='Skip data generation if dataset already exists'
    )
    parser.add_argument(
        '--skip_preparation',
        action='store_true',
        help='Skip data preparation if splits already exist'
    )
    parser.add_argument(
        '--skip_training',
        action='store_true',
        help='Skip model training if model already exists'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("GPT-2 Math Fine-Tuning - Complete Pipeline")
    print("="*60)
    print(f"Configuration:")
    print(f"  Dataset size: {args.num_problems} problems")
    print(f"  Training epochs: {args.epochs}")
    print(f"  Batch size: {args.batch_size}")
    print("="*60)
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    steps = []
    
    # Step 1: Generate dataset
    if not args.skip_generation:
        steps.append((
            [sys.executable, 'scripts/1_generate_dataset.py', 
             '--num_problems', str(args.num_problems)],
            "Generate synthetic math dataset"
        ))
    else:
        print("\nSkipping dataset generation (--skip_generation)")
    
    # Step 2: Prepare data
    if not args.skip_preparation:
        steps.append((
            [sys.executable, 'scripts/2_prepare_data.py'],
            "Prepare training and test splits"
        ))
    else:
        print("Skipping data preparation (--skip_preparation)")
    
    # Step 3: Fine-tune model
    if not args.skip_training:
        steps.append((
            [sys.executable, 'scripts/3_finetune_model.py',
             '--epochs', str(args.epochs),
             '--batch_size', str(args.batch_size)],
            "Fine-tune GPT-2 model"
        ))
    else:
        print("Skipping model training (--skip_training)")
    
    # Step 4: Evaluate models
    steps.append((
        [sys.executable, 'scripts/4_evaluate_models.py'],
        "Evaluate baseline and fine-tuned models"
    ))
    
    # Step 5: Test hypothesis
    steps.append((
        [sys.executable, 'scripts/5_test_hypothesis.py'],
        "Perform statistical hypothesis testing"
    ))
    
    # Run all steps
    success_count = 0
    total_steps = len(steps)
    
    for i, (cmd, description) in enumerate(steps, 1):
        print(f"\n\n{'#'*60}")
        print(f"# PIPELINE STEP {i}/{total_steps}")
        print(f"{'#'*60}")
        
        if run_command(cmd, description):
            success_count += 1
        else:
            print(f"\n✗ Pipeline failed at step {i}/{total_steps}")
            print(f"Failed step: {description}")
            sys.exit(1)
    
    # Summary
    print(f"\n\n{'='*60}")
    print(f"PIPELINE COMPLETE")
    print('='*60)
    print(f"Successfully completed {success_count}/{total_steps} steps")
    print(f"\nResults are available in:")
    print(f"  - data/: Dataset and splits")
    print(f"  - fine_tuned_model/: Trained model")
    print(f"  - results/: Evaluation and hypothesis test results")
    print(f"  - logs/: Training logs")
    print(f"\nTo view training logs:")
    print(f"  tensorboard --logdir logs/")
    print(f"\nTo review hypothesis test results:")
    print(f"  cat results/hypothesis_test.json")
    print('='*60)


if __name__ == "__main__":
    main()
