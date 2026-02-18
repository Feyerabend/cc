#!/usr/bin/env python3
"""
Script 4: Evaluate Models

This script evaluates both the baseline GPT-2 and the fine-tuned model
on the test set, comparing their performance on mathematical reasoning.

Usage:
    python 4_evaluate_models.py [OPTIONS]

Output:
    results/baseline_results.json - Baseline model performance
    results/finetuned_results.json - Fine-tuned model performance
"""

import json
import argparse
import os
import re
from pathlib import Path
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from tqdm import tqdm


def load_model_and_tokenizer(model_path):
    """
    Load a GPT-2 model and tokenizer.
    
    Args:
        model_path (str): Path to model or model identifier
        
    Returns:
        tuple: (model, tokenizer)
    """
    print(f"Loading model from: {model_path}")
    
    tokenizer = GPT2Tokenizer.from_pretrained(model_path)
    model = GPT2LMHeadModel.from_pretrained(model_path)
    
    # Set pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Move to GPU if available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    model.eval()  # Set to evaluation mode
    
    print(f"✓ Model loaded on {device}")
    
    return model, tokenizer, device


def load_test_data(test_path):
    """
    Load test dataset.
    
    Args:
        test_path (str): Path to test JSON file
        
    Returns:
        list: Test samples
    """
    print(f"Loading test data from: {test_path}")
    
    with open(test_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ Loaded {len(data)} test samples")
    return data


def extract_answer(generated_text, prompt):
    """
    Extract the numeric answer from generated text.
    
    Args:
        generated_text (str): Full generated text
        prompt (str): Original prompt
        
    Returns:
        str: Extracted answer or None
    """
    # Remove the prompt from generated text
    if prompt in generated_text:
        answer_part = generated_text[len(prompt):].strip()
    else:
        answer_part = generated_text.strip()
    
    # Try to extract the first number after "A:"
    if "A:" in answer_part:
        answer_part = answer_part.split("A:", 1)[1].strip()
    
    # Extract numbers (including decimals)
    numbers = re.findall(r'-?\d+\.?\d*', answer_part)
    
    if numbers:
        return numbers[0]
    
    return None


def evaluate_single(model, tokenizer, device, test_item, max_length=50):
    """
    Evaluate model on a single test item.
    
    Args:
        model: GPT-2 model
        tokenizer: GPT-2 tokenizer
        device: torch device
        test_item (dict): Test sample with 'text' field
        max_length (int): Maximum generation length
        
    Returns:
        dict: Evaluation results
    """
    # Get the question part (before "A:")
    text = test_item['text']
    if "A:" in text:
        question, answer = text.split("A:", 1)
        question = question.strip()
        ground_truth = answer.strip()
    else:
        return None
    
    # Generate prediction
    inputs = tokenizer(question, return_tensors="pt", padding=True).to(device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            num_return_sequences=1,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=False,  # Deterministic generation
            temperature=1.0,
        )
    
    # Decode output
    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract predicted answer
    predicted = extract_answer(generated, question)
    
    # Check correctness
    is_correct = False
    if predicted is not None:
        try:
            pred_float = float(predicted)
            true_float = float(ground_truth)
            is_correct = abs(pred_float - true_float) < 0.01  # Allow small floating point errors
        except ValueError:
            is_correct = predicted == ground_truth
    
    return {
        'question': question,
        'ground_truth': ground_truth,
        'generated': generated,
        'predicted': predicted,
        'correct': is_correct
    }


def evaluate_model(model, tokenizer, device, test_data, model_name):
    """
    Evaluate model on entire test set.
    
    Args:
        model: GPT-2 model
        tokenizer: GPT-2 tokenizer
        device: torch device
        test_data (list): Test dataset
        model_name (str): Name for logging
        
    Returns:
        dict: Evaluation results and statistics
    """
    print(f"\n{'='*60}")
    print(f"Evaluating {model_name}")
    print('='*60)
    
    results = []
    correct_count = 0
    total_count = 0
    operation_stats = {'+': {'correct': 0, 'total': 0},
                      '-': {'correct': 0, 'total': 0},
                      '*': {'correct': 0, 'total': 0},
                      '/': {'correct': 0, 'total': 0}}
    
    # Evaluate each test item
    for item in tqdm(test_data, desc=f"Evaluating {model_name}"):
        result = evaluate_single(model, tokenizer, device, item)
        
        if result is None:
            continue
        
        results.append(result)
        total_count += 1
        
        if result['correct']:
            correct_count += 1
        
        # Track by operation
        question = result['question']
        for op in ['+', '-', '*', '/']:
            if op in question:
                operation_stats[op]['total'] += 1
                if result['correct']:
                    operation_stats[op]['correct'] += 1
                break
    
    # Calculate statistics
    accuracy = correct_count / total_count if total_count > 0 else 0
    
    print(f"\nResults:")
    print(f"  Total questions: {total_count}")
    print(f"  Correct: {correct_count}")
    print(f"  Accuracy: {accuracy:.2%}")
    
    print(f"\nAccuracy by operation:")
    for op, stats in sorted(operation_stats.items()):
        if stats['total'] > 0:
            op_acc = stats['correct'] / stats['total']
            print(f"  {op}: {op_acc:.2%} ({stats['correct']}/{stats['total']})")
    
    return {
        'model_name': model_name,
        'accuracy': accuracy,
        'correct': correct_count,
        'total': total_count,
        'operation_stats': operation_stats,
        'detailed_results': results
    }


def save_results(results, output_path):
    """
    Save evaluation results to JSON.
    
    Args:
        results (dict): Evaluation results
        output_path (str): Output file path
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Results saved to: {output_path}")


def display_sample_predictions(results, num_samples=5):
    """
    Display sample predictions for inspection.
    
    Args:
        results (dict): Evaluation results
        num_samples (int): Number of samples to display
    """
    detailed = results['detailed_results']
    
    # Show some correct predictions
    correct = [r for r in detailed if r['correct']]
    incorrect = [r for r in detailed if not r['correct']]
    
    print(f"\n{'='*60}")
    print(f"Sample Correct Predictions ({len(correct)} total):")
    print('='*60)
    
    for i, result in enumerate(correct[:num_samples], 1):
        print(f"{i}. {result['question']}")
        print(f"   Ground truth: {result['ground_truth']}")
        print(f"   Predicted: {result['predicted']}")
        print()
    
    print(f"{'='*60}")
    print(f"Sample Incorrect Predictions ({len(incorrect)} total):")
    print('='*60)
    
    for i, result in enumerate(incorrect[:num_samples], 1):
        print(f"{i}. {result['question']}")
        print(f"   Ground truth: {result['ground_truth']}")
        print(f"   Predicted: {result['predicted']}")
        print(f"   Full output: {result['generated']}")
        print()


def compare_models(baseline_results, finetuned_results):
    """
    Compare baseline and fine-tuned model performance.
    
    Args:
        baseline_results (dict): Baseline evaluation results
        finetuned_results (dict): Fine-tuned evaluation results
    """
    print(f"\n{'='*60}")
    print("Model Comparison")
    print('='*60)
    
    baseline_acc = baseline_results['accuracy']
    finetuned_acc = finetuned_results['accuracy']
    improvement = finetuned_acc - baseline_acc
    
    print(f"\nOverall Accuracy:")
    print(f"  Baseline:    {baseline_acc:.2%}")
    print(f"  Fine-tuned:  {finetuned_acc:.2%}")
    print(f"  Improvement: {improvement:+.2%}")
    
    print(f"\nAccuracy by Operation:")
    print(f"{'Operation':<12} {'Baseline':<12} {'Fine-tuned':<12} {'Improvement':<12}")
    print('-' * 48)
    
    for op in ['+', '-', '*', '/']:
        base_stats = baseline_results['operation_stats'][op]
        fine_stats = finetuned_results['operation_stats'][op]
        
        if base_stats['total'] > 0 and fine_stats['total'] > 0:
            base_acc = base_stats['correct'] / base_stats['total']
            fine_acc = fine_stats['correct'] / fine_stats['total']
            imp = fine_acc - base_acc
            
            print(f"{op:<12} {base_acc:<12.2%} {fine_acc:<12.2%} {imp:+<12.2%}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Evaluate GPT-2 models on math test set'
    )
    parser.add_argument(
        '--test_file',
        type=str,
        default='data/test.json',
        help='Test data file (default: data/test.json)'
    )
    parser.add_argument(
        '--baseline_model',
        type=str,
        default='gpt2',
        help='Baseline model (default: gpt2)'
    )
    parser.add_argument(
        '--finetuned_model',
        type=str,
        default='./fine_tuned_model',
        help='Fine-tuned model path (default: ./fine_tuned_model)'
    )
    parser.add_argument(
        '--baseline_output',
        type=str,
        default='results/baseline_results.json',
        help='Baseline results output (default: results/baseline_results.json)'
    )
    parser.add_argument(
        '--finetuned_output',
        type=str,
        default='results/finetuned_results.json',
        help='Fine-tuned results output (default: results/finetuned_results.json)'
    )
    parser.add_argument(
        '--max_length',
        type=int,
        default=50,
        help='Maximum generation length (default: 50)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("Model Evaluation on Math Test Set")
    print("="*60)
    print(f"Test file: {args.test_file}")
    print(f"Baseline model: {args.baseline_model}")
    print(f"Fine-tuned model: {args.finetuned_model}")
    print("="*60)
    
    # Load test data
    test_data = load_test_data(args.test_file)
    
    # Evaluate baseline model
    print("\n" + "="*60)
    print("BASELINE MODEL EVALUATION")
    print("="*60)
    baseline_model, baseline_tokenizer, device = load_model_and_tokenizer(args.baseline_model)
    baseline_results = evaluate_model(
        baseline_model,
        baseline_tokenizer,
        device,
        test_data,
        "Baseline GPT-2"
    )
    save_results(baseline_results, args.baseline_output)
    display_sample_predictions(baseline_results, num_samples=3)
    
    # Clear memory
    del baseline_model
    del baseline_tokenizer
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    
    # Evaluate fine-tuned model
    print("\n" + "="*60)
    print("FINE-TUNED MODEL EVALUATION")
    print("="*60)
    finetuned_model, finetuned_tokenizer, device = load_model_and_tokenizer(args.finetuned_model)
    finetuned_results = evaluate_model(
        finetuned_model,
        finetuned_tokenizer,
        device,
        test_data,
        "Fine-tuned GPT-2"
    )
    save_results(finetuned_results, args.finetuned_output)
    display_sample_predictions(finetuned_results, num_samples=3)
    
    # Compare models
    compare_models(baseline_results, finetuned_results)
    
    print("\n" + "="*60)
    print("✓ Evaluation complete!")
    print("="*60)
    print(f"\nResults saved:")
    print(f"  Baseline: {args.baseline_output}")
    print(f"  Fine-tuned: {args.finetuned_output}")
    print(f"\nNext step: Run 'python scripts/5_test_hypothesis.py'")


if __name__ == "__main__":
    main()
