#!/usr/bin/env python3
"""
Script 1: Generate Synthetic Math Dataset

This script generates a synthetic dataset of arithmetic problems including
addition, subtraction, multiplication, and division operations.

Usage:
    python 1_generate_dataset.py [--num_problems N] [--max_value M]

Output:
    data/math_dataset.json - JSON file with problem-solution pairs
"""

import random
import json
import argparse
import os
from pathlib import Path


def generate_math_problems(num_problems=1000, max_value=100):
    """
    Generate arithmetic problems with random operands and operations.
    
    Args:
        num_problems (int): Number of problems to generate
        max_value (int): Maximum value for operands
        
    Returns:
        list: List of dictionaries with 'problem' and 'solution' keys
    """
    problems = []
    operations = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: a / b
    }
    
    print(f"Generating {num_problems} math problems...")
    
    for i in range(num_problems):
        # Randomly choose an operation
        operation = random.choice(list(operations.keys()))
        a = random.randint(1, max_value)
        b = random.randint(1, max_value)
        
        # Special handling for division to ensure integer results
        if operation == "/":
            # Make a divisible by b for cleaner results
            b = random.randint(1, 20)  # Keep divisor smaller
            a = b * random.randint(1, max_value // 20)
        
        # Calculate solution
        solution = operations[operation](a, b)
        
        # Format as integer if possible
        if isinstance(solution, float) and solution.is_integer():
            solution = int(solution)
        
        # Create problem dictionary
        problem_dict = {
            "problem": f"{a} {operation} {b}",
            "solution": solution,
            "operation": operation,
            "operands": [a, b]
        }
        
        problems.append(problem_dict)
        
        # Progress indicator
        if (i + 1) % 100 == 0:
            print(f"  Generated {i + 1}/{num_problems} problems")
    
    print(f"✓ Successfully generated {len(problems)} problems")
    return problems


def save_dataset(problems, output_path):
    """
    Save the generated dataset to a JSON file.
    
    Args:
        problems (list): List of problem dictionaries
        output_path (str): Path to save the JSON file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(problems, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Dataset saved to: {output_path}")


def display_sample(problems, num_samples=5):
    """
    Display a sample of generated problems.
    
    Args:
        problems (list): List of problem dictionaries
        num_samples (int): Number of samples to display
    """
    print(f"\n{'='*60}")
    print(f"Sample of {num_samples} generated problems:")
    print('='*60)
    
    samples = random.sample(problems, min(num_samples, len(problems)))
    for i, prob in enumerate(samples, 1):
        print(f"{i}. Problem: {prob['problem']}")
        print(f"   Solution: {prob['solution']}")
        print(f"   Operation: {prob['operation']}")
        print()


def get_statistics(problems):
    """
    Calculate and display dataset statistics.
    
    Args:
        problems (list): List of problem dictionaries
    """
    operations = {}
    for prob in problems:
        op = prob['operation']
        operations[op] = operations.get(op, 0) + 1
    
    print(f"\n{'='*60}")
    print("Dataset Statistics:")
    print('='*60)
    print(f"Total problems: {len(problems)}")
    print(f"\nBreakdown by operation:")
    for op, count in sorted(operations.items()):
        percentage = (count / len(problems)) * 100
        print(f"  {op:>10}: {count:>4} ({percentage:>5.1f}%)")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Generate synthetic math dataset for GPT-2 fine-tuning'
    )
    parser.add_argument(
        '--num_problems',
        type=int,
        default=1000,
        help='Number of problems to generate (default: 1000)'
    )
    parser.add_argument(
        '--max_value',
        type=int,
        default=100,
        help='Maximum value for operands (default: 100)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/math_dataset.json',
        help='Output file path (default: data/math_dataset.json)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("Math Dataset Generator")
    print("="*60)
    print(f"Configuration:")
    print(f"  Number of problems: {args.num_problems}")
    print(f"  Max operand value: {args.max_value}")
    print(f"  Output path: {args.output}")
    print("="*60 + "\n")
    
    # Generate dataset
    problems = generate_math_problems(
        num_problems=args.num_problems,
        max_value=args.max_value
    )
    
    # Display statistics
    get_statistics(problems)
    
    # Display samples
    display_sample(problems, num_samples=5)
    
    # Save dataset
    save_dataset(problems, args.output)
    
    print("\n" + "="*60)
    print("✓ Dataset generation complete!")
    print("="*60)
    print(f"\nNext step: Run 'python scripts/2_prepare_data.py'")


if __name__ == "__main__":
    main()
