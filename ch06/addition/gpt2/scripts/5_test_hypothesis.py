#!/usr/bin/env python3
"""
Script 5: Statistical Hypothesis Testing

This script performs statistical hypothesis testing to determine if fine-tuning
significantly improves model performance on mathematical reasoning tasks.

Null Hypothesis (H₀): Fine-tuning does not improve accuracy
Alternative Hypothesis (H₁): Fine-tuning improves accuracy

Usage:
    python 5_test_hypothesis.py [OPTIONS]

Output:
    results/hypothesis_test.json - Statistical test results
"""

import json
import argparse
import os
import numpy as np
from scipy import stats
from pathlib import Path


def load_results(filepath):
    """
    Load evaluation results from JSON file.
    
    Args:
        filepath (str): Path to results JSON
        
    Returns:
        dict: Evaluation results
    """
    print(f"Loading results from: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ Loaded results for {data.get('model_name', 'unknown model')}")
    print(f"  Accuracy: {data['accuracy']:.2%}")
    print(f"  Total samples: {data['total']}")
    
    return data


def create_binary_arrays(results):
    """
    Create binary arrays (0/1) for statistical testing.
    
    Args:
        results (dict): Evaluation results
        
    Returns:
        numpy.ndarray: Binary array where 1 = correct, 0 = incorrect
    """
    detailed = results['detailed_results']
    return np.array([1 if r['correct'] else 0 for r in detailed])


def perform_ttest(baseline_array, finetuned_array):
    """
    Perform independent t-test.
    
    Args:
        baseline_array (np.ndarray): Baseline binary results
        finetuned_array (np.ndarray): Fine-tuned binary results
        
    Returns:
        dict: Test statistics
    """
    print(f"\nPerforming independent t-test...")
    
    # Calculate statistics
    t_statistic, p_value = stats.ttest_ind(baseline_array, finetuned_array)
    
    # Calculate means and standard deviations
    baseline_mean = np.mean(baseline_array)
    finetuned_mean = np.mean(finetuned_array)
    baseline_std = np.std(baseline_array, ddof=1)
    finetuned_std = np.std(finetuned_array, ddof=1)
    
    return {
        'test_name': 'Independent t-test',
        't_statistic': float(t_statistic),
        'p_value': float(p_value),
        'baseline_mean': float(baseline_mean),
        'finetuned_mean': float(finetuned_mean),
        'baseline_std': float(baseline_std),
        'finetuned_std': float(finetuned_std)
    }


def calculate_effect_size(baseline_array, finetuned_array):
    """
    Calculate Cohen's d effect size.
    
    Args:
        baseline_array (np.ndarray): Baseline binary results
        finetuned_array (np.ndarray): Fine-tuned binary results
        
    Returns:
        dict: Effect size statistics
    """
    print(f"Calculating effect size (Cohen's d)...")
    
    # Calculate means
    mean1 = np.mean(baseline_array)
    mean2 = np.mean(finetuned_array)
    
    # Calculate pooled standard deviation
    n1 = len(baseline_array)
    n2 = len(finetuned_array)
    var1 = np.var(baseline_array, ddof=1)
    var2 = np.var(finetuned_array, ddof=1)
    
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    # Calculate Cohen's d
    cohens_d = (mean2 - mean1) / pooled_std if pooled_std > 0 else 0
    
    # Interpret effect size
    if abs(cohens_d) < 0.2:
        interpretation = "negligible"
    elif abs(cohens_d) < 0.5:
        interpretation = "small"
    elif abs(cohens_d) < 0.8:
        interpretation = "medium"
    else:
        interpretation = "large"
    
    return {
        'cohens_d': float(cohens_d),
        'interpretation': interpretation
    }


def perform_mannwhitney(baseline_array, finetuned_array):
    """
    Perform Mann-Whitney U test (non-parametric alternative to t-test).
    
    Args:
        baseline_array (np.ndarray): Baseline binary results
        finetuned_array (np.ndarray): Fine-tuned binary results
        
    Returns:
        dict: Test statistics
    """
    print(f"Performing Mann-Whitney U test...")
    
    u_statistic, p_value = stats.mannwhitneyu(
        baseline_array,
        finetuned_array,
        alternative='less'  # Testing if baseline < finetuned
    )
    
    return {
        'test_name': 'Mann-Whitney U test',
        'u_statistic': float(u_statistic),
        'p_value': float(p_value)
    }


def bootstrap_confidence_interval(baseline_array, finetuned_array, n_bootstrap=10000, confidence=0.95):
    """
    Calculate bootstrap confidence interval for the difference in means.
    
    Args:
        baseline_array (np.ndarray): Baseline binary results
        finetuned_array (np.ndarray): Fine-tuned binary results
        n_bootstrap (int): Number of bootstrap samples
        confidence (float): Confidence level
        
    Returns:
        dict: Bootstrap statistics
    """
    print(f"Computing bootstrap confidence interval ({n_bootstrap} samples)...")
    
    differences = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        baseline_sample = np.random.choice(baseline_array, size=len(baseline_array), replace=True)
        finetuned_sample = np.random.choice(finetuned_array, size=len(finetuned_array), replace=True)
        
        # Calculate difference in means
        diff = np.mean(finetuned_sample) - np.mean(baseline_sample)
        differences.append(diff)
    
    differences = np.array(differences)
    
    # Calculate confidence interval
    alpha = 1 - confidence
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    ci_lower = np.percentile(differences, lower_percentile)
    ci_upper = np.percentile(differences, upper_percentile)
    
    return {
        'method': 'Bootstrap',
        'n_samples': n_bootstrap,
        'confidence_level': confidence,
        'mean_difference': float(np.mean(differences)),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper)
    }


def test_hypothesis(baseline_results, finetuned_results, alpha=0.05):
    """
    Perform complete hypothesis testing.
    
    Args:
        baseline_results (dict): Baseline evaluation results
        finetuned_results (dict): Fine-tuned evaluation results
        alpha (float): Significance level
        
    Returns:
        dict: Complete test results
    """
    print(f"\n{'='*60}")
    print("Statistical Hypothesis Testing")
    print('='*60)
    print(f"Significance level (α): {alpha}")
    
    # Create binary arrays
    baseline_array = create_binary_arrays(baseline_results)
    finetuned_array = create_binary_arrays(finetuned_results)
    
    print(f"\nSample sizes:")
    print(f"  Baseline: {len(baseline_array)}")
    print(f"  Fine-tuned: {len(finetuned_array)}")
    
    # Perform tests
    ttest_results = perform_ttest(baseline_array, finetuned_array)
    effect_size = calculate_effect_size(baseline_array, finetuned_array)
    mannwhitney_results = perform_mannwhitney(baseline_array, finetuned_array)
    bootstrap_results = bootstrap_confidence_interval(baseline_array, finetuned_array)
    
    # Determine hypothesis test decision
    reject_null = ttest_results['p_value'] < alpha
    
    # Compile results
    results = {
        'hypothesis_test': {
            'null_hypothesis': 'Fine-tuning does not improve accuracy',
            'alternative_hypothesis': 'Fine-tuning improves accuracy',
            'significance_level': alpha,
            'decision': 'Reject H₀' if reject_null else 'Fail to reject H₀',
            'reject_null': reject_null
        },
        'baseline_accuracy': baseline_results['accuracy'],
        'finetuned_accuracy': finetuned_results['accuracy'],
        'accuracy_difference': finetuned_results['accuracy'] - baseline_results['accuracy'],
        'statistical_tests': {
            'ttest': ttest_results,
            'mannwhitney': mannwhitney_results,
            'effect_size': effect_size,
            'bootstrap_ci': bootstrap_results
        }
    }
    
    return results


def display_results(results):
    """
    Display hypothesis test results in a formatted way.
    
    Args:
        results (dict): Hypothesis test results
    """
    print(f"\n{'='*60}")
    print("HYPOTHESIS TEST RESULTS")
    print('='*60)
    
    # Display hypotheses
    print(f"\nNull Hypothesis (H₀): {results['hypothesis_test']['null_hypothesis']}")
    print(f"Alternative Hypothesis (H₁): {results['hypothesis_test']['alternative_hypothesis']}")
    
    # Display accuracies
    print(f"\n{'Accuracy Results:'}")
    print(f"  Baseline:     {results['baseline_accuracy']:.4f} ({results['baseline_accuracy']:.2%})")
    print(f"  Fine-tuned:   {results['finetuned_accuracy']:.4f} ({results['finetuned_accuracy']:.2%})")
    print(f"  Difference:   {results['accuracy_difference']:+.4f} ({results['accuracy_difference']:+.2%})")
    
    # Display t-test results
    ttest = results['statistical_tests']['ttest']
    print(f"\n{'Independent t-test:'}")
    print(f"  t-statistic:  {ttest['t_statistic']:.4f}")
    print(f"  p-value:      {ttest['p_value']:.6f}")
    
    # Display Mann-Whitney results
    mw = results['statistical_tests']['mannwhitney']
    print(f"\n{'Mann-Whitney U test:'}")
    print(f"  U-statistic:  {mw['u_statistic']:.4f}")
    print(f"  p-value:      {mw['p_value']:.6f}")
    
    # Display effect size
    effect = results['statistical_tests']['effect_size']
    effect_title = "Effect Size (Cohen's d):"
    print(f"\n{effect_title}")
    print(f"  Cohen's d:    {effect['cohens_d']:.4f}")
    print(f"  Interpretation: {effect['interpretation'].upper()}")
    
    # Display bootstrap CI
    bootstrap = results['statistical_tests']['bootstrap_ci']
    print(f"\n{'Bootstrap Confidence Interval:'}")
    print(f"  Confidence:   {bootstrap['confidence_level']:.1%}")
    print(f"  Mean diff:    {bootstrap['mean_difference']:.4f}")
    print(f"  95% CI:       [{bootstrap['ci_lower']:.4f}, {bootstrap['ci_upper']:.4f}]")
    
    # Display decision
    print(f"\n{'='*60}")
    print(f"DECISION (α = {results['hypothesis_test']['significance_level']}):")
    print('='*60)
    
    decision = results['hypothesis_test']['decision']
    reject = results['hypothesis_test']['reject_null']
    
    if reject:
        print(f"✓ {decision}")
        print(f"\nConclusion: Fine-tuning SIGNIFICANTLY improves accuracy.")
        print(f"The improvement is unlikely due to chance (p < {results['hypothesis_test']['significance_level']}).")
    else:
        print(f"✗ {decision}")
        print(f"\nConclusion: No significant evidence that fine-tuning improves accuracy.")
        print(f"The observed difference could be due to chance (p ≥ {results['hypothesis_test']['significance_level']}).")
    
    print('='*60)


def save_results(results, output_path):
    """
    Save hypothesis test results to JSON.
    
    Args:
        results (dict): Test results
        output_path (str): Output file path
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Results saved to: {output_path}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Perform statistical hypothesis testing on model results'
    )
    parser.add_argument(
        '--baseline_results',
        type=str,
        default='results/baseline_results.json',
        help='Baseline results file (default: results/baseline_results.json)'
    )
    parser.add_argument(
        '--finetuned_results',
        type=str,
        default='results/finetuned_results.json',
        help='Fine-tuned results file (default: results/finetuned_results.json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/hypothesis_test.json',
        help='Output file for test results (default: results/hypothesis_test.json)'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.05,
        help='Significance level (default: 0.05)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("Hypothesis Testing: Fine-Tuning Effect on Math Performance")
    print("="*60)
    
    # Load results
    print(f"\nLoading evaluation results...")
    baseline_results = load_results(args.baseline_results)
    finetuned_results = load_results(args.finetuned_results)
    
    # Perform hypothesis testing
    test_results = test_hypothesis(
        baseline_results,
        finetuned_results,
        alpha=args.alpha
    )
    
    # Display results
    display_results(test_results)
    
    # Save results
    save_results(test_results, args.output)
    
    print("\n" + "="*60)
    print("✓ Hypothesis testing complete!")
    print("="*60)
    print(f"\nAll results saved in: results/")
    print(f"\nExperiment complete! Review the results to understand:")
    print(f"  1. Whether fine-tuning significantly improves performance")
    print(f"  2. The magnitude of the improvement (effect size)")
    print(f"  3. The statistical confidence in the results")


if __name__ == "__main__":
    main()
