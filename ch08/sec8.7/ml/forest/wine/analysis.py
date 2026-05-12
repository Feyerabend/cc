import pandas as pd
import numpy as np
from collections import Counter

def analyze_predictions(csv_file='predictions.csv'):    
    print("Random Forest Predictions Analysis")
    print("=" * 50)

    # predictions data
    try:
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} predictions from {csv_file}")
    except FileNotFoundError:
        print(f"Error: Could not find {csv_file}")
        return None
    
    # accuracy calculation
    correct_predictions = (df['true_quality'] == df['predicted_quality']).sum()
    total_predictions = len(df)
    accuracy = correct_predictions / total_predictions
    
    print(f"\nOverall Results:")
    print(f"Accuracy: {accuracy:.3f} ({correct_predictions}/{total_predictions})")
    
    # distribution analysis
    true_dist = df['true_quality'].value_counts().sort_index()
    pred_dist = df['predicted_quality'].value_counts().sort_index()
    
    print(f"\nTrue quality distribution:")
    for quality, count in true_dist.items():
        print(f"  Quality {quality}: {count} samples")
    
    print(f"\nPredicted quality distribution:")
    for quality, count in pred_dist.items():
        print(f"  Quality {quality}: {count} samples")
    
    # confidence analysis
    confidence_stats = df['prediction_confidence'].describe()
    print(f"\nConfidence analysis:")
    print(f"  Average confidence: {confidence_stats['mean']:.3f}")
    print(f"  Min confidence: {confidence_stats['min']:.3f}")
    print(f"  Max confidence: {confidence_stats['max']:.3f}")
    print(f"  Std deviation: {confidence_stats['std']:.3f}")
    
    # accuracy by quality level
    print(f"\nAccuracy by quality level:")
    quality_accuracy = {}
    
    for quality in sorted(df['true_quality'].unique()):
        quality_mask = df['true_quality'] == quality
        quality_df = df[quality_mask]
        
        correct = (quality_df['true_quality'] == quality_df['predicted_quality']).sum()
        total = len(quality_df)
        acc_rate = correct / total if total > 0 else 0
        
        quality_accuracy[quality] = {'correct': correct, 'total': total, 'rate': acc_rate}
        print(f"  Quality {quality}: {acc_rate:.3f} ({correct}/{total})")
    
    # Off-by-one analysis (important for ordinal data like quality ratings)
    df['prediction_error'] = abs(df['true_quality'] - df['predicted_quality'])
    off_by_one = (df['prediction_error'] == 1).sum()
    off_by_one_pct = off_by_one / total_predictions * 100
    
    exact_plus_close = correct_predictions + off_by_one
    close_accuracy = exact_plus_close / total_predictions
    
    print(f"\nOrdinal accuracy analysis:")
    print(f"  Off-by-one predictions: {off_by_one} ({off_by_one_pct:.1f}%)")
    print(f"  Exact + off-by-one accuracy: {close_accuracy:.3f}")
    
    # error distribution
    error_dist = df['prediction_error'].value_counts().sort_index()
    print(f"\nPrediction error distribution:")
    for error, count in error_dist.items():
        print(f"  Error {error}: {count} predictions ({count/total_predictions*100:.1f}%)")
    
    # confidence calibration analysis
    correct_mask = df['true_quality'] == df['predicted_quality']
    correct_conf = df[correct_mask]['prediction_confidence'].mean()
    incorrect_conf = df[~correct_mask]['prediction_confidence'].mean()
    confidence_gap = correct_conf - incorrect_conf
    
    print(f"\nConfidence calibration:")
    print(f"  Average confidence for correct predictions: {correct_conf:.3f}")
    print(f"  Average confidence for incorrect predictions: {incorrect_conf:.3f}")
    print(f"  Confidence gap: {confidence_gap:.3f}")
    
    # confusion matrix analysis
    print(f"\nConfusion Matrix:")
    confusion_matrix = pd.crosstab(df['true_quality'], df['predicted_quality'], margins=True)
    print(confusion_matrix)
    
    # model bias analysis
    print(f"\nModel Bias Analysis:")
    avg_true = df['true_quality'].mean()
    avg_pred = df['predicted_quality'].mean()
    bias = avg_pred - avg_true
    
    print(f"  Average true quality: {avg_true:.3f}")
    print(f"  Average predicted quality: {avg_pred:.3f}")
    print(f"  Prediction bias: {bias:.3f}")
    
    if abs(bias) < 0.1:
        print("  → Model shows minimal bias")
    elif bias > 0:
        print("  → Model tends to over-predict quality")
    else:
        print("  → Model tends to under-predict quality")
    
    # high/low confidence analysis
    high_conf_threshold = df['prediction_confidence'].quantile(0.75)
    low_conf_threshold = df['prediction_confidence'].quantile(0.25)
    
    high_conf_mask = df['prediction_confidence'] >= high_conf_threshold
    low_conf_mask = df['prediction_confidence'] <= low_conf_threshold
    
    high_conf_accuracy = (df[high_conf_mask]['true_quality'] == df[high_conf_mask]['predicted_quality']).mean()
    low_conf_accuracy = (df[low_conf_mask]['true_quality'] == df[low_conf_mask]['predicted_quality']).mean()
    
    print(f"\nConfidence-based accuracy:")
    print(f"  High confidence (≥{high_conf_threshold:.3f}): {high_conf_accuracy:.3f}")
    print(f"  Low confidence (≤{low_conf_threshold:.3f}): {low_conf_accuracy:.3f}")
    
    print(f"\n" + "="*50)
    print("ASSESSMENT SUMMARY")
    print("="*50)
    
    if accuracy >= 0.8:
        performance = "Excellent"
    elif accuracy >= 0.6:
        performance = "Good"
    elif accuracy >= 0.4:
        performance = "Fair"
    else:
        performance = "Poor"
    
    print(f"Overall Performance: {performance} ({accuracy:.1%})")
    
    if close_accuracy >= 0.95:
        print(f"Ordinal Performance: Excellent ({close_accuracy:.1%} within 1 quality level)")
    elif close_accuracy >= 0.85:
        print(f"Ordinal Performance: Good ({close_accuracy:.1%} within 1 quality level)")
    else:
        print(f"Ordinal Performance: Needs improvement ({close_accuracy:.1%} within 1 quality level)")
    
    if confidence_gap > 0.05:
        print("Confidence Calibration: Well calibrated")
    elif confidence_gap > 0:
        print("Confidence Calibration: Moderately calibrated")
    else:
        print("Confidence Calibration: Poor calibration")
    
    results = {
        'accuracy': accuracy,
        'close_accuracy': close_accuracy,
        'confidence_gap': confidence_gap,
        'bias': bias,
        'quality_accuracy': quality_accuracy,
        'confidence_stats': confidence_stats.to_dict()
    }
    
    return results

def main():
    
    # Try prediction file name
    possible_files = ['predictions.csv']
    
    analysis_results = None
    for filename in possible_files:
        try:
            analysis_results = analyze_predictions(filename)
            if analysis_results is not None:
                break
        except FileNotFoundError:
            continue
    
    if analysis_results is None:
        print("Could not find any prediction files. Please ensure you have:")
        print("- predictions.csv (from Random Forest script)")
        print("Also ensure you run the Random Forest script first to generate predictions.")
    
    return analysis_results

if __name__ == "__main__":
    results = main()

    if results:
        print("\nAnalysis completed successfully.")
        print("Results:", results)
    else:
        print("No results to display. Please check the input data and try again.")

# This code is part of a an analysis module for evaluating the performance
# of a Random Forest model on quality predictions.
