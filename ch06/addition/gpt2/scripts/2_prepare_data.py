#!/usr/bin/env python3
"""
Script 2: Prepare Data for Training

This script splits the generated dataset into training and test sets,
and formats them for use with Hugging Face's Trainer API.

Usage:
    python 2_prepare_data.py [--train_split RATIO]

Output:
    data/train.json - Training dataset
    data/test.json - Test dataset
"""

import json
import argparse
import random
from pathlib import Path


def load_dataset(input_path):
    """
    Load the generated math dataset.
    
    Args:
        input_path (str): Path to the input JSON file
        
    Returns:
        list: List of problem dictionaries
    """
    print(f"Loading dataset from: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ Loaded {len(data)} problems")
    return data


def format_for_training(problems):
    """
    Format problems for language model training.
    
    Each problem is formatted as: "Q: {problem} A: {solution}"
    
    Args:
        problems (list): List of problem dictionaries
        
    Returns:
        list: Formatted text samples
    """
    formatted = []
    
    for prob in problems:
        # Format: "Q: 5 + 3 A: 8"
        text = f"Q: {prob['problem']} A: {prob['solution']}"
        formatted.append({"text": text})
    
    return formatted


def split_dataset(data, train_ratio=0.8, seed=42):
    """
    Split dataset into training and test sets.
    
    Args:
        data (list): Full dataset
        train_ratio (float): Proportion for training set
        seed (int): Random seed for reproducibility
        
    Returns:
        tuple: (train_data, test_data)
    """
    random.seed(seed)
    
    # Shuffle data
    shuffled = data.copy()
    random.shuffle(shuffled)
    
    # Calculate split index
    split_idx = int(len(shuffled) * train_ratio)
    
    # Split
    train_data = shuffled[:split_idx]
    test_data = shuffled[split_idx:]
    
    print(f"\nDataset split:")
    print(f"  Training samples: {len(train_data)} ({train_ratio*100:.0f}%)")
    print(f"  Test samples: {len(test_data)} ({(1-train_ratio)*100:.0f}%)")
    
    return train_data, test_data


def save_split(data, output_path, split_name):
    """
    Save a dataset split to JSON file.
    
    Args:
        data (list): Dataset split
        output_path (str): Output file path
        split_name (str): Name of the split (for logging)
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ {split_name} set saved to: {output_path}")


def display_samples(train_data, test_data, num_samples=3):
    """
    Display sample problems from both splits.
    
    Args:
        train_data (list): Training dataset
        test_data (list): Test dataset
        num_samples (int): Number of samples to display per split
    """
    print(f"\n{'='*60}")
    print("Sample Training Examples:")
    print('='*60)
    
    for i, sample in enumerate(random.sample(train_data, min(num_samples, len(train_data))), 1):
        print(f"{i}. {sample['text']}")
    
    print(f"\n{'='*60}")
    print("Sample Test Examples:")
    print('='*60)
    
    for i, sample in enumerate(random.sample(test_data, min(num_samples, len(test_data))), 1):
        print(f"{i}. {sample['text']}")


def verify_no_overlap(train_data, test_data):
    """
    Verify there's no data leakage between train and test sets.
    
    Args:
        train_data (list): Training dataset
        test_data (list): Test dataset
        
    Returns:
        bool: True if no overlap, False otherwise
    """
    train_problems = {item['text'] for item in train_data}
    test_problems = {item['text'] for item in test_data}
    
    overlap = train_problems & test_problems
    
    if overlap:
        print(f"\n⚠ WARNING: Found {len(overlap)} overlapping problems!")
        print("Sample overlaps:", list(overlap)[:3])
        return False
    else:
        print(f"\n✓ No overlap between training and test sets")
        return True


def get_split_statistics(train_data, test_data):
    """
    Calculate statistics for each split.
    
    Args:
        train_data (list): Training dataset
        test_data (list): Test dataset
    """
    def count_operations(data):
        """Count problems by operation type."""
        ops = {}
        for item in data:
            # Extract operation from text
            text = item['text']
            for op in ['+', '-', '*', '/']:
                if op in text:
                    ops[op] = ops.get(op, 0) + 1
                    break
        return ops
    
    train_ops = count_operations(train_data)
    test_ops = count_operations(test_data)
    
    print(f"\n{'='*60}")
    print("Split Statistics:")
    print('='*60)
    
    print("\nTraining Set Operations:")
    for op, count in sorted(train_ops.items()):
        percentage = (count / len(train_data)) * 100
        print(f"  {op:>10}: {count:>4} ({percentage:>5.1f}%)")
    
    print("\nTest Set Operations:")
    for op, count in sorted(test_ops.items()):
        percentage = (count / len(test_data)) * 100
        print(f"  {op:>10}: {count:>4} ({percentage:>5.1f}%)")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Prepare math dataset for GPT-2 fine-tuning'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/math_dataset.json',
        help='Input dataset path (default: data/math_dataset.json)'
    )
    parser.add_argument(
        '--train_split',
        type=float,
        default=0.8,
        help='Training set ratio (default: 0.8)'
    )
    parser.add_argument(
        '--train_output',
        type=str,
        default='data/train.json',
        help='Training set output path (default: data/train.json)'
    )
    parser.add_argument(
        '--test_output',
        type=str,
        default='data/test.json',
        help='Test set output path (default: data/test.json)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("Data Preparation for Training")
    print("="*60)
    print(f"Configuration:")
    print(f"  Input file: {args.input}")
    print(f"  Train/Test split: {args.train_split:.1%}/{1-args.train_split:.1%}")
    print(f"  Random seed: {args.seed}")
    print("="*60 + "\n")
    
    # Load dataset
    problems = load_dataset(args.input)
    
    # Format for training
    print("\nFormatting problems for language model training...")
    formatted_data = format_for_training(problems)
    print(f"✓ Formatted {len(formatted_data)} problems")
    
    # Split dataset
    train_data, test_data = split_dataset(
        formatted_data,
        train_ratio=args.train_split,
        seed=args.seed
    )
    
    # Verify no overlap
    verify_no_overlap(train_data, test_data)
    
    # Get statistics
    get_split_statistics(train_data, test_data)
    
    # Display samples
    display_samples(train_data, test_data, num_samples=3)
    
    # Save splits
    print(f"\n{'='*60}")
    print("Saving dataset splits...")
    print('='*60)
    save_split(train_data, args.train_output, "Training")
    save_split(test_data, args.test_output, "Test")
    
    print("\n" + "="*60)
    print("✓ Data preparation complete!")
    print("="*60)
    print(f"\nDataset ready for training:")
    print(f"  Training: {args.train_output}")
    print(f"  Test: {args.test_output}")
    print(f"\nNext step: Run 'python scripts/3_finetune_model.py'")


if __name__ == "__main__":
    main()
