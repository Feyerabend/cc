import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler
from PIL import Image, ImageDraw, ImageFont
import json
import os

def create_sample_data():
    np.random.seed(42)
    n_samples = 1000
    
    # Create synthetic features
    data = {
        'fixed_acidity': np.random.normal(8.3, 1.7, n_samples),
        'volatile_acidity': np.random.normal(0.5, 0.18, n_samples),
        'citric_acid': np.random.normal(0.27, 0.19, n_samples),
        'residual_sugar': np.random.lognormal(1.8, 1.2, n_samples),
        'chlorides': np.random.normal(0.087, 0.047, n_samples),
        'free_sulfur_dioxide': np.random.normal(15.9, 10.5, n_samples),
        'total_sulfur_dioxide': np.random.normal(46, 32, n_samples),
        'density': np.random.normal(0.997, 0.002, n_samples),
        'pH': np.random.normal(3.3, 0.15, n_samples),
        'sulphates': np.random.normal(0.66, 0.17, n_samples),
        'alcohol': np.random.normal(10.4, 1.07, n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # create quality target based on feature combinations
    quality_score = (
        (df['alcohol'] - 10.4) * 0.3 +
        (12 - df['volatile_acidity']) * 0.2 +
        (df['citric_acid'] - 0.27) * 0.15 +
        np.random.normal(0, 0.5, n_samples)
    )
    
    df['quality'] = np.clip(np.round(quality_score + 6), 3, 9).astype(int)
    
    # Save to CSV
    df.to_csv('wine_quality_data.csv', index=False)
    print(f"Created sample dataset: wine_quality_data.csv ({df.shape[0]} rows, {df.shape[1]} columns)")
    return df

def create_feature_importance_chart(feature_importance, filename='feature_importance.png'):
    
    # Chart dimensions
    width, height = 800, 600
    margin = 80
    chart_width = width - 2 * margin
    chart_height = height - 2 * margin
    
    # Create image
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Try loading font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 12)
        title_font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # Sort features by importance
    sorted_features = feature_importance.sort_values('importance', ascending=True)
    
    # Calculate bar dimensions
    n_features = len(sorted_features)
    bar_height = chart_height // n_features - 5
    max_importance = sorted_features['importance'].max()
    
    # Draw title
    draw.text((width//2 - 100, 20), "Feature Importance", fill='black', font=title_font)
    
    # Draw bars and labels
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8C471']
    
    for i, (idx, row) in enumerate(sorted_features.iterrows()):
        y_pos = margin + i * (bar_height + 5)
        bar_width = int((row['importance'] / max_importance) * (chart_width - 150))
        
        # Draw bar
        color = colors[i % len(colors)]
        draw.rectangle([margin + 150, y_pos, margin + 150 + bar_width, y_pos + bar_height], 
                      fill=color, outline='black')
        
        # Draw feature name
        draw.text((margin, y_pos + bar_height//2 - 6), row['feature'][:15], fill='black', font=font)
        
        # Draw importance value
        draw.text((margin + 150 + bar_width + 5, y_pos + bar_height//2 - 6), 
                 f"{row['importance']:.3f}", fill='black', font=font)
    
    # Save image
    img.save(filename)
    print(f"Feature importance chart saved as: {filename}")

def create_confusion_matrix_chart(cm, class_labels, filename='confusion_matrix.png'):    
    width, height = 600, 600
    margin = 80
    chart_size = min(width, height) - 2 * margin
    
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 12)
        title_font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # Draw title
    draw.text((width//2 - 80, 20), "Confusion Matrix", fill='black', font=title_font)
    
    n_classes = len(class_labels)
    cell_size = chart_size // n_classes
    max_value = cm.max()
    
    # Draw matrix
    for i in range(n_classes):
        for j in range(n_classes):
            x1 = margin + j * cell_size
            y1 = margin + i * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            
            # Color based on value (darker = higher)
            intensity = int(255 * (1 - cm[i, j] / max_value))
            color = (intensity, intensity, 255)
            
            draw.rectangle([x1, y1, x2, y2], fill=color, outline='black')
            
            # Draw value
            text = str(cm[i, j])
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            draw.text((x1 + cell_size//2 - text_width//2, y1 + cell_size//2 - text_height//2), 
                     text, fill='black', font=font)
    
    # Draw labels
    for i, label in enumerate(class_labels):
        # Row labels (True)
        draw.text((margin - 30, margin + i * cell_size + cell_size//2 - 6), 
                 str(label), fill='black', font=font)
        # Column labels (Predicted)
        draw.text((margin + i * cell_size + cell_size//2 - 6, margin - 30), 
                 str(label), fill='black', font=font)
    
    draw.text((margin - 50, margin + chart_size//2), "True", fill='black', font=font)
    draw.text((margin + chart_size//2, margin - 50), "Predicted", fill='black', font=font)
    
    img.save(filename)
    print(f"Confusion matrix chart saved as: {filename}")


def main():
    print("Random Forest Wine Quality Classification with File I/O")
    print("=" * 60)
    
    # Create sample data if it doesn't exist
    if not os.path.exists('wine_quality_data.csv'):
        print("Creating sample dataset ..")
        create_sample_data()
    
    # Read data from CSV
    print("\nReading data from wine_quality_data.csv ..")
    df = pd.read_csv('wine_quality_data.csv')
    
    print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"\nQuality distribution:")
    quality_dist = df['quality'].value_counts().sort_index()
    print(quality_dist)
    
    # Prepare features and target
    X = df.drop('quality', axis=1)
    y = df['quality']
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTraining set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    
    # Create and train Random Forest
    rf_classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        oob_score=True,  # Enable out-of-bag scoring
        n_jobs=-1
    )
    
    print("\nTraining Random Forest...")
    rf_classifier.fit(X_train, y_train)
    
    # Make predictions
    y_pred = rf_classifier.predict(X_test)
    y_pred_proba = rf_classifier.predict_proba(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    cv_scores = cross_val_score(rf_classifier, X_train, y_train, cv=5)
    
    # Prepare results dictionary
    results = {
        'model_performance': {
            'accuracy': float(accuracy),
            'cross_validation_mean': float(cv_scores.mean()),
            'cross_validation_std': float(cv_scores.std()),
            'oob_score': float(rf_classifier.oob_score_),
            'cv_scores': cv_scores.tolist()
        },
        'model_parameters': {
            'n_estimators': rf_classifier.n_estimators,
            'max_depth': rf_classifier.max_depth,
            'min_samples_split': rf_classifier.min_samples_split,
            'min_samples_leaf': rf_classifier.min_samples_leaf
        },
        'feature_importance': {
            feature: float(importance) 
            for feature, importance in zip(X.columns, rf_classifier.feature_importances_)
        },
        'quality_distribution': quality_dist.to_dict()
    }
    
    # Save results to JSON
    with open('random_forest_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: random_forest_results.json")
    
    # Save detailed classification report
    class_report = classification_report(y_test, y_pred, output_dict=True)
    with open('classification_report.json', 'w') as f:
        json.dump(class_report, f, indent=2)
    print(f"Classification report saved to: classification_report.json")
    
    # Save predictions
    predictions_df = pd.DataFrame({
        'true_quality': y_test.values,
        'predicted_quality': y_pred,
        'prediction_confidence': np.max(y_pred_proba, axis=1)
    })
    predictions_df.to_csv('predictions.csv', index=False)
    print(f"Predictions saved to: predictions.csv")
    
    # Create feature importance DataFrame for visualization
    feature_importance_df = pd.DataFrame({
        'feature': X.columns,
        'importance': rf_classifier.feature_importances_
    })
    
    # Create visualizations using Pillow
    print(f"\nCreating visualizations...")
    create_feature_importance_chart(feature_importance_df)
    
    # Create confusion matrix with consistent labels
    unique_labels = sorted(y_test.unique())  # Only use labels present in test set
    cm = confusion_matrix(y_test, y_pred, labels=unique_labels)
    create_confusion_matrix_chart(cm, unique_labels)
    
    # Print summary to console
    print(f"\n" + "="*60)
    print("SUMMARY RESULTS")
    print("="*60)
    print(f"Model Accuracy: {accuracy:.3f}")
    print(f"Cross-validation: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    print(f"Out-of-bag Score: {rf_classifier.oob_score_:.3f}")
    
    print(f"\nTop 5 Most Important Features:")
    top_features = feature_importance_df.sort_values('importance', ascending=False).head()
    for _, row in top_features.iterrows():
        print(f"  {row['feature']:<20}: {row['importance']:.4f}")
    
    print(f"\nFiles created:")
    print(f"  - wine_quality_data.csv (input data)")
    print(f"  - random_forest_results.json (model metrics)")
    print(f"  - classification_report.json (detailed metrics)")
    print(f"  - predictions.csv (test predictions)")
    print(f"  - feature_importance.png (feature importance chart)")
    print(f"  - confusion_matrix.png (confusion matrix)")

if __name__ == "__main__":
    main()

